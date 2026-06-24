import logging
from html import escape

import requests
from celery import shared_task
from django.conf import settings

from .models import JobPosting, SearchQuery
from .scraper import ScrapeError, fetch_jobs

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: int, text: str, job_url: str) -> None:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    proxies = None
    if settings.TELEGRAM_PROXY_URL:
        proxies = {"http": settings.TELEGRAM_PROXY_URL, "https": settings.TELEGRAM_PROXY_URL}
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[{"text": "🔗 مشاهده و ارسال رزومه", "url": job_url}]]
        },
    }
    response = requests.post(url, json=payload, timeout=15, proxies=proxies)
    response.raise_for_status()


def _notify(search_query: SearchQuery, posting: JobPosting) -> None:
    text = (
        f"\U0001f4bc <b>{escape(posting.title)}</b>\n"
        f"\U0001f3e2 {escape(posting.company)}\n"
        f"\U0001f4cd {escape(posting.location)}\n"
        f"\U0001f550 {escape(posting.posted_text)}"
    )
    try:
        send_telegram_message(search_query.user.chat_id, text, posting.job_url)
        posting.notified = True
        posting.save(update_fields=["notified"])
    except requests.RequestException as exc:
        logger.warning("Failed to notify chat_id=%s: %s", search_query.user.chat_id, exc)


@shared_task
def check_search_query(search_query_id: int) -> None:
    try:
        search_query = SearchQuery.objects.select_related("user").get(
            id=search_query_id, is_active=True
        )
    except SearchQuery.DoesNotExist:
        return

    try:
        listings = fetch_jobs(search_query.url)
    except ScrapeError as exc:
        logger.warning("Scrape failed for search_query=%s: %s", search_query_id, exc)
        return

    is_first_scan = not JobPosting.objects.filter(search_query=search_query).exists()

    new_postings = []
    for job in listings:
        posting, created = JobPosting.objects.get_or_create(
            search_query=search_query, external_id=job["external_id"], defaults=job
        )
        if created:
            new_postings.append(posting)

    if is_first_scan:
        # Listings are newest-first, so only the first one is worth notifying about;
        # the rest become a silent baseline so future scans don't re-flood old postings.
        to_notify, baseline = new_postings[:1], new_postings[1:]
        if baseline:
            JobPosting.objects.filter(id__in=[p.id for p in baseline]).update(notified=True)
    else:
        to_notify = new_postings

    for posting in to_notify:
        _notify(search_query, posting)


@shared_task
def scan_active_search_queries() -> None:
    search_query_ids = list(
        SearchQuery.objects.filter(is_active=True, user__is_active=True).values_list(
            "id", flat=True
        )
    )
    for search_query_id in search_query_ids:
        check_search_query.delay(search_query_id)
