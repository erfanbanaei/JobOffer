from urllib.parse import urlparse

from .providers import PROVIDERS
from .providers.common import ScrapeError

__all__ = ["ScrapeError", "fetch_jobs"]


def fetch_jobs(search_url: str) -> list[dict]:
    host = urlparse(search_url).netloc
    for provider in PROVIDERS.values():
        if provider.DOMAIN in host:
            return provider.fetch_jobs(search_url)
    raise ScrapeError(f"no provider registered for host: {host}")
