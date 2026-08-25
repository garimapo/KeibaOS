"""Exact historical race-entry selection without identity translation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence as _Sequence
from dataclasses import dataclass
from typing import Sequence


__all__ = (
    "ExactRaceEntrySelectionResolver",
)


@dataclass(frozen=True, slots=True)
class ExactRaceEntrySelectionResolver:
    """Accept only already-canonical internal race-entry IDs for one race."""

    race_id: int
    allowed_race_entry_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        if type(self.race_id) is not int or self.race_id <= 0:
            raise ValueError("race_id must be a positive int")
        if type(self.allowed_race_entry_ids) is not tuple:
            raise ValueError("allowed_race_entry_ids must be a tuple")
        if not self.allowed_race_entry_ids:
            raise ValueError("allowed_race_entry_ids must not be empty")
        if any(
            type(value) is not int or value <= 0
            for value in self.allowed_race_entry_ids
        ):
            raise ValueError("allowed_race_entry_ids must contain positive ints")
        if len(set(self.allowed_race_entry_ids)) != len(self.allowed_race_entry_ids):
            raise ValueError("allowed_race_entry_ids must not contain duplicates")

    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        """Validate and return the supplied exact race-entry IDs in order."""

        if type(race_id) is not int or race_id <= 0:
            raise ValueError("race_id must be a positive int")
        if race_id != self.race_id:
            raise ValueError("race_id does not match the resolver race_id")
        if (
            isinstance(horse_ids, str | bytes | bytearray | Mapping)
            or not isinstance(horse_ids, _Sequence)
        ):
            raise ValueError("horse_ids must be a non-string, non-mapping Sequence")
        requested = tuple(horse_ids)
        if not requested:
            raise ValueError("horse_ids must not be empty")
        if any(type(value) is not int or value <= 0 for value in requested):
            raise ValueError("horse_ids must contain positive ints")
        if len(set(requested)) != len(requested):
            raise ValueError("horse_ids must not contain duplicates")
        if any(value not in self.allowed_race_entry_ids for value in requested):
            raise ValueError("horse_ids must be allowlisted race-entry IDs")
        return requested
