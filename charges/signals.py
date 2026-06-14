from django.dispatch import receiver
from django.db.models.signals import post_save

from charges.models import Charge


@receiver(post_save, sender=Charge)
def update_visit_status(_, instance, **kwargs):
    visit = instance.visit
    visit.visit_status = visit.derive_visit_status()
    visit.save(update_fields=["visit_status"])
