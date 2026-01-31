from django.db import models

from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class PhysicalExam(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    heent = models.TextField(blank=True, help_text="Head, Eye, Ear, Nose, and Throat")
    chest = models.TextField(blank=True, help_text="Chest")
    cardiovascular = models.TextField(blank=True, help_text="Cardiovascular")
    abdomen = models.TextField(blank=True, help_text="Abdomen")
    musculoskeletal = models.TextField(blank=True, help_text="Musculoskeletal")
    genitourinary = models.TextField(blank=True, help_text="Genitourinary")
    cns = models.TextField(blank=True, help_text="Central nervous system")
    miscellaneous = models.TextField(blank=True, help_text="Miscellaneous")
    is_active = models.BooleanField(default=True)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="physical_exams",
    )
    examined_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="physical_exams_examined",
    )
    visit = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        null=True,
        related_name="physical_exams"
    )

    def __str__(self):
        return f"Patient {self.patient.fullname} physical exam: {self.examined_by.username}"