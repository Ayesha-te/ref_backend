from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, DepositRequest
from apps.earnings.models import PassiveEarning
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help = 'Check the status of passive earnings for all users'

    def handle(self, *args, **options):
        User = get_user_model()
        today = timezone.now().date()

        self.stdout.write(self.style.WARNING(f"=== Passive Earnings Status Report ==="))
        self.stdout.write(self.style.WARNING(f"Today's date: {today}\n"))

        users = User.objects.filter(is_approved=True)
        
        users_with_deposits = 0
        users_with_earnings = 0
        users_missing_earnings = 0
        users_with_future_earnings = 0
        total_future_earnings = 0

        self.stdout.write(self.style.WARNING("User Status:"))
        self.stdout.write("-" * 120)

        for u in users:
            # Get first credited deposit
            first_dep = DepositRequest.objects.filter(
                user=u, 
                status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()
            
            if not first_dep:
                self.stdout.write(f"❌ {u.username:20s} - No credited deposits")
                continue
            
            if not first_dep.processed_at:
                self.stdout.write(f"❌ {u.username:20s} - Deposit has no processed_at date")
                continue
            
            users_with_deposits += 1
            
            first_dep_date = first_dep.processed_at.date()
            days_since_first_deposit = (today - first_dep_date).days
            max_valid_day_index = days_since_first_deposit + 1
            
            # Get earnings info
            earnings = PassiveEarning.objects.filter(user=u)
            earnings_count = earnings.count()
            
            if earnings_count == 0:
                users_missing_earnings += 1
                self.stdout.write(
                    f"⚠️  {u.username:20s} - "
                    f"Deposit: {first_dep_date} ({days_since_first_deposit} days ago), "
                    f"Earnings: 0/{max_valid_day_index} ❌ MISSING ALL"
                )
                continue
            
            users_with_earnings += 1
            
            last_earning = earnings.order_by('-day_index').first()
            last_day = last_earning.day_index if last_earning else 0
            
            # Check for future earnings
            future_earnings = earnings.filter(day_index__gt=max_valid_day_index)
            future_count = future_earnings.count()
            
            if future_count > 0:
                users_with_future_earnings += 1
                total_future_earnings += future_count
                future_amount = sum(e.amount_usd for e in future_earnings)
                status = f"⚠️  FUTURE EARNINGS: {future_count} (${future_amount})"
            elif last_day < max_valid_day_index:
                missing = max_valid_day_index - last_day
                status = f"⚠️  MISSING: {missing} days"
            elif last_day == max_valid_day_index:
                status = "✅ UP TO DATE"
            else:
                status = "❓ UNKNOWN STATE"
            
            # Get wallet info
            wallet = Wallet.objects.filter(user=u).first()
            wallet_income = wallet.income_usd if wallet else Decimal('0')
            
            # Calculate expected income
            expected_income = sum(e.amount_usd for e in earnings.filter(day_index__lte=max_valid_day_index))
            
            income_match = "✅" if abs(wallet_income - expected_income) < Decimal('0.01') else "❌"
            
            self.stdout.write(
                f"{u.username:20s} - "
                f"Deposit: {first_dep_date} ({days_since_first_deposit:3d} days), "
                f"Earnings: {earnings_count:3d}/{max_valid_day_index:3d} (last: day {last_day:3d}), "
                f"Wallet: ${wallet_income:8.2f} {income_match}, "
                f"{status}"
            )

        # Summary
        self.stdout.write("\n" + "=" * 120)
        self.stdout.write(self.style.SUCCESS("\n=== Summary ==="))
        self.stdout.write(f"Total approved users: {users.count()}")
        self.stdout.write(f"Users with credited deposits: {users_with_deposits}")
        self.stdout.write(f"Users with earnings: {users_with_earnings}")
        self.stdout.write(f"Users missing ALL earnings: {users_missing_earnings}")
        self.stdout.write(f"Users with future earnings: {users_with_future_earnings}")
        self.stdout.write(f"Total future earnings records: {total_future_earnings}")
        
        if users_missing_earnings > 0 or users_with_future_earnings > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Issues found! Run these commands to fix:\n"
                    f"1. python manage.py fix_passive_earnings --dry-run  (to see what will be fixed)\n"
                    f"2. python manage.py fix_passive_earnings  (to apply fixes)\n"
                    f"3. python manage.py backfill_passive_earnings  (to add missing earnings)"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All users are up to date!"))