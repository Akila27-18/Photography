# core/admin.py
from django.contrib import admin
from .models import LoginPageConfig


@admin.register(LoginPageConfig)
class LoginPageConfigAdmin(admin.ModelAdmin):
    list_display = (
        "welcome_text",
        "admin_label",
        "forgot_text",
        "remember_me_enabled",
    )

    def has_add_permission(self, request):
        # Allow only ONE row
        return not LoginPageConfig.objects.exists()