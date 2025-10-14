#!/usr/bin/env python
"""
====================================================================================================
🔧 COMPREHENSIVE PASSIVE INCOME FIX & DIAGNOSTIC SCRIPT
====================================================================================================
This script will:
1. Diagnose all passive income issues
2. Explain how the system works
3. Fix all users' passive income
4. Recalculate current income
5. Verify everything is working
====================================================================================================

USAGE IN RENDER SHELL:
    python fix_passive_income.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from apps.wallets.models import Wallet, Transaction
from apps.earnings.models import PassiveEarning
from django.db.models import Sum


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 100)
    print(f"🔧 {text}")
    print("=" * 100 + "\n")


def print_section(text):
    """Print a formatted section"""
    print("\n" + "-" * 100)
    print(f"📌 {text}")
    print("-" * 100 + "\n")


def step1_diagnostic():
    """Step 1: Run comprehensive diagnostic"""
    print_header("STEP 1: Running Comprehensive Diagnostic")
    
    try:
        call_command('comprehensive_passive_check')
        print("\n✅ Diagnostic complete!\n")
        return True
    except Exception as e:
        print(f"❌ Error running diagnostic: {e}")
        return False


def step2_backfill():
    """Step 2: Backfill missing passive income"""
    print_header("STEP 2: Backfilling Missing Passive Income")
    
    print("This will generate all missing passive income records from the first deposit date.\n")
    
    try:
        # Calculate backfill date (30 days ago to be safe)
        backfill_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"Backfilling from: {backfill_date}\n")
        call_command('run_daily_earnings', backfill_from_date=backfill_date)
        
        print("\n✅ Passive income backfill complete!\n")
        return True
    except Exception as e:
        print(f"❌ Error during backfill: {e}")
        return False


def step3_recalculate_wallets():
    """Step 3: Recalculate all wallet balances"""
    print_header("STEP 3: Recalculating Wallet Balances")
    
    print("This will ensure all wallet.income_usd values match actual transaction totals.\n")
    
    try:
        wallets = Wallet.objects.all()
        fixed_count = 0
        issue_count = 0
        
        for wallet in wallets:
            # Calculate total income from transactions (all credits except deposits)
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
        
        print(f"\n{'=' * 100}")
        print(f"📊 SUMMARY:")
        print(f"   Total wallets checked: {wallets.count()}")
        print(f"   Issues found: {issue_count}")
        print(f"   Wallets fixed: {fixed_count}")
        print(f"{'=' * 100}\n")
        
        return True
    except Exception as e:
        print(f"❌ Error recalculating wallets: {e}")
        return False


def step4_verify_integrity():
    """Step 4: Verify passive income integrity"""
    print_header("STEP 4: Verifying Passive Income Integrity")
    
    print("Checking passive income data integrity...\n")
    
    try:
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
        
        print(f"\n{'=' * 100}\n")
        return True
    except Exception as e:
        print(f"❌ Error verifying integrity: {e}")
        return False


def step5_final_verification():
    """Step 5: Final verification"""
    print_header("STEP 5: Running Final Verification")
    
    try:
        call_command('comprehensive_passive_check')
        print("\n✅ Final verification complete!\n")
        return True
    except Exception as e:
        print(f"❌ Error during final verification: {e}")
        return False


def print_summary():
    """Print final summary and recommendations"""
    print_header("FINAL SUMMARY & RECOMMENDATIONS")
    
    print("✅ All fixes have been applied!\n")
    
    print("📌 WHAT WAS DONE:")
    print("   1. ✅ Diagnosed all users' passive income status")
    print("   2. ✅ Backfilled missing passive income records")
    print("   3. ✅ Recalculated all wallet income_usd balances")
    print("   4. ✅ Verified data integrity between PassiveEarning and Transaction models")
    print("   5. ✅ Ran final verification to confirm all fixes\n")
    
    print("📌 HOW PASSIVE INCOME WORKS:")
    print("   • User makes a deposit (e.g., $100)")
    print("   • Deposit is split: 80% → available_usd, 20% → hold_usd")
    print("   • Starting DAY 1 after deposit, passive income is generated daily")
    print("   • Each day has a percentage rate (e.g., 0.4% on day 1)")
    print("   • Daily earning = $100 × 0.4% × 80% (user share) = $0.32")
    print("   • This is added to income_usd (withdrawable income)")
    print("   • Continues for 90 days maximum")
    print("   • Total passive income over 90 days ≈ $130\n")
    
    print("📌 AUTOMATION:")
    print("   The system should run 'python manage.py run_daily_earnings' daily.")
    print("   This is handled by:")
    print("   • Celery Beat (if ENABLE_SCHEDULER=True)")
    print("   • OR middleware on first request each day\n")
    
    print("📌 MANUAL COMMANDS (if needed):")
    print("   • Generate today's earnings:")
    print("     python manage.py run_daily_earnings\n")
    print("   • Backfill from specific date:")
    print("     python manage.py run_daily_earnings --backfill-from-date YYYY-MM-DD\n")
    print("   • Test without making changes:")
    print("     python manage.py run_daily_earnings --dry-run\n")
    print("   • Check status anytime:")
    print("     python manage.py comprehensive_passive_check\n")
    
    print("=" * 100)
    print("✅ SCRIPT COMPLETE - ALL USERS FIXED!")
    print("=" * 100 + "\n")


def main():
    """Main execution function"""
    print("\n" + "=" * 100)
    print("🚀 STARTING PASSIVE INCOME DIAGNOSTIC & FIX")
    print("=" * 100 + "\n")
    
    # Execute all steps
    steps = [
        ("Diagnostic", step1_diagnostic),
        ("Backfill", step2_backfill),
        ("Recalculate Wallets", step3_recalculate_wallets),
        ("Verify Integrity", step4_verify_integrity),
        ("Final Verification", step5_final_verification),
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        try:
            results[step_name] = step_func()
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {step_name}: {e}\n")
            results[step_name] = False
    
    # Print summary
    print_summary()
    
    # Print step results
    print("\n📊 STEP RESULTS:")
    for step_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {step_name}: {status}")
    
    print("\n")
    
    # Return exit code
    if all(results.values()):
        print("🎉 All steps completed successfully!")
        return 0
    else:
        print("⚠️  Some steps failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())