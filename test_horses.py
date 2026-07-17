import os
import sqlite3

print(os.path.abspath("database/keiba.db"))

conn = sqlite3.connect("database/keiba.db")
cursor = conn.cursor()
conn = sqlite3.connect("database/keiba.db")
cursor = conn.cursor()

cursor.execute("""
SELECT COUNT(*)
FROM horses
""")

print(cursor.fetchone())

cursor.execute("""
SELECT
    race_id,
    horse_no,
    horse_name
FROM horses
LIMIT 20
""")

for row in cursor.fetchall():
    print(row)

conn.close()