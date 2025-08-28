from django.contrib import admin
from .models import Wallet, Transaction, DepositRequest

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "available_usd", "hold_usd")

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet", "type", "amount_usd", "created_at")
    list_filter = ("type",)

@admin.register(DepositRequest)
class DepositRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "amount_pkr", "amount_usd", "status", "created_at")
    list_filter = ("status",)