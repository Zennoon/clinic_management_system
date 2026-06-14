from django.contrib.auth.decorators import user_passes_test
from dateutil.relativedelta import relativedelta
from django.http import QueryDict
from django.utils import timezone
from django.db.models import F, Count, Sum, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
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
        procedure=Sum("amount", filter=Q(charge_type=Charge.ChargeTypeEnum.PROCEDURE)),
        medication=Sum(
            "amount", filter=Q(charge_type=Charge.ChargeTypeEnum.MEDICATION)
        ),
        other=Sum("amount", filter=Q(charge_type=Charge.ChargeTypeEnum.OTHER)),
    )

    charges_breakdown["consultation"] = float(charges_breakdown["consultation"] or 0)
    charges_breakdown["laboratory"] = float(charges_breakdown["laboratory"] or 0)
    charges_breakdown["procedure"] = float(charges_breakdown["procedure"] or 0)
    charges_breakdown["medication"] = float(charges_breakdown["medication"] or 0)
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
        .values("lab_services__id", "lab_service__name")
        .annotate(order_count=Count("lab_services__id"), service_name=F("lab_services__name"))
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
        procedure=Sum(
            "charges__amount",
            filter=Q(charges__charge_type=Charge.ChargeTypeEnum.PROCEDURE),
        ),
        medication=Sum(
            "charges__amount",
            filter=Q(charges__charge_type=Charge.ChargeTypeEnum.MEDICATION),
        ),
        other=Sum(
            "charges__amount",
            filter=Q(charges__charge_type=Charge.ChargeTypeEnum.OTHER),
        ),
    )

    charges_breakdown["consultation"] = float(charges_breakdown["consultation"] or 0)
    charges_breakdown["laboratory"] = float(charges_breakdown["laboratory"] or 0)
    charges_breakdown["procedure"] = float(charges_breakdown["procedure"] or 0)
    charges_breakdown["medication"] = float(charges_breakdown["medication"] or 0)
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
        .annotate(order_count=Count("lab_services__id"), service_name=F("lab_services__name"))
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
