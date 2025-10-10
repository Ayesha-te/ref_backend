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
                
            finally:
                self._processing = False