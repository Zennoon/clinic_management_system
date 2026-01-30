from django.db import models
from django_enum import EnumField

from staff.models import Staff


# Create your models here.
class TestGroup(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_test_groups',
    )

    def __str__(self):
        return f"{self.name}: {self.price}"


class Test(models.Model):
    class TestTypeEnum(models.TextChoices):
        CATEGORICAL = 'CATEGORICAL'
        NUMERICAL = 'NUMERICAL'

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    test_type = EnumField(TestTypeEnum)
    is_active = models.BooleanField(default=True)

    # Only have a value for numerical tests
    unit_of_measurement = models.CharField(max_length=100, null=True, blank=True)
    reference_min = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reference_max = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    test_group = models.ForeignKey(TestGroup, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        related_name='created_tests',
        null=True,
    )

    def __str__(self):
        return f"{self.name}: {self.test_group} {self.price}"

class LabRequest(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tests = models.ManyToManyField(Test, through=TestGroup)


class LabTestRequest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tests = models.ForeignKey(Test, on_delete=models.CASCADE)
    ordered_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
    )
