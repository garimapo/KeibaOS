"""Version three schema for isolated JRA accessD target-card captures."""

from __future__ import annotations

from datetime import datetime as _datetime, timezone as _timezone
import hashlib as _hashlib
import sqlite3 as _sqlite3

from scripts.simulation.jra_official_identity import build_jra_final_win_odds_request_locator as _build_final_locator
from scripts.simulation.jra_official_response_capture import (
    JRAFinalWinOddsResponseCapture as _FinalCapture,
    JRAOfficialResponseCapture as _LegacyCapture,
    JRAOfficialResponseCaptureError as _CaptureError,
)

VERSION = 3
NAME = "v003_jra_official_response_capture_target_race_card_schema"

_TABLE = "jra_official_response_captures"
_OLD = "jra_official_response_captures_v002"
_COLUMNS = "capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,http_date,etag,last_modified,content_length,request_method,request_identity_sha256,request_cname"
_BODY_COLUMNS = (("response_sha256", "TEXT", 1, 1), ("response_body", "BLOB", 1, 0), ("byte_length", "INTEGER", 1, 0))
_CAPTURE_COLUMNS = (
    ("capture_id", "TEXT", 1, 1), ("schema_version", "INTEGER", 1, 0), ("page_kind", "TEXT", 1, 0),
    ("canonical_source_url", "TEXT", 1, 0), ("response_sha256", "TEXT", 1, 0), ("charset", "TEXT", 1, 0),
    ("requested_at_utc", "TEXT", 1, 0), ("observed_at_utc", "TEXT", 1, 0), ("stored_at_utc", "TEXT", 1, 0),
    ("http_status", "INTEGER", 1, 0), ("content_type", "TEXT", 1, 0), ("content_encoding", "TEXT", 0, 0),
    ("http_date", "TEXT", 0, 0), ("etag", "TEXT", 0, 0), ("last_modified", "TEXT", 0, 0),
    ("content_length", "INTEGER", 0, 0), ("request_method", "TEXT", 1, 0),
    ("request_identity_sha256", "TEXT", 0, 0), ("request_cname", "TEXT", 0, 0),
)
_EVIDENCE_INDEX = "ux_jra_official_response_captures_evidence"
_REQUEST_INDEX = "ux_jra_official_response_captures_request_evidence"


def _normalized_ddl(value: object) -> str:
    if type(value) is not str:
        return ""
    return " ".join(value.split()).upper()


_EXPECTED_V002_DDL = {
    "jra_official_response_bodies": _normalized_ddl("""CREATE TABLE jra_official_response_bodies (
        response_sha256 TEXT PRIMARY KEY CHECK(typeof(response_sha256)='text' AND length(response_sha256)=64 AND response_sha256 NOT GLOB '*[^0-9a-f]*'),
        response_body BLOB NOT NULL CHECK(typeof(response_body)='blob'),
        byte_length INTEGER NOT NULL CHECK(typeof(byte_length)='integer' AND byte_length>0 AND byte_length=length(response_body))
    ) WITHOUT ROWID"""),
    _TABLE: _normalized_ddl("""CREATE TABLE jra_official_response_captures (
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
    ) WITHOUT ROWID"""),
    _EVIDENCE_INDEX: _normalized_ddl("CREATE UNIQUE INDEX ux_jra_official_response_captures_evidence ON jra_official_response_captures(canonical_source_url,response_sha256,observed_at_utc) WHERE request_identity_sha256 IS NULL"),
    _REQUEST_INDEX: _normalized_ddl("CREATE UNIQUE INDEX ux_jra_official_response_captures_request_evidence ON jra_official_response_captures(canonical_source_url,request_identity_sha256,response_sha256,observed_at_utc) WHERE request_identity_sha256 IS NOT NULL"),
}


def _time(value: object) -> _datetime:
    if type(value) is not str or len(value) != 32:
        raise RuntimeError("v002 stored timestamp is invalid")
    try:
        result = _datetime.fromisoformat(value)
        if result.tzinfo is None or result.utcoffset() != _timezone.utc.utcoffset(result) or result.astimezone(_timezone.utc).isoformat(timespec="microseconds") != value:
            raise ValueError
        return result.astimezone(_timezone.utc)
    except (TypeError, ValueError, OverflowError) as error:
        raise RuntimeError("v002 stored timestamp is invalid") from error


def _columns(connection: _sqlite3.Connection, table: str) -> tuple[tuple[str, str, int, int], ...]:
    return tuple((row[1], row[2], row[3], row[5]) for row in connection.execute(f"PRAGMA table_info({table})"))


def _without_rowid(connection: _sqlite3.Connection, table: str, count: int) -> None:
    items = [row for row in connection.execute("PRAGMA table_list") if row[0] == "main" and row[1] == table]
    if items != [("main", table, "table", count, 1, 0)]:
        raise RuntimeError(f"{table} exact WITHOUT ROWID structure is invalid")


def _index(connection: _sqlite3.Connection, name: str, columns: tuple[str, ...], predicate: str) -> None:
    entries = connection.execute(f"PRAGMA index_list({_TABLE})").fetchall()
    wanted = [row for row in entries if row[1] == name]
    automatic = [row for row in entries if row[3] == "pk"]
    custom = [row for row in entries if row[3] == "c"]
    if len(entries) != 3 or len(automatic) != 1 or len(custom) != 2 or len(wanted) != 1 or wanted[0][2:] != (1, "c", 1):
        raise RuntimeError("v002 capture indexes are invalid")
    if tuple(row[2] for row in connection.execute(f"PRAGMA index_info({name})")) != columns:
        raise RuntimeError("v002 evidence index order is invalid")
    xinfo = connection.execute(f"PRAGMA index_xinfo({name})").fetchall()
    if [(row[0], row[2], row[5]) for row in xinfo] != [(index, column, 1) for index, column in enumerate(columns)] + [(len(columns), "capture_id", 0)]:
        raise RuntimeError("v002 evidence index has expressions or extra keys")
    sql = connection.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name=?", (name,)).fetchone()
    if len(sql or ()) != 1 or type(sql[0]) is not str or " ".join(sql[0].split()).upper() != predicate:
        raise RuntimeError("v002 evidence index predicate is invalid")


def _rejected(connection: _sqlite3.Connection, sql: str, values: tuple[object, ...]) -> None:
    try:
        connection.execute(sql, values)
    except _sqlite3.IntegrityError:
        return
    raise RuntimeError("v002 CHECK constraint is not enforced")


def _probe_constraints(connection: _sqlite3.Connection) -> None:
    if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
        raise RuntimeError("v002 foreign-key enforcement is disabled")
    digest = _hashlib.sha256(b"__jra_v002_probe_body__").hexdigest()
    unknown = _hashlib.sha256(b"__jra_v002_probe_unknown__").hexdigest()
    values = ["__jra_v002_probe__", 1, "race_result", "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC", digest, "cp932", "2026-01-01T00:00:00.000000+00:00", "2026-01-01T00:00:00.000000+00:00", "2026-01-01T00:00:00.000000+00:00", 200, "text/html", None, None, None, None, None, "GET", None, None]
    names = _COLUMNS.split(",")
    insert = f"INSERT INTO {_TABLE}({_COLUMNS}) VALUES({','.join('?' for _ in names)})"
    connection.execute("SAVEPOINT jra_v002_schema_probe")
    try:
        for body_values in (("g" * 64, b"x", 1), (_hashlib.sha256(b"text").hexdigest(), "not-a-blob", 1), (_hashlib.sha256(b"zero").hexdigest(), b"x", 0), (_hashlib.sha256(b"mismatch").hexdigest(), b"x", 2)):
            _rejected(connection, "INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", body_values)
        connection.execute("INSERT INTO jra_official_response_bodies(response_sha256,response_body,byte_length) VALUES(?,?,?)", (digest, b"x", 1))
        for index, value in ((1, 3), (2, "unknown"), (3, ""), (3, _sqlite3.Binary(b"url")), (4, unknown), (5, "utf8"), (9, 201), (11, "gzip"), (15, -1), (15, "one"), (16, "PUT"), (17, "x" * 64), (18, ""), (6, "2026-01-01T00:00:01.000000+00:00"), (7, "2026-01-01T00:00:01.000000+00:00"), (16, "POST")):
            candidate = list(values)
            candidate[index] = value
            _rejected(connection, insert, tuple(candidate))
    finally:
        connection.execute("ROLLBACK TO jra_v002_schema_probe")
        connection.execute("RELEASE jra_v002_schema_probe")


def _validate_v002(connection: _sqlite3.Connection) -> None:
    """Fail closed before mutation; v003 never adopts an arbitrary v002 lookalike."""

    for name, expected in _EXPECTED_V002_DDL.items():
        row = connection.execute("SELECT sql FROM sqlite_master WHERE name=?", (name,)).fetchone()
        if len(row or ()) != 1 or _normalized_ddl(row[0]) != expected:
            raise RuntimeError("v002 DDL differs from the approved registered schema")
    if _columns(connection, "jra_official_response_bodies") != _BODY_COLUMNS:
        raise RuntimeError("v002 response-body table columns are invalid")
    _without_rowid(connection, "jra_official_response_bodies", 3)
    body_indexes = connection.execute("PRAGMA index_list(jra_official_response_bodies)").fetchall()
    if len(body_indexes) != 1 or body_indexes[0][2:] != (1, "pk", 0):
        raise RuntimeError("v002 response-body indexes are invalid")
    if _columns(connection, _TABLE) != _CAPTURE_COLUMNS:
        raise RuntimeError("v002 capture table columns are invalid")
    _without_rowid(connection, _TABLE, 19)
    capture_sql_row = connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (_TABLE,)).fetchone()
    capture_sql = " ".join(capture_sql_row[0].split()).upper() if len(capture_sql_row or ()) == 1 and type(capture_sql_row[0]) is str else ""
    for fragment in (
        "SCHEMA_VERSION INTEGER NOT NULL CHECK(TYPEOF(SCHEMA_VERSION)='INTEGER' AND SCHEMA_VERSION IN (1,2))",
        "PAGE_KIND TEXT NOT NULL CHECK(PAGE_KIND IN ('RACE_RESULT','HORSE_PROFILE_HISTORY','FINAL_WIN_ODDS'))",
        "CHECK(REQUESTED_AT_UTC<=OBSERVED_AT_UTC AND OBSERVED_AT_UTC<=STORED_AT_UTC)",
        "(SCHEMA_VERSION=1 AND PAGE_KIND IN ('RACE_RESULT','HORSE_PROFILE_HISTORY') AND REQUEST_METHOD='GET' AND REQUEST_IDENTITY_SHA256 IS NULL AND REQUEST_CNAME IS NULL)",
        "(SCHEMA_VERSION=2 AND PAGE_KIND='FINAL_WIN_ODDS' AND REQUEST_METHOD='POST' AND REQUEST_IDENTITY_SHA256 IS NOT NULL AND REQUEST_CNAME IS NOT NULL)",
    ):
        if fragment not in capture_sql:
            raise RuntimeError("v002 capture CHECK structure is invalid")
    foreign_keys = connection.execute(f"PRAGMA foreign_key_list({_TABLE})").fetchall()
    if foreign_keys != [(0, 0, "jra_official_response_bodies", "response_sha256", "response_sha256", "RESTRICT", "RESTRICT", "NONE")]:
        raise RuntimeError("v002 capture foreign key is invalid")
    _index(connection, _EVIDENCE_INDEX, ("canonical_source_url", "response_sha256", "observed_at_utc"), "CREATE UNIQUE INDEX UX_JRA_OFFICIAL_RESPONSE_CAPTURES_EVIDENCE ON JRA_OFFICIAL_RESPONSE_CAPTURES(CANONICAL_SOURCE_URL,RESPONSE_SHA256,OBSERVED_AT_UTC) WHERE REQUEST_IDENTITY_SHA256 IS NULL")
    _index(connection, _REQUEST_INDEX, ("canonical_source_url", "request_identity_sha256", "response_sha256", "observed_at_utc"), "CREATE UNIQUE INDEX UX_JRA_OFFICIAL_RESPONSE_CAPTURES_REQUEST_EVIDENCE ON JRA_OFFICIAL_RESPONSE_CAPTURES(CANONICAL_SOURCE_URL,REQUEST_IDENTITY_SHA256,RESPONSE_SHA256,OBSERVED_AT_UTC) WHERE REQUEST_IDENTITY_SHA256 IS NOT NULL")
    _probe_constraints(connection)
    invalid = connection.execute("SELECT 1 FROM jra_official_response_captures WHERE (schema_version=1 AND (page_kind NOT IN ('race_result','horse_profile_history') OR request_method<>'GET' OR request_identity_sha256 IS NOT NULL OR request_cname IS NOT NULL)) OR (schema_version=2 AND (page_kind<>'final_win_odds' OR request_method<>'POST' OR request_identity_sha256 IS NULL OR request_cname IS NULL)) OR schema_version NOT IN (1,2) LIMIT 1").fetchone()
    if invalid is not None:
        raise RuntimeError("v002 capture row family is invalid")
    rows = connection.execute(f"SELECT {_COLUMNS} FROM {_TABLE}").fetchall()
    for row in rows:
        capture_id, version, kind, url, digest, charset, requested, observed, stored, status, content_type, encoding, http_date, etag, last_modified, length, method, request_digest, cname = row
        body_rows = connection.execute("SELECT response_body,byte_length FROM jra_official_response_bodies WHERE response_sha256=?", (digest,)).fetchall()
        if len(body_rows) != 1:
            raise RuntimeError("v002 capture body is missing or duplicated")
        body, byte_length = body_rows[0]
        if type(body) is not bytes or type(byte_length) is not int or byte_length != len(body) or type(digest) is not str or _hashlib.sha256(body).hexdigest() != digest:
            raise RuntimeError("v002 capture body is invalid")
        try:
            if version == 1:
                capture = _LegacyCapture(canonical_source_url=url, response_body=body, charset=charset, requested_at=_time(requested), observed_at=_time(observed), stored_at=_time(stored), http_status=status, content_type=content_type, content_encoding=encoding, http_date=http_date, etag=etag, last_modified=last_modified, content_length=length)
            elif version == 2:
                locator = _build_final_locator(cname=cname)
                if locator.endpoint_url != url or locator.request_identity_sha256 != request_digest:
                    raise ValueError
                capture = _FinalCapture(request_locator=locator, response_body=body, charset=charset, requested_at=_time(requested), observed_at=_time(observed), stored_at=_time(stored), http_status=status, content_type=content_type, content_encoding=encoding, http_date=http_date, etag=etag, last_modified=last_modified, content_length=length)
            else:
                raise ValueError
        except (_CaptureError, TypeError, ValueError, OverflowError) as error:
            raise RuntimeError("v002 capture row violates its domain") from error
        if capture.capture_id != capture_id or capture.page_kind.value != kind or capture.response_sha256 != digest:
            raise RuntimeError("v002 capture identity is invalid")


def apply(connection: _sqlite3.Connection) -> None:
    """Rebuild only captures; caller owns transaction and registry registration."""

    _validate_v002(connection)
    connection.execute(f"ALTER TABLE {_TABLE} RENAME TO {_OLD}")
    connection.execute("DROP INDEX ux_jra_official_response_captures_evidence")
    connection.execute("DROP INDEX ux_jra_official_response_captures_request_evidence")
    connection.execute("""CREATE TABLE jra_official_response_captures (
        capture_id TEXT PRIMARY KEY,
        schema_version INTEGER NOT NULL CHECK(typeof(schema_version)='integer' AND schema_version IN (1,2,3)),
        page_kind TEXT NOT NULL CHECK(page_kind IN ('race_result','horse_profile_history','final_win_odds','target_race_card')),
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
        CHECK((schema_version=1 AND page_kind IN ('race_result','horse_profile_history') AND request_method='GET' AND request_identity_sha256 IS NULL AND request_cname IS NULL) OR (schema_version=2 AND page_kind='final_win_odds' AND request_method='POST' AND request_identity_sha256 IS NOT NULL AND request_cname IS NOT NULL) OR (schema_version=3 AND page_kind='target_race_card' AND request_method='GET' AND request_identity_sha256 IS NULL AND request_cname IS NULL))
    ) WITHOUT ROWID""")
    connection.execute(f"INSERT INTO {_TABLE}({_COLUMNS}) SELECT {_COLUMNS} FROM {_OLD}")
    connection.execute("CREATE UNIQUE INDEX ux_jra_official_response_captures_evidence ON jra_official_response_captures(canonical_source_url,response_sha256,observed_at_utc) WHERE request_identity_sha256 IS NULL")
    connection.execute("CREATE UNIQUE INDEX ux_jra_official_response_captures_request_evidence ON jra_official_response_captures(canonical_source_url,request_identity_sha256,response_sha256,observed_at_utc) WHERE request_identity_sha256 IS NOT NULL")
    connection.execute(f"DROP TABLE {_OLD}")


if "annotations" in globals():
    del annotations
