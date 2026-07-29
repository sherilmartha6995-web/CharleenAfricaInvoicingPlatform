from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, AuditLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ( "username", "email", "first_name", "last_name")
    ordering = ("username",)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "business", "user", "action", "model_name", "object_repr",)
    list_filter = ("business", "action", "model_name", "timestamp")
    search_fields = ("user__username", "object_repr", "description")
    readonly_fields = ("business", "user", "action", "model_name", "object_id", "object_repr", "description", "ip_address", "timestamp")
    ordering = ("-timestamp",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
