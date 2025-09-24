from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from apps.earnings.services import compute_daily_earning_usd
from apps.earnings.models_global_pool import GlobalPool, GlobalPoolPayout
from apps.referrals.services import record_direct_first_investment
from decimal import Decimal
from datetime import date

class Command(BaseCommand):
    help = 'Compute daily passive earnings for all approved users who have invested (first credited deposit).'

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.filter(is_approved=True)
        pool, _ = GlobalPool.objects.get_or_create(pk=1)
        for u in users:
            # Only start passive earnings after first credited deposit (exclude signup initial)
            # Detect first credited investment (excluding signup init); if present and not yet recorded to referrer milestone, record it once.
            first_dep = DepositRequest.objects.filter(user=u, status='CREDITED').exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()
            if not first_dep:
                continue
            # Link to referrer milestone once per user: use a transaction meta flag to ensure idempotence.
            wallet, _ = Wallet.objects.get_or_create(user=u)
            flag_key = f"first_investment_recorded:{u.id}"
            already = wallet.transactions.filter(meta__flag=flag_key).exists()
            if not already and u.referred_by:
                record_direct_first_investment(u.referred_by, u, first_dep.amount_usd)
                Transaction.objects.create(wallet=wallet, type=Transaction.CREDIT, amount_usd=Decimal('0.00'), meta={'type': 'meta', 'flag': flag_key})

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



            Transaction.objects.create(
                wallet=wallet,
                type=Transaction.CREDIT,
                amount_usd=metrics['user_share_usd'],
                meta={'type': 'passive', 'day_index': next_day, 'percent': str(metrics['percent'])}
            )

            self.stdout.write(self.style.SUCCESS(f"Credited {u.username} day {next_day}: {metrics['user_share_usd']} USD"))

        # Monday global pool logic
        today = date.today()
        if today.weekday() == 0:  # Monday
            # Collect 0.5 from users joined today
            monday_joiners = User.objects.filter(date_joined__date=today, is_approved=True)
            for user in monday_joiners:
                wallet, _ = Wallet.objects.get_or_create(user=user)
                if wallet.available_usd >= Decimal('0.5'):
                    wallet.available_usd = (Decimal(wallet.available_usd) - Decimal('0.5')).quantize(Decimal('0.01'))
                    wallet.save()
                    pool.balance_usd = (Decimal(pool.balance_usd) + Decimal('0.5')).quantize(Decimal('0.01'))
                    pool.save()
                    Transaction.objects.create(
                        wallet=wallet,
                        type=Transaction.DEBIT,
                        amount_usd=Decimal('0.5'),
                        meta={'type': 'global_pool_contribution', 'date': str(today)}
                    )
                    self.stdout.write(self.style.SUCCESS(f"Collected 0.5 USD from {user.username} for global pool"))

            # Distribute the pool
            balance = Decimal(pool.balance_usd)
            if balance > 0:
                all_users = list(User.objects.filter(is_approved=True))
                if all_users:
                    per_user_gross = (balance / Decimal(len(all_users))).quantize(Decimal('0.01'))
                    tax_rate = Decimal('0.20')
                    tax_per_user = (per_user_gross * tax_rate).quantize(Decimal('0.01'))
                    net_per_user = (per_user_gross - tax_per_user).quantize(Decimal('0.01'))

                    for user in all_users:
                        wallet, _ = Wallet.objects.get_or_create(user=user)
                        wallet.available_usd = (Decimal(wallet.available_usd) + net_per_user).quantize(Decimal('0.01'))
                        wallet.save()
                        Transaction.objects.create(
                            wallet=wallet,
                            type=Transaction.CREDIT,
                            amount_usd=net_per_user,
                            meta={
                                'type': 'global_pool_payout',
                                'gross_usd': str(per_user_gross),
                                'tax_usd': str(tax_per_user),
                                'net_usd': str(net_per_user),
                                'total_users': len(all_users),
                                'total_pool_usd': str(balance),
                                'date': str(today)
                            }
                        )

                    # Record payout
                    GlobalPoolPayout.objects.create(
                        amount_usd=balance,
                        meta={
                            'count': len(all_users),
                            'per_user_gross': str(per_user_gross),
                            'per_user_net': str(net_per_user),
                            'tax_rate': str(tax_rate),
                            'date': str(today)
                        }
                    )
                    pool.balance_usd = Decimal('0.00')
                    pool.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'Distributed {balance} USD to {len(all_users)} users '
                        f'(gross: {per_user_gross} USD, net after 20% tax: {net_per_user} USD each)'
                    ))