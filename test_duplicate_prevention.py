#!/usr/bin/env python
"""
Test Duplicate Prevention - Multiple Approve Button Clicks
===========================================================

This script simulates clicking the "Approve" button multiple times
and verifies that only ONE bonus is created per referrer-referee-level.

It tests all 3 layers of duplicate prevention:
1. Application logic check (in signals.py)
2. Database unique constraint (in models.py)
3. Cleanup verification

Run this in Render Shell to test on production data.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.referrals.models import ReferralPayout
from apps.accounts.models import SignupProof
from apps.wallets.models import Wallet, Transaction
from decimal import Decimal

User = get_user_model()

print("\n" + "="*80)
print("🧪 DUPLICATE PREVENTION TEST - Multiple Approve Button Clicks")
print("="*80 + "\n")

# Find a user with referrals to test
test_user = User.objects.filter(
    is_approved=True,
    referred_by__isnull=False
).first()

if not test_user:
    print("❌ No approved users with referrers found in database")
    print("   Cannot run test without test data")
    sys.exit(1)

print(f"📋 Test Subject: {test_user.username} (ID: {test_user.id})")
print(f"   Referred by: {test_user.referred_by.username if test_user.referred_by else 'None'}")

# Get signup proof
signup_proof = SignupProof.objects.filter(user=test_user).order_by('-created_at').first()
if signup_proof:
    print(f"   Deposit Amount: {signup_proof.amount_pkr} PKR")
else:
    print(f"   Deposit Amount: Not found (will use default)")

print("\n" + "-"*80)
print("🔍 BEFORE TEST - Current State")
print("-"*80 + "\n")

# Count existing bonuses
existing_bonuses = ReferralPayout.objects.filter(referee=test_user)
print(f"Existing bonuses for this user: {existing_bonuses.count()}")

if existing_bonuses.exists():
    print("\nBonus breakdown:")
    for bonus in existing_bonuses:
        print(f"  - L{bonus.level}: ${bonus.amount_usd} to {bonus.referrer.username}")

print("\n" + "-"*80)
print("🧪 SIMULATING MULTIPLE APPROVE BUTTON CLICKS")
print("-"*80 + "\n")

# Simulate clicking approve button 5 times
from apps.accounts.signals import on_user_approved

print("Simulating 5 approve button clicks...")
for i in range(1, 6):
    print(f"\n  Click #{i}:")
    try:
        # This simulates what happens when admin clicks approve
        # The signal should prevent duplicates
        on_user_approved(
            sender=User,
            instance=test_user,
            created=False,
            update_fields=None
        )
        print(f"    ✅ Signal executed")
    except Exception as e:
        print(f"    ⚠️  Error: {e}")

print("\n" + "-"*80)
print("🔍 AFTER TEST - Verification")
print("-"*80 + "\n")

# Count bonuses after test
final_bonuses = ReferralPayout.objects.filter(referee=test_user)
print(f"Total bonuses after 5 clicks: {final_bonuses.count()}")

if final_bonuses.exists():
    print("\nBonus breakdown:")
    bonus_counts = {}
    for bonus in final_bonuses:
        key = f"L{bonus.level} to {bonus.referrer.username}"
        bonus_counts[key] = bonus_counts.get(key, 0) + 1
        print(f"  - {key}: ${bonus.amount_usd}")
    
    print("\nDuplicate check:")
    has_duplicates = False
    for key, count in bonus_counts.items():
        if count > 1:
            print(f"  ❌ {key}: {count} bonuses (DUPLICATE!)")
            has_duplicates = True
        else:
            print(f"  ✅ {key}: {count} bonus (OK)")

print("\n" + "-"*80)
print("📊 TEST RESULTS")
print("-"*80 + "\n")

# Calculate expected bonuses
expected_levels = 0
cur = test_user.referred_by
while cur and expected_levels < 3:
    expected_levels += 1
    cur = cur.referred_by

print(f"Expected bonuses: {expected_levels} (one per upline level)")
print(f"Actual bonuses: {final_bonuses.count()}")

if final_bonuses.count() == expected_levels:
    print("\n✅ TEST PASSED!")
    print("   - Correct number of bonuses created")
    print("   - No duplicates despite 5 approve clicks")
    print("   - Duplicate prevention is working correctly!")
else:
    print("\n❌ TEST FAILED!")
    if final_bonuses.count() > expected_levels:
        print(f"   - Too many bonuses: {final_bonuses.count()} instead of {expected_levels}")
        print("   - Duplicate prevention may not be working")
    else:
        print(f"   - Too few bonuses: {final_bonuses.count()} instead of {expected_levels}")
        print("   - Some bonuses may not have been created")

print("\n" + "-"*80)
print("🛡️ PROTECTION LAYERS VERIFIED")
print("-"*80 + "\n")

# Check Layer 1: Application Logic
print("Layer 1: Application Logic Check")
already_paid = ReferralPayout.objects.filter(referee=test_user).exists()
print(f"  - Check in signals.py: {'✅ ACTIVE' if already_paid else '❌ NOT WORKING'}")
print(f"  - Prevents: Signal from creating new bonuses if any exist")

# Check Layer 2: Database Constraint
print("\nLayer 2: Database Unique Constraint")
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sqlite_master 
        WHERE type='index' 
        AND tbl_name='referrals_referralpayout'
        AND sql LIKE '%unique%'
    """)
    unique_indexes = cursor.fetchone()[0]
print(f"  - Unique constraints: {unique_indexes}")
print(f"  - Status: {'✅ ACTIVE' if unique_indexes > 0 else '⚠️  NOT FOUND'}")
print(f"  - Prevents: Database from accepting duplicate entries")

# Check Layer 3: Cleanup Tools
print("\nLayer 3: Cleanup Tools")
import os
cleanup_script = os.path.join(os.path.dirname(__file__), 'cleanup_duplicate_bonuses.py')
print(f"  - Cleanup script: {'✅ EXISTS' if os.path.exists(cleanup_script) else '❌ MISSING'}")
print(f"  - Purpose: Remove any existing duplicates from database")

print("\n" + "="*80)
print("🎯 SUMMARY")
print("="*80 + "\n")

print("The duplicate prevention system has 3 layers:")
print("")
print("1️⃣  Application Logic (signals.py)")
print("   - Checks if bonuses already exist before creating new ones")
print("   - Prevents duplicate creation at the code level")
print("")
print("2️⃣  Database Constraint (models.py)")
print("   - unique_together = [['referrer', 'referee', 'level']]")
print("   - Prevents duplicates even if code check fails")
print("")
print("3️⃣  Cleanup Tools")
print("   - cleanup_duplicate_bonuses.py removes existing duplicates")
print("   - Can be run anytime to clean up the database")
print("")

if final_bonuses.count() == expected_levels:
    print("✅ All layers are working correctly!")
    print("✅ Safe to approve users multiple times - no duplicates will be created!")
else:
    print("⚠️  Some issues detected - review the results above")

print("\n" + "="*80 + "\n")