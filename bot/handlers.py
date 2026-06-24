from html import escape
from typing import Callable, Coroutine

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from jobs.providers import PROVIDERS

from . import services
from .keyboards import (
    BTN_ADD_SEARCH,
    BTN_HELP,
    BTN_MY_SEARCHES,
    after_add_keyboard,
    city_keyboard,
    job_types_keyboard,
    main_menu_keyboard,
    provider_keyboard,
    search_list_keyboard,
)
from .states import AddSearchStates

router = Router()

WELCOME_TEXT = (
    "سلام! 👋\n"
    "این ربات آگهی‌های استخدامی جدید جابینجا رو هر ۱۵ دقیقه چک می‌کنه و برات می‌فرسته.\n\n"
    "از دکمه‌های پایین استفاده کن، یا این دستورات رو بزن:\n"
    "/addsearch - ساخت سرچ جدید با چندتا سوال (کلمه، شهر، نوع همکاری)\n"
    "/mysearches - لیست سرچ‌های من\n"
    "/removesearch &lt;id&gt; - حذف یه سرچ\n"
    "/help - نمایش این راهنما"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await services.get_or_create_user(
        message.chat.id, message.from_user.username, message.from_user.first_name
    )
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())


async def _start_wizard(message: Message, state: FSMContext) -> None:
    user = await services.get_user(message.chat.id)
    if user is None:
        await message.answer("اول دستور /start رو بزن.")
        return
    await state.clear()
    await state.set_state(AddSearchStates.choosing_provider)
    await message.answer("از کدوم سایت می‌خوای جستجو کنی؟", reply_markup=provider_keyboard())


@router.message(Command("addsearch"))
async def cmd_addsearch(message: Message, state: FSMContext) -> None:
    await _start_wizard(message, state)


@router.message(F.text == BTN_ADD_SEARCH)
async def btn_addsearch(message: Message, state: FSMContext) -> None:
    await _start_wizard(message, state)


@router.callback_query(AddSearchStates.choosing_provider, F.data.startswith("provider:"))
async def cb_choose_provider(callback: CallbackQuery, state: FSMContext) -> None:
    provider_key = callback.data.split(":", 1)[1]
    provider = PROVIDERS.get(provider_key)
    if provider is None:
        await callback.answer("این گزینه پیدا نشد.")
        return

    await state.update_data(provider=provider_key)
    await state.set_state(AddSearchStates.waiting_for_keyword)
    await callback.message.edit_text(f"منبع: {provider.LABEL}\nچی می‌خوای جستجو کنی؟ (مثلاً flutter)")
    await callback.answer()


@router.message(AddSearchStates.waiting_for_keyword)
async def process_keyword(message: Message, state: FSMContext) -> None:
    keyword = (message.text or "").strip()
    if not keyword:
        await message.answer("یه کلمه برای جستجو بفرست (مثلاً flutter):")
        return
    await state.update_data(keyword=keyword, job_types=[])
    await state.set_state(AddSearchStates.choosing_city)
    await message.answer("شهر/استان رو انتخاب کن:", reply_markup=city_keyboard())


@router.callback_query(AddSearchStates.choosing_city, F.data.startswith("city:"))
async def cb_choose_city(callback: CallbackQuery, state: FSMContext) -> None:
    raw_city = callback.data.split(":", 1)[1]
    city = None if raw_city == "__all__" else raw_city
    await state.update_data(city=city)
    await state.set_state(AddSearchStates.choosing_job_types)
    await callback.message.edit_text(
        "نوع همکاری رو انتخاب کن (می‌تونی چندتا بزنی)، بعد «تأیید و ادامه» رو بزن:",
        reply_markup=job_types_keyboard(set()),
    )
    await callback.answer()


@router.callback_query(AddSearchStates.choosing_job_types, F.data.startswith("jt:"))
async def cb_job_type(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    data = await state.get_data()

    if key == "confirm":
        provider = PROVIDERS[data["provider"]]
        keyword = data.get("keyword", "")
        city = data.get("city")
        job_types = set(data.get("job_types", []))
        url = provider.build_url(keyword, city, job_types)
        title = f"{provider.LABEL}: {keyword} ({city})" if city else f"{provider.LABEL}: {keyword}"
        await state.clear()
        await _save_search(callback.message, callback.from_user.id, url, title)
        await callback.answer()
        return

    job_types = set(data.get("job_types", []))
    job_types.symmetric_difference_update({key})
    await state.update_data(job_types=list(job_types))
    await callback.message.edit_reply_markup(reply_markup=job_types_keyboard(job_types))
    await callback.answer()


async def _save_search(message: Message, chat_id: int, url: str, title: str) -> None:
    user = await services.get_user(chat_id)
    if user is None:
        await message.answer("اول دستور /start رو بزن.")
        return

    search_query = await services.create_search_query(user, title, url)
    text = (
        f"✅ سرچ «{escape(search_query.title)}» اضافه شد.\n"
        "هر ۱۵ دقیقه چک می‌شه و آگهی‌های جدید برات ارسال می‌شه."
    )
    await message.answer(text, reply_markup=after_add_keyboard())


SendFunc = Callable[..., Coroutine]


async def _send_search_list(chat_id: int, send: SendFunc) -> None:
    user = await services.get_user(chat_id)
    if user is None:
        await send("اول دستور /start رو بزن.")
        return

    queries = await services.list_search_queries(user)
    if not queries:
        await send("هنوز هیچ سرچی اضافه نکردی. از دکمه‌ی «➕ افزودن سرچ» استفاده کن.")
        return

    await send("سرچ‌های تو:", reply_markup=search_list_keyboard(queries))


@router.message(Command("mysearches"))
@router.message(F.text == BTN_MY_SEARCHES)
async def cmd_mysearches(message: Message) -> None:
    await _send_search_list(message.chat.id, message.answer)


@router.message(Command("removesearch"))
async def cmd_removesearch(message: Message, command: CommandObject) -> None:
    if not command.args or not command.args.strip().isdigit():
        await message.answer("استفاده: /removesearch &lt;id&gt;\n(آی‌دی رو از /mysearches بگیر)")
        return

    user = await services.get_user(message.chat.id)
    if user is None:
        await message.answer("اول دستور /start رو بزن.")
        return

    deleted = await services.delete_search_query(user, int(command.args.strip()))
    await message.answer("🗑 حذف شد." if deleted else "سرچی با این شناسه برای شما پیدا نشد.")


@router.callback_query(F.data == "list_searches")
async def cb_list_searches(callback: CallbackQuery) -> None:
    await _send_search_list(callback.message.chat.id, callback.message.answer)
    await callback.answer()


@router.callback_query(F.data.startswith("del:"))
async def cb_delete(callback: CallbackQuery) -> None:
    user = await services.get_user(callback.from_user.id)
    search_query_id = int(callback.data.split(":")[1])
    deleted = await services.delete_search_query(user, search_query_id) if user else False
    await callback.answer("🗑 حذف شد." if deleted else "پیدا نشد.")

    if not deleted:
        return

    queries = await services.list_search_queries(user)
    if queries:
        await callback.message.edit_text("سرچ‌های تو:", reply_markup=search_list_keyboard(queries))
    else:
        await callback.message.edit_text("هیچ سرچی نداری. از دکمه‌ی «➕ افزودن سرچ» استفاده کن.")


@router.callback_query(F.data.startswith("toggle:"))
async def cb_toggle(callback: CallbackQuery) -> None:
    user = await services.get_user(callback.from_user.id)
    search_query_id = int(callback.data.split(":")[1])
    search_query = await services.toggle_search_query(user, search_query_id) if user else None

    if search_query is None:
        await callback.answer("پیدا نشد.")
        return

    await callback.answer("▶️ از سر گرفته شد." if search_query.is_active else "⏸ موقتاً متوقف شد.")
    queries = await services.list_search_queries(user)
    await callback.message.edit_text("سرچ‌های تو:", reply_markup=search_list_keyboard(queries))
