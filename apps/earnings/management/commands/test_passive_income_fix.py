from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import DepositRequest
from apps.earnings.models import PassiveEarning

class Command(BaseCommand):
    help = 'Test passive income visibility fix'

    def handle(self, *args, **options):
        User = get_user_model()
        
        self.stdout.write("🔍 Testing Passive Income Visibility Fix")
        self.stdout.write("=" * 50)
        
        # Get all users
        all_users = User.objects.filter(is_approved=True)
        
        users_with_investments = []
        users_without_investments = []
        
        for user in all_users:
            # Check if user has actual investments (excluding signup initial)
            has_investment = DepositRequest.objects.filter(
                user=user, 
                status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').exists()
            
            has_passive_earnings = PassiveEarning.objects.filter(user=user).exists()
            
            if has_investment:
                users_with_investments.append({
                    'user': user,
                    'has_passive_earnings': has_passive_earnings
                })
            else:
                users_without_investments.append({
                    'user': user,
                    'has_passive_earnings': has_passive_earnings
                })
        
        self.stdout.write(f"📊 Summary:")
        self.stdout.write(f"   Total approved users: {len(all_users)}")
        self.stdout.write(f"   Users with investments: {len(users_with_investments)}")
        self.stdout.write(f"   Users without investments: {len(users_without_investments)}")
        
        self.stdout.write(f"\n✅ Users WITH investments (should have passive earnings):")
        for item in users_with_investments:
            status = "✅ HAS" if item['has_passive_earnings'] else "❌ MISSING"
            self.stdout.write(f"   {item['user'].username}: {status} passive earnings")
        
        self.stdout.write(f"\n❌ Users WITHOUT investments (should NOT have passive earnings):")
        issues_found = 0
        for item in users_without_investments:
            if item['has_passive_earnings']:
                issues_found += 1
                self.stdout.write(f"   🚨 {item['user'].username}: INCORRECTLY has passive earnings")
            else:
                self.stdout.write(f"   ✅ {item['user'].username}: Correctly has NO passive earnings")
        
        if issues_found == 0:
            self.stdout.write(f"\n🎉 SUCCESS: All users without investments correctly have NO passive earnings!")
        else:
            self.stdout.write(f"\n⚠️  WARNING: {issues_found} users without investments incorrectly have passive earnings")
            self.stdout.write("   This might be from old data. New passive earnings will only be generated for users with investments.")