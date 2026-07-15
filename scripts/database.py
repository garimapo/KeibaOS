import sqlite3

from scripts.models import Race

DB_PATH = "database/keiba.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS races (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        race_date TEXT,
        organization TEXT,
        place TEXT,
        race_no INTEGER,
        race_name TEXT,
        distance INTEGER,
        track TEXT,
        weather TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_race(race: Race):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO races (
        race_date,
        organization,
        place,
        race_no,
        race_name,
        distance,
        track,
        weather,
        status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        race.race_date,
        race.organization,
        race.place,
        race.race_no,
        race.race_name,
        race.distance,
        race.track,
        race.weather,
        "scheduled"
    ))

    conn.commit()
    conn.close()