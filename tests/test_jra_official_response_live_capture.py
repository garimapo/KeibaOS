from __future__ import annotations

from datetime import datetime, timedelta, timezone
import ast
import inspect
from pathlib import Path
import unittest
from unittest import mock

import scripts.simulation.jra_official_response_live_capture as module
from scripts.simulation.jra_official_response_capture import (
    JRAFinalWinOddsSuppliedOfficialResponse,
    JRAOfficialPageKind,
    JRAOfficialResponseCaptureUnsupportedError,
    JRAOfficialResponseCaptureValidationError,
    JRAOfficialTargetRaceCardResponseCapture,
    JRATargetRaceSelectionResponseCapture,
)
from scripts.simulation.jra_official_identity import (
    JRAExternalRaceIdentity,
    JRAOfficialFinalWinOddsRequestLocator,
    JRAOfficialIdentityValidationError,
)
from scripts.simulation.jra_official_response_live_capture import (
    JRAOfficialLiveResponseCaptureService,
    JRAOfficialResponseCaptureTransportError,
    JRATargetRaceNavigationCaptureResult,
    build_jra_official_live_response_capture_service,
)


_S = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC"
_U = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud002020102902%2F22"
_D = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0106202504030420250913%2FDC"
_O = "https://www.jra.go.jp/JRADB/accessO.html"
_CNAME = "pw151ou1006202601021220260105Z/2E"
_BODY = "<meta charset=\"Shift_JIS\">テスト".encode("cp932")
_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
_ROOT = "https://www.jra.go.jp/"
_TARGET_RACE_ID = "jra:race:2025:06:04:03:04"
_MEETING_CNAME = "pw01dli00/AA"
_RACE_CNAME = "pw01drl00062025040320250913/AB"
_ROOT_BODY = ('<div id="quick_menu"><a href="#" data-ga-click="quick_pc-1" onclick="doAction(\'/JRADB/accessD.html\',\'pw01dli00/AA\');return false;">x</a></div>').encode("cp932")
_MEETING_BODY = ('<div id="contentsBody"><div class="link_list multi div3 center"><div class="waku"><a href="#" onclick="return doAction(\'/JRADB/accessD.html\', \'pw01drl00062025040320250913/AB\');">x</a></div></div></div>').encode("cp932")
_RACE_BODY = (f'<div id="contentsBody"><div class="race_select"><table id="race_list" class="basic mt20"><tbody><tr><th class="race_num"><a href="{_D}">4</a></th><td class="syutsuba"><a class="btn-def btn-sm btn-narrow" href="{_D}">x</a></td></tr></tbody></table></div></div>').encode("cp932")


def _locator() -> JRAOfficialFinalWinOddsRequestLocator:
    identity = JRAExternalRaceIdentity("2026", "06", "01", "02", "12")
    return JRAOfficialFinalWinOddsRequestLocator(
        endpoint_url=_O,
        cname=_CNAME,
        external_race_identity=identity,
        request_identity_sha256="9c4a4f2dfc7e2c21841f7a2bb3f36ec7397312a34b565ff7e511e74800774ade",
    )


class _Archive:
    def __init__(self, *, error: BaseException | None = None) -> None:
        self.error = error
        self.values = []
        self.legacy_calls = 0
        self.final_calls = 0
        self.target_calls = 0
        self.selection_calls = 0

    def save_capture(self, *, capture) -> None:
        self.legacy_calls += 1
        if self.error is not None:
            raise self.error
        self.values.append(capture)

    def save_final_win_odds_capture(self, *, capture) -> None:
        self.final_calls += 1
        if self.error is not None:
            raise self.error
        self.values.append(capture)

    def save_target_race_card_capture(self, *, capture) -> None:
        self.target_calls += 1
        if self.error is not None:
            raise self.error
        self.values.append(capture)

    def save_target_race_selection_capture(self, *, capture) -> None:
        self.selection_calls += 1
        if self.error is not None:
            raise self.error
        self.values.append(capture)


class _Transport:
    def __init__(self, result: object = None, *, error: BaseException | None = None) -> None:
        self.result = result
        self.error = error
        self.urls: list[str] = []
        self.locators: list[object] = []

    def fetch(self, *, canonical_source_url: str):
        self.urls.append(canonical_source_url)
        if self.error is not None:
            raise self.error
        return self.result

    def fetch_final_win_odds(self, *, request_locator):
        self.locators.append(request_locator)
        if self.error is not None:
            raise self.error
        return self.result


class _NavigationTransport:
    def __init__(self, *, root: object, meeting: object, race: object, error: BaseException | None = None) -> None:
        self.root, self.meeting, self.race, self.error = root, meeting, race, error
        self.calls: list[tuple[str, object | None]] = []

    def _result(self, name: str, value: object):
        self.calls.append((name, None))
        if self.error is not None:
            raise self.error
        return value

    def fetch_target_navigation_root(self):
        return self._result("root", self.root)

    def fetch_target_meeting_selection(self, *, request_locator):
        self.calls.append(("meeting", request_locator))
        if self.error is not None:
            raise self.error
        return self.meeting

    def fetch_target_race_selection(self, *, request_locator):
        self.calls.append(("race", request_locator))
        if self.error is not None:
            raise self.error
        return self.race


class _Clock:
    def __init__(self, *values: object) -> None:
        self.values = list(values)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.values.pop(0)


class _Raw:
    def __init__(self, chunks: tuple[object, ...]) -> None:
        self.chunks = chunks
        self.decode_content = None
        self.calls = []

    def stream(self, *, amt: int, decode_content: bool):
        self.calls.append((amt, decode_content))
        for item in self.chunks:
            if isinstance(item, BaseException):
                raise item
            yield item


class _Response:
    def __init__(self, *, status: int = 200, url: str = _S, headers: dict[str, object] | None = None, chunks: tuple[object, ...] = (_BODY,)) -> None:
        self.status_code = status
        self.url = url
        self.headers = {"Content-Type": "text/html", **(headers or {})}
        self.raw = _Raw(chunks)
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _Session:
    def __init__(self, outcome: object) -> None:
        self.outcome = outcome
        self.headers = {}
        self.mounts = []
        self.calls = []

    def mount(self, prefix: str, adapter: object) -> None:
        self.mounts.append((prefix, adapter))

    def get(self, url: str, **kwargs):
        self.calls.append((url, kwargs))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome

    def send(self, request, **kwargs):
        self.calls.append((request, kwargs))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


def _result(
    *,
    url: str = _S,
    body: bytes = _BODY,
    content_type: str = "text/html",
    content_length: int | None = None,
    content_encoding: str | None = None,
):
    return module._JRAOfficialHTTPResponse(
        canonical_source_url=url,
        response_body=body,
        content_type=content_type,
        content_encoding=content_encoding,
        http_date=None,
        etag=None,
        last_modified=None,
        content_length=content_length,
    )


def _service(*, transport: _Transport, archive: _Archive, clock: _Clock) -> JRAOfficialLiveResponseCaptureService:
    return JRAOfficialLiveResponseCaptureService(archive=archive, transport=transport, utc_clock=clock)


class JRAOfficialLiveResponseCaptureTests(unittest.TestCase):
    def test_exact_public_surface_signature_and_raw_byte_boundary(self):
        self.assertEqual(
            {name for name in vars(module) if not name.startswith("_")},
            {
                "JRAOfficialLiveResponseCaptureService",
                "JRAOfficialResponseCaptureTransportError",
                "JRATargetRaceNavigationCaptureResult",
                "build_jra_official_live_response_capture_service",
            },
        )
        self.assertEqual(tuple(inspect.signature(JRAOfficialLiveResponseCaptureService.capture_response).parameters), ("self", "page_kind", "response_url"))
        self.assertEqual(
            tuple(inspect.signature(JRAOfficialLiveResponseCaptureService.capture_target_race_card_response).parameters),
            ("self", "response_url"),
        )
        self.assertEqual(tuple(inspect.signature(JRAOfficialLiveResponseCaptureService.capture_final_win_odds_response).parameters), ("self", "request_locator"))
        self.assertEqual(
            tuple(inspect.signature(JRAOfficialLiveResponseCaptureService.capture_target_race_navigation).parameters),
            ("self", "external_race_id"),
        )
        self.assertTrue(getattr(JRATargetRaceNavigationCaptureResult, "__dataclass_params__").frozen)
        self.assertEqual(JRATargetRaceNavigationCaptureResult.__slots__, ("discovery", "target_race_selection_capture_id"))
        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("response.text", source)
        self.assertNotIn(".decode(", source)
        self.assertNotIn(".encode(", source)
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(node, ast.ImportFrom) and node.module == "scripts.simulation.nar_official_response_live_capture" for node in ast.walk(tree)))

    def test_final_win_odds_service_archives_the_exact_v2_capture_before_return(self):
        archive = _Archive()
        transport = _Transport(_result(url=_O))
        clock = _Clock(_TIME, _TIME + timedelta(microseconds=1), _TIME + timedelta(microseconds=2))
        locator = _locator()
        value = _service(transport=transport, archive=archive, clock=clock).capture_final_win_odds_response(
            request_locator=locator
        )
        self.assertIsInstance(value, JRAFinalWinOddsSuppliedOfficialResponse)
        self.assertIs(value.request_locator, locator)
        self.assertEqual(value.response_body, _BODY)
        self.assertEqual(transport.locators, [locator])
        self.assertEqual(archive.legacy_calls, 0)
        self.assertEqual(archive.final_calls, 1)
        self.assertEqual(len(archive.values), 1)
        capture = archive.values[0]
        self.assertEqual(capture.schema_version, 2)
        self.assertEqual(capture.page_kind, JRAOfficialPageKind.FINAL_WIN_ODDS)
        self.assertEqual(capture.request_method, "POST")
        self.assertEqual((capture.requested_at, capture.observed_at, capture.stored_at), (
            _TIME,
            _TIME + timedelta(microseconds=1),
            _TIME + timedelta(microseconds=2),
        ))

    def test_target_race_card_service_archives_the_exact_v3_capture_before_return(self):
        archive = _Archive()
        transport = _Transport(_result(url=_D))
        clock = _Clock(_TIME, _TIME + timedelta(microseconds=1), _TIME + timedelta(microseconds=2))
        value = _service(transport=transport, archive=archive, clock=clock).capture_target_race_card_response(
            response_url=_D
        )
        self.assertIsInstance(value, JRAOfficialTargetRaceCardResponseCapture)
        self.assertEqual(transport.urls, [_D])
        self.assertEqual(transport.locators, [])
        self.assertEqual(clock.calls, 3)
        self.assertEqual(archive.legacy_calls, 0)
        self.assertEqual(archive.final_calls, 0)
        self.assertEqual(archive.target_calls, 1)
        self.assertEqual(archive.values, [value])
        self.assertEqual(value.canonical_source_url, _D)
        self.assertEqual(value.response_body, _BODY)
        self.assertEqual(value.schema_version, 3)
        self.assertEqual(value.page_kind, JRAOfficialPageKind.TARGET_RACE_CARD)
        self.assertEqual(value.request_method, "GET")
        self.assertEqual((value.requested_at, value.observed_at, value.stored_at), (
            _TIME,
            _TIME + timedelta(microseconds=1),
            _TIME + timedelta(microseconds=2),
        ))

    def test_target_race_card_input_rejection_happens_before_clock_transport_or_archive(self):
        archive = _Archive()
        transport = _Transport(_result(url=_D))
        clock = _Clock(_TIME, _TIME, _TIME)
        service = _service(transport=transport, archive=archive, clock=clock)
        for value in (object(), _D.replace("%2F", "/"), _S, _U, _O, "https://bad.example/"):
            with self.subTest(value=value), self.assertRaises(JRAOfficialResponseCaptureValidationError):
                service.capture_target_race_card_response(response_url=value)
        self.assertEqual(clock.calls, 0)
        self.assertEqual(transport.urls, [])
        self.assertEqual(archive.legacy_calls, 0)
        self.assertEqual(archive.final_calls, 0)
        self.assertEqual(archive.target_calls, 0)
        self.assertEqual(archive.values, [])

    def test_target_race_card_transport_clock_domain_and_archive_failures_never_return(self):
        archive = _Archive()
        for result in (object(), _result(url=_S)):
            with self.subTest(result=result), self.assertRaises(JRAOfficialResponseCaptureTransportError):
                _service(
                    transport=_Transport(result),
                    archive=archive,
                    clock=_Clock(_TIME, _TIME, _TIME),
                ).capture_target_race_card_response(response_url=_D)
        self.assertEqual(archive.target_calls, 0)
        self.assertEqual(archive.values, [])

        requested_clock = _Clock(datetime(2026, 1, 1))
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            _service(
                transport=_Transport(_result(url=_D)),
                archive=archive,
                clock=requested_clock,
            ).capture_target_race_card_response(response_url=_D)
        self.assertEqual(requested_clock.calls, 1)
        self.assertEqual(archive.target_calls, 0)

        for clock in (
            _Clock(_TIME, datetime(2026, 1, 1)),
            _Clock(_TIME, _TIME, datetime(2026, 1, 1)),
            _Clock(_TIME + timedelta(microseconds=1), _TIME, _TIME),
        ):
            with self.subTest(clock=clock.values), self.assertRaises(JRAOfficialResponseCaptureValidationError):
                _service(
                    transport=_Transport(_result(url=_D)),
                    archive=archive,
                    clock=clock,
                ).capture_target_race_card_response(response_url=_D)
        self.assertEqual(archive.target_calls, 0)

        for result, error in (
            (_result(url=_D, body=b"", content_length=0), JRAOfficialResponseCaptureValidationError),
            (_result(url=_D, body=b"\x81", content_length=1), JRAOfficialResponseCaptureUnsupportedError),
            (_result(url=_D, content_type="application/json"), JRAOfficialResponseCaptureUnsupportedError),
            (_result(url=_D, content_encoding="gzip"), JRAOfficialResponseCaptureUnsupportedError),
            (_result(url=_D, content_length=len(_BODY) + 1), JRAOfficialResponseCaptureValidationError),
        ):
            with self.subTest(result=result, error=error), self.assertRaises(error):
                _service(
                    transport=_Transport(result),
                    archive=archive,
                    clock=_Clock(_TIME, _TIME, _TIME),
                ).capture_target_race_card_response(response_url=_D)
        self.assertEqual(archive.target_calls, 0)
        self.assertEqual(archive.values, [])

        error = RuntimeError("archive unavailable")
        failing_archive = _Archive(error=error)
        with self.assertRaises(RuntimeError) as raised:
            _service(
                transport=_Transport(_result(url=_D)),
                archive=failing_archive,
                clock=_Clock(_TIME, _TIME, _TIME),
            ).capture_target_race_card_response(response_url=_D)
        self.assertIs(raised.exception, error)
        self.assertEqual(failing_archive.legacy_calls, 0)
        self.assertEqual(failing_archive.final_calls, 0)
        self.assertEqual(failing_archive.target_calls, 1)
        self.assertEqual(failing_archive.values, [])

    def test_final_win_odds_validation_clock_domain_and_archive_failures_never_return(self):
        archive = _Archive()
        transport = _Transport(_result(url=_O))
        service = _service(transport=transport, archive=archive, clock=_Clock(_TIME, _TIME, _TIME))
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            service.capture_final_win_odds_response(request_locator=object())
        self.assertEqual(transport.locators, [])
        self.assertEqual(archive.values, [])

        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            _service(transport=transport, archive=archive, clock=_Clock(datetime(2026, 1, 1))).capture_final_win_odds_response(
                request_locator=_locator()
            )
        self.assertEqual(transport.locators, [])

        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            _service(
                transport=_Transport(_result(url=_O)),
                archive=archive,
                clock=_Clock(_TIME, datetime(2026, 1, 1)),
            ).capture_final_win_odds_response(request_locator=_locator())
        self.assertEqual(archive.values, [])

        for result in (object(), _result(url=_S)):
            with self.subTest(result=result), self.assertRaises(JRAOfficialResponseCaptureTransportError):
                _service(
                    transport=_Transport(result),
                    archive=archive,
                    clock=_Clock(_TIME, _TIME, _TIME),
                ).capture_final_win_odds_response(request_locator=_locator())
        self.assertEqual(archive.values, [])

        for body, error in ((b"", JRAOfficialResponseCaptureValidationError), (b"\x81", JRAOfficialResponseCaptureUnsupportedError)):
            with self.subTest(body=body), self.assertRaises(error):
                _service(
                    transport=_Transport(_result(url=_O, body=body, content_length=len(body))),
                    archive=archive,
                    clock=_Clock(_TIME, _TIME, _TIME),
                ).capture_final_win_odds_response(request_locator=_locator())
        self.assertEqual(archive.values, [])

        error = RuntimeError("archive unavailable")
        with self.assertRaises(RuntimeError) as raised:
            _service(
                transport=_Transport(_result(url=_O)),
                archive=_Archive(error=error),
                clock=_Clock(_TIME, _TIME, _TIME),
            ).capture_final_win_odds_response(request_locator=_locator())
        self.assertIs(raised.exception, error)

    def test_access_s_and_u_canonicalize_before_network_and_persist_before_return(self):
        archive = _Archive()
        clock = _Clock(_TIME, _TIME + timedelta(microseconds=1), _TIME + timedelta(microseconds=2))
        transport = _Transport(_result())
        value = _service(transport=transport, archive=archive, clock=clock).capture_response(
            page_kind=JRAOfficialPageKind.RACE_RESULT,
            response_url=_S.replace("%2F", "/"),
        )
        self.assertEqual(transport.urls, [_S])
        self.assertEqual(value.response_body, _BODY)
        self.assertEqual(archive.values, [value])
        self.assertEqual(value.to_supplied_official_response().response_body, _BODY)
        self.assertEqual((value.requested_at, value.observed_at, value.stored_at), (_TIME, _TIME + timedelta(microseconds=1), _TIME + timedelta(microseconds=2)))

        archive_u = _Archive()
        transport_u = _Transport(_result(url=_U))
        clock_u = _Clock(_TIME, _TIME + timedelta(microseconds=1), _TIME + timedelta(microseconds=2))
        value_u = _service(transport=transport_u, archive=archive_u, clock=clock_u).capture_response(
            page_kind=JRAOfficialPageKind.HORSE_PROFILE_HISTORY,
            response_url=_U,
        )
        self.assertEqual(value_u.page_kind, JRAOfficialPageKind.HORSE_PROFILE_HISTORY)
        self.assertEqual(transport_u.urls, [_U])

    def test_page_kind_or_url_rejection_happens_before_clock_transport_or_archive(self):
        archive = _Archive()
        transport = _Transport(_result())
        clock = _Clock(_TIME, _TIME, _TIME)
        service = _service(transport=transport, archive=archive, clock=clock)
        for kind, url in (
            (JRAOfficialPageKind.RACE_RESULT, _U),
            (JRAOfficialPageKind.HORSE_PROFILE_HISTORY, _S),
            (JRAOfficialPageKind.FINAL_WIN_ODDS, _O),
            (JRAOfficialPageKind.TARGET_RACE_CARD, _D),
            (JRAOfficialPageKind.RACE_RESULT, "https://bad.example/"),
        ):
            with self.subTest(kind=kind, url=url), self.assertRaises(JRAOfficialResponseCaptureValidationError):
                service.capture_response(page_kind=kind, response_url=url)
        self.assertEqual(clock.calls, 0)
        self.assertEqual(transport.urls, [])
        self.assertEqual(archive.values, [])

    def test_invalid_clock_or_transport_result_never_archives(self):
        archive = _Archive()
        transport = _Transport(_result())
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            _service(transport=transport, archive=archive, clock=_Clock(datetime(2026, 1, 1))).capture_response(page_kind=JRAOfficialPageKind.RACE_RESULT, response_url=_S)
        self.assertEqual(transport.urls, [])
        self.assertEqual(archive.values, [])

        transport = _Transport(object())
        with self.assertRaises(JRAOfficialResponseCaptureTransportError):
            _service(transport=transport, archive=archive, clock=_Clock(_TIME, _TIME, _TIME)).capture_response(page_kind=JRAOfficialPageKind.RACE_RESULT, response_url=_S)
        self.assertEqual(archive.values, [])

        bad_url = _Transport(_result(url=_U))
        with self.assertRaises(JRAOfficialResponseCaptureTransportError):
            _service(transport=bad_url, archive=archive, clock=_Clock(_TIME, _TIME, _TIME)).capture_response(page_kind=JRAOfficialPageKind.RACE_RESULT, response_url=_S)
        self.assertEqual(archive.values, [])

    def test_post_fetch_clock_c1_errors_and_archive_failure_propagate_without_return(self):
        archive = _Archive()
        transport = _Transport(_result())
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            _service(transport=transport, archive=archive, clock=_Clock(_TIME, datetime(2026, 1, 1))).capture_response(page_kind=JRAOfficialPageKind.RACE_RESULT, response_url=_S)
        self.assertEqual(archive.values, [])

        reversal = _service(transport=_Transport(_result()), archive=archive, clock=_Clock(_TIME + timedelta(seconds=1), _TIME, _TIME))
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            reversal.capture_response(page_kind=JRAOfficialPageKind.RACE_RESULT, response_url=_S)
        error = RuntimeError("archive unavailable")
        with self.assertRaises(RuntimeError) as raised:
            _service(transport=_Transport(_result()), archive=_Archive(error=error), clock=_Clock(_TIME, _TIME, _TIME)).capture_response(page_kind=JRAOfficialPageKind.RACE_RESULT, response_url=_S)
        self.assertIs(raised.exception, error)

    def test_requests_configuration_raw_stream_and_closed_non_successful_responses(self):
        outcomes = []
        for status in (301, 302, 404, 429, 500):
            response = _Response(status=status)
            session = _Session(response)
            transport = object.__new__(module._RequestsJRAOfficialHTTPTransport)
            transport._session = session
            with self.subTest(status=status), self.assertRaises(JRAOfficialResponseCaptureTransportError):
                transport.fetch(canonical_source_url=_S)
            self.assertTrue(response.closed)
            outcomes.append(session)
        for session in outcomes:
            url, kwargs = session.calls[0]
            self.assertEqual(url, _S)
            self.assertEqual(kwargs, {"headers": {"Accept-Encoding": "identity"}, "stream": True, "allow_redirects": False, "verify": True, "timeout": (10.0, 10.0)})

        response = _Response(headers={"Content-Length": str(len(_BODY)), "Content-Encoding": " Identity "})
        session = _Session(response)
        transport = object.__new__(module._RequestsJRAOfficialHTTPTransport)
        transport._session = session
        result = transport.fetch(canonical_source_url=_S)
        self.assertEqual(result.response_body, _BODY)
        self.assertEqual(result.content_encoding, "identity")
        self.assertTrue(response.closed)
        self.assertFalse(response.raw.decode_content)
        self.assertEqual(response.raw.calls, [(64 * 1024, False)])

    def test_final_win_odds_post_wire_is_exact_cookie_free_and_raw(self):
        response = _Response(
            url=_O,
            headers={"Content-Length": str(len(_BODY)), "Content-Encoding": "identity"},
        )
        session = _Session(response)
        session.headers.update({"Cookie": "stale=1", "Referer": "https://example.invalid/", "Origin": "https://example.invalid"})
        transport = object.__new__(module._RequestsJRAOfficialHTTPTransport)
        transport._session = session
        result = transport.fetch_final_win_odds(request_locator=_locator())
        request, kwargs = session.calls[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url, _O)
        self.assertEqual(request.body, "cname=pw151ou1006202601021220260105Z%2F2E")
        self.assertEqual(request.headers["Content-Type"], "application/x-www-form-urlencoded")
        self.assertEqual(request.headers["Accept-Encoding"], "identity")
        self.assertNotIn("Cookie", request.headers)
        self.assertNotIn("Referer", request.headers)
        self.assertNotIn("Origin", request.headers)
        self.assertEqual(kwargs, {"stream": True, "allow_redirects": False, "verify": True, "timeout": (10.0, 10.0)})
        self.assertEqual(result.canonical_source_url, _O)
        self.assertEqual(result.response_body, _BODY)
        self.assertTrue(response.closed)
        self.assertFalse(response.raw.decode_content)
        self.assertEqual(response.raw.calls, [(64 * 1024, False)])

    def test_final_win_odds_post_transport_failures_close_and_fail_closed(self):
        for status, url, headers, chunks, error in (
            (301, _O, {}, (_BODY,), JRAOfficialResponseCaptureTransportError),
            (200, _S, {}, (_BODY,), JRAOfficialResponseCaptureTransportError),
            (200, _O, {"Content-Encoding": "gzip"}, (_BODY,), JRAOfficialResponseCaptureUnsupportedError),
            (200, _O, {"Content-Length": "01"}, (_BODY,), JRAOfficialResponseCaptureTransportError),
            (200, _O, {"Content-Length": "2"}, (b"a",), JRAOfficialResponseCaptureTransportError),
            (200, _O, {}, (b"a" * (4 * 1024 * 1024 + 1),), JRAOfficialResponseCaptureTransportError),
            (200, _O, {}, (object(),), JRAOfficialResponseCaptureTransportError),
        ):
            response = _Response(status=status, url=url, headers=headers, chunks=chunks)
            transport = object.__new__(module._RequestsJRAOfficialHTTPTransport)
            transport._session = _Session(response)
            with self.subTest(status=status, url=url, headers=headers, error=error), self.assertRaises(error):
                transport.fetch_final_win_odds(request_locator=_locator())
            self.assertTrue(response.closed)
        response = _Response(url=_O, headers={"Content-Length": str(4 * 1024 * 1024)}, chunks=(b"a" * (4 * 1024 * 1024),))
        transport = object.__new__(module._RequestsJRAOfficialHTTPTransport)
        transport._session = _Session(response)
        self.assertEqual(len(transport.fetch_final_win_odds(request_locator=_locator()).response_body), 4 * 1024 * 1024)
        transport = object.__new__(module._RequestsJRAOfficialHTTPTransport)
        transport._session = _Session(module._requests.Timeout("timeout"))
        with self.assertRaises(JRAOfficialResponseCaptureTransportError):
            transport.fetch_final_win_odds(request_locator=_locator())

    def test_transport_encoding_length_size_and_stream_failures_fail_closed(self):
        for encoding in ("gzip", "br", "deflate"):
            response = _Response(headers={"Content-Encoding": encoding})
            transport = object.__new__(module._RequestsJRAOfficialHTTPTransport); transport._session = _Session(response)
            with self.subTest(encoding=encoding), self.assertRaises(JRAOfficialResponseCaptureUnsupportedError):
                transport.fetch(canonical_source_url=_S)
            self.assertTrue(response.closed)
        for length in ("01", "+1", "-1", "1.0", " 1", "1 ", "١", "4194305"):
            response = _Response(headers={"Content-Length": length})
            transport = object.__new__(module._RequestsJRAOfficialHTTPTransport); transport._session = _Session(response)
            with self.subTest(length=length), self.assertRaises(JRAOfficialResponseCaptureTransportError):
                transport.fetch(canonical_source_url=_S)
            self.assertTrue(response.closed)
        for chunks, headers in (((b"a",), {"Content-Length": "2"}), ((b"ab",), {"Content-Length": "1"}), ((b"a" * (4 * 1024 * 1024 + 1),), {}), ((module._requests.Timeout("timeout"),), {}), ((OSError("protocol"),), {})):
            response = _Response(headers=headers, chunks=chunks)
            transport = object.__new__(module._RequestsJRAOfficialHTTPTransport); transport._session = _Session(response)
            with self.assertRaises(JRAOfficialResponseCaptureTransportError):
                transport.fetch(canonical_source_url=_S)
            self.assertTrue(response.closed)
        response = _Response(headers={"Content-Length": str(4 * 1024 * 1024)}, chunks=(b"a" * (4 * 1024 * 1024),))
        transport = object.__new__(module._RequestsJRAOfficialHTTPTransport); transport._session = _Session(response)
        self.assertEqual(len(transport.fetch(canonical_source_url=_S).response_body), 4 * 1024 * 1024)

    def test_c1_rejects_empty_or_invalid_cp932_without_archive(self):
        for body, error in ((b"", JRAOfficialResponseCaptureValidationError), (b"\x81", JRAOfficialResponseCaptureUnsupportedError)):
            archive = _Archive()
            with self.subTest(body=body), self.assertRaises(error):
                _service(transport=_Transport(_result(body=body, content_length=len(body))), archive=archive, clock=_Clock(_TIME, _TIME, _TIME)).capture_response(page_kind=JRAOfficialPageKind.RACE_RESULT, response_url=_S)
            self.assertEqual(archive.values, [])

    def test_factory_uses_private_requests_transport_and_utc_clock_without_public_exports(self):
        service = build_jra_official_live_response_capture_service(archive=_Archive())
        self.assertIsInstance(service, JRAOfficialLiveResponseCaptureService)
        self.assertIsInstance(service._transport, module._RequestsJRAOfficialHTTPTransport)
        self.assertEqual(service._transport._session.get_adapter("https://").max_retries.total, 0)
        value = service._utc_clock()
        self.assertIs(type(value), datetime)
        self.assertIsNotNone(value.tzinfo)

    def test_target_navigation_composes_response_derived_chain_and_archives_v4_before_return(self):
        archive = _Archive()
        transport = _NavigationTransport(
            root=_result(url=_ROOT, body=_ROOT_BODY, content_length=len(_ROOT_BODY)),
            meeting=_result(url=_D.split("?")[0], body=_MEETING_BODY, content_length=len(_MEETING_BODY)),
            race=_result(url=_D.split("?")[0], body=_RACE_BODY, content_length=len(_RACE_BODY)),
        )
        clock = _Clock(
            _TIME,
            _TIME + timedelta(microseconds=1),
            _TIME + timedelta(microseconds=2),
            _TIME + timedelta(microseconds=3),
            _TIME + timedelta(microseconds=4),
        )
        discovery = module._discover_jra_target_race_card_locator

        def after_save(**kwargs):
            self.assertEqual(archive.selection_calls, 1)
            return discovery(**kwargs)

        with mock.patch.object(module, "_discover_jra_target_race_card_locator", side_effect=after_save):
            result = JRAOfficialLiveResponseCaptureService(
                archive=archive, transport=transport, utc_clock=clock
            ).capture_target_race_navigation(external_race_id=_TARGET_RACE_ID)
        self.assertIs(type(result), JRATargetRaceNavigationCaptureResult)
        self.assertEqual([name for name, _ in transport.calls], ["root", "meeting", "race"])
        self.assertEqual(transport.calls[1][1].cname, _MEETING_CNAME)
        self.assertEqual(transport.calls[2][1].cname, _RACE_CNAME)
        self.assertEqual(archive.selection_calls, 1)
        self.assertEqual(archive.legacy_calls, 0)
        self.assertEqual(archive.final_calls, 0)
        self.assertEqual(archive.target_calls, 0)
        capture = archive.values[0]
        self.assertIs(type(capture), JRATargetRaceSelectionResponseCapture)
        self.assertEqual(result.target_race_selection_capture_id, capture.capture_id)
        self.assertEqual(result.discovery.locator.canonical_target_race_card_url, _D)
        self.assertEqual(clock.calls, 5)

    def test_target_navigation_invalid_id_has_zero_collaborator_calls(self):
        archive = _Archive()
        transport = _NavigationTransport(root=object(), meeting=object(), race=object())
        clock = _Clock(_TIME)
        service = JRAOfficialLiveResponseCaptureService(archive=archive, transport=transport, utc_clock=clock)
        for value in (object(), "jra:race:2025:06:04:03:04 ", "not-a-race"):
            with self.subTest(value=value), self.assertRaises(JRAOfficialIdentityValidationError):
                service.capture_target_race_navigation(external_race_id=value)
        self.assertEqual(clock.calls, 0)
        self.assertEqual(transport.calls, [])
        self.assertEqual(archive.values, [])

    def test_target_navigation_archive_failure_prevents_discovery_and_success(self):
        archive_error = RuntimeError("archive unavailable")
        archive = _Archive(error=archive_error)
        transport = _NavigationTransport(
            root=_result(url=_ROOT, body=_ROOT_BODY, content_length=len(_ROOT_BODY)),
            meeting=_result(url=_D.split("?")[0], body=_MEETING_BODY, content_length=len(_MEETING_BODY)),
            race=_result(url=_D.split("?")[0], body=_RACE_BODY, content_length=len(_RACE_BODY)),
        )
        with mock.patch.object(module, "_discover_jra_target_race_card_locator") as discovery:
            with self.assertRaises(RuntimeError) as raised:
                JRAOfficialLiveResponseCaptureService(
                    archive=archive,
                    transport=transport,
                    utc_clock=_Clock(_TIME, _TIME, _TIME, _TIME, _TIME),
                ).capture_target_race_navigation(external_race_id=_TARGET_RACE_ID)
        discovery.assert_not_called()
        self.assertIs(raised.exception, archive_error)
        self.assertEqual(archive.selection_calls, 1)
        self.assertEqual(archive.values, [])

    def test_target_navigation_post_save_discovery_failure_keeps_saved_capture_without_result(self):
        archive = _Archive()
        transport = _NavigationTransport(
            root=_result(url=_ROOT, body=_ROOT_BODY, content_length=len(_ROOT_BODY)),
            meeting=_result(url=_D.split("?")[0], body=_MEETING_BODY, content_length=len(_MEETING_BODY)),
            race=_result(url=_D.split("?")[0], body=_RACE_BODY, content_length=len(_RACE_BODY)),
        )
        error = RuntimeError("target unavailable")
        with mock.patch.object(module, "_discover_jra_target_race_card_locator", side_effect=error):
            with self.assertRaises(RuntimeError) as raised:
                JRAOfficialLiveResponseCaptureService(
                    archive=archive,
                    transport=transport,
                    utc_clock=_Clock(_TIME, _TIME, _TIME, _TIME, _TIME),
                ).capture_target_race_navigation(external_race_id=_TARGET_RACE_ID)
        self.assertIs(raised.exception, error)
        self.assertEqual(archive.selection_calls, 1)
        self.assertEqual(len(archive.values), 1)

    def test_navigation_private_transport_is_cookie_referer_origin_free_for_all_requests(self):
        class _SequenceSession:
            def __init__(self, responses):
                self.responses = list(responses)
                self.headers = {"Cookie": "seed=1", "Referer": "https://bad.invalid/", "Origin": "https://bad.invalid"}
                self.calls = []

            def send(self, request, **kwargs):
                self.calls.append((request, kwargs))
                return self.responses.pop(0)

        root = _Response(url=_ROOT, headers={"Set-Cookie": "root=1", "Content-Length": str(len(_ROOT_BODY))}, chunks=(_ROOT_BODY,))
        meeting = _Response(url=_D.split("?")[0], headers={"Set-Cookie": "meeting=1", "Content-Length": str(len(_MEETING_BODY))}, chunks=(_MEETING_BODY,))
        race = _Response(url=_D.split("?")[0], headers={"Content-Length": str(len(_RACE_BODY))}, chunks=(_RACE_BODY,))
        session = _SequenceSession((root, meeting, race))
        transport = object.__new__(module._RequestsJRAOfficialHTTPTransport)
        transport._session = session
        root_value = transport.fetch_target_navigation_root()
        self.assertEqual(root_value.response_body, _ROOT_BODY)
        from scripts.simulation.jra_target_race_card_locator import (
            build_jra_target_meeting_selection_request_locator,
            build_jra_target_race_selection_request_locator,
        )
        transport.fetch_target_meeting_selection(request_locator=build_jra_target_meeting_selection_request_locator(cname=_MEETING_CNAME))
        transport.fetch_target_race_selection(request_locator=build_jra_target_race_selection_request_locator(cname=_RACE_CNAME))
        self.assertEqual([call[0].method for call in session.calls], ["GET", "POST", "POST"])
        for request, kwargs in session.calls:
            self.assertNotIn("Cookie", request.headers)
            self.assertNotIn("Referer", request.headers)
            self.assertNotIn("Origin", request.headers)
            self.assertEqual(kwargs, {"stream": True, "allow_redirects": False, "verify": True, "timeout": (10.0, 10.0)})

    def test_target_navigation_result_rejects_unrelated_capture(self):
        archive = _Archive()
        transport = _NavigationTransport(
            root=_result(url=_ROOT, body=_ROOT_BODY, content_length=len(_ROOT_BODY)),
            meeting=_result(url=_D.split("?")[0], body=_MEETING_BODY, content_length=len(_MEETING_BODY)),
            race=_result(url=_D.split("?")[0], body=_RACE_BODY, content_length=len(_RACE_BODY)),
        )
        result = JRAOfficialLiveResponseCaptureService(
            archive=archive,
            transport=transport,
            utc_clock=_Clock(_TIME, _TIME, _TIME, _TIME, _TIME),
        ).capture_target_race_navigation(external_race_id=_TARGET_RACE_ID)
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            JRATargetRaceNavigationCaptureResult(discovery=result.discovery, capture=object())
