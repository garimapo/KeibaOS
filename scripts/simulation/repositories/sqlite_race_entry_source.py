"""SQLite-backed race-entry lookup for one requested prediction-horse selection."""

from __future__ import annotations

import sqlite3
from typing import Mapping, Sequence

from scripts.simulation.race_entry_source import RaceEntrySource

from .errors import RepositoryDataIntegrityError, RepositoryValidationError


class SQLiteRaceEntrySource:
    """Resolve requested horse IDs to race-entry IDs from an injected SQLite connection."""

    __slots__ = ("_connection",)

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise RepositoryValidationError("connection must be sqlite3.Connection")
        self._connection = connection
        self._ensure_foreign_keys()

    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        requested_horse_ids = self._validate_request(race_id=race_id, horse_ids=horse_ids)
        placeholders = ", ".join("?" for _ in requested_horse_ids)
        query = f"""
            SELECT h.id AS prediction_horse_id, h.id AS race_entry_id
            FROM horses AS h
            WHERE h.race_id = ?
              AND h.id IN ({placeholders})
        """
        try:
            rows = self._connection.execute(query, (race_id, *requested_horse_ids)).fetchall()
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc).lower() or "no such column" in str(exc).lower():
                raise RepositoryDataIntegrityError("horses schema is unavailable") from exc
            raise

        resolved: dict[int, int] = {}
        resolved_entry_ids: set[int] = set()
        requested_set = set(requested_horse_ids)
        for row in rows:
            try:
                prediction_horse_id, race_entry_id = row
            except (TypeError, ValueError) as exc:
                raise RepositoryDataIntegrityError("horses query returned an invalid row") from exc
            if (
                not self._is_positive_int(prediction_horse_id)
                or not self._is_positive_int(race_entry_id)
                or prediction_horse_id not in requested_set
                or prediction_horse_id in resolved
                or race_entry_id in resolved_entry_ids
            ):
                raise RepositoryDataIntegrityError("horses query returned contradictory row data")
            resolved[prediction_horse_id] = race_entry_id
            resolved_entry_ids.add(race_entry_id)

        return {
            horse_id: resolved[horse_id]
            for horse_id in requested_horse_ids
            if horse_id in resolved
        }

    def _ensure_foreign_keys(self) -> None:
        try:
            self._connection.execute("PRAGMA foreign_keys=ON")
            enabled = self._connection.execute("PRAGMA foreign_keys").fetchone()
        except sqlite3.Error as exc:
            raise RepositoryValidationError("connection is not usable") from exc
        if enabled is None or enabled[0] != 1:
            raise RepositoryValidationError("foreign_keys could not be enabled")

    @classmethod
    def _validate_request(cls, *, race_id: object, horse_ids: object) -> tuple[int, ...]:
        if not cls._is_positive_int(race_id):
            raise RepositoryValidationError("race_id must be a positive int")
        if (
            isinstance(horse_ids, (str, bytes, bytearray, Mapping))
            or not isinstance(horse_ids, Sequence)
        ):
            raise RepositoryValidationError("horse_ids must be a non-empty Sequence of positive ints")
        requested_horse_ids = tuple(horse_ids)
        if not requested_horse_ids:
            raise RepositoryValidationError("horse_ids must not be empty")
        if not all(cls._is_positive_int(horse_id) for horse_id in requested_horse_ids):
            raise RepositoryValidationError("horse_ids must contain only positive ints")
        if len(set(requested_horse_ids)) != len(requested_horse_ids):
            raise RepositoryValidationError("horse_ids must not contain duplicates")
        return requested_horse_ids

    @staticmethod
    def _is_positive_int(value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value > 0
