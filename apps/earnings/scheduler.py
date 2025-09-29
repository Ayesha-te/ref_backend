"""
Automatic scheduler for daily earnings generation
This scheduler runs in the background and triggers daily earnings automatically
Designed for Render free tier - no external cron needed
"""

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
from django.conf import settings
import logging
import atexit
import os

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

def start_scheduler():
    """Start the background scheduler for automated daily tasks"""
    global scheduler
    
    if scheduler and scheduler.running:
        logger.info("Scheduler is already running")
        return
    
    # Check if scheduler should be enabled
    enable_scheduler = getattr(settings, 'ENABLE_SCHEDULER', False)
    if not enable_scheduler:
        logger.info("Scheduler disabled by settings")
        return
    
    try:
        scheduler = BackgroundScheduler(timezone='UTC')
        
        # Get scheduler configuration from settings
        config = getattr(settings, 'SCHEDULER_CONFIG', {})
        daily_hour = config.get('DAILY_EARNINGS_HOUR', 0)
        daily_minute = config.get('DAILY_EARNINGS_MINUTE', 1)
        heartbeat_interval = config.get('HEARTBEAT_INTERVAL', 3600)
        
        # Schedule daily earnings generation
        scheduler.add_job(
            run_daily_earnings,
            'cron',
            hour=daily_hour,
            minute=daily_minute,
            id='daily_earnings_generation',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            name='Daily Earnings Generation'
        )
        
        # Schedule heartbeat for monitoring (every hour)
        scheduler.add_job(
            heartbeat_check,
            'interval',
            seconds=heartbeat_interval,
            id='scheduler_heartbeat',
            replace_existing=True,
            max_instances=1,
            name='Scheduler Heartbeat'
        )
        
        # For testing - add a job that runs every 5 minutes in debug mode
        if getattr(settings, 'DEBUG', False) and os.environ.get('ENABLE_DEBUG_SCHEDULER') == 'true':
            scheduler.add_job(
                test_earnings_generation,
                'interval',
                minutes=5,
                id='debug_earnings_test',
                replace_existing=True,
                max_instances=1,
                name='Debug Earnings Test'
            )
            logger.info("Debug scheduler enabled - earnings will generate every 5 minutes")
        
        scheduler.start()
        logger.info("✅ Automated earnings scheduler started successfully")
        logger.info(f"📅 Daily earnings scheduled for {daily_hour:02d}:{daily_minute:02d} UTC")
        
        # Ensure scheduler shuts down cleanly
        atexit.register(stop_scheduler)
        
        # Log current jobs
        jobs = scheduler.get_jobs()
        logger.info(f"📋 Scheduled {len(jobs)} jobs:")
        for job in jobs:
            logger.info(f"   - {job.name}: {job.next_run_time}")
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {str(e)}")
        raise

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

def run_daily_earnings():
    """Function called by scheduler to generate daily earnings"""
    try:
        logger.info("🚀 Starting automated daily earnings generation")
        call_command('run_daily_earnings')
        logger.info("✅ Automated daily earnings completed successfully")
    except Exception as e:
        logger.error(f"❌ Automated daily earnings failed: {str(e)}")

def test_earnings_generation():
    """Test function for debug mode - generates earnings every 5 minutes"""
    try:
        logger.info("🧪 Debug: Generating test earnings")
        call_command('run_daily_earnings')
        logger.info("✅ Debug earnings generation completed")
    except Exception as e:
        logger.error(f"❌ Debug earnings generation failed: {str(e)}")

def heartbeat_check():
    """Heartbeat function to verify scheduler is working"""
    logger.info("💓 Scheduler heartbeat - automation system is running")
    
    # Log scheduler status
    global scheduler
    if scheduler:
        jobs = scheduler.get_jobs()
        next_earnings = None
        for job in jobs:
            if job.id == 'daily_earnings_generation':
                next_earnings = job.next_run_time
                break
        
        if next_earnings:
            logger.info(f"⏰ Next earnings generation: {next_earnings}")
        else:
            logger.warning("⚠️ Daily earnings job not found!")

# Manual functions for testing and monitoring
def trigger_daily_earnings_now():
    """Manually trigger daily earnings generation (for testing)"""
    logger.info("Manual trigger: Daily earnings generation")
    run_daily_earnings()

def get_scheduler_status():
    """Get current scheduler status"""
    global scheduler
    if scheduler:
        jobs = scheduler.get_jobs()
        job_info = []
        for job in jobs:
            job_info.append({
                'id': job.id,
                'name': job.name,
                'next_run': str(job.next_run_time) if job.next_run_time else None
            })
        
        return {
            'running': scheduler.running,
            'jobs_count': len(jobs),
            'jobs': job_info
        }
    return {'running': False, 'jobs_count': 0, 'jobs': []}

def restart_scheduler():
    """Restart the scheduler (for debugging)"""
    global scheduler
    if scheduler:
        stop_scheduler()
    start_scheduler()