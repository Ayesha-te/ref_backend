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