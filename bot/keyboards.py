from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from jobs.models import SearchQuery
from jobs.providers import IRAN_PROVINCES, JOB_TYPE_OPTIONS, PROVIDERS

BTN_ADD_SEARCH = "➕ افزودن سرچ"
BTN_MY_SEARCHES = "📋 سرچ‌های من"
BTN_HELP = "❓ راهنما"
BTN_ACCOUNT = "👤 حساب کاربری"
BTN_SUPPORT = "🆘 پشتیبانی"

SUPPORT_USERNAME = "MrTakDev"
CHANNEL_USERNAME = "erfanbanaei_ir"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_ADD_SEARCH)
    builder.button(text=BTN_MY_SEARCHES)
    builder.button(text=BTN_ACCOUNT)
    builder.button(text=BTN_SUPPORT)
    builder.button(text=BTN_HELP)
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def search_list_keyboard(queries: list[SearchQuery]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for query in queries:
        status_icon = "🔵 توقف" if query.is_active else "🟢 ازسرگیری"
        builder.button(text=f"{status_icon} | {query.title}", callback_data=f"toggle:{query.id}")
        builder.button(text="🔴 حذف", callback_data=f"del:{query.id}")
    builder.button(text="➕ افزودن سرچ جدید", callback_data="add_search")
    builder.adjust(*([2] * len(queries)), 1)
    return builder.as_markup()


def after_add_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 مشاهده سرچ‌های من", callback_data="list_searches")
    return builder.as_markup()


def providers_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, provider in PROVIDERS.items():
        mark = "✅" if key in selected else "⬜"
        builder.button(text=f"{mark} {provider.LABEL}", callback_data=f"provider:{key}")
    builder.button(text="➡️ تأیید و ادامه", callback_data="provider:confirm")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def city_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🌍 همه‌ی ایران (بدون فیلتر شهر)", callback_data="city:__all__")
    for city in IRAN_PROVINCES:
        builder.button(text=city, callback_data=f"city:{city}")
    builder.adjust(1, *([3] * (len(IRAN_PROVINCES) // 3 + 1)))
    return builder.as_markup()


def job_types_keyboard(selected: set[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in JOB_TYPE_OPTIONS:
        mark = "✅" if key in selected else "⬜"
        builder.button(text=f"{mark} {label}", callback_data=f"jt:{key}")
    builder.button(text="➡️ تأیید و ادامه", callback_data="jt:confirm")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def support_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 ارتباط با پشتیبانی", url=f"https://t.me/{SUPPORT_USERNAME}")
    return builder.as_markup()


def join_channel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}")
    builder.button(text="✅ عضو شدم، بررسی کن", callback_data="check_membership")
    builder.adjust(1)
    return builder.as_markup()
