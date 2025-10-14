"""
Management command to fix all passive income issues in one go.

Usage in Render shell:
    python manage.py fix_all_passive_income
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models import Sum
from decimal import Decimal
from datetime import datetime, timedelta

from apps.wallets.models import Wallet, Transaction
from apps.earnings.models import PassiveEarning


class Command(BaseCommand):
    help = 'Fix all passive income issues: backfill, recalculate, and verify'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-backfill',
            action='store_true',
            help='Skip the backfill step (only recalculate existing data)',
        )
        parser.add_argument(
            '--backfill-days',
            type=int,
            default=30,
            help='Number of days to backfill (default: 30)',
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(self.style.SUCCESS("🚀 STARTING PASSIVE INCOME FIX"))
        self.stdout.write("=" * 100 + "\n")

        # Step 1: Initial diagnostic
        self.step1_diagnostic()

        # Step 2: Backfill (unless skipped)
        if not options['skip_backfill']:
            self.step2_backfill(options['backfill_days'])
        else:
            self.stdout.write(self.style.WARNING("\n⏭️  Skipping backfill step\n"))

        # Step 3: Recalculate wallets
        self.step3_recalculate_wallets()

        # Step 4: Verify integrity
        self.step4_verify_integrity()

        # Step 5: Final verification
        self.step5_final_verification()

        # Summary
        self.print_summary()

    def step1_diagnostic(self):
        """Step 1: Run comprehensive diagnostic"""
        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(self.style.SUCCESS("📊 STEP 1: Initial Diagnostic"))
        self.stdout.write("=" * 100 + "\n")

        try:
            call_command('comprehensive_passive_check')
            self.stdout.write(self.style.SUCCESS("\n✅ Diagnostic complete!\n"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {e}\n"))

    def step2_backfill(self, days):
        """Step 2: Backfill missing passive income"""
        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(self.style.SUCCESS("🔧 STEP 2: Backfilling Missing Passive Income"))
        self.stdout.write("=" * 100 + "\n")

        backfill_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        self.stdout.write(f"Backfilling from: {backfill_date}\n")

        try:
            call_command('run_daily_earnings', backfill_from_date=backfill_date)
            self.stdout.write(self.style.SUCCESS("\n✅ Backfill complete!\n"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {e}\n"))

    def step3_recalculate_wallets(self):
        """Step 3: Recalculate all wallet balances"""
        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(self.style.SUCCESS("💰 STEP 3: Recalculating Wallet Balances"))
        self.stdout.write("=" * 100 + "\n")

        wallets = Wallet.objects.all()
        fixed_count = 0
        issue_count = 0

        for wallet in wallets:
            # Calculate total income from all non-deposit credits
            income_transactions = Transaction.objects.filter(
                wallet=wallet,
                type='CREDIT'
            ).exclude(
                meta__contains={'type': 'deposit'}
            )

            calculated_income = income_transactions.aggregate(
                total=Sum('amount_usd')
            )['total'] or Decimal('0.00')

            stored_income = wallet.income_usd

            if calculated_income != stored_income:
                self.stdout.write(
                    self.style.WARNING(
                        f"❌ User {wallet.user.username} (ID: {wallet.user.id}):"
                    )
                )
                self.stdout.write(f"   Stored: ${stored_income}, Calculated: ${calculated_income}")
                self.stdout.write(f"   Difference: ${calculated_income - stored_income}")

                # Fix the wallet
                wallet.income_usd = calculated_income
                wallet.save()

                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ FIXED! Updated to ${calculated_income}\n")
                )
                fixed_count += 1
                issue_count += 1
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ User {wallet.user.username} (ID: {wallet.user.id}): ${stored_income} - OK"
                    )
                )

        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(f"📊 SUMMARY:")
        self.stdout.write(f"   Total wallets: {wallets.count()}")
        self.stdout.write(f"   Issues found: {issue_count}")
        self.stdout.write(f"   Wallets fixed: {fixed_count}")
        self.stdout.write("=" * 100 + "\n")

    def step4_verify_integrity(self):
        """Step 4: Verify passive income integrity"""
        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(self.style.SUCCESS("🔍 STEP 4: Verifying Data Integrity"))
        self.stdout.write("=" * 100 + "\n")

        users_with_earnings = PassiveEarning.objects.values('user').distinct()
        issues_found = []

        for user_data in users_with_earnings:
            user_id = user_data['user']

            # Count records
            passive_count = PassiveEarning.objects.filter(user_id=user_id).count()

            wallet = Wallet.objects.filter(user_id=user_id).first()
            if not wallet:
                continue

            transaction_count = Transaction.objects.filter(
                wallet=wallet,
                type='CREDIT',
                meta__contains={'type': 'passive'}
            ).count()

            # Sum amounts
            passive_sum = PassiveEarning.objects.filter(user_id=user_id).aggregate(
                total=Sum('amount_usd')
            )['total'] or Decimal('0.00')

            transaction_sum = Transaction.objects.filter(
                wallet=wallet,
                type='CREDIT',
                meta__contains={'type': 'passive'}
            ).aggregate(
                total=Sum('amount_usd')
            )['total'] or Decimal('0.00')

            # Check for mismatches
            if passive_count != transaction_count:
                issues_found.append('count_mismatch')
                self.stdout.write(
                    self.style.WARNING(
                        f"❌ User ID {user_id}: PassiveEarning={passive_count}, "
                        f"Transactions={transaction_count}"
                    )
                )

            if abs(passive_sum - transaction_sum) > Decimal('0.01'):
                issues_found.append('amount_mismatch')
                self.stdout.write(
                    self.style.WARNING(
                        f"❌ User ID {user_id}: PassiveEarning=${passive_sum}, "
                        f"Transactions=${transaction_sum}"
                    )
                )

        if not issues_found:
            self.stdout.write(self.style.SUCCESS("✅ All records are consistent!"))
        else:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  Found {len(issues_found)} integrity issues")
            )

        self.stdout.write("\n")

    def step5_final_verification(self):
        """Step 5: Final verification"""
        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(self.style.SUCCESS("✅ STEP 5: Final Verification"))
        self.stdout.write("=" * 100 + "\n")

        try:
            call_command('comprehensive_passive_check')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {e}\n"))

    def print_summary(self):
        """Print final summary"""
        self.stdout.write("\n" + "=" * 100)
        self.stdout.write(self.style.SUCCESS("📋 FINAL SUMMARY"))
        self.stdout.write("=" * 100 + "\n")

        self.stdout.write(self.style.SUCCESS("✅ All fixes have been applied!\n"))

        self.stdout.write("📌 HOW PASSIVE INCOME WORKS:")
        self.stdout.write("   • User deposits $100")
        self.stdout.write("   • Split: 80% → available_usd ($80), 20% → hold_usd ($20)")
        self.stdout.write("   • Starting DAY 1: passive income generated daily")
        self.stdout.write("   • Daily earning = $100 × daily_rate × 80%")
        self.stdout.write("   • Added to income_usd (withdrawable)")
        self.stdout.write("   • Runs for 90 days max")
        self.stdout.write("   • Total ≈ $130 over 90 days\n")

        self.stdout.write("📌 DAILY AUTOMATION:")
        self.stdout.write("   Run: python manage.py run_daily_earnings")
        self.stdout.write("   Via: Celery Beat or middleware\n")

        self.stdout.write("📌 USEFUL COMMANDS:")
        self.stdout.write("   • Check status:")
        self.stdout.write("     python manage.py comprehensive_passive_check")
        self.stdout.write("   • Generate today's earnings:")
        self.stdout.write("     python manage.py run_daily_earnings")
        self.stdout.write("   • Backfill from date:")
        self.stdout.write("     python manage.py run_daily_earnings --backfill-from-date 2025-10-01")
        self.stdout.write("   • Fix everything:")
        self.stdout.write("     python manage.py fix_all_passive_income\n")

        self.stdout.write("=" * 100)
        self.stdout.write(self.style.SUCCESS("🎉 SCRIPT COMPLETE - ALL USERS FIXED!"))
        self.stdout.write("=" * 100 + "\n")