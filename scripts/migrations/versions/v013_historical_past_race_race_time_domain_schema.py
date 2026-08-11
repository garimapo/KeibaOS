"""Remove the obsolete historical past-race comparison column from empty stores."""

from __future__ import annotations

import sqlite3


VERSION = 13
NAME = "v013_historical_past_race_race_time_domain_schema"


def apply(connection: sqlite3.Connection) -> None:
    snapshot_count = connection.execute(
        "SELECT COUNT(*) FROM historical_input_snapshots"
    ).fetchone()[0]
    if snapshot_count != 0:
        raise RuntimeError(
            "cannot migrate nonempty historical input snapshot store to race-time-only semantics"
        )
    connection.execute(
        "ALTER TABLE historical_input_snapshot_past_races "
        "DROP COLUMN reference_time_difference_seconds_text"
    )
