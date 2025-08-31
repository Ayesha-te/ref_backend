from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from apps.wallets.models import Wallet, DepositRequest
from apps.withdrawals.models import WithdrawalRequest
from .models import SignupProof
from apps.referrals.models import ReferralPayout

User = get_user_model()

class WalletInline(admin.StackedInline):
    model = Wallet
    can_delete = False
    fk_name = 'user'
    extra = 0
    fields = ('available_usd', 'hold_usd')

class DepositRequestInline(admin.TabularInline):
    model = DepositRequest
    extra = 0
    fields = ('amount_pkr','amount_usd','tx_id','status','created_at')
    readonly_fields = ('created_at',)

class WithdrawalRequestInline(admin.TabularInline):
    model = WithdrawalRequest
    extra = 0
    fields = ('amount_pkr','amount_usd','method','tx_id','status','created_at')
    readonly_fields = ('created_at',)

class SignupProofInline(admin.TabularInline):
    model = SignupProof
    extra = 0
    fields = ('amount_pkr','tx_id','proof_preview','status','created_at')
    readonly_fields = ('proof_preview','created_at')

    def proof_preview(self, obj):
        if obj.proof_image and hasattr(obj.proof_image, 'url'):
            return format_html('<a href="{}" target="_blank"><img src="{}" style="max-height:60px;"/></a>', obj.proof_image.url, obj.proof_image.url)
        return ""
    proof_preview.short_description = "Proof"

class ReferralPayoutAsReferrerInline(admin.TabularInline):
    model = ReferralPayout
    fk_name = 'referrer'
    extra = 0
    fields = ('referee','level','amount_usd','created_at')
    readonly_fields = ('created_at',)

class ReferralPayoutAsRefereeInline(admin.TabularInline):
    model = ReferralPayout
    fk_name = 'referee'
    extra = 0
    fields = ('referrer','level','amount_usd','created_at')
    readonly_fields = ('created_at',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "referral_code", "referred_by", "referral_count", "is_approved", "is_staff", "wallet_available", "wallet_hold")
    list_filter = ("is_approved", "is_staff")
    search_fields = ("username", "email", "referral_code")
    actions = ["approve_users", "reject_users"]
    inlines = [WalletInline, SignupProofInline, DepositRequestInline, WithdrawalRequestInline, ReferralPayoutAsReferrerInline, ReferralPayoutAsRefereeInline]

    def referral_count(self, obj):
        return obj.referrals.count()
    referral_count.short_description = "Referrals"

    def wallet_available(self, obj):
        try:
            return obj.wallet.available_usd
        except Wallet.DoesNotExist:
            return 0
    wallet_available.short_description = "Avail USD"

    def wallet_hold(self, obj):
        try:
            return obj.wallet.hold_usd
        except Wallet.DoesNotExist:
            return 0
    wallet_hold.short_description = "Hold USD"

    def approve_users(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Approved {updated} user(s).")
    approve_users.short_description = "Approve selected users"

    def reject_users(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"Marked {updated} user(s) as not approved.")
    reject_users.short_description = "Reject selected users"

@admin.register(SignupProof)
class SignupProofAdmin(admin.ModelAdmin):
    list_display = ('user','amount_pkr','tx_id','proof_preview','status','created_at')
    list_filter = ('status',)
    search_fields = ('user__email','user__username','tx_id')
    readonly_fields = ('proof_preview',)

    def proof_preview(self, obj):
        if obj.proof_image and hasattr(obj.proof_image, 'url'):
            return format_html('<a href="{}" target="_blank"><img src="{}" style="max-height:60px;"/></a>', obj.proof_image.url, obj.proof_image.url)
        return ""
    proof_preview.short_description = "Proof"