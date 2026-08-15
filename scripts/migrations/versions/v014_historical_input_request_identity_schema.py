"""Add an optional provider-neutral request identity to historical evidence."""

from __future__ import annotations

import sqlite3


VERSION = 14
NAME = "v014_historical_input_request_identity_schema"


def apply(connection: sqlite3.Connection) -> None:
    connection.execute(
        """ALTER TABLE historical_input_snapshot_provenance_evidence
           ADD COLUMN request_identity_sha256 TEXT NULL CHECK (
               request_identity_sha256 IS NULL OR (
                   typeof(request_identity_sha256) = 'text'
                   AND length(request_identity_sha256) = 64
                   AND request_identity_sha256 NOT GLOB '*[^0-9a-f]*'
               )
           )"""
    )
