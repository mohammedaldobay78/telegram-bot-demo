# handlers/profile_handler.py
from telebot import TeleBot
from telebot.types import Message
from db import get_user_profile, get_user_rank

PROFILE_ICON = "👤"
XP_ICON = "⚡"
LEVEL_ICON = "🏅"
COINS_ICON = "💰"
LESSON_ICON = "📘"
QUIZ_ICON = "📝"
RANK_ICON = "📊"

def register(bot: TeleBot):
    @bot.message_handler(commands=['profile'])
    def profile_cmd(message: Message):
        user_id = message.from_user.id

        data = get_user_profile(user_id)
        if not data:
            bot.reply_to(message, "❗ لا توجد بيانات لهذا المستخدم. أرسل /start.")
            return

        rank = get_user_rank(user_id) or "—"

        text = (
            f"{PROFILE_ICON} *ملفك الشخصي*\n"
            f"━━━━━━━━━━━━━━\n"
            f"{XP_ICON} *XP:* {data.get('xp', 0)}\n"
            f"{LEVEL_ICON} *Level:* {data.get('level', 'A1')}\n"
            f"{COINS_ICON} *Coins:* {data.get('coins', 0)}\n"
            f"{LESSON_ICON} *الدروس المكتملة:* {data.get('lessons_completed', data.get('progress', 0))}\n"
            f"{QUIZ_ICON} *الاختبارات المكتملة:* {data.get('quizzes_completed', 0)}\n"
            f"{RANK_ICON} *ترتيبك:* {rank}\n"
            f"━━━━━━━━━━━━━━\n"
            f"اكتب /leaderboard لعرض المتصدرين 🔥"
        )

        bot.reply_to(message, text, parse_mode="Markdown")

    return bot