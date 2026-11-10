from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render
from django.urls import path, re_path
from django.utils import timezone

from staff.models import Staff
from staff.utils import user_has_role
from visits.models import Visit
from vital_signs.models import VitalSign


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_vital_signs(request: HttpRequest):
    today = timezone.now().date()
    hide_queue = request.GET.get("hide_queue")
    hide_history = request.GET.get("hide_history")

    context = {}

    if not hide_queue:
        queue_page = request.GET.get("q_page", 1)
        queue_per_page = 10

        try:
            queue_page_number = int(queue_page)
        except (TypeError, ValueError):
            queue_page_number = 1

        q_q = request.GET.get("q_q")
        q_order_by = request.GET.get("q_sort")
        q_show_archived = request.GET.get("q_archived")
        q_include_past = request.GET.get("q_past")

        if q_order_by and q_order_by.endswith("date_of_birth"):
            if q_order_by.startswith("-"):
                q_order_by = q_order_by[1:]
            elif q_order_by.startswith("date_of_birth"):
                q_order_by = "-" + q_order_by

        queue_qs = Visit.objects.filter(
            visit_status_annotated=Visit.VisitStatusEnum.AWAITING_VITALS
        )

        if not q_show_archived:
            queue_qs = queue_qs.filter(is_operational_annotated=True)
        if not q_include_past:
            queue_qs = queue_qs.filter(date__date=today)
        if q_q:
            try:
                id_q = int(q_q)
            except ValueError:
                id_q = q_q
            queue_qs = (
                queue_qs.annotate(
                    full_name=Concat(
                        "patient__first_name", Value(" "), "patient__last_name"
                    )
                )
                .filter(
                    Q(id__icontains=id_q)
                    | Q(full_name__icontains=q_q)
                    | Q(patient__phone__icontains=q_q)
                    | Q(patient__city__icontains=q_q)
                    | Q(patient__id__icontains=id_q)
                )
                .distinct()
            )

        if q_order_by:
            queue_qs = queue_qs.order_by(q_order_by)
        else:
            queue_qs = queue_qs.order_by("date")
        queue_paginator = Paginator(queue_qs, per_page=queue_per_page)
        vital_signs_queue = queue_paginator.get_page(queue_page_number)
        context["queue"] = True
        context["vital_signs_queue"] = vital_signs_queue
        context["vital_signs_queue_order_options"] = {
            "date": "Date",
            "id": "ID",
            "patient__first_name": "Patient First Name",
            "patient__last_name": "Patient Last Name",
        }

    if not hide_history:
        history_page = request.GET.get("h_page", 1)
        history_per_page = 10

        try:
            history_page_number = int(history_page)
        except (TypeError, ValueError):
            history_page = 1

        h_q = request.GET.get("h_q")
        h_order_by = request.GET.get("h_sort")
        h_show_archived = request.GET.get("h_archived")
        h_include_past = request.GET.get("h_past")

        history_qs = VitalSign.objects

        if not h_show_archived:
            history_qs = history_qs.filter(is_operational_annotated=True)
        if not h_include_past:
            history_qs = history_qs.filter(date__date=today)

        if h_q:
            try:
                id_q = int(h_q)
            except ValueError:
                id_q = h_q
            history_qs = (
                history_qs.annotate(
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
                    | Q(full_name__icontains=h_q)
                    | Q(visit__patient__phone__icontains=h_q)
                    | Q(visit__patient__city__icontains=h_q)
                    | Q(visit__patient__id__icontains=id_q)
                )
                .distinct()
            )

        if h_order_by:
            history_qs = history_qs.order_by(h_order_by)
        else:
            history_qs = history_qs.order_by("-date")

        history_paginator = Paginator(history_qs, per_page=history_per_page)
        vital_sign_history = history_paginator.get_page(history_page_number)
        context["history"] = True
        context["vital_signs_history"] = vital_sign_history
        context["vital_signs_history_order_options"] = {
            "date": "Date",
            "id": "ID",
            "visit__id": "Visit ID",
            "visit__patient__id": "Patient ID",
            "visit__patient__first_name": "Patient First Name",
            "visit__patient__last_name": "Patient Last Name",
        }
    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/nurse/vital_signs/partials/vital-signs-partial.html",
            context,
        )
    return render(request, "staff/nurse/vital_signs/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_vital_signs_queue_filter(request: HttpRequest):
    today = timezone.now().date()
    page = request.GET.get("q_page", 1)
    per_page = 10

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("q_q")
    order_by = request.GET.get("q_sort")
    show_archived = request.GET.get("q_archived")
    include_past = request.GET.get("q_past")

    if order_by and order_by.endswith("date_of_birth"):
        if order_by.startswith("-"):
            order_by = order_by[1:]
        elif order_by.startswith("date_of_birth"):
            order_by = "-" + order_by

    qs = Visit.objects.filter(
        visit_status_annotated=Visit.VisitStatusEnum.AWAITING_VITALS
    )

    if not show_archived:
        qs = qs.filter(is_operational_annotated=True)
    if not include_past:
        qs = qs.filter(date__date=today)
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
                | Q(full_name__icontains=q)
                | Q(patient__phone__icontains=q)
                | Q(patient__city__icontains=q)
                | Q(patient__id__icontains=id_q)
            )
            .distinct()
        )

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("date")

    paginator = Paginator(qs, per_page)
    vital_signs_queue = paginator.get_page(page_number)

    context = {"vital_signs_queue": vital_signs_queue, "queue": True}

    return render(
        request,
        "staff/nurse/vital_signs/partials/vital-signs-queue-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_vital_signs_history_filter(request: HttpRequest):
    today = timezone.now().date()
    page = request.GET.get("h_page", 1)
    per_page = 10

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("h_q")
    order_by = request.GET.get("h_sort")
    show_archived = request.GET.get("h_archived")
    include_past = request.GET.get("h_past")

    if order_by and order_by.endswith("date_of_birth"):
        if order_by.startswith("-"):
            order_by = order_by[1:]
        elif order_by.startswith("date_of_birth"):
            order_by = "-" + order_by

    qs = VitalSign.objects
    if not show_archived:
        qs = qs.filter(is_operational_annotated=True)
    if not include_past:
        qs = qs.filter(date__date=today)
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
                | Q(visit__patient__city__icontains=q)
                | Q(visit__patient__id__icontains=id_q)
            )
            .distinct()
        )

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    paginator = Paginator(qs, per_page)
    vital_signs_history = paginator.get_page(page_number)
    vital_signs_history
    context = {"vital_signs_history": vital_signs_history, "history": True}

    return render(
        request,
        "staff/nurse/vital_signs/partials/vital-signs-history-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_vital_signs_history_table_row(request: HttpRequest, id):
    vital_sign = get_object_or_404(VitalSign, pk=id)
    return render(
        request,
        "staff/nurse/vital_signs/partials/vital-signs-history-table-row-partial.html",
        {"vital_sign": vital_sign},
    )


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_vital_sign_details(request: HttpRequest, id):
    vital_sign = get_object_or_404(VitalSign, pk=id)
    context = {"vital_sign": vital_sign}
    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/nurse/vital_signs/partials/vital-sign-details-partial.html",
            context,
        )
    return render(request, "staff/nurse/vital_signs/details/page.html", context)


nurse_vital_signs_urlpatterns = [
    path("nurse/vital_signs/", nurse_vital_signs, name="nurse_vital_signs"),
    path(
        "nurse/vital_signs_queue/filter",
        nurse_vital_signs_queue_filter,
        name="nurse_vital_signs_queue_filter",
    ),
    path(
        "nurse/vital_signs_history/filter",
        nurse_vital_signs_history_filter,
        name="nurse_vital_signs_history_filter",
    ),
    re_path(
        r"^nurse/vital_signs_history/table_row/(?P<id>[0-9]+|__ID__)/$",
        nurse_vital_signs_history_table_row,
        name="nurse_vital_signs_history_table_row",
    ),
    path(
        "nurse/vital_sign_details/<int:id>/",
        nurse_vital_sign_details,
        name="nurse_vital_sign_details",
    ),
]
