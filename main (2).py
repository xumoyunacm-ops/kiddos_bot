# -*- coding: utf-8 -*-
"""
Kiddos Showroom — бот подтверждения визитов.
Шаги клиента: имя -> телефон -> удобная дата -> заявка уходит в групповой чат.

Версия для Railway: токен и chat_id берутся из переменных окружения,
чтобы их не было в коде.
"""

import os
import logging
import telebot
from telebot import types

# ---------- логи (видно в Railway -> Deployments -> Logs) ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s"
)
log = logging.getLogger("kiddos")

# ---------- настройки из переменных окружения ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID", "").strip()

if not BOT_TOKEN:
    raise SystemExit("❌ Не задан BOT_TOKEN. Добавьте его в Variables на Railway.")
if not GROUP_CHAT_ID:
    raise SystemExit("❌ Не задан GROUP_CHAT_ID. Добавьте его в Variables на Railway.")

try:
    GROUP_CHAT_ID = int(GROUP_CHAT_ID)
except ValueError:
    raise SystemExit("❌ GROUP_CHAT_ID должен быть числом, например -1001234567890")

bot = telebot.TeleBot(BOT_TOKEN)
sessions = {}


@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    sessions[chat_id] = {}
    bot.send_message(
        chat_id,
        "🧸 Добро пожаловать в Kiddos Showroom!\n\n"
        "Рады подтвердить Ваш визит. Ответьте, пожалуйста, "
        "на 3 коротких вопроса.\n\n"
        "1️⃣ Как Вас зовут? (имя и компания)",
    )
    bot.register_next_step_handler(message, ask_phone)


def ask_phone(message):
    chat_id = message.chat.id
    sessions.setdefault(chat_id, {})
    sessions[chat_id]["name"] = (message.text or "").strip()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 Отправить мой номер", request_contact=True))
    bot.send_message(
        chat_id,
        "2️⃣ Укажите Ваш номер телефона.\n"
        "Нажмите кнопку ниже или напишите вручную.",
        reply_markup=markup,
    )
    bot.register_next_step_handler(message, ask_date)


def ask_date(message):
    chat_id = message.chat.id
    sessions.setdefault(chat_id, {})
    if getattr(message, "contact", None):
        sessions[chat_id]["phone"] = message.contact.phone_number
    else:
        sessions[chat_id]["phone"] = (message.text or "").strip()

    bot.send_message(
        chat_id,
        "3️⃣ Какая дата и время Вам удобны?\n"
        "Например: 25 июня, после 14:00",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(message, finish)


def finish(message):
    chat_id = message.chat.id
    sessions.setdefault(chat_id, {})
    sessions[chat_id]["date"] = (message.text or "").strip()
    data = sessions.get(chat_id, {})

    user = message.from_user
    username = f"@{user.username}" if user.username else "(без username)"

    # Без Markdown: данные клиента шлём чистым текстом,
    # иначе символы _ * ( ломают разметку и Telegram отклоняет сообщение.
    report = (
        "✅ Новое подтверждение визита\n\n"
        f"👤 Имя: {data.get('name', '—')}\n"
        f"📞 Телефон: {data.get('phone', '—')}\n"
        f"🗓 Удобная дата: {data.get('date', '—')}\n"
        f"✈️ Telegram: {username}"
    )
    try:
        bot.send_message(GROUP_CHAT_ID, report)
    except Exception as e:
        log.error("Не удалось отправить заявку в группу: %s", e)

    bot.send_message(
        chat_id,
        "🎉 Спасибо! Ваш визит зарегистрирован.\n\n"
        "Мы свяжемся с Вами для подтверждения времени.\n"
        "До встречи в Kiddos Showroom! 🧸💙💛",
    )
    sessions.pop(chat_id, None)


@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "Чтобы подтвердить визит, нажмите /start")


if __name__ == "__main__":
    log.info("Kiddos bot запущен...")
    # skip_pending=True — не отвечать на старые сообщения после перезапуска
    bot.infinity_polling(skip_pending=True, timeout=30)
