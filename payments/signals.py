from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from charges.models import Charge
from payments.models import Payment


@receiver(post_save, sender=Payment)
def check_charge_status(_, instance, **kwargs):
    charge = instance.charge
    total_paid = charge.payments.aggregate(Sum("amount"))["amount__sum"] or 0
    if total_paid >= charge.amount:
        Charge.objects.filter(pk=charge.pk).update(
            charge_status=Charge.ChargeStatusEnum.SETTLED
        )
    else:
        Charge.objects.filter(pk=charge.pk).update(
            charge_status=Charge.ChargeStatusEnum.PENDING
        )

@receiver(post_save, sender=Payment)
def update_visit_status(_, instance, **kwargs):
    visit = instance.charge.visit
    visit.visit_status = visit.derive_visit_status()
    visit.save(update_fields=["visit_status"])
