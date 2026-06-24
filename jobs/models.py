from django.db import models

from accounts.models import TelegramUser


class SearchQuery(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name="search_queries")
    title = models.CharField(max_length=128, help_text="Friendly name, e.g. 'Flutter - Tehran'")
    url = models.URLField(max_length=1000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user})"


class JobPosting(models.Model):
    search_query = models.ForeignKey(SearchQuery, on_delete=models.CASCADE, related_name="postings")
    external_id = models.CharField(max_length=64)
    title = models.CharField(max_length=512)
    company = models.CharField(max_length=256, blank=True)
    location = models.CharField(max_length=256, blank=True)
    contract_type = models.CharField(max_length=128, blank=True)
    posted_text = models.CharField(max_length=64, blank=True)
    job_url = models.URLField(max_length=1000)
    found_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["search_query", "external_id"], name="uniq_job_per_search")
        ]
        ordering = ["-found_at"]

    def __str__(self):
        return self.title
