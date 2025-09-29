from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import DepositRequest
from apps.earnings.models import PassiveEarning
from datetime import date

class Command(BaseCommand):
    help = 'Check the status of passive earnings for all users'

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.filter(is_approved=True)
        
        self.stdout.write("=== PASSIVE EARNINGS STATUS ===\n")
        
        total_users = 0
        users_with_deposits = 0
        users_with_earnings = 0
        
        for user in users:
            total_users += 1
            
            # Check if user has made first credited deposit
            first_dep = DepositRequest.objects.filter(
                user=user, 
                status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()
            
            if not first_dep:
                self.stdout.write(f"❌ {user.username}: No credited deposits (excluding signup)")
                continue
            
            users_with_deposits += 1
            
            # Check passive earnings
            last_earning = PassiveEarning.objects.filter(user=user).order_by('-day_index').first()
            
            if not last_earning:
                days_since_deposit = (date.today() - first_dep.processed_at.date()).days
                self.stdout.write(
                    f"⚠️  {user.username}: Has deposit ({first_dep.amount_usd} USD on {first_dep.processed_at.date()}) "
                    f"but NO passive earnings yet! ({days_since_deposit} days ago)"
                )
                continue
            
            users_with_earnings += 1
            days_since_deposit = (date.today() - first_dep.processed_at.date()).days
            expected_days = min(days_since_deposit, 90)  # Cap at 90 for standard plan
            
            if last_earning.day_index < expected_days:
                missing_days = expected_days - last_earning.day_index
                self.stdout.write(
                    f"⚠️  {user.username}: Behind by {missing_days} days "
                    f"(current: day {last_earning.day_index}, expected: day {expected_days})"
                )
            else:
                self.stdout.write(
                    f"✅ {user.username}: Up to date (day {last_earning.day_index})"
                )
        
        self.stdout.write(f"\n=== SUMMARY ===")
        self.stdout.write(f"Total approved users: {total_users}")
        self.stdout.write(f"Users with credited deposits: {users_with_deposits}")
        self.stdout.write(f"Users with passive earnings: {users_with_earnings}")
        self.stdout.write(f"Users missing earnings: {users_with_deposits - users_with_earnings}")
        
        if users_with_deposits > users_with_earnings:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  {users_with_deposits - users_with_earnings} users have deposits but no passive earnings!"
                )
            )
            self.stdout.write("Run 'python manage.py backfill_daily_earnings' to fix this.")