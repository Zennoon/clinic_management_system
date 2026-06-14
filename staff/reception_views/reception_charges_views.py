import json
from decimal import Decimal

from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Value
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404, render
from django.urls import path, re_path, reverse
from django.utils import timezone
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from ..utils import clean_urlencode, user_has_role

from charges.models import Charge
from payments.models import Payment
from staff.models import Staff


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_charges(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 20

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("q")
    type = request.GET.get("type")
    status = request.GET.get("status")
    order_by = request.GET.get("sort")
    include_past_charges = request.GET.get("include_past")
    show_settled_charges = request.GET.get("show_settled")
    show_archived = request.GET.get("show_archived")

    qs = Charge.objects.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)
    if not show_settled_charges and status != Charge.ChargeStatusEnum.SETTLED:
        qs = qs.exclude(net_balance_annotated=Decimal("0.00"))
    if not include_past_charges:
        qs = qs.filter(date__date=timezone.now().date())

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q
        qs = (
            qs.annotate(
                full_name=Concat(
                    "visit__patient__first_name",
                    Value(" "),
                    "visit__patient__last_name",
                )
            )
            .filter(
                Q(id__icontains=id_q)
                | Q(visit__id__icontains=id_q)
                | Q(visit__patient__id__icontains=id_q)
                | Q(full_name__icontains=q)
                | Q(visit__patient__phone__icontains=q)
            )
            .distinct()
        )
    if type:
        qs = qs.filter(charge_type=type)
    if status:
        qs = qs.filter(charge_status_annotated=status)
    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")
    paginator = Paginator(qs, per_page)
    try:
        charges = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        charges = paginator.page(1)
    except EmptyPage:
        charges = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {
        "charges": charges,
        "charge_types": Charge.ChargeTypeEnum.choices,
        "charge_statuses": Charge.ChargeStatusEnum.choices,
        "order_options": {
            "id": "ID",
            "visit__patient__first_name": "Patient First Name",
            "visit__patient__last_name": "Patient Last Name",
            "amount": "Amount",
            "net_paid_annotated": "Total Payments",
            "net_balance_annotated": "Balance",
            "date": "Date",
        },
    }

    if request.headers.get("HX-Request"):
        return render(
            request, "staff/reception/charges/partials/charges-partial.html", context
        )

    return render(request, "staff/reception/charges/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_charges_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 20

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("q")
    type = request.GET.get("type")
    status = request.GET.get("status")
    order_by = request.GET.get("sort")
    include_past_charges = request.GET.get("include_past")
    show_settled_charges = request.GET.get("show_settled")
    show_archived = request.GET.get("show_archived")

    qs = Charge.objects.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)
    if not show_settled_charges and status != Charge.ChargeStatusEnum.SETTLED:
        print(status)
        qs = qs.exclude(net_balance_annotated=Decimal("0.00"))
    if not include_past_charges:
        qs = qs.filter(date__date=timezone.now().date())

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q
        qs = (
            qs.annotate(
                full_name=Concat(
                    "visit__patient__first_name",
                    Value(" "),
                    "visit__patient__last_name",
                )
            )
            .filter(
                Q(id__icontains=id_q)
                | Q(visit__id__icontains=id_q)
                | Q(visit__patient__id__icontains=id_q)
                | Q(full_name__icontains=q)
                | Q(visit__patient__phone__icontains=q)
            )
            .distinct()
        )
    if type:
        qs = qs.filter(charge_type=type)
    if status:
        qs = qs.filter(charge_status_annotated=status)
    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")
    paginator = Paginator(qs, per_page)
    try:
        charges = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        charges = paginator.page(1)
    except EmptyPage:
        charges = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"charges": charges}
    response = render(
        request,
        "staff/reception/charges/partials/charges-table-partial.html",
        context,
    )
    if not show_settled_charges and status == Charge.ChargeStatusEnum.SETTLED:
        response["HX-Trigger"] = json.dumps(
            {
                "update-element-value": {
                    "elementId": "show_settled",
                    "value": "on",
                    "message": "Please remove the 'Settled' status filter to hide settled charges",
                }
            }
        )
        response["HX-Push-Url"] = (
            f"{reverse("staff:reception_charges")}{clean_urlencode(request.GET, show_settled="on")}"
        )
    else:
        response["HX-Push-Url"] = (
            f"{reverse("staff:reception_charges")}{clean_urlencode(request.GET)}"
        )
    return response


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_charges_table_row(request: HttpRequest, id):
    charge = get_object_or_404(Charge.objects.with_financials(), pk=id)
    return render(
        request,
        "staff/reception/charges/partials/charges-table-row-partial.html",
        {"charge": charge},
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_charge_details(request: HttpRequest, id):
    charge = get_object_or_404(Charge.objects.with_financials(), pk=id)

    total_paid = charge.net_paid_annotated

    payment_by_method = (
        Payment.objects.with_financials()
        .filter(charge=charge, net_paid_annotated__gt=Decimal("0.00"))
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

    payments_paginator = Paginator(
        charge.payments.with_financials()
        .exclude(is_operational_annotated=False)
        .order_by("-date"),
        per_page=5,
    )
    charge_payments = payments_paginator.get_page(1)

    context = {
        "charge": charge,
        "charge_payments": charge_payments,
        "payment_order_options": {
            "id": "ID",
            "amount": "Amount",
            "total_adjusted_annotated": "Adjustment Amount",
            "net_paid_annotated": "Net Paid Amount",
            "date": "Date",
        },
        "payment_method_breakdown": payment_method_breakdown,
    }

    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/reception/charges/partials/charge-details-partial.html",
            context,
        )
    else:
        return render(request, "staff/reception/charges/details/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_charge_payments_filter(request: HttpRequest, id):
    charge = get_object_or_404(Charge, pk=id)

    page = request.GET.get("page", 1)
    per_page = 5

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    order_by = request.GET.get("sort")
    hide_waivers = request.GET.get("hide_waivers")
    show_archived = request.GET.get("show_archived")

    qs = charge.payments.with_financials()

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
        charge_payments = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        charge_payments = paginator.page(1)
    except EmptyPage:
        charge_payments = paginator.page(
            paginator.num_pages if paginator.num_pages else 1
        )

    context = {"charge": charge, "charge_payments": charge_payments}
    return render(
        request,
        "staff/reception/charges/partials/charge-payments-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_charge_payments_table_row(request: HttpRequest, id):
    payment = get_object_or_404(Payment, pk=id)
    return render(
        request,
        "staff/reception/charges/partials/charge-payments-table-row-partial.html",
        {"payment": payment},
    )


reception_charges_urlpatterns = [
    path(
        "reception/charges/",
        reception_charges,
        name="reception_charges",
    ),
    path(
        "reception/charges/filter/",
        reception_charges_filter,
        name="reception_charges_filter",
    ),
    re_path(
        r"^reception/charges/table-row/(?P<id>[0-9]+|__ID__)/$",
        reception_charges_table_row,
        name="reception_charges_table_row",
    ),
    re_path(
        r"^reception/charges/(?P<id>[0-9]+|__ID__)/$",
        reception_charge_details,
        name="reception_charge_details",
    ),
    path(
        "reception/charges/<int:id>/payments/filter/",
        reception_charge_payments_filter,
        name="reception_charge_payments_filter",
    ),
    path(
        "reception/charges/payments/table-row/<int:id>/",
        reception_charge_payments_table_row,
        name="reception_charge_payments_table_row",
    ),
]
