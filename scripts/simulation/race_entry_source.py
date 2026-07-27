"""Protocol boundary for resolving prediction horse IDs to race-entry IDs."""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence


class RaceEntrySource(Protocol):
    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        ...
