#!/usr/bin/env python
"""
Check Referral Relationships
=============================

This script checks all referral relationships in the database.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.accounts.models import User

print("\n" + "="*80)
print("🔍 CHECKING REFERRAL RELATIONSHIPS")
print("="*80 + "\n")

all_users = User.objects.all().order_by('date_joined')

print(f"Total users: {all_users.count()}\n")

users_with_referrer = []
users_without_referrer = []

for user in all_users:
    print(f"📧 {user.email} (Username: {user.username})")
    print(f"   - Referral Code: {user.referral_code}")
    print(f"   - Approved: {user.is_approved}")
    print(f"   - Referred By: {user.referred_by.email if user.referred_by else 'None (Root User)'}")
    
    if user.referred_by:
        users_with_referrer.append(user)
    else:
        users_without_referrer.append(user)
    
    print()

print("="*80)
print(f"\n📊 SUMMARY:")
print(f"   - Users with referrer: {len(users_with_referrer)}")
print(f"   - Users without referrer (root users): {len(users_without_referrer)}")

print(f"\n🌳 REFERRAL TREE:")
print("="*80 + "\n")

# Build referral tree
for root_user in users_without_referrer:
    print(f"🌟 {root_user.email} (Code: {root_user.referral_code})")
    
    # Get direct referrals
    direct_referrals = User.objects.filter(referred_by=root_user)
    
    if direct_referrals.exists():
        for ref in direct_referrals:
            print(f"   └─ L1: {ref.email} (Code: {ref.referral_code}, Approved: {ref.is_approved})")
            
            # Get L2 referrals
            l2_referrals = User.objects.filter(referred_by=ref)
            if l2_referrals.exists():
                for l2 in l2_referrals:
                    print(f"      └─ L2: {l2.email} (Code: {l2.referral_code}, Approved: {l2.is_approved})")
                    
                    # Get L3 referrals
                    l3_referrals = User.objects.filter(referred_by=l2)
                    if l3_referrals.exists():
                        for l3 in l3_referrals:
                            print(f"         └─ L3: {l3.email} (Code: {l3.referral_code}, Approved: {l3.is_approved})")
    else:
        print(f"   (No referrals)")
    
    print()

print("="*80 + "\n")