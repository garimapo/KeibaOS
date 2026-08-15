"""Version two schema for request-aware JRA final-win-odds captures."""

from __future__ import annotations

import hashlib as _hashlib
import sqlite3 as _sqlite3

from scripts.simulation.jra_official_response_capture import (
    JRAOfficialResponseCapture as _Capture,
    JRAOfficialResponseCaptureError as _CaptureError,
)

VERSION = 2
NAME = "v002_jra_official_response_capture_request_identity_schema"

_TABLE = "jra_official_response_captures"
_OLD = "jra_official_response_captures_v001"
_OLD_INDEX = "ux_jra_official_response_captures_evidence"
_COLUMNS = (
    "capture_id", "schema_version", "page_kind", "canonical_source_url", "response_sha256", "charset",
    "requested_at_utc", "observed_at_utc", "stored_at_utc", "http_status", "content_type",
    "content_encoding", "http_date", "etag", "last_modified", "content_length",
)
_BODY_COLUMNS = (
    ("response_sha256", "TEXT", 1, 1), ("response_body", "BLOB", 1, 0), ("byte_length", "INTEGER", 1, 0),
)
_CAPTURE_COLUMNS = (
    ("capture_id", "TEXT", 1, 1), ("schema_version", "INTEGER", 1, 0), ("page_kind", "TEXT", 1, 0),
    ("canonical_source_url", "TEXT", 1, 0), ("response_sha256", "TEXT", 1, 0), ("charset", "TEXT", 1, 0),
    ("requested_at_utc", "TEXT", 1, 0), ("observed_at_utc", "TEXT", 1, 0), ("stored_at_utc", "TEXT", 1, 0),
    ("http_status", "INTEGER", 1, 0), ("content_type", "TEXT", 1, 0), ("content_encoding", "TEXT", 0, 0),
    ("http_date", "TEXT", 0, 0), ("etag", "TEXT", 0, 0), ("last_modified", "TEXT", 0, 0),
    ("content_length", "INTEGER", 0, 0),
)


def _stored_time(value: object):
    from datetime import datetime as _datetime, timezone as _timezone
    if type(value) is not str or len(value) != 32:
        raise RuntimeError("v001 capture timestamp is invalid")
    try:
        parsed = _datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() != _timezone.utc.utcoffset(parsed):
            raise ValueError
        if parsed.astimezone(_timezone.utc).isoformat(timespec="microseconds") != value:
            raise ValueError
        return parsed.astimezone(_timezone.utc)
    except (TypeError, ValueError, OverflowError) as error:
        raise RuntimeError("v001 capture timestamp is invalid") from error


def _table_columns(connection: _sqlite3.Connection, table: str) -> tuple[tuple[str, str, int, int], ...]:
    return tuple((item[1], item[2], item[3], item[5]) for item in connection.execute(f"PRAGMA table_info({table})"))


def _table_without_rowid(connection: _sqlite3.Connection, table: str, columns: int) -> None:
    values = [item for item in connection.execute("PRAGMA table_list").fetchall() if item[0] == "main" and item[1] == table]
    if values != [("main", table, "table", columns, 1, 0)]:
        raise RuntimeError(f"{table} WITHOUT ROWID schema is invalid")


def _validate_structure(connection: _sqlite3.Connection) -> None:
    if _table_columns(connection, "jra_official_response_bodies") != _BODY_COLUMNS:
        raise RuntimeError("v001 response body table columns are invalid")
    _table_without_rowid(connection, "jra_official_response_bodies", 3)
    body_indexes = connection.execute("PRAGMA index_list(jra_official_response_bodies)").fetchall()
    if len(body_indexes) != 1 or body_indexes[0][2:] != (1, "pk", 0):
        raise RuntimeError("v001 response body indexes are invalid")
    if _table_columns(connection, _TABLE) != _CAPTURE_COLUMNS:
        raise RuntimeError("v001 capture table columns are invalid")
    _table_without_rowid(connection, _TABLE, 16)
    foreign_keys = connection.execute(f"PRAGMA foreign_key_list({_TABLE})").fetchall()
    if foreign_keys != [(0, 0, "jra_official_response_bodies", "response_sha256", "response_sha256", "RESTRICT", "RESTRICT", "NONE")]:
        raise RuntimeError("v001 capture foreign key is invalid")
    indexes = connection.execute(f"PRAGMA index_list({_TABLE})").fetchall()
    evidence = [item for item in indexes if item[1] == _OLD_INDEX]
    automatic = [item for item in indexes if item[3] == "pk"]
    if len(indexes) != 2 or len(evidence) != 1 or len(automatic) != 1 or evidence[0][2:] != (1, "c", 0):
        raise RuntimeError("v001 capture indexes are invalid")
    if [(item[0], item[2]) for item in connection.execute(f"PRAGMA index_info({_OLD_INDEX})")] != [(0, "canonical_source_url"), (1, "response_sha256"), (2, "observed_at_utc")]:
        raise RuntimeError("v001 capture evidence index is invalid")
    xinfo = connection.execute(f"PRAGMA index_xinfo({_OLD_INDEX})").fetchall()
    if [(item[1], item[2], item[5]) for item in xinfo] != [(3, "canonical_source_url", 1), (4, "response_sha256", 1), (7, "observed_at_utc", 1), (0, "capture_id", 0)]:
        raise RuntimeError("v001 capture evidence index has expressions or extra keys")


def _probe_rejected(connection: _sqlite3.Connection, sql: str, values: tuple[object, ...]) -> None:
    try:
        connection.execute(sql, values)
    except _sqlite3.IntegrityError:
        return
    raise RuntimeError("v001 schema constraint is not enforced")


def _probe_values(label: str, body_sha: str, **changes: object) -> tuple[object, ...]:
    values: dict[str, object] = {
        "capture_id": "__jra_v001_probe_" + label + "__", "schema_version": 1, "page_kind": "race_result",
        "canonical_source_url": "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC",
        "response_sha256": body_sha, "charset": "cp932", "requested_at_utc": "2026-01-01T00:00:00.000000+00:00",
        "observed_at_utc": "2026-01-01T00:00:00.000000+00:00", "stored_at_utc": "2026-01-01T00:00:00.000000+00:00",
        "http_status": 200, "content_type": "text/html", "content_encoding": None, "http_date": None,
        "etag": None, "last_modified": None, "content_length": None,
    }
    values.update(changes)
    return tuple(values[name] for name in _COLUMNS)


def _probe_constraints(connection: _sqlite3.Connection) -> None:
    if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("v001 foreign key enforcement is disabled")
    digest = _hashlib.sha256(b"__jra_v001_probe_body__").hexdigest()
    unknown = _hashlib.sha256(b"__jra_v001_unknown_body__").hexdigest()
    capture_sql = f"INSERT INTO {_TABLE}({','.join(_COLUMNS)}) VALUES({','.join('?' for _ in _COLUMNS)})"
    connection.execute("SAVEPOINT jra_v001_schema_probe")
    try:
        for sql, values in (
            ("INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", ("g" * 64, b"x", 1)),
            ("INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", (_hashlib.sha256(b"text").hexdigest(), "not-a-blob", 10)),
            ("INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", (_hashlib.sha256(b"zero").hexdigest(), b"x", 0)),
            ("INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", (_hashlib.sha256(b"negative").hexdigest(), b"x", -1)),
            ("INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", (_hashlib.sha256(b"mismatch").hexdigest(), b"x", 2)),
        ):
            _probe_rejected(connection, sql, values)
        connection.execute("INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", (digest, b"x", 1))
        for label, changes in (
            ("version", {"schema_version": 2}), ("kind", {"page_kind": "unknown"}),
            ("empty_url", {"canonical_source_url": ""}), ("nontext_url", {"canonical_source_url": _sqlite3.Binary(b"url")}),
            ("foreign_key", {"response_sha256": unknown}), ("charset", {"charset": "utf8"}),
            ("status", {"http_status": 201}), ("encoding", {"content_encoding": "gzip"}),
            ("negative_length", {"content_length": -1}), ("text_length", {"content_length": "one"}),
            ("requested_order", {"requested_at_utc": "2026-01-01T00:00:01.000000+00:00"}),
            ("observed_order", {"observed_at_utc": "2026-01-01T00:00:01.000000+00:00"}),
        ):
            _probe_rejected(connection, capture_sql, _probe_values(label, digest, **changes))
    finally:
        connection.execute("ROLLBACK TO jra_v001_schema_probe")
        connection.execute("RELEASE jra_v001_schema_probe")


def _validate_v001(connection: _sqlite3.Connection) -> None:
    _validate_structure(connection)
    _probe_constraints(connection)
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", ("jra_official_response_bodies",)).fetchone() is None:
        raise RuntimeError("v001 response body table is missing")
    rows = connection.execute(
        "SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length FROM jra_official_response_captures"
    ).fetchall()
    if connection.execute("SELECT 1 FROM jra_official_response_captures GROUP BY canonical_source_url,response_sha256,observed_at_utc HAVING COUNT(*)<>1").fetchone() is not None:
        raise RuntimeError("v001 capture evidence is duplicated")
    for row in rows:
        capture_id, version, kind, url, digest, charset, requested, observed, stored, status, content_type, encoding, http_date, etag, last_modified, length = row
        body_rows = connection.execute("SELECT response_body,byte_length FROM jra_official_response_bodies WHERE response_sha256=?", (digest,)).fetchall()
        if len(body_rows) != 1:
            raise RuntimeError("v001 capture body is missing or duplicated")
        body, body_length = body_rows[0]
        if type(body) is not bytes or type(body_length) is not int or body_length != len(body) or _hashlib.sha256(body).hexdigest() != digest:
            raise RuntimeError("v001 response body is invalid")
        try:
            capture = _Capture(canonical_source_url=url, response_body=body, charset=charset, requested_at=_stored_time(requested), observed_at=_stored_time(observed), stored_at=_stored_time(stored), http_status=status, content_type=content_type, content_encoding=encoding, http_date=http_date, etag=etag, last_modified=last_modified, content_length=length)
        except (_CaptureError, TypeError, ValueError, OverflowError) as error:
            raise RuntimeError("v001 capture row violates the legacy domain") from error
        if version != 1 or kind != capture.page_kind.value or capture.capture_id != capture_id or capture.response_sha256 != digest:
            raise RuntimeError("v001 capture identity is invalid")


def apply(connection: _sqlite3.Connection) -> None:
    """Rebuild only the capture table; the caller owns the transaction."""

    _validate_v001(connection)
    connection.execute(f"ALTER TABLE {_TABLE} RENAME TO {_OLD}")
    connection.execute(f"DROP INDEX {_OLD_INDEX}")
    connection.execute("""CREATE TABLE jra_official_response_captures (
        capture_id TEXT PRIMARY KEY,
        schema_version INTEGER NOT NULL CHECK(typeof(schema_version)='integer' AND schema_version IN (1,2)),
        page_kind TEXT NOT NULL CHECK(page_kind IN ('race_result','horse_profile_history','final_win_odds')),
        canonical_source_url TEXT NOT NULL CHECK(typeof(canonical_source_url)='text' AND canonical_source_url<>''),
        response_sha256 TEXT NOT NULL REFERENCES jra_official_response_bodies(response_sha256) ON UPDATE RESTRICT ON DELETE RESTRICT,
        charset TEXT NOT NULL CHECK(charset='cp932'), requested_at_utc TEXT NOT NULL, observed_at_utc TEXT NOT NULL, stored_at_utc TEXT NOT NULL,
        http_status INTEGER NOT NULL CHECK(typeof(http_status)='integer' AND http_status=200), content_type TEXT NOT NULL,
        content_encoding TEXT NULL CHECK(content_encoding IS NULL OR content_encoding='identity'), http_date TEXT NULL, etag TEXT NULL,
        last_modified TEXT NULL, content_length INTEGER NULL CHECK(content_length IS NULL OR (typeof(content_length)='integer' AND content_length>=0)),
        request_method TEXT NOT NULL CHECK(request_method IN ('GET','POST')),
        request_identity_sha256 TEXT NULL CHECK(request_identity_sha256 IS NULL OR (typeof(request_identity_sha256)='text' AND length(request_identity_sha256)=64 AND request_identity_sha256 NOT GLOB '*[^0-9a-f]*')),
        request_cname TEXT NULL CHECK(request_cname IS NULL OR (typeof(request_cname)='text' AND length(request_cname)>0)),
        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc),
        CHECK((schema_version=1 AND page_kind IN ('race_result','horse_profile_history') AND request_method='GET' AND request_identity_sha256 IS NULL AND request_cname IS NULL) OR (schema_version=2 AND page_kind='final_win_odds' AND request_method='POST' AND request_identity_sha256 IS NOT NULL AND request_cname IS NOT NULL))
    ) WITHOUT ROWID""")
    connection.execute("""INSERT INTO jra_official_response_captures(
        capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length,request_method,request_identity_sha256,request_cname
    ) SELECT capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length,'GET',NULL,NULL FROM jra_official_response_captures_v001""")
    connection.execute("CREATE UNIQUE INDEX ux_jra_official_response_captures_evidence ON jra_official_response_captures(canonical_source_url,response_sha256,observed_at_utc) WHERE request_identity_sha256 IS NULL")
    connection.execute("CREATE UNIQUE INDEX ux_jra_official_response_captures_request_evidence ON jra_official_response_captures(canonical_source_url,request_identity_sha256,response_sha256,observed_at_utc) WHERE request_identity_sha256 IS NOT NULL")
    connection.execute(f"DROP TABLE {_OLD}")


if "annotations" in globals():
    del annotations
