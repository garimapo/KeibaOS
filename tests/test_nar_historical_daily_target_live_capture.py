import inspect
import unittest
from datetime import datetime, timedelta, timezone

from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetPageKind,
    NARHistoricalDailyTargetRequestIdentity,
)
from scripts.simulation.nar_historical_daily_target_live_capture import (
    NARHistoricalDailyTargetCaptureTransportError,
    NARHistoricalDailyTargetLiveCaptureService,
    _NARHistoricalDailyTargetHTTPResponse,
    _RequestsNARHistoricalDailyTargetHTTPTransport,
)


class _Archive:
    def __init__(self, fail=False):
        self.saved = []
        self.fail = fail

    def load_capture(self, *, capture_id):
        return next((item for item in self.saved if item.capture_id == capture_id), None)

    def save_capture(self, *, capture):
        if self.fail:
            raise RuntimeError("archive failed")
        self.saved.append(capture)


class _Transport:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def fetch(self, *, request_identity):
        self.calls.append(request_identity)
        if self.error:
            raise self.error
        return self.response


class _Clock:
    def __init__(self):
        self.value = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class _HTTPResponse:
    def __init__(self, *, url, status=200, headers=None, chunks=(b"<html></html>",)):
        self.url = url
        self.status_code = status
        self.headers = headers or {"Content-Type": "text/html; charset=UTF-8"}
        self.chunks = chunks
        self.closed = False

    def iter_content(self, *, chunk_size):
        self.chunk_size = chunk_size
        yield from self.chunks

    def close(self):
        self.closed = True


class _Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class NARHistoricalDailyTargetLiveCaptureTest(unittest.TestCase):
    def request(self):
        raw = b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2025&k_month=1"
        return NARHistoricalDailyTargetRequestIdentity(
            NARHistoricalDailyTargetPageKind.MONTHLY_CONVENE_INFO,
            raw,
            "https://www.keiba.go.jp" + raw.decode("ascii"),
            "supplied-locator:test",
        )

    def response(self, request):
        return _NARHistoricalDailyTargetHTTPResponse(
            request.resolved_request_url,
            b"<html></html>",
            "text/html; charset=UTF-8",
            None,
            "date",
            None,
            None,
            13,
        )

    def test_one_exact_supplied_request_is_archived_before_return(self):
        request = self.request()
        transport = _Transport(self.response(request))
        archive = _Archive()
        result = NARHistoricalDailyTargetLiveCaptureService(
            archive=archive, transport=transport, utc_clock=_Clock()
        ).capture_supplied_response(request_identity=request)
        self.assertEqual([request], transport.calls)
        self.assertEqual([result], archive.saved)
        self.assertLessEqual(result.requested_at, result.observed_at)
        self.assertLessEqual(result.observed_at, result.stored_at)
        self.assertEqual(request.official_supplied_request_material, result.request_identity.official_supplied_request_material)

    def test_transport_effective_identity_mismatch_returns_no_capture(self):
        request = self.request()
        bad = self.response(request)
        bad = _NARHistoricalDailyTargetHTTPResponse(
            bad.effective_url + "&alias=1", bad.response_body, bad.content_type,
            bad.content_encoding, bad.http_date, bad.etag, bad.last_modified, bad.content_length
        )
        archive = _Archive()
        with self.assertRaises(NARHistoricalDailyTargetCaptureTransportError):
            NARHistoricalDailyTargetLiveCaptureService(
                archive=archive, transport=_Transport(bad), utc_clock=_Clock()
            ).capture_supplied_response(request_identity=request)
        self.assertEqual([], archive.saved)

    def test_transport_and_archive_failures_do_not_return_a_capture(self):
        request = self.request()
        archive = _Archive()
        with self.assertRaises(NARHistoricalDailyTargetCaptureTransportError):
            NARHistoricalDailyTargetLiveCaptureService(
                archive=archive,
                transport=_Transport(error=NARHistoricalDailyTargetCaptureTransportError("failed")),
                utc_clock=_Clock(),
            ).capture_supplied_response(request_identity=request)
        self.assertEqual([], archive.saved)
        with self.assertRaisesRegex(RuntimeError, "archive failed"):
            NARHistoricalDailyTargetLiveCaptureService(
                archive=_Archive(fail=True), transport=_Transport(self.response(request)), utc_clock=_Clock()
            ).capture_supplied_response(request_identity=request)

    def test_capture_api_has_no_locator_construction_parameters(self):
        signature = inspect.signature(NARHistoricalDailyTargetLiveCaptureService.capture_supplied_response)
        self.assertEqual(["self", "request_identity"], list(signature.parameters))
        source = inspect.getsource(NARHistoricalDailyTargetLiveCaptureService)
        self.assertNotIn("target_date", source)
        self.assertNotIn("baba_code", source)
        self.assertNotIn("k_raceDate", source)
        self.assertNotIn("k_year", source)

    def test_requests_transport_disables_redirects_and_compression_for_one_get(self):
        request = self.request()
        response = _HTTPResponse(url=request.resolved_request_url)
        session = _Session(response)
        transport = object.__new__(_RequestsNARHistoricalDailyTargetHTTPTransport)
        transport._session = session
        result = transport.fetch(request_identity=request)
        self.assertEqual(b"<html></html>", result.response_body)
        self.assertEqual(1, len(session.calls))
        url, options = session.calls[0]
        self.assertEqual(request.resolved_request_url, url)
        self.assertEqual({"Accept-Encoding": "identity"}, options["headers"])
        self.assertFalse(options["allow_redirects"])
        self.assertTrue(options["stream"])
        self.assertTrue(options["verify"])
        self.assertTrue(response.closed)

    def test_requests_transport_fails_closed_on_status_type_size_and_encoding(self):
        request = self.request()
        cases = (
            _HTTPResponse(url=request.resolved_request_url, status=302),
            _HTTPResponse(url=request.resolved_request_url, headers={"Content-Type": "text/html; charset=Shift_JIS"}),
            _HTTPResponse(url=request.resolved_request_url, headers={"Content-Type": "text/html; charset=UTF-8", "Content-Encoding": "gzip"}),
            _HTTPResponse(url=request.resolved_request_url, headers={"Content-Type": "text/html; charset=UTF-8", "Content-Length": "4194305"}),
        )
        for response in cases:
            with self.subTest(status=response.status_code, headers=response.headers):
                session = _Session(response)
                transport = object.__new__(_RequestsNARHistoricalDailyTargetHTTPTransport)
                transport._session = session
                with self.assertRaises(Exception):
                    transport.fetch(request_identity=request)
                self.assertTrue(response.closed)


if __name__ == "__main__":
    unittest.main()
