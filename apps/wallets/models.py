from django.db import models
from django.conf import settings
from decimal import Decimal

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    available_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # 80% of deposits only
    hold_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # 20% platform hold
    income_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Withdrawable income (passive + referral + milestone)
    
    def get_current_income_usd(self):
        """Calculate total current income from transactions (passive + referral + milestone + global pool)"""
        from django.db.models import Sum, Q
        
        # Sum all income credits (passive, referral, milestone, global_pool)
        # Using meta__contains for PostgreSQL JSONB compatibility
        income_credits = self.transactions.filter(
            type=Transaction.CREDIT
        ).filter(
            Q(meta__contains={'type': 'passive'}) | 
            Q(meta__contains={'type': 'referral'}) | 
            Q(meta__contains={'type': 'milestone'}) |
            Q(meta__contains={'type': 'global_pool'}) |
            Q(meta__contains={'type': 'referral_correction'})  # Include correction transactions
        ).exclude(
            meta__contains={'source': 'signup-initial'}
        ).exclude(
            meta__contains={'non_income': True}
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        # Subtract all income-related debits (withdrawals and referral reversals)
        income_debits = self.transactions.filter(
            type=Transaction.DEBIT
        ).filter(
            Q(meta__contains={'type': 'withdrawal'}) |
            Q(meta__contains={'type': 'referral_reversal'})  # Include reversal transactions
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        return (income_credits - income_debits).quantize(Decimal('0.01'))

class Transaction(models.Model):
    CREDIT = 'CREDIT'
    DEBIT = 'DEBIT'
    TYPES = [(CREDIT, 'Credit'), (DEBIT, 'Debit')]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=TYPES)
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class DepositRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposit_requests')
    amount_pkr = models.DecimalField(max_digits=14, decimal_places=2)
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2)
    fx_rate = models.DecimalField(max_digits=10, decimal_places=4)
    tx_id = models.CharField(max_length=100)
    # New fields for bank/account info
    bank_name = models.CharField(max_length=120, blank=True)
    account_name = models.CharField(max_length=120, blank=True)
    proof_image = models.ImageField(upload_to='deposit_proofs/', null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')  # PENDING/APPROVED/REJECTED/CREDITED
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']