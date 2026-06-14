from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from appointments.forms import AppointmentForm
from appointments.models import Appointment

# Create your views here.
@login_required
def new_appointment_modal(request: HttpRequest):
    form = AppointmentForm()
    context = { "form": form }
    return render(request, "appointments/partials/new-appointment-modal-partial.html", context)

@login_required
def register_new_appointment(request: HttpRequest):
    form = AppointmentForm(request.POST)
    if form.is_valid():
        appointment = form.save()
        response = render(request, "staff/admin/appointments/partials/appointments-table-row-partial.html", { "appointment": appointment })
        response["HX-Trigger"] = "new-appointment-success"
        return response
    else:
        response = render(request, "appointments/partials/new-appointment-modal-partial.html", { "form": form })
        response["HX-Retarget"] = "#new_appointment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "new-appointment-fail"
        return response

@login_required
def update_appointment_modal(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    form = AppointmentForm(instance=appointment)
    context = { "form": form, "appointment": appointment }
    return render(request, "appointments/partials/update-appointment-modal-partial.html", context)    

@login_required
@require_POST
def update_appointment(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    form = AppointmentForm(request.POST, instance=appointment)
    if form.is_valid():
        appointment = form.save()
        response = render(request, "staff/admin/appointments/partials/appointments-table-row-partial.html", { "appointment": appointment })
        response["HX-Trigger"] = "update-appointment-success"
        response["HX-Retarget"] = f"#appointments-table-row-id-{appointment.id}"
        response["HX-Reswap"] = "outerHTML"
        return response
    else:
        response = render(request, "appointments/partials/update-appointment-modal-partial.html", { "form": form })
        response["HX-Retarget"] = "#update_appointment_modal"
        response["HX-Reswap"] = "outerHTML"
        response["HX-Trigger-After-Settle"] = "update-appointment-fail"
        return response

@login_required
def delete_appointment_modal(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    context = { "appointment": appointment }
    return render(request, "appointments/partials/delete-appointment-modal-partial.html", context)

@login_required
@require_POST
def delete_appointment(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    appointment.is_active = False
    appointment.save()
    response = render(request, "staff/admin/appointments/partials/appointments-table-row-partial.html", { "appointment": appointment })
    response["HX-Trigger"] = "delete-appointment-success"
    response["HX-Retarget"] = f"#appointments-table-row-id-{appointment.id}"
    response["HX-Reswap"] = "outerHTML"
    return response

@login_required
def restore_appointment_modal(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    context = { "appointment": appointment }
    return render(request, "appointments/partials/restore-appointment-modal-partial.html", context)

@login_required
@require_POST
def restore_appointment(request: HttpRequest, id):
    appointment = get_object_or_404(Appointment, pk=id)
    appointment.is_active = True
    appointment.save()
    response = render(request, "staff/admin/appointments/partials/appointments-table-row-partial.html", { "appointment": appointment }) 
    response["HX-Trigger"] = "restore-appointment-success"
    response["HX-Retarget"] = f"#appointments-table-row-id-{appointment.id}"
    response["HX-Reswap"] = "outerHTML"
    return response

@login_required
def get_patient_visits(request: HttpRequest):
    form = AppointmentForm(request.GET)
    return HttpResponse(form["visit"])