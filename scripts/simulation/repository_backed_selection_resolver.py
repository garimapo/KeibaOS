"""Concrete boundary for resolving prediction horse IDs through a race-entry Source."""

from __future__ import annotations

from typing import Mapping, Sequence

from scripts.simulation.race_entry_source import RaceEntrySource
from scripts.simulation.selection_resolver import RaceEntrySelectionResolver


class RepositoryBackedRaceEntrySelectionResolver:
    """Resolve one ordered horse selection through an injected ``RaceEntrySource``."""

    __slots__ = ("_race_entry_source",)

    def __init__(self, *, race_entry_source: RaceEntrySource) -> None:
        source_method = getattr(race_entry_source, "load_race_entry_id_map", None)
        if not callable(source_method):
            raise ValueError("race_entry_source must provide a callable load_race_entry_id_map method")
        self._race_entry_source = race_entry_source

    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        requested_horse_ids = self._validate_request(race_id=race_id, horse_ids=horse_ids)
        mapping = self._race_entry_source.load_race_entry_id_map(
            race_id=race_id,
            horse_ids=requested_horse_ids,
        )
        return self._validate_mapping(mapping=mapping, requested_horse_ids=requested_horse_ids)

    @classmethod
    def _validate_request(cls, *, race_id: object, horse_ids: object) -> tuple[int, ...]:
        if not cls._is_positive_int(race_id):
            raise ValueError("race_id must be a positive int")
        if (
            isinstance(horse_ids, (str, bytes, bytearray, Mapping))
            or not isinstance(horse_ids, Sequence)
        ):
            raise ValueError("horse_ids must be a non-empty Sequence of positive ints")
        requested_horse_ids = tuple(horse_ids)
        if not requested_horse_ids:
            raise ValueError("horse_ids must not be empty")
        if not all(cls._is_positive_int(horse_id) for horse_id in requested_horse_ids):
            raise ValueError("horse_ids must contain only positive ints")
        if len(set(requested_horse_ids)) != len(requested_horse_ids):
            raise ValueError("horse_ids must not contain duplicates")
        return requested_horse_ids

    @classmethod
    def _validate_mapping(
        cls,
        *,
        mapping: object,
        requested_horse_ids: tuple[int, ...],
    ) -> tuple[int, ...]:
        if not isinstance(mapping, Mapping):
            raise ValueError("race_entry_source must return a Mapping")

        mapping_keys = tuple(mapping.keys())
        if not all(cls._is_positive_int(horse_id) for horse_id in mapping_keys):
            raise ValueError("race_entry_source returned invalid horse IDs")
        requested_keys = set(requested_horse_ids)
        returned_keys = set(mapping_keys)
        if returned_keys != requested_keys or len(mapping_keys) != len(requested_horse_ids):
            raise ValueError("race_entry_source did not resolve exactly the requested horse IDs")

        race_entry_ids = tuple(mapping[horse_id] for horse_id in requested_horse_ids)
        if not all(cls._is_positive_int(race_entry_id) for race_entry_id in race_entry_ids):
            raise ValueError("race_entry_source returned invalid race entry IDs")
        if len(set(race_entry_ids)) != len(race_entry_ids):
            raise ValueError("race_entry_source returned duplicate race entry IDs")
        return race_entry_ids

    @staticmethod
    def _is_positive_int(value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool) and value > 0
