from django.db import models
from django_enum import EnumField

from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class TestGroup(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100, help_text="Name of the group")
    price = models.DecimalField(max_digits=5, decimal_places=2, help_text="Price of the tests in this group as an aggregate.")
    is_active = models.BooleanField(default=True, help_text="Is this group active?")

    created_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="created_test_groups",
    )

    def __str__(self):
        return f"Test group {self.name}: Price {self.price}"


class Test(models.Model):
    class TestTypeEnum(models.TextChoices):
        CATEGORICAL = 'C', 'Categorical'
        NUMERICAL = 'N', 'Numerical'

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100, help_text="Name of the test")
    price = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Price of the test")
    test_type = EnumField(TestTypeEnum)
    is_active = models.BooleanField(default=True, help_text="Is this test active?")

    unit_of_measurement = models.CharField(max_length=100, blank=True, null=True, help_text="Unit of measurement of the test")
    reference_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Minimum value considered within the normal range")
    reference_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Maximum value considered within the normal range")

    test_group = models.ForeignKey(TestGroup, on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
        related_name="created_tests",
    )

    def __str__(self):
        return f"Test {self.name}: Price {self.price}"

class LabRequest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    price = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, help_text="Is this request active?")

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="lab_requests",
    )
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
    def total_price(self):
        return sum(test.price for test in self.tests.all())

    def __str__(self):
        return f"Patient {self.patient.fullname} lab request {self.id}: Ordered by: {self.ordered_by.username} | Price: {self.total_price}"


class LabRequestTest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Is this request active?")

    test = models.ForeignKey(Test, on_delete=models.PROTECT, related_name="lab_requests")
    lab_request = models.ForeignKey(LabRequest, on_delete=models.PROTECT, related_name="tests")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="lab_request_tests")
    ordered_by = models.ForeignKey(
        Staff,
        on_delete=models.PROTECT,
    )

    @property
    def price(self):
        return round(self.test.price or self.test.test_group.price, 2)

    def __str_(self):
        return f"Patient {self.patient.fullname} lab request test: {self.test.name} price"