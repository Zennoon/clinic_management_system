import json

from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required
from django.urls import path, re_path, reverse
from django.utils import timezone
from ..utils import clean_urlencode, user_has_role

from payments.models import Adjustment, Payment
from staff.models import Staff


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_payments(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 20

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("q")
    method = request.GET.get("method")
    order_by = request.GET.get("sort")
    include_past_payments = request.GET.get("include_past")
    hide_waivers = request.GET.get("hide_waivers")
    show_archived = request.GET.get("show_archived")

    qs = Payment.objects.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)
    if hide_waivers and method not in Payment.waiver_payment_methods():
        qs = qs.exclude(payment_method__in=Payment.waiver_payment_methods())
    if not include_past_payments:
        qs = qs.filter(date__date=timezone.now().date())

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q
        qs = (
            qs.annotate(
                full_name=Concat(
                    "charge__visit__patient__first_name",
                    Value(" "),
                    "charge__visit__patient__last_name",
                )
            )
            .filter(
                Q(id__icontains=id_q)
                | Q(charge__id__icontains=id_q)
                | Q(charge__visit__id__icontains=id_q)
                | Q(charge__visit__patient__id__icontains=id_q)
                | Q(full_name__icontains=q)
                | Q(charge__visit__patient__phone__icontains=q)
            )
            .distinct()
        )
    if method:
        qs = qs.filter(payment_method=method)
    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)
    try:
        payments = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        payments = paginator.get_page(1)
    except EmptyPage:
        payments = paginator.get_page(paginator.num_pages if paginator.num_pages else 1)

    context = {
        "payments": payments,
        "payment_methods": Payment.PaymentMethodEnum.choices,
        "order_options": {
            "id": "ID",
            "charge__visit__patient__first_name": "Patient First Name",
            "charge__visit__patient__last_name": "Patient Last Name",
            "amount": "Amount",
            "total_adjusted_annotated": "Adjustment Amount",
            "net_paid_annotated": "Net paid amount",
        },
    }

    if request.headers.get("HX-Request"):
        return render(
            request, "staff/reception/payments/partials/payments-partial.html", context
        )
    return render(request, "staff/reception/payments/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_payments_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 20

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("q")
    method = request.GET.get("method")
    order_by = request.GET.get("sort")
    include_past_payments = request.GET.get("include_past")
    hide_waivers = request.GET.get("hide_waivers")
    show_archived = request.GET.get("show_archived")

    qs = Payment.objects.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)
    if hide_waivers and method not in Payment.waiver_payment_methods():
        qs = qs.exclude(payment_method__in=Payment.waiver_payment_methods())
    if not include_past_payments:
        qs = qs.filter(date__date=timezone.now().date())

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q
        qs = (
            qs.annotate(
                full_name=Concat(
                    "charge__visit__patient__first_name",
                    Value(" "),
                    "charge__visit__patient__last_name",
                )
            )
            .filter(
                Q(id__icontains=id_q)
                | Q(charge__id__icontains=id_q)
                | Q(charge__visit__id__icontains=id_q)
                | Q(charge__visit__patient__id__icontains=id_q)
                | Q(full_name__icontains=q)
                | Q(charge__visit__patient__phone__icontains=q)
            )
            .distinct()
        )
    if method:
        qs = qs.filter(payment_method=method)
    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)
    try:
        payments = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        payments = paginator.get_page(1)
    except EmptyPage:
        payments = paginator.get_page(paginator.num_pages if paginator.num_pages else 1)

    context = {"payments": payments}
    response = render(
        request,
        "staff/reception/payments/partials/payments-table-partial.html",
        context,
    )
    if hide_waivers and method in Payment.waiver_payment_methods():
        response["HX-Trigger"] = json.dumps(
            {
                "update-element-value": {
                    "elementId": "hide_waivers",
                    "value": "on",
                    "message": "Please change the method filter value to hide waiver payments",
                }
            }
        )
        response["HX-Push-Url"] = (
            f"{reverse("staff:reception_payments")}{clean_urlencode(request.GET, hide_waivers=None)}"
        )
    else:
        response["HX-Push-Url"] = (
            f"{reverse("staff:reception_payments")}{clean_urlencode(request.GET)}"
        )
    return response


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_payments_table_row(request: HttpRequest, id):
    payment = get_object_or_404(Payment.objects.with_financials(), pk=id)
    return render(
        request,
        "staff/reception/payments/partials/payments-table-row-partial.html",
        {"payment": payment},
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_payment_details(request: HttpRequest, id):
    payment = get_object_or_404(Payment.objects.with_financials(), pk=id)
    adjustments_paginator = Paginator(
        payment.adjustments.exclude(is_operational_annotated=False).order_by("-date"),
        per_page=5,
    )
    payment_adjustments = adjustments_paginator.get_page(1)

    context = {
        "payment": payment,
        "payment_adjustments": payment_adjustments,
        "adjustment_order_options": {"id": "ID", "amount": "Amount", "date": "Date"},
    }
    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/reception/payments/partials/payment-details-partial.html",
            context,
        )
    else:
        return render(request, "staff/reception/payments/details/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_payment_adjustments_filter(request: HttpRequest, id):
    payment = get_object_or_404(Payment, pk=id)

    page = request.GET.get("page", 1)
    per_page = 5

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    order_by = request.GET.get("sort")
    show_archived = request.GET.get("show_archived")

    qs = payment.adjustments.with_financials()

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)

    if order_by:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)

    try:
        payment_adjustments = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        payment_adjustments = paginator.get_page(1)
    except EmptyPage:
        payment_adjustments = paginator.get_page(
            paginator.num_pages if paginator.num_pages else 1
        )

    context = {"payment": payment, "payment_adjustments": payment_adjustments}
    return render(
        request,
        "staff/reception/payments/partials/payment-adjustments-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_payment_adjustments_table_row(request: HttpRequest, id):
    adjustment = get_object_or_404(Adjustment, pk=id)
    return render(
        request,
        "staff/reception/payments/partials/payment-adjustments-table-row-partial.html",
        {"adjustment": adjustment},
    )


reception_payments_urlpatterns = [
    path("reception/payments", reception_payments, name="reception_payments"),
    path(
        "reception/payments/filter",
        reception_payments_filter,
        name="reception_payments_filter",
    ),
    re_path(
        r"^reception/payments/table-row/(?P<id>[0-9]+|__ID__)/$",
        reception_payments_table_row,
        name="reception_payments_table_row",
    ),
    re_path(
        r"^reception/payments/(?P<id>[0-9]+|__ID__)/$",
        reception_payment_details,
        name="reception_payment_details",
    ),
    path(
        "reception/payments/<int:id>/adjustments/filter/",
        reception_payment_adjustments_filter,
        name="reception_payment_adjustments_filter",
    ),
    re_path(
        r"^reception/payments/adjustments/table-row/(?P<id>[0-9]+|__ID__)/$",
        reception_payment_adjustments_table_row,
        name="reception_payment_adjustments_table_row",
    ),
]
