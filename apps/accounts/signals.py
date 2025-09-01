from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

from apps.earnings.models_global_pool import GlobalPool
from apps.referrals.services import pay_on_package_purchase
from apps.wallets.models import Wallet, Transaction, DepositRequest

User = get_user_model()


@receiver(post_save, sender=User)
def on_user_approved(sender, instance: User, created, **kwargs):
    # Trigger only when approval status changes to True (admin action)
    if created:
        return

    if instance.is_approved and instance._state.adding is False:
        # 1) Referral payouts on "joining" (approval event)
        pay_on_package_purchase(instance)

        # 2) Add $0.5 to global pool per joining
        pool, _ = GlobalPool.objects.get_or_create(pk=1)
        pool.balance_usd = (Decimal(pool.balance_usd) + Decimal('0.50')).quantize(Decimal('0.01'))
        pool.save()

        # 3) Initial signup deposit credit (PKR 1410) -> converted to USD by admin rate
        try:
            rate = Decimal(str(settings.ADMIN_USD_TO_PKR))
            amount_pkr = Decimal('1410')
            amount_usd = (amount_pkr / rate).quantize(Decimal('0.01'))

            wallet, _ = Wallet.objects.get_or_create(user=instance)

            # Record transaction only (do not credit to available balance)
            Transaction.objects.create(
                wallet=wallet,
                type=Transaction.CREDIT,
                amount_usd=amount_usd,
                meta={
                    'type': 'deposit',
                    'source': 'signup-initial',
                    'tx_id': 'SIGNUP-INIT',
                    'amount_pkr': str(amount_pkr),
                    'non_income': True,
                }
            )

            # Record deposit for traceability without affecting balance
            DepositRequest.objects.create(
                user=instance,
                amount_pkr=amount_pkr,
                amount_usd=amount_usd,
                fx_rate=rate,
                tx_id='SIGNUP-INIT',
                status='CREDITED',
                processed_at=timezone.now(),
            )
        except Exception:
            # Fail silently to avoid breaking approval; admin can adjust manually
            pass