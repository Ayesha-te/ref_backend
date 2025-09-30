from decimal import Decimal
from django.db.models import Sum
from rest_framework import views, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.management import call_command
from apps.wallets.models import Wallet
from .models import PassiveEarning
from .models_global_pool import GlobalPool, GlobalPoolPayout
import io
import sys


class MyEarningsSummary(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        total_gross = sum(e.amount_usd for e in PassiveEarning.objects.filter(user=request.user))
        total_count = PassiveEarning.objects.filter(user=request.user).count()
        return Response({
            'available_usd': wallet.available_usd,
            'hold_usd': wallet.hold_usd,
            'entries': total_count,
            'total_credited_usd': total_gross,
        })


class AdminGlobalPoolView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # Pool balance and last payout
        pool = GlobalPool.objects.first()
        last_payout = GlobalPoolPayout.objects.order_by('-distributed_on').first()
        # Top passive earners and per-user passive totals
        per_user = (
            PassiveEarning.objects.values('user__id', 'user__username')
            .annotate(total_passive=Sum('amount_usd'))
            .order_by('-total_passive')[:50]
        )
        return Response({
            'payout_day': 'Monday',
            'pool_balance_usd': str(pool.balance_usd if pool else Decimal('0.00')),
            'last_payout': {
                'amount_usd': str(last_payout.amount_usd) if last_payout else None,
                'distributed_on': last_payout.distributed_on if last_payout else None,
                'meta': last_payout.meta if last_payout else None,
            },
            'per_user_passive': [
                {
                    'user_id': row['user__id'],
                    'username': row['user__username'],
                    'total_passive_usd': str(row['total_passive'] or Decimal('0.00')),
                }
                for row in per_user
            ],
        })


class AdminSystemOverviewView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        econ = settings.ECONOMICS
        return Response({
            'PASSIVE_MODE': econ.get('PASSIVE_MODE'),
            'USER_WALLET_SHARE': econ.get('USER_WALLET_SHARE'),
            'WITHDRAW_TAX': econ.get('WITHDRAW_TAX'),
            'GLOBAL_POOL_CUT': econ.get('GLOBAL_POOL_CUT'),
            'REFERRAL_TIERS': econ.get('REFERRAL_TIERS'),
            'FX_SOURCE': econ.get('FX_SOURCE'),
        })


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


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def scheduler_status_api(request):
    """
    API endpoint to check scheduler status
    Only accessible by admin users
    """
    try:
        from .scheduler import get_scheduler_status
        status = get_scheduler_status()
        
        return Response({
            'success': True,
            'scheduler_status': status,
            'message': 'Scheduler is running' if status['running'] else 'Scheduler is not running'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def trigger_earnings_now_api(request):
    """
    API endpoint to manually trigger earnings generation immediately
    Only accessible by admin users
    """
    try:
        from .scheduler import trigger_daily_earnings_now
        trigger_daily_earnings_now()
        
        return Response({
            'success': True,
            'message': 'Daily earnings triggered successfully'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def bulk_generate_earnings_api(request):
    """
    API endpoint to generate sample earnings for all users
    Only accessible by admin users
    """
    try:
        days = int(request.data.get('days', 15))
        reset = request.data.get('reset', False)
        
        if reset:
            PassiveEarning.objects.all().delete()
        
        User = get_user_model()
        # Only generate earnings for users who have made investments (excluding signup initial)
        from apps.wallets.models import DepositRequest
        eligible_users = []
        for u in User.objects.filter(is_approved=True):
            first_dep = DepositRequest.objects.filter(user=u, status='CREDITED').exclude(tx_id='SIGNUP-INIT').first()
            if first_dep:
                eligible_users.append(u)
        
        users = eligible_users
        total_created = 0
        
        for user in users:
            user_created = 0
            for day in range(1, days + 1):
                # Progressive earnings calculation
                base_amount = Decimal("100.00")
                percent = Decimal("0.004") + (Decimal("0.0002") * day)
                amount = base_amount * percent
                
                # Add variation
                import random
                variation = Decimal(str(random.uniform(-0.1, 0.1)))
                amount = max(amount + variation, Decimal("0.01"))
                
                earning, created = PassiveEarning.objects.get_or_create(
                    user=user,
                    day_index=day,
                    defaults={
                        'percent': percent,
                        'amount_usd': amount
                    }
                )
                
                if created:
                    user_created += 1
                    total_created += 1
        
        return Response({
            'success': True,
            'message': f'Successfully created {total_created} earnings records for {users.count()} users',
            'total_created': total_created,
            'users_count': users.count()
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)