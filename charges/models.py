from decimal import Decimal

from django.db import models
from django.db.models import (
    F,
    Q,
    Case,
    DecimalField,
    ExpressionWrapper,
    Sum,
    Subquery,
    BooleanField,
    OuterRef,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Round
from django.core.exceptions import ObjectDoesNotExist
from django_enum import EnumField
from django.utils import timezone

from lab_requests.models import LabRequest
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class ChargeQuerySet(models.QuerySet):
    def with_operational(self):
        return self.annotate(
            is_operational_annotated=ExpressionWrapper(
                Q(is_active=True)
                & Q(visit__is_active=True)
                & Q(visit__patient__is_active=True),
                output_field=BooleanField(),
            )
        )

    def with_financials(self):
        from payments.models import Payment, Adjustment

        # Total
        payment_all_subquery = (
            Payment.objects.filter(charge=OuterRef("pk"))
            .values("charge")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        adjustment_all_subquery = (
            Adjustment.objects.filter(payment__charge=OuterRef("pk"))
            .values("payment__charge")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        # Waivers
        waiver_methods = Payment.waiver_payment_methods()
        payment_waiver_subquery = (
            Payment.objects.filter(
                charge=OuterRef("pk"), payment_method__in=waiver_methods
            )
            .values("charge")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        adjustment_waiver_subquery = (
            Adjustment.objects.filter(
                payment__charge=OuterRef("pk"),
                payment__payment_method__in=waiver_methods,
            )
            .values("payment__charge")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        return (
            self.annotate(
                total_adjusted_annotated=Coalesce(
                    Subquery(adjustment_all_subquery), 0.0, output_field=DecimalField()
                ),
                total_paid_annotated=Coalesce(
                    Subquery(payment_all_subquery), 0.0, output_field=DecimalField()
                ),
                total_waiver_adjusted_annotated=Coalesce(
                    Subquery(adjustment_waiver_subquery),
                    0.0,
                    output_field=DecimalField(),
                ),
                total_waived_annotated=Coalesce(
                    Subquery(payment_waiver_subquery), 0.0, output_field=DecimalField()
                ),
            )
            .annotate(
                net_paid_annotated=Round(
                    F("total_paid_annotated") - F("total_adjusted_annotated"),
                    precision=2,
                ),
                net_waived_annotated=Round(
                    F("total_waived_annotated") - F("total_waiver_adjusted_annotated"),
                    precision=2,
                ),
                net_money_collected_annotated=Round(
                    F("net_paid_annotated") - F("net_waived_annotated"), precision=2
                ),
            )
            .annotate(
                net_balance_annotated=Round(
                    F("amount") - F("net_paid_annotated"),
                    precision=2,
                    output_field=DecimalField(),
                ),
                is_settled_annotated=Case(
                    When(net_balance_annotated=Decimal("0.00"), then=True),
                    default=False,
                    output_field=BooleanField(),
                ),
                is_overpaid_annotated=Case(
                    When(net_balance_annotated__lt=Decimal("0.00"), then=True),
                    default=False,
                    output_field=BooleanField(),
                ),
                is_due_annotated=Case(
                    When(net_balance_annotated__gt=Decimal("0.00"), then=True),
                    default=False,
                    output_field=BooleanField(),
                ),
            )
            .annotate(
                charge_status_annotated=Case(
                    When(
                        is_settled_annotated=True,
                        then=Value(Charge.ChargeStatusEnum.SETTLED),
                    ),
                    When(
                        is_due_annotated=True,
                        then=Value(Charge.ChargeStatusEnum.PENDING),
                    ),
                    When(
                        is_overpaid_annotated=True,
                        then=Value(Charge.ChargeStatusEnum.CREDIT),
                    ),
                    default=Value(Charge.ChargeStatusEnum.PENDING),
                    output_field=EnumField(Charge.ChargeStatusEnum),
                ),
            )
        )


class ChargeManager(models.Manager):
    def get_queryset(self):
        return ChargeQuerySet(self.model, self._db).with_operational()

    def with_financials(self):
        return self.get_queryset().with_financials()


class Charge(models.Model):
    class ChargeStatusEnum(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SETTLED = "SETTLED", "Settled"
        CREDIT = "CREDIT", "Overpaid"
        CANCELLED = "CANCELLED", "Cancelled"
        OTHER = "OTHER", "Other"

    class ChargeTypeEnum(models.TextChoices):
        CONSULTATION = "CONSULTATION", "Consultation"
        LABORATORY = "LABORATORY", "Laboratory"
        PROCEDURE = "PROCEDURE", "Procedure"
        MEDICATION = "MEDICATION", "Medication"
        MEDICAL_REPORT = "MEDICAL_REPORT", "Medical Report"
        EQUIPMENT_AND_CONSUMABLES = (
            "EQUIPMENT_AND_CONSUMABLES",
            "Equipment and Consumables",
        )
        PENALTY = "PENALTY", "Penalty"
        OTHER = "OTHER", "Other"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    charge_type = EnumField(ChargeTypeEnum)
    description = models.TextField(
        null=True, blank=True, help_text="Description of the charge"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    visit = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        related_name="charges",
    )
    lab_request = models.OneToOneField(
        LabRequest, on_delete=models.PROTECT, related_name="charge", null=True
    )

    issuer = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="charges")

    objects = ChargeManager()

    @property
    def charge_status(self):
        if hasattr(self, "charge_status_annotated"):
            return self.charge_status_annotated
        if self.is_settled:
            return Charge.ChargeStatusEnum.SETTLED
        elif self.is_overpaid:
            return Charge.ChargeStatusEnum.CREDIT
        return Charge.ChargeStatusEnum.PENDING

    @property
    def is_operational(self):
        if hasattr(self, "is_operational_annotated"):
            return self.is_operational_annotated
        return self.is_active and self.visit.is_operational

    @property
    def override(self):
        try:
            return self.charge_override
        except ObjectDoesNotExist:
            return None

    @property
    def is_misc_charge(self):
        return self.charge_type in self.miscelaneous_charge_types()

    @property
    def is_settled(self):
        if hasattr(self, "is_settled_annotated"):
            return self.is_settled_annotated
        return self.amount == self.net_paid

    @property
    def is_due(self):
        if hasattr(self, "is_due_annotated"):
            return self.is_due_annotated
        return self.amount > self.net_paid

    @property
    def is_overpaid(self):
        if hasattr(self, "is_overpaid_annotated"):
            return self.is_overpaid_annotated
        return self.amount < self.net_paid

    @property
    def net_paid(self):
        if hasattr(self, "net_paid_annotated"):
            return self.net_paid_annotated

        total_payments = self.payments.aggregate(
            total=Coalesce(Sum("amount"), Decimal("0.00"))
        )["total"]
        total_adjustments = self.payments.aggregate(
            total=Coalesce(Sum("adjustments__amount"), Decimal("0.00"))
        )["total"]

        return round(
            total_payments - total_adjustments,
            2,
        )

    @property
    def net_waived(self):
        if hasattr(self, "net_waived_annotated"):
            return self.net_waived_annotated

        from payments.models import Payment

        waiver_methods = Payment.waiver_payment_methods()

        payments = self.payments.filter(payment_method__in=waiver_methods).aggregate(
            total=Coalesce(Sum("amount"), Decimal("0.00"))
        )["total"]
        adjustments = self.payments.filter(payment_method__in=waiver_methods).aggregate(
            total=Coalesce(Sum("adjustments__amount"), Decimal("0.00"))
        )["total"]

        return round(payments - adjustments, 2)

    @property
    def net_money_collected(self):
        if hasattr(self, "net_money_collected_annotated"):
            return self.net_money_collected_annotated

        from payments.models import Payment

        waiver_methods = Payment.waiver_payment_methods()

        payments = self.payments.filter(
            ~Q(payment_method__in=waiver_methods)
        ).aggregate(total=Coalesce(Sum("amount"), Decimal("0.00")))["total"]
        adjustments = self.payments.filter(
            ~Q(payment_method__in=waiver_methods)
        ).aggregate(total=Coalesce(Sum("adjustments__amount"), Decimal("0.00")))[
            "total"
        ]

        return round(payments - adjustments, 2)

    @property
    def net_balance(self):
        if hasattr(self, "net_balance_annotated"):
            return self.net_balance_annotated
        return round(self.amount - self.net_paid, 2)
    
    @property
    def paid_percentage(self):
        return round((self.net_paid / self.amount) * 100, 0)
    
    @property
    def unpaid_percentage(self):
        return 100 - self.paid_percentage

    @classmethod
    def miscelaneous_charge_types(cls):
        return [
            Charge.ChargeTypeEnum.MEDICAL_REPORT,
            Charge.ChargeTypeEnum.EQUIPMENT_AND_CONSUMABLES,
            Charge.ChargeTypeEnum.PENALTY,
            Charge.ChargeTypeEnum.OTHER,
        ]

    def __str__(self):
        return f"{self.visit.patient.fullname} {self.charge_type.label} charge on {self.date.date().strftime("%a %b %d, %Y")}, visit ID: {self.visit.id}, amount: {round(self.amount, 2)}"


class ChargeOverride(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    reason = models.TextField(blank=True, null=True)
    date = models.DateTimeField(default=timezone.now)

    charge = models.OneToOneField(
        Charge, on_delete=models.CASCADE, related_name="charge_override"
    )
    overridden_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="overrides"
    )
