from rest_framework import views, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import ReferralPayout

User = get_user_model()

class MyReferralsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # counts
        l1 = User.objects.filter(referred_by=request.user).count()
        l2 = User.objects.filter(referred_by__referred_by=request.user).count()
        payouts = ReferralPayout.objects.filter(referrer=request.user)
        total_earnings = sum(p.amount_usd for p in payouts)
        return Response({
            'level1_count': l1,
            'level2_count': l2,
            'total_earnings_usd': total_earnings,
        })