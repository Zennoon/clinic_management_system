from django.db import models
from django_enum import EnumField

from lab_requests.models import LabRequest, LabTest, LabObservation
from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class LabRequestResult(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

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
        return f"Patient {self.visit.patient.fullname} lab result {self.id} for lab request {self.lab_request.id} reported by {self.reported_by.username}"

class LabTestResult(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    lab_test = models.ForeignKey(
        LabTest,
        on_delete=models.PROTECT,
    )
    lab_request_result = models.ForeignKey(
        LabRequestResult,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return f"Lab Test Result {self.lab_test.name}"

class ObservationResult(models.Model):
    class CategoricalEnum(models.TextChoices):
        POSITIVE = "+", "Positive"
        NEGATIVE = "-", "Negative"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    value_numeric = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    value_categorical = EnumField(CategoricalEnum)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    observation = models.ForeignKey(
        LabObservation,
        on_delete=models.PROTECT,
        related_name="results"
    )
    reported_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="results_reported"
    )
    lab_test_result = models.ForeignKey(
        LabTestResult,
        on_delete=models.PROTECT,
        related_name="observation_results"
    )

    @property
    def result_display(self):
        if self.observation.result_type == "NUMERIC":
            return f"{self.value_numeric} {self.observation.unit_of_measurement}"
        return self.value_categorical

    @property
    def is_abnormal(self):
        if self.observation.result_type == "NUMERIC":
            return not (self.observation.reference_min <= self.value_numeric <= self.observation.reference_max)
        return self.value_categorical == ObservationResult.CategoricalEnum.POSITIVE

    def __str__(self):
        return f"Patient {self.lab_result.visit.patient.fullname} test {self.observation.name} result: {self.result_display} | Abnormal: {self.is_abnormal}"