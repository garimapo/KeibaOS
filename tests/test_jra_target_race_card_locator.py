from __future__ import annotations

import ast
from dataclasses import is_dataclass
from datetime import datetime, timezone
import inspect
from pathlib import Path

import pytest

from scripts.simulation.jra_target_race_card_locator import (
    JRAOfficialTargetNavigationMenuSuppliedResponse,
    JRATargetMeetingSelectionRequestLocator,
    JRATargetMeetingSelectionSuppliedOfficialResponse,
    JRATargetRaceCardLocator,
    JRATargetRaceCardLocatorUnavailableError,
    JRATargetRaceCardLocatorValidationError,
    JRATargetRaceSelectionRequestLocator,
    build_jra_target_meeting_selection_request_locator,
    build_jra_target_race_selection_request_locator,
    discover_jra_target_meeting_selection_request_locator,
    discover_jra_target_race_selection_request_locator,
)


UTC = timezone.utc
OBSERVED = datetime(2025, 9, 12, 3, 4, tzinfo=UTC)
RACE_ID = "jra:race:2025:06:04:03:04"
MEETING_CNAME = "pw01dli00/F3"
RACE_CNAME = "pw01drl00062025040320250913/DC"
CARD_URL = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0106202504030420250913%2FDC"


def _bytes(value: str) -> bytes:
    return value.encode("cp932")


def _root(onclick: str = "doAction('/JRADB/accessD.html','pw01dli00/F3');return false;") -> JRAOfficialTargetNavigationMenuSuppliedResponse:
    return JRAOfficialTargetNavigationMenuSuppliedResponse(
        _bytes(f'<div id="quick_menu"><a href="#" data-ga-click="quick_pc-1" onclick="{onclick}">出馬表</a></div>'),
        "cp932",
        OBSERVED,
    )


def _meeting_response(*, controls: tuple[str, ...] = (RACE_CNAME,)) -> JRATargetMeetingSelectionSuppliedOfficialResponse:
    links = "".join(
        f'<div class="waku"><a href="#" onclick="return doAction(\'/JRADB/accessD.html\', \'{cname}\');">選択</a></div>'
        for cname in controls
    )
    html = f'<div id="contentsBody"><div class="link_list multi div3 center">{links}</div></div>'
    return JRATargetMeetingSelectionSuppliedOfficialResponse(
        build_jra_target_meeting_selection_request_locator(cname=MEETING_CNAME), _bytes(html), "cp932", OBSERVED
    )


def test_exact_public_surface_and_pure_dependencies() -> None:
    import scripts.simulation.jra_target_race_card_locator as module

    assert module.__all__ == (
        "JRAOfficialTargetNavigationMenuSuppliedResponse",
        "JRATargetMeetingSelectionRequestLocator",
        "JRATargetMeetingSelectionSuppliedOfficialResponse",
        "JRATargetRaceSelectionRequestLocator",
        "JRATargetRaceCardLocator",
        "JRATargetRaceCardLocatorError",
        "JRATargetRaceCardLocatorValidationError",
        "JRATargetRaceCardLocatorUnavailableError",
        "build_jra_target_meeting_selection_request_locator",
        "build_jra_target_race_selection_request_locator",
        "discover_jra_target_meeting_selection_request_locator",
        "discover_jra_target_race_selection_request_locator",
    )
    assert tuple(inspect.signature(discover_jra_target_meeting_selection_request_locator).parameters) == ("navigation_menu_response",)
    assert tuple(inspect.signature(discover_jra_target_race_selection_request_locator).parameters) == (
        "external_race_id", "meeting_selection_response"
    )
    for domain in (
        JRAOfficialTargetNavigationMenuSuppliedResponse,
        JRATargetMeetingSelectionRequestLocator,
        JRATargetMeetingSelectionSuppliedOfficialResponse,
        JRATargetRaceSelectionRequestLocator,
        JRATargetRaceCardLocator,
    ):
        assert is_dataclass(domain) and domain.__dataclass_params__.frozen
        assert hasattr(domain, "__slots__")
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"requests", "httpx", "sqlite3", "pathlib", "random", "subprocess", "time", "socket"}
    assert not any(
        (isinstance(node, ast.Import) and any(item.name.split(".")[0] in forbidden for item in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden)
        for node in ast.walk(tree)
    )
    assert not any(isinstance(node, ast.ExceptHandler) and isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"} for node in ast.walk(tree))
    assert "now(" not in source and "open(" not in source


def test_root_supplied_domain_is_exact_strict_cp932_and_aware() -> None:
    value = _root()
    assert value.charset == "cp932" and value.observed_at is OBSERVED
    with pytest.raises(JRATargetRaceCardLocatorValidationError):
        JRAOfficialTargetNavigationMenuSuppliedResponse(b"", "cp932", OBSERVED)
    with pytest.raises(JRATargetRaceCardLocatorValidationError):
        JRAOfficialTargetNavigationMenuSuppliedResponse("x", "cp932", OBSERVED)  # type: ignore[arg-type]
    with pytest.raises(JRATargetRaceCardLocatorValidationError):
        JRAOfficialTargetNavigationMenuSuppliedResponse(b"\x81", "cp932", OBSERVED)
    with pytest.raises(JRATargetRaceCardLocatorValidationError):
        JRAOfficialTargetNavigationMenuSuppliedResponse(_bytes("x"), "shift_jis", OBSERVED)
    with pytest.raises(JRATargetRaceCardLocatorValidationError):
        JRAOfficialTargetNavigationMenuSuppliedResponse(_bytes("x"), "cp932", datetime(2025, 1, 1))


def test_meeting_locator_raw_grammar_and_exact_fingerprint() -> None:
    locator = build_jra_target_meeting_selection_request_locator(cname=MEETING_CNAME)
    assert locator.endpoint_url == "https://www.jra.go.jp/JRADB/accessD.html"
    assert locator.cname == MEETING_CNAME
    assert locator.request_identity_sha256 == "94c45931bea6f880f3234edbaaf2d486009d704921b250cd2ce76ea03dae8aac"
    for cname in ("pw01dli00/f3", "pw01dli00/%2FF3", "pw01dli00+F3", "pw01dli00/F3 ", "pw01dli00/F3/", "pw01dli00/", "pw01dli10/F3", "pw01xli00/F3"):
        with pytest.raises(JRATargetRaceCardLocatorValidationError):
            build_jra_target_meeting_selection_request_locator(cname=cname)


def test_root_discovery_is_exact_raw_control_and_not_hard_coded() -> None:
    assert discover_jra_target_meeting_selection_request_locator(navigation_menu_response=_root()).cname == MEETING_CNAME
    assert discover_jra_target_meeting_selection_request_locator(
        navigation_menu_response=_root("doAction('/JRADB/accessD.html','pw01dli00/F4');return false;")
    ).cname == "pw01dli00/F4"
    for onclick in (
        "", "doAction('/JRADB/accessD.html','pw01dli00/F3')", "return doAction('/JRADB/accessD.html','pw01dli00/F3');",
        'doAction("/JRADB/accessD.html","pw01dli00/F3");return false;',
        "doAction('/JRADB/accessD.html','pw01dli00/' + 'F3');return false;",
        "doAction('/JRADB/accessS.html','pw01dli00/F3');return false;",
    ):
        with pytest.raises(JRATargetRaceCardLocatorValidationError):
            discover_jra_target_meeting_selection_request_locator(navigation_menu_response=_root(onclick))
    duplicate = _bytes(
        '<div id="quick_menu"><a href="#" data-ga-click="quick_pc-1" onclick="doAction(\'/JRADB/accessD.html\',\'pw01dli00/F3\');return false;">A</a>'
        '<a href="#" data-ga-click="quick_pc-1" onclick="doAction(\'/JRADB/accessD.html\',\'pw01dli00/F4\');return false;">B</a></div>'
    )
    response = JRAOfficialTargetNavigationMenuSuppliedResponse(duplicate, "cp932", OBSERVED)
    with pytest.raises(JRATargetRaceCardLocatorValidationError):
        discover_jra_target_meeting_selection_request_locator(navigation_menu_response=response)
    entity_recovered = JRAOfficialTargetNavigationMenuSuppliedResponse(
        _bytes('<div id="quick_menu"><a href="#" data-ga-click="quick_pc-1" onclick="doAction(&#39;/JRADB/accessD.html&#39;,&#39;pw01dli00/F3&#39;);return false;">出馬表</a></div>'),
        "cp932",
        OBSERVED,
    )
    with pytest.raises(JRATargetRaceCardLocatorValidationError):
        discover_jra_target_meeting_selection_request_locator(navigation_menu_response=entity_recovered)


def test_meeting_supplied_and_race_selection_locator_fail_closed() -> None:
    meeting = _meeting_response()
    result = discover_jra_target_race_selection_request_locator(external_race_id=RACE_ID, meeting_selection_response=meeting)
    assert (result.year, result.venue_code, result.meeting_number, result.meeting_day, result.calendar_date) == ("2025", "06", "04", "03", "20250913")
    assert result.cname == RACE_CNAME
    assert result.request_identity_sha256 == "6d19d4f89d926dcaa9f5b845316efb3434392305f3c95f5aa1964ed11bd2a6bb"
    alternate_race = "jra:race:2025:06:04:03:12"
    assert discover_jra_target_race_selection_request_locator(external_race_id=alternate_race, meeting_selection_response=meeting) == result
    with pytest.raises(JRATargetRaceCardLocatorUnavailableError):
        discover_jra_target_race_selection_request_locator(external_race_id="jra:race:2025:05:04:03:04", meeting_selection_response=meeting)
    conflicting = _meeting_response(controls=(RACE_CNAME, RACE_CNAME.replace("/DC", "/DD")))
    with pytest.raises(JRATargetRaceCardLocatorValidationError):
        discover_jra_target_race_selection_request_locator(external_race_id=RACE_ID, meeting_selection_response=conflicting)
    for cname in (RACE_CNAME.replace("20250913", "20251313"), RACE_CNAME.replace("/DC", "%2FDC"), RACE_CNAME.replace("/DC", "/dc")):
        with pytest.raises(JRATargetRaceCardLocatorValidationError):
            build_jra_target_race_selection_request_locator(cname=cname)


def test_target_locator_requires_canonical_exact_accessd_url_and_matching_race() -> None:
    assert JRATargetRaceCardLocator(RACE_ID, CARD_URL).canonical_target_race_card_url == CARD_URL
    for url in (CARD_URL.replace("%2F", "/"), CARD_URL.replace("accessD", "accessS"), CARD_URL.replace("0403", "0404", 1)):
        with pytest.raises(JRATargetRaceCardLocatorValidationError):
            JRATargetRaceCardLocator(RACE_ID, url)
