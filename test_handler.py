# handlers/test_handler.py
from telebot import TeleBot
from telebot.types import Message, PollAnswer
from db import create_user_if_not_exists, update_user_test_result
import threading
import time

# -----------------------------------------------------
# قائمة الأسئلة — 30 سؤال
# -----------------------------------------------------
questions = [
    {"q": "She ____ to school every day.", "choices": ["go", "goes", "going"], "answer": 1},
    {"q": "They ____ happy yesterday.", "choices": ["were", "are", "is"], "answer": 0},
    {"q": "I would like ____ tea, please.", "choices": ["a", "some", "any"], "answer": 1},
    {"q": "He can't ____ the car.", "choices": ["drive", "drives", "driving"], "answer": 0},
    {"q": "We ____ to the cinema last week.", "choices": ["go", "went", "goes"], "answer": 1},

    {"q": "She is taller ____ her brother.", "choices": ["than", "then", "that"], "answer": 0},
    {"q": "This book is ____ interesting.", "choices": ["much", "very", "many"], "answer": 1},
    {"q": "He ____ breakfast every morning.", "choices": ["eat", "eating", "eats"], "answer": 2},
    {"q": "There ____ a cat on the roof.", "choices": ["is", "are", "be"], "answer": 0},
    {"q": "I ____ the movie already.", "choices": ["saw", "have seen", "see"], "answer": 1},

    {"q": "We ____ in this city since 2010.", "choices": ["live", "lived", "have lived"], "answer": 2},
    {"q": "She ____ English very well.", "choices": ["speaks", "speak", "speaking"], "answer": 0},
    {"q": "The weather is ____ today.", "choices": ["beautiful", "beautifully", "beauty"], "answer": 0},
    {"q": "He didn’t ____ the exam.", "choices": ["pass", "passed", "passing"], "answer": 0},
    {"q": "____ you like some coffee?", "choices": ["Do", "Would", "Are"], "answer": 1},

    {"q": "My brother is ____ engineer.", "choices": ["an", "a", "the"], "answer": 0},
    {"q": "They ____ TV when I arrived.", "choices": ["watch", "were watching", "watched"], "answer": 1},
    {"q": "I ____ to London twice.", "choices": ["have been", "was", "go"], "answer": 0},
    {"q": "If it rains, we ____ stay home.", "choices": ["will", "would", "are"], "answer": 0},
    {"q": "He is ____ than me.", "choices": ["more fast", "faster", "fastly"], "answer": 1},

    {"q": "The car ____ by John.", "choices": ["was driven", "drove", "driven"], "answer": 0},
    {"q": "She asked me ____ I was fine.", "choices": ["if", "when", "that"], "answer": 0},
    {"q": "This is the place ____ we met.", "choices": ["what", "where", "who"], "answer": 1},
    {"q": "I don't mind ____ you.", "choices": ["help", "helping", "helped"], "answer": 1},
    {"q": "It was ____ interesting story.", "choices": ["an", "a", "the"], "answer": 0},

    {"q": "I prefer tea ____ coffee.", "choices": ["than", "to", "over"], "answer": 1},
    {"q": "She has ____ friends in London.", "choices": ["much", "many", "a"], "answer": 1},
    {"q": "He said that he ____ busy.", "choices": ["is", "was", "were"], "answer": 1},
    {"q": "They ____ finished their homework.", "choices": ["haven't", "didn't", "not"], "answer": 0},
    {"q": "She ____ her keys yesterday.", "choices": ["loses", "lost", "lose"], "answer": 1},
]

# -----------------------------------------------------
# Hint لكل سؤال
# -----------------------------------------------------
hints = [
    "💡 Hint: مع She/He نضيف s → goes",
    "💡 Hint: yesterday = ماضي → were",
    "💡 Hint: some تُستخدم مع الأشياء غير المعدودة",
    "💡 Hint: بعد can/can’t نستخدم الفعل بدون s",
    "💡 Hint: الماضي من go هو went",
    "💡 Hint: taller → than",
    "💡 Hint: very تستخدم مع الصفات",
    "💡 Hint: He + verb → eats",
    "💡 Hint: للمفرد نستخدم is",
    "💡 Hint: present perfect → have seen",
    "💡 Hint: since → have lived",
    "💡 Hint: She → speaks",
    "💡 Hint: beautiful صفة",
    "💡 Hint: بعد didn’t نستخدم الفعل بدون ed",
    "💡 Hint: would you like",
    "💡 Hint: engineer تبدأ بحرف متحرك → an",
    "💡 Hint: past continuous → were watching",
    "💡 Hint: have been",
    "💡 Hint: If + present → will",
    "💡 Hint: المقارنة → faster",
    "💡 Hint: passive → was driven",
    "💡 Hint: reported question → if",
    "💡 Hint: المكان → where",
    "💡 Hint: don't mind → helping",
    "💡 Hint: تبدأ بصوتي → an",
    "💡 Hint: prefer → to",
    "💡 Hint: friends (جمع) → many",
    "💡 Hint: reported speech للماضي → was",
    "💡 Hint: haven't + past participle",
    "💡 Hint: yesterday → lost",
]

# -----------------------------------------------------
# تحديد المستوى
# -----------------------------------------------------
def determine_level(score):
    if score <= 9:
        return "A1"
    elif score <= 16:
        return "A2"
    elif score <= 23:
        return "B1"
    else:
        return "B2"

# -----------------------------------------------------
# التسجيل
# -----------------------------------------------------
def register(bot: TeleBot):
    sessions = {}   # user_id: {score, index, answered}

    @bot.message_handler(commands=["test"])
    def start_test(message: Message):
        user_id = message.from_user.id
        create_user_if_not_exists(user_id, message.from_user.username)

        sessions[user_id] = {"score": 0, "index": 0, "answered": False}

        bot.send_message(message.chat.id,
            "📘 *اختبار تحديد المستوى (Poll + Timer)*\n\n"
            "⏳ لديك 10 ثوانٍ لكل سؤال.\n"
            "❌ إذا أخطأت → يظهر Hint قبل الانتقال للسؤال التالي.",
            parse_mode="Markdown"
        )

        send_poll(bot, message.chat.id, user_id)

    # ---------------------------------------------------
    # إرسال Poll + تشغيل المؤقت
    # ---------------------------------------------------
    def send_poll(bot, chat_id, user_id):
        session = sessions[user_id]
        session["answered"] = False  # إعادة الحالة للسؤال الجديد

        idx = session["index"]
        q = questions[idx]

        bot.send_poll(
            chat_id,
            question=f"{idx+1}) {q['q']}",
            options=q["choices"],
            type="quiz",
            correct_option_id=q["answer"],
            is_anonymous=False
        )

        # تشغيل التايمر
        threading.Thread(target=start_timer, args=(bot, user_id, chat_id, idx), daemon=True).start()

    # ---------------------------------------------------
    # التايمر: 10 ثوانٍ
    # ---------------------------------------------------
    def start_timer(bot, user_id, chat_id, question_idx):
        time.sleep(10)

        # إذا المستخدم لم يجاوب خلال 10 ثوان
        if user_id in sessions:
            if sessions[user_id]["index"] == question_idx and sessions[user_id]["answered"] == False:
                bot.send_message(chat_id, "⏳ انتهى الوقت! ننتقل للسؤال التالي…")
                sessions[user_id]["index"] += 1

                # اختبار النهاية
                if sessions[user_id]["index"] >= len(questions):
                    finish_test(bot, user_id)
                    return

                send_poll(bot, chat_id, user_id)

    # ---------------------------------------------------
    # استقبال إجابة المستخدم على Poll
    # ---------------------------------------------------
    @bot.poll_answer_handler()
    def handle_poll_answer(poll: PollAnswer):
        user_id = poll.user.id

        if user_id not in sessions:
            return

        session = sessions[user_id]

        # تجاهل الإجابة إذا الوقت انتهى
        if session["answered"]:
            return

        session["answered"] = True
        idx = session["index"]

        correct_answer = questions[idx]["answer"]
        user_answer = poll.option_ids[0]

        # خاطئة → Hint
        if user_answer != correct_answer:
            bot.send_message(user_id, hints[idx])
        else:
            session["score"] += 1

        # سؤال جديد
        session["index"] += 1

        if session["index"] >= len(questions):
            finish_test(bot, user_id)
            return

        send_poll(bot, user_id, user_id)

    # ---------------------------------------------------
    # إنهاء الاختبار
    # ---------------------------------------------------
    def finish_test(bot, user_id):
        score = sessions[user_id]["score"]
        level = determine_level(score)

        update_user_test_result(user_id, level, score)

        bot.send_message(
            user_id,
            f"🎯 *انتهى الاختبار!*\n\n"
            f"نتيجتك: *{score} / {len(questions)}*\n"
            f"مستواك: *{level}*",
            parse_mode="Markdown"
        )

        del sessions[user_id]

    return bot