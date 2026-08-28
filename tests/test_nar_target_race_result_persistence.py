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
from scripts.simulation.nar_official_response_capture import (
    NAROfficialPageKind,
    NAROfficialResponseCapture,
)
from scripts.simulation.nar_target_race_result_persistence import (
    NARTargetRaceResultPersistenceError,
    NARTargetRaceResultPersistenceUnavailableError,
    NARTargetRaceResultPersistenceUnsupportedError,
    NARTargetRaceResultPersistenceValidationError,
    normalize_and_persist_nar_target_race_result,
)
from scripts.simulation.repositories.interfaces import (
    PersistedRaceResult,
    RaceResultEntryStatus,
    RaceResultRepository,
    RaceResultStatus,
)


UTC = timezone.utc
CAPTURE_TIME = datetime(2026, 8, 27, 15, 41, 31, tzinfo=UTC)
SNAPSHOT_TIME = datetime(2026, 5, 2, 12, tzinfo=UTC)
URL = (
    "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?"
    "k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1"
)
RACE_ID = "nar:20260503:31:1"
FINALITY = "※2026年4月以降、優勝馬の情報はレース終了翌日までに表示されます。また、優勝馬の情報はレース結果確定時点の情報となります。"
HEADINGS = (
    ("a", "着順"), ("b", "枠"), ("c", "馬番"), ("d", "馬名"), ("e", "所属"), ("f", "性齢"),
    ("g", "負担<br>重量"), ("h", "騎手<span>（所属）</span>"), ("i", "調教師"),
    ("j", "馬体重<br><span>（増減）</span>"), ("k", "タイム"), ("l", "着差"),
    ("m", "上がり<br>3F"), ("n", "コーナー<br>通過順"), ("o", "人気"), ("p", "単勝<br>オッズ"),
)


class _Archive:
    def __init__(self, value: object) -> None:
        self.value = value
        self.calls: list[str] = []
        self.error: BaseException | None = None

    def load_capture(self, *, capture_id: str) -> NAROfficialResponseCapture | None:
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
        "https://evidence.example.test/nar",
        "b" * 64,
        None,
        SNAPSHOT_TIME - timedelta(minutes=1),
    )


def _snapshot(
    *,
    horse_numbers: tuple[int, ...] = (1, 2, 3),
    source_race_id: str = RACE_ID,
    entry_race_id: str | None = None,
    entry_id_suffix: int | None = None,
    organization: str = "NAR",
    duplicate_entry_id: bool = False,
) -> HistoricalInputSnapshot:
    source = HistoricalSourceIdentity(organization, "nar_official", source_race_id, URL)
    external_race = HistoricalExternalRaceIdentity(organization, "nar_official", entry_race_id or source_race_id)
    entries = tuple(
        HistoricalRaceEntrySnapshot(
            race_entry_id=1000 + (1 if duplicate_entry_id else horse_no),
            external_entry_identity=HistoricalExternalEntryIdentity(
                external_race,
                f"{entry_race_id or source_race_id}:entry:{horse_no if entry_id_suffix is None or horse_no != horse_numbers[0] else entry_id_suffix}",
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
        HistoricalInputProvenance("track", "track", "nar_official", "track", None, (_evidence("track"),)),
    ]
    for entry in entries:
        entry_id = entry.race_entry_id
        provenance.extend(
            (
                HistoricalInputProvenance("entry", f"entry/{entry_id}", "nar_official", f"entry-{entry_id}", entry_id, (_evidence("entry"),)),
                HistoricalInputProvenance("odds", f"odds/{entry_id}", "nar_official", f"odds-{entry_id}", entry_id, (_evidence("odds_win"),)),
                HistoricalInputProvenance("jockey", f"jockey/{entry_id}", "nar_official", f"jockey-{entry_id}", entry_id, (_evidence("jockey"),)),
                HistoricalInputProvenance("past_race", f"past_race/{entry_id}/none", "nar_official", f"absence-{entry_id}", entry_id, (_evidence("past_race_absence_query"),)),
            )
        )
    return HistoricalInputSnapshot(
        identity=HistoricalInputSnapshotIdentity("dataset-nar", source, SNAPSHOT_TIME),
        internal_race_id=800,
        information_cutoff=SNAPSHOT_TIME + timedelta(hours=1),
        race=HistoricalRaceSnapshot(
            target_race_date=date(2026, 5, 3),
            scheduled_start_at=datetime(2026, 5, 3, 3, tzinfo=UTC),
            place="高知",
            distance_m=1400,
            track="ダート",
            track_condition="不良",
        ),
        entries=entries,
        past_races=(),
        provenance=tuple(provenance),
    )


def _row(horse_no: int, finish: object, *, row_class: str = "tBorder", extra: str = "") -> str:
    values = (finish, "1", horse_no, "馬", "高知", "牡 4", "56.0", "騎手", "調教師", "500 (0)", "1:30.0", "", "40.0", "1-1-1-1", "1", "2.0")
    classes = ("a", "b courseNum course_01", "c", "d horseName", "e", "f", "g", "h jockeyName", "i", "j horseWeight", "k", "l", "m", "n corner_position", "o", "p")
    cells = "".join(f"<td class='{css}'>{value}</td>" for css, value in zip(classes, values, strict=True))
    return f"<tr class='{row_class}'>{cells}{extra}</tr>"


def _winner(*, populated: bool = True, heading: str = "優勝馬情報") -> str:
    if not populated:
        return f"<section class='winHorseTable'><h4><span class='smallTitle'>{heading}</span></h4></section>"
    return (
        "<section class='winHorseTable'><h4><span class='smallTitle'>" + heading + "</span></h4>"
        "<h3>勝馬<span class='smallFont01'>牡</span><span class='smallFont03'>4</span><a class='cNaviBtn'>馬出走履歴</a></h3>"
        "<table class='infoAndBonus'><tr><td>馬情報</td></tr></table>"
        "<table class='pedigreeTable'><tr><td>血統表</td></tr></table>"
        "<table class='horseGrade'><tr><td>生涯成績</td></tr></table></section>"
    )


def _html(
    *,
    horse_numbers: tuple[int, ...] = (1, 2, 3),
    finishes: tuple[object, ...] | None = None,
    place: str = "高 知",
    active_place: str = "高知",
    heading: str = "2026年5月3日（日） 高 知 第1競走 競走成績",
    table_count: int = 1,
    include_thead: bool = False,
    extra_table_content: str = "",
    extra_tbody_content: str = "",
    row_extra: str = "",
    winner_count: int = 1,
    winner_populated: bool = True,
    winner_heading: str = "優勝馬情報",
    finality_count: int = 1,
    finality: str = FINALITY,
) -> bytes:
    positions = finishes if finishes is not None else tuple(range(1, len(horse_numbers) + 1))
    headers = "".join(f"<th class='{css}'>{value}</th>" for css, value in HEADINGS)
    rows = "".join(_row(horse, finish, extra=row_extra) for horse, finish in zip(horse_numbers, positions, strict=True))
    table = f"<section class='gradeTable'><table>{extra_table_content}<tbody><tr>{headers}</tr>{rows}{extra_tbody_content}</tbody></table></section>"
    if include_thead:
        table = table.replace("<table>", "<table><thead><tr><th>x</th></tr></thead>", 1)
    attention = "".join(f"<p>{finality}</p>" for _ in range(finality_count))
    return (
        "<html><body><div class='chartNavi trackNameNavi'><a class='cNaviBtn courseBtn active'>" + active_place + "</a></div>"
        "<article class='raceResult'><div class='innerWrapper'><h4>" + heading + "</h4>" + table * table_count
        + "".join(_winner(populated=winner_populated, heading=winner_heading) for _ in range(winner_count))
        + "</div></article><article class='attention'><div class='innerWrapper'>" + attention + "</div></article></body></html>"
    ).encode("utf-8")


def _capture(*, body: bytes | None = None, url: str = URL) -> NAROfficialResponseCapture:
    return NAROfficialResponseCapture(
        canonical_source_url=url,
        response_body=_html() if body is None else body,
        charset="utf-8",
        requested_at=CAPTURE_TIME - timedelta(seconds=1),
        observed_at=CAPTURE_TIME,
        stored_at=CAPTURE_TIME + timedelta(seconds=1),
        http_status=200,
        content_type="text/html; charset=UTF-8",
    )


def _invoke(*, capture: object | None = None, snapshot: HistoricalInputSnapshot | None = None, capture_id: str | None = None) -> tuple[PersistedRaceResult, _Archive, _RaceResultRepository]:
    supplied = _capture() if capture is None else capture
    archive = _Archive(supplied)
    repository = _RaceResultRepository()
    actual_capture_id = supplied.capture_id if isinstance(supplied, NAROfficialResponseCapture) else "capture-id"
    result = normalize_and_persist_nar_target_race_result(
        capture_id=actual_capture_id if capture_id is None else capture_id,
        capture_archive=archive,
        snapshot=_snapshot() if snapshot is None else snapshot,
        race_result_repository=repository,
    )
    return result, archive, repository


class NARTargetRaceResultPersistenceTests(unittest.TestCase):
    def _assert_no_save(self, body: bytes, *, snapshot: HistoricalInputSnapshot | None = None, error: type[Exception] = NARTargetRaceResultPersistenceError) -> None:
        capture = _capture(body=body)
        archive = _Archive(capture)
        repository = _RaceResultRepository()
        with self.assertRaises(error):
            normalize_and_persist_nar_target_race_result(
                capture_id=capture.capture_id,
                capture_archive=archive,
                snapshot=_snapshot() if snapshot is None else snapshot,
                race_result_repository=repository,
            )
        self.assertEqual(archive.calls, [capture.capture_id])
        self.assertEqual(repository.saved, [])

    def test_public_surface_and_signature_are_exact(self) -> None:
        import scripts.simulation.nar_target_race_result_persistence as module

        self.assertEqual(
            module.__all__,
            (
                "NARTargetRaceResultPersistenceError",
                "NARTargetRaceResultPersistenceValidationError",
                "NARTargetRaceResultPersistenceUnavailableError",
                "NARTargetRaceResultPersistenceUnsupportedError",
                "normalize_and_persist_nar_target_race_result",
            ),
        )
        self.assertFalse(hasattr(simulation_package, "normalize_and_persist_nar_target_race_result"))
        signature = inspect.signature(normalize_and_persist_nar_target_race_result)
        self.assertEqual(tuple(signature.parameters), ("capture_id", "capture_archive", "snapshot", "race_result_repository"))
        self.assertTrue(all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values()))
        hints = get_type_hints(normalize_and_persist_nar_target_race_result)
        self.assertEqual(hints["capture_id"], str)
        self.assertEqual(hints["capture_archive"].__name__, "NAROfficialResponseCaptureArchive")
        self.assertEqual(hints["snapshot"], HistoricalInputSnapshot)
        self.assertEqual(hints["race_result_repository"], RaceResultRepository)
        self.assertEqual(hints["return"], PersistedRaceResult)
        self.assertTrue(issubclass(NARTargetRaceResultPersistenceValidationError, NARTargetRaceResultPersistenceError))

    def test_normal_result_is_persisted_once_with_race_local_identity(self) -> None:
        result, archive, repository = _invoke()
        self.assertEqual(archive.calls, [_capture().capture_id])
        self.assertEqual(repository.saved, [result])
        self.assertEqual(result.race_id, 800)
        self.assertIs(result.result_status, RaceResultStatus.COMPLETE)
        self.assertEqual(result.observed_at, CAPTURE_TIME)
        self.assertEqual(result.finalized_at, CAPTURE_TIME)
        self.assertEqual(result.source, _capture().capture_id)
        self.assertEqual(
            {(item.horse_no, item.race_entry_id, item.finish_position, item.result_status) for item in result.entries},
            {(1, 1001, 1, RaceResultEntryStatus.CONFIRMED), (2, 1002, 2, RaceResultEntryStatus.CONFIRMED), (3, 1003, 3, RaceResultEntryStatus.CONFIRMED)},
        )

    def test_normal_result_derives_multiple_row_counts_and_row_order_is_not_identity(self) -> None:
        for horses, finishes in (((1, 2), (2, 1)), ((4, 2, 5, 1), (3, 2, 4, 1))):
            with self.subTest(horses=horses):
                result, _, repository = _invoke(capture=_capture(body=_html(horse_numbers=horses, finishes=finishes)), snapshot=_snapshot(horse_numbers=horses))
                self.assertEqual(len(result.entries), len(horses))
                self.assertEqual({item.finish_position for item in result.entries}, set(range(1, len(horses) + 1)))
                self.assertEqual(repository.saved, [result])

    def test_public_boundary_failures_happen_before_archive_io(self) -> None:
        archive = _Archive(_capture())
        repository = _RaceResultRepository()
        cases = (("", archive, _snapshot(), repository), ("x", object(), _snapshot(), repository), ("x", archive, object(), repository), ("x", archive, _snapshot(), object()))
        for capture_id, source, snapshot, target_repository in cases:
            with self.subTest(capture_id=capture_id), self.assertRaises(ValueError):
                normalize_and_persist_nar_target_race_result(capture_id=capture_id, capture_archive=source, snapshot=snapshot, race_result_repository=target_repository)  # type: ignore[arg-type]
        self.assertEqual(archive.calls, [])
        self.assertEqual(repository.saved, [])

    def test_archive_failure_modes_fail_closed(self) -> None:
        cases: tuple[tuple[object, BaseException | None, str, type[Exception]], ...] = (
            (None, None, _capture().capture_id, NARTargetRaceResultPersistenceUnavailableError),
            (object(), None, _capture().capture_id, NARTargetRaceResultPersistenceValidationError),
            (_capture(), None, "different", NARTargetRaceResultPersistenceValidationError),
            (_capture(url="https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1"), None, "", NARTargetRaceResultPersistenceValidationError),
            (_capture(), RuntimeError("archive"), _capture().capture_id, RuntimeError),
        )
        for supplied, error, capture_id, expected in cases:
            with self.subTest(supplied=type(supplied).__name__, error=error):
                archive = _Archive(supplied)
                archive.error = error
                repository = _RaceResultRepository()
                requested = capture_id or (supplied.capture_id if isinstance(supplied, NAROfficialResponseCapture) else _capture().capture_id)
                with self.assertRaises(expected) as raised:
                    normalize_and_persist_nar_target_race_result(capture_id=requested, capture_archive=archive, snapshot=_snapshot(), race_result_repository=repository)
                if error is not None:
                    self.assertIs(raised.exception, error)
                self.assertEqual(len(archive.calls), 1)
                self.assertEqual(repository.saved, [])

    def test_identity_and_visible_header_fail_closed(self) -> None:
        cases = (
            (_html(heading="2026年5月4日（日） 高 知 第1競走 競走成績"), None),
            (_html(heading="2026年5月3日（日） 別場所 第1競走 競走成績"), None),
            (_html(heading="2026年5月3日（日） 高 知 第2競走 競走成績"), None),
            (_html(active_place="別場所"), None),
            (_html().replace(b"courseBtn active", b"courseBtn", 1), None),
            (_html().replace(b"</div><article class='raceResult'", "<a class='cNaviBtn courseBtn active'>高知</a></div><article class='raceResult'".encode(), 1), None),
            (_html(heading="X2026年5月3日（日） 高 知 第1競走 競走成績"), None),
            (_html(heading="2026年5月3日（日） 高 知 第11競走 競走成績"), None),
            (_html(heading="2026年5月3日（日） 高 知 X第1競走 競走成績"), None),
            (_html(heading="2026年5月3日（日） 高 知 第1競走X 競走成績"), None),
            (_html(heading="2026年5月3日（日） 高 知 第1競走 第2競走 競走成績"), None),
            (_html(), _snapshot(source_race_id="nar:20260503:31:2")),
        )
        for body, snapshot in cases:
            with self.subTest(body=body[:60]):
                self._assert_no_save(body, snapshot=snapshot)

    def test_table_header_and_row_structure_fail_closed(self) -> None:
        valid = _html()
        bodies = (
            valid.replace(b"<section class='gradeTable'><table>", b"", 1),
            _html(table_count=2),
            _html(include_thead=True),
            valid.replace(b"<tbody>", b"<tbody><div>x</div>", 1),
            valid.replace(b"</tbody>", b"</tbody><tbody></tbody>", 1),
            valid.replace(b"<th class='a'>", b"<th class='z'>", 1),
            valid.replace(b"<th class='p'>", b"", 1),
            valid.replace("着順".encode(), "着順X".encode(), 1),
            valid.replace(b"<th class='p'>", b"<th class='p'>X<span></span>", 1),
            valid.replace(b"<tr class='tBorder'>", b"<tr>", 1),
            valid.replace(b"<tr class='tBorder'>", b"<tr class='tBorder extra'>", 1),
            valid.replace(b"<td class='d horseName'>", b"<td class='z horseName'>", 1),
            valid.replace(b"<td class='d horseName'>", b"<td class='d horseName extra'>", 1),
            valid.replace(b"</td><td class='e'>", b"</td><td class='x'>extra</td><td class='e'>", 1),
            _html(row_extra="X"),
        )
        for body in bodies:
            with self.subTest(body=body[:70]):
                self._assert_no_save(body)

    def test_horse_number_and_finish_grammar_fail_closed(self) -> None:
        for horse, finish in (("0", 1), ("01", 1), ("+1", 1), ("1.0", 1), ("１", 1), ("1 0", 1), ("", 1), (1, "0"), (1, "01"), (1, "+1"), (1, "1.0"), (1, "１"), (1, "1 0"), (1, "同着")):
            with self.subTest(horse=horse, finish=finish):
                self._assert_no_save(_html(horse_numbers=(horse, 2, 3), finishes=(finish, 2, 3)))
        self._assert_no_save(_html(horse_numbers=(1, 1, 3)))
        self._assert_no_save(_html(finishes=(1, 1, 3)))
        self._assert_no_save(_html(finishes=(1, 2, 4)))

    def test_known_exceptional_row_markers_fail_closed_outside_finish_cell(self) -> None:
        for marker in ("取消", "除外", "中止", "失格", "降着"):
            with self.subTest(marker=marker):
                body = _html().replace(
                    b"<td class='l'></td>",
                    f"<td class='l'>{marker}</td>".encode("utf-8"),
                    1,
                )
                self._assert_no_save(
                    body,
                    error=NARTargetRaceResultPersistenceUnsupportedError,
                )

    def test_crosswalk_and_snapshot_coverage_fail_closed(self) -> None:
        self._assert_no_save(_html(horse_numbers=(1, 2, 4)), snapshot=_snapshot(horse_numbers=(1, 2, 3)))
        self._assert_no_save(_html(horse_numbers=(1, 2)), snapshot=_snapshot(horse_numbers=(1, 2, 3)))
        self._assert_no_save(_html(), snapshot=_snapshot(source_race_id="nar:20260503:31:2"))
        self._assert_no_save(_html(), snapshot=_snapshot(entry_id_suffix=99))
        self._assert_no_save(_html(), snapshot=_snapshot(organization="JRA"))

    def test_positive_finality_requires_populated_unique_winner_and_exact_statement(self) -> None:
        cases = (
            _html(winner_count=0),
            _html(winner_count=2),
            _html(winner_heading="優勝馬情報X"),
            _html().replace("<h4><span class='smallTitle'>優勝馬情報</span></h4>".encode(), b"<h4></h4>", 1),
            _html(winner_populated=False),
            _html(finality_count=0),
            _html(finality_count=2),
            _html(finality="結果確定"),
            _html(finality=FINALITY + "X"),
        )
        for body in cases:
            with self.subTest(body=body[-100:]):
                self._assert_no_save(body)

    def test_repository_error_propagates_after_one_save_attempt(self) -> None:
        capture = _capture()
        archive = _Archive(capture)
        repository = _RaceResultRepository()
        error = RuntimeError("repository")
        repository.error = error
        with self.assertRaises(RuntimeError) as raised:
            normalize_and_persist_nar_target_race_result(capture_id=capture.capture_id, capture_archive=archive, snapshot=_snapshot(), race_result_repository=repository)
        self.assertIs(raised.exception, error)
        self.assertEqual(archive.calls, [capture.capture_id])
        self.assertEqual(repository.saved, [])

    def test_static_ownership_is_narrow(self) -> None:
        import scripts.simulation.nar_target_race_result_persistence as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {"requests", "httpx", "sqlite3", "random", "time", "pathlib", "subprocess"}
        self.assertFalse(any(
            (isinstance(node, ast.Import) and any(alias.name.split(".")[0] in forbidden for alias in node.names))
            or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden)
            for node in ast.walk(tree)
        ))
        self.assertNotIn("datetime.now", source)
        self.assertNotIn("except Exception", source)
        self.assertNotIn("except BaseException", source)
        self.assertNotIn("load_capture_for", source)
        self.assertNotIn("save_capture", source)
        self.assertNotIn("nar_historical_past_race_source", source)
        self.assertNotIn("_CANCELLATIONS", source)
        self.assertNotIn("HorseMarkInfo", source)
        self.assertNotIn("Prediction", source)
        self.assertNotIn("Payout", source)


if __name__ == "__main__":
    unittest.main()
