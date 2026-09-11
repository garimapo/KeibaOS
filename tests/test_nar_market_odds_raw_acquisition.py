from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone
import inspect
from pathlib import Path
import unittest
from unittest.mock import patch

import requests

from scripts.simulation.nar_market_odds_capture import (
    NARMarketOddsPageKind,
    NARMarketOddsRaceIdentity,
    NARMarketOddsRequestIdentity,
    NARMarketOddsResponseCapture,
    build_nar_market_odds_request_identity,
)
import scripts.simulation.nar_market_odds_raw_acquisition as acquisition
from scripts.simulation.nar_market_odds_raw_acquisition import (
    NARMarketOddsRawAcquisitionTarget,
    NARMarketOddsRawAcquisitionTransportError,
    NARMarketOddsRawAcquisitionUnsupportedError,
    NARMarketOddsRawAcquisitionValidationError,
    NARMarketOddsRawHTTPResponse,
    RequestsNARMarketOddsRawAcquisitionTransport,
    acquire_nar_market_odds_raw_response,
)


_UTC = timezone.utc
_T0 = datetime(2026, 9, 9, 5, 59, 59, 100000, tzinfo=_UTC)
_T1 = _T0 + timedelta(microseconds=1)
_T2 = _T1 + timedelta(microseconds=1)
_BODY = "<html>盛岡\r\nオッズ</html>".encode("utf-8")


def _request(
    page_kind: NARMarketOddsPageKind = NARMarketOddsPageKind.ODDS_WIDE,
) -> NARMarketOddsRequestIdentity:
    return build_nar_market_odds_request_identity(
        page_kind=page_kind,
        baba_code="36",
        race_date=date(2026, 9, 9),
        race_no=9,
    )


def _response(
    request: NARMarketOddsRequestIdentity,
    **changes: object,
) -> NARMarketOddsRawHTTPResponse:
    values: dict[str, object] = {
        "effective_url": request.canonical_request_url,
        "response_body": _BODY,
        "http_status": 200,
        "content_type": "text/html; charset=UTF-8",
        "content_encoding": None,
        "http_date": "Wed, 09 Sep 2026 06:00:00 GMT",
        "etag": '"fixture"',
        "last_modified": None,
        "content_length": len(_BODY),
    }
    values.update(changes)
    return NARMarketOddsRawHTTPResponse(**values)  # type: ignore[arg-type]


class _Clock:
    def __init__(self, values: list[object]) -> None:
        self.values = list(values)
        self.calls = 0

    def now_utc(self) -> object:
        self.calls += 1
        return self.values.pop(0)


class _Transport:
    def __init__(self, response: object = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[NARMarketOddsRequestIdentity, datetime]] = []

    def fetch(
        self,
        *,
        request_identity: NARMarketOddsRequestIdentity,
        requested_at: datetime,
    ) -> object:
        self.calls.append((request_identity, requested_at))
        if self.error is not None:
            raise self.error
        return self.response


def _acquire(
    *,
    request: NARMarketOddsRequestIdentity | None = None,
    response: object = None,
    clock_values: list[object] | None = None,
) -> tuple[NARMarketOddsResponseCapture, _Transport, _Clock]:
    selected = request or _request()
    transport = _Transport(response or _response(selected))
    clock = _Clock(clock_values or [_T0, _T1, _T2])
    capture = acquire_nar_market_odds_raw_response(
        target=NARMarketOddsRawAcquisitionTarget(request_identity=selected),
        transport=transport,
        clock=clock,
    )
    return capture, transport, clock


class NARMarketOddsRawAcquisitionDomainTests(unittest.TestCase):
    def test_all_four_page_kinds_forward_exact_phase32_request_once(self) -> None:
        for kind in NARMarketOddsPageKind:
            with self.subTest(kind=kind):
                request = _request(kind)
                capture, transport, clock = _acquire(request=request)
                self.assertEqual(transport.calls, [(request, _T0)])
                self.assertEqual(clock.calls, 3)
                self.assertEqual(capture.request_identity, request)
                self.assertEqual(capture.effective_url, request.canonical_request_url)

    def test_target_rejects_non_request_and_forged_request(self) -> None:
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError):
            NARMarketOddsRawAcquisitionTarget(request_identity=object())  # type: ignore[arg-type]
        forged = _request()
        object.__setattr__(forged, "canonical_request_url", "https://example.test/")
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError):
            NARMarketOddsRawAcquisitionTarget(request_identity=forged)

    def test_forged_page_kind_is_exact_validation_before_clock_or_transport(self) -> None:
        request = _request()
        target = NARMarketOddsRawAcquisitionTarget(request_identity=request)
        object.__setattr__(target.request_identity, "page_kind", "odds_wide")
        transport = _Transport(_response(_request()))
        clock = _Clock([_T0, _T1, _T2])
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError) as raised:
            acquire_nar_market_odds_raw_response(
                target=target,
                transport=transport,
                clock=clock,
            )
        self.assertIs(type(raised.exception), NARMarketOddsRawAcquisitionValidationError)
        self.assertEqual(transport.calls, [])
        self.assertEqual(clock.calls, 0)

    def test_forged_race_identity_is_exact_validation_before_clock_or_transport(self) -> None:
        request = _request()
        target = NARMarketOddsRawAcquisitionTarget(request_identity=request)
        object.__setattr__(target.request_identity, "race_identity", object())
        transport = _Transport(_response(_request()))
        clock = _Clock([_T0, _T1, _T2])
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError) as raised:
            acquire_nar_market_odds_raw_response(
                target=target,
                transport=transport,
                clock=clock,
            )
        self.assertIs(type(raised.exception), NARMarketOddsRawAcquisitionValidationError)
        self.assertEqual(transport.calls, [])
        self.assertEqual(clock.calls, 0)

    def test_forged_exact_race_identity_fields_are_validation_before_side_effects(self) -> None:
        request = _request()
        target = NARMarketOddsRawAcquisitionTarget(request_identity=request)
        malformed_race = object.__new__(NARMarketOddsRaceIdentity)
        object.__setattr__(target.request_identity, "race_identity", malformed_race)
        transport = _Transport(_response(_request()))
        clock = _Clock([_T0, _T1, _T2])
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError) as raised:
            acquire_nar_market_odds_raw_response(
                target=target,
                transport=transport,
                clock=clock,
            )
        self.assertIs(type(raised.exception), NARMarketOddsRawAcquisitionValidationError)
        self.assertEqual(transport.calls, [])
        self.assertEqual(clock.calls, 0)

    def test_forged_request_missing_canonical_url_is_validation_before_side_effects(self) -> None:
        request = _request()
        target = NARMarketOddsRawAcquisitionTarget(request_identity=request)
        object.__delattr__(target.request_identity, "canonical_request_url")
        transport = _Transport(_response(_request()))
        clock = _Clock([_T0, _T1, _T2])
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError) as raised:
            acquire_nar_market_odds_raw_response(
                target=target,
                transport=transport,
                clock=clock,
            )
        self.assertIs(type(raised.exception), NARMarketOddsRawAcquisitionValidationError)
        self.assertEqual(transport.calls, [])
        self.assertEqual(clock.calls, 0)

    def test_forged_request_missing_digest_is_validation_before_side_effects(self) -> None:
        request = _request()
        target = NARMarketOddsRawAcquisitionTarget(request_identity=request)
        object.__delattr__(target.request_identity, "request_identity_sha256")
        transport = _Transport(_response(_request()))
        clock = _Clock([_T0, _T1, _T2])
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError) as raised:
            acquire_nar_market_odds_raw_response(
                target=target,
                transport=transport,
                clock=clock,
            )
        self.assertIs(type(raised.exception), NARMarketOddsRawAcquisitionValidationError)
        self.assertEqual(transport.calls, [])
        self.assertEqual(clock.calls, 0)

    def test_forged_request_wrong_type_canonical_url_is_validation_before_side_effects(self) -> None:
        class _Text(str):
            pass

        request = _request()
        target = NARMarketOddsRawAcquisitionTarget(request_identity=request)
        object.__setattr__(
            target.request_identity,
            "canonical_request_url",
            _Text(target.request_identity.canonical_request_url),
        )
        transport = _Transport(_response(_request()))
        clock = _Clock([_T0, _T1, _T2])
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError) as raised:
            acquire_nar_market_odds_raw_response(
                target=target,
                transport=transport,
                clock=clock,
            )
        self.assertIs(type(raised.exception), NARMarketOddsRawAcquisitionValidationError)
        self.assertEqual(transport.calls, [])
        self.assertEqual(clock.calls, 0)

    def test_public_target_has_no_url_or_implicit_race_fields(self) -> None:
        self.assertEqual(
            tuple(NARMarketOddsRawAcquisitionTarget.__dataclass_fields__),
            ("request_identity",),
        )
        signature = inspect.signature(acquire_nar_market_odds_raw_response)
        self.assertEqual(tuple(signature.parameters), ("target", "transport", "clock"))

    def test_exact_raw_japanese_crlf_bytes_are_preserved(self) -> None:
        capture, _, _ = _acquire()
        self.assertIs(type(capture.response_body), bytes)
        self.assertEqual(capture.response_body, _BODY)
        self.assertIn(b"\r\n", capture.response_body)

    def test_lf_and_one_byte_variants_remain_distinct(self) -> None:
        request = _request()
        first, _, _ = _acquire(response=_response(request, response_body=b"A\r\nB", content_length=4))
        second, _, _ = _acquire(response=_response(request, response_body=b"A\nB", content_length=3))
        third, _, _ = _acquire(response=_response(request, response_body=b"A\nC", content_length=3))
        self.assertNotEqual(first.response_sha256, second.response_sha256)
        self.assertNotEqual(second.response_sha256, third.response_sha256)

    def test_exact_timestamps_are_supplied_to_phase32(self) -> None:
        jst = timezone(timedelta(hours=9))
        values = [value.astimezone(jst) for value in (_T0, _T1, _T2)]
        capture, _, clock = _acquire(clock_values=values)
        self.assertEqual((capture.requested_at, capture.observed_at, capture.captured_at), (_T0, _T1, _T2))
        self.assertEqual(clock.calls, 3)

    def test_invalid_clock_samples_and_order_fail_closed(self) -> None:
        cases = (
            ["not-time", _T1, _T2],
            [_T0.replace(tzinfo=None), _T1, _T2],
            [_T1, _T0, _T2],
        )
        for values in cases:
            with self.subTest(values=values):
                with self.assertRaises(NARMarketOddsRawAcquisitionValidationError):
                    _acquire(clock_values=list(values))

    def test_transport_exception_is_mapped_without_retry(self) -> None:
        request = _request()
        transport = _Transport(error=TimeoutError("timeout"))
        clock = _Clock([_T0])
        with self.assertRaises(NARMarketOddsRawAcquisitionTransportError):
            acquire_nar_market_odds_raw_response(
                target=NARMarketOddsRawAcquisitionTarget(request_identity=request),
                transport=transport,
                clock=clock,
            )
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(clock.calls, 1)

    def test_invalid_transport_value_is_validation_error(self) -> None:
        request = _request()
        transport = _Transport(object())
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError):
            acquire_nar_market_odds_raw_response(
                target=NARMarketOddsRawAcquisitionTarget(request_identity=request),
                transport=transport,
                clock=_Clock([_T0, _T1, _T2]),
            )

    def test_non_200_and_wrong_urls_fail_without_retry(self) -> None:
        request = _request()
        cases = (
            _response(request, http_status=500),
            _response(request, effective_url="https://example.test/"),
            _response(request, effective_url="https://www.keiba.go.jp/other"),
        )
        for response in cases:
            with self.subTest(response=response):
                transport = _Transport(response)
                with self.assertRaises(NARMarketOddsRawAcquisitionTransportError):
                    acquire_nar_market_odds_raw_response(
                        target=NARMarketOddsRawAcquisitionTarget(request_identity=request),
                        transport=transport,
                        clock=_Clock([_T0, _T1, _T2]),
                    )
                self.assertEqual(len(transport.calls), 1)

    def test_incompatible_profile_and_bytes_fail_closed(self) -> None:
        request = _request()
        cases = (
            _response(request, content_type="text/html; charset=Shift_JIS"),
            _response(request, content_encoding="gzip"),
            _response(request, response_body=b"\xff", content_length=1),
        )
        for response in cases:
            with self.subTest(response=response):
                with self.assertRaises(NARMarketOddsRawAcquisitionUnsupportedError):
                    _acquire(response=response)

    def test_content_length_and_body_validation_are_not_bypassed(self) -> None:
        request = _request()
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError):
            _acquire(response=_response(request, content_length=len(_BODY) + 1))
        with self.assertRaises(NARMarketOddsRawAcquisitionValidationError):
            _acquire(response=_response(request, response_body=b"", content_length=0))

    def test_approved_metadata_maps_exactly_and_absence_stays_none(self) -> None:
        capture, _, _ = _acquire()
        self.assertEqual(capture.content_type, "text/html; charset=UTF-8")
        self.assertIsNone(capture.content_encoding)
        self.assertEqual(capture.http_date, "Wed, 09 Sep 2026 06:00:00 GMT")
        self.assertEqual(capture.etag, '"fixture"')
        self.assertIsNone(capture.last_modified)
        self.assertEqual(capture.content_length, len(_BODY))

        request = _request()
        empty = _response(
            request,
            http_date=None,
            etag=None,
            last_modified=None,
            content_length=None,
        )
        capture, _, _ = _acquire(response=empty)
        self.assertIsNone(capture.http_date)
        self.assertIsNone(capture.etag)
        self.assertIsNone(capture.last_modified)
        self.assertIsNone(capture.content_length)

    def test_transport_response_has_only_frozen_metadata_fields(self) -> None:
        self.assertEqual(
            tuple(NARMarketOddsRawHTTPResponse.__dataclass_fields__),
            (
                "effective_url", "response_body", "http_status", "content_type",
                "content_encoding", "http_date", "etag", "last_modified", "content_length",
            ),
        )


class _Raw:
    def __init__(self, chunks: list[bytes], error: Exception | None = None) -> None:
        self.chunks = chunks
        self.error = error
        self.decode_content: bool | None = None
        self.calls: list[tuple[int, bool]] = []

    def stream(self, *, amt: int, decode_content: bool):
        self.calls.append((amt, decode_content))
        if self.error is not None:
            raise self.error
        yield from self.chunks


class _HTTPResponse:
    def __init__(
        self,
        request: NARMarketOddsRequestIdentity,
        *,
        body: bytes = _BODY,
        status: int = 200,
        url: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status
        self.url = request.canonical_request_url if url is None else url
        self.headers = {
            "Content-Type": "text/html; charset=UTF-8",
            "Date": "Wed, 09 Sep 2026 06:00:00 GMT",
            "Content-Length": str(len(body)),
            "Set-Cookie": "must-not-be-retained=secret",
            "X-CSRF-Token": "must-not-be-retained",
        }
        if headers:
            self.headers.update(headers)
        self.raw = _Raw([body])
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _Session:
    def __init__(self, response: _HTTPResponse | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.mounts: list[tuple[str, object]] = []
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.closed = False
        self.trust_env = True
        self.headers = {"Default": "must-be-cleared"}

    def mount(self, prefix: str, adapter: object) -> None:
        self.mounts.append((prefix, adapter))

    def get(self, url: str, **options: object) -> _HTTPResponse:
        self.calls.append((url, options))
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response

    def close(self) -> None:
        self.closed = True


class RequestsTransportTests(unittest.TestCase):
    def test_concrete_transport_makes_one_exact_raw_get_and_whitelists_headers(self) -> None:
        request = _request()
        http_response = _HTTPResponse(request)
        session = _Session(http_response)
        with patch.object(acquisition._requests, "Session", return_value=session):
            response = RequestsNARMarketOddsRawAcquisitionTransport().fetch(
                request_identity=request,
                requested_at=_T0,
            )
        self.assertEqual(len(session.calls), 1)
        url, options = session.calls[0]
        self.assertEqual(url, request.canonical_request_url)
        self.assertEqual(
            options,
            {
                "headers": {
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Encoding": "identity",
                },
                "stream": True,
                "allow_redirects": False,
                "verify": True,
                "timeout": (10.0, 20.0),
            },
        )
        self.assertEqual(len(session.mounts), 1)
        self.assertEqual(session.mounts[0][0], "https://")
        self.assertEqual(session.mounts[0][1].max_retries.total, 0)
        self.assertFalse(session.trust_env)
        self.assertEqual(session.headers, {})
        self.assertEqual(http_response.raw.calls, [(64 * 1024, False)])
        self.assertFalse(http_response.raw.decode_content)
        self.assertEqual(response.response_body, _BODY)
        self.assertFalse(hasattr(response, "set_cookie"))
        self.assertFalse(hasattr(response, "csrf_token"))
        self.assertTrue(http_response.closed)
        self.assertTrue(session.closed)

    def test_each_fetch_uses_a_fresh_session(self) -> None:
        request = _request()
        sessions = [_Session(_HTTPResponse(request)), _Session(_HTTPResponse(request))]
        with patch.object(acquisition._requests, "Session", side_effect=sessions) as factory:
            transport = RequestsNARMarketOddsRawAcquisitionTransport()
            transport.fetch(request_identity=request, requested_at=_T0)
            transport.fetch(request_identity=request, requested_at=_T0)
        self.assertEqual(factory.call_count, 2)
        self.assertTrue(all(session.closed for session in sessions))

    def test_concrete_transport_rejects_response_boundaries_without_second_get(self) -> None:
        request = _request()
        cases = (
            (_HTTPResponse(request, status=500), NARMarketOddsRawAcquisitionTransportError),
            (_HTTPResponse(request, url="https://example.test/"), NARMarketOddsRawAcquisitionTransportError),
            (_HTTPResponse(request, headers={"Content-Type": "text/plain"}), NARMarketOddsRawAcquisitionUnsupportedError),
            (_HTTPResponse(request, headers={"Content-Encoding": "gzip"}), NARMarketOddsRawAcquisitionUnsupportedError),
            (_HTTPResponse(request, headers={"Content-Length": "01"}), NARMarketOddsRawAcquisitionTransportError),
        )
        for response, error_type in cases:
            with self.subTest(error_type=error_type):
                session = _Session(response)
                with patch.object(acquisition._requests, "Session", return_value=session):
                    with self.assertRaises(error_type):
                        RequestsNARMarketOddsRawAcquisitionTransport().fetch(
                            request_identity=request,
                            requested_at=_T0,
                        )
                self.assertEqual(len(session.calls), 1)
                self.assertTrue(session.closed)

    def test_requests_timeout_maps_to_transport_error_without_retry(self) -> None:
        request = _request()
        session = _Session(error=requests.Timeout("timeout"))
        with patch.object(acquisition._requests, "Session", return_value=session):
            with self.assertRaises(NARMarketOddsRawAcquisitionTransportError):
                RequestsNARMarketOddsRawAcquisitionTransport().fetch(
                    request_identity=request,
                    requested_at=_T0,
                )
        self.assertEqual(len(session.calls), 1)
        self.assertTrue(session.closed)

    def test_raw_stream_failure_maps_to_transport_error_without_retry(self) -> None:
        request = _request()
        response = _HTTPResponse(request)
        response.raw = _Raw([], error=RuntimeError("broken raw stream"))
        session = _Session(response)
        with patch.object(acquisition._requests, "Session", return_value=session):
            with self.assertRaises(NARMarketOddsRawAcquisitionTransportError):
                RequestsNARMarketOddsRawAcquisitionTransport().fetch(
                    request_identity=request,
                    requested_at=_T0,
                )
        self.assertEqual(len(session.calls), 1)
        self.assertTrue(response.closed)
        self.assertTrue(session.closed)

    def test_oversize_and_length_mismatch_fail_closed(self) -> None:
        request = _request()
        responses = (
            _HTTPResponse(request, headers={"Content-Length": str(4 * 1024 * 1024 + 1)}),
            _HTTPResponse(request, body=b"short", headers={"Content-Length": "6"}),
        )
        for response in responses:
            session = _Session(response)
            with patch.object(acquisition._requests, "Session", return_value=session):
                with self.assertRaises(NARMarketOddsRawAcquisitionTransportError):
                    RequestsNARMarketOddsRawAcquisitionTransport().fetch(
                        request_identity=request,
                        requested_at=_T0,
                    )


class StaticBoundaryTests(unittest.TestCase):
    def test_public_exports_are_exact(self) -> None:
        self.assertEqual(
            set(acquisition.__all__),
            {
                "NARMarketOddsRawAcquisitionClock",
                "NARMarketOddsRawAcquisitionError",
                "NARMarketOddsRawAcquisitionTarget",
                "NARMarketOddsRawAcquisitionTransport",
                "NARMarketOddsRawAcquisitionTransportError",
                "NARMarketOddsRawAcquisitionUnsupportedError",
                "NARMarketOddsRawAcquisitionValidationError",
                "NARMarketOddsRawHTTPResponse",
                "RequestsNARMarketOddsRawAcquisitionTransport",
                "acquire_nar_market_odds_raw_response",
            },
        )

    def test_production_has_no_forbidden_dependencies_or_semantics(self) -> None:
        path = Path(acquisition.__file__)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        forbidden_import_fragments = (
            "bs4", "beautifulsoup", "lxml", "decimal", "ranking_probability",
            "value_engine", "bet_generator", "strategy", "settlement", "payout",
            "sqlite", "repository", "jra", "fixture",
        )
        self.assertFalse(
            any(fragment in module.lower() for fragment in forbidden_import_fragments for module in imports)
        )
        forbidden_calls = ("datetime.now", "datetime.utcnow", "time.time", "sleep(")
        self.assertFalse(any(value in source for value in forbidden_calls))
        forbidden_state_terms = ("NOT_AVAILABLE", "SUSPENDED", "CANCELLED")
        self.assertFalse(any(value in source for value in forbidden_state_terms))


if __name__ == "__main__":
    unittest.main()
