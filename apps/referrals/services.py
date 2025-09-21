from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet, Transaction
from .models import ReferralPayout, ReferralMilestoneProgress, ReferralMilestoneAward

REFERRAL_TIERS = [Decimal(str(x)) for x in settings.ECONOMICS['REFERRAL_TIERS']]
# Base amount considered as the "joining earning" for referral payouts
PACKAGE_USD = Decimal('5.00')

# Milestone rewards by target direct-count
MILESTONE_AMOUNTS = {
    10: Decimal('5.00'),
    30: Decimal('30.00'),
    50: Decimal('60.00'),
    100: Decimal('150.00'),
}

User = get_user_model()


def _credit(wallet: Wallet, amount: Decimal, meta: dict):
    wallet.available_usd = (Decimal(wallet.available_usd) + amount).quantize(Decimal('0.01'))
    wallet.save()
    Transaction.objects.create(wallet=wallet, type=Transaction.CREDIT, amount_usd=amount, meta=meta)


def _l1_gate_okay(user: User) -> bool:
    """L1 referral only if referrer has >=10 current-cycle directs (no earnings before 10)."""
    # Count direct referrals since last award boundary (we track with progress)
    try:
        prog = user.referral_milestone_progress
    except ReferralMilestoneProgress.DoesNotExist:
        return False
    # L1 gate opens at 10 directs in current cycle
    return prog.current_count >= 10 or prog.current_target() > 10


def _process_milestones(referrer: User) -> None:
    """Increment direct count and pay milestone if target hit; then advance stage and reset count."""
    prog, _ = ReferralMilestoneProgress.objects.get_or_create(user=referrer)
    prog.current_count += 1
    # If hit target, pay award and advance
    target = prog.current_target()
    if prog.current_count >= target:
        amt = MILESTONE_AMOUNTS.get(target, Decimal('0'))
        if amt > 0:
            wallet, _ = Wallet.objects.get_or_create(user=referrer)
            _credit(wallet, amt, meta={'type': 'milestone', 'target': target})
            ReferralMilestoneAward.objects.create(user=referrer, target=target, amount_usd=amt)
        prog.advance_stage()
    prog.save()


def pay_on_package_purchase(buyer: User):
    """Distribute referral rewards when buyer is approved (joins).
    - L1: 6% (no gate)
    - L2: 3% (no gate)
    - L3: 1% (no gate)
    - Milestones: when a direct referral joins, increment L1 referrer milestone and pay [10:$5, 30:$30, 50:$60, 100:$150], then advance stage.
    """
    upline = []
    cur = buyer.referred_by
    level = 1
    while cur and level <= 3:
        upline.append((cur, level))
        cur = cur.referred_by
        level += 1

    # Milestone progression for L1 referrer only
    if upline:
        ref_user, lvl = upline[0]
        if lvl == 1:
            _process_milestones(ref_user)

    # Payouts without gates
    for ref_user, lvl in upline:
        pct = REFERRAL_TIERS[lvl-1]
        amt = (PACKAGE_USD * pct).quantize(Decimal('0.01'))
        wallet, _ = Wallet.objects.get_or_create(user=ref_user)
        _credit(wallet, amt, meta={'type': 'referral', 'level': lvl, 'source_user': buyer.id, 'trigger': 'join'})
        ReferralPayout.objects.create(referrer=ref_user, referee=buyer, level=lvl, amount_usd=amt)


def pay_on_first_investment(buyer: User, amount_usd: Decimal):
    """Distribute referral rewards on buyer's first investment (first credited deposit not including signup-initial).
    Uses same tiers: L1=6%, L2=3%, L3=1%.
    """
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
        _credit(wallet, amt, meta={'type': 'referral', 'level': lvl, 'source_user': buyer.id, 'trigger': 'first_investment'})
        ReferralPayout.objects.create(referrer=ref_user, referee=buyer, level=lvl, amount_usd=amt)