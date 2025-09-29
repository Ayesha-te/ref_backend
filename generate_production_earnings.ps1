# PowerShell script to generate production earnings data
try {
    Write-Host "🔑 Getting authentication token..."
    $response = Invoke-RestMethod -Uri "https://ref-backend-8arb.onrender.com/api/auth/token/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"username":"Ahmad","password":"12345"}'
    $token = $response.access
    Write-Host "✅ Token obtained"
    
    Write-Host ""
    Write-Host "🚀 Generating bulk earnings data for all users..."
    $bulkResult = Invoke-RestMethod -Uri "https://ref-backend-8arb.onrender.com/api/earnings/bulk-generate/" -Method POST -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} -Body '{"days": 25, "reset": true}'
    
    if ($bulkResult.success) {
        Write-Host "✅ Bulk generation successful!"
        Write-Host "   Created: $($bulkResult.total_created) earnings records"
        Write-Host "   For: $($bulkResult.users_count) users"
        
        Write-Host ""
        Write-Host "📊 Checking updated user data..."
        Start-Sleep 3
        
        $users = Invoke-RestMethod -Uri "https://ref-backend-8arb.onrender.com/api/accounts/admin/users/" -Method GET -Headers @{"Authorization"="Bearer $token"}
        
        Write-Host "Users with passive earnings:"
        foreach ($user in $users.results) {
            if ([decimal]$user.total_passive_earnings -gt 0) {
                Write-Host "  $($user.username): `$$($user.total_passive_earnings)"
            }
        }
        
        Write-Host ""
        Write-Host "🎉 SUCCESS! Check the admin panel:"
        Write-Host "   https://adminui-etbh.vercel.app/?api_base=https://ref-backend-8arb.onrender.com"
        Write-Host ""
        Write-Host "   Passive earnings should now show real amounts instead of `$0.00!"
        
    } else {
        Write-Host "❌ Bulk generation failed: $($bulkResult.error)"
    }
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)"
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode
        Write-Host "Status Code: $statusCode"
        
        if ($statusCode -eq 404) {
            Write-Host ""
            Write-Host "💡 The API endpoint might not be deployed yet."
            Write-Host "   Please ensure you've deployed the updated code to production."
            Write-Host "   The following files need to be updated:"
            Write-Host "   - apps/accounts/views.py"
            Write-Host "   - apps/earnings/views.py" 
            Write-Host "   - apps/earnings/urls.py"
        }
    }
}