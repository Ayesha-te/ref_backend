from django.db import models
from django.conf import settings

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    available_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hold_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # 20% platform hold

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
    status = models.CharField(max_length=20, default='PENDING')  # PENDING/APPROVED/REJECTED/CREDITED
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']