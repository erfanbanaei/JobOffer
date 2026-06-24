import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

MAX_INIT_DATA_AGE_SECONDS = 24 * 60 * 60


def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """Validate a Telegram Mini App initData string against the bot token.

    Per https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    Returns the parsed payload (with "user" decoded to a dict) on success, None otherwise.
    """
    if not init_data:
        return None

    pairs = parse_qsl(init_data, keep_blank_values=True)
    data = dict(pairs)
    received_hash = data.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    auth_date = data.get("auth_date")
    if auth_date:
        try:
            if time.time() - int(auth_date) > MAX_INIT_DATA_AGE_SECONDS:
                return None
        except ValueError:
            return None

    user_raw = data.get("user")
    try:
        user = json.loads(user_raw) if user_raw else None
    except json.JSONDecodeError:
        return None

    return {"user": user, "auth_date": auth_date, "raw": data}
