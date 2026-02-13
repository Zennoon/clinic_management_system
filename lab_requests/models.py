from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django_enum import EnumField

from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class LabTest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100, help_text="Name of the test")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price of the test")
    is_active = models.BooleanField(default=True, help_text="Is this test active?")

    created_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="created_tests",
    )
    
    def __str__(self):
        return f"Test {self.name}: Price: {self.price}"

class LabObservation(models.Model):
    class ResultTypeEnum(models.TextChoices):
        CATEGORICAL = 'C', 'Categorical'
        NUMERICAL = 'N', 'Numerical'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100, help_text="Name of the observation")
    result_type = EnumField(ResultTypeEnum)
    is_active = models.BooleanField(default=True, help_text="Is this observation active?")

    unit_of_measurement = models.CharField(max_length=100, blank=True, null=True,
                                           help_text="Unit of measurement of the test")
    reference_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True,
                                        help_text="Minimum value considered within the normal range")
    reference_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True,
                                        help_text="Maximum value considered within the normal range")

    lab_test = models.ForeignKey(
        LabTest,
        on_delete=models.PROTECT,
        related_name="observations",
    )
    created_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="created_observations",
    )

    def __str__(self):
        return f"Lab Observation {self.name}: | Test: {self.lab_test.name} | Type: {self.result_type}"

class LabRequest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True, help_text="Is this request active?")

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
    def price(self):
        result = self.tests.aggregate(total=Sum('price'))['total']
        return result or Decimal("0.00")

    def __str__(self):
        return f"Patient {self.visit.patient.fullname} lab request {self.id}: Ordered by: {self.ordered_by.username} | Price: {self.price}"


class LabTestRequest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Is this request active?")

    lab_test = models.ForeignKey(LabTest, on_delete=models.PROTECT, related_name="lab_requests")
    lab_request = models.ForeignKey(LabRequest, on_delete=models.PROTECT, related_name="tests")
    ordered_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.lab_test and self.lab_test.price:
            self.price = self.lab_test.price
        else:
            self.price = Decimal("0.00")
        print("Saved successfully")
        super().save(*args, **kwargs)

    def __str_(self):
        return f"Lab test request: {self.lab_test.name} | Price: {self.price} for {self.lab_request.visit.patient.fullname}"