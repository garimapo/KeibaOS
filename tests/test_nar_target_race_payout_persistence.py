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
from scripts.simulation.nar_target_race_payout_persistence import (
    NARTargetRacePayoutPersistenceError,
    NARTargetRacePayoutPersistenceUnavailableError,
    NARTargetRacePayoutPersistenceUnsupportedError,
    NARTargetRacePayoutPersistenceValidationError,
    normalize_and_persist_nar_target_race_payout,
)
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutRepository,
    PayoutStatus,
)


UTC = timezone.utc
CAPTURE_TIME = datetime(2026, 8, 27, 15, 41, 31, tzinfo=UTC)
SNAPSHOT_TIME = datetime(2026, 5, 2, 12, tzinfo=UTC)
URL = (
    "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?"
    "k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1"
)
DEBA_URL = (
    "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?"
    "k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1"
)
RACE_ID = "nar:20260503:31:1"
FINALITY = (
    "※2026年4月以降、優勝馬の情報はレース終了翌日までに表示されます。"
    "また、優勝馬の情報はレース結果確定時点の情報となります。"
)
NORMAL_ROWS = {
    "単勝": (("8", "720円"),),
    "複勝": (("8", "180円"), ("10", "120円"), ("11", "150円")),
    "枠連複": (("7-8", "550円"),),
    "馬連複": (("8-10", "730円"),),
    "馬連単": (("8-10", "1,870円"),),
    "ワイド": (("8-10", "300円"), ("8-11", "410円"), ("10-11", "350円")),
    "三連複": (("8-10-11", "1,230円"),),
    "三連単": (("8-10-11", "6,440円"),),
}


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
        "https://evidence.example.test/nar",
        "b" * 64,
        None,
        SNAPSHOT_TIME - timedelta(minutes=1),
    )


def _snapshot(
    *,
    horse_numbers: tuple[int, ...] = (7, 8, 10, 11),
    source_race_id: str = RACE_ID,
    entry_race_id: str | None = None,
    organization: str = "NAR",
    source_system: str = "nar_official",
    race_entry_ids: dict[int, int] | None = None,
) -> HistoricalInputSnapshot:
    source = HistoricalSourceIdentity(organization, source_system, source_race_id, URL)
    external_race = HistoricalExternalRaceIdentity(organization, source_system, entry_race_id or source_race_id)
    entries = tuple(
        HistoricalRaceEntrySnapshot(
            race_entry_id=(race_entry_ids or {}).get(horse_no, 1000 + horse_no),
            external_entry_identity=HistoricalExternalEntryIdentity(
                external_race,
                f"{entry_race_id or source_race_id}:entry:{horse_no}",
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
        HistoricalInputProvenance("track", "track", source_system, "track", None, (_evidence("track"),)),
    ]
    for entry in entries:
        entry_id = entry.race_entry_id
        provenance.extend(
            (
                HistoricalInputProvenance("entry", f"entry/{entry_id}", source_system, f"entry-{entry_id}", entry_id, (_evidence("entry"),)),
                HistoricalInputProvenance("odds", f"odds/{entry_id}", source_system, f"odds-{entry_id}", entry_id, (_evidence("odds_win"),)),
                HistoricalInputProvenance("jockey", f"jockey/{entry_id}", source_system, f"jockey-{entry_id}", entry_id, (_evidence("jockey"),)),
                HistoricalInputProvenance("past_race", f"past_race/{entry_id}/none", source_system, f"absence-{entry_id}", entry_id, (_evidence("past_race_absence_query"),)),
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


def _group(label: str, rows: tuple[tuple[str, str], ...], selection_class: str, *, rowspan: str | None = None) -> str:
    result = []
    for index, (selection, amount) in enumerate(rows):
        title = (
            f"<td class='title' rowspan='{len(rows) if rowspan is None else rowspan}'>{label}</td>"
            if index == 0
            else ""
        )
        result.append(
            "<tr>"
            + title
            + f"<td class='{selection_class}'>{selection}</td>"
            + f"<td class='refundMoney'>{amount}</td>"
            + "<td class='c'>1人気</td></tr>"
        )
    return "".join(result)


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
    rows: dict[str, tuple[tuple[str, str], ...]] | None = None,
    heading: str = "2026年5月3日（日） 高 知 第1競走 競走成績",
    active_place: str = "高知",
    payout_heading: str = "払戻金",
    finality: str = FINALITY,
    finality_count: int = 1,
    winner_count: int = 1,
    winner_populated: bool = True,
) -> bytes:
    values = dict(NORMAL_ROWS)
    if rows:
        values.update(rows)
    first = "".join(_group(label, values[label], "a") for label in ("単勝", "複勝", "枠連複", "馬連複"))
    second = "".join(_group(label, values[label], "d") for label in ("馬連単", "ワイド", "三連複", "三連単"))
    payout = (
        "<section class='newRefundTable'><h4><span class='smallTitle'>" + payout_heading + "</span></h4>"
        "<div class='twoRefundTable'><table><tbody>" + first + "</tbody></table>"
        "<table><tbody>" + second + "</tbody></table></div></section>"
    )
    attention = "".join(f"<p>{finality}</p>" for _ in range(finality_count))
    return (
        "<html><body><div class='chartNavi trackNameNavi'><a class='cNaviBtn courseBtn active'>"
        + active_place
        + "</a></div><article class='raceResult'><div class='innerWrapper'><h4>"
        + heading
        + "</h4>"
        + payout
        + "".join(_winner(populated=winner_populated) for _ in range(winner_count))
        + "</div></article><article class='attention'><div class='innerWrapper'>"
        + attention
        + "</div></article></body></html>"
    ).encode("utf-8")


def _capture(*, body: bytes | None = None, url: str = URL, offset: int = 0) -> NAROfficialResponseCapture:
    observed = CAPTURE_TIME + timedelta(seconds=offset)
    return NAROfficialResponseCapture(
        canonical_source_url=url,
        response_body=_html() if body is None else body,
        charset="utf-8",
        requested_at=observed - timedelta(seconds=1),
        observed_at=observed,
        stored_at=observed + timedelta(seconds=1),
        http_status=200,
        content_type="text/html; charset=UTF-8",
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
    capture_id = supplied.capture_id if isinstance(supplied, NAROfficialResponseCapture) else "capture-id"
    result = normalize_and_persist_nar_target_race_payout(
        capture_id=capture_id,
        capture_archive=archive,
        snapshot=_snapshot() if snapshot is None else snapshot,
        bet_type=bet_type,
        payout_repository=repository,
    )
    return result, archive, repository


class NARTargetRacePayoutPersistenceTests(unittest.TestCase):
    def _assert_no_save(
        self,
        body: bytes,
        *,
        bet_type: str = "単勝",
        snapshot: HistoricalInputSnapshot | None = None,
        error: type[Exception] = NARTargetRacePayoutPersistenceError,
    ) -> None:
        capture = _capture(body=body)
        archive = _Archive(capture)
        repository = _PayoutRepository()
        with self.assertRaises(error):
            normalize_and_persist_nar_target_race_payout(
                capture_id=capture.capture_id,
                capture_archive=archive,
                snapshot=_snapshot() if snapshot is None else snapshot,
                bet_type=bet_type,
                payout_repository=repository,
            )
        self.assertEqual(archive.calls, [capture.capture_id])
        self.assertEqual(repository.saved, [])

    def test_public_surface_signature_hints_and_hierarchy_are_exact(self) -> None:
        import scripts.simulation.nar_target_race_payout_persistence as module

        self.assertEqual(
            module.__all__,
            (
                "NARTargetRacePayoutPersistenceError",
                "NARTargetRacePayoutPersistenceValidationError",
                "NARTargetRacePayoutPersistenceUnavailableError",
                "NARTargetRacePayoutPersistenceUnsupportedError",
                "normalize_and_persist_nar_target_race_payout",
            ),
        )
        self.assertFalse(hasattr(simulation_package, "normalize_and_persist_nar_target_race_payout"))
        signature = inspect.signature(normalize_and_persist_nar_target_race_payout)
        self.assertEqual(
            tuple(signature.parameters),
            ("capture_id", "capture_archive", "snapshot", "bet_type", "payout_repository"),
        )
        self.assertTrue(all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values()))
        hints = get_type_hints(normalize_and_persist_nar_target_race_payout)
        self.assertEqual(hints["capture_id"], str)
        self.assertEqual(hints["capture_archive"].__name__, "NAROfficialResponseCaptureArchive")
        self.assertEqual(hints["snapshot"], HistoricalInputSnapshot)
        self.assertEqual(hints["bet_type"], str)
        self.assertEqual(hints["payout_repository"], PayoutRepository)
        self.assertEqual(hints["return"], PayoutPublication)
        for error_type in (
            NARTargetRacePayoutPersistenceValidationError,
            NARTargetRacePayoutPersistenceUnavailableError,
            NARTargetRacePayoutPersistenceUnsupportedError,
        ):
            self.assertTrue(issubclass(error_type, NARTargetRacePayoutPersistenceError))

    def test_all_supported_normal_types_persist_exact_complete_publications(self) -> None:
        expected = {
            "単勝": (((1008,), 720),),
            "馬連": (((1008, 1010), 730),),
            "ワイド": (((1008, 1010), 300), ((1008, 1011), 410), ((1010, 1011), 350)),
            "3連複": (((1008, 1010, 1011), 1230),),
        }
        for bet_type, expected_records in expected.items():
            with self.subTest(bet_type=bet_type):
                publication, archive, repository = _run(bet_type=bet_type)
                self.assertEqual(archive.calls, [_capture().capture_id])
                self.assertEqual(repository.saved, [publication])
                self.assertEqual(publication.race_id, 800)
                self.assertEqual(publication.bet_type, bet_type)
                self.assertEqual(publication.observed_at, CAPTURE_TIME)
                self.assertEqual(publication.finalized_at, CAPTURE_TIME)
                self.assertTrue(publication.is_complete)
                self.assertEqual(publication.source, _capture().capture_id)
                self.assertEqual(publication.source_url, URL)
                self.assertEqual(
                    tuple((record.race_entry_ids, record.payout_per_100) for record in publication.entries),
                    expected_records,
                )
                self.assertEqual({record.payout_status for record in publication.entries}, {PayoutStatus.WINNING})

    def test_repository_return_identity_and_exception_propagate(self) -> None:
        capture = _capture()
        archive = _Archive(capture)
        repository = _PayoutRepository()
        expected = PayoutPublication(
            race_id=800,
            bet_type="単勝",
            finalized_at=CAPTURE_TIME,
            observed_at=CAPTURE_TIME,
            is_complete=True,
            source=capture.capture_id,
            entries=(PayoutRecord((1008,), 720, PayoutStatus.WINNING),),
            source_url=URL,
            publication_id=91,
        )
        repository.return_value = expected
        actual = normalize_and_persist_nar_target_race_payout(
            capture_id=capture.capture_id,
            capture_archive=archive,
            snapshot=_snapshot(),
            bet_type="単勝",
            payout_repository=repository,
        )
        self.assertIs(actual, expected)
        failure = RuntimeError("save")
        repository = _PayoutRepository()
        repository.error = failure
        with self.assertRaises(RuntimeError) as raised:
            normalize_and_persist_nar_target_race_payout(
                capture_id=capture.capture_id,
                capture_archive=_Archive(capture),
                snapshot=_snapshot(),
                bet_type="単勝",
                payout_repository=repository,
            )
        self.assertIs(raised.exception, failure)
        self.assertEqual(len(repository.saved), 1)

    def test_invalid_public_arguments_fail_before_archive_io(self) -> None:
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
            with self.subTest(bet_type=bet_type), self.assertRaises(ValueError):
                normalize_and_persist_nar_target_race_payout(
                    capture_id=capture_id,
                    capture_archive=supplied_archive,  # type: ignore[arg-type]
                    snapshot=snapshot,  # type: ignore[arg-type]
                    bet_type=bet_type,
                    payout_repository=supplied_repository,  # type: ignore[arg-type]
                )
        self.assertEqual(archive.calls, [])
        self.assertEqual(repository.saved, [])

    def test_archive_boundary_is_exact_and_fail_closed(self) -> None:
        wrong_page = _capture(url=DEBA_URL)
        different = _capture(offset=2)
        cases: tuple[tuple[object, BaseException | None, str, type[Exception]], ...] = (
            (None, None, _capture().capture_id, NARTargetRacePayoutPersistenceUnavailableError),
            (object(), None, _capture().capture_id, NARTargetRacePayoutPersistenceValidationError),
            (different, None, _capture().capture_id, NARTargetRacePayoutPersistenceValidationError),
            (wrong_page, None, wrong_page.capture_id, NARTargetRacePayoutPersistenceValidationError),
            (_capture(), RuntimeError("archive"), _capture().capture_id, RuntimeError),
        )
        for supplied, error, capture_id, expected in cases:
            with self.subTest(expected=expected.__name__):
                archive = _Archive(supplied)
                archive.error = error
                repository = _PayoutRepository()
                with self.assertRaises(expected) as raised:
                    normalize_and_persist_nar_target_race_payout(
                        capture_id=capture_id,
                        capture_archive=archive,
                        snapshot=_snapshot(),
                        bet_type="単勝",
                        payout_repository=repository,
                    )
                if error is not None:
                    self.assertIs(raised.exception, error)
                self.assertEqual(archive.calls, [capture_id])
                self.assertEqual(repository.saved, [])

    def test_race_and_visible_identity_mismatches_never_save(self) -> None:
        cases = (
            (_html(heading="2026年5月4日（日） 高 知 第1競走 競走成績"), None),
            (_html(heading="2026年5月3日（日） 別場所 第1競走 競走成績"), None),
            (_html(heading="2026年5月3日（日） 高 知 第2競走 競走成績"), None),
            (_html(heading="X2026年5月3日（日） 高 知 第1競走 競走成績"), None),
            (_html(heading="2026年5月3日（日） 高 知 第11競走 競走成績"), None),
            (_html(heading="2026年5月3日（日） 高 知 第1競走X 競走成績"), None),
            (_html(active_place="別場所"), None),
            (_html(), _snapshot(source_race_id="nar:20260503:31:2")),
            (_html(), _snapshot(organization="JRA")),
            (_html(), _snapshot(source_system="other")),
        )
        for body, snapshot in cases:
            with self.subTest(body=body[:70]):
                self._assert_no_save(body, snapshot=snapshot)
        valid = _html().replace(
            b"</div><article class='raceResult'>",
            "<a class='cNaviBtn courseBtn active'>高知</a></div><article class='raceResult'>".encode(),
            1,
        )
        self._assert_no_save(valid)

    def test_payout_container_structure_is_exact(self) -> None:
        valid = _html()
        cases = (
            valid.replace(b"<section class='newRefundTable'>", b"", 1),
            valid.replace(b"</section><section class='winHorseTable'>", b"</section><section class='newRefundTable'></section><section class='winHorseTable'>", 1),
            valid.replace(b"<section class='newRefundTable'>", b"<section class='newRefundTable extra'>", 1),
            valid.replace(b"<section class='newRefundTable'><h4>", b"<section class='newRefundTable'><div></div><h4>", 1),
            valid.replace(b"<section class='newRefundTable'><h4>", b"<section class='newRefundTable'><h4 class='extra'>", 1),
            valid.replace("払戻金".encode(), "払戻金X".encode(), 1),
            valid.replace(b"<div class='twoRefundTable'>", b"<div class='twoRefundTable' id='extra'>", 1),
            valid.replace(b"<div class='twoRefundTable'>", b"<div class='twoRefundTable'><div></div>", 1),
            valid.replace(b"</tbody></table><table><tbody>", b"</tbody></table><table></table><table><tbody>", 1),
            valid.replace(b"<table><tbody>", b"<table><thead></thead><tbody>", 1),
            valid.replace(b"<table><tbody>", b"<table><tbody></tbody><tbody>", 1),
            valid.replace(b"<tbody><tr>", b"<tbody><div></div><tr>", 1),
        )
        for body in cases:
            with self.subTest(body=body[:80]):
                self._assert_no_save(body)

    def test_group_boundaries_and_labels_are_exhaustively_classified(self) -> None:
        valid = _html()
        cases = (
            valid.replace("複勝".encode(), "未知".encode(), 1),
            valid.replace(b"rowspan='1'", b"rowspan='0'", 1),
            valid.replace(b"rowspan='1'", b"rowspan='+1'", 1),
            valid.replace(b"rowspan='1'", "rowspan='１'".encode(), 1),
            valid.replace(b"rowspan='1'", b"rowspan='99'", 1),
            valid.replace(b"<td class='title' rowspan='3'>", b"<td class='title' rowspan='2'>", 1),
            valid.replace(b"<tr><td class='a'>10</td>", b"<tr><td class='title' rowspan='1'>X</td><td class='a'>10</td>", 1),
            valid.replace(b"<td class='title' rowspan='1'>", b"", 1),
            valid.replace(
                b"</tbody></table><table>",
                "<tr><td class='a'>8</td><td class='refundMoney'>100円</td><td class='c'>1人気</td></tr></tbody></table><table>".encode(),
                1,
            ),
            valid.replace(b"<tr><td class='title'", b"<tr class='x'><td class='title'", 1),
        )
        for body in cases:
            with self.subTest(body=body[:80]):
                self._assert_no_save(body)

    def test_exact_normal_row_counts_are_required(self) -> None:
        cases = (
            ("単勝", {"単勝": (("8", "720円"), ("10", "100円"))}),
            ("馬連", {"馬連複": (("8-10", "730円"), ("8-11", "500円"))}),
            ("ワイド", {"ワイド": (("8-10", "300円"), ("8-11", "410円"))}),
            ("ワイド", {"ワイド": (("8-10", "300円"), ("8-11", "410円"), ("10-11", "350円"), ("7-8", "500円"))}),
            ("3連複", {"三連複": (("8-10-11", "1,230円"), ("7-8-10", "900円"))}),
        )
        for bet_type, rows in cases:
            with self.subTest(bet_type=bet_type):
                self._assert_no_save(_html(rows=rows), bet_type=bet_type)

    def test_selection_grammar_and_exact_cell_class_fail_closed(self) -> None:
        invalid = ("0", "08", "+8", "8.0", "８", " 8", "8 ", "8/10", "8--10", "8-", "8-8", "8-10X")
        for value in invalid:
            with self.subTest(value=value):
                self._assert_no_save(_html(rows={"馬連複": ((value, "730円"),)}), bet_type="馬連")
        self._assert_no_save(_html(rows={"単勝": (("8-10", "720円"),)}), bet_type="単勝")
        self._assert_no_save(_html(rows={"三連複": (("8-10", "1,230円"),)}), bet_type="3連複")
        self._assert_no_save(
            _html().replace(b"<td class='a'>8-10</td>", b"<td class='d'>8-10</td>", 1),
            bet_type="馬連",
        )

    def test_amount_grammar_and_same_row_association_fail_closed(self) -> None:
        invalid = ("0円", "+720円", "-720円", "7.20円", "07円", "1,23円", "1,2300円", "720 円", "720", "720ドル", "720円X")
        for amount in invalid:
            with self.subTest(amount=amount):
                self._assert_no_save(_html(rows={"単勝": (("8", amount),)}))
        valid = _html()
        self._assert_no_save(valid.replace(b"<td class='refundMoney'>720", b"<td class='refundMoney'><span>720</span>", 1))
        self._assert_no_save(valid.replace(b"<td class='refundMoney'>720", b"<td class='refundMoney'>720</td><td class='refundMoney'>720", 1))
        self._assert_no_save(valid.replace(b"<td class='refundMoney'>720", b"<td class='x'>720", 1))

    def test_race_local_crosswalk_and_canonical_selection_are_exact(self) -> None:
        snapshot = _snapshot(race_entry_ids={8: 2008, 10: 1001})
        publication, _, repository = _run(bet_type="馬連", snapshot=snapshot)
        self.assertEqual(publication.entries[0].race_entry_ids, (1001, 2008))
        self.assertEqual(repository.saved, [publication])

        wrong_race = _snapshot()
        object.__setattr__(
            wrong_race.entries[0].external_entry_identity.external_race_identity,
            "external_race_id",
            "nar:20260503:31:2",
        )
        cases = (
            _snapshot(horse_numbers=(7, 8, 10)),
            wrong_race,
        )
        for supplied in cases:
            with self.subTest(entries=len(supplied.entries)):
                self._assert_no_save(_html(), bet_type="3連複", snapshot=supplied)
        duplicate_external = _snapshot()
        object.__setattr__(
            duplicate_external.entries[1].external_entry_identity,
            "external_entry_id",
            duplicate_external.entries[0].external_entry_identity.external_entry_id,
        )
        self._assert_no_save(_html(), snapshot=duplicate_external)
        duplicate_internal = _snapshot()
        object.__setattr__(duplicate_internal.entries[1], "race_entry_id", duplicate_internal.entries[0].race_entry_id)
        self._assert_no_save(_html(), snapshot=duplicate_internal)

    def test_duplicate_canonical_selection_and_wide_partial_failure_never_save(self) -> None:
        self._assert_no_save(
            _html(rows={"ワイド": (("8-10", "300円"), ("10-8", "410円"), ("10-11", "350円"))}),
            bet_type="ワイド",
        )
        self._assert_no_save(
            _html(rows={"ワイド": (("8-10", "300円"), ("8-11", "bad"), ("10-11", "350円"))}),
            bet_type="ワイド",
        )

    def test_positive_finality_is_required_from_same_capture(self) -> None:
        valid = _html()
        cases = (
            _html(winner_count=0),
            _html(winner_count=2),
            _html(winner_populated=False),
            valid.replace("優勝馬情報".encode(), "優勝馬情報X".encode(), 1),
            _html(finality_count=0),
            _html(finality_count=2),
            _html(finality=FINALITY.replace("確定時点", "確定")),
        )
        for body in cases:
            with self.subTest(body=body[-100:]):
                self._assert_no_save(body)

    def test_known_exceptional_representations_are_unsupported_and_never_saved(self) -> None:
        for marker in ("返還", "不成立", "同着", "特払い"):
            with self.subTest(marker=marker):
                self._assert_no_save(
                    _html(rows={"単勝": ((marker, "720円"),)}),
                    error=NARTargetRacePayoutPersistenceUnsupportedError,
                )
                self._assert_no_save(
                    _html(rows={"単勝": (("8", marker),)}),
                    error=NARTargetRacePayoutPersistenceUnsupportedError,
                )

    def test_static_ownership_is_narrow_and_has_no_forbidden_dependencies(self) -> None:
        path = Path(__file__).parents[1] / "scripts" / "simulation" / "nar_target_race_payout_persistence.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_imports = {"requests", "httpx", "urllib", "sqlite3", "random", "time", "pathlib", "subprocess"}
        self.assertFalse(
            any(
                (isinstance(node, ast.Import) and any(alias.name.split(".")[0] in forbidden_imports for alias in node.names))
                or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden_imports)
                for node in ast.walk(tree)
            )
        )
        for forbidden in (
            "datetime.now",
            "except Exception",
            "except BaseException",
            "get_latest",
            "save_capture",
            "normalize_and_persist_nar_target_race_result",
            "RaceResultRepository",
            "Prediction",
            "settlement",
            "beginner/step6.html",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
