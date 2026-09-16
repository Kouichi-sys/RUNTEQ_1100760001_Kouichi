from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "name", "is_staff", "created_at")
    search_fields = ("email", "name")

    # 標準のUserAdminはusername前提のため、email向けに項目を差し替える
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("個人情報", {"fields": ("name",)}),
        ("権限", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("日時", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "password1", "password2"),
        }),
    )
    readonly_fields = ("last_login", "created_at", "updated_at")
