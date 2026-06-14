from decimal import Decimal

from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce, Concat
from django.shortcuts import get_object_or_404, render
from django.urls import path, re_path, reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from ..utils import clean_urlencode, user_has_role

from charges.models import Charge
from patients.models import Patient
from payments.models import Payment
from staff.models import Staff
from visits.models import Visit


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_patients(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 20

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("q")
    sex = request.GET.get("sex")
    region = request.GET.get("region")
    order_by = request.GET.get("sort")
    show_archived = request.GET.get("show_archived")

    if order_by and order_by.endswith("date_of_birth"):
        if order_by.startswith("-"):
            order_by = order_by[1:]
        elif order_by.startswith("date_of_birth"):
            order_by = "-" + order_by

    qs = Patient.objects.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q
        qs = (
            qs.annotate(full_name=Concat("first_name", Value(" "), "last_name"))
            .filter(
                Q(id__icontains=id_q)
                | Q(full_name__icontains=q)
                | Q(phone__icontains=q)
                | Q(city__icontains=q)
                | Q(visits__id__icontains=id_q)
            )
            .distinct()
        )
    if sex:
        qs = qs.filter(sex=sex)
    if region:
        qs = qs.filter(region=region)
    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("id")
    paginator = Paginator(qs, per_page)
    patients = paginator.get_page(page_number)
    context = {
        "patients": patients,
        "regions": Patient.RegionEnum.choices,
        "order_options": {
            "id": "ID",
            "first_name": "First name",
            "last_name": "Last name",
            "date_of_birth": "Age",
            "weight": "Weight",
            "height": "Height",
            "balance": "Outstanding Balance",
            "created_at": "Registration date",
        },
    }

    if request.headers.get("HX-Request"):
        response = render(
            request, "staff/reception/patients/partials/patients-partial.html", context
        )
    else:
        response = render(request, "staff/reception/patients/page.html", context)

    return response


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_patients_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 20

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("q")
    sex = request.GET.get("sex")
    region = request.GET.get("region")
    order_by = request.GET.get("sort")
    show_archived = request.GET.get("show_archived")

    if order_by and order_by.endswith("date_of_birth"):
        if order_by.startswith("-"):
            order_by = order_by[1:]
        elif order_by.startswith("date_of_birth"):
            order_by = "-" + order_by

    qs = Patient.objects.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q
        qs = (
            qs.annotate(full_name=Concat("first_name", Value(" "), "last_name"))
            .filter(
                Q(id__icontains=id_q)
                | Q(full_name__icontains=q)
                | Q(phone__icontains=q)
                | Q(city__icontains=q)
                | Q(visits__id__icontains=id_q)
            )
            .distinct()
        )
    if sex:
        qs = qs.filter(sex=sex)
    if region:
        qs = qs.filter(region=region)
    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("id")

    paginator = Paginator(qs, per_page)
    try:
        patients = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        patients = paginator.page(1)
    except EmptyPage:
        patients = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"patients": patients}
    response = render(
        request,
        "staff/reception/patients/partials/patients-table-partial.html",
        context,
    )
    response["HX-Push-Url"] = (
        f"{reverse("staff:reception_patients")}{clean_urlencode(request.GET)}"
    )
    return response


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_patients_table_row(request: HttpRequest, id):
    patient = get_object_or_404(Patient.objects.with_financials(), pk=id)
    return render(
        request,
        "staff/reception/patients/partials/patients-table-row-partial.html",
        {"patient": patient},
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_patient_details(request: HttpRequest, id):
    patient = get_object_or_404(Patient.objects.with_financials(), pk=id)
    total_charged = patient.total_charged
    total_paid = patient.net_paid

    charges_by_type = (
        patient.charges.values("charge_type")
        .annotate(total_amount=Sum("amount"))
        .order_by("-total_amount")
    )
    charge_type_breakdown = []
    for item in charges_by_type:
        percentage = (
            (item["total_amount"] * 100 / total_charged) if total_charged > 0 else 0
        )
        charge_type_breakdown.append(
            {
                "type": item["charge_type"],
                "amount": item["total_amount"],
                "percentage": percentage,
            }
        )

    payment_by_method = patient.payments.values("payment_method").annotate(
        total_amount=Coalesce(Sum("amount"), Decimal("0.00"))
    )
    adjustment_by_method = patient.payments.values("payment_method").annotate(
        total_amount=Coalesce(Sum("adjustments__amount"), Decimal("0.00"))
    )

    payment_method_breakdown = []
    for item in payment_by_method:
        filtered_adjs = list(
            filter(
                lambda adj: item["payment_method"] == adj["payment_method"],
                adjustment_by_method,
            )
        )

        adjustment = filtered_adjs[0] if filtered_adjs else None
        net_paid = item["total_amount"] - (
            adjustment["total_amount"] if adjustment else Decimal("0.00")
        )
        percentage = (net_paid * 100 / total_paid) if total_paid > 0 else 0
        payment_method_breakdown.append(
            {
                "method": item["payment_method"],
                "amount": net_paid,
                "percentage": percentage,
            }
        )
    payment_method_breakdown.sort(key=lambda item: item["amount"], reverse=True)

    visits_paginator = Paginator(
        patient.visits.with_financials().exclude(is_operational_annotated=False).order_by("-date"), per_page=5
    )
    patient_visits = visits_paginator.get_page(1)

    payments_paginator = Paginator(
        patient.payments.with_financials().exclude(is_operational_annotated=False).order_by("-date"), per_page=5
    )
    patient_payments = payments_paginator.get_page(1)

    charges_paginator = Paginator(
        patient.charges.with_financials()
        .exclude(is_operational_annotated=False)
        .filter(net_balance_annotated__gt=Decimal("0.00"))
        .order_by("-date"),
        per_page=5,
    )
    patient_charges = charges_paginator.get_page(1)

    context = {
        "patient": patient,
        "patient_visits": patient_visits,
        "patient_payments": patient_payments,
        "patient_charges": patient_charges,
        "visit_order_options": {
            "id": "ID",
            "net_charged_annotated": "Total Charges",
            "net_paid_annotated": "Total Payments",
            "net_balance": "Balance",
            "date": "Date",
        },
        "payment_order_options": {
            "id": "ID",
            "amount": "Amount",
            "total_adjusted_annotated": "Adjustment Amount",
            "net_paid_annotated": "Net Paid Amount",
            "date": "Date",
        },
        "charge_order_options": {
            "id": "ID",
            "amount": "Amount",
            "net_paid_annotated": "Net Paid Amount",
            "net_waived_annotated": "Net Waived Amount",
            "net_balance_annotated": "Balance",
            "date": "Date",
        },
        "charge_type_breakdown": charge_type_breakdown,
        "payment_method_breakdown": payment_method_breakdown,
    }

    if request.headers.get("HX-Request"):
        response = render(
            request,
            "staff/reception/patients/partials/patient-details-partial.html",
            context,
        )
        response["HX-Push-Url"] = request.get_full_path()
        return response
    else:
        return render(
            request,
            "staff/reception/patients/details/page.html",
            context,
        )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_patient_visits_filter(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)

    page = request.GET.get("page", 1)
    per_page = 5

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    order_by = request.GET.get("sort")
    hide_inactive = request.GET.get("hide_inactive")
    show_archived = request.GET.get("show_archived")

    qs = patient.visits.with_financials()
    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)
    if hide_inactive:
        qs = qs.exclude(
            visit_status__in=[
                Visit.VisitStatusEnum.CANCELLED,
                Visit.VisitStatusEnum.COMPLETED,
                Visit.VisitStatusEnum.STALE,
            ]
        )

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)
    try:
        patient_visits = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        patient_visits = paginator.page(1)
    except EmptyPage:
        patient_visits = paginator.page(
            paginator.num_pages if paginator.num_pages else 1
        )

    context = {"patient": patient, "patient_visits": patient_visits}
    return render(
        request,
        "staff/reception/patients/partials/patient-visits-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_patient_visits_table_row(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    return render(
        request,
        "staff/reception/patients/partials/patient-visits-table-row-partial.html",
        {"visit": visit},
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_patient_charges_filter(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)

    page = request.GET.get("page", 1)
    per_page = 5

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    order_by = request.GET.get("sort")
    show_archived = request.GET.get("show_archived")
    show_settled = request.GET.get("show_settled")

    qs = patient.charges.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)

    if not show_settled:
        qs = qs.filter(net_balance_annotated__gt=Decimal("0.00"))

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)
    try:
        patient_charges = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        patient_charges = paginator.page(1)
    except EmptyPage:
        patient_charges = paginator.page(
            paginator.num_pages if paginator.num_pages else 1
        )

    context = {"patient": patient, "patient_charges": patient_charges}
    return render(
        request,
        "staff/reception/patients/partials/patient-charges-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_patient_charges_table_row(request: HttpRequest, id):
    charge = get_object_or_404(Charge, pk=id)
    return render(
        request,
        "staff/reception/patients/partials/patient-charges-table-row-partial.html",
        {"charge": charge},
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_patient_payments_filter(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)

    page = request.GET.get("page", 1)
    per_page = 5

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    order_by = request.GET.get("sort")
    hide_waivers = request.GET.get("hide_waivers")
    show_archived = request.GET.get("show_archived")

    qs = patient.payments.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)

    if hide_waivers:
        qs = qs.exclude(
            payment_method__in=[
                Payment.PaymentMethodEnum.GRACE_PERIOD,
                Payment.PaymentMethodEnum.WAIVER,
            ]
        )

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)
    try:
        patient_payments = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        patient_payments = paginator.page(1)
    except EmptyPage:
        patient_payments = paginator.page(
            paginator.num_pages if paginator.num_pages else 1
        )

    context = {"patient": patient, "patient_payments": patient_payments}
    return render(
        request,
        "staff/reception/patients/partials/patient-payments-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_patient_payments_table_row(request: HttpRequest, id):
    payment = get_object_or_404(Payment, pk=id)
    return render(
        request,
        "staff/reception/patients/partials/patient-payments-table-row-partial.html",
        {"payment": payment},
    )


reception_patients_urlpatterns = [
    path("reception/patients/", reception_patients, name="reception_patients"),
    path(
        "reception/patients/filter/",
        reception_patients_filter,
        name="reception_patients_filter",
    ),
    re_path(
        r"^reception/patients/table-row/(?P<id>[0-9]+|__ID__)/$",
        reception_patients_table_row,
        name="reception_patients_table_row",
    ),
    re_path(
        r"^reception/patients/(?P<id>[0-9]+|__ID__)/$",
        reception_patient_details,
        name="reception_patient_details",
    ),
    path(
        "reception/patients/<int:id>/visits/filter/",
        reception_patient_visits_filter,
        name="reception_patient_visits_filter",
    ),
    path(
        "reception/patients/visits/table-row/<int:id>",
        reception_patient_visits_table_row,
        name="reception_patient_visits_table_row",
    ),
    path(
        "reception/patients/<int:id>/payments/filter/",
        reception_patient_payments_filter,
        name="reception_patient_payments_filter",
    ),
    path(
        "reception/patients/payments/table-row/<int:id>",
        reception_patient_payments_table_row,
        name="reception_patient_payments_table_row",
    ),
    path(
        "reception/patients/<int:id>/charges/filter/",
        reception_patient_charges_filter,
        name="reception_patient_charges_filter",
    ),
    path(
        "reception/patients/charges/table-row/<int:id>",
        reception_patient_charges_table_row,
        name="reception_patient_charges_table_row",
    ),
]
