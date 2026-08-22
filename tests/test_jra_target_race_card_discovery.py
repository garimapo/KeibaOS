from __future__ import annotations

import ast
from dataclasses import is_dataclass
from datetime import datetime, timezone
import hashlib
import inspect
from pathlib import Path

import pytest

from scripts.simulation.jra_target_race_card_discovery import (
    JRATargetRaceCardDiscovery,
    JRATargetRaceCardDiscoveryUnavailableError,
    JRATargetRaceCardDiscoveryValidationError,
    JRATargetRaceSelectionSuppliedOfficialResponse,
    discover_jra_target_race_card_locator,
)
from scripts.simulation.jra_target_race_card_locator import (
    JRATargetRaceCardLocator,
    build_jra_target_race_selection_request_locator,
)


UTC = timezone.utc
OBSERVED = datetime(2025, 9, 12, 3, 4, tzinfo=UTC)
RACE_ID = "jra:race:2025:06:04:03:04"
RACE_CNAME = "pw01drl00062025040320250913/DC"
RAW_CARD = "/JRADB/accessD.html?CNAME=pw01dde0106202504030420250913/DC"
CANONICAL_CARD = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0106202504030420250913%2FDC"


def _bytes(value: str) -> bytes:
    return value.encode("cp932")


def _row(*, race_href: str = RAW_CARD, card_href: str = RAW_CARD) -> str:
    return (
        '<tr><th class="race_num"><a href="' + race_href + '">表示名</a></th>'
        '<td class="syutsuba"><a class="btn-def btn-sm btn-narrow" href="' + card_href + '">出馬表</a></td></tr>'
    )


def _response(*rows: str, cname: str = RACE_CNAME) -> JRATargetRaceSelectionSuppliedOfficialResponse:
    html = '<div id="contentsBody"><div class="race_select"><table id="race_list" class="basic mt20"><tbody>' + "".join(rows) + "</tbody></table></div></div>"
    return JRATargetRaceSelectionSuppliedOfficialResponse(
        build_jra_target_race_selection_request_locator(cname=cname), _bytes(html), "cp932", OBSERVED
    )


def test_exact_public_surface_and_pure_boundary() -> None:
    import scripts.simulation.jra_target_race_card_discovery as module

    assert module.__all__ == (
        "JRATargetRaceSelectionSuppliedOfficialResponse",
        "JRATargetRaceCardDiscovery",
        "JRATargetRaceCardDiscoveryError",
        "JRATargetRaceCardDiscoveryValidationError",
        "JRATargetRaceCardDiscoveryUnavailableError",
        "discover_jra_target_race_card_locator",
    )
    assert tuple(inspect.signature(discover_jra_target_race_card_locator).parameters) == ("external_race_id", "navigation_response")
    assert is_dataclass(JRATargetRaceSelectionSuppliedOfficialResponse)
    assert JRATargetRaceSelectionSuppliedOfficialResponse.__dataclass_params__.frozen
    assert is_dataclass(JRATargetRaceCardDiscovery) and JRATargetRaceCardDiscovery.__dataclass_params__.frozen
    assert hasattr(JRATargetRaceSelectionSuppliedOfficialResponse, "__slots__") and hasattr(JRATargetRaceCardDiscovery, "__slots__")
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"requests", "httpx", "sqlite3", "pathlib", "random", "subprocess", "time", "socket"}
    assert not any(
        (isinstance(node, ast.Import) and any(item.name.split(".")[0] in forbidden for item in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden)
        for node in ast.walk(tree)
    )
    assert not any(isinstance(node, ast.ExceptHandler) and isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"} for node in ast.walk(tree))


def test_race_selection_response_requires_exact_cp932_types_and_aware_time() -> None:
    request = build_jra_target_race_selection_request_locator(cname=RACE_CNAME)
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        JRATargetRaceSelectionSuppliedOfficialResponse(object(), b"x", "cp932", OBSERVED)  # type: ignore[arg-type]
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        JRATargetRaceSelectionSuppliedOfficialResponse(request, b"", "cp932", OBSERVED)
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        JRATargetRaceSelectionSuppliedOfficialResponse(request, b"\x81", "cp932", OBSERVED)
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        JRATargetRaceSelectionSuppliedOfficialResponse(request, b"x", "utf-8", OBSERVED)
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        JRATargetRaceSelectionSuppliedOfficialResponse(request, b"x", "cp932", datetime(2025, 1, 1))


def test_final_discovery_canonicalizes_relative_href_and_binds_exact_navigation_evidence() -> None:
    response = _response(_row())
    result = discover_jra_target_race_card_locator(external_race_id=RACE_ID, navigation_response=response)
    assert result.locator == JRATargetRaceCardLocator(RACE_ID, CANONICAL_CARD)
    assert result.navigation_request_locator is response.request_locator
    assert result.navigation_response_sha256 == hashlib.sha256(response.response_body).hexdigest()
    assert result.navigation_observed_at is OBSERVED


def test_final_discovery_requires_two_same_row_anchors_and_exact_table_scope() -> None:
    response = _response(_row(card_href=RAW_CARD.replace("/DC", "/DD")))
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        discover_jra_target_race_card_locator(external_race_id=RACE_ID, navigation_response=response)
    missing = _response('<tr><th class="race_num"><a href="' + RAW_CARD + '">4R</a></th><td class="syutsuba"></td></tr>')
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        discover_jra_target_race_card_locator(external_race_id=RACE_ID, navigation_response=missing)
    bad_scope = JRATargetRaceSelectionSuppliedOfficialResponse(
        build_jra_target_race_selection_request_locator(cname=RACE_CNAME), _bytes('<table id="race_list" class="basic mt20"><tbody>' + _row() + "</tbody></table>"), "cp932", OBSERVED
    )
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        discover_jra_target_race_card_locator(external_race_id=RACE_ID, navigation_response=bad_scope)


def test_final_discovery_is_fail_closed_for_absence_duplicate_and_site_variant_conflict() -> None:
    absent_href = RAW_CARD.replace("0420250913", "0520250913")
    absent = _response(_row(race_href=absent_href, card_href=absent_href))
    with pytest.raises(JRATargetRaceCardDiscoveryUnavailableError):
        discover_jra_target_race_card_locator(external_race_id=RACE_ID, navigation_response=absent)
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        discover_jra_target_race_card_locator(external_race_id=RACE_ID, navigation_response=_response(_row(), _row()))
    variant = RAW_CARD.replace("dde01", "dde10").replace("/DC", "/DD")
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        discover_jra_target_race_card_locator(external_race_id=RACE_ID, navigation_response=_response(_row(), _row(race_href=variant, card_href=variant)))


def test_final_discovery_rejects_wrong_family_noncanonical_and_navigation_identity_conflict() -> None:
    for href in (RAW_CARD.replace("accessD", "accessS"), RAW_CARD.replace("/DC", "%2fDC"), RAW_CARD.replace("/DC", "/D/C")):
        with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
            discover_jra_target_race_card_locator(external_race_id=RACE_ID, navigation_response=_response(_row(race_href=href, card_href=href)))
    wrong_navigation = _response(_row(), cname=RACE_CNAME.replace("0403", "0503", 1))
    with pytest.raises(JRATargetRaceCardDiscoveryValidationError):
        discover_jra_target_race_card_locator(external_race_id=RACE_ID, navigation_response=wrong_navigation)
    with pytest.raises(JRATargetRaceCardDiscoveryUnavailableError):
        discover_jra_target_race_card_locator(external_race_id="jra:race:2025:06:04:03:05", navigation_response=_response(_row()))
