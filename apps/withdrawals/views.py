from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from apps.wallets.models import Wallet, Transaction
from .models import WithdrawalRequest
from .serializers import WithdrawalRequestSerializer
from apps.earnings.services import apply_withdraw_tax


def get_fx_rate():
    # admin-set rate for now
    return Decimal(str(settings.ADMIN_USD_TO_PKR))

class MyWithdrawalsView(generics.ListCreateAPIView):
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WithdrawalRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        amount_pkr_raw = self.request.data.get('amount_pkr')
        if not amount_pkr_raw:
            raise ValueError('amount_pkr is required')
        amount_pkr = Decimal(amount_pkr_raw)
        rate = get_fx_rate()
        amount_usd = (amount_pkr / rate).quantize(Decimal('0.01'))

        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        if amount_usd > wallet.available_usd:
            raise ValueError('Insufficient balance')

        tax = apply_withdraw_tax(amount_usd)
        net_usd = tax['net_usd']

        # Hold funds while pending
        wallet.available_usd = (Decimal(wallet.available_usd) - amount_usd).quantize(Decimal('0.01'))
        wallet.save()

        # Default method/account_details if frontend omits them
        method = self.request.data.get('method') or 'BANK'
        account_details = self.request.data.get('account_details') or {}

        serializer.save(
            user=self.request.user,
            amount_usd=amount_usd,
            fx_rate=rate,
            tax_usd=tax['tax_usd'],
            net_usd=net_usd,
            method=method,
            account_details=account_details,
        )

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_pending_withdrawals(request):
    qs = WithdrawalRequest.objects.filter(status='PENDING').order_by('-created_at')
    data = WithdrawalRequestSerializer(qs, many=True, context={'request': request}).data
    return Response(data)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_withdraw_action(request, pk):
    action = request.data.get('action')  # APPROVE/REJECT/PAID
    wr = WithdrawalRequest.objects.get(pk=pk)

    if action == 'REJECT':
        # refund to wallet
        wallet = wr.user.wallet
        wallet.available_usd = (Decimal(wallet.available_usd) + wr.amount_usd).quantize(Decimal('0.01'))
        wallet.save()
        wr.status = 'REJECTED'
        wr.processed_at = timezone.now()
        wr.save()
    elif action == 'APPROVE':
        wr.status = 'APPROVED'
        wr.processed_at = timezone.now()
        wr.save()
    elif action == 'PAID':
        # final settle
        wallet = wr.user.wallet
        Transaction.objects.create(wallet=wallet, type=Transaction.DEBIT, amount_usd=wr.net_usd, meta={'type': 'withdrawal', 'id': wr.id, 'tx_id': wr.tx_id})
        wr.status = 'PAID'
        wr.processed_at = timezone.now()
        wr.save()
    else:
        return Response({'detail': 'Invalid action'}, status=400)

    return Response({'status': wr.status})