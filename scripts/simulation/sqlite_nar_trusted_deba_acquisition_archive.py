"""Append-only Phase111 lineage repository, with a durable exclusive send claim."""
import sqlite3

from scripts.simulation.nar_trusted_deba_acquisition import (
    AcquisitionIntegrityError, NARProspectiveDebaAcquisitionDeclarationV1 as Declaration,
    NARProspectiveDebaSendClaimV1 as Claim, NARProspectiveDebaFailureV1 as Failure,
    NARProspectiveDebaAcquisitionReceiptV1 as Receipt, record_from_bytes,
)
from scripts.simulation.nar_trusted_deba_acquisition_archive_migration import require_nar_trusted_deba_acquisition_archive_schema
from scripts.simulation.repositories.errors import RepositoryConflictError, RepositoryDataIntegrityError, RepositoryValidationError


TABLES = {Declaration: "phase111_declarations", Claim: "phase111_claims",
          Failure: "phase111_failures", Receipt: "phase111_receipts"}

# Trusted composition/API discipline, not cryptographic security or stored content.
_PHASE111_TERMINAL_ISSUANCE_MARKER = object()


class SQLiteNARTrustedDebaAcquisitionArchive:
    def __init__(self, *, connection):
        if type(connection) is not sqlite3.Connection or connection.in_transaction:
            raise RepositoryValidationError("exact connection without active transaction required")
        self._connection = connection
        require_nar_trusted_deba_acquisition_archive_schema(connection)

    def _gate(self):
        require_nar_trusted_deba_acquisition_archive_schema(self._connection)

    def _load(self, record_type, identity):
        self._gate()
        if type(identity) is not str or not identity.startswith("phase111-" + record_type.__name__ + ":"):
            raise RepositoryValidationError("exact record identity required")
        row = self._connection.execute(f"SELECT * FROM {TABLES[record_type]} WHERE identity=?", (identity,)).fetchone()
        if row is None:
            return None
        try:
            if type(row[1]) is not str:
                raise AcquisitionIntegrityError("stored payload must be exact text")
            record = record_from_bytes(record_type, row[1].encode("utf-8"))
            if record.identity != identity or (len(row) > 2 and row[2] != record.declaration_id) or (len(row) > 3 and row[3] != record.claim_id):
                raise AcquisitionIntegrityError("stored identity/ancestry differs")
            self._validate_ancestry(record)
            return record
        except (ValueError, TypeError, KeyError, AttributeError) as error:
            raise RepositoryDataIntegrityError("corrupt Phase111 record") from error

    def load_declaration(self, *, declaration_id):
        return self._load(Declaration, declaration_id)

    def load_claim(self, *, claim_id):
        return self._load(Claim, claim_id)

    def load_receipt(self, *, receipt_id):
        return self._load(Receipt, receipt_id)

    def load_failure(self, *, failure_id):
        return self._load(Failure, failure_id)

    def _validate_ancestry(self, record):
        if type(record) is Declaration:
            return
        declaration = self.load_declaration(declaration_id=record.declaration_id)
        if declaration is None:
            raise AcquisitionIntegrityError("orphan declaration ancestry")
        if type(record) is Claim:
            if not declaration.issued_at <= record.claimed_at <= declaration.prediction_information_cutoff:
                raise AcquisitionIntegrityError("claim outside declaration window")
            return
        claim = self.load_claim(claim_id=record.claim_id)
        if claim is None or claim.declaration_id != declaration.identity:
            raise AcquisitionIntegrityError("claim ancestry differs")
        if type(record) is Receipt:
            if (record.external_race_id != declaration.external_race_id or
                    record.canonical_deba_url != declaration.canonical_deba_url or
                    record.prediction_information_cutoff != declaration.prediction_information_cutoff or
                    record.requested_at < claim.claimed_at):
                raise AcquisitionIntegrityError("receipt ancestry differs")

    def _write(self, record, *, exclusive=False):
        if type(record) not in TABLES:
            raise RepositoryValidationError("unsupported Phase111 authority row")
        if self._connection.in_transaction:
            raise RepositoryValidationError("active caller transaction rejected")
        self._gate()
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._validate_ancestry(record)
            existing = self._load(type(record), record.identity)
            if existing is not None:
                if exclusive or existing != record:
                    raise RepositoryConflictError("authority already consumed/conflicting")
            else:
                values = [record.identity, record.canonical_bytes().decode("utf-8")]
                if type(record) is not Declaration:
                    values.append(record.declaration_id)
                if type(record) in (Receipt, Failure):
                    values.append(record.claim_id)
                placeholders = ",".join("?" for _ in values)
                self._connection.execute(f"INSERT INTO {TABLES[type(record)]} VALUES({placeholders})", values)
                if self._load(type(record), record.identity) != record:
                    raise RepositoryDataIntegrityError("insert exact reload differs")
            self._connection.commit()
        except sqlite3.IntegrityError as error:
            self._connection.rollback()
            raise RepositoryConflictError("immutable/unique authority conflict") from error
        except BaseException:
            self._connection.rollback()
            raise

    def save_declaration(self, *, declaration):
        if type(declaration) is not Declaration:
            raise RepositoryValidationError("exact declaration required")
        self._write(declaration)

    def acquire_claim(self, *, declaration_id, claimed_at):
        claim = Claim(declaration_id, claimed_at)
        self._write(claim, exclusive=True)
        return claim

    def _publish_receipt(self, *, receipt, _issuance_marker=None):
        if _issuance_marker is not _PHASE111_TERMINAL_ISSUANCE_MARKER:
            raise RepositoryValidationError("terminal publication requires controlled current-process issuance")
        if type(receipt) is not Receipt:
            raise RepositoryValidationError("exact receipt required")
        self._write(receipt)

    def _publish_failure(self, *, failure, _issuance_marker=None):
        if _issuance_marker is not _PHASE111_TERMINAL_ISSUANCE_MARKER:
            raise RepositoryValidationError("terminal publication requires controlled current-process issuance")
        if type(failure) is not Failure:
            raise RepositoryValidationError("exact failure required")
        self._write(failure)

    def disposition(self, *, declaration_id):
        """Read-only reconciliation; an incomplete consumed claim stays UNKNOWN."""
        if self.load_declaration(declaration_id=declaration_id) is None:
            raise RepositoryValidationError("declaration missing")
        row = self._connection.execute("SELECT identity FROM phase111_claims WHERE declaration_id=?", (declaration_id,)).fetchone()
        if row is None:
            return "DECLARED_NOT_CLAIMED"
        claim = self.load_claim(claim_id=row[0])
        for record_type in (Receipt, Failure):
            row = self._connection.execute(f"SELECT identity FROM {TABLES[record_type]} WHERE claim_id=?", (claim.identity,)).fetchone()
            if row is not None:
                self._load(record_type, row[0])
                return "RECEIPT_COMPLETE" if record_type is Receipt else "SEND_TERMINAL_FAILURE"
        return "UNKNOWN_SEND_OUTCOME"
