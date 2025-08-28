from django.urls import path
from .views import MyReferralsView

urlpatterns = [
    path('me/', MyReferralsView.as_view()),
]