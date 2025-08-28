from django.contrib import admin
from .models import PassiveEarning
from .models_global_pool import GlobalPool, GlobalPoolPayout

@admin.register(PassiveEarning)
class PassiveEarningAdmin(admin.ModelAdmin):
    list_display = ("user", "day_index", "percent", "amount_usd", "created_at")
    list_filter = ("day_index",)

@admin.register(GlobalPool)
class GlobalPoolAdmin(admin.ModelAdmin):
    list_display = ("id", "balance_usd", "updated_at")

@admin.register(GlobalPoolPayout)
class GlobalPoolPayoutAdmin(admin.ModelAdmin):
    list_display = ("amount_usd", "distributed_on")