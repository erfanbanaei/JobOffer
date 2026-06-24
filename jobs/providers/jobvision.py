import re
from urllib.parse import quote

import requests

from .common import IRAN_PROVINCES, JOB_TYPE_OPTIONS, USER_AGENT, ScrapeError

LABEL = "جاب‌ویژن"
DOMAIN = "jobvision.ir"
CITIES = IRAN_PROVINCES

API_URL = "https://candidateapi.jobvision.ir/api/v1/JobPost/List"

# Maps our canonical province names to jobvision's location-wrapper slug
# (the value its search API expects in the "LocationWrapper" field).
_PROVINCE_SLUGS = {
    "آذربایجان شرقی": "all-cities-of-azarbayjan-sharghi",
    "آذربایجان غربی": "all-cities-of-azarbayjan-gharbi",
    "اردبیل": "all-cities-of-ardabil",
    "اصفهان": "all-cities-of-isfahan",
    "البرز": "all-cities-of-alborz",
    "ایلام": "all-cities-of-ilam",
    "بوشهر": "all-cities-of-booshehr",
    "تهران": "all-cities-of-tehran",
    "چهارمحال و بختیاری": "all-cities-of-chaharmahal-&-bakhtiari",
    "خراسان جنوبی": "all-cities-of-khorasan-jonoobi",
    "خراسان رضوی": "all-cities-of-khorasan-razavi",
    "خراسان شمالی": "all-cities-of-khorasan-shomali",
    "خوزستان": "all-cities-of-khoozestan",
    "زنجان": "all-cities-of-zanjan",
    "سمنان": "all-cities-of-semnan",
    "سیستان و بلوچستان": "all-cities-of-sistan-&-baluchestan",
    "فارس": "all-cities-of-fars",
    "قزوین": "all-cities-of-ghazvin",
    "قم": "all-cities-of-ghom",
    "کردستان": "all-cities-of-kodestan",
    "کرمان": "all-cities-of-kerman",
    "کرمانشاه": "all-cities-of-kermanshah",
    "کهگیلویه و بویراحمد": "all-cities-of-kohgilooye-&-boyerahmad",
    "گلستان": "all-cities-of-golestan",
    "گیلان": "all-cities-of-gilan",
    "لرستان": "all-cities-of-lorestan",
    "مازندران": "all-cities-of-mazandaran",
    "مرکزی": "all-cities-of-markazi",
    "هرمزگان": "all-cities-of-hormozgan",
    "همدان": "all-cities-of-hamedan",
    "یزد": "all-cities-of-yazd",
}

# Canonical job-type key -> jobvision URL path token (used in /type/<a>-and-<b>).
_TYPE_URL_TOKENS = {
    "is_fulltime": "full-time",
    "is_parttime": "part-time",
    "internship": "internship",
    "remote": "remote",
}
_TYPE_TOKEN_TO_KEY = {v: k for k, v in _TYPE_URL_TOKENS.items()}

_KEYWORD_RE = re.compile(r"/jobs/keyword/([^/?]+)")
_CATEGORY_RE = re.compile(r"/category/in-([^/?]+)")
_TYPE_RE = re.compile(r"/type/([^/?]+)")


def build_url(keyword: str, city: str | None, job_types: set[str]) -> str:
    url = f"https://jobvision.ir/jobs/keyword/{quote(keyword)}"

    if city:
        slug = _PROVINCE_SLUGS.get(city)
        if slug:
            url += f"/category/in-{slug}"

    tokens = [_TYPE_URL_TOKENS[key] for key in ("remote", "internship", "is_fulltime", "is_parttime") if key in job_types]
    if tokens:
        url += "/type/" + "-and-".join(tokens)

    return url + "?page=1&sort=0"


def _parse_url(search_url: str) -> tuple[str, str | None, set[str]]:
    keyword_match = _KEYWORD_RE.search(search_url)
    keyword = keyword_match.group(1) if keyword_match else ""

    category_match = _CATEGORY_RE.search(search_url)
    location_wrapper = category_match.group(1) if category_match else None

    type_match = _TYPE_RE.search(search_url)
    job_types: set[str] = set()
    if type_match:
        for token in type_match.group(1).split("-and-"):
            key = _TYPE_TOKEN_TO_KEY.get(token)
            if key:
                job_types.add(key)

    return keyword, location_wrapper, job_types


def fetch_jobs(search_url: str) -> list[dict]:
    keyword, location_wrapper, job_types = _parse_url(search_url)

    payload: dict = {"Keyword": keyword, "PageNumber": 1, "PageSize": 20}
    if location_wrapper:
        payload["LocationWrapper"] = location_wrapper
    work_types = [_TYPE_URL_TOKENS[k] for k in ("is_fulltime", "is_parttime") if k in job_types]
    if work_types:
        payload["WorkTypes"] = work_types
    if "internship" in job_types:
        payload["IsInternship"] = True
    if "remote" in job_types:
        payload["IsRemote"] = True

    response = requests.post(
        API_URL,
        json=payload,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
        timeout=20,
    )
    if response.status_code != 200:
        raise ScrapeError(f"jobvision returned status {response.status_code}")

    body = response.json()
    if not body.get("isSuccess"):
        raise ScrapeError(f"jobvision API error: {body.get('message')}")

    listings = []
    for job in body.get("data", {}).get("jobPosts", []):
        company = job.get("company") or {}
        location = job.get("location") or {}
        province = (location.get("province") or {}).get("titleFa") or ""
        city = (location.get("city") or {}).get("titleFa") or ""
        properties = job.get("properties") or {}
        work_type = (job.get("workType") or {}).get("titleFa") or ""

        contract_bits = [bit for bit in [work_type] if bit]
        if properties.get("isRemote"):
            contract_bits.append("دورکاری")
        if properties.get("isInternship"):
            contract_bits.append("کارآموزی")

        activation = job.get("activationTime") or {}

        listings.append(
            {
                "external_id": str(job["id"]),
                "title": job.get("title", ""),
                "company": company.get("nameFa") or company.get("nameEn") or "",
                "location": "، ".join(bit for bit in [province, city] if bit),
                "contract_type": " | ".join(contract_bits),
                "posted_text": activation.get("beautifyFa", ""),
                "job_url": f"https://jobvision.ir/jobs/{job['id']}",
            }
        )

    return listings
