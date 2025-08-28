from rest_framework import views, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from apps.wallets.models import Wallet
from .models import PassiveEarning

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