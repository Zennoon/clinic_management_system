from django.db import models
from django_enum import EnumField

from patients.models import Patient
from staff.models import Staff


# Create your models here.
class Prescription(models.Model):
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="prescriptions")
    prescribed_by = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="prescribed_prescriptions")

    def __str__(self):
        return f"Prescription: {self.patient.fullname} prescribed by: {self.prescribed_by.username} at {self.created_at}"

class Medication(models.Model):
    class RouteEnum(models.TextChoices):
        ORAL = 'PO'
        INTRAVENOUS = 'IV'
        INTRAMUSCULAR = 'IM'
        SUBCUTANEOUS = 'SUBCUTANEOUS'
        TOPICAL = 'TOPICAL'
        INHALATION = 'INHALATION'
        OPHTHALMIC = 'OPH'
        OTIC = 'OTIC'
        RECTAL = 'RECTAL'
        SUBLINGUAL = 'SUBLINGUAL'
        OTHER = 'OTHER'
    class FrequencyEnum(models.TextChoices):
        QD = 'QD'
        BID = 'BID'
        TID = 'TID'
        QID = 'QID'
        PRN = 'PRN'
        STAT = 'STAT'
        WEEKLY = 'WEEKLY'
        BIWEEKLY = 'BIWEEKLY'
        OTHER = 'OTHER'

    name = models.CharField(max_length=200)
    strength = models.CharField(max_length=200)
    route = EnumField(RouteEnum)
    frequency = EnumField(FrequencyEnum)
    days = models.IntegerField()
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="medications")
    prescribed_by = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="prescribed_medications")
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="medications")

    def __str__(self):
        return f"Medication {self.name} {self.strength} {self.route} taken {self.frequency.name} for {self.days} days prescribed for {self.patient.fullname} by {self.prescribed_by.username} at {self.created_at}"

