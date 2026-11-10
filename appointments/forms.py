from constance import config
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from dynamic_forms import DynamicField, DynamicFormMixin

from appointments.models import Appointment
from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


class AppointmentForm(DynamicFormMixin, forms.ModelForm):
    def initial_patient(self=None):
        if self and self.instance.pk:
            return self.instance.patient
        return Patient.objects.exclude(is_active=False).order_by("first_name").first()

    def get_bound_field_value(self, name):
        try:
            return self[name].value()
        except Exception:
            return None

    def visit_choices(self):
        patient = self.get_bound_field_value("patient")
        if patient is None:
            return Visit.objects.none()
        return (
            Visit.objects.exclude(is_operational_annotated=False)
            .filter(patient=patient)
            .order_by("-date")
        )

    def initial_visit(self):
        if self.instance.pk:
            return self.instance.visit
        patient = self.get_bound_field_value("patient")
        if patient is None:
            return None
        return (
            Visit.objects.exclude(is_operational_annotated=False)
            .filter(patient=patient)
            .order_by("-date")
            .first()
        )

    patient = forms.ModelChoiceField(
        Patient.objects.exclude(is_active=False).order_by("first_name"),
        required=True,
        initial=initial_patient,
        empty_label="Select a patient",
        widget=forms.Select(
            {"class": "input input-bordered w-full", "placeholder": "Select a patient"}
        ),
    )
    visit = DynamicField(
        forms.ModelChoiceField,
        queryset=visit_choices,
        initial=initial_visit,
        required=False,
    )
    doctor = forms.ModelChoiceField(
        Staff.objects.filter(role=Staff.RoleEnum.DOCTOR),
        required=True,
        empty_label="Select a doctor",
        widget=forms.Select(
            {"class": "input input-bordered w-full", "placeholder": "Select a doctor"}
        ),
    )
    reason = forms.CharField(
        widget=forms.Textarea(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Reason for appointment",
            }
        ),
        required=False,
    )
    appointment_date = forms.DateTimeField(
        initial=timezone.now().date(),
        widget=forms.DateInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Scheduled For",
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields.get("visit").queryset = self.visit_choices()
        self.fields.get("visit").initial = self.initial_visit()
        
        if self.instance.pk:
            self.fields.get("patient").disabled = True
            self.fields.get("visit").disabled = True

        if self.instance.pk and not self.instance.is_operational:
            for field in self.fields.copy():
                self.fields.pop(field)
            self.add_error(
                None,
                "This appointment is archived, and cannot be modified. Please contact an admin to get it restored.",
            )
            self.disable_submit = True

    def clean_patient(self):
        patient = self.cleaned_data.get("patient")
        if self.instance.pk and patient != self.instance.patient:
            self.add_error("patient", f"This appointment is intended for {self.appointment.patient.fullname}")
        if not (patient and patient.is_operational):
            self.add_error(
                "patient",
                "This patient is not available for modification. Please contact an admin to get them restored.",
            )
        return patient

    def clean_visit(self):
        visit = self.cleaned_data.get("visit")
        
        if not visit and self.instance.pk:
            return self.instance.visit
        if self.instance.pk and visit != self.instance.visit:
            self.add_error("visit", f"This appointment is intended for visit {self.appointment.visit.id.zfill(6)}")

        if not (visit and visit.is_operational):
            self.add_error(
                "visit",
                "This visit is not available for modification. Please contact an admin to get it restored.",
            )
        return visit

    def clean_doctor(self):
        doctor = self.cleaned_data.get("doctor")
        if not doctor or (
            config.STRICT_MODE == True and doctor.role != Staff.RoleEnum.DOCTOR
        ):
            self.add_error(
                "doctor", "Please select a valid option from the list of doctors."
            )
        return doctor

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get("appointment_date")
        if not (appointment_date and appointment_date.date() >= timezone.now().date()):
            raise ValidationError("Appointments cannot be scheduled for a past date.")
        return appointment_date

    def clean(self):
        patient = self.cleaned_data.get("patient")
        doctor = self.cleaned_data.get("doctor")
        appointment_date = self.cleaned_data.get("appointment_date")
        existing_appointment =  Appointment.objects.filter(
            patient=patient, doctor=doctor, appointment_date__date=appointment_date
        )
        if self.instance.pk:
            existing_appointment = existing_appointment.exclude(id=self.instance.id)
        
        if existing_appointment.exists():
            raise ValidationError(
                "There already is an appointment for this patient under the same doctor, and at the same date"
            )
        return super().clean()

    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "visit", "reason", "appointment_date", "date"]


class PatientAppointmentForm(DynamicFormMixin, forms.ModelForm):
    def visit_choices(self):
        patient = self.patient
        if patient is None:
            return Visit.objects.none()
        return (Visit.objects.exclude(is_operational_annotated=False)
            .filter(patient=patient)
            .order_by("-date")
        )
    
    def initial_visit(self):
        if self.instance.pk:
            return self.instance.visit
        
        patient = self.patient
        if patient is None:
            return None
        return (
            Visit.objects.exclude(is_operational_annotated=False)
            .filter(patient=patient)
            .order_by("-date")
            .first()
        )
    
    visit = DynamicField(
        forms.ModelChoiceField,
        queryset=visit_choices,
        initial=initial_visit,
        required=False,
    )
    doctor = forms.ModelChoiceField(
        Staff.objects.filter(role=Staff.RoleEnum.DOCTOR),
        required=True,
        empty_label="Select a doctor",
        widget=forms.Select(
            {"class": "input input-bordered w-full", "placeholder": "Select a doctor"}
        ),
    )
    reason = forms.CharField(
        widget=forms.Textarea(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Reason for appointment",
            }
        ),
        required=False,
    )
    appointment_date = forms.DateTimeField(
        initial=timezone.now().date(),
        widget=forms.DateInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Scheduled For",
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
    
    def __init__(self, *args, patient=None, **kwargs):
        self.patient = patient
        super().__init__(*args, **kwargs)

        if self.instance.pk and not self.instance.is_operational:
            for field in self.fields.copy():
                self.fields.pop(field)
            self.add_error(
                None,
                "This appointment is archived, and cannot be modified. Please contact an admin to get it restored.",
            )
            self.disable_submit = True
        
        if self.patient and not self.patient.is_operational:
            for field in self.fields.copy():
                self.fields.pop(field)
            self.add_error(
                None,
                "This patient is archived, and cannot be modified. Please contact an admin to get them restored.",
            )
            self.disable_submit = True
    
    def clean_visit(self):
        visit = self.cleaned_data.get("visit")
        if not (visit and visit.is_operational):
            self.add_error(
                "visit",
                "This visit is not available for modification. Please contact an admin to get it restored.",
            )
        return visit

    def clean_doctor(self):
        doctor = self.cleaned_data.get("doctor")
        if not doctor or (
            config.STRICT_MODE == True and doctor.role != Staff.RoleEnum.DOCTOR
        ):
            self.add_error(
                "doctor", "Please select a valid option from the list of doctors."
            )
        return doctor

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get("appointment_date")
        if not (appointment_date and appointment_date.date() >= timezone.now().date()):
            raise ValidationError("Appointments cannot be scheduled for a past date.")
        return appointment_date

    def clean(self):
        patient = self.patient
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
        fields = ["doctor", "visit", "reason", "appointment_date", "date"]
        