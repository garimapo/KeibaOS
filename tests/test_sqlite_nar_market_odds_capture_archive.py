from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import inspect
import sqlite3
import unittest
from unittest.mock import patch

from scripts.simulation.nar_market_odds_capture import (
    NARMarketOddsCaptureArchive,
    NARMarketOddsPageKind,
    NARMarketOddsResponseCapture,
    build_nar_market_odds_request_identity,
)
from scripts.simulation.nar_market_odds_capture_archive_migration import (
    apply_nar_market_odds_capture_archive_migrations,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.sqlite_nar_market_odds_capture_archive import (
    SQLiteNARMarketOddsCaptureArchive,
)


T0 = datetime(2026, 9, 10, 3, 4, 5, 100001, tzinfo=timezone.utc)


def make_capture(
    *,
    kind: NARMarketOddsPageKind = NARMarketOddsPageKind.ODDS_TAN_FUKU,
    baba_code: str = "11",
    race_no: int = 7,
    body: bytes = "地方競馬\r\nオッズ  \r\n".encode("utf-8"),
    requested_at: datetime = T0,
    observed_at: datetime = T0 + timedelta(microseconds=1),
    captured_at: datetime = T0 + timedelta(microseconds=2),
    content_type: str | None = "text/html; charset=UTF-8",
    content_encoding: str | None = None,
    etag: str | None = None,
    content_length: int | None = None,
) -> NARMarketOddsResponseCapture:
    request = build_nar_market_odds_request_identity(
        page_kind=kind,
        baba_code=baba_code,
        race_date=date(2026, 9, 10),
        race_no=race_no,
    )
    return NARMarketOddsResponseCapture(
        request_identity=request,
        effective_url=request.canonical_request_url,
        response_body=body,
        charset="utf-8",
        requested_at=requested_at,
        observed_at=observed_at,
        captured_at=captured_at,
        http_status=200,
        content_type=content_type,
        content_encoding=content_encoding,
        etag=etag,
        content_length=content_length,
    )


class SQLiteNARMarketOddsCaptureArchiveTests(unittest.TestCase):
    def repository(self) -> tuple[sqlite3.Connection, SQLiteNARMarketOddsCaptureArchive]:
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        apply_nar_market_odds_capture_archive_migrations(connection)
        return connection, SQLiteNARMarketOddsCaptureArchive(connection=connection)

    def test_exact_connection_and_constructor_transaction_gates(self) -> None:
        with self.assertRaises(RepositoryValidationError):
            SQLiteNARMarketOddsCaptureArchive(connection=object())  # type: ignore[arg-type]
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        apply_nar_market_odds_capture_archive_migrations(connection)
        connection.execute("BEGIN")
        with self.assertRaises(RepositoryValidationError):
            SQLiteNARMarketOddsCaptureArchive(connection=connection)
        connection.rollback()

    def test_exact_save_load_roundtrip_preserves_body_and_metadata(self) -> None:
        connection, repository = self.repository()
        capture = make_capture(content_encoding="identity", etag='"exact"')
        archive: NARMarketOddsCaptureArchive = repository
        archive.save_capture(capture=capture)
        loaded = archive.load_capture(capture_id=capture.capture_id)
        self.assertEqual(loaded, capture)
        self.assertIsNot(loaded, capture)
        stored = connection.execute(
            "SELECT response_body,byte_length FROM nar_market_odds_response_bodies"
        ).fetchone()
        self.assertEqual(stored, (capture.response_body, len(capture.response_body)))
        self.assertEqual(hashlib.sha256(stored[0]).hexdigest(), capture.response_sha256)

    def test_exact_duplicate_is_idempotent_and_connection_stays_open_clean(self) -> None:
        connection, repository = self.repository()
        capture = make_capture()
        repository.save_capture(capture=capture)
        repository.save_capture(capture=capture)
        self.assertFalse(connection.in_transaction)
        self.assertEqual(
            connection.execute("SELECT count(*) FROM nar_market_odds_response_captures").fetchone(),
            (1,),
        )
        self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))

    def test_same_capture_id_with_different_content_is_conflict(self) -> None:
        _connection, repository = self.repository()
        original = make_capture()
        conflicting = make_capture(body=b"different")
        object.__setattr__(conflicting, "capture_id", original.capture_id)
        repository.save_capture(capture=original)
        with self.assertRaises(RepositoryConflictError):
            repository.save_capture(capture=conflicting)
        self.assertEqual(repository.load_capture(capture_id=original.capture_id), original)

    def test_same_evidence_tuple_with_different_header_identity_is_conflict(self) -> None:
        connection, repository = self.repository()
        original = make_capture(etag='"one"')
        conflict = make_capture(etag='"two"')
        self.assertNotEqual(original.capture_id, conflict.capture_id)
        repository.save_capture(capture=original)
        with self.assertRaises(RepositoryConflictError):
            repository.save_capture(capture=conflict)
        self.assertFalse(connection.in_transaction)

    def test_multiple_observations_share_one_immutable_body(self) -> None:
        connection, repository = self.repository()
        first = make_capture()
        second = make_capture(
            requested_at=T0 + timedelta(seconds=1),
            observed_at=T0 + timedelta(seconds=1, microseconds=1),
            captured_at=T0 + timedelta(seconds=1, microseconds=2),
        )
        repository.save_capture(capture=first)
        repository.save_capture(capture=second)
        self.assertNotEqual(first.capture_id, second.capture_id)
        self.assertEqual(first.response_sha256, second.response_sha256)
        self.assertEqual(
            connection.execute("SELECT count(*) FROM nar_market_odds_response_bodies").fetchone(),
            (1,),
        )
        self.assertEqual(
            connection.execute("SELECT count(*) FROM nar_market_odds_response_captures").fetchone(),
            (2,),
        )

    def test_missing_exact_id_and_malformed_lookup_are_distinct(self) -> None:
        _connection, repository = self.repository()
        self.assertIsNone(
            repository.load_capture(
                capture_id="nar-market-odds-capture-v1:" + "f" * 64,
            )
        )
        for value in ("bad", 1, None):
            with self.subTest(value=value):
                with self.assertRaises(RepositoryValidationError):
                    repository.load_capture(capture_id=value)  # type: ignore[arg-type]

    def test_body_bytes_digest_and_length_corruption_fail_closed(self) -> None:
        mutations = (
            ("response_body", b"corrupt"),
            ("byte_length", 999),
            ("response_sha256", "0" * 64),
        )
        for column, value in mutations:
            with self.subTest(column=column):
                connection = sqlite3.connect(":memory:")
                self.addCleanup(connection.close)
                apply_nar_market_odds_capture_archive_migrations(connection)
                repository = SQLiteNARMarketOddsCaptureArchive(connection=connection)
                capture = make_capture()
                repository.save_capture(capture=capture)
                connection.execute("PRAGMA foreign_keys=OFF")
                connection.execute("PRAGMA ignore_check_constraints=ON")
                connection.execute(
                    f"UPDATE nar_market_odds_response_bodies SET {column}=? "
                    "WHERE response_sha256=?",
                    (value, capture.response_sha256),
                )
                connection.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    repository.load_capture(capture_id=capture.capture_id)

    def test_semantic_capture_row_corruption_fails_closed(self) -> None:
        for column, value in (
            ("page_kind", "wrong"),
            ("request_identity_sha256", "1" * 64),
            ("observed_at_utc", "bad"),
            ("organization", "JRA"),
            ("effective_url", "https://example.test/"),
        ):
            with self.subTest(column=column):
                connection = sqlite3.connect(":memory:")
                self.addCleanup(connection.close)
                apply_nar_market_odds_capture_archive_migrations(connection)
                repository = SQLiteNARMarketOddsCaptureArchive(connection=connection)
                capture = make_capture()
                repository.save_capture(capture=capture)
                connection.execute("PRAGMA ignore_check_constraints=ON")
                connection.execute(
                    f"UPDATE nar_market_odds_response_captures SET {column}=? WHERE capture_id=?",
                    (value, capture.capture_id),
                )
                connection.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    repository.load_capture(capture_id=capture.capture_id)

    def test_missing_body_is_corruption_and_save_never_repairs_it(self) -> None:
        connection, repository = self.repository()
        capture = make_capture()
        repository.save_capture(capture=capture)
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute(
            "DELETE FROM nar_market_odds_response_bodies WHERE response_sha256=?",
            (capture.response_sha256,),
        )
        connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.load_capture(capture_id=capture.capture_id)
        with self.assertRaises(RepositoryDataIntegrityError):
            repository.save_capture(capture=capture)
        self.assertIsNone(
            connection.execute(
                "SELECT 1 FROM nar_market_odds_response_bodies WHERE response_sha256=?",
                (capture.response_sha256,),
            ).fetchone()
        )

    def test_failed_publication_rolls_back_body_and_capture(self) -> None:
        connection, repository = self.repository()
        capture = make_capture()
        with patch.object(
            SQLiteNARMarketOddsCaptureArchive,
            "_require_evidence_unique",
            side_effect=RuntimeError("publication failed"),
        ):
            with self.assertRaisesRegex(RuntimeError, "publication failed"):
                repository.save_capture(capture=capture)
        self.assertFalse(connection.in_transaction)
        self.assertEqual(
            connection.execute("SELECT count(*) FROM nar_market_odds_response_bodies").fetchone(),
            (0,),
        )
        self.assertEqual(
            connection.execute("SELECT count(*) FROM nar_market_odds_response_captures").fetchone(),
            (0,),
        )

    def test_active_caller_transaction_and_invalid_capture_are_rejected(self) -> None:
        connection, repository = self.repository()
        with self.assertRaises(RepositoryValidationError):
            repository.save_capture(capture=object())  # type: ignore[arg-type]
        connection.execute("BEGIN")
        with self.assertRaises(RepositoryValidationError):
            repository.save_capture(capture=make_capture())
        connection.rollback()

    def test_no_latest_mutation_repair_or_selection_api_exists(self) -> None:
        _connection, repository = self.repository()
        for name in (
            "load_latest",
            "load_closest",
            "find_by_date",
            "list_captures",
            "update_capture",
            "delete_capture",
            "repair",
            "load_before_cutoff",
        ):
            self.assertFalse(hasattr(repository, name), name)

    def test_static_repository_boundary_is_raw_only_and_insert_only(self) -> None:
        source = inspect.getsource(SQLiteNARMarketOddsCaptureArchive)
        for forbidden in (
            "INSERT OR REPLACE",
            "REPLACE INTO",
            "UPDATE nar_market_odds",
            "DELETE FROM nar_market_odds",
            "requests",
            "urllib.request",
            "datetime.now",
            "datetime.utcnow",
            "random",
            "uuid",
            "ranking_probability",
            "ValueEngine",
            "BetGenerator",
            "latest",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
