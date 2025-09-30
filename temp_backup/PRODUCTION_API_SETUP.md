# Production Backend API Endpoint for Earnings Generation

## Overview
This API endpoint allows you to trigger daily earnings generation via HTTP POST request to your production backend.

## Files to Update in Your Production Backend Repository

### 1. Update `apps/earnings/views.py`

Add these imports to the top of the file:
```python
from rest_framework.decorators import api_view, permission_classes
from django.core.management import call_command
import io
import sys
```

Add this function at the end of the file:
```python
@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
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
```

### 2. Update `apps/earnings/urls.py`

Add the import:
```python
from .views import generate_daily_earnings_api
```

Add this URL pattern to urlpatterns:
```python
path('generate-daily/', generate_daily_earnings_api, name='generate-daily-earnings'),
```

## How to Use After Deployment

### Step 1: Get Admin Token
```powershell
$response = Invoke-RestMethod -Uri "https://ref-backend-8arb.onrender.com/api/auth/token/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"username":"Ahmad","password":"12345"}'
$token = $response.access
```

### Step 2: Generate Daily Earnings
```powershell
$result = Invoke-RestMethod -Uri "https://ref-backend-8arb.onrender.com/api/earnings/generate-daily/" -Method POST -Headers @{"Authorization"="Bearer $token"}
$result | ConvertTo-Json -Depth 3
```

### Step 3: Verify in Admin Panel
Visit: https://adminui-etbh.vercel.app/?api_base=https://ref-backend-8arb.onrender.com

## Security Notes
- Only admin users can access this endpoint
- Requires valid JWT token
- Can be called multiple times to generate multiple days of earnings
- Each call generates one day of earnings for all eligible users

## Expected Response
```json
{
  "success": true,
  "message": "Daily earnings generated successfully",
  "output": "Generated earnings for X users..."
}
```

## Troubleshooting
- If you get 404: URL pattern not added correctly
- If you get 403: User is not admin or token invalid
- If you get 500: Check server logs for detailed error message