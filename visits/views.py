import json

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from patients.models import Patient
from utils import get_url_model_id, visit_details
from visits.forms import PatientVisitForm, VisitForm
from visits.models import Visit

# Create your views here.


@login_required
def new_visit_modal(request: HttpRequest):
    form = VisitForm()
    context = {"form": form}
    response = render(request, "visits/partials/new-visit-modal-partial.html", context)
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_visit_modal"}}
        )
    return response


@login_required
def register_new_visit(request: HttpRequest):
    form = VisitForm(request.POST)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")

    next_model = request.GET.get("next_model", "visit")
    if form.is_valid():
        visit = form.save(commit=False)
        visit.created_by = request.user
        visit.save()
        visit.create_consultation_charge(staff=request.user)
        response = HttpResponse()
        details_url = visit_details(request, visit.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model, patient=visit.patient, visit=visit
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_visit_modal",
                    "message": "Visit created successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        return response
    else:
        response = render(
            request, "visits/partials/new-visit-modal-partial.html", {"form": form}
        )
        response["HX-Retarget"] = "#new_visit_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_visit_modal"}}
        )
        return response


@login_required
def new_patient_visit_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientVisitForm(patient=patient)
    context = {"patient": patient, "form": form}
    response = render(
        request, "visits/partials/new-patient-visit-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_patient_visit_modal"}}
        )
    return response


@login_required
def register_new_patient_visit(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientVisitForm(request.POST, patient=patient)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")

    next_model = request.GET.get("next_model", "visit")

    if form.is_valid():
        visit = form.save(commit=False)
        visit.patient = patient
        visit.created_by = request.user
        visit.save()
        visit.create_consultation_charge(staff=request.user)
        response = HttpResponse()
        details_url = visit_details(request, visit.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model, patient=visit.patient, visit=visit
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_patient_visit_modal",
                    "message": "Visit created successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        return response
    else:
        response = render(
            request,
            "visits/partials/new-patient-visit-modal-partial.html",
            {"form": form, "patient": patient},
        )
        response["HX-Retarget"] = "#new_patient_visit_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_patient_visit_modal"}}
        )
        return response


@login_required
def update_visit_modal(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    form = VisitForm(instance=visit)
    context = {"form": form, "visit": visit}
    response = render(
        request, "visits/partials/update-visit-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "update_visit_modal"}}
        )
    return response


@login_required
@require_POST
def update_visit(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    form = VisitForm(request.POST, instance=visit, user=request.user)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")

    next_model = request.GET.get("next_model", "visit")
    if form.is_valid():
        visit = form.save()
        response = HttpResponse()
        details_url = visit_details(request, visit.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model, patient=visit.patient, visit=visit
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "update_visit_modal",
                    "message": f"Visit {visit.id} updated successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        return response
    else:
        response = render(
            request,
            "visits/partials/update-visit-modal-partial.html",
            {"visit": visit, "form": form},
        )
        response["HX-Retarget"] = "#update_visit_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "update_visit_modal"}}
        )
        return response


@login_required
def delete_visit_modal(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    context = {"visit": visit}
    return render(request, "visits/partials/delete-visit-modal-partial.html", context)


@login_required
@require_POST
def delete_visit(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    visit.is_active = False
    visit.save()
    response = render(
        request,
        "staff/admin/visits/partials/visits-table-row-partial.html",
        {"visit": visit},
    )
    response["HX-Trigger"] = json.dumps(
        {"form-success": {"modalId": "delete_visit_modal"}}
    )
    response["HX-Retarget"] = f"#visits-table-row-id-{visit.id}"
    response["HX-Reswap"] = "outerHTML"
    return response


@login_required
def restore_visit_modal(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    context = {"visit": visit}
    return render(request, "visits/partials/restore-visit-modal-partial.html", context)


@login_required
@require_POST
def restore_visit(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    visit.is_active = True
    visit.save()
    response = render(
        request,
        "staff/admin/visits/partials/visits-table-row-partial.html",
        {"visit": visit},
    )
    response["HX-Trigger"] = "restore-visit-success"
    response["HX-Retarget"] = f"#visits-table-row-id-{visit.id}"
    response["HX-Reswap"] = "outerHTML"
    return response
