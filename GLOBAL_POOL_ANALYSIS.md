# Global Pool System Analysis & Fix

## 🔍 Current Implementation Issues

### Issue 1: Global Pool is NEVER Collected
**Location**: `apps/earnings/management/commands/run_daily_earnings.py`

**Problem**: 
- Line 92: `metrics = compute_daily_earning_usd(current_day)` calculates `global_pool_usd`
- Lines 106-108: Only `income_usd` and `hold_usd` are updated
- **The `global_pool_usd` value is calculated but NEVER added to GlobalPool.balance_usd**

**Result**: GlobalPool balance stays at $0, so Monday distributions have nothing to distribute.

### Issue 2: Wrong Collection Source & Rate
**Current**: 10% from daily passive earnings (all users, all days)
**Required**: 0.5% from Monday signups only

**Settings**: `GLOBAL_POOL_CUT = 0.10` (10%) in `core/settings.py` line 193

---

## ✅ Required Changes

### Change 1: Fix Collection in Daily Earnings
**File**: `apps/earnings/management/commands/run_daily_earnings.py`

Add after line 108 (after `wallet.save()`):
```python
# Collect global pool cut
pool.balance_usd = (Decimal(pool.balance_usd) + metrics['global_pool_usd']).quantize(Decimal('0.01'))
pool.save()
```

### Change 2: Change Collection Rate to 0.5%
**File**: `core/settings.py` line 193

Change from:
```python
'GLOBAL_POOL_CUT': float(os.getenv('GLOBAL_POOL_CUT', '0.10')),  # 10%
```

To:
```python
'GLOBAL_POOL_CUT': float(os.getenv('GLOBAL_POOL_CUT', '0.005')),  # 0.5%
```

### Change 3: Collect Only from Monday Signups (Optional - Complex)
**Current**: Collects from all daily passive earnings
**Required**: Collect only from users who signed up on Monday

This requires:
1. Track signup day of week in User model
2. Modify `run_daily_earnings.py` to only collect pool from Monday signups
3. Or: Create separate collection logic that runs on deposits instead of passive earnings

---

## 🎯 Recommended Approach

### Option A: Simple Fix (Recommended)
**What**: Fix the collection bug + change rate to 0.5%
**Pros**: 
- Quick to implement (2 small changes)
- Works with existing architecture
- Collects from all passive earnings (fair distribution)

**Cons**: 
- Collects from all users, not just Monday signups
- Different from stated requirement

### Option B: Full Requirement Implementation
**What**: Collect 0.5% only from Monday signups' deposits
**Pros**: 
- Matches exact requirement
- More targeted collection

**Cons**: 
- Requires tracking signup day
- More complex logic
- Need to modify deposit processing instead of passive earnings

---

## 📊 Current System Flow

### Daily Passive Earnings (Automated)
```
1. Scheduler runs daily at 00:01 UTC
2. For each approved user with deposits:
   - Calculate daily earning (e.g., 2% of $100 = $2)
   - User gets 80% = $1.60 (added to income_usd)
   - Platform holds 20% = $0.40 (added to hold_usd)
   - Global pool should get 10% = $0.20 (CURRENTLY NOT COLLECTED)
3. Create PassiveEarning record
4. Create Transaction record
```

### Monday Distribution (Automated)
```
1. Cron runs every Monday at 00:00 UTC
2. Get GlobalPool balance (currently always $0)
3. Divide equally among all approved users
4. Apply 20% withdrawal tax
5. Credit net amount to each user's available_usd
6. Reset pool to $0
```

---

## 🚀 Implementation Steps

### Step 1: Apply Simple Fix
1. Fix collection in `run_daily_earnings.py`
2. Change rate to 0.5% in `settings.py`
3. Test locally
4. Deploy to production

### Step 2: Verify
1. Check GlobalPool balance increases daily
2. Wait for Monday distribution
3. Verify users receive pool payouts

### Step 3: (Optional) Implement Monday-Only Logic
If you want to collect ONLY from Monday signups:
1. Add `signup_day_of_week` field to User model
2. Modify collection logic to filter by Monday signups
3. Or: Move collection from passive earnings to deposit processing

---

## 📝 Files to Modify

1. **`apps/earnings/management/commands/run_daily_earnings.py`** (lines 108-109)
   - Add global pool collection

2. **`core/settings.py`** (line 193)
   - Change rate from 0.10 to 0.005

3. **(Optional) User model** 
   - Add signup day tracking for Monday-only collection

---

## ⚠️ Important Notes

1. **Current Balance**: GlobalPool.balance_usd is likely $0 because collection was never implemented
2. **Distribution Works**: The Monday distribution command works correctly, just has nothing to distribute
3. **Rate Mismatch**: 10% vs 0.5% is a huge difference - verify which is correct
4. **Source Mismatch**: Passive earnings vs Monday signups - clarify requirement

---

## 🧪 Testing Commands

```bash
# Check current global pool balance
python manage.py shell -c "from apps.earnings.models_global_pool import GlobalPool; print(GlobalPool.objects.get_or_create(pk=1)[0].balance_usd)"

# Run daily earnings (after fix)
python manage.py run_daily_earnings

# Check pool balance again (should increase)
python manage.py shell -c "from apps.earnings.models_global_pool import GlobalPool; print(GlobalPool.objects.get_or_create(pk=1)[0].balance_usd)"

# Test distribution (dry run)
python manage.py distribute_global_pool

# Check distribution history
python manage.py shell -c "from apps.earnings.models_global_pool import GlobalPoolPayout; print(GlobalPoolPayout.objects.all().values())"
```

---

## 🎯 Decision Needed

**Please clarify:**
1. ✅ Should we collect 0.5% or 10%?
2. ✅ Should we collect from ALL users' passive earnings OR only Monday signups?
3. ✅ Should we collect from passive earnings OR from deposits?

**Current recommendation**: 
- Fix the collection bug (it's definitely broken)
- Use 0.5% rate (as you mentioned)
- Collect from all passive earnings (simpler, fairer)
- Can change to Monday-only later if needed