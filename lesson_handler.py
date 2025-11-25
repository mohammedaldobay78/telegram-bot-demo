# handlers/quiz_handler.py
import os
import json
from telebot import TeleBot
from telebot.types import Message
from db import (
    get_user_data,
    create_user_if_not_exists,
    add_xp,            # يجب إضافتها في db.py
    add_coins,         # يجب إضافتها في db.py
    save_quiz_result,  # يجب إضافتها في db.py
    update_quiz_progress
)

LESSONS_DIR = "lessons"
QUIZ_DIR = "quizzes"

# ذاكرة مؤقتة لتتبع Polls النشطة: poll_id -> context
# context: { "user_id", "chat_id", "questions", "current_idx", "lesson_id" }
active_polls = {}

def register(bot: TeleBot):
    @bot.message_handler(commands=['quiz'])
    def start_lesson_quiz(message: Message):
        user = message.from_user
        create_user_if_not_exists(user.id, user.username or user.first_name)
        u = get_user_data(user.id)
        level = u.get("level", "A1")
        progress = u.get("progress", 0)

        # الدرس الأخير الذي عُرض هو progress-1 (لأننا زودنا بعد عرض الدرس)
        lesson_index = max(0, progress - 1)
        level_dir = os.path.join(LESSONS_DIR, level)
        lesson_files = sorted([f for f in os.listdir(level_dir) if f.endswith(".json")])
        if lesson_index >= len(lesson_files):
            bot.send_message(message.chat.id, "❗ لا يوجد درس للاختبار حالياً.")
            return

        lesson_file = lesson_files[lesson_index]
        lesson_path = os.path.join(level_dir, lesson_file)

        try:
            with open(lesson_path, "r", encoding="utf-8") as f:
                lesson = json.load(f)
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ خطأ أثناء تحميل ملف الدرس:\n{e}")
            return

        # نأخذ الأسئلة من الجزء multiple_choice داخل exercises
        questions = lesson.get("exercises", {}).get("multiple_choice", [])
        if not questions:
            bot.send_message(message.chat.id, "❗ لا توجد أسئلة اختيارية لهذا الدرس.")
            return

        # نبدأ من السؤال الأول
        q0 = questions[0]
        options = q0.get("options", [])
        # نحاول إيجاد index الجواب الصحيح إذا وُجد في ملف الدرس (نقارن بالنص)
        correct_idx = None
        ans_text = q0.get("answer")
        if ans_text is not None:
            try:
                correct_idx = options.index(ans_text)
            except ValueError:
                correct_idx = None

        # ترسل Poll (quiz type if correct_idx available)
        if correct_idx is not None:
            poll = bot.send_poll(
                message.chat.id,
                q0.get("question"),
                options,
                is_anonymous=False,
                type='quiz',
                correct_option_id=correct_idx
            )
        else:
            poll = bot.send_poll(
                message.chat.id,
                q0.get("question"),
                options,
                is_anonymous=False
            )

        # احفظ الريدع (poll_id) في الذاكرة مع السياق
        active_polls[poll.poll.id] = {
            "user_id": user.id,
            "chat_id": message.chat.id,
            "questions": questions,
            "current_idx": 0,
            "lesson_id": lesson_file  # أو يمكنك حفظ lesson.get("lesson_id")
        }

        bot.send_message(message.chat.id, "🔔 اجب على الاختبار عبر التصويت في Polls. سيتم الحساب وحفظ النتائج تلقائياً.")

    # -----------------------------------------
    # عندما يرد المستخدم على Poll (الإجابة على سؤال)
    # -----------------------------------------
    @bot.poll_answer_handler()
    def handle_poll_answer(poll_answer):
        # poll_answer: has fields poll_id, user, option_ids (list)
        poll_id = poll_answer.poll_id
        user_id = poll_answer.user.id
        selected_options = poll_answer.option_ids  # list of selected option indices

        ctx = active_polls.get(poll_id)
        if not ctx:
            # ليس ضمن اختباراتنا النشطة
            return

        # فقط نفس المستخدم يقدر يجاوب (أو نحسب للجميع؟ هنا نحسب فقط لصاحب الاختبار)
        if user_id != ctx["user_id"]:
            # تجاهل أو يمكنك إرسال رسالة: "هذا الاختبار ليس لك"
            return

        q_idx = ctx["current_idx"]
        questions = ctx["questions"]
        chat_id = ctx["chat_id"]
        lesson_id = ctx["lesson_id"]

        # تأكد من صحة index
        if q_idx >= len(questions):
            return

        q = questions[q_idx]
        options = q.get("options", [])
        correct_answer_text = q.get("answer")

        # المستخدم قد يختار إجابة واحدة فقط (القيمة الأولى)
        selected_idx = selected_options[0] if selected_options else None
        selected_text = options[selected_idx] if selected_idx is not None and selected_idx < len(options) else None

        # تحقق من الصحة
        is_correct = False
        if correct_answer_text is not None and selected_text is not None:
            is_correct = (selected_text == correct_answer_text)

        # منح XP/Coins حسب النتيجة
        xp_gain = 10 if is_correct else 2
        coins_gain = 5 if is_correct else 0

        try:
            add_xp(user_id, xp_gain)
            add_coins(user_id, coins_gain)
        except Exception:
            # إذا لم توجد الدوال أو حصل خطأ، لا نكسر البوت - لكن الأفضل إضافة الدوال في db.py
            pass

        # حفظ نتيجة السؤال في DB
        try:
            save_quiz_result(
                user_id=user_id,
                lesson_id=lesson_id,
                question_index=q_idx,
                selected_option=selected_text,
                correct=is_correct
            )
        except Exception:
            pass

        # أرسل نتيجة قصيرة للمستخدم
        if is_correct:
            bot.send_message(chat_id, f"✅ إجابة صحيحة! +{xp_gain} XP, +{coins_gain} coins")
        else:
            correct_msg = f" (الإجابة الصحيحة: {correct_answer_text})" if correct_answer_text else ""
            bot.send_message(chat_id, f"❌ إجابة خاطئة.{correct_msg} +{xp_gain} XP", parse_mode="Markdown")

        # ---- ارسال السؤال التالي إن وجد ----
        next_idx = q_idx + 1
        if next_idx < len(questions):
            next_q = questions[next_idx]
            opts = next_q.get("options", [])
            # إيجاد index للإجابة الصحيحة إن وُجد
            corr_idx = None
            atext = next_q.get("answer")
            if atext is not None:
                try:
                    corr_idx = opts.index(atext)
                except ValueError:
                    corr_idx = None

            if corr_idx is not None:
                new_poll = bot.send_poll(
                    chat_id,
                    next_q.get("question"),
                    opts,
                    is_anonymous=False,
                    type='quiz',
                    correct_option_id=corr_idx
                )
            else:
                new_poll = bot.send_poll(
                    chat_id,
                    next_q.get("question"),
                    opts,
                    is_anonymous=False
                )

            # حدّث السياق: احذف المفتاح القديم وأضف الجديد مع current_idx جديد
            try:
                del active_polls[poll_id]
            except KeyError:
                pass

            active_polls[new_poll.poll.id] = {
                "user_id": user_id,
                "chat_id": chat_id,
                "questions": questions,
                "current_idx": next_idx,
                "lesson_id": lesson_id
            }

        else:
            # انتهت الأسئلة
            try:
                del active_polls[poll_id]
            except KeyError:
                pass

            bot.send_message(chat_id, "🏁 انتهى الاختبار. نُشكر إجاباتك! تم حفظ النتائج وحساب المكافآت.")
            # تسجيل تقدم / كويز مكتمل لو تحب
            try:
                update_quiz_progress(user_id, 1)
            except Exception:
                pass