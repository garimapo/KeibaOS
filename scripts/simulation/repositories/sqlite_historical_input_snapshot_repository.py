"""Atomic SQLite persistence for immutable historical input snapshots."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
import sqlite3

from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot

from .errors import RepositoryConflictError, RepositoryDataIntegrityError, RepositoryValidationError


class SQLiteHistoricalInputSnapshotRepository:
    """Persist one complete V3a snapshot through the committed v010 schema."""

    __slots__ = ("_connection",)

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise RepositoryValidationError("connection must be sqlite3.Connection")
        self._connection = connection
        self._ensure_foreign_keys()

    def save_snapshot(self, *, snapshot: HistoricalInputSnapshot) -> None:
        if type(snapshot) is not HistoricalInputSnapshot:
            raise RepositoryValidationError("snapshot must be HistoricalInputSnapshot")
        if self._connection.in_transaction:
            raise RepositoryValidationError("repository writes require no active transaction")

        self._ensure_foreign_keys()
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            existing = self._find_existing_header(snapshot)
            if existing is not None:
                _snapshot_id, content_sha256 = existing
                if content_sha256 == snapshot.content_sha256:
                    self._connection.commit()
                    return
                raise RepositoryConflictError("historical input snapshot differs from existing snapshot")

            self._ensure_mappings(snapshot)
            snapshot_id = self._insert_header(snapshot)
            self._insert_race(snapshot_id, snapshot)
            self._insert_entries(snapshot_id, snapshot)
            self._insert_past_races(snapshot_id, snapshot)
            self._insert_provenance(snapshot_id, snapshot)
            self._connection.commit()
        except RepositoryConflictError:
            self._connection.rollback()
            raise
        except RepositoryDataIntegrityError:
            self._connection.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            self._connection.rollback()
            raise RepositoryDataIntegrityError("SQLite integrity constraint failed") from exc
        except Exception:
            self._connection.rollback()
            raise

    def _ensure_foreign_keys(self) -> None:
        try:
            self._connection.execute("PRAGMA foreign_keys=ON")
            enabled = self._connection.execute("PRAGMA foreign_keys").fetchone()
        except sqlite3.Error as exc:
            raise RepositoryValidationError("connection is not usable") from exc
        if enabled is None or enabled[0] != 1:
            raise RepositoryValidationError("foreign_keys could not be enabled")

    def _find_existing_header(self, snapshot: HistoricalInputSnapshot) -> tuple[int, str] | None:
        source = snapshot.identity.source_identity
        rows = self._connection.execute(
            """SELECT snapshot_id, content_sha256
               FROM historical_input_snapshots
               WHERE dataset_id=? AND organization=? AND source_system=?
                 AND external_race_id=? AND captured_at_utc=?""",
            (
                snapshot.identity.dataset_id,
                source.organization,
                source.source_system,
                source.external_race_id,
                self._datetime_text(snapshot.identity.captured_at),
            ),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise RepositoryDataIntegrityError("multiple historical snapshot headers match one identity")
        snapshot_id, content_sha256 = rows[0]
        if type(snapshot_id) is not int or type(content_sha256) is not str:
            raise RepositoryDataIntegrityError("historical snapshot header is malformed")
        return snapshot_id, content_sha256

    def _ensure_mappings(self, snapshot: HistoricalInputSnapshot) -> None:
        source = snapshot.identity.source_identity
        self._ensure_source_identity(source.organization, source.source_system)
        self._ensure_external_race(
            organization=source.organization,
            source_system=source.source_system,
            external_race_id=source.external_race_id,
            internal_race_id=snapshot.internal_race_id,
        )
        for entry in snapshot.entries:
            external = entry.external_entry_identity
            race_identity = external.external_race_identity
            self._ensure_external_entry(
                organization=race_identity.organization,
                source_system=race_identity.source_system,
                external_race_id=race_identity.external_race_id,
                external_entry_id=external.external_entry_id,
                internal_race_id=snapshot.internal_race_id,
                race_entry_id=entry.race_entry_id,
            )

    def _ensure_source_identity(self, organization: str, source_system: str) -> None:
        row = self._connection.execute(
            """SELECT 1 FROM historical_input_source_identities
               WHERE organization=? AND source_system=?""",
            (organization, source_system),
        ).fetchone()
        if row is None:
            self._connection.execute(
                "INSERT INTO historical_input_source_identities(organization,source_system) VALUES(?,?)",
                (organization, source_system),
            )

    def _ensure_external_race(
        self,
        *,
        organization: str,
        source_system: str,
        external_race_id: str,
        internal_race_id: int,
    ) -> None:
        forward = self._connection.execute(
            """SELECT internal_race_id FROM historical_input_external_races
               WHERE organization=? AND source_system=? AND external_race_id=?""",
            (organization, source_system, external_race_id),
        ).fetchall()
        if len(forward) > 1:
            raise RepositoryDataIntegrityError("multiple external-race mappings match one identity")
        if forward:
            if forward[0][0] != internal_race_id:
                raise RepositoryConflictError("external race maps to a different internal race")
            return

        reverse = self._connection.execute(
            """SELECT external_race_id FROM historical_input_external_races
               WHERE organization=? AND source_system=? AND internal_race_id=?""",
            (organization, source_system, internal_race_id),
        ).fetchall()
        if len(reverse) > 1:
            raise RepositoryDataIntegrityError("multiple external-race mappings match one internal race")
        if reverse:
            raise RepositoryConflictError("internal race maps to a different external race")
        self._connection.execute(
            """INSERT INTO historical_input_external_races
               (organization,source_system,external_race_id,internal_race_id) VALUES(?,?,?,?)""",
            (organization, source_system, external_race_id, internal_race_id),
        )

    def _ensure_external_entry(
        self,
        *,
        organization: str,
        source_system: str,
        external_race_id: str,
        external_entry_id: str,
        internal_race_id: int,
        race_entry_id: int,
    ) -> None:
        forward = self._connection.execute(
            """SELECT internal_race_id,race_entry_id FROM historical_input_external_entries
               WHERE organization=? AND source_system=? AND external_race_id=? AND external_entry_id=?""",
            (organization, source_system, external_race_id, external_entry_id),
        ).fetchall()
        if len(forward) > 1:
            raise RepositoryDataIntegrityError("multiple external-entry mappings match one identity")
        if forward:
            if tuple(forward[0]) != (internal_race_id, race_entry_id):
                raise RepositoryConflictError("external entry maps to a different internal entry")
            return

        reverse = self._connection.execute(
            """SELECT external_entry_id FROM historical_input_external_entries
               WHERE organization=? AND source_system=? AND internal_race_id=? AND race_entry_id=?""",
            (organization, source_system, internal_race_id, race_entry_id),
        ).fetchall()
        if len(reverse) > 1:
            raise RepositoryDataIntegrityError("multiple external-entry mappings match one internal entry")
        if reverse:
            raise RepositoryConflictError("internal entry maps to a different external entry")
        self._connection.execute(
            """INSERT INTO historical_input_external_entries
               (organization,source_system,external_race_id,external_entry_id,internal_race_id,race_entry_id)
               VALUES(?,?,?,?,?,?)""",
            (organization, source_system, external_race_id, external_entry_id, internal_race_id, race_entry_id),
        )

    def _insert_header(self, snapshot: HistoricalInputSnapshot) -> int:
        source = snapshot.identity.source_identity
        cursor = self._connection.execute(
            """INSERT INTO historical_input_snapshots(
                   dataset_id,organization,source_system,external_race_id,internal_race_id,source_url,
                   captured_at_utc,information_cutoff_utc,content_sha256
               ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                snapshot.identity.dataset_id,
                source.organization,
                source.source_system,
                source.external_race_id,
                snapshot.internal_race_id,
                source.source_url,
                self._datetime_text(snapshot.identity.captured_at),
                self._datetime_text(snapshot.information_cutoff),
                snapshot.content_sha256,
            ),
        )
        return int(cursor.lastrowid)

    def _insert_race(self, snapshot_id: int, snapshot: HistoricalInputSnapshot) -> None:
        race = snapshot.race
        self._connection.execute(
            """INSERT INTO historical_input_snapshot_races(
                   snapshot_id,target_race_date,scheduled_start_at_utc,place,distance_m,track,track_condition,
                   race_name,race_class,weather
               ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                snapshot_id,
                self._date_text(race.target_race_date),
                self._datetime_text(race.scheduled_start_at),
                race.place,
                race.distance_m,
                race.track,
                race.track_condition,
                race.race_name,
                race.race_class,
                race.weather,
            ),
        )

    def _insert_entries(self, snapshot_id: int, snapshot: HistoricalInputSnapshot) -> None:
        self._connection.executemany(
            """INSERT INTO historical_input_snapshot_entries(
                   snapshot_id,race_entry_id,external_entry_id,external_horse_id,horse_no,jockey,
                   win_odds_text,entry_order
               ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                (
                    snapshot_id,
                    entry.race_entry_id,
                    entry.external_entry_identity.external_entry_id,
                    entry.external_entry_identity.external_horse_id,
                    entry.horse_no,
                    entry.jockey,
                    self._decimal_text(entry.win_odds),
                    entry.entry_order,
                )
                for entry in snapshot.entries
            ),
        )

    def _insert_past_races(self, snapshot_id: int, snapshot: HistoricalInputSnapshot) -> None:
        self._connection.executemany(
            """INSERT INTO historical_input_snapshot_past_races(
                   snapshot_id,race_entry_id,past_race_index,race_date,place,race_name,race_class,distance_m,
                   track,weather,track_condition,finish,margin_text,race_time,weight_text,weight_diff_text,
                   jockey,popularity,odds_text,passing_order,fourth_corner_position
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                (
                    snapshot_id,
                    item.race_entry_id,
                    item.past_race_index,
                    self._date_text(item.race_date),
                    item.place,
                    item.race_name,
                    item.race_class,
                    item.distance_m,
                    item.track,
                    item.weather,
                    item.track_condition,
                    item.finish,
                    self._decimal_text(item.margin),
                    item.race_time,
                    self._decimal_text(item.weight),
                    self._decimal_text(item.weight_diff),
                    item.jockey,
                    item.popularity,
                    self._decimal_text(item.odds),
                    item.passing_order,
                    item.fourth_corner_position,
                )
                for item in snapshot.past_races
            ),
        )

    def _insert_provenance(self, snapshot_id: int, snapshot: HistoricalInputSnapshot) -> None:
        self._connection.executemany(
            """INSERT INTO historical_input_snapshot_provenance(
                   snapshot_id,input_type,audit_key,source,source_id,race_entry_id,
                   available_at_utc,observed_at_utc,past_race_index
               ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                (
                    snapshot_id,
                    item.input_type,
                    item.audit_key,
                    item.source,
                    item.source_id,
                    item.race_entry_id,
                    None if item.available_at is None else self._datetime_text(item.available_at),
                    None if item.observed_at is None else self._datetime_text(item.observed_at),
                    item.past_race_index,
                )
                for item in snapshot.provenance
            ),
        )

    @staticmethod
    def _datetime_text(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds")

    @staticmethod
    def _date_text(value: date) -> str:
        return value.isoformat()

    @staticmethod
    def _decimal_text(value: Decimal) -> str:
        return format(value, "f")
