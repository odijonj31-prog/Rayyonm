from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import WEBAPP_URL


def open_app_inline_kb() -> InlineKeyboardMarkup:
    builder = [[InlineKeyboardButton(text="🛋 Ilovani ochish", web_app=WebAppInfo(url=WEBAPP_URL))]]
    return InlineKeyboardMarkup(inline_keyboard=builder)


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Doimiy pastki menyu — barcha asosiy funksiyalar shu yerda."""
    kb = [
        [KeyboardButton(text="🛋 Ilovani ochish", web_app=WebAppInfo(url=WEBAPP_URL))] if WEBAPP_URL else [KeyboardButton(text="🖼 Ishlarimiz")],
        [KeyboardButton(text="🆕 Buyurtma berish"), KeyboardButton(text="📦 Buyurtmalarim")],
        [KeyboardButton(text="📞 Menejer bilan bog'lanish")],
        [KeyboardButton(text="ℹ️ Biz haqimizda"), KeyboardButton(text="💡 Yordam")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def phone_request_kb() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def subscription_kb(channels) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        url = ch.invite_link or (f"https://t.me/{ch.username.lstrip('@')}" if ch.username else ch.invite_link)
        builder.row(InlineKeyboardButton(text=f"🔒 {ch.title}", url=url))
    builder.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription"))
    return builder.as_markup()
