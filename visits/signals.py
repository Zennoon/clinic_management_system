from django.db.models.signals import post_save
from django.utils import timezone
from django.dispatch import receiver
from constance import config

from charges.models import Charge
from visits.models import Consultation, Review, Visit, VisitStatusLog


@receiver(post_save, sender=Visit)
def create_status_log(_, instance, created, **kwargs):
    last_log = instance.status_history.first()

    if created or (last_log and last_log.status != instance.visit_status):
        VisitStatusLog.objects.create(
            visit=instance,
            status=instance.visit_status,
        )
        Visit.objects.filter(pk=instance.pk).update(current_status_since=timezone.now())


@receiver(post_save, sender=Visit)
def create_consultation_charge(_, instance, created, **kwargs):
    if created:
        consultation_charge = instance.charges.filter(
            charge_type=Charge.ChargeTypeEnum.CONSULTATION
        ).first()
        print("Consultation charge:")
        print(consultation_charge)
        if not consultation_charge:
            consultation_charge = Charge.objects.create(
                charge_type=Charge.ChargeTypeEnum.CONSULTATION,
                amount=config.CONSULTATION_FEE,
                visit=instance,
                issuer=instance.created_by,
            )
        print(consultation_charge)


@receiver(post_save, sender=Consultation)
def update_visit_status_on_consultation_creation(_, instance, created, **kwargs):
    if created:
        visit = instance.visit
        visit.visit_status = instance.derive_visit_status()
        visit.save(update_fields=["visit_status"])


@receiver(post_save, sender=Review)
def update_visit_status_on_review_creation(_, instance, created, **kwargs):
    if created:
        visit = instance.visit
        visit.visit_status = instance.derive_visit_status()
        visit.save(update_fields=["visit_status"])
