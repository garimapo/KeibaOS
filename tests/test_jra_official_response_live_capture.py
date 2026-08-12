from __future__ import annotations

from datetime import datetime, timedelta, timezone
import ast
import inspect
from pathlib import Path
import unittest

import scripts.simulation.jra_official_response_live_capture as module
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialPageKind,
    JRAOfficialResponseCaptureUnsupportedError,
    JRAOfficialResponseCaptureValidationError,
)
from scripts.simulation.jra_official_response_live_capture import (
    JRAOfficialLiveResponseCaptureService,
    JRAOfficialResponseCaptureTransportError,
    build_jra_official_live_response_capture_service,
)


_S = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC"
_U = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud002020102902%2F22"
_BODY = "<meta charset=\"Shift_JIS\">テスト".encode("cp932")
_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _Archive:
    def __init__(self, *, error: BaseException | None = None) -> None:
        self.error = error
        self.values = []

    def save_capture(self, *, capture) -> None:
        if self.error is not None:
            raise self.error
        self.values.append(capture)


class _Transport:
    def __init__(self, result: object = None, *, error: BaseException | None = None) -> None:
        self.result = result
        self.error = error
        self.urls: list[str] = []

    def fetch(self, *, canonical_source_url: str):
        self.urls.append(canonical_source_url)
        if self.error is not None:
            raise self.error
        return self.result


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


def _result(*, url: str = _S, body: bytes = _BODY, content_length: int | None = None, content_encoding: str | None = None):
    return module._JRAOfficialHTTPResponse(
        canonical_source_url=url,
        response_body=body,
        content_type="text/html",
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
                "build_jra_official_live_response_capture_service",
            },
        )
        self.assertEqual(tuple(inspect.signature(JRAOfficialLiveResponseCaptureService.capture_response).parameters), ("self", "page_kind", "response_url"))
        source = Path(module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("response.text", source)
        self.assertNotIn(".decode(", source)
        self.assertNotIn(".encode(", source)
        tree = ast.parse(source)
        self.assertFalse(any(isinstance(node, ast.ImportFrom) and node.module == "scripts.simulation.nar_official_response_live_capture" for node in ast.walk(tree)))

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
        for kind, url in ((JRAOfficialPageKind.RACE_RESULT, _U), (JRAOfficialPageKind.HORSE_PROFILE_HISTORY, _S), (JRAOfficialPageKind.RACE_RESULT, "https://bad.example/")):
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
