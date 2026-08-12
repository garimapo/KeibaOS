from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import inspect
import unittest

import scripts.simulation.jra_official_response_capture as module
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialPageKind, JRAOfficialResponseCapture, JRAOfficialResponseCaptureUnsupportedError,
    JRAOfficialResponseCaptureValidationError, JRASuppliedOfficialResponse, canonicalize_jra_official_capture_url,
)

S = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC"
U = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud002020102902%2F22"
BODY = "<meta charset=\"Shift_JIS\">\u30c6\u30b9\u30c8".encode("cp932")
T = datetime(2026, 1, 1, tzinfo=timezone.utc)


def capture(**changes):
    values = dict(canonical_source_url=S, response_body=BODY, charset="cp932", requested_at=T, observed_at=T, stored_at=T, http_status=200, content_type=" Text/HTML ; charset=Shift_JIS ")
    values.update(changes)
    return JRAOfficialResponseCapture(**values)


class JRAOfficialResponseCaptureTests(unittest.TestCase):
    def test_public_surface_and_signature(self):
        self.assertEqual({n for n in vars(module) if not n.startswith("_")}, {"JRAOfficialPageKind", "JRAOfficialResponseCaptureError", "JRAOfficialResponseCaptureValidationError", "JRAOfficialResponseCaptureUnsupportedError", "JRAOfficialResponseCaptureMissingError", "JRASuppliedOfficialResponse", "JRAOfficialResponseCapture", "JRAOfficialResponseCaptureArchive", "canonicalize_jra_official_capture_url"})
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
