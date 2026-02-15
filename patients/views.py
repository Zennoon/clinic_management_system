from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from patients.models import Patient
from .forms import NewPatientForm, UpdatePatientForm

# Create your views here.
@login_required
def new_patient_modal(request: HttpRequest):
    form = NewPatientForm()
    context = { "form": form }
    return render(request, "patients/partials/new-patient-modal-partial.html", context)

@login_required
@require_POST
def register_new_patient(request: HttpRequest):
    form = NewPatientForm(request.POST)
    if form.is_valid():
        patient = form.save()
        response = render(request, "staff/admin/patients/partials/patients-table-row-partial.html", { "patient": patient })
        response["HX-Trigger"] = "new-patient-success"
        return response
    else:
        response = render(request, "patients/partials/new-patient-modal-partial.html", { "form": form })
        response["+HX-Retarget"] = "#new_patient_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "new-patient-fail"
        return response

@login_required
def update_patient_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = UpdatePatientForm(instance=patient)
    context = { "form": form, "patient": patient }
    return render(request, "patients/partials/update-patient-modal-partial.html", context)

@login_required
@require_POST
def update_patient(request: HttpRequest):
    id = request.POST.get("id")
    patient = get_object_or_404(Patient, pk=id)
    form = UpdatePatientForm(request.POST, instance=patient)
    if form.is_valid():
        patient = form.save()
        response = render(request, "staff/admin/patients/partials/patients-table-row-partial.html", { "patient": patient })
        response["HX-Trigger"] = "update-patient-success"
        response["HX-Retarget"] = f"#patients-table-row-id-{patient.id}"
        response["HX-Reswap"] = "outerHTML"
        return response
    else:
        print(form.errors)
        response = render(request, "patients/partials/update-patient-modal-partial.html", { "form": form })
        response["HX-Retarget"] = "#update_patient_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "update-patient-fail"
        return response

@login_required
def delete_patient_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    context = { "patient": patient }
    return render(request, "patients/partials/delete-patient-modal-partial.html", context)

@login_required
@require_POST
def delete_patient(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    patient.is_active = False
    patient.save()
    response = render(request, "staff/admin/patients/partials/patients-table-row-partial.html", { "patient": patient }) 
    response["HX-Trigger"] = "delete-patient-success"
    response["HX-Retarget"] = f"#patients-table-row-id-{patient.id}"
    response["HX-Reswap"] = "outerHTML"
    return response

@login_required
def restore_patient_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    context = { "patient": patient }
    return render(request, "patients/partials/restore-patient-modal-partial.html", context)

@login_required
def restore_patient(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    patient.is_active = True
    patient.save()
    response = render(request, "staff/admin/patients/partials/patients-table-row-partial.html", { "patient": patient }) 
    response["HX-Trigger"] = "restore-patient-success"
    response["HX-Retarget"] = f"#patients-table-row-id-{patient.id}"
    response["HX-Reswap"] = "outerHTML"
    return response