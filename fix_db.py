import sqlite3

# DIQQAT: Bazangiz fayl nomini aniq yozing! 
# Odatda config.py yoki .env da yozilgan bo'ladi (masalan: "test.db", "app.db")
DB_NAME = "enwis.db"  # <-- SHUNI O'ZGARTIRING

try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Yangi ustun qo'shish buyrug'i
    cursor.execute("ALTER TABLE reading_results ADD COLUMN standard_score FLOAT")
    
    conn.commit()
    print("✅ Muvaffaqiyatli! 'standard_score' ustuni qo'shildi.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Xatolik yoki ustun allaqachon mavjud: {e}")
finally:
    conn.close() # type: ignore