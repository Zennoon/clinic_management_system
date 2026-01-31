from django.db import models

from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class Appointment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    scheduled_for = models.DateTimeField()
    reason = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments',
    )
    scheduled_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name='appointments',
    )
    visit = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        related_name='appointments',
    )

    def __str__(self):
        return f"Patient {self.patient.fullname} appointment scheduled for {self.scheduled_for} by {self.scheduled_by.username}"