from django.urls import path
from .views import (
    MyEarningsSummary, AdminGlobalPoolView, AdminSystemOverviewView, 
    generate_daily_earnings_api, scheduler_status_api, trigger_earnings_now_api,
    bulk_generate_earnings_api
)
from .admin_views import AdminGenerateEarningsView

urlpatterns = [
    path('me/summary/', MyEarningsSummary.as_view()),
    # Admin global pool summary (balance, last payout, user passive totals)
    path('admin/global-pool/', AdminGlobalPoolView.as_view()),
    # Admin system overview (economics config)
    path('admin/system-overview/', AdminSystemOverviewView.as_view()),
    # Admin generate earnings for testing
    path('admin/generate-earnings/', AdminGenerateEarningsView.as_view()),
    # API endpoint to generate daily earnings
    path('generate-daily/', generate_daily_earnings_api, name='generate-daily-earnings'),
    # API endpoint to check scheduler status
    path('scheduler-status/', scheduler_status_api, name='scheduler-status'),
    # API endpoint to manually trigger earnings now
    path('trigger-now/', trigger_earnings_now_api, name='trigger-earnings-now'),
    # API endpoint to bulk generate sample earnings
    path('bulk-generate/', bulk_generate_earnings_api, name='bulk-generate-earnings'),
]