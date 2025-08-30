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

class MyReferralListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        level = int(request.query_params.get('level', '1'))
        if level == 1:
            qs = User.objects.filter(referred_by=request.user)
        elif level == 2:
            qs = User.objects.filter(referred_by__referred_by=request.user)
        elif level == 3:
            qs = User.objects.filter(referred_by__referred_by__referred_by=request.user)
        else:
            return Response({'detail': 'Invalid level'}, status=400)
        data = [
            {
                'id': u.id,
                'username': u.username,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'email': u.email,
                'is_approved': u.is_approved,
                'date_joined': u.date_joined.isoformat() if getattr(u, 'date_joined', None) else None,
            }
            for u in qs.order_by('-date_joined')[:200]
        ]
        return Response({'results': data})