from rest_framework import views, permissions
from rest_framework.response import Response
from django.core.management import call_command
from io import StringIO
import sys

class AdminGenerateEarningsView(views.APIView):
    """Admin endpoint to generate daily earnings for testing purposes"""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        try:
            # Capture the command output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # Run the daily earnings command
            call_command('run_daily_earnings')
            
            # Get the output
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            return Response({
                'success': True,
                'message': 'Daily earnings generated successfully',
                'output': output
            })
            
        except Exception as e:
            sys.stdout = old_stdout
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)


class SchedulerStatusView(views.APIView):
    """Check the status of the automated scheduler"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        try:
            from apps.earnings.scheduler import get_scheduler_status
            from django.conf import settings
            
            status = get_scheduler_status()
            status['enabled'] = getattr(settings, 'ENABLE_SCHEDULER', False)
            status['config'] = getattr(settings, 'SCHEDULER_CONFIG', {})
            
            return Response(status)
        except Exception as e:
            return Response({
                'error': str(e),
                'running': False
            }, status=500)


class TriggerEarningsNowView(views.APIView):
    """Manually trigger earnings generation immediately"""
    permission_classes = [permissions.AllowAny]  # Allow external cron services
    
    def post(self, request):
        try:
            from django.conf import settings
            from apps.earnings.scheduler import trigger_daily_earnings_now
            
            # Check for secret key if configured (for security)
            secret_key = getattr(settings, 'CRON_SECRET_KEY', None)
            if secret_key:
                provided_key = request.headers.get('X-Cron-Secret') or request.data.get('secret')
                if provided_key != secret_key:
                    return Response({
                        'success': False,
                        'error': 'Invalid or missing secret key'
                    }, status=403)
            
            # Capture output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            trigger_daily_earnings_now()
            
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            return Response({
                'success': True,
                'message': 'Earnings generation triggered successfully',
                'output': output
            })
        except Exception as e:
            sys.stdout = old_stdout
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get(self, request):
        """Allow GET requests for simple cron services"""
        return self.post(request)


class MiddlewareStatusView(views.APIView):
    """Check if the AutoDailyEarningsMiddleware is working"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            from django.conf import settings
            from apps.earnings.models import DailyEarningsState
            from django.utils import timezone
            
            # Check middleware configuration
            middleware_list = settings.MIDDLEWARE
            middleware_enabled = 'core.middleware.AutoDailyEarningsMiddleware' in middleware_list
            
            # Get current state
            today = timezone.now().date()
            try:
                state = DailyEarningsState.objects.get(pk=1)
                last_processed = state.last_processed_date
                last_processed_at = state.last_processed_at
                is_processed_today = last_processed >= today
            except DailyEarningsState.DoesNotExist:
                last_processed = None
                last_processed_at = None
                is_processed_today = False
            
            return Response({
                'middleware_enabled': middleware_enabled,
                'middleware_class': 'core.middleware.AutoDailyEarningsMiddleware',
                'today': str(today),
                'last_processed_date': str(last_processed) if last_processed else None,
                'last_processed_at': str(last_processed_at) if last_processed_at else None,
                'is_processed_today': is_processed_today,
                'status': 'Working' if middleware_enabled and is_processed_today else 'Not processed today',
                'message': 'Middleware will auto-process on next request' if middleware_enabled and not is_processed_today else 'All good!'
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'middleware_enabled': False
            }, status=500)