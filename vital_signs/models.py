from django.db import models
from django_enum import EnumField

from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class VitalSign(models.Model):
    class TemperatureUnitEnum(models.TextChoices):
        CELSIUS = "C", "Celsius"
        FAHRENHEIT = "F", "Fahrenheit"
        KELVIN = "K", "Kelvin"

    class WeightUnitEnum(models.TextChoices):
        KG = "K", "Kg"
        POUND = "P", "Lb"
        OTHER = "O", "Other"

    class HeightUnitEnum(models.TextChoices):
        METER = "M", "M"
        FEET = "FT", "Ft"
        CENTIMETER = "C", "Cm"
        OTHER = "O", "Other"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    bp_systolic = models.IntegerField(blank=True, null=True, help_text="Systolic pressure in mmHg (the top number).")
    bp_diastolic = models.IntegerField(blank=True, null=True, help_text="Diastolic pressure in mmHg (the bottom number).")
    pulse_rate = models.IntegerField(blank=True, null=True, help_text="Heart rate in beats per minute (BPM).")
    respiratory_rate = models.IntegerField(blank=True, null=True, help_text="Breaths per minute.")
    temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Body temperature reading.")
    temperature_unit = EnumField(TemperatureUnitEnum, blank=True, null=True, default=TemperatureUnitEnum.CELSIUS, help_text="Scale used for the temperature reading.")
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Patient's measured weight.")
    weight_unit = EnumField(WeightUnitEnum, blank=True, null=True, default=WeightUnitEnum.KG, help_text="Unit of measurement for weight.")
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Patient's measured height.")
    height_unit = EnumField(HeightUnitEnum, blank=True, null=True, default=HeightUnitEnum.METER, help_text="Unit of measurement for height.")
    spo2 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Oxygen saturation percentage (0-100).")
    notes = models.TextField(blank=True, help_text="Any distinct clinical observations or irregularities noted during measurement.")
    is_active = models.BooleanField(default=True)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vital_signs')
    recorded_by = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='recorded_vital_signs')
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name='vital_signs')

    def __str__(self):
        return f"Patient {self.patient.fullname} vital signs: Blood Pressure: {self.bp_systolic}/{self.bp_diastolic} mmhg | Pulse rate: {self.pulse_rate} bpm | Respiratory rate: {self.respiratory_rate} bpm | temperature: {self.temperature} {self.temperature_unit} | Weight: {self.weight} {self.weight_unit} | Height: {self.height} {self.height_unit}"