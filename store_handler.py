# handlers/store_handler.py
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from db import add_coins, get_user_profile, purchase_item, get_item_link, get_store_items

AI_BOT_USERNAME = "Your_AI_Bot_Username_Here"

STORE_ITEMS = {
    "xp_boost": {"name": "⚡ Boost XP ×2 (24h)", "price": 300, "desc": "يضاعف XP لمدة 24 ساعة"},
    "premium_lesson": {"name": "🌟 Premium Lesson", "price": 500, "desc": "يفتح درس مميز"},
    "quiz_retry": {"name": "🔄 Quiz Retry", "price": 200, "desc": "إعادة محاولة اختبار"},
    "profile_badge": {"name": "🎖️ Profile Badge", "price": 150, "desc": "شارة مميزة لملفك الشخصي"},
    "skip_lesson": {"name": "⏭️ Skip Lesson", "price": 250, "desc": "تخطي درس واحد"},
    "ai_24": {"name": "🤖 AI Access 24h", "price": 700, "desc": "وصول كامل لبوت الـ AI لمدة 24 ساعة"},
    "ai_chat_training": {"name": "🗣 AI Conversation Training", "price": 900, "desc": "تدريب محادثة احترافي"},
    "ai_premium": {"name": "🌟 AI Premium Unlimited", "price": 2500, "desc": "وصول غير محدود لمدة شهر"}
}

def store_menu(bot: TeleBot, chat_id):
    kb = InlineKeyboardMarkup(row_width=1)
    for key, item in STORE_ITEMS.items():
        kb.add(InlineKeyboardButton(text=f"{item['name']} — {item['price']}🪙", callback_data=f"buy:{key}"))
    bot.send_message(chat_id, "🛒 *المتجر — اختر منتجًا للشراء*\nبعد الشراء سيتم تفعيل المنتج مباشرة.\n\n💰 Coins تحصل عليها من الدروس والاختبارات.", reply_markup=kb, parse_mode="Markdown")

def handle_purchase(bot: TeleBot, call):
    user_id = call.from_user.id
    product_key = call.data.split(":")[1]
    if product_key not in STORE_ITEMS:
        bot.answer_callback_query(call.id, "❌ المنتج غير موجود!")
        return

    item = STORE_ITEMS[product_key]
    user = get_user_profile(user_id)
    if not user:
        bot.answer_callback_query(call.id, "❌ لم يتم العثور على ملفك! اكتب /start", show_alert=True)
        return

    if user.get("coins", 0) < item["price"]:
        bot.answer_callback_query(call.id, "❌ ليس لديك Coins كافية!", show_alert=True)
        return

    # خصم السعر
    add_coins(user_id, -item["price"])
    bot.answer_callback_query(call.id, "✔️ تمت عملية الشراء بنجاح!", show_alert=True)

    if product_key.startswith("ai_"):
        bot.send_message(call.message.chat.id, f"🎉 *مبرووك!*\nلقد اشتريت: *{item['name']}*\n\n🤖 رابط الوصول إلى بوت الـ AI:\nhttps://t.me/{AI_BOT_USERNAME}\n\n📌 {item['desc']}", parse_mode="Markdown")
        return

    bot.send_message(call.message.chat.id, f"🎉 *تم الشراء!*\nالمنتج: *{item['name']}*\n\n📌 {item['desc']}", parse_mode="Markdown")

def register(bot: TeleBot):
    @bot.message_handler(commands=['store'])
    def store_cmd(message: Message):
        store_menu(bot, message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy:"))
    def buy_handler(call):
        handle_purchase(bot, call)

    return bot