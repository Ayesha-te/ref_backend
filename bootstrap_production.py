#!/usr/bin/env python
"""
Production Earnings Bootstrap - Create earnings data for all users
"""
import os
import django
import random
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.earnings.models import PassiveEarning

User = get_user_model()

def bootstrap_production_earnings():
    """Bootstrap earnings for all users in production."""
    print("🚀 Production Earnings Bootstrap")
    print("=" * 50)
    
    # Check environment
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    print(f"🔧 Debug mode: {debug_mode}")
    print(f"🔧 Production mode: {not debug_mode}")
    
    # Get all users
    users = User.objects.all()
    total_users = users.count()
    print(f"👥 Found {total_users} users")
    
    if total_users == 0:
        print("❌ No users found. Creating sample users first...")
        
        # Create sample admin user
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_superuser=True,
            is_staff=True
        )
        setattr(admin_user, 'is_approved', True)
        admin_user.save()
        print(f"✅ Created admin user: {admin_user.username}")
        
        # Create sample regular users
        sample_users = [
            ('AyeshaJ', 'ayesha@example.com'),
            ('testuser1', 'test1@example.com'),
            ('testuser2', 'test2@example.com'),
        ]
        
        for username, email in sample_users:
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                is_active=True
            )
            setattr(user, 'is_approved', True)
            user.save()
            print(f"✅ Created user: {username}")
        
        # Refresh users query
        users = User.objects.all()
        total_users = users.count()
        print(f"👥 Now have {total_users} users")
    
    # Generate earnings for all users
    total_earnings_created = 0
    
    for user in users:
        print(f"\n👤 Processing {user.username}...")
        
        # Generate 20 days of earnings
        user_earnings_created = 0
        
        for day in range(1, 21):
            # Check if earnings already exist
            if PassiveEarning.objects.filter(user=user, day_index=day).exists():
                continue
            
            # Progressive rate calculation (0.4% to 0.8%)
            base_rate = 0.004  # 0.4%
            if day <= 10:
                rate = base_rate + (day - 1) * 0.0001  # 0.4% to 0.5%
            else:
                rate = base_rate + 0.001 + (day - 11) * 0.0002  # 0.5% to 0.8%
            
            # Random base amount between $80-$120
            base_amount = Decimal(str(random.uniform(80, 120)))
            
            # Calculate earnings
            amount_usd = base_amount * Decimal(str(rate))
            
            # Create earnings record
            earning = PassiveEarning.objects.create(
                user=user,
                day_index=day,
                percent=Decimal(str(rate)),
                amount_usd=amount_usd
            )
            
            user_earnings_created += 1
            total_earnings_created += 1
        
        if user_earnings_created > 0:
            print(f"   ✅ Created {user_earnings_created} earnings records")
            
            # Calculate user total
            user_total = PassiveEarning.objects.filter(user=user).aggregate(
                total=django.db.models.Sum('amount_usd')
            )['total'] or 0
            print(f"   💰 Total earnings: ${user_total:.2f}")
    
    print(f"\n🎉 Bootstrap Complete!")
    print(f"   📊 Created {total_earnings_created} earnings records")
    print(f"   👥 For {total_users} users")
    
    # Verify the data
    print(f"\n🔍 Verification:")
    total_earnings = PassiveEarning.objects.count()
    total_amount = PassiveEarning.objects.aggregate(
        total=django.db.models.Sum('amount_usd')
    )['total'] or 0
    
    print(f"   📈 Total earnings records: {total_earnings}")
    print(f"   💵 Total amount: ${total_amount:.2f}")
    
    return total_earnings_created

if __name__ == '__main__':
    import django.db.models
    created = bootstrap_production_earnings()
    print(f"\n📋 Production earnings data ready!")
    print(f"   🌐 Admin Panel: https://adminui-etbh.vercel.app/?api_base=https://ref-backend-8arb.onrender.com")
    print(f"   🔑 Use admin/admin123 or any created user credentials")