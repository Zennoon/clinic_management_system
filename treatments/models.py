from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import F, Count
from django.utils import timezone
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.contrib.contenttypes.models import ContentType
from django_enum import EnumField
from constance import config

from staff.models import Staff
from visits.models import Visit


# Create your models here.
class TreatmentQuerySet(models.QuerySet):
    def with_derived_status(self):
        pass


class Treatment(models.Model):
    class TreatmentTypeEnum(models.TextChoices):
        MEDICATION = "MEDICATION", "Medication"
        OPERATION = "OPERATION", "Operation"
        OTHER = "OTHER", "Other"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    type = EnumField(TreatmentTypeEnum)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="created_treatments"
    )

    @property
    def is_operational(self):
        return self.is_active

    def __str__(self):
        return f"Treatment {self.name} of type {self.type.label}"


class TreatmentService(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    treatments = models.ManyToManyField(Treatment, related_name="treatment_services")
    created_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="created_treatment_services"
    )

    def clean(self):
        treatment_ids = set(self.treatments.values_list("id", flat=True))
        equal_count_services = (
            TreatmentService.objects.exclude(pk=self.pk)
            .annotate(treatments_count=Count("treatments"))
            .filter(treatments_count=self.treatments.count())
            .distinct()
        )

        for service in equal_count_services.all():
            service_treatment_ids = set(service.treatments.values_list("id", flat=True))
            if treatment_ids == service_treatment_ids:
                print(self.treatments)
                print(service.treatments)
                raise ValidationError(
                    "There exists another treatment service with the exact same treatments set."
                )

        return super().clean()

    def __str__(self):
        return f"Treatment Service {self.name}: Price: {self.price}"


class TreatmentRequest(models.Model):
    class RequestStatusEnum(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    request_status = EnumField(RequestStatusEnum, default=RequestStatusEnum.PENDING)
    date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(null=True)
    is_active = models.BooleanField(default=True, help_text="Is this request active?")

    treatment_services = models.ManyToManyField(
        TreatmentService, related_name="treatment_requests"
    )
    ordered_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="treatment_requests"
    )
    visit = models.ForeignKey(
        Visit, on_delete=models.PROTECT, related_name="treatment_requests"
    )

    @property
    def is_operational(self):
        return self.is_active and self.visit.is_operational

    @property
    def is_pending(self):
        return self.request_status == TreatmentRequest.RequestStatusEnum.PENDING

    @property
    def is_completed(self):
        return self.request_status == TreatmentRequest.RequestStatusEnum.COMPLETED

    @property
    def is_in_progress(self):
        return self.request_status == TreatmentRequest.RequestStatusEnum.IN_PROGRESS

    @property
    def is_failed(self):
        return self.request_status == TreatmentRequest.RequestStatusEnum.FAILED

    @property
    def is_cancelled(self):
        return self.request_status == TreatmentRequest.RequestStatusEnum.CANCELLED

    @property
    def price(self):
        return self.treatment_services.aggregate(
            total=Coalesce(Sum("price"), Decimal("0.00"))
        )["total"]

    @property
    def treatments(self):
        return {
            treatment
            for service in self.treatment_services.all()
            for treatment in service.treatments.all()
        }

    @property
    def can_proceed(self):
        from charges.models import Charge

        require_partial_payment = config.REQUIRE_PARTIAL_PAYMENT

        if not require_partial_payment:
            return True

        partial_payment_percent = (Decimal(config.PARTIAL_PAYMENT_PERCENT or 50)) / 100

        return (
            Charge.objects.with_financials()
            .filter(
                charge_type=Charge.ChargeTypeEnum.TREATMENT,
                content_type=ContentType.objects.get_for_model(TreatmentRequest),
                object_id=self.pk,
            )
            .filter(net_paid_annotated__gte=F("amount") * partial_payment_percent)
            .exists()
        )

    def __str__(self):
        return f"Treatment Request {self.pk} for {self.visit.patient.fullname} | Ordered by: {self.ordered_by.username} | Price: {self.price}"


class TreatmentRequestResult(models.Model):
    class OutcomeTypeEnum(models.TextChoices):
        PARTIAL = "PARTIAL", "Partial / In-Progress Dose"
        COMPLETED = "COMPLETED", "Fully Administered"
        NOT_ADMINISTERED = "NOT_ADMINISTERED", "Refused / Unable to Administer"
        OBSERVATION = "OBSERVATION", "Status Update / Follow-up Note"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    outcome_type = EnumField(OutcomeTypeEnum)
    date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(null=True)
    is_active = models.BooleanField(
        default=True, help_text="Is this treatment request result active?"
    )

    treatment_request = models.ForeignKey(
        TreatmentRequest,
        on_delete=models.PROTECT,
        related_name="treatment_request_results",
    )
    administered_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="treatment_requests_administered"
    )

    @property
    def is_operational(self):
        return self.is_active and self.treatment_request.is_operational

    def update_request_status(self):
        match self.outcome_type:
            case (
                TreatmentRequestResult.OutcomeTypeEnum.PARTIAL
                | TreatmentRequestResult.OutcomeTypeEnum.OBSERVATION
            ):
                self.treatment_request.request_status = (
                    TreatmentRequest.RequestStatusEnum.IN_PROGRESS
                )
            case TreatmentRequestResult.OutcomeTypeEnum.NOT_ADMINISTERED:
                self.treatment_request.request_status = (
                    TreatmentRequest.RequestStatusEnum.FAILED
                )
            case TreatmentRequestResult.OutcomeTypeEnum.COMPLETED:
                self.treatment_request.request_status = (
                    TreatmentRequest.RequestStatusEnum.COMPLETED
                )
            case _:
                pass

        self.treatment_request.save()

    def __str__(self):
        return f"Treatment result for {self.treatment_request.visit.patient.fullname} | ID: {self.pk} | Treatment Request ID: {self.treatment_request.pk} | Performed by: {self.performed_by.username}"


class TreatmentResult(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(null=True)
    is_active = models.BooleanField(
        default=True, help_text="Is this treatment result active?"
    )

    treatment_request_result = models.ForeignKey(
        TreatmentRequestResult,
        on_delete=models.PROTECT,
        related_name="treatment_results",
    )
    treatment = models.ForeignKey(
        Treatment, on_delete=models.PROTECT, related_name="results"
    )
    administered_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="treatments_performed"
    )

    @property
    def is_operational(self):
        return self.is_active and self.treatment_request_result.is_operational

    def __str__(self):
        return f"Treatment Result for {self.treatment_request_result.treatment_request.visit.patient.fullname} | ID: {self.pk} | Treatment: {self.treatment.name} | Performed by: {self.performed_by.username}"
