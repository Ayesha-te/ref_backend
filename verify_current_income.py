#!/usr/bin/env python
"""
Verification script to check that current income is properly calculated and displayed.
This script checks:
1. Wallet model's get_current_income_usd() includes all income types
2. Users with passive earnings have non-zero current income
3. Global pool transactions are included in calculations
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SECRET_KEY', 'test-key')
os.environ.setdefault('DJANGO_DEBUG', '1')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.models import User
from apps.wallets.models import Wallet, Transaction
from django.db.models import Q, Count, Sum
from decimal import Decimal


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def verify_income_calculation():
    """Verify that income calculation includes all types"""
    print_section("1. Verifying Income Calculation Logic")
    
    # Check if any global pool transactions exist
    global_pool_count = Transaction.objects.filter(meta__type='global_pool').count()
    print(f"✓ Global pool transactions in database: {global_pool_count}")
    
    # Check income types in database
    income_types = Transaction.objects.filter(
        type=Transaction.CREDIT
    ).exclude(
        meta__source='signup-initial'
    ).exclude(
        meta__non_income=True
    ).values('meta__type').annotate(
        count=Count('id'),
        total=Sum('amount_usd')
    ).order_by('-total')
    
    print("\n📊 Income Transactions by Type:")
    print(f"{'Type':<20} {'Count':<10} {'Total USD':<15}")
    print("-" * 45)
    for item in income_types:
        income_type = item['meta__type'] or 'Unknown'
        count = item['count']
        total = item['total'] or Decimal('0')
        print(f"{income_type:<20} {count:<10} ${total:>12.2f}")
    
    if not income_types:
        print("⚠️  No income transactions found in database")


def verify_users_with_income():
    """Check users who have income transactions"""
    print_section("2. Verifying Users with Income")
    
    # Get users with wallets
    users_with_wallets = User.objects.filter(wallet__isnull=False).select_related('wallet')
    
    print(f"\n📈 Total users with wallets: {users_with_wallets.count()}")
    
    # Check users with income transactions
    users_with_income = []
    users_with_zero_income = []
    
    for user in users_with_wallets[:20]:  # Check first 20 users
        wallet = user.wallet
        current_income = wallet.get_current_income_usd()
        
        # Get breakdown by type
        passive = wallet.transactions.filter(
            type=Transaction.CREDIT,
            meta__type='passive'
        ).exclude(
            meta__source='signup-initial'
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        referral = wallet.transactions.filter(
            type=Transaction.CREDIT,
            meta__type='referral'
        ).exclude(
            meta__source='signup-initial'
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        milestone = wallet.transactions.filter(
            type=Transaction.CREDIT,
            meta__type='milestone'
        ).exclude(
            meta__source='signup-initial'
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        global_pool = wallet.transactions.filter(
            type=Transaction.CREDIT,
            meta__type='global_pool'
        ).exclude(
            meta__source='signup-initial'
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        if current_income > 0:
            users_with_income.append({
                'username': user.username,
                'current_income': current_income,
                'passive': passive,
                'referral': referral,
                'milestone': milestone,
                'global_pool': global_pool,
            })
        else:
            users_with_zero_income.append(user.username)
    
    if users_with_income:
        print(f"\n✅ Users with Current Income: {len(users_with_income)}")
        print(f"\n{'Username':<20} {'Total':<12} {'Passive':<12} {'Referral':<12} {'Milestone':<12} {'Global Pool':<12}")
        print("-" * 92)
        for u in users_with_income[:10]:  # Show first 10
            print(f"{u['username']:<20} ${u['current_income']:>10.2f} ${u['passive']:>10.2f} ${u['referral']:>10.2f} ${u['milestone']:>10.2f} ${u['global_pool']:>10.2f}")
    else:
        print("\n⚠️  No users found with current income > 0")
    
    if users_with_zero_income:
        print(f"\n📊 Users with zero income: {len(users_with_zero_income)}")
        if len(users_with_zero_income) <= 5:
            print(f"   {', '.join(users_with_zero_income)}")


def verify_api_serializer():
    """Verify that wallet serializer includes current_income_usd"""
    print_section("3. Verifying API Serializer")
    
    from apps.wallets.serializers import WalletSerializer
    
    # Check if current_income_usd is in fields
    serializer_fields = WalletSerializer.Meta.fields
    
    print(f"\n📋 Wallet Serializer Fields: {serializer_fields}")
    
    if 'current_income_usd' in serializer_fields:
        print("✅ current_income_usd is exposed in API")
    else:
        print("❌ current_income_usd is NOT exposed in API")
    
    # Test serialization with a real wallet
    wallet = Wallet.objects.first()
    if wallet:
        serializer = WalletSerializer(wallet)
        data = serializer.data
        print(f"\n📦 Sample Wallet API Response:")
        for key, value in data.items():
            print(f"   {key}: {value}")
        
        if 'current_income_usd' in data:
            print("\n✅ current_income_usd is present in serialized data")
        else:
            print("\n❌ current_income_usd is MISSING from serialized data")
    else:
        print("\n⚠️  No wallets found to test serialization")


def verify_transaction_types():
    """Check what transaction types exist and their meta structure"""
    print_section("4. Verifying Transaction Types and Meta Structure")
    
    # Get sample transactions of each type
    sample_transactions = Transaction.objects.filter(
        type=Transaction.CREDIT
    ).exclude(
        meta__source='signup-initial'
    )[:20]
    
    print(f"\n📝 Sample Transactions (first 20):")
    print(f"{'ID':<8} {'Type':<10} {'Amount':<12} {'Meta Type':<15} {'Meta Source':<20}")
    print("-" * 75)
    
    for txn in sample_transactions:
        meta_type = txn.meta.get('type', 'N/A')
        meta_source = txn.meta.get('source', 'N/A')
        print(f"{txn.id:<8} {txn.type:<10} ${txn.amount_usd:>10.2f} {meta_type:<15} {meta_source:<20}")


def main():
    """Run all verification checks"""
    print("\n" + "=" * 80)
    print("  CURRENT INCOME VERIFICATION SCRIPT")
    print("  Checking that current income includes all income types")
    print("=" * 80)
    
    try:
        verify_income_calculation()
        verify_users_with_income()
        verify_api_serializer()
        verify_transaction_types()
        
        print_section("✅ VERIFICATION COMPLETE")
        print("\nAll checks completed. Review the output above for any issues.")
        print("\nNext Steps:")
        print("1. If users have passive earnings but current_income is 0, check transaction meta fields")
        print("2. If current_income_usd is missing from API, restart the Django server")
        print("3. If global pool transactions are 0, run: python manage.py distribute_global_pool")
        print("4. Test the frontend by visiting the user dashboard and admin UI")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())