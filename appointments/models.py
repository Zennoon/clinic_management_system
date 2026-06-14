from django.db import models
from django.utils import timezone

from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class Appointment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    appointment_date = models.DateTimeField()
    reason = models.TextField(blank=True, null=True)
    checked_in = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    doctor = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    visit = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        related_name="appointments",
        null=True,
        blank=True,
    )

    @property
    def is_operational(self):
        return self.is_active and self.visit.is_operational

    def __str__(self):
        return f"Patient {self.patient.fullname} appointment scheduled for {self.appointment_date} by {self.doctor.username}"
