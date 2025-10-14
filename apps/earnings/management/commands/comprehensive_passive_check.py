from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from apps.earnings.services import compute_daily_earning_usd, daily_percent_for_day
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Comprehensive passive income diagnostic - explains how it works and identifies issues'

    def handle(self, *args, **options):
        self.stdout.write("=" * 100)
        self.stdout.write(self.style.SUCCESS("🔍 COMPREHENSIVE PASSIVE INCOME DIAGNOSTIC REPORT"))
        self.stdout.write("=" * 100)
        self.stdout.write("")

        # Get economics settings
        USER_SHARE = Decimal(str(settings.ECONOMICS['USER_WALLET_SHARE']))
        GLOBAL_POOL_CUT = Decimal(str(settings.ECONOMICS['GLOBAL_POOL_CUT']))
        PACKAGE_USD = Decimal('100.00')

        self.stdout.write(self.style.WARNING("📊 ECONOMICS CONFIGURATION:"))
        self.stdout.write(f"   • Package Amount: ${PACKAGE_USD}")
        self.stdout.write(f"   • User Share: {USER_SHARE * 100}% (of gross earnings)")
        self.stdout.write(f"   • Platform Hold: {(1 - USER_SHARE) * 100}%")
        self.stdout.write(f"   • Global Pool Cut: {GLOBAL_POOL_CUT * 100}%")
        self.stdout.write("")

        self.stdout.write(self.style.WARNING("💡 HOW PASSIVE INCOME WORKS:"))
        self.stdout.write("   1. User makes a deposit (e.g., $100)")
        self.stdout.write("   2. Deposit is split:")
        self.stdout.write(f"      • {USER_SHARE * 100}% (${PACKAGE_USD * USER_SHARE}) → available_usd (user's wallet)")
        self.stdout.write(f"      • {(1 - USER_SHARE) * 100}% (${PACKAGE_USD * (1 - USER_SHARE)}) → hold_usd (platform)")
        self.stdout.write(f"      • {GLOBAL_POOL_CUT * 100}% (${PACKAGE_USD * GLOBAL_POOL_CUT}) → global pool")
        self.stdout.write("")
        self.stdout.write("   3. Starting from DAY 1 after deposit, passive income is generated:")
        self.stdout.write("      • Each day has a percentage rate (e.g., 0.4% on day 1)")
        self.stdout.write("      • Daily earning = $100 × 0.4% = $0.40 (gross)")
        self.stdout.write(f"      • User gets {USER_SHARE * 100}% of gross = $0.40 × {USER_SHARE} = ${Decimal('0.40') * USER_SHARE}")
        self.stdout.write("      • This is added to income_usd (withdrawable income)")
        self.stdout.write("")
        self.stdout.write("   4. Passive income runs for 90 days maximum")
        self.stdout.write("   5. Total passive income over 90 days ≈ $130 (user share)")
        self.stdout.write("")

        self.stdout.write("=" * 100)
        self.stdout.write(self.style.SUCCESS("🔎 ANALYZING ALL USERS"))
        self.stdout.write("=" * 100)
        self.stdout.write("")

        users = User.objects.filter(is_approved=True).order_by('username')
        total_users = users.count()
        users_with_deposits = 0
        users_with_passive = 0
        users_with_issues = 0

        issue_details = []

        for user in users:
            self.stdout.write(f"\n{'=' * 100}")
            self.stdout.write(self.style.WARNING(f"👤 USER: {user.username} (ID: {user.id})"))
            self.stdout.write(f"{'=' * 100}")
            
            # Get wallet
            wallet = Wallet.objects.filter(user=user).first()
            if not wallet:
                self.stdout.write("   ⚠️  NO WALLET FOUND")
                continue
            
            # Get first credited deposit (excluding signup initial)
            first_deposit = DepositRequest.objects.filter(
                user=user, 
                status='CREDITED'
            ).exclude(
                tx_id='SIGNUP-INIT'
            ).order_by('processed_at', 'created_at').first()
            
            if not first_deposit:
                self.stdout.write("   ℹ️  No credited deposits yet (passive income not started)")
                self.stdout.write(f"   💰 Wallet Balance: available=${wallet.available_usd}, income=${wallet.income_usd}")
                continue
            
            users_with_deposits += 1
            
            # Calculate days since deposit
            deposit_date = first_deposit.processed_at or first_deposit.created_at
            days_since_deposit = (timezone.now() - deposit_date).days
            
            self.stdout.write(f"\n📅 DEPOSIT INFORMATION:")
            self.stdout.write(f"   • First Deposit: ${first_deposit.amount_usd} on {deposit_date.strftime('%Y-%m-%d %H:%M')}")
            self.stdout.write(f"   • Days Since Deposit: {days_since_deposit}")
            self.stdout.write(f"   • Deposit TX ID: {first_deposit.tx_id}")
            
            # Get passive earnings
            passive_earnings = PassiveEarning.objects.filter(user=user).order_by('day_index')
            passive_count = passive_earnings.count()
            
            if passive_count > 0:
                users_with_passive += 1
                last_earning = passive_earnings.last()
                self.stdout.write(f"\n📈 PASSIVE EARNINGS RECORDS:")
                self.stdout.write(f"   • Total Records: {passive_count}")
                self.stdout.write(f"   • Last Day Index: {last_earning.day_index}")
                self.stdout.write(f"   • Expected Day Index: {min(days_since_deposit, 90)}")
                
                # Calculate total from PassiveEarning model
                total_passive_model = sum(pe.amount_usd for pe in passive_earnings)
                self.stdout.write(f"   • Total from PassiveEarning model: ${total_passive_model}")
            else:
                self.stdout.write(f"\n⚠️  NO PASSIVE EARNINGS RECORDS")
                self.stdout.write(f"   • Expected: {min(days_since_deposit, 90)} records")
                if days_since_deposit >= 1:
                    self.stdout.write(self.style.ERROR(f"   • ❌ ISSUE: User should have passive earnings by now!"))
                    users_with_issues += 1
                    issue_details.append({
                        'user': user.username,
                        'issue': 'No passive earnings generated',
                        'days_since_deposit': days_since_deposit
                    })
            
            # Get passive income from transactions
            passive_transactions = Transaction.objects.filter(
                wallet=wallet,
                type=Transaction.CREDIT,
                meta__contains={'type': 'passive'}
            )
            
            passive_tx_count = passive_transactions.count()
            total_passive_tx = sum(tx.amount_usd for tx in passive_transactions)
            
            self.stdout.write(f"\n💸 PASSIVE INCOME TRANSACTIONS:")
            self.stdout.write(f"   • Total Transactions: {passive_tx_count}")
            self.stdout.write(f"   • Total Amount: ${total_passive_tx}")
            
            # Calculate expected passive income
            expected_days = min(days_since_deposit, 90)
            expected_total = Decimal('0.00')
            
            if expected_days >= 1:
                self.stdout.write(f"\n🧮 EXPECTED PASSIVE INCOME CALCULATION:")
                self.stdout.write(f"   Days to calculate: {expected_days}")
                
                for day in range(1, expected_days + 1):
                    metrics = compute_daily_earning_usd(day)
                    expected_total += metrics['user_share_usd']
                    if day <= 5 or day == expected_days:  # Show first 5 and last day
                        self.stdout.write(f"   • Day {day}: {metrics['percent']}% × ${PACKAGE_USD} × {USER_SHARE} = ${metrics['user_share_usd']}")
                    elif day == 6:
                        self.stdout.write(f"   • ... (days 6-{expected_days-1})")
                
                self.stdout.write(self.style.SUCCESS(f"   • TOTAL EXPECTED: ${expected_total}"))
            
            # Get wallet method calculation
            wallet_income = wallet.get_current_income_usd()
            
            self.stdout.write(f"\n💰 WALLET STATUS:")
            self.stdout.write(f"   • available_usd: ${wallet.available_usd} (80% of deposits)")
            self.stdout.write(f"   • income_usd (stored): ${wallet.income_usd}")
            self.stdout.write(f"   • income_usd (calculated): ${wallet_income}")
            self.stdout.write(f"   • hold_usd: ${wallet.hold_usd}")
            
            # Check for discrepancies
            has_issue = False
            
            if passive_count > 0 and passive_tx_count > 0:
                if passive_count != passive_tx_count:
                    self.stdout.write(self.style.ERROR(f"\n   ❌ ISSUE: PassiveEarning records ({passive_count}) ≠ Transactions ({passive_tx_count})"))
                    has_issue = True
                    issue_details.append({
                        'user': user.username,
                        'issue': f'Record mismatch: {passive_count} earnings vs {passive_tx_count} transactions',
                        'days_since_deposit': days_since_deposit
                    })
                
                if abs(total_passive_model - total_passive_tx) > Decimal('0.01'):
                    self.stdout.write(self.style.ERROR(f"\n   ❌ ISSUE: PassiveEarning total (${total_passive_model}) ≠ Transaction total (${total_passive_tx})"))
                    has_issue = True
                    issue_details.append({
                        'user': user.username,
                        'issue': f'Amount mismatch: ${total_passive_model} vs ${total_passive_tx}',
                        'days_since_deposit': days_since_deposit
                    })
            
            if expected_days >= 1 and passive_count > 0:
                if passive_count < expected_days:
                    self.stdout.write(self.style.WARNING(f"\n   ⚠️  WARNING: Missing earnings (has {passive_count}, expected {expected_days})"))
                    has_issue = True
                    issue_details.append({
                        'user': user.username,
                        'issue': f'Missing earnings: {passive_count}/{expected_days} days',
                        'days_since_deposit': days_since_deposit
                    })
                
                if abs(total_passive_tx - expected_total) > Decimal('0.01'):
                    self.stdout.write(self.style.WARNING(f"\n   ⚠️  WARNING: Total passive (${total_passive_tx}) ≠ Expected (${expected_total})"))
                    self.stdout.write(f"      Difference: ${abs(total_passive_tx - expected_total)}")
                    has_issue = True
                    issue_details.append({
                        'user': user.username,
                        'issue': f'Amount discrepancy: ${total_passive_tx} vs expected ${expected_total}',
                        'days_since_deposit': days_since_deposit
                    })
            
            # Check if passive income exceeds current income (CRITICAL)
            if total_passive_tx > wallet_income:
                self.stdout.write(self.style.ERROR(f"\n   🚨 CRITICAL: Passive income (${total_passive_tx}) > Total income (${wallet_income})"))
                has_issue = True
                issue_details.append({
                    'user': user.username,
                    'issue': f'CRITICAL: Passive (${total_passive_tx}) > Total income (${wallet_income})',
                    'days_since_deposit': days_since_deposit
                })
            
            if has_issue:
                users_with_issues += 1
                self.stdout.write(self.style.ERROR(f"\n   ❌ STATUS: HAS ISSUES"))
            else:
                self.stdout.write(self.style.SUCCESS(f"\n   ✅ STATUS: OK"))

        # Summary
        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(self.style.SUCCESS("📊 SUMMARY REPORT"))
        self.stdout.write("=" * 100)
        self.stdout.write(f"\n👥 Total Approved Users: {total_users}")
        self.stdout.write(f"💰 Users with Deposits: {users_with_deposits}")
        self.stdout.write(f"📈 Users with Passive Earnings: {users_with_passive}")
        self.stdout.write(self.style.ERROR(f"❌ Users with Issues: {users_with_issues}"))
        self.stdout.write(self.style.SUCCESS(f"✅ Users OK: {users_with_deposits - users_with_issues}"))

        if issue_details:
            self.stdout.write("\n" + "=" * 100)
            self.stdout.write(self.style.ERROR("🚨 DETAILED ISSUE LIST"))
            self.stdout.write("=" * 100)
            for idx, issue in enumerate(issue_details, 1):
                self.stdout.write(f"\n{idx}. {issue['user']} (Days since deposit: {issue['days_since_deposit']})")
                self.stdout.write(f"   Issue: {issue['issue']}")

        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(self.style.WARNING("💡 RECOMMENDATIONS"))
        self.stdout.write("=" * 100)
        self.stdout.write("""
1. Run the daily earnings command to generate missing passive income:
   python manage.py run_daily_earnings

2. For backfilling from a specific date:
   python manage.py run_daily_earnings --backfill-from-date YYYY-MM-DD

3. To see what would happen without making changes:
   python manage.py run_daily_earnings --dry-run

4. Check the passive earnings schedule in settings.ECONOMICS['PASSIVE_SCHEDULE']

5. Verify that the daily earnings task is running automatically via Celery
""")

        self.stdout.write("=" * 100)
        self.stdout.write(self.style.SUCCESS("✅ DIAGNOSTIC COMPLETE"))
        self.stdout.write("=" * 100)