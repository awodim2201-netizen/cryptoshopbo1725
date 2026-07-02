import asyncio
import logging
import os
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile

from config import *
from database import *
from states import OrderStates
from keyboards import *

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ========== ВЕБ-СЕРВЕР ДЛЯ RENDER ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!", 200

@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    asyncio.run(dp.start_polling(bot))

# ========== ВСЕ КОМАНДЫ БОТА ==========

# Корзина (хранилище)
cart = {}

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=city_keyboard())
    await state.set_state(OrderStates.selecting_city)

@dp.callback_query(StateFilter(OrderStates.selecting_city), F.data.startswith("city_"))
async def select_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split("_")[1]
    await state.update_data(city=city)
    await callback.message.edit_text(f"📍 Город: {city}\n\nВыберите товар:", reply_markup=product_keyboard())
    await state.set_state(OrderStates.viewing_product)

@dp.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    items = cart.get(user_id, [])
    if not items:
        await callback.answer("Корзина пуста", show_alert=True)
        return
    total = sum(p['price'] for p in items)
    text = "🛒 Ваша корзина:\n\n"
    for p in items:
        text += f"• {p['name']} — {p['price']} USDT\n"
    text += f"\nИтого: {total} USDT"
    await callback.message.edit_text(text, reply_markup=cart_keyboard())
    await state.update_data(cart_items=items)

@dp.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    city = data.get("city", "Город")
    await callback.message.edit_text(f"📍 {city}\n\nВыберите товар:", reply_markup=product_keyboard())

@dp.callback_query(F.data.startswith("product_"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        await callback.answer("Товар не найден")
        return
    
    user_id = callback.from_user.id
    if user_id not in cart:
        cart[user_id] = []
    cart[user_id].append(product.copy())
    
    await callback.answer(f"✅ {product['name']} добавлен в корзину!", show_alert=True)
    
    try:
        photo = FSInputFile(f"photos/{product['photo']}")
        await callback.message.answer_photo(
            photo,
            caption=f"{product['name']}\nЦена: {product['price']} USDT",
            reply_markup=product_keyboard()
        )
    except:
        await callback.message.answer(f"{product['name']} — {product['price']} USDT", reply_markup=product_keyboard())

@dp.callback_query(F.data == "checkout")
async def checkout(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    items = cart.get(user_id, [])
    if not items:
        await callback.answer("Корзина пуста")
        return
    
    total = sum(p['price'] for p in items)
    data = await state.get_data()
    city = data.get("city", "Город")
    products_text = "\n".join([f"{p['name']} — {p['price']} USDT" for p in items])
    
    order_id = create_order(
        user_id=user_id,
        username=callback.from_user.username or "без_юзернейма",
        city=city,
        products=products_text,
        total=total
    )
    await state.update_data(order_id=order_id)
    
    await bot.send_message(
        ADMIN_ID,
        f"🆕 НОВЫЙ ЗАКАЗ #{order_id}\n"
        f"👤 {callback.from_user.full_name} (@{callback.from_user.username})\n"
        f"📍 {city}\n"
        f"📦 {products_text}\n"
        f"💵 Итого: {total} USDT"
    )
    
    await callback.message.edit_text(
        f"📦 Заказ #{order_id} оформлен!\n\n"
        f"💰 Сумма: {total} USDT\n"
        f"💳 Оплатите на кошелек:\n<code>{CRYPTO_WALLET}</code>\n\n"
        f"После оплаты нажмите кнопку ниже",
        reply_markup=payment_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.waiting_for_payment)

@dp.callback_query(F.data == "paid")
async def paid(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✅ Заявка отправлена продавцу!\n"
        "Ожидайте координаты для получения товара.",
        reply_markup=None
    )
    
    data = await state.get_data()
    order_id = data.get("order_id")
    update_order_status(order_id, "paid")
    
    await bot.send_message(
        ADMIN_ID,
        f"💳 КЛИЕНТ ОПЛАТИЛ ЗАКАЗ #{order_id}\n"
        f"Нажмите кнопку, чтобы отправить координаты",
        reply_markup=admin_order_keyboard(order_id)
    )

@dp.callback_query(F.data.startswith("deliver_"))
async def deliver_order(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав")
        return
    
    order_id = int(callback.data.split("_")[1])
    await state.update_data(deliver_order_id=order_id)
    
    await callback.message.edit_text(
        f"📦 Отправка заказа #{order_id}\n"
        "Отправьте геолокацию и фото места",
        reply_markup=delivery_keyboard()
    )

@dp.callback_query(F.data == "send_location")
async def ask_location(callback: CallbackQuery):
    await callback.message.answer("📍 Отправьте геолокацию (кнопка скрепка → Location)")

@dp.message(F.location)
async def get_location(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    order_id = data.get("deliver_order_id")
    if not order_id:
        return
    
    order = get_order(order_id)
    if not order:
        return
    
    lat = message.location.latitude
    lon = message.location.longitude
    maps_link = f"https://maps.google.com/?q={lat},{lon}"
    
    await bot.send_message(
        order[1],
        f"📍 Координаты для получения заказа:\n<code>{lat}, {lon}</code>\n\n"
        f"<a href='{maps_link}'>🗺 Открыть в картах</a>",
        parse_mode="HTML"
    )
    await message.answer("✅ Координаты отправлены клиенту")

@dp.callback_query(F.data == "send_photo")
async def ask_photo(callback: CallbackQuery):
    await callback.message.answer("📸 Отправьте фото (кнопка скрепка → Photo или Gallery)")

@dp.message(F.photo)
async def get_photo(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    order_id = data.get("deliver_order_id")
    if not order_id:
        return
    
    order = get_order(order_id)
    if not order:
        return
    
    await bot.send_photo(
        order[1],
        message.photo[-1].file_id,
        caption="📸 Ориентир для получения товара"
    )
    await message.answer("✅ Фото отправлено клиенту")
    update_order_status(order_id, "delivered")
    await message.answer(f"✅ Заказ #{order_id} завершен!")

@dp.callback_query(F.data == "delivery_done")
async def delivery_done(callback: CallbackQuery):
    await callback.message.edit_text("✅ Отправка завершена")

@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_order(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("У вас нет прав")
        return
    order_id = int(callback.data.split("_")[1])
    update_order_status(order_id, "cancelled")
    await callback.message.edit_text(f"❌ Заказ #{order_id} отменен")
    
    order = get_order(order_id)
    if order:
        await bot.send_message(order[1], "❌ Ваш заказ отменен продавцом")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    init_db()
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)