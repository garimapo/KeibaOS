"""Canonical Phase110 receipt digest and complete population semantics."""

from dataclasses import FrozenInstanceError, replace
from datetime import timedelta

import pytest

from scripts.simulation.nar_identity_complete_entry_persistence import (
    NARIdentityCompleteReceiptV1, NARIdentityPersistedEntryV1,
    canonical_json, parse_receipt,
)
from scripts.simulation.nar_trusted_deba_acquisition import canonical_deba_url
from test_nar_trusted_deba_acquisition import T0


def receipt(entries=None):
    if entries is None:
        entries = (
            NARIdentityPersistedEntryV1("nar:20250101:21:1:entry:1", 10, 1,
                                        "nar:horse:100", "ADOPTED_EXISTING_INTERNAL_ID"),
            NARIdentityPersistedEntryV1("nar:20250101:21:1:entry:2", 11, 2,
                                        None, "ISSUED_IDENTITY_ONLY_INTERNAL_ID"),
        )
    return NARIdentityCompleteReceiptV1(
        "nar:20250101:21:1", 1, canonical_deba_url("nar:20250101:21:1"),
        "declaration", "receipt", "capture", "a" * 64,
        T0, T0 + timedelta(minutes=20), T0 + timedelta(minutes=21), entries)


def test_canonical_roundtrip_and_immutable_content_identity():
    value = receipt()
    canonical = canonical_json(value.payload())
    assert parse_receipt(canonical, value.receipt_id) == value
    assert len(value.receipt_id) == 64 and len(value.population_sha256) == 64
    with pytest.raises(FrozenInstanceError):
        value.race_id = 2
    assert replace(value, race_id=2).receipt_id != value.receipt_id
    assert replace(value, phase111_receipt_id="other").receipt_id != value.receipt_id


def test_population_order_count_and_forward_reverse_uniqueness():
    value = receipt()
    with pytest.raises(ValueError):
        receipt(tuple(reversed(value.entries)))
    with pytest.raises(ValueError):
        receipt((value.entries[0], replace(value.entries[1], horse_id=10)))
    with pytest.raises(ValueError):
        receipt((value.entries[0], replace(value.entries[1], external_entry_id=value.entries[0].external_entry_id)))
    with pytest.raises(ValueError):
        receipt((value.entries[0], replace(value.entries[1], horse_no=1)))


def test_receipt_rejects_post_cutoff_and_noncanonical_reload():
    value = receipt()
    with pytest.raises(ValueError):
        replace(value, observed_at=T0 + timedelta(minutes=21))
    with pytest.raises(ValueError):
        parse_receipt(canonical_json(value.payload()), "0" * 64)
    with pytest.raises(ValueError):
        parse_receipt(canonical_json(value.payload()) + " ", value.receipt_id)
