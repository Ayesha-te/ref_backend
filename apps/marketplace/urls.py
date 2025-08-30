from django.urls import path
from .views import (
    ProductListCreateView,
    MyProductsView,
    OrderCreateView,
    MyOrdersView,
    MySalesStatsView,
)

urlpatterns = [
    path('products/', ProductListCreateView.as_view()),
    path('products/mine/', MyProductsView.as_view()),
    path('orders/', OrderCreateView.as_view()),
    path('orders/mine/', MyOrdersView.as_view()),
    path('stats/sales/', MySalesStatsView.as_view()),
]