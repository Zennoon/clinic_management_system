from decimal import Decimal

from django.db import models
from django.db.models import (
    F,
    Q,
    BooleanField,
    DecimalField,
    ExpressionWrapper,
    OuterRef,
    Sum,
    Subquery,
)
from django.db.models.functions import Coalesce
from django_enum import EnumField
from django.utils import timezone

from charges.models import Charge
from staff.models import Staff


# Create your models here.
class PaymentQuerySet(models.QuerySet):
    def with_operational(self):
        return self.annotate(
            is_operational_annotated=ExpressionWrapper(
                Q(is_active=True)
                & Q(charge__is_active=True)
                & Q(charge__visit__is_active=True)
                & Q(charge__visit__patient__is_active=True),
                output_field=BooleanField(),
            )
        )

    def with_financials(self):
        adjustment_subquery = (
            Adjustment.objects.filter(payment=OuterRef("pk"))
            .values("payment")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        return self.annotate(
            total_adjusted_annotated=Coalesce(
                Subquery(adjustment_subquery), 0.0, output_field=DecimalField()
            ),
            net_paid_annotated=F("amount") - F("total_adjusted_annotated"),
        )


class PaymentManager(models.Manager):
    def get_queryset(self):
        return PaymentQuerySet(self.model, using=self._db).with_operational()

    def with_financials(self):
        return self.get_queryset().with_financials()


class AdjustmentQuerySet(models.QuerySet):
    def with_operational(self):
        return self.annotate(
            is_operational_annotated=ExpressionWrapper(
                Q(is_active=True)
                & Q(payment__is_active=True)
                & Q(payment__charge__is_active=True)
                & Q(payment__charge__visit__is_active=True)
                & Q(payment__charge__visit__patient__is_active=True),
                output_field=BooleanField(),
            )
        )


class AdjustmentManager(models.Manager):
    def get_queryset(self):
        return AdjustmentQuerySet(self.model, using=self._db).with_operational()


class Payment(models.Model):
    class PaymentMethodEnum(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        MOBILE = "MOBILE", "Mobile"
        GRACE_PERIOD = "GRACE_PERIOD", "Grace Period"
        WAIVER = "WAIVER", "Waiver"
        OTHER = "OTHER", "Other"

    class PaymentStatusEnum(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REFUNDED = "REFUNDED", "Refunded"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = EnumField(PaymentMethodEnum, default=PaymentMethodEnum.CASH)
    payment_status = EnumField(PaymentStatusEnum, default=PaymentStatusEnum.CONFIRMED)
    is_active = models.BooleanField(default=True)

    charge = models.ForeignKey(
        Charge, on_delete=models.PROTECT, related_name="payments", null=True
    )
    acceptor = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="recorded_payments"
    )

    objects = PaymentManager()

    def create_adjustment(self, amount, reason, staff):
        if self.is_operational:
            adjustment = Adjustment.objects.create(
                amount=amount,
                reason=reason,
                payment=self,
                created_by=staff,
            )
            return adjustment

    @property
    def is_operational(self):
        if hasattr(self, "is_operational_annotated"):
            return self.is_operational_annotated
        return self.is_active and self.charge.is_operational

    @property
    def total_adjusted(self):
        if hasattr(self, "total_adjusted_annotated"):
            return self.total_adjusted_annotated
        return round(
            self.adjustments.aggregate(total=Coalesce(Sum("amount"), Decimal("0.00")))[
                "total"
            ],
            2,
        )

    @property
    def net_paid(self):
        if hasattr(self, "net_paid_annotated"):
            return self.net_paid_annotated

        return round(self.amount - self.total_adjusted, 2)

    @property
    def charge_paid_percentage(self):
        return round((self.net_paid / self.charge.amount) * 100)

    @property
    def charge_other_paid_percentage(self):
        return round(
            ((self.charge.net_paid - self.net_paid) / self.charge.amount) * 100
        )

    @classmethod
    def waiver_payment_methods(cls):
        return [
            Payment.PaymentMethodEnum.GRACE_PERIOD,
            Payment.PaymentMethodEnum.WAIVER,
        ]

    @classmethod
    def selectable_payment_methods(cls):
        return [
            Payment.PaymentMethodEnum.CARD,
            Payment.PaymentMethodEnum.CASH,
            Payment.PaymentMethodEnum.MOBILE,
            Payment.PaymentMethodEnum.WAIVER,
        ]

    def __str__(self):
        return f"Payment: {self.pk} | Date: {self.date} | Patient: {self.charge.visit.patient.fullname} | Amount: {self.amount} | Payment Method: {self.payment_method}"


class Adjustment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=100)
    date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="adjustments"
    )
    created_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="created_by"
    )

    objects = AdjustmentManager()
    
    @property
    def is_operational(self):
        if hasattr(self, "is_operational_annotated"):
            return self.is_operational_annotated
        return self.is_active and self.payment.is_operational
