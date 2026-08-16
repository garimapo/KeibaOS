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


def _validate_v002(connection: _sqlite3.Connection) -> None:
    """Fail closed before mutation; v003 never adopts an arbitrary v002 lookalike."""

    expected = (
        "capture_id", "schema_version", "page_kind", "canonical_source_url", "response_sha256", "charset",
        "requested_at_utc", "observed_at_utc", "stored_at_utc", "http_status", "content_type",
        "content_encoding", "http_date", "etag", "last_modified", "content_length", "request_method",
        "request_identity_sha256", "request_cname",
    )
    columns = tuple(row[1] for row in connection.execute(f"PRAGMA table_info({_TABLE})"))
    if columns != expected:
        raise RuntimeError("v002 capture table columns are invalid")
    table = [row for row in connection.execute("PRAGMA table_list") if row[0] == "main" and row[1] == _TABLE]
    if table != [("main", _TABLE, "table", 19, 1, 0)]:
        raise RuntimeError("v002 capture table is not WITHOUT ROWID")
    names = {row[1]: row for row in connection.execute(f"PRAGMA index_list({_TABLE})")}
    for name in ("ux_jra_official_response_captures_evidence", "ux_jra_official_response_captures_request_evidence"):
        item = names.get(name)
        if item is None or item[2:] != (1, "c", 1):
            raise RuntimeError("v002 evidence indexes are invalid")
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='jra_official_response_bodies'").fetchone() is None:
        raise RuntimeError("v002 response body table is missing")
    # Reconstructing through the current repository is deliberately avoided here:
    # v003 must validate v002 without recursively requiring v003 schema support.
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
