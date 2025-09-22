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
    New windows: [10, 30, 100]. Each window pays a percentage of the combined
    first-investment amounts of included directs, then resets to 0 and advances.
    """
    STAGES = [10, 30, 100]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_milestone_progress')
    stage_index = models.PositiveSmallIntegerField(default=0)  # 0..2 index into STAGES
    current_count = models.PositiveIntegerField(default=0)     # number of directs included in current window
    current_sum_usd = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    included_direct_ids = models.JSONField(default=list)       # list of direct user IDs counted in current window

    def current_target(self) -> int:
        return self.STAGES[self.stage_index]

    def advance_stage(self):
        self.stage_index = (self.stage_index + 1) % len(self.STAGES)
        self.reset_window()

    def reset_window(self):
        self.current_count = 0
        self.current_sum_usd = 0
        self.included_direct_ids = []


class ReferralMilestoneAward(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_milestone_awards')
    target = models.PositiveIntegerField()  # 10/30/100
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']