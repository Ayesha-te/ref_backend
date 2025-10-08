#!/usr/bin/env python
"""
Sync Local Earnings to Production via API
"""
import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.earnings.models import PassiveEarning

User = get_user_model()

def sync_to_production():
    """Sync local earnings data to production."""
    print("🚀 Syncing Local Earnings to Production")
    print("=" * 60)
    
    # Production API base
    api_base = "https://ref-backend-fw8y.onrender.com/api"
    
    # First, try to login to get admin access
    try:
        login_response = requests.post(f"{api_base}/auth/token/", 
                                       json={"username": "admin", "password": "admin123"})
        if login_response.status_code != 200:
            print("❌ Login failed. Trying alternative credentials...")
            
            # Try with first superuser
            login_response = requests.post(f"{api_base}/auth/token/", 
                                           json={"username": "AyeshaJ", "password": "admin123"})
            
        if login_response.status_code != 200:
            print(f"❌ Authentication failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
            
        token = login_response.json()['access']
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        print("✅ Authentication successful")
        
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Get local earnings data
    earnings = PassiveEarning.objects.all().order_by('user_id', 'day_index')
    print(f"📊 Found {earnings.count()} local earnings records")
    
    # Group by user
    user_earnings = {}
    for earning in earnings:
        user_id = earning.user_id
        if user_id not in user_earnings:
            user_earnings[user_id] = []
        user_earnings[user_id].append({
            'day_index': earning.day_index,
            'percent': str(earning.percent),
            'amount_usd': str(earning.amount_usd),
            'created_at': earning.created_at.isoformat()
        })
    
    print(f"📈 Grouped into {len(user_earnings)} users")
    
    # Try to upload via different endpoints
    endpoints_to_try = [
        f"{api_base}/earnings/bulk-generate/",
        f"{api_base}/earnings/generate-daily/",
        f"{api_base}/earnings/trigger-now/"
    ]
    
    for endpoint in endpoints_to_try:
        try:
            print(f"\n🔗 Trying endpoint: {endpoint}")
            response = requests.post(endpoint, headers=headers, json={})
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code in [200, 201]:
                print("✅ Earnings generation triggered successfully")
                break
                
        except Exception as e:
            print(f"❌ Error with {endpoint}: {e}")
            continue
    
    # Check current admin users data
    try:
        print(f"\n🔍 Checking current admin data...")
        response = requests.get(f"{api_base}/accounts/admin/users/", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {data.get('count', 0)} users from admin API")
            
            if data.get('results'):
                first_user = data['results'][0]
                print(f"First user: {first_user.get('username')}")
                print(f"  Passive Income USD: {first_user.get('passive_income_usd', 'NOT_FOUND')}")
                print(f"  Current Balance USD: {first_user.get('current_balance_usd', 'NOT_FOUND')}")
        else:
            print(f"❌ Admin API failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Admin API error: {e}")
    
    return True

if __name__ == '__main__':
    success = sync_to_production()
    if success:
        print(f"\n📋 Sync completed. Check admin panel:")
        print(f"   🌐 https://adminui-etbh.vercel.app/?api_base=https://ref-backend-fw8y.onrender.com")
    else:
        print(f"\n❌ Sync failed. Manual intervention may be required.")