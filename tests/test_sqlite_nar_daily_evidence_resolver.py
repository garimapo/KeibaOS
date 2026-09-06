"""Offline integration tests for exact read-only daily evidence resolution."""

from contextlib import contextmanager, ExitStack
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import ast
import inspect
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from scripts.migrations.runner import apply_migrations
from scripts.simulation import sqlite_nar_daily_evidence_resolver as subject
from scripts.simulation import historical_daily_evidence_resolution as values
from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayTarget, DailyHistoricalReplayTargetSet, DailyHistoricalReplayProviderScope,
    HistoricalDailyProviderIdentity, DailyHistoricalReplayCompletenessEvidence,
    ProviderNativeDispositionEvidenceReference, TargetDiscoveryIncompleteError,
)
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalEntryIdentity, HistoricalExternalRaceIdentity, HistoricalInputProvenance,
    HistoricalInputSnapshot, HistoricalInputSnapshotIdentity, HistoricalRaceEntrySnapshot,
    HistoricalRaceSnapshot, HistoricalSourceIdentity,
)
from scripts.simulation.nar_official_response_capture import NAROfficialResponseCapture
from scripts.simulation.nar_official_response_capture_migration_runner import apply_capture_schema_migrations
from scripts.simulation.repositories.errors import RepositoryDataIntegrityError, RepositoryValidationError
from scripts.simulation.repositories.sqlite_historical_input_snapshot_repository import SQLiteHistoricalInputSnapshotRepository
from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import SQLiteNAROfficialResponseCaptureRepository


_UTC = timezone.utc
_DATE = date(2025, 1, 1)
_START = datetime(2025, 1, 1, 5, tzinfo=_UTC)
_CAPTURED = _START - timedelta(hours=1)
_PREDICTION = _START - timedelta(minutes=30)
_SETTLEMENT = _START + timedelta(hours=3)
_PROVIDER = HistoricalDailyProviderIdentity("NAR", "nar_official")
_NORMAL = "nar-race-list-target-row-v1"
_NON_RUN = "nar-race-list-whole-meeting-cancelled-no-substitute-v1"


def _target(no=1, *, start=_START, kind=_NORMAL, external=None):
    return DailyHistoricalReplayTarget(_PROVIDER, external or f"nar:20250101:10:{no}", start,
        ProviderNativeDispositionEvidenceReference(kind, "daily-test-capture", "a" * 64, f"row:{no}", "b" * 64))


def _targets(*targets):
    return DailyHistoricalReplayTargetSet(_DATE, DailyHistoricalReplayProviderScope((_PROVIDER,)), targets,
        (DailyHistoricalReplayCompletenessEvidence(_PROVIDER, "test-audited-projection", "daily-test-capture",
            "test-request", "c" * 64, datetime(2026, 9, 1, tzinfo=_UTC), None, "test-day-coverage"),))


def _snapshot(no=1, *, captured=_CAPTURED, cutoff=_PREDICTION, start=_START, available=None, observed=None,
              dataset="dataset", external=None, target_date=_DATE):
    external = external or f"nar:20250101:10:{no}"
    source = HistoricalSourceIdentity("NAR", "nar_official", external, None)
    identity = HistoricalInputSnapshotIdentity(dataset, source, captured)
    race_identity = HistoricalExternalRaceIdentity("NAR", "nar_official", external)
    entry_id = no * 10 + 1
    entry = HistoricalRaceEntrySnapshot(entry_id, HistoricalExternalEntryIdentity(race_identity, external + ":entry:1", None),
        1, "Jockey", Decimal("2.5"), 0)
    race = HistoricalRaceSnapshot(target_date, start, "Place", 1200, "dirt", "good", None, None, None)
    observed = captured if observed is None else observed
    def evidence(role):
        return (HistoricalInputEvidenceReference(role, "https://example.test/prediction", "d" * 64, available, observed),)
    provenance = (
        HistoricalInputProvenance("track", "track", "nar", "track-1", None, evidence("track")),
        HistoricalInputProvenance("entry", f"entry/{entry_id}", "nar", "entry-1", entry_id, evidence("entry")),
        HistoricalInputProvenance("odds", f"odds/{entry_id}", "nar", "odds-1", entry_id, evidence("odds_win")),
        HistoricalInputProvenance("jockey", f"jockey/{entry_id}", "nar", "jockey-1", entry_id, evidence("jockey")),
        HistoricalInputProvenance("past_race", f"past_race/{entry_id}/none", "nar", "absence-1", entry_id, evidence("past_race_absence_query")),
    )
    return HistoricalInputSnapshot(identity, no, cutoff, race, (entry,), (), provenance)


def _capture(no=1, *, observed=_SETTLEMENT, requested=None, stored=None, body=b"synthetic bytes: deliberately not settlement HTML", page="RaceMarkTable"):
    return NAROfficialResponseCapture(
        canonical_source_url=f"https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/{page}?k_babaCode=10&k_raceDate=2025%2F01%2F01&k_raceNo={no}",
        response_body=body, charset="utf-8", requested_at=requested or observed - timedelta(seconds=1),
        observed_at=observed, stored_at=stored or observed + timedelta(seconds=1), http_status=200, content_length=len(body))


def _initialize(main, archive, snapshots, captures):
    main.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
    main.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER NOT NULL)")
    main.executemany("INSERT INTO races VALUES(?)", ((n,) for n in range(1, 21)))
    main.executemany("INSERT INTO horses VALUES(?,?)", ((n * 10 + 1, n) for n in range(1, 21)))
    main.commit()
    apply_migrations(main)
    apply_capture_schema_migrations(archive)
    snapshot_repo = SQLiteHistoricalInputSnapshotRepository(connection=main)
    capture_repo = SQLiteNAROfficialResponseCaptureRepository(connection=archive)
    for item in snapshots:
        snapshot_repo.save_snapshot(snapshot=item)
    for item in captures:
        capture_repo.save_capture(capture=item)


@contextmanager
def _databases(snapshots=(), captures=()):
    main, archive = sqlite3.connect(":memory:"), sqlite3.connect(":memory:")
    try:
        _initialize(main, archive, snapshots, captures)
        yield main, archive
    finally:
        main.close()
        archive.close()


def _resolve(main, archive, *, targets=None, cutoff=_SETTLEMENT, dataset="dataset"):
    return subject.resolve_sqlite_nar_daily_evidence(target_set=targets or _targets(_target()), dataset_id=dataset,
        settlement_information_cutoff=cutoff, snapshot_connection=main, capture_connection=archive)


def _time(value):
    return value.astimezone(_UTC).isoformat(timespec="microseconds")


def _unconstrained_copy(connection, table):
    # Corrupt an isolated test database to exercise fail-closed storage detection.
    connection.execute("PRAGMA foreign_keys=OFF")
    if table == "historical_input_snapshots":
        for trigger in ("trg_his_snapshot_entry_mapping_insert", "trg_his_snapshot_entry_mapping_update",
                        "trg_his_snapshot_header_mapping_update", "trg_his_external_entry_referenced_update",
                        "trg_his_external_entry_referenced_delete"):
            connection.execute(f"DROP TRIGGER {trigger}")
    connection.execute(f"CREATE TABLE copy_for_corruption AS SELECT * FROM {table}")
    connection.execute(f"DROP TABLE {table}")
    connection.execute(f"ALTER TABLE copy_for_corruption RENAME TO {table}")
    connection.commit()


class SQLiteDailyResolverTests(unittest.TestCase):
    def test_exact_api_and_latest_then_exact_loader_calls(self):
        self.assertEqual({name for name in vars(subject) if not name.startswith("_")}, {"resolve_sqlite_nar_daily_evidence"})
        signature = inspect.signature(subject.resolve_sqlite_nar_daily_evidence)
        self.assertEqual(tuple(signature.parameters), ("target_set", "dataset_id", "settlement_information_cutoff", "snapshot_connection", "capture_connection"))
        self.assertTrue(all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in signature.parameters.values()))
        snapshot, capture = _snapshot(), _capture()
        order = []
        latest = SQLiteHistoricalInputSnapshotRepository.load_latest_snapshot
        exact = SQLiteHistoricalInputSnapshotRepository.load_snapshot_by_identity
        def latest_spy(repo, **kwargs):
            order.append(("latest", kwargs))
            return latest(repo, **kwargs)
        def exact_spy(repo, **kwargs):
            order.append(("exact", kwargs))
            return exact(repo, **kwargs)
        with _databases((snapshot,), (capture,)) as (main, archive), \
                patch.object(SQLiteHistoricalInputSnapshotRepository, "load_latest_snapshot", latest_spy), \
                patch.object(SQLiteHistoricalInputSnapshotRepository, "load_snapshot_by_identity", exact_spy):
            target = _target()
            result = _resolve(main, archive, targets=_targets(target))
            outcome = result.outcomes[0]
            self.assertEqual(result.day_state.value, "ALL_TARGETS_RESOLVED")
            self.assertIs(outcome.target, target)
            self.assertEqual(outcome.snapshot_identity, snapshot.identity)
            self.assertEqual(outcome.snapshot_content_sha256, snapshot.content_sha256)
            self.assertEqual(outcome.internal_race_id, 1)
            self.assertEqual(outcome.result_capture_reference.capture_id, capture.capture_id)
            self.assertIs(outcome.result_capture_reference, outcome.payout_capture_reference)
        self.assertEqual([item[0] for item in order], ["latest", "exact"])
        self.assertEqual(order[0][1]["information_cutoff"], _START)
        self.assertEqual(order[0][1]["source_identity"], HistoricalExternalRaceIdentity("NAR", "nar_official", "nar:20250101:10:1"))
        self.assertEqual(order[1][1]["identity"], snapshot.identity)

    def test_unique_latest_none_availability_and_inclusive_bound(self):
        older = _snapshot(available=_CAPTURED - timedelta(minutes=1))
        latest = _snapshot(captured=_START, cutoff=_START, available=None)
        for snapshots in ((older, latest), (latest, older)):
            with self.subTest(order=snapshots), _databases(snapshots, (_capture(),)) as (main, archive):
                result = _resolve(main, archive)
                self.assertEqual(result.outcomes[0].snapshot_identity, latest.identity)
                self.assertEqual(result.day_state.value, "ALL_TARGETS_RESOLVED")

    def test_future_captured_or_cutoff_excluded_without_backdating(self):
        future = _START + timedelta(minutes=1)
        cases = (_snapshot(captured=future, cutoff=future, start=future),
                 _snapshot(captured=_PREDICTION, cutoff=future, start=future))
        for snapshot in cases:
            with self.subTest(snapshot=snapshot), _databases((snapshot,), (_capture(),)) as (main, archive):
                result = _resolve(main, archive)
                self.assertEqual(result.outcomes[0].reason_codes, ("SNAPSHOT_AFTER_SELECTION_BOUND",))
                self.assertIsNone(result.outcomes[0].snapshot_identity)
                self.assertEqual(result.day_state.value, "NO_EXECUTABLE_TARGETS")
        with _databases((_snapshot(), *cases), (_capture(),)) as (main, archive):
            self.assertEqual(_resolve(main, archive).outcomes[0].snapshot_identity, _snapshot().identity)

    def test_causal_invalid_domains_reject_known_and_none_variants(self):
        cases = ({"available": _CAPTURED + timedelta(seconds=1)},
                 {"observed": _CAPTURED + timedelta(seconds=1)},
                 {"captured": _PREDICTION + timedelta(seconds=1)},
                 {"cutoff": _START + timedelta(seconds=1)})
        for change in cases:
            with self.subTest(change=change), self.assertRaises(ValueError):
                _snapshot(**change)

    def test_stored_causal_corruption_raises_globally_without_older_fallback(self):
        latest = _snapshot(captured=_PREDICTION, cutoff=_PREDICTION)
        cases = (
            ("UPDATE historical_input_snapshot_provenance_evidence SET available_at_utc=? WHERE snapshot_id=2", (_time(_PREDICTION + timedelta(seconds=1)),)),
            ("UPDATE historical_input_snapshot_provenance_evidence SET observed_at_utc=? WHERE snapshot_id=2", (_time(_PREDICTION + timedelta(seconds=1)),)),
            ("UPDATE historical_input_snapshots SET information_cutoff_utc=? WHERE snapshot_id=2", (_time(_CAPTURED),)),
            ("UPDATE historical_input_snapshot_races SET scheduled_start_at_utc=? WHERE snapshot_id=2", (_time(_CAPTURED),)),
        )
        for sql, params in cases:
            with self.subTest(sql=sql), _databases((_snapshot(), latest), (_capture(),)) as (main, archive):
                main.execute("PRAGMA ignore_check_constraints=ON")
                main.execute(sql, params)
                main.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    _resolve(main, archive)
                self.assertFalse(main.in_transaction)
                self.assertFalse(archive.in_transaction)

    def test_selected_corrupt_digest_no_fallback(self):
        with _databases((_snapshot(), _snapshot(captured=_PREDICTION)), (_capture(),)) as (main, archive):
            main.execute("UPDATE historical_input_snapshots SET content_sha256=? WHERE snapshot_id=2", ("0" * 64,))
            main.commit()
            with self.assertRaises(RepositoryDataIntegrityError):
                _resolve(main, archive)

    def test_duplicate_greatest_snapshot_and_incompatible_uniqueness_fail_globally(self):
        with _databases((_snapshot(),), (_capture(),)) as (main, archive):
            _unconstrained_copy(main, "historical_input_snapshots")
            main.execute("INSERT INTO historical_input_snapshots SELECT * FROM historical_input_snapshots")
            main.commit()
            with patch.object(SQLiteHistoricalInputSnapshotRepository, "load_latest_snapshot", side_effect=AssertionError("must not tie-break")), \
                    self.assertRaises(RepositoryDataIntegrityError):
                _resolve(main, archive)
            with patch.object(SQLiteHistoricalInputSnapshotRepository, "load_latest_snapshot", side_effect=AssertionError("must not tie-break")), \
                    self.assertRaisesRegex(RepositoryDataIntegrityError, "duplicate snapshot identity"):
                subject._prediction(main, SQLiteHistoricalInputSnapshotRepository(connection=main), _target(), "dataset", _DATE)

    def test_loader_metadata_and_exact_disagreements_fail_globally(self):
        for method, returned in (("load_latest_snapshot", None), ("load_snapshot_by_identity", None),
                                 ("load_latest_snapshot", _snapshot(captured=_CAPTURED - timedelta(seconds=1)))):
            with self.subTest(method=method, returned=returned), _databases((_snapshot(),), (_capture(),)) as (main, archive), \
                    patch.object(SQLiteHistoricalInputSnapshotRepository, method, return_value=returned), \
                    self.assertRaises(RepositoryDataIntegrityError):
                _resolve(main, archive)
        with _databases((), (_capture(),)) as (main, archive):
            main.execute("INSERT INTO historical_input_source_identities VALUES('NAR','nar_official')")
            main.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official','nar:20250101:10:1',1)")
            main.commit()
            with patch.object(SQLiteHistoricalInputSnapshotRepository, "load_latest_snapshot", return_value=_snapshot()), \
                    self.assertRaises(RepositoryDataIntegrityError):
                _resolve(main, archive)

    def test_exact_snapshot_digest_compared_even_when_dataclass_equality_matches(self):
        tampered = _snapshot()
        object.__setattr__(tampered, "content_sha256", "0" * 64)
        self.assertEqual(tampered, _snapshot())
        with _databases((_snapshot(),), (_capture(),)) as (main, archive), \
                patch.object(SQLiteHistoricalInputSnapshotRepository, "load_snapshot_by_identity", return_value=tampered), \
                self.assertRaises(RepositoryDataIntegrityError):
            _resolve(main, archive)

    def test_target_date_start_and_external_identity_mismatch_retained(self):
        for snapshot in (_snapshot(start=_START + timedelta(minutes=1)), _snapshot(target_date=date(2025, 1, 2))):
            with self.subTest(snapshot=snapshot), _databases((snapshot,), (_capture(),)) as (main, archive):
                outcome = _resolve(main, archive).outcomes[0]
                self.assertEqual(outcome.disposition.value, "INVALID_EVIDENCE")
                self.assertEqual(outcome.reason_codes, ("SNAPSHOT_TARGET_MISMATCH",))
                self.assertIsNone(outcome.snapshot_identity)
        for external in ("nar:20250102:10:1", "nar:20250101:010:1", "nar:20250101:10:01", "other"):
            with self.subTest(external=external), _databases() as (main, archive):
                outcome = _resolve(main, archive, targets=_targets(_target(external=external))).outcomes[0]
                self.assertEqual(outcome.reason_codes, ("TARGET_EVIDENCE_IDENTITY_MISMATCH",))

    def test_missing_mapping_or_snapshot_and_exact_dataset_retained(self):
        for snapshots, dataset, reason in (((), "dataset", "INTERNAL_RACE_MAPPING_MISSING"),
                                          ((_snapshot(),), "other", "SNAPSHOT_MISSING")):
            with self.subTest(reason=reason), _databases(snapshots, (_capture(),)) as (main, archive):
                result = _resolve(main, archive, dataset=dataset)
                self.assertEqual(result.outcomes[0].disposition.value, "MISSING_PREDICTION_EVIDENCE")
                self.assertEqual(result.outcomes[0].reason_codes, (reason,))
                self.assertIsNotNone(result.outcomes[0].result_capture_reference)
                self.assertEqual(len(result.outcomes), 1)

    def test_wrong_stored_internal_linkage_raises_globally(self):
        with _databases((_snapshot(),), (_capture(),)) as (main, archive):
            main.execute("PRAGMA foreign_keys=OFF")
            main.execute("DROP TRIGGER trg_his_snapshot_header_mapping_update")
            main.execute("UPDATE historical_input_snapshots SET internal_race_id=2")
            main.commit()
            with self.assertRaises(RepositoryDataIntegrityError):
                _resolve(main, archive)

    def test_settlement_only_observed_ranking_inclusive_cutoff_and_exact_reuse(self):
        older = _capture(observed=_SETTLEMENT - timedelta(seconds=1), stored=_SETTLEMENT + timedelta(days=3), body=b"older")
        latest = _capture(requested=_START, body=b"chosen")
        future = _capture(observed=_SETTLEMENT + timedelta(microseconds=1), body=b"future")
        with _databases((_snapshot(),), (older, future, latest)) as (main, archive):
            outcome = _resolve(main, archive).outcomes[0]
            self.assertEqual(outcome.result_capture_reference.capture_id, latest.capture_id)
            self.assertIs(outcome.result_capture_reference, outcome.payout_capture_reference)
            self.assertEqual(outcome.disposition.value, "EXECUTABLE")
        with _databases((_snapshot(),), (future,)) as (main, archive):
            self.assertEqual(_resolve(main, archive).outcomes[0].disposition.value, "MISSING_SETTLEMENT_EVIDENCE")

    def test_settlement_same_greatest_different_captures_is_target_invalid(self):
        a = _capture(body=b"a")
        b = _capture(body=b"b", requested=_START, stored=_SETTLEMENT + timedelta(days=5))
        for captures in ((a, b), (b, a)):
            with self.subTest(order=captures), _databases((_snapshot(),), captures) as (main, archive), \
                    patch.object(SQLiteNAROfficialResponseCaptureRepository, "load_capture", side_effect=AssertionError("must not tie-break")):
                result = _resolve(main, archive)
                self.assertEqual(result.outcomes[0].disposition.value, "INVALID_EVIDENCE")
                self.assertEqual(result.outcomes[0].reason_codes, ("SETTLEMENT_CAPTURE_AMBIGUOUS",))
                self.assertIsNotNone(result.outcomes[0].snapshot_identity)
                self.assertIsNone(result.outcomes[0].result_capture_reference)

    def test_duplicate_persisted_capture_identity_is_global_not_target_ambiguity(self):
        with _databases((_snapshot(),), (_capture(),)) as (main, archive):
            _unconstrained_copy(archive, "nar_official_response_captures")
            archive.execute("INSERT INTO nar_official_response_captures SELECT * FROM nar_official_response_captures")
            archive.execute("UPDATE nar_official_response_captures SET capture_id=? WHERE rowid=(SELECT MAX(rowid) FROM nar_official_response_captures)",
                            ("nar-capture-v1:" + "0" * 64,))
            archive.commit()
            with self.assertRaises(RepositoryDataIntegrityError):
                _resolve(main, archive)
            # Independently exercise the metadata duplicate guard on the same corrupt rows.
            with self.assertRaisesRegex(RepositoryDataIntegrityError, "duplicate persisted evidence identity"):
                subject._capture_metadata(archive)

    def test_capture_integrity_and_malformed_metadata_are_global(self):
        cases = (
            ("UPDATE nar_official_response_captures SET capture_id=?", ("nar-capture-v1:" + "0" * 64,)),
            ("UPDATE nar_official_response_bodies SET response_body=?", (b"corrupted bytes",)),
            ("UPDATE nar_official_response_bodies SET byte_length=1", ()),
            ("UPDATE nar_official_response_captures SET response_sha256=?", ("0" * 64,)),
            ("UPDATE nar_official_response_captures SET canonical_source_url=?", ("https://other.test/unknown",)),
            ("UPDATE nar_official_response_captures SET observed_at_utc=?", ("2025-01-01T08:00:00Z",)),
            ("UPDATE nar_official_response_captures SET requested_at_utc=?", (_time(_SETTLEMENT + timedelta(days=1)),)),
        )
        for sql, params in cases:
            with self.subTest(sql=sql), _databases((_snapshot(),), (_capture(),)) as (main, archive):
                archive.execute("PRAGMA foreign_keys=OFF")
                archive.execute("PRAGMA ignore_check_constraints=ON")
                archive.execute(sql, params)
                archive.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    _resolve(main, archive)

    def test_capture_exact_disappearance_and_disagreement_are_global(self):
        for value in (None, _capture(body=b"different body")):
            with self.subTest(value=value), _databases((_snapshot(),), (_capture(),)) as (main, archive), \
                    patch.object(SQLiteNAROfficialResponseCaptureRepository, "load_capture", return_value=value), \
                    self.assertRaises(RepositoryDataIntegrityError):
                _resolve(main, archive)

    def test_missing_settlement_and_both_sides_shortage_preserve_references(self):
        with _databases((_snapshot(),), (_capture(2), _capture(page="DebaTable"))) as (main, archive):
            outcome = _resolve(main, archive).outcomes[0]
            self.assertEqual(outcome.disposition.value, "MISSING_SETTLEMENT_EVIDENCE")
            self.assertIsNotNone(outcome.snapshot_identity)
            self.assertEqual(outcome.reason_codes, ("PAYOUT_CAPTURE_MISSING", "RESULT_CAPTURE_MISSING"))
        with _databases() as (main, archive):
            outcome = _resolve(main, archive).outcomes[0]
            self.assertEqual(outcome.disposition.value, "MISSING_PREDICTION_EVIDENCE")
            self.assertEqual(outcome.reason_codes, ("INTERNAL_RACE_MAPPING_MISSING", "PAYOUT_CAPTURE_MISSING", "RESULT_CAPTURE_MISSING"))

    def test_prediction_settlement_and_completeness_times_remain_separate(self):
        snapshot = _snapshot(available=None)
        with _databases((snapshot,), (_capture(),)) as (main, archive):
            result = _resolve(main, archive)
            self.assertEqual(result.day_state.value, "ALL_TARGETS_RESOLVED")
            self.assertGreater(result.outcomes[0].result_capture_reference.observed_at, snapshot.race.scheduled_start_at)
            self.assertEqual(result.outcomes[0].snapshot_identity.captured_at, _CAPTURED)
            loaded = SQLiteHistoricalInputSnapshotRepository(connection=main).load_snapshot_by_identity(identity=snapshot.identity)
            self.assertTrue(all(item.available_at is None for p in loaded.provenance for item in p.evidence))
            self.assertGreater(result.target_set.completeness_evidence[0].observed_at, _SETTLEMENT)

    def test_denominator_and_native_non_run_none_unknown_states(self):
        targets = _targets(_target(1), _target(2, kind=_NON_RUN), _target(3, start=None, kind=_NON_RUN),
                           _target(4, kind="unqualified-kind"), _target(5, start=None))
        with _databases((_snapshot(),), (_capture(),)) as (main, archive):
            result = _resolve(main, archive, targets=targets)
            self.assertEqual(result.day_state.value, "PARTIALLY_RESOLVED")
            self.assertEqual(tuple(item.target for item in result.outcomes), targets.target_races)
            self.assertEqual([item.disposition.value for item in result.outcomes], ["EXECUTABLE", "UNSUPPORTED", "UNSUPPORTED", "UNSUPPORTED", "INVALID_EVIDENCE"])
            self.assertEqual(result.outcomes[4].reason_codes, ("SCHEDULED_START_UNAVAILABLE",))
            self.assertIsNone(result.outcomes[2].snapshot_identity)

    def test_deterministic_snapshot_capture_insertion_order_and_timezone(self):
        snapshots = (_snapshot(1), _snapshot(2), _snapshot(1, captured=_PREDICTION))
        captures = (_capture(1, observed=_START + timedelta(hours=1)), _capture(2), _capture(1))
        results = []
        for reverse in (False, True):
            with _databases(tuple(reversed(snapshots)) if reverse else snapshots,
                            tuple(reversed(captures)) if reverse else captures) as (main, archive):
                cutoff = _SETTLEMENT.astimezone(timezone(timedelta(hours=9))) if reverse else _SETTLEMENT
                results.append(_resolve(main, archive, targets=_targets(_target(2), _target(1)), cutoff=cutoff))
        self.assertEqual(results[0], results[1])

    def test_global_late_failure_never_constructs_partial_day(self):
        with _databases((_snapshot(1), _snapshot(2)), (_capture(1), _capture(2))) as (main, archive):
            main.execute("UPDATE historical_input_snapshots SET content_sha256=? WHERE internal_race_id=2", ("0" * 64,))
            main.commit()
            with patch.object(subject, "_Resolution", side_effect=AssertionError("partial result must not be constructed")), \
                    self.assertRaises(RepositoryDataIntegrityError):
                _resolve(main, archive, targets=_targets(_target(1), _target(2)))
            self.assertFalse(main.in_transaction)
            self.assertFalse(archive.in_transaction)

    def test_missing_evolved_schema_or_unique_index_fail_even_for_non_run(self):
        for corruption in ("DROP TABLE historical_input_snapshot_provenance_evidence",
                           "ALTER TABLE historical_input_snapshot_provenance_evidence DROP COLUMN request_identity_sha256"):
            with self.subTest(corruption=corruption), _databases() as (main, archive):
                main.execute(corruption)
                main.commit()
                with self.assertRaises(RepositoryDataIntegrityError):
                    _resolve(main, archive, targets=_targets(_target(kind=_NON_RUN)))
        with _databases() as (main, archive):
            archive.execute("DROP INDEX ux_nar_official_response_captures_evidence")
            archive.commit()
            with self.assertRaises(RepositoryDataIntegrityError):
                _resolve(main, archive)

    def test_invalid_api_scope_connections_and_caller_transaction_not_repaired(self):
        with _databases() as (main, archive):
            for kwargs in ({"dataset": " bad"}, {"cutoff": _SETTLEMENT.replace(tzinfo=None)}):
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    _resolve(main, archive, **kwargs)
            with self.assertRaises(TargetDiscoveryIncompleteError):
                _resolve(main, archive, targets=_targets())
            with self.assertRaises(RepositoryValidationError):
                _resolve(main, main)
            main.execute("BEGIN")
            with self.assertRaises(RepositoryValidationError):
                _resolve(main, archive)
            self.assertTrue(main.in_transaction)
            self.assertFalse(archive.in_transaction)
            main.rollback()
        closed = sqlite3.connect(":memory:")
        closed.close()
        with _databases() as (main, archive), self.assertRaises(RepositoryValidationError):
            _resolve(closed, archive)

    def test_no_network_clock_writes_migrations_normalizers_or_runner(self):
        sources = [inspect.getsource(module) for module in (subject, values)]
        for source in sources:
            tree = ast.parse(source)
            attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
            self.assertFalse(attributes & {"now", "today", "utcnow", "time", "connect", "save_snapshot", "save_capture"})
            for token in ("requests", "httpx", "urllib.request", "socket", "apply_migrations", "apply_capture_schema_migrations", "BeautifulSoup", "run_sqlite_historical_replay", "normalize_and_persist", "target_race_count"):
                self.assertNotIn(token, source)
        with _databases((_snapshot(),), (_capture(),)) as (main, archive), ExitStack() as stack:
            for name in ("socket.create_connection", "socket.socket", "urllib.request.urlopen", "time.time",
                         "scripts.migrations.runner.apply_migrations",
                         "scripts.simulation.nar_official_response_capture_migration_runner.apply_capture_schema_migrations",
                         "scripts.simulation.sqlite_historical_replay_application.run_sqlite_historical_replay",
                         "scripts.simulation.nar_target_race_result_persistence.normalize_and_persist_nar_target_race_result",
                         "scripts.simulation.nar_target_race_payout_persistence.normalize_and_persist_nar_target_race_payout"):
                stack.enter_context(patch(name, side_effect=AssertionError("forbidden dependency called")))
            stack.enter_context(patch.object(SQLiteHistoricalInputSnapshotRepository, "save_snapshot", side_effect=AssertionError("write")))
            stack.enter_context(patch.object(SQLiteNAROfficialResponseCaptureRepository, "save_capture", side_effect=AssertionError("write")))
            forbidden = []
            allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_PRAGMA, sqlite3.SQLITE_TRANSACTION}
            def authorize(action, first, second, database, trigger):
                if action not in allowed or (action == sqlite3.SQLITE_TRANSACTION and first not in ("BEGIN", "ROLLBACK")):
                    forbidden.append((action, first, second))
                    return sqlite3.SQLITE_DENY
                return sqlite3.SQLITE_OK
            before = (main.total_changes, archive.total_changes)
            for connection in (main, archive):
                connection.set_authorizer(authorize)
            result = _resolve(main, archive)
            self.assertEqual(result.day_state.value, "ALL_TARGETS_RESOLVED")
            self.assertEqual(forbidden, [])
            self.assertEqual(before, (main.total_changes, archive.total_changes))
            for connection in (main, archive):
                self.assertFalse(connection.in_transaction)
                self.assertEqual(connection.execute("PRAGMA query_only").fetchone()[0], 1)
                self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
                connection.set_authorizer(None)

    def test_mode_ro_disk_connections_remain_open_and_bytes_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = (Path(directory) / "main.db", Path(directory) / "archive.db")
            main, archive = (sqlite3.connect(path) for path in paths)
            try:
                _initialize(main, archive, (_snapshot(),), (_capture(),))
            finally:
                main.close()
                archive.close()
            before = tuple(path.read_bytes() for path in paths)
            main, archive = (sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) for path in paths)
            try:
                self.assertEqual(_resolve(main, archive).day_state.value, "ALL_TARGETS_RESOLVED")
                for connection in (main, archive):
                    self.assertEqual(connection.execute("SELECT 1").fetchone()[0], 1)
                    self.assertFalse(connection.in_transaction)
            finally:
                main.close()
                archive.close()
            self.assertEqual(before, tuple(path.read_bytes() for path in paths))


if __name__ == "__main__":
    unittest.main()
