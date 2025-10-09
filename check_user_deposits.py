#!/usr/bin/env python
"""
Check User Deposits and Referral Bonuses
=========================================

This script checks a user's deposits and referral bonuses to diagnose issues.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.wallets.models import DepositRequest, Transaction
from apps.referrals.models import ReferralPayout
from decimal import Decimal

User = get_user_model()

print("\n" + "="*80)
print("🔍 USER DEPOSITS AND REFERRAL BONUS CHECKER")
print("="*80 + "\n")

# Get your email
email = input("Enter your email (or press Enter for default): ").strip()
if not email:
    email = "sardarlaeiq3@gmail.com"

try:
    user = User.objects.get(email=email)
    print(f"✅ Found user: {user.email}")
    print(f"   - Username: {user.username}")
    print(f"   - Approved: {user.is_approved}")
    print(f"   - Referral Code: {user.referral_code}")
    
    # Check referrals (team members)
    referrals = User.objects.filter(referred_by=user, is_approved=True)
    print(f"\n👥 Team Members (Approved Referrals): {referrals.count()}")
    
    for i, ref in enumerate(referrals, 1):
        print(f"\n   {i}. {ref.email}")
        print(f"      - Username: {ref.username}")
        print(f"      - Joined: {ref.date_joined}")
        
        # Check their deposits
        deposits = DepositRequest.objects.filter(user=ref, status='CREDITED').order_by('created_at')
        print(f"      - Deposits: {deposits.count()}")
        
        for dep in deposits:
            print(f"        • {dep.amount_pkr} PKR (${dep.amount_usd} USD) - {dep.tx_id} - {dep.created_at}")
        
        # Check referral payouts for this referee
        payouts = ReferralPayout.objects.filter(referrer=user, referee=ref)
        print(f"      - Referral Payouts to You: {payouts.count()}")
        
        for payout in payouts:
            print(f"        • Level {payout.level}: ${payout.amount_usd} USD - {payout.created_at}")
    
    # Check all referral payouts you received
    print(f"\n💰 All Referral Payouts You Received:")
    all_payouts = ReferralPayout.objects.filter(referrer=user).order_by('created_at')
    print(f"   Total: {all_payouts.count()}")
    
    total_usd = Decimal('0')
    for payout in all_payouts:
        total_usd += payout.amount_usd
        print(f"   - From {payout.referee.email} (L{payout.level}): ${payout.amount_usd} USD - {payout.created_at}")
    
    print(f"\n   📊 Total Referral Earnings: ${total_usd} USD")
    
    # Convert to PKR (approximate)
    from django.conf import settings
    rate = Decimal(str(settings.ADMIN_USD_TO_PKR))
    total_pkr = (total_usd * rate).quantize(Decimal('0.01'))
    print(f"   📊 Total Referral Earnings: Rs{total_pkr} PKR (at rate {rate})")
    
    # Check for duplicates
    print(f"\n🔍 Checking for Duplicate Payouts...")
    from django.db.models import Count
    duplicates = ReferralPayout.objects.filter(referrer=user).values('referee', 'level').annotate(count=Count('id')).filter(count__gt=1)
    
    if duplicates:
        print(f"   ⚠️  Found {len(duplicates)} duplicate payout groups:")
        for dup in duplicates:
            referee = User.objects.get(id=dup['referee'])
            print(f"      - {referee.email} (Level {dup['level']}): {dup['count']} payouts (should be 1)")
    else:
        print(f"   ✅ No duplicates found!")

except User.DoesNotExist:
    print(f"❌ User with email '{email}' not found!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80 + "\n")