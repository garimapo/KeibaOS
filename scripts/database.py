"""
KeibaOS Database Module

SQLiteへの接続およびレース情報の保存を管理する。
"""

import sqlite3
from typing import Optional

from scripts.models import Race

DB_PATH = "database/keiba.db"


def get_connection() -> sqlite3.Connection:
    """
    SQLiteデータベースへ接続する。

    Returns:
        sqlite3.Connection: SQLite接続オブジェクト
    """
    return sqlite3.connect(DB_PATH)


def create_tables() -> None:
    """
    racesテーブルを作成する。
    存在する場合は何もしない。
    """

    with get_connection() as conn:
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


def race_exists(race: Race) -> bool:
    """
    同じレースが既に登録されているか確認する。

    Args:
        race (Race): レース情報

    Returns:
        bool: 登録済みならTrue
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM races
            WHERE race_date = ?
              AND organization = ?
              AND place = ?
              AND race_no = ?
            LIMIT 1
            """,
            (
                race.race_date,
                race.organization,
                race.place,
                race.race_no,
            ),
        )

        return cursor.fetchone() is not None


def save_race(race: Race) -> bool:
    """
    レース情報を保存する。

    同一レースが既に存在する場合は保存しない。

    Args:
        race (Race): 保存するレース

    Returns:
        bool:
            True  -> 保存成功
            False -> 登録済みのため保存しなかった
    """

    if race_exists(race):
        return False

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
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
                """,
                (
                    race.race_date,
                    race.organization,
                    race.place,
                    race.race_no,
                    race.race_name,
                    race.distance,
                    race.track,
                    race.weather,
                    "scheduled",
                ),
            )

            conn.commit()

        return True

    except sqlite3.Error as e:
        print(f"[DB ERROR] {e}")
        return False