from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_enum.forms import EnumChoiceField
from dynamic_forms import DynamicField, DynamicFormMixin

from charges.models import Charge
from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


class ChargeForm(DynamicFormMixin, forms.ModelForm):
    def initial_patient(self=None):
        if self and self.instance.pk:
            return self.instance.visit.patient
        return Patient.objects.exclude(is_active=False).order_by("first_name").first()

    def visit_choices(self):
        patient = self["patient"].value()
        return (
            Visit.objects.exclude(is_active=False)
            .filter(patient=patient)
            .order_by("-date")
        )

    def initial_visit(self):
        if self.instance.pk:
            return self.instance.visit
        patient = self["patient"].value()
        return (
            Visit.objects.exclude(is_active=False)
            .filter(patient=patient)
            .order_by("-date")
            .first()
        )

    patient = forms.ModelChoiceField(
        Patient.objects.exclude(is_active=False).order_by("first_name"),
        required=True,
        empty_label="Select a patient",
        initial=initial_patient,
        widget=forms.Select(
            {
                "class": "select select-bordered w-full",
            }
        ),
    )
    visit = DynamicField(
        forms.ModelChoiceField,
        queryset=visit_choices,
        initial=initial_visit,
        required=True,
    )
    charge_type = EnumChoiceField(
        enum=Charge.ChargeTypeEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            Charge.miscelaneous_charge_types(),
        ),
        required=True,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Select the charge type"}
        ),
    ) 
    description = forms.CharField(
        widget=forms.Textarea(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Optional notes concerning the charge",
            }
        ),
        required=False,
    )
    amount = forms.DecimalField(
        min_value=0.0,
        required=True,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Amount",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
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

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if self.instance.pk:
            msg = "Please use the update form for updates."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        if self.user and self.user.role == Staff.RoleEnum.ADMIN:
            self.fields.get("charge_type").choices = [
                (tag.value, tag.label) for tag in Charge.ChargeTypeEnum
            ]

    def clean_patient(self):
        patient = self.cleaned_data.get("patient")
        if patient and not patient.is_operational:
            self.add_error(
                "patient",
                "This patient is archived, and cannot be modified. Please contact an admin to get them restored.",
            )

        return patient

    def clean_visit(self):
        visit = self.cleaned_data.get("visit")
        if visit and not visit.is_operational:
            self.add_error(
                "visit",
                "This visit is archived, and cannot be modified. Please contact an admin to get it restored.",
            )

        return visit

    def clean_date(self):
        date = self.cleaned_data.get("date")
        visit = self.cleaned_data.get("visit")
        if date.date() > timezone.now().date():
            raise ValidationError(
                "Charges cannot be scheduled for future dates.",
            )
        if visit and date.date() < visit.date.date():
            raise ValidationError(
                f"The visit took place in {visit.date.date()}.",
            )
        source_date = timezone.now()
        if source_date:
            date = date.replace(
                hour=source_date.hour,
                minute=source_date.minute,
                second=source_date.second,
                microsecond=source_date.microsecond,
            )
        return date

    class Meta:
        model = Charge
        fields = [
            "visit",
            "charge_type",
            "description",
            "amount",
            "date",
        ]


class VisitChargeForm(DynamicFormMixin, forms.ModelForm):
    charge_type = EnumChoiceField(
        enum=Charge.ChargeTypeEnum,
        required=True,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Select the charge type"}
        ),
    )
    description = forms.CharField(
        widget=forms.Textarea(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Optional notes concerning the charge",
            }
        ),
        required=False,
    )
    amount = forms.DecimalField(
        min_value=1.0,
        required=True,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Amount",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
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

    def __init__(self, *args, visit=None, user=None, **kwargs):
        self.user = user
        self.visit = visit
        super().__init__(*args, **kwargs)

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if self.instance.pk:
            msg = "Please use the update form for updates."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        if self.user and self.user.role == Staff.RoleEnum.ADMIN:
            self.fields.get("charge_type").choices = [
                (tag.value, tag.label) for tag in Charge.ChargeTypeEnum
            ]
        else:
            self.fields.get("charge_type").choices = [
                (tag.value, tag.label) for tag in Charge.miscelaneous_charge_types()
            ]

        if visit and not visit.is_operational:
            msg = "This visit is archived, and cannot be modified. Please contact an admin to get it restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date.date() > timezone.now().date():
            raise ValidationError(
                "Charges cannot be scheduled for future dates.",
            )
        if self.visit and date.date() < self.visit.date.date():
            raise ValidationError(
                f"The visit took place in {self.visit.date.date()}.",
            )
        source_date = timezone.now()
        if source_date:
            date = date.replace(
                hour=source_date.hour,
                minute=source_date.minute,
                second=source_date.second,
                microsecond=source_date.microsecond,
            )
        return date

    class Meta:
        model = Charge
        fields = {"charge_type", "description", "amount", "date"}


class PatientChargeForm(DynamicFormMixin, forms.ModelForm):
    visit = forms.ModelChoiceField(
        required=True,
        queryset=Visit.objects.exclude(is_active=False).order_by("-date"),
        empty_label="Select a visit",
        widget=forms.Select(
            {"class": "input input-bordered w-full", "placeholder": "Select a visit"}
        ),
    )
    charge_type = EnumChoiceField(
        enum=Charge.ChargeTypeEnum,
        required=True,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Select the charge type"}
        ),
    )
    description = forms.CharField(
        widget=forms.Textarea(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Optional notes concerning the charge",
            }
        ),
        required=False,
    )
    amount = forms.DecimalField(
        min_value=1.0,
        required=True,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Amount",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
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

    def __init__(self, *args, patient=None, user=None, **kwargs):
        self.patient = patient
        self.user = user
        super().__init__(*args, **kwargs)

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if self.instance.pk:
            self.add_error(None, "Please use the update form for updates")

        if self.patient and not self.patient.is_operational:
            msg = "This patient is archived, and cannot be modified. Please contact an admin to get them restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True

        if self.user and self.user.role == Staff.RoleEnum.ADMIN:
            self.fields.get("charge_type").choices = [
                (tag.value, tag.label) for tag in Charge.ChargeTypeEnum
            ]
        else:
            self.fields.get("charge_type").choices = [
                (tag.value, tag.label) for tag in Charge.miscelaneous_charge_types()
            ]

        self.fields.get("visit").queryset = (
            Visit.objects.exclude(is_active=False)
            .filter(patient=self.patient)
            .order_by("-date")
        )

    def clean_visit(self):
        visit = self.cleaned_data.get("visit")
        if visit and not visit.is_operational:
            self.add_error(
                "visit",
                "This visit is archived, and cannot be modified. Please contact an admin to get it restored.",
            )

        return visit

    def clean_date(self):
        date = self.cleaned_data.get("date")
        visit = self.cleaned_data.get("visit")

        if date.date() > timezone.now().date():
            raise ValidationError(
                "Charges cannot be scheduled for future dates.",
            )
        if visit and date.date() < visit.date.date():
            raise ValidationError(
                f"The visit took place in {visit.date.date()}.",
            )
        source_date = timezone.now()
        if source_date:
            date = date.replace(
                hour=source_date.hour,
                minute=source_date.minute,
                second=source_date.second,
                microsecond=source_date.microsecond,
            )
        return date

    class Meta:
        model = Charge
        fields = ["visit", "charge_type", "description", "amount", "date"]


class UpdateChargeForm(forms.ModelForm):
    charge_type = EnumChoiceField(
        enum=Charge.ChargeTypeEnum,
        required=True,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Select the charge type"}
        ),
    )
    description = forms.CharField(
        widget=forms.Textarea(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Optional notes concerning the charge",
            }
        ),
        required=False,
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

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if not self.instance.pk:
            self.add_error(
                None, "Please use one of the generic charge forms for new charges"
            )

        if not self.instance.is_operational:
            msg = "This charge is archived, and cannot be modified. Please contact an admin to get it restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True

        self.fields.get("charge_type").choices = [
            (tag.value, tag.label) for tag in Charge.ChargeTypeEnum
        ]

        if self.instance.charge_type not in Charge.miscelaneous_charge_types() and not (
            user and user.role == Staff.RoleEnum.ADMIN
        ):

            self.add_error(
                None,
                "You are not authorized to modify system generated charges. Please contact an admin with your request.",
            )
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        if not (self.user and self.user.role == Staff.RoleEnum.ADMIN):
            self.fields.get("charge_type").choices = [
                (tag.value, tag.label) for tag in Charge.miscelaneous_charge_types()
            ]

    def clean_date(self):
        date = self.cleaned_data.get("date")
        visit = self.cleaned_data.get("visit")

        if date.date() > timezone.now().date():
            raise ValidationError(
                "Charges cannot be scheduled for future dates.",
            )
        if visit and date.date() < visit.date.date():
            raise ValidationError(
                f"The visit took place in {visit.date.date()}.",
            )
        source_date = self.instance.date if self.instance else timezone.now()
        if source_date:
            date = date.replace(
                hour=source_date.hour,
                minute=source_date.minute,
                second=source_date.second,
                microsecond=source_date.microsecond,
            )
        return date

    class Meta:
        model = Charge
        fields = ["charge_type", "description", "date"]
