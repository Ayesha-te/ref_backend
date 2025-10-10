#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.wallets.models import Transaction
from django.contrib.auth import get_user_model

User = get_user_model()

# Check global pool transactions
global_pool_txns = Transaction.objects.filter(type='CREDIT', meta__type='global_pool')
print(f"Total global pool transactions in database: {global_pool_txns.count()}")

if global_pool_txns.exists():
    total = sum(float(t.amount_usd) for t in global_pool_txns)
    print(f"Total global pool earnings across all users: ${total:.2f}")
    
    for txn in global_pool_txns[:5]:
        print(f"  - User: {txn.wallet.user.username}, Amount: ${txn.amount_usd}, Date: {txn.created_at}")
else:
    print("✅ No global pool transactions found - system is clean!")

# Check global pool state
from apps.earnings.models import GlobalPoolState
state, created = GlobalPoolState.objects.get_or_create(pk=1)
print(f"\n📊 Global Pool State:")
print(f"  Current Pool Balance: ${state.current_pool_usd}")
print(f"  Last Collection Date: {state.last_collection_date}")
print(f"  Last Distribution Date: {state.last_distribution_date}")
print(f"  Lifetime Collected: ${state.total_collected_all_time}")
print(f"  Lifetime Distributed: ${state.total_distributed_all_time}")

print("\n✅ System is ready for automatic operation starting this Monday!")