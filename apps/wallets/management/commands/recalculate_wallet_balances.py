from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction, DepositRequest
from decimal import Decimal

class Command(BaseCommand):
    help = 'Recalculate wallet balances based on new logic: available_usd = 80% of deposits, income_usd = passive + referral + milestone'

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all()
        
        self.stdout.write(self.style.SUCCESS("\n" + "="*80))
        self.stdout.write(self.style.SUCCESS("🔄 RECALCULATING WALLET BALANCES"))
        self.stdout.write(self.style.SUCCESS("="*80))
        
        for u in users:
            wallet, _ = Wallet.objects.get_or_create(user=u)
            
            # Calculate available_usd: 80% of all CREDITED deposits
            credited_deposits = DepositRequest.objects.filter(user=u, status='CREDITED')
            total_deposit_usd = sum((Decimal(d.amount_usd) for d in credited_deposits), Decimal('0'))
            available_usd = (total_deposit_usd * Decimal('0.80')).quantize(Decimal('0.01'))
            
            # Calculate income_usd: passive + referral + milestone - withdrawals
            income_credits = wallet.transactions.filter(
                type=Transaction.CREDIT
            ).filter(
                meta__type__in=['passive', 'referral', 'milestone']
            ).exclude(
                meta__source='signup-initial'
            ).exclude(
                meta__non_income=True
            )
            
            total_income = sum((Decimal(t.amount_usd) for t in income_credits), Decimal('0'))
            
            # Subtract withdrawals
            withdrawal_debits = wallet.transactions.filter(
                type=Transaction.DEBIT,
                meta__type='withdrawal'
            )
            total_withdrawals = sum((Decimal(t.amount_usd) for t in withdrawal_debits), Decimal('0'))
            
            income_usd = (total_income - total_withdrawals).quantize(Decimal('0.01'))
            
            # Calculate hold_usd: 20% of deposits + 20% of passive earnings
            deposit_hold = (total_deposit_usd * Decimal('0.20')).quantize(Decimal('0.01'))
            
            # Get passive earnings from PassiveEarning model
            from apps.earnings.models import PassiveEarning
            passive_earnings = PassiveEarning.objects.filter(user=u)
            total_passive = sum((Decimal(pe.amount_usd) for pe in passive_earnings), Decimal('0'))
            passive_hold = (total_passive * Decimal('0.20')).quantize(Decimal('0.01'))
            
            hold_usd = (deposit_hold + passive_hold).quantize(Decimal('0.01'))
            
            # Update wallet
            old_available = wallet.available_usd
            old_income = wallet.income_usd
            old_hold = wallet.hold_usd
            
            wallet.available_usd = available_usd
            wallet.income_usd = income_usd
            wallet.hold_usd = hold_usd
            wallet.save()
            
            self.stdout.write(f"\n👤 {u.username}:")
            self.stdout.write(f"   Available: ${old_available} → ${available_usd} (80% of ${total_deposit_usd} deposits)")
            self.stdout.write(f"   Income: ${old_income} → ${income_usd} (${total_income} earned - ${total_withdrawals} withdrawn)")
            self.stdout.write(f"   Hold: ${old_hold} → ${hold_usd}")
        
        self.stdout.write(self.style.SUCCESS("\n" + "="*80))
        self.stdout.write(self.style.SUCCESS("✅ RECALCULATION COMPLETE"))
        self.stdout.write(self.style.SUCCESS("="*80))