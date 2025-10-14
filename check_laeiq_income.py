"""
Check Laeiq's passive income calculation
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from decimal import Decimal

User = get_user_model()

# Find user Laeiq (check username contains 'laeiq')
from django.db.models import Q

user = User.objects.filter(
    Q(username__iexact='laeiq') | 
    Q(username__icontains='laeiq') |
    Q(email__icontains='laeiq')
).first()

if not user:
    print("❌ User 'Laeiq' not found")
    print("\nAvailable users:")
    for u in User.objects.all()[:10]:
        print(f"  - {u.username}")
    exit(1)

print(f"✅ Found user: {user.username} (ID: {user.id})")
print(f"   Approved: {user.is_approved}")
print()

# Get wallet
wallet, _ = Wallet.objects.get_or_create(user=user)
print("💰 WALLET BALANCES:")
print(f"   Available USD: ${wallet.available_usd}")
print(f"   Hold USD: ${wallet.hold_usd}")
print(f"   Income USD: ${wallet.income_usd}")
print()

# Get deposits
deposits = DepositRequest.objects.filter(user=user).order_by('created_at')
print(f"📥 DEPOSITS ({deposits.count()}):")
for dep in deposits:
    print(f"   {dep.created_at.date()} - ${dep.amount_usd} ({dep.status}) - TX: {dep.tx_id}")
print()

# Get first credited deposit (excluding signup)
first_dep = DepositRequest.objects.filter(
    user=user, 
    status='CREDITED'
).exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()

if first_dep:
    print(f"🎯 FIRST CREDITED DEPOSIT:")
    print(f"   Amount: ${first_dep.amount_usd}")
    print(f"   Date: {first_dep.processed_at or first_dep.created_at}")
    
    from django.utils import timezone
    deposit_date = first_dep.processed_at or first_dep.created_at
    days_since = (timezone.now() - deposit_date).days
    print(f"   Days since deposit: {days_since}")
    print()

# Get passive earnings
passive_earnings = PassiveEarning.objects.filter(user=user).order_by('day_index')
print(f"📊 PASSIVE EARNINGS RECORDS ({passive_earnings.count()}):")
total_passive_from_model = Decimal('0')
for pe in passive_earnings:
    print(f"   Day {pe.day_index}: ${pe.amount_usd} ({pe.percent}%)")
    total_passive_from_model += pe.amount_usd
print(f"   TOTAL from PassiveEarning model: ${total_passive_from_model}")
print()

# Get transactions
transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
print(f"💳 TRANSACTIONS ({transactions.count()}):")

passive_txns = []
other_income_txns = []
deposit_txns = []

for txn in transactions:
    meta_type = txn.meta.get('type', 'unknown')
    
    if meta_type == 'passive':
        passive_txns.append(txn)
    elif meta_type in ['referral', 'milestone', 'global_pool']:
        other_income_txns.append(txn)
    elif meta_type == 'deposit':
        deposit_txns.append(txn)

print(f"\n📈 PASSIVE INCOME TRANSACTIONS ({len(passive_txns)}):")
total_passive_from_txns = Decimal('0')
for txn in passive_txns[:10]:  # Show first 10
    print(f"   {txn.created_at.date()} - ${txn.amount_usd} - Day {txn.meta.get('day_index', '?')}")
    total_passive_from_txns += txn.amount_usd
if len(passive_txns) > 10:
    print(f"   ... and {len(passive_txns) - 10} more")
    for txn in passive_txns[10:]:
        total_passive_from_txns += txn.amount_usd
print(f"   TOTAL from passive transactions: ${total_passive_from_txns}")
print()

print(f"📊 OTHER INCOME TRANSACTIONS ({len(other_income_txns)}):")
total_other_income = Decimal('0')
for txn in other_income_txns:
    meta_type = txn.meta.get('type', 'unknown')
    print(f"   {txn.created_at.date()} - ${txn.amount_usd} - {meta_type}")
    total_other_income += txn.amount_usd
print(f"   TOTAL from other income: ${total_other_income}")
print()

print(f"💵 DEPOSIT TRANSACTIONS ({len(deposit_txns)}):")
for txn in deposit_txns:
    print(f"   {txn.created_at.date()} - ${txn.amount_usd}")
    print(f"      User share: ${txn.meta.get('user_share_usd', 'N/A')}")
    print(f"      Platform hold: ${txn.meta.get('platform_hold_usd', 'N/A')}")
    print(f"      Global pool: ${txn.meta.get('global_pool_usd', 'N/A')}")
print()

# Calculate current income using wallet method
current_income = wallet.get_current_income_usd()
print("="*60)
print("📊 INCOME SUMMARY:")
print("="*60)
print(f"Passive Income (from transactions): ${total_passive_from_txns} = ₨{float(total_passive_from_txns) * 280:,.2f}")
print(f"Other Income (referral/milestone/pool): ${total_other_income} = ₨{float(total_other_income) * 280:,.2f}")
print(f"Current Income (total): ${current_income} = ₨{float(current_income) * 280:,.2f}")
print(f"Available Balance: ${wallet.available_usd} = ₨{float(wallet.available_usd) * 280:,.2f}")
print("="*60)
print()

# Check if passive income is higher than current income
if total_passive_from_txns > current_income:
    print("⚠️  WARNING: Passive income is HIGHER than current income!")
    print(f"   This should not happen. Current income should include passive + other income.")
    print(f"   Difference: ${total_passive_from_txns - current_income}")
else:
    print("✅ Passive income is correctly less than or equal to current income")
print()

# Check the 0.4% calculation
if first_dep:
    expected_daily_0_4_percent = first_dep.amount_usd * Decimal('0.004')
    print(f"🔍 CHECKING 0.4% CALCULATION:")
    print(f"   First deposit amount: ${first_dep.amount_usd}")
    print(f"   Expected 0.4% daily: ${expected_daily_0_4_percent}")
    
    # Check first passive earning
    first_passive = PassiveEarning.objects.filter(user=user, day_index=1).first()
    if first_passive:
        print(f"   Actual day 1 earning: ${first_passive.amount_usd} ({first_passive.percent}%)")
        
        # The earning is based on 80% of deposit (user share)
        user_share = first_dep.amount_usd * Decimal('0.80')
        expected_from_user_share = user_share * Decimal('0.004')
        print(f"   User share (80% of deposit): ${user_share}")
        print(f"   Expected 0.4% of user share: ${expected_from_user_share}")
        
        if abs(first_passive.amount_usd - expected_from_user_share) < Decimal('0.01'):
            print(f"   ✅ Calculation is correct!")
        else:
            print(f"   ⚠️  Mismatch detected!")