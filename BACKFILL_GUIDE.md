# 🚀 Passive Earnings - Deployment & Backfill Guide

Your backend is deployed at: **https://ref-backend-fw8y.onrender.com**

---

## ✅ Step 1: Check if Scheduler is Running

### Option A: Check Render Logs (RECOMMENDED)

1. Go to your Render dashboard: https://dashboard.render.com
2. Click on your backend service
3. Click on "Logs" tab
4. Look for these messages:

**✅ SUCCESS - You should see:**
```
✅ Earnings automation started successfully
📅 Daily earnings job scheduled for 00:01 UTC
💓 Scheduler heartbeat (appears every hour)
```

**❌ ERROR - If you see errors:**
- Share the error logs with me
- The scheduler might not have started

### Option B: Use API Endpoint (if you have admin access)

Open this URL in your browser (you'll need to be logged in as admin):
```
https://ref-backend-fw8y.onrender.com/api/earnings/scheduler-status/
```

**Expected Response:**
```json
{
  "scheduler_running": true,
  "jobs_count": 2,
  "next_run_time": "2024-01-15T00:01:00+00:00"
}
```

---

## 💰 Step 2: Backfill Missing Earnings (September 22 - Today)

You have **TWO OPTIONS** to backfill earnings:

### **Option A: Using Render Shell (RECOMMENDED)**

1. Go to Render Dashboard → Your Service → "Shell" tab
2. Run this command to see what will happen (DRY RUN):
   ```bash
   python manage.py run_daily_earnings --backfill-from-date 2024-09-22 --dry-run
   ```

3. If the dry run looks good, run the actual backfill:
   ```bash
   python manage.py run_daily_earnings --backfill-from-date 2024-09-22
   ```

### **Option B: Using Local Script (if you have DB access)**

If you have the database credentials configured locally:

1. Open PowerShell in the backend directory
2. Run dry run first:
   ```powershell
   python backfill_earnings.py --from-date 2024-09-22 --dry-run
   ```

3. If it looks good, run the actual backfill:
   ```powershell
   python backfill_earnings.py --from-date 2024-09-22
   ```

---

## 📊 What the Backfill Will Do

The backfill command will:

1. ✅ Find all **approved users** with **credited deposits** (excluding signup bonuses)
2. ✅ Calculate how many days have passed since their last earning
3. ✅ Generate passive earnings for each missing day
4. ✅ Credit the earnings to their wallets
5. ✅ Create transaction records
6. ✅ Show a summary of total users processed and amounts

**Example Output:**
```
📅 Backfilling from 2024-09-22 to 2024-01-15 (115 days)

✅ Credited user123 day 45: 0.56 USD (1.0%)
✅ Credited user456 day 23: 0.45 USD (0.8%)
...

============================================================
📈 EARNINGS SUMMARY
============================================================
👥 Users Processed: 25
💰 Total Earnings Generated: 2,875
💵 Total Amount: $1,437.50
💵 Total Amount (PKR): ₨402,500.00
============================================================
```

---

## 🔍 Step 3: Verify Earnings Were Added

### Check User Wallets:

1. **Via Admin Panel:**
   - Go to: `https://ref-backend-fw8y.onrender.com/admin/`
   - Navigate to Wallets → Transactions
   - Filter by `type = CREDIT` and `meta contains "passive"`

2. **Via API:**
   ```
   GET https://ref-backend-fw8y.onrender.com/api/wallets/me/transactions/
   ```
   Look for transactions with `meta.type = "passive"`

3. **Via Frontend:**
   - Log in to your app
   - Check the dashboard - passive income should now show

---

## ⏰ Step 4: Confirm Daily Automation

The scheduler will now run automatically every day at **00:01 UTC** (5:01 AM Pakistan time).

### To manually trigger earnings (for testing):

**Using Render Shell:**
```bash
python manage.py run_daily_earnings
```

**Using API (requires admin auth):**
```bash
POST https://ref-backend-fw8y.onrender.com/api/earnings/trigger-earnings-now/
```

---

## 🐛 Troubleshooting

### Issue: Scheduler not running

**Check:**
1. Render logs for errors
2. Environment variable `DEBUG` should be `False` in production
3. The app should be running via Gunicorn (not Django dev server)

**Fix:**
- Restart the Render service
- Check that `ENABLE_SCHEDULER` is not set to `false` in environment variables

### Issue: Backfill not working

**Check:**
1. Users must be **approved** (`is_approved=True`)
2. Users must have at least one **credited deposit** (excluding signup bonus)
3. Database connection is working

**Fix:**
- Run with `--dry-run` first to see what would happen
- Check Render logs for error messages

### Issue: Earnings not showing in frontend

**Check:**
1. Transaction type is `CREDIT`
2. Transaction meta has `type: "passive"`
3. Frontend is filtering correctly

**Fix:**
- Clear browser cache
- Check API response: `/api/wallets/me/transactions/`

---

## 📝 Quick Command Reference

### Check scheduler status:
```bash
# In Render Shell
python manage.py shell -c "from apps.earnings.scheduler import scheduler; print(f'Running: {scheduler.running}')"
```

### Backfill from specific date:
```bash
python manage.py run_daily_earnings --backfill-from-date 2024-09-22
```

### Backfill last N days:
```bash
python manage.py run_daily_earnings --backfill-days 30
```

### Dry run (no changes):
```bash
python manage.py run_daily_earnings --backfill-from-date 2024-09-22 --dry-run
```

### Manual trigger (single day):
```bash
python manage.py run_daily_earnings
```

---

## 🎯 Next Steps

1. ✅ **Check Render logs** to confirm scheduler is running
2. ✅ **Run backfill** to add missing earnings since Sept 22
3. ✅ **Verify** earnings appear in user wallets
4. ✅ **Monitor** daily at 00:01 UTC to ensure automation works

---

## 📞 Need Help?

If you encounter any issues:

1. **Share Render logs** - especially any error messages
2. **Share backfill output** - the summary from the command
3. **Check database** - ensure users are approved and have deposits

The system is now fully automated and will run daily without manual intervention! 🎉