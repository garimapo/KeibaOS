from __future__ import annotations

import ast
from dataclasses import is_dataclass
from datetime import datetime, timedelta, timezone
import inspect

import pytest

import scripts.simulation.jra_target_race_card_resolution as _module
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialTargetRaceCardResponseCapture,
    JRASuppliedOfficialResponse,
    JRATargetRaceSelectionResponseCapture,
)
from scripts.simulation.jra_target_race_card_resolution import (
    JRATargetRaceCardResolution,
    JRATargetRaceCardResolutionUnavailableError,
    JRATargetRaceCardResolutionValidationError,
    resolve_jra_target_race_card_response,
)
from scripts.simulation.jra_target_race_input_source import (
    normalize_jra_target_race_input_source_records,
)
from scripts.simulation.jra_target_race_card_locator import (
    build_jra_target_race_selection_request_locator,
)
from scripts.simulation.repositories.errors import RepositoryDataIntegrityError, RepositoryValidationError


UTC = timezone.utc
RACE_ID = "jra:race:2025:05:01:01:01"
RACE_CNAME = "pw01drl00052025010120250105/AB"
RAW_CARD_URL = "/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105/AB"
CARD_URL = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105%2FAB"
OTHER_CARD_URL = CARD_URL.replace("%2FAB", "%2FAC")
OBSERVED = datetime(2025, 1, 5, 1, 0, tzinfo=UTC)
CAPTURED = datetime(2025, 1, 5, 2, 0, tzinfo=UTC)
STORED = datetime(2025, 1, 5, 3, 0, tzinfo=UTC)


def _selection_body(*, card_url: str = RAW_CARD_URL) -> bytes:
    return (
        '<div id="contentsBody"><div class="race_select"><table id="race_list" '
        'class="basic mt20"><tbody><tr><th class="race_num"><a href="'
        + card_url
        + '">1R</a></th><td class="syutsuba"><a class="btn-def btn-sm btn-narrow" href="'
        + card_url
        + '">出馬表</a></td></tr></tbody></table></div></div>'
    ).encode("cp932")


def _target_body() -> bytes:
    return '''<div id="contentsBody"><div class="line main"><div class="inner"><h1>1レース</h1></div></div><div class="syutsuba"><table class="basic narrow-xy mt20"><caption><div class="race_header"><div class="left"><div class="date_line"><div class="inner"><div class="cell date">2025年1月5日(日) 1回東京1日</div><div class="cell time"><strong>15時00分</strong></div></div></div></div><div class="race_title"><div class="inner"><div class="txt"><span class="main"><span class="race_name">テストレース</span></span></div></div><div class="type"><div class="cell course">コース：1600メートル（芝・左）</div><div class="cell class">3歳1勝</div></div></div><div class="cell baba"><ul><li class="turf"><span class="cap">芝</span><span class="txt">良</span></li><li class="weather"><span class="inner"><span class="txt">晴</span></span></li></ul></div></div></caption><tbody><tr><td class="num">1</td><td class="horse"><div class="name_line"><div class="name"><a href="/JRADB/accessU.html?CNAME=pw01dud001234567890%2FAB">horse</a></div><div class="odds"><div class="odds_line"><span class="num">2.5</span></div></div></div></td><td class="jockey"><p class="jockey">騎手</p></td></tr></tbody></table></div></div>'''.encode("cp932")


def _selection_capture(
    *,
    body: bytes | None = None,
    observed: datetime = OBSERVED,
    stored: datetime = STORED,
) -> JRATargetRaceSelectionResponseCapture:
    return JRATargetRaceSelectionResponseCapture(
        request_locator=build_jra_target_race_selection_request_locator(cname=RACE_CNAME),
        response_body=_selection_body() if body is None else body,
        charset="cp932",
        requested_at=observed,
        observed_at=observed,
        stored_at=stored,
        http_status=200,
        content_type="text/html",
    )


def _card_capture(
    *,
    url: str = CARD_URL,
    body: bytes | None = None,
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


def _resolve(
    *,
    selection: object | None = None,
    card: object | None = None,
    captured_at: datetime = CAPTURED,
) -> JRATargetRaceCardResolution:
    actual_selection = _selection_capture() if selection is None else selection
    actual_card = _card_capture() if card is None else card
    capture_id = actual_selection.capture_id  # type: ignore[union-attr]
    return resolve_jra_target_race_card_response(
        external_race_id=RACE_ID,
        target_race_selection_capture_id=capture_id,
        captured_at=captured_at,
        target_race_selection_capture_provider=lambda *, capture_id: actual_selection,
        target_race_card_capture_provider=lambda *, locator, observed_at_not_after: actual_card,
    )


def test_public_surface_signature_result_shape_and_pure_boundary() -> None:
    assert _module.__all__ == (
        "JRATargetRaceSelectionCaptureProvider",
        "JRATargetRaceCardCaptureProvider",
        "JRATargetRaceCardResolutionError",
        "JRATargetRaceCardResolutionValidationError",
        "JRATargetRaceCardResolutionUnavailableError",
        "JRATargetRaceCardResolution",
        "resolve_jra_target_race_card_response",
    )
    assert tuple(inspect.signature(resolve_jra_target_race_card_response).parameters) == (
        "external_race_id",
        "target_race_selection_capture_id",
        "captured_at",
        "target_race_selection_capture_provider",
        "target_race_card_capture_provider",
    )
    assert is_dataclass(JRATargetRaceCardResolution)
    assert JRATargetRaceCardResolution.__dataclass_params__.frozen
    assert hasattr(JRATargetRaceCardResolution, "__slots__")
    tree = ast.parse(inspect.getsource(_module))
    forbidden = {"requests", "httpx", "sqlite3", "pathlib", "subprocess", "random", "os", "time", "socket"}
    imported = {
        alias.name.split(".")[0]
        for node in tree.body
        for alias in getattr(node, "names", ())
        if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    assert not imported & forbidden
    assert not any(
        isinstance(node, ast.ExceptHandler)
        and isinstance(node.type, ast.Name)
        and node.type.id in {"Exception", "BaseException"}
        for node in ast.walk(tree)
    )
    import scripts.simulation as package
    assert not hasattr(package, "resolve_jra_target_race_card_response")


def test_success_preserves_exact_provenance_and_normalizer_input() -> None:
    selection = _selection_capture()
    card = _card_capture()
    calls: list[tuple[str, object]] = []

    def selection_provider(*, capture_id: str) -> JRATargetRaceSelectionResponseCapture:
        calls.append(("v4", capture_id))
        return selection

    def card_provider(*, locator: object, observed_at_not_after: datetime) -> JRAOfficialTargetRaceCardResponseCapture:
        calls.append(("v3", (locator, observed_at_not_after)))
        return card

    result = resolve_jra_target_race_card_response(
        external_race_id=RACE_ID,
        target_race_selection_capture_id=selection.capture_id,
        captured_at=CAPTURED,
        target_race_selection_capture_provider=selection_provider,
        target_race_card_capture_provider=card_provider,
    )
    assert calls == [("v4", selection.capture_id), ("v3", (result.discovery.locator, CAPTURED))]
    assert result.response == card.to_supplied_official_response()
    assert result.target_race_selection_capture_id == selection.capture_id
    assert result.target_race_card_capture_id == card.capture_id
    assert result.target_race_card_response_sha256 == card.response_sha256
    assert result.captured_at is CAPTURED
    assert result.discovery.locator.canonical_target_race_card_url == CARD_URL
    assert normalize_jra_target_race_input_source_records(response=result.response).target_track_record.external_race_id == RACE_ID


@pytest.mark.parametrize(
    ("race_id", "capture_id", "bound"),
    [
        ("jra:race:2025:05:01:01:1", "jra-capture-v4:" + "a" * 64, CAPTURED),
        (RACE_ID, "jra-capture-v1:" + "a" * 64, CAPTURED),
        (RACE_ID, "jra-capture-v4:" + "A" * 64, CAPTURED),
        (RACE_ID, "jra-capture-v4:" + "a" * 64, datetime(2025, 1, 5, 2, 0)),
    ],
)
def test_invalid_caller_input_makes_zero_provider_calls(race_id: str, capture_id: str, bound: datetime) -> None:
    calls: list[str] = []
    with pytest.raises(JRATargetRaceCardResolutionValidationError):
        resolve_jra_target_race_card_response(
            external_race_id=race_id,
            target_race_selection_capture_id=capture_id,
            captured_at=bound,
            target_race_selection_capture_provider=lambda **_: calls.append("v4"),
            target_race_card_capture_provider=lambda **_: calls.append("v3"),
        )
    assert calls == []


def test_missing_and_provider_exceptions_preserve_error_taxonomy() -> None:
    selection = _selection_capture()
    with pytest.raises(JRATargetRaceCardResolutionUnavailableError):
        resolve_jra_target_race_card_response(
            external_race_id=RACE_ID,
            target_race_selection_capture_id=selection.capture_id,
            captured_at=CAPTURED,
            target_race_selection_capture_provider=lambda **_: None,
            target_race_card_capture_provider=lambda **_: pytest.fail("v3 provider must not run"),
        )
    with pytest.raises(JRATargetRaceCardResolutionUnavailableError):
        resolve_jra_target_race_card_response(
            external_race_id=RACE_ID,
            target_race_selection_capture_id=selection.capture_id,
            captured_at=CAPTURED,
            target_race_selection_capture_provider=lambda **_: selection,
            target_race_card_capture_provider=lambda **_: None,
        )
    error = RepositoryDataIntegrityError("unchanged")
    with pytest.raises(RepositoryDataIntegrityError) as raised:
        resolve_jra_target_race_card_response(
            external_race_id=RACE_ID,
            target_race_selection_capture_id=selection.capture_id,
            captured_at=CAPTURED,
            target_race_selection_capture_provider=lambda **_: selection,
            target_race_card_capture_provider=lambda **_: (_ for _ in ()).throw(error),
        )
    assert raised.value is error


def test_selection_validation_prevents_v3_provider_call() -> None:
    future = _selection_capture(observed=CAPTURED + timedelta(microseconds=1), stored=CAPTURED + timedelta(hours=1))
    v3_calls = 0

    def card_provider(**_: object) -> JRAOfficialTargetRaceCardResponseCapture:
        nonlocal v3_calls
        v3_calls += 1
        return _card_capture()

    with pytest.raises(JRATargetRaceCardResolutionValidationError):
        resolve_jra_target_race_card_response(
            external_race_id=RACE_ID,
            target_race_selection_capture_id=future.capture_id,
            captured_at=CAPTURED,
            target_race_selection_capture_provider=lambda **_: future,
            target_race_card_capture_provider=card_provider,
        )
    invalid_navigation = _selection_capture(body=_selection_body(card_url=RAW_CARD_URL.replace("0120250105", "0220250105")))
    with pytest.raises(JRATargetRaceCardResolutionValidationError):
        resolve_jra_target_race_card_response(
            external_race_id=RACE_ID,
            target_race_selection_capture_id=invalid_navigation.capture_id,
            captured_at=CAPTURED,
            target_race_selection_capture_provider=lambda **_: invalid_navigation,
            target_race_card_capture_provider=card_provider,
        )
    assert v3_calls == 0


def test_selection_provider_type_and_capture_id_mismatch_are_validation() -> None:
    selection = _selection_capture()
    card_calls = 0

    def card_provider(**_: object) -> JRAOfficialTargetRaceCardResponseCapture:
        nonlocal card_calls
        card_calls += 1
        return _card_capture()

    for supplied in (object(), _selection_capture(body=b"<html></html>")):
        requested_id = selection.capture_id
        with pytest.raises(JRATargetRaceCardResolutionValidationError):
            resolve_jra_target_race_card_response(
                external_race_id=RACE_ID,
                target_race_selection_capture_id=requested_id,
                captured_at=CAPTURED,
                target_race_selection_capture_provider=lambda **_: supplied,
                target_race_card_capture_provider=card_provider,
            )
    assert card_calls == 0


def test_v3_type_url_and_future_bound_are_validation() -> None:
    selection = _selection_capture()
    for card in (
        object(),
        _card_capture(url=OTHER_CARD_URL),
        _card_capture(observed=CAPTURED + timedelta(microseconds=1), stored=CAPTURED + timedelta(hours=1)),
    ):
        with pytest.raises(JRATargetRaceCardResolutionValidationError):
            _resolve(selection=selection, card=card)


def test_observed_bound_is_inclusive_and_stored_at_is_not_a_replay_cutoff() -> None:
    selection = _selection_capture(observed=CAPTURED, stored=CAPTURED + timedelta(hours=1))
    card = _card_capture(observed=CAPTURED, stored=CAPTURED + timedelta(hours=1))
    result = _resolve(selection=selection, card=card, captured_at=CAPTURED)
    assert result.response.observed_at == CAPTURED
    assert selection.stored_at > CAPTURED and card.stored_at > CAPTURED


def test_exact_discovered_site_variant_and_opaque_tail_are_preserved() -> None:
    variant_url = CARD_URL.replace("dde01", "dde10").replace("%2FAB", "%2FAC")
    variant_raw = RAW_CARD_URL.replace("dde01", "dde10").replace("/AB", "/AC")
    selection = _selection_capture(body=_selection_body(card_url=variant_raw))
    card = _card_capture(url=variant_url)
    result = _resolve(selection=selection, card=card)
    assert result.discovery.locator.canonical_target_race_card_url == variant_url
    assert result.response.response_url == variant_url


def test_direct_result_construction_rechecks_lineage() -> None:
    selection = _selection_capture()
    card = _card_capture()
    result = _resolve(selection=selection, card=card)
    wrong_selection = _selection_capture(body=b"<html></html>")
    with pytest.raises(JRATargetRaceCardResolutionValidationError):
        JRATargetRaceCardResolution(
            discovery=result.discovery,
            target_race_selection_capture=wrong_selection,
            target_race_card_capture=card,
            captured_at=CAPTURED,
        )
    with pytest.raises(JRATargetRaceCardResolutionValidationError):
        JRATargetRaceCardResolution(
            discovery=result.discovery,
            target_race_selection_capture=selection,
            target_race_card_capture=_card_capture(url=OTHER_CARD_URL),
            captured_at=CAPTURED,
        )


def test_repository_validation_error_propagates_unchanged() -> None:
    selection = _selection_capture()
    error = RepositoryValidationError("unchanged")
    with pytest.raises(RepositoryValidationError) as raised:
        resolve_jra_target_race_card_response(
            external_race_id=RACE_ID,
            target_race_selection_capture_id=selection.capture_id,
            captured_at=CAPTURED,
            target_race_selection_capture_provider=lambda **_: selection,
            target_race_card_capture_provider=lambda **_: (_ for _ in ()).throw(error),
        )
    assert raised.value is error
