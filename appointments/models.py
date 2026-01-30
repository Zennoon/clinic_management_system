from django.db import models

from patients.models import Patient
from staff.models import Staff


# Create your models here.
class Appointments(models.Model):
    appointment = models.DateTimeField()
    reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    scheduled_by = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"Appointment: {self.patient.fullname} at {self.appointment} scheduled by {self.scheduled_by.username} for -> {self.reason}"