from decimal import Decimal

from django.db import models
from django.db.models import (
    Q,
    BooleanField,
    DecimalField,
    ExpressionWrapper,
    Sum,
    F,
    OuterRef,
    Subquery,
)
from django.db.models.functions import Coalesce
from django_enum import EnumField
from django.utils import timezone
from constance import config

from patients.models import Patient
from staff.models import Staff


# Create your models here.
class VisitQuerySet(models.QuerySet):
    def with_operational(self):
        return self.annotate(
            is_operational_annotated=ExpressionWrapper(
                Q(is_active=True) & Q(patient__is_active=True),
                output_field=BooleanField(),
            )
        )

    def with_financials(self):
        from charges.models import Charge
        from payments.models import Payment, Adjustment

        # Charges
        charge_subquery = (
            Charge.objects.filter(visit=OuterRef("pk"))
            .values("visit")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        # Payments and adjustments
        base_payment_filter = Payment.objects.filter(charge__visit=OuterRef("pk"))
        base_adjustment_filter = Adjustment.objects.filter(
            payment__charge__visit=OuterRef("pk")
        )

        # Total
        payment_all_subquery = (
            base_payment_filter.values("charge__visit")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        adjustment_all_subquery = (
            base_adjustment_filter.values("payment__charge__visit")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        # Waivers
        waiver_methods = Payment.waiver_payment_methods()
        payment_waiver_subquery = (
            base_payment_filter.filter(payment_method__in=waiver_methods)
            .values("charge__visit")
            .annotate(total=Sum("amount"))
            .values("total")
        )

        adjustment_waiver_subquery = (
            base_adjustment_filter.filter(payment__payment_method__in=waiver_methods)
            .values("payment__charge__visit")
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
        )


class VisitManager(models.Manager):
    def get_queryset(self):
        return VisitQuerySet(self.model, self._db).with_operational()

    def with_financials(self):
        return self.get_queryset().with_financials()


class Visit(models.Model):
    class VisitCategoryEnum(models.TextChoices):
        HISTORY_AND_PHYSICAL = "HISTORY_AND_PHYSICAL", "History and Physical"
        MEDICAL_CERTIFICATE = "MEDICAL_CERTIFICATE", "Medical Certificate"
        PROGRESS_NOTE = "PROGRESS_NOTE", "Progress Note"
        OTHER = "OTHER", "Other"

    class VisitStatusEnum(models.TextChoices):
        AWAITING_INITIATION = "AWAITING_INITIATION", "Awaiting to be initiated"
        AWAITING_CONSULTATION_PAYMENT = (
            "AWAITING_CONSULTATION_PAYMENT",
            "Awaiting Visit Fee",
        )
        AWAITING_MISC_PAYMENT = (
            "AWAITING_MISC_PAYMENT",
            "Awaiting payment for misc charges",
        )
        AWAITING_VITALS = "AWAITING_VITALS", "Awaiting Vitals"
        AWAITING_CONSULTATION = "AWAITING_CONSULTATION", "Awaiting Doctor Consultation"
        IN_CONSULTATION = "IN_CONSULTATION", "With Doctor"
        AWAITING_LAB_PAYMENT = "AWAITING_LAB_PAYMENT", "Awaiting Lab Payment"
        AWAITING_LAB_RESULT = "AWAITING_LAB_RESULT", "Awaiting Lab Results"
        IN_LAB = "IN_LAB", "In Lab"
        AWAITING_REVIEW = "AWAITING_REVIEW", "Awaiting Lab Results Review"
        COMPLETED = "COMPLETED", "Completed"
        STALE = "STALE", "Stale Visit"
        CANCELLED = "CANCELLED", "Cancelled"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    visit_status = EnumField(
        VisitStatusEnum, default=VisitStatusEnum.AWAITING_CONSULTATION_PAYMENT
    )
    visit_category = EnumField(VisitCategoryEnum)
    current_status_since = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="visits",
    )
    created_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="created_visits"
    )

    objects = VisitManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "date"], name="unique_patient_date"
            )
        ]

    def create_consultation_charge(self, staff, date=None):
        from charges.models import Charge
        from payments.models import Payment

        consultation_charge = self.charges.filter(
            charge_type=Charge.ChargeTypeEnum.CONSULTATION
        )

        if not consultation_charge.exists():
            consultation_fee = config.CONSULTATION_FEE or 0
            consultation_charge = Charge.objects.create(
                visit=self,
                charge_type=Charge.ChargeTypeEnum.CONSULTATION,
                amount=consultation_fee,
                issuer=staff,
                date=date or self.date,
            )

            if self.patient.is_within_grace_period(date=self.date):
                Payment.objects.create(
                    date=date or self.date,
                    amount=consultation_fee,
                    payment_method=Payment.PaymentMethodEnum.GRACE_PERIOD,
                    charge=consultation_charge,
                    acceptor=staff,
                )

            self.update_status()
        return consultation_charge

    def create_lab_request_charge(self, lab_request, staff, date=None):
        from charges.models import Charge

        lab_charge = Charge.objects.filter(
            lab_request=lab_request, charge_type=Charge.ChargeTypeEnum.LABORATORY
        )
        if not lab_charge.exists():
            lab_charge = Charge.objects.create(
                charge_type=Charge.ChargeTypeEnum.LABORATORY,
                amount=lab_request.price,
                visit=self,
                lab_request=lab_request,
                issuer=staff,
                date=date or lab_request.date,
            )
        self.update_status()
        return lab_charge

    def reconcile_consultation_charge(self, reason, staff):
        from charges.models import Charge
        from payments.models import Payment

        consultation_charge = self.charges.filter(
            charge_type=Charge.ChargeTypeEnum.CONSULTATION
        ).first()

        if not consultation_charge:
            return

        is_within_grace_period = self.patient.is_within_grace_period(date=self.date)
        total_grace_payment = (
            consultation_charge.payments.with_financials()
            .filter(
                payment_method=Payment.PaymentMethodEnum.GRACE_PERIOD,
            )
            .aggregate(total=Coalesce(Sum("net_paid_annotated"), Decimal("0.00")))[
                "total"
            ]
        )

        if is_within_grace_period and (
            total_grace_payment < consultation_charge.amount
        ):
            Payment.objects.create(
                charge=consultation_charge,
                amount=(consultation_charge.amount - total_grace_payment),
                payment_method=Payment.PaymentMethodEnum.GRACE_PERIOD,
                acceptor=staff,
            )
        elif not is_within_grace_period and total_grace_payment > 0:
            grace_payments = consultation_charge.payments.with_financials().filter(
                payment_method=Payment.PaymentMethodEnum.GRACE_PERIOD,
            )

            for payment in grace_payments.all():
                payment.create_adjustment(
                    amount=payment.net_paid,
                    reason=f"Charge reconciliation: {reason}",
                    staff=staff,
                )
        self.update_status()

    def pay_charge(self, charge, amount, method, staff, date=None):
        from payments.models import Payment

        payment = Payment.objects.create(
            charge=charge,
            payment_method=method,
            amount=amount,
            acceptor=staff,
            date=date or charge.date,
        )
        self.update_status()
        return payment

    def pay_consultation_charge(self, amount, method, staff, date=None):
        from charges.models import Charge
        from payments.models import Payment

        charge = (
            self.charges.filter(charge_type=Charge.ChargeTypeEnum.CONSULTATION)
            .annotate(
                total_paid=Coalesce(
                    Sum("payments__amount", distinct=True), Decimal("0.00")
                ),
                total_adjusted=Coalesce(
                    Sum("payments__adjustments__amount"), Decimal("0.00")
                ),
            )
            .annotate(balance=F("amount") - F("total_paid") + F("total_adjusted"))
            .filter(balance__gt=Decimal("0.00"))
            .first()
        )

        if charge:
            Payment.objects.create(
                charge=charge,
                payment_method=method,
                amount=amount,
                acceptor=staff,
                date=date or charge.date,
            )
        self.update_status()

    def derive_visit_status(self):
        from charges.models import Charge

        if not self.pk:
            return Visit.VisitStatusEnum.AWAITING_CONSULTATION_PAYMENT

        consultation_charge = self.charges.filter(
            charge_type=Charge.ChargeTypeEnum.CONSULTATION
        ).first()
        lab_charges = self.charges.filter(charge_type=Charge.ChargeTypeEnum.LABORATORY)
        misc_charges = self.charges.filter(
            charge_type__in=Charge.miscelaneous_charge_types()
        )

        if not consultation_charge:
            return Visit.VisitStatusEnum.AWAITING_INITIATION

        if consultation_charge.is_due and consultation_charge.override is None:
            return Visit.VisitStatusEnum.AWAITING_CONSULTATION_PAYMENT

        if lab_charges.exists():
            for charge in lab_charges.all():
                if charge.is_due and charge.override is None:
                    return Visit.VisitStatusEnum.AWAITING_LAB_PAYMENT

        if misc_charges.exists():
            for charge in misc_charges.all():
                if charge.is_due and charge.override is None:
                    return Visit.VisitStatusEnum.AWAITING_MISC_PAYMENT

        if not self.vital_signs.exists():
            return Visit.VisitStatusEnum.AWAITING_VITALS

        if not self.consultations.exists():
            return Visit.VisitStatusEnum.AWAITING_CONSULTATION

        if self.lab_requests.exists():
            for request in self.lab_requests.all():
                if not request.lab_results.exists():
                    return Visit.VisitStatusEnum.AWAITING_LAB_RESULT

        if not self.reviews.exists():
            return Visit.VisitStatusEnum.AWAITING_REVIEW

        return Visit.VisitStatusEnum.COMPLETED

    def update_status(self):
        old_status = self.visit_status
        last_log = self.status_history.first()
        new_status = self.derive_visit_status()
        if last_log and last_log.status != new_status:
            VisitStatusLog.objects.create(visit=self, status=new_status)
        self.visit_status = self.derive_visit_status()
        if old_status != new_status:
            self.current_status_since = timezone.now()
            print(self.current_status_since)

        self.save()

    @property
    def is_awaiting_payment(self):
        return self.derive_visit_status() in [
            Visit.VisitStatusEnum.AWAITING_CONSULTATION_PAYMENT,
            Visit.VisitStatusEnum.AWAITING_LAB_PAYMENT,
            Visit.VisitStatusEnum.AWAITING_MISC_PAYMENT,
        ]

    @property
    def is_completed(self):
        return self.derive_visit_status() is Visit.VisitStatusEnum.COMPLETED

    @property
    def total_charged(self):
        if hasattr(self, "total_charged_annotated"):
            return round(self.total_charged_annotated, 2)

        return round(
            self.charges.aggregate(total=Coalesce(Sum("amount"), Decimal("0.00")))[
                "total"
            ],
            2,
        )

    @property
    def net_paid(self):
        if hasattr(self, "net_paid_annotated"):
            return round(self.net_paid_annotated, 2)
        total_payments = self.charges.aggregate(
            total=Coalesce(Sum("payments__amount"), Decimal("0.00"))
        )["total"]

        total_adjustments = self.charges.aggregate(
            total=Coalesce(Sum("payments__adjustments__amount"), Decimal("0.00"))
        )["total"]

        return round(total_payments - total_adjustments, 2)

    @property
    def net_money_collected(self):
        if hasattr(self, "net_money_collected_annotated"):
            return round(self.net_money_collected_annotated, 2)

        from payments.models import Payment

        waiver_methods = Payment.waiver_payment_methods()

        total_payments = self.charges.aggregate(
            total=Coalesce(
                Sum(
                    "payments__amount",
                    filter=~Q(payments__payment_method__in=waiver_methods),
                ),
                Decimal("0.00"),
            )
        )["total"]
        total_adjustments = self.charges.aggregate(
            total=Coalesce(
                Sum(
                    "payments__adjustments__amount",
                    filter=~Q(payments__payment_method__in=waiver_methods),
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

        total_payments = self.charges.aggregate(
            total=Coalesce(
                Sum(
                    "payments__amount",
                    filter=Q(payments__payment_method__in=waiver_methods),
                ),
                Decimal("0.00"),
            )
        )["total"]
        total_adjustments = self.charges.aggregate(
            total=Coalesce(
                Sum(
                    "payments__adjustments__amount",
                    filter=Q(payments__payment_method__in=waiver_methods),
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
    def payments(self):
        from payments.models import Payment

        return Payment.objects.filter(charge__visit=self)

    @property
    def is_operational(self):
        if hasattr(self, "is_operational_annotated"):
            return self.is_operational_annotated
        return self.is_active and self.patient.is_operational

    def save(self, *args, **kwargs):
        self.visit_status = self.derive_visit_status()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.fullname} visit on {self.date.date().strftime("%a %b %d, %Y")}"


class Consultation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    chief_complaint = models.TextField(blank=True, null=True)
    history = models.TextField(blank=True, null=True)
    assessment = models.TextField(blank=True, null=True)

    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name="consultations"
    )
    consulted_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="consultations"
    )


class Review(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    assessment = models.TextField(null=True, blank=True)

    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="reviews")
    reviewed_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="reviews"
    )


class VisitUpdateLog(models.Model):
    old_patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="updated_from_visits_logs",
    )
    new_patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="updated_to_visits_logs",
    )
    old_date = models.DateTimeField()
    new_date = models.DateTimeField()
    reason = models.CharField()
    visit = models.ForeignKey(
        Visit,
        on_delete=models.CASCADE,
        related_name="update_logs",
    )

    updated_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="updated_visits"
    )

    def __str__(self):
        return f"Visit [{self.visit.id:06d}] updated by {self.updated_by.username}:\n\tPatient: {self.old_patient.fullname} -> {self.new_patient.fullname}\n\tDate: {self.old_date.strftime("%a %b %d, %Y")} -> {self.new_date.strftime("%a %b %d, %Y")}"


class VisitStatusLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = EnumField(Visit.VisitStatusEnum)
    changed_at = models.DateTimeField(auto_now=True)

    visit = models.ForeignKey(
        Visit,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    changed_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        null=True,
    )

    class Meta:
        ordering = ["-changed_at"]
