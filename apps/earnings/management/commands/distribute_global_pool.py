from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.earnings.models_global_pool import GlobalPool, GlobalPoolPayout

class Command(BaseCommand):
    help = 'Distribute global pool equally among all approved users (run weekly Monday)'

    def handle(self, *args, **options):
        User = get_user_model()
        users = list(User.objects.filter(is_approved=True))
        if not users:
            self.stdout.write('No approved users to distribute to.')
            return
        pool, _ = GlobalPool.objects.get_or_create(pk=1)
        balance = Decimal(pool.balance_usd)
        if balance <= 0:
            self.stdout.write('No pool balance to distribute.')
            return
        per_user = (balance / Decimal(len(users))).quantize(Decimal('0.01'))
        if per_user <= 0:
            self.stdout.write('Per user amount is zero.')
            return
        # Reset pool and record payout
        GlobalPoolPayout.objects.create(amount_usd=balance, meta={'count': len(users)})
        pool.balance_usd = Decimal('0.00')
        pool.save()
        self.stdout.write(self.style.SUCCESS(f'Distributed {balance} USD to {len(users)} users (~{per_user} each)'))