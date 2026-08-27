from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import inspect
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalEntryIdentity,
    HistoricalExternalRaceIdentity,
    HistoricalInputProvenance,
    HistoricalInputSnapshot,
    HistoricalInputSnapshotIdentity,
    HistoricalRaceEntrySnapshot,
    HistoricalRaceSnapshot,
    HistoricalSourceIdentity,
)
from scripts.simulation.jra_official_identity import (
    build_jra_external_entry_id,
    parse_jra_result_url_identity,
)
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialPageKind,
    JRAOfficialResponseCapture,
)
from scripts.simulation.jra_target_race_result_persistence import (
    JRATargetRaceResultPersistenceError,
    JRATargetRaceResultPersistenceUnavailableError,
    JRATargetRaceResultPersistenceUnsupportedError,
    JRATargetRaceResultPersistenceValidationError,
    normalize_and_persist_jra_target_race_result,
)
from scripts.simulation.repositories.interfaces import (
    PersistedRaceResult,
    RaceResultEntryStatus,
    RaceResultStatus,
    RaceResultRepository,
)


UTC = timezone.utc
CAPTURE_TIME = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
SNAPSHOT_CAPTURE_TIME = datetime(2025, 9, 13, 0, 0, tzinfo=UTC)
URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC"
RACE_IDENTITY = parse_jra_result_url_identity(URL)
RESULT_HEADINGS = (
    "着順", "枠", "馬番", "馬名", "性齢", "負担重量", "騎手名", "タイム", "着差",
    "コーナー通過順位", "馬体重（増減）", "調教師名", "単勝人気",
)


class _Archive:
    def __init__(self, value: object) -> None:
        self.value = value
        self.calls: list[str] = []
        self.error: BaseException | None = None

    def load_capture(self, *, capture_id: str) -> JRAOfficialResponseCapture | None:
        self.calls.append(capture_id)
        if self.error is not None:
            raise self.error
        return self.value  # type: ignore[return-value]


class _RaceResultRepository:
    def __init__(self) -> None:
        self.saved: list[PersistedRaceResult] = []
        self.error: BaseException | None = None

    def save_race_result(self, result: PersistedRaceResult) -> None:
        if self.error is not None:
            raise self.error
        self.saved.append(result)


def _evidence(role: str) -> HistoricalInputEvidenceReference:
    return HistoricalInputEvidenceReference(
        role,
        "https://evidence.example.test/jra",
        "a" * 64,
        None,
        SNAPSHOT_CAPTURE_TIME - timedelta(minutes=1),
    )


def _snapshot(*, horse_numbers: tuple[int, ...] = tuple(range(1, 14)), organization: str = "JRA") -> HistoricalInputSnapshot:
    source = HistoricalSourceIdentity(
        organization,
        "jra_official",
        RACE_IDENTITY.external_race_id,
        URL,
    )
    external_race = HistoricalExternalRaceIdentity(
        organization,
        "jra_official",
        RACE_IDENTITY.external_race_id,
    )
    entries = tuple(
        HistoricalRaceEntrySnapshot(
            race_entry_id=1000 + horse_no,
            external_entry_identity=HistoricalExternalEntryIdentity(
                external_race,
                build_jra_external_entry_id(race_identity=RACE_IDENTITY, horse_no=horse_no),
                None,
            ),
            horse_no=horse_no,
            jockey=f"騎手{horse_no}",
            win_odds=Decimal("2.0"),
            entry_order=index,
        )
        for index, horse_no in enumerate(horse_numbers)
    )
    provenance: list[HistoricalInputProvenance] = [
        HistoricalInputProvenance("track", "track", "jra_official", "track", None, (_evidence("track"),)),
    ]
    for entry in entries:
        entry_id = entry.race_entry_id
        provenance.extend(
            (
                HistoricalInputProvenance("entry", f"entry/{entry_id}", "jra_official", f"entry-{entry_id}", entry_id, (_evidence("entry"),)),
                HistoricalInputProvenance("odds", f"odds/{entry_id}", "jra_official", f"odds-{entry_id}", entry_id, (_evidence("odds_win"),)),
                HistoricalInputProvenance("jockey", f"jockey/{entry_id}", "jra_official", f"jockey-{entry_id}", entry_id, (_evidence("jockey"),)),
                HistoricalInputProvenance("past_race", f"past_race/{entry_id}/none", "jra_official", f"absence-{entry_id}", entry_id, (_evidence("past_race_absence_query"),)),
            )
        )
    return HistoricalInputSnapshot(
        identity=HistoricalInputSnapshotIdentity("dataset-jra", source, SNAPSHOT_CAPTURE_TIME),
        internal_race_id=700,
        information_cutoff=SNAPSHOT_CAPTURE_TIME + timedelta(hours=1),
        race=HistoricalRaceSnapshot(
            target_race_date=date(2025, 9, 13),
            scheduled_start_at=datetime(2025, 9, 13, 2, 30, tzinfo=UTC),
            place="中山",
            distance_m=1600,
            track="芝",
            track_condition="良",
        ),
        entries=entries,
        past_races=(),
        provenance=tuple(provenance),
    )


def _html(
    *,
    horse_numbers: tuple[int, ...] = tuple(range(1, 14)),
    places: tuple[str, ...] | None = None,
    margins: tuple[str, ...] | None = None,
    refund: bool = True,
    refund_heading: str = "払戻金",
    refund_amount: str = "160 円",
    table_count: int = 1,
    race_alt: str = "4R",
) -> bytes:
    values = places if places is not None else tuple(str(item) for item in range(1, len(horse_numbers) + 1))
    gaps = margins if margins is not None else tuple("" for _ in horse_numbers)
    headings = "".join(f"<th>{heading}</th>" for heading in RESULT_HEADINGS)
    rows = "".join(
        f"<tr><td class='place'>{place}</td><td class='num'>{horse_no}</td><td class='margin'>{margin}</td></tr>"
        for horse_no, place, margin in zip(horse_numbers, values, gaps, strict=True)
    )
    table = f"<table><thead><tr>{headings}</tr></thead><tbody>{rows}</tbody></table>"
    tables = table * table_count
    payout = (
        f"<div class='refund_area'><div class='block_header'>{refund_heading}</div>"
        f"<div class='refund_unit'><ul><li><span class='yen'>{refund_amount}</span></li></ul></div></div>"
        if refund else ""
    )
    return (
        "<html><body><div id='race_result'><div class='race_header'>"
        "<div class='cell date'>2025年9月13日（土曜） 4回中山3日</div>"
        f"<div class='race_number'><img alt='{race_alt}'></div></div>"
        f"{tables}{payout}</div></body></html>"
    ).encode("cp932")


def _capture(*, body: bytes | None = None, url: str = URL) -> JRAOfficialResponseCapture:
    return JRAOfficialResponseCapture(
        canonical_source_url=url,
        response_body=_html() if body is None else body,
        charset="cp932",
        requested_at=CAPTURE_TIME - timedelta(seconds=1),
        observed_at=CAPTURE_TIME,
        stored_at=CAPTURE_TIME + timedelta(seconds=1),
        http_status=200,
        content_type="text/html; charset=cp932",
    )


def _run(*, capture: object | None = None, snapshot: HistoricalInputSnapshot | None = None) -> tuple[PersistedRaceResult, _Archive, _RaceResultRepository]:
    supplied = _capture() if capture is None else capture
    archive = _Archive(supplied)
    repository = _RaceResultRepository()
    actual_capture_id = supplied.capture_id if isinstance(supplied, JRAOfficialResponseCapture) else "capture-id"
    result = normalize_and_persist_jra_target_race_result(
        capture_id=actual_capture_id,
        capture_archive=archive,
        snapshot=_snapshot() if snapshot is None else snapshot,
        race_result_repository=repository,
    )
    return result, archive, repository


class JRATargetRaceResultPersistenceTest(unittest.TestCase):
    def test_public_surface_and_signature_are_exact(self) -> None:
        import scripts.simulation.jra_target_race_result_persistence as module

        self.assertEqual(
            module.__all__,
            (
                "JRATargetRaceResultPersistenceError",
                "JRATargetRaceResultPersistenceValidationError",
                "JRATargetRaceResultPersistenceUnavailableError",
                "JRATargetRaceResultPersistenceUnsupportedError",
                "normalize_and_persist_jra_target_race_result",
            ),
        )
        self.assertFalse(hasattr(simulation_package, "normalize_and_persist_jra_target_race_result"))
        signature = inspect.signature(normalize_and_persist_jra_target_race_result)
        self.assertEqual(tuple(signature.parameters), ("capture_id", "capture_archive", "snapshot", "race_result_repository"))
        self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in signature.parameters.values()))
        hints = get_type_hints(normalize_and_persist_jra_target_race_result)
        self.assertEqual(hints["capture_id"], str)
        self.assertEqual(hints["capture_archive"].__name__, "JRAOfficialResponseCaptureArchive")
        self.assertEqual(hints["snapshot"], HistoricalInputSnapshot)
        self.assertEqual(hints["race_result_repository"], RaceResultRepository)
        self.assertEqual(hints["return"], PersistedRaceResult)
        self.assertTrue(issubclass(JRATargetRaceResultPersistenceValidationError, JRATargetRaceResultPersistenceError))

    def test_normal_final_complete_thirteen_entry_result_is_persisted_once(self) -> None:
        result, archive, repository = _run()
        self.assertEqual(archive.calls, [_capture().capture_id])
        self.assertEqual(repository.saved, [result])
        self.assertIs(repository.saved[0], result)
        self.assertEqual(result.race_id, 700)
        self.assertIs(result.result_status, RaceResultStatus.COMPLETE)
        self.assertEqual(result.observed_at, CAPTURE_TIME)
        self.assertEqual(result.finalized_at, CAPTURE_TIME)
        self.assertEqual(result.source, _capture().capture_id)
        self.assertEqual({entry.horse_no for entry in result.entries}, set(range(1, 14)))
        self.assertEqual({entry.race_entry_id for entry in result.entries}, set(range(1001, 1014)))
        self.assertEqual({entry.finish_position for entry in result.entries}, set(range(1, 14)))
        self.assertEqual({entry.result_status for entry in result.entries}, {RaceResultEntryStatus.CONFIRMED})

    def test_public_boundary_failures_happen_before_archive_io(self) -> None:
        archive = _Archive(_capture())
        repository = _RaceResultRepository()
        cases = (
            ("", archive, _snapshot(), repository),
            ("capture", object(), _snapshot(), repository),
            ("capture", archive, object(), repository),
            ("capture", archive, _snapshot(), object()),
        )
        for capture_id, collaborator, snapshot, target_repository in cases:
            with self.subTest(case=capture_id), self.assertRaises(ValueError):
                normalize_and_persist_jra_target_race_result(
                    capture_id=capture_id,
                    capture_archive=collaborator,  # type: ignore[arg-type]
                    snapshot=snapshot,  # type: ignore[arg-type]
                    race_result_repository=target_repository,  # type: ignore[arg-type]
                )
        self.assertEqual(archive.calls, [])
        self.assertEqual(repository.saved, [])

    def test_archive_absence_invalid_return_and_exception_do_not_write(self) -> None:
        for supplied, error, expected in (
            (None, None, JRATargetRaceResultPersistenceUnavailableError),
            (object(), None, JRATargetRaceResultPersistenceValidationError),
            (_capture(), RuntimeError("archive"), RuntimeError),
        ):
            with self.subTest(supplied=supplied, error=error):
                archive = _Archive(supplied)
                archive.error = error
                repository = _RaceResultRepository()
                capture_id = _capture().capture_id
                with self.assertRaises(expected) as raised:
                    normalize_and_persist_jra_target_race_result(
                        capture_id=capture_id,
                        capture_archive=archive,
                        snapshot=_snapshot(),
                        race_result_repository=repository,
                    )
                if error is not None:
                    self.assertIs(raised.exception, error)
                self.assertEqual(len(archive.calls), 1)
                self.assertEqual(repository.saved, [])

    def test_capture_id_page_kind_and_identity_mismatches_fail_closed(self) -> None:
        good = _capture()
        for supplied, capture_id in ((good, "other"),):
            archive = _Archive(supplied)
            repository = _RaceResultRepository()
            with self.assertRaises(JRATargetRaceResultPersistenceValidationError):
                normalize_and_persist_jra_target_race_result(
                    capture_id=capture_id, capture_archive=archive, snapshot=_snapshot(), race_result_repository=repository
                )
            self.assertEqual(repository.saved, [])
        incompatible = _snapshot(organization="NAR")
        archive = _Archive(good)
        repository = _RaceResultRepository()
        with self.assertRaises(JRATargetRaceResultPersistenceValidationError):
            normalize_and_persist_jra_target_race_result(
                capture_id=good.capture_id, capture_archive=archive, snapshot=incompatible, race_result_repository=repository
            )
        self.assertEqual(repository.saved, [])

    def test_result_grammar_rejects_dead_heat_non_normal_duplicate_and_non_contiguous_finishes(self) -> None:
        cases = (
            (_html(margins=("同着",) + ("",) * 12), JRATargetRaceResultPersistenceUnsupportedError),
            (_html(places=("中止",) + tuple(str(item) for item in range(2, 14))), JRATargetRaceResultPersistenceUnsupportedError),
            (_html(places=("1", "1") + tuple(str(item) for item in range(3, 14))), JRATargetRaceResultPersistenceValidationError),
            (_html(places=("1", "3") + tuple(str(item) for item in range(3, 14))), JRATargetRaceResultPersistenceValidationError),
        )
        for body, error in cases:
            with self.subTest(error=error.__name__):
                capture = _capture(body=body)
                archive = _Archive(capture)
                repository = _RaceResultRepository()
                with self.assertRaises(error):
                    normalize_and_persist_jra_target_race_result(
                        capture_id=capture.capture_id, capture_archive=archive, snapshot=_snapshot(), race_result_repository=repository
                    )
                self.assertEqual(repository.saved, [])

    def test_visible_race_number_requires_exact_complete_approved_value(self) -> None:
        for value in ("14R", "X4R", "4Rfoo", "foo4R", "4R5R", "4R 5R", "04R", "R", ""):
            with self.subTest(value=value):
                capture = _capture(body=_html(race_alt=value))
                repository = _RaceResultRepository()
                with self.assertRaises(JRATargetRaceResultPersistenceValidationError):
                    normalize_and_persist_jra_target_race_result(
                        capture_id=capture.capture_id,
                        capture_archive=_Archive(capture),
                        snapshot=_snapshot(),
                        race_result_repository=repository,
                    )
                self.assertEqual(repository.saved, [])

    def test_structural_and_positive_finality_failures_do_not_persist(self) -> None:
        bodies = (
            _html(refund=False),
            _html(refund_heading="払戻"),
            _html(refund_amount="0 円"),
            _html(table_count=2),
        )
        for body in bodies:
            with self.subTest(body=body[:30]):
                capture = _capture(body=body)
                repository = _RaceResultRepository()
                with self.assertRaises(JRATargetRaceResultPersistenceError):
                    normalize_and_persist_jra_target_race_result(
                        capture_id=capture.capture_id, capture_archive=_Archive(capture), snapshot=_snapshot(), race_result_repository=repository
                    )
                self.assertEqual(repository.saved, [])

    def test_exact_entry_crosswalk_requires_complete_race_specific_snapshot_coverage(self) -> None:
        capture = _capture()
        repository = _RaceResultRepository()
        with self.assertRaises(JRATargetRaceResultPersistenceValidationError):
            normalize_and_persist_jra_target_race_result(
                capture_id=capture.capture_id,
                capture_archive=_Archive(capture),
                snapshot=_snapshot(horse_numbers=tuple(range(1, 13))),
                race_result_repository=repository,
            )
        self.assertEqual(repository.saved, [])

    def test_repository_exception_propagates_the_exact_object_after_one_save_attempt(self) -> None:
        capture = _capture()
        repository = _RaceResultRepository()
        error = RuntimeError("save")
        repository.error = error
        with self.assertRaises(RuntimeError) as raised:
            normalize_and_persist_jra_target_race_result(
                capture_id=capture.capture_id, capture_archive=_Archive(capture), snapshot=_snapshot(), race_result_repository=repository
            )
        self.assertIs(raised.exception, error)
        self.assertEqual(repository.saved, [])

    def test_static_scope_excludes_payout_http_database_and_broad_fallbacks(self) -> None:
        import scripts.simulation.jra_target_race_result_persistence as module

        source = inspect.getsource(module)
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        forbidden = {"sqlite3", "requests", "urllib", "httpx", "os", "random", "time"}
        self.assertFalse(imported & forbidden)
        self.assertNotIn("PayoutPublication", source)
        self.assertNotIn("PayoutRecord", source)
        self.assertNotIn("PayoutRepository", source)
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("_RACE_NUMBER.search", source)
        self.assertIn("_RACE_NUMBER.fullmatch", source)
        self.assertNotIn("except Exception", source)
        self.assertNotIn("except BaseException", source)


if __name__ == "__main__":
    unittest.main()
