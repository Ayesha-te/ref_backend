from django.db import models

class GlobalPool(models.Model):
    # accumulated USD for pool
    balance_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

class GlobalPoolPayout(models.Model):
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2)
    distributed_on = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)