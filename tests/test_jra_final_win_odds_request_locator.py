from __future__ import annotations

import ast
from datetime import datetime, timezone
import inspect
from pathlib import Path
import unittest

from scripts.simulation.jra_final_win_odds_request_locator import (
    JRAFinalWinOddsRequestLocatorExtractionError,
    JRAFinalWinOddsRequestLocatorExtractionValidationError,
    extract_jra_final_win_odds_request_locator,
)
from scripts.simulation.jra_official_identity import JRAExternalRaceIdentity
from scripts.simulation.jra_official_response_capture import JRASuppliedOfficialResponse


ACCESS_S_URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde1006202601021220260105%2F2E"
CNAME = "pw151ou1006202601021220260105Z/2E"
FINGERPRINT = "9c4a4f2dfc7e2c21841f7a2bb3f36ec7397312a34b565ff7e511e74800774ade"
OBSERVED = datetime(2026, 1, 5, 12, tzinfo=timezone.utc)


def _control(*, cname: str = CNAME, label: str = "オッズ", href: str = "#", onclick: str | None = None) -> str:
    if onclick is None:
        onclick = f"return doAction('/JRADB/accessO.html', '{cname}');"
    return (
        '<li><a class="btn-def btn-sm blue btn-block"'
        f' href="{href}" onclick="{onclick}"><i class="fa"></i>{label}</a></li>'
    )


def _body(*, control: str | None = None, generic: str = "", hidden: str = "", duplicate_table: bool = False) -> bytes:
    if control is None:
        control = _control()
    table = (
        '<div id="race_result" class="mt20"><div class="race_result_unit">'
        '<table class="basic narrow-xy striped"><caption><div class="race_header">'
        '<div class="right"><div class="race_related_link"><ul>'
        f"{control}</ul></div></div></div></caption><tbody><tr><td>result</td></tr></tbody></table>"
        "</div></div>"
    )
    if duplicate_table:
        table += table
    return f"<html><body>{generic}{hidden}{table}</body></html>".encode("cp932")


def _response(*, body: bytes | None = None, url: str = ACCESS_S_URL) -> JRASuppliedOfficialResponse:
    return JRASuppliedOfficialResponse(url, _body() if body is None else body, "cp932", OBSERVED)


def _extract(**changes: object):
    response = changes.pop("race_result_response", None)
    if response is None:
        response = _response(**changes)
    return extract_jra_final_win_odds_request_locator(race_result_response=response)


class JRAFinalWinOddsRequestLocatorExtractionTests(unittest.TestCase):
    def test_public_api_and_pure_boundary(self) -> None:
        import scripts.simulation.jra_final_win_odds_request_locator as module

        self.assertEqual(
            {name for name in vars(module) if not name.startswith("_")},
            {
                "JRAFinalWinOddsRequestLocatorExtractionError",
                "JRAFinalWinOddsRequestLocatorExtractionValidationError",
                "extract_jra_final_win_odds_request_locator",
            },
        )
        self.assertTrue(
            issubclass(
                JRAFinalWinOddsRequestLocatorExtractionValidationError,
                JRAFinalWinOddsRequestLocatorExtractionError,
            )
        )
        self.assertEqual(tuple(inspect.signature(extract_jra_final_win_odds_request_locator).parameters), ("race_result_response",))
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {"requests", "httpx", "sqlite3", "pathlib", "random", "subprocess", "time", "socket", "os"}
        self.assertFalse(any(
            (isinstance(node, ast.Import) and any(item.name.split(".")[0] in forbidden for item in node.names))
            or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden)
            for node in ast.walk(tree)
        ))
        self.assertNotIn("open(", source)
        package_root = Path(__file__).resolve().parents[1] / "scripts" / "simulation" / "__init__.py"
        if package_root.exists():
            self.assertNotIn("jra_final_win_odds_request_locator", package_root.read_text(encoding="utf-8"))

    def test_exact_result_header_control_builds_deterministic_locator(self) -> None:
        locator = _extract()
        self.assertEqual(locator.endpoint_url, "https://www.jra.go.jp/JRADB/accessO.html")
        self.assertEqual(locator.cname, CNAME)
        self.assertEqual(locator.request_identity_sha256, FINGERPRINT)
        self.assertEqual(locator.external_race_identity, JRAExternalRaceIdentity("2026", "06", "01", "02", "12"))
        self.assertEqual(_extract(), locator)

    def test_input_type_family_url_and_cp932_fail_closed(self) -> None:
        with self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
            _extract(race_result_response=object())
        with self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
            _extract(url="https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud103001234567%2FAA")
        malformed_url = _response()
        object.__setattr__(malformed_url, "response_url", "https://www.jra.go.jp/JRADB/accessS.html?CNAME=bad")
        with self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
            _extract(race_result_response=malformed_url)
        malformed_cp932 = _response()
        object.__setattr__(malformed_cp932, "response_body", b"\x81")
        with self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
            _extract(race_result_response=malformed_cp932)
        malformed_charset = _response()
        object.__setattr__(malformed_charset, "charset", "utf-8")
        with self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
            _extract(race_result_response=malformed_charset)

    def test_generic_navigation_and_hidden_form_are_not_candidates(self) -> None:
        generic = '<a class="btn-def btn-sm blue btn-block" href="#" onclick="return doAction(\'/JRADB/accessO.html\', \'pw15oli00/6D\');">menu</a>'
        hidden = f'<form id="commForm01"><input name="cname" value="{CNAME}" /></form>'
        locator = _extract(body=_body(generic=generic, hidden=hidden))
        self.assertEqual(locator.cname, CNAME)
        with self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
            _extract(body=_body(control="", generic=generic, hidden=hidden))

    def test_navigation_structure_label_href_and_multiplicity_fail_closed(self) -> None:
        for control in (
            "",
            _control(label="別のオッズ"),
            _control(href="/JRADB/accessO.html"),
            _control(onclick="return doAction('/JRADB/accessP.html', '" + CNAME + "');"),
        ):
            with self.subTest(control=control), self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
                _extract(body=_body(control=control))
        duplicate = _control() + _control()
        with self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
            _extract(body=_body(control=duplicate))
        with self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
            _extract(body=_body(duplicate_table=True))

    def test_onclick_grammar_and_raw_source_spelling_fail_closed(self) -> None:
        invalid = (
            "doAction('/JRADB/accessO.html', '" + CNAME + "');",
            "return doAction(\"/JRADB/accessO.html\", \"" + CNAME + "\");",
            "return doAction('/JRADB/accessO.html', '" + CNAME.replace("/", "\\\\u002F") + "');",
            "return doAction('/JRADB/accessO.html', '" + CNAME.replace("/", "%2F") + "');",
            "return doAction('/JRADB/accessO.html', 'pw151ou1006202601021220260105Z/' + '2E');",
            "return doAction('/JRADB/accessO.html', '" + CNAME + "'); alert(1)",
            "return doAction('/JRADB/accessO.html?x=1', '" + CNAME + "');",
            "return doAction('/JRADB/accessO.html', '" + CNAME + "', 'extra');",
            "return wrongAction('/JRADB/accessO.html', '" + CNAME + "');",
        )
        for onclick in invalid:
            with self.subTest(onclick=onclick), self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
                _extract(body=_body(control=_control(onclick=onclick)))
        for entity_marker in ("&#39;", "&#x27;", "&apos;"):
            entity = _control().replace("'", entity_marker)
            with self.subTest(entity_marker=entity_marker), self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
                _extract(body=_body(control=entity))

    def test_entity_encoded_selected_control_cannot_use_unrelated_raw_decoy(self) -> None:
        entity = _control().replace("'", "&#39;")
        decoded = f'onclick="return doAction(\'/JRADB/accessO.html\', \'{CNAME}\');"'
        comment_decoy = f"<!-- {decoded} -->"
        script_decoy = f"<script>const rawNavigation = `{decoded}`;</script>"
        for decoy in (comment_decoy, script_decoy):
            with self.subTest(decoy=decoy), self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
                _extract(body=_body(control=entity, generic=decoy))

    def test_cname_grammar_identity_crosscheck_and_no_synthesis_fail_closed(self) -> None:
        for cname in (CNAME.replace("2E", "2e"), CNAME + " ", "pw151ou1006202601021220260105Z%2F2E"):
            with self.subTest(cname=cname), self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
                _extract(body=_body(control=_control(cname=cname)))
        wrong_race = CNAME.replace("0212", "0211", 1)
        with self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
            _extract(body=_body(control=_control(cname=wrong_race)))
        with self.assertRaises(JRAFinalWinOddsRequestLocatorExtractionValidationError):
            _extract(body=_body(control=""))


if __name__ == "__main__":
    unittest.main()
