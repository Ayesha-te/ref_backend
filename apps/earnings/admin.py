from django.contrib import admin
from .models import PassiveEarning, DailyEarningsState, GlobalPoolState, GlobalPoolCollection, GlobalPoolDistribution

@admin.register(PassiveEarning)
class PassiveEarningAdmin(admin.ModelAdmin):
    list_display = ("user", "day_index", "percent", "amount_usd", "created_at")
    list_filter = ("day_index",)

@admin.register(DailyEarningsState)
class DailyEarningsStateAdmin(admin.ModelAdmin):
    list_display = ("last_processed_date", "last_processed_at")

@admin.register(GlobalPoolState)
class GlobalPoolStateAdmin(admin.ModelAdmin):
    list_display = ("current_pool_usd", "last_collection_date", "last_distribution_date", "total_collected_all_time", "total_distributed_all_time")
    readonly_fields = ("updated_at",)

@admin.register(GlobalPoolCollection)
class GlobalPoolCollectionAdmin(admin.ModelAdmin):
    list_display = ("user", "signup_amount_usd", "collection_amount_usd", "collection_date", "created_at")
    list_filter = ("collection_date",)
    search_fields = ("user__username", "user__email")

@admin.register(GlobalPoolDistribution)
class GlobalPoolDistributionAdmin(admin.ModelAdmin):
    list_display = ("user", "amount_usd", "distribution_date", "total_pool_amount", "total_users", "created_at")
    list_filter = ("distribution_date",)
    search_fields = ("user__username", "user__email")