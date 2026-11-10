from black.output import out
from django.db import models
from django.db.models import Q, ExpressionWrapper, BooleanField
from django_enum import EnumField
from django.utils import timezone

from staff.models import Staff
from staff.utils import convert_height_to_cms, convert_weight_to_kg
from visits.models import Visit


# Create your models here.
class VitalSignQuerySet(models.QuerySet):
    def with_operational(self):
        return self.annotate(
            is_operational_annotated=ExpressionWrapper(
                Q(is_active=True) & Q(visit__is_active=True) & Q(visit__patient__is_active=True),
                output_field=BooleanField()
            )
        )
    

class VitalSignManager(models.Manager):
    def get_queryset(self):
        return VitalSignQuerySet(self.model, self._db).with_operational()


class VitalSign(models.Model):
    class TemperatureUnitEnum(models.TextChoices):
        CELSIUS = "°C", "Celsius"
        FAHRENHEIT = "°F", "Fahrenheit"
        KELVIN = "K", "Kelvin"

    class WeightUnitEnum(models.TextChoices):
        KILOGRAMS = "Kg", "Kilograms"
        GRAMS= "Gm", "Grams"
        POUNDS = "Lb", "Pounds"
        STONES = "St", "Stones"
        OUNCES = "Oz", "Ounces"
        OTHER = "Other", "Other"

    class HeightUnitEnum(models.TextChoices):
        METERS = "Mt", "Meters"
        FEET = "Ft", "Feet"
        INCHES = "In", "Inches"
        CENTIMETERS = "Cm", "Centimeters"
        OTHER = "Other", "Other"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    date = models.DateTimeField(default=timezone.now)
    bp_systolic = models.IntegerField(blank=True, null=True, help_text="Systolic pressure in mmHg (the top number).")
    bp_diastolic = models.IntegerField(blank=True, null=True, help_text="Diastolic pressure in mmHg (the bottom number).")
    pulse_rate = models.IntegerField(blank=True, null=True, help_text="Heart rate in beats per minute (BPM).")
    respiratory_rate = models.IntegerField(blank=True, null=True, help_text="Breaths per minute.")
    temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Body temperature reading.")
    temperature_unit = EnumField(TemperatureUnitEnum, blank=True, null=True, default=TemperatureUnitEnum.CELSIUS, help_text="Scale used for the temperature reading.")
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Patient's measured weight.")
    weight_unit = EnumField(WeightUnitEnum, blank=True, null=True, default=WeightUnitEnum.KILOGRAMS, help_text="Unit of measurement for weight.")
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Patient's measured height.")
    height_unit = EnumField(HeightUnitEnum, blank=True, null=True, default=HeightUnitEnum.CENTIMETERS, help_text="Unit of measurement for height.")
    spo2 = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Oxygen saturation percentage (0-100).")
    notes = models.TextField(blank=True, help_text="Any distinct clinical observations or irregularities noted during measurement.")
    is_active = models.BooleanField(default=True)

    recorded_by = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='recorded_vital_signs')
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name='vital_signs')
    
    objects = VitalSignManager()
    
    @property
    def is_operational(self):
        return self.is_active and self.visit.is_operational
    
    def update_patient(self):
        patient = self.visit.patient
        if self.weight:
            patient.weight = convert_weight_to_kg(self.weight, self.weight_unit)
        if self.height:
            patient.height = convert_height_to_cms(self.height, self.height_unit)
        patient.save()
        return patient
        
    
    def __str__(self):
        return f"Patient {self.visit.patient.fullname} vital signs: Blood Pressure: {self.bp_systolic}/{self.bp_diastolic} mmhg | Pulse rate: {self.pulse_rate} bpm | Respiratory rate: {self.respiratory_rate} bpm | temperature: {self.temperature} {self.temperature_unit} | Weight: {self.weight} {self.weight_unit} | Height: {self.height} {self.height_unit}"