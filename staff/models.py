from django.contrib.auth.models import AbstractUser
from django.db import models
from django_enum import EnumField
from django.utils import timezone

# Create your models here.
class Staff(AbstractUser):
    class RoleEnum(models.TextChoices):
        ADMIN = 'ADMIN'
        DOCTOR = 'DOCTOR'
        NURSE = 'NURSE'
        LABORATORY = 'LABORATORY'
        RECEPTION = 'RECEPTION'
        OTHER = 'OTHER'
    
    date = models.DateTimeField(default=timezone.now)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    role = EnumField(RoleEnum)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    REQUIRED_FIELDS = ['role']

    def __str__(self):
        return f"{self.username}: {self.phone} <{self.role.name}>"
