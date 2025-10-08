#!/usr/bin/env python
"""
Quick diagnostic script to check deposit status
"""
import os
import django

os.environ.setdefault('DJANGO_SECRET_KEY', 'dev-secret-key')
os.environ.setdefault('DJANGO_DEBUG', '1')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django.setup()

from apps.wallets.models import DepositRequest, Wallet
from django.contrib.auth import get_user_model

User = get_user_model()

print("="*70)
print("DEPOSIT STATUS CHECK")
print("="*70)
print()

# Check all deposits
deposits = DepositRequest.objects.all().order_by('created_at')
print(f"📊 Total Deposits: {deposits.count()}")
print()

if deposits.exists():
    print("Deposit Details:")
    print("-" * 70)
    for d in deposits:
        print(f"ID: {d.id}")
        print(f"  User: {d.user.username} (ID: {d.user.id})")
        print(f"  Amount: {d.amount_pkr} PKR = ${d.amount_usd} USD")
        print(f"  TX ID: {d.tx_id}")
        print(f"  Status: {d.status}")
        print(f"  Created: {d.created_at}")
        print(f"  Processed: {d.processed_at}")
        print(f"  Is Signup Init: {'Yes' if d.tx_id == 'SIGNUP-INIT' else 'No'}")
        print()

# Check credited deposits (excluding signup)
credited = DepositRequest.objects.filter(status='CREDITED').exclude(tx_id='SIGNUP-INIT')
print(f"✅ Credited Deposits (excluding SIGNUP-INIT): {credited.count()}")
print()

# Check wallets
wallets = Wallet.objects.all()
print(f"💰 Total Wallets: {wallets.count()}")
print()

if wallets.exists():
    print("Wallet Details:")
    print("-" * 70)
    for w in wallets:
        print(f"User: {w.user.username} (ID: {w.user.id})")
        print(f"  Available USD: ${w.available_usd}")
        print(f"  Hold USD: ${w.hold_usd}")
        print(f"  Income USD: ${w.income_usd}")
        print(f"  Current Income USD: ${w.get_current_income_usd()}")
        print(f"  Transactions: {w.transactions.count()}")
        print()

# Check users
users = User.objects.filter(is_approved=True)
print(f"👥 Approved Users: {users.count()}")
for u in users:
    print(f"  - {u.username} (ID: {u.id}, Approved: {u.is_approved}, Active: {u.is_active})")

print()
print("="*70)
print("RECOMMENDATION:")
print("="*70)

if credited.count() == 0:
    print("⚠️  No credited deposits found (excluding SIGNUP-INIT)")
    print()
    print("To generate passive earnings, you need to:")
    print("1. Have users make deposit requests")
    print("2. Admin approves and credits the deposits")
    print("3. Then run: python manage.py backfill_from_start")
    print()
    print("OR for testing:")
    print("1. Manually create a credited deposit in admin")
    print("2. Run: python manage.py backfill_from_start")
else:
    print("✅ You have credited deposits!")
    print("Run: python manage.py backfill_from_start")

print("="*70)