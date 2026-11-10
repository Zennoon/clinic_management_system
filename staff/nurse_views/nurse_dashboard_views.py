import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.db.models import F, Count
from django.urls import path, reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from charges.models import Charge
from staff.models import Staff
from staff.utils import user_has_role
from treatments.models import TreatmentRequest, TreatmentRequestResult, TreatmentResult
from visits.models import Visit
from vital_signs.models import VitalSign


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse(_: HttpRequest):
    return redirect(reverse("staff:nurse_dashboard"))


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_dashboard(request: HttpRequest):
    today = timezone.now()
    awaiting_vital_signs = Visit.objects.filter(
        date__date=today, visit_status_annotated=Visit.VisitStatusEnum.AWAITING_VITALS
    ).order_by("-date")

    total_vital_signs_today = VitalSign.objects.filter(date__date=today).count()
    total_awaiting_treatments = (
        Visit.objects.filter(date__date=today)
        .filter(visit_status_annotated=Visit.VisitStatusEnum.AWAITING_TREATMENT)
        .count()
    )
    total_treatment_requests_today = TreatmentRequest.objects.filter(
        date__date=today
    ).count()
    total_treatment_requests_handled_today = TreatmentRequestResult.objects.filter(
        date__date=today,
    ).count()
    total_earlier_treatment_requests_handled_today = TreatmentRequestResult.objects.filter(
        date__date=today,
        treatment_request__date__date__lt=today
    ).count()
    total_awaiting_treatment_payment = (
        Visit.objects.filter(date__date=today)
        .filter(visit_status_annotated=Visit.VisitStatusEnum.AWAITING_TREATMENT_PAYMENT)
        .count()
    )
    treatments_by_requests = (
        TreatmentRequest.objects.filter(date__date=today)
        .values(
            "treatment_services__treatments__id", "treatment_services__treatments__name"
        )
        .annotate(
            order_count=Count("treatment_services__treatments__id"),
            treatment_name=F("treatment_services__treatments__name"),
        )
        .order_by("-order_count")
        .distinct()[:5]
    )
    most_requested_treatments = []
    for item in treatments_by_requests:
        most_requested_treatments.append(
            {"name": item["treatment_name"], "amount": item["order_count"]}
        )
    treatment_services_by_request = (
        TreatmentRequest.objects.filter(date__date=today)
        .values("treatment_services__id", "treatment_services__name")
        .annotate(
            order_count=Count("treatment_services__id"),
            service_name=F("treatment_services__name"),
        )
        .order_by("-order_count")
        .distinct()[:5]
    )
    most_requested_treatment_services = []
    for item in treatment_services_by_request:
        most_requested_treatment_services.append(
            {"name": item["service_name"], "amount": item["order_count"]}
        )

    treatment_requests_by_type = (
        TreatmentRequest.objects.filter(date__date=today)
        .values("treatment_services__treatments__type")
        .annotate(
            count=Count("treatment_services__treatments__type"),
            type=F("treatment_services__treatments__type"),
        )
        .values("count", "type")
        .order_by("-count")
    )
    treatment_requests_type_breakdown = []
    for item in treatment_requests_by_type:
        treatment_requests_type_breakdown.append(
            {"name": item["type"].label, "count": item["count"]}
        )

    available_treatment_requests = TreatmentRequest.objects.filter(
        date__date=today, treatment_request_results__isnull=True
    )
    pending_treatment_requests = []

    # Eliminate treatment requests which have not been paid for yet
    for treatment_request in available_treatment_requests:
        treatment_charge = Charge.objects.filter(
            content_type=ContentType.objects.get_for_model(TreatmentRequest),
            object_id=treatment_request.pk,
        )
        if treatment_charge.exists() and not treatment_charge.first().is_due:
            pending_treatment_requests.append(treatment_request)
    # pending_treatment_visits = Visit.objects.filter(visit_status_annotated=Visit.VisitStatusEnum.AWAITING_TREATMENT, date__date=today).all()

    context = {
        "awaiting_vital_signs": awaiting_vital_signs,
        "total_vital_signs_today": total_vital_signs_today,
        "total_awaiting_treatments": total_awaiting_treatments,
        "total_treatment_requests_today": total_treatment_requests_today,
        "total_earlier_treatment_requests_handled_today": total_earlier_treatment_requests_handled_today,
        "total_treatment_requests_from_today_handled_today": total_treatment_requests_handled_today - total_earlier_treatment_requests_handled_today,
        "total_treatment_requests_handled_today": total_treatment_requests_handled_today,
        "total_awaiting_treatment_payment": total_awaiting_treatment_payment,
        "most_requested_treatments": most_requested_treatments,
        "most_requested_treatments_json": json.dumps(
            most_requested_treatments, cls=DjangoJSONEncoder
        ),
        "most_requested_treatment_services": most_requested_treatment_services,
        "most_requested_treatment_services_json": json.dumps(
            most_requested_treatment_services, cls=DjangoJSONEncoder
        ),
        "treatment_requests_type_breakdown": treatment_requests_type_breakdown,
        "treatment_requests_type_breakdown_json": json.dumps(
            treatment_requests_type_breakdown, cls=DjangoJSONEncoder
        ),
        "pending_treatment_requests": pending_treatment_requests,
    }

    if request.headers.get("HX-Request"):
        return render(
            request,
            "staff/nurse/dashboard/partials/dashboard-partial.html",
            context,
        )
    else:
        return render(request, "staff/nurse/dashboard/page.html", context)


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_dashboard_vital_signs_queue(request: HttpRequest):
    today = timezone.now()
    awaiting_vital_signs = Visit.objects.filter(
        date__date=today, visit_status_annotated=Visit.VisitStatusEnum.AWAITING_VITALS
    ).order_by("-date")
    return render(
        request,
        "staff/nurse/dashboard/partials/dashboard-vital-signs-queue-table-body-partial.html",
        {"awaiting_vital_signs": awaiting_vital_signs},
    )


@login_required
@user_has_role(Staff.RoleEnum.NURSE)
def nurse_dashboard_treatment_requests_queue(request: HttpRequest):
    today = timezone.now()
    available_treatment_requests = TreatmentRequest.objects.filter(
        date__date=today, treatment_request_results__isnull=True
    )
    pending_treatment_requests = []

    # Eliminate treatment requests which have not been paid for yet
    for treatment_request in available_treatment_requests:
        treatment_charge = Charge.objects.filter(
            content_type=ContentType.objects.get_for_model(TreatmentRequest),
            object_id=treatment_request.pk,
        )
        if treatment_charge.exists() and not treatment_charge.first().is_due:
            pending_treatment_requests.append(treatment_request)
    return render(
        request,
        "staff/nurse/dashboard/partials/dashboard-treatment-requests-queue-table-body-partial.html",
        {"pending_treatment_requests": pending_treatment_requests},
    )


nurse_dashboard_urlpatterns = [
    path("nurse/", nurse, name="nurse"),
    path("nurse/dashboard/", nurse_dashboard, name="nurse_dashboard"),
    path(
        "nurse/dashboard/vital_signs_queue",
        nurse_dashboard_vital_signs_queue,
        name="nurse_dashboard_vital_signs_queue",
    ),
    path(
        "nurse/dashboard/treatment_requests_queue",
        nurse_dashboard_treatment_requests_queue,
        name="nurse_dashboard_treatment_requests_queue",
    ),
]
