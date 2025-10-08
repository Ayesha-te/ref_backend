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
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        try:
            from apps.earnings.scheduler import trigger_daily_earnings_now
            
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