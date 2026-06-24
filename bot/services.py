from asgiref.sync import sync_to_async

from accounts.models import TelegramUser
from jobs.models import SearchQuery


@sync_to_async
def get_or_create_user(
    chat_id: int, username: str | None, first_name: str | None, last_name: str | None
) -> TelegramUser:
    user, _ = TelegramUser.objects.update_or_create(
        chat_id=chat_id,
        defaults={
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": True,
        },
    )
    return user


@sync_to_async
def get_user(chat_id: int) -> TelegramUser | None:
    return TelegramUser.objects.filter(chat_id=chat_id).first()


@sync_to_async
def create_search_query(user: TelegramUser, title: str, url: str) -> SearchQuery:
    return SearchQuery.objects.create(user=user, title=title, url=url)


@sync_to_async
def list_search_queries(user: TelegramUser) -> list[SearchQuery]:
    return list(user.search_queries.order_by("id"))


@sync_to_async
def active_search_count(user: TelegramUser) -> int:
    return user.search_queries.filter(is_active=True).count()


@sync_to_async
def delete_search_query(user: TelegramUser, search_query_id: int) -> bool:
    deleted, _ = SearchQuery.objects.filter(id=search_query_id, user=user).delete()
    return deleted > 0


@sync_to_async
def toggle_search_query(user: TelegramUser, search_query_id: int) -> SearchQuery | None:
    search_query = SearchQuery.objects.filter(id=search_query_id, user=user).first()
    if search_query is None:
        return None
    search_query.is_active = not search_query.is_active
    search_query.save(update_fields=["is_active"])
    return search_query
