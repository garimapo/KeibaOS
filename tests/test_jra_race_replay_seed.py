from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import datetime, timezone

import pytest

import scripts.simulation.jra_race_replay_seed as module
from scripts.simulation.jra_race_replay_seed import (
    JRARaceReplaySeed,
    JRARaceReplaySeedEntry,
    JRARaceReplaySeedValidationError,
    build_jra_race_replay_seed,
)


UTC = timezone.utc
RACE = "jra:race:2025:05:01:01:01"
URL = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105%2FAB"


def build_seed(**changes: object) -> JRARaceReplaySeed:
    values: dict[str, object] = {
        "dataset_id": "dataset-1",
        "external_race_id": RACE,
        "internal_race_id": 4,
        "target_race_selection_capture_id": "jra-capture-v4:" + "a" * 64,
        "target_race_card_capture_id": "jra-capture-v3:" + "b" * 64,
        "target_race_card_response_sha256": "c" * 64,
        "canonical_target_race_card_url": URL,
        "captured_at": datetime(2025, 1, 5, 1, tzinfo=UTC),
        "information_cutoff": datetime(2025, 1, 5, 2, tzinfo=UTC),
        "entries": (
            JRARaceReplaySeedEntry(0, RACE + ":entry:1", "jra:horse:1234567890", 1, 7),
        ),
    }
    values.update(changes)
    return build_jra_race_replay_seed(**values)  # type: ignore[arg-type]


def test_public_surface_and_deterministic_identity() -> None:
    assert module.__all__ == (
        "JRARaceReplaySeedError", "JRARaceReplaySeedValidationError", "JRARaceReplaySeedEntry",
        "JRARaceReplaySeed", "build_jra_race_replay_seed", "is_jra_race_replay_seed_id",
        "jra_race_replay_seed_datetime_text",
    )
    first, second = build_seed(), build_seed()
    assert is_dataclass(first) and first.__dataclass_params__.frozen and hasattr(first, "__slots__")
    assert first == second
    assert first.seed_id == "jra-race-replay-seed-v1:" + first.content_sha256
    with pytest.raises(FrozenInstanceError):
        first.dataset_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("field,value", [
    ("dataset_id", ""),
    ("external_race_id", "jra:race:2025:05:01:01:1"),
    ("target_race_selection_capture_id", "jra-capture-v3:" + "a" * 64),
    ("canonical_target_race_card_url", URL.replace("%2FAB", "/AB")),
])
def test_seed_rejects_noncanonical_identity(field: str, value: object) -> None:
    with pytest.raises(JRARaceReplaySeedValidationError):
        build_seed(**{field: value})


def test_entry_order_and_race_binding_are_exact() -> None:
    with pytest.raises(JRARaceReplaySeedValidationError):
        build_seed(entries=(JRARaceReplaySeedEntry(0, RACE + ":entry:2", "jra:horse:1234567890", 1, 7),))
    with pytest.raises(JRARaceReplaySeedValidationError):
        build_seed(entries=(JRARaceReplaySeedEntry(1, RACE + ":entry:1", "jra:horse:1234567890", 1, 7),))
