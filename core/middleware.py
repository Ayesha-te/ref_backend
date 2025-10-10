"""
Middleware to handle Neon database connection issues and auto-trigger daily earnings
"""
from django.db import OperationalError, transaction
from django.utils import timezone
from time import sleep
import logging

logger = logging.getLogger(__name__)


class DBRetryMiddleware:
    """
    Middleware to retry database operations when Neon DB wakes up from sleep mode.
    Neon free tier auto-sleeps after ~5 minutes of inactivity.
    The first request after wake-up might throw OperationalError.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for attempt in range(2):
            try:
                return self.get_response(request)
            except OperationalError as e:
                if attempt == 0:
                    logger.warning(f"Database connection failed (attempt {attempt + 1}), retrying in 1 second: {e}")
                    sleep(1)  # Wait 1 second and retry
                else:
                    logger.error(f"Database connection failed after retry: {e}")
                    raise
            except Exception as e:
                # Don't retry for non-database errors
                raise


class AutoDailyEarningsMiddleware:
    """
    Middleware to automatically trigger daily earnings generation on any request.
    This is Render-friendly and survives container restarts.
    
    How it works:
    - On every request, check if today's earnings have been processed
    - If not, trigger the daily earnings generation
    - Uses a singleton model to track last processed date
    - Thread-safe with database-level locking
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._processing = False  # Prevent concurrent processing in same instance

    def __call__(self, request):
        # Check and process earnings before handling the request
        if not self._processing:
            try:
                self._check_and_process_daily_earnings()
            except Exception as e:
                # Log error but don't break the request
                logger.error(f"Error in AutoDailyEarningsMiddleware: {e}", exc_info=True)
        
        response = self.get_response(request)
        return response
    
    def _check_and_process_daily_earnings(self):
        """Check if daily earnings need to be processed and trigger if needed"""
        from apps.earnings.models import DailyEarningsState
        from django.contrib.auth import get_user_model
        from apps.wallets.models import Wallet, Transaction, DepositRequest
        from apps.earnings.models import PassiveEarning
        from apps.earnings.services import compute_daily_earning_usd
        from apps.referrals.services import record_direct_first_investment
        from decimal import Decimal
        
        today = timezone.now().date()
        
        # Use select_for_update to prevent race conditions
        with transaction.atomic():
            try:
                state = DailyEarningsState.objects.select_for_update(nowait=True).get(pk=1)
            except DailyEarningsState.DoesNotExist:
                # Create initial state
                state = DailyEarningsState.objects.create(pk=1, last_processed_date=today - timezone.timedelta(days=1))
            except Exception:
                # Another process is already processing, skip
                return
            
            # Check if we need to process today
            if state.last_processed_date >= today:
                return  # Already processed today
            
            # Mark as processing to prevent concurrent runs in this instance
            self._processing = True
            
            try:
                logger.info(f"🚀 Auto-triggering daily earnings for {today}")
                
                User = get_user_model()
                users = User.objects.filter(is_approved=True)
                
                total_users_processed = 0
                total_earnings_generated = 0
                total_amount_usd = Decimal('0.00')
                
                for u in users:
                    # Only start passive earnings after first credited deposit (exclude signup initial)
                    first_dep = DepositRequest.objects.filter(
                        user=u, 
                        status='CREDITED'
                    ).exclude(
                        tx_id='SIGNUP-INIT'
                    ).order_by('processed_at', 'created_at').first()
                    
                    if not first_dep:
                        continue
                    
                    # ===== CRITICAL: Day 0 Protection =====
                    # Calculate how many days have passed since the deposit was credited
                    deposit_date = first_dep.processed_at or first_dep.created_at
                    if not deposit_date:
                        logger.warning(f"⚠️ Skipping {u.username}: No deposit date available")
                        continue
                    
                    # Calculate days elapsed since deposit
                    now = timezone.now()
                    time_diff = now - deposit_date
                    days_since_deposit = time_diff.days
                    
                    # CRITICAL: Don't generate passive income on day 0 (same day as deposit)
                    # User must wait at least 1 full day before receiving passive income
                    if days_since_deposit < 1:
                        logger.warning(f"⚠️ Skipping {u.username}: Deposit was made today (day 0). Passive income starts after 1 full day.")
                        continue
                    
                    # Link to referrer milestone once per user
                    wallet, _ = Wallet.objects.get_or_create(user=u)
                    flag_key = f"first_investment_recorded:{u.id}"
                    already = wallet.transactions.filter(meta__flag=flag_key).exists()
                    if not already and u.referred_by:
                        record_direct_first_investment(u.referred_by, u, first_dep.amount_usd)
                        Transaction.objects.create(
                            wallet=wallet, 
                            type=Transaction.CREDIT, 
                            amount_usd=Decimal('0.00'), 
                            meta={'type': 'meta', 'flag': flag_key}
                        )
                    
                    # Find the last day index
                    last = PassiveEarning.objects.filter(user=u).order_by('-day_index').first()
                    current_day = (last.day_index + 1) if last else 1
                    
                    # Cap earnings at the minimum of days_since_deposit and 90 (max earning period)
                    # This prevents generating earnings for future days that haven't occurred yet
                    max_allowed_day = min(days_since_deposit, 90)
                    
                    # Stop if we've already generated earnings up to the allowed day
                    if current_day > max_allowed_day:
                        continue
                    
                    # Compute and credit earnings
                    metrics = compute_daily_earning_usd(current_day)
                    
                    PassiveEarning.objects.create(
                        user=u,
                        day_index=current_day,
                        percent=metrics['percent'],
                        amount_usd=metrics['user_share_usd'],
                    )
                    
                    # Add passive earnings to income_usd (withdrawable income)
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
                    
                    total_users_processed += 1
                    total_earnings_generated += 1
                    total_amount_usd += metrics['user_share_usd']
                    
                    logger.info(f"✅ Credited {u.username} day {current_day}: {metrics['user_share_usd']} USD ({metrics['percent']}%)")
                
                # Update state to mark today as processed
                state.last_processed_date = today
                state.save()
                
                logger.info(f"✅ Daily earnings auto-processed: {total_users_processed} users, ${total_amount_usd}")
                
                # ===== GLOBAL POOL PROCESSING (Mondays Only) =====
                # Check if today is Monday (weekday() returns 0 for Monday)
                if today.weekday() == 0:
                    self._process_global_pool_monday(today)
                
            finally:
                self._processing = False
    
    def _process_global_pool_monday(self, monday_date):
        """Process global pool on Mondays: collect from signups and distribute to all users"""
        from apps.earnings.models import GlobalPoolState, GlobalPoolCollection, GlobalPoolDistribution
        from apps.wallets.models import Wallet, Transaction, DepositRequest
        from django.contrib.auth import get_user_model
        from decimal import Decimal
        
        logger.info(f"🌍 Processing Global Pool for Monday: {monday_date}")
        
        User = get_user_model()
        
        # Get or create global pool state
        pool_state, created = GlobalPoolState.objects.get_or_create(pk=1)
        
        # ===== COLLECTION PHASE =====
        # Only collect if we haven't collected for this Monday yet
        if pool_state.last_collection_date != monday_date:
            logger.info(f"📥 Collecting 0.5% from Monday signups...")
            
            # Find all SIGNUP-INIT deposits from this Monday
            from datetime import datetime
            monday_start = datetime.combine(monday_date, datetime.min.time())
            monday_end = datetime.combine(monday_date, datetime.max.time())
            
            signup_deposits = DepositRequest.objects.filter(
                tx_id='SIGNUP-INIT',
                status='CREDITED',
                created_at__gte=monday_start,
                created_at__lte=monday_end
            )
            
            total_collected = Decimal('0')
            collection_count = 0
            
            for deposit in signup_deposits:
                # Check if already collected
                existing = GlobalPoolCollection.objects.filter(
                    user=deposit.user,
                    collection_date=monday_date
                ).exists()
                
                if existing:
                    continue
                
                # Calculate 0.5% of signup amount
                signup_amount = deposit.amount_usd
                collection_amount = (signup_amount * Decimal('0.005')).quantize(Decimal('0.01'))
                
                # Record the collection
                GlobalPoolCollection.objects.create(
                    user=deposit.user,
                    signup_amount_usd=signup_amount,
                    collection_amount_usd=collection_amount,
                    collection_date=monday_date
                )
                
                total_collected += collection_amount
                collection_count += 1
                
                logger.info(f"  ✅ Collected ${collection_amount} from {deposit.user.username}")
            
            # Update pool state
            pool_state.current_pool_usd += total_collected
            pool_state.total_collected_all_time += total_collected
            pool_state.last_collection_date = monday_date
            pool_state.save()
            
            logger.info(f"✅ Collection complete: ${total_collected} from {collection_count} signups. Pool now: ${pool_state.current_pool_usd}")
        
        # ===== DISTRIBUTION PHASE =====
        # Only distribute if we haven't distributed for this Monday yet AND pool has balance
        if pool_state.last_distribution_date != monday_date and pool_state.current_pool_usd > 0:
            logger.info(f"📤 Distributing pool to all users...")
            
            # Get all active users (users with wallets)
            active_users = User.objects.filter(wallet__isnull=False).distinct()
            
            if not active_users.exists():
                logger.warning("⚠️ No active users to distribute to")
                return
            
            total_users = active_users.count()
            pool_amount = pool_state.current_pool_usd
            per_user_amount = (pool_amount / Decimal(total_users)).quantize(Decimal('0.01'))
            
            if per_user_amount <= 0:
                logger.warning("⚠️ Per-user amount is zero or negative")
                return
            
            logger.info(f"💰 Distributing ${pool_amount} to {total_users} users (${per_user_amount} each)")
            
            distribution_count = 0
            
            for user in active_users:
                # Check if already distributed
                existing = GlobalPoolDistribution.objects.filter(
                    user=user,
                    distribution_date=monday_date
                ).exists()
                
                if existing:
                    continue
                
                # Get user's wallet
                wallet = user.wallet
                
                # Credit to income_usd (80% user share) and hold_usd (20% platform hold)
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
            
            # Update pool state - reset pool to 0 after distribution
            pool_state.current_pool_usd = Decimal('0')
            pool_state.total_distributed_all_time += pool_amount
            pool_state.last_distribution_date = monday_date
            pool_state.save()
            
            logger.info(f"✅ Distribution complete: ${pool_amount} to {distribution_count} users. Pool reset to $0")