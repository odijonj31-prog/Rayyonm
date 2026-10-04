from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import WEBAPP_URL, COMPANY_NAME, MANAGER_USERNAME, MANAGER_PHONE, SUPER_ADMIN_IDS
from database.requests import (
    get_or_create_user, get_setting, get_orders_with_payments, get_user, create_order,
    set_user_phone, get_portfolio_item,
)
from filters.subscription import get_unsubscribed_channels
from keyboards.user_kb import open_app_inline_kb, main_menu_kb, subscription_kb, phone_request_kb
from states import CustomerOrderRequest, RegisterPhone

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )

    unsubscribed = await get_unsubscribed_channels(bot, message.from_user.id)
    if unsubscribed:
        await message.answer(
            "👋 Botdan to'liq foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling!",
            reply_markup=subscription_kb(unsubscribed),
        )
        return

    if not user.phone:
        await state.set_state(RegisterPhone.waiting_contact)
        await message.answer(
            "📱 Botdan to'liq foydalanish uchun telefon raqamingizni yuboring "
            "(bu buyurtmangiz bo'yicha bog'lanish uchun kerak):",
            reply_markup=phone_request_kb(),
        )
        return

    await send_welcome(message)


@router.message(RegisterPhone.waiting_contact, F.contact)
async def register_phone_contact(message: Message, state: FSMContext):
    await set_user_phone(message.from_user.id, message.contact.phone_number)
    await state.clear()
    await message.answer("✅ Rahmat! Raqamingiz saqlandi.")
    await send_welcome(message)


@router.message(RegisterPhone.waiting_contact, F.text)
async def register_phone_text(message: Message, state: FSMContext):
    text = message.text.strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) < 9:
        await message.answer("❌ Iltimos, \"📱 Raqamni yuborish\" tugmasini bosing yoki to'g'ri raqam yozing.")
        return
    await set_user_phone(message.from_user.id, text)
    await state.clear()
    await message.answer("✅ Rahmat! Raqamingiz saqlandi.")
    await send_welcome(message)


async def send_welcome(message: Message):
    text = (
        f"👋 Assalomu alaykum, {message.from_user.first_name}!\n"
        f"🛋 <b>{COMPANY_NAME}</b> botiga xush kelibsiz!\n\n"
        f"Quyidagi menyudan foydalaning 👇"
    )
    await message.answer(text, reply_markup=main_menu_kb())

    if WEBAPP_URL:
        await message.answer(
            "🖼 Bizning ilgari qilgan ishlarimizni ko'rish uchun ilovani oching:",
            reply_markup=open_app_inline_kb(),
        )


@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery, bot: Bot):
    unsubscribed = await get_unsubscribed_channels(bot, callback.from_user.id)
    if unsubscribed:
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return
    await callback.message.delete()
    await send_welcome(callback.message)
    await callback.answer()


# ---------- PASTKI MENYU TUGMALARI ----------

@router.message(F.text == "🖼 Ishlarimiz")
async def show_works_fallback(message: Message):
    # WEBAPP_URL sozlanmagan holatda ham foydalanuvchi biror narsa ko'rsin
    await message.answer("🖼 Bizning ishlarimiz bilan tanishish uchun Mini App tez orada ishga tushadi.")


@router.message(F.text == "📞 Menejer bilan bog'lanish")
async def contact_manager(message: Message):
    if not MANAGER_USERNAME:
        await message.answer("📞 Menejer bilan bog'lanish hozircha sozlanmagan. Iltimos, keyinroq urinib ko'ring.")
        return
    await message.answer(f"📞 Menejerimiz bilan bog'lanish uchun bosing: @{MANAGER_USERNAME}")


@router.message(F.text == "ℹ️ Biz haqimizda")
async def about_us(message: Message):
    text = await get_setting("about_us_text")
    if not text:
        text = f"🛋 <b>{COMPANY_NAME}</b> — zamonaviy mebel ustaxonasi.\n\nBatafsil ma'lumot tez orada qo'shiladi."
    await message.answer(text)


@router.message(F.text == "💡 Yordam")
async def show_help(message: Message):
    await message.answer(
        "💡 <b>Yordam</b>\n\n"
        "🖼 Ishlarimiz — bizning oldingi ishlarimiz bilan tanishing\n"
        "📦 Buyurtmalarim — buyurtmangiz holati, narx va to'lovlar\n"
        "📞 Menejer bilan bog'lanish — to'g'ridan-to'g'ri chat\n"
        "ℹ️ Biz haqimizda — kompaniya haqida ma'lumot\n\n"
        "Buyurtma berish uchun bizning do'konimizga tashrif buyuring — "
        "menejerimiz sizga yordam beradi!"
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    if await state.get_state() is None:
        return
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())


# ---------- MIJOZ O'ZI BUYURTMA SO'RAYDI ----------

@router.message(F.text == "🆕 Buyurtma berish")
async def customer_order_start(message: Message, state: FSMContext):
    await state.set_state(CustomerOrderRequest.waiting_description)
    await message.answer(
        "📝 Qanday mebel buyurtma qilmoqchisiz? Tavsiflab yozing "
        "(masalan: \"Oshxona garnituri, 3.5m, jigarrang rangda\").\n\n"
        "Agar namuna rasm bo'lsa, shu rasmni tavsif bilan birga yuborishingiz mumkin.\n\n"
        "(Bekor qilish uchun /cancel)"
    )


@router.message(CustomerOrderRequest.waiting_description, F.photo)
async def customer_order_description_photo(message: Message, state: FSMContext):
    await state.update_data(description=message.caption or "(tavsif yozilmagan)", photo_file_id=message.photo[-1].file_id)
    db_user = await get_user(message.from_user.id)
    if db_user and db_user.phone:
        await finalize_customer_order(message, state, message.bot, phone=db_user.phone)
        return
    await state.set_state(CustomerOrderRequest.waiting_phone)
    await message.answer("📱 Telefon raqamingizni kiriting (masalan: +998901234567):")


@router.message(CustomerOrderRequest.waiting_description, F.text)
async def customer_order_description_text(message: Message, state: FSMContext):
    data = await state.get_data()
    # Agar mijoz portfolio'dan rasm tanlagan bo'lsa, o'sha rasmni saqlab qolamiz
    await state.update_data(
        description=message.text.strip(),
        photo_file_id=data.get("photo_file_id"),
    )
    db_user = await get_user(message.from_user.id)
    if db_user and db_user.phone:
        # Telefon allaqachon ro'yxatdan o'tishda olingan — qayta so'ramaymiz
        await finalize_customer_order(message, state, message.bot, phone=db_user.phone)
        return
    await state.set_state(CustomerOrderRequest.waiting_phone)
    await message.answer("📱 Telefon raqamingizni kiriting (masalan: +998901234567):")


@router.message(F.web_app_data)
async def handle_web_app_data(message: Message, state: FSMContext, bot: Bot):
    """Mini App'dan 'Shu mebelni tanlash' bosilganda ishga tushadi."""
    import json
    try:
        payload = json.loads(message.web_app_data.data)
    except Exception:
        return
    if payload.get("type") != "portfolio_select":
        return

    item = await get_portfolio_item(int(payload.get("item_id", 0)))
    if not item:
        await message.answer("❌ Bu mebel topilmadi.")
        return

    await state.set_state(CustomerOrderRequest.waiting_description)
    await state.update_data(photo_file_id=item.photo_file_id, portfolio_item_id=item.id)

    caption = (
        f"🛋 <b>{item.title}</b>\n"
        + (f"{item.description}\n" if item.description else "")
        + "\n📝 Shu mebelga o'xshash nima qildirmoqchisiz? O'lcham, rang va boshqa istaklaringizni yozing — "
          "menejerimizga yetkazamiz.\n\n(Bekor qilish uchun /cancel)"
    )
    await bot.send_photo(message.chat.id, photo=item.photo_file_id, caption=caption)


@router.message(CustomerOrderRequest.waiting_phone)
async def customer_order_phone(message: Message, state: FSMContext, bot: Bot):
    phone = message.text.strip()
    await set_user_phone(message.from_user.id, phone)
    await finalize_customer_order(message, state, bot, phone=phone)


async def finalize_customer_order(message: Message, state: FSMContext, bot: Bot, phone: str):
    data = await state.get_data()
    await state.clear()

    db_user = await get_user(message.from_user.id)
    order = await create_order(
        user_id=db_user.id, width_mm=None, height_mm=None, depth_mm=None,
        selected_option_ids=[], ai_estimated_price=None, description=data["description"],
        contact_phone=phone, contact_name=message.from_user.full_name,
        portfolio_item_id=data.get("portfolio_item_id"),
    )

    manager_phone_line = f"\n📞 Savol-takliflar: {MANAGER_PHONE}" if MANAGER_PHONE else ""
    await message.answer(
        f"✅ <b>So'rovingiz qabul qilindi!</b>\n\n"
        f"📦 Buyurtma #{order.id}\n"
        f"📝 {data['description']}\n\n"
        f"Menejerimiz tez orada siz bilan bog'lanib, aniq narxni belgilaydi."
        f"{manager_phone_line}",
        reply_markup=main_menu_kb(),
    )

    admin_text = (
        f"🆕 <b>Yangi buyurtma so'rovi (botdan)</b>\n\n"
        f"👤 {message.from_user.full_name} (@{message.from_user.username or '—'})\n"
        f"📱 {phone}\n"
        f"📝 {data['description']}\n"
        f"🆔 <code>{message.from_user.id}</code>\n"
        f"🔢 Buyurtma #{order.id}"
    )
    for admin_id in SUPER_ADMIN_IDS:
        try:
            if data.get("photo_file_id"):
                await bot.send_photo(admin_id, photo=data["photo_file_id"], caption=admin_text)
            else:
                await bot.send_message(admin_id, admin_text)
        except Exception:
            pass


@router.message(F.text == "📦 Buyurtmalarim")
async def my_orders(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Avval /start bosing.")
        return

    rows = await get_orders_with_payments(user.id)
    if not rows:
        await message.answer("📦 Sizda hali buyurtma yo'q.\n\nBuyurtma berish uchun do'konimizga tashrif buyuring!")
        return

    status_labels = {
        "new": "🆕 Yangi", "confirmed": "✅ Kelishuv va to'lov", "in_production": "🛠 Ishlab chiqarilmoqda",
        "delivered": "🚚 Yetkazib berildi", "cancelled": "❌ Bekor qilingan",
    }

    for row in rows:
        order = row["order"]
        text = (
            f"📦 <b>Buyurtma #{order.id}</b> — {status_labels.get(order.status, order.status)}\n\n"
            f"📝 {order.description or '—'}\n"
        )
        if order.agreed_price:
            text += (
                f"💰 Kelishilgan summa: {order.agreed_price:,} so'm\n".replace(",", " ")
                + f"✅ To'langan: {row['paid']:,} so'm\n".replace(",", " ")
                + f"⏳ Qarzdorlik: {row['debt']:,} so'm\n".replace(",", " ")
            )
        else:
            text += "💰 Narx hali kelishilmagan\n"
        await message.answer(text)
