"""Isolated schema and explicit migration runner for NAR daily-target evidence."""

from __future__ import annotations

import sqlite3 as _sqlite3


VERSION = 1
NAME = "v001_nar_daily_target_evidence_archive_schema"
_REGISTRY = "nar_daily_target_evidence_archive_schema_migrations"
_REGISTRY_DDL = """CREATE TABLE nar_daily_target_evidence_archive_schema_migrations (
    version INTEGER PRIMARY KEY CHECK (typeof(version) = 'integer' AND version > 0),
    name TEXT NOT NULL UNIQUE CHECK (typeof(name) = 'text' AND name <> '')
) WITHOUT ROWID"""
_BODY_DDL = """CREATE TABLE nar_daily_target_evidence_bodies (
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
_SUPPLIER_DDL = """CREATE TABLE nar_daily_target_supplier_captures (
    capture_id TEXT PRIMARY KEY CHECK (
        typeof(capture_id) = 'text' AND length(capture_id) = 97
        AND substr(capture_id, 1, 33) = 'nar-monthly-bootstrap-capture-v1:'
        AND substr(capture_id, 34) NOT GLOB '*[^0-9a-f]*'
    ),
    schema_version INTEGER NOT NULL CHECK (
        typeof(schema_version) = 'integer' AND schema_version = 1
    ),
    page_kind TEXT NOT NULL CHECK (
        page_kind IN ('official_home', 'monthly_root', 'locator_script')
    ),
    canonical_request_url TEXT NOT NULL CHECK (
        typeof(canonical_request_url) = 'text' AND canonical_request_url <> ''
    ),
    effective_url TEXT NOT NULL CHECK (
        typeof(effective_url) = 'text' AND effective_url <> ''
    ),
    response_sha256 TEXT NOT NULL CHECK (
        typeof(response_sha256) = 'text' AND length(response_sha256) = 64
        AND response_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    charset TEXT NOT NULL CHECK (typeof(charset) = 'text' AND charset = 'utf-8'),
    requested_at_utc TEXT NOT NULL CHECK (
        typeof(requested_at_utc) = 'text' AND length(requested_at_utc) = 32
        AND requested_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    observed_at_utc TEXT NOT NULL CHECK (
        typeof(observed_at_utc) = 'text' AND length(observed_at_utc) = 32
        AND observed_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    stored_at_utc TEXT NOT NULL CHECK (
        typeof(stored_at_utc) = 'text' AND length(stored_at_utc) = 32
        AND stored_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    http_status INTEGER NOT NULL CHECK (typeof(http_status) = 'integer' AND http_status = 200),
    content_type TEXT NOT NULL CHECK (typeof(content_type) = 'text' AND content_type <> ''),
    content_encoding TEXT NULL CHECK (content_encoding IS NULL OR content_encoding = 'identity'),
    content_length INTEGER NULL CHECK (
        content_length IS NULL OR (typeof(content_length) = 'integer' AND content_length >= 0)
    ),
    CHECK (requested_at_utc <= observed_at_utc AND observed_at_utc <= stored_at_utc),
    FOREIGN KEY (response_sha256) REFERENCES nar_daily_target_evidence_bodies (response_sha256)
        ON UPDATE RESTRICT ON DELETE RESTRICT
) WITHOUT ROWID"""
_RESPONSE_DDL = """CREATE TABLE nar_daily_target_response_captures (
    capture_id TEXT PRIMARY KEY CHECK (
        typeof(capture_id) = 'text' AND length(capture_id) = 92
        AND substr(capture_id, 1, 28) = 'nar-daily-target-capture-v1:'
        AND substr(capture_id, 29) NOT GLOB '*[^0-9a-f]*'
    ),
    schema_version INTEGER NOT NULL CHECK (typeof(schema_version) = 'integer' AND schema_version = 1),
    page_kind TEXT NOT NULL CHECK (page_kind IN ('monthly_convene_info', 'race_list')),
    request_schema_version INTEGER NOT NULL CHECK (
        typeof(request_schema_version) = 'integer' AND request_schema_version = 1
    ),
    request_identity TEXT NOT NULL CHECK (
        typeof(request_identity) = 'text' AND length(request_identity) = 92
        AND substr(request_identity, 1, 28) = 'nar-daily-target-request-v1:'
        AND substr(request_identity, 29) NOT GLOB '*[^0-9a-f]*'
    ),
    request_identity_sha256 TEXT NOT NULL CHECK (
        typeof(request_identity_sha256) = 'text' AND length(request_identity_sha256) = 64
        AND request_identity_sha256 NOT GLOB '*[^0-9a-f]*'
        AND request_identity = 'nar-daily-target-request-v1:' || request_identity_sha256
    ),
    request_method TEXT NOT NULL CHECK (request_method = 'GET'),
    request_official_origin TEXT NOT NULL CHECK (request_official_origin = 'https://www.keiba.go.jp'),
    official_supplied_request_material BLOB NOT NULL CHECK (
        typeof(official_supplied_request_material) = 'blob'
        AND length(official_supplied_request_material) > 0
    ),
    resolved_request_url TEXT NOT NULL CHECK (
        typeof(resolved_request_url) = 'text' AND resolved_request_url <> ''
    ),
    supplier_evidence_identity TEXT NOT NULL CHECK (
        typeof(supplier_evidence_identity) = 'text' AND supplier_evidence_identity <> ''
    ),
    request_target_date TEXT NULL CHECK (
        request_target_date IS NULL OR (
            typeof(request_target_date) = 'text' AND length(request_target_date) = 10
            AND request_target_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        )
    ),
    request_baba_code TEXT NULL CHECK (
        request_baba_code IS NULL OR (typeof(request_baba_code) = 'text' AND request_baba_code <> '')
    ),
    request_target_year INTEGER NOT NULL CHECK (
        typeof(request_target_year) = 'integer' AND request_target_year BETWEEN 1 AND 9999
    ),
    request_target_month INTEGER NOT NULL CHECK (
        typeof(request_target_month) = 'integer' AND request_target_month BETWEEN 1 AND 12
    ),
    response_sha256 TEXT NOT NULL CHECK (
        typeof(response_sha256) = 'text' AND length(response_sha256) = 64
        AND response_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    charset TEXT NOT NULL CHECK (typeof(charset) = 'text' AND charset = 'utf-8'),
    requested_at_utc TEXT NOT NULL CHECK (
        typeof(requested_at_utc) = 'text' AND length(requested_at_utc) = 32
        AND requested_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    observed_at_utc TEXT NOT NULL CHECK (
        typeof(observed_at_utc) = 'text' AND length(observed_at_utc) = 32
        AND observed_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    stored_at_utc TEXT NOT NULL CHECK (
        typeof(stored_at_utc) = 'text' AND length(stored_at_utc) = 32
        AND stored_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    http_status INTEGER NOT NULL CHECK (typeof(http_status) = 'integer' AND http_status = 200),
    content_type TEXT NULL CHECK (content_type IS NULL OR typeof(content_type) = 'text'),
    content_encoding TEXT NULL CHECK (content_encoding IS NULL OR content_encoding = 'identity'),
    http_date TEXT NULL CHECK (http_date IS NULL OR typeof(http_date) = 'text'),
    etag TEXT NULL CHECK (etag IS NULL OR typeof(etag) = 'text'),
    last_modified TEXT NULL CHECK (last_modified IS NULL OR typeof(last_modified) = 'text'),
    content_length INTEGER NULL CHECK (
        content_length IS NULL OR (typeof(content_length) = 'integer' AND content_length >= 0)
    ),
    CHECK (requested_at_utc <= observed_at_utc AND observed_at_utc <= stored_at_utc),
    CHECK (
        (page_kind = 'monthly_convene_info' AND request_target_date IS NULL AND request_baba_code IS NULL)
        OR (page_kind = 'race_list' AND request_target_date IS NOT NULL AND request_baba_code IS NOT NULL)
    ),
    FOREIGN KEY (response_sha256) REFERENCES nar_daily_target_evidence_bodies (response_sha256)
        ON UPDATE RESTRICT ON DELETE RESTRICT
) WITHOUT ROWID"""
_SUPPLIER_INDEX_DDL = """CREATE UNIQUE INDEX ux_nar_daily_target_supplier_captures_evidence
    ON nar_daily_target_supplier_captures (
        page_kind, canonical_request_url, response_sha256, observed_at_utc
    )"""
_RESPONSE_INDEX_DDL = """CREATE UNIQUE INDEX ux_nar_daily_target_response_captures_evidence
    ON nar_daily_target_response_captures (
        request_identity_sha256, response_sha256, observed_at_utc
    )"""
_EXPECTED_SQL = {
    _REGISTRY: ("table", _REGISTRY_DDL),
    "nar_daily_target_evidence_bodies": ("table", _BODY_DDL),
    "nar_daily_target_supplier_captures": ("table", _SUPPLIER_DDL),
    "nar_daily_target_response_captures": ("table", _RESPONSE_DDL),
    "ux_nar_daily_target_supplier_captures_evidence": ("index", _SUPPLIER_INDEX_DDL),
    "ux_nar_daily_target_response_captures_evidence": ("index", _RESPONSE_INDEX_DDL),
}


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
    return " ".join(value.upper().split())


def _user_objects(connection: _sqlite3.Connection) -> dict[str, tuple[str, str]]:
    rows = connection.execute(
        "SELECT name,type,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    result: dict[str, tuple[str, str]] = {}
    for name, kind, sql in rows:
        if type(name) is not str or type(kind) is not str or type(sql) is not str or name in result:
            raise RuntimeError("daily-target archive schema objects are malformed")
        result[name] = (kind, sql)
    return result


def _validate_registry(connection: _sqlite3.Connection) -> dict[int, str] | None:
    objects = _user_objects(connection)
    item = objects.get(_REGISTRY)
    if item is None:
        if objects:
            raise RuntimeError("database is not an empty dedicated daily-target archive")
        return None
    if item[0] != "table" or _normalized_sql(item[1]) != _normalized_sql(_REGISTRY_DDL):
        raise RuntimeError("daily-target archive migration registry schema is malformed")
    columns = connection.execute(f"PRAGMA table_info({_REGISTRY})").fetchall()
    expected = (("version", "INTEGER", 1, 1), ("name", "TEXT", 1, 0))
    actual = tuple((row[1], row[2], row[3], row[5]) for row in columns)
    if actual != expected:
        raise RuntimeError("daily-target archive migration registry columns are malformed")
    rows = connection.execute(f"SELECT version,name FROM {_REGISTRY}").fetchall()
    applied: dict[int, str] = {}
    for version, name in rows:
        if type(version) is not int or version <= 0 or type(name) is not str or not name or version in applied:
            raise RuntimeError("daily-target archive migration registry rows are malformed")
        applied[version] = name
    return applied


def _validate_v1_objects(connection: _sqlite3.Connection) -> None:
    objects = _user_objects(connection)
    if set(objects) != set(_EXPECTED_SQL):
        raise RuntimeError("daily-target archive schema object set is incompatible")
    for name, (expected_kind, expected_sql) in _EXPECTED_SQL.items():
        actual_kind, actual_sql = objects[name]
        if actual_kind != expected_kind or _normalized_sql(actual_sql) != _normalized_sql(expected_sql):
            raise RuntimeError(f"daily-target archive schema object {name} is incompatible")
    expected_supplier_fk = [
        ("nar_daily_target_evidence_bodies", "response_sha256", "response_sha256", "RESTRICT", "RESTRICT")
    ]
    for table in ("nar_daily_target_supplier_captures", "nar_daily_target_response_captures"):
        rows = connection.execute(f"PRAGMA foreign_key_list({table})").fetchall()
        actual = [(row[2], row[3], row[4], row[5], row[6]) for row in rows]
        if actual != expected_supplier_fk:
            raise RuntimeError(f"daily-target archive foreign keys for {table} are incompatible")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise RuntimeError("daily-target archive foreign-key integrity is invalid")


def apply(connection: _sqlite3.Connection) -> None:
    """Create v1 domain objects only; the caller owns the transaction."""

    connection = _connection(connection)
    connection.execute(_BODY_DDL)
    connection.execute(_SUPPLIER_DDL)
    connection.execute(_RESPONSE_DDL)
    connection.execute(_SUPPLIER_INDEX_DDL)
    connection.execute(_RESPONSE_INDEX_DDL)


def get_applied_nar_daily_target_evidence_archive_schema_versions(
    connection: _sqlite3.Connection,
) -> dict[int, str]:
    """Read and validate applied isolated archive versions without creating schema."""

    connection = _connection(connection)
    _foreign_keys(connection)
    applied = _validate_registry(connection)
    if applied is None:
        return {}
    if set(applied) - {VERSION}:
        raise RuntimeError("unknown future daily-target archive schema version")
    if VERSION in applied and applied[VERSION] != NAME:
        raise RuntimeError("daily-target archive migration name mismatch")
    if VERSION in applied:
        _validate_v1_objects(connection)
    elif len(_user_objects(connection)) != 1:
        raise RuntimeError("unregistered daily-target archive schema objects exist")
    return applied


def get_pending_nar_daily_target_evidence_archive_migrations(
    connection: _sqlite3.Connection,
) -> tuple[object, ...]:
    """Return the one transaction-neutral v1 migration when it is pending."""

    applied = get_applied_nar_daily_target_evidence_archive_schema_versions(connection)
    return () if VERSION in applied else (apply,)


def apply_nar_daily_target_evidence_archive_migrations(
    connection: _sqlite3.Connection,
) -> None:
    """Explicitly and atomically apply the isolated archive migration sequence."""

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
            raise RuntimeError("unknown future daily-target archive schema version")
        if VERSION in applied:
            if applied[VERSION] != NAME:
                raise RuntimeError("daily-target archive migration name mismatch")
            _validate_v1_objects(connection)
        else:
            if set(_user_objects(connection)) != {_REGISTRY}:
                raise RuntimeError("unregistered daily-target archive schema objects exist")
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


def require_nar_daily_target_evidence_archive_schema(
    connection: _sqlite3.Connection,
) -> None:
    """Read-only exact schema gate for repository construction and operations."""

    applied = get_applied_nar_daily_target_evidence_archive_schema_versions(connection)
    if applied != {VERSION: NAME}:
        raise RuntimeError("daily-target evidence archive schema version 1 is required")


if "annotations" in globals():
    del annotations
