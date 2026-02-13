from django.shortcuts import redirect, render
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from charges.models import Charge
from staff.models import Staff
from staff.utils import user_has_role
from staff.utils import get_today_data, get_week_data, get_month_data, get_year_data, get_all_data
from visits.models import Visit
from lab_requests.models import LabTestRequest

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
def admin(request: HttpRequest):
    data = get_today_data()
    data["most_ordered_tests"] = [
        {
            "test__name": "Glucose (Fasting)",
            "order_count": 125
        },
        {
            "test__name": "Glucose (Random)",
            "order_count": 120
        },
        {
            "test__name": "Blood Pressure",
            "order_count": 108
        },
        {
            "test__name": "Cholesterol",
            "order_count": 101
        },
        {
            "test__name": "Vitamin D",
            "order_count": 15
        },
    ]
    return render(request, "staff/admin/admin.html", {
        "data": data["visit_data"],
        "history": data["historic_data"],
        "charges_breakdown": data["charges_breakdown"],
        "most_ordered_tests": data["most_ordered_tests"]
    })

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_dashboard_section(request: HttpRequest):
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
    data["most_ordered_tests"] = [
        {
            "test__name": "Glucose (Fasting)",
            "order_count": 125
        },
        {
            "test__name": "Glucose (Random)",
            "order_count": 120
        },
        {
            "test__name": "Blood Pressure",
            "order_count": 108
        },
        {
            "test__name": "Cholesterol",
            "order_count": 101
        },
        {
            "test__name": "Vitamin D",
            "order_count": 15
        },
    ]
    return render(
        request,
        "staff/admin/partials/dashboard.html",
        {
            "data": data["visit_data"],
            "history": data["historic_data"],
            "charges_breakdown": data["charges_breakdown"],
            "most_ordered_tests": data["most_ordered_tests"]
        }
    )

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_dashboard(request: HttpRequest):
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
    data["most_ordered_tests"] = [
        {
            "test__name": "Glucose (Fasting)",
            "order_count": 125
        },
        {
            "test__name": "Glucose (Random)",
            "order_count": 120
        },
        {
            "test__name": "Blood Pressure",
            "order_count": 108
        },
        {
            "test__name": "Cholesterol",
            "order_count": 101
        },
        {
            "test__name": "Vitamin D",
            "order_count": 15
        },
    ]
    return render(
        request,
        "staff/admin/partials/admin_dashboard.html",
        {
            "data": data["visit_data"],
            "history": data["historic_data"],
            "charges_breakdown": data["charges_breakdown"],
            "most_ordered_tests": data["most_ordered_tests"]
        }
    )

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_activity(request: HttpRequest):
    return render(
        request,
        "staff/admin/partials/activity.html",
    )