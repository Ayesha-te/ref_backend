# Passive Income Issue Fix

## Problem
Passive income is not showing in user dashboards because the daily earnings generation command was not scheduled to run automatically.

## Root Cause
The system has all the logic for calculating and distributing passive income, but the `run_daily_earnings` management command was not being executed daily as required.

## Solution

### 1. Automatic Daily Execution (Render Deployment)
I've added a cron job service to your `render.yaml` file that will run the daily earnings command every day at 00:01 UTC.

**Changes made:**
- Added a new cron service in `render.yaml` 
- The cron job runs `python manage.py run_daily_earnings` daily

### 2. Backfill Missing Earnings
Since the system hasn't been running for 4-5 days, you need to backfill the missing passive income.

**Steps to fix immediately:**

1. **Check current status:**
   ```bash
   python manage.py check_earnings_status
   ```

2. **Preview what will be backfilled (dry run):**
   ```bash
   python manage.py backfill_daily_earnings --days=7 --dry-run
   ```

3. **Actually backfill the missing earnings:**
   ```bash
   python manage.py backfill_daily_earnings --days=7
   ```

### 3. Deploy the Changes
After running the backfill command, deploy your updated `render.yaml` to Render so the daily cron job starts running automatically.

## How Passive Income Works

1. **Requirements for passive income:**
   - User must be approved (`is_approved = True`)
   - User must have made at least one credited deposit (excluding signup deposit)

2. **Daily Schedule:**
   - Days 1-10: 0.4% daily
   - Days 11-20: 0.6% daily  
   - Days 21-30: 0.8% daily
   - Days 31-60: 1.0% daily
   - Days 61-90: 1.3% daily

3. **Distribution:**
   - 80% goes to user's available balance
   - 20% held by platform

## Verification

After running the backfill command, users should see:
- **Current Income**: Shows total earnings from passive income, referrals, and milestones
- **Passive Income**: Shows earnings specifically from daily passive income
- **Available Balance**: Shows withdrawable amount

## Monitoring

Use these commands to monitor the system:

- `python manage.py check_earnings_status` - Check if all users are up to date
- `python manage.py run_daily_earnings` - Manually run daily earnings (for testing)
- `python manage.py backfill_daily_earnings --days=N` - Backfill N days of missing earnings

## Important Notes

1. The backfill command is idempotent - it won't create duplicate earnings
2. The system automatically caps earnings at 90 days for the standard plan
3. First-time investment referral bonuses are also handled during backfill
4. All amounts are calculated in USD and converted to PKR for display (280 PKR = 1 USD)