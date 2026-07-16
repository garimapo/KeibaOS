"""
KeibaOS Database Module

SQLiteへの接続および
レース・馬情報の保存を管理する。
"""

import sqlite3

from scripts.models import Race, Horse


DB_PATH = "database/keiba.db"


def get_connection() -> sqlite3.Connection:
    """
    SQLiteデータベースへ接続する。
    """

    return sqlite3.connect(DB_PATH)


def create_tables() -> None:
    """
    SQLiteテーブル作成。
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


        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS horses (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                race_id INTEGER,

                frame_no INTEGER,
                horse_no INTEGER,

                horse_name TEXT,

                jockey TEXT,
                trainer TEXT,

                odds REAL,
                popularity INTEGER,

                weight REAL
            )
            """
        )


        conn.commit()

        _migrate_race_table(
            cursor
        )

        conn.commit()



def _migrate_race_table(
    cursor: sqlite3.Cursor,
) -> None:
    """
    既存racesテーブル移行処理。
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



def get_race_id(
    race: Race,
) -> int | None:
    """
    レースID取得。

    既存Raceの場合:
        race_idを返す

    存在しない場合:
        None
    """

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
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

        result = cursor.fetchone()


        if result is None:

            return None


        return int(
            result[0]
        )


def save_race(
    race: Race,
) -> int | None:
    """
    レース情報保存。

    保存成功:
        race_idを返す

    重複:
        None
    """

    if race_exists(race):

        return None


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


            race_id = cursor.lastrowid


            conn.commit()


        return race_id


    except sqlite3.Error as e:

        print(
            f"[DB ERROR] {e}"
        )

        return None



def horse_exists(
    horse: Horse,
) -> bool:
    """
    同一馬情報存在確認。
    """

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM horses
            WHERE race_id = ?
              AND horse_no = ?
            LIMIT 1
            """,
            (
                horse.race_id,
                horse.horse_no,
            ),
        )

        return cursor.fetchone() is not None



def save_horse(
    horse: Horse,
) -> bool:
    """
    馬情報保存。
    """

    if horse_exists(horse):

        return False


    try:

        with get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO horses (

                    race_id,

                    frame_no,
                    horse_no,

                    horse_name,

                    jockey,
                    trainer,

                    odds,
                    popularity,

                    weight
                )

                VALUES (
                    ?,?,?,?,?,?,?,?,?
                )
                """,
                (
                    horse.race_id,

                    horse.frame_no,
                    horse.horse_no,

                    horse.horse_name,

                    horse.jockey,
                    horse.trainer,

                    horse.odds,
                    horse.popularity,

                    horse.weight,
                ),
            )

            conn.commit()


        return True


    except sqlite3.Error as e:

        print(
            f"[DB ERROR] {e}"
        )

        return False