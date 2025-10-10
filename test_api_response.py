#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.wallets.serializers import WalletSerializer
from apps.wallets.models import Wallet
from django.contrib.auth import get_user_model

User = get_user_model()

# Get first user with a wallet
user = User.objects.filter(wallet__isnull=False).first()

if user:
    wallet = user.wallet
    print(f"Testing API response for user: {user.username}\n")
    
    # Serialize wallet (this is what the API returns)
    try:
        serializer = WalletSerializer(wallet)
        data = serializer.data
        
        print("API Response Data:")
        print(f"  available_usd: ${data.get('available_usd', 'N/A')}")
        print(f"  hold_usd: ${data.get('hold_usd', 'N/A')}")
        print(f"  income_usd: ${data.get('income_usd', 'N/A')}")
        
        # Check if serializer includes calculated fields
        if 'current_income_usd' in data:
            print(f"  current_income_usd: ${data['current_income_usd']}")
        if 'passive_earnings_usd' in data:
            print(f"  passive_earnings_usd: ${data['passive_earnings_usd']}")
            
        print(f"\n✅ This is what the frontend receives from /api/wallets/me/")
        
    except Exception as e:
        print(f"❌ Error serializing wallet: {e}")
        print(f"   This might be the SQLite compatibility issue with meta__contains")
        print(f"\n💡 Solution: The frontend will calculate from transactions instead")
        
else:
    print("No users with wallets found")