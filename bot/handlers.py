from html import escape
from typing import Callable, Coroutine

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from jobs.providers import PROVIDERS

from . import services
from .keyboards import (
    BTN_ACCOUNT,
    BTN_ADD_SEARCH,
    BTN_HELP,
    BTN_MY_SEARCHES,
    BTN_SUPPORT,
    after_add_keyboard,
    city_keyboard,
    job_types_keyboard,
    main_menu_keyboard,
    providers_keyboard,
    search_list_keyboard,
    support_keyboard,
)
from .states import AddSearchStates

router = Router()

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
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await _send_welcome(message, state)


@router.callback_query(F.data == "check_membership")
async def cb_check_membership(callback: CallbackQuery, state: FSMContext) -> None:
    # The membership middleware already verified the user is a member by the
    # time this handler runs - otherwise it would have intercepted the event.
    await services.get_or_create_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name,
        callback.from_user.last_name,
    )
    await state.clear()
    await callback.message.answer(
        "✅ عضویتت تأیید شد! خوش اومدی.\n\n" + WELCOME_TEXT, reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


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
    username_text = f"@{user.username}" if user.username else "—"

    text = (
        "👤 <b>اطلاعات حساب شما</b>\n\n"
        f"نام: {escape(user.first_name or '—')}\n"
        f"نام خانوادگی: {escape(user.last_name or '—')}\n"
        f"آیدی: {escape(username_text)}\n"
        f"آیدی عددی: <code>{user.chat_id}</code>\n"
        f"تعداد سرچ‌های فعال: {active_count}"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


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

    created_titles = []
    for provider_key in provider_keys:
        provider = PROVIDERS.get(provider_key)
        if provider is None:
            continue
        url = provider.build_url(keyword, city, job_types)
        title = f"{provider.LABEL}: {keyword} ({city})" if city else f"{provider.LABEL}: {keyword}"
        search_query = await services.create_search_query(user, title, url)
        created_titles.append(search_query.title)

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
