from django.db import models
from django_enum import EnumField

from staff.models import Staff
from visits.models import Visit


# Create your models here.
class Payment(models.Model):
    class PaymentMethodEnum(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Card'
        MOBILE = 'MOBILE', 'Mobile'
        OTHER = 'OTHER', 'Other'
    class PaymentStatusEnum(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        REFUNDED = 'REFUNDED', 'Refunded'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = EnumField(PaymentMethodEnum, default=PaymentMethodEnum.CASH)
    payment_status = EnumField(PaymentStatusEnum, default=PaymentStatusEnum.CONFIRMED)

    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name='payments')
    recorded_by = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='recorded_payments')
    
    def __str__(self):
        return f"Payment: {self.pk} | Visit: {self.visit.id} | Patient: {self.visit.patient.fullname} | Amount: {self.amount} | Payment Method: {self.payment_method}"