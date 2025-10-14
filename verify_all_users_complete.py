#!/usr/bin/env python
"""
Complete verification script to ensure:
1. Current income >= Passive income (passive should NEVER exceed current)
2. All income calculations are correct
3. Available balance matches expected values
"""
import os
import django

os.environ.setdefault('DJANGO_SECRET_KEY', 'dev-secret-key')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.models import User
from apps.wallets.models import Wallet, Transaction
from apps.earnings.models import PassiveEarning
from decimal import Decimal
from django.db.models import Q

print("=" * 100)
print("🔍 COMPLETE USER INCOME VERIFICATION")
print("=" * 100)

users = User.objects.filter(is_approved=True).order_by('id')
print(f"\nFound {users.count()} approved users\n")

critical_issues = []
all_results = []

for user in users:
    print("=" * 100)
    print(f"👤 USER: {user.username} (ID: {user.id})")
    print("=" * 100)
    
    try:
        wallet = user.wallet
    except:
        print("❌ NO WALLET FOUND - SKIPPING")
        continue
    
    # Get all transactions
    all_txns = Transaction.objects.filter(wallet=wallet).order_by('created_at')
    
    print(f"\n💰 WALLET STORED VALUES:")
    print(f"   Available USD: ${wallet.available_usd}")
    print(f"   Hold USD:      ${wallet.hold_usd}")
    print(f"   Income USD:    ${wallet.income_usd}")
    
    # Calculate using wallet method
    current_income_wallet = wallet.get_current_income_usd()
    
    # Get passive earnings from PassiveEarning model
    passive_earnings = PassiveEarning.objects.filter(user=user).order_by('day_index')
    total_passive_from_model = sum([pe.amount_usd for pe in passive_earnings])
    
    # Get transactions by type using JSONB contains
    passive_txns = all_txns.filter(meta__contains={'type': 'passive'}, type='CREDIT')
    referral_txns = all_txns.filter(meta__contains={'type': 'referral'}, type='CREDIT')
    milestone_txns = all_txns.filter(meta__contains={'type': 'milestone'}, type='CREDIT')
    global_pool_txns = all_txns.filter(meta__contains={'type': 'global_pool'}, type='CREDIT')
    
    # Get ALL debits (withdrawals)
    withdrawal_txns = all_txns.filter(type='DEBIT')
    
    total_passive = sum([t.amount_usd for t in passive_txns])
    total_referral = sum([t.amount_usd for t in referral_txns])
    total_milestone = sum([t.amount_usd for t in milestone_txns])
    total_global_pool = sum([t.amount_usd for t in global_pool_txns])
    total_withdrawals = sum([t.amount_usd for t in withdrawal_txns])
    
    print(f"\n📊 INCOME BREAKDOWN:")
    print(f"   Passive Income:    ${total_passive:>8.2f} ({passive_txns.count()} txns)")
    print(f"   Referral Income:   ${total_referral:>8.2f} ({referral_txns.count()} txns)")
    print(f"   Milestone Income:  ${total_milestone:>8.2f} ({milestone_txns.count()} txns)")
    print(f"   Global Pool:       ${total_global_pool:>8.2f} ({global_pool_txns.count()} txns)")
    print(f"   Withdrawals:      -${total_withdrawals:>8.2f} ({withdrawal_txns.count()} txns)")
    
    # Manual calculation
    manual_current_income = total_passive + total_referral + total_milestone + total_global_pool - total_withdrawals
    
    print(f"\n💵 CURRENT INCOME CALCULATIONS:")
    print(f"   Wallet Method:     ${current_income_wallet:>8.2f}")
    print(f"   Manual Calc:       ${manual_current_income:>8.2f}")
    print(f"   Stored income_usd: ${wallet.income_usd:>8.2f}")
    
    # CRITICAL CHECK: Passive should NEVER exceed current
    issues = []
    
    print(f"\n🔍 VALIDATION CHECKS:")
    
    # Check 1: CRITICAL - Passive income should NEVER exceed current income
    if total_passive > current_income_wallet:
        issue = f"🚨 CRITICAL: Passive (${total_passive}) > Current (${current_income_wallet})"
        issues.append(issue)
        critical_issues.append({
            'user': user.username,
            'passive': float(total_passive),
            'current': float(current_income_wallet),
            'difference': float(total_passive - current_income_wallet)
        })
        print(f"   ❌ {issue}")
    else:
        print(f"   ✅ Passive (${total_passive}) <= Current (${current_income_wallet})")
    
    # Check 2: Wallet method vs manual calculation
    if abs(current_income_wallet - manual_current_income) > Decimal('0.01'):
        issue = f"Wallet method (${current_income_wallet}) ≠ Manual (${manual_current_income})"
        issues.append(issue)
        print(f"   ❌ {issue}")
    else:
        print(f"   ✅ Wallet method matches manual calculation")
    
    # Check 3: PassiveEarning model vs Transaction totals
    if abs(total_passive_from_model - total_passive) > Decimal('0.01'):
        issue = f"PassiveEarning model (${total_passive_from_model}) ≠ Transactions (${total_passive})"
        issues.append(issue)
        print(f"   ❌ {issue}")
    else:
        print(f"   ✅ PassiveEarning model matches transactions")
    
    # Check 4: Available balance
    # Available should equal current income for users with only income (no deposits)
    # For users with deposits, available = deposit user share + income - withdrawals
    deposits = all_txns.filter(meta__contains={'type': 'deposit'}, type='CREDIT')
    total_deposits = sum([t.amount_usd for t in deposits])
    
    if total_deposits > 0:
        # User has deposits - available should be deposit amount (not income)
        expected_available = total_deposits
    else:
        # User has no deposits - available should equal current income
        expected_available = current_income_wallet
    
    if abs(wallet.available_usd - expected_available) > Decimal('0.01'):
        issue = f"Available (${wallet.available_usd}) ≠ Expected (${expected_available})"
        issues.append(issue)
        print(f"   ⚠️  {issue}")
    else:
        print(f"   ✅ Available balance is correct")
    
    # List ALL transactions for transparency
    if all_txns.count() > 0:
        print(f"\n📋 ALL TRANSACTIONS ({all_txns.count()} total):")
        for txn in all_txns:
            meta_type = txn.meta.get('type', 'unknown')
            meta_source = txn.meta.get('source', '')
            symbol = "+" if txn.type == 'CREDIT' else "-"
            print(f"   {txn.created_at.strftime('%Y-%m-%d')} | {txn.type:6} | {symbol}${txn.amount_usd:>7.2f} | {meta_type:15} | {meta_source}")
    
    # Summary
    if issues:
        print(f"\n❌ ISSUES FOUND: {len(issues)}")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print(f"\n✅ ALL CHECKS PASSED")
    
    all_results.append({
        'user': user.username,
        'current': float(current_income_wallet),
        'passive': float(total_passive),
        'referral': float(total_referral),
        'milestone': float(total_milestone),
        'global_pool': float(total_global_pool),
        'withdrawals': float(total_withdrawals),
        'issues': len(issues),
        'has_critical': total_passive > current_income_wallet
    })
    
    print()

# Final Summary
print("=" * 100)
print("📊 FINAL SUMMARY")
print("=" * 100)

print(f"\n{'User':<35} {'Current':>10} {'Passive':>10} {'Referral':>10} {'Status':>10}")
print("-" * 100)

users_ok = 0
users_with_issues = 0
users_critical = 0

for result in all_results:
    status = "✅ OK" if result['issues'] == 0 else f"❌ {result['issues']}"
    if result['has_critical']:
        status = "🚨 CRITICAL"
        users_critical += 1
    
    if result['issues'] == 0:
        users_ok += 1
    else:
        users_with_issues += 1
    
    print(f"{result['user']:<35} ${result['current']:>9.2f} ${result['passive']:>9.2f} ${result['referral']:>9.2f} {status:>10}")

print("-" * 100)

total_current = sum([r['current'] for r in all_results])
total_passive = sum([r['passive'] for r in all_results])
total_referral = sum([r['referral'] for r in all_results])

print(f"{'TOTALS':<35} ${total_current:>9.2f} ${total_passive:>9.2f} ${total_referral:>9.2f}")

print(f"\n📈 STATISTICS:")
print(f"   Total Users:           {len(all_results)}")
print(f"   Users OK:              {users_ok} ✅")
print(f"   Users with Issues:     {users_with_issues} ❌")
print(f"   Users CRITICAL:        {users_critical} 🚨")

if critical_issues:
    print(f"\n🚨 CRITICAL ISSUES (Passive > Current):")
    print("-" * 100)
    for issue in critical_issues:
        print(f"   User: {issue['user']}")
        print(f"   Passive:    ${issue['passive']:.2f}")
        print(f"   Current:    ${issue['current']:.2f}")
        print(f"   Difference: ${issue['difference']:.2f} (passive is higher by this amount)")
        print()
else:
    print(f"\n✅ NO CRITICAL ISSUES - All users have passive income <= current income")

print("=" * 100)
print("✅ VERIFICATION COMPLETE")
print("=" * 100)