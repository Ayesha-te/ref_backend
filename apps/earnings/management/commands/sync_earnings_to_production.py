from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models
from apps.earnings.models import PassiveEarning
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate sample passive earnings for all users'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=15, help='Number of days of earnings to generate')
        parser.add_argument('--reset', action='store_true', help='Delete existing earnings first')

    def handle(self, *args, **options):
        days = options['days']
        reset = options['reset']
        
        if reset:
            self.stdout.write('Deleting existing earnings...')
            PassiveEarning.objects.all().delete()
        
        users = User.objects.all()
        self.stdout.write(f'Generating {days} days of earnings for {users.count()} users...')
        
        total_created = 0
        
        for user in users:
            user_created = 0
            for day in range(1, days + 1):
                # Progressive earnings calculation
                base_amount = Decimal("100.00")  # Assume $100 base
                percent = Decimal("0.004") + (Decimal("0.0002") * day)  # 0.4% + progressive
                amount = base_amount * percent
                
                # Add some realistic variation
                variation = Decimal(str(random.uniform(-0.1, 0.1)))
                amount = amount + variation
                
                # Ensure minimum amount
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
                    user_created += 1
                    total_created += 1
            
            if user_created > 0:
                # Calculate total for user
                total = user.passive_earnings.aggregate(
                    total=models.Sum('amount_usd')
                )['total'] or Decimal('0')
                
                self.stdout.write(
                    f'  {user.username}: Created {user_created} earnings, total: ${total:.2f}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {total_created} earnings records')
        )