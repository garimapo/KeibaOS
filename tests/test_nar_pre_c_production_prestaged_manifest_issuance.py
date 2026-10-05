"""Only exact accepted Phase109 receipts can enter Phase112 issuance."""

import inspect
import sqlite3
from datetime import datetime, timedelta

import pytest

from scripts.simulation import nar_pre_c_production_prestaged_manifest_archive_migration as schema
from scripts.simulation.nar_pre_c_production_prestaged_manifest import NARPreCProductionPrestagingError
from scripts.simulation.nar_pre_c_production_prestaged_manifest_issuance import (
    issue_nar_pre_c_production_prestaged_authority,
)
from scripts.simulation.sqlite_nar_pre_c_production_prestaged_manifest_archive import (
    SQLiteNARPreCProductionPrestagedManifestArchive,
)
from test_sqlite_nar_production_mapping_repository import close_all, publish, ready


def prepared():
    env, main, source, repo = ready()
    receipt = publish(repo, env, source)
    companion = sqlite3.connect(":memory:")
    schema.apply(companion)
    archive = SQLiteNARPreCProductionPrestagedManifestArchive(connection=companion)
    return env, main, repo, receipt, companion, archive


def issue(repo, receipt, archive, **kwargs):
    return issue_nar_pre_c_production_prestaged_authority(
        phase109_repository=repo, companion_archive=archive,
        phase109_receipt_id=receipt.receipt_id,
        expected_external_race_id=receipt.external_race_id,
        expected_prediction_cutoff=receipt.prediction_cutoff,
        utc_clock=lambda: receipt.issued_at + timedelta(seconds=1), **kwargs,
    )


def test_issuer_has_no_caller_mapping_or_phase111_input_and_no_extra_send():
    env, main, repo, receipt, companion, archive = prepared()
    try:
        parameters = inspect.signature(issue_nar_pre_c_production_prestaged_authority).parameters
        assert set(parameters) == {
            "phase109_repository", "companion_archive", "phase109_receipt_id",
            "expected_external_race_id", "expected_prediction_cutoff", "utc_clock"}
        assert not any("phase111" in name or "capture" in name or "mapping" in name
                       for name in parameters)
        before_urls = tuple(env.transport.urls)
        before_changes = main.total_changes
        authority = issue(repo, receipt, archive)
        assert tuple(env.transport.urls) == before_urls
        assert main.total_changes == before_changes
        assert authority.manifest.entries == receipt.entries
        assert "available_at" not in authority.manifest.payload()
        assert "available_at" in authority.availability_receipt.payload()
        with pytest.raises(TypeError):
            issue_nar_pre_c_production_prestaged_authority(
                phase109_repository=repo, companion_archive=archive,
                phase109_receipt_id=receipt.receipt_id,
                expected_external_race_id=receipt.external_race_id,
                expected_prediction_cutoff=receipt.prediction_cutoff,
                utc_clock=lambda: receipt.issued_at, entry_mapping={"forged": 999})
    finally:
        companion.close()
        close_all(env, main)


def test_wrong_target_cutoff_or_missing_receipt_cannot_stage_anything():
    env, main, repo, receipt, companion, archive = prepared()
    try:
        for kwargs in ({"expected_external_race_id": "nar:wrong"},
                       {"expected_prediction_cutoff": receipt.prediction_cutoff + timedelta(seconds=1)},
                       {"phase109_receipt_id": "0" * 64}):
            arguments = dict(phase109_repository=repo, companion_archive=archive,
                             phase109_receipt_id=receipt.receipt_id,
                             expected_external_race_id=receipt.external_race_id,
                             expected_prediction_cutoff=receipt.prediction_cutoff,
                             utc_clock=lambda: receipt.issued_at)
            arguments.update(kwargs)
            with pytest.raises(Exception):
                issue_nar_pre_c_production_prestaged_authority(**arguments)
        assert companion.execute(f"SELECT count(*) FROM {schema.MANIFESTS}").fetchone() == (0,)
        assert companion.execute(f"SELECT count(*) FROM {schema.AVAILABILITY}").fetchone() == (0,)
    finally:
        companion.close()
        close_all(env, main)


@pytest.mark.parametrize("corrupt", ["v018", "v019"])
def test_inactive_upstream_schema_fails_closed(corrupt):
    env, main, repo, receipt, companion, archive = prepared()
    try:
        if corrupt == "v018":
            main.execute("DROP TRIGGER nar_identity_complete_entries_no_update")
        else:
            main.execute("DROP TRIGGER nar_production_mapping_receipts_no_update")
        main.commit()
        with pytest.raises(RuntimeError):
            issue(repo, receipt, archive)
        assert companion.execute(f"SELECT count(*) FROM {schema.MANIFESTS}").fetchone() == (0,)
    finally:
        companion.close()
        close_all(env, main)


@pytest.mark.parametrize("offset", [None, -1])
def test_naive_or_backdated_clock_leaves_only_inert_manifest(offset):
    env, main, repo, receipt, companion, archive = prepared()
    try:
        value = (datetime.now() if offset is None else
                 receipt.issued_at - timedelta(microseconds=1))
        with pytest.raises(NARPreCProductionPrestagingError):
            issue_nar_pre_c_production_prestaged_authority(
                phase109_repository=repo, companion_archive=archive,
                phase109_receipt_id=receipt.receipt_id,
                expected_external_race_id=receipt.external_race_id,
                expected_prediction_cutoff=receipt.prediction_cutoff,
                utc_clock=lambda: value)
        assert companion.execute(f"SELECT count(*) FROM {schema.MANIFESTS}").fetchone() == (1,)
        assert companion.execute(f"SELECT count(*) FROM {schema.AVAILABILITY}").fetchone() == (0,)
        assert not companion.in_transaction
    finally:
        companion.close()
        close_all(env, main)
