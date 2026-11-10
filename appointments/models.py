from django.db import models
from django.utils import timezone
from django_enum import EnumField
from django.db.models import Q, BooleanField, ExpressionWrapper

from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class AppointmentQuerySet(models.QuerySet):
    def with_operational(self):
        return self.annotate(
            is_operational_annotated=ExpressionWrapper(
                Q(is_active=True) & Q(patient__is_active=True),
                output_field=BooleanField(),
            )
        )


class AppointmentManager(models.Manager):
    def get_queryset(self):
        return AppointmentQuerySet(self.model, using=self._db).with_operational()


class Appointment(models.Model):
    class AppointmentStatus(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        CANCELLED = "CANCELLED", "Cancelled"
        MISSED = "MISSED", "Missed"
        DELAYED = "DELAYED", "Delayed"
        COMPLETED = "COMPLETED", "Completed"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    appointment_date = models.DateTimeField()
    reason = models.TextField(blank=True, null=True)
    appointment_status = EnumField(
        AppointmentStatus, default=AppointmentStatus.SCHEDULED
    )

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
    
    objects = AppointmentManager()

    def derive_appointment_status(self):
        if self.appointment_status == self.AppointmentStatus.SCHEDULED:
            if self.appointment_date.date() < timezone.now().date():
                return Appointment.AppointmentStatus.MISSED
        return self.appointment_status

    def update_appointment_status(self):
        self.appointment_status = self.derive_appointment_status()
        self.save()

    @property
    def is_operational(self):
        return self.is_active and self.patient.is_operational
    
    @property
    def is_scheduled(self):
        return self.derive_appointment_status() == Appointment.AppointmentStatus.SCHEDULED
    
    @property
    def is_completed(self):
        return self.derive_appointment_status() == Appointment.AppointmentStatus.COMPLETED

    def __str__(self):
        return f"Patient {self.patient.fullname} appointment scheduled for {self.appointment_date} by {self.doctor.username} - {self.appointment_status.label}"
