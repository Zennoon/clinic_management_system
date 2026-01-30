from django.db import models

from patients.models import Patient
from staff.models import Staff


# Create your models here.
class PhysicalExam(models.Model):
    heent = models.TextField(max_length=500, blank=True, null=True)
    chest = models.TextField(max_length=500, blank=True, null=True)
    cardiovascular = models.TextField(max_length=500, blank=True, null=True)
    abdomen = models.TextField(max_length=500, blank=True, null=True)
    musculoskeletal = models.TextField(max_length=500, blank=True, null=True)
    genitourinary = models.TextField(max_length=500, blank=True, null=True)
    cns = models.TextField(max_length=500, blank=True, null=True)
    miscellaneous = models.TextField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='physical_exams',
    )

    performed_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_physical_exams',
    )