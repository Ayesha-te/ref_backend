#!/usr/bin/env python
import os
import django

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
    print(f"   Current Income: ${wallet.get_current_income_usd()}")
    print(f"   Passive Earnings: ${wallet.get_passive_earnings_usd()}")
    
    # Check transactions
    passive_txns = Transaction.objects.filter(wallet=wallet, type='CREDIT', meta__type='passive')
    referral_txns = Transaction.objects.filter(wallet=wallet, type='CREDIT', meta__type='referral')
    milestone_txns = Transaction.objects.filter(wallet=wallet, type='CREDIT', meta__type='milestone')
    global_pool_txns = Transaction.objects.filter(wallet=wallet, type='CREDIT', meta__type='global_pool')
    
    print(f"   Transactions:")
    print(f"     - Passive: {passive_txns.count()} (${sum(float(t.amount_usd) for t in passive_txns):.2f})")
    print(f"     - Referral: {referral_txns.count()} (${sum(float(t.amount_usd) for t in referral_txns):.2f})")
    print(f"     - Milestone: {milestone_txns.count()} (${sum(float(t.amount_usd) for t in milestone_txns):.2f})")
    print(f"     - Global Pool: {global_pool_txns.count()} (${sum(float(t.amount_usd) for t in global_pool_txns):.2f})")
    print()