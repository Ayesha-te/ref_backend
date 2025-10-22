# Signup Fee Passive Income Implementation Guide

## Overview
This implementation integrates signup fees into the passive income calculation system. When a user's signup is approved, their signup fee is automatically credited as a deposit, triggering passive income generation according to the platform's schedule.

## Changes Made

### 1. **Modified: `apps/accounts/views.py` - `admin_signup_proof_action` endpoint**

**What Changed:**
- When a signup proof is approved, the endpoint now creates a credited DepositRequest with `tx_id='SIGNUP-INIT'`
- The deposit amount is automatically credited to the user's wallet
- The credit is split according to economics settings:
  - 80% goes to `wallet.available_usd` (USER_WALLET_SHARE)
  - 20% goes to `wallet.hold_usd` (platform hold)
  - 0.5% is added to global pool (GLOBAL_POOL_CUT)

**Implementation Details:**
```python
# When signup proof is APPROVED:
1. Convert signup_proof.amount_pkr to USD using admin FX rate
2. Check if SIGNUP-INIT deposit already exists (prevent duplicates)
3. Create DepositRequest with:
   - amount_pkr from SignupProof
   - amount_usd (calculated)
   - tx_id = 'SIGNUP-INIT'
   - status = 'CREDITED'
   - processed_at = now()
4. Update Wallet:
   - available_usd += user_share (80%)
   - hold_usd += platform_hold (20%)
5. Record in GlobalPool:
   - balance_usd += global_pool (0.5%)
6. Create Transaction record with metadata for tracking
```

**Key Features:**
- Idempotent: Checks if deposit already exists before creating
- Follows same pattern as `admin_deposit_action` for consistency
- Marks transaction with `'source': 'signup-initial'` to distinguish from regular deposits
- Includes proof_image link for audit trail

### 2. **Modified: `core/middleware.py` - `AutoDailyEarningsMiddleware`**

**What Changed:**
- Passive income generation now includes SIGNUP-INIT deposits in calculations
- Uses accumulated total of all credited deposits (not just the first one)
- Properly handles multiple deposits from same user

**Implementation Details:**

**Change 1: Include SIGNUP-INIT in first deposit lookup**
```python
# BEFORE: Excluded SIGNUP-INIT deposits
first_dep = DepositRequest.objects.filter(
    user=u, 
    status='CREDITED'
).exclude(tx_id='SIGNUP-INIT').order_by('processed_at', 'created_at').first()

# AFTER: Includes SIGNUP-INIT deposits
first_dep = DepositRequest.objects.filter(
    user=u, 
    status='CREDITED'
).order_by('processed_at', 'created_at').first()
```

**Change 2: Use total accumulated deposits for passive income**
```python
# Get total of ALL credited deposits (signup fee + any additional deposits)
total_deposits = DepositRequest.objects.filter(
    user=u,
    status='CREDITED'
).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')

# Use total_deposits for passive income calculation
metrics = compute_daily_earning_usd(current_day, total_deposits)
```

**Key Benefits:**
- When a user makes additional deposits after signup, passive income increases automatically
- Day counter (day_index) continues from where it left off
- No need to restart passive income calculation for new deposits

### 3. **Modified: `apps/accounts/signals.py` - Removed duplicate deposit creation**

**What Changed:**
- Removed the old deposit creation logic from the `on_user_approved` signal handler
- Deposit creation is now exclusively handled in `admin_signup_proof_action` view
- Prevents duplicate SIGNUP-INIT deposits

**Why:**
- The old implementation in signals.py didn't properly credit the deposit to wallet
- The new implementation in views.py follows the standard crediting process
- Single responsibility principle: view handles signup proof logic

**Note:** The signal handler still handles:
1. Referral payouts on joining
2. Monday joining global pool contribution (0.5% from Monday signups)

## How It Works - User Flow

### Step 1: User Signup
```
User submits signup with proof of payment
↓
Amount is stored in SignupProof model
↓
Status = 'PENDING' (awaiting admin approval)
```

### Step 2: Admin Approves Signup
```
Admin approves signup proof in admin panel
↓
Endpoint: admin_signup_proof_action(action='APPROVE')
↓
Creates DepositRequest:
  - tx_id = 'SIGNUP-INIT'
  - status = 'CREDITED'
  - amount_usd from SignupProof.amount_pkr
↓
Credits wallet:
  - available_usd += 80% of deposit
  - hold_usd += 20% of deposit
↓
Updates global_pool:
  - balance_usd += 0.5% of deposit
```

### Step 3: Passive Income Generation
```
Daily (via middleware trigger):
↓
For each approved user:
  - Get first credited deposit (including SIGNUP-INIT)
  - Calculate days since deposit
  - Check if >= 1 day (Day 0 protection)
  - Get TOTAL of all credited deposits
  - Calculate daily passive income:
    - daily_percent based on day_index and schedule
    - gross = total_deposits * daily_percent
    - passive_income = gross * 0.80 (user share)
  - Create PassiveEarning record
  - Credit income_usd to wallet
  - Create Transaction record for tracking
```

### Step 4: Additional Deposit
```
User makes additional investment (normal deposit process)
↓
Admin credits additional deposit
↓
Next day's passive income calculation:
  - Uses NEW total: signup_fee + new_deposit
  - Continues from day_index + 1
  - Higher passive income for remaining days
```

## Economics & Calculations

### Passive Income Schedule
Default 90-day plan (UNCHANGED mode):
```
Days 1-10:   0.4% daily
Days 11-20:  0.6% daily
Days 21-30:  0.8% daily
Days 31-60:  1.0% daily
Days 61-90:  1.3% daily
```

### Example Calculation
```
User signs up with: 5000 PKR
Converted to USD (at 280 PKR/USD): $17.86

Wallet credits:
- available_usd: $17.86 * 0.80 = $14.29
- hold_usd: $17.86 * 0.20 = $3.57

Global pool:
- balance += $17.86 * 0.005 = $0.09

Day 1 passive income:
- daily_percent = 0.004 (0.4%)
- gross = $17.86 * 0.004 = $0.071
- passive_income = $0.071 * 0.80 = $0.057
- platform_hold = $0.071 * 0.20 = $0.014

After 5 additional days at higher tier:
Day 6-10: same rate
Day 11 (0.6% tier):
- gross = $17.86 * 0.006 = $0.107
- passive_income = $0.107 * 0.80 = $0.086

If user deposits $20 more (another $7.14 USD):
New total_deposits = $25.00
Day 12:
- daily_percent = 0.006 (0.6%)
- gross = $25.00 * 0.006 = $0.15
- passive_income = $0.15 * 0.80 = $0.12
```

## Key Features

### Day 0 Protection
- Passive income does NOT generate on the same day as deposit
- User must wait at least 1 full day after deposit before earning
- Prevents gaming/abuse

### Cumulative Deposits
- All credited deposits are summed for passive income calculation
- Day counter continues regardless of new deposits
- New deposits immediately increase daily passive income amount

### Idempotency
- Signup deposit creation checks for existing SIGNUP-INIT records
- Prevents duplicate deposits even if endpoint is called multiple times
- Safe to retry on network failures

### Automatic Global Pool
- On Mondays, 0.5% of all signup fees credited on that Monday are collected
- Pool is distributed equally among all active users
- Separate from passive income calculation

## Configuration

### Environment Variables
```bash
# Admin FX rate (PKR to USD)
ADMIN_USD_TO_PKR=280

# Signup fee in PKR (used as fallback, normally from SignupProof)
SIGNUP_FEE_PKR=1410

# Wallet share of deposits
USER_WALLET_SHARE=0.80

# Withdraw tax
WITHDRAW_TAX=0.20

# Global pool cut
GLOBAL_POOL_CUT=0.005

# Passive income mode
PASSIVE_MODE=UNCHANGED  # or CYCLIC_130
```

### Settings
In `core/settings.py`:
```python
ECONOMICS = {
    'PASSIVE_MODE': 'UNCHANGED',  # or 'CYCLIC_130'
    'PASSIVE_SCHEDULE': [
        (1, 10, 0.004),    # 0.4%
        (11, 20, 0.006),   # 0.6%
        (21, 30, 0.008),   # 0.8%
        (31, 60, 0.010),   # 1.0%
        (61, 90, 0.013),   # 1.3%
    ],
    'USER_WALLET_SHARE': 0.80,
    'WITHDRAW_TAX': 0.20,
    'GLOBAL_POOL_CUT': 0.005,
}
```

## Testing the Implementation

### 1. Test Signup Approval
```bash
# Via admin API
POST /api/accounts/admin/signup-proofs/{id}/action/
{
  "action": "APPROVE"
}

# Check results:
# 1. DepositRequest created with tx_id='SIGNUP-INIT'
# 2. Wallet available_usd increased
# 3. Transaction recorded
```

### 2. Test Passive Income Generation
```bash
# Manual trigger (if enabled)
curl http://localhost:8000/api/earnings/trigger-daily/

# Or wait for scheduled daily earnings

# Check:
# 1. PassiveEarning records created
# 2. Wallet income_usd increased
# 3. Correct daily percentage applied
```

### 3. Test Multiple Deposits
```bash
# Create additional deposit
POST /api/wallets/deposits/
{
  "amount_pkr": "5000",
  "tx_id": "txn_123"
}

# Admin credits it
POST /api/wallets/admin/deposits/{id}/
{
  "action": "CREDIT"
}

# Next day's passive income should use:
# total = signup_deposit + new_deposit

# Check:
# 1. PassiveEarning for next day uses higher amount
# 2. Day index continues from previous day
```

## Troubleshooting

### Issue: Passive income not generating after signup approval
**Solution:** 
1. Check DepositRequest exists with status='CREDITED'
2. Verify current date is > deposit_date (Day 0 protection)
3. Check middleware is running (if not using cron)
4. Verify user has is_approved=True and is_active=True

### Issue: Duplicate SIGNUP-INIT deposits
**Solution:**
1. The endpoint checks for existing deposits
2. If duplicates exist, delete extras manually via admin
3. Ensure code was updated to handle idempotency

### Issue: Wallet not credited after signup approval
**Solution:**
1. Verify admin_signup_proof_action is being called
2. Check user has wallet created (auto-created in view)
3. Verify settings.ECONOMICS values are correct
4. Check for exceptions in transaction creation

## Rollback Plan

If issues arise:

1. **To disable signup fee deposits:**
   - Revert changes to `admin_signup_proof_action` in views.py
   - Restore old signal handler code in signals.py

2. **To exclude signup fees from passive income:**
   - Add back `.exclude(tx_id='SIGNUP-INIT')` in middleware.py
   - Passive income will only calculate from subsequent deposits

3. **Database cleanup (if needed):**
```sql
-- Delete all SIGNUP-INIT deposits created after a date
DELETE FROM wallets_depositrequest 
WHERE tx_id='SIGNUP-INIT' 
AND created_at > '2024-01-01';

-- Reset daily earnings state
DELETE FROM earnings_dailyearningsstate;

-- Reset passive earnings (if needed)
DELETE FROM earnings_passiveearning 
WHERE created_at > '2024-01-01';
```

## Performance Considerations

- Middleware runs on every request (daily check)
- Uses `select_for_update` to prevent race conditions
- Aggregation query sums all deposits per user (O(n) where n=deposits per user)
- For systems with many users/deposits, consider:
  - Caching deposit totals
  - Batch processing via management command
  - Database indexing on DepositRequest(user, status)

## Files Modified

1. `/ref_backend/apps/accounts/views.py` - Added signup deposit creation logic
2. `/ref_backend/core/middleware.py` - Modified passive income calculation
3. `/ref_backend/apps/accounts/signals.py` - Removed duplicate deposit creation

## Migration Notes

- No database schema changes required
- All changes use existing models and fields
- Backward compatible with existing deposits
- Safe to deploy to production

---

**Last Updated:** 2024
**Status:** Implementation Complete
**Next Steps:** Deploy to production, monitor for 24 hours