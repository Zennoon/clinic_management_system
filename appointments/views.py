import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from appointments.forms import AppointmentForm, PatientAppointmentForm
from appointments.models import Appointment
from patients.models import Patient
from utils import appointment_details, get_url_model_id


# Create your views here.
@login_required
def new_appointment_modal(request: HttpRequest):
    form = AppointmentForm()
    context = {"form": form}
    response = render(
        request, "appointments/partials/new-appointment-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_appointment_modal"}}
        )
    return response


@login_required
def register_new_appointment(request: HttpRequest):
    form = AppointmentForm(request.POST)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "appointment")

    if form.is_valid():
        appointment = form.save()
        appointment.update_appointment_status()
        response = HttpResponse()
        details_url = appointment_details(request, appointment.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=appointment.patient,
                            visit=appointment.visit,
                            appointment=appointment,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_appointment_modal",
                    "message": "Appointment created successfully!",
                },
            }
        )

        return response
    else:
        response = render(
            request,
            "appointments/partials/new-appointment-modal-partial.html",
            {"form": form},
        )
        response["HX-Retarget"] = "#new_appointment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_appointment_modal"}}
        )
        return response


@login_required
def new_patient_appointment_modal(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientAppointmentForm(patient=patient)
    context = {"form": form, "patient": patient}
    response = render(
        request,
        "appointments/partials/new-patient-appointment-modal-partial.html",
        context,
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "new_patient_appointment_modal"}}
        )
    return response


@login_required
def register_new_patient_appointment(request: HttpRequest, id):
    patient = get_object_or_404(Patient, pk=id)
    form = PatientAppointmentForm(request.POST)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "appointment")

    if form.is_valid():
        appointment = form.save(commit=False)
        appointment.patient = patient
        appointment.save()
        appointment.update_appointment_status()
        response = HttpResponse()
        details_url = appointment_details(request, appointment.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model, visit=appointment.visit, appointment=appointment
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "new_patient_appointment_modal",
                    "message": "Appointment created successfully!",
                },
            }
        )

        return response
    else:
        response = render(
            request,
            "appointments/partials/new-patient-appointment-modal-partial.html",
            {"form": form, "patient": patient},
        )
        response["HX-Retarget"] = "#new_patient_appointment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"form-error": {"modalId": "new_patient_appointment_modal"}}
        )
        return response


@login_required
def update_appointment_modal(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    form = AppointmentForm(instance=appointment)
    context = {"form": form, "appointment": appointment}
    response = render(
        request, "appointments/partials/update-appointment-modal-partial.html", context
    )
    if request.headers.get("HX-Request"):
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"modal-response": {"modalId": "update_appointment_modal"}}
        )
    return response


@login_required
@require_POST
def update_appointment(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    form = AppointmentForm(request.POST, instance=appointment)
    next_url = request.GET.get("next_url")
    next_target = request.GET.get("next_target", "main_content")
    next_swap = request.GET.get("next_swap", "innerHTML")
    next_model = request.GET.get("next_model", "appointment")

    if form.is_valid():
        appointment = form.save()
        appointment.update_appointment_status()
        response = HttpResponse()
        details_url = appointment_details(request, appointment.id)
        response["HX-Trigger"] = json.dumps(
            {
                "next-htmx-request": {
                    "nextUrl": (next_url or details_url).replace(
                        "__ID__",
                        get_url_model_id(
                            next_model,
                            patient=appointment.patient,
                            visit=appointment.visit,
                            appointment=appointment,
                        ),
                    ),
                    "nextTarget": next_target,
                    "nextSwap": next_swap,
                },
                "form-success": {
                    "modalId": "update_appointment_modal",
                    "message": "Appointment updated successfully!"
                }
            }
        )
        return response
    else:
        response = render(
            request,
            "appointments/partials/update-appointment-modal-partial.html",
            {"form": form, "appointment": appointment},
        )
        response["HX-Retarget"] = "#update_appointment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = json.dumps({
            "form-error": { "modalId": "update_appointment_modal" }
        })
        return response


@login_required
def cancel_appointment_modal(request: HttpRequest, id):
    pass


@login_required
@require_POST
def cancel_appointment(request: HttpRequest, id):
    pass


@login_required
def delete_appointment_modal(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    context = {"appointment": appointment}
    return render(
        request, "appointments/partials/delete-appointment-modal-partial.html", context
    )


@login_required
@require_POST
def delete_appointment(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    appointment.is_active = False
    appointment.save()
    response = render(
        request,
        "staff/admin/appointments/partials/appointments-table-row-partial.html",
        {"appointment": appointment},
    )
    response["HX-Trigger"] = "delete-appointment-success"
    response["HX-Retarget"] = f"#appointments-table-row-id-{appointment.id}"
    response["HX-Reswap"] = "outerHTML"
    return response


@login_required
def restore_appointment_modal(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    context = {"appointment": appointment}
    return render(
        request, "appointments/partials/restore-appointment-modal-partial.html", context
    )


@login_required
@require_POST
def restore_appointment(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    appointment.is_active = True
    appointment.save()
    response = render(
        request,
        "staff/admin/appointments/partials/appointments-table-row-partial.html",
        {"appointment": appointment},
    )
    response["HX-Trigger"] = "restore-appointment-success"
    response["HX-Retarget"] = f"#appointments-table-row-id-{appointment.id}"
    response["HX-Reswap"] = "outerHTML"
    return response


@login_required
def get_patient_visits(request: HttpRequest):
    form = AppointmentForm(request.GET)
    return HttpResponse(form["visit"])
