from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Wallet, Transaction, DepositRequest
from .serializers import WalletSerializer, TransactionSerializer, DepositRequestSerializer


def get_fx_rate():
    return Decimal(str(settings.ADMIN_USD_TO_PKR))

class MyWalletView(generics.RetrieveAPIView):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet

class MyTransactionsView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        return wallet.transactions.all()

class MyDepositsView(generics.ListCreateAPIView):
    serializer_class = DepositRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DepositRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        amount_pkr = Decimal(self.request.data.get('amount_pkr'))
        tx_id = self.request.data.get('tx_id')
        rate = get_fx_rate()
        amount_usd = (amount_pkr / rate).quantize(Decimal('0.01'))
        serializer.save(user=self.request.user, amount_usd=amount_usd, fx_rate=rate, tx_id=tx_id)

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_deposit_action(request, pk):
    action = request.data.get('action')  # APPROVE/REJECT/CREDIT
    dr = DepositRequest.objects.get(pk=pk)
    if action == 'REJECT':
        dr.status = 'REJECTED'
        dr.processed_at = timezone.now()
        dr.save()
    elif action == 'APPROVE':
        dr.status = 'APPROVED'
        dr.processed_at = timezone.now()
        dr.save()
    elif action == 'CREDIT':
        wallet, _ = Wallet.objects.get_or_create(user=dr.user)
        wallet.available_usd = (Decimal(wallet.available_usd) + dr.amount_usd).quantize(Decimal('0.01'))
        wallet.save()
        Transaction.objects.create(wallet=wallet, type=Transaction.CREDIT, amount_usd=dr.amount_usd, meta={'type': 'deposit', 'id': dr.id, 'tx_id': dr.tx_id})
        dr.status = 'CREDITED'
        dr.processed_at = timezone.now()
        dr.save()
    else:
        return Response({'detail': 'Invalid action'}, status=400)
    return Response({'status': dr.status})