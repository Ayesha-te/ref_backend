from rest_framework import serializers
from .models import WithdrawalRequest

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = '__all__'
        read_only_fields = ['user', 'amount_usd', 'fx_rate', 'tax_usd', 'net_usd', 'status', 'processed_at']