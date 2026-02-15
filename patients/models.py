from django.db import models
from django_enum import EnumField
from django.utils import timezone
from datetime import datetime


# Create your models here.
class Patient(models.Model):
    class SexEnum(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
    class RegionEnum(models.TextChoices):
        ADDIS_ABABA = 'ADDIS_ABABA', 'Addis Ababa'
        AFAR = 'AFAR', 'Afar'
        AMHARA = 'AMHARA', 'Amhara'
        BENISHANGUL_GUMUZ = 'BENISHANGUL_GUMUZ', 'Benishangul Gumuz'
        CENTRAL_ETHIOPIA = 'CENTRAL_ETHIOPIA', 'Central Ethiopia'
        DIRE_DAWA = 'DIRE_DAWA', 'Dire Dawa'
        GAMBELA = 'GAMBELA', 'Gambela'
        HARARI = 'HARARI', 'Harari'
        OROMIA = 'OROMIA', 'Oromia'
        SIDAMA = 'SIDAMA', 'Sidama'
        SOMALI = 'SOMALI', 'Somali'
        SOUTH_ETHIOPIA = 'SOUTH_ETHIOPIA', 'South Ethiopia'
        SOUTH_WEST_ETHIOPIA = 'SOUTH_WEST_ETHIOPIA', 'South West Ethiopia'
        TIGRAY = 'TIGRAY', 'Tigray'
        OTHER = 'OTHER', 'Other'

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    first_name = models.CharField(max_length=100, help_text="First name of the patient")
    last_name = models.CharField(max_length=100, help_text="Last name of the patient")
    date_of_birth = models.DateField(help_text="Date of birth of the patient")
    sex = EnumField(SexEnum)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Weight of the patient")
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Height of the patient")
    phone = models.CharField(max_length=20, help_text="Patient's phone number", null=True, blank=True)
    region = EnumField(RegionEnum, help_text="Region where patient resides")
    city = models.CharField(max_length=100, help_text="City where the patient resides")
    is_active = models.BooleanField(default=True, help_text="Whether the patient is active. Used for soft deletes")

    @property
    def fullname(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def age(self):
        return timezone.now().year - self.date_of_birth.year
    
    @property
    def address(self):
        return f"{self.city}, {self.region.label}"

    @property
    def bmi(self):
        if self.weight and self.height:
            if self.height > 100:
                self.height = self.height / 100
            return round(self.weight / (self.height * self.height), 2)
        return 0

    def needs_to_pay_visit_fee(self):
        last_visit = self.visits.filter(visit_status='FIN').order_by('-created_at').first()
        if last_visit:
            diff = timezone.now() - last_visit.created_at
            return diff.days > 10
        return True

    def __str__(self):
        return f"Patient {self.id}: {self.fullname} | Age: {self.age} | Region: {self.region} | City: {self.city} | Weight: {self.weight} | Height: {self.height} | BMI: {self.bmi}"

