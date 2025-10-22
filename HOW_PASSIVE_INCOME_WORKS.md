# How Passive Income Works - Complete Guide

## 🎯 System Overview

**ONLY ONE SYSTEM IS ACTIVE:** Middleware (AutoDailyEarningsMiddleware)

✅ **Scheduler:** DISABLED (to prevent double earnings)  
✅ **Middleware:** ENABLED (handles all passive income generation)

---

## 🔄 How It Works

### **Step-by-Step Flow:**

```
1. User deposits money (e.g., 5,410 PKR)
   ↓
2. Admin approves deposit → Status = "CREDITED"
   ↓
3. Deposit timestamp recorded (e.g., Jan 10, 2025 at 8:00 PM)
   ↓
4. Day 0 (Deposit Day) - NO EARNINGS
   ├─ Any user visits website → Middleware checks
   ├─ Calculates: days_since_deposit = 0
   └─ ❌ Skips: "Deposit was made today (day 0)"
   ↓
5. Day 1 (Next Day) - FIRST EARNINGS
   ├─ 24+ hours have passed
   ├─ Any user visits website → Middleware triggers
   ├─ Calculates: days_since_deposit = 1
   ├─ Checks: Has user received Day 1 earnings? NO
   ├─ Generates: 0.4% of deposit
   └─ ✅ Credits to wallet
   ↓
6. Day 2, 3, 4... up to Day 90
   └─ Same process repeats daily
```

---

## 🛡️ Protection Against Double Earnings

### **Three Layers of Protection:**

#### **1. DailyEarningsState (Primary Protection)**
```python
# Singleton model tracks last processed date
DailyEarningsState.objects.get(pk=1)
├─ last_processed_date: 2025-01-10
└─ If today = 2025-01-10 → Skip (already processed)
```

**How it works:**
- Middleware checks: "Have we processed today's earnings?"
- If YES → Skip entire processing
- If NO → Process all users, then update date
- **Result:** Only processes ONCE per day, no matter how many requests

#### **2. Database Locking (Race Condition Protection)**
```python
# select_for_update prevents concurrent processing
with transaction.atomic():
    state = DailyEarningsState.objects.select_for_update(nowait=True).get(pk=1)
```

**How it works:**
- First request locks the database row
- Other concurrent requests get "locked" error and skip
- **Result:** Only ONE process can run at a time

#### **3. Unique Constraint (Duplicate Prevention)**
```python
class PassiveEarning(models.Model):
    class Meta:
        unique_together = ("user", "day_index")
```

**How it works:**
- Database prevents duplicate (user, day_index) combinations
- If Day 1 already exists for user → Database error
- **Result:** Impossible to create duplicate earnings for same day

---

## 📊 Real Example: Ahmed's Journey

### **Deposit Details:**
- Amount: 5,410 PKR (≈ $19.32 USD)
- Date: January 10, 2025 at 8:00 PM
- Status: CREDITED

---

### **Day 0 - January 10, 2025 (Deposit Day)**

```
8:00 PM - Ahmed deposits 5,410 PKR
├─ Admin approves → Status = "CREDITED"
├─ Timestamp: 2025-01-10 20:00:00 UTC
└─ Wallet balance: $19.32 USD

9:00 PM - User visits website
├─ Middleware triggers
├─ Checks DailyEarningsState:
│   ├─ last_processed_date: 2025-01-09
│   └─ Today: 2025-01-10 → Need to process
├─ Locks database row (prevents concurrent processing)
├─ Finds Ahmed has credited deposit
├─ Calculates: days_since_deposit = 0
├─ Logs: "⚠️ Skipping Ahmed: Deposit was made today (day 0)"
├─ Updates DailyEarningsState:
│   └─ last_processed_date: 2025-01-10
└─ ❌ NO earnings generated

10:00 PM - Another user visits website
├─ Middleware triggers
├─ Checks DailyEarningsState:
│   ├─ last_processed_date: 2025-01-10
│   └─ Today: 2025-01-10 → Already processed
└─ ❌ Skips entire processing (already done today)

Ahmed's earnings: $0.00
```

---

### **Day 1 - January 11, 2025 (First Earnings Day)**

```
8:00 AM - First user visits website
├─ Middleware triggers
├─ Checks DailyEarningsState:
│   ├─ last_processed_date: 2025-01-10
│   └─ Today: 2025-01-11 → Need to process
├─ Locks database row
├─ Finds Ahmed has credited deposit
├─ Calculates: days_since_deposit = 1 (24+ hours passed)
├─ Checks PassiveEarning table:
│   └─ Has Ahmed received Day 1 earnings? NO
├─ Calculates earnings:
│   ├─ Day 1 rate: 0.4% (Days 1-10 tier)
│   ├─ Deposit: $19.32 USD
│   ├─ Daily earning: $19.32 × 0.4% = $0.077 USD
│   ├─ User share (80%): $0.062 USD
│   └─ Platform hold (20%): $0.015 USD
├─ Creates PassiveEarning record:
│   ├─ user: Ahmed
│   ├─ day_index: 1
│   ├─ percent: 0.004
│   └─ amount_usd: 0.062
├─ Updates wallet:
│   ├─ income_usd: $0.00 → $0.062 USD
│   └─ hold_usd: $0.00 → $0.015 USD
├─ Creates Transaction record:
│   ├─ type: CREDIT
│   ├─ amount_usd: 0.062
│   └─ meta: {'type': 'passive', 'day_index': 1}
├─ Updates DailyEarningsState:
│   └─ last_processed_date: 2025-01-11
└─ ✅ Logs: "✅ Credited Ahmed day 1: $0.062 USD (0.4%)"

9:00 AM - Another user visits website
├─ Middleware triggers
├─ Checks DailyEarningsState:
│   ├─ last_processed_date: 2025-01-11
│   └─ Today: 2025-01-11 → Already processed
└─ ❌ Skips (already done today)

Ahmed's earnings: $0.062 USD (≈ 17.36 PKR)
```

---

### **Day 2 - January 12, 2025**

```
Any time during the day - User visits website
├─ Middleware triggers
├─ Checks: last_processed_date = 2025-01-11, today = 2025-01-12
├─ Processes Ahmed:
│   ├─ days_since_deposit = 2
│   ├─ Day 2 rate: 0.4%
│   ├─ Creates PassiveEarning: day_index=2, amount=$0.062
│   └─ Updates wallet: income_usd = $0.124 USD
└─ Updates: last_processed_date = 2025-01-12

Ahmed's total earnings: $0.124 USD (≈ 34.72 PKR)
```

---

### **Day 11 - January 21, 2025 (Rate Increases)**

```
Middleware processes:
├─ days_since_deposit = 11
├─ Day 11 rate: 0.6% (Days 11-20 tier) ⬆️
├─ Daily earning: $19.32 × 0.6% = $0.116 USD
├─ User share: $0.093 USD
└─ ✅ Higher earnings!

Ahmed's total earnings: $0.713 USD (≈ 199.64 PKR)
```

---

### **Day 90 - April 10, 2025 (Last Day)**

```
Middleware processes:
├─ days_since_deposit = 90
├─ Day 90 rate: 1.3%
├─ Creates PassiveEarning: day_index=90
└─ ✅ Final earnings day

Ahmed's total earnings: ~$11.58 USD (≈ 3,242 PKR)
```

---

### **Day 91 - April 11, 2025 (No More Earnings)**

```
Middleware processes:
├─ days_since_deposit = 91
├─ max_allowed_day = min(91, 90) = 90
├─ current_day = 91 > max_allowed_day (90)
└─ ❌ Skips: "User has reached 90-day earning cap"

Ahmed's earnings stop (90-day cap reached)
```

---

## 🔒 Why Only Middleware (No Scheduler)?

### **Comparison:**

| Feature | Middleware | Scheduler |
|---------|-----------|-----------|
| **Reliability** | ✅ High (runs on every request) | ⚠️ Medium (can crash) |
| **Simplicity** | ✅ Simple (no background threads) | ❌ Complex (APScheduler) |
| **Hosting** | ✅ Works everywhere | ⚠️ May not work on some hosts |
| **Restarts** | ✅ Survives restarts | ❌ Needs restart logic |
| **Dependencies** | ✅ None | ❌ APScheduler required |
| **Timing** | ⚠️ Depends on traffic | ✅ Exact time (12:01 AM) |

### **Decision:**
✅ **Use Middleware** - More reliable, simpler, works everywhere

**Note:** If you need exact timing (e.g., 12:01 AM), you can enable scheduler by setting:
```bash
ENABLE_SCHEDULER=true
```

But **BOTH will NOT run twice** due to `DailyEarningsState` protection.

---

## 📋 Complete Earnings Schedule

### **For 5,410 PKR Deposit:**

| Period | Days | Rate | Daily Earning | Total for Period |
|--------|------|------|---------------|------------------|
| Day 0 | 1 | 0% | ₨0.00 | ₨0.00 |
| Days 1-10 | 10 | 0.4% | ₨17.36 | ₨173.60 |
| Days 11-20 | 10 | 0.6% | ₨26.04 | ₨260.40 |
| Days 21-30 | 10 | 0.8% | ₨34.72 | ₨347.20 |
| Days 31-60 | 30 | 1.0% | ₨43.40 | ₨1,302.00 |
| Days 61-90 | 30 | 1.3% | ₨56.42 | ₨1,692.60 |
| **TOTAL** | **90** | - | - | **₨3,775.80** |

**Total Return:** 70% over 90 days

---

## 🧪 Testing & Verification

### **Test 1: Day 0 Protection**
```bash
# Create test deposit today
# Check logs for: "⚠️ Skipping [user]: Deposit was made today (day 0)"
# Verify: No PassiveEarning record created
```

### **Test 2: Day 1 Earnings**
```bash
# Wait 24 hours after deposit
# Make any API request (or visit website)
# Check logs for: "✅ Credited [user] day 1: $X.XX USD (0.4%)"
# Verify: PassiveEarning record created with day_index=1
```

### **Test 3: No Double Processing**
```bash
# Make multiple API requests on same day
# First request: Processes earnings
# Subsequent requests: Skip (already processed)
# Verify: Only ONE PassiveEarning record per day
```

### **Test 4: Database Queries**
```python
# Check DailyEarningsState
from apps.earnings.models import DailyEarningsState
state = DailyEarningsState.objects.get(pk=1)
print(state.last_processed_date)  # Should be today

# Check PassiveEarnings
from apps.earnings.models import PassiveEarning
earnings = PassiveEarning.objects.filter(user=user).order_by('day_index')
for e in earnings:
    print(f"Day {e.day_index}: ${e.amount_usd} ({e.percent}%)")
```

---

## 🆘 Troubleshooting

### **Issue: No earnings generated**
**Check:**
1. User has credited deposit (not SIGNUP-INIT)
2. At least 24 hours passed since deposit
3. User is approved (`is_approved=True`)
4. Middleware is enabled in settings.py
5. Check logs for error messages

### **Issue: Earnings generated on day 0**
**Check:**
1. Middleware has day 0 protection (we fixed this)
2. Check deposit timestamp vs earning timestamp
3. Run cleanup script to remove premature earnings

### **Issue: Double earnings**
**Check:**
1. Scheduler is disabled (`ENABLE_SCHEDULER=false`)
2. Only middleware is running
3. Check `DailyEarningsState` for protection
4. Check database for duplicate `PassiveEarning` records

---

## 📞 Quick Commands

```powershell
# Navigate to backend
Set-Location "c:\Users\Ayesha Jahangir\Downloads\nexocart-redline-dash\ref_backend"

# Check DailyEarningsState
python manage.py shell
>>> from apps.earnings.models import DailyEarningsState
>>> DailyEarningsState.objects.get(pk=1)

# Check user's passive earnings
>>> from apps.earnings.models import PassiveEarning
>>> PassiveEarning.objects.filter(user__username='ahmed')

# Manual trigger (for testing)
python manage.py run_daily_earnings

# Cleanup premature earnings
python cleanup_premature_passive_income.py
```

---

## ✅ Summary

**How Passive Income Works:**
1. ✅ User deposits → Admin approves
2. ✅ Day 0 → NO earnings (deposit day)
3. ✅ Day 1+ → Earnings start automatically
4. ✅ Middleware processes once per day (on first request)
5. ✅ Protected against double processing
6. ✅ Continues for 90 days
7. ✅ Tiered rates: 0.4% → 1.3%

**Key Points:**
- ✅ Only middleware is active (scheduler disabled)
- ✅ Day 0 protection prevents premature earnings
- ✅ DailyEarningsState prevents double processing
- ✅ Unique constraint prevents duplicate day earnings
- ✅ No manual intervention needed

**Status:** ✅ Ready to use!