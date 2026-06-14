import json
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from patients.models import Patient
from utils import get_url_model_id, patient_details
from .forms import PatientForm


# Create your views here.
@login_required
def new_patient_modal(request: HttpRequest):
    form = PatientForm()
    context = {"form": form}
    response = render(
        request, "patients/partials/new-patient-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_patient_modal"}}
        )
    return response


@login_required
@require_POST
def register_new_patient(request: HttpRequest):
    form = PatientForm(request.POST)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")

    if form.is_valid():
        patient = form.save()
        response = HttpResponse()
        details_url = patient_details(request, patient.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__", get_url_model_id("patient", patient=patient)
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_patient_modal",
                    "message": "Patient created successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        return response
    else:
        response = render(
            request, "patients/partials/new-patient-modal-partial.html", {"form": form}
        )
        response["HX-Retarget"] = "#new_patient_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_patient_modal"}}
        )
        return response


@login_required
def update_patient_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientForm(instance=patient)
    context = {"form": form, "patient": patient}
    response = render(
        request, "patients/partials/update-patient-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "update_patient_modal"}}
        )
    return response


@login_required
@require_POST
def update_patient(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")

    form = PatientForm(request.POST, instance=patient, initial={"id": patient.id})
    if form.is_valid():
        patient = form.save()
        response = HttpResponse()
        details_url = patient_details(request, patient.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__", get_url_model_id("patient", patient=patient)
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "update_patient_modal",
                    "message": "Patient updated successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        return response
    else:
        response = render(
            request,
            "patients/partials/update-patient-modal-partial.html",
            {"form": form, "patient": patient},
        )
        response["HX-Retarget"] = "#update_patient_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "update_patient_modal"}}
        )
        return response


@login_required
def delete_patient_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    context = {"patient": patient}
    return render(
        request, "patients/partials/delete-patient-modal-partial.html", context
    )


@login_required
@require_POST
def delete_patient(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    patient.is_active = False
    patient.save()
    response = render(
        request,
        "staff/admin/patients/partials/patients-table-row-partial.html",
        {"patient": patient},
    )
    response["HX-Trigger"] = json.dumps(
        {
            "form-success": {
                "modalId": "delete_patient_modal",
                "message": "Patient record created successfully!",
            }
        }
    )
    response["HX-Retarget"] = f"#patients-table-row-id-{patient.id}"
    response["HX-Reswap"] = "outerHTML"
    return response


@login_required
def restore_patient_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    context = {"patient": patient}
    return render(
        request, "patients/partials/restore-patient-modal-partial.html", context
    )


@login_required
@require_POST
def restore_patient(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    patient.is_active = True
    patient.save()
    response = render(
        request,
        "staff/admin/patients/partials/patients-table-row-partial.html",
        {"patient": patient},
    )
    response["HX-Trigger"] = "restore-patient-success"
    response["HX-Retarget"] = f"#patients-table-row-id-{patient.id}"
    response["HX-Reswap"] = "outerHTML"
    return response
