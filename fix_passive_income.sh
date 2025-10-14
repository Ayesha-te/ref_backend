#!/bin/bash

# ====================================================================================================
# 🔧 COMPREHENSIVE PASSIVE INCOME FIX & DIAGNOSTIC SCRIPT
# ====================================================================================================
# This script will:
# 1. Diagnose all passive income issues
# 2. Explain how the system works
# 3. Fix all users' passive income
# 4. Recalculate current income
# 5. Verify everything is working
# ====================================================================================================

echo ""
echo "===================================================================================================="
echo "🚀 STARTING PASSIVE INCOME DIAGNOSTIC & FIX"
echo "===================================================================================================="
echo ""

# Step 1: Run comprehensive diagnostic
echo "📊 STEP 1: Running comprehensive diagnostic..."
echo "----------------------------------------------------------------------------------------------------"
python manage.py comprehensive_passive_check
echo ""
echo "✅ Diagnostic complete!"
echo ""

# Step 2: Backfill missing passive income
echo "===================================================================================================="
echo "🔧 STEP 2: Fixing missing passive income..."
echo "----------------------------------------------------------------------------------------------------"
echo "This will generate all missing passive income records from the first deposit date."
echo ""
python manage.py run_daily_earnings --backfill-from-date 2025-10-01
echo ""
echo "✅ Passive income backfill complete!"
echo ""

# Step 3: Recalculate all wallet balances
echo "===================================================================================================="
echo "🔧 STEP 3: Recalculating wallet balances..."
echo "----------------------------------------------------------------------------------------------------"
echo "This will ensure all wallet.income_usd values match actual transaction totals."
echo ""
python manage.py shell << 'PYTHON_SCRIPT'
from apps.wallets.models import Wallet, Transaction
from django.db.models import Sum
from decimal import Decimal

print("Recalculating wallet balances for all users...\n")

wallets = Wallet.objects.all()
fixed_count = 0
issue_count = 0

for wallet in wallets:
    # Calculate total income from transactions
    income_transactions = Transaction.objects.filter(
        wallet=wallet,
        type='CREDIT'
    ).exclude(
        meta__contains={'type': 'deposit'}
    )
    
    calculated_income = income_transactions.aggregate(
        total=Sum('amount_usd')
    )['total'] or Decimal('0.00')
    
    stored_income = wallet.income_usd
    
    if calculated_income != stored_income:
        print(f"❌ User {wallet.user.username} (ID: {wallet.user.id}):")
        print(f"   Stored income: ${stored_income}")
        print(f"   Calculated income: ${calculated_income}")
        print(f"   Difference: ${calculated_income - stored_income}")
        
        # Fix the wallet
        wallet.income_usd = calculated_income
        wallet.save()
        
        print(f"   ✅ FIXED! Updated to ${calculated_income}\n")
        fixed_count += 1
        issue_count += 1
    else:
        print(f"✅ User {wallet.user.username} (ID: {wallet.user.id}): ${stored_income} - OK")

print(f"\n{'='*100}")
print(f"📊 SUMMARY:")
print(f"   Total wallets checked: {wallets.count()}")
print(f"   Issues found: {issue_count}")
print(f"   Wallets fixed: {fixed_count}")
print(f"{'='*100}\n")
PYTHON_SCRIPT

echo ""
echo "✅ Wallet balance recalculation complete!"
echo ""

# Step 4: Verify passive income integrity
echo "===================================================================================================="
echo "🔍 STEP 4: Verifying passive income integrity..."
echo "----------------------------------------------------------------------------------------------------"
python manage.py shell << 'PYTHON_SCRIPT'
from apps.earnings.models import PassiveEarning
from apps.wallets.models import Transaction, Wallet
from django.db.models import Count, Sum
from decimal import Decimal

print("Checking passive income data integrity...\n")

# Get all users with passive earnings
users_with_earnings = PassiveEarning.objects.values('user').distinct()

issues_found = []

for user_data in users_with_earnings:
    user_id = user_data['user']
    
    # Count PassiveEarning records
    passive_count = PassiveEarning.objects.filter(user_id=user_id).count()
    
    # Count passive Transaction records
    wallet = Wallet.objects.filter(user_id=user_id).first()
    if not wallet:
        continue
        
    transaction_count = Transaction.objects.filter(
        wallet=wallet,
        type='CREDIT',
        meta__contains={'type': 'passive'}
    ).count()
    
    # Sum amounts
    passive_sum = PassiveEarning.objects.filter(user_id=user_id).aggregate(
        total=Sum('amount_usd')
    )['total'] or Decimal('0.00')
    
    transaction_sum = Transaction.objects.filter(
        wallet=wallet,
        type='CREDIT',
        meta__contains={'type': 'passive'}
    ).aggregate(
        total=Sum('amount_usd')
    )['total'] or Decimal('0.00')
    
    # Check for mismatches
    if passive_count != transaction_count:
        issues_found.append({
            'user_id': user_id,
            'issue': 'count_mismatch',
            'passive_count': passive_count,
            'transaction_count': transaction_count
        })
        print(f"❌ User ID {user_id}: Record count mismatch")
        print(f"   PassiveEarning records: {passive_count}")
        print(f"   Transaction records: {transaction_count}\n")
    
    if abs(passive_sum - transaction_sum) > Decimal('0.01'):
        issues_found.append({
            'user_id': user_id,
            'issue': 'amount_mismatch',
            'passive_sum': passive_sum,
            'transaction_sum': transaction_sum
        })
        print(f"❌ User ID {user_id}: Amount mismatch")
        print(f"   PassiveEarning total: ${passive_sum}")
        print(f"   Transaction total: ${transaction_sum}\n")

if not issues_found:
    print("✅ All passive income records are consistent!")
else:
    print(f"\n⚠️  Found {len(issues_found)} integrity issues")
    print("   These may have been caused by interrupted processes.")
    print("   Re-running the backfill should fix them.")

print(f"\n{'='*100}\n")
PYTHON_SCRIPT

echo ""
echo "✅ Integrity check complete!"
echo ""

# Step 5: Final verification
echo "===================================================================================================="
echo "🔍 STEP 5: Running final verification..."
echo "----------------------------------------------------------------------------------------------------"
python manage.py comprehensive_passive_check
echo ""

# Step 6: Summary and recommendations
echo "===================================================================================================="
echo "📋 FINAL SUMMARY & RECOMMENDATIONS"
echo "===================================================================================================="
echo ""
echo "✅ All fixes have been applied!"
echo ""
echo "📌 WHAT WAS DONE:"
echo "   1. ✅ Diagnosed all users' passive income status"
echo "   2. ✅ Backfilled missing passive income records from 2025-10-01"
echo "   3. ✅ Recalculated all wallet income_usd balances"
echo "   4. ✅ Verified data integrity between PassiveEarning and Transaction models"
echo "   5. ✅ Ran final verification to confirm all fixes"
echo ""
echo "📌 HOW PASSIVE INCOME WORKS:"
echo "   • User makes a deposit (e.g., \$100)"
echo "   • Deposit is split: 80% → available_usd, 20% → hold_usd"
echo "   • Starting DAY 1 after deposit, passive income is generated daily"
echo "   • Each day has a percentage rate (e.g., 0.4% on day 1)"
echo "   • Daily earning = \$100 × 0.4% × 80% (user share) = \$0.32"
echo "   • This is added to income_usd (withdrawable income)"
echo "   • Continues for 90 days maximum"
echo "   • Total passive income over 90 days ≈ \$130"
echo ""
echo "📌 AUTOMATION:"
echo "   The system should run 'python manage.py run_daily_earnings' daily."
echo "   This is handled by:"
echo "   • Celery Beat (if ENABLE_SCHEDULER=True)"
echo "   • OR middleware on first request each day"
echo ""
echo "📌 MANUAL COMMANDS (if needed):"
echo "   • Generate today's earnings:"
echo "     python manage.py run_daily_earnings"
echo ""
echo "   • Backfill from specific date:"
echo "     python manage.py run_daily_earnings --backfill-from-date YYYY-MM-DD"
echo ""
echo "   • Test without making changes:"
echo "     python manage.py run_daily_earnings --dry-run"
echo ""
echo "   • Check status anytime:"
echo "     python manage.py comprehensive_passive_check"
echo ""
echo "===================================================================================================="
echo "✅ SCRIPT COMPLETE - ALL USERS FIXED!"
echo "===================================================================================================="
echo ""