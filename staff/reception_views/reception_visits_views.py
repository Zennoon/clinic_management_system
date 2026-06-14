from decimal import Decimal

from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404, render
from django.urls import path, re_path, reverse
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from ..utils import clean_urlencode, user_has_role

from charges.models import Charge
from payments.models import Payment
from staff.models import Staff
from visits.models import Visit


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_visits(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 20

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("q")
    category = request.GET.get("category")
    status = request.GET.get("status")
    order_by = request.GET.get("sort")
    include_past_visits = request.GET.get("include_past")
    hide_inactive = request.GET.get("hide_inactive")
    show_archived = request.GET.get("show_archived")

    qs = Visit.objects.with_financials()

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
    if not include_past_visits:
        qs = qs.filter(date__date=timezone.now().date())

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q
        qs = (
            qs.annotate(
                full_name=Concat(
                    "patient__first_name", Value(" "), "patient__last_name"
                )
            )
            .filter(
                Q(id__icontains=id_q)
                | Q(patient__id__icontains=id_q)
                | Q(full_name__icontains=q)
                | Q(patient__phone__icontains=q)
            )
            .distinct()
        )
    if category:
        qs = qs.filter(visit_category=category)
    if status:
        qs = qs.filter(visit_status=status)
    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")
    paginator = Paginator(qs, per_page)
    try:
        visits = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        visits = paginator.page(1)
    except EmptyPage:
        visits = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {
        "visits": visits,
        "visit_categories": Visit.VisitCategoryEnum.choices,
        "visit_statuses": Visit.VisitStatusEnum.choices,
        "order_options": {
            "id": "ID",
            "patient__first_name": "Patient First Name",
            "patient__last_name": "Patient Last Name",
            "total_charged_annotated": "Total Charges",
            "net_paid_annotated": "Total Payments",
            "net_balance_annotated": "Balance",
            "date": "Date",
        },
    }

    if request.headers.get("HX-Request"):
        return render(
            request, "staff/reception/visits/partials/visits-partial.html", context
        )

    return render(request, "staff/reception/visits/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_visits_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 20

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("q")
    category = request.GET.get("category")
    status = request.GET.get("status")
    order_by = request.GET.get("sort")
    include_past_visits = request.GET.get("include_past")
    hide_inactive = request.GET.get("hide_inactive")
    show_archived = request.GET.get("show_archived")

    qs = Visit.objects.with_financials()

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
    if not include_past_visits:
        qs = qs.filter(date__date=timezone.now().date())

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q
        qs = (
            qs.annotate(
                full_name=Concat(
                    "patient__first_name", Value(" "), "patient__last_name"
                )
            )
            .filter(
                Q(id__icontains=id_q)
                | Q(patient__id__icontains=id_q)
                | Q(full_name__icontains=q)
                | Q(patient__phone__icontains=q)
            )
            .distinct()
        )
    if category:
        qs = qs.filter(visit_category=category)
    if status:
        qs = qs.filter(visit_status=status)
    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")
    paginator = Paginator(qs, per_page)
    try:
        visits = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        visits = paginator.page(1)
    except EmptyPage:
        visits = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"visits": visits}
    response = render(
        request,
        "staff/reception/visits/partials/visits-table-partial.html",
        context,
    )
    response["HX-Push-Url"] = (
        f"{reverse("staff:reception_visits")}{clean_urlencode(request.GET)}"
    )
    return response


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_visits_table_row(request: HttpRequest, id):
    visit = get_object_or_404(Visit.objects.with_financials(), pk=id)
    return render(
        request,
        "staff/reception/visits/partials/visits-table-row-partial.html",
        {"visit": visit},
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_visit_details(request: HttpRequest, id):
    print(request.headers)
    visit = get_object_or_404(Visit.objects.with_financials(), pk=id)

    total_charged = visit.total_charged_annotated
    total_paid = visit.net_paid_annotated
    charges_by_type = (
        visit.charges.values("charge_type")
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

    payment_by_method = (
        Payment.objects.with_financials()
        .filter(charge__visit=visit, net_paid_annotated__gt=Decimal("0.00"))
        .values("payment_method")
        .annotate(total_amount=Sum("amount"))
        .order_by("-total_amount")
    )
    payment_method_breakdown = []
    for item in payment_by_method:
        percentage = (item["total_amount"] * 100 / total_paid) if total_paid > 0 else 0
        payment_method_breakdown.append(
            {
                "method": item["payment_method"],
                "amount": item["total_amount"],
                "percentage": percentage,
            }
        )

    charges_paginator = Paginator(
        visit.charges.with_financials()
        .exclude(is_operational_annotated=False)
        .filter(net_paid_annotated__lt=F("amount"))
        .order_by("-date"),
        per_page=5,
    )
    visit_charges = charges_paginator.get_page(1)

    payments_paginator = Paginator(
        visit.payments.with_financials()
        .exclude(is_operational_annotated=False)
        .order_by("-date"),
        per_page=5,
    )
    visit_payments = payments_paginator.get_page(1)

    context = {
        "visit": visit,
        "visit_charges": visit_charges,
        "visit_payments": visit_payments,
        "charge_order_options": {
            "id": "ID",
            "amount": "Amount",
            "net_paid_annotated": "Net Paid Amount",
            "net_Waived_annotated": "Net Waived Amount",
            "net_balance_annotated": "Balance",
            "date": "Date",
        },
        "payment_order_options": {
            "id": "ID",
            "amount": "Amount",
            "total_adjusted_annotated": "Adjustment Amount",
            "net_paid_annotated": "Net Paid Amount",
            "date": "Date",
        },
        "charge_type_breakdown": charge_type_breakdown,
        "payment_method_breakdown": payment_method_breakdown,
    }

    if request.headers.get("HX-Request"):
        response = render(
            request,
            "staff/reception/visits/partials/visit-details-partial.html",
            context,
        )
        response["HX-Push-Url"] = request.path
        return response
    else:
        return render(request, "staff/reception/visits/details/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_visit_charges_filter(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)

    page = request.GET.get("page", 1)
    per_page = 5

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    order_by = request.GET.get("sort")
    show_archived = request.GET.get("show_archived")
    show_settled = request.GET.get("show_settled")

    qs = visit.charges.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)

    if not show_settled:
        qs = qs.filter(net_paid_annotated__lt=F("amount"))

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)
    try:
        visit_charges = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        visit_charges = paginator.page(1)
    except EmptyPage:
        visit_charges = paginator.page(
            paginator.num_pages if paginator.num_pages else 1
        )

    context = {"visit": visit, "visit_charges": visit_charges}
    return render(
        request,
        "staff/reception/visits/partials/visit-charges-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_visit_charges_table_row(request: HttpRequest, id):
    charge = get_object_or_404(Charge, pk=id)
    return render(
        request,
        "staff/reception/visits/partials/visit-charges-table-row-partial.html",
        {"charge": charge},
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_visit_payments_filter(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)

    page = request.GET.get("page", 1)
    per_page = 5

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    order_by = request.GET.get("sort")
    hide_waivers = request.GET.get("hide_waivers")
    show_archived = request.GET.get("show_archived")

    qs = visit.payments.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)

    if hide_waivers:
        qs = qs.exclude(payment_method__in=Payment.waiver_payment_methods())

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)
    try:
        visit_payments = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        visit_payments = paginator.page(1)
    except EmptyPage:
        visit_payments = paginator.page(
            paginator.num_pages if paginator.num_pages else 1
        )

    context = {"visit": visit, "visit_payments": visit_payments}
    return render(
        request,
        "staff/reception/visits/partials/visit-payments-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_visit_payments_table_row(request: HttpRequest, id):
    payment = get_object_or_404(Payment, pk=id)
    return render(
        request,
        "staff/reception/visits/partials/visit-payments-table-row-partial.html",
        {"payment": payment},
    )


reception_visits_urlpatterns = [
    path(
        "reception/visits/",
        reception_visits,
        name="reception_visits",
    ),
    path(
        "reception/visits/filter/",
        reception_visits_filter,
        name="reception_visits_filter",
    ),
    re_path(
        r"^reception/visits/table-row/(?P<id>[0-9]+|__ID__)/$",
        reception_visits_table_row,
        name="reception_visits_table_row",
    ),
    re_path(
        r"^reception/visits/(?P<id>[0-9]+|__ID__)/$",
        reception_visit_details,
        name="reception_visit_details",
    ),
    path(
        "reception/visits/<int:id>/charges/filter/",
        reception_visit_charges_filter,
        name="reception_visit_charges_filter",
    ),
    path(
        "reception/visits/charges/table-row/<int:id>",
        reception_visit_charges_table_row,
        name="reception_visit_charges_table_row",
    ),
    path(
        "reception/visits/<int:id>/payments/filter/",
        reception_visit_payments_filter,
        name="reception_visit_payments_filter",
    ),
    path(
        "reception/visits/payments/table-row/<int:id>",
        reception_visit_payments_table_row,
        name="reception_visit_payments_table_row",
    ),
]
