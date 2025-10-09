#!/usr/bin/env python
"""
Test Income Calculation
========================

This script tests the income calculation for sardarlaeiq3@gmail.com
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models import Sum, Q
from apps.accounts.models import User
from apps.wallets.models import Wallet, Transaction
from decimal import Decimal

email = "sardarlaeiq3@gmail.com"
user = User.objects.get(email=email)
wallet = user.wallet

print("\n" + "="*80)
print(f"Testing Income Calculation for {email}")
print("="*80 + "\n")

# Get all transactions
all_txs = wallet.transactions.all()
print(f"Total transactions: {all_txs.count()}\n")

# Manually calculate
print("Manual Calculation:")
print("-" * 80)

total_credits = Decimal('0')
total_debits = Decimal('0')

for tx in all_txs:
    meta_type = tx.meta.get('type', 'unknown')
    source = tx.meta.get('source', '')
    non_income = tx.meta.get('non_income', False)
    
    print(f"{tx.type:6} ${tx.amount_usd:6.2f} | type={meta_type:20} | source={source:15} | non_income={non_income}")
    
    if tx.type == Transaction.CREDIT:
        if meta_type in ['passive', 'referral', 'milestone', 'global_pool', 'referral_correction']:
            if source != 'signup-initial' and not non_income:
                total_credits += tx.amount_usd
                print(f"       ✅ Counted as income credit")
            else:
                print(f"       ❌ Excluded (source={source}, non_income={non_income})")
        else:
            print(f"       ⚠️  Not an income type")
    
    elif tx.type == Transaction.DEBIT:
        if meta_type in ['withdrawal', 'referral_reversal']:
            total_debits += tx.amount_usd
            print(f"       ✅ Counted as income debit")
        else:
            print(f"       ⚠️  Not an income debit type")

print("\n" + "-" * 80)
print(f"Total Income Credits: ${total_credits:.2f}")
print(f"Total Income Debits:  ${total_debits:.2f}")
print(f"Net Income:           ${(total_credits - total_debits):.2f}")

print("\n" + "="*80)
print("Using get_current_income_usd() method:")
print("="*80)
calculated = wallet.get_current_income_usd()
print(f"Calculated Income: ${calculated:.2f}")

print("\n" + "="*80)
print("Stored income_usd field:")
print("="*80)
print(f"Stored Income: ${wallet.income_usd:.2f}")

print("\n" + "="*80 + "\n")