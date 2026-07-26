"""Read and write protocol boundaries for persisted simulation bet-plan snapshots."""

from __future__ import annotations

from typing import Protocol

from .bet_plan_identity import SimulationBetPlanIdentity
from .bet_plan_snapshot import SimulationBetPlanSnapshot


class SimulationBetPlanSnapshotSource(Protocol):
    """Load an immutable simulation bet-plan snapshot by its natural identity."""

    def load_snapshot(
        self,
        *,
        identity: SimulationBetPlanIdentity,
    ) -> SimulationBetPlanSnapshot | None:
        ...


class SimulationBetPlanSnapshotRepository(Protocol):
    """Persist an immutable simulation bet-plan snapshot."""

    def save_snapshot(
        self,
        *,
        snapshot: SimulationBetPlanSnapshot,
    ) -> None:
        ...
