import functools
import json

from django.conf import settings
from django.http import JsonResponse

from accounts.models import TelegramUser

from .auth import validate_init_data


def telegram_auth(view_func):
    """Validates the X-Telegram-Init-Data header and attaches request.telegram_user
    (a TelegramUser instance, created/updated from the validated payload)."""

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        init_data = request.headers.get("X-Telegram-Init-Data", "")
        payload = validate_init_data(init_data, settings.TELEGRAM_BOT_TOKEN)
        if payload is None or not payload.get("user"):
            return JsonResponse({"error": "invalid_init_data"}, status=401)

        tg_user = payload["user"]
        user, _ = TelegramUser.objects.update_or_create(
            chat_id=tg_user["id"],
            defaults={
                "username": tg_user.get("username"),
                "first_name": tg_user.get("first_name"),
                "last_name": tg_user.get("last_name"),
                "is_active": True,
            },
        )
        request.telegram_user = user
        return view_func(request, *args, **kwargs)

    return wrapper


def parse_json_body(request) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return {}
