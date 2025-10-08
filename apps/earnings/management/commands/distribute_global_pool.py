from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.earnings.models_global_pool import GlobalPool, GlobalPoolPayout
from apps.wallets.models import Wallet, Transaction

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
        
        per_user_gross = (balance / Decimal(len(users))).quantize(Decimal('0.01'))
        if per_user_gross <= 0:
            self.stdout.write('Per user amount is zero.')
            return
        
        # Apply 20% withdrawal tax
        withdrawal_tax_rate = Decimal('0.20')
        tax_per_user = (per_user_gross * withdrawal_tax_rate).quantize(Decimal('0.01'))
        net_per_user = (per_user_gross - tax_per_user).quantize(Decimal('0.01'))
        
        # Distribute to each user's wallet
        distributed_count = 0
        for user in users:
            wallet, _ = Wallet.objects.get_or_create(user=user)
            wallet.available_usd = (Decimal(wallet.available_usd) + net_per_user).quantize(Decimal('0.01'))
            wallet.save()
            
            # Record transaction
            Transaction.objects.create(
                wallet=wallet,
                type=Transaction.CREDIT,
                amount_usd=net_per_user,
                meta={
                    'type': 'global_pool_payout',
                    'gross_usd': str(per_user_gross),
                    'tax_usd': str(tax_per_user),
                    'net_usd': str(net_per_user),
                    'total_users': len(users),
                    'total_pool_usd': str(balance),
                }
            )
            distributed_count += 1
        
        # Record payout and reset pool
        GlobalPoolPayout.objects.create(
            amount_usd=balance, 
            meta={
                'count': len(users),
                'per_user_gross': str(per_user_gross),
                'per_user_net': str(net_per_user),
                'tax_rate': str(withdrawal_tax_rate),
                'distributed_count': distributed_count,
            }
        )
        pool.balance_usd = Decimal('0.00')
        pool.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'Distributed {balance} USD to {distributed_count} users '
            f'(gross: {per_user_gross} USD, net after 20% tax: {net_per_user} USD each)'
        ))