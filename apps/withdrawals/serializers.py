from rest_framework import serializers
from .models import WithdrawalRequest

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'user', 'username', 'email', 'amount_pkr', 'amount_usd', 'fx_rate', 'method',
            'bank_name', 'account_name', 'account_details', 'tx_id',
            'tax_usd', 'net_usd', 'status', 'created_at', 'processed_at'
        ]
        read_only_fields = ['user', 'username', 'email', 'amount_usd', 'fx_rate', 'tax_usd', 'net_usd', 'status', 'processed_at']