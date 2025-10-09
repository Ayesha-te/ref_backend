#!/usr/bin/env python
"""
List All Users
==============
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("\n" + "="*80)
print("👥 ALL USERS IN DATABASE")
print("="*80 + "\n")

users = User.objects.all().order_by('-date_joined')
print(f"Total users: {users.count()}\n")

for i, user in enumerate(users, 1):
    print(f"{i}. {user.email}")
    print(f"   - Username: {user.username}")
    print(f"   - Approved: {user.is_approved}")
    print(f"   - Joined: {user.date_joined}")
    print(f"   - Referral Code: {user.referral_code}")
    if user.referred_by:
        print(f"   - Referred by: {user.referred_by.email}")
    print()

print("="*80 + "\n")