from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from django_enum import EnumField
from django.utils import timezone

from staff.models import Staff
from visits.models import Visit


# Create your models here.
class LabGroup(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(
        max_length=100,
        help_text="Name of the semantic group ot tests/observations",
        unique=True,
    )
    is_active = models.BooleanField(
        default=True, help_text="Is this test group active or archived?"
    )

    created_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="created_lab_groups",
    )

    @property
    def is_operational(self):
        return self.is_active

    def __str__(self):
        return f"{self.name} group with {self.lab_observations.count()} observations"


class LabObservation(models.Model):
    class ObservationTypeEnum(models.TextChoices):
        CATEGORICAL = "C", "Categorical"
        NUMERICAL = "N", "Numerical"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100, help_text="Name of the test")
    type = EnumField(ObservationTypeEnum)
    is_active = models.BooleanField(
        default=True, help_text="Is this observation active?"
    )

    unit_of_measurement = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Unit of measurement of the test",
    )
    reference_min = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Minimum value considered within the normal range; only used if this observation is numerical",
    )
    reference_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Maximum value considered within the normal range; only used if this observation is numerical",
    )
    lab_group = models.ForeignKey(
        LabGroup, on_delete=models.PROTECT, related_name="lab_observations"
    )
    created_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="created_lab_observations",
    )

    @property
    def is_operational(self):
        return self.lab_group.is_operational and self.is_active

    def __str__(self):
        return f"Lab Observation {self.name}: | Group: {self.lab_group.name} | Type: {self.type.label}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "lab_group"], name="unique_name")
        ]


class LabService(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(
        max_length=100, help_text="Name of the billable lab service"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)

    lab_group = models.ForeignKey(LabGroup, on_delete=models.PROTECT)
    lab_observations = models.ManyToManyField(
        LabObservation, related_name="lab_services"
    )
    created_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="created_lab_services",
    )

    def clean(self):
        lab_observation_ids = self.lab_observations.values_list("id", flat=True)

        matching_services = (
            LabService.objects.exclude(pk=self.pk)
            .filter(lab_observations__in=self.lab_observations.all())
            .annotate(observations_count=Count("lab_observations"))
            .filter(observations_count=self.lab_observations.count())
            .distinct()
        )

        if matching_services.exists():
            raise ValidationError(
                "There exists another lab service with the exact same observations set."
            )
        return super().clean()

    def __str__(self):
        return f"Lab Service {self.name}: | Group: {self.lab_group.name} | Price: {self.price} | Observations: {self.lab_observations.all()}"


class LabRequest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(null=True)
    is_active = models.BooleanField(default=True, help_text="Is this request active?")

    lab_services = models.ManyToManyField(LabService, related_name="lab_requests")
    ordered_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
    )
    visit = models.ForeignKey(
        Visit,
        on_delete=models.PROTECT,
        related_name="lab_requests",
    )

    @property
    def is_operational(self):
        return self.is_active and self.visit.is_operational

    @property
    def price(self):
        return self.lab_services.aggregate(
            total=Coalesce(Sum("price"), Decimal("0.00"))
        )["total"]

    @property
    def observations(self):
        return {
            observation
            for service in self.lab_services.all()
            for observation in service.lab_observations.all()
        }

    def __str__(self):
        return f"Patient {self.visit.patient.fullname} lab request {self.id}: Ordered by: {self.ordered_by.username} | Price: {self.price}"
