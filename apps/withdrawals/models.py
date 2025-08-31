from django.db import models
from django.conf import settings

class WithdrawalRequest(models.Model):
    METHOD_CHOICES = [
        ('BANK', 'Bank'),
        ('EASYPaisa', 'EasyPaisa'),
        ('JAZZCASH', 'JazzCash'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdraw_requests')
    amount_pkr = models.DecimalField(max_digits=14, decimal_places=2)
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2)
    fx_rate = models.DecimalField(max_digits=10, decimal_places=4)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    account_details = models.JSONField(default=dict)
    tx_id = models.CharField(max_length=100, null=True, blank=True)
    tax_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='PENDING')  # PENDING/APPROVED/REJECTED/PAID
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']