from django.apps import AppConfig
from django.conf import settings
import os
import threading
import time

class EarningsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.earnings'

    def ready(self):
        """Initialize the earnings app and start automation if enabled"""
        # Only start scheduler in production and when explicitly enabled
        enable_scheduler = getattr(settings, 'ENABLE_SCHEDULER', False)
        is_production = not getattr(settings, 'DEBUG', True)
        
        # Also check if this is the main process (not a worker or migration)
        is_main_process = os.environ.get('RUN_MAIN') != 'true'
        
        if enable_scheduler and (is_production or os.environ.get('FORCE_SCHEDULER') == 'true'):
            # Use a delayed start to ensure Django is fully initialized
            def delayed_start():
                time.sleep(3)  # Wait 3 seconds for Django to fully initialize
                try:
                    from .scheduler import start_scheduler
                    start_scheduler()
                    print("✅ Earnings automation started successfully")
                except Exception as e:
                    print(f"⚠️ Could not start earnings automation: {e}")
            
            # Start scheduler in a separate thread to avoid blocking Django startup
            if is_main_process:
                scheduler_thread = threading.Thread(target=delayed_start, daemon=True)
                scheduler_thread.start()
                print("🚀 Earnings automation starting in background...")
        else:
            print(f"ℹ️ Earnings automation disabled (enabled={enable_scheduler}, production={is_production})")