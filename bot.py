# bot.py
import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from db import init_db

# import handlers
from handlers import (
    start_handler,
    test_handler,
    lesson_handler,
    quiz_handler,
    profile_handler,
    leaderboard_handler,
    store_handler
)

TOKEN = os.environ.get("TELEGRAM_TOKEN") or "8546655963:AAFfHBEgyP6I4U2VjYRVLISqiAXOJ6oEirk"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

init_db()

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    btn_start = KeyboardButton("🏁 Start")
    btn_test = KeyboardButton("🧪 Test")
    btn_lessons = KeyboardButton("📘 Lesson")
    btn_store = KeyboardButton("🛒 Store")
    btn_leaderboard = KeyboardButton("🏆 Leaderboard")
    btn_profile = KeyboardButton("👤 Profile")
    kb.row(btn_start, btn_test)
    kb.row(btn_lessons, btn_store)
    kb.row(btn_leaderboard, btn_profile)
    return kb

@bot.message_handler(func=lambda m: m.text in ["🏁 Start", "🧪 Test", "📘 Lessons", "🛒 Store", "🏆 Leaderboard", "👤 Profile"])
def menu_router(message):
    if message.text == "🏁 Start":
        bot.send_message(message.chat.id, "⚡ اكتب /start للبدء.", reply_markup=main_menu())
    elif message.text == "🧪 Test":
        bot.send_message(message.chat.id, "اكتب /test لبدء اختبار تحديد المستوى.", reply_markup=main_menu())
    elif message.text == "📘 Lessons":
        bot.send_message(message.chat.id, "اكتب /lesson لبدء الدرس التالي.", reply_markup=main_menu())
    elif message.text == "🛒 Store":
        bot.send_message(message.chat.id, "اكتب /store لفتح المتجر.", reply_markup=main_menu())
    elif message.text == "🏆 Leaderboard":
        bot.send_message(message.chat.id, "اكتب /leaderboard لعرض المتصدرين.", reply_markup=main_menu())
    elif message.text == "👤 Profile":
        bot.send_message(message.chat.id, "اكتب /profile لعرض ملفك.", reply_markup=main_menu())

# register handlers (كل ملف يرجع نفسه أو دالة تسجيل)
start_handler.register(bot)
test_handler.register(bot)
# lesson_handler: إن كان لديك register تابع له
try:
    lesson_handler.register(bot)
except Exception:
    pass

quiz_handler.register_quiz_handler(bot)
profile_handler.register(bot)
leaderboard_handler.register_leaderboard_handler(bot)
store_handler.register(bot)

if __name__ == "__main__":
    print("Bot started successfully...")
    bot.infinity_polling()
    
    
