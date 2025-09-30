from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Wallet, Transaction, DepositRequest
from .serializers import WalletSerializer, TransactionSerializer, DepositRequestSerializer
from apps.referrals.models import ReferralPayout
from apps.referrals.services import pay_on_package_purchase


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
        from rest_framework.exceptions import ValidationError
        from decimal import InvalidOperation

        amount_pkr_raw = self.request.data.get('amount_pkr')
        if amount_pkr_raw in (None, ""):
            raise ValidationError({"amount_pkr": ["This field is required."]})
        try:
            amount_pkr = Decimal(str(amount_pkr_raw))
        except (InvalidOperation, TypeError):
            raise ValidationError({"amount_pkr": ["Invalid decimal amount."]})
        if amount_pkr <= 0:
            raise ValidationError({"amount_pkr": ["Must be greater than 0."]})
        # Removed minimum deposit amount validation - users can add any amount

        tx_id = self.request.data.get('tx_id')
        bank_name = self.request.data.get('bank_name', '')
        account_name = self.request.data.get('account_name', '')
        proof_image = self.request.FILES.get('proof_image')
        rate = get_fx_rate()
        try:
            amount_usd = (amount_pkr / rate).quantize(Decimal('0.01'))
        except (InvalidOperation, ZeroDivisionError):
            raise ValidationError({"detail": ["Invalid FX rate configuration."]})
        serializer.save(
            user=self.request.user,
            amount_usd=amount_usd,
            fx_rate=rate,
            tx_id=tx_id,
            bank_name=bank_name,
            account_name=account_name,
            proof_image=proof_image,
        )

class AdminPendingDepositsView(generics.ListAPIView):
    serializer_class = DepositRequestSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return DepositRequest.objects.filter(status='PENDING').order_by('-created_at')

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
        # Apply economics: split deposit into user available share and platform hold
        # NO global pool contribution from regular deposits - only Monday joiners contribute
        from django.conf import settings as dj_settings
        from apps.referrals.services import pay_on_first_investment
        wallet, _ = Wallet.objects.get_or_create(user=dr.user)
        user_share_rate = Decimal(str(dj_settings.ECONOMICS['USER_WALLET_SHARE']))
        
        user_share = (dr.amount_usd * user_share_rate).quantize(Decimal('0.01'))
        platform_hold = (dr.amount_usd - user_share).quantize(Decimal('0.01'))

        wallet.available_usd = (Decimal(wallet.available_usd) + user_share).quantize(Decimal('0.01'))
        wallet.hold_usd = (Decimal(wallet.hold_usd) + platform_hold).quantize(Decimal('0.01'))
        wallet.save()

        # Record full deposit in transactions with breakdown
        Transaction.objects.create(
            wallet=wallet,
            type=Transaction.CREDIT,
            amount_usd=dr.amount_usd,
            meta={
                'type': 'deposit',
                'id': dr.id,
                'tx_id': dr.tx_id,
                'user_share_usd': str(user_share),
                'platform_hold_usd': str(platform_hold),
                'global_pool_contribution': 'none',  # No global pool from deposits
            }
        )
        dr.status = 'CREDITED'
        dr.processed_at = timezone.now()
        dr.save()

        # Referral payouts on investment disabled; payouts handled on join approval (pay_on_package_purchase).
    else:
        return Response({'detail': 'Invalid action'}, status=400)
    return Response({'status': dr.status})