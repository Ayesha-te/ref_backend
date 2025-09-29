from django.contrib.auth import get_user_model
from apps.earnings.models import PassiveEarning
from decimal import Decimal
import random

User = get_user_model()

# Get all users
users = User.objects.all()
print(f"Found {users.count()} users")

for user in users:
    print(f"Generating earnings for {user.username}...")
    
    # Create 15 days of progressive earnings for each user
    for day in range(1, 16):
        # Calculate progressive earnings (0.4% to 0.7%)
        base_amount = Decimal("100.00")  # Assume $100 base
        percent = Decimal("0.004") + (Decimal("0.0002") * day)  # 0.4% + progressive
        amount = base_amount * percent
        
        # Add some randomness
        amount = amount + (Decimal(str(random.uniform(-0.1, 0.1))))
        
        earning, created = PassiveEarning.objects.get_or_create(
            user=user,
            day_index=day,
            defaults={
                'percent': percent,
                'amount_usd': amount
            }
        )
        
        if created:
            print(f"  Day {day}: ${amount} ({percent*100}%)")
    
    # Check total
    total = user.passive_earnings.aggregate(total=models.Sum('amount_usd'))['total'] or Decimal('0')
    print(f"  Total for {user.username}: ${total}")
    print()
