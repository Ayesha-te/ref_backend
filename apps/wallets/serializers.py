from rest_framework import serializers
from .models import Wallet, Transaction, DepositRequest

class WalletSerializer(serializers.ModelSerializer):
    current_income_usd = serializers.SerializerMethodField()
    passive_earnings_usd = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = ["available_usd", "hold_usd", "income_usd", "current_income_usd", "passive_earnings_usd"]
    
    def get_current_income_usd(self, obj):
        """Return calculated current income from all sources (passive + referral + milestone + global pool)"""
        return float(obj.get_current_income_usd())
    
    def get_passive_earnings_usd(self, obj):
        """Return only passive earnings"""
        from django.db.models import Sum
        from decimal import Decimal
        
        passive_total = obj.transactions.filter(
            type=Transaction.CREDIT,
            meta__type='passive'
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
        
        return float(passive_total)

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id", "type", "amount_usd", "meta", "created_at"]

class DepositRequestSerializer(serializers.ModelSerializer):
    proof_image_url = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)  # expose username/email to admin UI

    class Meta:
        model = DepositRequest
        fields = [
            "id",
            "user",
            "amount_pkr",
            "amount_usd",
            "fx_rate",
            "tx_id",
            "bank_name",
            "account_name",
            "proof_image",
            "proof_image_url",
            "status",
            "created_at",
            "processed_at",
        ]
        read_only_fields = ["user", "amount_usd", "fx_rate", "status", "processed_at"]

    def get_user(self, obj):
        u = obj.user
        return {"id": u.id, "username": getattr(u, "username", ""), "email": getattr(u, "email", "")}

    def get_proof_image_url(self, obj):
        request = self.context.get('request')
        if obj.proof_image and hasattr(obj.proof_image, 'url'):
            url = obj.proof_image.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None