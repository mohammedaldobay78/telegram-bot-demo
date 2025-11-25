# handlers/leaderboard_handler.py
from telebot import TeleBot
from db import get_top10

def register_leaderboard_handler(bot: TeleBot):
    @bot.message_handler(commands=["leaderboard", "leaderboard"])
    def leaderboard_cmd(message):
        top = get_top10()

        if not top:
            bot.send_message(message.chat.id, "لا يوجد متصدرين بعد.")
            return

        text = "🏆 **قائمة المتصدرين Top 10**\n\n"
        medals = ["🥇", "🥈", "🥉"]

        for i, user in enumerate(top, start=1):
            medal = medals[i-1] if i <= 3 else f"{i}️⃣"
            username = user.get('username') or "—"
            xp = user.get('xp', 0)
            text += f"{medal} @{username} — {xp} XP\n"

        bot.send_message(message.chat.id, text, parse_mode="Markdown")