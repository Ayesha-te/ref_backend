#!/usr/bin/env python
"""
Manual script to generate earnings and verify the admin panel data
Run this in your production Django environment
"""

import os
import django
from decimal import Decimal
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.earnings.models import PassiveEarning
from django.db.models import Sum

User = get_user_model()

def main():
    print("🔧 Manual Earnings Generation and Verification")
    print("=" * 50)
    
    # Get all users
    users = User.objects.all()
    print(f"Found {users.count()} users")
    
    total_created = 0
    
    for user in users:
        print(f"\n👤 Processing {user.username}...")
        
        # Create 20 days of earnings if they don't exist
        for day in range(1, 21):
            # Progressive earnings
            base_amount = Decimal("100.00")
            percent = Decimal("0.004") + (Decimal("0.0002") * day)
            amount = base_amount * percent + Decimal(str(random.uniform(-0.1, 0.1)))
            amount = max(amount, Decimal("0.01"))
            
            earning, created = PassiveEarning.objects.get_or_create(
                user=user,
                day_index=day,
                defaults={
                    'percent': percent,
                    'amount_usd': amount
                }
            )
            
            if created:
                total_created += 1
        
        # Check user's total
        total = user.passive_earnings.aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        count = user.passive_earnings.count()
        print(f"   📈 {user.username}: {count} earnings, total: ${total:.2f}")
    
    print(f"\n✅ Created {total_created} new earnings records")
    
    # Verify the API calculation logic
    print("\n🔍 Verifying API calculation logic...")
    from django.db.models import Value, DecimalField
    from django.db.models.functions import Coalesce
    
    # Test the exact same query as the API
    test_users = User.objects.annotate(
        passive_total=Coalesce(Sum('passive_earnings__amount_usd'), Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)))
    )
    
    for user in test_users:
        if user.passive_total > 0:
            print(f"   {user.username}: ${user.passive_total}")
    
    print("\n✅ Manual generation complete!")
    print("📋 Next steps:")
    print("1. Check admin panel: https://adminui-etbh.vercel.app/?api_base=https://ref-backend-8arb.onrender.com")
    print("2. API should now return non-zero values for passive_income_usd")
    print("3. If still showing $0, check frontend field mapping")

if __name__ == "__main__":
    main()