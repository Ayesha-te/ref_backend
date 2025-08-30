from django.urls import path
from .views import MyReferralsView, MyReferralListView

urlpatterns = [
    path('me/', MyReferralsView.as_view()),
    path('list/', MyReferralListView.as_view()),
]