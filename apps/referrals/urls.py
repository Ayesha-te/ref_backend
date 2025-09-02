from django.urls import path
from .views import MyReferralsView, MyReferralListView, AdminReferralSummaryView

urlpatterns = [
    path('me/', MyReferralsView.as_view()),
    path('list/', MyReferralListView.as_view()),
    path('admin/summary/', AdminReferralSummaryView.as_view()),
]