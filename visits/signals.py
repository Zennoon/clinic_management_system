from django.db.models.signals import post_save
from django.utils import timezone
from django.dispatch import receiver

from visits.models import Visit, VisitStatusLog


@receiver(post_save, sender=Visit)
def create_status_log(_, instance, created, **kwargs):
    last_log = instance.status_history.first()

    if created or (last_log and last_log.status != instance.visit_status):
        VisitStatusLog.objects.create(
            visit=instance,
            status=instance.visit_status,
        )
        Visit.objects.filter(pk=instance.pk).update(current_status_since=timezone.now())