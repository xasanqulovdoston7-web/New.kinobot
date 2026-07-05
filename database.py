import sqlite3
from datetime import datetime

DB_FILE = "kino_bot.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Foydalanuvchilar jadvali
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id   INTEGER UNIQUE NOT NULL,
            username      TEXT,
            full_name     TEXT,
            joined_at     TEXT DEFAULT (strftime('%Y-%m', 'now')),
            joined_full   TEXT DEFAULT (datetime('now')),
            is_active     INTEGER DEFAULT 1
        )
    """)

    # Kinolar jadvali (type qo'shildi: tekin yoki pullik)
    c.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT UNIQUE NOT NULL,
            title       TEXT NOT NULL,
            file_id     TEXT NOT NULL,
            movie_type  TEXT NOT NULL DEFAULT 'tekin',
            added_at    TEXT DEFAULT (datetime('now'))
        )
    """)

    # Kanallar jadvali (platforma va obunachilar soni qo'shildi)
    c.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id  TEXT UNIQUE NOT NULL,
            title       TEXT NOT NULL,
            link        TEXT NOT NULL,
            platform    TEXT NOT NULL DEFAULT 'telegram',
            sub_count   INTEGER DEFAULT 0,
            is_active   INTEGER DEFAULT 1
        )
    """)

    # Oylik statistika
    c.execute("""
        CREATE TABLE IF NOT EXISTS left_users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            left_at     TEXT DEFAULT (strftime('%Y-%m', 'now'))
        )
    """)

    # Baholar
    c.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            rating      INTEGER NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()

# ── FOYDALANUVCHILAR ─────────────────────────────────────
def add_user(telegram_id, username=None, full_name=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO users (telegram_id, username, full_name)
        VALUES (?, ?, ?)
    """, (telegram_id, username, full_name))
    c.execute("UPDATE users SET is_active=1 WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()

def mark_user_left(telegram_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET is_active=0 WHERE telegram_id=?", (telegram_id,))
    c.execute("INSERT INTO left_users (telegram_id) VALUES (?)", (telegram_id,))
    conn.commit()
    conn.close()

def get_all_user_ids():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users WHERE is_active=1")
    rows = c.fetchall()
    conn.close()
    return [r["telegram_id"] for r in rows]

def get_total_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM users WHERE is_active=1")
    count = c.fetchone()["cnt"]
    conn.close()
    return count

def get_monthly_stats():
    conn = get_conn()
    c = conn.cursor()
    month = datetime.now().strftime("%Y-%m")
    c.execute("SELECT COUNT(*) as cnt FROM users WHERE joined_at=?", (month,))
    joined = c.fetchone()["cnt"]
    c.execute("SELECT COUNT(*) as cnt FROM left_users WHERE left_at=?", (month,))
    left = c.fetchone()["cnt"]
    conn.close()
    return {"joined": joined, "left": left, "month": month}

def add_rating(telegram_id, rating):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO ratings (telegram_id, rating) VALUES (?, ?)", (telegram_id, rating))
    conn.commit()
    conn.close()

def get_monthly_rating():
    conn = get_conn()
    c = conn.cursor()
    month = datetime.now().strftime("%Y-%m")
    c.execute("""
        SELECT COUNT(*) as cnt, AVG(rating) as avg
        FROM ratings
        WHERE strftime('%Y-%m', created_at) = ?
    """, (month,))
    row = c.fetchone()
    conn.close()
    count = row["cnt"] or 0
    avg = round(row["avg"], 2) if row["avg"] else 0
    return {"count": count, "avg": avg}

# ── KINOLAR ──────────────────────────────────────────────
def add_movie(code, title, file_id, movie_type):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO movies (code, title, file_id, movie_type)
            VALUES (?, ?, ?, ?)
        """, (code.upper(), title, file_id, movie_type))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_movie_by_code(code):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM movies WHERE code=?", (code.upper(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_movie(code):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM movies WHERE code=?", (code.upper(),))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_all_movies():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM movies ORDER BY added_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── KANALLAR ─────────────────────────────────────────────
def add_channel(channel_id, title, link, platform, sub_count=0):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO channels (channel_id, title, link, platform, sub_count)
            VALUES (?, ?, ?, ?, ?)
        """, (channel_id, title, link, platform, sub_count))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_channel(channel_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM channels WHERE channel_id=?", (channel_id,))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_active_channels():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM channels WHERE is_active=1")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_channels_by_platform(platform):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM channels WHERE platform=?", (platform,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
# ── BAZANI MAJBURIY YANGILASH SKRIPTI (database.py OXIRIGA QO'YING) ──

def auto_upgrade_database():
    import sqlite3
    conn = sqlite3.connect("kino_bot.db")
    c = conn.cursor()
    
    # channels jadvaliga platform ustunini majburiy tekshirish va qo'shish
    try:
        c.execute("ALTER TABLE channels ADD COLUMN platform TEXT NOT NULL DEFAULT 'telegram'")
    except sqlite3.OperationalError:
        pass  # Agar ustun allaqachon bo'lsa xatoni o'tkazib yuboradi

    # channels jadvaliga sub_count ustunini majburiy tekshirish va qo'shish
    try:
        c.execute("ALTER TABLE channels ADD COLUMN sub_count INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Agar ustun allaqachon bo'lsa xatoni o'tkazib yuboradi
        
    conn.commit()
    conn.close()

# Bot har safar yonganda ushbu tekshiruv avtomatik ishlaydi
auto_upgrade_database()