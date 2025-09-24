from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
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
        # Validate amount_pkr
        amount_pkr_raw = self.request.data.get('amount_pkr')
        print(f"DEBUG: Received amount_pkr_raw: {repr(amount_pkr_raw)} (type: {type(amount_pkr_raw)})")
        print(f"DEBUG: Request data: {dict(self.request.data)}")
        
        if amount_pkr_raw in (None, ""):
            raise ValidationError({"amount_pkr": ["This field is required."]})
        try:
            # Handle both string and numeric inputs
            if isinstance(amount_pkr_raw, str):
                # Remove any locale-specific formatting (commas, spaces)
                amount_pkr_clean = amount_pkr_raw.replace(',', '').replace(' ', '').strip()
                amount_pkr = Decimal(amount_pkr_clean)
            else:
                amount_pkr = Decimal(str(amount_pkr_raw))
            print(f"DEBUG: Converted amount_pkr: {amount_pkr}")
        except (InvalidOperation, TypeError, ValueError) as e:
            print(f"DEBUG: Conversion error: {e}")
            raise ValidationError({"amount_pkr": ["Invalid decimal amount."]})
        
        if amount_pkr <= 0:
            raise ValidationError({"amount_pkr": ["Must be greater than 0."]})

        # Check if user has minimum income requirement (5000 PKR total)
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
        total_income_usd = wallet.available_usd + wallet.hold_usd
        total_income_pkr = total_income_usd * get_fx_rate()
        
        if total_income_pkr < Decimal('5000'):
            print(f"DEBUG: User total income {total_income_pkr} PKR is less than 5000, raising validation error")
            raise ValidationError({"amount_pkr": ["You need a minimum income of 5000 PKR to make withdrawals."]})

        # FX and USD conversion
        rate = get_fx_rate()
        try:
            amount_usd = (amount_pkr / rate).quantize(Decimal('0.01'))
        except (InvalidOperation, ZeroDivisionError):
            raise ValidationError({"detail": ["Invalid FX rate configuration."]})

        # Wallet balance check (only check available balance, not minimum withdrawal amount)
        if amount_usd > wallet.available_usd:
            raise ValidationError({"detail": ["Insufficient balance."]})

        tax = apply_withdraw_tax(amount_usd)
        net_usd = tax['net_usd']

        # Default method/account_details if frontend omits them
        method = self.request.data.get('method') or 'BANK'
        account_details = self.request.data.get('account_details') or {}
        # Allow stringified JSON for account_details
        if isinstance(account_details, str):
            try:
                import json
                account_details = json.loads(account_details) or {}
            except Exception:
                account_details = {}
        bank_name = self.request.data.get('bank_name') or account_details.get('bank') or ''
        account_name = self.request.data.get('account_name') or account_details.get('account_name') or ''
        tx_id = self.request.data.get('tx_id') or ''  # Get TX ID from frontend
        
        print(f"DEBUG: Creating withdrawal - TX ID from frontend: {repr(tx_id)}")

        serializer.save(
            user=self.request.user,
            amount_usd=amount_usd,
            fx_rate=rate,
            tax_usd=tax['tax_usd'],
            net_usd=net_usd,
            method=method,
            account_details=account_details,
            bank_name=bank_name,
            account_name=account_name,
            tx_id=tx_id,  # Include TX ID in save
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
        wr.status = 'REJECTED'
        wr.processed_at = timezone.now()
        wr.save()
    elif action == 'APPROVE':
        # deduct funds on approval
        wallet = wr.user.wallet
        wallet.available_usd = (Decimal(wallet.available_usd) - wr.amount_usd).quantize(Decimal('0.01'))
        wallet.save()
        wr.status = 'APPROVED'
        wr.processed_at = timezone.now()
        wr.save()
    elif action == 'PAID':
        # final settle
        wallet = wr.user.wallet
        # allow admin to attach/override tx_id in payout
        tx_id = request.data.get('tx_id') or wr.tx_id
        if request.data.get('tx_id') and not wr.tx_id:
            wr.tx_id = tx_id
        Transaction.objects.create(wallet=wallet, type=Transaction.DEBIT, amount_usd=wr.net_usd, meta={'type': 'withdrawal', 'id': wr.id, 'tx_id': tx_id})
        wr.status = 'PAID'
        wr.processed_at = timezone.now()
        wr.save()
    else:
        return Response({'detail': 'Invalid action'}, status=400)

    return Response({'status': wr.status})