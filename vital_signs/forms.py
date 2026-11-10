from django import forms
from django.utils import timezone
from django_enum.forms import EnumChoiceField
from dynamic_forms import DynamicField, DynamicFormMixin

from patients.models import Patient
from visits.models import Visit
from vital_signs.models import VitalSign


class VitalSignsForm(DynamicFormMixin, forms.ModelForm):
    def initial_patient(self=None):
        if self and self.instance.pk:
            return self.instance.visit.patient
        return (
            Patient.objects.exclude(is_operational_annotated=False)
            .order_by("first_name")
            .first()
        )

    def visit_choices(self):
        patient = self["patient"].value()
        return (
            Visit.objects.exclude(is_operational_annotated=False)
            .filter(patient=patient)
            .order_by("-date")
        )

    def initial_visit(self):
        if self.instance.pk:
            return self.instance.visit

        patient = self["patient"].value()
        return (
            Visit.objects.exclude(is_operational_annotated=False)
            .filter(patient=patient)
            .order_by("-date")
            .first()
        )

    patient = forms.ModelChoiceField(
        Patient.objects.exclude(is_operational_annotated=False).order_by("first_name"),
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
    bp_systolic = forms.IntegerField(
        min_value=0.0,
        max_value=300,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Systolic Pressure",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    bp_diastolic = forms.IntegerField(
        min_value=0.0,
        max_value=300,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Diastolic Pressure",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    pulse_rate = forms.IntegerField(
        min_value=0.0,
        max_value=300,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Heart Pulse Rate",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    respiratory_rate = forms.IntegerField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Respiratory Rate",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    temperature = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Temperature",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    temperature_unit = EnumChoiceField(
        enum=VitalSign.TemperatureUnitEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            VitalSign.TemperatureUnitEnum,
        ),
        required=False,
        initial=VitalSign.TemperatureUnitEnum.CELSIUS,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Temperature Unit"}
        ),
    )
    weight = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Weight",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    weight_unit = EnumChoiceField(
        enum=VitalSign.WeightUnitEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            VitalSign.WeightUnitEnum,
        ),
        required=False,
        initial=VitalSign.WeightUnitEnum.KILOGRAMS,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Weight Unit"}
        ),
    )
    height = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Height",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    height_unit = EnumChoiceField(
        enum=VitalSign.HeightUnitEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            VitalSign.HeightUnitEnum,
        ),
        required=False,
        initial=VitalSign.HeightUnitEnum.CENTIMETERS,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Height Unit"}
        ),
    )
    spo2 = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Spo2",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Notes",
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

    def clean_patient(self):
        patient = self.cleaned_data.get("patient")
        if patient and not patient.is_operational:
            self.add_error(
                "patient",
                "This patient is archived, and cannot be modified. Please contact an admin to get them restored.",
            )
        
        if patient and patient.unpaid_consultation_fee_charge:
            self.add_error(
                "patient",
                "This patient has an unpaid consultation fee. Please direct them to the reception desk."
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
            self.add_error(
                "date", "A vital sign recording cannot be set for future dates,"
            )
        if visit and date.date() < visit.date.date():
            self.add_error("visit", f"The visit took place in {visit.date.date()}.")
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
        model = VitalSign
        fields = [
            "visit",
            "bp_systolic",
            "bp_diastolic",
            "pulse_rate",
            "respiratory_rate",
            "temperature",
            "temperature_unit",
            "weight",
            "weight_unit",
            "height",
            "height_unit",
            "spo2",
            "notes",
            "date",
        ]


class VisitVitalSignsForm(forms.ModelForm):
    bp_systolic = forms.IntegerField(
        min_value=0.0,
        max_value=300,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Systolic Pressure",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    bp_diastolic = forms.IntegerField(
        min_value=0.0,
        max_value=300,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Diastolic Pressure",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    pulse_rate = forms.IntegerField(
        min_value=0.0,
        max_value=300,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Heart Pulse Rate",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    respiratory_rate = forms.IntegerField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Respiratory Rate",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    temperature = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Temperature",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    temperature_unit = EnumChoiceField(
        enum=VitalSign.TemperatureUnitEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            VitalSign.TemperatureUnitEnum,
        ),
        required=False,
        initial=VitalSign.TemperatureUnitEnum.CELSIUS,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Temperature Unit"}
        ),
    )
    weight = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Weight",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    weight_unit = EnumChoiceField(
        enum=VitalSign.WeightUnitEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            VitalSign.WeightUnitEnum,
        ),
        required=False,
        initial=VitalSign.WeightUnitEnum.KILOGRAMS,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Weight Unit"}
        ),
    )
    height = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Height",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    height_unit = EnumChoiceField(
        enum=VitalSign.HeightUnitEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            VitalSign.HeightUnitEnum,
        ),
        required=False,
        initial=VitalSign.HeightUnitEnum.CENTIMETERS,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Height Unit"}
        ),
    )
    spo2 = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Spo2",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Notes",
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

    def __init__(self, *args, visit=None, **kwargs):
        self.visit = visit
        super().__init__(*args, **kwargs)
        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}
        
        if visit and not visit.is_operational:
            msg = "This visit is archived, and cannot be modified. Please contact an admin to get it restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True
        
        if visit and visit.patient.unpaid_consultation_fee_charge:
            msg = "This patient has an unpaid consultation fee. Please direct them to the reception desk.."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True
        

    def clean_date(self):
        date = self.cleaned_data.get("date")
        visit = self.visit
        if date.date() > timezone.now().date():
            self.add_error(
                "date", "A vital sign recording cannot be set for future dates,"
            )
        if visit and date.date() < visit.date.date():
            self.add_error("visit", f"The visit took place in {visit.date.date()}.")
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
        model = VitalSign
        fields = [
            "bp_systolic",
            "bp_diastolic",
            "pulse_rate",
            "respiratory_rate",
            "temperature",
            "temperature_unit",
            "weight",
            "weight_unit",
            "height",
            "height_unit",
            "spo2",
            "notes",
            "date",
        ]


class PatientVitalSignsForm(DynamicFormMixin, forms.ModelForm):
    def visit_choices(self=None):
        return (
            Visit.objects.exclude(is_operational_annotated=False)
            .filter(patient=self.patient)
            .order_by("-date")
        )

    def initial_visit(self=None):
        if self.instance.pk:
            return self.instance.visit
        return (
            Visit.objects.exclude(is_operational_annotated=False)
            .filter(patient=self.patient)
            .order_by("-date")
            .first()
        )

    visit = DynamicField(
        forms.ModelChoiceField,
        queryset=visit_choices,
        initial=initial_visit,
        required=True,
    )
    bp_systolic = forms.IntegerField(
        min_value=0.0,
        max_value=300,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Systolic Pressure",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    bp_diastolic = forms.IntegerField(
        min_value=0.0,
        max_value=300,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Diastolic Pressure",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    pulse_rate = forms.IntegerField(
        min_value=0.0,
        max_value=300,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Heart Pulse Rate",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    respiratory_rate = forms.IntegerField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Respiratory Rate",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    temperature = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Temperature",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    temperature_unit = EnumChoiceField(
        enum=VitalSign.TemperatureUnitEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            VitalSign.TemperatureUnitEnum,
        ),
        required=False,
        initial=VitalSign.TemperatureUnitEnum.CELSIUS,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Temperature Unit"}
        ),
    )
    weight = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Weight",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    weight_unit = EnumChoiceField(
        enum=VitalSign.WeightUnitEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            VitalSign.WeightUnitEnum,
        ),
        required=False,
        initial=VitalSign.WeightUnitEnum.KILOGRAMS,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Weight Unit"}
        ),
    )
    height = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Height",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    height_unit = EnumChoiceField(
        enum=VitalSign.HeightUnitEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            VitalSign.HeightUnitEnum,
        ),
        required=False,
        initial=VitalSign.HeightUnitEnum.CENTIMETERS,
        widget=forms.Select(
            {"class": "select select-bordered", "placeholder": "Height Unit"}
        ),
    )
    spo2 = forms.DecimalField(
        min_value=0.0,
        required=False,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Spo2",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Notes",
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
        
        if patient and not patient.is_operational:
            msg = "This patient is archived, and cannot be modified. Please contact an admin to get them restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True
        
        if patient and patient.unpaid_consultation_fee_charge:
            msg = "This patient has an unpaid consultation fee. Please direct them to the reception desk."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

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
            self.add_error(
                "date", "A vital sign recording cannot be set for future dates,"
            )
        if visit and date.date() < visit.date.date():
            self.add_error("visit", f"The visit took place in {visit.date.date()}.")
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
        model = VitalSign
        fields = [
            "visit",
            "bp_systolic",
            "bp_diastolic",
            "pulse_rate",
            "respiratory_rate",
            "temperature",
            "temperature_unit",
            "weight",
            "weight_unit",
            "height",
            "height_unit",
            "spo2",
            "notes",
            "date",
        ]
