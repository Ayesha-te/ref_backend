# Global Pool Fix - Deployment Guide

## 🎯 What Was Fixed

### Issue 1: Global Pool Never Collected ❌ → ✅
**Problem**: The `global_pool_usd` was calculated but never added to the GlobalPool balance.

**Fix**: Added collection logic in `run_daily_earnings.py` (lines 111-114):
```python
# Collect global pool cut
pool.balance_usd = (Decimal(pool.balance_usd) + metrics['global_pool_usd']).quantize(Decimal('0.01'))
pool.save()
total_global_pool_collected += metrics['global_pool_usd']
```

### Issue 2: Wrong Collection Rate ❌ → ✅
**Problem**: Rate was set to 10% instead of 0.5%

**Fix**: Changed `GLOBAL_POOL_CUT` in `core/settings.py` (line 193):
```python
'GLOBAL_POOL_CUT': float(os.environ.get('GLOBAL_POOL_CUT', '0.005')), # 0.5% for global pool
```

### Issue 3: No Visibility ❌ → ✅
**Problem**: No way to see how much is being collected

**Fix**: Added summary output showing:
- 🏦 Global Pool Collected (this run)
- 🏦 Global Pool Balance (total)

---

## 📦 Files Modified

1. **`apps/earnings/management/commands/run_daily_earnings.py`**
   - Line 61: Added `total_global_pool_collected` tracker
   - Lines 111-114: Added global pool collection
   - Lines 143-144: Added pool summary to output

2. **`core/settings.py`**
   - Line 193: Changed rate from 0.10 to 0.005

---

## 🚀 Deployment Steps

### Step 1: Commit Changes
```bash
git add .
git commit -m "Fix: Implement global pool collection (0.5% from passive earnings)

- Add global pool collection in run_daily_earnings command
- Change GLOBAL_POOL_CUT from 10% to 0.5%
- Add pool balance tracking to earnings summary
- Fixes issue where pool was calculated but never collected"
```

### Step 2: Push to Production
```bash
git push origin main
```

### Step 3: Verify Deployment on Render
1. Go to Render dashboard
2. Wait for deployment to complete
3. Check deployment logs for any errors

### Step 4: Test in Production
```bash
# SSH into Render shell
# Run the test script
python test_global_pool.py

# Check current pool balance
python manage.py shell -c "from apps.earnings.models_global_pool import GlobalPool; print(f'Pool Balance: ${GlobalPool.objects.get_or_create(pk=1)[0].balance_usd}')"
```

### Step 5: Run Daily Earnings (if needed)
```bash
# This will collect pool from today's earnings
python manage.py run_daily_earnings

# Check pool balance again (should increase)
python manage.py shell -c "from apps.earnings.models_global_pool import GlobalPool; print(f'Pool Balance: ${GlobalPool.objects.get_or_create(pk=1)[0].balance_usd}')"
```

---

## 🧪 Testing Locally (Optional)

### Test 1: Check Configuration
```bash
cd ref_backend
python test_global_pool.py
```

Expected output:
```
📋 Configuration:
  - GLOBAL_POOL_CUT: 0.005 (0.5%)

🧮 Test Calculation (Day 1):
  - Package: $100.00
  - Daily Rate: 2.0%
  - Gross Earning: $2.00
  - User Share (80%): $1.60
  - Platform Hold (20%): $0.40
  - Global Pool Cut (0.5%): $0.01
```

### Test 2: Run Daily Earnings
```bash
python manage.py run_daily_earnings
```

Expected output should include:
```
🏦 Global Pool Collected: $0.XX
🏦 Global Pool Balance: $X.XX
```

### Test 3: Test Distribution (Dry Run)
```bash
# Check what would be distributed
python manage.py shell -c "
from apps.earnings.models_global_pool import GlobalPool
from django.contrib.auth import get_user_model
pool = GlobalPool.objects.get_or_create(pk=1)[0]
users = get_user_model().objects.filter(is_approved=True).count()
print(f'Pool Balance: ${pool.balance_usd}')
print(f'Approved Users: {users}')
if users > 0:
    per_user = float(pool.balance_usd) / users
    net = per_user * 0.8  # After 20% tax
    print(f'Per User (gross): ${per_user:.2f}')
    print(f'Per User (net after 20% tax): ${net:.2f}')
"
```

---

## 📊 How It Works Now

### Daily Collection (Automated)
```
Every day at 00:01 UTC:
1. Scheduler runs run_daily_earnings command
2. For each approved user with deposits:
   - Calculate daily earning (e.g., 2% of $100 = $2)
   - User gets 80% = $1.60 (income_usd)
   - Platform holds 20% = $0.40 (hold_usd)
   - Global pool gets 0.5% = $0.01 (pool.balance_usd) ✅ NOW WORKING
3. Pool balance accumulates daily
```

### Monday Distribution (Automated)
```
Every Monday at 00:00 UTC:
1. Cron runs distribute_global_pool command
2. Get total pool balance (e.g., $10.00)
3. Count approved users (e.g., 20 users)
4. Calculate per user: $10.00 / 20 = $0.50 gross
5. Apply 20% tax: $0.50 * 0.8 = $0.40 net
6. Credit $0.40 to each user's available_usd
7. Create transaction records
8. Reset pool balance to $0
```

---

## 🔍 Monitoring

### Check Pool Balance Anytime
```bash
python manage.py shell -c "from apps.earnings.models_global_pool import GlobalPool; print(f'${GlobalPool.objects.get_or_create(pk=1)[0].balance_usd}')"
```

### Check Distribution History
```bash
python manage.py shell -c "from apps.earnings.models_global_pool import GlobalPoolPayout; [print(f'{p.distributed_on}: ${p.amount_usd} to {p.meta.get(\"count\")} users') for p in GlobalPoolPayout.objects.all().order_by('-distributed_on')[:5]]"
```

### Check User Received Payout
```bash
python manage.py shell -c "
from apps.wallets.models import Transaction
from django.contrib.auth import get_user_model
user = get_user_model().objects.get(email='sardarlaeiq3@gmail.com')
payouts = Transaction.objects.filter(wallet__user=user, meta__type='global_pool_payout')
print(f'Total Payouts: {payouts.count()}')
for t in payouts:
    print(f'{t.created_at}: ${t.amount_usd}')
"
```

---

## ⚠️ Important Notes

### Collection Source
**Current**: Collects 0.5% from ALL users' daily passive earnings
**Your Requirement**: Collect 0.5% from Monday signups only

If you want to collect ONLY from Monday signups, we need additional changes:
1. Track signup day of week in User model
2. Modify collection logic to filter by Monday signups
3. Or: Move collection from passive earnings to deposit processing

### Rate Verification
- Changed from 10% to 0.5%
- This is a 20x reduction
- Verify this is the correct rate for your business model

### Distribution Timing
- Currently: Every Monday at 00:00 UTC
- Collection: Daily at 00:01 UTC
- First distribution will happen next Monday after deployment

---

## 🐛 Troubleshooting

### Pool Balance Not Increasing
1. Check if daily earnings are running:
   ```bash
   python manage.py shell -c "from apps.earnings.models import PassiveEarning; print(PassiveEarning.objects.latest('created_at'))"
   ```

2. Check if users have deposits:
   ```bash
   python manage.py shell -c "from apps.wallets.models import DepositRequest; print(DepositRequest.objects.filter(status='CREDITED').exclude(tx_id='SIGNUP-INIT').count())"
   ```

3. Check scheduler status:
   ```bash
   python check_scheduler.py
   ```

### Distribution Not Working
1. Check cron is configured:
   ```bash
   python manage.py crontab show
   ```

2. Manually test distribution:
   ```bash
   python manage.py distribute_global_pool
   ```

3. Check pool has balance:
   ```bash
   python manage.py shell -c "from apps.earnings.models_global_pool import GlobalPool; print(GlobalPool.objects.get_or_create(pk=1)[0].balance_usd)"
   ```

---

## ✅ Success Criteria

After deployment, you should see:
- ✅ Pool balance increases daily (check after daily earnings run)
- ✅ Daily earnings summary shows "Global Pool Collected"
- ✅ Monday distributions credit users with pool payouts
- ✅ Pool balance resets to $0 after Monday distribution
- ✅ Transaction records show `type='global_pool_payout'`

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review deployment logs on Render
3. Run `test_global_pool.py` to verify configuration
4. Check database directly for pool balance and transactions

---

**Deployment Date**: _[Add date when deployed]_
**Deployed By**: _[Add your name]_
**Production URL**: https://nexocart-redline-dash.onrender.com