from django.dispatch import receiver
from django.db.models.signals import post_save

from vital_signs.models import VitalSign


@receiver(post_save, sender=VitalSign)
def update_visit_status(_, instance, created, **kwargs):
    if created:
        visit = instance.visit
        visit.visit_status = visit.derive_visit_status()
        visit.save(update_fields=["visit_status"])
