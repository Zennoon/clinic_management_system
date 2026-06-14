from django import forms
from django_enum.forms import EnumChoiceField
from django.utils import timezone
from django.db.transaction import atomic
from django.core.exceptions import ValidationError
from constance import config

from patients.models import Patient
from visits.models import Visit, VisitUpdateLog


class VisitForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        Patient.objects.exclude(is_active=False).order_by("first_name"),
        required=True,
        empty_label="Select a patient",
        widget=forms.Select(
            {"class": "input input-bordered w-full", "placeholder": "John"}
        ),
    )
    visit_category = EnumChoiceField(
        enum=Visit.VisitCategoryEnum,
        choices=[(tag.value, tag.label) for tag in Visit.VisitCategoryEnum],
        required=True,
        widget=forms.Select(
            {
                "class": "select select-bordered",
                "placeholder": "Select the visit category",
            }
        ),
    )
    date = forms.DateTimeField(
        initial=timezone.now(),
        widget=forms.DateInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Date",
                "type": "date",
            }
        ),
    )
    confirmed = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    reason = forms.CharField(
        widget=forms.TextInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Reason for modification",
            },
        ),
        required=False,
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if self.instance.pk and not self.instance.is_operational:
            msg = "This visit is archived, and cannot be modified. Please contact an admin to get it restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        self._old_patient = self.instance.patient if self.instance.pk else None
        self._old_date = self.instance.date if self.instance.pk else None

    def clean_patient(self):
        patient = self.cleaned_data.get("patient")
        if patient and not patient.is_operational:
            raise ValidationError("Changes cannot be saved for an archived patient.")

        if not self.instance.pk or self.instance.patient != patient:
            require_partial_payment = config.REQUIRE_PARTIAL_PAYMENT
            partial_payment_percent = config.PARTIAL_PAYMENT_PERCENT

            if require_partial_payment and patient and patient.pk:
                unpaid_charge = patient.unpaid_consultation_fee_charge
                if unpaid_charge:
                    raise ValidationError(
                        f"Patient has a consultation fee charge (ID: {str(unpaid_charge.pk).zfill(6)}) that hasn't been paid up to the required amount ({partial_payment_percent/100:.1%}). Please make sure to fulfill it before creating a new visit."
                    )
        return patient

    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date.date() > timezone.now().date():
            raise ValidationError(
                "Visits cannot be scheduled for future dates. Please create an appointment instead.",
            )
        source_date = self._old_date or timezone.now()
        if source_date:
            date = date.replace(
                hour=source_date.hour,
                minute=source_date.minute,
                second=source_date.second,
                microsecond=source_date.microsecond,
            )
        return date

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.id and not self.instance.is_operational:
            raise ValidationError("Changes cannot be saved for an archived visit.")

        patient = cleaned_data.get("patient")
        date = cleaned_data.get("date")
        reason = cleaned_data.get("reason")

        self.sensitive_change_attempted = False

        if not patient or not date:
            return cleaned_data

        qs = Visit.objects

        if self.instance.pk:
            qs = qs.exclude(id=self.instance.pk)
        if patient and date and qs.filter(patient=patient, date__date=date).exists():
            self.add_error(
                "date",
                f"This patient already has a visit scheduled for {date.strftime("%a %b %d, %Y")}",
            )
            return cleaned_data

        patient_changed = self.instance.pk and patient != self.instance.patient
        date_changed = self.instance.pk and date != self.instance.date

        if patient_changed or date_changed:
            is_confirmed = cleaned_data.get("confirmed")
            reason = self.cleaned_data.get("reason")
            self.sensitive_change_attempted = True

            if not is_confirmed:
                self.add_error(None, "Attempting to perform a sensitive action")
                if not reason:
                    self.add_error(
                        "reason", "Please provide a reason for the modification"
                    )
                return cleaned_data
        return cleaned_data

    @atomic
    def save(self, commit=...):
        instance = super().save(commit)

        if commit and getattr(self, "sensitive_change_attempted", False):
            VisitUpdateLog.objects.create(
                old_patient=self._old_patient,
                old_date=self._old_date,
                new_patient=instance.patient,
                new_date=instance.date,
                visit=instance,
                updated_by=self.user,
            )
            instance.reconcile_consultation_charge(
                reason=self.cleaned_data.get("reason"), staff=self.user
            )

        return instance

    class Meta:
        model = Visit
        fields = {"patient", "visit_category", "date"}


class PatientVisitForm(forms.ModelForm):
    visit_category = EnumChoiceField(
        enum=Visit.VisitCategoryEnum,
        choices=[(tag.value, tag.label) for tag in Visit.VisitCategoryEnum],
        required=True,
        widget=forms.Select(
            {
                "class": "select select-bordered",
                "placeholder": "Select the visit category",
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

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if self.patient and not self.patient.is_operational:
            msg = "This patient is archived, and cannot be modified. Please contact an admin to get them restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        require_partial_payment = config.REQUIRE_PARTIAL_PAYMENT
        partial_payment_percent = config.PARTIAL_PAYMENT_PERCENT
        if require_partial_payment and self.patient and self.patient.pk:
            unpaid_charge = self.patient.unpaid_consultation_fee_charge
            if unpaid_charge:
                self.add_error(
                    None,
                    f"Patient has a consultation fee charge (ID: {str(unpaid_charge.pk).zfill(6)}) that hasn't been paid up to the required amount ({partial_payment_percent/100:.1%}). Please make sure to fulfill it before creating a new visit.",
                )

                for field in self.fields.values():
                    field.disabled = True
                self.disable_submit = True

        if self.instance.pk and not self.instance.is_operational:
            msg = "This visit is archived, and cannot be modified. Please contact an admin to get it restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        self._old_patient = self.instance.patient if self.instance.pk else None
        self._old_date = self.instance.date if self.instance.pk else None

    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date.date() > timezone.now().date():
            raise ValidationError(
                "Visits cannot be scheduled for future dates. Please create an appointment instead.",
            )
        source_date = self._old_date or timezone.now()
        if source_date:
            date = date.replace(
                hour=source_date.hour,
                minute=source_date.minute,
                second=source_date.second,
                microsecond=source_date.microsecond,
            )
        return date

    def clean(self):
        visit = self.instance
        if visit.id and not visit.is_operational:
            raise ValidationError("Changes cannot be saved for an archived visit.")
        if self.patient and not self.patient.is_operational:
            raise ValidationError("Changes cannot be saved for an archived patient.")

        require_partial_payment = config.REQUIRE_PARTIAL_PAYMENT
        partial_payment_percent = config.PARTIAL_PAYMENT_PERCENT

        if require_partial_payment and self.patient and self.patient.pk:
            unpaid_charge = self.patient.unpaid_consultation_fee_charge
            if unpaid_charge:
                raise ValidationError(
                    f"Patient has a consultation fee charge (ID: {str(unpaid_charge.pk).zfill(6)}) that hasn't been paid up to the required amount ({partial_payment_percent/100:.1%}). Please make sure to fulfill it before creating a new visit."
                )

        date = self.cleaned_data.get("date")
        qs = Visit.objects
        if visit.pk:
            qs = qs.exclude(id=visit.pk)

        if self.patient and date and qs.filter(patient=self.patient, date__date=date):
            raise ValidationError(
                f"There already is a visit for {self.patient.fullname} on { date.strftime("%a %b %d, %Y") }."
            )

        return super().clean()

    class Meta:
        model = Visit
        fields = {"visit_category", "date"}
