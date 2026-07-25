"""Protocol boundary for resolving prediction horse selections to race entries."""

from __future__ import annotations

from typing import Protocol, Sequence


class RaceEntrySelectionResolver(Protocol):
    """Resolve one race's horse-ID selection to race-entry IDs in the same order."""

    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        """Resolve the supplied horse IDs for the specified race without reordering."""
        ...
