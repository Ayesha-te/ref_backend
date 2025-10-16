from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from apps.earnings.services import compute_daily_earning_usd
from apps.earnings.models_global_pool import GlobalPool
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help = 'Recalculate ALL passive earnings using ACTUAL deposit amounts instead of fixed $100'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Recalculate only for specific user ID'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        user_id = options.get('user_id')

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No changes will be made\n"))

        User = get_user_model()
        pool, _ = GlobalPool.objects.get_or_create(pk=1)

        # Get all users with passive earnings
        if user_id:
            users = User.objects.filter(id=user_id, passive_earnings__isnull=False).distinct()
        else:
            users = User.objects.filter(passive_earnings__isnull=False).distinct()

        if not users.exists():
            self.stdout.write(self.style.WARNING("❌ No users with passive earnings found"))
            return

        self.stdout.write(self.style.SUCCESS(f"📊 Found {users.count()} users to recalculate\n"))

        total_old_earnings = Decimal('0')
        total_new_earnings = Decimal('0')
        total_diff = Decimal('0')
        total_global_pool_adjustment = Decimal('0')

        for u in users:
            # Get first credited deposit
            first_dep = DepositRequest.objects.filter(
                user=u, status='CREDITED'
            ).exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()

            if not first_dep:
                self.stdout.write(self.style.WARNING(f"⏭️  {u.username}: No credited deposit found, skipping"))
                continue

            deposit_usd = first_dep.amount_usd
            wallet = Wallet.objects.get(user=u)

            # Get all passive earnings for this user
            earnings = PassiveEarning.objects.filter(user=u).order_by('day_index')

            if not earnings.exists():
                self.stdout.write(self.style.WARNING(f"⏭️  {u.username}: No passive earnings to recalculate"))
                continue

            user_old_total = Decimal('0')
            user_new_total = Decimal('0')
            user_count = 0

            self.stdout.write(self.style.SUCCESS(f"\n👤 {u.username} (Deposit: ${deposit_usd})"))
            self.stdout.write(f"   Recalculating {earnings.count()} days of earnings...")

            for earning in earnings:
                day_index = earning.day_index
                old_amount = earning.amount_usd
                user_old_total += old_amount

                # Recalculate using actual deposit
                metrics = compute_daily_earning_usd(day_index, deposit_usd)
                new_amount = metrics['user_share_usd']

                user_new_total += new_amount
                diff = new_amount - old_amount
                total_diff += diff

                if diff != 0:
                    user_count += 1
                    diff_str = f"+${diff}" if diff > 0 else f"-${abs(diff)}"
                    self.stdout.write(f"   Day {day_index:>2}: ${old_amount} → ${new_amount} ({diff_str})")

                if not dry_run:
                    # Update PassiveEarning record
                    earning.amount_usd = new_amount
                    earning.percent = metrics['percent']
                    earning.save()

            if user_count == 0:
                self.stdout.write(f"   ✅ All {earnings.count()} earnings already correct!")
                total_old_earnings += user_old_total
                total_new_earnings += user_new_total
                continue

            # Update wallet income and transactions
            if not dry_run:
                wallet.income_usd = user_new_total
                wallet.save()

                # Update all passive income transactions for this user
                transactions = Transaction.objects.filter(
                    wallet=wallet,
                    type=Transaction.CREDIT,
                    meta__type='passive'
                )

                for tx in transactions:
                    # Find corresponding PassiveEarning
                    day_idx = tx.meta.get('day_index')
                    if day_idx:
                        pe = PassiveEarning.objects.filter(user=u, day_index=day_idx).first()
                        if pe:
                            tx.amount_usd = pe.amount_usd
                            tx.save()

                # Recalculate global pool adjustments
                global_pool_diff = Decimal('0')
                for earning in earnings:
                    metrics = compute_daily_earning_usd(earning.day_index, deposit_usd)
                    # We don't have the old global pool amounts, so just use new ones
                    # This will be handled by the global pool system

                self.stdout.write(self.style.SUCCESS(f"   ✅ Updated {user_count} earnings"))
                self.stdout.write(f"   💰 Old Total: ${user_old_total}")
                self.stdout.write(f"   💰 New Total: ${user_new_total}")
                self.stdout.write(f"   📊 Difference: ${total_diff if total_diff != 0 else 'None'}")
            else:
                self.stdout.write(self.style.WARNING(f"   [DRY RUN] Would update {user_count} earnings"))
                self.stdout.write(f"   💰 Old Total: ${user_old_total}")
                self.stdout.write(f"   💰 New Total: ${user_new_total}")
                self.stdout.write(f"   📊 Difference: ${total_diff if total_diff != 0 else 'None'}")

            total_old_earnings += user_old_total
            total_new_earnings += user_new_total

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "="*70))
        self.stdout.write(self.style.SUCCESS("📊 RECALCULATION SUMMARY"))
        self.stdout.write(self.style.SUCCESS("="*70))
        self.stdout.write(self.style.SUCCESS(f"👥 Users Processed: {users.count()}"))
        self.stdout.write(self.style.SUCCESS(f"💰 Total Old Earnings: ${total_old_earnings}"))
        self.stdout.write(self.style.SUCCESS(f"💰 Total New Earnings: ${total_new_earnings}"))
        self.stdout.write(self.style.SUCCESS(f"📊 Total Adjustment: ${total_diff}"))

        if total_diff > 0:
            self.stdout.write(self.style.WARNING(f"⚠️  Users will receive ${total_diff} MORE (was undercharged)"))
        elif total_diff < 0:
            self.stdout.write(self.style.WARNING(f"⚠️  Users will receive ${abs(total_diff)} LESS (was overcharged)"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ No adjustment needed"))

        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 This was a DRY RUN - no changes were made"))
            self.stdout.write(self.style.WARNING("Run without --dry-run to apply changes"))

        self.stdout.write(self.style.SUCCESS("="*70))