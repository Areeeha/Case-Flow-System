import sqlite3

conn = sqlite3.connect("D:/university/fyp/fyp_database.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("📋 Tables in DB:", cursor.fetchall())

cursor.execute("PRAGMA table_info(payments);")
print("🧾 payments schema:", cursor.fetchall())

conn.close()
