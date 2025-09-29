# Celery tasks for automatic earnings generation
# Add this file: apps/earnings/tasks.py

from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def generate_daily_earnings_task():
    """
    Celery task to automatically generate daily earnings
    This task runs daily at 00:01 UTC
    """
    try:
        logger.info("Starting automatic daily earnings generation")
        call_command('run_daily_earnings')
        logger.info("Daily earnings generation completed successfully")
        return "Daily earnings generated successfully"
    except Exception as e:
        logger.error(f"Error generating daily earnings: {str(e)}")
        raise

@shared_task
def test_task():
    """Simple test task to verify Celery is working"""
    logger.info("Test task executed successfully")
    return "Test task completed"