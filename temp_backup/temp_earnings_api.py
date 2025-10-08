# Temporary API endpoint to add to your production backend
# Add this view to apps/earnings/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.core.management import call_command
import io
import sys

@api_view(['POST'])
@permission_classes([IsAdminUser])
def generate_daily_earnings_api(request):
    """
    API endpoint to trigger daily earnings generation
    Only accessible by admin users
    """
    try:
        # Capture the output of the management command
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()
        
        # Run the management command
        call_command('run_daily_earnings')
        
        # Restore stdout and get the output
        sys.stdout = old_stdout
        output = mystdout.getvalue()
        
        return Response({
            'success': True,
            'message': 'Daily earnings generated successfully',
            'output': output
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# Add this URL to apps/earnings/urls.py:
# path('generate-daily/', views.generate_daily_earnings_api, name='generate-daily-earnings'),