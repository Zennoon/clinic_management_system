from decimal import Decimal
from datetime import timedelta
from django.apps import apps
from django.db import models
from django_enum import EnumField
from django.utils import timezone
from django.db.models import (
    F,
    BooleanField,
    Case,
    DecimalField,
    ExpressionWrapper,
    Sum,
    Q,
    OuterRef,
    Subquery,
    When,
)
from django.db.models.functions import Coalesce
from constance import config


class PatientQuerySet(models.QuerySet):
    def with_operational(self):
        return self.annotate(
            is_operational_annotated=ExpressionWrapper(
                Q(is_active=True), output_field=BooleanField()
            )
        )

    def with_financials(self):
        from charges.models import Charge
        from payments.models import Payment, Adjustment

        # Charges
        charge_subquery = (
            Charge.objects.filter(visit__patient=OuterRef("pk"))
            .values("visit__patient")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        # Payments and adjustments
        base_payment_filter = Payment.objects.filter(
            charge__visit__patient=OuterRef("pk")
        )
        base_adjustment_filter = Adjustment.objects.filter(
            payment__charge__visit__patient=OuterRef("pk")
        )

        # Total
        payment_all_subquery = (
            base_payment_filter.values("charge__visit__patient")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        adjustment_all_subquery = (
            base_adjustment_filter.values("payment__charge__visit__patient")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        # Waivers
        waiver_methods = Payment.waiver_payment_methods()
        payment_waiver_subquery = (
            base_payment_filter.filter(payment_method__in=waiver_methods)
            .values("charge__visit__patient")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        adjustment_waiver_subquery = (
            base_adjustment_filter.filter(payment__payment_method__in=waiver_methods)
            .values("payment__charge__visit__patient")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        return (
            self.annotate(
                total_charged_annotated=Coalesce(
                    Subquery(charge_subquery), 0.0, output_field=DecimalField()
                ),
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
                net_paid_annotated=F("total_paid_annotated")
                - F("total_adjusted_annotated"),
                net_waived_annotated=F("total_waived_annotated")
                - F("total_waiver_adjusted_annotated"),
                net_money_collected_annotated=F("net_paid_annotated")
                - F("net_waived_annotated"),
            )
            .annotate(
                net_balance_annotated=F("total_charged_annotated")
                - F("net_paid_annotated")
            )
            .annotate(
                is_settled_annotated=Case(
                    When(net_balance_annotated=Decimal("0.00"), then=True),
                    default=False,
                    output_field=BooleanField(),
                ),
                has_overpaid_annotated=Case(
                    When(net_balance_annotated__lt=Decimal("0.00"), then=True),
                    default=False,
                    output_field=BooleanField(),
                ),
                has_due_annotated=Case(
                    When(net_balance_annotated__gt=Decimal("0.00"), then=True),
                    default=False,
                    output_field=BooleanField(),
                ),
            )
        )


class PatientManager(models.Manager):
    def get_queryset(self):
        return PatientQuerySet(self.model, self._db).with_operational()

    def with_financials(self):
        return self.get_queryset().with_financials()


# Create your models here.
class Patient(models.Model):
    class SexEnum(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    class RegionEnum(models.TextChoices):
        ADDIS_ABABA = "ADDIS_ABABA", "Addis Ababa"
        AFAR = "AFAR", "Afar"
        AMHARA = "AMHARA", "Amhara"
        BENISHANGUL_GUMUZ = "BENISHANGUL_GUMUZ", "Benishangul Gumuz"
        CENTRAL_ETHIOPIA = "CENTRAL_ETHIOPIA", "Central Ethiopia"
        DIRE_DAWA = "DIRE_DAWA", "Dire Dawa"
        GAMBELA = "GAMBELA", "Gambela"
        HARARI = "HARARI", "Harari"
        OROMIA = "OROMIA", "Oromia"
        SIDAMA = "SIDAMA", "Sidama"
        SOMALI = "SOMALI", "Somali"
        SOUTH_ETHIOPIA = "SOUTH_ETHIOPIA", "South Ethiopia"
        SOUTH_WEST_ETHIOPIA = "SOUTH_WEST_ETHIOPIA", "South West Ethiopia"
        TIGRAY = "TIGRAY", "Tigray"
        OTHER = "OTHER", "Other"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    first_name = models.CharField(max_length=100, help_text="First name of the patient")
    last_name = models.CharField(max_length=100, help_text="Last name of the patient")
    date_of_birth = models.DateField(help_text="Date of birth of the patient")
    sex = EnumField(SexEnum)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Weight of the patient",
    )
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Height of the patient",
    )
    phone = models.CharField(
        max_length=20, help_text="Patient's phone number", null=True, blank=True
    )
    region = EnumField(RegionEnum, help_text="Region where patient resides")
    city = models.CharField(max_length=100, help_text="City where the patient resides")
    is_active = models.BooleanField(
        default=True, help_text="Whether the patient is active. Used for soft deletes"
    )

    objects = PatientManager()

    @property
    def is_operational(self):
        if hasattr(self, "is_operational_annotated"):
            return self.is_operational_annotated
        return self.is_active

    @property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        return timezone.now().year - self.date_of_birth.year

    @property
    def address(self):
        if not (self.city or self.region):
            return None
        elif self.city and self.region:
            return f"{self.city}, {self.region.label}"
        return self.city or self.region

    @property
    def bmi(self):
        if self.weight and self.height:
            height_in_m = self.height / 100
            return round(self.weight / (height_in_m * height_in_m), 2)
        return 0

    @property
    def current_visit(self):
        current_visit = (
            self.visits.exclude(
                visit_status__in=[
                    "COMPLETED",
                    "CANCELLED",
                ]
            )
            .order_by("date")
            .first()
        )
        return current_visit

    @property
    def last_visit(self):
        visit = self.visits.order_by("-date").first()
        return visit

    @property
    def visits_most_recent_first(self):
        return self.visits.order_by("-date")

    @property
    def total_charged(self):
        if hasattr(self, "total_charged_annotated"):
            return round(self.total_charged_annotated, 2)
        return round(
            self.visits.aggregate(
                total_charged=Coalesce(Sum("charges__amount"), Decimal("0.00"))
            )["total_charged"],
            2,
        )

    @property
    def net_paid(self):
        if hasattr(self, "net_paid_annotated"):
            return round(self.net_paid_annotated, 2)
        total_payments = self.visits.aggregate(
            total=Coalesce(Sum("charges__payments__amount"), Decimal("0.00"))
        )["total"]

        total_adjustments = self.visits.aggregate(
            total=Coalesce(
                Sum("charges__payments__adjustments__amount"), Decimal("0.00")
            )
        )["total"]

        return round(total_payments - total_adjustments, 2)

    @property
    def net_money_collected(self):
        if hasattr(self, "net_money_collected_annotated"):
            return round(self.net_money_collected_annotated, 2)

        from payments.models import Payment

        waiver_methods = Payment.waiver_payment_methods()

        total_payments = self.visits.aggregate(
            total=Coalesce(
                Sum(
                    "charges__payments__amount",
                    filter=~Q(charges__payments__payment_method__in=waiver_methods),
                ),
                Decimal("0.00"),
            )
        )["total"]
        total_adjustments = self.visits.aggregate(
            total=Coalesce(
                Sum(
                    "charges__payments__adjustments__amount",
                    filter=~Q(charges__payments__payment_method__in=waiver_methods),
                ),
                Decimal("0.00"),
            )
        )["total"]

        return round(total_payments - total_adjustments, 2)

    @property
    def net_waived(self):
        if hasattr(self, "net_waived_annotated"):
            return round(self.net_waived_annotated, 2)

        from payments.models import Payment

        waiver_methods = Payment.waiver_payment_methods()

        total_payments = self.visits.aggregate(
            total=Coalesce(
                Sum(
                    "charges__payments__amount",
                    filter=Q(charges__payments__payment_method__in=waiver_methods),
                ),
                Decimal("0.00"),
            )
        )["total"]
        total_adjustments = self.visits.aggregate(
            total=Coalesce(
                Sum(
                    "charges__payments__adjustments__amount",
                    filter=Q(charges__payments__payment_method__in=waiver_methods),
                ),
                Decimal("0.00"),
            )
        )["total"]

        return round(total_payments - total_adjustments, 2)

    @property
    def net_balance(self):
        if hasattr(self, "net_balance_annotated"):
            return round(self.net_balance_annotated, 2)

        return round(self.total_charged - self.net_paid, 2)

    @property
    def is_settled(self):
        if hasattr(self, "is_settled_annotated"):
            return self.is_settled_annotated
        return self.net_balance == Decimal("0.00")

    @property
    def has_due(self):
        if hasattr(self, "has_due_annotated"):
            return self.has_due_annotated
        return self.net_balance > Decimal("0.00")

    @property
    def has_overpaid(self):
        if hasattr(self, "has_overpaid_annotated"):
            return self.has_overpaid_annotated
        return self.net_balance < Decimal("0.00")

    @property
    def all_charges(self):
        Charge = apps.get_model("charges", "Charge")

        return Charge.objects.filter(visit__patient=self)

    @property
    def payments(self):
        Payment = apps.get_model("payments", "Payment")

        return Payment.objects.filter(charge__visit__patient=self)

    @property
    def charges(self):
        Charge = apps.get_model("charges", "Charge")

        return Charge.objects.filter(visit__patient=self)

    @property
    def unpaid_consultation_fee_charge(self):
        from charges.models import Charge

        partial_payment_percent = Decimal(config.PARTIAL_PAYMENT_PERCENT or 50) / 100
        return (
            Charge.objects.with_financials()
            .filter(visit__patient=self, charge_type=Charge.ChargeTypeEnum.CONSULTATION)
            .filter(net_paid_annotated__lt=F("amount") * partial_payment_percent)
            .first()
        )

    def is_within_grace_period(self, date=timezone.now()):
        from charges.models import Charge

        grace_period = config.FOLLOW_UP_GRACE_DAYS or 0

        return (
            self.visits.filter(
                charges__charge_type=Charge.ChargeTypeEnum.CONSULTATION,
                charges__payments__amount__gt=0,
                date__date__gte=(date - timedelta(days=grace_period)).date(),
                date__date__lt=date.date(),
            )
            .distinct()
            .exists()
        )

    def __str__(self):
        return f"{self.fullname}: ID - {self.id}"
