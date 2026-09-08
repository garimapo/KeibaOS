from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import inspect
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from scripts.simulation.nar_daily_target_evidence_archive_migration import (
    apply_nar_daily_target_evidence_archive_migrations,
)
from scripts.simulation.nar_historical_daily_target_bootstrap import (
    NARMonthlyConveneInfoBootstrapEvidence,
)
from scripts.simulation.nar_historical_daily_target_bootstrap_capture import (
    NARMonthlyConveneInfoBootstrapPageKind,
    NARMonthlyConveneInfoBootstrapSupplierCapture,
)
from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetCaptureArchive,
    NARHistoricalDailyTargetPageKind,
    NARHistoricalDailyTargetRequestIdentity,
    NARHistoricalDailyTargetResponseCapture,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.sqlite_nar_daily_target_evidence_archive import (
    SQLiteNARDailyTargetEvidenceArchive,
)


T0 = datetime(2026, 9, 8, 1, 2, 3, 123456, tzinfo=timezone.utc)
SUPPLIER_URLS = {
    NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME: "https://www.keiba.go.jp/",
    NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT: (
        "https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"
    ),
    NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT: (
        "https://www.keiba.go.jp/KeibaWeb/resources/js/monthltconveninfo.js?t=20260130_1"
    ),
}
SUPPLIER_TYPES = {
    NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME: "text/html",
    NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT: "text/html; charset=UTF-8",
    NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT: "application/javascript; charset=UTF-8",
}


def supplier_capture(
    kind: NARMonthlyConveneInfoBootstrapPageKind,
    *,
    body: bytes | None = None,
    requested_at: datetime = T0,
    observed_at: datetime = T0 + timedelta(microseconds=1),
    stored_at: datetime = T0 + timedelta(microseconds=2),
    content_encoding: str | None = "identity",
    content_length: int | None = None,
) -> NARMonthlyConveneInfoBootstrapSupplierCapture:
    value = body if body is not None else f"<{kind.value}>\r\n\tvalue \t \r\n".encode()
    return NARMonthlyConveneInfoBootstrapSupplierCapture(
        page_kind=kind,
        canonical_request_url=SUPPLIER_URLS[kind],
        effective_url=SUPPLIER_URLS[kind],
        response_body=value,
        charset="utf-8",
        requested_at=requested_at,
        observed_at=observed_at,
        stored_at=stored_at,
        http_status=200,
        content_type=SUPPLIER_TYPES[kind],
        content_encoding=content_encoding,
        content_length=content_length,
    )


def daily_capture(
    kind: NARHistoricalDailyTargetPageKind,
    *,
    body: bytes | None = None,
    requested_at: datetime = T0,
    observed_at: datetime = T0 + timedelta(microseconds=1),
    stored_at: datetime = T0 + timedelta(microseconds=2),
    content_type: str | None = "text/html; charset=UTF-8",
    content_encoding: str | None = None,
    http_date: str | None = None,
    etag: str | None = None,
    last_modified: str | None = None,
    content_length: int | None = None,
) -> NARHistoricalDailyTargetResponseCapture:
    if kind is NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO:
        raw = b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2025&k_month=1"
        resolved = "https://www.keiba.go.jp" + raw.decode()
    else:
        raw = b"/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&amp;k_babaCode=11"
        resolved = (
            "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?"
            "k_raceDate=2025%2F01%2F01&k_babaCode=11"
        )
    request = NARHistoricalDailyTargetRequestIdentity(
        page_kind=kind,
        official_supplied_request_material=raw,
        resolved_request_url=resolved,
        supplier_evidence_identity="supplier-evidence-v1:exact",
    )
    value = body if body is not None else f"<{kind.value}>地方競馬\r\nrow \t \r\n".encode("utf-8")
    return NARHistoricalDailyTargetResponseCapture(
        request_identity=request,
        response_body=value,
        charset="utf-8",
        requested_at=requested_at,
        observed_at=observed_at,
        stored_at=stored_at,
        http_status=200,
        content_type=content_type,
        content_encoding=content_encoding,
        http_date=http_date,
        etag=etag,
        last_modified=last_modified,
        content_length=content_length,
    )


class SQLiteNARDailyTargetEvidenceArchiveTests(unittest.TestCase):
    def repository(self) -> tuple[sqlite3.Connection, SQLiteNARDailyTargetEvidenceArchive]:
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        apply_nar_daily_target_evidence_archive_migrations(connection)
        return connection, SQLiteNARDailyTargetEvidenceArchive(connection=connection)

    def test_all_three_supplier_kinds_round_trip_and_reconstruct_aggregate(self) -> None:
        _connection, repository = self.repository()
        captures = tuple(supplier_capture(kind) for kind in NARMonthlyConveneInfoBootstrapPageKind)
        for capture in captures:
            repository.save_supplier_capture(capture=capture)
            self.assertEqual(repository.load_supplier_capture(capture_id=capture.capture_id), capture)
        aggregate = NARMonthlyConveneInfoBootstrapEvidence(captures[0], captures[1], captures[2])
        loaded = NARMonthlyConveneInfoBootstrapEvidence(
            repository.load_supplier_capture(capture_id=captures[0].capture_id),  # type: ignore[arg-type]
            repository.load_supplier_capture(capture_id=captures[1].capture_id),  # type: ignore[arg-type]
            repository.load_supplier_capture(capture_id=captures[2].capture_id),  # type: ignore[arg-type]
        )
        self.assertEqual(loaded, aggregate)

    def test_monthly_and_race_list_round_trip_full_request_identity(self) -> None:
        _connection, repository = self.repository()
        for kind in NARHistoricalDailyTargetPageKind:
            capture = daily_capture(
                kind,
                content_encoding="identity",
                http_date="Tue, 08 Sep 2026 01:02:03 GMT",
                etag='"exact"',
                last_modified="Tue, 01 Sep 2026 00:00:00 GMT",
            )
            repository.save_capture(capture=capture)
            loaded = repository.load_capture(capture_id=capture.capture_id)
            self.assertEqual(loaded, capture)
            self.assertEqual(loaded.request_identity, capture.request_identity)  # type: ignore[union-attr]

    def test_blob_bytes_crlf_whitespace_and_utf8_are_exact(self) -> None:
        connection, repository = self.repository()
        body = "地方\r\nspace  \r\n \tindent\r\n".encode("utf-8")
        capture = daily_capture(NARHistoricalDailyTargetPageKind.RACE_LIST, body=body)
        repository.save_capture(capture=capture)
        stored = connection.execute(
            "SELECT response_body,byte_length FROM nar_daily_target_evidence_bodies WHERE response_sha256=?",
            (capture.response_sha256,),
        ).fetchone()
        self.assertEqual(stored, (body, len(body)))
        self.assertEqual(repository.load_capture(capture_id=capture.capture_id).response_body, body)  # type: ignore[union-attr]

    def test_utc_microseconds_and_nullable_metadata_round_trip(self) -> None:
        _connection, repository = self.repository()
        offset = timezone(timedelta(hours=9))
        capture = daily_capture(
            NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO,
            requested_at=datetime(2026, 9, 8, 10, 2, 3, 100001, tzinfo=offset),
            observed_at=datetime(2026, 9, 8, 10, 2, 3, 100002, tzinfo=offset),
            stored_at=datetime(2026, 9, 8, 10, 2, 3, 100003, tzinfo=offset),
            content_type=None,
            content_encoding=None,
            http_date=None,
            etag=None,
            last_modified=None,
            content_length=None,
        )
        repository.save_capture(capture=capture)
        loaded = repository.load_capture(capture_id=capture.capture_id)
        self.assertEqual(loaded, capture)
        self.assertEqual(loaded.requested_at.microsecond, 100001)  # type: ignore[union-attr]
        self.assertEqual(loaded.requested_at.utcoffset(), timedelta(0))  # type: ignore[union-attr]

    def test_exact_duplicate_is_idempotent_for_both_families(self) -> None:
        connection, repository = self.repository()
        supplier = supplier_capture(NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME)
        daily = daily_capture(NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO)
        for save, capture in (
            (repository.save_supplier_capture, supplier),
            (repository.save_capture, daily),
        ):
            save(capture=capture)
            save(capture=capture)
        self.assertEqual(connection.execute("SELECT count(*) FROM nar_daily_target_supplier_captures").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT count(*) FROM nar_daily_target_response_captures").fetchone()[0], 1)

    def test_same_identity_conflicting_body_or_metadata_is_rejected(self) -> None:
        _connection, repository = self.repository()
        original = supplier_capture(NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME)
        repository.save_supplier_capture(capture=original)
        other_body = supplier_capture(
            NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME,
            body=b"different exact body",
        )
        object.__setattr__(other_body, "capture_id", original.capture_id)
        with self.assertRaises(RepositoryConflictError):
            repository.save_supplier_capture(capture=other_body)
        metadata = supplier_capture(
            NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME,
            stored_at=T0 + timedelta(microseconds=50),
        )
        self.assertEqual(metadata.capture_id, original.capture_id)
        with self.assertRaises(RepositoryConflictError):
            repository.save_supplier_capture(capture=metadata)
        self.assertEqual(repository.load_supplier_capture(capture_id=original.capture_id), original)

    def test_conflicting_daily_metadata_is_rejected(self) -> None:
        _connection, repository = self.repository()
        original = daily_capture(NARHistoricalDailyTargetPageKind.RACE_LIST)
        conflict = daily_capture(
            NARHistoricalDailyTargetPageKind.RACE_LIST,
            stored_at=T0 + timedelta(microseconds=20),
        )
        self.assertEqual(conflict.capture_id, original.capture_id)
        repository.save_capture(capture=original)
        with self.assertRaises(RepositoryConflictError):
            repository.save_capture(capture=conflict)

    def test_stored_body_digest_corruption_fails_closed(self) -> None:
        connection, repository = self.repository()
        capture = daily_capture(NARHistoricalDailyTargetPageKind.RACE_LIST)
        repository.save_capture(capture=capture)
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            "UPDATE nar_daily_target_evidence_bodies SET response_body=?,byte_length=? WHERE response_sha256=?",
            (b"corrupt", 7, capture.response_sha256),
        )
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_capture(capture_id=capture.capture_id)

    def test_stored_capture_id_and_metadata_corruption_fail_closed(self) -> None:
        connection, repository = self.repository()
        capture = supplier_capture(NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT)
        repository.save_supplier_capture(capture=capture)
        bad_id = "nar-monthly-bootstrap-capture-v1:" + "0" * 64
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            "UPDATE nar_daily_target_supplier_captures SET capture_id=? WHERE capture_id=?",
            (bad_id, capture.capture_id),
        )
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_supplier_capture(capture_id=bad_id)

        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        apply_nar_daily_target_evidence_archive_migrations(connection)
        repository = SQLiteNARDailyTargetEvidenceArchive(connection=connection)
        daily = daily_capture(NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO)
        repository.save_capture(capture=daily)
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            "UPDATE nar_daily_target_response_captures SET request_identity_sha256=? WHERE capture_id=?",
            ("1" * 64, daily.capture_id),
        )
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_capture(capture_id=daily.capture_id)

    def test_malformed_timestamp_and_invalid_page_kind_fail_closed(self) -> None:
        for column, value in (("observed_at_utc", "bad"), ("page_kind", "unknown")):
            with self.subTest(column=column):
                connection = sqlite3.connect(":memory:")
                self.addCleanup(connection.close)
                apply_nar_daily_target_evidence_archive_migrations(connection)
                repository = SQLiteNARDailyTargetEvidenceArchive(connection=connection)
                capture = daily_capture(NARHistoricalDailyTargetPageKind.RACE_LIST)
                repository.save_capture(capture=capture)
                connection.execute("PRAGMA ignore_check_constraints=ON")
                connection.execute(
                    f"UPDATE nar_daily_target_response_captures SET {column}=? WHERE capture_id=?",
                    (value, capture.capture_id),
                )
                connection.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    repository.load_capture(capture_id=capture.capture_id)

    def test_missing_body_is_corruption_and_save_does_not_repair(self) -> None:
        connection, repository = self.repository()
        capture = daily_capture(NARHistoricalDailyTargetPageKind.RACE_LIST)
        repository.save_capture(capture=capture)
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute(
            "DELETE FROM nar_daily_target_evidence_bodies WHERE response_sha256=?",
            (capture.response_sha256,),
        )
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_capture(capture_id=capture.capture_id)
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.save_capture(capture=capture)
        self.assertIsNone(
            connection.execute(
                "SELECT 1 FROM nar_daily_target_evidence_bodies WHERE response_sha256=?",
                (capture.response_sha256,),
            ).fetchone()
        )

    def test_missing_exact_id_returns_none_and_never_falls_back(self) -> None:
        connection, repository = self.repository()
        earlier = daily_capture(NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO)
        later = daily_capture(
            NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO,
            observed_at=T0 + timedelta(hours=1),
            stored_at=T0 + timedelta(hours=1, microseconds=1),
        )
        repository.save_capture(capture=earlier)
        repository.save_capture(capture=later)
        self.assertIsNone(repository.load_capture(capture_id="nar-daily-target-capture-v1:" + "f" * 64))
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(
            "UPDATE nar_daily_target_response_captures SET observed_at_utc='bad' WHERE capture_id=?",
            (later.capture_id,),
        )
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_capture(capture_id=later.capture_id)
        self.assertEqual(repository.load_capture(capture_id=earlier.capture_id), earlier)

    def test_no_latest_list_or_target_set_api_exists(self) -> None:
        _connection, repository = self.repository()
        for name in ("load_latest", "list_captures", "find_by_date", "build_target_set", "load_evidence"):
            self.assertFalse(hasattr(repository, name), name)

    def test_read_only_connection_load_executes_no_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "archive.sqlite3"
            connection = sqlite3.connect(path)
            apply_nar_daily_target_evidence_archive_migrations(connection)
            repository = SQLiteNARDailyTargetEvidenceArchive(connection=connection)
            capture = daily_capture(NARHistoricalDailyTargetPageKind.RACE_LIST)
            repository.save_capture(capture=capture)
            connection.close()

            reader = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
            statements: list[str] = []
            reader.set_trace_callback(statements.append)
            read_repository = SQLiteNARDailyTargetEvidenceArchive(connection=reader)
            before = reader.total_changes
            self.assertEqual(read_repository.load_capture(capture_id=capture.capture_id), capture)
            self.assertEqual(reader.total_changes, before)
            reader.close()
            mutations = ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER")
            self.assertFalse(any(statement.lstrip().upper().startswith(mutations) for statement in statements))

    def test_single_save_rolls_back_body_and_metadata_together(self) -> None:
        connection, repository = self.repository()
        capture = supplier_capture(NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME)
        with patch.object(
            SQLiteNARDailyTargetEvidenceArchive,
            "_insert_supplier",
            side_effect=RuntimeError("publication failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "publication failed"):
                repository.save_supplier_capture(capture=capture)
        self.assertFalse(connection.in_transaction)
        self.assertEqual(connection.execute("SELECT count(*) FROM nar_daily_target_evidence_bodies").fetchone()[0], 0)
        self.assertEqual(connection.execute("SELECT count(*) FROM nar_daily_target_supplier_captures").fetchone()[0], 0)

    def test_insertion_order_does_not_affect_exact_load(self) -> None:
        first = daily_capture(NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO)
        second = daily_capture(NARHistoricalDailyTargetPageKind.RACE_LIST)
        results = []
        for order in ((first, second), (second, first)):
            _connection, repository = self.repository()
            for capture in order:
                repository.save_capture(capture=capture)
            results.append(tuple(repository.load_capture(capture_id=item.capture_id) for item in (first, second)))
        self.assertEqual(results[0], results[1])

    def test_protocol_shape_and_partial_rows_make_no_completeness_claim(self) -> None:
        connection, repository = self.repository()
        archive: NARHistoricalDailyTargetCaptureArchive = repository
        partial = daily_capture(NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO)
        archive.save_capture(capture=partial)
        self.assertEqual(archive.load_capture(capture_id=partial.capture_id), partial)
        self.assertEqual(connection.execute("SELECT count(*) FROM nar_daily_target_response_captures").fetchone()[0], 1)
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertFalse(any("target_set" in name or "bootstrap_evidence" in name for name in names))

    def test_input_validation_and_active_transaction_are_fail_closed(self) -> None:
        connection, repository = self.repository()
        with self.assertRaises(RepositoryValidationError):
            repository.load_capture(capture_id="bad")
        with self.assertRaises(RepositoryValidationError):
            repository.save_capture(capture=object())  # type: ignore[arg-type]
        connection.execute("BEGIN")
        with self.assertRaises(RepositoryValidationError):
            repository.save_supplier_capture(
                capture=supplier_capture(NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT)
            )
        connection.rollback()

    def test_no_network_clock_mutation_or_settlement_shortcut(self) -> None:
        source = inspect.getsource(SQLiteNARDailyTargetEvidenceArchive)
        for forbidden in (
            "requests",
            "httpx",
            "urllib.request",
            "urlopen",
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "INSERT OR REPLACE",
            "nar_official_response_capture",
            "UPDATE nar_daily_target",
            "DELETE FROM nar_daily_target",
        ):
            self.assertNotIn(forbidden, source)
        constructor = inspect.getsource(SQLiteNARDailyTargetEvidenceArchive.__init__)
        self.assertNotIn("apply_nar_daily", constructor)

    def test_body_digest_is_exact_sha256(self) -> None:
        connection, repository = self.repository()
        capture = supplier_capture(NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT)
        repository.save_supplier_capture(capture=capture)
        digest, body = connection.execute(
            "SELECT response_sha256,response_body FROM nar_daily_target_evidence_bodies"
        ).fetchone()
        self.assertEqual(digest, hashlib.sha256(body).hexdigest())
        self.assertEqual(digest, capture.response_sha256)


if __name__ == "__main__":
    unittest.main()
