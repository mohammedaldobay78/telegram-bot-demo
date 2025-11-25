# db.py — النسخة النهائية الشاملة
import sqlite3

DB_NAME = "bot.db"


# -----------------------------------------------------
# 🔥 إنشاء الجداول
# -----------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # جدول المستخدمين
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        level TEXT DEFAULT 'A1',
        xp INTEGER DEFAULT 0,
        progress INTEGER DEFAULT 0,
        quizzes_completed INTEGER DEFAULT 0,
        coins INTEGER DEFAULT 0
    )
    """)

    # المتجر
    c.execute("""
    CREATE TABLE IF NOT EXISTS store_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        price INTEGER,
        ai_bot_link TEXT
    )
    """)

    # عمليات الشراء
    c.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        user_id INTEGER,
        item_id INTEGER,
        purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # نتائج الكويزات
    c.execute("""
    CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        correct_answers INTEGER,
        total_questions INTEGER,
        score INTEGER,
        taken_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()


# -----------------------------------------------------
# 🔥 إنشاء مستخدم
# -----------------------------------------------------
def create_user_if_not_exists(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    exists = c.fetchone()

    if not exists:
        c.execute("""
        INSERT INTO users (user_id, username)
        VALUES (?, ?)
        """, (user_id, username))

    conn.commit()
    conn.close()


# -----------------------------------------------------
# 🔥 جلب بيانات المستخدم dict
# -----------------------------------------------------
def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT level, xp, progress, quizzes_completed
    FROM users WHERE user_id=?
    """, (user_id,))

    row = c.fetchone()
    conn.close()

    if not row:
        return {
            "level": "A1",
            "xp": 0,
            "progress": 0,
            "quizzes_completed": 0
        }

    return {
        "level": row[0],
        "xp": row[1],
        "progress": row[2],
        "quizzes_completed": row[3]
    }


# -----------------------------------------------------
# 🔥 دالة Profile كاملة
# -----------------------------------------------------
def get_user_profile(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT user_id, username, level, xp, progress, quizzes_completed, coins
    FROM users WHERE user_id=?
    """, (user_id,))

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "level": row[2],
        "xp": row[3],
        "progress": row[4],
        "quizzes_completed": row[5],
        "coins": row[6]
    }


# -----------------------------------------------------
# 🔥 إضافة عملات
# -----------------------------------------------------
def add_coins(user_id: int, amount: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET coins = coins + ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()


# -----------------------------------------------------
# 🔥 تحديث التقدم + XP
# -----------------------------------------------------
def update_user_progress(user_id, new_progress):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    UPDATE users
    SET progress = ?, xp = xp + 10
    WHERE user_id = ?
    """, (new_progress, user_id))

    conn.commit()
    conn.close()


# -----------------------------------------------------
# 🔥 تسجيل كويز مكتمل
# -----------------------------------------------------
def update_quiz_progress(user_id, new_quiz_count):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    UPDATE users
    SET quizzes_completed = ?, xp = xp + 20
    WHERE user_id = ?
    """, (new_quiz_count, user_id))

    conn.commit()
    conn.close()


# -----------------------------------------------------
# 🔥 تحديث نتيجة اختبار تحديد المستوى
# -----------------------------------------------------
def update_user_test_result(user_id, new_level, xp_gain=50):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    UPDATE users
    SET level = ?, xp = xp + ?, progress = 0, quizzes_completed = 0
    WHERE user_id = ?
    """, (new_level, xp_gain, user_id))

    conn.commit()
    conn.close()


# -----------------------------------------------------
# 🔥 إضافة منتج للمتجر
# -----------------------------------------------------
def add_store_item(name, desc, price, ai_link):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO store_items (name, description, price, ai_bot_link)
    VALUES (?, ?, ?, ?)
    """, (name, desc, price, ai_link))

    conn.commit()
    conn.close()


# -----------------------------------------------------
# 🔥 جلب منتجات المتجر
# -----------------------------------------------------
def get_store_items():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT id, name, description, price FROM store_items")
    rows = c.fetchall()

    conn.close()
    return rows


# -----------------------------------------------------
# 🔥 شراء منتج
# -----------------------------------------------------
def purchase_item(user_id, item_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO purchases (user_id, item_id)
    VALUES (?, ?)
    """, (user_id, item_id))

    conn.commit()
    conn.close()


# -----------------------------------------------------
# 🔥 جلب رابط بوت AI
# -----------------------------------------------------
def get_item_link(item_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT ai_bot_link FROM store_items WHERE id=?", (item_id,))
    row = c.fetchone()

    conn.close()
    return row[0] if row else None


# -----------------------------------------------------
# 🔥 جلب Top 10
# -----------------------------------------------------
def get_top10():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT username, xp
    FROM users
    ORDER BY xp DESC
    LIMIT 10
    """)

    top = c.fetchall()
    conn.close()
    return top


# -----------------------------------------------------
# 🔥 جلب رتبة المستخدم
# -----------------------------------------------------
def get_user_rank(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT xp FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return None

    user_xp = row[0]

    c.execute("SELECT COUNT(*) FROM users WHERE xp > ?", (user_xp,))
    higher = c.fetchone()[0]

    conn.close()
    return higher + 1
    
    
def add_xp(user_id: int, amount: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        UPDATE users
        SET xp = xp + ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()
    
def save_quiz_result(user_id, correct, total):
    score = int((correct / total) * 100)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1) حفظ نتيجة الكويز في جدول quiz_results
    c.execute("""
        INSERT INTO quiz_results (user_id, correct_answers, total_questions, score)
        VALUES (?, ?, ?, ?)
    """, (user_id, correct, total, score))

    # 2) زيادة عدد الكويزات المكتملة + XP
    c.execute("""
        UPDATE users
        SET quizzes_completed = quizzes_completed + 1,
            xp = xp + 20,
            coins = coins + 5
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    return score
