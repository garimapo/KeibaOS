from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import inspect
import unittest

import scripts.simulation.jra_official_response_capture as module
from scripts.simulation.jra_official_response_capture import (
    JRAFinalWinOddsResponseCapture, JRAFinalWinOddsSuppliedOfficialResponse, JRAOfficialPageKind,
    JRAOfficialResponseCapture, JRAOfficialResponseCaptureUnsupportedError,
    JRAOfficialTargetRaceCardResponseCapture,
    JRAOfficialResponseCaptureValidationError, JRASuppliedOfficialResponse, canonicalize_jra_official_capture_url,
)
from scripts.simulation.jra_official_identity import JRAExternalRaceIdentity, JRAOfficialFinalWinOddsRequestLocator

S = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC"
U = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud002020102902%2F22"
D = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0106202504030420250913%2FDC"
BODY = "<meta charset=\"Shift_JIS\">\u30c6\u30b9\u30c8".encode("cp932")
T = datetime(2026, 1, 1, tzinfo=timezone.utc)


def capture(**changes):
    values = dict(canonical_source_url=S, response_body=BODY, charset="cp932", requested_at=T, observed_at=T, stored_at=T, http_status=200, content_type=" Text/HTML ; charset=Shift_JIS ")
    values.update(changes)
    return JRAOfficialResponseCapture(**values)


def locator():
    return JRAOfficialFinalWinOddsRequestLocator(
        endpoint_url="https://www.jra.go.jp/JRADB/accessO.html", cname="pw151ou1006202601021220260105Z/2E",
        external_race_identity=JRAExternalRaceIdentity("2026", "06", "01", "02", "12"),
        request_identity_sha256="9c4a4f2dfc7e2c21841f7a2bb3f36ec7397312a34b565ff7e511e74800774ade",
    )


def final_capture(**changes):
    values = dict(request_locator=locator(), response_body=BODY, charset="cp932", requested_at=T, observed_at=T, stored_at=T, http_status=200, content_type="text/html")
    values.update(changes)
    return JRAFinalWinOddsResponseCapture(**values)

def target_capture(**changes):
    values = dict(canonical_source_url=D, response_body=BODY, charset="cp932", requested_at=T, observed_at=T, stored_at=T, http_status=200, content_type="text/html")
    values.update(changes)
    return JRAOfficialTargetRaceCardResponseCapture(**values)


class JRAOfficialResponseCaptureTests(unittest.TestCase):
    def test_public_surface_and_signature(self):
        self.assertEqual({n for n in vars(module) if not n.startswith("_")}, {"JRAOfficialPageKind", "JRAOfficialResponseCaptureError", "JRAOfficialResponseCaptureValidationError", "JRAOfficialResponseCaptureUnsupportedError", "JRAOfficialResponseCaptureMissingError", "JRASuppliedOfficialResponse", "JRAFinalWinOddsSuppliedOfficialResponse", "JRAOfficialResponseCapture", "JRAFinalWinOddsResponseCapture", "JRAOfficialTargetRaceCardResponseCapture", "JRAOfficialResponseCaptureArchive", "canonicalize_jra_official_capture_url"})
        self.assertEqual(tuple(inspect.signature(canonicalize_jra_official_capture_url).parameters), ("page_kind", "response_url"))

    def test_canonical_urls_and_supplied_reconstruction(self):
        self.assertEqual(canonicalize_jra_official_capture_url(page_kind=JRAOfficialPageKind.RACE_RESULT, response_url=S.replace("%2F", "/")), S)
        self.assertEqual(canonicalize_jra_official_capture_url(page_kind=JRAOfficialPageKind.HORSE_PROFILE_HISTORY, response_url=U), U)
        item = capture()
        self.assertEqual(item.response_sha256, hashlib.sha256(BODY).hexdigest())
        self.assertEqual(item.content_type, "text/html; charset=shift_jis")
        self.assertEqual(item.to_supplied_official_response(), JRASuppliedOfficialResponse(response_url=S, response_body=BODY, observed_at=T))

    def test_closed_validation_and_capture_id_semantics(self):
        for bad in (S.replace("%2F", "%2f"), S.replace("%2F", "%252F"), S + "&x=1"):
            with self.assertRaises(JRAOfficialResponseCaptureValidationError):
                canonicalize_jra_official_capture_url(page_kind=JRAOfficialPageKind.RACE_RESULT, response_url=bad)
        with self.assertRaises(JRAOfficialResponseCaptureUnsupportedError):
            capture(response_body=b"\x81")
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            capture(http_status=True)
        with self.assertRaises(JRAOfficialResponseCaptureUnsupportedError):
            capture(content_encoding="gzip")
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            capture(content_length=len(BODY) + 1)
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            capture(observed_at=datetime(2026, 1, 1))
        self.assertNotEqual(capture().capture_id, capture(observed_at=T + timedelta(microseconds=1), stored_at=T + timedelta(microseconds=1)).capture_id)
        self.assertEqual(capture().capture_id, capture(etag="x", content_encoding="identity", content_type="text/html").capture_id)

    def test_final_odds_response_and_v2_capture_identity(self):
        value = final_capture()
        self.assertEqual(value.page_kind, JRAOfficialPageKind.FINAL_WIN_ODDS)
        self.assertEqual(value.capture_id, "jra-capture-v2:c2f10e8802ae1ea6037d497b9d2bfe96587b09fb76218b774547b6dabff0b7a7")
        self.assertEqual(value.to_supplied_official_response(), JRAFinalWinOddsSuppliedOfficialResponse(locator(), BODY, observed_at=T))
        self.assertNotEqual(value.capture_id, final_capture(observed_at=T + timedelta(microseconds=1), stored_at=T + timedelta(microseconds=1)).capture_id)
        changed_locator = JRAOfficialFinalWinOddsRequestLocator(
            endpoint_url=locator().endpoint_url, cname=locator().cname.replace("2E", "2F"),
            external_race_identity=locator().external_race_identity,
            request_identity_sha256="ad66f5407394c0c1166c338faa4d17c766ae7ce6f1cd43d75aa22780799b2432",
        )
        self.assertNotEqual(value.capture_id, final_capture(request_locator=changed_locator).capture_id)
        self.assertEqual(capture().capture_id, "jra-capture-v1:6346ff4ffb171d35d9bfa72477537dcd6fc9abe36253b7b4edb2be0cf671cc89")

    def test_access_d_is_supplied_only_for_v1_and_has_v3_domain(self):
        self.assertEqual(JRASuppliedOfficialResponse(response_url=D, response_body=BODY, observed_at=T).response_url, D)
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            capture(canonical_source_url=D)
        with self.assertRaises(JRAOfficialResponseCaptureValidationError):
            canonicalize_jra_official_capture_url(page_kind=JRAOfficialPageKind.TARGET_RACE_CARD, response_url=D)
        value = target_capture()
        self.assertEqual(value.schema_version, 3)
        self.assertEqual(value.page_kind, JRAOfficialPageKind.TARGET_RACE_CARD)
        self.assertTrue(value.capture_id.startswith("jra-capture-v3:"))
        self.assertEqual(value.to_supplied_official_response(), JRASuppliedOfficialResponse(response_url=D, response_body=BODY, observed_at=T))
