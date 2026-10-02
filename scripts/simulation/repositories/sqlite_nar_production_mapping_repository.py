"""Atomic V010 mirror plus independently issued immutable Phase109 receipt."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone

from scripts.migrations.versions.v018_nar_identity_complete_entry_schema import require_phase110_schema
from scripts.migrations.versions.v019_nar_production_mapping_authority_schema import require_phase109_schema
from scripts.simulation.nar_production_mapping_authority import (
    NARProductionMappingError, NARProductionMappingReceiptV1,
    _canonical_json, parse_mapping_receipt, receipt_from_phase110,
)
from scripts.simulation.nar_trusted_deba_acquisition import (
    NARProspectiveDebaAcquisitionDeclarationV1 as Declaration,
    NARProspectiveDebaAcquisitionReceiptV1 as AcquisitionReceipt,
    NARProspectiveDebaSendClaimV1 as Claim,
    NARQualifiedDebaResultV1, read_qualified_deba_bytes,
)
from scripts.simulation.repositories.sqlite_nar_identity_complete_entry_repository import (
    SQLiteNARIdentityCompleteEntryRepository,
)
from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import (
    SQLiteNAROfficialResponseCaptureRepository,
)
from scripts.simulation.sqlite_nar_trusted_deba_acquisition_archive import (
    SQLiteNARTrustedDebaAcquisitionArchive,
)

ORG = "NAR"
SOURCE = "nar_official"
_PHASE109_PUBLICATION_MARKER = object()


def _phase111_preflight(*, phase110_receipt_id, phase110_repository,
                        lineage_archive, capture_archive):
    # Read-only across the separate Phase111 stores before taking a main-DB lock.
    phase110 = phase110_repository.load_receipt(receipt_id=phase110_receipt_id)
    receipt = lineage_archive.load_receipt(receipt_id=phase110.phase111_receipt_id)
    if type(receipt) is not AcquisitionReceipt:
        raise NARProductionMappingError("exact Phase111 receipt required")
    declaration = lineage_archive.load_declaration(declaration_id=receipt.declaration_id)
    claim = lineage_archive.load_claim(claim_id=receipt.claim_id)
    capture = capture_archive.load_capture(capture_id=receipt.capture_id)
    if (type(declaration) is not Declaration or type(claim) is not Claim
            or capture is None or declaration.identity != receipt.declaration_id
            or claim.identity != receipt.claim_id or claim.declaration_id != declaration.identity):
        raise NARProductionMappingError("Phase111 ancestry missing or contradictory")
    result = NARQualifiedDebaResultV1(
        receipt.declaration_id, receipt.claim_id, receipt.identity, receipt.capture_id,
        receipt.canonical_deba_url, receipt.response_sha256, receipt.observed_at)
    body = read_qualified_deba_bytes(
        result=result, lineage_archive=lineage_archive, capture_archive=capture_archive)
    if hashlib.sha256(body).hexdigest() != receipt.response_sha256:
        raise NARProductionMappingError("exact Phase111 capture digest differs")
    if (receipt.identity != phase110.phase111_receipt_id
            or declaration.identity != phase110.phase111_declaration_id
            or capture.capture_id != phase110.phase111_capture_id
            or receipt.external_race_id != phase110.external_race_id
            or receipt.canonical_deba_url != phase110.canonical_deba_url
            or receipt.response_sha256 != phase110.response_sha256
            or receipt.observed_at != phase110.observed_at
            or receipt.prediction_information_cutoff != phase110.prediction_cutoff):
        raise NARProductionMappingError("Phase110/111 ancestry differs")
    return phase110


class SQLiteNARProductionMappingRepository:
    def __init__(self, *, connection: sqlite3.Connection):
        if type(connection) is not sqlite3.Connection or connection.in_transaction:
            raise NARProductionMappingError("exact idle SQLite connection required")
        connection.execute("PRAGMA foreign_keys=ON")
        if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
            raise NARProductionMappingError("foreign keys required")
        self._connection = connection
        self._phase110 = SQLiteNARIdentityCompleteEntryRepository(connection=connection)

    def publish(self, *, phase110_receipt_id: str, lineage_archive, capture_archive,
                expected_external_race_id: str, expected_prediction_cutoff: datetime):
        if (type(phase110_receipt_id) is not str or not phase110_receipt_id
                or type(expected_external_race_id) is not str
                or type(expected_prediction_cutoff) is not datetime):
            raise NARProductionMappingError("exact receipt/target/cutoff expectation required")
        if (type(lineage_archive) is not SQLiteNARTrustedDebaAcquisitionArchive
                or type(capture_archive) is not SQLiteNAROfficialResponseCaptureRepository):
            raise NARProductionMappingError("exact persisted Phase111 archives required")
        if self._connection.in_transaction:
            raise NARProductionMappingError("active caller transaction rejected")
        preflight = _phase111_preflight(
            phase110_receipt_id=phase110_receipt_id, phase110_repository=self._phase110,
            lineage_archive=lineage_archive, capture_archive=capture_archive)
        if (preflight.external_race_id != expected_external_race_id
                or preflight.prediction_cutoff != expected_prediction_cutoff):
            raise NARProductionMappingError("expected target/cutoff differs")
        connection = self._connection
        connection.execute("BEGIN IMMEDIATE")
        try:
            require_phase110_schema(connection)
            require_phase109_schema(connection)
            phase110 = self._phase110.load_receipt(receipt_id=phase110_receipt_id)
            if phase110 != preflight:
                raise NARProductionMappingError("Phase110 receipt changed after ancestry preflight")
            existing = connection.execute("""SELECT receipt_id,phase110_receipt_id
                FROM nar_production_mapping_receipts
                WHERE phase110_receipt_id=? OR external_race_id=? OR internal_race_id=?""",
                (phase110_receipt_id, phase110.external_race_id, phase110.race_id)).fetchall()
            if existing:
                if len(existing) != 1 or existing[0][1] != phase110_receipt_id:
                    raise NARProductionMappingError("conflicting Phase109 republication")
                loaded = self.load_receipt(receipt_id=existing[0][0])
                connection.commit()
                return loaded
            self._ensure_v010(phase110)
            issued_at = datetime.now(timezone.utc)
            receipt = receipt_from_phase110(source=phase110, issued_at=issued_at)
            self._insert_receipt(receipt, _publication_marker=_PHASE109_PUBLICATION_MARKER)
            loaded = self.load_receipt(receipt_id=receipt.receipt_id)
            if loaded != receipt:
                raise NARProductionMappingError("Phase109 publication reload differs")
            connection.commit()
            return self.load_receipt(receipt_id=receipt.receipt_id)
        except BaseException:
            connection.rollback()
            raise

    def _ensure_v010(self, phase110) -> None:
        c = self._connection
        source = c.execute("""SELECT organization,source_system
            FROM historical_input_source_identities
            WHERE organization=? AND source_system=?""", (ORG, SOURCE)).fetchone()
        if source is None:
            c.execute("INSERT INTO historical_input_source_identities VALUES (?,?)", (ORG, SOURCE))
        elif source != (ORG, SOURCE):
            raise NARProductionMappingError("V010 source identity differs")
        race_rows = c.execute("""SELECT external_race_id,internal_race_id
            FROM historical_input_external_races
            WHERE organization=? AND source_system=?
              AND (external_race_id=? OR internal_race_id=?)""",
            (ORG, SOURCE, phase110.external_race_id, phase110.race_id)).fetchall()
        expected_race = (phase110.external_race_id, phase110.race_id)
        if race_rows and race_rows != [expected_race]:
            raise NARProductionMappingError("V010 race forward/reverse conflict")
        if not race_rows:
            c.execute("""INSERT INTO historical_input_external_races
                (organization,source_system,external_race_id,internal_race_id)
                VALUES (?,?,?,?)""", (ORG, SOURCE, *expected_race))
        current = c.execute("""SELECT external_race_id,external_entry_id,internal_race_id,race_entry_id
            FROM historical_input_external_entries
            WHERE organization=? AND source_system=?
              AND (external_race_id=? OR internal_race_id=?)""",
            (ORG, SOURCE, phase110.external_race_id, phase110.race_id)).fetchall()
        expected = {(phase110.external_race_id, item.external_entry_id,
                     phase110.race_id, item.horse_id) for item in phase110.entries}
        if any(row not in expected for row in current):
            raise NARProductionMappingError("extra or conflicting forward/reverse target V010 entry")
        present = {external for _, external, _, _ in current}
        for entry in phase110.entries:
            collisions = c.execute("""SELECT external_race_id,external_entry_id,race_entry_id
                FROM historical_input_external_entries
                WHERE organization=? AND source_system=?
                  AND (external_entry_id=? OR race_entry_id=?)""",
                (ORG, SOURCE, entry.external_entry_id, entry.horse_id)).fetchall()
            if any(row != (phase110.external_race_id, entry.external_entry_id, entry.horse_id)
                   for row in collisions):
                raise NARProductionMappingError("V010 entry forward/reverse conflict")
            if entry.external_entry_id not in present:
                c.execute("""INSERT INTO historical_input_external_entries
                    (organization,source_system,external_race_id,external_entry_id,
                     internal_race_id,race_entry_id) VALUES (?,?,?,?,?,?)""",
                    (ORG, SOURCE, phase110.external_race_id, entry.external_entry_id,
                     phase110.race_id, entry.horse_id))
        self._verify_v010(phase110.external_race_id, phase110.race_id,
                          tuple((item.external_entry_id, item.horse_id) for item in phase110.entries))

    def _verify_v010(self, external_race_id, internal_race_id, entries) -> None:
        c = self._connection
        if c.execute("""SELECT organization,source_system
            FROM historical_input_source_identities WHERE organization=? AND source_system=?""",
            (ORG, SOURCE)).fetchone() != (ORG, SOURCE):
            raise NARProductionMappingError("V010 source identity missing")
        if c.execute("""SELECT internal_race_id FROM historical_input_external_races
            WHERE organization=? AND source_system=? AND external_race_id=?""",
            (ORG, SOURCE, external_race_id)).fetchone() != (internal_race_id,):
            raise NARProductionMappingError("V010 race mapping drift")
        rows = c.execute("""SELECT external_race_id,external_entry_id,internal_race_id,race_entry_id
            FROM historical_input_external_entries
            WHERE organization=? AND source_system=?
              AND (external_race_id=? OR internal_race_id=?)""",
            (ORG, SOURCE, external_race_id, internal_race_id)).fetchall()
        if sorted(rows) != sorted((external_race_id, external, internal_race_id, internal)
                                  for external, internal in entries):
            raise NARProductionMappingError("V010 complete forward/reverse entry mapping drift")

    def _insert_receipt(self, receipt: NARProductionMappingReceiptV1,
                        *, _publication_marker=None) -> None:
        if _publication_marker is not _PHASE109_PUBLICATION_MARKER:
            raise NARProductionMappingError("Phase109 receipt requires controlled publication")
        if type(receipt) is not NARProductionMappingReceiptV1:
            raise NARProductionMappingError("exact Phase109 receipt required")
        c = self._connection
        c.execute("""INSERT INTO nar_production_mapping_receipts
            (receipt_id,phase110_receipt_id,organization,source_system,
             external_race_id,internal_race_id,phase110_population_sha256,
             phase110_population_count,phase110_issued_at,phase111_declaration_id,
             phase111_receipt_id,phase111_capture_id,response_sha256,observed_at,
             prediction_cutoff,mapping_population_sha256,mapping_population_count,
             issued_at,receipt_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (receipt.receipt_id, receipt.phase110_receipt_id, ORG, SOURCE,
             receipt.external_race_id, receipt.internal_race_id,
             receipt.phase110_population_sha256, receipt.phase110_population_count,
             receipt.phase110_issued_at.isoformat(), receipt.phase111_declaration_id,
             receipt.phase111_receipt_id, receipt.phase111_capture_id,
             receipt.response_sha256, receipt.observed_at.isoformat(),
             receipt.prediction_cutoff.isoformat(), receipt.mapping_population_sha256,
             len(receipt.entries), receipt.issued_at.isoformat(),
             _canonical_json(receipt.payload())))
        for entry in receipt.entries:
            c.execute("""INSERT INTO nar_production_mapping_entries
                (receipt_id,phase110_receipt_id,organization,source_system,
                 external_race_id,external_entry_id,internal_race_id,race_entry_id,horse_no)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (receipt.receipt_id, receipt.phase110_receipt_id, ORG, SOURCE,
                 receipt.external_race_id, entry.external_entry_id,
                 receipt.internal_race_id, entry.race_entry_id, entry.horse_no))

    def load_receipt(self, *, receipt_id: str) -> NARProductionMappingReceiptV1:
        c = self._connection
        require_phase110_schema(c)
        require_phase109_schema(c)
        row = c.execute("SELECT * FROM nar_production_mapping_receipts WHERE receipt_id=?",
                        (receipt_id,)).fetchone()
        if row is None:
            raise NARProductionMappingError("Phase109 receipt not found")
        receipt = parse_mapping_receipt(row[-1], receipt_id)
        expected = (receipt.receipt_id, receipt.phase110_receipt_id, ORG, SOURCE,
            receipt.external_race_id, receipt.internal_race_id,
            receipt.phase110_population_sha256, receipt.phase110_population_count,
            receipt.phase110_issued_at.isoformat(), receipt.phase111_declaration_id,
            receipt.phase111_receipt_id, receipt.phase111_capture_id,
            receipt.response_sha256, receipt.observed_at.isoformat(),
            receipt.prediction_cutoff.isoformat(), receipt.mapping_population_sha256,
            len(receipt.entries), receipt.issued_at.isoformat(),
            _canonical_json(receipt.payload()))
        if row != expected:
            raise NARProductionMappingError("Phase109 SQL projection differs")
        rows = c.execute("""SELECT external_entry_id,race_entry_id,horse_no
            FROM nar_production_mapping_entries WHERE receipt_id=? ORDER BY horse_no""",
            (receipt_id,)).fetchall()
        if rows != [(e.external_entry_id, e.race_entry_id, e.horse_no)
                    for e in receipt.entries]:
            raise NARProductionMappingError("Phase109 entry projection differs")
        phase110 = self._phase110.load_receipt(receipt_id=receipt.phase110_receipt_id)
        if receipt_from_phase110(source=phase110, issued_at=receipt.issued_at) != receipt:
            raise NARProductionMappingError("Phase109/110 complete population differs")
        self._verify_v010(receipt.external_race_id, receipt.internal_race_id,
                          tuple((e.external_entry_id, e.race_entry_id) for e in receipt.entries))
        return receipt
