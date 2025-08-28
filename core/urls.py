from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/wallets/', include('apps.wallets.urls')),
    path('api/earnings/', include('apps.earnings.urls')),
    path('api/referrals/', include('apps.referrals.urls')),
    path('api/withdrawals/', include('apps.withdrawals.urls')),
    path('api/marketplace/', include('apps.marketplace.urls')),
]