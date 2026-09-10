from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
import hashlib
import inspect
import json
import unittest

from scripts.simulation import nar_market_odds_capture as module
from scripts.simulation.nar_market_odds_capture import (
    NARMarketOddsCaptureArchive,
    NARMarketOddsCaptureSource,
    NARMarketOddsCaptureUnsupportedError,
    NARMarketOddsCaptureValidationError,
    NARMarketOddsPageKind,
    NARMarketOddsRaceIdentity,
    NARMarketOddsRequestIdentity,
    NARMarketOddsResponseCapture,
    build_nar_market_odds_request_identity,
)


T0 = datetime(2026, 9, 10, 3, 4, 5, 100001, tzinfo=timezone.utc)
PATHS = {
    NARMarketOddsPageKind.ODDS_TAN_FUKU: "/KeibaWeb/TodayRaceInfo/OddsTanFuku",
    NARMarketOddsPageKind.ODDS_UM_LEN_FUKU: "/KeibaWeb/TodayRaceInfo/OddsUmLenFuku",
    NARMarketOddsPageKind.ODDS_WIDE: "/KeibaWeb/TodayRaceInfo/OddsWide",
    NARMarketOddsPageKind.ODDS_3_LEN_FUKU: "/KeibaWeb/TodayRaceInfo/Odds3LenFuku",
}


def request(
    kind: NARMarketOddsPageKind = NARMarketOddsPageKind.ODDS_TAN_FUKU,
    *,
    baba_code: str = "11",
    race_date: date = date(2026, 9, 10),
    race_no: int = 7,
) -> NARMarketOddsRequestIdentity:
    return build_nar_market_odds_request_identity(
        page_kind=kind,
        baba_code=baba_code,
        race_date=race_date,
        race_no=race_no,
    )


def capture(
    *,
    request_identity: NARMarketOddsRequestIdentity | None = None,
    body: bytes = "地方競馬\r\nオッズ  \r\n".encode("utf-8"),
    requested_at: datetime = T0,
    observed_at: datetime = T0 + timedelta(microseconds=1),
    captured_at: datetime = T0 + timedelta(microseconds=2),
    content_type: str | None = "text/html; charset=UTF-8",
    content_encoding: str | None = None,
    http_date: str | None = None,
    etag: str | None = None,
    last_modified: str | None = None,
    content_length: int | None = None,
) -> NARMarketOddsResponseCapture:
    identity = request_identity or request()
    return NARMarketOddsResponseCapture(
        request_identity=identity,
        effective_url=identity.canonical_request_url,
        response_body=body,
        charset="utf-8",
        requested_at=requested_at,
        observed_at=observed_at,
        captured_at=captured_at,
        http_status=200,
        content_type=content_type,
        content_encoding=content_encoding,
        http_date=http_date,
        etag=etag,
        last_modified=last_modified,
        content_length=content_length,
    )


class NARMarketOddsCaptureTests(unittest.TestCase):
    def test_page_kinds_paths_query_order_and_uppercase_date_escape_are_exact(self) -> None:
        self.assertEqual(
            tuple((item.name, item.value) for item in NARMarketOddsPageKind),
            (
                ("ODDS_TAN_FUKU", "odds_tan_fuku"),
                ("ODDS_UM_LEN_FUKU", "odds_um_len_fuku"),
                ("ODDS_WIDE", "odds_wide"),
                ("ODDS_3_LEN_FUKU", "odds_3_len_fuku"),
            ),
        )
        for kind, path in PATHS.items():
            with self.subTest(kind=kind):
                identity = request(kind)
                self.assertEqual(
                    identity.canonical_request_url,
                    "https://www.keiba.go.jp"
                    + path
                    + "?k_babaCode=11&k_raceDate=2026%2F09%2F10&k_raceNo=7",
                )
                self.assertNotIn("%2f", identity.canonical_request_url)

    def test_request_identity_uses_exact_canonical_payload_and_is_deterministic(self) -> None:
        identity = request()
        payload = {
            "baba_code": "11",
            "canonical_request_url": identity.canonical_request_url,
            "method": "GET",
            "official_origin": "https://www.keiba.go.jp",
            "organization": "NAR",
            "page_kind": "odds_tan_fuku",
            "race_date": "2026-09-10",
            "race_no": 7,
            "schema_version": 1,
            "source_system": "keiba.go.jp",
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        self.assertEqual(identity.request_identity_sha256, digest)
        self.assertEqual(identity.request_identity, "nar-market-odds-request-v1:" + digest)
        self.assertEqual(identity, request())

    def test_each_provider_request_component_changes_identity(self) -> None:
        original = request()
        alternatives = (
            request(NARMarketOddsPageKind.ODDS_WIDE),
            request(baba_code="12"),
            request(race_date=date(2026, 9, 11)),
            request(race_no=8),
        )
        self.assertEqual(len({original.request_identity, *(item.request_identity for item in alternatives)}), 5)

    def test_race_identity_rejects_noncanonical_or_wrong_exact_types(self) -> None:
        for baba_code in ("", "0", "01", " 1", "1 ", "+1", "１"):
            with self.subTest(baba_code=baba_code):
                with self.assertRaises(NARMarketOddsCaptureValidationError):
                    NARMarketOddsRaceIdentity(baba_code, date(2026, 1, 1), 1)
        for race_date in (datetime(2026, 1, 1), "2026-01-01"):
            with self.subTest(race_date=race_date):
                with self.assertRaises(NARMarketOddsCaptureValidationError):
                    NARMarketOddsRaceIdentity("1", race_date, 1)  # type: ignore[arg-type]
        for race_no in (True, 0, -1, 1.0):
            with self.subTest(race_no=race_no):
                with self.assertRaises(NARMarketOddsCaptureValidationError):
                    NARMarketOddsRaceIdentity("1", date(2026, 1, 1), race_no)  # type: ignore[arg-type]

    def test_capture_preserves_exact_raw_bytes_sha_length_and_is_deterministic(self) -> None:
        value = capture()
        self.assertEqual(value.response_body, "地方競馬\r\nオッズ  \r\n".encode("utf-8"))
        self.assertEqual(value.response_sha256, hashlib.sha256(value.response_body).hexdigest())
        self.assertEqual(value.byte_length, len(value.response_body))
        payload = {
            "captured_at_utc": value.captured_at.isoformat(timespec="microseconds"),
            "charset": "utf-8",
            "content_encoding": None,
            "content_length": None,
            "content_type": "text/html; charset=UTF-8",
            "effective_url": value.effective_url,
            "etag": None,
            "http_date": None,
            "http_status": 200,
            "last_modified": None,
            "observed_at_utc": value.observed_at.isoformat(timespec="microseconds"),
            "request_identity_sha256": value.request_identity.request_identity_sha256,
            "requested_at_utc": value.requested_at.isoformat(timespec="microseconds"),
            "response_sha256": value.response_sha256,
            "schema_version": 1,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(
            value.capture_id,
            "nar-market-odds-capture-v1:" + hashlib.sha256(encoded).hexdigest(),
        )
        self.assertEqual(value, capture())
        self.assertEqual(value.capture_id, capture().capture_id)
        with self.assertRaises(FrozenInstanceError):
            value.charset = "other"  # type: ignore[misc]

    def test_byte_level_differences_are_not_normalized(self) -> None:
        crlf = capture(body="地方\r\n".encode("utf-8"))
        lf = capture(body="地方\n".encode("utf-8"))
        changed = capture(body="地方\r\n!".encode("utf-8"))
        self.assertEqual(len({crlf.response_sha256, lf.response_sha256, changed.response_sha256}), 3)
        self.assertEqual(len({crlf.capture_id, lf.capture_id, changed.capture_id}), 3)

    def test_each_header_and_owned_timestamp_changes_capture_identity(self) -> None:
        original = capture()
        alternatives = (
            capture(content_type="text/plain"),
            capture(content_encoding="identity"),
            capture(http_date="Thu, 10 Sep 2026 03:04:05 GMT"),
            capture(etag='"v1"'),
            capture(last_modified="Wed, 09 Sep 2026 00:00:00 GMT"),
            capture(content_length=len(original.response_body)),
            capture(requested_at=T0 - timedelta(microseconds=1)),
            capture(
                observed_at=T0 + timedelta(microseconds=2),
                captured_at=T0 + timedelta(microseconds=3),
            ),
            capture(captured_at=T0 + timedelta(microseconds=3)),
        )
        self.assertEqual(len({original.capture_id, *(item.capture_id for item in alternatives)}), 10)

    def test_capture_normalizes_aware_times_to_exact_utc_microseconds(self) -> None:
        offset = timezone(timedelta(hours=9))
        value = capture(
            requested_at=datetime(2026, 9, 10, 12, 4, 5, 100001, tzinfo=offset),
            observed_at=datetime(2026, 9, 10, 12, 4, 5, 100002, tzinfo=offset),
            captured_at=datetime(2026, 9, 10, 12, 4, 5, 100003, tzinfo=offset),
        )
        self.assertEqual(value.requested_at.isoformat(timespec="microseconds"), "2026-09-10T03:04:05.100001+00:00")
        self.assertEqual(value.captured_at.utcoffset(), timedelta(0))

    def test_capture_rejects_invalid_url_bytes_status_and_length(self) -> None:
        identity = request()
        base = dict(
            request_identity=identity,
            effective_url=identity.canonical_request_url,
            response_body=b"valid",
            charset="utf-8",
            requested_at=T0,
            observed_at=T0,
            captured_at=T0,
            http_status=200,
        )
        variants = (
            {"effective_url": "https://example.test/"},
            {"response_body": bytearray(b"valid")},
            {"response_body": b""},
            {"http_status": True},
            {"http_status": 404},
            {"content_length": True},
            {"content_length": 4},
            {"etag": "bad\rvalue"},
        )
        for override in variants:
            with self.subTest(override=override):
                with self.assertRaises(NARMarketOddsCaptureValidationError):
                    NARMarketOddsResponseCapture(**(base | override))  # type: ignore[arg-type]

    def test_capture_rejects_unsupported_response_profiles(self) -> None:
        identity = request()
        base = dict(
            request_identity=identity,
            effective_url=identity.canonical_request_url,
            response_body=b"valid",
            charset="utf-8",
            requested_at=T0,
            observed_at=T0,
            captured_at=T0,
            http_status=200,
        )
        for override in (
            {"charset": "shift_jis"},
            {"response_body": b"\xff"},
            {"content_encoding": "gzip"},
        ):
            with self.subTest(override=override):
                with self.assertRaises(NARMarketOddsCaptureUnsupportedError):
                    NARMarketOddsResponseCapture(**(base | override))  # type: ignore[arg-type]

    def test_naive_and_out_of_order_timestamps_are_rejected(self) -> None:
        with self.assertRaises(NARMarketOddsCaptureValidationError):
            capture(requested_at=datetime(2026, 9, 10, 3, 4, 5))
        for times in (
            (T0 + timedelta(seconds=1), T0, T0 + timedelta(seconds=2)),
            (T0, T0 + timedelta(seconds=2), T0 + timedelta(seconds=1)),
        ):
            with self.subTest(times=times):
                with self.assertRaises(NARMarketOddsCaptureValidationError):
                    capture(requested_at=times[0], observed_at=times[1], captured_at=times[2])

    def test_public_protocols_and_static_raw_only_boundary(self) -> None:
        self.assertTrue(hasattr(NARMarketOddsCaptureSource, "load_capture"))
        self.assertTrue(hasattr(NARMarketOddsCaptureArchive, "save_capture"))
        source = inspect.getsource(module)
        for forbidden in (
            "requests",
            "urllib.request",
            "aiohttp",
            "datetime.now",
            "datetime.utcnow",
            "random",
            "uuid",
            "ranking_probability",
            "ValueEngine",
            "BetGenerator",
            "Decimal",
            "sqlite3",
            "JRA",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
