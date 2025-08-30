from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "referral_code", "referred_by", "is_approved", "is_staff")
    list_filter = ("is_approved", "is_staff")
    search_fields = ("username", "email", "referral_code")
    actions = ["approve_users", "reject_users"]

    def approve_users(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Approved {updated} user(s).")
    approve_users.short_description = "Approve selected users"

    def reject_users(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"Marked {updated} user(s) as not approved.")
    reject_users.short_description = "Reject selected users"