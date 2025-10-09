#!/usr/bin/env python
"""
Verify Actual Deposit Amount Fix
=================================

This script verifies that referral bonuses are being calculated
based on actual deposit amounts, not the hardcoded SIGNUP_FEE_PKR.

Run this after deploying the fix to verify it's working correctly.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import SignupProof
from apps.referrals.models import ReferralPayout
from apps.wallets.models import Transaction
from django.conf import settings
from decimal import Decimal

User = get_user_model()

print("\n" + "="*80)
print("🔍 VERIFY ACTUAL DEPOSIT AMOUNT FIX")
print("="*80 + "\n")

# Get all approved users with signup proofs
users_with_proofs = User.objects.filter(
    is_approved=True,
    signup_proofs__isnull=False
).distinct().order_by('-date_joined')[:10]  # Last 10 approved users

print(f"Checking last {users_with_proofs.count()} approved users with signup proofs...\n")

rate = Decimal(str(settings.ADMIN_USD_TO_PKR))
default_fee = Decimal(str(settings.SIGNUP_FEE_PKR))

issues_found = 0
correct_bonuses = 0

for user in users_with_proofs:
    print(f"👤 {user.email}")
    
    # Get signup proof
    signup_proof = user.signup_proofs.order_by('-created_at').first()
    if not signup_proof:
        print(f"   ⚠️  No signup proof found")
        continue
    
    actual_amount_pkr = signup_proof.amount_pkr
    actual_amount_usd = (actual_amount_pkr / rate).quantize(Decimal('0.01'))
    
    print(f"   💰 Signup Amount: {actual_amount_pkr} PKR (${actual_amount_usd} USD)")
    
    # Check if this user has a referrer
    if not user.referred_by:
        print(f"   ℹ️  No referrer (direct signup)")
        print()
        continue
    
    print(f"   👆 Referred by: {user.referred_by.email}")
    
    # Get referral payouts for this user
    payouts = ReferralPayout.objects.filter(referee=user).order_by('level')
    
    if not payouts.exists():
        print(f"   ⚠️  No referral payouts found (might not be approved yet)")
        print()
        continue
    
    print(f"   📊 Referral Payouts:")
    
    for payout in payouts:
        # Calculate expected bonus
        if payout.level == 1:
            expected_pct = Decimal('0.06')  # 6%
        elif payout.level == 2:
            expected_pct = Decimal('0.03')  # 3%
        elif payout.level == 3:
            expected_pct = Decimal('0.01')  # 1%
        else:
            expected_pct = Decimal('0.00')
        
        # Expected based on ACTUAL deposit
        expected_usd = (actual_amount_usd * expected_pct).quantize(Decimal('0.01'))
        expected_pkr = (expected_usd * rate).quantize(Decimal('0.01'))
        
        # Expected based on DEFAULT fee (old behavior)
        default_usd_base = (default_fee / rate).quantize(Decimal('0.01'))
        old_expected_usd = (default_usd_base * expected_pct).quantize(Decimal('0.01'))
        old_expected_pkr = (old_expected_usd * rate).quantize(Decimal('0.01'))
        
        actual_bonus_usd = payout.amount_usd
        actual_bonus_pkr = (actual_bonus_usd * rate).quantize(Decimal('0.01'))
        
        # Check if bonus matches expected (with small tolerance for rounding)
        tolerance = Decimal('0.02')  # 2 cents tolerance
        is_correct = abs(actual_bonus_usd - expected_usd) <= tolerance
        is_old_behavior = abs(actual_bonus_usd - old_expected_usd) <= tolerance
        
        status = "✅" if is_correct else ("⚠️ OLD" if is_old_behavior else "❌")
        
        print(f"      {status} L{payout.level} to {payout.referrer.email}:")
        print(f"         Actual:   ${actual_bonus_usd} USD (Rs{actual_bonus_pkr} PKR)")
        print(f"         Expected: ${expected_usd} USD (Rs{expected_pkr} PKR) - {expected_pct*100}% of {actual_amount_pkr} PKR")
        
        if is_old_behavior and not is_correct:
            print(f"         ⚠️  Using old behavior (${old_expected_usd} USD from {default_fee} PKR)")
            issues_found += 1
        elif not is_correct:
            print(f"         ❌ MISMATCH! Expected ${expected_usd} but got ${actual_bonus_usd}")
            issues_found += 1
        else:
            correct_bonuses += 1
    
    print()

print("="*80)
print(f"\n📊 SUMMARY:")
print(f"   ✅ Correct bonuses: {correct_bonuses}")
print(f"   ⚠️  Issues found: {issues_found}")

if issues_found == 0:
    print(f"\n🎉 All bonuses are calculated correctly based on actual deposit amounts!")
else:
    print(f"\n⚠️  Some bonuses are still using old behavior (hardcoded {default_fee} PKR)")
    print(f"   This is expected for users approved BEFORE the fix was deployed.")
    print(f"   New approvals should use actual deposit amounts.")

print("\n" + "="*80 + "\n")