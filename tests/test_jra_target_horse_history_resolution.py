from __future__ import annotations

import ast
from dataclasses import fields
from datetime import datetime, timezone
import inspect

import pytest

import scripts.simulation.jra_target_horse_history_resolution as _module
from scripts.simulation.jra_official_response_capture import JRASuppliedOfficialResponse
from scripts.simulation.jra_target_horse_history_resolution import (
    JRATargetHorseHistoryResolutionUnavailableError,
    JRATargetHorseHistoryResolutionValidationError,
    resolve_jra_target_horse_history_response,
)
from scripts.simulation.jra_target_race_input_source import normalize_jra_target_race_input_source_records


_CARD_URL = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105%2FAB"
_HISTORY_URL = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud001234567890%2FAB"
_START = datetime(2025, 1, 5, 6, 0, tzinfo=timezone.utc)
_OBSERVED = datetime(2025, 1, 5, 1, 0, tzinfo=timezone.utc)


def _target() -> tuple[object, object, object]:
    html = '''<div id="contentsBody"><div class="line main"><div class="inner"><h1>1レース</h1></div></div><div class="syutsuba"><table class="basic narrow-xy mt20"><caption><div class="race_header"><div class="left"><div class="date_line"><div class="inner"><div class="cell date">2025年1月5日(日) 1回東京1日</div><div class="cell time"><strong>15時00分</strong></div></div></div></div><div class="race_title"><div class="inner"><div class="txt"><span class="main"><span class="race_name">テスト</span></span></div></div><div class="type"><div class="cell course">コース：1600メートル（芝・左）</div><div class="cell class">3歳1勝</div></div></div><div class="cell baba"><ul><li class="turf"><span class="cap">芝</span><span class="txt">良</span></li></ul></div></div></caption><tbody><tr><td class="num">1</td><td class="horse"><div class="name_line"><div class="name"><a href="/JRADB/accessU.html?CNAME=pw01dud001234567890%2FAB">horse</a></div><div class="odds"><div class="odds_line"><span class="num">2.5</span></div></div></div></td><td class="jockey"><p class="jockey">騎手</p></td></tr></tbody></table></div></div>'''
    result = normalize_jra_target_race_input_source_records(
        response=JRASuppliedOfficialResponse(
            response_url=_CARD_URL, response_body=html.encode("cp932"), observed_at=_OBSERVED
        )
    )
    return result.target_track_record, result.target_entry_records[0], result.target_horse_history_locators[0]


def _response(*, url: str = _HISTORY_URL, observed: datetime = _OBSERVED) -> JRASuppliedOfficialResponse:
    return JRASuppliedOfficialResponse(response_url=url, response_body=b"<html></html>", observed_at=observed)


def _forge(value: object, **changes: object) -> object:
    """Create an exact frozen domain type with deliberately inconsistent internals."""
    result = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(result, field.name, changes.get(field.name, getattr(value, field.name)))
    return result


def test_public_surface_signature_and_pure_imports() -> None:
    assert _module.__all__ == (
        "JRATargetHorseHistoryResponseProvider",
        "JRATargetHorseHistoryResolutionError",
        "JRATargetHorseHistoryResolutionValidationError",
        "JRATargetHorseHistoryResolutionUnavailableError",
        "resolve_jra_target_horse_history_response",
    )
    assert tuple(inspect.signature(resolve_jra_target_horse_history_response).parameters) == (
        "target_track_record", "target_entry_record", "locator", "observed_at_not_after", "horse_history_response_provider"
    )
    tree = ast.parse(inspect.getsource(_module))
    imported = {alias.name.split(".")[0] for node in tree.body for alias in getattr(node, "names", ()) if isinstance(node, (ast.Import, ast.ImportFrom))}
    assert not imported & {"sqlite3", "requests", "urllib", "pathlib", "subprocess", "random", "os", "time"}


def test_resolver_binds_exact_explicit_cutoff_once() -> None:
    track, entry, locator = _target()
    bound = datetime(2025, 1, 5, 5, 0, tzinfo=timezone.utc)
    calls: list[tuple[object, object]] = []

    def provider(*, locator: object, observed_at_not_after: datetime) -> JRASuppliedOfficialResponse:
        calls.append((locator, observed_at_not_after))
        return _response()

    assert resolve_jra_target_horse_history_response(
        target_track_record=track, target_entry_record=entry, locator=locator,
        observed_at_not_after=bound, horse_history_response_provider=provider,
    ) == _response()
    assert calls == [(locator, bound)]


@pytest.mark.parametrize(
    ("target_name", "changes"),
    [
        ("track", {"organization": "NAR"}),
        ("track", {"record_kind": "entry"}),
        ("entry", {"organization": "NAR"}),
        ("entry", {"external_race_id": "jra:race:2025:05:01:01:02"}),
        ("entry", {"external_entry_id": "jra:race:2025:05:01:01:01:entry:01"}),
    ],
)
def test_target_lineage_failures_are_validation(target_name: str, changes: dict[str, object]) -> None:
    track, entry, locator = _target()
    if target_name == "track":
        track = _forge(track, **changes)
    else:
        entry = _forge(entry, **changes)
    with pytest.raises(JRATargetHorseHistoryResolutionValidationError):
        resolve_jra_target_horse_history_response(
            target_track_record=track, target_entry_record=entry, locator=locator,
            observed_at_not_after=_START, horse_history_response_provider=lambda **_: _response(),
        )


@pytest.mark.parametrize("changes", [
    {"external_race_id": "jra:race:2025:05:01:01:02"},
    {"external_entry_id": "jra:race:2025:05:01:01:01:entry:2"},
    {"external_horse_id": "jra:horse:1234567891"},
])
def test_locator_mismatch_or_nonexact_locator_is_validation(changes: dict[str, object]) -> None:
    track, entry, locator = _target()
    forged = _forge(locator, **changes)
    with pytest.raises(JRATargetHorseHistoryResolutionValidationError):
        resolve_jra_target_horse_history_response(
            target_track_record=track, target_entry_record=entry, locator=forged,
            observed_at_not_after=_START, horse_history_response_provider=lambda **_: _response(),
        )
    with pytest.raises(JRATargetHorseHistoryResolutionValidationError):
        resolve_jra_target_horse_history_response(
            target_track_record=track, target_entry_record=entry, locator=object(),  # type: ignore[arg-type]
            observed_at_not_after=_START, horse_history_response_provider=lambda **_: _response(),
        )


@pytest.mark.parametrize("url", [
    "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud001234567890%2FAC",
    "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud001234567891%2FAB",
    "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0105202501010120250105%2FAB",
    _CARD_URL,
])
def test_response_url_must_equal_retained_accessu_locator(url: str) -> None:
    track, entry, locator = _target()
    with pytest.raises(JRATargetHorseHistoryResolutionValidationError):
        resolve_jra_target_horse_history_response(
            target_track_record=track, target_entry_record=entry, locator=locator,
            observed_at_not_after=_START, horse_history_response_provider=lambda **_: _response(url=url),
        )


def test_forged_accesso_response_type_is_still_rejected_as_wrong_family() -> None:
    track, entry, locator = _target()
    accesso = _forge(_response(), response_url="https://www.jra.go.jp/JRADB/accessO.html")
    with pytest.raises(JRATargetHorseHistoryResolutionValidationError):
        resolve_jra_target_horse_history_response(
            target_track_record=track, target_entry_record=entry, locator=locator,
            observed_at_not_after=_START, horse_history_response_provider=lambda **_: accesso,
        )


def test_bounds_none_and_provider_exception_fail_closed_without_fallback() -> None:
    track, entry, locator = _target()
    with pytest.raises(JRATargetHorseHistoryResolutionValidationError):
        resolve_jra_target_horse_history_response(
            target_track_record=track, target_entry_record=entry, locator=locator,
            observed_at_not_after=datetime(2025, 1, 5, 7, 0, tzinfo=timezone.utc), horse_history_response_provider=lambda **_: _response(),
        )
    with pytest.raises(JRATargetHorseHistoryResolutionUnavailableError):
        resolve_jra_target_horse_history_response(
            target_track_record=track, target_entry_record=entry, locator=locator,
            observed_at_not_after=_START, horse_history_response_provider=lambda **_: None,
        )
    class ProviderFailure(RuntimeError):
        pass
    def failing(**_: object) -> None:
        raise ProviderFailure("unchanged")
    with pytest.raises(ProviderFailure):
        resolve_jra_target_horse_history_response(
            target_track_record=track, target_entry_record=entry, locator=locator,
            observed_at_not_after=_START, horse_history_response_provider=failing,
        )


def test_nonexact_provider_response_and_invalid_bounds_do_not_call_provider() -> None:
    track, entry, locator = _target()
    with pytest.raises(JRATargetHorseHistoryResolutionValidationError):
        resolve_jra_target_horse_history_response(
            target_track_record=track, target_entry_record=entry, locator=locator,
            observed_at_not_after=_START, horse_history_response_provider=lambda **_: object(),  # type: ignore[return-value]
        )
    calls = 0
    def provider(**_: object) -> JRASuppliedOfficialResponse:
        nonlocal calls
        calls += 1
        return _response()
    for bound in (datetime(2025, 1, 5, 7, 0, tzinfo=timezone.utc), datetime(2025, 1, 5, 5, 0)):
        with pytest.raises(JRATargetHorseHistoryResolutionValidationError):
            resolve_jra_target_horse_history_response(
                target_track_record=track, target_entry_record=entry, locator=locator,
                observed_at_not_after=bound, horse_history_response_provider=provider,
            )
    assert calls == 0


def test_late_response_and_naive_cutoff_are_validation() -> None:
    track, entry, locator = _target()
    for bound, response in [
        (datetime(2025, 1, 5, 5, 0), _response()),
        (_START, _response(observed=datetime(2025, 1, 5, 6, 0, 1, tzinfo=timezone.utc))),
    ]:
        with pytest.raises(JRATargetHorseHistoryResolutionValidationError):
            resolve_jra_target_horse_history_response(
                target_track_record=track, target_entry_record=entry, locator=locator,
                observed_at_not_after=bound, horse_history_response_provider=lambda **_: response,
            )


def test_response_exactly_at_explicit_and_scheduled_bound_is_accepted() -> None:
    track, entry, locator = _target()
    explicit = datetime(2025, 1, 5, 5, 0, tzinfo=timezone.utc)
    response = _response(observed=explicit)
    assert resolve_jra_target_horse_history_response(
        target_track_record=track, target_entry_record=entry, locator=locator,
        observed_at_not_after=explicit, horse_history_response_provider=lambda **_: response,
    ) is response
    response_at_start = _response(observed=_START)
    assert resolve_jra_target_horse_history_response(
        target_track_record=track, target_entry_record=entry, locator=locator,
        observed_at_not_after=_START, horse_history_response_provider=lambda **_: response_at_start,
    ) is response_at_start


def test_static_error_boundary_and_no_package_root_export() -> None:
    tree = ast.parse(inspect.getsource(_module))
    assert not any(
        isinstance(node, ast.ExceptHandler)
        and isinstance(node.type, ast.Name)
        and node.type.id in {"Exception", "BaseException"}
        for node in ast.walk(tree)
    )
    import scripts.simulation as package
    assert not hasattr(package, "resolve_jra_target_horse_history_response")
