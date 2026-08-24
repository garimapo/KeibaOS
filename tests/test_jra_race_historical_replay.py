from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime, timedelta, timezone
import inspect
from pathlib import Path
import sqlite3
from unittest.mock import Mock

import pytest

from scripts.migrations.runner import apply_migrations
import scripts.simulation.jra_race_historical_replay as _module
from scripts.simulation.historical_input_snapshot_builder import (
    HistoricalInputSnapshotAssemblyError,
)
from scripts.simulation.jra_historical_input_source_collection import (
    JRAHistoricalSourceCollection,
    JRAHistoricalSourceCollectionUnavailableError,
    JRAHistoricalSourceCollectionUnsupportedError,
    JRAHistoricalSourceCollectionValidationError,
)
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialTargetRaceCardResponseCapture,
    JRASuppliedOfficialResponse,
    JRATargetRaceSelectionResponseCapture,
)
from scripts.simulation.jra_official_response_capture_migration_runner import (
    apply_jra_capture_schema_migrations,
)
from scripts.simulation.jra_official_response_live_capture import (
    JRATargetRaceNavigationCaptureResult,
)
from scripts.simulation.jra_race_historical_replay import (
    JRARaceHistoricalReplayError,
    JRARaceHistoricalReplayResult,
    JRARaceHistoricalReplayUnavailableError,
    JRARaceHistoricalReplayUnsupportedError,
    JRARaceHistoricalReplayValidationError,
    build_jra_race_historical_replay,
)
from scripts.simulation.jra_race_replay_seed import (
    JRARaceReplaySeed,
    JRARaceReplaySeedEntry,
    build_jra_race_replay_seed,
)
from scripts.simulation.jra_target_horse_history_resolution import (
    JRATargetHorseHistoryResolutionUnavailableError,
    JRATargetHorseHistoryResolutionValidationError,
)
from scripts.simulation.jra_target_race_card_locator import (
    build_jra_target_race_selection_request_locator,
)
from scripts.simulation.jra_target_race_card_resolution import (
    JRATargetRaceCardResolutionUnavailableError,
    JRATargetRaceCardResolutionValidationError,
    resolve_jra_target_race_card_response,
)
from scripts.simulation.jra_target_race_input_source import (
    JRATargetRaceSourceUnsupportedError,
    JRATargetRaceSourceValidationError,
    normalize_jra_target_race_input_source_records,
)
from scripts.simulation.repositories.errors import RepositoryDataIntegrityError
from scripts.simulation.repositories.sqlite_jra_official_response_capture_repository import (
    SQLiteJRAOfficialResponseCaptureRepository,
)
from scripts.simulation.repositories.sqlite_jra_race_replay_seed_repository import (
    SQLiteJRARaceReplaySeedRepository,
)


UTC = timezone.utc
RACE_ID = "jra:race:2025:05:01:01:01"
RACE_CNAME = "pw01drl00052025010120250105/AB"
RAW_CARD_URL = "/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105/AB"
CARD_URL = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105%2FAB"
OTHER_CARD_URL = CARD_URL.replace("%2FAB", "%2FAC")
OBSERVED = datetime(2025, 1, 5, 1, 0, tzinfo=UTC)
CAPTURED = datetime(2025, 1, 5, 2, 0, tzinfo=UTC)
CUTOFF = datetime(2025, 1, 5, 3, 0, tzinfo=UTC)
SCHEDULED = datetime(2025, 1, 5, 6, 0, tzinfo=UTC)
STORED = datetime(2025, 1, 5, 8, 0, tzinfo=UTC)


def _horse_key(number: int) -> str:
    return f"123456789{number - 1}"


def _horse_id(number: int) -> str:
    return f"jra:horse:{_horse_key(number)}"


def _entry_id(number: int) -> str:
    return f"{RACE_ID}:entry:{number}"


def _profile_url(number: int) -> str:
    return (
        "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud00"
        f"{_horse_key(number)}%2FAB"
    )


def _selection_body(*, raw_url: str = RAW_CARD_URL) -> bytes:
    return (
        '<div id="contentsBody"><div class="race_select"><table id="race_list" '
        'class="basic mt20"><tbody><tr><th class="race_num"><a href="'
        + raw_url
        + '">1R</a></th><td class="syutsuba"><a class="btn-def btn-sm btn-narrow" href="'
        + raw_url
        + '">出馬表</a></td></tr></tbody></table></div></div>'
    ).encode("cp932")


def _target_row(number: int) -> str:
    return f'''<tr><td class="num">{number}</td><td class="horse"><div class="name_line"><div class="name"><a href="/JRADB/accessU.html?CNAME=pw01dud00{_horse_key(number)}%2FAB">horse</a></div><div class="odds"><div class="odds_line"><span class="num">{number + 1}.5</span></div></div></div></td><td class="jockey"><p class="jockey">騎手 {number}</p></td></tr>'''


def _target_body(*, numbers: tuple[int, ...] = (1,), race_name: str = "テストレース") -> bytes:
    rows = "".join(_target_row(number) for number in numbers)
    return f'''<div id="contentsBody"><div class="line main"><div class="inner"><h1>1レース</h1></div></div><div class="syutsuba"><table class="basic narrow-xy mt20"><caption><div class="race_header"><div class="left"><div class="date_line"><div class="inner"><div class="cell date">2025年1月5日(日) 1回東京1日</div><div class="cell time"><strong>15時00分</strong></div></div></div></div><div class="race_title"><div class="inner"><div class="txt"><span class="main"><span class="race_name">{race_name}</span></span></div></div><div class="type"><div class="cell course">コース：1600メートル（芝・左）</div><div class="cell class">3歳1勝</div></div></div><div class="cell baba"><ul><li class="turf"><span class="cap">芝</span><span class="txt">良</span></li><li class="weather"><span class="inner"><span class="txt">晴</span></span></li></ul></div></div></caption><tbody>{rows}</tbody></table></div></div>'''.encode("cp932")


def _zero_history_body() -> bytes:
    def aggregate(caption: str) -> str:
        return (
            '<table class="basic narrow"><caption class="simple"><div class="main">'
            + caption
            + '</div></caption><tbody><tr><td>該当するデータがありません。</td></tr></tbody></table>'
        )

    return (
        '<html><body><div class="race_detail"><p><strong>該当するデータがありません。</strong></p></div>'
        '<ul><li id="result_unit"><div class="contents_header"><h2>レース条件別成績</h2></div>'
        '<div class="race_data mt10"><div class="layout_grid"><div class="cell left">'
        + aggregate("平地レース合計")
        + '</div><div class="cell right">'
        + aggregate("障害レース合計")
        + "</div></div></div></li></ul></body></html>"
    ).encode("cp932")


def _selection_capture() -> JRATargetRaceSelectionResponseCapture:
    return JRATargetRaceSelectionResponseCapture(
        request_locator=build_jra_target_race_selection_request_locator(cname=RACE_CNAME),
        response_body=_selection_body(),
        charset="cp932",
        requested_at=OBSERVED,
        observed_at=OBSERVED,
        stored_at=STORED,
        http_status=200,
        content_type="text/html",
    )


def _card_capture(
    *,
    body: bytes | None = None,
    url: str = CARD_URL,
    observed: datetime = OBSERVED,
    stored: datetime = STORED,
) -> JRAOfficialTargetRaceCardResponseCapture:
    return JRAOfficialTargetRaceCardResponseCapture(
        canonical_source_url=url,
        response_body=_target_body() if body is None else body,
        charset="cp932",
        requested_at=observed,
        observed_at=observed,
        stored_at=stored,
        http_status=200,
        content_type="text/html",
    )


def _seed(
    *,
    card: JRAOfficialTargetRaceCardResponseCapture | None = None,
    numbers: tuple[int, ...] = (1,),
    cutoff: datetime = CUTOFF,
) -> JRARaceReplaySeed:
    card = _card_capture(body=_target_body(numbers=numbers)) if card is None else card
    return build_jra_race_replay_seed(
        dataset_id="dataset-jra-replay",
        external_race_id=RACE_ID,
        internal_race_id=77,
        target_race_selection_capture_id=_selection_capture().capture_id,
        target_race_card_capture_id=card.capture_id,
        target_race_card_response_sha256=card.response_sha256,
        canonical_target_race_card_url=card.canonical_source_url,
        captured_at=CAPTURED,
        information_cutoff=cutoff,
        entries=tuple(
            JRARaceReplaySeedEntry(
                entry_order=index,
                external_entry_id=_entry_id(number),
                external_horse_id=_horse_id(number),
                horse_no=number,
                internal_race_entry_id=100 + number,
            )
            for index, number in enumerate(numbers)
        ),
    )


def _horse_response(number: int) -> JRASuppliedOfficialResponse:
    return JRASuppliedOfficialResponse(
        response_url=_profile_url(number),
        response_body=_zero_history_body(),
        observed_at=OBSERVED,
    )


def _providers(
    *,
    seed: JRARaceReplaySeed,
    selection: object | None = None,
    card: object | None = None,
) -> dict[str, object]:
    actual_selection = _selection_capture() if selection is None else selection
    actual_card = _card_capture() if card is None else card

    def horse_provider(*, locator: object, observed_at_not_after: datetime) -> JRASuppliedOfficialResponse:
        number = next(
            entry.horse_no
            for entry in seed.entries
            if entry.external_horse_id == locator.external_horse_id  # type: ignore[attr-defined]
        )
        return _horse_response(number)

    return {
        "seed": seed,
        "target_race_selection_capture_provider": lambda **_: actual_selection,
        "target_race_card_capture_by_id_provider": lambda **_: actual_card,
        "horse_history_response_provider": horse_provider,
        "race_result_response_provider": lambda **_: pytest.fail("zero history must not request accessS"),
        "final_win_odds_response_provider": lambda **_: pytest.fail("zero history must not request accessO"),
    }


def _forge(value: object, **changes: object) -> object:
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
    return result


def _resolution(
    *,
    selection: JRATargetRaceSelectionResponseCapture | None = None,
    card: JRAOfficialTargetRaceCardResponseCapture | None = None,
) -> object:
    selection = _selection_capture() if selection is None else selection
    card = _card_capture() if card is None else card
    return resolve_jra_target_race_card_response(
        external_race_id=RACE_ID,
        target_race_selection_capture_id=selection.capture_id,
        captured_at=CAPTURED,
        target_race_selection_capture_provider=lambda **_: selection,
        target_race_card_capture_provider=lambda **_: card,
    )


def test_public_surface_signature_result_and_static_purity() -> None:
    assert _module.__all__ == (
        "JRARaceHistoricalReplayError",
        "JRARaceHistoricalReplayValidationError",
        "JRARaceHistoricalReplayUnavailableError",
        "JRARaceHistoricalReplayUnsupportedError",
        "JRARaceHistoricalReplayResult",
        "build_jra_race_historical_replay",
    )
    assert {name for name in vars(_module) if not name.startswith("_")} == set(_module.__all__)
    assert tuple(inspect.signature(build_jra_race_historical_replay).parameters) == (
        "seed",
        "target_race_selection_capture_provider",
        "target_race_card_capture_by_id_provider",
        "horse_history_response_provider",
        "race_result_response_provider",
        "final_win_odds_response_provider",
    )
    assert tuple(
        inspect.signature(_module._JRATargetRaceCardCaptureByIdProvider.__call__).parameters
    ) == ("self", "capture_id")
    assert is_dataclass(JRARaceHistoricalReplayResult)
    assert JRARaceHistoricalReplayResult.__dataclass_params__.frozen
    assert hasattr(JRARaceHistoricalReplayResult, "__slots__")
    assert issubclass(JRARaceHistoricalReplayValidationError, JRARaceHistoricalReplayError)
    assert issubclass(JRARaceHistoricalReplayUnavailableError, JRARaceHistoricalReplayError)
    assert issubclass(JRARaceHistoricalReplayUnsupportedError, JRARaceHistoricalReplayError)
    result = build_jra_race_historical_replay(**_providers(seed=_seed()))
    with pytest.raises(FrozenInstanceError):
        result.seed = _seed()  # type: ignore[misc]
    import scripts.simulation as package

    assert not hasattr(package, "build_jra_race_historical_replay")
    tree = ast.parse(Path(_module.__file__).read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    forbidden = {
        "sqlite3", "requests", "httpx", "urllib", "pathlib", "subprocess", "random",
        "os", "time", "socket",
    }
    assert not {name.split(".")[0] for name in imported} & forbidden
    source = Path(_module.__file__).read_text(encoding="utf-8")
    for token in (
        "SQLite", "Repository", "load_latest", "save_snapshot", "capture_target_race_navigation",
        "build_jra_race_replay_seed", "BeautifulSoup", "datetime.now", "date.today",
    ):
        assert token not in source
    assert not any(
        isinstance(node, ast.ExceptHandler)
        and isinstance(node.type, ast.Name)
        and node.type.id in {"Exception", "BaseException"}
        for node in ast.walk(tree)
    )


@pytest.mark.parametrize("field", [
    "target_race_selection_capture_provider",
    "target_race_card_capture_by_id_provider",
    "horse_history_response_provider",
    "race_result_response_provider",
    "final_win_odds_response_provider",
])
def test_exact_seed_and_all_callable_inputs_reject_before_provider_use(field: str) -> None:
    calls: list[str] = []
    providers = _providers(seed=_seed())
    providers[field] = object()
    providers["target_race_selection_capture_provider"] = (
        object() if field == "target_race_selection_capture_provider" else lambda **_: calls.append("v4")
    )
    with pytest.raises(JRARaceHistoricalReplayValidationError):
        build_jra_race_historical_replay(**providers)  # type: ignore[arg-type]
    assert calls == []
    invalid = _providers(seed=_seed())
    invalid["seed"] = object()
    invalid["target_race_selection_capture_provider"] = lambda **_: calls.append("v4")
    with pytest.raises(JRARaceHistoricalReplayValidationError):
        build_jra_race_historical_replay(**invalid)  # type: ignore[arg-type]
    assert calls == []


def test_canonical_one_entry_replay_uses_actual_formal_stack_and_exact_seed() -> None:
    card = _card_capture()
    seed = _seed(card=card)
    result = build_jra_race_historical_replay(**_providers(seed=seed, card=card))
    assert result.seed is seed
    snapshot = result.snapshot
    assert snapshot.identity.dataset_id == seed.dataset_id
    assert snapshot.identity.source_identity.organization == "JRA"
    assert snapshot.identity.source_identity.source_system == "jra_official"
    assert snapshot.identity.source_identity.external_race_id == seed.external_race_id
    assert snapshot.identity.captured_at == seed.captured_at
    assert snapshot.internal_race_id == seed.internal_race_id
    assert snapshot.information_cutoff == seed.information_cutoff
    assert len(snapshot.entries) == 1
    assert snapshot.entries[0].race_entry_id == seed.entries[0].internal_race_entry_id
    assert snapshot.entries[0].external_entry_identity.external_entry_id == seed.entries[0].external_entry_id
    assert snapshot.past_races == ()
    assert {item.input_type for item in snapshot.provenance} == {
        "track", "entry", "jockey", "odds", "past_race",
    }


def test_multiple_entries_preserve_seed_calls_union_and_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    card = _card_capture(body=_target_body(numbers=(2, 1)))
    seed = _seed(card=card, numbers=(1, 2))
    accessu_calls: list[tuple[str, datetime]] = []
    historical_calls: list[tuple[str, datetime]] = []
    source_union: list[object] = []
    original_horse = _module._resolve_horse_history
    original_collect = _module._collect_history
    original_builder = _module._build_snapshot

    def horse_wrapper(**kwargs: object) -> object:
        accessu_calls.append((kwargs["locator"].external_entry_id, kwargs["observed_at_not_after"]))  # type: ignore[union-attr]
        return original_horse(**kwargs)  # type: ignore[arg-type]

    def builder_wrapper(**kwargs: object) -> object:
        source_union.extend(kwargs["source_records"])  # type: ignore[arg-type]
        return original_builder(**kwargs)  # type: ignore[arg-type]

    def collect_wrapper(**kwargs: object) -> object:
        historical_calls.append(
            (
                kwargs["target_entry_record"].external_entry_id,  # type: ignore[union-attr]
                kwargs["observed_at_not_after"],  # type: ignore[arg-type]
            )
        )
        return original_collect(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(_module, "_resolve_horse_history", horse_wrapper)
    monkeypatch.setattr(_module, "_collect_history", collect_wrapper)
    monkeypatch.setattr(_module, "_build_snapshot", builder_wrapper)
    result = build_jra_race_historical_replay(**_providers(seed=seed, card=card))
    assert accessu_calls == [(_entry_id(1), CAPTURED), (_entry_id(2), CAPTURED)]
    assert historical_calls == [(_entry_id(1), CAPTURED), (_entry_id(2), CAPTURED)]
    assert [entry.race_entry_id for entry in result.snapshot.entries] == [101, 102]
    assert [entry.entry_order for entry in result.snapshot.entries] == [0, 1]
    assert [record.record_kind for record in source_union[:7]] == [
        "track", "entry", "jockey", "odds_win", "entry", "jockey", "odds_win",
    ]
    assert [record.external_entry_id for record in source_union[7:]] == [_entry_id(1), _entry_id(2)]


def test_exact_v3_archive_enrichment_and_restart_never_substitute_latest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed_database = tmp_path / "application.sqlite3"
    capture_database = tmp_path / "jra-captures.sqlite3"
    selection = _selection_capture()
    capture_a = _card_capture()
    capture_b = _card_capture(
        body=_target_body(race_name="後から追加"),
        observed=OBSERVED + timedelta(minutes=30),
        stored=OBSERVED + timedelta(minutes=45),
    )
    resolution = _resolution(selection=selection, card=capture_a)
    navigation = JRATargetRaceNavigationCaptureResult(
        discovery=resolution.discovery,
        capture=selection,
    )
    target_sources = normalize_jra_target_race_input_source_records(response=resolution.response)

    seed_connection = sqlite3.connect(seed_database)
    seed_connection.execute(
        """CREATE TABLE races(
            id INTEGER PRIMARY KEY, race_date TEXT, organization TEXT, place TEXT, race_no INTEGER,
            race_name TEXT, distance INTEGER, track TEXT, weather TEXT, track_condition TEXT,
            horse_count INTEGER
        )"""
    )
    seed_connection.execute(
        "CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER, horse_no INTEGER)"
    )
    apply_migrations(seed_connection)
    seed_repository = SQLiteJRARaceReplaySeedRepository(connection=seed_connection)
    materialized_seed = seed_repository.materialize_seed(
        dataset_id="dataset-jra-replay-restart",
        navigation_capture_result=navigation,
        target_race_card_resolution=resolution,
        target_sources=target_sources,
        information_cutoff=CUTOFF,
    )
    assert materialized_seed.target_race_card_capture_id == capture_a.capture_id

    capture_connection = sqlite3.connect(capture_database)
    apply_jra_capture_schema_migrations(capture_connection)
    archive = SQLiteJRAOfficialResponseCaptureRepository(connection=capture_connection)
    archive.save_target_race_selection_capture(capture=selection)
    archive.save_target_race_card_capture(capture=capture_a)
    seed_connection.close()
    capture_connection.close()

    seed_connection = sqlite3.connect(seed_database)
    capture_connection = sqlite3.connect(capture_database)
    try:
        seed_repository = SQLiteJRARaceReplaySeedRepository(connection=seed_connection)
        archive = SQLiteJRAOfficialResponseCaptureRepository(connection=capture_connection)
        reloaded_seed = seed_repository.load_seed(seed_id=materialized_seed.seed_id)
        assert reloaded_seed is not None
        assert reloaded_seed == materialized_seed
        assert reloaded_seed is not materialized_seed
        assert reloaded_seed.target_race_card_capture_id == capture_a.capture_id

        archive.save_target_race_card_capture(capture=capture_b)
        assert capture_b.capture_id != capture_a.capture_id
        assert capture_b.observed_at <= reloaded_seed.captured_at
        assert capture_b.stored_at < capture_a.stored_at
        exact_calls: list[str] = []

        def exact_provider(*, capture_id: str) -> JRAOfficialTargetRaceCardResponseCapture | None:
            exact_calls.append(capture_id)
            return archive.load_target_race_card_capture(capture_id=capture_id)

        def forbidden_latest(*args: object, **kwargs: object) -> object:
            pytest.fail("generic latest-v3 lookup must not run")

        monkeypatch.setattr(
            SQLiteJRAOfficialResponseCaptureRepository,
            "load_latest_target_race_card_capture",
            forbidden_latest,
        )
        values = _providers(seed=reloaded_seed, selection=selection, card=capture_a)
        values["target_race_selection_capture_provider"] = (
            archive.load_target_race_selection_capture
        )
        values["target_race_card_capture_by_id_provider"] = exact_provider
        result = build_jra_race_historical_replay(**values)  # type: ignore[arg-type]
        assert exact_calls == [capture_a.capture_id]
        assert result.seed is reloaded_seed
        assert result.seed.target_race_card_capture_id == capture_a.capture_id
        assert result.seed.target_race_card_capture_id != capture_b.capture_id
    finally:
        seed_connection.close()
        capture_connection.close()


def test_exact_v3_missing_is_unavailable_without_fallback() -> None:
    seed = _seed()
    calls: list[str] = []

    def missing(*, capture_id: str) -> None:
        calls.append(capture_id)
        return None

    values = _providers(seed=seed)
    values["target_race_card_capture_by_id_provider"] = missing
    with pytest.raises(JRARaceHistoricalReplayUnavailableError):
        build_jra_race_historical_replay(**values)  # type: ignore[arg-type]
    assert calls == [seed.target_race_card_capture_id]


@pytest.mark.parametrize("change", [
    {"capture_id": "jra-capture-v3:" + "0" * 64},
    {"response_sha256": "0" * 64},
    {"canonical_source_url": OTHER_CARD_URL},
    {
        "canonical_source_url":
            "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202501010220250105%2FAB"
    },
    {"observed_at": CAPTURED + timedelta(microseconds=1)},
])
def test_exact_v3_contradictions_fail_closed(change: dict[str, object]) -> None:
    card = _card_capture()
    seed = _seed(card=card)
    forged = _forge(card, **change)
    with pytest.raises(JRARaceHistoricalReplayValidationError):
        build_jra_race_historical_replay(**_providers(seed=seed, card=forged))


def test_exact_v3_wrong_type_and_integrity_exception_propagate() -> None:
    seed = _seed()
    with pytest.raises(JRARaceHistoricalReplayValidationError):
        build_jra_race_historical_replay(**_providers(seed=seed, card=object()))
    marker = RepositoryDataIntegrityError("corrupt exact capture")
    values = _providers(seed=seed)
    values["target_race_card_capture_by_id_provider"] = Mock(side_effect=marker)
    with pytest.raises(RepositoryDataIntegrityError) as raised:
        build_jra_race_historical_replay(**values)  # type: ignore[arg-type]
    assert raised.value is marker


@pytest.mark.parametrize("stage", ["selection", "target", "horse", "collect"])
def test_provider_integrity_propagates_unchanged_from_every_stage(
    stage: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed = _seed()
    marker = RepositoryDataIntegrityError(stage)
    values = _providers(seed=seed)
    if stage == "selection":
        values["target_race_selection_capture_provider"] = Mock(side_effect=marker)
    elif stage == "target":
        values["target_race_card_capture_by_id_provider"] = Mock(side_effect=marker)
    elif stage == "horse":
        monkeypatch.setattr(_module, "_resolve_horse_history", Mock(side_effect=marker))
    else:
        monkeypatch.setattr(_module, "_collect_history", Mock(side_effect=marker))
    with pytest.raises(RepositoryDataIntegrityError) as raised:
        build_jra_race_historical_replay(**values)  # type: ignore[arg-type]
    assert raised.value is marker


def test_c4c_called_once_with_exact_seed_inputs_and_post_provenance_checked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selection = _selection_capture()
    card = _card_capture()
    seed = _seed(card=card)
    real = _resolution(selection=selection, card=card)
    calls: list[dict[str, object]] = []

    def resolver(**kwargs: object) -> object:
        calls.append(kwargs)
        return real

    monkeypatch.setattr(_module, "_resolve_target", resolver)
    result = build_jra_race_historical_replay(**_providers(seed=seed, selection=selection, card=card))
    assert result.seed is seed
    assert len(calls) == 1
    assert calls[0]["external_race_id"] == seed.external_race_id
    assert calls[0]["target_race_selection_capture_id"] == seed.target_race_selection_capture_id
    assert calls[0]["captured_at"] == seed.captured_at
    contradictory_resolutions = (
        _forge(real, target_race_selection_capture_id="jra-capture-v4:" + "0" * 64),
        _forge(real, target_race_card_capture_id="jra-capture-v3:" + "0" * 64),
        _forge(real, target_race_card_response_sha256="0" * 64),
        _forge(
            real,
            discovery=_forge(
                real.discovery,
                locator=_forge(
                    real.discovery.locator,
                    external_race_id="jra:race:2025:05:01:01:02",
                ),
            ),
        ),
        _forge(
            real,
            discovery=_forge(
                real.discovery,
                locator=_forge(
                    real.discovery.locator,
                    canonical_target_race_card_url=OTHER_CARD_URL,
                ),
            ),
        ),
        _forge(real, response=_forge(real.response, response_url=OTHER_CARD_URL)),
        _forge(real, captured_at=CAPTURED + timedelta(microseconds=1)),
    )
    for contradictory_resolution in contradictory_resolutions:
        monkeypatch.setattr(_module, "_resolve_target", lambda **_: contradictory_resolution)
        with pytest.raises(JRARaceHistoricalReplayValidationError):
            build_jra_race_historical_replay(**_providers(seed=seed, selection=selection, card=card))


def test_target_normalization_once_and_entry_contradictions_precede_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    card = _card_capture(body=_target_body(numbers=(1, 2)))
    seed = _seed(card=card, numbers=(1, 2))
    resolution = _resolution(card=card)
    target = normalize_jra_target_race_input_source_records(response=resolution.response)
    history_calls: list[str] = []
    original = _module._normalize_target
    normalize_calls = 0

    def normalized(**kwargs: object) -> object:
        nonlocal normalize_calls
        normalize_calls += 1
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(_module, "_normalize_target", normalized)
    values = _providers(seed=seed, card=card)
    values["horse_history_response_provider"] = lambda **_: history_calls.append("accessU")
    build_jra_race_historical_replay(**_providers(seed=seed, card=card))
    assert normalize_calls == 1

    contradictions = (
        _forge(target, target_entry_records=target.target_entry_records[:-1]),
        _forge(target, target_entry_records=target.target_entry_records + (target.target_entry_records[0],)),
        _forge(target, target_entry_records=tuple(reversed(target.target_entry_records))),
        _forge(
            target,
            target_entry_records=(
                _forge(target.target_entry_records[0], external_entry_id=_entry_id(2)),
                target.target_entry_records[1],
            ),
        ),
        _forge(
            target,
            target_entry_records=(
                _forge(
                    target.target_entry_records[0],
                    record_values={**target.target_entry_records[0].record_values, "external_horse_id": _horse_id(2)},
                ),
                target.target_entry_records[1],
            ),
        ),
        _forge(
            target,
            target_entry_records=(
                _forge(
                    target.target_entry_records[0],
                    record_values={**target.target_entry_records[0].record_values, "horse_no": 2},
                ),
                target.target_entry_records[1],
            ),
        ),
        _forge(
            target,
            target_horse_history_locators=(
                _forge(target.target_horse_history_locators[0], external_race_id="jra:race:2025:05:01:01:02"),
                target.target_horse_history_locators[1],
            ),
        ),
        _forge(
            target,
            target_horse_history_locators=(
                _forge(target.target_horse_history_locators[0], external_entry_id=_entry_id(2)),
                target.target_horse_history_locators[1],
            ),
        ),
        _forge(
            target,
            target_horse_history_locators=(
                _forge(target.target_horse_history_locators[0], external_horse_id=_horse_id(2)),
                target.target_horse_history_locators[1],
            ),
        ),
    )
    for contradiction in contradictions:
        monkeypatch.setattr(_module, "_normalize_target", lambda item=contradiction, **_: item)
        with pytest.raises(JRARaceHistoricalReplayValidationError):
            build_jra_race_historical_replay(**values)  # type: ignore[arg-type]
    assert history_calls == []


def test_causal_bounds_use_captured_not_cutoff_and_fail_before_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed = _seed()
    horse_bounds: list[datetime] = []
    collection_bounds: list[datetime] = []
    original_horse = _module._resolve_horse_history
    original_collect = _module._collect_history

    def horse(**kwargs: object) -> object:
        horse_bounds.append(kwargs["observed_at_not_after"])  # type: ignore[arg-type]
        return original_horse(**kwargs)  # type: ignore[arg-type]

    def collect(**kwargs: object) -> object:
        collection_bounds.append(kwargs["observed_at_not_after"])  # type: ignore[arg-type]
        return original_collect(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(_module, "_resolve_horse_history", horse)
    monkeypatch.setattr(_module, "_collect_history", collect)
    build_jra_race_historical_replay(**_providers(seed=seed))
    assert horse_bounds == [seed.captured_at]
    assert collection_bounds == [seed.captured_at]
    assert seed.information_cutoff not in horse_bounds + collection_bounds

    late_seed = _seed(cutoff=SCHEDULED + timedelta(microseconds=1))
    history = Mock()
    values = _providers(seed=late_seed)
    values["horse_history_response_provider"] = history
    with pytest.raises(JRARaceHistoricalReplayValidationError):
        build_jra_race_historical_replay(**values)  # type: ignore[arg-type]
    history.assert_not_called()


def test_complete_union_duplicate_foreign_and_partial_fail_before_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed = _seed()
    resolution = _resolution()
    target = normalize_jra_target_race_input_source_records(response=resolution.response)
    real_history = _module._collect_history(
        target_track_record=target.target_track_record,
        target_entry_record=target.target_entry_records[0],
        horse_history_response=_horse_response(1),
        observed_at_not_after=CAPTURED,
        race_result_response_provider=lambda **_: pytest.fail("not called"),
        final_win_odds_response_provider=lambda **_: pytest.fail("not called"),
    )
    builder = Mock()
    monkeypatch.setattr(_module, "_build_snapshot", builder)

    duplicate_record = _forge(
        real_history.source_records[0],
        source_id=target.source_records[0].source_id,
    )
    duplicate = _forge(real_history, source_records=(duplicate_record,))
    monkeypatch.setattr(_module, "_collect_history", lambda **_: duplicate)
    with pytest.raises(JRARaceHistoricalReplayValidationError, match="duplicate"):
        build_jra_race_historical_replay(**_providers(seed=seed))
    builder.assert_not_called()

    foreign = _forge(real_history, target_external_entry_id=_entry_id(2))
    monkeypatch.setattr(_module, "_collect_history", lambda **_: foreign)
    with pytest.raises(JRARaceHistoricalReplayValidationError):
        build_jra_race_historical_replay(**_providers(seed=seed))
    builder.assert_not_called()

    marker = JRAHistoricalSourceCollectionUnavailableError("later entry unavailable")
    multi_card = _card_capture(body=_target_body(numbers=(1, 2)))
    multi_seed = _seed(card=multi_card, numbers=(1, 2))
    calls = 0

    def later_failure(**kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise marker
        return real_history

    monkeypatch.setattr(_module, "_collect_history", later_failure)
    with pytest.raises(JRARaceHistoricalReplayUnavailableError):
        build_jra_race_historical_replay(**_providers(seed=multi_seed, card=multi_card))
    assert calls == 2
    builder.assert_not_called()


def test_snapshot_builder_exactly_once_with_seed_mapping_and_failure_translation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed = _seed()
    original = _module._build_snapshot
    calls: list[dict[str, object]] = []

    def builder(**kwargs: object) -> object:
        calls.append(kwargs)
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(_module, "_build_snapshot", builder)
    result = build_jra_race_historical_replay(**_providers(seed=seed))
    assert result.seed is seed
    assert len(calls) == 1
    assert calls[0]["dataset_id"] == seed.dataset_id
    assert calls[0]["internal_race_id"] == seed.internal_race_id
    assert calls[0]["captured_at"] == seed.captured_at
    assert calls[0]["information_cutoff"] == seed.information_cutoff
    assert calls[0]["race_entry_id_by_external_entry_id"] == {_entry_id(1): 101}

    marker = HistoricalInputSnapshotAssemblyError("bad snapshot")
    monkeypatch.setattr(_module, "_build_snapshot", Mock(side_effect=marker))
    with pytest.raises(JRARaceHistoricalReplayValidationError) as raised:
        build_jra_race_historical_replay(**_providers(seed=seed))
    assert raised.value.__cause__ is marker


@pytest.mark.parametrize(
    ("stage", "error", "expected"),
    [
        ("target", JRATargetRaceCardResolutionValidationError("x"), JRARaceHistoricalReplayValidationError),
        ("target", JRATargetRaceCardResolutionUnavailableError("x"), JRARaceHistoricalReplayUnavailableError),
        ("normalize", JRATargetRaceSourceValidationError("x"), JRARaceHistoricalReplayValidationError),
        ("normalize", JRATargetRaceSourceUnsupportedError("x"), JRARaceHistoricalReplayUnsupportedError),
        ("horse", JRATargetHorseHistoryResolutionValidationError("x"), JRARaceHistoricalReplayValidationError),
        ("horse", JRATargetHorseHistoryResolutionUnavailableError("x"), JRARaceHistoricalReplayUnavailableError),
        ("collect", JRAHistoricalSourceCollectionValidationError("x"), JRARaceHistoricalReplayValidationError),
        ("collect", JRAHistoricalSourceCollectionUnavailableError("x"), JRARaceHistoricalReplayUnavailableError),
        ("collect", JRAHistoricalSourceCollectionUnsupportedError("x"), JRARaceHistoricalReplayUnsupportedError),
    ],
)
def test_exact_error_translation(
    stage: str,
    error: ValueError,
    expected: type[JRARaceHistoricalReplayError],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed = _seed()
    if stage == "target":
        monkeypatch.setattr(_module, "_resolve_target", Mock(side_effect=error))
    elif stage == "normalize":
        monkeypatch.setattr(_module, "_normalize_target", Mock(side_effect=error))
    elif stage == "horse":
        monkeypatch.setattr(_module, "_resolve_horse_history", Mock(side_effect=error))
    else:
        monkeypatch.setattr(_module, "_collect_history", Mock(side_effect=error))
    with pytest.raises(expected):
        build_jra_race_historical_replay(**_providers(seed=seed))


def test_result_direct_construction_requires_exact_seed_snapshot_agreement() -> None:
    seed = _seed()
    result = build_jra_race_historical_replay(**_providers(seed=seed))
    with pytest.raises(JRARaceHistoricalReplayValidationError):
        JRARaceHistoricalReplayResult(seed=object(), snapshot=result.snapshot)  # type: ignore[arg-type]
    with pytest.raises(JRARaceHistoricalReplayValidationError):
        JRARaceHistoricalReplayResult(seed=seed, snapshot=object())  # type: ignore[arg-type]
    identity = result.snapshot.identity
    source = identity.source_identity
    snapshot_changes = (
        {"identity": _forge(identity, dataset_id="other")},
        {"identity": _forge(identity, source_identity=_forge(source, organization="NAR"))},
        {"identity": _forge(identity, source_identity=_forge(source, source_system="other"))},
        {"identity": _forge(identity, source_identity=_forge(source, external_race_id="other"))},
        {"identity": _forge(identity, captured_at=CAPTURED + timedelta(microseconds=1))},
        {"internal_race_id": seed.internal_race_id + 1},
        {"information_cutoff": seed.information_cutoff + timedelta(microseconds=1)},
    )
    for changes in snapshot_changes:
        with pytest.raises(JRARaceHistoricalReplayValidationError):
            JRARaceHistoricalReplayResult(
                seed=seed,
                snapshot=_forge(result.snapshot, **changes),  # type: ignore[arg-type]
            )
    entry = result.snapshot.entries[0]
    external = entry.external_entry_identity
    entry_changes = (
        {"entry_order": 1},
        {"external_entry_identity": _forge(external, external_entry_id="other")},
        {"external_entry_identity": _forge(external, external_horse_id="other")},
        {"horse_no": 2},
        {"race_entry_id": 999},
    )
    for changes in entry_changes:
        wrong_entry = _forge(entry, **changes)
        wrong_entries = _forge(result.snapshot, entries=(wrong_entry,))
        with pytest.raises(JRARaceHistoricalReplayValidationError):
            JRARaceHistoricalReplayResult(seed=seed, snapshot=wrong_entries)  # type: ignore[arg-type]
