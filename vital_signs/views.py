import json

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from patients.models import Patient
from utils import get_url_model_id, vital_sign_details
from visits.models import Visit
from vital_signs.forms import PatientVitalSignsForm, VisitVitalSignsForm


# Create your views here.
@login_required
def new_visit_vital_sign_modal(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    form = VisitVitalSignsForm(visit=visit)
    context = {"form": form, "visit": visit}
    response = render(
        request,
        "vital_signs/partials/new-visit-vital-sign-modal-partial.html",
        context,
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_visit_vital_sign_modal"}}
        )
    return response


@login_required
@require_POST
def register_new_visit_vital_sign(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    form = VisitVitalSignsForm(request.POST, visit=visit)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "vital_sign")

    if form.is_valid():
        vital_sign = form.save(commit=False)
        vital_sign.visit = visit
        vital_sign.recorded_by = request.user
        vital_sign.save()
        vital_sign.update_patient()
        vital_sign.visit.transition_status()
        response = HttpResponse()
        details_url = vital_sign_details(request, vital_sign.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=vital_sign.visit.patient,
                            visit=vital_sign.visit,
                            vital_sign=vital_sign,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_visit_vital_sign_modal",
                    "message": "Vital Signs recorded successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        return response
    else:
        response = render(
            request,
            "vital_signs/partials/new-visit-vital-sign-modal-partial.html",
            {"form": form, "visit": visit},
        )
        response["HX-Retarget"] = "#new_visit_vital_sign_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_visit_vital_sign_modal"}}
        )
        return response


@login_required
def new_patient_vital_sign_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientVitalSignsForm(patient=patient)
    context = {"form": form, "patient": patient}
    response = render(
        request,
        "vital_signs/partials/new-patient-vital-sign-modal-partial.html",
        context,
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_patient_vital_sign_modal"}}
        )
    return response


@login_required
@require_POST
def register_new_patient_vital_sign(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientVitalSignsForm(request.POST, patient=patient)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "vital_sign")

    if form.is_valid():
        vital_sign = form.save(commit=False)
        vital_sign.recorded_by = request.user
        vital_sign.save()
        vital_sign.update_patient()
        vital_sign.visit.transition_status()
        response = HttpResponse()
        details_url = vital_sign_details(request, vital_sign.id)
        print("details_url")
        print(details_url)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=vital_sign.visit.patient,
                            visit=vital_sign.visit,
                            vital_sign=vital_sign,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_patient_vital_sign_modal",
                    "message": "Vital Signs recorded successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        print(response.headers)
        return response
    else:
        response = render(
            request,
            "vital_signs/partials/new-patient-vital-sign-modal-partial.html",
            {"form": form, "patient": patient},
        )
        response["HX-Retarget"] = "#new_patient_vital_sign_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_patient_vital_sign_modal"}}
        )
        return response
