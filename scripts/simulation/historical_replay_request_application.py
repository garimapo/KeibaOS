"""Thin request-file boundary for exact SQLite historical replay."""

from __future__ import annotations

from pathlib import Path

from scripts.simulation.historical_replay_request_document import (
    load_historical_replay_request_document,
)
from scripts.simulation.models import SimulationSummary
from scripts.simulation.sqlite_historical_replay_application import (
    run_sqlite_historical_replay,
)


__all__ = (
    "run_historical_replay_request",
)


def run_historical_replay_request(
    *,
    request_path: str | Path,
) -> SimulationSummary:
    """Load one exact replay request and return its SQLite-runner summary."""

    document = load_historical_replay_request_document(
        request_path=request_path,
    )
    return run_sqlite_historical_replay(
        document=document,
    )
