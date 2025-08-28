from django.urls import path
from .views import MeView, SignupView, request_approval

urlpatterns = [
    path('me/', MeView.as_view()),
    path('signup/', SignupView.as_view()),
    path('request-approval/', request_approval),
]