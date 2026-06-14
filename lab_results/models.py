from django.db import models
from django_enum import EnumField
from django.utils import timezone

from lab_requests.models import LabRequest, LabObservation
from staff.models import Staff


# Create your models here.
class LabResult(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    lab_request = models.ForeignKey(
        LabRequest, on_delete=models.PROTECT, related_name="lab_results"
    )
    reported_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="lab_results_reported"
    )

    @property
    def is_operational(self):
        return self.is_active and self.lab_request.is_operational

    def __str__(self):
        return f"Patient {self.visit.patient.fullname} lab result {self.id} for lab request {self.lab_request.id} reported by {self.reported_by.username}"


class LabObservationResult(models.Model):
    class CategoricalEnum(models.TextChoices):
        POSITIVE = "+", "Positive"
        NEGATIVE = "-", "Negative"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    value_numeric = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    value_categorical = EnumField(CategoricalEnum, null=True)

    date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    lab_result = models.ForeignKey(
        LabResult, on_delete=models.PROTECT, related_name="lab_observation_results"
    )
    lab_observation = models.ForeignKey(
        LabObservation, on_delete=models.PROTECT, related_name="results"
    )
    reported_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="lab_observation_results_reported"
    )

    @property
    def is_operational(self):
        return self.is_active and self.lab_result.is_operational

    @property
    def display_result(self):
        if self.lab_observation.type == LabObservation.ObservationTypeEnum.NUMERICAL:
            return f"{self.value_numeric} {self.lab_observation.unit_of_measurement}"
        return self.value_categorical.label if self.value_categorical else None

    @property
    def is_abnormal(self):
        if self.lab_observation.type == LabObservation.ObservationTypeEnum.NUMERICAL:
            return not (
                self.lab_observation.reference_min
                <= self.value_numeric
                <= self.lab_observation.reference_max
            )
        return None

    def __str__(self):
        return f"Patient {self.lab_result.lab_request.visit.patient.fullname} observation {self.lab_observation.name} result: {self.display_result} | Abnormal: {self.is_abnormal}"
