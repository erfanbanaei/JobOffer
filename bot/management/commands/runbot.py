import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonDefault, MenuButtonWebApp, WebAppInfo
from django.conf import settings
from django.core.management.base import BaseCommand

from bot.handlers import router
from bot.middlewares import ChannelMembershipMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the Telegram bot with long polling (aiogram)"

    def handle(self, *args, **options):
        asyncio.run(self._run())

    async def _run(self):
        session = AiohttpSession(proxy=settings.TELEGRAM_PROXY_URL) if settings.TELEGRAM_PROXY_URL else None
        bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            session=session,
        )
        dispatcher = Dispatcher()

        membership_middleware = ChannelMembershipMiddleware()
        dispatcher.message.outer_middleware(membership_middleware)
        dispatcher.callback_query.outer_middleware(membership_middleware)

        dispatcher.include_router(router)

        await bot.set_my_commands(
            [
                BotCommand(command="start", description="شروع کار با ربات"),
                BotCommand(command="help", description="راهنمای استفاده"),
            ]
        )

        if settings.MINI_APP_URL.startswith("https://"):
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text="اپلیکیشن", web_app=WebAppInfo(url=settings.MINI_APP_URL))
            )
        else:
            await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
            logger.warning("MINI_APP_URL is not set to an https:// URL - mini app menu button disabled")

        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot started polling")
        await dispatcher.start_polling(bot)
