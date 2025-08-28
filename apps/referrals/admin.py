from django.contrib import admin
from .models import ReferralPayout

@admin.register(ReferralPayout)
class ReferralPayoutAdmin(admin.ModelAdmin):
    list_display = ("referrer", "referee", "level", "amount_usd", "created_at")
    list_filter = ("level",)