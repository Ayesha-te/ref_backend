from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from apps.earnings.services import compute_daily_earning_usd
from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction

class Command(BaseCommand):
    help = 'Fix passive earnings: remove future earnings and recalculate wallet balances'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
        parser.add_argument('--recalculate-wallets', action='store_true', help='Recalculate wallet balances from scratch')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        recalculate_wallets = options.get('recalculate_wallets', False)

        User = get_user_model()
        today = timezone.now().date()

        self.stdout.write(self.style.WARNING(f"Today's date: {today}"))
        self.stdout.write(self.style.WARNING(f"Dry run: {dry_run}"))
        
        total_deleted = 0
        total_users_affected = 0

        # Step 1: Remove earnings that are beyond today's date for each user
        self.stdout.write(self.style.WARNING("\n=== Step 1: Removing future earnings ==="))
        
        users = User.objects.filter(is_approved=True)
        
        for u in users:
            # Get first credited deposit
            first_dep = DepositRequest.objects.filter(
                user=u, 
                status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()
            
            if not first_dep or not first_dep.processed_at:
                continue
            
            first_dep_date = first_dep.processed_at.date()
            days_since_first_deposit = (today - first_dep_date).days
            max_valid_day_index = days_since_first_deposit + 1
            
            # Find earnings beyond the valid range
            invalid_earnings = PassiveEarning.objects.filter(
                user=u,
                day_index__gt=max_valid_day_index
            )
            
            if invalid_earnings.exists():
                count = invalid_earnings.count()
                total_amount = sum(e.amount_usd for e in invalid_earnings)
                
                self.stdout.write(
                    self.style.WARNING(
                        f"User {u.username}: Found {count} future earnings (days > {max_valid_day_index}), "
                        f"total amount: {total_amount} USD"
                    )
                )
                
                if not dry_run:
                    # Delete the invalid earnings
                    invalid_earnings.delete()
                    
                    # Delete corresponding transactions
                    wallet = Wallet.objects.filter(user=u).first()
                    if wallet:
                        deleted_txs = wallet.transactions.filter(
                            type=Transaction.CREDIT,
                            meta__type='passive',
                            meta__day_index__gt=max_valid_day_index
                        ).delete()
                        self.stdout.write(f"  Deleted {deleted_txs[0]} transactions")
                
                total_deleted += count
                total_users_affected += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Step 1 complete: Deleted {total_deleted} future earnings from {total_users_affected} users"
            )
        )

        # Step 2: Recalculate wallet balances if requested
        if recalculate_wallets:
            self.stdout.write(self.style.WARNING("\n=== Step 2: Recalculating wallet balances ==="))
            
            for u in users:
                wallet = Wallet.objects.filter(user=u).first()
                if not wallet:
                    continue
                
                # Calculate income from passive earnings
                passive_total = PassiveEarning.objects.filter(user=u).aggregate(
                    total=db_transaction.models.Sum('amount_usd')
                )['total'] or Decimal('0')
                
                # Calculate hold from passive earnings
                hold_total = Decimal('0')
                for earning in PassiveEarning.objects.filter(user=u):
                    metrics = compute_daily_earning_usd(earning.day_index)
                    hold_total += metrics.get('platform_hold_usd', Decimal('0'))
                
                old_income = wallet.income_usd
                old_hold = wallet.hold_usd
                
                if old_income != passive_total or old_hold != hold_total:
                    self.stdout.write(
                        f"User {u.username}: "
                        f"Income {old_income} -> {passive_total}, "
                        f"Hold {old_hold} -> {hold_total}"
                    )
                    
                    if not dry_run:
                        wallet.income_usd = passive_total
                        wallet.hold_usd = hold_total
                        wallet.save()
                        self.stdout.write(self.style.SUCCESS(f"  ✅ Updated wallet for {u.username}"))

        # Step 3: Show summary
        self.stdout.write(self.style.WARNING("\n=== Summary ==="))
        
        for u in users:
            first_dep = DepositRequest.objects.filter(
                user=u, 
                status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()
            
            if not first_dep or not first_dep.processed_at:
                continue
            
            first_dep_date = first_dep.processed_at.date()
            days_since_first_deposit = (today - first_dep_date).days
            max_valid_day_index = days_since_first_deposit + 1
            
            earnings_count = PassiveEarning.objects.filter(user=u).count()
            last_earning = PassiveEarning.objects.filter(user=u).order_by('-day_index').first()
            last_day = last_earning.day_index if last_earning else 0
            
            wallet = Wallet.objects.filter(user=u).first()
            wallet_income = wallet.income_usd if wallet else Decimal('0')
            
            status = "✅" if last_day == max_valid_day_index else "⚠️"
            
            self.stdout.write(
                f"{status} {u.username}: "
                f"First deposit: {first_dep_date}, "
                f"Days since: {days_since_first_deposit}, "
                f"Earnings: {earnings_count} (up to day {last_day}), "
                f"Should be: {max_valid_day_index}, "
                f"Wallet income: {wallet_income} USD"
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️ This was a DRY RUN. No changes were made. "
                    "Run without --dry-run to apply changes."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\n✅ Fix complete! Now run: python manage.py backfill_passive_earnings"
                )
            )