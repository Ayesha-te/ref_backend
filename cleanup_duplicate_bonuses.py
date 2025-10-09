#!/usr/bin/env python
"""
Cleanup Duplicate Referral Bonuses
===================================

This script identifies and optionally removes duplicate referral bonuses
that were created due to the signal firing multiple times.

IMPORTANT: This script will show you what duplicates exist and ask for
confirmation before deleting anything.
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
from apps.wallets.models import Transaction, Wallet
from django.db.models import Count

User = get_user_model()

print("\n" + "="*80)
print("🧹 DUPLICATE REFERRAL BONUS CLEANUP")
print("="*80 + "\n")

print("⚠️  WARNING: This script will identify duplicate referral bonuses.")
print("   Review carefully before confirming any deletions!\n")

# Find all users with duplicate payouts
print("🔍 Scanning for duplicate referral payouts...\n")

all_payouts = ReferralPayout.objects.all().order_by('referrer', 'referee', 'level', 'created_at')

# Group by (referrer, referee, level)
duplicates_map = {}
for payout in all_payouts:
    key = (payout.referrer.id, payout.referee.id, payout.level)
    if key not in duplicates_map:
        duplicates_map[key] = []
    duplicates_map[key].append(payout)

# Find duplicates
duplicate_groups = {k: v for k, v in duplicates_map.items() if len(v) > 1}

if not duplicate_groups:
    print("✅ No duplicate referral payouts found!")
    print("   The system is clean.\n")
    sys.exit(0)

print(f"⚠️  Found {len(duplicate_groups)} groups with duplicate payouts:\n")

total_duplicates = 0
total_amount_to_reverse = Decimal('0.00')

for (referrer_id, referee_id, level), payouts in duplicate_groups.items():
    referrer = User.objects.get(id=referrer_id)
    referee = User.objects.get(id=referee_id)
    
    print(f"📌 Duplicate Group:")
    print(f"   Referrer: {referrer.username} ({referrer.email})")
    print(f"   Referee: {referee.username} ({referee.email})")
    print(f"   Level: L{level}")
    print(f"   Total Payouts: {len(payouts)} (should be 1)")
    print(f"   Payouts:")
    
    for idx, payout in enumerate(payouts, 1):
        marker = "✅ KEEP" if idx == 1 else "❌ DELETE"
        print(f"     {idx}. {marker} - ${payout.amount_usd} at {payout.created_at} (ID: {payout.id})")
        
        if idx > 1:
            total_duplicates += 1
            total_amount_to_reverse += Decimal(str(payout.amount_usd))
    
    print()

print("-"*80)
print(f"📊 SUMMARY:")
print(f"   Duplicate Payouts to Remove: {total_duplicates}")
print(f"   Total Amount to Reverse: ${total_amount_to_reverse}")
print("-"*80 + "\n")

# Ask for confirmation
response = input("Do you want to proceed with cleanup? (yes/no): ").strip().lower()

if response != 'yes':
    print("\n❌ Cleanup cancelled. No changes made.")
    sys.exit(0)

print("\n🧹 Starting cleanup...\n")

deleted_payouts = 0
reversed_transactions = 0
reversed_amount = Decimal('0.00')

for (referrer_id, referee_id, level), payouts in duplicate_groups.items():
    referrer = User.objects.get(id=referrer_id)
    
    # Keep the first payout, delete the rest
    for idx, payout in enumerate(payouts):
        if idx == 0:
            continue  # Keep the first one
        
        # Find and reverse the corresponding transaction
        try:
            wallet = Wallet.objects.get(user=referrer)
            # Find transaction with matching metadata
            matching_txs = Transaction.objects.filter(
                wallet=wallet,
                type=Transaction.CREDIT,
                amount_usd=payout.amount_usd,
                meta__type='referral',
                meta__level=level,
                meta__source_user=referee_id
            )
            
            for tx in matching_txs:
                # Create a reversal transaction
                Transaction.objects.create(
                    wallet=wallet,
                    type=Transaction.DEBIT,
                    amount_usd=payout.amount_usd,
                    meta={
                        'type': 'referral_reversal',
                        'reason': 'duplicate_cleanup',
                        'original_tx_id': tx.id,
                        'level': level,
                        'source_user': referee_id
                    }
                )
                
                # Update wallet income
                wallet.income_usd = (Decimal(wallet.income_usd) - Decimal(payout.amount_usd)).quantize(Decimal('0.01'))
                wallet.save()
                
                reversed_transactions += 1
                reversed_amount += Decimal(str(payout.amount_usd))
                print(f"   ✅ Reversed transaction ${payout.amount_usd} for {referrer.username}")
                break  # Only reverse one matching transaction
                
        except Wallet.DoesNotExist:
            print(f"   ⚠️  No wallet found for {referrer.username}")
        except Exception as e:
            print(f"   ⚠️  Error reversing transaction: {e}")
        
        # Delete the duplicate payout
        payout.delete()
        deleted_payouts += 1
        print(f"   ✅ Deleted duplicate payout (ID: {payout.id})")

print("\n" + "="*80)
print("✅ CLEANUP COMPLETE!")
print("="*80)
print(f"\nDeleted Payouts: {deleted_payouts}")
print(f"Reversed Transactions: {reversed_transactions}")
print(f"Total Amount Reversed: ${reversed_amount}")
print("\n⚠️  IMPORTANT: The duplicate prevention has been added to the signal.")
print("   Future approvals will not create duplicates.\n")
print("="*80 + "\n")