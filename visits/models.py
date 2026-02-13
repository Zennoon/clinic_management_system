from decimal import Decimal

from django.db import models
from django.db.models import Sum, Value, F
from django.db.models.functions import Coalesce
from django_enum import EnumField

from patients.models import Patient
from staff.models import Staff


# Create your models here.
class VisitQuerySet(models.QuerySet):
    def with_financials(self):
        return self.annotate(
            total_charged=Coalesce(Sum("charges__amount"), Value(Decimal("0.00"))),
            total_paid=Coalesce(Sum("payments__amount"), Value(Decimal("0.00"))),
        ).annotate(
            balance=F("total_charged") - F("total_paid"),
        )

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
        AWAITING_REVIEW = 'REV', 'Awaiting Results Review'
        COMPLETED = 'FIN', 'Visit Finished'
        CANCELLED = 'CAN', 'Visit Cancelled'
        OTHER = 'OTH', 'Other'


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    visit_category = EnumField(VisitCategoryEnum)
    visit_status = EnumField(VisitStatusEnum, editable=False)
    chief_complaint = models.TextField(blank=True)
    current_status_since = models.DateTimeField(auto_now_add=True)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='visits',
    )

    objects = VisitQuerySet.as_manager()

    @property
    def total_charged(self):
        return self.charges.aggregate(
            total=Sum("amount")
        )['total'] or Decimal("0.00")

    @property
    def total_paid(self):
        return self.payments.aggregate(
            total=Sum("amount")
        )['total'] or Decimal("0.00")

    @property
    def balance(self):
        return self.total_charged - self.total_paid

    def get_valid_transitions(self):
        return {
            self.VisitStatusEnum.AWAITING_PAYMENT: self.VisitStatusEnum.AWAITING_VITALS,
            self.VisitStatusEnum.AWAITING_VITALS: self.VisitStatusEnum.AWAITING_CONSULTATION,
            self.VisitStatusEnum.AWAITING_CONSULTATION: self.VisitStatusEnum.AWAITING_LAB_PAYMENT,
            self.VisitStatusEnum.AWAITING_LAB_PAYMENT: self.VisitStatusEnum.AWAITING_LAB_SAMPLE,
            self.VisitStatusEnum.AWAITING_LAB_SAMPLE: self.VisitStatusEnum.AWAITING_REVIEW,
            self.VisitStatusEnum.AWAITING_REVIEW: self.VisitStatusEnum.COMPLETED,
        }

    def advance_status(self, new_status):
        valid_transitions = self.get_valid_transitions()

        if new_status == self.VisitStatusEnum.CANCELLED:
             if self.visit_status != self.VisitStatusEnum.COMPLETED:
                 self.visit_status = new_status
        elif new_status == valid_transitions[self.visit_status]:
            self.visit_status = new_status

    def transition_to_next_status(self):
        valid_transitions = self.get_valid_transitions()
        if self.visit_status != self.VisitStatusEnum.COMPLETED:
            self.visit_status = valid_transitions[self.visit_status]

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