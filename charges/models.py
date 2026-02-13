from django.db import models
from django_enum import EnumField

from staff.models import Staff
from visits.models import Visit


# Create your models here.
class Charge(models.Model):
    class ChargeStatusEnum(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CANCELLED = 'CANCELLED', 'Cancelled'
        WAIVED = 'WAIVED', 'Wait'
    class ChargeTypeEnum(models.TextChoices):
        CONSULTATION = 'CONSULTATION', 'Consultation'
        LABORATORY = 'LABORATORY', 'Laboratory'
        PROCEDURE = 'PROCEDURE', 'Procedure'
        MEDICATION = 'MEDICATION', 'Medication'
        OTHER = 'OTHER', 'Other'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    charge_type = EnumField(ChargeTypeEnum)
    description = models.TextField(null=True, blank=True, help_text='Description of the charge')
    charge_status = EnumField(ChargeStatusEnum)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    visit = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        related_name='charges',
    )
    
    charged_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="charges"
    )
    
    def __str__(self):
        return f"Charge: {self.pk} | Visit: {self.visit.id} | Patient: {self.visit.patient.fullname} | Amount: {self.amount} | Reason: {self.charge_type}"