"""Phase109 content values never self-authorize without persisted Phase110/111."""

from datetime import timedelta

import pytest

from scripts.simulation.nar_production_mapping_authority import (
    NARProductionMappingEntryV1, NARProductionMappingError,
    NARProductionMappingReceiptV1, _canonical_json, parse_mapping_receipt,
    receipt_from_phase110,
)
from test_sqlite_nar_identity_complete_entry_repository import (
    close_all, persist, repository_env,
)


def test_canonical_complete_receipt_round_trip_and_digest():
    env, result, connection, repo = repository_env()
    try:
        source = persist(repo, env, result)
        value = receipt_from_phase110(source=source, issued_at=source.issued_at + timedelta(seconds=1))
        assert value.payload()["schema"] == "nar-production-mapping-receipt-v1"
        assert value.payload()["organization"] == "NAR"
        assert value.payload()["source_system"] == "nar_official"
        assert len(value.entries) == len(source.entries) == 3
        assert [e.race_entry_id for e in value.entries] == [e.horse_id for e in source.entries]
        assert parse_mapping_receipt(_canonical_json(value.payload()), value.receipt_id) == value
        assert receipt_from_phase110(source=source, issued_at=value.issued_at).receipt_id == value.receipt_id
    finally:
        close_all(env, connection)


def test_mapping_is_bijective_and_chronological():
    env, result, connection, repo = repository_env()
    try:
        source = persist(repo, env, result)
        value = receipt_from_phase110(source=source, issued_at=source.issued_at)
        with pytest.raises(NARProductionMappingError, match="chronology"):
            receipt_from_phase110(source=source, issued_at=source.issued_at - timedelta(seconds=1))
        duplicate = (value.entries[0],
                     NARProductionMappingEntryV1(value.entries[1].external_entry_id,
                                                 value.entries[0].race_entry_id,
                                                 value.entries[1].horse_no))
        with pytest.raises(NARProductionMappingError, match="non-bijective"):
            NARProductionMappingReceiptV1(
                value.external_race_id, value.internal_race_id, value.canonical_deba_url,
                value.phase110_receipt_id, value.phase110_population_sha256, 2,
                value.phase110_issued_at, value.phase111_declaration_id,
                value.phase111_receipt_id, value.phase111_capture_id,
                value.response_sha256, value.observed_at, value.prediction_cutoff,
                value.issued_at, duplicate)
    finally:
        close_all(env, connection)


def test_manual_value_does_not_publish_v019_authority():
    env, result, connection, repo = repository_env()
    try:
        source = persist(repo, env, result)
        receipt = receipt_from_phase110(source=source, issued_at=source.issued_at)
        assert connection.execute("SELECT count(*) FROM nar_production_mapping_receipts").fetchone() == (0,)
        assert receipt.receipt_id
    finally:
        close_all(env, connection)
