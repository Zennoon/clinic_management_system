from django import forms
from django.core.exceptions import ValidationError
from django_enum.forms import EnumChoiceField

from lab_requests.models import LabObservation, LabGroup

class LabGroupForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "Name of Test"
        })
    )

    class Meta:
        model = LabGroup
        fields = ["name"]

class LabGroupObservationForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "Name of Observation"
        })
    )
    type = EnumChoiceField(
        enum=LabObservation.ObservationTypeEnum,
        required=True,
        widget=forms.Select(attrs={
            "class": "select select-bordered w-full",
        })
    )
    unit_of_measurement = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "Unit of measurement (eg. mg/dl, mmhg, ...)"
        })
    )
    reference_min = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "Reference Min"
        })
    )
    reference_max = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "Reference Max"
        })
    )
    
    def __init__(self, *args, lab_group=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.lab_group = lab_group
    
    def clean_name(self):
        name = self.cleaned_data["name"]
        if self.lab_group:
            if LabObservation.objects.filter(name=name, lab_group=self.lab_group).exists():
                raise ValidationError(f"There already is an observation with the same name under {self.lab_group.name}")
        return name
    
    class Meta:
        model = LabObservation
        fields = ["name", "type", "unit_of_measurement", "reference_min", "reference_max"]

class LabObservationForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "Name of Observation"
        })
    )
    lab_group = forms.ModelChoiceField(
        queryset=LabGroup.objects.order_by("name"),
        required=True,
        widget=forms.Select({
            "class": "input input-bordered w-full",
            "placeholder": "Select a test"
        })
    )
    type = EnumChoiceField(
        enum=LabObservation.ObservationTypeEnum,
        required=True,
        widget=forms.Select(attrs={
            "class": "select select-bordered w-full",
        })
    )
    unit_of_measurement = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "Unit of measurement (eg. mg/dl, mmhg, ...)"
        })
    )
    reference_min = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "Reference Min"
        })
    )
    reference_max = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "input input-bordered w-full",
            "placeholder": "Reference Max"
        })
    )
    
    def clean_name(self):
        name = self.cleaned_data.get("name")
        lab_group = self.cleaned_data.get("lab_group")
        if lab_group:
            if LabObservation.objects.filter(name=name, lab_group=lab_group).exists():
                raise ValidationError(f"There already is an observation with the same name under {lab_group.name}")
        return name

    class Meta:
        model = LabObservation
        fields = ["name", "type", "unit_of_measurement", "reference_min", "reference_max", "lab_group"]