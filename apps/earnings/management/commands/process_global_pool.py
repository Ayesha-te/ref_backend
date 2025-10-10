"""
Global Pool Management Command

This command handles both collection and distribution of the global pool:

COLLECTION (runs on Monday):
- Collects 0.5% from all users who signed up on Monday (SIGNUP-INIT deposits)
- Adds to the current pool balance

DISTRIBUTION (runs on Monday):
- Distributes the entire pool equally among ALL active users
- Resets the pool to 0 after distribution

Usage:
    python manage.py process_global_pool --collect    # Collect from Monday signups
    python manage.py process_global_pool --distribute # Distribute pool to all users
    python manage.py process_global_pool --both       # Do both (collect then distribute)
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from apps.earnings.models import GlobalPoolState, GlobalPoolCollection, GlobalPoolDistribution
from apps.wallets.models import Wallet, Transaction, DepositRequest

User = get_user_model()


class Command(BaseCommand):
    help = 'Process global pool: collect 0.5%% from Monday signups and/or distribute to all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--collect',
            action='store_true',
            help='Collect 0.5%% from Monday signups',
        )
        parser.add_argument(
            '--distribute',
            action='store_true',
            help='Distribute pool to all users',
        )
        parser.add_argument(
            '--both',
            action='store_true',
            help='Collect then distribute',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Specific Monday date in YYYY-MM-DD format (default: last Monday)',
        )

    def handle(self, *args, **options):
        if options['both']:
            options['collect'] = True
            options['distribute'] = True
        
        if not options['collect'] and not options['distribute']:
            self.stdout.write(self.style.ERROR('Please specify --collect, --distribute, or --both'))
            return
        
        # Determine the Monday to process
        if options['date']:
            target_monday = datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            target_monday = self.get_last_monday()
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Processing Global Pool for Monday: {target_monday}")
        self.stdout.write(f"{'='*60}\n")
        
        if options['collect']:
            self.collect_from_monday_signups(target_monday)
        
        if options['distribute']:
            self.distribute_pool(target_monday)

    def get_last_monday(self):
        """Get the most recent Monday (or today if today is Monday)"""
        today = timezone.now().date()
        days_since_monday = today.weekday()  # Monday = 0
        if days_since_monday == 0:
            return today
        else:
            return today - timedelta(days=days_since_monday)

    @transaction.atomic
    def collect_from_monday_signups(self, monday_date):
        """Collect 0.5% from all users who signed up on the specified Monday"""
        self.stdout.write(f"\n📥 COLLECTION PHASE")
        self.stdout.write(f"{'─'*60}")
        
        # Get or create global pool state
        pool_state, created = GlobalPoolState.objects.get_or_create(pk=1)
        
        if pool_state.last_collection_date == monday_date:
            self.stdout.write(self.style.WARNING(
                f"⚠️  Already collected for {monday_date}. Skipping collection."
            ))
            return
        
        # Find all SIGNUP-INIT deposits from this Monday
        monday_start = datetime.combine(monday_date, datetime.min.time())
        monday_end = datetime.combine(monday_date, datetime.max.time())
        
        signup_deposits = DepositRequest.objects.filter(
            tx_id='SIGNUP-INIT',
            status='CREDITED',
            created_at__gte=monday_start,
            created_at__lte=monday_end
        )
        
        if not signup_deposits.exists():
            self.stdout.write(self.style.WARNING(
                f"⚠️  No signup deposits found for {monday_date}"
            ))
            pool_state.last_collection_date = monday_date
            pool_state.save()
            return
        
        total_collected = Decimal('0')
        collection_count = 0
        
        for deposit in signup_deposits:
            # Calculate 0.5% of signup amount
            signup_amount = deposit.amount_usd
            collection_amount = (signup_amount * Decimal('0.005')).quantize(Decimal('0.01'))
            
            # Check if already collected for this user on this Monday
            existing = GlobalPoolCollection.objects.filter(
                user=deposit.user,
                collection_date=monday_date
            ).exists()
            
            if existing:
                self.stdout.write(f"  ⏭️  Skipping {deposit.user.username} (already collected)")
                continue
            
            # Record the collection
            GlobalPoolCollection.objects.create(
                user=deposit.user,
                signup_amount_usd=signup_amount,
                collection_amount_usd=collection_amount,
                collection_date=monday_date
            )
            
            total_collected += collection_amount
            collection_count += 1
            
            self.stdout.write(
                f"  ✅ {deposit.user.username}: ${signup_amount} signup → ${collection_amount} collected (0.5%)"
            )
        
        # Update pool state
        pool_state.current_pool_usd += total_collected
        pool_state.total_collected_all_time += total_collected
        pool_state.last_collection_date = monday_date
        pool_state.save()
        
        self.stdout.write(f"\n{'─'*60}")
        self.stdout.write(self.style.SUCCESS(
            f"✅ Collection Complete!\n"
            f"   • Collected from: {collection_count} users\n"
            f"   • Total collected: ${total_collected}\n"
            f"   • Current pool balance: ${pool_state.current_pool_usd}"
        ))

    @transaction.atomic
    def distribute_pool(self, monday_date):
        """Distribute the entire pool equally among all active users"""
        self.stdout.write(f"\n📤 DISTRIBUTION PHASE")
        self.stdout.write(f"{'─'*60}")
        
        # Get pool state
        pool_state = GlobalPoolState.objects.filter(pk=1).first()
        if not pool_state or pool_state.current_pool_usd <= 0:
            self.stdout.write(self.style.WARNING(
                f"⚠️  No pool balance to distribute (${pool_state.current_pool_usd if pool_state else 0})"
            ))
            return
        
        if pool_state.last_distribution_date == monday_date:
            self.stdout.write(self.style.WARNING(
                f"⚠️  Already distributed for {monday_date}. Skipping distribution."
            ))
            return
        
        # Get all active users (users with wallets)
        active_users = User.objects.filter(wallet__isnull=False).distinct()
        
        if not active_users.exists():
            self.stdout.write(self.style.WARNING("⚠️  No active users to distribute to"))
            return
        
        total_users = active_users.count()
        pool_amount = pool_state.current_pool_usd
        per_user_amount = (pool_amount / Decimal(total_users)).quantize(Decimal('0.01'))
        
        if per_user_amount <= 0:
            self.stdout.write(self.style.WARNING("⚠️  Per-user amount is zero or negative"))
            return
        
        self.stdout.write(f"\n💰 Pool Details:")
        self.stdout.write(f"   • Total pool: ${pool_amount}")
        self.stdout.write(f"   • Active users: {total_users}")
        self.stdout.write(f"   • Per user: ${per_user_amount}\n")
        
        distribution_count = 0
        
        for user in active_users:
            # Check if already distributed to this user on this Monday
            existing = GlobalPoolDistribution.objects.filter(
                user=user,
                distribution_date=monday_date
            ).exists()
            
            if existing:
                self.stdout.write(f"  ⏭️  Skipping {user.username} (already distributed)")
                continue
            
            # Get user's wallet
            wallet = user.wallet
            
            # Credit to income_usd (80% user share)
            user_share = (per_user_amount * Decimal('0.80')).quantize(Decimal('0.01'))
            platform_hold = (per_user_amount * Decimal('0.20')).quantize(Decimal('0.01'))
            
            wallet.income_usd += user_share
            wallet.hold_usd += platform_hold
            wallet.save()
            
            # Create transaction record
            Transaction.objects.create(
                wallet=wallet,
                type=Transaction.CREDIT,
                amount_usd=per_user_amount,
                meta={
                    'type': 'global_pool',
                    'distribution_date': str(monday_date),
                    'total_pool': str(pool_amount),
                    'total_users': total_users,
                    'user_share': str(user_share),
                    'platform_hold': str(platform_hold),
                }
            )
            
            # Record distribution
            GlobalPoolDistribution.objects.create(
                user=user,
                amount_usd=per_user_amount,
                distribution_date=monday_date,
                total_pool_amount=pool_amount,
                total_users=total_users
            )
            
            distribution_count += 1
            self.stdout.write(f"  ✅ {user.username}: ${per_user_amount} (${user_share} income + ${platform_hold} hold)")
        
        # Update pool state
        pool_state.current_pool_usd = Decimal('0')
        pool_state.total_distributed_all_time += pool_amount
        pool_state.last_distribution_date = monday_date
        pool_state.save()
        
        self.stdout.write(f"\n{'─'*60}")
        self.stdout.write(self.style.SUCCESS(
            f"✅ Distribution Complete!\n"
            f"   • Distributed to: {distribution_count} users\n"
            f"   • Total distributed: ${pool_amount}\n"
            f"   • Per user: ${per_user_amount}\n"
            f"   • Pool balance now: ${pool_state.current_pool_usd}"
        ))