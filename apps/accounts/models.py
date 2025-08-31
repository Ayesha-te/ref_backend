from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # referral structure
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    referral_code = models.CharField(max_length=12, unique=True, blank=True)
    is_approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.referral_code:
            import random, string
            self.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)

class SignupProof(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signup_proofs')
    amount_pkr = models.DecimalField(max_digits=14, decimal_places=2)
    tx_id = models.CharField(max_length=100)
    proof_image = models.ImageField(upload_to='signup_proofs/', null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')  # PENDING/APPROVED/REJECTED
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']