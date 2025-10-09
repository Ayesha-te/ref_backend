# Actual Deposit Amount Bonus Fix

## Problem Summary

Previously, the referral bonus system was calculating bonuses based on a **hardcoded `SIGNUP_FEE_PKR` value (1410 PKR)**, regardless of the actual deposit amount.

### Example of the Issue:
- User A deposits **1410 PKR** → Referrer gets **Rs84** (6% of 1410)
- User B deposits **5410 PKR** → Referrer gets **Rs84** (6% of 1410) ❌ **WRONG!**
- User B should generate **Rs325** (6% of 5410) ✅ **CORRECT!**

## Root Cause

The `pay_on_package_purchase()` function in `apps/referrals/services.py` was using:
```python
signup_fee_pkr = Decimal(str(settings.SIGNUP_FEE_PKR))  # Always 1410
```

This meant all bonuses were calculated from 1410 PKR, not the actual deposit amount.

## Solution Implemented

### Changes Made:

#### 1. **Modified `pay_on_package_purchase()` function** (`apps/referrals/services.py`)
   - Added `signup_amount_pkr` parameter to accept actual deposit amount
   - Falls back to `settings.SIGNUP_FEE_PKR` if no amount is provided
   - Now calculates bonuses based on actual deposit: `actual_amount × 6%`

#### 2. **Updated Signal** (`apps/accounts/signals.py`)
   - Retrieves actual signup amount from `SignupProof` model
   - Passes actual amount to `pay_on_package_purchase()`
   - Also updates Monday contribution (0.5%) to use actual amount
   - Also updates initial deposit record to use actual amount

### How It Works Now:

1. **User submits signup proof** with their deposit amount (e.g., 5410 PKR)
2. **Admin approves user** by setting `is_approved=True`
3. **Signal fires** and:
   - Retrieves the actual deposit amount from `SignupProof`
   - Calculates referral bonuses based on **actual amount**:
     - L1: 6% of actual deposit
     - L2: 3% of actual deposit
     - L3: 1% of actual deposit
   - Creates Monday contribution (0.5% of actual deposit if Monday)
   - Creates initial deposit record with actual amount

### Example Calculations:

#### Deposit: 1410 PKR
- Exchange Rate: 280 PKR/USD
- USD Amount: 1410 ÷ 280 = $5.04 USD
- L1 Bonus: $5.04 × 6% = $0.30 USD ≈ **Rs84 PKR**

#### Deposit: 5410 PKR
- Exchange Rate: 280 PKR/USD
- USD Amount: 5410 ÷ 280 = $19.32 USD
- L1 Bonus: $19.32 × 6% = $1.16 USD ≈ **Rs325 PKR**

## Files Modified

1. **`apps/referrals/services.py`**
   - Modified `pay_on_package_purchase()` to accept `signup_amount_pkr` parameter
   - Added actual amount to transaction metadata for tracking

2. **`apps/accounts/signals.py`**
   - Updated `on_user_approved` signal to retrieve actual signup amount
   - Passes actual amount to all relevant functions
   - Updated Monday contribution calculation
   - Updated initial deposit creation

## Deployment Steps

### 1. **Commit and Push Changes**
```bash
git add .
git commit -m "Fix: Calculate referral bonuses based on actual deposit amount"
git push origin main
```

### 2. **Render Auto-Deploy**
- Render will automatically detect the push and redeploy
- No migration needed (no database schema changes)

### 3. **Verify on Production**
After deployment, test with a new user:
1. Create a new user with a signup proof (e.g., 5410 PKR)
2. Approve the user in admin panel
3. Check the referrer's wallet to verify correct bonus amount
4. Expected: Rs325 (6% of 5410) instead of Rs84

### 4. **Run Diagnostic Script** (Optional)
To check existing bonuses and identify any issues:
```bash
# In Render Shell
python check_user_deposits.py
```

## Important Notes

### ✅ What This Fix Does:
- Calculates referral bonuses based on **actual deposit amount**
- Works for any deposit amount (1410, 5410, 10000, etc.)
- Maintains the same percentage rates (L1=6%, L2=3%, L3=1%)
- Updates Monday contribution to use actual amount
- Updates initial deposit record to use actual amount

### ⚠️ What This Fix Does NOT Do:
- Does **NOT** retroactively fix existing bonuses
- Does **NOT** remove duplicate bonuses (use `cleanup_duplicate_bonuses.py` for that)
- Only affects **new approvals** after deployment

### 🔄 Backward Compatibility:
- If no `SignupProof` exists, falls back to `settings.SIGNUP_FEE_PKR`
- Existing code that calls `pay_on_package_purchase()` without parameters still works
- No breaking changes to existing functionality

## Testing Checklist

After deployment, verify:

- [ ] New user with 1410 PKR deposit generates Rs84 bonus
- [ ] New user with 5410 PKR deposit generates Rs325 bonus
- [ ] L2 and L3 bonuses also calculated correctly
- [ ] Monday contribution uses actual amount
- [ ] Initial deposit record shows actual amount
- [ ] No duplicate bonuses created (signal protection still works)

## Rollback Plan

If issues occur, you can rollback by:
1. Reverting the commit: `git revert HEAD`
2. Pushing: `git push origin main`
3. Render will auto-deploy the previous version

## Related Issues

This fix addresses:
- ✅ Issue: 5410 PKR deposit only generating Rs84 bonus
- ✅ Issue: All bonuses calculated from hardcoded 1410 PKR
- ✅ Enhancement: Support for variable deposit amounts

This fix works together with:
- ✅ Duplicate bonus prevention (already implemented)
- ✅ Database unique constraint (already implemented)
- ✅ Cleanup scripts (for removing existing duplicates)

## Questions?

If you encounter any issues:
1. Check Render logs for errors
2. Run `check_user_deposits.py` to diagnose
3. Verify `SignupProof` records exist for users
4. Check that `amount_pkr` field is populated correctly