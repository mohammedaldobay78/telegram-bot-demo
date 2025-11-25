# handlers/start_handler.py
from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from db import create_user_if_not_exists, get_user_profile, get_user_rank

WELCOME_TEXT = """
👋 أهلاً بك في *Learn English Pro*!

📘 بوت متكامل لتعلم الإنجليزية عبر:
• دروس قصيرة وسهلة
• اختبارات بعد كل 5 دروس
• قياس مستوى تلقائي
• نظام XP + Levels
• متجر قادم قريباً 🔥

اختر من القائمة 👇
"""

def register(bot: TeleBot):

    def send_main_menu(chat_id):
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("/start", "/profile")
        kb.row("/test", "/lessons")
        kb.row("/store", "/leaderboard")
        bot.send_message(chat_id, "⚡ *القائمة الرئيسية*:", reply_markup=kb, parse_mode="Markdown")

    @bot.message_handler(commands=['start'])
    def start_cmd(message: Message):
        user = message.from_user
        create_user_if_not_exists(user.id, user.username or user.first_name)
        send_main_menu(message.chat.id)
        bot.send_message(message.chat.id, WELCOME_TEXT, parse_mode="Markdown")

    @bot.message_handler(commands=['profile'])
    def profile_cmd(message: Message):
        user_id = message.from_user.id
        profile = get_user_profile(user_id)
        rank = get_user_rank(user_id)
        if not profile:
            bot.reply_to(message, "❗ لم يتم العثور على بياناتك. اكتب /start لإعادة التسجيل.")
            return

        xp = profile.get("xp", 0)
        level = profile.get("level", "A1")
        lessons_done = profile.get("lessons_completed", profile.get("progress", 0))
        quizzes_done = profile.get("quizzes_completed", 0)

        text = f"""
🧑‍🎓 *ملفك الشخصي*:

🏅 المستوى: *{level}*
⭐ نقاط الخبرة XP: *{xp}*
📊 ترتيبك بين المتصدرين: *#{rank if rank else '—'}*

📚 دروس مكتملة: *{lessons_done}*
📝 اختبارات منجزة: *{quizzes_done}*

استمر! كل درس يعطيك XP 🤩
"""
        bot.send_message(message.chat.id, text, parse_mode="Markdown")

    return bot