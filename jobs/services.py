from accounts.models import TelegramUser

from .models import SearchQuery
from .providers import PROVIDERS


def build_search_title(provider_label: str, keyword: str, city: str | None) -> str:
    if city:
        return f"{provider_label}: {keyword} ({city})"
    return f"{provider_label}: {keyword}"


def create_searches_for_providers(
    user: TelegramUser,
    keyword: str,
    city: str | None,
    provider_keys: list[str],
    job_types: set[str],
) -> list[SearchQuery]:
    created = []
    for key in provider_keys:
        provider = PROVIDERS.get(key)
        if provider is None:
            continue
        url = provider.build_url(keyword, city, job_types)
        title = build_search_title(provider.LABEL, keyword, city)
        created.append(SearchQuery.objects.create(user=user, title=title, url=url))
    return created
