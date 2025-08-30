from decimal import Decimal
from django.contrib import admin
from django.utils import timezone
from .models import WithdrawalRequest
from apps.wallets.models import Transaction

@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "amount_usd", "amount_pkr", "status", "created_at")
    list_filter = ("status",)
    actions = ["approve_withdrawals", "reject_withdrawals", "mark_paid_withdrawals"]

    def approve_withdrawals(self, request, queryset):
        updated = queryset.update(status='APPROVED', processed_at=timezone.now())
        self.message_user(request, f"Approved {updated} withdrawal(s).")
    approve_withdrawals.short_description = "Approve selected withdrawals"

    def reject_withdrawals(self, request, queryset):
        count = 0
        for wr in queryset:
            if wr.status in ['PENDING', 'APPROVED']:
                wallet = wr.user.wallet
                wallet.available_usd = (Decimal(wallet.available_usd) + wr.amount_usd).quantize(Decimal('0.01'))
                wallet.save()
                wr.status = 'REJECTED'
                wr.processed_at = timezone.now()
                wr.save()
                count += 1
        self.message_user(request, f"Rejected and refunded {count} withdrawal(s).")
    reject_withdrawals.short_description = "Reject and refund selected withdrawals"

    def mark_paid_withdrawals(self, request, queryset):
        count = 0
        for wr in queryset:
            if wr.status in ['APPROVED']:
                wallet = wr.user.wallet
                Transaction.objects.create(
                    wallet=wallet,
                    type=Transaction.DEBIT,
                    amount_usd=wr.net_usd,
                    meta={'type': 'withdrawal', 'id': wr.id}
                )
                wr.status = 'PAID'
                wr.processed_at = timezone.now()
                wr.save()
                count += 1
        self.message_user(request, f"Marked {count} withdrawal(s) as paid.")
    mark_paid_withdrawals.short_description = "Mark selected withdrawals as PAID"