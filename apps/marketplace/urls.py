from django.urls import path
from .views import ProductListCreateView, MyProductsView, OrderCreateView

urlpatterns = [
    path('products/', ProductListCreateView.as_view()),
    path('products/mine/', MyProductsView.as_view()),
    path('orders/', OrderCreateView.as_view()),
]