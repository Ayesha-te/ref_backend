#!/usr/bin/env python
"""
Quick verification that the fix works
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check if DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    print("\n⚠️  DATABASE_URL NOT SET")
    print("Run with: $env:DATABASE_URL='...'; python verify_fix.py")
    sys.exit(1)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.models import User
from apps.wallets.models import Wallet

print("\n" + "="*80)
print("✅ VERIFYING INCOME CALCULATION FIX")
print("="*80 + "\n")

email = "sardarlaeiq3@gmail.com"
user = User.objects.get(email=email)
wallet = user.wallet

print(f"User: {email}")
print(f"Stored income_usd: ${wallet.income_usd}")
print(f"Calculated income: ${wallet.get_current_income_usd()}")

if wallet.income_usd == wallet.get_current_income_usd():
    print("\n✅ SUCCESS! Income calculation matches stored value!")
else:
    print(f"\n⚠️  Mismatch: Stored=${wallet.income_usd}, Calculated=${wallet.get_current_income_usd()}")

print("\n" + "="*80 + "\n")