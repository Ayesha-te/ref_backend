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
        # 1) Referral payouts on "joining" (approval event) - now percentage of signup payment
        pay_on_package_purchase(instance)

        # 2) Add 0.5% of signup payment to global pool ONLY if user joins on Monday
        current_day = timezone.now().weekday()  # Monday = 0, Sunday = 6
        if current_day == 0:  # Only on Monday
            pool, _ = GlobalPool.objects.get_or_create(pk=1)
            try:
                signup_fee_pkr = Decimal(str(settings.SIGNUP_FEE_PKR))
                rate = Decimal(str(settings.ADMIN_USD_TO_PKR))
                join_base_usd = (signup_fee_pkr / rate).quantize(Decimal('0.01'))
                # 0.5% of signup fee for Monday joiners
                monday_contribution = (join_base_usd * Decimal('0.005')).quantize(Decimal('0.01'))
            except Exception:
                monday_contribution = Decimal('0.00')  # No fallback - only Monday joiners contribute
            
            if monday_contribution > 0:
                pool.balance_usd = (Decimal(pool.balance_usd) + monday_contribution).quantize(Decimal('0.01'))
                pool.save()
                
                # Record the Monday joining contribution in transaction
                wallet, _ = Wallet.objects.get_or_create(user=instance)
                Transaction.objects.create(
                    wallet=wallet,
                    type=Transaction.DEBIT,  # This is taken from their signup fee
                    amount_usd=monday_contribution,
                    meta={
                        'type': 'global_pool_contribution',
                        'source': 'monday_joining',
                        'signup_fee_pkr': str(signup_fee_pkr),
                        'contribution_rate': '0.5%',
                        'day_of_week': 'Monday'
                    }
                )

        # 3) Initial signup deposit credit -> PKR to USD by admin rate
        try:
            rate = Decimal(str(settings.ADMIN_USD_TO_PKR))
            amount_pkr = Decimal(str(settings.SIGNUP_FEE_PKR))
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