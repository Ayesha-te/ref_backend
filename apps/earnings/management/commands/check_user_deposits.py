from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import DepositRequest
from apps.earnings.models import PassiveEarning

class Command(BaseCommand):
    help = 'Check deposit status for all approved users'

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.filter(is_approved=True)
        
        self.stdout.write(self.style.SUCCESS("\n" + "="*80))
        self.stdout.write(self.style.SUCCESS("📊 USER DEPOSIT STATUS REPORT"))
        self.stdout.write(self.style.SUCCESS("="*80))
        
        for u in users:
            self.stdout.write(f"\n👤 User: {u.username} (ID: {u.id})")
            self.stdout.write(f"   Email: {u.email}")
            self.stdout.write(f"   Approved: {u.is_approved}")
            
            # Check all deposits
            all_deposits = DepositRequest.objects.filter(user=u).exclude(tx_id='SIGNUP-INIT')
            self.stdout.write(f"   Total Deposits (excluding signup): {all_deposits.count()}")
            
            for dep in all_deposits:
                self.stdout.write(f"      💰 {dep.amount_pkr} PKR (${dep.amount_usd}) - Status: {dep.status} - TX: {dep.tx_id}")
                self.stdout.write(f"         Created: {dep.created_at}, Processed: {dep.processed_at}")
            
            # Check CREDITED deposits specifically
            credited_deposits = DepositRequest.objects.filter(user=u, status='CREDITED').exclude(tx_id='SIGNUP-INIT')
            self.stdout.write(f"   ✅ CREDITED Deposits: {credited_deposits.count()}")
            
            # Check passive earnings
            earnings = PassiveEarning.objects.filter(user=u)
            self.stdout.write(f"   📈 Passive Earnings Records: {earnings.count()}")
            if earnings.exists():
                last_earning = earnings.order_by('-day_index').first()
                self.stdout.write(f"      Last earning: Day {last_earning.day_index}")
            
            self.stdout.write("-" * 80)
        
        self.stdout.write(self.style.SUCCESS("\n" + "="*80))
        self.stdout.write(self.style.SUCCESS("✅ REPORT COMPLETE"))
        self.stdout.write(self.style.SUCCESS("="*80))