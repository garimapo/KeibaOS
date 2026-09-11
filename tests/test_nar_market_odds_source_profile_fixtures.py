from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.simulation.nar_market_odds_capture import (
    NARMarketOddsPageKind,
    NARMarketOddsResponseCapture,
    build_nar_market_odds_request_identity,
)


REPOSITORY_ROOT = Path(__file__).parent.parent
FIXTURE_ROOT = REPOSITORY_ROOT / "tests/fixtures/nar_market_odds/source_profiles/v1"
MANIFEST_PATH = FIXTURE_ROOT / "manifest.json"
ATTRIBUTE_RULE = "tests/fixtures/nar_market_odds/source_profiles/v1/** -text -diff"
PURPOSE = "nar_market_odds_parser_source_profile"
IDENTITY_PREFIX = "nar-market-odds-source-profile-fixture-set-v1:"
QUALIFICATION_METHOD = "nar-market-odds-source-state-qualification-v1"
SAFETY_METHOD = "nar-market-odds-public-data-safety-review-v1"

SLOTS = (
    "open/odds_tan_fuku",
    "open/odds_um_len_fuku",
    "open/odds_wide",
    "open/odds_3_len_fuku",
    "final/odds_tan_fuku",
    "final/odds_um_len_fuku",
    "final/odds_wide",
    "final/odds_3_len_fuku",
)
PATHS = (
    "tests/fixtures/nar_market_odds/source_profiles/v1/open/odds_tan_fuku.html",
    "tests/fixtures/nar_market_odds/source_profiles/v1/open/odds_um_len_fuku.html",
    "tests/fixtures/nar_market_odds/source_profiles/v1/open/odds_wide.html",
    "tests/fixtures/nar_market_odds/source_profiles/v1/open/odds_3_len_fuku.html",
    "tests/fixtures/nar_market_odds/source_profiles/v1/final/odds_tan_fuku.html",
    "tests/fixtures/nar_market_odds/source_profiles/v1/final/odds_um_len_fuku.html",
    "tests/fixtures/nar_market_odds/source_profiles/v1/final/odds_wide.html",
    "tests/fixtures/nar_market_odds/source_profiles/v1/final/odds_3_len_fuku.html",
)
PAGE_KINDS = (
    "odds_tan_fuku",
    "odds_um_len_fuku",
    "odds_wide",
    "odds_3_len_fuku",
)
ROOT_KEYS = {
    "fixture_set_identity",
    "fixtures",
    "manifest_schema_version",
    "purpose",
}
FIXTURE_KEYS = {
    "fixture_slot",
    "page_kind",
    "qualified_state",
    "fixture_relative_path",
    "organization",
    "source_system",
    "request_schema_version",
    "request_identity",
    "request_identity_sha256",
    "baba_code",
    "race_date",
    "race_no",
    "canonical_request_url",
    "capture_schema_version",
    "capture_id",
    "response_sha256",
    "byte_length",
    "effective_url",
    "http_status",
    "charset",
    "content_type",
    "content_encoding",
    "http_date",
    "etag",
    "last_modified",
    "content_length",
    "requested_at_utc",
    "observed_at_utc",
    "captured_at_utc",
    "qualification",
    "publication_safety",
}
QUALIFICATION_KEYS = {
    "method",
    "state_token_utf8",
    "state_token_byte_offset",
    "state_token_occurrence_count",
    "state_context_byte_start",
    "state_context_byte_end",
    "state_context_sha256",
    "state_context_utf8",
    "state_container_locator",
    "market_container_byte_start",
    "market_container_byte_end",
    "market_container_sha256",
    "market_container_locator",
    "selection_key_representation",
    "odds_representation",
}
SAFETY_KEYS = {"method", "result", "reviewed_response_sha256"}


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value: {value}")


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _load_manifest() -> tuple[bytes, dict[str, Any]]:
    raw = MANIFEST_PATH.read_bytes()
    value = json.loads(
        raw.decode("utf-8", errors="strict"),
        object_pairs_hook=_strict_pairs,
        parse_constant=_reject_constant,
    )
    if type(value) is not dict:
        raise ValueError("manifest root must be an object")
    return raw, value


def _exact_datetime(value: object, name: str) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be exact str")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo != timezone.utc or parsed.isoformat(timespec="microseconds") != value:
        raise ValueError(f"{name} must be canonical UTC microsecond text")
    return parsed


def _validate_complete_manifest(value: dict[str, Any]) -> None:
    if set(value) != ROOT_KEYS or value["manifest_schema_version"] != 1 or value["purpose"] != PURPOSE:
        raise ValueError("manifest root contract is invalid")
    fixtures = value["fixtures"]
    if type(fixtures) is not list or len(fixtures) != 8:
        raise ValueError("manifest must contain exactly eight fixtures")
    if tuple(item.get("fixture_slot") for item in fixtures) != SLOTS:
        raise ValueError("fixture slot matrix is incomplete or out of order")
    if tuple(item.get("fixture_relative_path") for item in fixtures) != PATHS:
        raise ValueError("fixture paths are incomplete or out of order")
    if Counter(item.get("qualified_state") for item in fixtures) != Counter({"open": 4, "final": 4}):
        raise ValueError("OPEN/FINAL matrix is incomplete")
    pairs = Counter((item.get("page_kind"), item.get("qualified_state")) for item in fixtures)
    if pairs != Counter((page_kind, state) for state in ("open", "final") for page_kind in PAGE_KINDS):
        raise ValueError("page-kind/state matrix is incomplete")


def test_manifest_is_canonical_complete_and_identity_bound() -> None:
    raw, manifest = _load_manifest()
    assert raw == _canonical_json(manifest)
    _validate_complete_manifest(manifest)
    payload = {
        "fixtures": manifest["fixtures"],
        "manifest_schema_version": 1,
        "purpose": PURPOSE,
    }
    assert manifest["fixture_set_identity"] == IDENTITY_PREFIX + sha256(_canonical_json(payload)).hexdigest()
    assert len({item["fixture_slot"] for item in manifest["fixtures"]}) == 8
    assert len({item["fixture_relative_path"] for item in manifest["fixtures"]}) == 8


def test_partial_matrix_is_rejected_by_the_fixture_contract() -> None:
    _raw, manifest = _load_manifest()
    partial = dict(manifest)
    partial["fixtures"] = list(manifest["fixtures"][:-1])
    with pytest.raises(ValueError, match="exactly eight"):
        _validate_complete_manifest(partial)


def test_raw_fixtures_reconstruct_exact_phase32_captures_and_qualification() -> None:
    _raw, manifest = _load_manifest()
    _validate_complete_manifest(manifest)
    for item in manifest["fixtures"]:
        assert set(item) == FIXTURE_KEYS
        assert item["organization"] == "NAR"
        assert item["source_system"] == "keiba.go.jp"
        assert item["request_schema_version"] == item["capture_schema_version"] == 1
        assert item["http_status"] == 200
        assert item["charset"] == "utf-8"
        assert item["content_type"] == "text/html; charset=UTF-8"
        assert item["content_encoding"] in (None, "identity")
        assert item["content_length"] is None or item["content_length"] == item["byte_length"]

        fixture_path = REPOSITORY_ROOT / item["fixture_relative_path"]
        assert fixture_path.is_file()
        body = fixture_path.read_bytes()
        assert len(body) == item["byte_length"]
        assert sha256(body).hexdigest() == item["response_sha256"]
        assert body.decode("utf-8", errors="strict").encode("utf-8") == body

        request = build_nar_market_odds_request_identity(
            page_kind=NARMarketOddsPageKind(item["page_kind"]),
            baba_code=item["baba_code"],
            race_date=date.fromisoformat(item["race_date"]),
            race_no=item["race_no"],
        )
        assert request.request_identity == item["request_identity"]
        assert request.request_identity_sha256 == item["request_identity_sha256"]
        assert request.canonical_request_url == item["canonical_request_url"] == item["effective_url"]
        assert request.canonical_request_url.startswith("https://www.keiba.go.jp/")

        capture = NARMarketOddsResponseCapture(
            request_identity=request,
            effective_url=item["effective_url"],
            response_body=body,
            charset=item["charset"],
            requested_at=_exact_datetime(item["requested_at_utc"], "requested_at_utc"),
            observed_at=_exact_datetime(item["observed_at_utc"], "observed_at_utc"),
            captured_at=_exact_datetime(item["captured_at_utc"], "captured_at_utc"),
            http_status=item["http_status"],
            content_type=item["content_type"],
            content_encoding=item["content_encoding"],
            http_date=item["http_date"],
            etag=item["etag"],
            last_modified=item["last_modified"],
            content_length=item["content_length"],
        )
        assert capture.response_sha256 == item["response_sha256"]
        assert capture.byte_length == item["byte_length"]
        assert capture.capture_id == item["capture_id"]

        qualification = item["qualification"]
        assert set(qualification) == QUALIFICATION_KEYS
        assert qualification["method"] == QUALIFICATION_METHOD
        token = qualification["state_token_utf8"].encode("utf-8")
        assert token
        assert body.count(token) == qualification["state_token_occurrence_count"] == 1
        assert body.find(token) == qualification["state_token_byte_offset"]
        if item["qualified_state"] == "open":
            assert "現在" in qualification["state_token_utf8"] and "最終" not in qualification["state_token_utf8"]
        else:
            assert "最終" in qualification["state_token_utf8"] and "現在" not in qualification["state_token_utf8"]

        context_start = qualification["state_context_byte_start"]
        context_end = qualification["state_context_byte_end"]
        context = body[context_start:context_end]
        assert 1 <= len(context) <= 512
        assert context.decode("utf-8", errors="strict") == qualification["state_context_utf8"]
        assert sha256(context).hexdigest() == qualification["state_context_sha256"]
        assert context_start <= qualification["state_token_byte_offset"] < context_end

        market_start = qualification["market_container_byte_start"]
        market_end = qualification["market_container_byte_end"]
        assert 0 <= market_start < market_end <= len(body)
        assert sha256(body[market_start:market_end]).hexdigest() == qualification["market_container_sha256"]
        for name in (
            "state_container_locator",
            "market_container_locator",
            "selection_key_representation",
            "odds_representation",
        ):
            assert type(qualification[name]) is str and qualification[name]

        safety = item["publication_safety"]
        assert set(safety) == SAFETY_KEYS
        assert safety == {
            "method": SAFETY_METHOD,
            "result": "approved_exact_public_bytes",
            "reviewed_response_sha256": item["response_sha256"],
        }


def test_manifest_schema_excludes_unapproved_or_sensitive_metadata() -> None:
    _raw, manifest = _load_manifest()
    forbidden = {
        "set-cookie",
        "cookie",
        "authorization",
        "csrf",
        "xsrf",
        "session",
        "session_id",
        "headers",
    }
    for item in manifest["fixtures"]:
        assert not ({key.lower() for key in item} & forbidden)
        assert set(item) == FIXTURE_KEYS


def test_git_attributes_disable_text_conversion_and_diff_for_fixture_root() -> None:
    attributes = (REPOSITORY_ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert attributes.count(ATTRIBUTE_RULE) == 1
