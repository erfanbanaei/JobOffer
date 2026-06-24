from django.contrib import admin

from .models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "username", "first_name", "last_name", "is_active", "created_at")
    search_fields = ("chat_id", "username", "first_name", "last_name")
    list_filter = ("is_active",)
