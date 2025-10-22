"""
Backfill script to generate passive income from October 16, 2024 onwards.

This script will:
1. Find all approved users with credited deposits
2. Generate missing passive income from Oct 16 onwards
3. Respect the 1-day wait period after deposit
4. Continue to present day
5. Print a summary of generated earnings
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.earnings.models import PassiveEarning, DailyEarningsState
from apps.earnings.services import compute_daily_earning_usd
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.referrals.services import record_direct_first_investment

User = get_user_model()

def daterange(start_date, end_date):
    """Generate all dates from start_date to end_date (exclusive)"""
    current = start_date
    while current < end_date:
        yield current
        current += timedelta(days=1)

# Backfill start date
BACKFILL_START = datetime(2024, 10, 16).date()
TODAY = timezone.now().date()

print(f"\n{'='*80}")
print(f"🔄 PASSIVE INCOME BACKFILL")
print(f"{'='*80}")
print(f"Backfill Period: {BACKFILL_START} to {TODAY}")
print(f"{'='*80}\n")

total_users_processed = 0
total_earnings_generated = 0
total_amount_usd = Decimal('0.00')
users_data = []

# Get all approved users
approved_users = User.objects.filter(is_approved=True).order_by('username')
print(f"📊 Processing {approved_users.count()} approved users...")

for user in approved_users:
    # Get first credited deposit (exclude signup initial)
    first_dep = DepositRequest.objects.filter(
        user=user, 
        status='CREDITED'
    ).exclude(
        tx_id='SIGNUP-INIT'
    ).order_by('processed_at', 'created_at').first()
    
    if not first_dep:
        continue  # No deposit, skip
    
    deposit_date = first_dep.processed_at or first_dep.created_at
    if not deposit_date:
        continue
    
    # Convert to date if it's datetime
    if hasattr(deposit_date, 'date'):
        deposit_date = deposit_date.date()
    
    # Calculate earliest day this user can receive earnings
    # Must wait 1 full day after deposit
    earliest_earning_date = deposit_date + timedelta(days=1)
    
    # If deposit is after backfill period, start from deposit + 1 day
    # Otherwise, start from backfill start date but not before deposit + 1 day
    start_date = max(earliest_earning_date, BACKFILL_START)
    
    # If start date is in the future, skip
    if start_date > TODAY:
        continue
    
    # Get existing earnings for this user
    existing_earnings = PassiveEarning.objects.filter(user=user).values_list('day_index', flat=True)
    existing_set = set(existing_earnings)
    
    # Calculate day indices to generate
    # day_index = number of days since deposit + 1 day wait
    user_earnings_data = []
    days_generated = 0
    user_amount_usd = Decimal('0.00')
    
    for date in daterange(start_date, TODAY + timedelta(days=1)):
        # Calculate how many days have passed since deposit
        days_since_deposit = (date - deposit_date).days
        
        # Day index = days since deposit (0-based) + 1
        day_index = days_since_deposit
        
        # Skip if already generated or if day_index is invalid
        if day_index in existing_set or day_index < 1 or day_index > 90:
            continue
        
        try:
            # Compute earnings
            metrics = compute_daily_earning_usd(day_index, first_dep.amount_usd)
            
            # Create passive earning record
            earning = PassiveEarning.objects.create(
                user=user,
                day_index=day_index,
                percent=metrics['percent'],
                amount_usd=metrics['user_share_usd'],
            )
            
            # Update wallet
            wallet, _ = Wallet.objects.get_or_create(user=user)
            wallet.income_usd = (Decimal(wallet.income_usd) + metrics['user_share_usd']).quantize(Decimal('0.01'))
            wallet.hold_usd = (Decimal(wallet.hold_usd) + metrics['platform_hold_usd']).quantize(Decimal('0.01'))
            wallet.save()
            
            # Create transaction record
            Transaction.objects.create(
                wallet=wallet,
                type=Transaction.CREDIT,
                amount_usd=metrics['user_share_usd'],
                meta={'type': 'passive', 'day_index': day_index, 'percent': str(metrics['percent']), 'backfilled': True}
            )
            
            days_generated += 1
            user_amount_usd += metrics['user_share_usd']
            user_earnings_data.append({
                'date': date,
                'day_index': day_index,
                'percent': metrics['percent'],
                'amount_usd': metrics['user_share_usd']
            })
            
            total_earnings_generated += 1
            total_amount_usd += metrics['user_share_usd']
            
        except Exception as e:
            print(f"  ⚠️ Error generating earning for {user.username} on day {day_index}: {e}")
            continue
    
    if days_generated > 0:
        total_users_processed += 1
        users_data.append({
            'username': user.username,
            'deposit_amount': first_dep.amount_usd,
            'deposit_date': deposit_date,
            'days_generated': days_generated,
            'total_amount': user_amount_usd,
            'earnings': user_earnings_data
        })
        print(f"✅ {user.username:20} | Generated {days_generated:3} days | ${user_amount_usd:10.2f}")

print(f"\n{'='*80}")
print(f"📈 BACKFILL SUMMARY")
print(f"{'='*80}")
print(f"Users processed:        {total_users_processed}")
print(f"Total earnings entries: {total_earnings_generated}")
print(f"Total amount generated: ${total_amount_usd:.2f}")
print(f"{'='*80}\n")

# Reset DailyEarningsState to yesterday so it regenerates today
try:
    state = DailyEarningsState.objects.get(pk=1)
    state.last_processed_date = TODAY - timedelta(days=1)
    state.save()
    print(f"✅ Reset DailyEarningsState to {TODAY - timedelta(days=1)} for today's processing\n")
except DailyEarningsState.DoesNotExist:
    print(f"⚠️ DailyEarningsState not found, will be created on next request\n")

print(f"✅ Backfill complete! Middleware will process today's earnings on next request.\n")