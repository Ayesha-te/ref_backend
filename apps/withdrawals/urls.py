from django.urls import path
from .views import MyWithdrawalsView, admin_withdraw_action, admin_pending_withdrawals

urlpatterns = [
    path('me/', MyWithdrawalsView.as_view()),
    path('admin/action/<int:pk>/', admin_withdraw_action),
    path('admin/pending/', admin_pending_withdrawals),
]