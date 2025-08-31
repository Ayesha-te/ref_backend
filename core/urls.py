from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views import TokenObtainPairPatchedView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/', TokenObtainPairPatchedView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/wallets/', include('apps.wallets.urls')),
    path('api/earnings/', include('apps.earnings.urls')),
    path('api/referrals/', include('apps.referrals.urls')),
    path('api/withdrawals/', include('apps.withdrawals.urls')),
    path('api/marketplace/', include('apps.marketplace.urls')),
]

# Serve media and adminui in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    from django.views.static import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^adminui/?$', lambda request: serve(request, 'index.html', document_root=settings.BASE_DIR / 'adminui')),
        re_path(r'^adminui/(?P<path>.*)$', lambda request, path: serve(request, path, document_root=settings.BASE_DIR / 'adminui')),
    ]