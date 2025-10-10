#!/usr/bin/env python
"""
Test Production Backend Authentication
========================================
This script tests authentication against the production backend.
"""

import requests
import json

PRODUCTION_API = "https://ref-backend-fw8y.onrender.com/api"

print("\n" + "="*70)
print("🔍 PRODUCTION BACKEND AUTHENTICATION TEST")
print("="*70 + "\n")

print(f"🌐 Testing against: {PRODUCTION_API}")
print(f"👤 Username: Ahmad")
print(f"🔑 Password: 12345\n")

# Test 1: Check if API is reachable
print("📡 Test 1: API Reachability")
try:
    response = requests.get(f"{PRODUCTION_API}/", timeout=10)
    print(f"   ✅ API is reachable (Status: {response.status_code})")
except Exception as e:
    print(f"   ❌ API is not reachable: {e}")
    print("\n" + "="*70 + "\n")
    exit(1)

# Test 2: Try to login
print("\n🔐 Test 2: Login Attempt")
try:
    response = requests.post(
        f"{PRODUCTION_API}/auth/token/",
        headers={"Content-Type": "application/json"},
        json={"username": "Ahmad", "password": "12345"},
        timeout=10
    )
    
    print(f"   Response Status: {response.status_code}")
    print(f"   Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ LOGIN SUCCESSFUL!")
        print(f"   - Access Token: {data.get('access', 'N/A')[:50]}...")
        print(f"   - Refresh Token: {data.get('refresh', 'N/A')[:50]}...")
        
        # Test 3: Try to access admin endpoint with token
        print("\n🔒 Test 3: Admin Endpoint Access")
        access_token = data.get('access')
        admin_response = requests.get(
            f"{PRODUCTION_API}/accounts/admin/users/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        print(f"   Response Status: {admin_response.status_code}")
        if admin_response.status_code == 200:
            users = admin_response.json()
            print(f"   ✅ Admin endpoint accessible!")
            print(f"   - Total users: {len(users)}")
        else:
            print(f"   ❌ Admin endpoint failed: {admin_response.status_code}")
            print(f"   - Response: {admin_response.text[:200]}")
            
    elif response.status_code == 401:
        print("   ❌ LOGIN FAILED - Invalid credentials")
        print(f"   - Response: {response.text}")
        print("\n💡 Possible reasons:")
        print("   1. Ahmad user doesn't exist in production database")
        print("   2. Password is different in production")
        print("   3. User is not active or approved")
        
    elif response.status_code == 403:
        print("   ❌ LOGIN FAILED - Account not approved")
        print(f"   - Response: {response.text}")
        
    else:
        print(f"   ❌ LOGIN FAILED - Unexpected status: {response.status_code}")
        print(f"   - Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("   ❌ Request timed out")
except requests.exceptions.ConnectionError:
    print("   ❌ Connection error")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Try alternative usernames
print("\n🔍 Test 4: Trying Alternative Usernames")
alternative_usernames = ["ahmad", "Ahmad12", "AyeshaJ"]
for username in alternative_usernames:
    try:
        response = requests.post(
            f"{PRODUCTION_API}/auth/token/",
            headers={"Content-Type": "application/json"},
            json={"username": username, "password": "12345"},
            timeout=5
        )
        if response.status_code == 200:
            print(f"   ✅ {username} - LOGIN SUCCESSFUL!")
        elif response.status_code == 401:
            print(f"   ❌ {username} - Invalid credentials")
        elif response.status_code == 403:
            print(f"   ⚠️  {username} - Account not approved")
        else:
            print(f"   ❓ {username} - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ {username} - Error: {e}")

print("\n" + "="*70 + "\n")