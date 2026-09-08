import ast
import dataclasses
from datetime import date, datetime, timedelta, timezone
import inspect
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import scripts.simulation.nar_daily_target_live_acquisition as subject
from scripts.simulation.nar_daily_target_evidence_archive_migration import (
    apply_nar_daily_target_evidence_archive_migrations,
)
from scripts.simulation.nar_daily_target_live_acquisition import (
    NARDailyTargetLiveAcquisitionApplication,
    NARDailyTargetLiveAcquisitionResult,
)
from scripts.simulation.nar_historical_daily_target_bootstrap_capture import (
    NARMonthlyConveneInfoBootstrapPageKind,
)
from scripts.simulation.nar_historical_daily_target_bootstrap_live_capture import (
    _NARMonthlyConveneInfoBootstrapHTTPResponse,
)
from scripts.simulation.nar_historical_daily_target_live_capture import (
    _NARHistoricalDailyTargetHTTPResponse,
)
from scripts.simulation.nar_historical_daily_target_source import (
    NARHistoricalDailyTargetSourceValidationError,
    build_nar_historical_daily_replay_target_set,
    normalize_nar_monthly_convene_info,
)
from scripts.simulation.sqlite_nar_daily_target_evidence_archive import (
    SQLiteNARDailyTargetEvidenceArchive,
)
from tests.test_nar_historical_daily_target_bootstrap import _capture as supplier_fixture
from tests.test_nar_historical_daily_target_source import (
    CASES,
    FIXTURES,
    case_captures,
)


_SUPPLIER_ROLES = {
    NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME: "official_home",
    NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT: "monthly_root",
    NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT: "locator_script",
}
_SUPPLIER_TYPES = {
    NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME: "text/html",
    NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT: "text/html; charset=UTF-8",
    NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT: (
        "application/javascript; charset=UTF-8"
    ),
}


class _Clock:
    def __init__(self, start=None):
        self.start = start or datetime(2031, 1, 1, tzinfo=timezone.utc)
        self.calls = 0

    def __call__(self):
        value = self.start + timedelta(microseconds=self.calls)
        self.calls += 1
        return value


class _SupplierTransport:
    def __init__(self, *, changed_bodies=None, failure_kind=None, events=None):
        self.changed_bodies = changed_bodies or {}
        self.failure_kind = failure_kind
        self.calls = []
        self.events = events

    def fetch(self, *, page_kind, canonical_request_url):
        self.calls.append((page_kind, canonical_request_url))
        if self.events is not None:
            self.events.append(("supplier", page_kind))
        if page_kind is self.failure_kind:
            raise RuntimeError(f"supplier failure: {page_kind.value}")
        capture = supplier_fixture(_SUPPLIER_ROLES[page_kind])
        body = self.changed_bodies.get(page_kind, capture.response_body)
        return _NARMonthlyConveneInfoBootstrapHTTPResponse(
            effective_url=canonical_request_url,
            response_body=body,
            content_type=_SUPPLIER_TYPES[page_kind],
            content_encoding=None,
            content_length=len(body),
        )


class _DailyTransport:
    def __init__(
        self,
        target_date,
        *,
        failure_index=None,
        monthly_body=None,
        race_body_changes=None,
        events=None,
    ):
        envelope_capture, envelope, _race_captures = case_captures(target_date)
        monthly_path, race_paths = CASES[target_date]
        self.monthly_body = (
            (FIXTURES / monthly_path).read_bytes()
            if monthly_body is None
            else monthly_body
        )
        self.race_bodies = {
            locator.request_identity.official_supplied_request_material: (
                race_body_changes or {}
            ).get(index, (FIXTURES / path).read_bytes())
            for index, (locator, path) in enumerate(
                zip(envelope.venue_locators, race_paths)
            )
        }
        self.failure_index = failure_index
        self.calls = []
        self.events = events
        self.fixture_envelope_capture = envelope_capture

    def fetch(self, *, request_identity):
        index = len(self.calls)
        self.calls.append(request_identity)
        if self.events is not None:
            self.events.append(("daily", request_identity))
        if index == self.failure_index:
            raise RuntimeError(f"daily failure: {index}")
        if request_identity.page_kind.value == "monthly_convene_info":
            body = self.monthly_body
        else:
            body = self.race_bodies[
                request_identity.official_supplied_request_material
            ]
        return _NARHistoricalDailyTargetHTTPResponse(
            effective_url=request_identity.resolved_request_url,
            response_body=body,
            content_type="text/html; charset=UTF-8",
            content_encoding=None,
            http_date=None,
            etag=None,
            last_modified=None,
            content_length=len(body),
        )


class _RecordingArchive:
    def __init__(self, *, fail_on_save=None):
        self.supplier = []
        self.daily = []
        self.saves = 0
        self.fail_on_save = fail_on_save
        self.loads = 0

    def _before_save(self):
        self.saves += 1
        if self.saves == self.fail_on_save:
            raise RuntimeError("archive failure")

    def save_supplier_capture(self, *, capture):
        self._before_save()
        self.supplier.append(capture)

    def save_capture(self, *, capture):
        self._before_save()
        self.daily.append(capture)

    def load_capture(self, **kwargs):
        self.loads += 1
        raise AssertionError("application must not load cached evidence")

    def load_supplier_capture(self, **kwargs):
        self.loads += 1
        raise AssertionError("application must not load cached evidence")


def _target_set(target_date=date(2025, 1, 1)):
    envelope_capture, _envelope, race_captures = case_captures(target_date)
    return build_nar_historical_daily_replay_target_set(
        target_date=target_date,
        envelope_capture=envelope_capture,
        race_list_captures=race_captures,
    )


class NARDailyTargetLiveAcquisitionTests(unittest.TestCase):
    def _real_application(self, target_date=date(2025, 1, 1), **daily_options):
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        apply_nar_daily_target_evidence_archive_migrations(connection=connection)
        archive = SQLiteNARDailyTargetEvidenceArchive(connection=connection)
        supplier_transport = _SupplierTransport()
        daily_transport = _DailyTransport(target_date, **daily_options)
        clock = _Clock()
        application = NARDailyTargetLiveAcquisitionApplication(
            archive=archive,
            supplier_transport=supplier_transport,
            daily_target_transport=daily_transport,
            utc_clock=clock,
        )
        return application, archive, supplier_transport, daily_transport, clock

    def test_complete_real_composition_archives_all_evidence_and_returns_exact_set(self):
        target_date = date(2025, 1, 1)
        application, archive, supplier, daily, clock = self._real_application(target_date)
        result = application.acquire(target_date=target_date)
        self.assertIs(type(result), NARDailyTargetLiveAcquisitionResult)
        self.assertEqual(result.target_date, target_date)
        self.assertEqual(len(supplier.calls), 3)
        self.assertEqual(len(daily.calls), 4)
        self.assertEqual(
            [value.value for value, _url in supplier.calls],
            ["official_home", "monthly_root", "locator_script"],
        )
        for capture_id in (
            result.homepage_supplier_capture_id,
            result.monthly_root_supplier_capture_id,
            result.locator_script_supplier_capture_id,
        ):
            self.assertIsNotNone(archive.load_supplier_capture(capture_id=capture_id))
        monthly_loaded = archive.load_capture(capture_id=result.monthly_capture_id)
        self.assertIsNotNone(monthly_loaded)
        envelope = normalize_nar_monthly_convene_info(
            target_date=target_date,
            capture=monthly_loaded,
        )
        self.assertEqual(
            tuple(item.request_identity for item in envelope.venue_locators),
            tuple(daily.calls[1:]),
        )
        self.assertEqual(3, len(result.race_list_capture_ids))
        for capture_id in result.race_list_capture_ids:
            self.assertIsNotNone(archive.load_capture(capture_id=capture_id))
        self.assertEqual(33, len(result.target_set.target_races))
        self.assertEqual(21, clock.calls)

    def test_constructor_uses_same_dependencies_without_side_effect_or_hidden_clock(self):
        archive = object()
        supplier_transport = object()
        daily_transport = object()
        clock = Mock(side_effect=AssertionError("constructor called clock"))
        supplier_service = object()
        daily_service = object()
        with patch.object(subject, "_SupplierService", return_value=supplier_service) as supplier_cls, patch.object(
            subject, "_DailyTargetService", return_value=daily_service
        ) as daily_cls:
            application = NARDailyTargetLiveAcquisitionApplication(
                archive=archive,
                supplier_transport=supplier_transport,
                daily_target_transport=daily_transport,
                utc_clock=clock,
            )
        supplier_cls.assert_called_once_with(
            archive=archive, transport=supplier_transport, utc_clock=clock
        )
        daily_cls.assert_called_once_with(
            archive=archive, transport=daily_transport, utc_clock=clock
        )
        self.assertIs(application._supplier_service, supplier_service)
        self.assertIs(application._daily_target_service, daily_service)
        clock.assert_not_called()

    def test_exact_date_is_validated_before_any_capture(self):
        application, _archive, supplier, daily, clock = self._real_application()
        for invalid in (datetime(2025, 1, 1), "2025-01-01", None):
            with self.subTest(invalid=invalid), self.assertRaises(
                NARHistoricalDailyTargetSourceValidationError
            ):
                application.acquire(target_date=invalid)
        self.assertEqual(supplier.calls, [])
        self.assertEqual(daily.calls, [])
        self.assertEqual(clock.calls, 0)

    def test_exact_sequence_reuses_existing_functions_and_all_five_request_objects(self):
        events = []
        home = SimpleNamespace(capture_id="home")
        root = SimpleNamespace(capture_id="root")
        script = SimpleNamespace(capture_id="script")
        root_locator, script_resolution = object(), object()
        evidence = SimpleNamespace(supplier_evidence_identity="evidence")
        monthly_request = object()
        monthly_capture = SimpleNamespace(capture_id="monthly")
        locators = tuple(SimpleNamespace(request_identity=object()) for _ in range(5))
        envelope = SimpleNamespace(venue_locators=locators)
        race_captures = tuple(SimpleNamespace(capture_id=f"race-{index}") for index in range(5))
        target_set = _target_set()

        supplier_service = Mock()
        supplier_service.capture_official_home.side_effect = lambda: events.append("home") or home
        supplier_service.capture_monthly_root.side_effect = (
            lambda **kwargs: events.append(("root-capture", kwargs)) or root
        )
        supplier_service.capture_locator_script.side_effect = (
            lambda **kwargs: events.append(("script-capture", kwargs)) or script
        )
        daily_service = Mock()
        daily_service.capture_supplied_response.side_effect = (
            lambda **kwargs: events.append(("daily-capture", kwargs["request_identity"]))
            or ([monthly_capture] + list(race_captures)).pop(0)
        )
        responses = iter((monthly_capture,) + race_captures)
        daily_service.capture_supplied_response.side_effect = (
            lambda **kwargs: events.append(("daily-capture", kwargs["request_identity"]))
            or next(responses)
        )

        with patch.object(subject, "_SupplierService", return_value=supplier_service), patch.object(
            subject, "_DailyTargetService", return_value=daily_service
        ), patch.object(
            subject, "_resolve_root", side_effect=lambda **kwargs: events.append(("stage-a", kwargs)) or root_locator
        ) as stage_a, patch.object(
            subject, "_resolve_script", side_effect=lambda **kwargs: events.append(("stage-b", kwargs)) or script_resolution
        ) as stage_b, patch.object(
            subject, "_BootstrapEvidence", side_effect=lambda **kwargs: events.append(("evidence", kwargs)) or evidence
        ) as evidence_cls, patch.object(
            subject, "_resolve_monthly_request", side_effect=lambda **kwargs: events.append(("monthly-identity", kwargs)) or monthly_request
        ) as final_resolver, patch.object(
            subject, "_normalize_monthly", side_effect=lambda **kwargs: events.append(("normalize", kwargs)) or envelope
        ) as normalizer, patch.object(
            subject, "_build_target_set", side_effect=lambda **kwargs: events.append(("builder", kwargs)) or target_set
        ) as builder:
            application = NARDailyTargetLiveAcquisitionApplication(
                archive=object(),
                supplier_transport=object(),
                daily_target_transport=object(),
                utc_clock=object(),
            )
            result = application.acquire(target_date=date(2025, 1, 1))

        stage_a.assert_called_once_with(homepage_capture=home)
        stage_b.assert_called_once_with(
            target_date=date(2025, 1, 1),
            root_locator=root_locator,
            monthly_root_capture=root,
        )
        supplier_service.capture_monthly_root.assert_called_once_with(
            homepage_capture=home, root_locator=root_locator
        )
        supplier_service.capture_locator_script.assert_called_once_with(
            monthly_root_capture=root,
            locator_script_resolution=script_resolution,
        )
        evidence_cls.assert_called_once_with(
            homepage_capture=home,
            monthly_root_capture=root,
            locator_script_capture=script,
        )
        final_resolver.assert_called_once_with(
            target_date=date(2025, 1, 1), supplier_evidence=evidence
        )
        normalizer.assert_called_once_with(
            target_date=date(2025, 1, 1), capture=monthly_capture
        )
        self.assertEqual(
            [call.kwargs["request_identity"] for call in daily_service.capture_supplied_response.call_args_list],
            [monthly_request] + [locator.request_identity for locator in locators],
        )
        builder.assert_called_once_with(
            target_date=date(2025, 1, 1),
            envelope_capture=monthly_capture,
            race_list_captures=race_captures,
        )
        self.assertIs(result.target_set, target_set)
        self.assertEqual(result.race_list_capture_ids, tuple(item.capture_id for item in race_captures))
        self.assertEqual(events[-1][0], "builder")

    def test_result_is_frozen_slotted_and_validates_exact_audit_fields(self):
        target_set = _target_set()
        values = dict(
            target_date=date(2025, 1, 1),
            homepage_supplier_capture_id="home",
            monthly_root_supplier_capture_id="root",
            locator_script_supplier_capture_id="script",
            supplier_evidence_identity="evidence",
            monthly_capture_id="monthly",
            race_list_capture_ids=("race-1", "race-2"),
            target_set=target_set,
        )
        result = NARDailyTargetLiveAcquisitionResult(**values)
        self.assertFalse(hasattr(result, "__dict__"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.monthly_capture_id = "changed"
        invalid_cases = (
            {"target_date": datetime(2025, 1, 1)},
            {"homepage_supplier_capture_id": ""},
            {"monthly_root_supplier_capture_id": "home"},
            {"race_list_capture_ids": []},
            {"race_list_capture_ids": ()},
            {"race_list_capture_ids": ("race", "race")},
            {"target_set": object()},
            {"target_date": date(2025, 1, 2)},
        )
        for change in invalid_cases:
            with self.subTest(change=change), self.assertRaises(
                NARHistoricalDailyTargetSourceValidationError
            ):
                NARDailyTargetLiveAcquisitionResult(**(values | change))

    def test_supplier_and_staged_failures_return_no_result_and_keep_only_prior_audit_rows(self):
        for failure_kind, expected_supplier_count in (
            (NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME, 0),
            (NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT, 1),
            (NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT, 2),
        ):
            archive = _RecordingArchive()
            application = NARDailyTargetLiveAcquisitionApplication(
                archive=archive,
                supplier_transport=_SupplierTransport(failure_kind=failure_kind),
                daily_target_transport=_DailyTransport(date(2025, 1, 1)),
                utc_clock=_Clock(),
            )
            with self.subTest(failure_kind=failure_kind), self.assertRaises(RuntimeError):
                application.acquire(target_date=date(2025, 1, 1))
            self.assertEqual(expected_supplier_count, len(archive.supplier))
            self.assertEqual(archive.daily, [])

        home = supplier_fixture("official_home").response_body.replace(
            b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop",
            b"/wrong",
            1,
        )
        archive = _RecordingArchive()
        application = NARDailyTargetLiveAcquisitionApplication(
            archive=archive,
            supplier_transport=_SupplierTransport(
                changed_bodies={NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME: home}
            ),
            daily_target_transport=_DailyTransport(date(2025, 1, 1)),
            utc_clock=_Clock(),
        )
        with self.assertRaises(Exception):
            application.acquire(target_date=date(2025, 1, 1))
        self.assertEqual(1, len(archive.supplier))
        self.assertEqual([], archive.daily)

    def test_pinned_script_failure_is_not_archived_or_converted_to_partial_success(self):
        archive = _RecordingArchive()
        changed = supplier_fixture("locator_script").response_body + b"x"
        application = NARDailyTargetLiveAcquisitionApplication(
            archive=archive,
            supplier_transport=_SupplierTransport(
                changed_bodies={NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT: changed}
            ),
            daily_target_transport=_DailyTransport(date(2025, 1, 1)),
            utc_clock=_Clock(),
        )
        with self.assertRaises(Exception):
            application.acquire(target_date=date(2025, 1, 1))
        self.assertEqual(2, len(archive.supplier))
        self.assertEqual([], archive.daily)

    def test_monthly_and_each_race_failure_return_no_result_with_prior_captures_retained(self):
        for failure_index, expected_daily_count in ((0, 0), (1, 1), (2, 2), (3, 3)):
            archive = _RecordingArchive()
            application = NARDailyTargetLiveAcquisitionApplication(
                archive=archive,
                supplier_transport=_SupplierTransport(),
                daily_target_transport=_DailyTransport(
                    date(2025, 1, 1), failure_index=failure_index
                ),
                utc_clock=_Clock(),
            )
            with self.subTest(failure_index=failure_index), self.assertRaises(RuntimeError):
                application.acquire(target_date=date(2025, 1, 1))
            self.assertEqual(3, len(archive.supplier))
            self.assertEqual(expected_daily_count, len(archive.daily))
            self.assertEqual(0, archive.loads)

    def test_archive_and_normalizer_failures_propagate_without_builder_or_partial_result(self):
        archive = _RecordingArchive(fail_on_save=4)
        application = NARDailyTargetLiveAcquisitionApplication(
            archive=archive,
            supplier_transport=_SupplierTransport(),
            daily_target_transport=_DailyTransport(date(2025, 1, 1)),
            utc_clock=_Clock(),
        )
        with self.assertRaisesRegex(RuntimeError, "archive failure"):
            application.acquire(target_date=date(2025, 1, 1))
        self.assertEqual(3, len(archive.supplier))
        self.assertEqual(0, len(archive.daily))

        archive = _RecordingArchive()
        application = NARDailyTargetLiveAcquisitionApplication(
            archive=archive,
            supplier_transport=_SupplierTransport(),
            daily_target_transport=_DailyTransport(date(2025, 1, 1)),
            utc_clock=_Clock(),
        )
        with patch.object(subject, "_normalize_monthly", side_effect=RuntimeError("normalize")), patch.object(
            subject, "_build_target_set"
        ) as builder:
            with self.assertRaisesRegex(RuntimeError, "normalize"):
                application.acquire(target_date=date(2025, 1, 1))
        builder.assert_not_called()
        self.assertEqual(1, len(archive.daily))

    def test_final_bootstrap_and_each_race_archive_failure_return_no_result(self):
        archive = _RecordingArchive()
        application = NARDailyTargetLiveAcquisitionApplication(
            archive=archive,
            supplier_transport=_SupplierTransport(),
            daily_target_transport=_DailyTransport(date(2025, 1, 1)),
            utc_clock=_Clock(),
        )
        with patch.object(
            subject,
            "_resolve_monthly_request",
            side_effect=RuntimeError("final bootstrap"),
        ), patch.object(subject, "_build_target_set") as builder:
            with self.assertRaisesRegex(RuntimeError, "final bootstrap"):
                application.acquire(target_date=date(2025, 1, 1))
        builder.assert_not_called()
        self.assertEqual(3, len(archive.supplier))
        self.assertEqual(0, len(archive.daily))

        for failed_save, expected_daily_count in ((5, 1), (6, 2), (7, 3)):
            archive = _RecordingArchive(fail_on_save=failed_save)
            application = NARDailyTargetLiveAcquisitionApplication(
                archive=archive,
                supplier_transport=_SupplierTransport(),
                daily_target_transport=_DailyTransport(date(2025, 1, 1)),
                utc_clock=_Clock(),
            )
            with self.subTest(failed_save=failed_save), self.assertRaisesRegex(
                RuntimeError, "archive failure"
            ):
                application.acquire(target_date=date(2025, 1, 1))
            self.assertEqual(3, len(archive.supplier))
            self.assertEqual(expected_daily_count, len(archive.daily))
            self.assertEqual(0, archive.loads)

    def test_builder_failure_occurs_only_after_all_captures_are_archived(self):
        archive = _RecordingArchive()
        application = NARDailyTargetLiveAcquisitionApplication(
            archive=archive,
            supplier_transport=_SupplierTransport(),
            daily_target_transport=_DailyTransport(date(2025, 1, 1)),
            utc_clock=_Clock(),
        )
        with patch.object(subject, "_build_target_set", side_effect=RuntimeError("builder")) as builder:
            with self.assertRaisesRegex(RuntimeError, "builder"):
                application.acquire(target_date=date(2025, 1, 1))
        builder.assert_called_once()
        self.assertEqual(3, len(archive.supplier))
        self.assertEqual(4, len(archive.daily))
        self.assertEqual(0, archive.loads)

    def test_repeated_acquire_is_fresh_and_equal_fixture_clocks_are_deterministic(self):
        application, _archive, supplier, daily, _clock = self._real_application()
        first = application.acquire(target_date=date(2025, 1, 1))
        second = application.acquire(target_date=date(2025, 1, 1))
        self.assertEqual(6, len(supplier.calls))
        self.assertEqual(8, len(daily.calls))
        self.assertNotEqual(first.homepage_supplier_capture_id, second.homepage_supplier_capture_id)
        self.assertNotEqual(first.monthly_capture_id, second.monthly_capture_id)

        one, *_ = self._real_application()
        two, *_ = self._real_application()
        self.assertEqual(
            one.acquire(target_date=date(2025, 1, 1)),
            two.acquire(target_date=date(2025, 1, 1)),
        )

    def test_public_api_and_static_composition_boundary_are_exact(self):
        public = {name for name in vars(subject) if not name.startswith("_")}
        self.assertEqual(
            public,
            {
                "NARDailyTargetLiveAcquisitionApplication",
                "NARDailyTargetLiveAcquisitionResult",
            },
        )
        self.assertEqual(
            tuple(inspect.signature(NARDailyTargetLiveAcquisitionApplication).parameters),
            ("archive", "supplier_transport", "daily_target_transport", "utc_clock"),
        )
        self.assertEqual(
            tuple(inspect.signature(NARDailyTargetLiveAcquisitionApplication.acquire).parameters),
            ("self", "target_date"),
        )
        source = inspect.getsource(subject)
        tree = ast.parse(source)
        imports = set()
        calls = set()
        constants = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                constants.add(node.value)
        self.assertFalse(any(value.startswith(("requests", "httpx", "urllib", "sqlite3")) for value in imports))
        self.assertFalse({"eval", "exec", "compile", "load_capture", "load_supplier_capture"} & calls)
        self.assertFalse(any("https://" in value or "SELECT " in value or "INSERT " in value for value in constants))
        for forbidden in (
            "HTMLParser",
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "migrate",
            "prediction",
            "settlement",
            "manifest",
            "replay runner",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
