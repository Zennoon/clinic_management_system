from django.db import models
from django_enum import EnumField

from patients.models import Patient
from staff.models import Staff


# Create your models here.
class Visit(models.Model):
    class VisitCategoryEnum(models.TextChoices):
        HISTORY_AND_PHYSICAL = 'HISTORY_AND_PHYSICAL', 'History and Physical'
        MEDICAL_CERTIFICATE = 'MEDICAL_CERTIFICATE', 'Medical Certificate'
        PROGRESS_NOTE = 'PROGRESS_NOTE', 'Progress Note'
        OTHER = 'OTHER', 'Other'
    class VisitStatusEnum(models.TextChoices):
        AWAITING_PAYMENT = 'PAY', 'Awaiting Visit Fee'
        AWAITING_VITALS = 'VIT', 'In Queue for Vitals'
        AWAITING_CONSULTATION = 'CON', 'Awaiting Doctor Consultation'
        IN_CONSULTATION = 'INC', 'With Doctor'
        AWAITING_LAB_PAYMENT = 'LBP', 'Awaiting Lab Payment'
        AWAITING_LAB_SAMPLE = 'LBS', 'Awaiting Lab Sample'
        AWAITING_LAB_RESULTS = 'LBR', 'Awaiting Lab Results'
        AWAITING_REVIEW = 'REV', 'Awaiting Results Review'
        COMPLETED = 'FIN', 'Visit Finished'
        CANCELLED = 'CAN', 'Visit Cancelled'
        OTHER = 'OTH', 'Other'


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    visit_category = EnumField(VisitCategoryEnum)
    visit_status = EnumField(VisitStatusEnum)
    chief_complaint = models.TextField(blank=True)
    current_status_since = models.DateTimeField(auto_now_add=True)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='visits',
    )

    def __str__(self):
        return f"{self.patient.fullname} - {self.visit_status.label}"

class VisitStatusLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = EnumField(Visit.VisitStatusEnum)
    changed_at = models.DateTimeField(auto_now=True)

    visit = models.ForeignKey(
        Visit,
        on_delete=models.CASCADE,
        related_name='status_history',
    )
    changed_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        null=True,
    )

    class Meta:
        ordering = ['-changed_at']