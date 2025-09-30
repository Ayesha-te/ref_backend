from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views import TokenObtainPairPatchedView
from django.http import JsonResponse
from django.contrib.auth import get_user_model

def health_check(request):
    """Health check endpoint for Render deployment"""
    return JsonResponse({"status": "ok", "service": "nexocart-backend"}, status=200)

def debug_admin(request):
    """Debug endpoint to check admin user status"""
    User = get_user_model()
    try:
        admin_user = User.objects.get(username='Ahmad')
        return JsonResponse({
            "admin_exists": True,
            "is_staff": admin_user.is_staff,
            "is_superuser": admin_user.is_superuser,
            "is_approved": getattr(admin_user, 'is_approved', True),
            "is_active": admin_user.is_active,
            "total_users": User.objects.count(),
        })
    except User.DoesNotExist:
        return JsonResponse({
            "admin_exists": False,
            "total_users": User.objects.count(),
        })

urlpatterns = [
    path('', health_check, name='health_check'),  # ✅ Root health check for Render
    path('debug/admin/', debug_admin, name='debug_admin'),  # Debug endpoint
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

# Serve adminui only from /adminui and restrict to staff
from django.contrib.auth.decorators import user_passes_test

def staff_only(view_func):
    return user_passes_test(lambda u: u.is_staff or u.is_superuser)(view_func)

urlpatterns += [
    # Protect /adminui behind staff auth; do not serve admin UI at root
    re_path(r'^adminui/?$', staff_only(lambda request: serve(request, 'index_django.html', document_root=settings.BASE_DIR / 'adminui'))),
    re_path(r'^adminui/(?P<path>.*)$', staff_only(lambda request, path: serve(request, path, document_root=settings.BASE_DIR / 'adminui'))),
]