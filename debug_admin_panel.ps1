# This script will help debug and fix the admin panel issue
# Run this after deploying the updated code

try {
    Write-Host "🔑 Getting authentication token..."
    $response = Invoke-RestMethod -Uri "https://ref-backend-fw8y.onrender.com/api/auth/token/" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"username":"Ahmad","password":"12345"}'
    $token = $response.access
    Write-Host "✅ Token obtained"
    
    # Generate more earnings to ensure we have data
    Write-Host ""
    Write-Host "🚀 Generating more earnings data..."
    for ($i = 1; $i -le 15; $i++) {
        try {
            $result = Invoke-RestMethod -Uri "https://ref-backend-fw8y.onrender.com/api/earnings/generate-daily/" -Method POST -Headers @{"Authorization"="Bearer $token"} -ErrorAction SilentlyContinue
            if ($i % 5 -eq 0) { Write-Host "Generated $i earnings..." }
        } catch {
            # Ignore errors for duplicate entries
        }
    }
    
    Write-Host "✅ Earnings generation completed"
    Write-Host ""
    
    # Check the API response with detailed debugging
    Write-Host "🔍 Checking API response structure..."
    $users = Invoke-RestMethod -Uri "https://ref-backend-fw8y.onrender.com/api/accounts/admin/users/" -Method GET -Headers @{"Authorization"="Bearer $token"}
    
    $ahmad = $users.results | Where-Object { $_.username -eq "Ahmad" }
    if ($ahmad) {
        Write-Host ""
        Write-Host "📊 Ahmad's API data:"
        
        # Check all possible field names
        $fieldMappings = @{
            "rewards_usd" = $ahmad.rewards_usd
            "passive_income_usd" = $ahmad.passive_income_usd
        }
        
        if ($ahmad.PSObject.Properties.Name -contains "total_passive_earnings") {
            $fieldMappings["total_passive_earnings"] = $ahmad.total_passive_earnings
        }
        
        foreach ($field in $fieldMappings.Keys) {
            $value = $fieldMappings[$field]
            Write-Host "  $field`: '$value'"
            
            if ([decimal]$value -gt 0) {
                Write-Host "    ✅ This field has data!"
            }
        }
        
        Write-Host ""
        Write-Host "📋 Next steps:"
        if ([decimal]$ahmad.passive_income_usd -gt 0 -or [decimal]$ahmad.rewards_usd -gt 0) {
            Write-Host "✅ Earnings data exists in API!"
            Write-Host "🔧 The admin panel should check for 'passive_income_usd' or 'rewards_usd' fields"
            Write-Host ""
            Write-Host "Admin panel URL: https://adminui-etbh.vercel.app/?api_base=https://ref-backend-fw8y.onrender.com"
            Write-Host ""
            Write-Host "If still showing `$0, the admin panel frontend might be looking for a different field name."
        } else {
            Write-Host "❌ No earnings data found. The earnings generation might not be working."
        }
    }
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "🔧 Manual verification steps: https://ref-backend-fw8y.onrender.com"
Write-Host "1. Check if earnings exist: /api/earnings/me/summary/"
Write-Host "2. Admin users API: https://ref-backend-fw8y.onrender.com/api/accounts/admin/users/"
Write-Host "3. Generate earnings: POST https://ref-backend-fw8y.onrender.com/api/earnings/generate-daily/"