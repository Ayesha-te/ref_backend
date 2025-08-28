from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from apps.earnings.models_global_pool import GlobalPool
from apps.referrals.services import pay_on_package_purchase

User = get_user_model()

@receiver(post_save, sender=User)
def on_user_approved(sender, instance: User, created, **kwargs):
    # Trigger only when approval status changes to True
    if created:
        return
    if instance.is_approved and instance._state.adding is False:
        # Referral payouts on "joining" (approval event)
        pay_on_package_purchase(instance)
        # Add $0.5 to global pool per joining
        pool, _ = GlobalPool.objects.get_or_create(pk=1)
        pool.balance_usd = (Decimal(pool.balance_usd) + Decimal('0.50')).quantize(Decimal('0.01'))
        pool.save()