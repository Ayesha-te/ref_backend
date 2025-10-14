#!/usr/bin/env python
"""
Debug script to investigate sardarlaeiq3@gmail.com transaction discrepancy
"""
import os
import django

os.environ.setdefault('DJANGO_SECRET_KEY', 'dev-secret-key')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.models import User
from apps.wallets.models import Wallet, Transaction
from decimal import Decimal

print("=" * 80)
print("🔍 DEBUGGING sardarlaeiq3@gmail.com TRANSACTIONS")
print("=" * 80)

user = User.objects.get(username='sardarlaeiq3@gmail.com')
wallet = user.wallet

print(f"\n👤 User: {user.username}")
print(f"💰 Wallet Income USD: ${wallet.income_usd}")
print(f"💰 Available USD: ${wallet.available_usd}")

# Get ALL transactions
all_txns = Transaction.objects.filter(wallet=wallet).order_by('created_at')

print(f"\n📋 ALL TRANSACTIONS ({all_txns.count()} total):")
print("-" * 80)

total_credits = Decimal('0')
total_debits = Decimal('0')

for txn in all_txns:
    meta_type = txn.meta.get('type', 'unknown')
    meta_source = txn.meta.get('source', '')
    meta_non_income = txn.meta.get('non_income', False)
    
    symbol = "+" if txn.type == 'CREDIT' else "-"
    
    print(f"{txn.created_at.strftime('%Y-%m-%d %H:%M')} | {txn.type:6} | {symbol}${txn.amount_usd:>8} | Type: {meta_type:20} | Source: {meta_source:20} | Non-income: {meta_non_income}")
    
    if txn.type == 'CREDIT':
        total_credits += txn.amount_usd
    else:
        total_debits += txn.amount_usd

print("-" * 80)
print(f"Total Credits:  ${total_credits}")
print(f"Total Debits:   ${total_debits}")
print(f"Net Balance:    ${total_credits - total_debits}")

# Now check what get_current_income_usd() returns
current_income = wallet.get_current_income_usd()
print(f"\n📊 get_current_income_usd(): ${current_income}")

# Manual calculation matching the script
from django.db.models import Q

referral_txns = all_txns.filter(meta__contains={'type': 'referral'}, type='CREDIT')
withdrawal_txns = all_txns.filter(type='DEBIT')

print(f"\n🔍 FILTERED TRANSACTIONS:")
print(f"Referral Credits: {referral_txns.count()} txns")
for txn in referral_txns:
    print(f"  - ${txn.amount_usd} | {txn.created_at.strftime('%Y-%m-%d')} | meta: {txn.meta}")

print(f"\nWithdrawal Debits: {withdrawal_txns.count()} txns")
for txn in withdrawal_txns:
    print(f"  - ${txn.amount_usd} | {txn.created_at.strftime('%Y-%m-%d')} | meta: {txn.meta}")

total_referral = sum([t.amount_usd for t in referral_txns])
total_withdrawals = sum([t.amount_usd for t in withdrawal_txns])

print(f"\n📊 MANUAL CALCULATION:")
print(f"Total Referral:    ${total_referral}")
print(f"Total Withdrawals: ${total_withdrawals}")
print(f"Manual Income:     ${total_referral - total_withdrawals}")

# Check what the wallet method is counting
print(f"\n🔍 CHECKING WALLET METHOD LOGIC:")
print("Looking for transactions that match wallet method criteria...")

income_credits = all_txns.filter(type='CREDIT').filter(
    Q(meta__contains={'type': 'passive'}) | 
    Q(meta__contains={'type': 'referral'}) | 
    Q(meta__contains={'type': 'milestone'}) |
    Q(meta__contains={'type': 'global_pool'}) |
    Q(meta__contains={'type': 'referral_correction'})
).exclude(
    meta__contains={'source': 'signup-initial'}
).exclude(
    meta__contains={'non_income': True}
)

print(f"\nIncome Credits (wallet method): {income_credits.count()} txns")
for txn in income_credits:
    print(f"  + ${txn.amount_usd} | {txn.created_at.strftime('%Y-%m-%d')} | Type: {txn.meta.get('type')} | Source: {txn.meta.get('source', 'N/A')}")

income_debits = all_txns.filter(type='DEBIT').filter(
    Q(meta__contains={'type': 'withdrawal'}) |
    Q(meta__contains={'type': 'referral_reversal'})
)

print(f"\nIncome Debits (wallet method): {income_debits.count()} txns")
for txn in income_debits:
    print(f"  - ${txn.amount_usd} | {txn.created_at.strftime('%Y-%m-%d')} | Type: {txn.meta.get('type')} | Source: {txn.meta.get('source', 'N/A')}")

total_income_credits = sum([t.amount_usd for t in income_credits])
total_income_debits = sum([t.amount_usd for t in income_debits])

print(f"\n📊 WALLET METHOD CALCULATION:")
print(f"Income Credits:  ${total_income_credits}")
print(f"Income Debits:   ${total_income_debits}")
print(f"Wallet Income:   ${total_income_credits - total_income_debits}")

print(f"\n🚨 DISCREPANCY ANALYSIS:")
print(f"Wallet Method:     ${current_income}")
print(f"Manual Calc:       ${total_referral - total_withdrawals}")
print(f"Difference:        ${current_income - (total_referral - total_withdrawals)}")
print(f"Stored income_usd: ${wallet.income_usd}")

print("\n" + "=" * 80)