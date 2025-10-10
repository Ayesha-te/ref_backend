from django.db import models
from django.conf import settings
from decimal import Decimal

class PassiveEarning(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='passive_earnings')
    day_index = models.PositiveIntegerField()  # 1..N for a cycle
    percent = models.DecimalField(max_digits=5, decimal_places=4)  # 0.004 = 0.4%
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "day_index")
        ordering = ['-created_at']


class DailyEarningsState(models.Model):
    """Singleton model to track when daily earnings were last processed"""
    last_processed_date = models.DateField()
    last_processed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Daily Earnings State"
        verbose_name_plural = "Daily Earnings State"
    
    def __str__(self):
        return f"Last processed: {self.last_processed_date}"


class GlobalPoolState(models.Model):
    """Singleton model to track global pool collection and distribution"""
    # Current week's collection (resets after distribution)
    current_pool_usd = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    
    # Tracking dates
    last_collection_date = models.DateField(null=True, blank=True)  # Last Monday we collected from
    last_distribution_date = models.DateField(null=True, blank=True)  # Last Monday we distributed
    
    # Stats
    total_collected_all_time = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total_distributed_all_time = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Global Pool State"
        verbose_name_plural = "Global Pool State"
    
    def __str__(self):
        return f"Pool: ${self.current_pool_usd} | Last Collection: {self.last_collection_date} | Last Distribution: {self.last_distribution_date}"


class GlobalPoolCollection(models.Model):
    """Track each collection from Monday signups"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='global_pool_collections')
    signup_amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    collection_amount_usd = models.DecimalField(max_digits=12, decimal_places=2)  # 0.5% of signup
    collection_date = models.DateField()  # The Monday this was collected for
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ("user", "collection_date")  # One collection per user per Monday
    
    def __str__(self):
        return f"{self.user.username} - ${self.collection_amount_usd} on {self.collection_date}"


class GlobalPoolDistribution(models.Model):
    """Track each distribution to users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='global_pool_distributions')
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    distribution_date = models.DateField()  # The Monday this was distributed
    total_pool_amount = models.DecimalField(max_digits=12, decimal_places=2)  # Total pool that was distributed
    total_users = models.PositiveIntegerField()  # Number of users who received a share
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ("user", "distribution_date")  # One distribution per user per Monday
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount_usd} on {self.distribution_date}"