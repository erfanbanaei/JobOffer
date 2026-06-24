from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, TelegramObject

from .keyboards import CHANNEL_USERNAME, join_channel_keyboard

JOIN_PROMPT_TEXT = (
    "برای استفاده از ربات، اول باید عضو کانال ما بشی:\n"
    f"👉 @{CHANNEL_USERNAME}\n\n"
    "بعد از عضویت، روی دکمه‌ی «عضو شدم، بررسی کن» بزن."
)


async def is_channel_member(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
    except TelegramBadRequest:
        return False
    return member.status not in ("left", "kicked")


class ChannelMembershipMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        bot = data["bot"]
        user = data.get("event_from_user")

        if user is None or await is_channel_member(bot, user.id):
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer("اول باید عضو کانال بشی!", show_alert=True)
            if event.message:
                await event.message.answer(JOIN_PROMPT_TEXT, reply_markup=join_channel_keyboard())
        elif isinstance(event, Message):
            await event.answer(JOIN_PROMPT_TEXT, reply_markup=join_channel_keyboard())

        return None
