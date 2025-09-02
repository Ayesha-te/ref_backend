from django.db import models
from django.conf import settings

class ReferralPayout(models.Model):
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_payouts')
    referee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referred_events')
    level = models.PositiveSmallIntegerField()  # 1,2,3
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ReferralMilestoneProgress(models.Model):
    """Tracks per-user cyclic milestone progress for direct referrals only.
    Stages: [10 -> $5], [30 -> $30], [50 -> $60], [100 -> $150], then repeat.
    """
    STAGES = [10, 30, 50, 100]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_milestone_progress')
    stage_index = models.PositiveSmallIntegerField(default=0)  # 0..3 index into STAGES
    current_count = models.PositiveIntegerField(default=0)     # counts directs since last award

    def current_target(self) -> int:
        return self.STAGES[self.stage_index]

    def advance_stage(self):
        self.stage_index = (self.stage_index + 1) % len(self.STAGES)
        self.current_count = 0


class ReferralMilestoneAward(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_milestone_awards')
    target = models.PositiveIntegerField()  # 10/30/50/100
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']