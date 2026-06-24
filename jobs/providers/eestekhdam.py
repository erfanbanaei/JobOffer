import re
from urllib.parse import quote

import requests

from .common import IRAN_PROVINCES, USER_AGENT, ScrapeError

LABEL = "ای‌استخدام"
DOMAIN = "e-estekhdam.com"
CITIES = IRAN_PROVINCES

SEARCH_API = "https://www.e-estekhdam.com/search-api/search"
SLUG_PARAMS_API = "https://www.e-estekhdam.com/search-api/search/slug-params"

# Canonical job-type key -> e-estekhdam slug token (also valid as a "contract"
# filter value in the search API body - confirmed against the live site).
_TYPE_TOKENS = {
    "is_fulltime": "تمام-وقت",
    "is_parttime": "پاره-وقت",
    "internship": "کارآموزی",
    "remote": "دورکاری",
}
_ORDER = ("is_fulltime", "is_parttime", "internship", "remote")

_SLUG_RE = re.compile(r"/search/([^/?]+)")


def build_url(keyword: str, city: str | None, job_types: set[str]) -> str:
    parts = ["استخدام"]
    if city:
        parts.append(f"در-{city.replace(' ', '-')}")

    tokens = [_TYPE_TOKENS[key] for key in _ORDER if key in job_types]
    if tokens:
        parts.append("بصورت-" + "--".join(tokens))

    parts.append(f"برای-{keyword}")
    slug = "-".join(parts)
    return f"https://www.e-estekhdam.com/search/{quote(slug)}?sort={quote('جدیدترین')}"


def fetch_jobs(search_url: str) -> list[dict]:
    match = _SLUG_RE.search(search_url)
    if not match:
        raise ScrapeError("could not parse e-estekhdam search slug from URL")
    slug = match.group(1)

    headers = {"User-Agent": USER_AGENT}

    params_response = requests.get(f"{SLUG_PARAMS_API}/{slug}", headers=headers, timeout=20)
    if params_response.status_code != 200:
        raise ScrapeError(f"e-estekhdam slug-params returned status {params_response.status_code}")
    params_body = params_response.json()
    if not params_body.get("ok"):
        raise ScrapeError(f"e-estekhdam slug-params error: {params_body}")

    payload = dict(params_body.get("data") or {})
    payload["sort"] = "جدیدترین"

    response = requests.post(
        SEARCH_API,
        json=payload,
        headers={**headers, "Content-Type": "application/json"},
        timeout=20,
    )
    if response.status_code not in (200, 201):
        raise ScrapeError(f"e-estekhdam search returned status {response.status_code}")

    body = response.json()
    if not body.get("ok"):
        raise ScrapeError(f"e-estekhdam search error: {body}")

    listings = []
    for job in body.get("data") or []:
        provinces = job.get("provinces") or []
        location = job.get("location") or (provinces[0] if provinces else "")
        contract = job.get("contract") or []

        listings.append(
            {
                "external_id": str(job["id"]),
                "title": job.get("short_title") or job.get("title", ""),
                "company": job.get("brand_name") or "",
                "location": location or "",
                "contract_type": " | ".join(contract),
                "posted_text": "جدید" if job.get("is_new") else "",
                "job_url": "https://www.e-estekhdam.com" + job.get("url", ""),
            }
        )

    return listings
