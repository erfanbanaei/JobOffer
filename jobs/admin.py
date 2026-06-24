from django.contrib import admin

from .models import JobPosting, SearchQuery


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title", "url", "user__username", "user__chat_id")


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "search_query", "notified", "found_at")
    list_filter = ("notified", "search_query")
    search_fields = ("title", "company", "external_id")
