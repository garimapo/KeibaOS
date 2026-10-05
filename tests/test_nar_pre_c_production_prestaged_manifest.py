"""Phase112 values bind all Phase109 entries without status or availability inference."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.simulation.nar_pre_c_production_prestaged_manifest import (
    NARPreCProductionPrestagedAuthorityV1,
    NARPreCProductionPrestagedAvailabilityReceiptV1,
    NARPreCProductionPrestagingError,
    manifest_from_phase109,
    parse_availability,
    parse_manifest,
)
from scripts.simulation.nar_production_mapping_authority import NARProductionMappingEntryV1
from test_sqlite_nar_production_mapping_repository import close_all, publish, ready


def test_manifest_is_exact_phase109_population_and_has_no_availability_field():
    env, connection, source, repo = ready()
    try:
        upstream = publish(repo, env, source)
        manifest = manifest_from_phase109(upstream)
        assert manifest.phase109_receipt_id == upstream.receipt_id
        assert manifest.external_race_id == upstream.external_race_id
        assert manifest.internal_race_id == upstream.internal_race_id
        assert manifest.prediction_cutoff == upstream.prediction_cutoff
        assert manifest.phase109_issued_at == upstream.issued_at
        assert manifest.entries == upstream.entries
        assert manifest.mapping_population_count == len(upstream.entries)
        assert manifest.mapping_population_sha256 == upstream.mapping_population_sha256
        assert "available_at" not in manifest.payload()
        assert parse_manifest(manifest.canonical_json(), manifest.identity) == manifest
        assert manifest_from_phase109(repo.load_receipt(receipt_id=upstream.receipt_id)).identity == manifest.identity
        assert connection.execute("SELECT count(*) FROM nar_identity_complete_denials").fetchone() == (3,)
    finally:
        close_all(env, connection)


def test_availability_is_separate_content_addressed_utc_receipt():
    env, connection, source, repo = ready()
    try:
        manifest = manifest_from_phase109(publish(repo, env, source))
        time = manifest.phase109_issued_at + timedelta(seconds=1)
        receipt = NARPreCProductionPrestagedAvailabilityReceiptV1(
            manifest.identity, manifest.phase109_receipt_id, time)
        assert receipt.payload()["available_at"] == time.isoformat()
        assert parse_availability(receipt.canonical_json(), receipt.identity) == receipt
        assert NARPreCProductionPrestagedAuthorityV1(manifest, receipt).availability_receipt == receipt
        assert receipt.identity == NARPreCProductionPrestagedAvailabilityReceiptV1(
            manifest.identity, manifest.phase109_receipt_id, time).identity
        with pytest.raises(NARPreCProductionPrestagingError, match="UTC"):
            NARPreCProductionPrestagedAvailabilityReceiptV1(
                manifest.identity, manifest.phase109_receipt_id, datetime.now())
        with pytest.raises(NARPreCProductionPrestagingError, match="prestaging pair"):
            NARPreCProductionPrestagedAuthorityV1(
                manifest, NARPreCProductionPrestagedAvailabilityReceiptV1(
                    manifest.identity, manifest.phase109_receipt_id,
                    manifest.phase109_issued_at - timedelta(microseconds=1)))
        with pytest.raises(NARPreCProductionPrestagingError):
            parse_availability(receipt.canonical_json().replace("+00:00", "+01:00"), receipt.identity)
    finally:
        close_all(env, connection)


@pytest.mark.parametrize("manifest_identity", [
    "nar-pre-c-production-prestaged-input-manifest-v1:extra:" + "a" * 64,
    "nar-pre-c-production-prestaged-input-manifest-v1:" + "a" * 63,
    "nar-pre-c-production-prestaged-input-manifest-v1:" + "a" * 65,
    "nar-pre-c-production-prestaged-input-manifest-v1:" + "A" * 64,
])
def test_availability_rejects_noncanonical_manifest_identity_shape(manifest_identity):
    with pytest.raises(NARPreCProductionPrestagingError):
        NARPreCProductionPrestagedAvailabilityReceiptV1(
            manifest_identity, "0" * 64, datetime(2026, 7, 4, tzinfo=timezone.utc),
        )


def test_missing_extra_reordered_duplicate_and_digest_mismatch_fail_closed():
    env, connection, source, repo = ready()
    try:
        original = manifest_from_phase109(publish(repo, env, source))
        entries = original.entries
        invalid = (
            entries[:-1],
            entries + (NARProductionMappingEntryV1(
                original.external_race_id + ":entry:999", 999, 999),),
            tuple(reversed(entries)),
            (entries[0], NARProductionMappingEntryV1(
                entries[0].external_entry_id, entries[1].race_entry_id, entries[1].horse_no), entries[2]),
            (entries[0], NARProductionMappingEntryV1(
                entries[1].external_entry_id, entries[0].race_entry_id, entries[1].horse_no), entries[2]),
            (entries[0], NARProductionMappingEntryV1(
                entries[1].external_entry_id, entries[1].race_entry_id, entries[0].horse_no), entries[2]),
        )
        for candidate in invalid:
            with pytest.raises(NARPreCProductionPrestagingError):
                replace(original, entries=candidate)
        with pytest.raises(NARPreCProductionPrestagingError, match="digest/count"):
            replace(original, mapping_population_sha256="0" * 64)
        with pytest.raises(NARPreCProductionPrestagingError, match="digest/count"):
            replace(original, mapping_population_count=2)
        with pytest.raises(NARPreCProductionPrestagingError, match="corrupt"):
            parse_manifest(original.canonical_json().replace('"NAR"', '"JRA"'), original.identity)
    finally:
        close_all(env, connection)
