#!/usr/bin/env python
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.wallets.models import Wallet, Transaction
from django.contrib.auth import get_user_model

User = get_user_model()

# Check all wallets
wallets = Wallet.objects.all()
print(f"Total wallets: {wallets.count()}\n")

for wallet in wallets:
    print(f"👤 User: {wallet.user.username}")
    print(f"   Available: ${wallet.available_usd}")
    print(f"   Hold: ${wallet.hold_usd}")
    print(f"   Income (field): ${wallet.income_usd}")
    
    # Check transactions manually (SQLite compatible)
    all_txns = Transaction.objects.filter(wallet=wallet, type='CREDIT')
    
    passive_total = 0
    referral_total = 0
    milestone_total = 0
    global_pool_total = 0
    deposit_total = 0
    other_total = 0
    
    for txn in all_txns:
        meta_type = txn.meta.get('type') if txn.meta else None
        amount = float(txn.amount_usd)
        
        if meta_type == 'passive':
            passive_total += amount
        elif meta_type == 'referral':
            referral_total += amount
        elif meta_type == 'milestone':
            milestone_total += amount
        elif meta_type == 'global_pool':
            global_pool_total += amount
        elif meta_type == 'deposit':
            deposit_total += amount
        else:
            other_total += amount
    
    total_income = passive_total + referral_total + milestone_total + global_pool_total
    
    print(f"   Transactions:")
    print(f"     - Passive: ${passive_total:.2f}")
    print(f"     - Referral: ${referral_total:.2f}")
    print(f"     - Milestone: ${milestone_total:.2f}")
    print(f"     - Global Pool: ${global_pool_total:.2f}")
    print(f"     - Deposits: ${deposit_total:.2f}")
    print(f"     - Other: ${other_total:.2f}")
    print(f"   📊 Total Income (calculated): ${total_income:.2f}")
    print()

print("\n✅ Global Pool System Status:")
from apps.earnings.models import GlobalPoolState
state, created = GlobalPoolState.objects.get_or_create(pk=1)
print(f"  Current Pool Balance: ${state.current_pool_usd}")
print(f"  Ready for Monday collection: {'Yes' if state.last_collection_date is None else f'Last collected: {state.last_collection_date}'}")