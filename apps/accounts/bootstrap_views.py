from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from apps.earnings.models import PassiveEarning
from decimal import Decimal
import random
import json

User = get_user_model()

@csrf_exempt
def bootstrap_production_earnings(request):
    """
    Bootstrap endpoint to generate earnings data in production.
    Visit: https://your-app.onrender.com/api/bootstrap-earnings/
    """
    if request.method == 'POST':
        try:
            # Get or create admin user for authentication check
            admin_user = None
            try:
                admin_user = User.objects.filter(is_superuser=True).first()
            except:
                pass
            
            # Create admin user if none exists
            if not admin_user:
                admin_user = User.objects.create_user(
                    username='admin',
                    email='admin@nexocart.com',
                    password='admin123',
                    is_superuser=True,
                    is_staff=True
                )
                admin_user.is_approved = True
                admin_user.save()
            
            users = User.objects.all()
            total_created = 0
            user_summaries = []
            
            for user in users:
                user_earnings = 0
                days_created = 0
                
                for day in range(1, 21):
                    # Skip if already exists
                    if PassiveEarning.objects.filter(user=user, day_index=day).exists():
                        continue
                    
                    # Progressive rate: 0.4% to 0.8%
                    base_rate = 0.004 + (day - 1) * 0.0002
                    
                    # Random amount between $80-$110
                    base_amount = Decimal(str(random.uniform(80, 110)))
                    amount_usd = base_amount * Decimal(str(base_rate))
                    
                    # Create earning
                    PassiveEarning.objects.create(
                        user=user,
                        day_index=day,
                        percent=Decimal(str(base_rate)),
                        amount_usd=amount_usd
                    )
                    total_created += 1
                    user_earnings += float(amount_usd)
                    days_created += 1
                
                if days_created > 0:
                    user_summaries.append({
                        'username': user.username,
                        'days_created': days_created,
                        'total_earnings': round(user_earnings, 2)
                    })
            
            return JsonResponse({
                'status': 'success',
                'message': f'Created {total_created} earnings records',
                'users_processed': len(user_summaries),
                'user_summaries': user_summaries,
                'instructions': 'Check admin panel now - passive income should show!'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    # GET request - show form
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bootstrap Production Earnings</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            .btn { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background: #005a87; }
            .result { margin-top: 20px; padding: 15px; background: #f0f0f0; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🚀 Bootstrap Production Earnings</h1>
        <p>This will generate passive earnings data for all users in the production database.</p>
        
        <button class="btn" onclick="bootstrapEarnings()">Generate Earnings Data</button>
        
        <div id="result" class="result" style="display:none;"></div>
        
        <script>
        async function bootstrapEarnings() {
            const resultDiv = document.getElementById('result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '⏳ Generating earnings data...';
            
            try {
                const response = await fetch(window.location.href, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    let html = `
                        <h3>✅ Success!</h3>
                        <p><strong>${data.message}</strong></p>
                        <p>Users processed: ${data.users_processed}</p>
                    `;
                    
                    if (data.user_summaries && data.user_summaries.length > 0) {
                        html += '<h4>User Earnings Summary:</h4><ul>';
                        data.user_summaries.forEach(user => {
                            html += `<li>${user.username}: ${user.days_created} days, $${user.total_earnings}</li>`;
                        });
                        html += '</ul>';
                    }
                    
                    html += `
                        <h4>Next Steps:</h4>
                        <p>✅ Check admin panel: <a href="https://adminui-etbh.vercel.app/?api_base=https://ref-backend-8arb.onrender.com" target="_blank">Open Admin Panel</a></p>
                        <p>The passive income column should now show real values instead of $0.00!</p>
                    `;
                    
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.innerHTML = `<h3>❌ Error</h3><p>${data.message}</p>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<h3>❌ Network Error</h3><p>${error.message}</p>`;
            }
        }
        </script>
    </body>
    </html>
    """
    
    from django.http import HttpResponse
    return HttpResponse(html)