from django.db import models
from django_enum import EnumField


# Create your models here.
class Patient(models.Model):
    class SexEnum(models.TextChoices):
        MALE = 'M'
        FEMALE = 'F'
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    sex = EnumField(SexEnum)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)