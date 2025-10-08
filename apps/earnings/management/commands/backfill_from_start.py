from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from apps.earnings.services import compute_daily_earning_usd
from apps.referrals.services import record_direct_first_investment
from decimal import Decimal
from datetime import date
from django.utils import timezone

class Command(BaseCommand):
    help = 'Backfill passive earnings from first deposit date until today for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Process only specific user ID'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options.get('user_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made\n"))
        
        self.stdout.write(self.style.SUCCESS("="*70))
        self.stdout.write(self.style.SUCCESS("📊 BACKFILL PASSIVE EARNINGS FROM START"))
        self.stdout.write(self.style.SUCCESS("="*70))
        self.stdout.write("")
        
        User = get_user_model()
        
        if user_id:
            users = User.objects.filter(id=user_id, is_approved=True)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f"❌ User with ID {user_id} not found or not approved"))
                return
        else:
            users = User.objects.filter(is_approved=True)
        
        total_users_processed = 0
        total_earnings_generated = Decimal('0.00')
        today = date.today()
        
        for user in users:
            # Only process users who have made their first credited deposit (excluding signup initial)
            first_dep = DepositRequest.objects.filter(
                user=user, 
                status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()
            
            if not first_dep:
                self.stdout.write(f"⏭️  Skipping {user.username} - No credited deposits")
                continue
            
            # Calculate days since first deposit
            first_deposit_date = first_dep.processed_at.date()
            days_since_first_deposit = (today - first_deposit_date).days
            
            if days_since_first_deposit < 0:
                self.stdout.write(f"⚠️  Skipping {user.username} - Deposit date is in the future")
                continue
            
            # Get the user's current highest day index
            last_earning = PassiveEarning.objects.filter(user=user).order_by('-day_index').first()
            current_day_index = last_earning.day_index if last_earning else 0
            
            # Calculate expected day index (capped at 90 days for standard plan)
            expected_day_index = min(days_since_first_deposit, 90)
            
            if expected_day_index <= current_day_index:
                self.stdout.write(f"✅ {user.username} is up to date (day {current_day_index}/90)")
                continue
            
            # Display user info
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS(f"👤 Processing: {user.username}"))
            self.stdout.write(f"   First Deposit: {first_deposit_date} (${first_dep.amount_usd})")
            self.stdout.write(f"   Days Since Deposit: {days_since_first_deposit}")
            self.stdout.write(f"   Current Day Index: {current_day_index}")
            self.stdout.write(f"   Expected Day Index: {expected_day_index}")
            self.stdout.write(f"   Days to Process: {expected_day_index - current_day_index}")
            
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
                self.stdout.write(f"   📝 Recorded first investment for referrer of {user.username}")
            
            # Process each missing day
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
                    
                    # Update wallet - passive earnings go to income_usd, NOT available_usd
                    # available_usd is ONLY for deposits (80% of deposit amount)
                    # income_usd is for passive + referral + milestone + global pool earnings
                    wallet.income_usd = (Decimal(wallet.income_usd) + metrics['user_share_usd']).quantize(Decimal('0.01'))
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
                
                # Show progress every 10 days
                if day_index % 10 == 0 or day_index == expected_day_index:
                    self.stdout.write(f"   💰 Day {day_index}: ${metrics['user_share_usd']} ({metrics['percent']*100}%)")
            
            if user_total_earnings > 0:
                total_users_processed += 1
                total_earnings_generated += user_total_earnings
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   ✅ Completed: {expected_day_index - current_day_index} days processed, "
                        f"Total: ${user_total_earnings} (₨{float(user_total_earnings) * 280:,.2f})"
                    )
                )
        
        # Final summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("="*70))
        self.stdout.write(self.style.SUCCESS("📈 BACKFILL SUMMARY"))
        self.stdout.write(self.style.SUCCESS("="*70))
        self.stdout.write(self.style.SUCCESS(f"👥 Users Processed: {total_users_processed}"))
        self.stdout.write(self.style.SUCCESS(f"💵 Total Earnings Generated: ${total_earnings_generated}"))
        self.stdout.write(self.style.SUCCESS(f"💵 Total Earnings (PKR): ₨{float(total_earnings_generated) * 280:,.2f}"))
        
        if dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("🔍 This was a DRY RUN - no actual changes were made."))
            self.stdout.write(self.style.WARNING("Run without --dry-run to apply these changes."))
        
        self.stdout.write(self.style.SUCCESS("="*70))