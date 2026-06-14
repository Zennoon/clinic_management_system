from django import forms
from django_enum.forms import EnumChoiceField
from django.core.exceptions import ValidationError

from patients.models import Patient


class PatientForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(
            {"class": "input input-bordered w-full", "placeholder": "John"}
        )
    )
    last_name = forms.CharField(
        widget=forms.TextInput(
            {"class": "input input-bordered w-full", "placeholder": "Doe"}
        )
    )
    date_of_birth = forms.DateTimeField(
        widget=forms.DateInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Date of birth",
                "type": "date",
            }
        )
    )
    sex = EnumChoiceField(
        enum=Patient.SexEnum,
        choices=[(tag.value, tag.label) for tag in Patient.SexEnum],
        required=True,
        widget=forms.Select(
            {
                "class": "select select-bordered",
                "placeholder": "Select the patient's sex",
            }
        ),
    )
    weight = forms.DecimalField(
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Weight in Kg",
            }
        ),
        required=False,
    )
    height = forms.DecimalField(
        widget=forms.NumberInput(
            {"class": "input input-bordered w-full", "placeholder": "Height in cms"}
        ),
        required=False,
    )
    phone = forms.CharField(
        widget=forms.TextInput(
            {"class": "input input-bordered w-full", "placeholder": "+2519********"}
        ),
        required=False,
    )
    region = EnumChoiceField(
        enum=Patient.RegionEnum,
        choices=[(tag.value, tag.label) for tag in Patient.RegionEnum],
        required=True,
        widget=forms.Select(
            {
                "class": "select select-bordered",
                "placeholder": "Select the patient's region",
            }
        ),
    )
    city = forms.CharField(
        widget=forms.TextInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Patient's residing city",
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if self.instance.pk and not self.instance.is_operational:
            msg = "This patient is archived, and cannot be modified. Please contact an admin to get them restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

    def clean(self):
        patient = self.instance
        if patient and not patient.is_operational:
            raise ValidationError("Changes cannot be saved for an archived patient.")

        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        phone = cleaned_data.get("phone")
        qs = Patient.objects
        if self.instance:
            qs = qs.exclude(id=self.instance.pk)
        if (
            first_name
            and last_name
            and phone
            and qs.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
                phone__iexact=phone,
            ).exists()
        ):
            raise ValidationError(
                "There already is a patient with the same first name, last name, and phone number"
            )
        return cleaned_data

    class Meta:
        model = Patient
        fields = {
            "first_name",
            "last_name",
            "date_of_birth",
            "sex",
            "weight",
            "height",
            "phone",
            "region",
            "city",
        }
