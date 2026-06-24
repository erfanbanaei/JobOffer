import requests
from django.conf import settings

from bot.keyboards import CHANNEL_USERNAME


def is_channel_member(user_id: int) -> bool:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getChatMember"
    proxies = None
    if settings.TELEGRAM_PROXY_URL:
        proxies = {"http": settings.TELEGRAM_PROXY_URL, "https": settings.TELEGRAM_PROXY_URL}

    try:
        response = requests.get(
            url,
            params={"chat_id": f"@{CHANNEL_USERNAME}", "user_id": user_id},
            proxies=proxies,
            timeout=10,
        )
        body = response.json()
    except (requests.RequestException, ValueError):
        return False

    if not body.get("ok"):
        return False

    status = body.get("result", {}).get("status")
    return status not in (None, "left", "kicked")
