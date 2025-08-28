from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction
from apps.earnings.models import PassiveEarning
from apps.earnings.services import compute_daily_earning_usd
from apps.earnings.models_global_pool import GlobalPool
from decimal import Decimal

class Command(BaseCommand):
    help = 'Compute daily passive earnings for all approved users'

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.filter(is_approved=True)
        pool, _ = GlobalPool.objects.get_or_create(pk=1)
        for u in users:
            wallet, _ = Wallet.objects.get_or_create(user=u)
            # find next day index
            last = PassiveEarning.objects.filter(user=u).order_by('-day_index').first()
            next_day = (last.day_index + 1) if last else 1
            metrics = compute_daily_earning_usd(next_day)

            PassiveEarning.objects.create(
                user=u,
                day_index=next_day,
                percent=metrics['percent'],
                amount_usd=metrics['user_share_usd'],
            )
            # credit user share
            wallet.available_usd = (Decimal(wallet.available_usd) + metrics['user_share_usd']).quantize(Decimal('0.01'))
            wallet.hold_usd = (Decimal(wallet.hold_usd) + metrics['platform_hold_usd']).quantize(Decimal('0.01'))
            wallet.save()

            # accumulate global pool
            pool.balance_usd = (Decimal(pool.balance_usd) + metrics['global_pool_usd']).quantize(Decimal('0.01'))
            pool.save()

            Transaction.objects.create(
                wallet=wallet,
                type=Transaction.CREDIT,
                amount_usd=metrics['user_share_usd'],
                meta={'type': 'passive', 'day_index': next_day, 'percent': str(metrics['percent'])}
            )

            self.stdout.write(self.style.SUCCESS(f"Credited {u.username} day {next_day}: {metrics['user_share_usd']} USD"))