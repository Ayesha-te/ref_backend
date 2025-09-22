from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction
from .models import ReferralPayout, ReferralMilestoneProgress, ReferralMilestoneAward

REFERRAL_TIERS = [Decimal(str(x)) for x in settings.ECONOMICS['REFERRAL_TIERS']]

# Read milestone percents from settings if provided (e.g., "10:0.05,30:0.10"). If not provided, default to zero (no milestone payout).
_MILESTONE_PCTS_RAW = settings.ECONOMICS.get('MILESTONE_PCTS', '')
MILESTONE_PCTS = {}
if _MILESTONE_PCTS_RAW:
    for pair in _MILESTONE_PCTS_RAW.split(','):
        k, v = pair.split(':')
        MILESTONE_PCTS[int(k.strip())] = Decimal(str(float(v.strip())))

User = get_user_model()


def _credit(wallet: Wallet, amount: Decimal, meta: dict):
    wallet.available_usd = (Decimal(wallet.available_usd) + amount).quantize(Decimal('0.01'))
    wallet.save()
    Transaction.objects.create(wallet=wallet, type=Transaction.CREDIT, amount_usd=amount, meta=meta)


def record_direct_first_investment(referrer: User, direct: User, amount_usd: Decimal) -> None:
    """Track a direct's first investment toward the current milestone window and pay when target is reached.
    Windows: [10, 30, 100] directs; award is a percentage of the combined first-investment amounts in the window.
    Payout percents: 10 → 1%, 30 → 3%, 100 → 5%.
    After payout, the window resets and advances to the next stage.
    """
    pct_map = {10: Decimal('0.01'), 30: Decimal('0.03'), 100: Decimal('0.05')}
    prog, _ = ReferralMilestoneProgress.objects.get_or_create(user=referrer)
    target = prog.current_target()

    # Only count each direct once per window
    included = set(prog.included_direct_ids or [])
    if direct.id in included:
        return

    included.add(direct.id)
    prog.included_direct_ids = list(included)
    prog.current_count += 1
    prog.current_sum_usd = (Decimal(prog.current_sum_usd) + Decimal(amount_usd)).quantize(Decimal('0.01'))

    if prog.current_count >= target:
        pct = pct_map.get(target, Decimal('0'))
        award = (Decimal(prog.current_sum_usd) * pct).quantize(Decimal('0.01')) if pct > 0 else Decimal('0')
        if award > 0:
            wallet, _ = Wallet.objects.get_or_create(user=referrer)
            _credit(wallet, award, meta={'type': 'milestone', 'target': target, 'sum_usd': str(prog.current_sum_usd), 'pct': str(pct)})
            ReferralMilestoneAward.objects.create(user=referrer, target=target, amount_usd=award)
        prog.advance_stage()
    prog.save()


def pay_on_package_purchase(buyer: User):
    """Distribute referral rewards when buyer is approved (joins).
    - L1: 6%
    - L2: 3%
    - L3: 1%
    Referral rewards are percentages of the signup payment amount (converted to USD).
    Milestones (if configured) are also percentage-based of the same base amount.
    """
    # Determine signup payment base in USD from PKR configured fee and current admin FX rate
    signup_fee_pkr = Decimal(str(settings.SIGNUP_FEE_PKR))
    rate = Decimal(str(settings.ADMIN_USD_TO_PKR))
    base_signup_usd = (signup_fee_pkr / rate).quantize(Decimal('0.01'))

    upline = []
    cur = buyer.referred_by
    level = 1
    while cur and level <= 3:
        upline.append((cur, level))
        cur = cur.referred_by
        level += 1

    # Milestones now trigger only on directs' first investments via record_direct_first_investment.
    # No milestone progression on signup approval.

    # Payouts: percentage of signup payment
    for ref_user, lvl in upline:
        pct = REFERRAL_TIERS[lvl-1]
        amt = (base_signup_usd * pct).quantize(Decimal('0.01'))
        if amt <= 0:
            continue
        wallet, _ = Wallet.objects.get_or_create(user=ref_user)
        _credit(wallet, amt, meta={'type': 'referral', 'level': lvl, 'source_user': buyer.id, 'trigger': 'join', 'base': str(base_signup_usd), 'pct': str(pct)})
        ReferralPayout.objects.create(referrer=ref_user, referee=buyer, level=lvl, amount_usd=amt)


def pay_on_first_investment(buyer: User, amount_usd: Decimal):
    """Distribute referral rewards on buyer's first investment using same tiers (% of investment amount)."""
    upline = []
    cur = buyer.referred_by
    level = 1
    while cur and level <= 3:
        upline.append((cur, level))
        cur = cur.referred_by
        level += 1

    for ref_user, lvl in upline:
        pct = REFERRAL_TIERS[lvl-1]
        amt = (Decimal(amount_usd) * pct).quantize(Decimal('0.01'))
        if amt <= 0:
            continue
        wallet, _ = Wallet.objects.get_or_create(user=ref_user)
        _credit(wallet, amt, meta={'type': 'referral', 'level': lvl, 'source_user': buyer.id, 'trigger': 'first_investment', 'base': str(amount_usd), 'pct': str(pct)})
        ReferralPayout.objects.create(referrer=ref_user, referee=buyer, level=lvl, amount_usd=amt)