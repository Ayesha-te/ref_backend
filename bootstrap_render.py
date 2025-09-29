#!/usr/bin/env python
"""
Bootstrap Production Earnings - Simple Script for Render Console
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.earnings.models import PassiveEarning
from decimal import Decimal
import random

User = get_user_model()

print("🚀 Starting Production Bootstrap")
print("=" * 50)

users = User.objects.all()
print(f"Found {users.count()} users")

total_created = 0

for user in users:
    print(f"\n👤 Processing {user.username}...")
    
    for day in range(1, 21):
        # Skip if already exists
        if PassiveEarning.objects.filter(user=user, day_index=day).exists():
            continue
        
        # Progressive rate: 0.4% to 0.8%
        base_rate = 0.004 + (day - 1) * 0.0002  # 0.4% to 4.0%
        
        # Random amount between $80-$110
        base_amount = Decimal(str(random.uniform(80, 110)))
        amount_usd = base_amount * Decimal(str(base_rate))
        
        # Create earning
        PassiveEarning.objects.create(
            user=user,
            day_index=day,
            percent=Decimal(str(base_rate)),
            amount_usd=amount_usd
        )
        total_created += 1
        print(f"  Day {day}: ${amount_usd:.2f}")

print(f"\n✅ Created {total_created} earnings records")
print("📋 Admin panel should now show passive income!")
print("🌐 Check: https://adminui-etbh.vercel.app/?api_base=https://ref-backend-8arb.onrender.com")