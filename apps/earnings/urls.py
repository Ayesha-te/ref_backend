from django.urls import path
from .views import MyEarningsSummary, AdminGlobalPoolView, AdminSystemOverviewView

urlpatterns = [
    path('me/summary/', MyEarningsSummary.as_view()),
    # Admin global pool summary (balance, last payout, user passive totals)
    path('admin/global-pool/', AdminGlobalPoolView.as_view()),
    # Admin system overview (economics config)
    path('admin/system-overview/', AdminSystemOverviewView.as_view()),
]