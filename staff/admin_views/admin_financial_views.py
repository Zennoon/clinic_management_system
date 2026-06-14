import json
from django.urls import path
import pandas as pd
from django.http import HttpRequest, HttpResponseBadRequest, FileResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder

from staff.utils import user_has_role
from charges.models import Charge
from payments.models import Payment
from staff.models import Staff
from staff.utils import (
    dataframe_to_excel,
    dataframe_to_pdf,
    get_today_data,
    get_week_data,
    get_month_data,
    get_year_data,
    get_all_data,
)


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_charges(request: HttpRequest):
    qs = Charge.objects.order_by("id").all()
    paginator = Paginator(qs, per_page=50)
    charges = paginator.get_page(1)
    context = {
        "charges": charges,
        "charge_types": Charge.ChargeTypeEnum.choices,
        "charge_statuses": Charge.ChargeStatusEnum.choices,
        "issuers": Staff.objects.order_by("username").all(),
        "order_options": {
            "id": "ID",
            "visit__patient__first_name": "Patient First Name",
            "visit__patient__last_name": "Patient Last Name",
            "amount": "Amount",
            "issuer__username": "Issuer Username",
            "date": "Date",
        },
    }
    if request.headers.get("HX-Request"):
        return render(
            request, "staff/admin/charges/partials/charges-partial.html", context
        )
    else:
        return render(request, "staff/admin/charges/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_charges_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 50

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("charge_q")
    type = request.GET.get("charge_type")
    status = request.GET.get("charge_status")
    issuer_id = request.GET.get("charge_issuer")
    order_by = request.GET.get("charge_order")
    show_only_today = request.GET.get("show_only_today")
    hide_deactivated = request.GET.get("hide_deactivated")

    qs = Charge.objects

    if hide_deactivated:
        qs = qs.exclude(is_active=False)

    if show_only_today:
        today = timezone.now().date()
        qs = qs.filter(date__date=today)

    if q:
        qs = qs.filter(
            Q(id__icontains=q)
            | Q(visit__id__icontains=q)
            | Q(visit__patient__id__icontains=q)
            | Q(visit__patient__first_name__icontains=q)
            | Q(visit__patient__last_name__icontains=q)
            | Q(visit__patient__phone__icontains=q)
            | Q(amount__icontains=q)
        )

    if type:
        qs = qs.filter(charge_type=type)

    if status:
        qs = qs.filter(charge_status=status)

    if issuer_id:
        qs = qs.filter(issuer__id=issuer_id)

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("id")

    paginator = Paginator(qs, per_page)

    try:
        charges = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        charges = paginator.page(1)
    except EmptyPage:
        charges = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"charges": charges}
    return render(
        request, "staff/admin/charges/partials/charges-table-partial.html", context
    )


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_payments(request: HttpRequest):
    qs = Payment.objects.order_by("id").all()
    paginator = Paginator(qs, per_page=50)
    payments = paginator.get_page(1)
    context = {
        "payments": payments,
        "payment_methods": Payment.PaymentMethodEnum.choices,
        "payment_statuses": Payment.PaymentStatusEnum.choices,
        "acceptors": Staff.objects.order_by("username").all(),
        "order_options": {
            "id": "ID",
            "charge__visit__patient__first_name": "Patient First Name",
            "charge__visit__patient__last_name": "Patient Last Name",
            "amount": "Amount",
            "acceptor": "Acceptor Username",
            "date": "Date",
        },
    }

    if request.headers.get("HX-Request"):
        return render(
            request, "staff/admin/payments/partials/payments-partial.html", context
        )
    else:
        return render(request, "staff/admin/payments/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_payments_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 50

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("payment_q")
    method = request.GET.get("payment_method")
    status = request.GET.get("payment_status")
    acceptor_id = request.GET.get("payment_acceptor")
    order_by = request.GET.get("payment_order")
    show_only_today = request.GET.get("show_only_today")
    hide_deactivated = request.GET.get("hide_deactivated")

    qs = Payment.objects

    if hide_deactivated:
        qs = qs.exclude(is_active=False)

    if show_only_today:
        today = timezone.now().date()
        qs = qs.filter(date__date=today)

    if q:
        qs = qs.filter(
            Q(id__icontains=q)
            | Q(charge__id__icontains=q)
            | Q(charge__visit__id__icontains=q)
            | Q(charge__visit__patient__id__icontains=q)
            | Q(charge__visit__patient__first_name__icontains=q)
            | Q(charge__visit__patient__last_name__icontains=q)
            | Q(charge__visit__patient__phone__icontains=q)
        )

    if method:
        qs = qs.filter(payment_method=method)

    if status:
        qs = qs.filter(payment_status=status)

    if acceptor_id:
        qs = qs.filter(acceptor__id=acceptor_id)

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("id")

    paginator = Paginator(qs, per_page)

    try:
        payments = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        payments = paginator.page(1)
    except EmptyPage:
        payments = paginator.page(paginator.num_pages if paginator.num_pages else 1)

    context = {"payments": payments}
    return render(
        request, "staff/admin/payments/partials/payments-table-partial.html", context
    )


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_financial_summary(request: HttpRequest):
    data = get_today_data()
    context = {
        "data": data["visit_data"],  # raw for template access
        "data_json": json.dumps(
            data["visit_data"], cls=DjangoJSONEncoder
        ),  # json for JS
        "history": data["history"],
        "history_json": json.dumps(data["history"], cls=DjangoJSONEncoder),
        "charges_breakdown": data["charges_breakdown"],
        "charges_breakdown_json": json.dumps(
            data["charges_breakdown"], cls=DjangoJSONEncoder
        ),
        "payments_method_breakdown": data["payments_method_breakdown"],
        "payments_method_breakdown_json": json.dumps(
            data["payments_method_breakdown"], cls=DjangoJSONEncoder
        ),
        "payments_status_breakdown": data["payments_status_breakdown"],
        "payments_status_breakdown_json": json.dumps(
            data["payments_status_breakdown"], cls=DjangoJSONEncoder
        ),
        "most_ordered_tests": data["most_ordered_tests"],
        "most_ordered_tests_json": json.dumps(
            data["most_ordered_tests"], cls=DjangoJSONEncoder
        ),
    }

    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/admin/financial-summary/partials/financial-summary-partial.html",
            context,
        )
    else:
        return render(request, "staff/admin/financial-summary/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_financial_summary_timespan(request: HttpRequest):
    timespan = request.GET.get("timespans") or "day"
    data_func = {
        "day": get_today_data,
        "week": get_week_data,
        "month": get_month_data,
        "year": get_year_data,
        "all": get_all_data,
    }.get(timespan)

    if not data_func:
        return HttpResponseBadRequest("Unknown timespan value.")
    data = data_func()

    context = {
        "data": data["visit_data"],
        "data_json": json.dumps(data["visit_data"], cls=DjangoJSONEncoder),
        "history": data["history"],
        "history_json": json.dumps(data["history"], cls=DjangoJSONEncoder),
        "charges_breakdown": data["charges_breakdown"],
        "charges_breakdown_json": json.dumps(
            data["charges_breakdown"], cls=DjangoJSONEncoder
        ),
        "payments_method_breakdown": data["payments_method_breakdown"],
        "payments_method_breakdown_json": json.dumps(
            data["payments_method_breakdown"], cls=DjangoJSONEncoder
        ),
        "payments_status_breakdown": data["payments_status_breakdown"],
        "payments_status_breakdown_json": json.dumps(
            data["payments_status_breakdown"], cls=DjangoJSONEncoder
        ),
        "most_ordered_tests": data["most_ordered_tests"],
        "most_ordered_tests_json": json.dumps(
            data["most_ordered_tests"], cls=DjangoJSONEncoder
        ),
    }

    return render(
        request,
        "staff/admin/financial-summary/partials/financial-summary-content.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_revenue_reports(request: HttpRequest):
    qs = Payment.objects.order_by("id").all()
    paginator = Paginator(qs, per_page=50)
    payments = paginator.get_page(1)
    columns = {
        "id": "ID",
        "patient_name": "Patient Name",
        "patient_phone": "Phone",
        "amount": "Amount",
        "payment_method": "Method",
        "payment_date": "Date",
    }
    payments_filtered = []
    for payment in payments:
        id = payment.id
        patient_name = payment.charge.visit.patient.fullname
        patient_phone = payment.charge.visit.patient.phone or "Not registered"
        amount = payment.amount
        method = payment.payment_method.label
        date = (
            payment.date.date().strftime("%a %b %d, %Y")
            if payment.date
            else "Not recorded"
        )
        payments_filtered.append(
            [id, patient_name, patient_phone, amount, method, date]
        )
    context = {
        "columns": columns,
        "payments": payments,
        "payments_filtered": payments_filtered,
        "revenue_reports_methods": Payment.PaymentMethodEnum.choices,
        "revenue_reports_statuses": Payment.PaymentStatusEnum.choices,
        "acceptors": Staff.objects.order_by("username").all(),
        "order_options": {
            "id": "ID",
            "charge__visit__patient__first_name": "Patient First Name",
            "charge__visit__patient__last_name": "Patient Last Name",
            "amount": "Amount",
            "acceptor": "Acceptor Username",
            "date": "Date",
        },
        "column_options": {
            "id": "ID",
            "patient_id": "Patient ID",
            "patient_name": "Patient Name",
            "patient_phone": "Patient Phone",
            "visit_id": "Visit ID",
            "charge_id": "Charge ID",
            "charge_amount": "Charge Amount",
            "charge_reason": "Charge Reason",
            "charge_issuer": "Charge Issuer",
            "amount": "Amount",
            "payment_method": "Payment Method",
            "payment_status": "Payment Status",
            "payment_date": "Payment Date",
        },
    }
    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/admin/revenue-reports/partials/revenue-reports-partial.html",
            context,
        )
    else:
        return render(request, "staff/admin/revenue-reports/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_revenue_reports_filter(request: HttpRequest):
    column_options = {
        "id": "ID",
        "patient_id": "Patient ID",
        "patient_name": "Patient Name",
        "patient_phone": "Patient Phone",
        "visit_id": "Visit ID",
        "charge_id": "Charge ID",
        "charge_amount": "Charge Amount",
        "charge_reason": "Charge Reason",
        "charge_issuer": "Charge Issuer",
        "amount": "Amount",
        "payment_method": "Payment Method",
        "payment_status": "Payment Status",
        "payment_date": "Payment Date",
    }

    page = request.GET.get("page", 1)
    per_page = 50

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("revenue_reports_q")
    start_date = request.GET.get("revenue_reports_start_date")
    end_date = request.GET.get("revenue_reports_end_date")
    method = request.GET.get("revenue_reports_method")
    status = request.GET.get("revenue_reports_status")
    acceptor_id = request.GET.get("revenue_reports_acceptor")
    order_by = request.GET.get("revenue_reports_order")
    selected_columns = request.GET.getlist(
        "revenue_reports_columns",
        [
            "id",
            "patient_name",
            "patient_phone",
            "amount",
            "payment_method",
            "payment_date",
        ],
    )
    hide_deactivated = request.GET.get("hide_deactivated")

    qs = Payment.objects

    if hide_deactivated:
        qs = qs.exclude(is_active=False)

    if start_date:
        qs = qs.filter(date__date__gte=start_date)
    if end_date:
        qs = qs.filter(date__date__lte=end_date)

    if acceptor_id:
        qs = qs.filter(acceptor__id=acceptor_id)

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("id")

    if q:
        qs = qs.filter(
            Q(id__icontains=q)
            | Q(charge__id__icontains=q)
            | Q(charge__visit__id__icontains=q)
            | Q(charge__visit__patient__id__icontains=q)
            | Q(charge__visit__patient__first_name__icontains=q)
            | Q(charge__visit__patient__last_name__icontains=q)
            | Q(charge__visit__patient__phone__icontains=q)
        )

    if method:
        qs = qs.filter(payment_method=method)
    if status:
        qs = qs.filter(payment_status=status)

    paginator = Paginator(qs.all(), per_page)

    try:
        payments = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        payments = paginator.page(1)
    except EmptyPage:
        payments = paginator.page(paginator.num_pages if paginator.num_pages else 1)

    payments_filtered = []
    for payment in payments:
        payment_item = []

        if "id" in selected_columns:
            payment_item.append(payment.id)
        if "patient_id" in selected_columns:
            payment_item.append(payment.charge.visit.patient.id)
        if "patient_name" in selected_columns:
            payment_item.append(payment.charge.visit.patient.fullname)
        if "patient_phone" in selected_columns:
            payment_item.append(payment.charge.visit.patient.phone or "Not registered")
        if "visit_id" in selected_columns:
            payment_item.append(payment.charge.visit.id)
        if "charge_id" in selected_columns:
            payment_item.append(payment.charge.id)
        if "charge_amount" in selected_columns:
            payment_item.append(round(payment.charge.amount or 0, 2))
        if "charge_reason" in selected_columns:
            payment_item.append(payment.charge.charge_type.label)
        if "charge_issuer" in selected_columns:
            payment_item.append(payment.charge.issuer.username)
        if "amount" in selected_columns:
            payment_item.append(round(payment.amount or 0, 2))
        if "payment_method" in selected_columns:
            payment_item.append(payment.payment_method.label)
        if "payment_status" in selected_columns:
            payment_item.append(payment.payment_status.label)
        if "payment_date" in selected_columns:
            payment_item.append(
                payment.date.date().strftime("%a %b %d, %Y")
                if payment.date
                else "Not recorded"
            )

        payments_filtered.append(payment_item)

    columns = {}
    for key, val in column_options.items():
        if key in selected_columns:
            columns[key] = val
    context = {
        "columns": columns,
        "payments": payments,
        "payments_filtered": payments_filtered,
    }
    return render(
        request,
        "staff/admin/revenue-reports/partials/revenue-reports-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_revenue_reports_export(request: HttpRequest):
    column_options = {
        "id": "ID",
        "patient_id": "Patient ID",
        "patient_name": "Patient Name",
        "patient_phone": "Patient Phone",
        "visit_id": "Visit ID",
        "charge_id": "Charge ID",
        "charge_amount": "Charge Amount",
        "charge_reason": "Charge Reason",
        "charge_issuer": "Charge Issuer",
        "amount": "Amount",
        "payment_method": "Payment Method",
        "payment_status": "Payment Status",
        "payment_date": "Payment Date",
    }
    q = request.GET.get("revenue_reports_q")
    start_date = request.GET.get("revenue_reports_start_date")
    end_date = request.GET.get("revenue_reports_end_date")
    method = request.GET.get("revenue_reports_method")
    status = request.GET.get("revenue_reports_status")
    acceptor_id = request.GET.get("revenue_reports_acceptor")
    order_by = request.GET.get("revenue_reports_order")
    selected_columns = request.GET.getlist(
        "revenue_reports_columns",
        [
            "id",
            "patient_name",
            "patient_phone",
            "amount",
            "payment_method",
            "payment_date",
        ],
    )
    hide_deactivated = request.GET.get("hide_deactivated")

    qs = Payment.objects

    if hide_deactivated:
        qs = qs.exclude(is_active=False)

    if start_date:
        qs = qs.filter(date__date__gte=start_date)
    if end_date:
        qs = qs.filter(date__date__lte=end_date)

    if acceptor_id:
        qs = qs.filter(acceptor__id=acceptor_id)

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("id")

    if q:
        qs = qs.filter(
            Q(id__icontains=q)
            | Q(charge__id__icontains=q)
            | Q(charge__visit__id__icontains=q)
            | Q(charge__visit__patient__id__icontains=q)
            | Q(charge__visit__patient__first_name__icontains=q)
            | Q(charge__visit__patient__last_name__icontains=q)
            | Q(charge__visit__patient__phone__icontains=q)
        )

    if method:
        qs = qs.filter(payment_method=method)
    if status:
        qs = qs.filter(payment_status=status)

    payments_filtered = []
    for payment in qs.all():
        payment_item = []

        if "id" in selected_columns:
            payment_item.append(payment.id)
        if "patient_id" in selected_columns:
            payment_item.append(payment.charge.visit.patient.id)
        if "patient_name" in selected_columns:
            payment_item.append(payment.charge.visit.patient.fullname)
        if "patient_phone" in selected_columns:
            payment_item.append(payment.charge.visit.patient.phone or "Not registered")
        if "visit_id" in selected_columns:
            payment_item.append(payment.charge.visit.id)
        if "charge_id" in selected_columns:
            payment_item.append(payment.charge.id)
        if "charge_amount" in selected_columns:
            payment_item.append(round(payment.charge.amount or 0, 2))
        if "charge_reason" in selected_columns:
            payment_item.append(payment.charge.charge_type.label)
        if "charge_issuer" in selected_columns:
            payment_item.append(payment.charge.issuer.username)
        if "amount" in selected_columns:
            payment_item.append(round(payment.amount or 0, 2))
        if "payment_method" in selected_columns:
            payment_item.append(payment.payment_method.label)
        if "payment_status" in selected_columns:
            payment_item.append(payment.payment_status.label)
        if "payment_date" in selected_columns:
            payment_item.append(
                payment.date.date().strftime("%a %b %d, %Y")
                if payment.date
                else "Not recorded"
            )

        payments_filtered.append(payment_item)

    columns = {}
    for key, val in column_options.items():
        if key in selected_columns:
            columns[key] = val

    df = pd.DataFrame(data=payments_filtered, columns=columns.values())
    fmt = request.GET.get("fmt")
    if fmt == "pdf":
        response = FileResponse(
            dataframe_to_pdf(df),
            as_attachment=True,
            filename=f"revenue-report-{timezone.now().date().strftime("%d-%m-%y")}.pdf",
            content_type="application/pdf",
        )
    else:
        response = FileResponse(
            dataframe_to_excel(df),
            as_attachment=True,
            filename=f"revenue-report-{timezone.now().date().strftime("%d-%m-%y")}.xlsx",
        )
    response["HX-Redirect"] = request.get_full_path()
    return response


admin_financial_urlpatterns = [
    path("admin/charges/", admin_charges, name="admin_charges"),
    path("admin/charges/filter", admin_charges_filter, name="admin_charges_filter"),
    path("admin/payments/", admin_payments, name="admin_payments"),
    path(
        "admin/payments/filter",
        admin_payments_filter,
        name="admin_payments_filter",
    ),
    path(
        "admin/financial_summary/",
        admin_financial_summary,
        name="admin_financial_summary",
    ),
    path(
        "admin/financial_summary/timespan",
        admin_financial_summary_timespan,
        name="admin_financial_summary_timespan",
    ),
    path(
        "admin/revenue_reports/",
        admin_revenue_reports,
        name="admin_revenue_reports",
    ),
    path(
        "admin/revenue_reports/filter/",
        admin_revenue_reports_filter,
        name="admin_revenue_reports_filter",
    ),
    path(
        "admin/revenue_reports/export/",
        admin_revenue_reports_export,
        name="admin_revenue_reports_export",
    ),
]
