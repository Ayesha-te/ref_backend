from django.contrib.auth import get_user_model
from apps.earnings.models import PassiveEarning
from apps.wallets.models import DepositRequest
from decimal import Decimal
import random

User = get_user_model()

# Only get users who have made investments (excluding signup initial)
eligible_users = []
for u in User.objects.filter(is_approved=True):
    first_dep = DepositRequest.objects.filter(user=u, status='CREDITED').exclude(tx_id='SIGNUP-INIT').first()
    if first_dep:
        eligible_users.append(u)

users = eligible_users
print(f"Found {len(users)} eligible users (with investments)")

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
    from django.db import models
    total = user.passive_earnings.aggregate(total=models.Sum('amount_usd'))['total'] or Decimal('0')
    print(f"  Total for {user.username}: ${total}")
    print()
