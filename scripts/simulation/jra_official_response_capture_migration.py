"""Version one schema for the separate trusted JRA capture archive."""

from __future__ import annotations

import sqlite3 as _sqlite3

VERSION = 1
NAME = "v001_jra_official_response_capture_schema"


def apply(connection: _sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE jra_official_response_bodies (
        response_sha256 TEXT PRIMARY KEY CHECK(typeof(response_sha256)='text' AND length(response_sha256)=64 AND response_sha256 NOT GLOB '*[^0-9a-f]*'),
        response_body BLOB NOT NULL CHECK(typeof(response_body)='blob'),
        byte_length INTEGER NOT NULL CHECK(typeof(byte_length)='integer' AND byte_length>0 AND byte_length=length(response_body))
    ) WITHOUT ROWID""")
    connection.execute("""CREATE TABLE jra_official_response_captures (
        capture_id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL CHECK(typeof(schema_version)='integer' AND schema_version=1),
        page_kind TEXT NOT NULL CHECK(page_kind IN ('race_result','horse_profile_history')),
        canonical_source_url TEXT NOT NULL CHECK(typeof(canonical_source_url)='text' AND canonical_source_url<>''),
        response_sha256 TEXT NOT NULL REFERENCES jra_official_response_bodies(response_sha256) ON UPDATE RESTRICT ON DELETE RESTRICT,
        charset TEXT NOT NULL CHECK(charset='cp932'), requested_at_utc TEXT NOT NULL, observed_at_utc TEXT NOT NULL, stored_at_utc TEXT NOT NULL,
        http_status INTEGER NOT NULL CHECK(typeof(http_status)='integer' AND http_status=200), content_type TEXT NOT NULL,
        content_encoding TEXT NULL CHECK(content_encoding IS NULL OR content_encoding='identity'), http_date TEXT NULL, etag TEXT NULL,
        last_modified TEXT NULL, content_length INTEGER NULL CHECK(content_length IS NULL OR (typeof(content_length)='integer' AND content_length>=0)),
        CHECK(requested_at_utc<=observed_at_utc AND observed_at_utc<=stored_at_utc)
    ) WITHOUT ROWID""")
    connection.execute("CREATE UNIQUE INDEX ux_jra_official_response_captures_evidence ON jra_official_response_captures(canonical_source_url,response_sha256,observed_at_utc)")


if "annotations" in globals():
    del annotations
