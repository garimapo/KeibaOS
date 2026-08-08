"""Rename the empty-store historical past-race time-difference column."""

from __future__ import annotations

import sqlite3


VERSION = 11
NAME = "v011_historical_past_race_time_difference_schema"


def apply(connection: sqlite3.Connection) -> None:
    snapshot_count = connection.execute(
        "SELECT COUNT(*) FROM historical_input_snapshots"
    ).fetchone()[0]
    if snapshot_count != 0:
        raise RuntimeError(
            "cannot migrate nonempty historical input snapshot store to time-difference semantics"
        )
    connection.execute(
        "ALTER TABLE historical_input_snapshot_past_races "
        "RENAME COLUMN margin_text TO reference_time_difference_seconds_text"
    )
