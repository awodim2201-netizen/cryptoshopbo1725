import os
import asyncio
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

# ===== ВСТАВЬТЕ СВОЙ ТОКЕН СЮДА =====
TOKEN = "8839023929:AAF8dmk-WN6nuRImxQgwiQDPIm2qwIJA-tg"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Тестовый бот работает!", 200

# Единственная команда — /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("✅ БОТ РАБОТАЕТ! Соединение с Telegram установлено.")

# Команда /ping для проверки
@dp.message(Command("ping"))
async def ping(message: Message):
    await message.answer("🏓 Pong!")

# Ловим любое текстовое сообщение
@dp.message()
async def echo(message: Message):
    await message.answer(f"Вы написали: {message.text}")

async def main():
    print("🚀 Тестовый бот запускается...")
    await dp.start_polling(bot)

def run_bot():
    asyncio.run(main())

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Запускаем Flask в фоне
    thread = Thread(target=run_flask)
    thread.start()
    # Запускаем бота
    asyncio.run(main())
