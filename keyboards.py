from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CITIES, PRODUCTS

def city_keyboard():
    kb = []
    for city in CITIES:
        kb.append([InlineKeyboardButton(text=city, callback_data=f"city_{city}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def product_keyboard():
    kb = []
    for p in PRODUCTS:
        kb.append([InlineKeyboardButton(text=f"{p['name']} — {p['price']} USDT", callback_data=f"product_{p['id']}")])
    kb.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def cart_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton(text="🔙 Назад к товарам", callback_data="back_to_products")]
    ])

def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data="paid")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_products")]
    ])

def admin_order_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Отправить гео и фото", callback_data=f"deliver_{order_id}")],
        [InlineKeyboardButton(text="❌ Отменить заказ", callback_data=f"cancel_{order_id}")]
    ])

def delivery_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Отправить геолокацию", callback_data="send_location")],
        [InlineKeyboardButton(text="📸 Отправить фото", callback_data="send_photo")],
        [InlineKeyboardButton(text="✅ Готово", callback_data="delivery_done")]
    ])