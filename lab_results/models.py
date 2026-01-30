from django.db import models
from django_enum import EnumField

from lab_requests.models import Test
from patients.models import Patient
from staff.models import Staff


# Create your models here.
class LabResult(models.Model):
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="lab_results"
    )
    performed_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_lab_results"
    )

    def __str__(self):
        return f"Lab result: {self.patient.fullname} performed by {self.performed_by.username} at {self.created_at}"

class Result(models.Model):
    class CategoricalEnum(models.TextChoices):
        POSITIVE = 'positive'
        NEGATIVE = 'negative'

    value_numeric = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    value_categorical = EnumField(CategoricalEnum)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="results")
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
    )
    performed_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_results"
    )
    lab_result = models.ForeignKey(
        LabResult,
        on_delete=models.CASCADE,
        related_name="results"
    )

    @property
    def result(self):
        if self.test.test_type.value == "NUMERIC":
            return f"{self.value_numeric} {self.test.unit_of_measurement}"
        return self.value_categorical

    @property
    def is_abnormal(self):
        if self.test.test_type.value == "NUMERIC":
            return not (self.test.reference_min <= self.value_numeric <= self.test.reference_max)
        return self.value_categorical == self.CategoricalEnum.POSITIVE

    def __str__(self):
        return f"{self.test.name} result: {str(self.value_numeric) + " " + self.test.unit_of_measurement if self.test.test_type.value == "NUMERIC" else self.value_categorical }\nAbnormal: {self.is_abnormal}"