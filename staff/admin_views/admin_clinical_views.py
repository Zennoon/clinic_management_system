from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.db.models import F, Q, Sum
from django.urls import path
from django.utils import timezone

from staff.utils import user_has_role
from appointments.models import Appointment
from patients.models import Patient
from staff.models import Staff
from visits.models import Visit

@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_patients(request: HttpRequest):
    qs = Patient.objects.order_by("id").all()
    paginator = Paginator(qs, per_page=50)
    patients = paginator.get_page(1)
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
            "created_at": "Registration date",
        },
    }

    if request.headers.get("HX-Request"):
        return render(
            request, "staff/admin/patients/partials/patients-partial.html", context
        )
    else:
        return render(request, "staff/admin/patients/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_patients_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 50

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("patient_q")
    sex = request.GET.get("patient_sex")
    region = request.GET.get("patient_region")
    order_by = request.GET.get("patient_order")
    hide_deactivated = request.GET.get("hide_deactivated")

    if order_by and order_by.endswith("date_of_birth"):
        if order_by.startswith("-"):
            order_by = order_by[1:]
        elif order_by.startswith("date_of_birth"):
            order_by = "-" + order_by

    qs = Patient.objects

    if hide_deactivated:
        qs = qs.exclude(is_active=False)

    if q:
        qs = qs.filter(
            Q(id__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(city__icontains=q)
            | Q(visits__id__icontains=q)
        ).distinct()
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
    return render(
        request, "staff/admin/patients/partials/patients-table-partial.html", context
    )


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_visits(request: HttpRequest):
    qs = Visit.objects.order_by("id").all()
    paginator = Paginator(qs, per_page=50)
    visits = paginator.get_page(1)
    context = {
        "visits": visits,
        "visit_categories": Visit.VisitCategoryEnum.choices,
        "visit_statuses": Visit.VisitStatusEnum.choices,
        "order_options": {
            "id": "ID",
            "patient__first_name": "Patient First Name",
            "patient__last_name": "Patient Last Name",
            "total_charges": "Total Charges",
            "total_payments": "Total Payments",
            "total_balance": "Balance",
            "date": "Date",
        },
    }
    if request.headers.get("HX-Request"):
        return render(
            request, "staff/admin/visits/partials/visits-partial.html", context
        )
    else:
        return render(request, "staff/admin/visits/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_visits_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 50

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("visit_q")
    category = request.GET.get("visit_category")
    status = request.GET.get("visit_status")
    order_by = request.GET.get("visit_order")
    show_only_today = request.GET.get("show_only_today")
    hide_deactivated = request.GET.get("hide_deactivated")

    qs = Visit.objects

    if hide_deactivated:
        qs = qs.exclude(is_active=False)

    if show_only_today:
        today = timezone.now().date()
        qs = qs.filter(date__date=today)

    if q:
        qs = qs.filter(
            Q(id__icontains=q)
            | Q(patient__id__icontains=q)
            | Q(patient__first_name__icontains=q)
            | Q(patient__last_name__icontains=q)
            | Q(patient__phone__icontains=q)
            | Q(chief_complaint__icontains=q)
            | Q(history__icontains=q)
        ).distinct()
    if category:
        qs = qs.filter(visit_category=category)
    if status:
        qs = qs.filter(visit_status=status)
    if order_by:
        if "total" in order_by or "balance" in order_by:
            qs = qs.annotate(
                total_charges=Sum("charges__amount", distinct=True),
                total_payments=Sum("charges__payments__amount"),
            ).annotate(total_balance=F("total_charges") - F("total_payments"))
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("id")

    paginator = Paginator(qs, per_page)
    try:
        visits = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        visits = paginator.page(1)
    except EmptyPage:
        visits = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"visits": visits}
    return render(
        request, "staff/admin/visits/partials/visits-table-partial.html", context
    )


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_appointments(request: HttpRequest):
    qs = Appointment.objects.order_by("id").all()
    paginator = Paginator(qs, per_page=50)
    appointments = paginator.get_page(1)
    context = {
        "appointments": appointments,
        "doctors": Staff.objects.filter(role=Staff.RoleEnum.DOCTOR),
        "order_options": {
            "id": "ID",
            "patient__first_name": "Patient First Name",
            "patient__last_name": "Patient Last Name",
            "appointment_date": "Appointment Date",
            "date": "Set Date",
        },
    }
    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/admin/appointments/partials/appointments-partial.html",
            context,
        )
    else:
        return render(request, "staff/admin/appointments/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.ADMIN)
def admin_appointments_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 50

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("appointment_q")
    doctor_id = request.GET.get("appointment_doctor")
    order_by = request.GET.get("appointment_order")
    show_only_today = request.GET.get("show_only_today")
    hide_deactivated = request.GET.get("hide_deactivated")

    qs = Appointment.objects

    if hide_deactivated:
        qs = qs.exclude(is_active=False)

    if show_only_today:
        today = timezone.now().date()
        qs = qs.filter(appointment_date__date=today)

    if q:
        qs = qs.filter(
            Q(id__icontains=q)
            | Q(patient__id__icontains=q)
            | Q(patient__first_name__icontains=q)
            | Q(patient__last_name__icontains=q)
            | Q(patient__phone__icontains=q)
            | Q(visit__id__icontains=q)
            | Q(reason__icontains=q)
        )

    if doctor_id:
        qs = qs.filter(doctor__id=doctor_id)

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("id")

    paginator = Paginator(qs, per_page)

    try:
        appointments = paginator.page(page_number)
    except (PageNotAnInteger, ValueError):
        appointments = paginator.page(1)
    except EmptyPage:
        appointments = paginator.page(paginator.num_pages if paginator.num_pages else 1)
    context = {"appointments": appointments}
    return render(
        request,
        "staff/admin/appointments/partials/appointments-table-partial.html",
        context,
    )
    
admin_clinical_urlpatterns = [
    path("admin/patients/", admin_patients, name="admin_patients"),
    path(
        "admin/patients/filter",
        admin_patients_filter,
        name="admin_patients_filter",
    ),
    path("admin/visits/", admin_visits, name="admin_visits"),
    path("admin/visits/filter/", admin_visits_filter, name="admin_visits_filter"),
    path("admin/appointments/", admin_appointments, name="admin_appointments"),
    path(
        "admin/appointments/filter",
        admin_appointments_filter,
        name="admin_appointments_filter",
    ),
]