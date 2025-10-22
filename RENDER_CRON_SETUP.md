# Quick Setup Guide: Render Cron Job for Daily Earnings

## ⏱️ Time Required: 5-10 minutes

---

## Step 1: Access Render Dashboard

1. Go to: **https://dashboard.render.com/**
2. Log in with your account
3. You should see your existing web service

---

## Step 2: Create New Cron Job

1. Click the **"New +"** button (top right)
2. Select **"Cron Job"** from the dropdown
3. Connect to your GitHub repository (same repo as your web service)

---

## Step 3: Configure the Cron Job

### Basic Settings:
```
Name: nexocart-daily-earnings
Branch: main (or your production branch)
```

### Build & Start:
```
Build Command: pip install -r requirements.txt
Command: cd ref_backend && python manage.py run_daily_earnings
```

### Schedule:
```
Schedule: 0 1 * * *
```
This means: Run at 00:01 UTC every day

**Cron Schedule Explanation:**
- `0 1 * * *` = Every day at 1:00 AM UTC (00:01)
- `0 */6 * * *` = Every 6 hours (if you want more frequent)
- `0 0 * * *` = Every day at midnight UTC

---

## Step 4: Environment Variables

**IMPORTANT:** Copy ALL environment variables from your web service!

### Required Variables:
```
DATABASE_URL=<your-database-url>
DJANGO_SECRET_KEY=<your-secret-key>
DJANGO_DEBUG=0
ENABLE_SCHEDULER=false
```

**Note:** Set `ENABLE_SCHEDULER=false` for the cron job since it will run the command directly.

### How to Copy Variables:
1. Go to your existing web service
2. Click "Environment" tab
3. Copy each variable
4. Paste into the cron job's environment variables

### Common Variables to Include:
- `DATABASE_URL`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `ADMIN_BANK_NAME`
- `ADMIN_ACCOUNT_NAME`
- `ADMIN_ACCOUNT_ID`
- Any other custom variables you have

---

## Step 5: Deploy

1. Click **"Create Cron Job"**
2. Wait for the initial build (2-3 minutes)
3. Once deployed, you'll see the cron job in your dashboard

---

## Step 6: Test Immediately

1. Go to your cron job in the dashboard
2. Click **"Trigger Job"** button (top right)
3. Watch the logs to see if it runs successfully

### Expected Log Output:
```
✅ Starting daily earnings generation
✅ Processing users with deposits...
✅ Generated earnings for X users
✅ Daily earnings completed successfully
```

---

## Step 7: Verify It's Working

### Check After 24 Hours:
1. Go to Render Dashboard → Your Cron Job → Logs
2. Look for successful runs at 00:01 UTC
3. Check your database to verify earnings were generated

### Via API:
```bash
# Run the test script
python test_scheduler_status.py
```

### Via Admin Panel:
1. Log into admin panel
2. Check user earnings to see if they're increasing daily
3. Check the last run timestamp

---

## Troubleshooting

### Issue: Cron job fails with "Module not found"
**Solution:** Make sure `Build Command` includes: `pip install -r requirements.txt`

### Issue: Database connection error
**Solution:** Verify `DATABASE_URL` is copied correctly from web service

### Issue: Command not found
**Solution:** Make sure command includes: `cd ref_backend && python manage.py run_daily_earnings`

### Issue: Cron job runs but no earnings generated
**Solution:** 
1. Check if users have deposits
2. Check if users are approved
3. Run manually: `python manage.py run_daily_earnings` and check output

---

## Alternative Schedules

### Run Every 12 Hours:
```
Schedule: 0 */12 * * *
```

### Run Every 6 Hours:
```
Schedule: 0 */6 * * *
```

### Run Twice Daily (6 AM and 6 PM UTC):
```
Schedule: 0 6,18 * * *
```

### Run Every Hour (for testing):
```
Schedule: 0 * * * *
```

---

## Monitoring

### Check Logs:
- Render Dashboard → Cron Job → Logs tab
- Shows all runs and their output

### Check Status:
- Render Dashboard → Cron Job → Overview
- Shows last run time and status

### Set Up Alerts:
- Render Dashboard → Cron Job → Settings
- Add email notifications for failures

---

## Cost

### Render Pricing:
- **Starter Plan:** Includes cron jobs
- **Pro Plan:** Includes cron jobs
- **Free Plan:** Does NOT include cron jobs (requires paid plan)

Since you mentioned you have a paid Render account, you should be good to go!

---

## Additional Cron Jobs (Optional)

### Weekly Global Pool Distribution:
```
Name: nexocart-weekly-pool
Command: cd ref_backend && python manage.py distribute_global_pool
Schedule: 0 0 * * 1
```
(Runs every Monday at midnight UTC)

---

## Summary Checklist

- [ ] Created new cron job in Render
- [ ] Set build command: `pip install -r requirements.txt`
- [ ] Set command: `cd ref_backend && python manage.py run_daily_earnings`
- [ ] Set schedule: `0 1 * * *`
- [ ] Copied all environment variables from web service
- [ ] Set `ENABLE_SCHEDULER=false` in cron job
- [ ] Deployed the cron job
- [ ] Tested with "Trigger Job" button
- [ ] Verified logs show success
- [ ] Checked after 24 hours to confirm automatic runs

---

## Need Help?

If you encounter any issues:
1. Check the logs in Render Dashboard
2. Verify environment variables are correct
3. Test the command locally first
4. Let me know and I can help troubleshoot!

---

**Setup Time:** 5-10 minutes  
**Difficulty:** Easy  
**Reliability:** Very High (99.9%+)