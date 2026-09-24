"""Exact Phase105 schema bootstrap under the existing process-wide archive lock."""

from __future__ import annotations

import sqlite3

from scripts.simulation import nar_operational_timing_observability_archive_migration as base
from scripts.simulation import nar_operational_timing_activation_archive_migration as activation
from scripts.simulation import nar_operational_timing_v2_authority_archive_migration as v2
from scripts.simulation import nar_operational_timing_runtime_execution_archive_migration as runtime
from scripts.simulation import nar_operational_timing_attempt_archive_migration as attempt
from scripts.simulation.nar_operational_timing_archive_bootstrap import bootstrap_nar_operational_timing_runtime_archive
from scripts.simulation.nar_operational_timing_campaign_lock import NAROperationalTimingCampaignLock


def bootstrap_nar_operational_timing_attempt_archive(
    *, connection: sqlite3.Connection, campaign_lock: NAROperationalTimingCampaignLock,
) -> None:
    if (type(connection) is not sqlite3.Connection or connection.in_transaction
            or type(campaign_lock) is not NAROperationalTimingCampaignLock
            or not campaign_lock.held_by_current_process):
        raise RuntimeError("Phase105 bootstrap requires exact idle connection and held campaign lock")
    objects = base._objects(connection)
    known_before = ({}, base._DDL, base._DDL | activation._DDL,
                    base._DDL | activation._DDL | v2._DDL,
                    base._DDL | activation._DDL | v2._DDL | runtime._DDL)
    if objects in known_before:
        bootstrap_nar_operational_timing_runtime_archive(connection=connection, campaign_lock=campaign_lock)
        attempt.apply_nar_operational_timing_attempt_archive_migrations(connection)
    elif objects != base._DDL | activation._DDL | v2._DDL | runtime._DDL | attempt._DDL:
        raise RuntimeError("Phase105 archive topology is partial or unknown")
    attempt.require_nar_operational_timing_attempt_archive_schema(connection)
