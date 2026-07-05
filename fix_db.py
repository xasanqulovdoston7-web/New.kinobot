import sqlite3

conn = sqlite3.connect("kino_bot.db")
c = conn.cursor()

try:
    # channels jadvaliga platform ustunini qo'shamiz
    c.execute("ALTER TABLE channels ADD COLUMN platform TEXT NOT NULL DEFAULT 'telegram'")
    print("✅ platform ustuni muvaffaqiyatli qo'shildi!")
except sqlite3.OperationalError:
    print("⚠️ platform ustuni allaqachon bor yoki boshqa xato.")

try:
    # channels jadvaliga sub_count ustunini qo'shamiz
    c.execute("ALTER TABLE channels ADD COLUMN sub_count INTEGER DEFAULT 0")
    print("✅ sub_count ustuni muvaffaqiyatli qo'shildi!")
except sqlite3.OperationalError:
    print("⚠️ sub_count ustuni allaqachon bor yoki boshqa xato.")

conn.commit()
conn.close()
print("🚀 Baza yangilandi. Endi botni bemalol ishga tushirishingiz mumkin!")