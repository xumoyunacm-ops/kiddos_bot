import os 

BOT_TOKEN = "8868462463:AAE3whoXo02aauhwMbV_9ya1DWWiYE65VX8"      # 
GROUP_CHAT_ID = -5511435642               #
# -*- coding: utf-8 -*-
"""
Kiddos Showroom — бот подтверждения визитов.
Спрашивает: имя -> телефон -> удобную дату, затем присылает заявку в групповой чат.

Запуск: python kiddos_bot.py
Нужна библиотека: pip install pyTelegramBotAPI
"""

import telebot
from telebot import types

# ====================== НАСТРОЙКИ ======================
# 1) Токен бота от @BotFather (см. инструкцию, шаг 1)
BOT_TOKEN = "ВСТАВЬТЕ_СЮДА_ТОКЕН_БОТА"

# 2) ID группового чата, куда приходят заявки (см. инструкцию, шаг 3)
#    Для группы это ОТРИЦАТЕЛЬНОЕ число, например: -1001234567890
GROUP_CHAT_ID = -1000000000000
# =======================================================

bot = telebot.TeleBot(BOT_TOKEN)

# временное хранилище ответов по каждому пользователю
sessions = {}


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    sessions[chat_id] = {}
    bot.send_message(
        chat_id,
        "🧸 Добро пожаловать в *Kiddos Showroom*!\n\n"
        "Рады подтвердить Ваш визит. Ответьте, пожалуйста, на 3 коротких вопроса.\n\n"
        "1️⃣ Как Вас зовут? (имя и компания)",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, ask_phone)


def ask_phone(message):
    chat_id = message.chat.id
    sessions.setdefault(chat_id, {})
    sessions[chat_id]['name'] = message.text.strip()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 Отправить мой номер", request_contact=True))
    bot.send_message(
        chat_id,
        "2️⃣ Укажите Ваш номер телефона.\n"
        "Можно нажать кнопку ниже или написать вручную.",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, ask_date)


def ask_date(message):
    chat_id = message.chat.id
    if message.contact is not None:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()
    sessions[chat_id]['phone'] = phone

    bot.send_message(
        chat_id,
        "3️⃣ Какая дата и время Вам удобны для визита?\n"
        "Например: «25 июня, после 14:00»",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(message, finish)


def finish(message):
    chat_id = message.chat.id
    sessions[chat_id]['date'] = message.text.strip()
    data = sessions.get(chat_id, {})

    user = message.from_user
    username = f"@{user.username}" if user.username else "(без username)"

    # заявка в групповой чат
    report = (
        "✅ *Новое подтверждение визита*\n\n"
        f"👤 Имя: {data.get('name','—')}\n"
        f"📞 Телефон: {data.get('phone','—')}\n"
        f"🗓 Удобная дата: {data.get('date','—')}\n"
        f"✈️ Telegram: {username}"
    )
    try:
        bot.send_message(GROUP_CHAT_ID, report, parse_mode="Markdown")
    except Exception as e:
        print("Ошибка отправки в группу:", e)

    # ответ клиенту
    bot.send_message(
        chat_id,
        "🎉 Спасибо! Ваш визит зарегистрирован.\n\n"
        "Мы свяжемся с Вами для подтверждения времени.\n"
        "До встречи в *Kiddos Showroom*! 🧸💙💛",
        parse_mode="Markdown"
    )
    sessions.pop(chat_id, None)


@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "Чтобы подтвердить визит, нажмите /start")


if __name__ == "__main__":
    print("Kiddos bot запущен...")
    bot.infinity_polling()
