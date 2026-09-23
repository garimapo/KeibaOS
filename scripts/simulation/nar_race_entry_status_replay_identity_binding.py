"""Fail-closed, read-only identity binding for the one published NAR V3 fixture.

This module binds identities only. It neither interprets entry status nor constructs
historical snapshots, and deliberately has no network or database write authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import re
import sqlite3

from bs4 import BeautifulSoup

from scripts.simulation import nar_historical_input_source as _nar_identity
from scripts.simulation.nar_race_entry_status_raw_capture import NARRaceEntryStatusRaceIdentity
from scripts.simulation.nar_race_entry_status_source_profile_fixture_consumer import (
    NARRaceEntryStatusSourceProfileFixtureBundleV3,
)
from scripts.simulation.nar_race_entry_status_source_profile_publication_contract import SourceProfileManifestV3
from scripts.simulation.nar_race_entry_status_source_profile_publication_plan import (
    EXPECTED_DEBA_TABLE_PATH_V3,
    EXPECTED_MANIFEST_PATH_V3,
    EXPECTED_RACE_LIST_PATH_V3,
)


_TARGET = NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
_ORGANIZATION = "NAR"
_SOURCE_SYSTEM = "nar_official"
_EXTERNAL_RACE_ID = "nar:20250101:21:6"
_FROZEN_BYTES = (
    (313317, "6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727"),
    (66307, "1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1"),
    (4254, "3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d"),
)
_FIXTURE_SET_ID = "nar-race-entry-status-source-profile-fixture-set-v3:11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225"
_QUALIFICATION_ID = "nar-race-entry-status-source-profile-qualification-v3:a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff"
ERROR_CLASSIFICATIONS = frozenset({
    "UNSUPPORTED_BUNDLE", "SQLITE_CONNECTION_INVALID", "SQLITE_SCHEMA_INVALID",
    "EXTERNAL_RACE_IDENTITY_CONTRADICTION", "INTERNAL_RACE_MAPPING_MISSING",
    "INTERNAL_RACE_MAPPING_AMBIGUOUS", "INTERNAL_RACE_MAPPING_CONTRADICTION",
    "SOURCE_ENTRY_IDENTITY_INVALID", "ENTRY_MAPPING_MISSING", "ENTRY_MAPPING_AMBIGUOUS",
    "ENTRY_MAPPING_CONTRADICTION", "DATABASE_ENTRY_SET_CONTRADICTION",
    "DUPLICATE_RACE_ENTRY_ID", "INTERNAL_ENTRY_ROW_MISSING",
    "HORSE_NUMBER_CONTRADICTION", "CROSS_PROVIDER_IDENTITY_UNSUPPORTED",
})


class NARRaceEntryStatusReplayIdentityBindingError(Exception):
    """A stable, fail-closed binding failure."""

    def __init__(self, classification: str, message: str) -> None:
        if classification not in ERROR_CLASSIFICATIONS:
            raise ValueError("unknown binding error classification")
        self.classification = classification
        super().__init__(f"{classification}: {message}")


def _failure(classification: str, message: str) -> NARRaceEntryStatusReplayIdentityBindingError:
    return NARRaceEntryStatusReplayIdentityBindingError(classification, message)


@dataclass(frozen=True, slots=True)
class _SourceEntryIdentity:
    external_entry_id: str
    external_horse_id: str
    horse_no: int


@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusReplayEntryIdentityBinding:
    external_entry_id: str
    external_horse_id: str
    horse_no: int
    race_entry_id: int


@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusReplayIdentityBinding:
    target: NARRaceEntryStatusRaceIdentity
    organization: str
    source_system: str
    external_race_id: str
    internal_race_id: int
    entry_bindings: tuple[NARRaceEntryStatusReplayEntryIdentityBinding, ...]


def _validate_bundle(bundle: object) -> NARRaceEntryStatusSourceProfileFixtureBundleV3:
    if type(bundle) is not NARRaceEntryStatusSourceProfileFixtureBundleV3:
        raise _failure("UNSUPPORTED_BUNDLE", "bundle type is not the published V3 type")
    try:
        if type(bundle.target) is not NARRaceEntryStatusRaceIdentity or bundle.target != _TARGET:
            raise ValueError("target")
        if type(bundle.repository_relative_paths) is not tuple or bundle.repository_relative_paths != (
            EXPECTED_DEBA_TABLE_PATH_V3, EXPECTED_RACE_LIST_PATH_V3, EXPECTED_MANIFEST_PATH_V3
        ):
            raise ValueError("paths")
        for payload, (length, digest) in zip(
            (bundle.deba_table_bytes, bundle.race_list_bytes, bundle.manifest_bytes), _FROZEN_BYTES
        ):
            if type(payload) is not bytes or len(payload) != length or sha256(payload).hexdigest() != digest:
                raise ValueError("bytes")
        if type(bundle.manifest) is not SourceProfileManifestV3:
            raise ValueError("manifest type")
        if bundle.manifest.canonical_bytes() != bundle.manifest_bytes:
            raise ValueError("manifest canonical bytes")
        document = bundle.manifest.to_canonical_dict()
        if (
            document["provider"] != _ORGANIZATION
            or document["target"] != {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6}
            or document["acquisition_semantics"] != "CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET"
            or document["market_eligibility"] != "UNSUPPORTED"
            or bundle.manifest.fixture_set.identity != _FIXTURE_SET_ID
            or bundle.manifest.qualification.identity != _QUALIFICATION_ID
        ):
            raise ValueError("manifest authority")
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise _failure("UNSUPPORTED_BUNDLE", "frozen V3 authority is contradictory") from error
    return bundle


def _extract_source_entries(deba_table_bytes: bytes, external_race_id: str) -> tuple[_SourceEntryIdentity, ...]:
    """Read only identity-bearing Deba structure; never inspect odds or status."""
    try:
        soup = BeautifulSoup(deba_table_bytes.decode("utf-8", errors="strict"), "html.parser")
        rows = _nar_identity._horse_rows(soup)
        entries = []
        for row in rows:
            cells = row.find_all("td", class_="horseNum", recursive=False)
            if len(cells) != 1:
                raise ValueError("horse number cell cardinality")
            token = cells[0].get_text(strip=False)
            if re.fullmatch(r"[1-9][0-9]*", token, flags=re.ASCII) is None:
                raise ValueError("noncanonical horse number")
            horse_no = int(token)
            links = row.select("a.horseName[href]")
            if len(links) != 1:
                raise ValueError("horse link cardinality")
            external_horse_id = _nar_identity._canonical_horse_identity(links[0]["href"])
            entries.append(_SourceEntryIdentity(
                f"{external_race_id}:entry:{horse_no}", external_horse_id, horse_no
            ))
        entries.sort(key=lambda item: item.horse_no)
        if tuple(item.horse_no for item in entries) != tuple(range(1, 15)):
            raise ValueError("frozen fourteen-entry universe")
        if len({item.external_entry_id for item in entries}) != 14:
            raise ValueError("duplicate external entry identity")
        return tuple(entries)
    except (UnicodeError, ValueError, TypeError, KeyError, _nar_identity.NarHistoricalInputSourceError) as error:
        raise _failure("SOURCE_ENTRY_IDENTITY_INVALID", "Deba entry identity structure is invalid") from error


def _connection_preconditions(connection: object) -> sqlite3.Connection:
    if type(connection) is not sqlite3.Connection:
        raise _failure("SQLITE_CONNECTION_INVALID", "connection must be an exact sqlite3.Connection")
    try:
        if connection.in_transaction:
            raise ValueError("caller transaction active")
        if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
            raise ValueError("foreign_keys not enabled")
        if connection.execute("PRAGMA query_only").fetchone() != (1,):
            raise ValueError("query_only not enabled")
        databases = connection.execute("PRAGMA database_list").fetchall()
        if len(databases) != 1 or databases[0][1] != "main":
            raise ValueError("attached database")
    except (sqlite3.Error, ValueError) as error:
        raise _failure("SQLITE_CONNECTION_INVALID", "read-only connection precondition failed") from error
    return connection


_COLUMNS = {
    "historical_input_source_identities": {"organization": "TEXT", "source_system": "TEXT"},
    "historical_input_external_races": {"organization": "TEXT", "source_system": "TEXT", "external_race_id": "TEXT", "internal_race_id": "INTEGER"},
    "historical_input_external_entries": {"organization": "TEXT", "source_system": "TEXT", "external_race_id": "TEXT", "external_entry_id": "TEXT", "internal_race_id": "INTEGER", "race_entry_id": "INTEGER"},
    "races": {"id": "INTEGER"},
    "horses": {"id": "INTEGER", "race_id": "INTEGER", "horse_no": "INTEGER"},
}
_PRIMARY_KEYS = {
    "historical_input_source_identities": ("organization", "source_system"),
    "historical_input_external_races": ("organization", "source_system", "external_race_id"),
    "historical_input_external_entries": ("organization", "source_system", "external_race_id", "external_entry_id"),
}
_UNIQUE_KEYS = {
    "historical_input_external_races": (
        ("organization", "source_system", "external_race_id", "internal_race_id"),
        ("organization", "source_system", "internal_race_id"),
    ),
    "historical_input_external_entries": (("organization", "source_system", "internal_race_id", "race_entry_id"),),
    "horses": (("race_id", "id"),),
}
_FOREIGN_KEYS = {
    "historical_input_external_races": {
        ("historical_input_source_identities", ("organization", "source_system"), ("organization", "source_system")),
        ("races", ("internal_race_id",), ("id",)),
    },
    "historical_input_external_entries": {
        ("historical_input_external_races", ("organization", "source_system", "external_race_id", "internal_race_id"), ("organization", "source_system", "external_race_id", "internal_race_id")),
        ("horses", ("internal_race_id", "race_entry_id"), ("race_id", "id")),
    },
}


def _unique_keys(connection: sqlite3.Connection, table: str) -> set[tuple[str, ...]]:
    result = set()
    for row in connection.execute(f"PRAGMA index_list('{table}')"):
        name, unique, partial = row[1], row[2], row[4]
        if not unique or partial:
            continue
        columns = connection.execute(f"PRAGMA index_xinfo('{name}')").fetchall()
        key_columns = [item for item in columns if item[5]]
        if any(item[2] is None or item[4] != "BINARY" for item in key_columns):
            continue
        result.add(tuple(item[2] for item in sorted(key_columns, key=lambda item: item[0])))
    return result


def _foreign_keys(connection: sqlite3.Connection, table: str) -> set[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    grouped: dict[int, list[tuple]] = {}
    for row in connection.execute(f"PRAGMA foreign_key_list('{table}')"):
        grouped.setdefault(row[0], []).append(row)
    result = set()
    for rows in grouped.values():
        rows.sort(key=lambda item: item[1])
        if any(item[5] != "RESTRICT" or item[6] != "RESTRICT" for item in rows):
            continue
        result.add((rows[0][2], tuple(item[3] for item in rows), tuple(item[4] for item in rows)))
    return result


def _validate_schema(connection: sqlite3.Connection) -> None:
    try:
        for table, expected in _COLUMNS.items():
            if connection.execute("SELECT type FROM sqlite_master WHERE name = ?", (table,)).fetchall() != [("table",)]:
                raise ValueError(f"table {table}")
            rows = connection.execute(f"PRAGMA table_info('{table}')").fetchall()
            columns = {item[1]: item for item in rows}
            if any(name not in columns or columns[name][2].upper() != kind for name, kind in expected.items()):
                raise ValueError(f"columns {table}")
            if table in _PRIMARY_KEYS:
                key = tuple(item[1] for item in sorted(rows, key=lambda item: item[5]) if item[5])
                if key != _PRIMARY_KEYS[table]:
                    raise ValueError(f"primary key {table}")
            if not set(_UNIQUE_KEYS.get(table, ())).issubset(_unique_keys(connection, table)):
                raise ValueError(f"unique keys {table}")
            if not _FOREIGN_KEYS.get(table, set()).issubset(_foreign_keys(connection, table)):
                raise ValueError(f"foreign keys {table}")
        for table in ("historical_input_external_races", "historical_input_external_entries"):
            if connection.execute(f"PRAGMA foreign_key_check('{table}')").fetchone() is not None:
                raise ValueError(f"foreign key integrity {table}")
    except (sqlite3.Error, ValueError) as error:
        raise _failure("SQLITE_SCHEMA_INVALID", "V010 identity schema is invalid") from error


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _one_row(rows: list[tuple], missing: str, ambiguous: str) -> tuple:
    if not rows:
        raise _failure(missing, "mapping row is absent")
    if len(rows) != 1:
        raise _failure(ambiguous, "mapping is not unique")
    return rows[0]


def _bind_rows(connection: sqlite3.Connection, source: tuple[_SourceEntryIdentity, ...]) -> NARRaceEntryStatusReplayIdentityBinding:
    race_rows = connection.execute(
        "SELECT internal_race_id FROM historical_input_external_races WHERE organization=? AND source_system=? AND external_race_id=?",
        (_ORGANIZATION, _SOURCE_SYSTEM, _EXTERNAL_RACE_ID),
    ).fetchall()
    (internal_race_id,) = _one_row(race_rows, "INTERNAL_RACE_MAPPING_MISSING", "INTERNAL_RACE_MAPPING_AMBIGUOUS")
    if not _positive_int(internal_race_id):
        raise _failure("INTERNAL_RACE_MAPPING_CONTRADICTION", "internal race ID is invalid")
    reverse = connection.execute(
        "SELECT external_race_id FROM historical_input_external_races WHERE organization=? AND source_system=? AND internal_race_id=?",
        (_ORGANIZATION, _SOURCE_SYSTEM, internal_race_id),
    ).fetchall()
    if reverse != [(_EXTERNAL_RACE_ID,)]:
        raise _failure("INTERNAL_RACE_MAPPING_CONTRADICTION", "reverse race mapping contradicts source")
    if connection.execute("SELECT id FROM races WHERE id=?", (internal_race_id,)).fetchall() != [(internal_race_id,)]:
        raise _failure("INTERNAL_RACE_MAPPING_CONTRADICTION", "internal race row is missing")
    db_rows = connection.execute(
        "SELECT external_entry_id, internal_race_id, race_entry_id FROM historical_input_external_entries WHERE organization=? AND source_system=? AND external_race_id=?",
        (_ORGANIZATION, _SOURCE_SYSTEM, _EXTERNAL_RACE_ID),
    ).fetchall()
    grouped: dict[str, list[tuple]] = {}
    for row in db_rows:
        grouped.setdefault(row[0], []).append(row)
    bindings = []
    seen_ids = set()
    for entry in source:
        row = _one_row(grouped.get(entry.external_entry_id, []), "ENTRY_MAPPING_MISSING", "ENTRY_MAPPING_AMBIGUOUS")
        _, entry_race_id, race_entry_id = row
        if entry_race_id != internal_race_id or not _positive_int(race_entry_id):
            raise _failure("ENTRY_MAPPING_CONTRADICTION", "entry mapping has a wrong internal identity")
        if race_entry_id in seen_ids:
            raise _failure("DUPLICATE_RACE_ENTRY_ID", "two source entries map to one internal entry")
        seen_ids.add(race_entry_id)
        horse_rows = connection.execute(
            "SELECT horse_no FROM horses WHERE race_id=? AND id=?", (internal_race_id, race_entry_id)
        ).fetchall()
        if len(horse_rows) != 1:
            raise _failure("INTERNAL_ENTRY_ROW_MISSING", "mapped internal horses row is missing")
        (stored_horse_no,) = horse_rows[0]
        if not _positive_int(stored_horse_no) or stored_horse_no != entry.horse_no:
            raise _failure("HORSE_NUMBER_CONTRADICTION", "mapped entry horse number contradicts source")
        bindings.append(NARRaceEntryStatusReplayEntryIdentityBinding(
            entry.external_entry_id, entry.external_horse_id, entry.horse_no, race_entry_id
        ))
    if set(grouped) != {item.external_entry_id for item in source} or len(db_rows) != len(source):
        raise _failure("DATABASE_ENTRY_SET_CONTRADICTION", "database entry universe differs from source")
    return NARRaceEntryStatusReplayIdentityBinding(
        _TARGET, _ORGANIZATION, _SOURCE_SYSTEM, _EXTERNAL_RACE_ID, internal_race_id, tuple(bindings)
    )


def bind_nar_race_entry_status_v3_identity(
    *,
    bundle: NARRaceEntryStatusSourceProfileFixtureBundleV3,
    connection: sqlite3.Connection,
) -> NARRaceEntryStatusReplayIdentityBinding:
    """Bind every frozen source entry to preexisting V010 identities, or fail."""
    authentic = _validate_bundle(bundle)
    if f"nar:{authentic.target.race_date:%Y%m%d}:{authentic.target.baba_code}:{authentic.target.race_no}" != _EXTERNAL_RACE_ID:
        raise _failure("EXTERNAL_RACE_IDENTITY_CONTRADICTION", "target race identity is contradictory")
    source = _extract_source_entries(authentic.deba_table_bytes, _EXTERNAL_RACE_ID)
    connection = _connection_preconditions(connection)
    started = False
    try:
        connection.execute("BEGIN")
        started = True
        _validate_schema(connection)
        return _bind_rows(connection, source)
    except sqlite3.Error as error:
        raise _failure("SQLITE_SCHEMA_INVALID", "SQLite read failed") from error
    finally:
        if started:
            connection.rollback()
