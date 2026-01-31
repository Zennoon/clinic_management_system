from django.db import models
from django_enum import EnumField

from lab_requests.models import LabRequest, Test
from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class LabResult(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="lab_results"
    )
    lab_request = models.ForeignKey(
        LabRequest,
        on_delete=models.PROTECT,
        related_name="lab_results"
    )
    reported_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="lab_results_reported"
    )
    visit = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        related_name="lab_results",
    )

    def __str__(self):
        return f"Patient {self.patient.fullname} lab result {self.id} for lab request {self.lab_request.id} reported by {self.reported_by.username}"

class Result(models.Model):
    class CategoricalEnum(models.TextChoices):
        POSITIVE = "+", "Positive"
        NEGATIVE = "-", "Negative"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    value_numeric = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    value_categorical = EnumField(CategoricalEnum)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    test = models.ForeignKey(
        Test,
        on_delete=models.PROTECT,
        related_name="results"
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="results"
    )
    reported_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="results_reported"
    )
    lab_result = models.ForeignKey(
        LabResult,
        on_delete=models.PROTECT,
        related_name="results"
    )

    @property
    def result_display(self):
        if self.test.test_type == "NUMERIC":
            return f"{self.value_numeric} {self.test.unit_of_measurement}"
        return self.value_categorical

    @property
    def is_abnormal(self):
        if self.test.test_type == "NUMERIC":
            return not (self.test.reference_min <= self.value_numeric <= self.test.reference_max)
        return self.value_categorical == Result.CategoricalEnum.POSITIVE

    def __str__(self):
        return f"Patient {self.patient.fullname} test {self.test.name} result: {self.result_display} | Abnormal: {self.is_abnormal}"