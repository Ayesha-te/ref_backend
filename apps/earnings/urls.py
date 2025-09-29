from django.urls import path
from .views import MyEarningsSummary, AdminGlobalPoolView, AdminSystemOverviewView
from .admin_views import AdminGenerateEarningsView

urlpatterns = [
    path('me/summary/', MyEarningsSummary.as_view()),
    # Admin global pool summary (balance, last payout, user passive totals)
    path('admin/global-pool/', AdminGlobalPoolView.as_view()),
    # Admin system overview (economics config)
    path('admin/system-overview/', AdminSystemOverviewView.as_view()),
    # Admin generate earnings for testing
    path('admin/generate-earnings/', AdminGenerateEarningsView.as_view()),
]