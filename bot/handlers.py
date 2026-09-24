import asyncio
from html import escape
from typing import Callable, Coroutine

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from jobs.providers import PROVIDERS

from . import services
from .keyboards import (
    BTN_ACCOUNT,
    BTN_ADD_SEARCH,
    BTN_ADMIN_PANEL,
    BTN_HELP,
    BTN_MY_SEARCHES,
    BTN_SUPPORT,
    admin_panel_keyboard,
    after_add_keyboard,
    broadcast_confirm_keyboard,
    city_keyboard,
    job_types_keyboard,
    main_menu_keyboard,
    providers_keyboard,
    search_list_keyboard,
    support_keyboard,
)
from .states import AddSearchStates, BroadcastStates

router = Router()

ADMIN_ID = 1075119392

WELCOME_TEXT = (
    "سلام و خوش اومدی! 👋✨\n\n"
    "من اینجام تا جدیدترین آگهی‌های استخدامی حوزه‌ی کاری‌ای که بخوای رو از چندین سایت معتبر "
    "(جابینجا، جاب‌ویژن، ای‌استخدام و ایران‌تلنت) برات پیدا کنم و همینجا توی تلگرام بفرستم. 🔎💼\n\n"
    "از دکمه‌های پایین صفحه استفاده کن و شروع کن!"
)

HELP_TEXT = (
    "❓ <b>راهنمای ربات</b>\n\n"
    "این ربات هر ۱۵ دقیقه سایت‌های کاریابی رو برای کلمه‌ای که تو انتخاب می‌کنی چک می‌کنه و "
    "به محض اینکه یه آگهی جدید پیدا بشه، همینجا برات می‌فرسته. 🔔\n\n"
    "<b>چجوری کار می‌کنه؟</b>\n"
    "۱️⃣ روی «➕ افزودن سرچ» بزن.\n"
    "۲️⃣ یه کلمه برای جستجو بفرست (مثلاً flutter یا حسابدار).\n"
    "۳️⃣ یک یا چند سایت رو که می‌خوای جستجو توشون انجام بشه تیک بزن.\n"
    "۴️⃣ شهر/استان مورد نظرت رو انتخاب کن (یا «همه‌ی ایران»).\n"
    "۵️⃣ نوع همکاری (تمام‌وقت/پاره‌وقت/کارآموزی/دورکاری) رو انتخاب کن — می‌تونی چندتا رو هم‌زمان بزنی.\n"
    "۶️⃣ تمام! از این به بعد آگهی‌های جدید همون سایت‌ها به‌صورت خودکار برات می‌آد.\n\n"
    "<b>دکمه‌های دیگه:</b>\n"
    "📋 سرچ‌های من — لیست سرچ‌هات، با امکان توقف موقت یا حذف هر کدوم.\n"
    "👤 حساب کاربری — اطلاعات حساب و تعداد سرچ‌های فعالت.\n"
    "🆘 پشتیبانی — ارتباط مستقیم با ادمین برای پیشنهاد یا گزارش مشکل."
)

SUPPORT_TEXT = "اگه نظر، پیشنهاد یا مشکلی داری، خوشحال می‌شیم بشنویم 🙏\nروی دکمه‌ی پایین بزن:"


async def _send_welcome(message: Message, state: FSMContext) -> None:
    await state.clear()
    await services.get_or_create_user(
        message.chat.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name,
    )
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard(is_admin=message.chat.id == ADMIN_ID))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await _send_welcome(message, state)


@router.callback_query(F.data == "check_membership")
async def cb_check_membership(callback: CallbackQuery, state: FSMContext) -> None:
    await services.get_or_create_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name,
        callback.from_user.last_name,
    )
    await state.clear()
    await callback.message.answer(
        "✅ عضویتت تأیید شد! خوش اومدی.\n\n" + WELCOME_TEXT,
        reply_markup=main_menu_keyboard(is_admin=callback.from_user.id == ADMIN_ID),
    )
    await callback.answer()


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard(is_admin=message.chat.id == ADMIN_ID))


@router.message(F.text == BTN_SUPPORT)
async def cmd_support(message: Message) -> None:
    await message.answer(SUPPORT_TEXT, reply_markup=support_keyboard())


@router.message(F.text == BTN_ACCOUNT)
async def cmd_account(message: Message) -> None:
    user = await services.get_user(message.chat.id)
    if user is None:
        await message.answer("اول دستور /start رو بزن.")
        return

    active_count = await services.active_search_count(user)
    dash = "—"
    username_text = f"@{user.username}" if user.username else dash

    text = (
        "👤 <b>اطلاعات حساب شما</b>\n\n"
        f"نام: {escape(user.first_name or dash)}\n"
        f"نام خانوادگی: {escape(user.last_name or dash)}\n"
        f"آیدی: {escape(username_text)}\n"
        f"آیدی عددی: <code>{user.chat_id}</code>\n"
        f"تعداد سرچ‌های فعال: {active_count}"
    )
    await message.answer(text, reply_markup=main_menu_keyboard(is_admin=message.chat.id == ADMIN_ID))


# ── Admin panel ────────────────────────────────────────────────────────────────

@router.message(F.text == BTN_ADMIN_PANEL)
async def cmd_admin_panel(message: Message, state: FSMContext) -> None:
    if message.chat.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("⚙️ <b>پنل مدیریت</b>\nیه بخش رو انتخاب کن:", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    stats = await services.get_user_stats()
    text = (
        "📊 <b>آمار کاربران</b>\n\n"
        f"👥 کل کاربران: <b>{stats['total']}</b>\n"
        f"✅ کاربران فعال: <b>{stats['active']}</b>\n"
        f"🚫 غیرفعال: <b>{stats['total'] - stats['active']}</b>"
    )
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:recent_users")
async def cb_admin_recent_users(callback: CallbackQuery) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    users = await services.get_recent_users(15)
    if not users:
        await callback.message.edit_text("هیچ کاربری ثبت نشده.", reply_markup=admin_panel_keyboard())
        await callback.answer()
        return

    lines = []
    for u in users:
        name = escape(((u.first_name or "") + " " + (u.last_name or "")).strip()) or "—"
        uname = f"@{escape(u.username)}" if u.username else "—"
        status = "✅" if u.is_active else "🚫"
        lines.append(f"{status} <code>{u.chat_id}</code> | {name} | {uname}")

    text = "👥 <b>آخرین ۱۵ کاربر</b>\n\n" + "\n".join(lines)
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.message.answer("📣 پیامی که می‌خوای به همه بفرستی رو بنویس:\n\n(برای لغو /start بزن)")
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext) -> None:
    if message.chat.id != ADMIN_ID:
        return
    text = message.text or message.caption or ""
    if not text.strip():
        await message.answer("پیام نمیتونه خالی باشه. یه متن بفرست:")
        return
    await state.update_data(broadcast_text=text)
    stats = await services.get_user_stats()
    preview = (
        f"📋 <b>پیش‌نمایش پیام:</b>\n\n{escape(text)}\n\n"
        f"این پیام به <b>{stats['active']}</b> کاربر فعال ارسال میشه.\n"
        "تأیید می‌کنی؟"
    )
    await message.answer(preview, reply_markup=broadcast_confirm_keyboard())


@router.callback_query(F.data == "broadcast:cancel")
async def cb_broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return
    await state.clear()
    await callback.message.edit_text("❌ ارسال همگانی لغو شد.")
    await callback.answer()


@router.callback_query(F.data == "broadcast:confirm")
async def cb_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()

    if not text:
        await callback.message.edit_text("خطا: متنی یافت نشد.")
        await callback.answer()
        return

    await callback.message.edit_text("⏳ در حال ارسال...")
    await callback.answer()

    chat_ids = await services.get_all_active_chat_ids()
    sent = 0
    failed = 0
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await callback.message.answer(
        f"✅ ارسال تموم شد.\n\n"
        f"موفق: <b>{sent}</b>\n"
        f"ناموفق: <b>{failed}</b>"
    )


# ── Search wizard ──────────────────────────────────────────────────────────────

async def _start_wizard(message: Message, state: FSMContext) -> None:
    user = await services.get_user(message.chat.id)
    if user is None:
        await message.answer("اول دستور /start رو بزن.")
        return
    await state.clear()
    await state.set_state(AddSearchStates.waiting_for_keyword)
    await message.answer("چی می‌خوای جستجو کنی؟ (مثلاً flutter یا حسابدار)")


@router.message(F.text == BTN_ADD_SEARCH)
async def btn_addsearch(message: Message, state: FSMContext) -> None:
    await _start_wizard(message, state)


@router.callback_query(F.data == "add_search")
async def cb_addsearch(callback: CallbackQuery, state: FSMContext) -> None:
    await _start_wizard(callback.message, state)
    await callback.answer()


@router.message(AddSearchStates.waiting_for_keyword)
async def process_keyword(message: Message, state: FSMContext) -> None:
    keyword = (message.text or "").strip()
    if not keyword:
        await message.answer("یه کلمه برای جستجو بفرست (مثلاً flutter):")
        return
    await state.update_data(keyword=keyword, providers=[], job_types=[])
    await state.set_state(AddSearchStates.choosing_providers)
    await message.answer(
        "چه سایت‌هایی رو می‌خوای جستجو کنی؟ (می‌تونی چندتا رو هم‌زمان انتخاب کنی)",
        reply_markup=providers_keyboard(set()),
    )


@router.callback_query(AddSearchStates.choosing_providers, F.data.startswith("provider:"))
async def cb_toggle_provider(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    data = await state.get_data()
    providers = set(data.get("providers", []))

    if key == "confirm":
        if not providers:
            await callback.answer("حداقل یه سایت رو انتخاب کن.", show_alert=True)
            return
        await state.set_state(AddSearchStates.choosing_city)
        await callback.message.edit_text(
            "شهر/استان رو انتخاب کن:", reply_markup=city_keyboard()
        )
        await callback.answer()
        return

    if key not in PROVIDERS:
        await callback.answer("این گزینه پیدا نشد.")
        return

    providers.symmetric_difference_update({key})
    await state.update_data(providers=list(providers))
    await callback.message.edit_reply_markup(reply_markup=providers_keyboard(providers))
    await callback.answer()


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
        keyword = data.get("keyword", "")
        city = data.get("city")
        provider_keys = data.get("providers", [])
        job_types = set(data.get("job_types", []))
        await state.clear()
        await _create_searches(callback.message, callback.from_user.id, keyword, city, provider_keys, job_types)
        await callback.answer()
        return

    job_types = set(data.get("job_types", []))
    job_types.symmetric_difference_update({key})
    await state.update_data(job_types=list(job_types))
    await callback.message.edit_reply_markup(reply_markup=job_types_keyboard(job_types))
    await callback.answer()


async def _create_searches(
    message: Message,
    chat_id: int,
    keyword: str,
    city: str | None,
    provider_keys: list[str],
    job_types: set[str],
) -> None:
    user = await services.get_user(chat_id)
    if user is None:
        await message.answer("اول دستور /start رو بزن.")
        return

    created = await services.create_searches(user, keyword, city, provider_keys, job_types)
    created_titles = [search_query.title for search_query in created]

    if not created_titles:
        await message.answer("هیچ سرچی ساخته نشد.")
        return

    lines = "\n".join(f"✅ {escape(title)}" for title in created_titles)
    text = f"{lines}\n\nهر ۱۵ دقیقه چک می‌شن و آگهی‌های جدید برات ارسال می‌شه."
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


@router.message(F.text == BTN_MY_SEARCHES)
async def cmd_mysearches(message: Message) -> None:
    await _send_search_list(message.chat.id, message.answer)


@router.callback_query(F.data == "list_searches")
async def cb_list_searches(callback: CallbackQuery) -> None:
    await _send_search_list(callback.message.chat.id, callback.message.answer)
    await callback.answer()


@router.callback_query(F.data.startswith("del:"))
async def cb_delete(callback: CallbackQuery) -> None:
    user = await services.get_user(callback.from_user.id)
    search_query_id = int(callback.data.split(":")[1])
    deleted = await services.delete_search_query(user, search_query_id) if user else False
    await callback.answer("🔴 حذف شد." if deleted else "پیدا نشد.")

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

    await callback.answer("🟢 از سر گرفته شد." if search_query.is_active else "🔵 موقتاً متوقف شد.")
    queries = await services.list_search_queries(user)
    await callback.message.edit_text("سرچ‌های تو:", reply_markup=search_list_keyboard(queries))
