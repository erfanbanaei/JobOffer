import json
import re
from datetime import date
from urllib.parse import quote

import requests

from .common import IRAN_PROVINCES, ScrapeError

LABEL = "ایران‌تلنت"
DOMAIN = "irantalent.com"
CITIES = IRAN_PROVINCES

# Pretending to be Googlebot makes irantalent's Angular Universal SSR return the
# fully rendered page (incl. an embedded ng-state JSON blob with the actual job
# results) instead of an empty client-rendered shell - this is the site's own
# dynamic-rendering-for-SEO behavior, not a bypass of any access control.
_GOOGLEBOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

# Confirmed against the live site's location lookup table (irantalent only
# lists provinces that currently have postings, so a handful are missing -
# those just silently skip the city filter in build_url).
_PROVINCE_SLUGS = {
    "تهران": "tehran",
    "خراسان رضوی": "khorasan-razavi",
    "البرز": "alborz",
    "اصفهان": "isfahan",
    "مازندران": "mazandaran",
    "فارس": "fars",
    "آذربایجان شرقی": "azerbaijan-east",
    "خوزستان": "khouzestan",
    "هرمزگان": "hormozgan",
    "بوشهر": "bushehr",
    "قزوین": "qazvin",
    "کرمان": "kerman",
    "اردبیل": "ardabil",
    "گیلان": "gilan",
    "کرمانشاه": "kermaanshah",
    "یزد": "yazd",
    "زنجان": "zanjan",
    "مرکزی": "markazi",
    "گلستان": "golestan",
    "قم": "qom",
    "کردستان": "kurdistan",
    "همدان": "hamadan",
    "سمنان": "semnan",
    "آذربایجان غربی": "azerbaijan-west",
    "سیستان و بلوچستان": "sistan-and-baluchestan",
    "چهارمحال و بختیاری": "chahar-mahaal-and-bakhtiari",
    "خراسان جنوبی": "khorasan-south",
    "لرستان": "lorestan",
}

_NG_STATE_RE = re.compile(
    r'<script id="ng-state" type="application/json">(.*?)</script>', re.S
)


def build_url(keyword: str, city: str | None, job_types: set[str]) -> str:
    segments = []

    slug_city = _PROVINCE_SLUGS.get(city) if city else None
    if slug_city:
        segments.append(f"in-{slug_city}")

    for key, token in (("is_fulltime", "Full-Time"), ("is_parttime", "Part-Time")):
        if key in job_types:
            segments.append(f"in-{token}-employment-type-level")

    if "internship" in job_types:
        segments.append("jobs-for-student-fresh-graduate")
    if "remote" in job_types:
        segments.append("work-type-remote")

    path = "jobs-" + "-".join(segments) if segments else "search"
    return f"https://www.irantalent.com/jobs/{path}?keyword={quote(keyword)}"


def _posted_text(created_at: str | None) -> str:
    if not created_at:
        return ""
    try:
        created = date.fromisoformat(created_at[:10])
    except ValueError:
        return ""
    days = (date.today() - created).days
    if days <= 0:
        return "امروز"
    return f"{days} روز پیش"


def fetch_jobs(search_url: str) -> list[dict]:
    response = requests.get(search_url, headers={"User-Agent": _GOOGLEBOT_UA}, timeout=25)
    if response.status_code != 200:
        raise ScrapeError(f"irantalent returned status {response.status_code}")

    match = _NG_STATE_RE.search(response.text)
    if not match:
        raise ScrapeError("irantalent ng-state blob not found (page may not have prerendered)")

    try:
        ng_state = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ScrapeError(f"irantalent ng-state JSON parse failed: {exc}") from exc

    ssr_result = ng_state.get("serverSideSearchResult") or {}
    raw_jobs = (ssr_result.get("data") or {}).get("data") or []

    listings = []
    for job in raw_jobs:
        brand = job.get("brand_data") or {}
        employment_type = job.get("employment_type") or {}

        contract_bits = []
        if employment_type.get("title_farsi"):
            contract_bits.append(employment_type["title_farsi"])
        if job.get("work_type") == "remote":
            contract_bits.append("دورکاری")

        listings.append(
            {
                "external_id": str(job["id"]),
                "title": job.get("title_farsi") or job.get("title", ""),
                "company": brand.get("name_fa") or brand.get("company_legal_name_fa") or "",
                "location": job.get("location_text_farsi") or "",
                "contract_type": " | ".join(contract_bits),
                "posted_text": _posted_text(job.get("created_at")),
                "job_url": f"https://www.irantalent.com/job/{job.get('slug', '')}/{job['id']}",
                "_created_at": job.get("created_at") or "",
            }
        )

    listings.sort(key=lambda j: j.pop("_created_at"), reverse=True)
    return listings
