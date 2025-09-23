from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
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

# Serve media files (including in production)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Serve adminui in both development and production
urlpatterns += [
    # Root path serves admin UI
    re_path(r'^$', lambda request: serve(request, 'index_django.html', document_root=settings.BASE_DIR / 'adminui')),
    # /adminui path also serves admin UI
    re_path(r'^adminui/?$', lambda request: serve(request, 'index_django.html', document_root=settings.BASE_DIR / 'adminui')),
    re_path(r'^adminui/(?P<path>.*)$', lambda request, path: serve(request, path, document_root=settings.BASE_DIR / 'adminui')),
]