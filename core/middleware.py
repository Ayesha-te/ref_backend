"""
Middleware to handle Neon database connection issues
"""
from django.db import OperationalError
from time import sleep
import logging

logger = logging.getLogger(__name__)


class DBRetryMiddleware:
    """
    Middleware to retry database operations when Neon DB wakes up from sleep mode.
    Neon free tier auto-sleeps after ~5 minutes of inactivity.
    The first request after wake-up might throw OperationalError.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for attempt in range(2):
            try:
                return self.get_response(request)
            except OperationalError as e:
                if attempt == 0:
                    logger.warning(f"Database connection failed (attempt {attempt + 1}), retrying in 1 second: {e}")
                    sleep(1)  # Wait 1 second and retry
                else:
                    logger.error(f"Database connection failed after retry: {e}")
                    raise
            except Exception as e:
                # Don't retry for non-database errors
                raise