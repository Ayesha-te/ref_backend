from django.urls import path
from .views import MyEarningsSummary

urlpatterns = [
    path('me/summary/', MyEarningsSummary.as_view()),
]