"""Controlled two-stage Phase112 companion archive; main V019 is read-only."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Callable

from scripts.simulation import nar_pre_c_production_prestaged_manifest_archive_migration as schema
from scripts.simulation.nar_pre_c_production_prestaged_manifest import (
    NARPreCProductionPrestagedAuthorityV1,
    NARPreCProductionPrestagedAvailabilityReceiptV1,
    NARPreCProductionPrestagedInputManifestV1,
    NARPreCProductionPrestagingError,
    manifest_from_phase109,
    parse_availability,
    parse_manifest,
)
from scripts.simulation.repositories.sqlite_nar_production_mapping_repository import (
    SQLiteNARProductionMappingRepository,
)


class SQLiteNARPreCProductionPrestagedManifestArchive:
    def __init__(self, *, connection: sqlite3.Connection):
        schema.require_phase112_schema(connection)
        if connection.in_transaction:
            raise NARPreCProductionPrestagingError("idle companion connection required")
        self._connection = connection

    @staticmethod
    def _manifest_row(value: NARPreCProductionPrestagedInputManifestV1) -> tuple[object, ...]:
        return (
            value.identity, value.phase109_receipt_id, value.organization,
            value.source_system, value.external_race_id, value.internal_race_id,
            value.prediction_cutoff.isoformat(), value.mapping_population_count,
            value.mapping_population_sha256, value.canonical_json(),
        )

    @staticmethod
    def _availability_row(
        value: NARPreCProductionPrestagedAvailabilityReceiptV1,
    ) -> tuple[object, ...]:
        return (value.identity, value.manifest_identity, value.phase109_receipt_id,
                value.available_at.isoformat(), value.canonical_json())

    def load_manifest(self, *, identity: str) -> NARPreCProductionPrestagedInputManifestV1 | None:
        schema.require_phase112_schema(self._connection)
        row = self._connection.execute(
            f"SELECT * FROM {schema.MANIFESTS} WHERE identity=?", (identity,),
        ).fetchone()
        if row is None:
            return None
        value = parse_manifest(row[-1], identity)
        if tuple(row) != self._manifest_row(value):
            raise NARPreCProductionPrestagingError("manifest SQL projection differs")
        return value

    def load_availability(
        self, *, manifest_identity: str,
    ) -> NARPreCProductionPrestagedAvailabilityReceiptV1 | None:
        schema.require_phase112_schema(self._connection)
        row = self._connection.execute(
            f"SELECT * FROM {schema.AVAILABILITY} WHERE manifest_identity=?",
            (manifest_identity,),
        ).fetchone()
        if row is None:
            return None
        value = parse_availability(row[-1], row[0])
        if tuple(row) != self._availability_row(value):
            raise NARPreCProductionPrestagingError("availability SQL projection differs")
        return value

    @staticmethod
    def _source(
        repository: SQLiteNARProductionMappingRepository, receipt_id: str,
    ):
        if type(repository) is not SQLiteNARProductionMappingRepository:
            raise NARPreCProductionPrestagingError("exact Phase109 repository required")
        if repository._connection.in_transaction:
            raise NARPreCProductionPrestagingError("committed Phase109 read required")
        return repository.load_receipt(receipt_id=receipt_id)

    def load_authority(
        self, *, manifest_identity: str,
        phase109_repository: SQLiteNARProductionMappingRepository,
    ) -> NARPreCProductionPrestagedAuthorityV1:
        manifest = self.load_manifest(identity=manifest_identity)
        if manifest is None:
            raise NARPreCProductionPrestagingError("exact manifest missing")
        receipt = self.load_availability(manifest_identity=manifest_identity)
        if receipt is None:
            raise NARPreCProductionPrestagingError("manifest has no availability authority")
        source = self._source(phase109_repository, manifest.phase109_receipt_id)
        if manifest_from_phase109(source) != manifest:
            raise NARPreCProductionPrestagingError("Phase109/112 complete mapping differs")
        return NARPreCProductionPrestagedAuthorityV1(manifest, receipt)

    def _stage_manifest(self, manifest: NARPreCProductionPrestagedInputManifestV1) -> None:
        c = self._connection
        if c.in_transaction:
            raise NARPreCProductionPrestagingError("caller transaction not accepted")
        schema.require_phase112_schema(c)
        c.execute("BEGIN IMMEDIATE")
        try:
            rows = c.execute(
                f"SELECT identity FROM {schema.MANIFESTS} WHERE phase109_receipt_id=? "
                "OR (organization=? AND source_system=? AND external_race_id=? "
                "AND prediction_cutoff=?) "
                "OR (organization=? AND source_system=? AND internal_race_id=? "
                "AND prediction_cutoff=?)",
                (manifest.phase109_receipt_id, manifest.organization, manifest.source_system,
                 manifest.external_race_id, manifest.prediction_cutoff.isoformat(),
                 manifest.organization, manifest.source_system, manifest.internal_race_id,
                 manifest.prediction_cutoff.isoformat()),
            ).fetchall()
            if rows:
                if len(rows) != 1 or rows[0][0] != manifest.identity:
                    raise NARPreCProductionPrestagingError("contradictory target prestaging")
                existing = self.load_manifest(identity=manifest.identity)
                if existing != manifest:
                    raise NARPreCProductionPrestagingError("existing manifest differs")
            else:
                row = self._manifest_row(manifest)
                c.execute(
                    f"INSERT INTO {schema.MANIFESTS} VALUES({','.join('?' for _ in row)})",
                    row,
                )
            c.commit()
        except BaseException:
            c.rollback()
            raise
        if self.load_manifest(identity=manifest.identity) != manifest:
            raise NARPreCProductionPrestagingError("committed manifest did not exact-reload")

    def _stage_availability(
        self, *, manifest: NARPreCProductionPrestagedInputManifestV1,
        utc_clock: Callable[[], datetime],
    ) -> None:
        c = self._connection
        if c.in_transaction:
            raise NARPreCProductionPrestagingError("caller transaction not accepted")
        schema.require_phase112_schema(c)
        c.execute("BEGIN IMMEDIATE")
        try:
            row = c.execute(
                f"SELECT identity FROM {schema.AVAILABILITY} WHERE manifest_identity=?",
                (manifest.identity,),
            ).fetchone()
            if row is None:
                # This clock call is deliberately inside the second write transaction.
                available_at = utc_clock()
                receipt = NARPreCProductionPrestagedAvailabilityReceiptV1(
                    manifest.identity, manifest.phase109_receipt_id, available_at,
                )
                NARPreCProductionPrestagedAuthorityV1(manifest, receipt)
                data = self._availability_row(receipt)
                c.execute(
                    f"INSERT INTO {schema.AVAILABILITY} VALUES({','.join('?' for _ in data)})",
                    data,
                )
            else:
                existing = self.load_availability(manifest_identity=manifest.identity)
                if existing is None:
                    raise NARPreCProductionPrestagingError("availability row vanished")
                NARPreCProductionPrestagedAuthorityV1(manifest, existing)
            c.commit()
        except BaseException:
            c.rollback()
            raise

    def publish(
        self, *, phase109_repository: SQLiteNARProductionMappingRepository,
        phase109_receipt_id: str, expected_external_race_id: str,
        expected_prediction_cutoff: datetime, utc_clock: Callable[[], datetime],
    ) -> NARPreCProductionPrestagedAuthorityV1:
        if (type(phase109_receipt_id) is not str or type(expected_external_race_id) is not str
                or type(expected_prediction_cutoff) is not datetime or not callable(utc_clock)):
            raise NARPreCProductionPrestagingError("exact receipt/target/cutoff/clock required")
        source = self._source(phase109_repository, phase109_receipt_id)
        if (source.external_race_id != expected_external_race_id
                or source.prediction_cutoff != expected_prediction_cutoff):
            raise NARPreCProductionPrestagingError("expected Phase109 target/cutoff differs")
        manifest = manifest_from_phase109(source)
        self._stage_manifest(manifest)
        self._stage_availability(manifest=manifest, utc_clock=utc_clock)
        authority = self.load_authority(
            manifest_identity=manifest.identity, phase109_repository=phase109_repository,
        )
        if authority.manifest != manifest:
            raise NARPreCProductionPrestagingError("published authority differs")
        return authority
