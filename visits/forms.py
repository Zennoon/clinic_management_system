from django import forms
from django_enum.forms import EnumChoiceField
from django.utils import timezone

from patients.models import Patient
from visits.models import Visit

class VisitForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        Patient.objects.order_by("first_name"),
        required=True,
        empty_label="Select a patient",
        widget=forms.Select({
            "class": "input input-bordered w-full",
            "placeholder": "John"
        })
    )
    visit_category = EnumChoiceField(
        enum=Visit.VisitCategoryEnum,
        choices=[(tag.value, tag.label) for tag in Visit.VisitCategoryEnum],
        required=True,
        widget=forms.Select({
            "class": "select select-bordered",
            "placeholder": "Select the patient's sex"
        })
    )
    visit_status = EnumChoiceField(
        enum=Visit.VisitStatusEnum,
        choices=[(tag.value, tag.label) for tag in Visit.VisitStatusEnum],
        required=True,
        widget=forms.Select({
            "class": "select select-bordered",
            "placeholder": "Select the patient's sex"
        })
    )
    chief_complaint = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full",
            "placeholder": "Chief Complaint"
        })
    )
    history = forms.CharField(
        widget=forms.Textarea({
            "class": "input input-bordered w-full",
            "placeholder": "History"
        })
    )
    date = forms.DateField(
        initial=timezone.now().date(),
        widget=forms.DateInput({
            "class": "input input-bordered w-full",
            "placeholder": "Date",
            "type": "date"
        })
    )

    class Meta:
        model = Visit
        fields = { "patient", "visit_category", "visit_status", "chief_complaint", "history", "date" }