import time

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import HttpRequest
from django.core.paginator import Paginator
from django.urls import path, re_path, reverse

from patients.models import Patient
from staff.models import Staff
from staff.utils import clean_urlencode, get_patient_vitals_chart_data, user_has_role


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_patients(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 10

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

    qs = Patient.objects

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
            request, "staff/nurse/patients/partials/patients-partial.html", context
        )
    else:
        response = render(request, "staff/nurse/patients/page.html", context)

    return response


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_patients_filter(request: HttpRequest):
    page = request.GET.get("page", 1)
    per_page = 10

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

    qs = Patient.objects

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
    patients = paginator.page(page_number)
    context = {"patients": patients}
    start = time.time()
    response = render(
        request,
        "staff/nurse/patients/partials/patients-table-partial.html",
        context,
    )
    end = time.time()
    response["HX-Push-Url"] = (
        f"{reverse("staff:nurse_patients")}{clean_urlencode(request.GET)}"
    )
    print(end - start)
    return response


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_patient_details(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)

    vital_signs_paginator = Paginator(patient.vital_signs.order_by("-date"), per_page=5)
    patient_vital_signs = vital_signs_paginator.get_page(1)

    treatment_requests_paginator = Paginator(
        patient.treatment_requests.filter().order_by("-date"), per_page=5
    )
    patient_treatment_requests = treatment_requests_paginator.get_page(1)
    context = {
        "patient": patient,
        "patient_vital_signs": patient_vital_signs,
        "patient_treatment_requests": patient_treatment_requests,
    }
    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/nurse/patients/partials/patient-details-partial.html",
            context,
        )
    return render(request, "staff/nurse/patients/details/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_patient_vital_signs_table(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)

    page = request.GET.get("page", 1)
    per_page = 5

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    vital_signs_paginator = Paginator(
        patient.vital_signs.order_by("-date"), per_page=per_page
    )
    patient_vital_signs = vital_signs_paginator.get_page(page_number)
    context = {"patient": patient, "patient_vital_signs": patient_vital_signs}
    return render(
        request,
        "staff/nurse/patients/partials/patient-vital-signs-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_patient_vital_signs_table_filter(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)

    page = request.GET.get("page", 1)
    per_page = 5

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    vital_signs_paginator = Paginator(
        patient.vital_signs.order_by("-date"), per_page=per_page
    )
    patient_vital_signs = vital_signs_paginator.get_page(page_number)
    context = {"patient": patient, "patient_vital_signs": patient_vital_signs}
    return render(
        request,
        "staff/nurse/patients/partials/patient-vital-signs-table-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_patient_vital_signs_visuals(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    patient_vital_signs_charts_data = get_patient_vitals_chart_data(patient)
    context = {
        "patient": patient,
        "patient_vital_signs_charts_data": patient_vital_signs_charts_data,
    }
    return render(
        request,
        "staff/nurse/patients/partials/patient-vital-signs-visualization-partial.html",
        context,
    )


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_patient_treatment_requests_filter(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    page = request.GET.get("page", 1)
    per_page = 5

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        page_number = 1

    q = request.GET.get("q")
    order_by = request.GET.get("sort")
    show_archived = request.GET.get("show_archived")

    qs = patient.treatment_requests

    if not show_archived:
        qs = qs.exclude(is_operational_annotated=False)

    if q:
        try:
            id_q = int(q)
        except ValueError:
            id_q = q

        qs = qs.filter(
            Q(id__icontains=id_q) | Q(visit__id__icontains=id_q) | Q()
        ).distinct()

    if order_by:
        qs = qs.order_by(order_by)
    else:
        qs = qs.order_by("-date")

    treatment_requests_paginator = Paginator(qs, per_page=per_page)

    patient_treatment_requests = treatment_requests_paginator.get_page(page_number)
    context = {
        "patient": patient,
        "patient_treatment_requests": patient_treatment_requests,
    }
    return render(
        request,
        "staff/nurse/patients/partials/patient-treatment-requests-table-partial.html",
        context,
    )


nurse_patients_urlpatterns = [
    path("nurse/patients/", nurse_patients, name="nurse_patients"),
    path("nurse/patients/filter/", nurse_patients_filter, name="nurse_patients_filter"),
    re_path(
        r"^nurse/patients/(?P<id>[0-9]+|__ID__)/$",
        nurse_patient_details,
        name="nurse_patient_details",
    ),
    path(
        "nurse/patients/<int:id>/vital_signs/table/",
        nurse_patient_vital_signs_table,
        name="nurse_patient_vital_signs_table",
    ),
    path(
        "nurse/patients/<int:id>/vital_signs/table/filter",
        nurse_patient_vital_signs_table_filter,
        name="nurse_patient_vital_signs_table_filter",
    ),
    path(
        "nurse/patients/<int:id>/vital_signs/visualization",
        nurse_patient_vital_signs_visuals,
        name="nurse_patient_vital_signs_visuals",
    ),
    path(
        "nurse/patients/<int:id>/treatment_requests/filter",
        nurse_patient_treatment_requests_filter,
        name="nurse_patient_treatment_requests_filter",
    ),
]
