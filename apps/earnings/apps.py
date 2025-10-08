from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class EarningsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.earnings'
    
    def ready(self):
        """Initialize the scheduler when Django starts"""
        # Only start scheduler in production (when running via WSGI/Gunicorn)
        # Avoid starting in management commands or migrations
        import sys
        
        # Check if we're running the actual server (not a management command)
        if 'runserver' not in sys.argv and 'migrate' not in sys.argv and 'makemigrations' not in sys.argv:
            try:
                from django.conf import settings
                if getattr(settings, 'ENABLE_SCHEDULER', False):
                    # Import and start scheduler
                    from apps.earnings.scheduler import start_scheduler
                    import threading
                    
                    # Start scheduler in a separate thread to avoid blocking Django startup
                    def delayed_start():
                        import time
                        time.sleep(5)  # Wait 5 seconds for Django to fully initialize
                        try:
                            start_scheduler()
                            logger.info("✅ Earnings automation started successfully")
                        except Exception as e:
                            logger.error(f"❌ Failed to start earnings automation: {str(e)}")
                    
                    thread = threading.Thread(target=delayed_start, daemon=True)
                    thread.start()
                    logger.info("🚀 Earnings automation starting in background...")
                else:
                    logger.info("ℹ️ Scheduler disabled (ENABLE_SCHEDULER=False)")
            except Exception as e:
                logger.error(f"❌ Error initializing scheduler: {str(e)}")