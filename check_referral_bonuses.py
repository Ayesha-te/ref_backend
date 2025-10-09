#!/usr/bin/env python
"""
Check Referral Bonuses
======================
This script checks why you're getting 3 bonuses for 2 members.
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

User = get_user_model()

print("\n" + "="*70)
print("🔍 REFERRAL BONUS DIAGNOSTIC")
print("="*70 + "\n")

# Get your user (assuming you're the one checking)
print("Enter your username:")
username = input().strip()

try:
    user = User.objects.get(username=username)
    print(f"\n✅ Found user: {user.username} (ID: {user.id})")
    print(f"   Email: {user.email}")
    print(f"   Approved: {user.is_approved}")
    
    # Check direct referrals
    direct_referrals = User.objects.filter(referred_by=user)
    print(f"\n📊 Direct Referrals: {direct_referrals.count()}")
    for ref in direct_referrals:
        print(f"   - {ref.username} (ID: {ref.id}, Approved: {ref.is_approved})")
    
    # Check referral payouts received
    payouts = ReferralPayout.objects.filter(referrer=user).order_by('-created_at')
    print(f"\n💰 Referral Payouts Received: {payouts.count()}")
    for payout in payouts:
        print(f"   - From: {payout.referee.username} | Level: {payout.level} | Amount: ${payout.amount_usd} | Date: {payout.created_at}")
    
    # Check referral transactions
    wallet = user.wallet
    ref_transactions = Transaction.objects.filter(
        wallet=wallet,
        type=Transaction.CREDIT,
        meta__type='referral'
    ).order_by('-created_at')
    
    print(f"\n📝 Referral Transactions: {ref_transactions.count()}")
    for tx in ref_transactions:
        source_user_id = tx.meta.get('source_user')
        try:
            source_user = User.objects.get(id=source_user_id)
            source_name = source_user.username
        except:
            source_name = f"Unknown (ID: {source_user_id})"
        
        print(f"   - From: {source_name} | Level: {tx.meta.get('level')} | Amount: ${tx.amount_usd} | Date: {tx.created_at}")
        print(f"     Meta: {tx.meta}")
    
    # Summary
    print(f"\n" + "="*70)
    print("SUMMARY:")
    print(f"  Direct Referrals: {direct_referrals.count()}")
    print(f"  Referral Payouts: {payouts.count()}")
    print(f"  Referral Transactions: {ref_transactions.count()}")
    
    if ref_transactions.count() > direct_referrals.count():
        print(f"\n⚠️  WARNING: You have more transactions ({ref_transactions.count()}) than direct referrals ({direct_referrals.count()})")
        print("   This could indicate:")
        print("   1. Duplicate signal triggers")
        print("   2. You're receiving bonuses from indirect referrals (L2/L3)")
        print("   3. Some referrals were deleted but transactions remain")
    
    print("="*70 + "\n")
    
except User.DoesNotExist:
    print(f"❌ User '{username}' not found")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()