#!/usr/bin/env python
"""
Check Referral Bonuses for sardarlaeiq3@gmail.com
==================================================
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

try:
    # Try to find user by email or username
    user = None
    try:
        user = User.objects.get(email='sardarlaeiq3@gmail.com')
    except User.DoesNotExist:
        try:
            user = User.objects.get(username='sardarlaeiq3@gmail.com')
        except User.DoesNotExist:
            pass
    
    if not user:
        print("❌ User 'sardarlaeiq3@gmail.com' not found")
        print("\nAvailable users:")
        for u in User.objects.all()[:10]:
            print(f"   - {u.username} ({u.email})")
        sys.exit(1)
    
    print(f"✅ Found user: {user.username} (ID: {user.id})")
    print(f"   Email: {user.email}")
    print(f"   Approved: {user.is_approved}")
    
    # Check direct referrals
    direct_referrals = User.objects.filter(referred_by=user)
    print(f"\n📊 Direct Referrals: {direct_referrals.count()}")
    for ref in direct_referrals:
        print(f"   - {ref.username} (ID: {ref.id}, Approved: {ref.is_approved}, Active: {ref.is_active})")
    
    # Check referral payouts received
    payouts = ReferralPayout.objects.filter(referrer=user).order_by('-created_at')
    print(f"\n💰 Referral Payouts Received: {payouts.count()}")
    for payout in payouts:
        print(f"   - From: {payout.referee.username} | Level: {payout.level} | Amount: ${payout.amount_usd} | Date: {payout.created_at}")
    
    # Check referral transactions
    try:
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
            print(f"     Trigger: {tx.meta.get('trigger')} | Base: ${tx.meta.get('base')} | Pct: {tx.meta.get('pct')}")
    except:
        print("\n⚠️  No wallet found for user")
        ref_transactions = []
    
    # Summary
    print(f"\n" + "="*70)
    print("SUMMARY:")
    print(f"  Direct Referrals: {direct_referrals.count()}")
    print(f"  Referral Payouts: {payouts.count()}")
    print(f"  Referral Transactions: {len(ref_transactions) if ref_transactions else 0}")
    
    if ref_transactions and len(ref_transactions) > direct_referrals.count():
        print(f"\n⚠️  ISSUE DETECTED:")
        print(f"   You have {len(ref_transactions)} transactions but only {direct_referrals.count()} direct referrals")
        print("\n   Possible causes:")
        print("   1. Signal fired multiple times for same user (duplicate bonuses)")
        print("   2. Some referrals were deleted but transactions remain")
        print("   3. System error during approval process")
    
    print("="*70 + "\n")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()