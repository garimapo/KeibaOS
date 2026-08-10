"""Version one schema for the separate trusted NAR capture archive."""

from __future__ import annotations

import sqlite3 as _sqlite3


VERSION = 1
NAME = "v001_nar_official_response_capture_schema"


def apply(connection: _sqlite3.Connection) -> None:
    """Create only capture-archive schema objects; caller owns transactions."""

    connection.execute(
        """CREATE TABLE nar_official_response_bodies (
            response_sha256 TEXT PRIMARY KEY CHECK (
                typeof(response_sha256) = 'text' AND length(response_sha256) = 64
                AND response_sha256 NOT GLOB '*[^0-9a-f]*'
            ),
            response_body BLOB NOT NULL CHECK (typeof(response_body) = 'blob'),
            byte_length INTEGER NOT NULL CHECK (
                typeof(byte_length) = 'integer' AND byte_length > 0 AND byte_length = length(response_body)
            )
        ) WITHOUT ROWID""",
    )
    connection.execute(
        """CREATE TABLE nar_official_response_captures (
            capture_id TEXT PRIMARY KEY CHECK (
                typeof(capture_id) = 'text' AND length(capture_id) = 79
                AND substr(capture_id, 1, 15) = 'nar-capture-v1:'
                AND substr(capture_id, 16) NOT GLOB '*[^0-9a-f]*'
            ),
            schema_version INTEGER NOT NULL CHECK (typeof(schema_version) = 'integer' AND schema_version = 1),
            page_kind TEXT NOT NULL CHECK (page_kind IN ('deba_table', 'horse_mark_info', 'race_mark_table')),
            canonical_source_url TEXT NOT NULL CHECK (typeof(canonical_source_url) = 'text' AND canonical_source_url <> ''),
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
            FOREIGN KEY (response_sha256) REFERENCES nar_official_response_bodies (response_sha256)
                ON UPDATE RESTRICT ON DELETE RESTRICT
        ) WITHOUT ROWID""",
    )
    connection.execute(
        """CREATE UNIQUE INDEX ux_nar_official_response_captures_evidence
            ON nar_official_response_captures (canonical_source_url, response_sha256, observed_at_utc)""",
    )


if "annotations" in globals():
    del annotations
