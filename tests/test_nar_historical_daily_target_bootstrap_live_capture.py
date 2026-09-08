import ast
import inspect
from datetime import date, datetime, timedelta, timezone
import unittest
from unittest.mock import patch

import scripts.simulation.nar_historical_daily_target_bootstrap_live_capture as live_module
from scripts.simulation.nar_historical_daily_target_bootstrap import (
    NARMonthlyConveneInfoBootstrapUnsupportedError,
    resolve_nar_monthly_convene_info_locator_script,
    resolve_nar_monthly_convene_info_root_locator,
)
from scripts.simulation.nar_historical_daily_target_bootstrap_capture import (
    NARMonthlyConveneInfoBootstrapCaptureUnsupportedError,
    NARMonthlyConveneInfoBootstrapCaptureValidationError,
    NARMonthlyConveneInfoBootstrapPageKind,
)
from scripts.simulation.nar_historical_daily_target_bootstrap_live_capture import (
    NARMonthlyConveneInfoBootstrapLiveCaptureService,
    NARMonthlyConveneInfoBootstrapTransportError,
    RequestsNARMonthlyConveneInfoBootstrapHTTPTransport,
    _NARMonthlyConveneInfoBootstrapHTTPResponse,
)
from tests.test_nar_historical_daily_target_bootstrap import _capture


_URLS = {
    NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME: "https://www.keiba.go.jp/",
    NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT: (
        "https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"
    ),
    NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT: (
        "https://www.keiba.go.jp/KeibaWeb/resources/js/"
        "monthltconveninfo.js?t=20260130_1"
    ),
}
_CONTENT_TYPES = {
    NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME: "text/html",
    NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT: "text/html; charset=UTF-8",
    NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT: (
        "application/javascript; charset=UTF-8"
    ),
}
_ROLES = {
    NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME: "official_home",
    NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT: "monthly_root",
    NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT: "locator_script",
}


class _Response:
    def __init__(self, *, kind, body=None, status=200, url=None, headers=None, chunks=None):
        original = _capture(_ROLES[kind]).response_body
        self.status_code = status
        self.url = _URLS[kind] if url is None else url
        self.headers = {
            "Content-Type": _CONTENT_TYPES[kind],
            "Content-Length": str(len(original if body is None else body)),
        }
        if headers:
            self.headers.update(headers)
        self._chunks = [original if body is None else body] if chunks is None else chunks
        self.closed = False

    def iter_content(self, *, chunk_size):
        self.chunk_size = chunk_size
        yield from self._chunks

    def close(self):
        self.closed = True


class _Session:
    def __init__(self, response):
        self.response = response
        self.headers = {}
        self.mounts = []
        self.calls = []

    def mount(self, prefix, adapter):
        self.mounts.append((prefix, adapter))

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class _Archive:
    def __init__(self, error=None):
        self.saved = []
        self.error = error
        self.load_calls = 0

    def save_supplier_capture(self, *, capture):
        if self.error is not None:
            raise self.error
        self.saved.append(capture)

    def load_supplier_capture(self, **kwargs):
        self.load_calls += 1
        raise AssertionError("live capture must not load a cached capture")


class _Transport:
    def __init__(self, bodies=None):
        self.bodies = bodies or {
            kind: _capture(role).response_body for kind, role in _ROLES.items()
        }
        self.calls = []

    def fetch(self, *, page_kind, canonical_request_url):
        self.calls.append((page_kind, canonical_request_url))
        body = self.bodies[page_kind]
        return _NARMonthlyConveneInfoBootstrapHTTPResponse(
            effective_url=canonical_request_url,
            response_body=body,
            content_type=_CONTENT_TYPES[page_kind],
            content_encoding=None,
            content_length=len(body),
        )


class _Clock:
    def __init__(self):
        start = datetime(2026, 9, 8, 1, 2, 3, 100, tzinfo=timezone.utc)
        self.values = [start + timedelta(microseconds=index) for index in range(30)]
        self.index = 0

    def __call__(self):
        value = self.values[self.index]
        self.index += 1
        return value


def _requests_transport(response):
    session = _Session(response)
    with patch.object(live_module._requests, "Session", return_value=session):
        transport = RequestsNARMonthlyConveneInfoBootstrapHTTPTransport()
    return transport, session


class NARMonthlyConveneInfoBootstrapLiveCaptureTests(unittest.TestCase):
    def test_requests_transport_uses_exact_get_safety_and_closes_response(self):
        kind = NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME
        response = _Response(kind=kind)
        transport, session = _requests_transport(response)
        result = transport.fetch(page_kind=kind, canonical_request_url=_URLS[kind])
        self.assertEqual(result.response_body, _capture("official_home").response_body)
        self.assertTrue(response.closed)
        self.assertEqual(session.headers, {"User-Agent": "Mozilla/5.0"})
        self.assertEqual({prefix for prefix, _adapter in session.mounts}, {"http://", "https://"})
        self.assertTrue(all(adapter.max_retries.total == 0 for _prefix, adapter in session.mounts))
        self.assertEqual(
            session.calls,
            [
                (
                    _URLS[kind],
                    {
                        "headers": {"Accept-Encoding": "identity"},
                        "stream": True,
                        "allow_redirects": False,
                        "verify": True,
                        "timeout": (10.0, 10.0),
                    },
                )
            ],
        )

    def test_requests_transport_accepts_only_exact_kind_url_and_content_type_pairs(self):
        for kind in NARMonthlyConveneInfoBootstrapPageKind:
            with self.subTest(kind=kind):
                response = _Response(kind=kind)
                transport, _session = _requests_transport(response)
                result = transport.fetch(page_kind=kind, canonical_request_url=_URLS[kind])
                self.assertEqual(result.content_type, _CONTENT_TYPES[kind])
        response = _Response(kind=NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME)
        transport, session = _requests_transport(response)
        for kind, url in (
            (object(), _URLS[NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME]),
            (NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME, "http://www.keiba.go.jp/"),
            (NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME, "https://evil.example/"),
        ):
            with self.subTest(kind=kind, url=url), self.assertRaises(
                NARMonthlyConveneInfoBootstrapCaptureValidationError
            ):
                transport.fetch(page_kind=kind, canonical_request_url=url)
        self.assertEqual(session.calls, [])

    def test_transport_rejects_status_redirect_effective_url_and_always_closes(self):
        kind = NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME
        cases = (
            _Response(kind=kind, status=500),
            _Response(kind=kind, status=302),
            _Response(kind=kind, url="https://www.keiba.go.jp/other"),
        )
        for response in cases:
            transport, _session = _requests_transport(response)
            with self.subTest(status=response.status_code, url=response.url), self.assertRaises(
                NARMonthlyConveneInfoBootstrapTransportError
            ):
                transport.fetch(page_kind=kind, canonical_request_url=_URLS[kind])
            self.assertTrue(response.closed)

    def test_transport_rejects_wrong_content_metadata_and_length(self):
        kind = NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT
        cases = (
            (_Response(kind=kind, headers={"Content-Type": "text/html"}), NARMonthlyConveneInfoBootstrapCaptureUnsupportedError),
            (_Response(kind=kind, headers={"Content-Encoding": "gzip"}), NARMonthlyConveneInfoBootstrapCaptureUnsupportedError),
            (_Response(kind=kind, headers={"Content-Length": "x"}), NARMonthlyConveneInfoBootstrapTransportError),
            (_Response(kind=kind, headers={"Content-Length": "1"}), NARMonthlyConveneInfoBootstrapTransportError),
        )
        for response, error in cases:
            transport, _session = _requests_transport(response)
            with self.subTest(headers=response.headers), self.assertRaises(error):
                transport.fetch(page_kind=kind, canonical_request_url=_URLS[kind])
            self.assertTrue(response.closed)

    def test_transport_enforces_byte_stream_and_four_mibibyte_bound(self):
        kind = NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME
        oversized = _Response(
            kind=kind,
            chunks=[b"x" * (4 * 1024 * 1024), b"x"],
            headers={"Content-Length": str(4 * 1024 * 1024 + 1)},
        )
        del oversized.headers["Content-Length"]
        cases = (
            _Response(kind=kind, chunks=["not bytes"], headers={"Content-Length": "9"}),
            oversized,
            _Response(kind=kind, body=b"", chunks=[b""], headers={"Content-Length": "0"}),
        )
        for response in cases:
            transport, _session = _requests_transport(response)
            with self.subTest(), self.assertRaises(NARMonthlyConveneInfoBootstrapTransportError):
                transport.fetch(page_kind=kind, canonical_request_url=_URLS[kind])
            self.assertTrue(response.closed)

    def test_service_captures_and_archives_the_exact_three_stage_chain(self):
        archive = _Archive()
        transport = _Transport()
        service = NARMonthlyConveneInfoBootstrapLiveCaptureService(
            archive=archive, transport=transport, utc_clock=_Clock()
        )
        homepage = service.capture_official_home()
        root_locator = resolve_nar_monthly_convene_info_root_locator(
            homepage_capture=homepage
        )
        root = service.capture_monthly_root(
            homepage_capture=homepage, root_locator=root_locator
        )
        script_resolution = resolve_nar_monthly_convene_info_locator_script(
            target_date=date(2025, 12, 26),
            root_locator=root_locator,
            monthly_root_capture=root,
        )
        script = service.capture_locator_script(
            monthly_root_capture=root,
            locator_script_resolution=script_resolution,
        )
        self.assertEqual(archive.saved, [homepage, root, script])
        self.assertEqual(archive.load_calls, 0)
        self.assertEqual(
            transport.calls,
            [(kind, _URLS[kind]) for kind in NARMonthlyConveneInfoBootstrapPageKind],
        )
        for capture in archive.saved:
            self.assertLessEqual(capture.requested_at, capture.observed_at)
            self.assertLessEqual(capture.observed_at, capture.stored_at)

    def test_service_rejects_cross_capture_stage_before_network(self):
        archive = _Archive()
        transport = _Transport()
        service = NARMonthlyConveneInfoBootstrapLiveCaptureService(
            archive=archive, transport=transport, utc_clock=_Clock()
        )
        homepage = _capture("official_home")
        root_locator = resolve_nar_monthly_convene_info_root_locator(
            homepage_capture=homepage
        )
        other_homepage = _capture(
            "official_home",
            body=homepage.response_body.replace(b"<title>", b"<!-- x --><title>", 1),
        )
        with self.assertRaises(NARMonthlyConveneInfoBootstrapCaptureValidationError):
            service.capture_monthly_root(
                homepage_capture=other_homepage, root_locator=root_locator
            )
        self.assertEqual(transport.calls, [])
        self.assertEqual(archive.saved, [])

    def test_service_rejects_forged_script_resolution_before_network(self):
        archive = _Archive()
        transport = _Transport()
        service = NARMonthlyConveneInfoBootstrapLiveCaptureService(
            archive=archive, transport=transport, utc_clock=_Clock()
        )
        homepage = _capture("official_home")
        root = _capture("monthly_root")
        root_locator = resolve_nar_monthly_convene_info_root_locator(
            homepage_capture=homepage
        )
        resolution = resolve_nar_monthly_convene_info_locator_script(
            target_date=date(2025, 1, 1),
            root_locator=root_locator,
            monthly_root_capture=root,
        )
        object.__setattr__(resolution, "monthly_root_capture_id", "nar-monthly-bootstrap-capture-v1:" + "0" * 64)
        with self.assertRaises(NARMonthlyConveneInfoBootstrapCaptureValidationError):
            service.capture_locator_script(
                monthly_root_capture=root,
                locator_script_resolution=resolution,
            )
        self.assertEqual(transport.calls, [])
        self.assertEqual(archive.saved, [])

    def test_pinned_script_is_validated_before_archive_publication(self):
        archive = _Archive()
        bodies = {kind: _capture(role).response_body for kind, role in _ROLES.items()}
        bodies[NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT] += b"x"
        transport = _Transport(bodies)
        service = NARMonthlyConveneInfoBootstrapLiveCaptureService(
            archive=archive, transport=transport, utc_clock=_Clock()
        )
        homepage = _capture("official_home")
        root = _capture("monthly_root")
        locator = resolve_nar_monthly_convene_info_root_locator(homepage_capture=homepage)
        resolution = resolve_nar_monthly_convene_info_locator_script(
            target_date=date(2025, 1, 1),
            root_locator=locator,
            monthly_root_capture=root,
        )
        with self.assertRaises(NARMonthlyConveneInfoBootstrapUnsupportedError):
            service.capture_locator_script(
                monthly_root_capture=root,
                locator_script_resolution=resolution,
            )
        self.assertEqual(archive.saved, [])

    def test_archive_failure_propagates_and_live_invocations_never_load_cache(self):
        failure = RuntimeError("archive failed")
        archive = _Archive(error=failure)
        transport = _Transport()
        service = NARMonthlyConveneInfoBootstrapLiveCaptureService(
            archive=archive, transport=transport, utc_clock=_Clock()
        )
        with self.assertRaisesRegex(RuntimeError, "archive failed"):
            service.capture_official_home()
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(archive.load_calls, 0)

        archive = _Archive()
        transport = _Transport()
        service = NARMonthlyConveneInfoBootstrapLiveCaptureService(
            archive=archive, transport=transport, utc_clock=_Clock()
        )
        first = service.capture_official_home()
        second = service.capture_official_home()
        self.assertEqual(len(transport.calls), 2)
        self.assertNotEqual(first.capture_id, second.capture_id)
        self.assertEqual(archive.load_calls, 0)

    def test_clock_requires_exact_timezone_aware_datetime(self):
        for value in (None, "2026-01-01", datetime(2026, 1, 1)):
            service = NARMonthlyConveneInfoBootstrapLiveCaptureService(
                archive=_Archive(), transport=_Transport(), utc_clock=lambda: value
            )
            with self.subTest(value=value), self.assertRaises(
                NARMonthlyConveneInfoBootstrapCaptureValidationError
            ):
                service.capture_official_home()

    def test_invalid_utf8_and_out_of_order_clock_fail_before_archive(self):
        kind = NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME
        archive = _Archive()
        transport = _Transport({kind: b"\xff"})
        service = NARMonthlyConveneInfoBootstrapLiveCaptureService(
            archive=archive, transport=transport, utc_clock=_Clock()
        )
        with self.assertRaises(NARMonthlyConveneInfoBootstrapCaptureUnsupportedError):
            service.capture_official_home()
        self.assertEqual(archive.saved, [])

        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        samples = iter((start, start - timedelta(seconds=1), start))
        archive = _Archive()
        service = NARMonthlyConveneInfoBootstrapLiveCaptureService(
            archive=archive,
            transport=_Transport(),
            utc_clock=lambda: next(samples),
        )
        with self.assertRaises(NARMonthlyConveneInfoBootstrapCaptureValidationError):
            service.capture_official_home()
        self.assertEqual(archive.saved, [])

    def test_supplier_module_has_no_forbidden_runtime_or_storage_boundaries(self):
        source = inspect.getsource(live_module)
        tree = ast.parse(source)
        imports = set()
        calls = set()
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
        self.assertFalse(any(value.startswith(("selenium", "playwright", "sqlite3")) for value in imports))
        self.assertFalse({"eval", "exec", "load_supplier_capture"} & calls)
        for forbidden in (
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "allow_redirects=True",
            "migrate",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
