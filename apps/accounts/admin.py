from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "referral_code", "referred_by", "is_approved", "is_staff")
    list_filter = ("is_approved", "is_staff")
    search_fields = ("username", "email", "referral_code")