import ast
import dataclasses
import inspect
import json
from datetime import date, datetime
from pathlib import Path
import unittest

import scripts.simulation.nar_historical_daily_target_bootstrap as bootstrap_module
from scripts.simulation.nar_historical_daily_target_bootstrap import (
    NARMonthlyConveneInfoBootstrapEvidence,
    NARMonthlyConveneInfoBootstrapIntegrityError,
    NARMonthlyConveneInfoLocatorScriptResolution,
    NARMonthlyConveneInfoRequestMaterialResolution,
    NARMonthlyConveneInfoRootLocator,
    NARMonthlyConveneInfoBootstrapUnsupportedError,
    NARMonthlyConveneInfoBootstrapValidationError,
    resolve_nar_monthly_convene_info_locator_script,
    resolve_nar_monthly_convene_info_request_material,
    resolve_nar_monthly_convene_info_request_identity,
    resolve_nar_monthly_convene_info_root_locator,
)
from scripts.simulation.nar_historical_daily_target_bootstrap_capture import (
    NARMonthlyConveneInfoBootstrapPageKind,
    NARMonthlyConveneInfoBootstrapSupplierCapture,
)
from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetPageKind,
    NARHistoricalDailyTargetRequestIdentity,
)


_FIXTURES = Path(__file__).parent / "fixtures" / "nar_daily_target_bootstrap"
_OLD_FIXTURES = Path(__file__).parent / "fixtures" / "nar_daily_targets"
_PROVENANCE = json.loads((_FIXTURES / "provenance.json").read_text(encoding="utf-8"))
_RECORDS = {item["fixture_role"]: item for item in _PROVENANCE["records"]}
_ROOT_RAW = b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"
_SCRIPT_RAW = b"/KeibaWeb/resources/js/monthltconveninfo.js?t=20260130_1"


def _capture(role, *, body=None):
    if role == "locator_script":
        old = json.loads((_OLD_FIXTURES / "provenance.json").read_text(encoding="utf-8"))
        record = next(item for item in old["records"] if item["role"] == "monthly_locator_supplier")
        item = _PROVENANCE["pinned_locator_script"]
        original = (_OLD_FIXTURES / record["path"]).read_bytes()
        return NARMonthlyConveneInfoBootstrapSupplierCapture(
            page_kind=NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT,
            canonical_request_url=record["requested_url"],
            effective_url=record["effective_url"],
            response_body=original if body is None else body,
            charset="utf-8",
            requested_at=datetime.fromisoformat(record["requested_at"]),
            observed_at=datetime.fromisoformat(record["observed_at"]),
            stored_at=datetime.fromisoformat(item["stored_at"]),
            http_status=old["acquisition_profile"]["http_status"],
            content_type=record["content_type"],
            content_encoding=record["content_encoding"],
            content_length=None,
        )
    item = _RECORDS[role]
    original = (_FIXTURES / item["path"]).read_bytes()
    value = original if body is None else body
    return NARMonthlyConveneInfoBootstrapSupplierCapture(
        page_kind={
            "official_home": NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME,
            "monthly_root": NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT,
        }[role],
        canonical_request_url=item["requested_url"],
        effective_url=item["effective_url"],
        response_body=value,
        charset=item["charset"],
        requested_at=datetime.fromisoformat(item["requested_at"]),
        observed_at=datetime.fromisoformat(item["observed_at"]),
        stored_at=datetime.fromisoformat(item["stored_at"]),
        http_status=item["http_status"],
        content_type=item["content_type"],
        content_encoding=item["content_encoding"],
        content_length=len(value) if item["content_length_header"] is not None else None,
    )


def _evidence(*, home_body=None, root_body=None, script_body=None):
    return NARMonthlyConveneInfoBootstrapEvidence(
        homepage_capture=_capture("official_home", body=home_body),
        monthly_root_capture=_capture("monthly_root", body=root_body),
        locator_script_capture=_capture("locator_script", body=script_body),
    )


def _replace_once(body, old, new):
    if body.count(old) != 1:
        raise AssertionError(f"test mutation is not unique: {old!r}")
    return body.replace(old, new, 1)


class NARMonthlyConveneInfoBootstrapTests(unittest.TestCase):
    def test_staged_relations_preserve_exact_source_material_and_capture_bindings(self):
        evidence = _evidence()
        root = resolve_nar_monthly_convene_info_root_locator(
            homepage_capture=evidence.homepage_capture
        )
        script = resolve_nar_monthly_convene_info_locator_script(
            target_date=date(2025, 12, 26),
            root_locator=root,
            monthly_root_capture=evidence.monthly_root_capture,
        )
        material = resolve_nar_monthly_convene_info_request_material(
            locator_script_resolution=script,
            locator_script_capture=evidence.locator_script_capture,
        )
        self.assertIs(type(root), NARMonthlyConveneInfoRootLocator)
        self.assertEqual(root.homepage_capture_id, evidence.homepage_capture.capture_id)
        self.assertEqual(root.homepage_response_sha256, evidence.homepage_capture.response_sha256)
        self.assertEqual(root.raw_href, _ROOT_RAW)
        self.assertEqual(script.root_locator, root)
        self.assertEqual(script.monthly_root_capture_id, evidence.monthly_root_capture.capture_id)
        self.assertEqual(script.raw_script_src, _SCRIPT_RAW)
        self.assertEqual(script.offered_year_token, b"2025")
        self.assertEqual(script.offered_month_token, b"12")
        self.assertIs(type(material), NARMonthlyConveneInfoRequestMaterialResolution)
        self.assertEqual(material.locator_script_capture_id, evidence.locator_script_capture.capture_id)
        self.assertEqual(
            material.official_supplied_request_material,
            _ROOT_RAW + b"?k_year=2025&k_month=12",
        )

    def test_staged_values_are_frozen_slotted_and_deterministic(self):
        evidence = _evidence()
        root = resolve_nar_monthly_convene_info_root_locator(
            homepage_capture=evidence.homepage_capture
        )
        again = resolve_nar_monthly_convene_info_root_locator(
            homepage_capture=evidence.homepage_capture
        )
        self.assertEqual(root, again)
        self.assertFalse(hasattr(root, "__dict__"))
        self.assertRegex(root.locator_identity, r"^nar-monthly-bootstrap-root-locator-v1:[0-9a-f]{64}$")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            root.resolved_url = "https://example.invalid/"

    def test_staged_capture_and_derived_identity_corruption_fail_closed(self):
        evidence = _evidence()
        root = resolve_nar_monthly_convene_info_root_locator(
            homepage_capture=evidence.homepage_capture
        )
        object.__setattr__(root, "homepage_capture_id", "nar-monthly-bootstrap-capture-v1:" + "0" * 64)
        with self.assertRaises(NARMonthlyConveneInfoBootstrapIntegrityError):
            resolve_nar_monthly_convene_info_locator_script(
                target_date=date(2025, 1, 1),
                root_locator=root,
                monthly_root_capture=evidence.monthly_root_capture,
            )

        root = resolve_nar_monthly_convene_info_root_locator(
            homepage_capture=evidence.homepage_capture
        )
        script = resolve_nar_monthly_convene_info_locator_script(
            target_date=date(2025, 1, 1),
            root_locator=root,
            monthly_root_capture=evidence.monthly_root_capture,
        )
        object.__setattr__(script, "monthly_root_response_sha256", "0" * 64)
        with self.assertRaises(NARMonthlyConveneInfoBootstrapIntegrityError):
            resolve_nar_monthly_convene_info_request_material(
                locator_script_resolution=script,
                locator_script_capture=evidence.locator_script_capture,
            )

    def test_staged_wrong_capture_kinds_and_types_fail_closed(self):
        evidence = _evidence()
        with self.assertRaises(NARMonthlyConveneInfoBootstrapValidationError):
            resolve_nar_monthly_convene_info_root_locator(
                homepage_capture=evidence.monthly_root_capture
            )
        root = resolve_nar_monthly_convene_info_root_locator(
            homepage_capture=evidence.homepage_capture
        )
        with self.assertRaises(NARMonthlyConveneInfoBootstrapValidationError):
            resolve_nar_monthly_convene_info_locator_script(
                target_date=date(2025, 1, 1),
                root_locator=root,
                monthly_root_capture=evidence.locator_script_capture,
            )

    def test_qualified_chain_returns_existing_exact_request_identity(self):
        evidence = _evidence()
        request = resolve_nar_monthly_convene_info_request_identity(
            target_date=date(2025, 1, 31), supplier_evidence=evidence
        )
        material = (
            b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"
            b"?k_year=2025&k_month=1"
        )
        self.assertIs(type(request), NARHistoricalDailyTargetRequestIdentity)
        self.assertIs(request.page_kind, NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO)
        self.assertEqual(request.official_supplied_request_material, material)
        self.assertEqual(request.resolved_request_url, b"https://www.keiba.go.jp".decode() + material.decode())
        self.assertEqual(request.supplier_evidence_identity, evidence.supplier_evidence_identity)
        self.assertEqual((request.target_year, request.target_month), (2025, 1))

    def test_all_qualified_year_cases_use_unpadded_source_tokens(self):
        evidence = _evidence()
        for target in (
            date(2020, 3, 1),
            date(2021, 1, 1),
            date(2024, 1, 1),
            date(2025, 1, 1),
            date(2026, 1, 1),
        ):
            with self.subTest(target=target):
                request = resolve_nar_monthly_convene_info_request_identity(
                    target_date=target, supplier_evidence=evidence
                )
                self.assertEqual(
                    request.official_supplied_request_material,
                    (
                        "/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"
                        f"?k_year={target.year}&k_month={target.month}"
                    ).encode("ascii"),
                )

    def test_repeat_is_deterministic_and_active_or_selected_state_is_not_authority(self):
        evidence = _evidence()
        first = resolve_nar_monthly_convene_info_request_identity(
            target_date=date(2024, 7, 2), supplier_evidence=evidence
        )
        second = resolve_nar_monthly_convene_info_request_identity(
            target_date=date(2024, 7, 2), supplier_evidence=evidence
        )
        self.assertEqual(first, second)
        root = evidence.monthly_root_capture.response_body
        changed = root.replace(b" selected ", b"          ", 1).replace(
            b'class="tab  active "', b'class="tab         "', 1
        )
        third = resolve_nar_monthly_convene_info_request_identity(
            target_date=date(2024, 7, 2), supplier_evidence=_evidence(root_body=changed)
        )
        self.assertEqual(
            third.official_supplied_request_material,
            first.official_supplied_request_material,
        )

    def test_dynamic_unrelated_home_and_root_changes_are_accepted(self):
        evidence = _evidence()
        home = _replace_once(
            evidence.homepage_capture.response_body,
            b"<title>",
            b"<!-- unrelated supplied change --><title>",
        )
        root = _replace_once(
            evidence.monthly_root_capture.response_body,
            b"<!-- Debug: Normal -->",
            b"<!-- unrelated dynamic supplier content -->",
        )
        request = resolve_nar_monthly_convene_info_request_identity(
            target_date=date(2025, 2, 1),
            supplier_evidence=_evidence(home_body=home, root_body=root),
        )
        self.assertEqual((request.target_year, request.target_month), (2025, 2))

    def test_homepage_missing_duplicate_lexical_and_wrong_structure_fail_closed(self):
        body = _capture("official_home").response_body
        exact = b'href="' + _ROOT_RAW + b'"'
        cases = (
            body.replace(exact, b'href="/wrong"', 1),
            body.replace(exact, exact + b"><a " + exact, 1),
            body.replace(exact, b"href='" + _ROOT_RAW + b"'", 1),
            body.replace(exact, b'href="&#47;KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"', 1),
            body.replace(b'class="gNaviitem2"', b'class="other"', 1),
        )
        for changed in cases:
            with self.subTest(prefix=changed[:20]), self.assertRaises(
                NARMonthlyConveneInfoBootstrapUnsupportedError
            ):
                resolve_nar_monthly_convene_info_request_identity(
                    target_date=date(2025, 1, 1),
                    supplier_evidence=_evidence(home_body=changed),
                )

    def test_root_script_missing_duplicate_single_quote_and_wrong_relation_fail_closed(self):
        body = _capture("monthly_root").response_body
        exact = b'src="' + _SCRIPT_RAW + b'"'
        cases = (
            body.replace(exact, b'src="/wrong.js"', 1),
            body.replace(exact, exact + b"></script><script " + exact, 1),
            body.replace(exact, b"src='" + _SCRIPT_RAW + b"'", 1),
            body.replace(exact, b'src="//evil.example/script.js"', 1),
        )
        for changed in cases:
            with self.subTest(), self.assertRaises(NARMonthlyConveneInfoBootstrapUnsupportedError):
                resolve_nar_monthly_convene_info_request_identity(
                    target_date=date(2025, 1, 1),
                    supplier_evidence=_evidence(root_body=changed),
                )

    def test_year_controls_missing_duplicate_malformed_and_unoffered_fail_closed(self):
        body = _capture("monthly_root").response_body
        cases = (
            body.replace(b'id="selectedYear"', b'id="other"', 1),
            body.replace(b'id="selectedYear"', b'id="selectedYear" name="k_year"', 1),
            body.replace(b'<option value="2025"', b'<option value="02025"', 1),
            body.replace(b'<option value="2025"', b'<option value="2024"', 1),
            body.replace(b"                                    2025\n", b"                                    9999\n", 1),
        )
        for changed in cases:
            with self.subTest(), self.assertRaises(NARMonthlyConveneInfoBootstrapUnsupportedError):
                resolve_nar_monthly_convene_info_request_identity(
                    target_date=date(2025, 1, 1),
                    supplier_evidence=_evidence(root_body=changed),
                )

    def test_month_controls_missing_duplicate_malformed_and_incomplete_fail_closed(self):
        body = _capture("monthly_root").response_body
        cases = (
            body.replace(b'class="monthTab clearfix"', b'class="other"', 1),
            body.replace(b'id="monthTab12"', b'id="monthTab11"', 1),
            body.replace(b'month="12"', b'month="11"', 1),
            body.replace(b'month="1"', b'month="01"', 1),
            body.replace(b"<p>1\xe6\x9c\x88</p>", b"<p>2\xe6\x9c\x88</p>", 1),
        )
        for changed in cases:
            with self.subTest(), self.assertRaises(NARMonthlyConveneInfoBootstrapUnsupportedError):
                resolve_nar_monthly_convene_info_request_identity(
                    target_date=date(2025, 1, 1),
                    supplier_evidence=_evidence(root_body=changed),
                )

    def test_exact_pinned_script_and_grammar_are_required(self):
        body = _capture("locator_script").response_body
        request = resolve_nar_monthly_convene_info_request_identity(
            target_date=date(2025, 12, 1), supplier_evidence=_evidence()
        )
        self.assertEqual(
            request.official_supplied_request_material,
            _ROOT_RAW + b"?k_year=2025&k_month=12",
        )
        mutations = (
            body.replace(b"k_year", b"x_year", 1),
            body.replace(b"&k_month", b"&x_month", 1),
            body.replace(b" + year + ", b" + month + ", 1),
            body.replace(b"//EOF", b"//EOX", 1),
            body + body,
        )
        for changed in mutations:
            with self.subTest(), self.assertRaises(NARMonthlyConveneInfoBootstrapUnsupportedError):
                resolve_nar_monthly_convene_info_request_identity(
                    target_date=date(2025, 1, 1),
                    supplier_evidence=_evidence(script_body=changed),
                )

    def test_no_direct_url_generation_fallback_for_absent_source_tokens(self):
        root = _capture("monthly_root").response_body
        root = root.replace(b'<option value="2025"', b'<option value="1997"', 1)
        with self.assertRaises(NARMonthlyConveneInfoBootstrapUnsupportedError):
            resolve_nar_monthly_convene_info_request_identity(
                target_date=date(2025, 1, 1), supplier_evidence=_evidence(root_body=root)
            )

    def test_date_type_floor_and_supplier_type_are_strict(self):
        evidence = _evidence()
        for invalid in (datetime(2025, 1, 1), "2025-01-01", None):
            with self.subTest(invalid=invalid), self.assertRaises(
                NARMonthlyConveneInfoBootstrapValidationError
            ):
                resolve_nar_monthly_convene_info_request_identity(
                    target_date=invalid, supplier_evidence=evidence
                )
        with self.assertRaises(NARMonthlyConveneInfoBootstrapUnsupportedError):
            resolve_nar_monthly_convene_info_request_identity(
                target_date=date(2019, 12, 31), supplier_evidence=evidence
            )
        with self.assertRaises(NARMonthlyConveneInfoBootstrapValidationError):
            resolve_nar_monthly_convene_info_request_identity(
                target_date=date(2025, 1, 1), supplier_evidence=object()
            )

    def test_aggregate_slots_and_identity_are_exact_immutable_and_deterministic(self):
        evidence = _evidence()
        self.assertEqual(evidence, _evidence())
        self.assertEqual(
            evidence.supplier_evidence_identity,
            _PROVENANCE["supplier_evidence_identity"],
        )
        self.assertFalse(hasattr(evidence, "__dict__"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            evidence.schema_version = 2
        with self.assertRaises(NARMonthlyConveneInfoBootstrapValidationError):
            NARMonthlyConveneInfoBootstrapEvidence(
                homepage_capture=evidence.monthly_root_capture,
                monthly_root_capture=evidence.homepage_capture,
                locator_script_capture=evidence.locator_script_capture,
            )

    def test_mutated_capture_body_and_capture_id_are_global_integrity_errors(self):
        for field, replacement in (
            ("response_body", b"corrupt"),
            ("response_sha256", "0" * 64),
            ("capture_id", "nar-monthly-bootstrap-capture-v1:" + "0" * 64),
        ):
            evidence = _evidence()
            object.__setattr__(evidence.homepage_capture, field, replacement)
            with self.subTest(field=field), self.assertRaises(
                NARMonthlyConveneInfoBootstrapIntegrityError
            ):
                resolve_nar_monthly_convene_info_request_identity(
                    target_date=date(2025, 1, 1), supplier_evidence=evidence
                )

    def test_mutated_aggregate_identity_is_global_integrity_error(self):
        evidence = _evidence()
        object.__setattr__(
            evidence,
            "supplier_evidence_identity",
            "nar-monthly-bootstrap-evidence-v1:" + "0" * 64,
        )
        with self.assertRaises(NARMonthlyConveneInfoBootstrapIntegrityError):
            resolve_nar_monthly_convene_info_request_identity(
                target_date=date(2025, 1, 1), supplier_evidence=evidence
            )

    def test_supplier_observation_times_remain_honest_and_are_not_output_causality(self):
        evidence = _evidence()
        request = resolve_nar_monthly_convene_info_request_identity(
            target_date=date(2020, 3, 1), supplier_evidence=evidence
        )
        self.assertGreater(evidence.homepage_capture.observed_at.date(), date(2020, 3, 1))
        self.assertGreater(evidence.monthly_root_capture.observed_at.date(), date(2020, 3, 1))
        self.assertFalse(hasattr(request, "observed_at"))
        self.assertFalse(hasattr(request, "information_cutoff"))

    def test_production_modules_have_no_network_clock_eval_browser_or_storage_calls(self):
        forbidden_import_roots = {
            "requests", "httpx", "urllib", "socket", "time", "sqlite3",
            "selenium", "playwright", "pathlib",
        }
        forbidden_calls = {"eval", "exec", "open", "save", "load"}
        for module in (bootstrap_module, __import__(
            "scripts.simulation.nar_historical_daily_target_bootstrap_capture",
            fromlist=["*"],
        )):
            tree = ast.parse(inspect.getsource(module))
            imports = set()
            calls = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        calls.add(node.func.attr)
            self.assertFalse(imports & forbidden_import_roots)
            self.assertFalse(calls & forbidden_calls)
            self.assertNotIn("datetime.now", inspect.getsource(module))
            self.assertNotIn("datetime.today", inspect.getsource(module))
            self.assertNotIn("utcnow", inspect.getsource(module))

    def test_public_exports_and_keyword_only_resolver_signature_are_exact(self):
        public = {name for name in vars(bootstrap_module) if not name.startswith("_")}
        self.assertEqual(
            public,
            {
                "NARMonthlyConveneInfoBootstrapError",
                "NARMonthlyConveneInfoBootstrapValidationError",
                "NARMonthlyConveneInfoBootstrapUnsupportedError",
                "NARMonthlyConveneInfoBootstrapIntegrityError",
                "NARMonthlyConveneInfoBootstrapEvidence",
                "NARMonthlyConveneInfoRootLocator",
                "NARMonthlyConveneInfoLocatorScriptResolution",
                "NARMonthlyConveneInfoRequestMaterialResolution",
                "resolve_nar_monthly_convene_info_root_locator",
                "resolve_nar_monthly_convene_info_locator_script",
                "resolve_nar_monthly_convene_info_request_material",
                "resolve_nar_monthly_convene_info_request_identity",
            },
        )
        staged_functions = (
            resolve_nar_monthly_convene_info_root_locator,
            resolve_nar_monthly_convene_info_locator_script,
            resolve_nar_monthly_convene_info_request_material,
        )
        self.assertTrue(
            all(
                value.kind is inspect.Parameter.KEYWORD_ONLY
                for function in staged_functions
                for value in inspect.signature(function).parameters.values()
            )
        )
        parameters = inspect.signature(
            resolve_nar_monthly_convene_info_request_identity
        ).parameters
        self.assertEqual(tuple(parameters), ("target_date", "supplier_evidence"))
        self.assertTrue(
            all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in parameters.values())
        )


if __name__ == "__main__":
    unittest.main()
