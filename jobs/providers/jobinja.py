import re
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from .common import IRAN_PROVINCES, JOB_TYPE_OPTIONS, USER_AGENT, ScrapeError

LABEL = "جابینجا"
DOMAIN = "jobinja.ir"
CITIES = IRAN_PROVINCES

_JOB_ID_RE = re.compile(r"/jobs/([^/?]+)/")


def build_url(keyword: str, city: str | None, job_types: set[str]) -> str:
    pairs: list[tuple[str, str]] = [("filters[keywords][0]", keyword)]

    if city:
        pairs.append(("filters[locations][]", city))

    index = 0
    for key in ("is_fulltime", "is_parttime"):
        if key in job_types:
            pairs.append((f"filters[job_types][{index}]", key))
            index += 1

    if "internship" in job_types:
        pairs.append(("filters[internship]", "1"))
    if "remote" in job_types:
        pairs.append(("filters[remote]", "1"))

    pairs.append(("sort_by", "published_at_desc"))
    return "https://jobinja.ir/jobs?" + urlencode(pairs)


def fetch_jobs(search_url: str) -> list[dict]:
    """Fetch the first page of a jobinja.ir search and return parsed listings.

    Newest-first sort (sort_by=published_at_desc) means page 1 is enough
    for periodic polling.
    """
    response = requests.get(search_url, headers={"User-Agent": USER_AGENT}, timeout=20)
    if response.status_code != 200:
        raise ScrapeError(f"jobinja returned status {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    listings = []

    for item in soup.select("li.c-jobListView__item"):
        title_link = item.select_one("a.c-jobListView__titleLink")
        if not title_link or not title_link.get("href"):
            continue

        job_url = title_link["href"].split("?")[0]
        match = _JOB_ID_RE.search(job_url)
        if not match:
            continue
        external_id = match.group(1)

        meta_items = item.select("ul.c-jobListView__meta li.c-jobListView__metaItem")
        meta_texts = []
        for meta_item in meta_items:
            for link in meta_item.find_all("a"):
                link.decompose()
            text = re.sub(r"\s+", " ", meta_item.get_text(strip=True))
            meta_texts.append(text)

        posted_el = item.select_one("span.c-jobListView__passedDays")

        listings.append(
            {
                "external_id": external_id,
                "title": title_link.get_text(strip=True),
                "company": meta_texts[0] if len(meta_texts) > 0 else "",
                "location": meta_texts[1] if len(meta_texts) > 1 else "",
                "contract_type": meta_texts[2] if len(meta_texts) > 2 else "",
                "posted_text": posted_el.get_text(strip=True).strip("()") if posted_el else "",
                "job_url": job_url,
            }
        )

    return listings
