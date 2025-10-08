from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from apps.earnings.services import compute_daily_earning_usd
from apps.earnings.models_global_pool import GlobalPool
from apps.referrals.services import record_direct_first_investment
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Compute daily passive earnings for all approved users who have invested (first credited deposit).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backfill-days',
            type=int,
            default=1,
            help='Number of days to backfill (default: 1 for today only)'
        )
        parser.add_argument(
            '--backfill-from-date',
            type=str,
            help='Backfill from specific date (YYYY-MM-DD format). Overrides --backfill-days'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        backfill_days = options['backfill_days']
        backfill_from_date = options.get('backfill_from_date')
        dry_run = options['dry_run']

        # Calculate how many days to process
        if backfill_from_date:
            try:
                from_date = datetime.strptime(backfill_from_date, '%Y-%m-%d').date()
                today = timezone.now().date()
                backfill_days = (today - from_date).days + 1
                self.stdout.write(self.style.WARNING(f"📅 Backfilling from {from_date} to {today} ({backfill_days} days)"))
            except ValueError:
                self.stdout.write(self.style.ERROR("Invalid date format. Use YYYY-MM-DD"))
                return
        else:
            self.stdout.write(self.style.WARNING(f"📅 Processing {backfill_days} day(s) of earnings"))

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made"))

        User = get_user_model()
        users = User.objects.filter(is_approved=True)
        pool, _ = GlobalPool.objects.get_or_create(pk=1)
        
        total_users_processed = 0
        total_earnings_generated = 0
        total_amount_usd = Decimal('0.00')

        for u in users:
            # Only start passive earnings after first credited deposit (exclude signup initial)
            first_dep = DepositRequest.objects.filter(user=u, status='CREDITED').exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()
            if not first_dep:
                continue

            # Link to referrer milestone once per user
            wallet, _ = Wallet.objects.get_or_create(user=u)
            flag_key = f"first_investment_recorded:{u.id}"
            already = wallet.transactions.filter(meta__flag=flag_key).exists()
            if not already and u.referred_by and not dry_run:
                record_direct_first_investment(u.referred_by, u, first_dep.amount_usd)
                Transaction.objects.create(wallet=wallet, type=Transaction.CREDIT, amount_usd=Decimal('0.00'), meta={'type': 'meta', 'flag': flag_key})

            # Find the last day index
            last = PassiveEarning.objects.filter(user=u).order_by('-day_index').first()
            start_day = (last.day_index + 1) if last else 1

            # Process multiple days if backfilling
            user_earnings_count = 0
            user_total_usd = Decimal('0.00')

            for day_offset in range(backfill_days):
                current_day = start_day + day_offset
                
                # Stop at day 90 (max earning period)
                if current_day > 90:
                    self.stdout.write(self.style.WARNING(f"⚠️  {u.username} reached max 90 days"))
                    break

                metrics = compute_daily_earning_usd(current_day)

                if dry_run:
                    self.stdout.write(f"  [DRY RUN] Would credit {u.username} day {current_day}: {metrics['user_share_usd']} USD ({metrics['percent']}%)")
                else:
                    PassiveEarning.objects.create(
                        user=u,
                        day_index=current_day,
                        percent=metrics['percent'],
                        amount_usd=metrics['user_share_usd'],
                    )
                    
                    # Add passive earnings to income_usd (withdrawable income)
                    # DO NOT add to available_usd (which is only for 80% of deposits)
                    wallet.income_usd = (Decimal(wallet.income_usd) + metrics['user_share_usd']).quantize(Decimal('0.01'))
                    wallet.hold_usd = (Decimal(wallet.hold_usd) + metrics['platform_hold_usd']).quantize(Decimal('0.01'))
                    wallet.save()

                    # Create transaction record for passive income display
                    Transaction.objects.create(
                        wallet=wallet,
                        type=Transaction.CREDIT,
                        amount_usd=metrics['user_share_usd'],
                        meta={'type': 'passive', 'day_index': current_day, 'percent': str(metrics['percent'])}
                    )

                    self.stdout.write(self.style.SUCCESS(f"✅ Credited {u.username} day {current_day}: {metrics['user_share_usd']} USD ({metrics['percent']}%)"))

                user_earnings_count += 1
                user_total_usd += metrics['user_share_usd']

            if user_earnings_count > 0:
                total_users_processed += 1
                total_earnings_generated += user_earnings_count
                total_amount_usd += user_total_usd
                self.stdout.write(self.style.SUCCESS(f"📊 {u.username}: {user_earnings_count} earnings, Total: ${user_total_usd}"))

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "="*60))
        self.stdout.write(self.style.SUCCESS("📈 EARNINGS SUMMARY"))
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(self.style.SUCCESS(f"👥 Users Processed: {total_users_processed}"))
        self.stdout.write(self.style.SUCCESS(f"💰 Total Earnings Generated: {total_earnings_generated}"))
        self.stdout.write(self.style.SUCCESS(f"💵 Total Amount: ${total_amount_usd}"))
        self.stdout.write(self.style.SUCCESS(f"💵 Total Amount (PKR): ₨{float(total_amount_usd) * 280:,.2f}"))
        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 This was a DRY RUN - no changes were made"))
            self.stdout.write(self.style.WARNING("Run without --dry-run to apply changes"))
        self.stdout.write(self.style.SUCCESS("="*60))