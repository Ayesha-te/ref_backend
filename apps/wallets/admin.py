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
    list_display = ("user", "amount_pkr", "amount_usd", "tx_id", "proof_preview", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("proof_preview",)
    search_fields = ("user__email", "user__username", "tx_id")
    actions = ["approve_deposits", "reject_deposits", "credit_deposits"]

    def proof_preview(self, obj):
        if obj.proof_image and hasattr(obj.proof_image, 'url'):
            return f'<a href="{obj.proof_image.url}" target="_blank"><img src="{obj.proof_image.url}" style="max-height:60px;"/></a>'
        return ""
    proof_preview.allow_tags = True
    proof_preview.short_description = "Proof"

    def approve_deposits(self, request, queryset):
        # Approve and immediately credit to avoid confusion
        from decimal import Decimal
        from apps.referrals.models import ReferralPayout
        from apps.referrals.services import pay_on_package_purchase
        count = 0
        for dr in queryset:
            if dr.status in ['PENDING', 'APPROVED']:
                wallet, _ = Wallet.objects.get_or_create(user=dr.user)
                wallet.available_usd = (Decimal(wallet.available_usd) + dr.amount_usd).quantize(Decimal('0.01'))
                wallet.save()
                Transaction.objects.create(wallet=wallet, type=Transaction.CREDIT, amount_usd=dr.amount_usd, meta={'type': 'deposit', 'id': dr.id, 'tx_id': dr.tx_id})
                # referral payouts once per buyer
                try:
                    has_payout = ReferralPayout.objects.filter(referee=dr.user).exists()
                    if not has_payout and getattr(dr.user, 'referred_by', None):
                        pay_on_package_purchase(dr.user)
                except Exception:
                    pass
                dr.status = 'CREDITED'
                dr.processed_at = timezone.now()
                dr.save()
                count += 1
        self.message_user(request, f"Approved and credited {count} deposit(s).")
    approve_deposits.short_description = "Approve & Credit selected deposits"

    def reject_deposits(self, request, queryset):
        updated = queryset.update(status='REJECTED', processed_at=timezone.now())
        self.message_user(request, f"Rejected {updated} deposit(s).")
    reject_deposits.short_description = "Reject selected deposits"

    def credit_deposits(self, request, queryset):
        from decimal import Decimal
        from apps.referrals.models import ReferralPayout
        from apps.referrals.services import pay_on_package_purchase
        count = 0
        for dr in queryset:
            if dr.status in ['APPROVED']:
                wallet, _ = Wallet.objects.get_or_create(user=dr.user)
                wallet.available_usd = (Decimal(wallet.available_usd) + dr.amount_usd).quantize(Decimal('0.01'))
                wallet.save()
                Transaction.objects.create(wallet=wallet, type=Transaction.CREDIT, amount_usd=dr.amount_usd, meta={'type': 'deposit', 'id': dr.id, 'tx_id': dr.tx_id})
                # trigger referral payouts once on first credited deposit
                try:
                    has_payout = ReferralPayout.objects.filter(referee=dr.user).exists()
                    if not has_payout and getattr(dr.user, 'referred_by', None):
                        pay_on_package_purchase(dr.user)
                except Exception:
                    pass
                dr.status = 'CREDITED'
                dr.processed_at = timezone.now()
                dr.save()
                count += 1
        self.message_user(request, f"Credited {count} deposit(s).")
    credit_deposits.short_description = "Credit selected deposits"