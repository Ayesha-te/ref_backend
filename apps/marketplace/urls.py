from django.urls import path
from .views import (
    ProductListCreateView,
    MyProductsView,
    OrderCreateView,
    MyOrdersView,
    MySalesStatsView,
    AdminProductsView,
    AdminProductToggleActiveView,
    AdminBankInfoView,
    AdminOrdersView,
    AdminOrderStatusView,
)

urlpatterns = [
    path('products/', ProductListCreateView.as_view()),
    path('products/mine/', MyProductsView.as_view()),
    path('orders/', OrderCreateView.as_view()),
    path('orders/mine/', MyOrdersView.as_view()),
    path('stats/sales/', MySalesStatsView.as_view()),
    path('bank-info/', AdminBankInfoView.as_view()),

    # Admin manage marketplace products (front-end visible when is_active=True)
    path('admin/products/', AdminProductsView.as_view()),
    path('admin/products/<int:pk>/toggle/', AdminProductToggleActiveView.as_view()),

    # Admin orders management
    path('admin/orders/', AdminOrdersView.as_view()),
    path('admin/orders/<int:pk>/status/', AdminOrderStatusView.as_view()),
]