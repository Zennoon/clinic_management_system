from django.contrib.auth.models import User
from django.db import models
from django_enum import EnumField

from patients.models import Patient
from staff.models import Staff
from visits.models import Visit


# Create your models here.
class Prescription(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    prescribed_by = models.ForeignKey(Staff, on_delete=models.PROTECT)
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT)

    def __str__(self):
        return f"Patient {self.visit.patient.fullname} prescription {self.id}: prescribed by: {self.prescribed_by.username}"

class Medication(models.Model):
    class RouteEnum(models.TextChoices):
        ORAL = 'PO', 'Orally'
        INTRAVENOUS = 'IV', 'Intravenous'
        INTRAMUSCULAR = 'IM', 'Intramuscular'
        SUBCUTANEOUS = 'SUBC', 'Subcutaneous'
        TOPICAL = 'TOP', 'Topical'
        INHALATION = 'INHALATION', 'Inhalation'
        OPHTHALMIC = 'OPH', 'Ophthalmic'
        OTIC = 'OTIC', 'Otic'
        RECTAL = 'RECTAL', 'Rectal'
        SUBLINGUAL = 'SUBLINGUAL', 'Sublingual'
        OTHER = 'OTHER', 'Other'
    class FrequencyEnum(models.TextChoices):
        QD = 'QD', 'Once per day'
        BID = 'BID', 'Twice per day'
        TID = 'TID', 'Three times per day'
        QID = 'QID', 'Four times per day'
        WEEKLY = 'WEEKLY', 'Once per week'
        BIWEEKLY = 'BIWEEKLY', 'Twice per week'
        PRN = 'PRN', 'As needed'
        STAT = 'STAT', 'Immediately'

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=200)
    strength = models.CharField(max_length=200)
    route = EnumField(RouteEnum)
    frequency = EnumField(FrequencyEnum)
    days = models.IntegerField()
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    prescribed_by = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="prescribed_medications")
    prescription = models.ForeignKey(Prescription, on_delete=models.PROTECT, related_name="medications")

    def __str__(self):
        return f"Patient {self.prescription.visit.patient.fullname} medication {self.name}: prescribed by: {self.prescribed_by.username}"