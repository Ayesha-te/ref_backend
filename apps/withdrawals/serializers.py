from rest_framework import serializers
from .models import WithdrawalRequest

class WithdrawalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'user', 'amount_pkr', 'amount_usd', 'fx_rate', 'method',
            'bank_name', 'account_name', 'account_details', 'tx_id',
            'tax_usd', 'net_usd', 'status', 'created_at', 'processed_at'
        ]
        read_only_fields = ['user', 'amount_usd', 'fx_rate', 'tax_usd', 'net_usd', 'status', 'processed_at']