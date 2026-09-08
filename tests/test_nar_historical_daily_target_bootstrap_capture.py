import dataclasses
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

import scripts.simulation.nar_historical_daily_target_bootstrap_capture as capture_module
from scripts.simulation.nar_historical_daily_target_bootstrap_capture import (
    NARMonthlyConveneInfoBootstrapCaptureUnsupportedError,
    NARMonthlyConveneInfoBootstrapCaptureValidationError,
    NARMonthlyConveneInfoBootstrapPageKind,
    NARMonthlyConveneInfoBootstrapSupplierCapture,
)


_FIXTURES = Path(__file__).parent / "fixtures" / "nar_daily_target_bootstrap"
_PROVENANCE = json.loads((_FIXTURES / "provenance.json").read_text(encoding="utf-8"))
_BY_ROLE = {item["fixture_role"]: item for item in _PROVENANCE["records"]}
_OLD_FIXTURES = Path(__file__).parent / "fixtures" / "nar_daily_targets"


def _capture(role):
    if role == "locator_script":
        item = _PROVENANCE["pinned_locator_script"]
        old = json.loads((_OLD_FIXTURES / "provenance.json").read_text(encoding="utf-8"))
        record = next(value for value in old["records"] if value["role"] == "monthly_locator_supplier")
        return NARMonthlyConveneInfoBootstrapSupplierCapture(
            page_kind=NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT,
            canonical_request_url=record["requested_url"],
            effective_url=record["effective_url"],
            response_body=(_OLD_FIXTURES / record["path"]).read_bytes(),
            charset="utf-8",
            requested_at=datetime.fromisoformat(record["requested_at"]),
            observed_at=datetime.fromisoformat(record["observed_at"]),
            stored_at=datetime.fromisoformat(item["stored_at"]),
            http_status=old["acquisition_profile"]["http_status"],
            content_type=record["content_type"],
            content_encoding=record["content_encoding"],
            content_length=record["content_length_header"],
        )
    item = _BY_ROLE[role]
    kind = {
        "official_home": NARMonthlyConveneInfoBootstrapPageKind.OFFICIAL_HOME,
        "monthly_root": NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT,
    }[role]
    return NARMonthlyConveneInfoBootstrapSupplierCapture(
        page_kind=kind,
        canonical_request_url=item["requested_url"],
        effective_url=item["effective_url"],
        response_body=(_FIXTURES / item["path"]).read_bytes(),
        charset=item["charset"],
        requested_at=datetime.fromisoformat(item["requested_at"]),
        observed_at=datetime.fromisoformat(item["observed_at"]),
        stored_at=datetime.fromisoformat(item["stored_at"]),
        http_status=item["http_status"],
        content_type=item["content_type"],
        content_encoding=item["content_encoding"],
        content_length=item["content_length_header"],
    )


def _replace(value, **changes):
    fields = {
        item.name: getattr(value, item.name)
        for item in dataclasses.fields(value)
        if item.init
    }
    fields.update(changes)
    return type(value)(**fields)


class NARMonthlyConveneInfoBootstrapCaptureTests(unittest.TestCase):
    def test_official_fixture_provenance_lengths_digests_and_capture_ids(self):
        for role in ("official_home", "monthly_root"):
            item = _BY_ROLE[role]
            body = (_FIXTURES / item["path"]).read_bytes()
            self.assertEqual(len(body), item["byte_length"])
            self.assertEqual(hashlib.sha256(body).hexdigest(), item["response_sha256"])
            value = _capture(role)
            self.assertEqual(value.response_sha256, item["response_sha256"])
            self.assertEqual(value.capture_id, item["capture_id"])
        script = _capture("locator_script")
        expected = _PROVENANCE["pinned_locator_script"]
        self.assertEqual(len(script.response_body), expected["byte_length"])
        self.assertEqual(script.response_sha256, expected["response_sha256"])
        self.assertEqual(script.capture_id, expected["capture_id"])

    def test_capture_identity_is_deterministic_and_uses_observation_not_storage(self):
        value = _capture("official_home")
        self.assertEqual(value, _replace(value))
        later = _replace(value, stored_at=value.stored_at + timedelta(days=1))
        self.assertEqual(value.capture_id, later.capture_id)
        changed = _replace(value, observed_at=value.observed_at + timedelta(microseconds=1))
        self.assertNotEqual(value.capture_id, changed.capture_id)

    def test_capture_is_frozen_slotted_and_retains_honest_utc_times(self):
        value = _capture("official_home")
        self.assertTrue(dataclasses.is_dataclass(value))
        self.assertFalse(hasattr(value, "__dict__"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            value.http_status = 201
        for moment in (value.requested_at, value.observed_at, value.stored_at):
            self.assertEqual(moment.utcoffset(), timedelta(0))
        self.assertLessEqual(value.requested_at, value.observed_at)
        self.assertLessEqual(value.observed_at, value.stored_at)

    def test_wrong_page_kind_and_exact_url_are_rejected(self):
        value = _capture("official_home")
        with self.assertRaises(NARMonthlyConveneInfoBootstrapCaptureValidationError):
            _replace(value, page_kind="official_home")
        for url in (
            "http://www.keiba.go.jp/",
            "https://www2.keiba.go.jp/",
            "https://www.keiba.go.jp:443/",
            "https://www.keiba.go.jp/?x=1",
        ):
            with self.subTest(url=url), self.assertRaises(
                NARMonthlyConveneInfoBootstrapCaptureValidationError
            ):
                _replace(value, canonical_request_url=url, effective_url=url)

    def test_effective_url_redirect_identity_is_rejected(self):
        value = _capture("official_home")
        with self.assertRaises(NARMonthlyConveneInfoBootstrapCaptureValidationError):
            _replace(value, effective_url="https://www.keiba.go.jp/other")

    def test_body_charset_status_content_type_and_encoding_are_strict(self):
        value = _capture("official_home")
        cases = (
            ({"response_body": b"\xff"}, NARMonthlyConveneInfoBootstrapCaptureUnsupportedError),
            ({"charset": "UTF-8"}, NARMonthlyConveneInfoBootstrapCaptureValidationError),
            ({"http_status": True}, NARMonthlyConveneInfoBootstrapCaptureValidationError),
            ({"http_status": 204}, NARMonthlyConveneInfoBootstrapCaptureValidationError),
            ({"content_type": "text/html; charset=UTF-8"}, NARMonthlyConveneInfoBootstrapCaptureUnsupportedError),
            ({"content_encoding": "gzip"}, NARMonthlyConveneInfoBootstrapCaptureUnsupportedError),
            ({"content_encoding": 1}, NARMonthlyConveneInfoBootstrapCaptureValidationError),
            ({"content_length": len(value.response_body) - 1}, NARMonthlyConveneInfoBootstrapCaptureValidationError),
        )
        for changes, error in cases:
            with self.subTest(changes=changes), self.assertRaises(error):
                _replace(value, **changes)

    def test_timestamp_types_awareness_and_order_are_strict(self):
        value = _capture("official_home")
        naive = value.requested_at.replace(tzinfo=None)
        cases = (
            {"requested_at": None},
            {"requested_at": naive},
            {"observed_at": value.requested_at - timedelta(microseconds=1)},
            {"stored_at": value.observed_at - timedelta(microseconds=1)},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(
                NARMonthlyConveneInfoBootstrapCaptureValidationError
            ):
                _replace(value, **changes)

    def test_non_utc_aware_inputs_are_normalized_without_changing_instants(self):
        value = _capture("official_home")
        offset = timezone(timedelta(hours=9))
        rebuilt = _replace(
            value,
            requested_at=value.requested_at.astimezone(offset),
            observed_at=value.observed_at.astimezone(offset),
            stored_at=value.stored_at.astimezone(offset),
        )
        self.assertEqual(rebuilt, value)

    def test_public_capture_exports_are_exact(self):
        public = {name for name in vars(capture_module) if not name.startswith("_")}
        self.assertEqual(
            public,
            {
                "NARMonthlyConveneInfoBootstrapPageKind",
                "NARMonthlyConveneInfoBootstrapCaptureError",
                "NARMonthlyConveneInfoBootstrapCaptureValidationError",
                "NARMonthlyConveneInfoBootstrapCaptureUnsupportedError",
                "NARMonthlyConveneInfoBootstrapSupplierCapture",
            },
        )


if __name__ == "__main__":
    unittest.main()
