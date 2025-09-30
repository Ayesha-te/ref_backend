# Celery configuration for automatic daily tasks
# Add this to your production backend

from celery import Celery
from django.conf import settings
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'daily-earnings-generation': {
        'task': 'apps.earnings.tasks.generate_daily_earnings_task',
        'schedule': crontab(hour=0, minute=1),  # Run daily at 00:01 UTC
        'options': {'timezone': 'UTC'}
    },
}

app.conf.timezone = 'UTC'