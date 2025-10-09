#!/usr/bin/env python
"""
Fix Old User Bonus - Correct earnwithjawad1@gmail.com's Bonus
==============================================================

This script corrects the bonus for earnwithjawad1@gmail.com who was
approved before the fix was deployed.

Current: Rs84 (from 1410 PKR)
Should be: Rs325 (from 5410 PKR)
Difference: Rs241 ($0.86 USD)

Run this in Render Shell ONLY ONCE.
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.referrals.models import ReferralPayout
from apps.accounts.models import SignupProof
from apps.wallets.models import Wallet, Transaction
from django.conf import settings

User = get_user_model()

print("\n" + "="*80)
print("🔧 FIX OLD USER BONUS - earnwithjawad1@gmail.com")
print("="*80 + "\n")

# Find the user
try:
    user = User.objects.get(email='earnwithjawad1@gmail.com')
    print(f"✅ Found user: {user.email}")
except User.DoesNotExist:
    print("❌ User not found: earnwithjawad1@gmail.com")
    sys.exit(1)

# Get signup proof
signup_proof = SignupProof.objects.filter(user=user).order_by('-created_at').first()
if not signup_proof:
    print("❌ No signup proof found for this user")
    sys.exit(1)

print(f"💰 Signup Amount: {signup_proof.amount_pkr} PKR")

# Get referrer
if not user.referred_by:
    print("❌ User has no referrer")
    sys.exit(1)

referrer = user.referred_by
print(f"👆 Referred by: {referrer.email}")

# Get existing payout
try:
    payout = ReferralPayout.objects.get(
        referrer=referrer,
        referee=user,
        level=1
    )
    print(f"\n📊 Current Payout:")
    print(f"   Amount: ${payout.amount_usd} USD (Rs{float(payout.amount_usd) * settings.ADMIN_USD_TO_PKR:.2f} PKR)")
except ReferralPayout.DoesNotExist:
    print("❌ No payout found for this user")
    sys.exit(1)

# Calculate correct amount
rate = Decimal(str(settings.ADMIN_USD_TO_PKR))
signup_amount_pkr = Decimal(str(signup_proof.amount_pkr))
base_usd = (signup_amount_pkr / rate).quantize(Decimal('0.01'))
correct_amount_usd = (base_usd * Decimal('0.06')).quantize(Decimal('0.01'))  # 6% for L1

print(f"\n📊 Correct Payout:")
print(f"   Amount: ${correct_amount_usd} USD (Rs{float(correct_amount_usd) * settings.ADMIN_USD_TO_PKR:.2f} PKR)")

# Calculate difference
difference_usd = (correct_amount_usd - Decimal(str(payout.amount_usd))).quantize(Decimal('0.01'))
difference_pkr = float(difference_usd) * settings.ADMIN_USD_TO_PKR

print(f"\n💰 Difference:")
print(f"   ${difference_usd} USD (Rs{difference_pkr:.2f} PKR)")

if difference_usd <= 0:
    print("\n✅ Payout is already correct or higher than expected")
    print("   No adjustment needed")
    sys.exit(0)

# Ask for confirmation
print("\n" + "-"*80)
print("⚠️  CONFIRMATION REQUIRED")
print("-"*80)
print(f"\nThis will:")
print(f"1. Update payout amount from ${payout.amount_usd} to ${correct_amount_usd}")
print(f"2. Add ${difference_usd} USD to {referrer.email}'s wallet")
print(f"3. Create a transaction record for the adjustment")
print("\n" + "-"*80)

response = input("\nProceed with correction? (yes/no): ").strip().lower()

if response != 'yes':
    print("\n❌ Correction cancelled")
    sys.exit(0)

print("\n" + "-"*80)
print("🔧 APPLYING CORRECTION")
print("-"*80 + "\n")

# Update payout
old_amount = payout.amount_usd
payout.amount_usd = correct_amount_usd
payout.save()
print(f"✅ Updated payout: ${old_amount} → ${correct_amount_usd}")

# Add difference to referrer's wallet
wallet, _ = Wallet.objects.get_or_create(user=referrer)
wallet.income_usd = (Decimal(wallet.income_usd) + difference_usd).quantize(Decimal('0.01'))
wallet.save()
print(f"✅ Added ${difference_usd} to {referrer.email}'s wallet")

# Create transaction record
Transaction.objects.create(
    wallet=wallet,
    type=Transaction.CREDIT,
    amount_usd=difference_usd,
    meta={
        'type': 'referral_correction',
        'reason': 'Fix for old user approved before actual deposit amount fix',
        'referee': user.email,
        'old_amount_usd': str(old_amount),
        'new_amount_usd': str(correct_amount_usd),
        'difference_usd': str(difference_usd),
        'signup_amount_pkr': str(signup_amount_pkr),
        'level': 1
    }
)
print(f"✅ Created transaction record")

print("\n" + "="*80)
print("✅ CORRECTION COMPLETE")
print("="*80 + "\n")

print(f"Summary:")
print(f"  User: {user.email}")
print(f"  Referrer: {referrer.email}")
print(f"  Old bonus: ${old_amount} USD")
print(f"  New bonus: ${correct_amount_usd} USD")
print(f"  Difference: ${difference_usd} USD (Rs{difference_pkr:.2f} PKR)")
print(f"  Status: ✅ Corrected")

print("\n" + "="*80 + "\n")