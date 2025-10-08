from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models
from apps.earnings.models import PassiveEarning
from apps.wallets.models import Transaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Sync PassiveEarning records with actual transaction records to fix admin UI display'

    def handle(self, *args, **options):
        User = get_user_model()
        
        self.stdout.write('🔄 Syncing PassiveEarning records with actual transactions...')
        
        # Clear all existing PassiveEarning records (they might be dummy data)
        deleted_count = PassiveEarning.objects.all().count()
        PassiveEarning.objects.all().delete()
        self.stdout.write(f'🗑️  Deleted {deleted_count} existing PassiveEarning records')
        
        # Recreate PassiveEarning records based on actual passive income transactions
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            # Get all passive income transactions for this user
            passive_transactions = Transaction.objects.filter(
                wallet__user=user,
                type=Transaction.CREDIT,
                meta__type='passive'
            ).order_by('created_at')
            
            if not passive_transactions.exists():
                continue
                
            self.stdout.write(f'👤 Processing {user.username}...')
            
            for transaction in passive_transactions:
                day_index = transaction.meta.get('day_index', 1)
                percent_str = transaction.meta.get('percent', '0.004')
                
                try:
                    percent = Decimal(str(percent_str))
                except:
                    percent = Decimal('0.004')  # Default 0.4%
                
                # Create PassiveEarning record that matches the transaction
                earning, created = PassiveEarning.objects.get_or_create(
                    user=user,
                    day_index=day_index,
                    defaults={
                        'percent': percent,
                        'amount_usd': transaction.amount_usd,
                        'created_at': transaction.created_at
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✅ Day {day_index}: ${transaction.amount_usd} ({percent*100}%)')
            
            # Calculate total for verification
            total = user.passive_earnings.aggregate(
                total=models.Sum('amount_usd')
            )['total'] or Decimal('0')
            
            self.stdout.write(f'  📊 Total for {user.username}: ${total}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Successfully synced! Created {created_count} PassiveEarning records based on actual transactions.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                '🎯 Admin UI and user dashboard should now show matching passive income values.'
            )
        )