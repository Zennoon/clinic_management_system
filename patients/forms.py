from django import forms
from django_enum.forms import EnumChoiceField
from django.core.exceptions import ValidationError

from patients.models import Patient

class NewPatientForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "John"
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "Doe"
        })
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput({
            "class": "input input-bordered w-full",
            "placeholder": "Date of birth",
            "type": "date"
        })
    )
    sex = EnumChoiceField(
        enum=Patient.SexEnum,
        choices=[(tag.value, tag.label) for tag in Patient.SexEnum],
        required=True,
        widget=forms.Select({
            "class": "select select-bordered",
            "placeholder": "Select the patient's sex"
        })
        
    )
    weight = forms.DecimalField(
        widget=forms.NumberInput({
            "class": "input input-bordered w-full",
            "placeholder": "Weight in Kg",
        }),
        required=False
    )
    height = forms.DecimalField(
        widget=forms.NumberInput({
            "class": "input input-bordered w-full",
            "placeholder": "Height in cms"
        }),
        required=False
    )
    phone = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "+2519********"
        }),
        required=False
    )
    region = EnumChoiceField(
        enum=Patient.RegionEnum,
        choices=[(tag.value, tag.label) for tag in Patient.RegionEnum],
        required=True,
        widget=forms.Select({
            "class": "select select-bordered",
            "placeholder": "Select the patient's sex"
        }),
    )
    city = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "Patient's residing city"
        })
    )

    def clean(self):
        first_name = self.cleaned_data.get("first_name")
        last_name = self.cleaned_data.get("last_name")
        phone = self.cleaned_data.get("phone")
        if Patient.objects.filter(first_name=first_name, last_name=last_name, phone=phone).exists():
            raise ValidationError("There already is a patient with the same first name, last name, and phone number")
        return super().clean()
    
    class Meta:
        model = Patient
        fields = { "first_name", "last_name", "date_of_birth", "sex", "weight", "height", "phone", "region", "city" }

class UpdatePatientForm(forms.ModelForm):
    id = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "readonly": "true"
        }),
    )
    first_name = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "John"
        })
    )
    last_name = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "Doe"
        })
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput({
            "class": "input input-bordered w-full",
            "placeholder": "Date of birth",
            "type": "date"
        })
    )
    sex = EnumChoiceField(
        enum=Patient.SexEnum,
        choices=[(tag.value, tag.label) for tag in Patient.SexEnum],
        required=True,
        widget=forms.Select({
            "class": "select select-bordered",
            "placeholder": "Select the patient's sex"
        })
        
    )
    weight = forms.DecimalField(
        widget=forms.NumberInput({
            "class": "input input-bordered w-full",
            "placeholder": "Weight in Kg",
        }),
        required=False
    )
    height = forms.DecimalField(
        widget=forms.NumberInput({
            "class": "input input-bordered w-full",
            "placeholder": "Height in cms"
        }),
        required=False
    )
    phone = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "+2519********"
        }),
        required=False
    )
    region = EnumChoiceField(
        enum=Patient.RegionEnum,
        choices=[(tag.value, tag.label) for tag in Patient.RegionEnum],
        required=True,
        widget=forms.Select({
            "class": "select select-bordered",
            "placeholder": "Select the patient's sex"
        }),
    )
    city = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "Patient's residing city"
        })
    )
    
    def clean(self):
        first_name = self.cleaned_data.get("first_name")
        last_name = self.cleaned_data.get("last_name")
        phone = self.cleaned_data.get("phone")
        if Patient.objects.exclude(id=self.cleaned_data["id"]).filter(first_name=first_name, last_name=last_name, phone=phone).exists():
            raise ValidationError("There already is a patient with the same first name, last name, and phone number")
        return super().clean()
    
    class Meta:
        model = Patient
        fields = { "id", "first_name", "last_name", "date_of_birth", "sex", "weight", "height", "phone", "region", "city" }