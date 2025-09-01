from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction
from .models import ReferralPayout

from django.conf import settings

REFERRAL_TIERS = [Decimal(str(x)) for x in settings.ECONOMICS['REFERRAL_TIERS']]
PACKAGE_USD = Decimal('100.00')

User = get_user_model()

def pay_on_package_purchase(buyer: User):
    """Distribute referral rewards up to 3 levels when buyer joins (approval event), not on later deposits."""
    upline = []
    cur = buyer.referred_by
    level = 1
    while cur and level <= 3:
        upline.append((cur, level))
        cur = cur.referred_by
        level += 1

    for ref_user, lvl in upline:
        pct = REFERRAL_TIERS[lvl-1]
        amt = (PACKAGE_USD * pct).quantize(Decimal('0.01'))
        wallet, _ = Wallet.objects.get_or_create(user=ref_user)
        wallet.available_usd = (Decimal(wallet.available_usd) + amt).quantize(Decimal('0.01'))
        wallet.save()
        Transaction.objects.create(wallet=wallet, type=Transaction.CREDIT, amount_usd=amt, meta={'type': 'referral', 'level': lvl, 'source_user': buyer.id, 'trigger': 'join'})
        ReferralPayout.objects.create(referrer=ref_user, referee=buyer, level=lvl, amount_usd=amt)