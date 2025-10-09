#!/usr/bin/env python
"""
Check User Income Issue
=======================
This script checks why sardarlaeiq3@gmail.com shows 0 income despite having 3 referrals.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import models
from apps.wallets.models import Wallet, Transaction
from apps.referrals.models import ReferralPayout
from apps.earnings.models_global_pool import GlobalPool
from decimal import Decimal

User = get_user_model()

print("\n" + "="*80)
print("🔍 USER INCOME DIAGNOSTIC")
print("="*80 + "\n")

# Check the specific user
email = "sardarlaeiq3@gmail.com"
try:
    user = User.objects.get(email=email)
    print(f"✅ Found user: {user.username} ({user.email})")
    print(f"   - Is Approved: {user.is_approved}")
    print(f"   - Referral Code: {user.referral_code}")
    print(f"   - Referred By: {user.referred_by}")
    
    # Check referrals
    referrals = user.referrals.all()
    print(f"\n📊 Referrals Count: {referrals.count()}")
    for i, ref in enumerate(referrals, 1):
        print(f"   {i}. {ref.username} ({ref.email}) - Approved: {ref.is_approved}")
    
    # Check wallet
    try:
        wallet = user.wallet
        print(f"\n💰 Wallet Status:")
        print(f"   - Available USD: ${wallet.available_usd}")
        print(f"   - Hold USD: ${wallet.hold_usd}")
        print(f"   - Income USD (field): ${wallet.income_usd}")
        
        # Calculate current income using the method
        calculated_income = wallet.get_current_income_usd()
        print(f"   - Income USD (calculated): ${calculated_income}")
        
        # Check transactions
        transactions = wallet.transactions.all()
        print(f"\n📝 Transactions Count: {transactions.count()}")
        
        if transactions.exists():
            print("\n   Transaction Details:")
            for tx in transactions:
                print(f"   - {tx.type}: ${tx.amount_usd} | Meta: {tx.meta} | Date: {tx.created_at}")
        else:
            print("   ⚠️  No transactions found!")
        
        # Check income-related transactions specifically
        income_txs = wallet.transactions.filter(
            type=Transaction.CREDIT
        ).filter(
            models.Q(meta__type='passive') | 
            models.Q(meta__type='referral') | 
            models.Q(meta__type='milestone') |
            models.Q(meta__type='global_pool')
        )
        print(f"\n   Income Transactions: {income_txs.count()}")
        for tx in income_txs:
            print(f"   - {tx.meta.get('type', 'unknown')}: ${tx.amount_usd}")
            
    except Wallet.DoesNotExist:
        print(f"\n❌ No wallet found for user!")
    
    # Check referral payouts
    payouts = ReferralPayout.objects.filter(referrer=user)
    print(f"\n💵 Referral Payouts (as referrer): {payouts.count()}")
    if payouts.exists():
        total_payout = sum(p.amount_usd for p in payouts)
        print(f"   Total Payout Amount: ${total_payout}")
        for payout in payouts:
            print(f"   - Level {payout.level}: ${payout.amount_usd} from {payout.referee.username} ({payout.created_at})")
    else:
        print("   ⚠️  No referral payouts found!")
        print("\n   🔍 Checking why payouts weren't created...")
        
        # Check if referrals have deposits
        for ref in referrals:
            deposits = ref.deposit_requests.filter(status='CREDITED')
            print(f"\n   Referral: {ref.username}")
            print(f"   - Deposits: {deposits.count()}")
            if deposits.exists():
                for dep in deposits:
                    print(f"     * ${dep.amount_usd} - Status: {dep.status} - Date: {dep.created_at}")
            
            # Check if this referral has any payouts recorded
            ref_payouts = ReferralPayout.objects.filter(referee=ref)
            print(f"   - Payouts triggered by this referral: {ref_payouts.count()}")
            if ref_payouts.exists():
                for rp in ref_payouts:
                    print(f"     * To {rp.referrer.username}: Level {rp.level}, ${rp.amount_usd}")
    
except User.DoesNotExist:
    print(f"❌ User with email '{email}' not found!")

# Check Global Pool
print("\n" + "="*80)
print("🌍 GLOBAL POOL STATUS")
print("="*80 + "\n")

pools = GlobalPool.objects.all()
if pools.exists():
    for pool in pools:
        print(f"Global Pool ID {pool.id}: ${pool.balance_usd} (Updated: {pool.updated_at})")
else:
    print("✅ No global pool records found (expected after database removal)")

print("\n" + "="*80 + "\n")