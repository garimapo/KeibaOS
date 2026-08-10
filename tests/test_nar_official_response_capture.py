from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import inspect
import json
import unittest

import scripts.simulation.nar_official_response_capture as capture_module
from scripts.simulation.nar_historical_input_source import NarSuppliedOfficialResponse
from scripts.simulation.nar_official_response_capture import (
    NAROfficialPageKind,
    NAROfficialResponseCapture,
    NAROfficialResponseCaptureUnsupportedError,
    NAROfficialResponseCaptureValidationError,
    canonicalize_nar_official_capture_url,
)


UTC = timezone.utc
REQUESTED = datetime(2026, 8, 10, 1, 2, 3, 4, tzinfo=UTC)
OBSERVED = REQUESTED + timedelta(seconds=1)
STORED = OBSERVED + timedelta(seconds=1)
DEBA = "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=19&k_raceDate=2026%2F07%2F04&k_raceNo=11"
RACE = "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1"
HORSE = "https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30074407776"
BODY = "<html>公式NAR</html>".encode()


def _capture(**changes: object) -> NAROfficialResponseCapture:
    values: dict[str, object] = {
        "canonical_source_url": DEBA,
        "response_body": BODY,
        "charset": "utf-8",
        "requested_at": REQUESTED,
        "observed_at": OBSERVED,
        "stored_at": STORED,
        "http_status": 200,
        "content_type": "text/html; charset=UTF-8",
        "content_encoding": None,
        "content_length": len(BODY),
    }
    values.update(changes)
    return NAROfficialResponseCapture(**values)  # type: ignore[arg-type]


class NAROfficialResponseCaptureTests(unittest.TestCase):
    def test_public_surface_enum_and_signature_are_exact(self) -> None:
        public = {name for name in vars(capture_module) if not name.startswith("_")}
        self.assertEqual(
            public,
            {
                "NAROfficialPageKind", "NAROfficialResponseCapture", "NAROfficialResponseCaptureArchive",
                "NAROfficialResponseCaptureError", "NAROfficialResponseCaptureValidationError",
                "NAROfficialResponseCaptureUnsupportedError", "NAROfficialResponseCaptureMissingError",
                "canonicalize_nar_official_capture_url",
            },
        )
        self.assertEqual(
            {item.name: item.value for item in NAROfficialPageKind},
            {"DEBA_TABLE": "deba_table", "HORSE_MARK_INFO": "horse_mark_info", "RACE_MARK_TABLE": "race_mark_table"},
        )
        self.assertEqual(tuple(inspect.signature(canonicalize_nar_official_capture_url).parameters), ("response_url",))
        self.assertFalse(hasattr(__import__("scripts.simulation", fromlist=["x"]), "NAROfficialResponseCapture"))

    def test_url_canonicalization_closed_vocabulary(self) -> None:
        self.assertEqual(canonicalize_nar_official_capture_url(DEBA), (NAROfficialPageKind.DEBA_TABLE, DEBA))
        self.assertEqual(canonicalize_nar_official_capture_url(RACE), (NAROfficialPageKind.RACE_MARK_TABLE, RACE))
        self.assertEqual(canonicalize_nar_official_capture_url(HORSE), (NAROfficialPageKind.HORSE_MARK_INFO, HORSE))
        self.assertEqual(
            canonicalize_nar_official_capture_url(
                "HTTPS://WWW.KEIBA.GO.JP/KeibaWeb/TodayRaceInfo/DebaTable?k_raceNo=11&k_babaCode=19&k_raceDate=2026%2F07%2F04",
            )[1],
            DEBA,
        )
        self.assertEqual(
            canonicalize_nar_official_capture_url(
                "https://www2.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30074407776",
            )[1],
            "https://www2.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30074407776",
        )

    def test_url_validation_and_unsupported_path_are_fail_closed(self) -> None:
        invalid = (
            "http://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=1&k_raceDate=2026%2F01%2F01&k_raceNo=1",
            "https://example.invalid/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=1&k_raceDate=2026%2F01%2F01&k_raceNo=1",
            "https://127.0.0.1/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=1&k_raceDate=2026%2F01%2F01&k_raceNo=1",
            "https://user@www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode=1&k_raceDate=2026%2F01%2F01&k_raceNo=1",
            DEBA + "#x", DEBA + "&x=1", DEBA.replace("19", "019", 1), DEBA.replace("2026%2F07%2F04", "2026%2F02%2F30"),
            DEBA.replace("k_raceNo=11", "k_raceNo=1+1"), DEBA.replace("k_raceNo=11", "k_raceNo=%ZZ"),
            DEBA + "&k_raceNo=12", DEBA.replace("k_raceNo=11", "k_raceNo=0"),
            DEBA.replace("k_raceNo=11", "k_raceNo=%EF%BC%91"), DEBA.replace("k_raceNo=11", "k_raceNo="),
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(NAROfficialResponseCaptureValidationError):
                    canonicalize_nar_official_capture_url(value)
        with self.assertRaises(NAROfficialResponseCaptureUnsupportedError):
            canonicalize_nar_official_capture_url("https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/Other?k=1")

    def test_capture_derives_exact_digest_and_id(self) -> None:
        value = _capture()
        digest = hashlib.sha256(BODY).hexdigest()
        material = {
            "canonical_source_url": DEBA,
            "observed_at_utc": "2026-08-10T01:02:04.000004+00:00",
            "page_kind": "deba_table",
            "response_sha256": digest,
            "schema_version": 1,
        }
        expected = "nar-capture-v1:" + hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
        ).hexdigest()
        self.assertEqual(value.response_sha256, digest)
        self.assertEqual(value.capture_id, expected)
        self.assertEqual(value.schema_version, 1)
        self.assertEqual(value.page_kind, NAROfficialPageKind.DEBA_TABLE)
        self.assertEqual(value.observed_at.isoformat(timespec="microseconds"), material["observed_at_utc"])

    def test_metadata_does_not_change_capture_id_but_observation_and_body_do(self) -> None:
        baseline = _capture()
        self.assertEqual(baseline.capture_id, _capture(etag="x", requested_at=REQUESTED - timedelta(seconds=1)).capture_id)
        self.assertNotEqual(baseline.capture_id, _capture(observed_at=OBSERVED + timedelta(seconds=1), stored_at=STORED + timedelta(seconds=1)).capture_id)
        self.assertNotEqual(baseline.capture_id, _capture(response_body=b"<html>different</html>", content_length=22).capture_id)

    def test_domain_validation_and_exact_supplied_response_reconstruction(self) -> None:
        for changes, error in (
            ({"response_body": b""}, NAROfficialResponseCaptureValidationError),
            ({"response_body": b"\xff"}, NAROfficialResponseCaptureUnsupportedError),
            ({"charset": "UTF-8"}, NAROfficialResponseCaptureValidationError),
            ({"content_encoding": "gzip"}, NAROfficialResponseCaptureUnsupportedError),
            ({"http_status": True}, NAROfficialResponseCaptureValidationError),
            ({"content_length": len(BODY) + 1}, NAROfficialResponseCaptureValidationError),
            ({"requested_at": REQUESTED.replace(tzinfo=None)}, NAROfficialResponseCaptureValidationError),
            ({"stored_at": REQUESTED}, NAROfficialResponseCaptureValidationError),
            ({"canonical_source_url": DEBA.replace("%2F", "/")}, NAROfficialResponseCaptureValidationError),
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(error):
                    _capture(**changes)
        response = _capture().to_supplied_official_response()
        self.assertIs(type(response), NarSuppliedOfficialResponse)
        self.assertEqual((response.response_url, response.response_body, response.charset, response.observed_at), (DEBA, BODY, "utf-8", OBSERVED))

    def test_utc_normalization_and_header_controls_are_checked(self) -> None:
        offset = timezone(timedelta(hours=9))
        value = _capture(
            requested_at=REQUESTED.astimezone(offset), observed_at=OBSERVED.astimezone(offset), stored_at=STORED.astimezone(offset),
        )
        self.assertEqual((value.requested_at, value.observed_at, value.stored_at), (REQUESTED, OBSERVED, STORED))
        for field in ("content_type", "http_date", "etag", "last_modified"):
            with self.subTest(field=field):
                with self.assertRaises(NAROfficialResponseCaptureValidationError):
                    _capture(**{field: "bad\nvalue"})

    def test_capture_is_frozen_slotted_and_has_no_forbidden_ownership(self) -> None:
        value = _capture()
        with self.assertRaises((AttributeError, TypeError)):
            value.capture_id = "x"  # type: ignore[misc]
        self.assertFalse(hasattr(value, "__dict__"))
        source = inspect.getsource(capture_module)
        for forbidden in ("requests", "httpx", "urllib.request", "socket", "sqlite3", "pathlib", "datetime.now", "datetime.today", "open("):
            self.assertNotIn(forbidden, source)
