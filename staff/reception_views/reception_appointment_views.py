import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.urls import path, re_path, reverse
from django.utils import timezone

from appointments.models import Appointment
from staff.models import Staff
from staff.utils import user_has_role, clean_urlencode


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_appointments(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 20

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    queue_mode = request.GET.get("queue")
    if queue_mode:
        request.GET = request.GET.copy()
        request.GET["sort"] = "date"
        request.GET["status"] = Appointment.AppointmentStatus.SCHEDULED
        request.GET["date"] = "today"

    q = request.GET.get("q")
    order_by = request.GET.get("sort")
    status = request.GET.get("status")
    date = request.GET.get("date")
    practitioner = request.GET.get("pr")
    show_archived = request.GET.get("show_archived")
    today = timezone.now().date()

    qs = Appointment.objects

    if not show_archived:
        qs = qs.filter(is_operational_annotated=True)

    if status:
        qs = qs.filter(appointment_status=status)

    if date:
        if date == "past":
            qs = qs.filter(appointment_date__date__lt=today)
        elif date == "today":
            qs = qs.filter(appointment_date__date=today)
        elif date == "future":
            qs = qs.filter(appointment_date__date__gt=today)

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q
        qs = (
            qs.annotate(
                full_name=Concat(
                    "patient__first_name",
                    Value(" "),
                    "patient__last_name",
                )
            )
            .filter(
                Q(id__icontains=id_q)
                | Q(patient__id__icontains=id_q)
                | Q(visit__id__icontains=id_q)
                | Q(doctor__id__icontains=id_q)
                | Q(full_name__icontains=q)
                | Q(doctor__username__icontains=q)
                | Q(patient__phone__icontains=q)
            )
            .distinct()
        )

    if practitioner:
        qs = qs.filter(doctor__id=practitioner)

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)
    try:
        appointments = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        appointments = paginator.get_page(1)
    except EmptyPage:
        appointments = paginator.get_page(
            paginator.num_pages if paginator.num_pages else 1
        )

    context = {
        "appointments": appointments,
        "appointment_statuses": Appointment.AppointmentStatus.choices,
        "practitioners": Staff.objects.filter(role=Staff.RoleEnum.DOCTOR).all(),
        "date_options": {
            "today": "Today's appointments",
            "past": "Past appointments",
            "future": "Future appointments",
        },
        "order_options": {
            "id": "ID",
            "patient__first_name": "Patient First Name",
            "patient__last_name": "Patient Last Name",
            "appointment_date": "Appointment Date",
        },
    }

    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/reception/appointments/partials/appointments-partial.html",
            context,
        )
    return render(request, "staff/reception/appointments/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_appointments_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 20

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    queue_mode = request.GET.get("queue")
    if queue_mode:
        request.GET = request.GET.copy()
        request.GET["sort"] = "appointment_date"
        request.GET.setlist("status", [Appointment.AppointmentStatus.SCHEDULED])
        request.GET.setlist("date", ["today"])

    q = request.GET.get("q")
    order_by = request.GET.get("sort")
    status = request.GET.get("status")
    date = request.GET.get("date")
    practitioner = request.GET.get("pr")
    show_archived = request.GET.get("show_archived")
    today = timezone.now().date()

    qs = Appointment.objects

    if not show_archived:
        qs = qs.filter(is_operational_annotated=True)

    if status:
        qs = qs.filter(appointment_status=status)

    if date:
        if date == "past":
            qs = qs.filter(appointment_date__date__lt=today)
        elif date == "today":
            qs = qs.filter(appointment_date__date=today)
        elif date == "future":
            qs = qs.filter(appointment_date__date__gt=today)

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q
        qs = (
            qs.annotate(
                full_name=Concat(
                    "patient__first_name",
                    Value(" "),
                    "patient__last_name",
                )
            )
            .filter(
                Q(id__icontains=id_q)
                | Q(patient__id__icontains=id_q)
                | Q(visit__id__icontains=id_q)
                | Q(doctor__id__icontains=id_q)
                | Q(full_name__icontains=q)
                | Q(doctor__username__icontains=q)
                | Q(patient__phone__icontains=q)
            )
            .distinct()
        )
    
    if practitioner:
        qs = qs.filter(doctor__id=practitioner)

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)
    try:
        appointments = paginator.get_page(page_number)
    except (PageNotAnInteger, ValueError):
        appointments = paginator.get_page(1)
    except EmptyPage:
        appointments = paginator.get_page(
            paginator.num_pages if paginator.num_pages else 1
        )

    context = {
        "appointments": appointments,
    }

    response = render(
        request,
        "staff/reception/appointments/partials/appointments-table-partial.html",
        context,
    )
    response["HX-Push-Url"] = (
        f"{reverse("staff:reception_appointments")}{clean_urlencode(request.GET)}"
    )

    trigger = {}
    if len(request.GET.getlist("status")) == 0:
        trigger["trigger-status-select"] = {"value": "SCHEDULED"}

    if len(request.GET.getlist("date")) == 0:
        trigger["trigger-date-select"] = {"value": "today"}
    response["HX-Trigger-After-Settle"] = json.dumps(trigger)
    return response


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_appointments_table_row(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    return render(
        request,
        "staff/reception/appointments/partials/appointments-table-row-partial.html",
        {"appointment": appointment},
    )


@login_required
@user_has_role(Staff.RoleEnum.RECEPTION)
def reception_appointment_details(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    
    context = {"appointment": appointment}
    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/reception/appointments/partials/appointment-details-partial.html",
            context,
        )

    return render(request, "staff/reception/appointments/details/page.html", context)


reception_appointments_urlpatterns = [
    path(
        "reception/appointments", reception_appointments, name="reception_appointments"
    ),
    path(
        "reception/appointments/filter",
        reception_appointments_filter,
        name="reception_appointments_filter",
    ),
    re_path(
        r"^reception/appointments/table-row/(?P<id>[0-9]+|__ID__)/$",
        reception_appointments_table_row,
        name="reception_appointments_table_row",
    ),
    re_path(
        r"^reception/appointments/(?P<id>[0-9]+|__ID__)/$",
        reception_appointment_details,
        name="reception_appointment_details",
    ),
]
