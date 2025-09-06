from decimal import Decimal
from django.conf import settings
from django.db.models import Sum
from rest_framework import generics, permissions, views, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer

class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer

    def get_permissions(self):
        # Allow anyone to list products; creation requires auth
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

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
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        quantity = int(self.request.data.get('quantity', 1))
        product = Product.objects.get(pk=product_id)
        unit_price = Decimal(product.price_usd)
        # 10% discount if authenticated
        if self.request.user and self.request.user.is_authenticated:
            unit_price = (unit_price * Decimal('0.90')).quantize(Decimal('0.01'))
        total = (unit_price * Decimal(quantity)).quantize(Decimal('0.01'))
        buyer = self.request.user if (self.request.user and self.request.user.is_authenticated) else None
        serializer.save(buyer=buyer, total_usd=total, status='PENDING')

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

# Public endpoint to provide admin bank details for checkout
class AdminBankInfoView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'bank_name': getattr(settings, 'ADMIN_BANK_NAME', ''),
            'account_name': getattr(settings, 'ADMIN_ACCOUNT_NAME', ''),
            'account_id': getattr(settings, 'ADMIN_ACCOUNT_ID', ''),
        })

# Admin: list/add products (visible in frontend when is_active=True)
class AdminProductsView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Product.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        # Admin-created product becomes globally visible (seller=admin)
        serializer.save(seller=self.request.user, is_active=True)

# Admin: toggle product active/hidden (frontend shows is_active=True)
class AdminProductToggleActiveView(generics.UpdateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Product.objects.all()

    def patch(self, request, *args, **kwargs):
        product = self.get_object()
        active = request.data.get('is_active')
        if active is None:
            product.is_active = not product.is_active
        else:
            product.is_active = str(active).lower() in ['1','true','yes','y']
        product.save()
        return Response(ProductSerializer(product, context={'request': request}).data)

# Admin: list orders and update status
class AdminOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = Order.objects.select_related('product', 'buyer').order_by('-created_at')
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        return qs

class AdminOrderStatusView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        new_status = str(request.data.get('status', '')).upper()
        if new_status not in ['PENDING', 'PAID', 'CANCELLED']:
            return Response({'detail': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = new_status
        order.save()
        return Response(OrderSerializer(order, context={'request': request}).data)