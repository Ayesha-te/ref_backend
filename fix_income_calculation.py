#!/usr/bin/env python
"""
Fix Income Calculation - Apply the correct JSONB query approach
================================================================

This script will:
1. Test which JSONB query approach works
2. Show you the correct code to use
3. Optionally apply the fix automatically
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check if DATABASE_URL is set
if 'DATABASE_URL' not in os.environ:
    print("\n" + "="*80)
    print("⚠️  DATABASE_URL NOT SET")
    print("="*80)
    print("\nThis script needs to connect to the PostgreSQL production database.")
    print("\nTo run this script, use:")
    print('  $env:DATABASE_URL="postgresql://..."; python fix_income_calculation.py')
    print("\nExiting...")
    print("="*80 + "\n")
    sys.exit(1)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models import Sum, Q
from apps.wallets.models import Wallet, Transaction
from django.contrib.auth import get_user_model

print("\n" + "="*80)
print("🔧 INCOME CALCULATION FIX")
print("="*80 + "\n")

# Test user
email = "sardarlaeiq3@gmail.com"
User = get_user_model()

try:
    user = User.objects.get(email=email)
    wallet = user.wallet
    
    print(f"✅ Testing with user: {email}")
    print(f"   Wallet ID: {wallet.id}")
    print(f"   Stored income_usd: ${wallet.income_usd}")
    print()
    
    # Expected values based on manual calculation
    EXPECTED_INCOME = Decimal('1.76')
    
    print("="*80)
    print("🧪 TESTING DIFFERENT QUERY APPROACHES")
    print("="*80 + "\n")
    
    # Approach 1: Current implementation (meta__type)
    print("1️⃣  Testing: Q(meta__type='...')")
    try:
        credits1 = wallet.transactions.filter(
            type=Transaction.CREDIT
        ).filter(
            Q(meta__type='passive') | 
            Q(meta__type='referral') | 
            Q(meta__type='milestone') |
            Q(meta__type='global_pool') |
            Q(meta__type='referral_correction')
        ).exclude(
            meta__source='signup-initial'
        ).exclude(
            meta__non_income=True
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        debits1 = wallet.transactions.filter(
            type=Transaction.DEBIT
        ).filter(
            Q(meta__type='withdrawal') |
            Q(meta__type='referral_reversal')
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        result1 = (credits1 - debits1).quantize(Decimal('0.01'))
        match1 = result1 == EXPECTED_INCOME
        
        print(f"   Credits: ${credits1}")
        print(f"   Debits: ${debits1}")
        print(f"   Result: ${result1}")
        print(f"   Expected: ${EXPECTED_INCOME}")
        print(f"   Status: {'✅ WORKS' if match1 else '❌ FAILS'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        match1 = False
    print()
    
    # Approach 2: Using __contains
    print("2️⃣  Testing: Q(meta__contains={'type': '...'})")
    try:
        credits2 = wallet.transactions.filter(
            type=Transaction.CREDIT
        ).filter(
            Q(meta__contains={'type': 'passive'}) | 
            Q(meta__contains={'type': 'referral'}) | 
            Q(meta__contains={'type': 'milestone'}) |
            Q(meta__contains={'type': 'global_pool'}) |
            Q(meta__contains={'type': 'referral_correction'})
        ).exclude(
            meta__contains={'source': 'signup-initial'}
        ).exclude(
            meta__contains={'non_income': True}
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        debits2 = wallet.transactions.filter(
            type=Transaction.DEBIT
        ).filter(
            Q(meta__contains={'type': 'withdrawal'}) |
            Q(meta__contains={'type': 'referral_reversal'})
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        result2 = (credits2 - debits2).quantize(Decimal('0.01'))
        match2 = result2 == EXPECTED_INCOME
        
        print(f"   Credits: ${credits2}")
        print(f"   Debits: ${debits2}")
        print(f"   Result: ${result2}")
        print(f"   Expected: ${EXPECTED_INCOME}")
        print(f"   Status: {'✅ WORKS' if match2 else '❌ FAILS'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        match2 = False
    print()
    
    # Approach 3: Python-based filtering (always works but slower)
    print("3️⃣  Testing: Python-based filtering")
    try:
        credits3 = Decimal('0')
        debits3 = Decimal('0')
        
        for txn in wallet.transactions.all():
            meta_type = txn.meta.get('type', '')
            
            if txn.type == Transaction.CREDIT:
                if meta_type in ['passive', 'referral', 'milestone', 'global_pool', 'referral_correction']:
                    if txn.meta.get('source') != 'signup-initial' and not txn.meta.get('non_income', False):
                        credits3 += txn.amount_usd
            
            elif txn.type == Transaction.DEBIT:
                if meta_type in ['withdrawal', 'referral_reversal']:
                    debits3 += txn.amount_usd
        
        result3 = (credits3 - debits3).quantize(Decimal('0.01'))
        match3 = result3 == EXPECTED_INCOME
        
        print(f"   Credits: ${credits3}")
        print(f"   Debits: ${debits3}")
        print(f"   Result: ${result3}")
        print(f"   Expected: ${EXPECTED_INCOME}")
        print(f"   Status: {'✅ WORKS' if match3 else '❌ FAILS'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        match3 = False
    print()
    
    # Determine best approach
    print("="*80)
    print("📊 RESULTS SUMMARY")
    print("="*80 + "\n")
    
    if match1:
        print("✅ Approach 1 (meta__type) WORKS!")
        print("   The current code should work correctly.")
        print("   No changes needed to the query approach.")
    elif match2:
        print("✅ Approach 2 (meta__contains) WORKS!")
        print("   Need to update the code to use __contains instead of __type")
        print("\n📝 RECOMMENDED FIX:")
        print("   Replace Q(meta__type='...') with Q(meta__contains={'type': '...'})")
    elif match3:
        print("✅ Approach 3 (Python filtering) WORKS!")
        print("   Database queries are not working, need to use Python-based filtering")
        print("\n📝 RECOMMENDED FIX:")
        print("   Replace database aggregation with Python loop")
    else:
        print("❌ None of the approaches worked!")
        print("   This requires deeper investigation of the JSONB storage format")
    
    print("\n" + "="*80)
    print("🔍 NEXT STEPS")
    print("="*80 + "\n")
    
    if match1:
        print("The query logic is correct. The issue might be:")
        print("1. The admin panel is caching old values")
        print("2. The stored income_usd field needs to be recalculated")
        print("3. The method is not being called in the admin panel")
        print("\nCheck apps/wallets/admin.py to see which field is displayed.")
    elif match2:
        print("To apply the fix:")
        print("1. Update apps/wallets/models.py")
        print("2. Change all meta__type to meta__contains={'type': '...'}")
        print("3. Change meta__source to meta__contains={'source': '...'}")
        print("4. Change meta__non_income to meta__contains={'non_income': True}")
        print("5. Test again with this script")
        print("6. Deploy to production")
    elif match3:
        print("To apply the fix:")
        print("1. Update apps/wallets/models.py")
        print("2. Replace the database query with Python-based filtering")
        print("3. Test again with this script")
        print("4. Deploy to production")
        print("\n⚠️  Note: This approach is slower but more reliable")
    
    print("\n" + "="*80 + "\n")
    
except User.DoesNotExist:
    print(f"❌ User {email} not found in database")
    print("   Make sure DATABASE_URL points to the production database")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()