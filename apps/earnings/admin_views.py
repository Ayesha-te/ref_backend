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