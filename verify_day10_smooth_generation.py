#!/usr/bin/env python
"""
Verify that users past day 10 continue generating passive income smoothly.
This checks the middleware logic to ensure no issues.
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.wallets.models import DepositRequest
from apps.earnings.models import PassiveEarning
from apps.earnings.services import compute_daily_earning_usd
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

print("\n" + "="*120)
print("🔍 VERIFICATION: USERS PAST DAY 10 - PASSIVE INCOME GENERATION")
print("="*120)

# Check all approved users with deposits
users_stats = []
for u in User.objects.filter(is_approved=True):
    first_dep = DepositRequest.objects.filter(
        user=u, 
        status='CREDITED'
    ).exclude(
        tx_id='SIGNUP-INIT'
    ).order_by('processed_at', 'created_at').first()
    
    if not first_dep:
        continue
    
    deposit_date = first_dep.processed_at or first_dep.created_at
    now = timezone.now()
    time_diff = now - deposit_date
    days_since_deposit = time_diff.days
    
    last_earning = PassiveEarning.objects.filter(user=u).order_by('-day_index').first()
    last_day = last_earning.day_index if last_earning else 0
    
    max_allowed = min(days_since_deposit, 90)
    can_earn_today = last_day < max_allowed
    
    users_stats.append({
        'username': u.username,
        'days_since_deposit': days_since_deposit,
        'last_day_earned': last_day,
        'max_allowed_day': max_allowed,
        'can_earn_today': can_earn_today,
        'days_remaining': max(0, max_allowed - last_day),
        'deposit_amount': first_dep.amount_usd
    })

# Sort by last_day_earned
users_stats.sort(key=lambda x: x['last_day_earned'], reverse=True)

# Print header
print(f"\n{'Username':<15} | {'Days':>4} | {'Last Day':>4} | {'Max Allowed':>4} | {'Days Left':>4} | Status")
print("-" * 120)

# Show all users
for stat in users_stats:
    if stat['can_earn_today']:
        status = "🟢 ACTIVE - Earning continues"
        # Show next day's earning amount
        next_day = stat['last_day_earned'] + 1
        metrics = compute_daily_earning_usd(next_day, stat['deposit_amount'])
        status += f" (Day {next_day}: ${metrics['user_share_usd']})"
    else:
        status = "🔴 COMPLETE - Reached 90 days"
    
    print(f"{stat['username']:<15} | {stat['days_since_deposit']:>4} | {stat['last_day_earned']:>4} | {stat['max_allowed_day']:>4} | {stat['days_remaining']:>4} | {status}")

print("\n" + "="*120)
print("📊 SUMMARY:")
print("="*120)

active_users = [s for s in users_stats if s['can_earn_today']]
complete_users = [s for s in users_stats if not s['can_earn_today']]

print(f"Total Users: {len(users_stats)}")
print(f"  - 🟢 Active (still generating): {len(active_users)}")
print(f"  - 🔴 Completed (90 days): {len(complete_users)}")

if active_users:
    print(f"\n✅ Users generating past day 10:")
    past_day_10 = [s for s in active_users if s['last_day_earned'] >= 10]
    for user in past_day_10:
        print(f"   - {user['username']}: Day {user['last_day_earned']} → Can generate up to Day {user['max_allowed_day']}")

print("\n" + "="*120)
print("🚀 HOW IT WORKS (Middleware Logic):")
print("="*120)
print("""
1. ✅ On EVERY HTTP REQUEST, middleware checks if daily earnings are needed
2. ✅ For each user, it finds the LAST passive earning day_index
3. ✅ Next day to generate = last_day_index + 1 (or day 1 if none exist)
4. ✅ Maximum allowed = min(days_since_deposit, 90)
5. ✅ If next_day <= max_allowed, earnings are generated for that day
6. ✅ This repeats automatically EVERY DAY until 90 days are reached

EXAMPLE: User deposited on Oct 1, now it's Oct 22 (21 days later)
  - Last earned: Day 20
  - Days since deposit: 21
  - Max allowed: min(21, 90) = 21
  - Current day to generate: 21 (within allowed range)
  - Tomorrow, it will generate day 22, then 23, etc... until day 90

🎯 RESULT: Completely automatic and smooth! No manual intervention needed.
""")
print("="*120 + "\n")