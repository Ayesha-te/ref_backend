#!/usr/bin/env python
"""
Check All Referral Bonuses
===========================
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.referrals.models import ReferralPayout
from apps.wallets.models import Transaction
from django.db.models import Count

User = get_user_model()

print("\n" + "="*70)
print("🔍 ALL REFERRAL BONUSES DIAGNOSTIC")
print("="*70 + "\n")

# Find users who have received referral bonuses
users_with_bonuses = User.objects.annotate(
    bonus_count=Count('referral_payouts')
).filter(bonus_count__gt=0).order_by('-bonus_count')

print(f"Users with referral bonuses: {users_with_bonuses.count()}\n")

for user in users_with_bonuses:
    print(f"\n{'='*70}")
    print(f"👤 User: {user.username} ({user.email})")
    print(f"   ID: {user.id} | Approved: {user.is_approved}")
    
    # Check direct referrals
    direct_referrals = User.objects.filter(referred_by=user)
    print(f"\n📊 Direct Referrals: {direct_referrals.count()}")
    for ref in direct_referrals:
        print(f"   - {ref.username} (Approved: {ref.is_approved})")
    
    # Check referral payouts
    payouts = ReferralPayout.objects.filter(referrer=user).order_by('-created_at')
    print(f"\n💰 Referral Payouts: {payouts.count()}")
    
    # Group by referee to see duplicates
    from collections import defaultdict
    by_referee = defaultdict(list)
    for payout in payouts:
        by_referee[payout.referee.username].append(payout)
    
    for referee_name, referee_payouts in by_referee.items():
        print(f"\n   From {referee_name}:")
        for payout in referee_payouts:
            print(f"      Level {payout.level}: ${payout.amount_usd} at {payout.created_at}")
        
        if len(referee_payouts) > 1:
            print(f"      ⚠️  DUPLICATE: {len(referee_payouts)} payouts from same user!")
    
    # Check transactions
    try:
        wallet = user.wallet
        ref_transactions = Transaction.objects.filter(
            wallet=wallet,
            type=Transaction.CREDIT,
            meta__type='referral'
        ).order_by('-created_at')
        
        print(f"\n📝 Referral Transactions: {ref_transactions.count()}")
        
        # Group by source
        by_source = defaultdict(list)
        for tx in ref_transactions:
            source_id = tx.meta.get('source_user')
            by_source[source_id].append(tx)
        
        for source_id, txs in by_source.items():
            try:
                source_user = User.objects.get(id=source_id)
                source_name = source_user.username
            except:
                source_name = f"Unknown (ID: {source_id})"
            
            print(f"\n   From {source_name}:")
            for tx in txs:
                print(f"      Level {tx.meta.get('level')}: ${tx.amount_usd} at {tx.created_at}")
            
            if len(txs) > 1:
                print(f"      ⚠️  DUPLICATE: {len(txs)} transactions from same user!")
    
    except Exception as e:
        print(f"\n⚠️  Error checking wallet: {e}")
    
    # Summary for this user
    print(f"\n📊 SUMMARY for {user.username}:")
    print(f"   Direct Referrals: {direct_referrals.count()}")
    print(f"   Payouts Received: {payouts.count()}")
    
    if payouts.count() > direct_referrals.count():
        print(f"   ⚠️  ISSUE: {payouts.count()} payouts but only {direct_referrals.count()} direct referrals!")

print(f"\n{'='*70}\n")