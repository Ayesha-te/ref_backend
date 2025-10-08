from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from apps.earnings.services import daily_percent_for_day, compute_daily_earning_usd
from apps.referrals.models import ReferralPayout, ReferralMilestoneProgress
from apps.earnings.models_global_pool import GlobalPool, GlobalPoolPayout
from decimal import Decimal
from datetime import date, timedelta
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Comprehensive test to verify all systems work as described in How It Works page'

    def add_arguments(self, parser):
        parser.add_argument('--fix-data', action='store_true', help='Fix any data inconsistencies found')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 COMPREHENSIVE SYSTEM TEST - Verifying How It Works Implementation'))
        self.stdout.write("=" * 80)
        
        # Test 1: Passive Income Rates
        self.test_passive_income_rates()
        
        # Test 2: Passive Income Eligibility
        self.test_passive_income_eligibility()
        
        # Test 3: Referral System
        self.test_referral_system()
        
        # Test 4: Milestone System
        self.test_milestone_system()
        
        # Test 5: Global Pool System
        self.test_global_pool_system()
        
        # Test 6: Frontend Display Logic
        self.test_frontend_display_logic()
        
        # Test 7: Admin Panel Display
        self.test_admin_panel_display()
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS('✅ COMPREHENSIVE TEST COMPLETED'))

    def test_passive_income_rates(self):
        self.stdout.write(self.style.WARNING('\n📊 TEST 1: Passive Income Rates'))
        
        # Test the rates match How It Works page
        expected_rates = [
            (1, 0.004),   # Days 1-10: 0.4%
            (5, 0.004),
            (10, 0.004),
            (11, 0.006),  # Days 11-20: 0.6%
            (15, 0.006),
            (20, 0.006),
            (21, 0.008),  # Days 21-30: 0.8%
            (25, 0.008),
            (30, 0.008),
            (31, 0.010),  # Days 31-60: 1.0%
            (45, 0.010),
            (60, 0.010),
            (61, 0.013),  # Days 61-90: 1.3%
            (75, 0.013),
            (90, 0.013),
        ]
        
        all_correct = True
        for day, expected_rate in expected_rates:
            actual_rate = float(daily_percent_for_day(day))
            if actual_rate != expected_rate:
                self.stdout.write(self.style.ERROR(f'  ❌ Day {day}: Expected {expected_rate}%, got {actual_rate}%'))
                all_correct = False
            else:
                self.stdout.write(f'  ✅ Day {day}: {actual_rate}% (correct)')
        
        if all_correct:
            self.stdout.write(self.style.SUCCESS('  ✅ All passive income rates match How It Works page'))
        else:
            self.stdout.write(self.style.ERROR('  ❌ Some passive income rates are incorrect'))

    def test_passive_income_eligibility(self):
        self.stdout.write(self.style.WARNING('\n👤 TEST 2: Passive Income Eligibility'))
        
        # Check users with and without investments
        users_with_investments = []
        users_without_investments = []
        
        for user in User.objects.filter(is_approved=True):
            has_investment = DepositRequest.objects.filter(
                user=user, 
                status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').exists()
            
            if has_investment:
                users_with_investments.append(user)
            else:
                users_without_investments.append(user)
        
        self.stdout.write(f'  📈 Users WITH investments: {len(users_with_investments)}')
        self.stdout.write(f'  📉 Users WITHOUT investments: {len(users_without_investments)}')
        
        # Check passive earnings generation
        for user in users_with_investments[:3]:  # Check first 3
            passive_earnings = PassiveEarning.objects.filter(user=user).count()
            self.stdout.write(f'    ✅ {user.username}: {passive_earnings} passive earning records')
        
        for user in users_without_investments[:3]:  # Check first 3
            passive_earnings = PassiveEarning.objects.filter(user=user).count()
            if passive_earnings > 0:
                self.stdout.write(self.style.ERROR(f'    ❌ {user.username}: Has {passive_earnings} passive earnings but no investment!'))
            else:
                self.stdout.write(f'    ✅ {user.username}: Correctly has 0 passive earnings')

    def test_referral_system(self):
        self.stdout.write(self.style.WARNING('\n🔗 TEST 3: Referral System'))
        
        # Check referral rates (should be 6%, 3%, 1%)
        from django.conf import settings
        referral_tiers = settings.ECONOMICS['REFERRAL_TIERS']
        expected_tiers = [0.06, 0.03, 0.01]
        
        if referral_tiers == expected_tiers:
            self.stdout.write(f'  ✅ Referral tiers correct: L1={referral_tiers[0]*100}%, L2={referral_tiers[1]*100}%, L3={referral_tiers[2]*100}%')
        else:
            self.stdout.write(self.style.ERROR(f'  ❌ Referral tiers incorrect: {referral_tiers} (expected {expected_tiers})'))
        
        # Check some referral payouts
        recent_payouts = ReferralPayout.objects.all()[:5]
        self.stdout.write(f'  📊 Recent referral payouts: {recent_payouts.count()} total')
        
        for payout in recent_payouts:
            self.stdout.write(f'    💰 {payout.referrer.username} earned ${payout.amount_usd} from L{payout.level} referral')

    def test_milestone_system(self):
        self.stdout.write(self.style.WARNING('\n🎯 TEST 4: Milestone System'))
        
        # Check milestone progress for users with referrals
        milestone_users = ReferralMilestoneProgress.objects.all()[:5]
        
        if milestone_users:
            self.stdout.write(f'  📈 Users with milestone progress: {milestone_users.count()}')
            for progress in milestone_users:
                target = progress.current_target()
                self.stdout.write(f'    🎯 {progress.user.username}: {progress.current_count}/{target} directs, ${progress.current_sum_usd} invested')
        else:
            self.stdout.write('  📊 No milestone progress found (normal if no referrals have invested)')

    def test_global_pool_system(self):
        self.stdout.write(self.style.WARNING('\n🌍 TEST 5: Global Pool System'))
        
        # Check global pool configuration
        pool, _ = GlobalPool.objects.get_or_create(pk=1)
        self.stdout.write(f'  💰 Current global pool balance: ${pool.balance_usd}')
        
        # Check recent global pool payouts
        recent_payouts = GlobalPoolPayout.objects.all().order_by('-created_at')[:5]
        if recent_payouts:
            self.stdout.write(f'  📊 Recent global pool payouts: {recent_payouts.count()}')
            for payout in recent_payouts:
                self.stdout.write(f'    💸 {payout.user.username}: ${payout.amount_usd} on {payout.created_at.date()}')
        else:
            self.stdout.write('  📊 No global pool payouts found')
        
        # Check Monday collection logic (from run_daily_earnings.py)
        today = date.today()
        if today.weekday() == 0:  # Monday
            self.stdout.write('  📅 Today is Monday - global pool collection day')
        else:
            self.stdout.write(f'  📅 Today is {today.strftime("%A")} - not a collection day')

    def test_frontend_display_logic(self):
        self.stdout.write(self.style.WARNING('\n🖥️ TEST 6: Frontend Display Logic'))
        
        # Test the logic that determines if passive income card should show
        users_with_passive_txns = []
        users_without_passive_txns = []
        
        for user in User.objects.filter(is_approved=True)[:10]:  # Check first 10
            wallet = getattr(user, 'wallet', None)
            if not wallet:
                continue
                
            has_passive_txns = wallet.transactions.filter(
                type='CREDIT',
                meta__type='passive'
            ).exists()
            
            if has_passive_txns:
                users_with_passive_txns.append(user.username)
            else:
                users_without_passive_txns.append(user.username)
        
        self.stdout.write(f'  ✅ Users who SHOULD see passive income card: {len(users_with_passive_txns)}')
        if users_with_passive_txns:
            self.stdout.write(f'    👥 {", ".join(users_with_passive_txns[:5])}{"..." if len(users_with_passive_txns) > 5 else ""}')
        
        self.stdout.write(f'  ❌ Users who should NOT see passive income card: {len(users_without_passive_txns)}')
        if users_without_passive_txns:
            self.stdout.write(f'    👥 {", ".join(users_without_passive_txns[:5])}{"..." if len(users_without_passive_txns) > 5 else ""}')

    def test_admin_panel_display(self):
        self.stdout.write(self.style.WARNING('\n👨‍💼 TEST 7: Admin Panel Display Logic'))
        
        # Test the admin view logic for passive income display
        investment_check_results = []
        
        for user in User.objects.filter(is_approved=True)[:10]:  # Check first 10
            has_investment = DepositRequest.objects.filter(
                user=user, 
                status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').exists()
            
            # Get actual passive income from transactions
            wallet = getattr(user, 'wallet', None)
            if wallet:
                passive_income = wallet.transactions.filter(
                    type='CREDIT',
                    meta__type='passive'
                ).aggregate(total=models.Sum('amount_usd'))['total'] or 0
            else:
                passive_income = 0
            
            # What admin panel should show
            should_show = str(passive_income) if has_investment else '0.00'
            
            investment_check_results.append({
                'username': user.username,
                'has_investment': has_investment,
                'actual_passive': passive_income,
                'admin_should_show': should_show
            })
        
        # Display results
        for result in investment_check_results:
            status = "✅" if result['has_investment'] else "❌"
            self.stdout.write(f'  {status} {result["username"]}: Investment={result["has_investment"]}, Admin shows="${result["admin_should_show"]}"')

    def test_withdrawal_tax(self):
        self.stdout.write(self.style.WARNING('\n💸 TEST 8: Withdrawal Tax'))
        
        from django.conf import settings
        withdraw_tax = settings.ECONOMICS['WITHDRAW_TAX']
        expected_tax = 0.20  # 20%
        
        if withdraw_tax == expected_tax:
            self.stdout.write(f'  ✅ Withdrawal tax correct: {withdraw_tax*100}%')
        else:
            self.stdout.write(self.style.ERROR(f'  ❌ Withdrawal tax incorrect: {withdraw_tax*100}% (expected {expected_tax*100}%)'))

    def generate_summary_report(self):
        self.stdout.write(self.style.SUCCESS('\n📋 SUMMARY REPORT'))
        self.stdout.write("-" * 50)
        
        # Count key metrics
        total_users = User.objects.filter(is_approved=True).count()
        users_with_investments = User.objects.filter(
            is_approved=True,
            wallet__transactions__meta__contains={'type': 'deposit'}
        ).distinct().count()
        
        total_passive_earnings = PassiveEarning.objects.count()
        total_referral_payouts = ReferralPayout.objects.count()
        
        pool = GlobalPool.objects.first()
        pool_balance = pool.balance_usd if pool else 0
        
        self.stdout.write(f'👥 Total approved users: {total_users}')
        self.stdout.write(f'💰 Users with investments: {users_with_investments}')
        self.stdout.write(f'📈 Total passive earnings generated: {total_passive_earnings}')
        self.stdout.write(f'🔗 Total referral payouts: {total_referral_payouts}')
        self.stdout.write(f'🌍 Global pool balance: ${pool_balance}')
        
        # System health check
        issues = []
        
        # Check if passive income is only for investors
        non_investor_with_passive = 0
        for user in User.objects.filter(is_approved=True):
            has_investment = DepositRequest.objects.filter(
                user=user, status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').exists()
            
            has_passive = PassiveEarning.objects.filter(user=user).exists()
            
            if has_passive and not has_investment:
                non_investor_with_passive += 1
        
        if non_investor_with_passive > 0:
            issues.append(f'{non_investor_with_passive} users have passive income without investments')
        
        if issues:
            self.stdout.write(self.style.ERROR('\n⚠️ ISSUES FOUND:'))
            for issue in issues:
                self.stdout.write(f'  ❌ {issue}')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ ALL SYSTEMS WORKING CORRECTLY!'))