#!/usr/bin/env python
"""
Diagnose Duplicate Referral Bonuses
====================================

This script investigates why a user received 5 referral bonuses for only 3 team members.
It checks for:
1. Duplicate ReferralPayout records
2. Duplicate Transaction records
3. Multiple approvals of the same user
4. Signal firing multiple times
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
from apps.wallets.models import Transaction
from django.db.models import Count

User = get_user_model()

print("\n" + "="*80)
print("🔍 DUPLICATE REFERRAL BONUS DIAGNOSTIC")
print("="*80 + "\n")

# Get the user
user_email = input("Enter user email to check (or press Enter for 'sardarlaeiq3@gmail.com'): ").strip()
if not user_email:
    user_email = "sardarlaeiq3@gmail.com"

try:
    user = User.objects.get(email=user_email)
    print(f"✅ Found user: {user.username} ({user.email})")
    print(f"   Referral Code: {user.referral_code}")
    print(f"   Is Approved: {user.is_approved}")
except User.DoesNotExist:
    print(f"❌ User with email '{user_email}' not found!")
    sys.exit(1)

print("\n" + "-"*80)
print("📊 TEAM MEMBERS (Direct Referrals)")
print("-"*80)

direct_referrals = User.objects.filter(referred_by=user)
print(f"Total Direct Referrals: {direct_referrals.count()}")

for idx, ref in enumerate(direct_referrals, 1):
    print(f"\n{idx}. {ref.username} ({ref.email})")
    print(f"   Referral Code: {ref.referral_code}")
    print(f"   Is Approved: {ref.is_approved}")
    print(f"   Created: {ref.date_joined}")

print("\n" + "-"*80)
print("💰 REFERRAL PAYOUTS RECEIVED (as Referrer)")
print("-"*80)

payouts = ReferralPayout.objects.filter(referrer=user).order_by('created_at')
print(f"Total Payouts: {payouts.count()}")

payout_summary = {}
for payout in payouts:
    print(f"\n  • From: {payout.referee.username} ({payout.referee.email})")
    print(f"    Level: L{payout.level}")
    print(f"    Amount: ${payout.amount_usd}")
    print(f"    Created: {payout.created_at}")
    
    # Track duplicates
    key = (payout.referee.id, payout.level)
    if key not in payout_summary:
        payout_summary[key] = []
    payout_summary[key].append(payout)

print("\n" + "-"*80)
print("🚨 DUPLICATE DETECTION")
print("-"*80)

duplicates_found = False
for (referee_id, level), payout_list in payout_summary.items():
    if len(payout_list) > 1:
        duplicates_found = True
        referee = User.objects.get(id=referee_id)
        print(f"\n⚠️  DUPLICATE FOUND!")
        print(f"   Referee: {referee.username} ({referee.email})")
        print(f"   Level: L{level}")
        print(f"   Count: {len(payout_list)} payouts (should be 1)")
        print(f"   Timestamps:")
        for p in payout_list:
            print(f"     - {p.created_at} (ID: {p.id})")

if not duplicates_found:
    print("✅ No duplicate payouts found in ReferralPayout table")

print("\n" + "-"*80)
print("💳 TRANSACTION RECORDS (Referral Bonuses)")
print("-"*80)

try:
    wallet = user.wallet
    transactions = Transaction.objects.filter(
        wallet=wallet,
        type=Transaction.CREDIT,
        meta__type='referral'
    ).order_by('created_at')
    
    print(f"Total Referral Bonus Transactions: {transactions.count()}")
    
    tx_summary = {}
    for tx in transactions:
        meta = tx.meta or {}
        source_user_id = meta.get('source_user')
        level = meta.get('level', '?')
        
        print(f"\n  • Amount: ${tx.amount_usd}")
        print(f"    Level: L{level}")
        print(f"    Source User ID: {source_user_id}")
        print(f"    Created: {tx.created_at}")
        print(f"    Meta: {meta}")
        
        # Track duplicates
        if source_user_id:
            key = (source_user_id, level)
            if key not in tx_summary:
                tx_summary[key] = []
            tx_summary[key].append(tx)
    
    print("\n" + "-"*80)
    print("🚨 TRANSACTION DUPLICATE DETECTION")
    print("-"*80)
    
    tx_duplicates_found = False
    for (source_user_id, level), tx_list in tx_summary.items():
        if len(tx_list) > 1:
            tx_duplicates_found = True
            try:
                source_user = User.objects.get(id=source_user_id)
                print(f"\n⚠️  DUPLICATE TRANSACTIONS FOUND!")
                print(f"   Source User: {source_user.username} ({source_user.email})")
                print(f"   Level: L{level}")
                print(f"   Count: {len(tx_list)} transactions (should be 1)")
                print(f"   Timestamps:")
                for t in tx_list:
                    print(f"     - {t.created_at} (ID: {t.id}, Amount: ${t.amount_usd})")
            except User.DoesNotExist:
                print(f"\n⚠️  DUPLICATE TRANSACTIONS FOUND!")
                print(f"   Source User ID: {source_user_id} (user not found)")
                print(f"   Level: L{level}")
                print(f"   Count: {len(tx_list)} transactions")
    
    if not tx_duplicates_found:
        print("✅ No duplicate transactions found")
        
except Exception as e:
    print(f"❌ Error checking transactions: {e}")

print("\n" + "-"*80)
print("📈 SUMMARY")
print("-"*80)

print(f"\nDirect Referrals: {direct_referrals.count()}")
print(f"Referral Payouts: {payouts.count()}")
print(f"Expected Payouts: {direct_referrals.count()} (1 per direct referral at L1)")

if payouts.count() > direct_referrals.count():
    print(f"\n⚠️  ISSUE DETECTED: More payouts ({payouts.count()}) than direct referrals ({direct_referrals.count()})")
    print(f"   Difference: {payouts.count() - direct_referrals.count()} extra payouts")
    print(f"\n   Possible causes:")
    print(f"   1. Signal fired multiple times for the same user approval")
    print(f"   2. User was approved multiple times")
    print(f"   3. Manual payout creation")
    print(f"   4. Indirect referrals (L2 or L3) - check if user has upline")

print("\n" + "-"*80)
print("🔧 RECOMMENDED ACTIONS")
print("-"*80)

if duplicates_found or tx_duplicates_found:
    print("\n1. Add duplicate prevention to the signal:")
    print("   - Check if ReferralPayout already exists before creating")
    print("   - Add unique constraint on (referrer, referee, level)")
    print("\n2. Clean up duplicate records:")
    print("   - Keep the first payout, delete duplicates")
    print("   - Reverse duplicate transactions")
    print("\n3. Add signal guard:")
    print("   - Use a flag to prevent multiple signal triggers")
    print("   - Or check if payouts already exist")
else:
    print("\n✅ No duplicates found. The extra bonuses might be from:")
    print("   - L2 or L3 level referrals (indirect)")
    print("   - Check if the user has an upline (referred_by)")

print("\n" + "="*80 + "\n")