#!/usr/bin/env python
"""
Test PostgreSQL JSONB Query Approaches
======================================

This script tests different ways to query JSONB fields in PostgreSQL
to find the correct approach for filtering transactions by meta.type.
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check if DATABASE_URL is set, if not, prompt user
if 'DATABASE_URL' not in os.environ:
    print("\n⚠️  DATABASE_URL environment variable not set!")
    print("This script needs to connect to the PostgreSQL production database.")
    print("\nPlease set DATABASE_URL before running this script:")
    print('  $env:DATABASE_URL="postgresql://..."; python test_jsonb_query.py')
    print("\nOr run with inline environment variable:")
    print('  python test_jsonb_query.py')
    print("\nExiting...")
    sys.exit(1)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models import Q, Sum
from apps.wallets.models import Wallet, Transaction
from django.db import connection

print("\n" + "="*80)
print("🔍 TESTING POSTGRESQL JSONB QUERY APPROACHES")
print("="*80 + "\n")

# Get the user
email = "sardarlaeiq3@gmail.com"
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(email=email)
    wallet = user.wallet
    
    print(f"✅ Found user: {email}")
    print(f"   Wallet ID: {wallet.id}")
    print(f"   Stored income_usd: ${wallet.income_usd}")
    print()
    
    # Get all transactions for inspection
    all_txns = wallet.transactions.all()
    print(f"📊 Total transactions: {all_txns.count()}")
    print()
    
    # Show sample meta field structure
    print("📋 Sample meta field structures:")
    for txn in all_txns[:3]:
        print(f"   Transaction {txn.id}: {txn.type} ${txn.amount_usd}")
        print(f"   meta = {txn.meta}")
        print(f"   meta type = {type(txn.meta)}")
        if 'type' in txn.meta:
            print(f"   meta['type'] = {txn.meta['type']} (type: {type(txn.meta['type'])})")
        print()
    
    print("\n" + "="*80)
    print("🧪 TESTING DIFFERENT QUERY APPROACHES")
    print("="*80 + "\n")
    
    # Approach 1: Using Q with meta__type (current approach)
    print("1️⃣  Approach 1: Q(meta__type='referral')")
    try:
        result1 = wallet.transactions.filter(
            type=Transaction.CREDIT,
            meta__type='referral'
        )
        print(f"   Result count: {result1.count()}")
        print(f"   SQL: {result1.query}")
        for txn in result1:
            print(f"   - Transaction {txn.id}: ${txn.amount_usd} | meta={txn.meta}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Approach 2: Using contains
    print("2️⃣  Approach 2: meta__contains={'type': 'referral'}")
    try:
        result2 = wallet.transactions.filter(
            type=Transaction.CREDIT,
            meta__contains={'type': 'referral'}
        )
        print(f"   Result count: {result2.count()}")
        print(f"   SQL: {result2.query}")
        for txn in result2:
            print(f"   - Transaction {txn.id}: ${txn.amount_usd} | meta={txn.meta}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Approach 3: Using has_key and then filter in Python
    print("3️⃣  Approach 3: meta__has_key='type' + Python filter")
    try:
        result3 = wallet.transactions.filter(
            type=Transaction.CREDIT,
            meta__has_key='type'
        )
        print(f"   Result count (has 'type' key): {result3.count()}")
        referral_txns = [txn for txn in result3 if txn.meta.get('type') == 'referral']
        print(f"   Referral count (after Python filter): {len(referral_txns)}")
        for txn in referral_txns:
            print(f"   - Transaction {txn.id}: ${txn.amount_usd} | meta={txn.meta}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Approach 4: Raw SQL
    print("4️⃣  Approach 4: Raw SQL with JSONB operators")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, type, amount_usd, meta
                FROM wallets_transaction
                WHERE wallet_id = %s
                AND type = 'CREDIT'
                AND meta->>'type' = 'referral'
                ORDER BY created_at DESC
            """, [wallet.id])
            
            rows = cursor.fetchall()
            print(f"   Result count: {len(rows)}")
            for row in rows:
                print(f"   - Transaction {row[0]}: {row[1]} ${row[2]} | meta={row[3]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Approach 5: Check actual database values
    print("5️⃣  Approach 5: Inspect actual database JSONB storage")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, type, amount_usd, 
                       meta,
                       meta->'type' as meta_type_json,
                       meta->>'type' as meta_type_text,
                       pg_typeof(meta->'type') as json_type
                FROM wallets_transaction
                WHERE wallet_id = %s
                AND type = 'CREDIT'
                LIMIT 5
            """, [wallet.id])
            
            rows = cursor.fetchall()
            print(f"   Inspecting {len(rows)} credit transactions:")
            for row in rows:
                print(f"   Transaction {row[0]}:")
                print(f"     - meta: {row[3]}")
                print(f"     - meta->'type' (JSONB): {row[4]}")
                print(f"     - meta->>'type' (text): {row[5]}")
                print(f"     - pg_typeof: {row[6]}")
                print()
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*80)
    print("💡 RECOMMENDATION")
    print("="*80 + "\n")
    
    # Test the working approach with full income calculation
    print("Testing full income calculation with working approach...")
    
    # Manual calculation using Python
    credits = Decimal('0')
    debits = Decimal('0')
    
    for txn in wallet.transactions.all():
        if txn.type == Transaction.CREDIT:
            meta_type = txn.meta.get('type', '')
            source = txn.meta.get('source', '')
            non_income = txn.meta.get('non_income', False)
            
            if meta_type in ['passive', 'referral', 'milestone', 'global_pool', 'referral_correction']:
                if source != 'signup-initial' and not non_income:
                    credits += txn.amount_usd
                    print(f"   ✅ Credit: ${txn.amount_usd} (type={meta_type})")
        
        elif txn.type == Transaction.DEBIT:
            meta_type = txn.meta.get('type', '')
            if meta_type in ['withdrawal', 'referral_reversal']:
                debits += txn.amount_usd
                print(f"   ❌ Debit: ${txn.amount_usd} (type={meta_type})")
    
    calculated = (credits - debits).quantize(Decimal('0.01'))
    print(f"\n   Total Credits: ${credits}")
    print(f"   Total Debits: ${debits}")
    print(f"   Calculated Income: ${calculated}")
    print(f"   Stored Income: ${wallet.income_usd}")
    print(f"   Match: {'✅ YES' if calculated == wallet.income_usd else '❌ NO'}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80 + "\n")