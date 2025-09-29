from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
import json

class Command(BaseCommand):
    help = 'Test passive earnings data for admin panel'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Test the exact same query as the admin API
        users = User.objects.filter(username='Ahmad').annotate(
            rewards_usd=Coalesce(Sum('passive_earnings__amount_usd'), Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))),
            passive_income_usd=Coalesce(Sum('passive_earnings__amount_usd'), Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))),
        )
        
        for user in users:
            self.stdout.write(f"User: {user.username}")
            self.stdout.write(f"ID: {user.id}")
            self.stdout.write(f"Rewards USD: {user.rewards_usd}")
            self.stdout.write(f"Passive Income USD: {user.passive_income_usd}")
            
            # Check wallet balance
            try:
                wallet = user.wallet
                self.stdout.write(f"Available USD: {wallet.available_usd}")
                self.stdout.write(f"Hold USD: {wallet.hold_usd}")
            except:
                self.stdout.write("No wallet found")
                
            # Check passive earnings directly
            earnings_count = user.passive_earnings.count()
            total_earnings = user.passive_earnings.aggregate(total=Sum('amount_usd'))['total'] or 0
            self.stdout.write(f"Direct earnings count: {earnings_count}")
            self.stdout.write(f"Direct total earnings: {total_earnings}")
            
            # Show recent earnings
            recent = user.passive_earnings.order_by('-day_index')[:5]
            for pe in recent:
                self.stdout.write(f"  Day {pe.day_index}: ${pe.amount_usd} ({pe.percent})")