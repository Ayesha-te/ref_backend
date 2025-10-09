#!/usr/bin/env python
"""
Find User with 3 Referrals
===========================

This script finds which user has 3 referrals.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.models import User
from apps.wallets.models import Wallet, Transaction
from django.db.models import Count

print("\n" + "="*80)
print("🔍 FINDING USER WITH 3 REFERRALS")
print("="*80 + "\n")

# Find users with referrals
users_with_referrals = User.objects.annotate(
    referral_count=Count('referrals')
).filter(referral_count__gt=0).order_by('-referral_count')

print(f"Users with referrals:\n")

for user in users_with_referrals:
    referral_count = user.referrals.count()
    print(f"📧 {user.email} (Username: {user.username})")
    print(f"   - Referrals: {referral_count}")
    print(f"   - Referral Code: {user.referral_code}")
    print(f"   - Approved: {user.is_approved}")
    
    # Get wallet info
    try:
        wallet = user.wallet
        print(f"   - Wallet Income (stored): ${wallet.income_usd:.2f}")
        print(f"   - Wallet Income (calculated): ${wallet.get_current_income_usd():.2f}")
        
        # Get referral transactions
        referral_transactions = Transaction.objects.filter(
            wallet=wallet,
            transaction_type='credit',
            income_type='referral'
        )
        total_referral_income = sum(t.amount_usd for t in referral_transactions)
        print(f"   - Referral Income from Transactions: ${total_referral_income:.2f}")
        print(f"   - Referral Transactions Count: {referral_transactions.count()}")
        
    except Exception as e:
        print(f"   - Wallet Error: {e}")
    
    # List referrals
    print(f"   - Referrals:")
    for i, referral in enumerate(user.referrals.all(), 1):
        print(f"     {i}. {referral.email} (Username: {referral.username}, Approved: {referral.is_approved})")
        
        # Check if referral has deposits
        try:
            ref_wallet = referral.wallet
            deposits = Transaction.objects.filter(
                wallet=ref_wallet,
                transaction_type='credit',
                income_type='passive'
            )
            total_deposits = sum(d.amount_usd for d in deposits)
            print(f"        - Deposits: ${total_deposits:.2f} ({deposits.count()} transactions)")
        except Exception as e:
            print(f"        - Wallet Error: {e}")
    
    print()

print("="*80 + "\n")