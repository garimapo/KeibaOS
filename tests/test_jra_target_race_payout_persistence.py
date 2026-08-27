from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import inspect
from pathlib import Path
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
from scripts.simulation.jra_target_race_payout_persistence import (
    JRATargetRacePayoutPersistenceError,
    JRATargetRacePayoutPersistenceUnavailableError,
    JRATargetRacePayoutPersistenceUnsupportedError,
    JRATargetRacePayoutPersistenceValidationError,
    normalize_and_persist_jra_target_race_payout,
)
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutRepository,
    PayoutStatus,
)


UTC = timezone.utc
CAPTURE_TIME = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
SNAPSHOT_CAPTURE_TIME = datetime(2025, 9, 13, 0, 0, tzinfo=UTC)
URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC"
HORSE_URL = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud002020102902%2F22"
RACE_IDENTITY = parse_jra_result_url_identity(URL)


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


class _PayoutRepository:
    def __init__(self) -> None:
        self.saved: list[PayoutPublication] = []
        self.error: BaseException | None = None
        self.return_value: PayoutPublication | None = None

    def save_payout_publication(self, publication: PayoutPublication) -> PayoutPublication:
        self.saved.append(publication)
        if self.error is not None:
            raise self.error
        return publication if self.return_value is None else self.return_value


def _evidence(role: str) -> HistoricalInputEvidenceReference:
    return HistoricalInputEvidenceReference(
        role,
        "https://evidence.example.test/jra",
        "a" * 64,
        None,
        SNAPSHOT_CAPTURE_TIME - timedelta(minutes=1),
    )


def _snapshot(
    *,
    horse_numbers: tuple[int, ...] = (3, 6, 7),
    organization: str = "JRA",
) -> HistoricalInputSnapshot:
    source = HistoricalSourceIdentity(organization, "jra_official", RACE_IDENTITY.external_race_id, URL)
    external_race = HistoricalExternalRaceIdentity(organization, "jra_official", RACE_IDENTITY.external_race_id)
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


_ITEMS = {
    "win": ("単勝", (("7", "160"),)),
    "place": ("複勝", (("7", "110"), ("3", "250"), ("6", "170"))),
    "wakuren": ("枠連", (("3-5", "1,160"),)),
    "wide": ("ワイド", (("3-7", "420"), ("6-7", "300"), ("3-6", "1,370"))),
    "umaren": ("馬連", (("3-7", "1,030"),)),
    "umatan": ("馬単", (("7-3", "1,380"),)),
    "trio": ("3連複", (("3-6-7", "2,280"),)),
    "tierce": ("3連単", (("7-3-6", "7,260"),)),
}


def _line(selection: str, amount: str, *, unit: str = "円") -> str:
    return (
        "<div class='line'>"
        f"<div class='num'>{selection}</div>"
        f"<div class='yen'>{amount}<span class='unit'>{unit}</span></div>"
        "<div class='pop'>1<span>番人気</span></div>"
        "</div>"
    )


def _item(class_name: str, label: str, values: tuple[tuple[str, str], ...]) -> str:
    return f"<li class='{class_name}'><dl><dt>{label}</dt><dd>{''.join(_line(*value) for value in values)}</dd></dl></li>"


def _html(
    *,
    race_date: str = "2025年9月13日（土曜） 4回中山3日",
    race_alt: str = "4R",
    heading: str = "払戻金",
    include_area: bool = True,
    unit_count: int = 1,
    item_values: dict[str, tuple[tuple[str, str], ...]] | None = None,
    item_markup: dict[str, str] | None = None,
) -> bytes:
    values = dict(_ITEMS)
    if item_values is not None:
        values.update({key: (_ITEMS[key][0], item) for key, item in item_values.items()})
    markup = item_markup or {}
    def make_item(class_name: str) -> str:
        if class_name in markup:
            return markup[class_name]
        label, rows = values[class_name]
        return _item(class_name, label, rows)
    unit = (
        "<div class='refund_unit'>"
        f"<div class='left'><ul>{make_item('win')}{make_item('place')}</ul></div>"
        f"<div class='center'><ul>{make_item('wakuren')}{make_item('wide')}</ul></div>"
        f"<div class='right'><ul>{make_item('umaren')}{make_item('umatan')}{make_item('trio')}{make_item('tierce')}</ul></div>"
        "</div>"
    )
    payout = (
        "<div class='refund_area'><div class='block_header'><div class='content'><h2>"
        f"{heading}</h2></div></div>{unit * unit_count}</div>"
        if include_area
        else ""
    )
    return (
        "<html><body><div id='race_result'><div class='race_header'>"
        f"<div class='cell date'>{race_date}</div>"
        f"<div class='race_number'><img alt='{race_alt}'></div></div>"
        f"{payout}</div></body></html>"
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


def _run(
    *,
    bet_type: str = "単勝",
    capture: object | None = None,
    snapshot: HistoricalInputSnapshot | None = None,
) -> tuple[PayoutPublication, _Archive, _PayoutRepository]:
    supplied = _capture() if capture is None else capture
    archive = _Archive(supplied)
    repository = _PayoutRepository()
    actual_capture_id = supplied.capture_id if isinstance(supplied, JRAOfficialResponseCapture) else "capture-id"
    result = normalize_and_persist_jra_target_race_payout(
        capture_id=actual_capture_id,
        capture_archive=archive,
        snapshot=_snapshot() if snapshot is None else snapshot,
        bet_type=bet_type,
        payout_repository=repository,
    )
    return result, archive, repository


class JRATargetRacePayoutPersistenceTest(unittest.TestCase):
    def test_public_surface_signature_and_type_hints_are_exact(self) -> None:
        import scripts.simulation.jra_target_race_payout_persistence as module

        self.assertEqual(
            module.__all__,
            (
                "JRATargetRacePayoutPersistenceError",
                "JRATargetRacePayoutPersistenceValidationError",
                "JRATargetRacePayoutPersistenceUnavailableError",
                "JRATargetRacePayoutPersistenceUnsupportedError",
                "normalize_and_persist_jra_target_race_payout",
            ),
        )
        self.assertFalse(hasattr(simulation_package, "normalize_and_persist_jra_target_race_payout"))
        signature = inspect.signature(normalize_and_persist_jra_target_race_payout)
        self.assertEqual(tuple(signature.parameters), ("capture_id", "capture_archive", "snapshot", "bet_type", "payout_repository"))
        self.assertTrue(all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values()))
        hints = get_type_hints(normalize_and_persist_jra_target_race_payout)
        self.assertEqual(hints["capture_id"], str)
        self.assertEqual(hints["capture_archive"].__name__, "JRAOfficialResponseCaptureArchive")
        self.assertEqual(hints["snapshot"], HistoricalInputSnapshot)
        self.assertEqual(hints["bet_type"], str)
        self.assertEqual(hints["payout_repository"], PayoutRepository)
        self.assertEqual(hints["return"], PayoutPublication)
        self.assertTrue(issubclass(JRATargetRacePayoutPersistenceValidationError, JRATargetRacePayoutPersistenceError))

    def test_normal_supported_types_persist_exact_publications(self) -> None:
        expected = {
            "単勝": (((1007,), 160),),
            "馬連": (((1003, 1007), 1030),),
            "ワイド": (((1003, 1006), 1370), ((1003, 1007), 420), ((1006, 1007), 300)),
            "3連複": (((1003, 1006, 1007), 2280),),
        }
        for bet_type, records in expected.items():
            with self.subTest(bet_type=bet_type):
                publication, archive, repository = _run(bet_type=bet_type)
                self.assertEqual(archive.calls, [_capture().capture_id])
                self.assertEqual(repository.saved, [publication])
                self.assertEqual(publication.race_id, 700)
                self.assertEqual(publication.bet_type, bet_type)
                self.assertTrue(publication.is_complete)
                self.assertEqual(publication.observed_at, CAPTURE_TIME)
                self.assertEqual(publication.finalized_at, CAPTURE_TIME)
                self.assertEqual(publication.source, _capture().capture_id)
                self.assertEqual(publication.source_url, URL)
                self.assertEqual(
                    tuple((record.race_entry_ids, record.payout_per_100) for record in publication.entries),
                    records,
                )
                self.assertEqual({record.payout_status for record in publication.entries}, {PayoutStatus.WINNING})

    def test_repository_return_identity_and_exception_are_preserved(self) -> None:
        capture = _capture()
        archive = _Archive(capture)
        repository = _PayoutRepository()
        expected = PayoutPublication(
            race_id=700,
            bet_type="単勝",
            finalized_at=CAPTURE_TIME,
            observed_at=CAPTURE_TIME,
            is_complete=True,
            source=capture.capture_id,
            entries=(PayoutRecord((1007,), 160, PayoutStatus.WINNING),),
            source_url=URL,
            publication_id=77,
        )
        repository.return_value = expected
        self.assertIs(
            normalize_and_persist_jra_target_race_payout(
                capture_id=capture.capture_id,
                capture_archive=archive,
                snapshot=_snapshot(),
                bet_type="単勝",
                payout_repository=repository,
            ),
            expected,
        )
        failure = RuntimeError("save")
        repository = _PayoutRepository()
        repository.error = failure
        with self.assertRaises(RuntimeError) as raised:
            normalize_and_persist_jra_target_race_payout(
                capture_id=capture.capture_id,
                capture_archive=_Archive(capture),
                snapshot=_snapshot(),
                bet_type="単勝",
                payout_repository=repository,
            )
        self.assertIs(raised.exception, failure)
        self.assertEqual(len(repository.saved), 1)

    def test_public_boundary_failures_happen_before_archive_io(self) -> None:
        archive = _Archive(_capture())
        repository = _PayoutRepository()
        cases = (
            ("", archive, _snapshot(), "単勝", repository),
            ("capture", object(), _snapshot(), "単勝", repository),
            ("capture", archive, object(), "単勝", repository),
            ("capture", archive, _snapshot(), "複勝", repository),
            ("capture", archive, _snapshot(), "単勝", object()),
        )
        for capture_id, supplied_archive, snapshot, bet_type, supplied_repository in cases:
            with self.subTest(case=capture_id, bet_type=bet_type), self.assertRaises(ValueError):
                normalize_and_persist_jra_target_race_payout(
                    capture_id=capture_id,
                    capture_archive=supplied_archive,  # type: ignore[arg-type]
                    snapshot=snapshot,  # type: ignore[arg-type]
                    bet_type=bet_type,
                    payout_repository=supplied_repository,  # type: ignore[arg-type]
                )
        self.assertEqual(archive.calls, [])
        self.assertEqual(repository.saved, [])

    def test_archive_absence_wrong_return_page_kind_and_exception_never_save(self) -> None:
        horse_capture = _capture(url=HORSE_URL)
        for supplied, error, expected in (
            (None, None, JRATargetRacePayoutPersistenceUnavailableError),
            (object(), None, JRATargetRacePayoutPersistenceValidationError),
            (horse_capture, None, JRATargetRacePayoutPersistenceValidationError),
            (_capture(), RuntimeError("archive"), RuntimeError),
        ):
            with self.subTest(supplied=supplied, error=error):
                archive = _Archive(supplied)
                archive.error = error
                repository = _PayoutRepository()
                with self.assertRaises(expected) as raised:
                    normalize_and_persist_jra_target_race_payout(
                        capture_id=_capture().capture_id,
                        capture_archive=archive,
                        snapshot=_snapshot(),
                        bet_type="単勝",
                        payout_repository=repository,
                    )
                if error is not None:
                    self.assertIs(raised.exception, error)
                self.assertEqual(len(archive.calls), 1)
                self.assertEqual(repository.saved, [])

    def test_capture_and_visible_race_identity_fail_closed_before_save(self) -> None:
        cases = (
            (_capture(body=_html(race_date="2025年9月14日（日曜） 4回中山3日")), _snapshot()),
            (_capture(body=_html(race_date="2025年9月13日（土曜） 4回東京3日")), _snapshot()),
            (_capture(body=_html(race_date="2025年9月13日（土曜） 5回中山3日")), _snapshot()),
            (_capture(body=_html(race_date="2025年9月13日（土曜） 4回中山4日")), _snapshot()),
            (_capture(body=_html(race_alt="14R")), _snapshot()),
            (_capture(body=_html(race_alt="X4R")), _snapshot()),
            (_capture(body=_html(race_alt="4Rfoo")), _snapshot()),
        )
        for capture, snapshot in cases:
            with self.subTest(capture_id=capture.capture_id):
                archive = _Archive(capture)
                repository = _PayoutRepository()
                with self.assertRaises(JRATargetRacePayoutPersistenceValidationError):
                    normalize_and_persist_jra_target_race_payout(
                        capture_id=capture.capture_id,
                        capture_archive=archive,
                        snapshot=snapshot,
                        bet_type="単勝",
                        payout_repository=repository,
                    )
                self.assertEqual(repository.saved, [])

    def test_snapshot_crosswalk_incoherence_unresolved_and_duplicate_identity_never_save(self) -> None:
        for snapshot, mutate in (
            (_snapshot(), lambda value: object.__setattr__(value.entries[0].external_entry_identity, "external_entry_id", "wrong")),
            (_snapshot(horse_numbers=(3, 6)), lambda value: None),
            (_snapshot(), lambda value: object.__setattr__(value.entries[1], "race_entry_id", value.entries[0].race_entry_id)),
        ):
            with self.subTest(snapshot=snapshot), self.assertRaises(JRATargetRacePayoutPersistenceValidationError):
                mutate(snapshot)
                archive = _Archive(_capture())
                repository = _PayoutRepository()
                normalize_and_persist_jra_target_race_payout(
                    capture_id=_capture().capture_id,
                    capture_archive=archive,
                    snapshot=snapshot,
                    bet_type="馬連",
                    payout_repository=repository,
                )
                self.assertEqual(repository.saved, [])

    def test_payout_container_and_requested_item_fail_closed_before_save(self) -> None:
        duplicate_area = _html().replace(
            b"</div></body></html>",
            b"<div class='refund_area'></div></div></body></html>",
        )
        duplicate_unit = _html(unit_count=2)
        bad_label = _html(item_markup={"win": _item("win", "単勝X", (("7", "160"),))})
        wrong_class = _html(item_markup={"win": _item("winner", "単勝", (("7", "160"),))})
        cases = (
            (_html(include_area=False), JRATargetRacePayoutPersistenceValidationError),
            (_html(heading="払戻"), JRATargetRacePayoutPersistenceUnavailableError),
            (duplicate_area, JRATargetRacePayoutPersistenceValidationError),
            (duplicate_unit, JRATargetRacePayoutPersistenceValidationError),
            (bad_label, JRATargetRacePayoutPersistenceValidationError),
            (wrong_class, JRATargetRacePayoutPersistenceValidationError),
        )
        for body, expected in cases:
            with self.subTest(expected=expected):
                capture = _capture(body=body)
                repository = _PayoutRepository()
                with self.assertRaises(expected):
                    normalize_and_persist_jra_target_race_payout(
                        capture_id=capture.capture_id,
                        capture_archive=_Archive(capture),
                        snapshot=_snapshot(),
                        bet_type="単勝",
                        payout_repository=repository,
                    )
                self.assertEqual(repository.saved, [])

    def test_selection_grammar_and_crosswalk_fail_closed_before_save(self) -> None:
        for selection in ("03", "+7", "７", "3 - 7", "3--7", "3-3", "", "3-6-7"):
            with self.subTest(selection=selection):
                capture = _capture(body=_html(item_values={"umaren": ((selection, "1,030"),)}))
                repository = _PayoutRepository()
                with self.assertRaises(JRATargetRacePayoutPersistenceError):
                    normalize_and_persist_jra_target_race_payout(
                        capture_id=capture.capture_id,
                        capture_archive=_Archive(capture),
                        snapshot=_snapshot(),
                        bet_type="馬連",
                        payout_repository=repository,
                    )
                self.assertEqual(repository.saved, [])
        capture = _capture(body=_html(item_values={"umaren": (("3-8", "1,030"),)}))
        repository = _PayoutRepository()
        with self.assertRaises(JRATargetRacePayoutPersistenceValidationError):
            normalize_and_persist_jra_target_race_payout(
                capture_id=capture.capture_id,
                capture_archive=_Archive(capture),
                snapshot=_snapshot(),
                bet_type="馬連",
                payout_repository=repository,
            )
        self.assertEqual(repository.saved, [])

    def test_amount_grammar_pairing_and_duplicate_selection_fail_closed_before_save(self) -> None:
        invalid_amounts = ("0", "-1", "+1", "1.0", "1,00", "", "1 000")
        for amount in invalid_amounts:
            with self.subTest(amount=amount):
                capture = _capture(body=_html(item_values={"win": (("7", amount),)}))
                repository = _PayoutRepository()
                with self.assertRaises(JRATargetRacePayoutPersistenceValidationError):
                    normalize_and_persist_jra_target_race_payout(
                        capture_id=capture.capture_id,
                        capture_archive=_Archive(capture),
                        snapshot=_snapshot(),
                        bet_type="単勝",
                        payout_repository=repository,
                    )
                self.assertEqual(repository.saved, [])
        no_unit = _html(item_markup={"win": "<li class='win'><dl><dt>単勝</dt><dd><div class='line'><div class='num'>7</div><div class='yen'>160</div><div class='pop'>1</div></div></dd></dl></li>"})
        duplicate_text = _html(item_markup={"win": "<li class='win'><dl><dt>単勝</dt><dd><div class='line'><div class='num'>7</div><div class='yen'>1<span class='unit'>円</span>60</div><div class='pop'>1</div></div></dd></dl></li>"})
        split_pair = _html(item_markup={"win": "<li class='win'><dl><dt>単勝</dt><dd><div class='line'><div class='num'>7</div><div class='yen'>160<span class='unit'>円</span></div></div></dd></dl></li>"})
        duplicate = _html(item_values={"wide": (("3-7", "420"), ("7-3", "420"))})
        for body, bet_type in ((no_unit, "単勝"), (duplicate_text, "単勝"), (split_pair, "単勝"), (duplicate, "ワイド")):
            with self.subTest(bet_type=bet_type):
                capture = _capture(body=body)
                repository = _PayoutRepository()
                with self.assertRaises(JRATargetRacePayoutPersistenceValidationError):
                    normalize_and_persist_jra_target_race_payout(
                        capture_id=capture.capture_id,
                        capture_archive=_Archive(capture),
                        snapshot=_snapshot(),
                        bet_type=bet_type,
                        payout_repository=repository,
                    )
                self.assertEqual(repository.saved, [])

    def test_wide_partial_failure_and_exceptional_states_do_not_save(self) -> None:
        corrupted_wide = _html(item_values={"wide": (("3-7", "420"), ("6-7", "0"), ("3-6", "1,370"))})
        exceptional = _html(item_values={"win": (("返還", "160"),)})
        empty = _html(item_markup={"win": "<li class='win'><dl><dt>単勝</dt><dd></dd></dl></li>"})
        for body, expected in (
            (corrupted_wide, JRATargetRacePayoutPersistenceValidationError),
            (exceptional, JRATargetRacePayoutPersistenceUnsupportedError),
            (empty, JRATargetRacePayoutPersistenceUnavailableError),
        ):
            with self.subTest(expected=expected):
                capture = _capture(body=body)
                repository = _PayoutRepository()
                with self.assertRaises(expected):
                    normalize_and_persist_jra_target_race_payout(
                        capture_id=capture.capture_id,
                        capture_archive=_Archive(capture),
                        snapshot=_snapshot(),
                        bet_type="ワイド" if body is corrupted_wide else "単勝",
                        payout_repository=repository,
                    )
                self.assertEqual(repository.saved, [])

    def test_static_scope_is_narrow_and_has_no_forbidden_ownership(self) -> None:
        source_path = Path(__file__).parents[1] / "scripts" / "simulation" / "jra_target_race_payout_persistence.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertEqual(
            {
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "normalize_and_persist_jra_target_race_payout"
            },
            {"normalize_and_persist_jra_target_race_payout"},
        )
        for forbidden in (
            "requests",
            "httpx",
            "urllib",
            "sqlite3",
            "datetime.now",
            "date.today",
            "random",
            "except Exception",
            "except BaseException",
            "build_historical_prediction_pipeline",
            "PredictionPipeline",
            "PersistedRaceSimulationExecutor",
            "Simulator",
            "normalize_and_persist_jra_target_race_result",
            "save_capture",
            "get_latest_payout_publication",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("build_jra_external_entry_id", source)
        self.assertIn("load_capture", source)
        self.assertIn("save_payout_publication", source)


if __name__ == "__main__":
    unittest.main()
