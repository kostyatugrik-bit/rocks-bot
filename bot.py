import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8653667847:AAE0KDDbxjSeonByvttGc5mpmW2ldghE9_A")
ADMIN_ID = 5872315444  # ← ВСТАВЬ СВОЙ TELEGRAM ID (узнай через @userinfobot)

# === ТОВАРЫ ===
# Цены в звёздах: $1 ≈ 50 звёзд
PRODUCTS = {
    "tokens_1000": {"title": "1000 токенов", "stars": 400, "tokens": 1000},
    "tokens_3000": {"title": "3000 токенов", "stars": 950, "tokens": 3000},
    "tokens_8000": {"title": "8000 токенов", "stars": 2200, "tokens": 8000},
    "tokens_20000": {"title": "20000 токенов", "stars": 4950, "tokens": 20000},
    "vip": {"title": "VIP навсегда", "stars": 1950, "tokens": 0, "vip": True},
}

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# === /start ===
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")],
    ])
    await message.answer(
        "💎 <b>Rocks Control</b>\n\n"
        "Добро пожаловать! Здесь ты можешь купить токены или VIP-статус.\n\n"
        "💰 <b>Что даёт VIP:</b>\n"
        "• +1500 токенов каждую неделю\n"
        "• Безлимит джойстика\n"
        "• Эксклюзивные темы\n\n"
        "Выбирай товар:",
        reply_markup=kb
    )

# === МАГАЗИН ===
@dp.callback_query(F.data == "shop")
async def shop_handler(callback: types.CallbackQuery):
    buttons = []
    for key, product in PRODUCTS.items():
        buttons.append([InlineKeyboardButton(
            text=f"{product['title']} — {product['stars']} ⭐",
            callback_data=f"buy_{key}"
        )])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("🛒 <b>Магазин</b>\n\nВыбери товар:", reply_markup=kb)
    await callback.answer()

# === ПОКУПКА ===
@dp.callback_query(F.data.startswith("buy_"))
async def buy_handler(callback: types.CallbackQuery):
    key = callback.data.replace("buy_", "")
    product = PRODUCTS.get(key)
    if not product:
        return

    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=product["title"],
        description=f"Покупка в Rocks Control: {product['title']}",
        payload=f"order_{key}_{callback.from_user.id}",
        currency="XTR",
        prices=[LabeledPrice(label=product["title"], amount=product["stars"])],
        provider_token=""
    )
    await callback.answer()

# === ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ===
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# === УСПЕШНАЯ ОПЛАТА ===
@dp.message(F.successful_payment)
async def success_handler(message: types.Message):
    payment = message.successful_payment
    user_id = message.from_user.id
    payload = payment.invoice_payload

    # Определяем товар
    key = payload.replace("order_", "").split("_")[0] + "_" + payload.split("_")[2] if "vip" not in payload else "vip"
    if "vip" in payload:
        key = "vip"
    else:
        parts = payload.split("_")
        key = f"tokens_{parts[2]}"

    product = PRODUCTS.get(key, {})

    # Отправляем админу уведомление
    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID,
            f"💰 <b>НОВАЯ ОПЛАТА!</b>\n\n"
            f"👤 User ID: <code>{user_id}</code>\n"
            f"📦 Товар: {product.get('title', key)}\n"
            f"⭐ Звёзд: {payment.total_amount}\n\n"
            f"✅ Выдай VIP/токены через кабинет"
        )

    # Подтверждение пользователю
    await message.answer(
        f"✅ <b>Оплата прошла!</b>\n\n"
        f"Товар: {product.get('title', key)}\n"
        f"Звёзд: {payment.total_amount}\n\n"
        f"💎 Токены/VIP будут зачислены в ближайшее время.\n"
        f"ID для выдачи: <code>{user_id}</code>",
    )

# === ЗАПУСК ===
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
