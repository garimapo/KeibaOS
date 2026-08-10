from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
import inspect
from pathlib import Path
import unittest
from unittest.mock import patch

import requests

import scripts.simulation.nar_official_response_live_capture as live
from scripts.simulation.nar_official_response_capture import (
    NAROfficialResponseCaptureError,
    NAROfficialResponseCaptureUnsupportedError,
    NAROfficialResponseCaptureValidationError,
    canonicalize_nar_official_capture_url,
)
from scripts.simulation.repositories.errors import RepositoryDataIntegrityError


_CANONICAL_URL = (
    "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?"
    "k_babaCode=19&k_raceDate=2026%2F07%2F04&k_raceNo=11"
)
_NONCANONICAL_URL = (
    "HTTPS://WWW.KEIBA.GO.JP/KeibaWeb/TodayRaceInfo/DebaTable?"
    "k_raceNo=11&k_raceDate=2026%2F07%2F04&k_babaCode=19"
)
_BODY = "NAR 日本語 bytes".encode("utf-8")
_START = datetime(2026, 7, 4, 1, tzinfo=timezone.utc)


class _Archive:
    def __init__(self, events: list[str], error: Exception | None = None) -> None:
        self.events = events
        self.error = error
        self.saved: list[object] = []

    def save_capture(self, *, capture: object) -> None:
        self.events.append("archive")
        if self.error is not None:
            raise self.error
        self.saved.append(capture)


class _Transport:
    def __init__(self, events: list[str], result: object | None = None, error: Exception | None = None) -> None:
        self.events = events
        self.result = result if result is not None else _result()
        self.error = error
        self.urls: list[str] = []

    def fetch(self, *, canonical_source_url: str) -> object:
        self.events.append("transport")
        self.urls.append(canonical_source_url)
        if self.error is not None:
            raise self.error
        return self.result


class _Clock:
    def __init__(self, events: list[str], values: list[object]) -> None:
        self.events = events
        self.values = iter(values)

    def __call__(self) -> object:
        self.events.append("clock")
        return next(self.values)


class _Response:
    def __init__(
        self,
        *,
        status: int = 200,
        url: str = _CANONICAL_URL,
        headers: dict[str, object] | None = None,
        chunks: tuple[bytes, ...] = (_BODY,),
        stream_error: Exception | None = None,
        events: list[str] | None = None,
    ) -> None:
        self.status_code = status
        self.url = url
        self.headers = headers or {}
        self._chunks = chunks
        self._stream_error = stream_error
        self._events = events if events is not None else []

    def iter_content(self, *, chunk_size: int):
        self._events.append("stream")
        for chunk in self._chunks:
            yield chunk
        if self._stream_error is not None:
            raise self._stream_error

    def close(self) -> None:
        self._events.append("close")


class _Session:
    def __init__(self, response: _Response | None = None, error: Exception | None = None) -> None:
        self.headers: dict[str, str] = {}
        self.response = response
        self.error = error
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.mounts: list[tuple[str, object]] = []

    def mount(self, prefix: str, adapter: object) -> None:
        self.mounts.append((prefix, adapter))

    def get(self, url: str, **kwargs: object) -> _Response:
        self.calls.append((url, kwargs))
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


def _result(**changes: object) -> object:
    values = {
        "canonical_source_url": _CANONICAL_URL,
        "response_body": _BODY,
        "content_type": "text/html; charset=UTF-8",
        "content_encoding": None,
        "http_date": "Fri, 04 Jul 2026 01:00:00 GMT",
        "etag": '"etag"',
        "last_modified": None,
        "content_length": len(_BODY),
    }
    values.update(changes)
    return live._NAROfficialHTTPResponse(**values)


def _service(
    *,
    events: list[str] | None = None,
    times: list[object] | None = None,
    result: object | None = None,
    archive_error: Exception | None = None,
    transport_error: Exception | None = None,
) -> tuple[live.NAROfficialLiveResponseCaptureService, _Archive, _Transport, list[str]]:
    ordered = events if events is not None else []
    archive = _Archive(ordered, archive_error)
    transport = _Transport(ordered, result, transport_error)
    values = times if times is not None else [_START, _START + timedelta(seconds=1), _START + timedelta(seconds=2)]
    return live.NAROfficialLiveResponseCaptureService(archive=archive, transport=transport, utc_clock=_Clock(ordered, values)), archive, transport, ordered


class NAROfficialResponseLiveCaptureTests(unittest.TestCase):
    def test_public_surface_and_signatures_are_exact(self) -> None:
        public = {name for name, value in vars(live).items() if not name.startswith("_") and inspect.isclass(value) or False}
        public |= {name for name, value in vars(live).items() if not name.startswith("_") and inspect.isfunction(value)}
        self.assertEqual(public, {
            "NAROfficialLiveResponseCaptureService",
            "NAROfficialResponseCaptureTransportError",
            "build_nar_official_live_response_capture_service",
        })
        self.assertTrue(issubclass(live.NAROfficialResponseCaptureTransportError, NAROfficialResponseCaptureError))
        self.assertEqual(tuple(inspect.signature(live.NAROfficialLiveResponseCaptureService.capture_response).parameters), ("self", "response_url"))
        self.assertEqual(inspect.signature(live.NAROfficialLiveResponseCaptureService.capture_response).parameters["response_url"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertEqual(tuple(inspect.signature(live.build_nar_official_live_response_capture_service).parameters), ("archive",))

    def test_success_is_causal_canonical_byte_exact_and_archived_before_return(self) -> None:
        service, archive, transport, events = _service()
        capture = service.capture_response(response_url=_NONCANONICAL_URL)
        self.assertEqual(events, ["clock", "transport", "clock", "clock", "archive"])
        self.assertEqual(transport.urls, [_CANONICAL_URL])
        self.assertEqual(capture.canonical_source_url, _CANONICAL_URL)
        self.assertIs(capture.response_body, _BODY)
        self.assertIs(archive.saved[0], capture)
        self.assertIs(archive.saved[0].response_body, _BODY)
        self.assertIs(capture.to_supplied_official_response().response_body, _BODY)
        self.assertEqual(capture.content_length, len(_BODY))
        self.assertEqual(capture.content_type, "text/html; charset=UTF-8")
        self.assertEqual(capture.http_date, "Fri, 04 Jul 2026 01:00:00 GMT")
        self.assertEqual(capture.etag, '"etag"')

    def test_invalid_url_and_invalid_requested_clock_do_not_contact_transport(self) -> None:
        service, archive, transport, events = _service()
        with self.assertRaises(NAROfficialResponseCaptureValidationError):
            service.capture_response(response_url="https://example.test/nope")
        self.assertEqual(events, [])
        self.assertEqual(archive.saved, [])
        service, archive, transport, events = _service(times=[datetime(2026, 1, 1), _START, _START])
        with self.assertRaises(NAROfficialResponseCaptureValidationError):
            service.capture_response(response_url=_CANONICAL_URL)
        self.assertEqual(events, ["clock"])
        self.assertEqual(transport.urls, [])
        self.assertEqual(archive.saved, [])

    def test_invalid_observed_or_stored_clock_never_archives_and_order_is_domain_checked(self) -> None:
        for values in (
            [_START, datetime(2026, 1, 1), _START],
            [_START, _START + timedelta(seconds=1), datetime(2026, 1, 1)],
        ):
            with self.subTest(values=values):
                service, archive, transport, events = _service(times=values)
                with self.assertRaises(NAROfficialResponseCaptureValidationError):
                    service.capture_response(response_url=_CANONICAL_URL)
                self.assertEqual(transport.urls, [_CANONICAL_URL])
                self.assertEqual(archive.saved, [])
        service, archive, _transport, _events = _service(times=[_START + timedelta(seconds=2), _START, _START + timedelta(seconds=3)])
        with self.assertRaises(NAROfficialResponseCaptureValidationError):
            service.capture_response(response_url=_CANONICAL_URL)
        self.assertEqual(archive.saved, [])

    def test_archive_errors_propagate_unchanged(self) -> None:
        sentinel = RepositoryDataIntegrityError("archive sentinel")
        service, _archive, _transport, events = _service(archive_error=sentinel)
        with self.assertRaises(RepositoryDataIntegrityError) as raised:
            service.capture_response(response_url=_CANONICAL_URL)
        self.assertIs(raised.exception, sentinel)
        self.assertEqual(events[-1], "archive")

    def test_transport_and_unsupported_errors_leave_no_unarchived_capture(self) -> None:
        for error in (live.NAROfficialResponseCaptureTransportError("transport"), NAROfficialResponseCaptureUnsupportedError("encoding")):
            with self.subTest(error=type(error)):
                service, archive, _transport, _events = _service(transport_error=error)
                with self.assertRaises(type(error)):
                    service.capture_response(response_url=_CANONICAL_URL)
                self.assertEqual(archive.saved, [])

    def test_domain_utf8_and_empty_body_fail_before_archive(self) -> None:
        for body, error in ((b"\xff", NAROfficialResponseCaptureUnsupportedError), (b"", NAROfficialResponseCaptureValidationError)):
            with self.subTest(body=body):
                service, archive, _transport, _events = _service(result=_result(response_body=body, content_length=len(body)))
                with self.assertRaises(error):
                    service.capture_response(response_url=_CANONICAL_URL)
                self.assertEqual(archive.saved, [])

    def test_transport_result_must_match_requested_canonical_url_and_exact_type(self) -> None:
        service, archive, _transport, _events = _service(result=object())
        with self.assertRaises(live.NAROfficialResponseCaptureTransportError):
            service.capture_response(response_url=_CANONICAL_URL)
        self.assertEqual(archive.saved, [])
        service, archive, _transport, _events = _service(result=_result(canonical_source_url="https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=1"))
        with self.assertRaises(live.NAROfficialResponseCaptureTransportError):
            service.capture_response(response_url=_CANONICAL_URL)
        self.assertEqual(archive.saved, [])

    def test_requests_transport_configures_strict_request_and_no_retries(self) -> None:
        response = _Response(headers={"Content-Length": str(len(_BODY))})
        session = _Session(response)
        with patch.object(live._requests, "Session", return_value=session):
            transport = live._RequestsNAROfficialHTTPTransport()
        result = transport.fetch(canonical_source_url=_CANONICAL_URL)
        self.assertEqual(result.response_body, _BODY)
        self.assertEqual(session.calls, [(_CANONICAL_URL, {
            "headers": {"Accept-Encoding": "identity"}, "stream": True, "allow_redirects": False,
            "verify": True, "timeout": (10.0, 10.0),
        })])
        self.assertEqual(session.headers["User-Agent"], live._USER_AGENT)
        self.assertEqual([prefix for prefix, _adapter in session.mounts], ["https://", "http://"])
        self.assertTrue(all(adapter.max_retries.total == 0 for _prefix, adapter in session.mounts))
        self.assertEqual(response._events, ["stream", "close"])

    def test_non_200_and_redirects_fail_closed_without_body_acceptance(self) -> None:
        for status in (301, 302, 404, 429, 500):
            with self.subTest(status=status):
                response = _Response(status=status)
                session = _Session(response)
                transport = live._RequestsNAROfficialHTTPTransport.__new__(live._RequestsNAROfficialHTTPTransport)
                transport._session = session
                with self.assertRaises(live.NAROfficialResponseCaptureTransportError):
                    transport.fetch(canonical_source_url=_CANONICAL_URL)
                self.assertEqual(response._events, ["close"])

    def test_content_encoding_policy(self) -> None:
        for header, expected in ((None, None), ("identity", "identity"), ("IDENTITY", "identity")):
            with self.subTest(header=header):
                response = _Response(headers={"Content-Encoding": header} if header is not None else {})
                transport = live._RequestsNAROfficialHTTPTransport.__new__(live._RequestsNAROfficialHTTPTransport)
                transport._session = _Session(response)
                self.assertEqual(transport.fetch(canonical_source_url=_CANONICAL_URL).content_encoding, expected)
        for header in ("gzip", "deflate", "br"):
            with self.subTest(header=header):
                response = _Response(headers={"Content-Encoding": header})
                transport = live._RequestsNAROfficialHTTPTransport.__new__(live._RequestsNAROfficialHTTPTransport)
                transport._session = _Session(response)
                with self.assertRaises(NAROfficialResponseCaptureUnsupportedError):
                    transport.fetch(canonical_source_url=_CANONICAL_URL)
                self.assertEqual(response._events, ["close"])

    def test_content_length_and_incremental_limit_policy(self) -> None:
        exact = b"x" * live._MAX_RESPONSE_BODY_BYTES
        response = _Response(headers={"Content-Length": str(len(exact))}, chunks=(exact,))
        transport = live._RequestsNAROfficialHTTPTransport.__new__(live._RequestsNAROfficialHTTPTransport); transport._session = _Session(response)
        self.assertEqual(len(transport.fetch(canonical_source_url=_CANONICAL_URL).response_body), live._MAX_RESPONSE_BODY_BYTES)
        cases = (
            ({"Content-Length": str(live._MAX_RESPONSE_BODY_BYTES + 1)}, (_BODY,)),
            ({}, (b"x" * live._MAX_RESPONSE_BODY_BYTES, b"x")),
            ({"Content-Length": "1"}, (b"x" * live._MAX_RESPONSE_BODY_BYTES, b"x")),
            ({"Content-Length": "bad"}, (_BODY,)),
            ({"Content-Length": "-1"}, (_BODY,)),
            ({"Content-Length": "99"}, (_BODY,)),
            ({"Content-Length": "1"}, (_BODY,)),
        )
        for headers, chunks in cases:
            with self.subTest(headers=headers, lengths=tuple(map(len, chunks))):
                response = _Response(headers=headers, chunks=chunks)
                transport = live._RequestsNAROfficialHTTPTransport.__new__(live._RequestsNAROfficialHTTPTransport); transport._session = _Session(response)
                with self.assertRaises(live.NAROfficialResponseCaptureTransportError):
                    transport.fetch(canonical_source_url=_CANONICAL_URL)
                self.assertEqual(response._events[-1], "close")
        response = _Response(headers={"Content-Length": "000"})
        transport = live._RequestsNAROfficialHTTPTransport.__new__(live._RequestsNAROfficialHTTPTransport); transport._session = _Session(response)
        with self.assertRaises(live.NAROfficialResponseCaptureTransportError):
            transport.fetch(canonical_source_url=_CANONICAL_URL)

    def test_effective_url_and_requests_failures_are_transport_errors(self) -> None:
        response = _Response(url="https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=1")
        transport = live._RequestsNAROfficialHTTPTransport.__new__(live._RequestsNAROfficialHTTPTransport); transport._session = _Session(response)
        with self.assertRaises(live.NAROfficialResponseCaptureTransportError):
            transport.fetch(canonical_source_url=_CANONICAL_URL)
        for error in (requests.Timeout(), requests.ConnectionError(), requests.exceptions.SSLError("tls")):
            with self.subTest(error=type(error)):
                transport = live._RequestsNAROfficialHTTPTransport.__new__(live._RequestsNAROfficialHTTPTransport); transport._session = _Session(error=error)
                with self.assertRaises(live.NAROfficialResponseCaptureTransportError):
                    transport.fetch(canonical_source_url=_CANONICAL_URL)
        response = _Response(stream_error=requests.ConnectionError())
        transport = live._RequestsNAROfficialHTTPTransport.__new__(live._RequestsNAROfficialHTTPTransport); transport._session = _Session(response)
        with self.assertRaises(live.NAROfficialResponseCaptureTransportError):
            transport.fetch(canonical_source_url=_CANONICAL_URL)
        self.assertEqual(response._events[-1], "close")

    def test_factory_uses_private_requests_transport_and_aware_utc_clock(self) -> None:
        service = live.build_nar_official_live_response_capture_service(archive=_Archive([]))
        self.assertIsInstance(service._transport, live._RequestsNAROfficialHTTPTransport)
        value = service._utc_clock()
        self.assertIs(type(value), datetime)
        self.assertIsNotNone(value.tzinfo)
        self.assertEqual(value.utcoffset(), timedelta(0))

    def test_source_contract_forbids_legacy_and_text_roundtrip_dependencies(self) -> None:
        path = Path(__file__).parents[1] / "scripts/simulation/nar_official_response_live_capture.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imports |= {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        self.assertFalse(any(name.startswith("scripts.providers.nar_provider") for name in imports))
        for forbidden in ("response.text", "response.content", "response.apparent_encoding", "response.encoding", "sqlite3", "pathlib", "open(", "NARProvider", "fetch_deba_table", "_save_html", "except Exception", "except BaseException"):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("nar_official_response_live_capture", Path(__file__).parents[1].joinpath("scripts/simulation/__init__.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
