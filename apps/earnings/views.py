from decimal import Decimal
from django.db.models import Sum
from rest_framework import views, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.conf import settings
from apps.wallets.models import Wallet, Transaction
from .models import PassiveEarning
from .models_global_pool import GlobalPool, GlobalPoolPayout


class MyEarningsSummary(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        
        # Calculate real passive income from transactions instead of dummy PassiveEarning records
        passive_transactions = Transaction.objects.filter(
            wallet=wallet,
            meta__type='passive'
        )
        total_gross = sum(Decimal(str(t.amount_usd)) for t in passive_transactions)
        total_count = passive_transactions.count()
        
        return Response({
            'available_usd': wallet.available_usd,
            'hold_usd': wallet.hold_usd,
            'entries': total_count,
            'total_credited_usd': str(total_gross.quantize(Decimal('0.01'))),
        })


class AdminGlobalPoolView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # Pool balance and last payout
        pool = GlobalPool.objects.first()
        last_payout = GlobalPoolPayout.objects.order_by('-distributed_on').first()
        
        # Top passive earners using real transaction data instead of dummy PassiveEarning records
        User = get_user_model()
        per_user_data = []
        
        # Get all users and calculate their real passive income from transactions
        users = User.objects.filter(is_approved=True).order_by('username')
        for user in users:
            # Calculate real passive income from transactions with meta.type = 'passive'
            passive_transactions = Transaction.objects.filter(
                wallet__user=user,
                meta__type='passive'
            )
            total_passive = sum(
                Decimal(str(t.amount_usd)) for t in passive_transactions
            )
            
            if total_passive > 0:  # Only include users with passive income
                per_user_data.append({
                    'user_id': user.id,
                    'username': user.username,
                    'total_passive_usd': str(total_passive.quantize(Decimal('0.01'))),
                })
        
        # Sort by total passive income (highest first) and limit to top 50
        per_user_data.sort(key=lambda x: Decimal(x['total_passive_usd']), reverse=True)
        per_user_data = per_user_data[:50]
        
        return Response({
            'payout_day': 'Monday',
            'pool_balance_usd': str(pool.balance_usd if pool else Decimal('0.00')),
            'last_payout': {
                'amount_usd': str(last_payout.amount_usd) if last_payout else None,
                'distributed_on': last_payout.distributed_on if last_payout else None,
                'meta': last_payout.meta if last_payout else None,
            },
            'per_user_passive': per_user_data,
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