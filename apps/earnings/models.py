from django.db import models
from django.conf import settings

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