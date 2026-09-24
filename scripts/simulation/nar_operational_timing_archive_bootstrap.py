"""Exact known-state migration composition under a held local archive lock."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as activation
from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as v2
from scripts.simulation import nar_operational_timing_runtime_execution_archive_migration as runtime
from scripts.simulation.nar_operational_timing_campaign_lock import NAROperationalTimingCampaignLock


def bootstrap_nar_operational_timing_runtime_archive(
    *, connection: sqlite3.Connection, campaign_lock: NAROperationalTimingCampaignLock,
) -> None:
    if (type(connection) is not sqlite3.Connection or connection.in_transaction
            or type(campaign_lock) is not NAROperationalTimingCampaignLock
            or not campaign_lock.held_by_current_process):
        raise RuntimeError("exact idle connection and held archive lock are required")
    objects = base._objects(connection)
    if objects == {}:
        base.apply_nar_operational_timing_observability_archive_migrations(connection)
        objects = base._objects(connection)
    if objects == base._DDL:
        base.require_nar_operational_timing_observability_archive_schema(connection)
        activation.apply_nar_operational_timing_activation_archive_migrations(connection)
        objects = base._objects(connection)
    if objects == base._DDL | activation._DDL:
        activation.require_nar_operational_timing_activation_archive_schema(connection)
        v2.apply_nar_operational_timing_v2_authority_archive_migrations(connection)
        objects = base._objects(connection)
    if objects == base._DDL | activation._DDL | v2._DDL:
        v2.require_nar_operational_timing_v2_authority_archive_schema(connection)
        runtime.apply_nar_operational_timing_runtime_execution_archive_migrations(connection)
        objects = base._objects(connection)
    runtime.require_nar_operational_timing_runtime_execution_archive_compatible_schema(connection)
