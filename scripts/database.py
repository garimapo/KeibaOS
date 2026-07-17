"""
KeibaOS Database Module

SQLiteへの接続および
レース・馬情報の保存・取得を管理する。
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from scripts.models import Horse, PastRace, Race


DB_PATH = "database/keiba.db"


# ==========================================================
# Connection
# ==========================================================

def get_connection() -> sqlite3.Connection:
    """
    SQLiteデータベースへ接続する。
    """

    return sqlite3.connect(DB_PATH)


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    """トランザクション完了後に必ずSQLite接続を閉じる。"""

    conn = get_connection()

    try:

        yield conn
        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==========================================================
# Table Create
# ==========================================================

def create_tables() -> None:
    """
    SQLiteテーブル作成。
    """

    with _connection() as conn:

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

                horse_detail_url TEXT,

                jockey TEXT,
                trainer TEXT,

                odds REAL,
                popularity INTEGER,

                weight REAL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS past_races (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                horse_id INTEGER,

                race_date TEXT,
                place TEXT,

                race_name TEXT,
                race_class TEXT,

                distance INTEGER,
                track TEXT,

                weather TEXT,
                track_condition TEXT,

                finish INTEGER,
                margin REAL,
                time TEXT,

                weight REAL,
                weight_diff REAL,

                jockey TEXT,

                popularity INTEGER,
                odds REAL
            )
            """
        )

        _migrate_race_table(cursor)
        _migrate_horse_table(cursor)
        _migrate_past_races_table(cursor)

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_horses_race_id
            ON horses (race_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_past_races_horse_date
            ON past_races (horse_id, race_date DESC)
            """
        )


def _migrate_race_table(
    cursor: sqlite3.Cursor,
) -> None:
    """
    racesテーブルのマイグレーション。
    """

    _add_missing_columns(
        cursor,
        "races",
        {

            "start_time": "TEXT",

            "track_condition": "TEXT",

            "horse_count": "INTEGER",

            "deba_table_url": "TEXT",
        },
    )


def _migrate_horse_table(
    cursor: sqlite3.Cursor,
) -> None:
    """horses テーブルを現在のスキーマへ移行する。"""

    _add_missing_columns(
        cursor,
        "horses",
        {
            "horse_detail_url": "TEXT",
        },
    )


def _migrate_past_races_table(
    cursor: sqlite3.Cursor,
) -> None:
    """past_races テーブルを現在のスキーマへ移行する。"""

    _add_missing_columns(
        cursor,
        "past_races",
        {
            "horse_id": "INTEGER",
            "race_date": "TEXT",
            "place": "TEXT",
            "race_name": "TEXT",
            "race_class": "TEXT",
            "distance": "INTEGER",
            "track": "TEXT",
            "weather": "TEXT",
            "track_condition": "TEXT",
            "finish": "INTEGER",
            "margin": "REAL",
            "time": "TEXT",
            "weight": "REAL",
            "weight_diff": "REAL",
            "jockey": "TEXT",
            "popularity": "INTEGER",
            "odds": "REAL",
        },
    )


def _add_missing_columns(
    cursor: sqlite3.Cursor,
    table_name: str,
    required_columns: dict[str, str],
) -> None:
    """SQLite テーブルに不足している列を追加する。"""

    allowed_tables = {"races", "horses", "past_races"}
    allowed_types = {"INTEGER", "REAL", "TEXT"}

    if table_name not in allowed_tables:

        raise ValueError(f"Unsupported migration table: {table_name}")

    if not set(required_columns.values()).issubset(allowed_types):

        raise ValueError("Unsupported migration column type")

    cursor.execute(f"PRAGMA table_info({table_name})")

    columns = {
        row[1]
        for row in cursor.fetchall()
    }

    for name, dtype in required_columns.items():

        if name not in columns:

            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {name} {dtype}"
            )


# ==========================================================
# Exists
# ==========================================================

def race_exists(
    race: Race,
) -> bool:
    """
    同一レース存在確認。
    """

    with _connection() as conn:

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


# ==========================================================
# Save
# ==========================================================

def save_race(
    race: Race,
) -> int | None:
    """
    レース情報保存。

    Returns:
        race_id: 保存成功
        None: 重複または保存失敗
    """

    try:

        if race_exists(race):

            return None

        with _connection() as conn:

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

                    ?, ?, ?,
                    ?, ?,

                    ?,

                    ?, ?,

                    ?, ?,

                    ?,

                    ?,

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

            return int(race_id)

    except sqlite3.Error as e:

        print(f"[DB ERROR] {e}")

        return None# ==========================================================
# Horse
# ==========================================================

def horse_exists(
    horse: Horse,
) -> bool:
    """
    同一馬情報存在確認。
    """

    with _connection() as conn:

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

    Returns:
        True : 保存成功
        False: 重複または保存失敗
    """

    try:

        if horse_exists(horse):

            return False

        with _connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO horses (

                    race_id,

                    frame_no,
                    horse_no,

                    horse_name,

                    horse_detail_url,

                    jockey,
                    trainer,

                    odds,
                    popularity,

                    weight

                )

                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    horse.race_id,

                    horse.frame_no,
                    horse.horse_no,

                    horse.horse_name,

                    horse.horse_detail_url,

                    horse.jockey,
                    horse.trainer,

                    horse.odds,
                    horse.popularity,

                    horse.weight,
                ),
            )

            return True

    except sqlite3.Error as e:

        print(f"[DB ERROR] {e}")

        return False


def past_race_exists(
    past_race: PastRace,
) -> bool:
    """同じ馬の同一過去走がすでに保存されているか確認する。"""

    with _connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM past_races
            WHERE horse_id = ?
              AND race_date = ?
              AND place = ?
              AND race_name = ?
            LIMIT 1
            """,
            (
                past_race.horse_id,
                past_race.race_date,
                past_race.place,
                past_race.race_name,
            ),
        )

        return cursor.fetchone() is not None


def get_horse_id(
    horse: Horse,
) -> int | None:
    """出走馬情報に対応する horses.id を取得する。"""

    with _connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
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

        result = cursor.fetchone()

        if result is None:

            return None

        return int(result[0])


def save_past_race(
    past_race: PastRace,
) -> bool:
    """過去走情報を保存する。重複する過去走は保存しない。"""

    try:

        if past_race_exists(past_race):

            return False

        with _connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO past_races (
                    horse_id,
                    race_date, place,
                    race_name, race_class,
                    distance, track,
                    weather, track_condition,
                    finish, margin, time,
                    weight, weight_diff,
                    jockey,
                    popularity, odds
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    past_race.horse_id,
                    past_race.race_date,
                    past_race.place,
                    past_race.race_name,
                    past_race.race_class,
                    past_race.distance,
                    past_race.track,
                    past_race.weather,
                    past_race.track_condition,
                    past_race.finish,
                    past_race.margin,
                    past_race.time,
                    past_race.weight,
                    past_race.weight_diff,
                    past_race.jockey,
                    past_race.popularity,
                    past_race.odds,
                ),
            )

            return True

    except sqlite3.Error as e:

        print(f"[DB ERROR] {e}")

        return False


# ==========================================================
# Get
# ==========================================================

def get_race_id(
    race: Race,
) -> int | None:
    """
    レースID取得。

    Returns:
        race_id: 存在する場合
        None   : 存在しない場合
    """

    with _connection() as conn:

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

        return int(result[0])


def get_all_races() -> list[tuple[int, Race]]:
    """
    登録済みレース一覧を取得する。

    Returns:
        [
            (race_id, Race),
            ...
        ]
    """

    with _connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT

                id,

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

                deba_table_url

            FROM races

            ORDER BY

                race_date,
                place,
                race_no
            """
        )

        rows = cursor.fetchall()

        races: list[tuple[int, Race]] = []

        for row in rows:

            race = Race(

                race_date=row[1],
                organization=row[2],
                place=row[3],

                race_no=row[4],
                race_name=row[5],

                start_time=row[6],

                distance=row[7],
                track=row[8],

                weather=row[9],
                track_condition=row[10],

                horse_count=row[11],

                deba_table_url=row[12],
            )

            races.append(
                (
                    row[0],
                    race,
                )
            )

        return races


def get_horses_by_race(
    race_id: int,
) -> list[Horse]:
    """
    指定レースの出走馬一覧を取得する。
    """

    with _connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT

                race_id,

                frame_no,
                horse_no,

                horse_name,

                horse_detail_url,

                jockey,
                trainer,

                odds,
                popularity,

                weight

            FROM horses

            WHERE race_id = ?

            ORDER BY horse_no
            """,
            (
                race_id,
            ),
        )

        rows = cursor.fetchall()

        horses: list[Horse] = []

        for row in rows:

            horses.append(
                Horse(

                    race_id=row[0],

                    frame_no=row[1],
                    horse_no=row[2],

                    horse_name=row[3],

                    horse_detail_url=row[4] or "",

                    jockey=row[5],
                    trainer=row[6],

                    odds=row[7],
                    popularity=row[8],

                    weight=row[9],
                )
            )

        return horses


def get_past_races(
    horse_id: int,
) -> list[PastRace]:
    """指定した馬の過去走を新しいレース順に取得する。"""

    with _connection() as conn:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                horse_id,
                race_date, place,
                race_name, race_class,
                distance, track,
                weather, track_condition,
                finish, margin, time,
                weight, weight_diff,
                jockey,
                popularity, odds
            FROM past_races
            WHERE horse_id = ?
            ORDER BY race_date DESC, rowid DESC
            """,
            (horse_id,),
        )

        return [
            PastRace(
                horse_id=row[0],
                race_date=row[1],
                place=row[2],
                race_name=row[3],
                race_class=row[4],
                distance=row[5],
                track=row[6],
                weather=row[7],
                track_condition=row[8],
                finish=row[9],
                margin=row[10],
                time=row[11],
                weight=row[12],
                weight_diff=row[13],
                jockey=row[14],
                popularity=row[15],
                odds=row[16],
            )
            for row in cursor.fetchall()
        ]
