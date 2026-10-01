"""Atomic Phase110 identity issuance in the existing horses.id namespace."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from scripts.migrations.versions.v018_nar_identity_complete_entry_schema import require_phase110_schema
from scripts.simulation.nar_historical_input_source import (
    NarHistoricalInputSourceError, _canonical_horse_identity,
)
from scripts.simulation.nar_identity_complete_entry_persistence import (
    NARIdentityPersistedEntryV1, canonical_json, create_receipt, parse_receipt,
)
from scripts.simulation.nar_identity_complete_entry_source import load_identity_complete_source
from scripts.simulation.nar_trusted_deba_acquisition import canonical_deba_url


class NARIdentityPersistenceError(ValueError):
    """Missing or contradictory complete-population authority."""


class SQLiteNARIdentityCompleteEntryRepository:
    def __init__(self, *, connection: sqlite3.Connection):
        if type(connection) is not sqlite3.Connection or connection.in_transaction:
            raise NARIdentityPersistenceError("exact idle SQLite connection required")
        connection.execute("PRAGMA foreign_keys=ON")
        if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
            raise NARIdentityPersistenceError("foreign keys required")
        self._connection = connection

    def persist(self, *, qualified_result, lineage_archive, capture_archive,
                place: str, issued_at: datetime):
        """Read Phase111 authority, then bind the complete population atomically."""
        if type(place) is not str or not place or place != place.strip():
            raise NARIdentityPersistenceError("exact local place candidate required")
        source = load_identity_complete_source(
            result=qualified_result, lineage_archive=lineage_archive,
            capture_archive=capture_archive)
        if source.observed_at > source.prediction_cutoff:
            raise NARIdentityPersistenceError("post-cutoff identity evidence")
        connection = self._connection
        if connection.in_transaction:
            raise NARIdentityPersistenceError("caller transaction not allowed")
        connection.execute("BEGIN IMMEDIATE")
        try:
            require_phase110_schema(connection)
            receipt = self._persist_locked(source, place, issued_at)
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        loaded = self.load_receipt(receipt_id=receipt.receipt_id)
        if loaded != receipt:
            raise NARIdentityPersistenceError("receipt exact reload differs")
        return loaded

    def _persist_locked(self, source, place, issued_at):
        connection = self._connection
        day, baba, number = source.external_race_id.split(":")[1:]
        race_date = f"{day[:4]}-{day[4:6]}-{day[6:]}"
        if canonical_deba_url(source.external_race_id) != source.canonical_deba_url:
            raise NARIdentityPersistenceError("Phase111 Deba ancestry differs")
        parents = connection.execute(
            """SELECT id,deba_table_url FROM races
               WHERE race_date=? AND organization='NAR' AND place=? AND race_no=?""",
            (race_date, place, int(number))).fetchall()
        if len(parents) != 1:
            raise NARIdentityPersistenceError("exact existing parent race required")
        race_id, stored_url = parents[0]
        if type(stored_url) is not str or not stored_url or stored_url != source.canonical_deba_url:
            raise NARIdentityPersistenceError("parent Deba URL is missing/noncanonical/contradictory")
        external_parents = connection.execute(
            """SELECT id FROM races WHERE organization='NAR' AND deba_table_url=? LIMIT 2""",
            (source.canonical_deba_url,),
        ).fetchall()
        if external_parents != [(race_id,)]:
            raise NARIdentityPersistenceError("canonical Deba URL has ambiguous NAR parent binding")
        if connection.execute(
            "SELECT 1 FROM nar_identity_complete_receipts WHERE race_id=? OR external_race_id=?",
            (race_id, source.external_race_id)).fetchone():
            raise NARIdentityPersistenceError("parent already has Phase110 receipt")
        existing_rows = connection.execute(
            "SELECT id,horse_no,horse_detail_url FROM horses WHERE race_id=?", (race_id,)).fetchall()
        if len(existing_rows) != len({row[1] for row in existing_rows}):
            raise NARIdentityPersistenceError("ambiguous existing horse number")
        by_number = {row[1]: row for row in existing_rows}
        if not set(by_number).issubset({entry.horse_no for entry in source.entries}):
            raise NARIdentityPersistenceError("existing race has extra entry identity")
        persisted = []
        for entry in source.entries:
            old = by_number.get(entry.horse_no)
            if old is None:
                cursor = connection.execute(
                    "INSERT INTO horses(race_id,horse_no) VALUES (?,?)",
                    (race_id, entry.horse_no))
                horse_id = cursor.lastrowid
                disposition = "ISSUED_IDENTITY_ONLY_INTERNAL_ID"
            else:
                horse_id, _, old_url = old
                if entry.external_horse_id is None or not old_url:
                    raise NARIdentityPersistenceError("existing entry lacks trusted horse-identity agreement")
                try:
                    old_identity = _canonical_horse_identity(old_url)
                except (ValueError, NarHistoricalInputSourceError) as error:
                    raise NARIdentityPersistenceError("existing horse URL is malformed") from error
                if old_identity != entry.external_horse_id:
                    raise NARIdentityPersistenceError("existing provider horse identity contradicts Deba")
                disposition = "ADOPTED_EXISTING_INTERNAL_ID"
            persisted.append(NARIdentityPersistedEntryV1(
                entry.external_entry_id, horse_id, entry.horse_no,
                entry.external_horse_id, disposition))
        receipt = create_receipt(source=source, race_id=race_id, issued_at=issued_at,
                                 entries=tuple(persisted))
        connection.execute(
            """INSERT INTO nar_identity_complete_receipts
               (receipt_id,external_race_id,race_id,canonical_deba_url,
                phase111_declaration_id,phase111_receipt_id,phase111_capture_id,
                response_sha256,observed_at,prediction_cutoff,population_sha256,
                population_count,receipt_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (receipt.receipt_id, receipt.external_race_id, receipt.race_id,
             receipt.canonical_deba_url, receipt.phase111_declaration_id,
             receipt.phase111_receipt_id, receipt.phase111_capture_id,
             receipt.response_sha256, receipt.observed_at.isoformat(),
             receipt.prediction_cutoff.isoformat(), receipt.population_sha256,
             len(receipt.entries), canonical_json(receipt.payload())))
        for entry in receipt.entries:
            connection.execute(
                """INSERT INTO nar_identity_complete_entries
                   (receipt_id,external_entry_id,race_id,horse_id,horse_no,
                    external_horse_id,issuance_disposition)
                   VALUES (?,?,?,?,?,?,?)""",
                (receipt.receipt_id, entry.external_entry_id, race_id,
                 entry.horse_id, entry.horse_no, entry.external_horse_id,
                 entry.issuance_disposition))
        return receipt

    def load_receipt(self, *, receipt_id: str):
        connection = self._connection
        require_phase110_schema(connection)
        row = connection.execute(
            """SELECT receipt_json,external_race_id,race_id,canonical_deba_url,
                      phase111_declaration_id,phase111_receipt_id,phase111_capture_id,
                      response_sha256,observed_at,prediction_cutoff,population_sha256,population_count
               FROM nar_identity_complete_receipts WHERE receipt_id=?""",
            (receipt_id,)).fetchone()
        if row is None:
            raise NARIdentityPersistenceError("Phase110 receipt not found")
        receipt = parse_receipt(row[0], receipt_id)
        if row[1:] != (
            receipt.external_race_id, receipt.race_id, receipt.canonical_deba_url,
            receipt.phase111_declaration_id, receipt.phase111_receipt_id,
            receipt.phase111_capture_id, receipt.response_sha256,
            receipt.observed_at.isoformat(), receipt.prediction_cutoff.isoformat(),
            receipt.population_sha256, len(receipt.entries)):
            raise NARIdentityPersistenceError("Phase110 receipt projection differs")
        rows = connection.execute(
            """SELECT external_entry_id,horse_id,horse_no,external_horse_id,issuance_disposition
               FROM nar_identity_complete_entries WHERE receipt_id=? ORDER BY horse_no""",
            (receipt_id,)).fetchall()
        if rows != [tuple((entry.external_entry_id, entry.horse_id, entry.horse_no,
                           entry.external_horse_id, entry.issuance_disposition))
                    for entry in receipt.entries]:
            raise NARIdentityPersistenceError("Phase110 entry bindings differ")
        for entry in receipt.entries:
            denied = connection.execute(
                "SELECT receipt_id,external_entry_id,race_id FROM nar_identity_complete_denials WHERE horse_id=?",
                (entry.horse_id,)).fetchone()
            expected = ((receipt.receipt_id, entry.external_entry_id, receipt.race_id)
                        if entry.issuance_disposition == "ISSUED_IDENTITY_ONLY_INTERNAL_ID" else None)
            if denied != expected:
                raise NARIdentityPersistenceError("Phase110 denial topology differs")
        return receipt
