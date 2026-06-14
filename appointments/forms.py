from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from dynamic_forms import DynamicField, DynamicFormMixin

from appointments.models import Appointment
from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


class AppointmentForm(DynamicFormMixin, forms.ModelForm):
    def visit_choices(form):
        patient = form["patient"].value()
        return Visit.objects.filter(patient=patient).order_by("-date")

    def initial_visit(form):
        patient = form["patient"].value()
        return Visit.objects.filter(patient=patient).order_by("-date").first()

    patient = forms.ModelChoiceField(
        Patient.objects.order_by("first_name"),
        required=True,
        empty_label="Select a patient",
        widget=forms.Select(
            {"class": "input input-bordered w-full", "placeholder": "Select a patient"}
        ),
    )
    doctor = forms.ModelChoiceField(
        Staff.objects.filter(role=Staff.RoleEnum.DOCTOR),
        required=True,
        empty_label="Select a doctor",
        widget=forms.Select(
            {"class": "input input-bordered w-full", "placeholder": "Select a doctor"}
        ),
    )
    visit = DynamicField(
        forms.ModelChoiceField,
        queryset=visit_choices,
        initial=initial_visit,
        required=False,
    )
    reason = forms.CharField(
        widget=forms.Textarea(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Reason for appointment",
                "required": False,
            }
        )
    )
    appointment_date = forms.DateTimeField(
        initial=timezone.now().date(),
        widget=forms.DateInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Appointment Date",
                "type": "date",
            }
        ),
    )
    date = forms.DateTimeField(
        initial=timezone.now().date(),
        widget=forms.DateInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Date",
                "type": "date",
            }
        ),
    )

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get("appointment_date")
        if appointment_date < timezone.now().date():
            raise ValidationError(
                "Please select today or a future date for the appointment."
            )
        return appointment_date

    def clean(self):
        patient = self.cleaned_data.get("patient")
        doctor = self.cleaned_data.get("doctor")
        appointment_date = self.cleaned_data.get("appointment_date")
        if Appointment.objects.filter(
            patient=patient, doctor=doctor, appointment_date__date=appointment_date
        ).exists():
            raise ValidationError(
                "There already is an appointment for this patient under the same doctor, and at the same date"
            )
        return super().clean()

    class Meta:
        model = Appointment
        fields = {"patient", "doctor", "visit", "reason", "appointment_date", "date"}
