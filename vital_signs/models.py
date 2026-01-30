from django.db import models
from django_enum import EnumField

from patients.models import Patient
from staff.models import Staff


# Create your models here.
class VitalSigns(models.Model):
    class TemperatureUnitEnum(models.TextChoices):
        CELSIUS = 'C'
        FAHRENHEIT = 'F'
        KELVIN = 'K'
        OTHER = 'other'
    class WeightUnitEnum(models.TextChoices):
        KG = 'kg'
        POUND = 'lb'
        OTHER = 'other'
    class HeightUnitEnum(models.TextChoices):
        METER = 'm'
        FEET = 'feet'
        INCH = 'inch'
        CENTIMETER = 'cm'
        OTHER = 'other'
    class Spo2UnitEnum(models.TextChoices):
        PERCENT = '%'
        OTHER = 'other'
    bp_systolic = models.IntegerField(blank=True, null=True)
    bp_diastolic = models.IntegerField(blank=True, null=True)
    pulse_rate = models.IntegerField(blank=True, null=True)
    respiratory_rate = models.IntegerField(blank=True, null=True)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temperature_unit = EnumField(TemperatureUnitEnum, blank=True, null=True, default=TemperatureUnitEnum.CELSIUS)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    weight_unit = EnumField(WeightUnitEnum, blank=True, null=True, default=WeightUnitEnum.KG)
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    height_unit = EnumField(HeightUnitEnum, blank=True, null=True, default=HeightUnitEnum.METER)
    spo2 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    spo2_unit = EnumField(Spo2UnitEnum, blank=True, null=True, default=Spo2UnitEnum.PERCENT)
    note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    performed_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    # visit = models.ForeignKey(Visit, on_delete=models.CASCADE)