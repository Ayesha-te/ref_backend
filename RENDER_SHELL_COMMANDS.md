# 🚀 Render Shell Commands - Passive Income Fix

## 📋 Quick Start (Copy & Paste in Render Shell)

### 1️⃣ Check Current Status
```bash
python manage.py comprehensive_passive_check
```
**What it does:** Shows detailed analysis of all users' passive income status

---

### 2️⃣ Fix Everything Automatically
```bash
python manage.py fix_all_passive_income
```
**What it does:**
- ✅ Diagnoses all issues
- ✅ Backfills missing passive income (last 30 days)
- ✅ Recalculates all wallet balances
- ✅ Verifies data integrity
- ✅ Shows final report

**Time:** ~2-3 minutes

---

### 3️⃣ Generate Today's Earnings Only
```bash
python manage.py run_daily_earnings
```
**What it does:** Generates passive income for today only (for all eligible users)

---

### 4️⃣ Backfill from Specific Date
```bash
python manage.py run_daily_earnings --backfill-from-date 2025-10-01
```
**What it does:** Generates all missing passive income from October 1st to today

---

### 5️⃣ Test Mode (No Changes)
```bash
python manage.py run_daily_earnings --dry-run
```
**What it does:** Shows what WOULD happen without actually making changes

---

## 🔍 Investigation Commands

### Check Specific User's Transactions
```bash
python manage.py shell
```

Then paste this (change user_id):
```python
from apps.wallets.models import Transaction, Wallet
from apps.accounts.models import User

user_id = 2  # CHANGE THIS to the user ID you want to check
wallet = Wallet.objects.get(user_id=user_id)

print(f"\n{'='*80}")
print(f"TRANSACTION BREAKDOWN FOR USER ID {user_id}")
print(f"{'='*80}\n")

# Show all income transactions
for tx_type in ['passive', 'referral', 'milestone', 'global_pool', 'deposit']:
    txs = Transaction.objects.filter(
        wallet=wallet,
        type='CREDIT',
        meta__contains={'type': tx_type}
    )
    total = sum(t.amount_usd for t in txs)
    print(f"{tx_type.upper()}: {txs.count()} transactions, Total: ${total}")

print(f"\nTotal income_usd in wallet: ${wallet.income_usd}")
print(f"Total available_usd in wallet: ${wallet.available_usd}")
print(f"Total hold_usd in wallet: ${wallet.hold_usd}")
print(f"\n{'='*80}\n")

# Exit shell
exit()
```

---

## 🎯 What Each Command Does

### `comprehensive_passive_check`
- Shows all users
- Identifies who has deposits
- Counts passive earning records
- Compares expected vs actual income
- Highlights issues

### `fix_all_passive_income`
- Runs comprehensive check
- Backfills missing earnings
- Recalculates wallet balances
- Verifies data integrity
- Shows final summary

### `run_daily_earnings`
- Generates passive income for eligible users
- Creates PassiveEarning records
- Creates Transaction records
- Updates wallet.income_usd
- Can backfill from specific dates

---

## 📊 Understanding the Output

### ✅ Good Output (User with Deposit):
```
👤 USER: ahmedsellar1@gmail.com (ID: 3)
📅 DEPOSIT INFORMATION:
   • First Deposit: $14.29 on 2025-10-09 16:19
   • Days Since Deposit: 4
📈 PASSIVE EARNINGS RECORDS:
   • Total Records: 4
   • Expected Day Index: 4
💸 PASSIVE INCOME TRANSACTIONS:
   • Total Transactions: 4
   • Total Amount: $1.28
🧮 EXPECTED PASSIVE INCOME: $1.28
✅ STATUS: OK
```

### ⚠️ Issue Output (Income Without Deposit):
```
👤 USER: sardarlaeiq3@gmail.com (ID: 2)
ℹ️  No credited deposits yet (passive income not started)
💰 Wallet Balance: available=$0.00, income=$2.81
❌ ISSUE: Has income but no deposit!
```

### ℹ️ Normal Output (No Deposit):
```
👤 USER: Ahmad (ID: 1)
ℹ️  No credited deposits yet (passive income not started)
💰 Wallet Balance: available=$0.00, income=$0.00
✅ STATUS: OK (no deposit = no passive income)
```

---

## 🚨 Common Issues & Solutions

### Issue 1: "User has income but no deposit"
**Cause:** User has income_usd but no credited deposit
**Solution:**
1. Check if it's referral/milestone income (VALID)
2. If it's passive income (INVALID - bug)
3. Run investigation command to see transaction types

### Issue 2: "Missing passive earnings"
**Cause:** Daily earnings command didn't run for some days
**Solution:**
```bash
python manage.py run_daily_earnings --backfill-from-date 2025-10-01
```

### Issue 3: "Record count mismatch"
**Cause:** PassiveEarning count ≠ Transaction count
**Solution:**
```bash
python manage.py fix_all_passive_income
```

### Issue 4: "Amount discrepancy"
**Cause:** wallet.income_usd doesn't match transaction totals
**Solution:**
```bash
python manage.py fix_all_passive_income
```

---

## 🔄 Daily Automation Setup

### Check if Scheduler is Enabled
```bash
python manage.py shell
```

Then:
```python
from django.conf import settings
print(f"ENABLE_SCHEDULER: {settings.ENABLE_SCHEDULER}")
exit()
```

### Enable Scheduler (if needed)
Add to Render environment variables:
```
ENABLE_SCHEDULER=True
```

This will automatically run `run_daily_earnings` every day at midnight.

---

## 📝 Step-by-Step Fix Process

### Step 1: Check Current Status
```bash
python manage.py comprehensive_passive_check
```
**Look for:**
- Users with deposits
- Users with passive earnings
- Any issues flagged

### Step 2: Run the Fix
```bash
python manage.py fix_all_passive_income
```
**This will:**
- Backfill missing earnings
- Fix wallet balances
- Verify everything

### Step 3: Verify Fix Worked
```bash
python manage.py comprehensive_passive_check
```
**Should show:**
- All users with deposits have correct passive income
- No issues flagged
- All balances match

### Step 4: Enable Daily Automation
Set environment variable:
```
ENABLE_SCHEDULER=True
```

### Step 5: Test Daily Run
```bash
python manage.py run_daily_earnings
```
**Should show:**
- "No new earnings to generate" (if already up to date)
- OR "Generated earnings for X users"

---

## 🎯 Expected Results After Fix

### For Users WITH Deposits:
- ✅ PassiveEarning records = Days since deposit
- ✅ Transaction records = PassiveEarning records
- ✅ wallet.income_usd = Sum of all income transactions
- ✅ Daily earnings continue automatically

### For Users WITHOUT Deposits:
- ✅ No PassiveEarning records
- ✅ No passive Transaction records
- ✅ wallet.income_usd = $0.00 (or only referral/milestone bonuses)
- ✅ No passive income generated

---

## 📞 Need Help?

If you see unexpected results, run this investigation:

```bash
python manage.py shell
```

```python
from apps.wallets.models import Wallet, Transaction, DepositRequest
from apps.earnings.models import PassiveEarning
from apps.accounts.models import User

# Check all users with issues
users = User.objects.filter(is_approved=True)

for user in users:
    wallet = Wallet.objects.filter(user=user).first()
    if not wallet:
        continue
    
    # Check deposits
    deposits = DepositRequest.objects.filter(
        user=user,
        status='CREDITED'
    ).exclude(tx_id='SIGNUP-INIT')
    
    # Check passive earnings
    passive_count = PassiveEarning.objects.filter(user=user).count()
    
    # Check income
    income = wallet.income_usd
    
    # Flag issues
    if income > 0 and deposits.count() == 0:
        print(f"⚠️  User {user.username} (ID: {user.id}): Has ${income} income but NO deposits")
        
        # Show where income came from
        txs = Transaction.objects.filter(wallet=wallet, type='CREDIT').exclude(meta__contains={'type': 'deposit'})
        for tx in txs:
            print(f"   - ${tx.amount_usd} from {tx.meta.get('type', 'unknown')} on {tx.created_at}")
        print()

exit()
```

This will show you EXACTLY what's wrong and where the income came from!

---

## ✅ Final Checklist

- [ ] Run `python manage.py comprehensive_passive_check`
- [ ] Run `python manage.py fix_all_passive_income`
- [ ] Verify no issues remain
- [ ] Set `ENABLE_SCHEDULER=True` in Render environment
- [ ] Test daily run with `python manage.py run_daily_earnings`
- [ ] Confirm automation is working

**Done!** Your passive income system should now be working perfectly! 🎉