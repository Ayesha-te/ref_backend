from rest_framework import serializers
from .models import Wallet, Transaction, DepositRequest

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["available_usd", "hold_usd"]

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id", "type", "amount_usd", "meta", "created_at"]

class DepositRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositRequest
        fields = "__all__"
        read_only_fields = ["user", "amount_usd", "fx_rate", "status", "processed_at"]