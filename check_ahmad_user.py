#!/usr/bin/env python
"""
Check Ahmad User Authentication
================================
This script verifies the Ahmad admin user exists and can authenticate.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password

User = get_user_model()

print("\n" + "="*70)
print("🔍 AHMAD USER AUTHENTICATION CHECK")
print("="*70 + "\n")

# Check if Ahmad user exists
try:
    ahmad = User.objects.get(username='Ahmad')
    print("✅ Ahmad user found!")
    print(f"   - ID: {ahmad.id}")
    print(f"   - Username: {ahmad.username}")
    print(f"   - Email: {ahmad.email}")
    print(f"   - is_active: {ahmad.is_active}")
    print(f"   - is_staff: {ahmad.is_staff}")
    print(f"   - is_superuser: {ahmad.is_superuser}")
    print(f"   - is_approved: {getattr(ahmad, 'is_approved', 'N/A')}")
    print(f"   - Date joined: {ahmad.date_joined}")
    print(f"   - Last login: {ahmad.last_login}")
    
    # Check password
    print("\n🔑 Password Check:")
    password_correct = check_password('12345', ahmad.password)
    print(f"   - Password '12345' is {'✅ CORRECT' if password_correct else '❌ INCORRECT'}")
    print(f"   - Password hash: {ahmad.password[:50]}...")
    
    # Try authentication
    print("\n🔐 Authentication Test:")
    auth_user = authenticate(username='Ahmad', password='12345')
    if auth_user:
        print("   ✅ Authentication SUCCESSFUL")
        print(f"   - Authenticated user ID: {auth_user.id}")
    else:
        print("   ❌ Authentication FAILED")
        print("   - This means Django's authenticate() returned None")
        print("   - Possible reasons:")
        print("     1. Password is incorrect")
        print("     2. User is not active (is_active=False)")
        print("     3. Custom authentication backend issue")
    
    # Check if user can get JWT token
    print("\n🎫 JWT Token Generation Test:")
    from rest_framework_simplejwt.tokens import RefreshToken
    try:
        refresh = RefreshToken.for_user(ahmad)
        access = str(refresh.access_token)
        print("   ✅ JWT tokens generated successfully")
        print(f"   - Access token (first 50 chars): {access[:50]}...")
        print(f"   - Refresh token (first 50 chars): {str(refresh)[:50]}...")
    except Exception as e:
        print(f"   ❌ JWT token generation failed: {e}")

except User.DoesNotExist:
    print("❌ Ahmad user NOT FOUND!")
    print("\n📝 Creating Ahmad user...")
    try:
        ahmad = User.objects.create_user(
            username='Ahmad',
            email='ahmad@admin.com',
            password='12345',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        # Set is_approved if the field exists
        if hasattr(ahmad, 'is_approved'):
            ahmad.is_approved = True
            ahmad.save()
        print("✅ Ahmad user created successfully!")
        print(f"   - Username: Ahmad")
        print(f"   - Password: 12345")
        print(f"   - is_staff: True")
        print(f"   - is_superuser: True")
    except Exception as e:
        print(f"❌ Failed to create Ahmad user: {e}")

print("\n" + "="*70)

# List all admin users
print("\n📋 All Admin Users:")
admins = User.objects.filter(is_staff=True)
if admins.exists():
    for admin in admins:
        print(f"   - {admin.username} (ID: {admin.id}, Email: {admin.email})")
else:
    print("   No admin users found")

print("\n" + "="*70 + "\n")