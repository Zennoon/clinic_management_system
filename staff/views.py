import json
from django.core.serializers.json import DjangoJSONEncoder

from django.shortcuts import redirect, render
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.utils import timezone

from charges.models import Charge
from lab_requests.models import LabRequest, LabTestRequest
from patients.models import Patient
from payments.models import Payment
from staff.models import Staff
from staff.utils import user_has_role
from staff.utils import get_today_data, get_week_data, get_month_data, get_year_data, get_all_data
from visits.models import Visit

from .forms import LoginForm

# Create your views here.
@require_http_methods(["GET"])
@user_passes_test(lambda user: not user.is_authenticated, login_url='/', redirect_field_name='')
def login_view(request: HttpRequest):
    form = LoginForm()
    return render(request, "staff/login.html", { "form": form })

@require_http_methods(["POST"])
def attempt_login(request: HttpRequest):
    form = LoginForm(request.POST)
    if form.is_valid():
        user = authenticate(request, username=form.cleaned_data.get("username"), password=form.cleaned_data.get("password"))
        if user:
            login(request, user)
            response = HttpResponse()
            response["HX-Location"] = reverse("index")
            return response
        else:
            return render(request, "partials/login-form.html", { "form": form, "error": "Incorrect login credentials" })
    else:
        return render(request, "partials/login-form.html", { form: "form" })

@login_required
def attempt_logout(request: HttpRequest):
    logout(request)
    return redirect(reverse('staff:login'))

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin(_: HttpRequest):
    return redirect(reverse("staff:admin_dashboard"))

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_dashboard(request: HttpRequest):  
    data = get_today_data()
    context = {
        "data": data["visit_data"],                                   # raw for template access
        "data_json": json.dumps(data["visit_data"], cls=DjangoJSONEncoder),  # json for JS
        "history": data["history"],
        "history_json": json.dumps(data["history"], cls=DjangoJSONEncoder),
        "charges_breakdown": data["charges_breakdown"],
        "charges_breakdown_json": json.dumps(data["charges_breakdown"], cls=DjangoJSONEncoder),
        "most_ordered_tests": data["most_ordered_tests"],
        "most_ordered_tests_json": json.dumps(data["most_ordered_tests"], cls=DjangoJSONEncoder),
    }

    if request.headers.get("HX-Request"):
        return render(
            request, 
            "staff/admin/dashboard/partials/dashboard-partial.html",
            context
        )
    else:
        return render(
            request,
            "staff/admin/dashboard/page.html",
            context
        )

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_dashboard_timespan(request: HttpRequest):
    timespan = request.GET.get("timespans") or "day"
    data_func = {
        "day": get_today_data,
        "week": get_week_data,
        "month": get_month_data,
        "year": get_year_data,
        "all": get_all_data
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
        "charges_breakdown_json": json.dumps(data["charges_breakdown"], cls=DjangoJSONEncoder),
        "most_ordered_tests": data["most_ordered_tests"],
        "most_ordered_tests_json": json.dumps(data["most_ordered_tests"], cls=DjangoJSONEncoder),
    }
    
    return render(
        request, 
        "staff/admin/dashboard/partials/dashboard-content.html",
        context
    )

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_activity(request: HttpRequest):
    visit_qs = Visit.objects.order_by("-created_at")
    visit_paginator = Paginator(visit_qs, 10)
    recent_visits = visit_paginator.get_page(1)
    
    patient_qs = Patient.objects.order_by("-created_at")
    patient_paginator = Paginator(patient_qs, 10)
    recent_patients = patient_paginator.get_page(1)
    
    lab_qs = LabRequest.objects.order_by("-created_at")
    lab_request_paginator = Paginator(lab_qs, 10)
    recent_lab_requests = lab_request_paginator.get_page(1)
    
    charge_qs = Charge.objects.order_by("-created_at")
    charge_paginator = Paginator(charge_qs, 10)
    recent_charges = charge_paginator.get_page(1)
    
    payment_qs = Payment.objects.order_by("-created_at")
    payment_paginator = Paginator(payment_qs, 10)
    recent_payments = payment_paginator.get_page(1)


    if request.headers.get("HX-Request"):
        return render(
             request,
             "staff/admin/activity/partials/activity-partial.html",
            {
                 "recent_visits": recent_visits,
                 "recent_patients": recent_patients,
                 "recent_lab_requests": recent_lab_requests,
                 "recent_charges": recent_charges,
                 "recent_payments": recent_payments,
                 "visit_statuses": Visit.VisitStatusEnum.choices,
                 "regions": Patient.RegionEnum.choices,
                 "charge_statuses": Charge.ChargeStatusEnum.choices,
                 "charge_types": Charge.ChargeTypeEnum.choices,
                 "payment_methods": Payment.PaymentMethodEnum.choices,
                 "payment_statuses": Payment.PaymentStatusEnum.choices,
            }
        )
    else:
        return render(
            request,
            "staff/admin/activity/page.html",
            {
                 "recent_visits": recent_visits,
                 "recent_patients": recent_patients,
                 "recent_lab_requests": recent_lab_requests,
                 "recent_charges": recent_charges,
                 "recent_payments": recent_payments,
                 "visit_statuses": Visit.VisitStatusEnum.choices,
                 "regions": Patient.RegionEnum.choices,
                 "charge_statuses": Charge.ChargeStatusEnum.choices,
                 "charge_types": Charge.ChargeTypeEnum.choices,
                 "payment_methods": Payment.PaymentMethodEnum.choices,
                 "payment_statuses": Payment.PaymentStatusEnum.choices,
            }
        )

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_activity_recent_visits(request: HttpRequest):
    per_page = 10
    page = request.GET.get("page", "1")
    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get('visit_q', '').strip()
    status = request.GET.get('visit_status', '').strip()

    qs = Visit.objects.order_by("-created_at")

    if q:
        qs = qs.filter(
            Q(id__icontains=q) |
            Q(patient__first_name__icontains=q) |
            Q(patient__last_name__icontains=q)
        )
    if status:
        qs = qs.filter(visit_status=status)

    paginator = Paginator(qs, per_page, allow_empty_first_page=True)

    try:
        recent_visits = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        recent_visits = paginator.page(1)
    except EmptyPage:
        recent_visits = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"recent_visits": recent_visits}
    return render(request, "staff/admin/activity/partials/recent-visits-table-partial.html", context)

def admin_activity_recent_patients(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 10
    
    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1
    
    q = request.GET.get("patient_q")
    sex = request.GET.get("patient_sex")
    region = request.GET.get("patient_region")
    
    qs = Patient.objects.order_by("-created_at")
    
    if q:
        qs = qs.filter(
            Q(id__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(phone__icontains=q) |
            Q(visits__id__icontains=q)
        ).distinct()
    if sex:
        qs = qs.filter(sex=sex)
    if region:
        qs = qs.filter(region=region)
    
    paginator = Paginator(qs, per_page, allow_empty_first_page=True)
    try:
        recent_patients = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        recent_patients = paginator.page(1)
    except EmptyPage:
        recent_patients = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"recent_patients": recent_patients}
    return render(request, "staff/admin/activity/partials/recent-patients-table-partial.html", context)

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_activity_recent_lab_requests(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 10
    
    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1
    
    q = request.GET.get("lab_q")
    
    qs = LabRequest.objects.order_by("-created_at")

    if q:
        qs = qs.filter(
            Q(id__icontains=q) |
            Q(tests__id__icontains=q) |
            Q(visit__patient__first_name__icontains=q) |
            Q(visit__patient__last_name__icontains=q) |
            Q(ordered_by__username__icontains=q)
        ).distinct()
    paginator = Paginator(qs, per_page, allow_empty_first_page=True)
    try:
        recent_lab_requests = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        recent_lab_requests = paginator.page(1)
    except EmptyPage:
        recent_lab_requests = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"recent_lab_requests": recent_lab_requests}
    return render(request, "staff/admin/activity/partials/recent-lab-requests-table-partial.html", context)

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_activity_recent_charges(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 10
    
    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1
    
    q = request.GET.get("charge_q")
    status = request.GET.get("charge_status")
    type = request.GET.get("charge_type")
    
    qs = Charge.objects.order_by("-created_at")

    if q:
        print(q)
        qs = qs.filter(
            Q(id__icontains=q) |
            Q(visit__id__icontains=q) |
            Q(visit__patient__first_name__icontains=q) |
            Q(visit__patient__last_name__icontains=q) |
            Q(description__icontains=q) |
            Q(charged_by__username__icontains=q)
        ).distinct()
    
    if status:
        qs = qs.filter(charge_status=status)
    if type:
        qs = qs.filter(charge_type=type)

    paginator = Paginator(qs, per_page, allow_empty_first_page=True)
    try:
        recent_charges = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        recent_charges = paginator.page(1)
    except EmptyPage:
        recent_charges = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"recent_charges": recent_charges}
    return render(request, "staff/admin/activity/partials/recent-charges-table-partial.html", context)

def admin_activity_recent_payments(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 10
    
    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1
    
    q = request.GET.get("payment_q")
    method = request.GET.get("payment_method")
    status = request.GET.get("payment_status")
    
    qs = Payment.objects.order_by("-created_at")

    if q:
        qs = qs.filter(
            Q(id__icontains=q) |
            Q(visit__id__icontains=q) |
            Q(visit__patient__first_name__icontains=q) |
            Q(visit__patient__last_name__icontains=q) |
            Q(recorded_by__username=q)
        ).distinct()
    
    if method:
        qs = qs.filter(payment_method=method)
    if status:
        qs = qs.filter(payment_status=status)

    paginator = Paginator(qs, per_page, allow_empty_first_page=True)
    try:
        recent_payments = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        recent_payments = paginator.page(1)
    except EmptyPage:
        recent_payments = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"recent_payments": recent_payments}
    return render(request, "staff/admin/activity/partials/recent-payments-table-partial.html", context)