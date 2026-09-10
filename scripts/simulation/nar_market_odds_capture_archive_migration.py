"""Isolated v1 schema and explicit migration runner for NAR market-odds captures."""

from __future__ import annotations

import sqlite3 as _sqlite3


VERSION = 1
NAME = "v001_nar_market_odds_capture_archive_schema"

_REGISTRY = "nar_market_odds_capture_archive_schema_migrations"
_BODIES = "nar_market_odds_response_bodies"
_CAPTURES = "nar_market_odds_response_captures"
_EVIDENCE_INDEX = "ux_nar_market_odds_response_captures_evidence"

_REGISTRY_DDL = """CREATE TABLE nar_market_odds_capture_archive_schema_migrations (
    version INTEGER PRIMARY KEY CHECK (typeof(version) = 'integer' AND version > 0),
    name TEXT NOT NULL UNIQUE CHECK (typeof(name) = 'text' AND name <> '')
) WITHOUT ROWID"""

_BODY_DDL = """CREATE TABLE nar_market_odds_response_bodies (
    response_sha256 TEXT PRIMARY KEY CHECK (
        typeof(response_sha256) = 'text' AND length(response_sha256) = 64
        AND response_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    response_body BLOB NOT NULL CHECK (
        typeof(response_body) = 'blob' AND length(response_body) > 0
    ),
    byte_length INTEGER NOT NULL CHECK (
        typeof(byte_length) = 'integer' AND byte_length > 0
        AND byte_length = length(response_body)
    )
) WITHOUT ROWID"""

_CAPTURE_DDL = """CREATE TABLE nar_market_odds_response_captures (
    capture_id TEXT PRIMARY KEY CHECK (
        typeof(capture_id) = 'text'
        AND length(capture_id) = length('nar-market-odds-capture-v1:') + 64
        AND substr(capture_id, 1, length('nar-market-odds-capture-v1:')) = 'nar-market-odds-capture-v1:'
        AND substr(capture_id, length('nar-market-odds-capture-v1:') + 1) NOT GLOB '*[^0-9a-f]*'
    ),
    schema_version INTEGER NOT NULL CHECK (
        typeof(schema_version) = 'integer' AND schema_version = 1
    ),
    request_schema_version INTEGER NOT NULL CHECK (
        typeof(request_schema_version) = 'integer' AND request_schema_version = 1
    ),
    request_identity TEXT NOT NULL CHECK (
        typeof(request_identity) = 'text'
        AND length(request_identity) = length('nar-market-odds-request-v1:') + 64
        AND request_identity = 'nar-market-odds-request-v1:' || request_identity_sha256
    ),
    request_identity_sha256 TEXT NOT NULL CHECK (
        typeof(request_identity_sha256) = 'text' AND length(request_identity_sha256) = 64
        AND request_identity_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    page_kind TEXT NOT NULL CHECK (
        page_kind IN ('odds_tan_fuku', 'odds_um_len_fuku', 'odds_wide', 'odds_3_len_fuku')
    ),
    organization TEXT NOT NULL CHECK (organization = 'NAR'),
    source_system TEXT NOT NULL CHECK (source_system = 'keiba.go.jp'),
    request_method TEXT NOT NULL CHECK (request_method = 'GET'),
    request_official_origin TEXT NOT NULL CHECK (
        request_official_origin = 'https://www.keiba.go.jp'
    ),
    request_baba_code TEXT NOT NULL CHECK (
        typeof(request_baba_code) = 'text' AND request_baba_code <> ''
        AND substr(request_baba_code, 1, 1) BETWEEN '1' AND '9'
        AND request_baba_code NOT GLOB '*[^0-9]*'
    ),
    request_race_date TEXT NOT NULL CHECK (
        typeof(request_race_date) = 'text' AND length(request_race_date) = 10
        AND request_race_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
    ),
    request_race_no INTEGER NOT NULL CHECK (
        typeof(request_race_no) = 'integer' AND request_race_no > 0
    ),
    canonical_request_url TEXT NOT NULL CHECK (
        typeof(canonical_request_url) = 'text'
        AND canonical_request_url = 'https://www.keiba.go.jp' ||
            CASE page_kind
                WHEN 'odds_tan_fuku' THEN '/KeibaWeb/TodayRaceInfo/OddsTanFuku'
                WHEN 'odds_um_len_fuku' THEN '/KeibaWeb/TodayRaceInfo/OddsUmLenFuku'
                WHEN 'odds_wide' THEN '/KeibaWeb/TodayRaceInfo/OddsWide'
                WHEN 'odds_3_len_fuku' THEN '/KeibaWeb/TodayRaceInfo/Odds3LenFuku'
            END || '?k_babaCode=' || request_baba_code ||
            '&k_raceDate=' || substr(request_race_date, 1, 4) || '%2F' ||
            substr(request_race_date, 6, 2) || '%2F' || substr(request_race_date, 9, 2) ||
            '&k_raceNo=' || request_race_no
    ),
    effective_url TEXT NOT NULL CHECK (
        typeof(effective_url) = 'text' AND effective_url = canonical_request_url
    ),
    response_sha256 TEXT NOT NULL CHECK (
        typeof(response_sha256) = 'text' AND length(response_sha256) = 64
        AND response_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    charset TEXT NOT NULL CHECK (charset = 'utf-8'),
    requested_at_utc TEXT NOT NULL CHECK (
        typeof(requested_at_utc) = 'text' AND length(requested_at_utc) = 32
        AND requested_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    observed_at_utc TEXT NOT NULL CHECK (
        typeof(observed_at_utc) = 'text' AND length(observed_at_utc) = 32
        AND observed_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    captured_at_utc TEXT NOT NULL CHECK (
        typeof(captured_at_utc) = 'text' AND length(captured_at_utc) = 32
        AND captured_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    http_status INTEGER NOT NULL CHECK (
        typeof(http_status) = 'integer' AND http_status = 200
    ),
    content_type TEXT NULL CHECK (content_type IS NULL OR typeof(content_type) = 'text'),
    content_encoding TEXT NULL CHECK (content_encoding IS NULL OR content_encoding = 'identity'),
    http_date TEXT NULL CHECK (http_date IS NULL OR typeof(http_date) = 'text'),
    etag TEXT NULL CHECK (etag IS NULL OR typeof(etag) = 'text'),
    last_modified TEXT NULL CHECK (last_modified IS NULL OR typeof(last_modified) = 'text'),
    content_length INTEGER NULL CHECK (
        content_length IS NULL OR (typeof(content_length) = 'integer' AND content_length >= 0)
    ),
    CHECK (requested_at_utc <= observed_at_utc AND observed_at_utc <= captured_at_utc),
    FOREIGN KEY (response_sha256) REFERENCES nar_market_odds_response_bodies (response_sha256)
        ON UPDATE RESTRICT ON DELETE RESTRICT
) WITHOUT ROWID"""

_INDEX_DDL = """CREATE UNIQUE INDEX ux_nar_market_odds_response_captures_evidence
    ON nar_market_odds_response_captures (
        request_identity_sha256, response_sha256, requested_at_utc,
        observed_at_utc, captured_at_utc
    )"""

_EXPECTED_SQL = {
    _REGISTRY: ("table", _REGISTRY_DDL),
    _BODIES: ("table", _BODY_DDL),
    _CAPTURES: ("table", _CAPTURE_DDL),
    _EVIDENCE_INDEX: ("index", _INDEX_DDL),
}

_REGISTRY_COLUMNS = (
    ("version", "INTEGER", 1, None, 1),
    ("name", "TEXT", 1, None, 0),
)
_BODY_COLUMNS = (
    ("response_sha256", "TEXT", 1, None, 1),
    ("response_body", "BLOB", 1, None, 0),
    ("byte_length", "INTEGER", 1, None, 0),
)
_CAPTURE_COLUMNS = (
    ("capture_id", "TEXT", 1, None, 1),
    ("schema_version", "INTEGER", 1, None, 0),
    ("request_schema_version", "INTEGER", 1, None, 0),
    ("request_identity", "TEXT", 1, None, 0),
    ("request_identity_sha256", "TEXT", 1, None, 0),
    ("page_kind", "TEXT", 1, None, 0),
    ("organization", "TEXT", 1, None, 0),
    ("source_system", "TEXT", 1, None, 0),
    ("request_method", "TEXT", 1, None, 0),
    ("request_official_origin", "TEXT", 1, None, 0),
    ("request_baba_code", "TEXT", 1, None, 0),
    ("request_race_date", "TEXT", 1, None, 0),
    ("request_race_no", "INTEGER", 1, None, 0),
    ("canonical_request_url", "TEXT", 1, None, 0),
    ("effective_url", "TEXT", 1, None, 0),
    ("response_sha256", "TEXT", 1, None, 0),
    ("charset", "TEXT", 1, None, 0),
    ("requested_at_utc", "TEXT", 1, None, 0),
    ("observed_at_utc", "TEXT", 1, None, 0),
    ("captured_at_utc", "TEXT", 1, None, 0),
    ("http_status", "INTEGER", 1, None, 0),
    ("content_type", "TEXT", 0, None, 0),
    ("content_encoding", "TEXT", 0, None, 0),
    ("http_date", "TEXT", 0, None, 0),
    ("etag", "TEXT", 0, None, 0),
    ("last_modified", "TEXT", 0, None, 0),
    ("content_length", "INTEGER", 0, None, 0),
)


def _connection(value: object) -> _sqlite3.Connection:
    if type(value) is not _sqlite3.Connection:
        raise ValueError("connection must be exact sqlite3.Connection")
    return value


def _foreign_keys(connection: _sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    row = connection.execute("PRAGMA foreign_keys").fetchone()
    if row is None or row[0] != 1:
        raise RuntimeError("SQLite foreign_keys could not be enabled")


def _normalized_sql(value: str) -> str:
    # Whitespace is non-semantic, but case inside SQL string literals is not.
    # Preserving all non-whitespace bytes keeps constants such as "NAR" and
    # canonical URL spellings inside the trusted schema contract.
    return " ".join(value.split())


def _user_objects(connection: _sqlite3.Connection) -> dict[str, tuple[str, str]]:
    rows = connection.execute(
        "SELECT name,type,sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY name",
    ).fetchall()
    result: dict[str, tuple[str, str]] = {}
    for name, kind, sql in rows:
        if type(name) is not str or type(kind) is not str or type(sql) is not str or name in result:
            raise RuntimeError("market-odds archive schema objects are malformed")
        result[name] = (kind, sql)
    return result


def _table_columns(
    connection: _sqlite3.Connection,
    table: str,
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (row[1], row[2], row[3], row[4], row[5])
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    )


def _validate_registry(connection: _sqlite3.Connection) -> dict[int, str] | None:
    objects = _user_objects(connection)
    item = objects.get(_REGISTRY)
    if item is None:
        if objects:
            raise RuntimeError("database is not an empty dedicated market-odds archive")
        return None
    if item[0] != "table" or _normalized_sql(item[1]) != _normalized_sql(_REGISTRY_DDL):
        raise RuntimeError("market-odds archive migration registry schema is malformed")
    if _table_columns(connection, _REGISTRY) != _REGISTRY_COLUMNS:
        raise RuntimeError("market-odds archive migration registry columns are malformed")
    rows = connection.execute(f"SELECT version,name FROM {_REGISTRY}").fetchall()
    applied: dict[int, str] = {}
    for version, name in rows:
        if (
            type(version) is not int
            or version <= 0
            or type(name) is not str
            or not name
            or version in applied
        ):
            raise RuntimeError("market-odds archive migration registry rows are malformed")
        applied[version] = name
    return applied


def _validate_v1_objects(connection: _sqlite3.Connection) -> None:
    objects = _user_objects(connection)
    if set(objects) != set(_EXPECTED_SQL):
        raise RuntimeError("market-odds archive schema object set is incompatible")
    for name, (expected_kind, expected_sql) in _EXPECTED_SQL.items():
        actual_kind, actual_sql = objects[name]
        if actual_kind != expected_kind or _normalized_sql(actual_sql) != _normalized_sql(expected_sql):
            raise RuntimeError(f"market-odds archive schema object {name} is incompatible")
    if _table_columns(connection, _REGISTRY) != _REGISTRY_COLUMNS:
        raise RuntimeError("market-odds archive registry columns are incompatible")
    if _table_columns(connection, _BODIES) != _BODY_COLUMNS:
        raise RuntimeError("market-odds archive body columns are incompatible")
    if _table_columns(connection, _CAPTURES) != _CAPTURE_COLUMNS:
        raise RuntimeError("market-odds archive capture columns are incompatible")
    foreign_keys = connection.execute(f"PRAGMA foreign_key_list({_CAPTURES})").fetchall()
    actual_foreign_keys = tuple((row[2], row[3], row[4], row[5], row[6]) for row in foreign_keys)
    expected_foreign_keys = ((_BODIES, "response_sha256", "response_sha256", "RESTRICT", "RESTRICT"),)
    if actual_foreign_keys != expected_foreign_keys:
        raise RuntimeError("market-odds archive foreign key is incompatible")
    index_rows = connection.execute(f"PRAGMA index_list({_CAPTURES})").fetchall()
    named = [row for row in index_rows if row[1] == _EVIDENCE_INDEX]
    if len(named) != 1 or named[0][2] != 1:
        raise RuntimeError("market-odds archive evidence index is incompatible")
    index_columns = tuple(
        row[2]
        for row in connection.execute(f"PRAGMA index_info({_EVIDENCE_INDEX})").fetchall()
    )
    if index_columns != (
        "request_identity_sha256",
        "response_sha256",
        "requested_at_utc",
        "observed_at_utc",
        "captured_at_utc",
    ):
        raise RuntimeError("market-odds archive evidence index columns are incompatible")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("market-odds archive foreign-key integrity is invalid")


def apply(connection: _sqlite3.Connection) -> None:
    """Create only v1 archive domain objects; caller owns the transaction."""

    connection = _connection(connection)
    connection.execute(_BODY_DDL)
    connection.execute(_CAPTURE_DDL)
    connection.execute(_INDEX_DDL)


def get_applied_nar_market_odds_capture_archive_schema_versions(
    connection: _sqlite3.Connection,
) -> dict[int, str]:
    """Read and validate applied isolated archive versions without migration."""

    connection = _connection(connection)
    _foreign_keys(connection)
    applied = _validate_registry(connection)
    if applied is None:
        return {}
    if set(applied) - {VERSION}:
        raise RuntimeError("unknown future market-odds archive schema version")
    if VERSION in applied and applied[VERSION] != NAME:
        raise RuntimeError("market-odds archive migration name mismatch")
    if VERSION in applied:
        _validate_v1_objects(connection)
    elif len(_user_objects(connection)) != 1:
        raise RuntimeError("unregistered market-odds archive schema objects exist")
    return applied


def get_pending_nar_market_odds_capture_archive_migrations(
    connection: _sqlite3.Connection,
) -> tuple[object, ...]:
    """Return the single v1 migration function when it is pending."""

    applied = get_applied_nar_market_odds_capture_archive_schema_versions(connection)
    return () if VERSION in applied else (apply,)


def apply_nar_market_odds_capture_archive_migrations(
    connection: _sqlite3.Connection,
) -> None:
    """Explicitly and atomically apply the isolated archive migration."""

    connection = _connection(connection)
    if connection.in_transaction:
        raise RuntimeError("connection must not already be in a transaction")
    _foreign_keys(connection)
    connection.execute("BEGIN IMMEDIATE")
    try:
        applied = _validate_registry(connection)
        if applied is None:
            connection.execute(_REGISTRY_DDL)
            applied = {}
        if set(applied) - {VERSION}:
            raise RuntimeError("unknown future market-odds archive schema version")
        if VERSION in applied:
            if applied[VERSION] != NAME:
                raise RuntimeError("market-odds archive migration name mismatch")
            _validate_v1_objects(connection)
        else:
            if set(_user_objects(connection)) != {_REGISTRY}:
                raise RuntimeError("unregistered market-odds archive schema objects exist")
            apply(connection)
            connection.execute(
                f"INSERT INTO {_REGISTRY}(version,name) VALUES(?,?)",
                (VERSION, NAME),
            )
            _validate_v1_objects(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise


def require_nar_market_odds_capture_archive_schema(
    connection: _sqlite3.Connection,
) -> None:
    """Require the exact applied v1 schema without creating or repairing it."""

    applied = get_applied_nar_market_odds_capture_archive_schema_versions(connection)
    if applied != {VERSION: NAME}:
        raise RuntimeError("NAR market-odds capture archive schema version 1 is required")


__all__ = (
    "NAME",
    "VERSION",
    "apply",
    "apply_nar_market_odds_capture_archive_migrations",
    "get_applied_nar_market_odds_capture_archive_schema_versions",
    "get_pending_nar_market_odds_capture_archive_migrations",
    "require_nar_market_odds_capture_archive_schema",
)


if "annotations" in globals():
    del annotations
