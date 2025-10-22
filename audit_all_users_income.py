#!/usr/bin/env python
"""
Complete audit of passive income generation for all users.
Shows who has generated income, who is missing income, and recommendations.
"""
import os
import sys
import django

# Set encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.wallets.models import DepositRequest, Wallet
from apps.earnings.models import PassiveEarning
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from datetime import datetime

User = get_user_model()

print("\n" + "="*150)
print("COMPLETE PASSIVE INCOME AUDIT - ALL USERS")
print("="*150 + "\n")

# Collect comprehensive data
audit_data = []

for u in User.objects.filter(is_approved=True).order_by('-date_joined'):
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
    
    # Calculate expected earnings
    max_allowed_day = min(days_since_deposit, 90)
    
    # Get actual earnings
    actual_earnings = PassiveEarning.objects.filter(user=u)
    last_earning = actual_earnings.order_by('-day_index').first()
    last_day_earned = last_earning.day_index if last_earning else 0
    
    total_earned_usd = actual_earnings.aggregate(
        total=Sum('amount_usd')
    )['total'] or Decimal('0.00')
    
    # Get wallet
    try:
        wallet = Wallet.objects.get(user=u)
        wallet_income = wallet.income_usd
    except:
        wallet_income = Decimal('0.00')
    
    # Calculate missing earnings
    expected_days = max_allowed_day
    actual_days = last_day_earned
    missing_days = max(0, expected_days - actual_days)
    
    audit_data.append({
        'username': u.username,
        'email': u.email,
        'deposit_date': deposit_date,
        'deposit_amount': first_dep.amount_usd,
        'days_since_deposit': days_since_deposit,
        'expected_days': expected_days,
        'actual_days': last_day_earned,
        'missing_days': missing_days,
        'total_earned_usd': total_earned_usd,
        'wallet_income': wallet_income,
        'earnings_count': actual_earnings.count(),
        'status': 'COMPLETE' if missing_days == 0 else 'MISSING'
    })

# Sort by missing days (highest first)
audit_data.sort(key=lambda x: x['missing_days'], reverse=True)

# Print detailed report
print("User                      | Days/Expected | Missing | Earned  | Wallet  | Status")
print("-" * 150)

complete_count = 0
missing_count = 0

for audit in audit_data:
    if audit['missing_days'] == 0:
        status = "[OK] COMPLETE"
        complete_count += 1
    else:
        status = "[MISSING] {} DAYS".format(audit['missing_days'])
        missing_count += 1
    
    days_str = "{}/{}".format(audit['actual_days'], audit['expected_days'])
    print("{:<25} | {:<13} | {:<7} | ${:<7} | ${:<7} | {}".format(
        audit['username'][:25], 
        days_str, 
        audit['missing_days'], 
        str(audit['total_earned_usd'])[:6],
        str(audit['wallet_income'])[:6],
        status
    ))

print("\n" + "="*150)
print("SUMMARY:")
print("="*150)
print("Total Approved Users with Deposits: {}".format(len(audit_data)))
print("  [OK] Complete (all earned): {}".format(complete_count))
print("  [MISSING] Missing earnings: {}".format(missing_count))

if missing_count > 0:
    print("\nUSERS MISSING EARNINGS:")
    missing_users = [a for a in audit_data if a['missing_days'] > 0]
    for user in missing_users:
        print("   * {}: Missing {} days (has {}/{} days)".format(
            user['username'], 
            user['missing_days'],
            user['actual_days'],
            user['expected_days']
        ))
        print("     Deposit: ${} on {}".format(
            user['deposit_amount'],
            user['deposit_date'].strftime('%Y-%m-%d %H:%M')
        ))
        print("     Days since deposit: {} days".format(user['days_since_deposit']))

print("\n" + "="*150)
print("RECOMMENDATIONS:")
print("="*150)

if missing_count == 0:
    print("[OK] ALL USERS ARE UP TO DATE! No backfill needed.")
    print("\n    The middleware is working correctly:")
    print("    - All users have generated income as expected")
    print("    - No missing earnings detected")
    print("    - System will continue auto-generating daily")
else:
    print("[ACTION] {} users have missing earnings and need backfill!".format(missing_count))
    print("\n    These users likely:")
    print("    - Had deposits approved but middleware didn't catch them")
    print("    - Had system downtime or errors during processing")
    print("    - Were added after the initial backfill script ran")
    print("\n    ACTION NEEDED:")
    print("    - Run backfill_passive_income_oct16.py again to generate missing earnings")
    print("    - OR create a new backfill script for these specific users")

print("\n" + "="*150 + "\n")