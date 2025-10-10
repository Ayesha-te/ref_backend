#!/usr/bin/env python
"""
Global Pool Test Script
=======================

This script tests the global pool collection and distribution.
Run this after applying the fixes.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.earnings.models_global_pool import GlobalPool, GlobalPoolPayout
from apps.earnings.services import compute_daily_earning_usd, GLOBAL_POOL_CUT
from decimal import Decimal
from django.conf import settings

print("\n" + "="*70)
print("🏦 GLOBAL POOL SYSTEM TEST")
print("="*70 + "\n")

# Check configuration
print("📋 Configuration:")
print(f"  - GLOBAL_POOL_CUT: {GLOBAL_POOL_CUT} ({float(GLOBAL_POOL_CUT) * 100}%)")
print(f"  - From settings: {settings.ECONOMICS['GLOBAL_POOL_CUT']}")

# Check current pool balance
pool, created = GlobalPool.objects.get_or_create(pk=1)
print(f"\n💰 Current Global Pool Balance: ${pool.balance_usd}")
if created:
    print("  ⚠️  Pool was just created (first time)")

# Test calculation for day 1
print("\n🧮 Test Calculation (Day 1):")
metrics = compute_daily_earning_usd(1)
print(f"  - Package: $100.00")
print(f"  - Daily Rate: {metrics['percent']}%")
print(f"  - Gross Earning: ${metrics['gross_usd']}")
print(f"  - User Share (80%): ${metrics['user_share_usd']}")
print(f"  - Platform Hold (20%): ${metrics['platform_hold_usd']}")
print(f"  - Global Pool Cut ({float(GLOBAL_POOL_CUT) * 100}%): ${metrics['global_pool_usd']}")

# Check distribution history
print("\n📊 Distribution History:")
payouts = GlobalPoolPayout.objects.all().order_by('-distributed_on')
if payouts.exists():
    print(f"  Total Distributions: {payouts.count()}")
    print("\n  Last 5 Distributions:")
    for payout in payouts[:5]:
        print(f"    - {payout.distributed_on.strftime('%Y-%m-%d %H:%M')}: ${payout.amount_usd}")
        if payout.meta:
            print(f"      Users: {payout.meta.get('count', 'N/A')}, Per User: ${payout.meta.get('per_user_net', 'N/A')}")
else:
    print("  ❌ No distributions yet")

# Check cron schedule
print("\n⏰ Distribution Schedule:")
print(f"  - Frequency: Every Monday at 00:00 UTC")
print(f"  - Command: distribute_global_pool")
print(f"  - Configured in: core/settings.py CRONJOBS")

print("\n" + "="*70)
print("✅ TEST COMPLETE")
print("="*70)

print("\n💡 Next Steps:")
print("  1. Run daily earnings: python manage.py run_daily_earnings")
print("  2. Check pool balance increases")
print("  3. Wait for Monday or manually run: python manage.py distribute_global_pool")
print("  4. Verify users receive payouts")

print("\n" + "="*70 + "\n")