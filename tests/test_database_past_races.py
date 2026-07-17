"""past_racesの通過順位列に関するDBテスト。"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from scripts import database
from scripts.models import PastRace


class PastRaceDatabaseTest(unittest.TestCase):
    """既存DBの移行と通過順位の保存・取得を検証する。"""

    def setUp(self) -> None:
        descriptor, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(descriptor)
        self.original_db_path = database.DB_PATH
        database.DB_PATH = self.db_path

        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute(
                """
                CREATE TABLE past_races (
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
            conn.execute(
                """
                INSERT INTO past_races (
                    horse_id, race_date, place, race_name, race_class,
                    distance, track, weather, track_condition,
                    finish, margin, time, weight, weight_diff,
                    jockey, popularity, odds
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    2, "2026-06-01", "Tokyo", "Legacy Race", "A1",
                    1600, "dirt", "sunny", "good",
                    2, 1.0, "1:37.0", 480.0, 0.0,
                    "Jockey", 2, 3.0,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def tearDown(self) -> None:
        database.DB_PATH = self.original_db_path
        os.unlink(self.db_path)

    def test_migrates_and_round_trips_passing_order(self) -> None:
        """旧past_racesへ列を追加し、通過順位を保存・取得できる。"""

        database.create_tables()

        conn = sqlite3.connect(self.db_path)

        try:
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(past_races)")
            }
        finally:
            conn.close()

        self.assertTrue(
            {"passing_order", "fourth_corner_position"}.issubset(columns)
        )
        self.assertEqual(
            database.get_past_races(2)[0].passing_order,
            "",
        )
        self.assertEqual(
            database.get_past_races(2)[0].fourth_corner_position,
            0,
        )

        past_race = PastRace(
            horse_id=1,
            race_date="2026-07-01",
            place="Tokyo",
            race_name="Test Race",
            race_class="A1",
            distance=1600,
            track="dirt",
            weather="sunny",
            track_condition="good",
            finish=1,
            margin=1.0,
            time="1:36.0",
            weight=480.0,
            weight_diff=0.0,
            jockey="Jockey",
            popularity=1,
            odds=2.0,
            passing_order="2-2-1-1",
            fourth_corner_position=1,
        )

        self.assertTrue(database.save_past_race(past_race))
        self.assertEqual(database.get_past_races(1), [past_race])


if __name__ == "__main__":
    unittest.main()
