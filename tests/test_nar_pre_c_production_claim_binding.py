"""Canonical content is not, by itself, independently qualified authority."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timezone
import hashlib
import json

import pytest

from scripts.simulation.nar_pre_c_production_claim_binding import (
    NARPreCProductionClaimBindingV1 as Value, NARPreCProductionClaimBindingError as Error,
    PREFIX, _PREFIXES, parse_binding,
)


def content():
    return Value(**{name: prefix + "a" * 64 for name, prefix in _PREFIXES.items()},
                 organization="NAR", source_system="nar_official", external_race_id="nar:20250101:21:1",
                 internal_race_id=1, prediction_cutoff=datetime(2025, 1, 1, tzinfo=timezone.utc))


def test_exact_thirteen_fields_deterministic_content_address_and_frozen_value():
    value = content()
    assert {f.name for f in fields(Value)} == {
        "claim_identity", "runtime_binding_identity", "session_identity", "campaign_readiness_receipt_identity",
        "phase112_manifest_identity", "phase112_availability_receipt_identity", "phase109_receipt_id",
        "organization", "source_system", "external_race_id", "internal_race_id", "prediction_cutoff", "schema_version"}
    assert value.identity == PREFIX + hashlib.sha256(value.canonical_json().encode()).hexdigest()
    assert parse_binding(value.canonical_json(), value.identity) == value
    assert content() == value
    assert replace(value, internal_race_id=2).identity != value.identity
    with pytest.raises(FrozenInstanceError):
        value.internal_race_id = 2
    for forbidden in ("entry_mapping", "horse_ids", "available_at", "issued_at", "bound_at", "started_at",
                      "capability", "root", "dataset_identity", "target_set_sha256", "cutoff_plan_sha256"):
        assert forbidden not in value.payload()
        assert not hasattr(value, forbidden)


@pytest.mark.parametrize("key,value", [
    ("organization", "JRA"), ("source_system", "caller"), ("schema_version", 2),
    ("schema_version", True), ("internal_race_id", True), ("internal_race_id", 0),
    ("external_race_id", "nar:20250230:21:1"), ("external_race_id", "nar:20250101:021:1"),
    ("prediction_cutoff", datetime(2025, 1, 1)),
])
def test_scope_is_exact(key, value):
    with pytest.raises(Error):
        replace(content(), **{key: value})


@pytest.mark.parametrize("suffix", ["A" * 64, "a" * 63, "a" * 65, "extra:" + "a" * 64])
@pytest.mark.parametrize("key", list(_PREFIXES))
def test_all_upstream_identity_shapes_are_exact(key, suffix):
    with pytest.raises(Error):
        replace(content(), **{key: _PREFIXES[key] + suffix})


@pytest.mark.parametrize("corruption", ["extra", "missing", "pretty", "digest"])
def test_exact_parse_rejects_payload_shape_noncanonical_json_or_wrong_digest(corruption):
    value = content()
    payload = value.payload()
    expected = value.identity
    if corruption == "extra":
        payload["execution_allowed"] = True
    if corruption == "missing":
        del payload["claim_identity"]
    if corruption == "digest":
        expected = PREFIX + "0" * 64
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if corruption == "pretty":
        raw = json.dumps(payload, indent=2)
    with pytest.raises(Error):
        parse_binding(raw, expected)
