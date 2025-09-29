from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from apps.earnings.services import compute_daily_earning_usd
from apps.referrals.services import record_direct_first_investment
from decimal import Decimal
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Backfill daily passive earnings for missed days. Use --days to specify how many days back to process.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to backfill (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        days_to_backfill = options['days']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f"DRY RUN MODE - No changes will be made"))
        
        self.stdout.write(f"Backfilling daily earnings for the last {days_to_backfill} days...")
        
        User = get_user_model()
        users = User.objects.filter(is_approved=True)
        
        total_users_processed = 0
        total_earnings_generated = Decimal('0.00')
        
        for user in users:
            # Only process users who have made their first credited deposit
            first_dep = DepositRequest.objects.filter(
                user=user, 
                status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()
            
            if not first_dep:
                continue
            
            # Get the user's current highest day index
            last_earning = PassiveEarning.objects.filter(user=user).order_by('-day_index').first()
            current_day_index = last_earning.day_index if last_earning else 0
            
            # Calculate how many days we should have processed
            days_since_first_deposit = (date.today() - first_dep.processed_at.date()).days
            expected_day_index = min(days_since_first_deposit, 90)  # Cap at 90 days for the standard plan
            
            if expected_day_index <= current_day_index:
                continue  # User is up to date
            
            # Process missing days
            wallet, _ = Wallet.objects.get_or_create(user=user)
            user_total_earnings = Decimal('0.00')
            
            # Handle first investment recording (idempotent)
            flag_key = f"first_investment_recorded:{user.id}"
            already_recorded = wallet.transactions.filter(meta__flag=flag_key).exists()
            if not already_recorded and user.referred_by:
                if not dry_run:
                    record_direct_first_investment(user.referred_by, user, first_dep.amount_usd)
                    Transaction.objects.create(
                        wallet=wallet, 
                        type=Transaction.CREDIT, 
                        amount_usd=Decimal('0.00'), 
                        meta={'type': 'meta', 'flag': flag_key}
                    )
                self.stdout.write(f"  Recorded first investment for referrer of {user.username}")
            
            for day_index in range(current_day_index + 1, expected_day_index + 1):
                metrics = compute_daily_earning_usd(day_index)
                
                if not dry_run:
                    # Create passive earning record
                    PassiveEarning.objects.create(
                        user=user,
                        day_index=day_index,
                        percent=metrics['percent'],
                        amount_usd=metrics['user_share_usd'],
                    )
                    
                    # Update wallet
                    wallet.available_usd = (Decimal(wallet.available_usd) + metrics['user_share_usd']).quantize(Decimal('0.01'))
                    wallet.hold_usd = (Decimal(wallet.hold_usd) + metrics['platform_hold_usd']).quantize(Decimal('0.01'))
                    wallet.save()
                    
                    # Create transaction record
                    Transaction.objects.create(
                        wallet=wallet,
                        type=Transaction.CREDIT,
                        amount_usd=metrics['user_share_usd'],
                        meta={'type': 'passive', 'day_index': day_index, 'percent': str(metrics['percent'])}
                    )
                
                user_total_earnings += metrics['user_share_usd']
                
                self.stdout.write(f"  Day {day_index}: {metrics['user_share_usd']} USD ({metrics['percent']*100}%)")
            
            if user_total_earnings > 0:
                total_users_processed += 1
                total_earnings_generated += user_total_earnings
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Processed {user.username}: {expected_day_index - current_day_index} days, "
                        f"Total: {user_total_earnings} USD"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nBackfill complete!"
                f"\nUsers processed: {total_users_processed}"
                f"\nTotal earnings generated: {total_earnings_generated} USD"
                f"\nTotal earnings in PKR: {total_earnings_generated * 280} PKR"
            )
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING("This was a dry run - no actual changes were made."))
            self.stdout.write("Run without --dry-run to apply these changes.")