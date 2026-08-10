from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import inspect
import sqlite3
import unittest

import scripts.simulation.repositories.sqlite_nar_official_response_capture_repository as repository_module
from scripts.simulation.nar_official_response_capture import (
    NAROfficialResponseCapture,
    NAROfficialResponseCaptureMissingError,
)
from scripts.simulation.nar_official_response_capture_migration_runner import apply_capture_schema_migrations
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import (
    SQLiteNAROfficialResponseCaptureRepository,
)


UTC = timezone.utc
REQUESTED = datetime(2026, 8, 10, 1, 2, 3, 4, tzinfo=UTC)
OBSERVED = REQUESTED + timedelta(seconds=1)
STORED = OBSERVED + timedelta(seconds=1)
URL = "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=19&k_raceDate=2026%2F07%2F04&k_raceNo=11"
BODY = b"<html>capture</html>"


def _capture(**changes: object) -> NAROfficialResponseCapture:
    values: dict[str, object] = {
        "canonical_source_url": URL, "response_body": BODY, "charset": "utf-8", "requested_at": REQUESTED,
        "observed_at": OBSERVED, "stored_at": STORED, "http_status": 200, "content_length": len(BODY),
    }
    values.update(changes)
    return NAROfficialResponseCapture(**values)  # type: ignore[arg-type]


class SQLiteCaptureRepositoryTests(unittest.TestCase):
    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        apply_capture_schema_migrations(connection)
        return connection

    def _repository(self) -> tuple[sqlite3.Connection, SQLiteNAROfficialResponseCaptureRepository]:
        connection = self._connection()
        return connection, SQLiteNAROfficialResponseCaptureRepository(connection=connection)

    def test_public_connection_injection_and_no_forbidden_ownership(self) -> None:
        self.assertEqual(
            {name for name in vars(repository_module) if not name.startswith("_")},
            {"SQLiteNAROfficialResponseCaptureRepository"},
        )
        self.assertEqual(tuple(inspect.signature(SQLiteNAROfficialResponseCaptureRepository).parameters), ("connection",))
        connection, repository = self._repository()
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        with self.assertRaises(RepositoryValidationError):
            SQLiteNAROfficialResponseCaptureRepository(connection=object())  # type: ignore[arg-type]
        source = inspect.getsource(repository_module)
        for forbidden in ("ATTACH", "requests", "httpx", "urllib.request", "socket", "pathlib", "open(", "datetime.now", "datetime.today"):
            self.assertNotIn(forbidden, source)
        self.assertIsInstance(repository, SQLiteNAROfficialResponseCaptureRepository)

    def test_save_load_idempotency_dedup_and_exact_evidence(self) -> None:
        connection, repository = self._repository()
        first = _capture()
        repository.save_capture(capture=first)
        self.assertEqual(repository.load_capture(capture_id=first.capture_id), first)
        self.assertEqual(
            repository.load_supplied_response_for_evidence(
                canonical_source_url=first.canonical_source_url, response_sha256=first.response_sha256,
                observed_at=first.observed_at,
            ).response_body,
            BODY,
        )
        repository.save_capture(capture=first)
        second = _capture(observed_at=OBSERVED + timedelta(seconds=5), stored_at=STORED + timedelta(seconds=5))
        repository.save_capture(capture=second)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM nar_official_response_bodies").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM nar_official_response_captures").fetchone()[0], 2)
        self.assertFalse(connection.in_transaction)

    def test_missing_and_invalid_caller_inputs_fail_closed(self) -> None:
        _connection, repository = self._repository()
        value = _capture()
        self.assertIsNone(repository.load_capture(capture_id=value.capture_id))
        with self.assertRaises(RepositoryValidationError):
            repository.load_capture(capture_id="bad")
        with self.assertRaises(NAROfficialResponseCaptureMissingError):
            repository.load_supplied_response_for_evidence(
                canonical_source_url=value.canonical_source_url, response_sha256=value.response_sha256,
                observed_at=value.observed_at,
            )
        with self.assertRaises(RepositoryValidationError):
            repository.save_capture(capture=object())  # type: ignore[arg-type]

    def test_conflict_and_atomic_rollback_after_late_failure(self) -> None:
        connection, repository = self._repository()
        first = _capture()
        repository.save_capture(capture=first)
        conflicting = _capture(content_type="text/html")
        with self.assertRaises(RepositoryConflictError):
            repository.save_capture(capture=conflicting)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM nar_official_response_captures").fetchone()[0], 1)
        bad = _capture(response_body=b"<html>new body</html>", content_length=21)
        connection.execute("DROP INDEX ux_nar_official_response_captures_evidence")
        connection.execute("CREATE TRIGGER late_failure BEFORE INSERT ON nar_official_response_captures BEGIN SELECT RAISE(ABORT, 'late'); END")
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.save_capture(capture=bad)
        self.assertIsNone(
            connection.execute("SELECT 1 FROM nar_official_response_bodies WHERE response_sha256=?", (bad.response_sha256,)).fetchone(),
        )
        self.assertFalse(connection.in_transaction)

    def test_persisted_corruption_is_not_repaired(self) -> None:
        connection, repository = self._repository()
        value = _capture()
        repository.save_capture(capture=value)
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute("UPDATE nar_official_response_bodies SET response_body=?,byte_length=? WHERE response_sha256=?", (b"<html>tampered</html>", 21, value.response_sha256))
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_capture(capture_id=value.capture_id)
        connection.execute("PRAGMA foreign_keys=ON")

    def test_missing_body_and_metadata_corruption_fail_closed(self) -> None:
        connection, repository = self._repository()
        value = _capture()
        repository.save_capture(capture=value)
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("DELETE FROM nar_official_response_bodies WHERE response_sha256=?", (value.response_sha256,))
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_supplied_response_for_evidence(
                canonical_source_url=value.canonical_source_url, response_sha256=value.response_sha256,
                observed_at=value.observed_at,
            )
        connection.execute("PRAGMA foreign_keys=ON")
        connection, repository = self._repository()
        value = _capture()
        repository.save_capture(capture=value)
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute("UPDATE nar_official_response_captures SET content_length=0 WHERE capture_id=?", (value.capture_id,))
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_capture(capture_id=value.capture_id)

    def test_active_transaction_is_rejected_and_no_global_schema_is_needed(self) -> None:
        connection, repository = self._repository()
        connection.execute("BEGIN")
        with self.assertRaises(RepositoryValidationError):
            repository.save_capture(capture=_capture())
        connection.rollback()
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertNotIn("races", names)
        self.assertNotIn("historical_input_snapshots", names)
        self.assertEqual(hashlib.sha256(BODY).hexdigest(), _capture().response_sha256)
