from decimal import Decimal
from django.conf import settings

ECON = settings.ECONOMICS

USER_SHARE = Decimal(str(ECON['USER_WALLET_SHARE']))
WITHDRAW_TAX = Decimal(str(ECON['WITHDRAW_TAX']))
GLOBAL_POOL_CUT = Decimal(str(ECON['GLOBAL_POOL_CUT']))
REFERRAL_TIERS = [Decimal(str(x)) for x in ECON['REFERRAL_TIERS']]


def _schedule():
    mode = ECON.get('PASSIVE_MODE', 'UNCHANGED')
    if mode == 'CYCLIC_130':
        return ECON['PASSIVE_SCHEDULE_CYCLIC_130']
    return ECON['PASSIVE_SCHEDULE']


def daily_percent_for_day(day_index: int) -> Decimal:
    schedule = _schedule()
    # if cyclic 130, wrap around
    if ECON.get('PASSIVE_MODE') == 'CYCLIC_130':
        cycle_len = 130
        idx = ((day_index - 1) % cycle_len) + 1
    else:
        idx = day_index
    for start, end, rate in schedule:
        if start <= idx <= end:
            return Decimal(str(rate))
    return Decimal('0')


def compute_daily_earning_usd(day_index: int, deposit_usd: Decimal) -> dict:
    """
    Calculate daily passive earnings based on user's ACTUAL deposit amount.
    
    Args:
        day_index: Which day of the 90-day earning period (1-90)
        deposit_usd: User's actual credited deposit amount in USD
    
    Returns:
        dict with percent, gross, user share, platform hold, and global pool amounts
    """
    p = daily_percent_for_day(day_index)
    deposit_amount = Decimal(str(deposit_usd))
    
    # Calculate gross earning for this day based on ACTUAL deposit
    gross = deposit_amount * p
    
    user_gross_share = gross * USER_SHARE
    # Platform hold is 20% of gross (1 - USER_SHARE); global pool is tracked separately
    global_pool = gross * GLOBAL_POOL_CUT
    platform_hold = gross * (Decimal('1') - USER_SHARE)
    
    return {
        'percent': p,
        'gross_usd': gross.quantize(Decimal('0.01')),
        'user_share_usd': user_gross_share.quantize(Decimal('0.01')),
        'platform_hold_usd': platform_hold.quantize(Decimal('0.01')),
        'global_pool_usd': global_pool.quantize(Decimal('0.01')),
    }


def apply_withdraw_tax(amount_usd: Decimal) -> dict:
    tax = (amount_usd * WITHDRAW_TAX).quantize(Decimal('0.01'))
    net = (amount_usd - tax).quantize(Decimal('0.01'))
    return {'tax_usd': tax, 'net_usd': net}