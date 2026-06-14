import json

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render

from charges.forms import (
    ChargeForm,
    PatientChargeForm,
    UpdateChargeForm,
    VisitChargeForm,
)
from charges.models import Charge
from patients.models import Patient
from utils import charge_details, get_url_model_id
from visits.models import Visit


# Create your views here.
@login_required
def new_charge_modal(request: HttpRequest):
    form = ChargeForm()
    context = {"form": form}
    response = render(
        request, "charges/partials/new-charge-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_charge_modal"}}
        )
    return response


@login_required
@require_POST
def register_new_charge(request: HttpRequest):
    form = ChargeForm(request.POST)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")

    next_model = request.GET.get("next_model", "charge")

    if form.is_valid():
        charge = form.save(commit=False)
        charge.issuer = request.user
        charge.save()
        charge.visit.update_status()
        response = HttpResponse()
        details_url = charge_details(request, charge.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=charge.visit.patient,
                            visit=charge.visit,
                            charge=charge,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_charge_modal",
                    "message": "Charge created successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        return response
    else:
        response = render(
            request, "charges/partials/new-charge-modal-partial.html", {"form": form}
        )
        response["HX-Retarget"] = "#new_charge_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_charge_modal"}}
        )
        return response


@login_required
def new_visit_charge_modal(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    form = VisitChargeForm(visit=visit, user=request.user)
    context = {"form": form, "visit": visit}
    response = render(
        request, "charges/partials/new-visit-charge-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_visit_charge_modal"}}
        )
    return response


@login_required
def register_new_visit_charge(request: HttpRequest, id):
    visit = get_object_or_404(Visit, pk=id)
    form = VisitChargeForm(request.POST, visit=visit, user=request.user)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")

    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "charge")

    if form.is_valid():
        charge = form.save(commit=False)
        charge.visit = visit
        charge.issuer = request.user
        charge.save()
        charge.visit.update_status()
        response = HttpResponse()
        details_url = charge_details(request, charge.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=charge.visit.patient,
                            visit=charge.visit,
                            charge=charge,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_visit_charge_modal",
                    "message": "Charge created successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        return response
    else:
        response = render(
            request,
            "charges/partials/new-visit-charge-modal-partial.html",
            {"form": form, "visit": visit},
        )
        response["HX-Retarget"] = "#new_visit_charge_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_visit_charge_modal"}}
        )
        return response


@login_required
def new_patient_charge_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientChargeForm(patient=patient, user=request.user)
    context = {"form": form, "patient": patient}
    response = render(
        request, "charges/partials/new-patient-charge-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_patient_charge_modal"}}
        )
    return response


@login_required
def register_new_patient_charge(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientChargeForm(request.POST, patient=patient, user=request.user)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")

    next_model = request.GET.get("next_model", "charge")

    if form.is_valid():
        charge = form.save(commit=False)
        charge.issuer = request.user
        charge.save()
        charge.visit.update_status()
        response = HttpResponse()
        details_url = charge_details(request, charge.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=charge.visit.patient,
                            visit=charge.visit,
                            charge=charge,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_patient_charge_modal",
                    "message": "Charge created successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        return response
    else:
        response = render(
            request,
            "charges/partials/new-patient-charge-modal-partial.html",
            {"form": form},
        )
        response["HX-Retarget"] = "#new_patient_charge_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_patient_charge_modal"}}
        )
        return response


@login_required
def update_charge_modal(request: HttpRequest, id: int):
    charge = get_object_or_404(Charge, pk=id)
    form = UpdateChargeForm(
        instance=charge,
        user=request.user,
    )
    context = {"form": form, "charge": charge}
    response = render(
        request, "charges/partials/update-charge-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "update_charge_modal"}}
        )
    return response


@login_required
@require_POST
def update_charge(request: HttpRequest, id: int):
    charge = get_object_or_404(Charge, pk=id)
    form = UpdateChargeForm(request.POST, instance=charge, user=request.user)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")

    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "charge")

    if form.is_valid():
        charge = form.save()
        response = HttpResponse()
        details_url = charge_details(request, charge.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=charge.visit.patient,
                            visit=charge.visit,
                            charge=charge,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "update_charge_modal",
                    "message": f"Charge {charge.id} updated successfully!",
                    "detailsUrl": details_url,
                },
            }
        )
        return response
    else:
        response = render(
            request, "charges/partials/update-charge-modal-partial.html", {"form": form}
        )
        response["HX-Retarget"] = "#update_charge_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "update-charge-fail"
        return response


@login_required
def delete_charge_modal(request: HttpRequest, id: int):
    charge = get_object_or_404(Charge, pk=id)
    context = {"charge": charge}
    return render(request, "charges/partials/delete-charge-modal-partial.html", context)


@login_required
@require_POST
def delete_charge(request: HttpRequest, id: int):
    charge = get_object_or_404(Charge, pk=id)
    charge.is_active = False
    charge.save()
    response = render(
        request,
        "staff/admin/charges/partials/charges-table-row-partial.html",
        {"charge": charge},
    )
    response["HX-Trigger"] = "delete-charge-success"
    response["HX-Retarget"] = f"#charges-table-row-id-{charge.id}"
    response["HX-Reswap"] = "outerHTML"
    return response


@login_required
def restore_charge_modal(request: HttpRequest, id: int):
    charge = get_object_or_404(Charge, pk=id)
    context = {"charge": charge}
    return render(
        request, "charges/partials/restore-charge-modal-partial.html", context
    )


@login_required
@require_POST
def restore_charge(request: HttpRequest, id: int):
    charge = get_object_or_404(Charge, pk=id)
    charge.is_active = True
    charge.save()
    response = render(
        request,
        "staff/admin/charges/partials/charges-table-row-partial.html",
        {"charge": charge},
    )
    response["HX-Trigger"] = "restore-charge-success"
    response["HX-Retarget"] = f"#charges-table-row-id-{charge.id}"
    response["HX-Reswap"] = "outerHTML"
    return response


@login_required
def get_patient_visits(request: HttpRequest):
    form = ChargeForm(request.GET)
    return HttpResponse(form["visit"])
