"""
Check all users' passive income calculations and verify correctness
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Q
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from decimal import Decimal

User = get_user_model()

def check_user(user):
    """Check a single user's income calculations"""
    print("\n" + "="*80)
    print(f"👤 USER: {user.username} (ID: {user.id})")
    print(f"   Approved: {user.is_approved}")
    print("="*80)
    
    # Get wallet
    wallet, _ = Wallet.objects.get_or_create(user=user)
    
    # Get deposits
    deposits = DepositRequest.objects.filter(user=user, status='CREDITED').exclude(tx_id='SIGNUP-INIT')
    total_deposits = sum([d.amount_usd for d in deposits])
    
    print(f"\n💰 WALLET BALANCES:")
    print(f"   Available USD: ${wallet.available_usd} = ₨{float(wallet.available_usd) * 280:,.2f}")
    print(f"   Hold USD: ${wallet.hold_usd}")
    print(f"   Income USD: ${wallet.income_usd}")
    
    print(f"\n📥 DEPOSITS: {deposits.count()} deposits, Total: ${total_deposits}")
    for dep in deposits:
        print(f"   {dep.created_at.date()} - ${dep.amount_usd} ({dep.status})")
    
    # Get first credited deposit
    first_dep = deposits.order_by('processed_at', 'created_at').first()
    
    if first_dep:
        from django.utils import timezone
        deposit_date = first_dep.processed_at or first_dep.created_at
        days_since = (timezone.now() - deposit_date).days
        print(f"\n🎯 FIRST DEPOSIT: ${first_dep.amount_usd} on {deposit_date.date()} ({days_since} days ago)")
    
    # Get passive earnings
    passive_earnings = PassiveEarning.objects.filter(user=user).order_by('day_index')
    total_passive_from_model = sum([pe.amount_usd for pe in passive_earnings])
    
    print(f"\n📊 PASSIVE EARNINGS: {passive_earnings.count()} records, Total: ${total_passive_from_model}")
    if passive_earnings.count() > 0:
        print(f"   Days 1-5:")
        for pe in passive_earnings[:5]:
            print(f"      Day {pe.day_index}: ${pe.amount_usd} ({pe.percent}%)")
        if passive_earnings.count() > 5:
            print(f"   ... and {passive_earnings.count() - 5} more days")
    
    # Get transactions by type
    all_txns = Transaction.objects.filter(wallet=wallet)
    
    passive_txns = all_txns.filter(meta__contains={'type': 'passive'}, type='CREDIT')
    referral_txns = all_txns.filter(meta__contains={'type': 'referral'}, type='CREDIT')
    milestone_txns = all_txns.filter(meta__contains={'type': 'milestone'}, type='CREDIT')
    global_pool_txns = all_txns.filter(meta__contains={'type': 'global_pool'}, type='CREDIT')
    withdrawal_txns = all_txns.filter(type='DEBIT')
    
    total_passive = sum([t.amount_usd for t in passive_txns])
    total_referral = sum([t.amount_usd for t in referral_txns])
    total_milestone = sum([t.amount_usd for t in milestone_txns])
    total_global_pool = sum([t.amount_usd for t in global_pool_txns])
    total_withdrawals = sum([t.amount_usd for t in withdrawal_txns])
    
    print(f"\n💳 TRANSACTIONS BREAKDOWN:")
    print(f"   Passive Income:    ${total_passive:>10} = ₨{float(total_passive) * 280:>12,.2f} ({passive_txns.count()} txns)")
    print(f"   Referral Income:   ${total_referral:>10} = ₨{float(total_referral) * 280:>12,.2f} ({referral_txns.count()} txns)")
    print(f"   Milestone Income:  ${total_milestone:>10} = ₨{float(total_milestone) * 280:>12,.2f} ({milestone_txns.count()} txns)")
    print(f"   Global Pool:       ${total_global_pool:>10} = ₨{float(total_global_pool) * 280:>12,.2f} ({global_pool_txns.count()} txns)")
    print(f"   Withdrawals:      -${total_withdrawals:>10} = ₨{float(total_withdrawals) * 280:>12,.2f} ({withdrawal_txns.count()} txns)")
    
    # Calculate current income using wallet method
    current_income = wallet.get_current_income_usd()
    
    # Manual calculation
    manual_current_income = total_passive + total_referral + total_milestone + total_global_pool - total_withdrawals
    
    print(f"\n📊 INCOME SUMMARY:")
    print(f"   Current Income (wallet method): ${current_income} = ₨{float(current_income) * 280:,.2f}")
    print(f"   Current Income (manual calc):   ${manual_current_income} = ₨{float(manual_current_income) * 280:,.2f}")
    print(f"   Passive Income:                 ${total_passive} = ₨{float(total_passive) * 280:,.2f}")
    
    # Validation checks
    issues = []
    
    # Check 1: Passive income should not exceed current income
    if total_passive > current_income:
        issues.append(f"⚠️  Passive income (${total_passive}) > Current income (${current_income})")
    
    # Check 2: Wallet method vs manual calculation
    if abs(current_income - manual_current_income) > Decimal('0.01'):
        issues.append(f"⚠️  Wallet method (${current_income}) ≠ Manual calc (${manual_current_income})")
    
    # Check 3: PassiveEarning model vs Transaction totals
    if abs(total_passive_from_model - total_passive) > Decimal('0.01'):
        issues.append(f"⚠️  PassiveEarning model (${total_passive_from_model}) ≠ Transactions (${total_passive})")
    
    # Check 4: Verify 0.4% calculation for first deposit
    if first_dep and passive_earnings.exists():
        first_passive = passive_earnings.first()
        user_share = first_dep.amount_usd * Decimal('0.80')
        expected_0_4_percent = user_share * Decimal('0.004')
        
        if first_passive.day_index == 1 and abs(first_passive.amount_usd - expected_0_4_percent) > Decimal('0.01'):
            issues.append(f"⚠️  Day 1 earning (${first_passive.amount_usd}) ≠ Expected 0.4% (${expected_0_4_percent})")
    
    # Check 5: Available balance should match income - withdrawals
    expected_available = current_income
    if abs(wallet.available_usd - expected_available) > Decimal('0.01'):
        issues.append(f"⚠️  Available balance (${wallet.available_usd}) ≠ Expected (${expected_available})")
    
    # Display results
    if issues:
        print(f"\n❌ ISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"   {issue}")
    else:
        print(f"\n✅ ALL CHECKS PASSED - Income calculations are correct!")
    
    return {
        'user': user.username,
        'current_income': float(current_income),
        'passive_income': float(total_passive),
        'referral_income': float(total_referral),
        'milestone_income': float(total_milestone),
        'global_pool_income': float(total_global_pool),
        'withdrawals': float(total_withdrawals),
        'available_balance': float(wallet.available_usd),
        'issues': len(issues),
        'has_issues': len(issues) > 0
    }

def main():
    print("\n" + "🔍 CHECKING ALL USERS' INCOME CALCULATIONS ".center(80, "="))
    
    # Get all users
    users = User.objects.all().order_by('username')
    
    print(f"\nFound {users.count()} users")
    
    results = []
    
    for user in users:
        result = check_user(user)
        results.append(result)
    
    # Summary table
    print("\n\n" + "="*80)
    print("📊 SUMMARY TABLE".center(80))
    print("="*80)
    print(f"{'User':<30} {'Current':<12} {'Passive':<12} {'Referral':<12} {'Issues':<10}")
    print("-"*80)
    
    for r in results:
        status = "❌" if r['has_issues'] else "✅"
        print(f"{r['user']:<30} ${r['current_income']:<11.2f} ${r['passive_income']:<11.2f} ${r['referral_income']:<11.2f} {status} {r['issues']}")
    
    print("="*80)
    
    # Overall statistics
    total_users = len(results)
    users_with_issues = sum([1 for r in results if r['has_issues']])
    users_ok = total_users - users_with_issues
    
    print(f"\n📈 OVERALL STATISTICS:")
    print(f"   Total Users: {total_users}")
    print(f"   Users OK: {users_ok} ✅")
    print(f"   Users with Issues: {users_with_issues} ❌")
    print(f"   Total Current Income: ${sum([r['current_income'] for r in results]):.2f}")
    print(f"   Total Passive Income: ${sum([r['passive_income'] for r in results]):.2f}")
    print(f"   Total Referral Income: ${sum([r['referral_income'] for r in results]):.2f}")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()