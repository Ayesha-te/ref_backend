from rest_framework import serializers
from .models import Product, Order

class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['seller']

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None

class OrderSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    proof_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['buyer', 'total_usd', 'status']

    def get_proof_image_url(self, obj):
        if getattr(obj, 'proof_image', None):
            try:
                url = obj.proof_image.url
                request = self.context.get('request')
                return request.build_absolute_uri(url) if request else url
            except Exception:
                return None
        return None