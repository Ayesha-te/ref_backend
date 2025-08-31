from django.urls import path
from .views import (
    MyWalletView,
    MyTransactionsView,
    MyDepositsView,
    admin_deposit_action,
    AdminPendingDepositsView,
)

urlpatterns = [
    path('me/', MyWalletView.as_view()),
    path('me/transactions/', MyTransactionsView.as_view()),
    path('me/deposits/', MyDepositsView.as_view()),
    path('admin/deposits/action/<int:pk>/', admin_deposit_action),
    path('admin/deposits/pending/', AdminPendingDepositsView.as_view()),
]