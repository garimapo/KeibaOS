"""
KeibaOS Database Module

SQLiteへの接続およびレース情報の保存を管理する。
"""

import sqlite3

from scripts.models import Race


DB_PATH = "database/keiba.db"


def get_connection() -> sqlite3.Connection:
    """
    SQLiteデータベースへ接続する。
    """

    return sqlite3.connect(DB_PATH)


def create_tables() -> None:
    """
    SQLiteテーブル作成。

    Ver0.7:
    Race情報拡張対応
    """

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS races (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                race_date TEXT,
                organization TEXT,
                place TEXT,

                race_no INTEGER,
                race_name TEXT,

                start_time TEXT,

                distance INTEGER,
                track TEXT,

                weather TEXT,
                track_condition TEXT,

                horse_count INTEGER,

                deba_table_url TEXT,

                status TEXT
            )
            """
        )

        conn.commit()

        _migrate_race_table(cursor)

        conn.commit()


def _migrate_race_table(
    cursor: sqlite3.Cursor,
) -> None:
    """
    既存DBへ不足カラムを追加する。

    Ver0.6 → Ver0.7移行用
    """

    cursor.execute(
        "PRAGMA table_info(races)"
    )

    columns = {
        row[1]
        for row in cursor.fetchall()
    }

    required_columns = {
        "start_time": "TEXT",
        "track_condition": "TEXT",
        "horse_count": "INTEGER",
        "deba_table_url": "TEXT",
    }

    for name, dtype in required_columns.items():

        if name not in columns:

            cursor.execute(
                f"""
                ALTER TABLE races
                ADD COLUMN {name} {dtype}
                """
            )


def race_exists(
    race: Race,
) -> bool:
    """
    同一レース存在確認。
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


def save_race(
    race: Race,
) -> bool:
    """
    レース情報保存。
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

                    start_time,

                    distance,
                    track,

                    weather,
                    track_condition,

                    horse_count,

                    deba_table_url,

                    status
                )

                VALUES (
                    ?,?,?,?,?,?,
                    ?,?,?,?,?,?,
                    ?
                )
                """,
                (
                    race.race_date,
                    race.organization,
                    race.place,

                    race.race_no,
                    race.race_name,

                    race.start_time,

                    race.distance,
                    race.track,

                    race.weather,
                    race.track_condition,

                    race.horse_count,

                    race.deba_table_url,

                    "scheduled",
                ),
            )

            conn.commit()

        return True

    except sqlite3.Error as e:

        print(
            f"[DB ERROR] {e}"
        )

        return False