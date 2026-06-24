from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from bot.keyboards import CHANNEL_USERNAME, SUPPORT_USERNAME
from jobs.providers import IRAN_PROVINCES, JOB_TYPE_OPTIONS, PROVIDERS
from jobs.services import create_searches_for_providers

from .decorators import parse_json_body, telegram_auth
from .telegram_api import is_channel_member


def index(request):
    return render(request, "webapp/index.html")


def _serialize_search(search_query) -> dict:
    return {
        "id": search_query.id,
        "title": search_query.title,
        "url": search_query.url,
        "is_active": search_query.is_active,
    }


def _serialize_user(user) -> dict:
    return {
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username or "",
        "chat_id": user.chat_id,
    }


@require_GET
@telegram_auth
def bootstrap(request):
    user = request.telegram_user
    searches = list(user.search_queries.order_by("id"))

    return JsonResponse(
        {
            "user": _serialize_user(user),
            "is_channel_member": is_channel_member(user.chat_id),
            "channel_username": CHANNEL_USERNAME,
            "support_username": SUPPORT_USERNAME,
            "providers": [{"key": key, "label": p.LABEL} for key, p in PROVIDERS.items()],
            "cities": IRAN_PROVINCES,
            "job_types": [{"key": key, "label": label} for key, label in JOB_TYPE_OPTIONS],
            "searches": [_serialize_search(s) for s in searches],
            "active_search_count": sum(1 for s in searches if s.is_active),
        }
    )


@csrf_exempt
@require_POST
@telegram_auth
def create_searches(request):
    user = request.telegram_user
    body = parse_json_body(request)

    keyword = (body.get("keyword") or "").strip()
    city = body.get("city") or None
    provider_keys = [key for key in body.get("providers") or [] if key in PROVIDERS]
    job_types = {key for key, _ in JOB_TYPE_OPTIONS if key in (body.get("job_types") or [])}

    if not keyword or not provider_keys:
        return JsonResponse({"error": "keyword_and_providers_required"}, status=400)

    created = create_searches_for_providers(user, keyword, city, provider_keys, job_types)
    return JsonResponse({"created": [_serialize_search(s) for s in created]})


@csrf_exempt
@require_POST
@telegram_auth
def toggle_search(request, search_id: int):
    user = request.telegram_user
    search_query = user.search_queries.filter(id=search_id).first()
    if search_query is None:
        return JsonResponse({"error": "not_found"}, status=404)

    search_query.is_active = not search_query.is_active
    search_query.save(update_fields=["is_active"])
    return JsonResponse({"search": _serialize_search(search_query)})


@csrf_exempt
@require_POST
@telegram_auth
def delete_search(request, search_id: int):
    user = request.telegram_user
    deleted, _ = user.search_queries.filter(id=search_id).delete()
    if not deleted:
        return JsonResponse({"error": "not_found"}, status=404)
    return JsonResponse({"ok": True})
