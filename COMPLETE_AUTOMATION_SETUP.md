# Complete Automation Setup for Daily Earnings and Global Pool

## ✅ Current System Status

### Global Pool Automation ✅ ALREADY WORKING
- **Status**: ✅ Fully automated and working
- **Schedule**: Every Monday
- **Last Payout**: $1.50 on Monday, September 29, 2025
- **What it does**:
  - Collects $0.50 from users who joined on Monday
  - Distributes the entire pool to all approved users
  - Applies 20% tax, gives 80% net to users
  - Automatically resets pool balance to $0.00

### Daily Earnings Automation ⚠️ NEEDS SETUP
- **Status**: ⚠️ Manual only (API endpoint available)
- **Current**: You call the API manually
- **Need**: Automatic daily generation

## 🎯 Solution: Set Up Automatic Daily Earnings

### Option 1: Render Cron Jobs (Recommended for Render deployment)

1. **Add to your production backend `requirements.txt`**:
```
APScheduler==3.10.4
```

2. **Create automatic scheduler in your Django app**:

Create `apps/earnings/scheduler.py`:
```python
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Schedule daily earnings generation at 00:01 UTC every day
    scheduler.add_job(
        run_daily_earnings,
        'cron',
        hour=0,
        minute=1,
        id='daily_earnings',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started for automated daily earnings")

def run_daily_earnings():
    """Function called by scheduler"""
    try:
        logger.info("Starting automated daily earnings generation")
        call_command('run_daily_earnings')
        logger.info("Automated daily earnings completed successfully")
    except Exception as e:
        logger.error(f"Automated daily earnings failed: {str(e)}")
```

3. **Update your `core/settings.py`**:
```python
INSTALLED_APPS = [
    # ... your existing apps ...
    'apscheduler',
]

# Add at the bottom
import os
if os.environ.get('ENABLE_SCHEDULER', 'true').lower() == 'true':
    from apps.earnings.scheduler import start_scheduler
    start_scheduler()
```

4. **Update your production environment variables**:
```
ENABLE_SCHEDULER=true
```

### Option 2: Using Render's Native Cron Jobs

1. **In your Render dashboard**, add a new **Cron Job** service
2. **Command**: `python manage.py run_automated_daily_tasks`
3. **Schedule**: `0 0 * * *` (daily at midnight)
4. **Environment**: Same as your web service

### Option 3: External Cron Service (UptimeRobot, etc.)

Set up external monitoring to call your API endpoint daily:
```bash
curl -X POST "https://ref-backend-fw8y.onrender.com/api/earnings/generate-daily/" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## 🔧 Testing the Automation

### Test the automated command locally:
```powershell
cd "c:\Users\Ayesha Jahangir\Downloads\nexocart-redline-dash\ref_backend"
python manage.py run_automated_daily_tasks --dry-run
python manage.py run_automated_daily_tasks
```

### Verify everything works:
```powershell
# Check earnings were generated
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
ahmad = User.objects.get(username='Ahmad')
print('Ahmad earnings count:', ahmad.passive_earnings.count())
print('Ahmad total earnings:', sum(e.amount_usd for e in ahmad.passive_earnings.all()))
"
```

## 📋 Complete System Flow

### Daily (Every Day at 00:01 UTC):
1. ✅ **Automated daily earnings generation**
   - Calculate progressive earning rates (0.4% to 0.6%+)
   - Credit user wallets with passive income
   - Create PassiveEarning records
   - Update wallet balances

### Monday (Every Monday during daily run):
2. ✅ **Global pool automation** (already working)
   - Collect $0.50 from Monday joiners
   - Distribute entire pool balance
   - Apply 20% tax (users get 80%)
   - Reset pool to $0.00

### Real-time (Always):
3. ✅ **Admin panel display**
   - Shows passive_income_usd for each user
   - Updates automatically as earnings are generated
   - Available at: https://adminui-etbh.vercel.app/

## 🚀 Deployment Steps

1. **Add the scheduler code** to your production backend repository
2. **Update requirements.txt** with APScheduler
3. **Deploy** to Render
4. **Verify** earnings appear daily in admin panel

## 📊 Monitoring

- **Admin Panel**: Check daily for new earnings
- **Logs**: Monitor Render logs for "Daily earnings generated successfully"
- **Database**: Verify PassiveEarning records are created daily

## 🎉 Expected Results

- **Users**: Will see passive income increase daily automatically
- **Admin Panel**: Will show updated passive_income_usd values daily
- **Global Pool**: Will continue Monday distributions automatically
- **System**: Fully automated, no manual intervention needed

The system will be completely autonomous once deployed!