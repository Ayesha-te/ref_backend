from django.contrib import admin
from django.utils import timezone
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
    actions = ["approve_deposits", "reject_deposits", "credit_deposits"]

    def approve_deposits(self, request, queryset):
        updated = queryset.update(status='APPROVED', processed_at=timezone.now())
        self.message_user(request, f"Approved {updated} deposit(s).")
    approve_deposits.short_description = "Approve selected deposits"

    def reject_deposits(self, request, queryset):
        updated = queryset.update(status='REJECTED', processed_at=timezone.now())
        self.message_user(request, f"Rejected {updated} deposit(s).")
    reject_deposits.short_description = "Reject selected deposits"

    def credit_deposits(self, request, queryset):
        from decimal import Decimal
        count = 0
        for dr in queryset:
            if dr.status in ['APPROVED']:
                wallet, _ = Wallet.objects.get_or_create(user=dr.user)
                wallet.available_usd = (Decimal(wallet.available_usd) + dr.amount_usd).quantize(Decimal('0.01'))
                wallet.save()
                Transaction.objects.create(wallet=wallet, type=Transaction.CREDIT, amount_usd=dr.amount_usd, meta={'type': 'deposit', 'id': dr.id, 'tx_id': dr.tx_id})
                dr.status = 'CREDITED'
                dr.processed_at = timezone.now()
                dr.save()
                count += 1
        self.message_user(request, f"Credited {count} deposit(s).")
    credit_deposits.short_description = "Credit selected deposits"