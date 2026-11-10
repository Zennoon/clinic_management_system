from decimal import Decimal
import json

from django.contrib.auth.decorators import user_passes_test
from dateutil.relativedelta import relativedelta
from django.http import QueryDict
from django.utils import timezone
from django.db.models import F, Count, QuerySet, Sum, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from django.core.serializers.json import DjangoJSONEncoder
from datetime import timedelta
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO
from constance import config

from charges.models import Charge
from lab_requests.models import LabRequest
from payments.models import Payment
from staff.models import Staff
from visits.models import Visit


def user_has_role(role: Staff.RoleEnum):
    def decorator(view_func):
        wrapper = user_passes_test(
            lambda u: (
                u.role is role
                or (config.STRICT_MODE is not True and role is not Staff.RoleEnum.ADMIN)
            ),
            login_url="/staff/login",
        )

        return wrapper(view_func)

    return decorator


def fill_missing(visit_data: dict) -> dict:
    visit_data["revenue"] = float(visit_data["revenue"] or 0)
    visit_data["previous_revenue"] = float(visit_data["previous_revenue"] or 0)
    visit_data["charges"] = float(visit_data["charges"] or 0)
    visit_data["previous_charges"] = float(visit_data["previous_charges"] or 0)
    visit_data["count_trend"] = (
        (visit_data["count"] - visit_data["previous_count"])
        / (visit_data["previous_count"] or 1)
        * 100
    )
    visit_data["revenue_trend"] = float(
        (visit_data["revenue"] - visit_data["previous_revenue"])
        / (visit_data["previous_revenue"] or 1)
        * 100
    )
    visit_data["charges_trend"] = float(
        (visit_data["charges"] - visit_data["previous_charges"])
        / (visit_data["previous_charges"] or 1)
        * 100
    )
    return visit_data


def get_timespan_data(start_date, previous_date, history_start_date, trunc):
    visit_count = Visit.objects.filter(date__gte=start_date).distinct().count()
    previous_count = (
        Visit.objects.filter(date__gte=previous_date, date__lt=start_date)
        .distinct()
        .count()
    )
    revenue = (
        Payment.objects.filter(date__gte=start_date)
        .distinct()
        .aggregate(value=Sum("amount"))["value"]
    )
    previous_revenue = (
        Payment.objects.filter(date__gte=previous_date, date__lt=start_date)
        .distinct()
        .aggregate(value=Sum("amount"))["value"]
    )
    charges = (
        Charge.objects.filter(date__gte=start_date)
        .distinct()
        .aggregate(value=Sum("amount"))["value"]
    )
    previous_charges = (
        Charge.objects.filter(date__gte=previous_date, date__lt=start_date)
        .distinct()
        .aggregate(value=Sum("amount"))["value"]
    )

    visit_data = {
        "count": visit_count,
        "previous_count": previous_count,
        "revenue": revenue,
        "previous_revenue": previous_revenue,
        "charges": charges,
        "previous_charges": previous_charges,
    }
    visit_data = fill_missing(visit_data)

    counts_qs = (
        Visit.objects.filter(date__gte=history_start_date)
        .annotate(time=trunc("date"))
        .values("time")
        .annotate(count=Count("id"))
        .order_by("time")
    )
    revenue_qs = (
        Visit.objects.filter(date__gte=history_start_date)
        .annotate(time=trunc("date"))
        .values("time")
        .annotate(revenue=Sum("charges__payments__amount"))
        .order_by("time")
    )
    charges_qs = (
        Visit.objects.filter(date__gte=history_start_date)
        .annotate(time=trunc("date"))
        .values("time")
        .annotate(charges=Sum("charges__amount"))
        .order_by("time")
    )

    revenue_map = {r["time"]: r["revenue"] for r in revenue_qs}
    charges_map = {c["time"]: c["charges"] for c in charges_qs}

    history = []
    for entry in counts_qs:
        t = entry["time"]
        history.append(
            {
                "time": t.isoformat(),
                "count": entry.get("count") or 0,
                "revenue": float(revenue_map.get(t) or 0),
                "charges": float(charges_map.get(t) or 0),
            }
        )

    charges_breakdown = Charge.objects.filter(date__gte=start_date).aggregate(
        consultation=Sum(
            "amount", filter=Q(charge_type=Charge.ChargeTypeEnum.CONSULTATION)
        ),
        laboratory=Sum(
            "amount", filter=Q(charge_type=Charge.ChargeTypeEnum.LABORATORY)
        ),
        treatment=Sum("amount", filter=Q(charge_type=Charge.ChargeTypeEnum.TREATMENT)),
        medical_report=Sum(
            "amount", filter=Q(charge_type=Charge.ChargeTypeEnum.MEDICAL_REPORT)
        ),
        other=Sum("amount", filter=Q(charge_type=Charge.ChargeTypeEnum.OTHER)),
    )

    charges_breakdown["consultation"] = float(charges_breakdown["consultation"] or 0)
    charges_breakdown["laboratory"] = float(charges_breakdown["laboratory"] or 0)
    charges_breakdown["treatment"] = float(charges_breakdown["treatment"] or 0)
    charges_breakdown["medical_report"] = float(
        charges_breakdown["medical_report"] or 0
    )
    charges_breakdown["other"] = float(charges_breakdown["other"] or 0)

    payments_method_breakdown = Payment.objects.filter(date__gte=start_date).aggregate(
        cash=Sum("amount", filter=Q(payment_method=Payment.PaymentMethodEnum.CASH)),
        card=Sum("amount", filter=Q(payment_method=Payment.PaymentMethodEnum.CARD)),
        mobile=Sum("amount", filter=Q(payment_method=Payment.PaymentMethodEnum.MOBILE)),
        other=Sum("amount", filter=Q(payment_method=Payment.PaymentMethodEnum.OTHER)),
    )

    payments_method_breakdown["cash"] = float(payments_method_breakdown["cash"] or 0)
    payments_method_breakdown["card"] = float(payments_method_breakdown["card"] or 0)
    payments_method_breakdown["mobile"] = float(
        payments_method_breakdown["mobile"] or 0
    )
    payments_method_breakdown["other"] = float(payments_method_breakdown["other"] or 0)

    payments_status_breakdown = Payment.objects.filter(date__gte=start_date).aggregate(
        pending=Sum(
            "amount", filter=Q(payment_status=Payment.PaymentStatusEnum.PENDING)
        ),
        confirmed=Sum(
            "amount", filter=Q(payment_status=Payment.PaymentStatusEnum.CONFIRMED)
        ),
        refunded=Sum(
            "amount", filter=Q(payment_status=Payment.PaymentStatusEnum.REFUNDED)
        ),
    )

    payments_status_breakdown["pending"] = float(
        payments_status_breakdown["pending"] or 0
    )
    payments_status_breakdown["confirmed"] = float(
        payments_status_breakdown["confirmed"] or 0
    )
    payments_status_breakdown["refunded"] = float(
        payments_status_breakdown["refunded"] or 0
    )

    most_ordered_lab_services = (
        LabRequest.objects.filter(date__gte=start_date)
        .values("lab_services__id", "lab_services__name")
        .annotate(
            order_count=Count("lab_services__id"), service_name=F("lab_services__name")
        )
        .order_by("-order_count")
        .distinct()[:5]
    )

    return {
        "visit_data": visit_data,
        "history": history,
        "charges_breakdown": charges_breakdown,
        "payments_method_breakdown": payments_method_breakdown,
        "payments_status_breakdown": payments_status_breakdown,
        "most_ordered_lab_services": list(most_ordered_lab_services),
    }


def get_today_data():
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    return get_timespan_data(
        start_date=today,
        previous_date=yesterday,
        history_start_date=today - relativedelta(days=29),
        trunc=TruncDate,
    )


def get_week_data():
    now = timezone.now()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    previous_week_start = week_start - timedelta(days=7)
    return get_timespan_data(
        start_date=week_start,
        previous_date=previous_week_start,
        history_start_date=week_start - relativedelta(weeks=9),
        trunc=TruncWeek,
    )


def get_month_data():
    now = timezone.now()
    today = now.date()
    month_start = today.replace(day=1)
    previous_month_start = month_start - relativedelta(months=1)
    return get_timespan_data(
        start_date=month_start,
        previous_date=previous_month_start,
        history_start_date=month_start - relativedelta(months=9),
        trunc=TruncMonth,
    )


def get_year_data():
    now = timezone.now()
    today = now.date()
    year_start = timezone.datetime(today.year, 1, 1, 0, 0, 0, 0)
    previous_year_start = year_start - relativedelta(years=1)
    return get_timespan_data(
        start_date=year_start,
        previous_date=previous_year_start,
        history_start_date=year_start - relativedelta(years=9),
        trunc=TruncYear,
    )


def get_all_data():
    visit_count = Visit.objects.count()
    previous_count = visit_count
    revenue = Visit.objects.aggregate(value=Sum("charges__payments__amount"))["value"]
    previous_revenue = revenue
    charges = Visit.objects.aggregate(value=Sum("charges__amount"))["value"]
    previous_charges = charges

    visit_data = {
        "count": visit_count,
        "previous_count": previous_count,
        "revenue": revenue,
        "previous_revenue": previous_revenue,
        "charges": charges,
        "previous_charges": previous_charges,
    }
    visit_data = fill_missing(visit_data)

    # build history by computing counts, revenues and charges in separate queries
    counts_qs = (
        Visit.objects.annotate(time=TruncYear("created_at"))
        .values("time")
        .annotate(count=Count("id"))
        .order_by("time")
    )

    revenue_qs = (
        Visit.objects.annotate(time=TruncYear("created_at"))
        .values("time")
        .annotate(revenue=Sum("charges__payments__amount"))
        .order_by("time")
    )

    charges_qs = (
        Visit.objects.annotate(time=TruncYear("created_at"))
        .values("time")
        .annotate(charges=Sum("charges__amount"))
        .order_by("time")
    )

    revenue_map = {r["time"]: r["revenue"] for r in revenue_qs}
    charges_map = {c["time"]: c["charges"] for c in charges_qs}

    history = []
    for entry in counts_qs:
        t = entry["time"]
        history.append(
            {
                "time": t.isoformat(),
                "count": entry.get("count") or 0,
                "revenue": float(revenue_map.get(t) or 0),
                "charges": float(charges_map.get(t) or 0),
            }
        )

    charges_breakdown = Visit.objects.aggregate(
        consultation=Sum(
            "charges__amount",
            filter=Q(charges__charge_type=Charge.ChargeTypeEnum.CONSULTATION),
        ),
        laboratory=Sum(
            "charges__amount",
            filter=Q(charges__charge_type=Charge.ChargeTypeEnum.LABORATORY),
        ),
        treatment=Sum(
            "charges__amount",
            filter=Q(charges__charge_type=Charge.ChargeTypeEnum.TREATMENT),
        ),
        medical_report=Sum(
            "charges__amount",
            filter=Q(charges__charge_type=Charge.ChargeTypeEnum.MEDICAL_REPORT),
        ),
        other=Sum(
            "charges__amount",
            filter=Q(charges__charge_type=Charge.ChargeTypeEnum.OTHER),
        ),
    )

    charges_breakdown["consultation"] = float(charges_breakdown["consultation"] or 0)
    charges_breakdown["laboratory"] = float(charges_breakdown["laboratory"] or 0)
    charges_breakdown["treatment"] = float(charges_breakdown["treatment"] or 0)
    charges_breakdown["medical_report"] = float(
        charges_breakdown["medical_report"] or 0
    )
    charges_breakdown["other"] = float(charges_breakdown["other"] or 0)

    payments_method_breakdown = Payment.objects.aggregate(
        cash=Sum("amount", filter=Q(payment_method=Payment.PaymentMethodEnum.CASH)),
        card=Sum("amount", filter=Q(payment_method=Payment.PaymentMethodEnum.CARD)),
        mobile=Sum("amount", filter=Q(payment_method=Payment.PaymentMethodEnum.MOBILE)),
        other=Sum("amount", filter=Q(payment_method=Payment.PaymentMethodEnum.OTHER)),
    )

    payments_method_breakdown["cash"] = float(payments_method_breakdown["cash"] or 0)
    payments_method_breakdown["card"] = float(payments_method_breakdown["card"] or 0)
    payments_method_breakdown["mobile"] = float(
        payments_method_breakdown["mobile"] or 0
    )
    payments_method_breakdown["other"] = float(payments_method_breakdown["other"] or 0)

    payments_status_breakdown = Payment.objects.aggregate(
        pending=Sum(
            "amount", filter=Q(payment_status=Payment.PaymentStatusEnum.PENDING)
        ),
        confirmed=Sum(
            "amount", filter=Q(payment_status=Payment.PaymentStatusEnum.CONFIRMED)
        ),
        refunded=Sum(
            "amount", filter=Q(payment_status=Payment.PaymentStatusEnum.REFUNDED)
        ),
    )

    payments_status_breakdown["pending"] = float(
        payments_status_breakdown["pending"] or 0
    )
    payments_status_breakdown["confirmed"] = float(
        payments_status_breakdown["confirmed"] or 0
    )
    payments_status_breakdown["refunded"] = float(
        payments_status_breakdown["refunded"] or 0
    )

    most_ordered_lab_services = (
        LabRequest.objects.values("lab_services__id", "lab_services__name")
        .annotate(
            order_count=Count("lab_services__id"), service_name=F("lab_services__name")
        )
        .order_by("-order_count")[:5]
    )

    return {
        "visit_data": visit_data,
        "history": history,
        "charges_breakdown": charges_breakdown,
        "payments_method_breakdown": payments_method_breakdown,
        "payments_status_breakdown": payments_status_breakdown,
        "most_ordered_lab_services": list(most_ordered_lab_services),
    }


def get_patient_vitals_chart_data(patient):
    base_qs: QuerySet = patient.vital_signs.order_by("date")

    bp_qs = (
        base_qs.exclude(bp_systolic__isnull=True)
        .exclude(bp_diastolic__isnull=True)
        .values_list("date", "bp_systolic", "bp_diastolic")
    )
    bp_labels, systolics, diastolics = zip(*bp_qs) if bp_qs else ([], [], [])

    pulse_qs = base_qs.exclude(pulse_rate__isnull=True).values_list(
        "date", "pulse_rate"
    )
    pulse_labels, pulses = zip(*pulse_qs) if pulse_qs else ([], [])

    respiratory_rate_qs = base_qs.exclude(respiratory_rate__isnull=True).values_list(
        "date", "respiratory_rate"
    )
    respiratory_labels, respiratory_rates = (
        zip(*respiratory_rate_qs) if respiratory_rate_qs else ([], [])
    )

    temperature_labels, temperature_values = get_temperature_chart_data(base_qs)

    weight_labels, weight_values = get_weight_chart_data(base_qs)

    height_labels, height_values = get_height_chart_data(base_qs)

    spo2_qs = base_qs.exclude(spo2__isnull=True).values_list("date", "spo2")
    spo2_labels, spo2_values = zip(*spo2_qs) if spo2_qs else ([], [])

    mock_vitals_data = {
        "blood_pressure": {
            "labels": [
                "Sep 01, 08:00", "Sep 01, 14:00", "Sep 01, 20:00",
                "Sep 02, 08:30", "Sep 02, 15:00", "Sep 02, 21:00",
                "Sep 03, 08:00", "Sep 03, 19:30",
                "Sep 04, 08:15", "Sep 04, 14:30", "Sep 04, 20:45",
                "Sep 05, 08:00", "Sep 05, 18:00",
                "Sep 06, 09:00", "Sep 06, 17:30",
                "Sep 07, 08:00"
            ],
            "systolic": [122, 128, 125, 130, 135, 128, 124, 121, 119, 126, 122, 120, 123, 118, 121, 120],
            "diastolic": [80, 84, 82, 85, 88, 83, 81, 79, 78, 82, 80, 78, 80, 76, 79, 78],
        },
        "pulse_rate": {
            "labels": [
                "Sep 01, 08:00", "Sep 01, 14:00", "Sep 01, 20:00",
                "Sep 02, 08:30", "Sep 02, 15:00", "Sep 02, 21:00",
                "Sep 03, 08:00", "Sep 03, 14:00", "Sep 03, 19:30",
                "Sep 04, 08:15", "Sep 04, 20:45",
                "Sep 05, 08:00", "Sep 05, 18:00",
                "Sep 06, 09:00", "Sep 06, 17:30",
                "Sep 07, 08:00"
            ],
            "values": [72, 78, 75, 82, 88, 80, 74, 76, 71, 69, 73, 70, 72, 68, 71, 69],
        },
        "respiratory_rate": {
            "labels": [
                "Sep 01, 08:00", "Sep 01, 20:00",
                "Sep 02, 08:30", "Sep 02, 21:00",
                "Sep 03, 08:00", "Sep 03, 19:30",
                "Sep 04, 08:15", "Sep 04, 20:45",
                "Sep 05, 08:00",
                "Sep 06, 09:00",
                "Sep 07, 08:00"
            ],
            "values": [16, 17, 19, 18, 16, 15, 16, 16, 15, 14, 15],
        },
        "temperature": {
            "labels": [
                "Sep 01, 08:00", "Sep 01, 14:00", "Sep 01, 20:00",
                "Sep 02, 08:30", "Sep 02, 15:00", "Sep 02, 21:00",
                "Sep 03, 08:00", "Sep 03, 19:30",
                "Sep 04, 08:15", "Sep 04, 20:45",
                "Sep 05, 08:00", "Sep 05, 18:00",
                "Sep 06, 09:00",
                "Sep 07, 08:00"
            ],
            "values": [36.8, 37.2, 37.5, 38.1, 38.6, 37.9, 37.3, 37.0, 36.9, 36.8, 36.7, 36.8, 36.6, 36.7],
        },
        "weight": {
            "labels": [
                "Sep 01, 08:00",
                "Sep 03, 08:00",
                "Sep 05, 08:00",
                "Sep 07, 08:00"
            ],
            "values": [74.5, 74.3, 74.1, 73.9],
        },
        "height": {
            "labels": [
                "Sep 01, 08:00"
            ],
            "values": [175.0],
        },
        "spo2": {
            "labels": [
                "Sep 01, 08:00", "Sep 01, 14:00", "Sep 01, 20:00",
                "Sep 02, 08:30", "Sep 02, 15:00", "Sep 02, 21:00",
                "Sep 03, 08:00", "Sep 03, 19:30",
                "Sep 04, 08:15", "Sep 04, 20:45",
                "Sep 05, 08:00",
                "Sep 06, 09:00",
                "Sep 07, 08:00"
            ],
            "values": [98, 97, 98, 95, 94, 96, 98, 99, 98, 98, 99, 98, 99],
        },
    }
    
    # return json.dumps(mock_vitals_data, cls=DjangoJSONEncoder)
    return json.dumps(
        {
            "blood_pressure": {
                "labels": [date.strftime("%b %d, %H:%M") for date in bp_labels],
                "systolic": list(systolics),
                "diastolic": list(diastolics),
            },
            "pulse_rate": {
                "labels": [date.strftime("%b %d, %H:%M") for date in pulse_labels],
                "values": list(pulses),
            },
            "respiratory_rate": {
                "labels": [
                    date.strftime("%b %d, %H:%M") for date in respiratory_labels
                ],
                "values": list(respiratory_rates),
            },
            "temperature": {"labels": temperature_labels, "values": temperature_values},
            "weight": {"labels": weight_labels, "values": weight_values},
            "height": {"labels": height_labels, "values": height_values},
            "spo2": {
                "labels": [date.strftime("%b %d, %H:%M") for date in spo2_labels],
                "values": list(spo2_values),
            },
        },
        cls=DjangoJSONEncoder
    )


def get_temperature_chart_data(vitals_qs: QuerySet):
    temp_qs = vitals_qs.exclude(temperature__isnull=True).values_list(
        "date", "temperature", "temperature_unit"
    )

    if not temp_qs:
        return ([], [])
    labels = []
    values = []

    for date, val, unit in temp_qs:
        celsius_val = convert_temp_to_celsius(val, unit)

        labels.append(date.strftime("%b %d, %H:%M"))
        values.append(celsius_val)
    return (labels, values)


def get_weight_chart_data(vitals_qs: QuerySet):
    weight_qs = vitals_qs.exclude(weight__isnull=True).values_list(
        "date", "weight", "weight_unit"
    )

    if not weight_qs:
        return ([], [])

    labels = []
    values = []

    for date, val, unit in weight_qs:
        kg_val = convert_weight_to_kg(val, unit)

        labels.append(date.strftime("%b %d, %H:%M"))
        values.append(kg_val)
    return (labels, values)


def get_height_chart_data(vitals_qs: QuerySet):
    height_qs = vitals_qs.exclude(height__isnull=True).values_list(
        "date", "height", "height_unit"
    )

    if not height_qs:
        return ([], [])

    labels = []
    values = []

    for date, val, unit in height_qs:
        cm_val = convert_height_to_cms(val, unit)

        labels.append(date.strftime("%b %d, %H:%M"))
        values.append(cm_val)
    return (labels, values)


def dataframe_to_pdf(df: pd.DataFrame):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=(letter if len(df.columns) < 7 else landscape(letter)),
        leftMargin=5 * cm,
        rightMargin=5 * cm,
    )
    table = Table([df.columns.tolist()] + df.values.tolist())
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    pdf.build([table])

    buffer.seek(0)
    return buffer


def dataframe_to_excel(df: pd.DataFrame):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer


def format_timedelta(td: timedelta) -> str:
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}m")

    parts.append(f"{seconds}s")
    return " ".join(parts)


def clean_urlencode(query_dict: QueryDict, **kwargs):
    params = query_dict.copy()
    for key, val in kwargs.items():
        params[key] = val

    empty_params = []
    for key, val in params.items():
        if isinstance(val, list):
            if val and val[0] == "":
                empty_params.append(key)
        elif val is None or val == "":
            empty_params.append(key)

    for param in empty_params:
        del params[param]

    encoded = params.urlencode()
    return f"?{encoded}" if encoded else ""


def convert_weight_to_kg(weight: Decimal, unit_from):
    from vital_signs.models import VitalSign

    match unit_from:
        case VitalSign.WeightUnitEnum.GRAMS:
            return weight / Decimal("1000")
        case VitalSign.WeightUnitEnum.POUNDS:
            return weight / Decimal("2.20462")
        case VitalSign.WeightUnitEnum.STONES:
            return weight * Decimal("6.350293")
        case VitalSign.WeightUnitEnum.OUNCES:
            return weight / Decimal("35.274")
        case _:
            return weight


def convert_height_to_cms(height: Decimal, unit_from):
    from vital_signs.models import VitalSign

    match unit_from:
        case VitalSign.HeightUnitEnum.METERS:
            return height * Decimal("100")
        case VitalSign.HeightUnitEnum.FEET:
            return height * Decimal("30.48")
        case VitalSign.HeightUnitEnum.INCHES:
            return height * Decimal("2.54")
        case _:
            return height


def convert_temp_to_celsius(temp: Decimal, unit):
    from vital_signs.models import VitalSign

    match unit:
        case VitalSign.TemperatureUnitEnum.FAHRENHEIT:
            return round((temp - 32) * 5 / 9, 1)
        case VitalSign.TemperatureUnitEnum.KELVIN:
            return round(temp - Decimal("273.15"), 1)
        case _:
            return round(temp, 1)
