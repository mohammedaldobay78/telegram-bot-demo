# handlers/quiz_handler.py
import os
import json
from telebot import TeleBot
from telebot.types import Message
from db import create_user_if_not_exists, get_user_data, add_xp, add_coins, save_quiz_result, update_quiz_progress

LESSONS_DIR = "lessons"

# نشيك وجود مجلد الدروس/الاختبارات عند الطلب
active_polls = {}

def register_quiz_handler(bot: TeleBot):

    @bot.message_handler(commands=['quiz'])
    def start_lesson_quiz(message: Message):
        user = message.from_user
        create_user_if_not_exists(user.id, user.username or user.first_name)
        u = get_user_data(user.id)
        level = u.get("level", "A1")
        progress = u.get("progress", 0)

        lesson_index = max(0, progress - 1)
        level_dir = os.path.join(LESSONS_DIR, level)
        if not os.path.isdir(level_dir):
            bot.send_message(message.chat.id, "❗ لا يوجد دروس لهذا المستوى بعد.")
            return
        lesson_files = sorted([f for f in os.listdir(level_dir) if f.endswith(".json")])
        if not lesson_files:
            bot.send_message(message.chat.id, "❗ لا توجد دروس بهذا المستوى.")
            return

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

        questions = lesson.get("exercises", {}).get("multiple_choice", [])
        if not questions:
            bot.send_message(message.chat.id, "❗ لا توجد أسئلة اختيارية لهذا الدرس.")
            return

        q0 = questions[0]
        options = q0.get("options", [])
        correct_idx = None
        ans_text = q0.get("answer")
        if ans_text is not None:
            try:
                correct_idx = options.index(ans_text)
            except ValueError:
                correct_idx = None

        if correct_idx is not None:
            poll = bot.send_poll(message.chat.id, q0.get("question"), options, is_anonymous=False, type='quiz', correct_option_id=correct_idx)
        else:
            poll = bot.send_poll(message.chat.id, q0.get("question"), options, is_anonymous=False)

        active_polls[poll.poll.id] = {
            "user_id": user.id,
            "chat_id": message.chat.id,
            "questions": questions,
            "current_idx": 0,
            "lesson_id": lesson_file
        }

        bot.send_message(message.chat.id, "🔔 اجب على الاختبار عبر Poll. سيتم الحساب وحفظ النتائج تلقائياً.")

    @bot.poll_answer_handler()
    def handle_poll_answer(poll_answer):
        poll_id = poll_answer.poll_id
        user_id = poll_answer.user.id
        selected_options = poll_answer.option_ids

        ctx = active_polls.get(poll_id)
        if not ctx:
            return

        if user_id != ctx["user_id"]:
            return

        q_idx = ctx["current_idx"]
        questions = ctx["questions"]
        chat_id = ctx["chat_id"]
        lesson_id = ctx["lesson_id"]

        if q_idx >= len(questions):
            return

        q = questions[q_idx]
        options = q.get("options", [])
        correct_answer_text = q.get("answer")

        selected_idx = selected_options[0] if selected_options else None
        selected_text = options[selected_idx] if selected_idx is not None and selected_idx < len(options) else None

        is_correct = False
        if correct_answer_text is not None and selected_text is not None:
            is_correct = (selected_text == correct_answer_text)

        xp_gain = 10 if is_correct else 2
        coins_gain = 5 if is_correct else 0

        try:
            add_xp(user_id, xp_gain)
            add_coins(user_id, coins_gain)
        except Exception:
            pass

        try:
            save_quiz_result(user_id=user_id, lesson_id=lesson_id, question_index=q_idx, selected_option=selected_text, correct=is_correct)
        except Exception:
            pass

        if is_correct:
            bot.send_message(chat_id, f"✅ إجابة صحيحة! +{xp_gain} XP, +{coins_gain} coins")
        else:
            correct_msg = f" (الإجابة الصحيحة: {correct_answer_text})" if correct_answer_text else ""
            bot.send_message(chat_id, f"❌ إجابة خاطئة.{correct_msg} +{xp_gain} XP", parse_mode="Markdown")

        next_idx = q_idx + 1
        try:
            del active_polls[poll_id]
        except KeyError:
            pass

        if next_idx < len(questions):
            next_q = questions[next_idx]
            opts = next_q.get("options", [])
            corr_idx = None
            atext = next_q.get("answer")
            if atext is not None:
                try:
                    corr_idx = opts.index(atext)
                except ValueError:
                    corr_idx = None

            if corr_idx is not None:
                new_poll = bot.send_poll(chat_id, next_q.get("question"), opts, is_anonymous=False, type='quiz', correct_option_id=corr_idx)
            else:
                new_poll = bot.send_poll(chat_id, next_q.get("question"), opts, is_anonymous=False)

            active_polls[new_poll.poll.id] = {
                "user_id": user_id,
                "chat_id": chat_id,
                "questions": questions,
                "current_idx": next_idx,
                "lesson_id": lesson_id
            }
        else:
            bot.send_message(chat_id, "🏁 انتهى الاختبار. تم حفظ النتائج وحساب المكافآت.")
            # ملخّص: نزيد كويز مكتمل
            try:
                update_quiz_progress(user_id, 1)
            except Exception:
                pass