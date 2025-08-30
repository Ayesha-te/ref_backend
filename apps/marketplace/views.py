from decimal import Decimal
from django.db.models import Sum
from rest_framework import generics, permissions, views
from rest_framework.response import Response
from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer

class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

class MyProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)

class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        quantity = int(self.request.data.get('quantity', 1))
        product = Product.objects.get(pk=product_id)
        total = (Decimal(product.price_usd) * Decimal(quantity)).quantize(Decimal('0.01'))
        serializer.save(buyer=self.request.user, total_usd=total, status='PAID')

class MyOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).order_by('-created_at')

class MySalesStatsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Seller-centric stats
        seller_orders = Order.objects.filter(product__seller=request.user, status='PAID')
        total_units = seller_orders.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0
        total_revenue = seller_orders.aggregate(total_rev=Sum('total_usd'))['total_rev'] or Decimal('0')
        return Response({
            'total_units_sold': int(total_units),
            'total_revenue_usd': str(total_revenue),
            'orders_count': seller_orders.count(),
        })