from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json

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


def test_digest_is_independently_pinned_canonical_json() -> None:
    seed = build_seed()
    material = {
        "canonical_target_race_card_url": URL,
        "captured_at_utc": "2025-01-05T01:00:00.000000+00:00",
        "dataset_id": "dataset-1",
        "entries": [{
            "entry_order": 0,
            "external_entry_id": RACE + ":entry:1",
            "external_horse_id": "jra:horse:1234567890",
            "horse_no": 1,
            "internal_race_entry_id": 7,
        }],
        "external_race_id": RACE,
        "information_cutoff_utc": "2025-01-05T02:00:00.000000+00:00",
        "internal_race_id": 4,
        "schema_version": 1,
        "target_race_card_capture_id": "jra-capture-v3:" + "b" * 64,
        "target_race_card_response_sha256": "c" * 64,
        "target_race_selection_capture_id": "jra-capture-v4:" + "a" * 64,
    }
    digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assert seed.content_sha256 == digest
    assert seed.seed_id == "jra-race-replay-seed-v1:" + digest


@pytest.mark.parametrize("changes", [
    {"dataset_id": "dataset-2"},
    {
        "external_race_id": "jra:race:2025:06:01:01:01",
        "canonical_target_race_card_url": "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0106202501010120250105%2FAB",
        "entries": (
            JRARaceReplaySeedEntry(
                0, "jra:race:2025:06:01:01:01:entry:1", "jra:horse:1234567890", 1, 7
            ),
        ),
    },
    {"internal_race_id": 5},
    {"target_race_selection_capture_id": "jra-capture-v4:" + "d" * 64},
    {"target_race_card_capture_id": "jra-capture-v3:" + "d" * 64},
    {"target_race_card_response_sha256": "d" * 64},
    {"canonical_target_race_card_url": URL.replace("%2FAB", "%2FAC")},
    {"captured_at": datetime(2025, 1, 5, 1, 1, tzinfo=UTC)},
    {"information_cutoff": datetime(2025, 1, 5, 2, 1, tzinfo=UTC)},
    {"entries": (JRARaceReplaySeedEntry(0, RACE + ":entry:1", "jra:horse:1234567890", 1, 8),)},
])
def test_every_mutable_content_family_participates_in_digest(changes: dict[str, object]) -> None:
    assert build_seed(**changes).content_sha256 != build_seed().content_sha256


def test_timezone_equivalent_instants_have_one_identity() -> None:
    offset = timezone(timedelta(hours=9))
    assert build_seed(
        captured_at=datetime(2025, 1, 5, 10, tzinfo=offset),
        information_cutoff=datetime(2025, 1, 5, 11, tzinfo=offset),
    ) == build_seed()


@pytest.mark.parametrize("field,value", [
    ("dataset_id", ""),
    ("dataset_id", "e\u0301"),
    ("external_race_id", "jra:race:2025:05:01:01:1"),
    ("target_race_selection_capture_id", "jra-capture-v3:" + "a" * 64),
    ("target_race_card_capture_id", "jra-capture-v4:" + "a" * 64),
    ("target_race_card_response_sha256", "A" * 64),
    ("canonical_target_race_card_url", URL.replace("%2FAB", "/AB")),
    ("canonical_target_race_card_url", URL.replace("01052025", "01062025")),
    ("information_cutoff", datetime(2025, 1, 5, 0, tzinfo=UTC)),
    ("entries", ()),
])
def test_seed_rejects_noncanonical_identity(field: str, value: object) -> None:
    with pytest.raises(JRARaceReplaySeedValidationError):
        build_seed(**{field: value})


def test_entry_order_and_race_binding_are_exact() -> None:
    with pytest.raises(JRARaceReplaySeedValidationError):
        build_seed(entries=(JRARaceReplaySeedEntry(0, RACE + ":entry:2", "jra:horse:1234567890", 1, 7),))
    with pytest.raises(JRARaceReplaySeedValidationError):
        build_seed(entries=(JRARaceReplaySeedEntry(1, RACE + ":entry:1", "jra:horse:1234567890", 1, 7),))


@pytest.mark.parametrize("entries", [
    (
        JRARaceReplaySeedEntry(0, RACE + ":entry:2", "jra:horse:1234567890", 2, 7),
        JRARaceReplaySeedEntry(1, RACE + ":entry:1", "jra:horse:1234567891", 1, 8),
    ),
    (
        JRARaceReplaySeedEntry(0, RACE + ":entry:1", "jra:horse:1234567890", 1, 7),
        JRARaceReplaySeedEntry(1, RACE + ":entry:1", "jra:horse:1234567891", 1, 8),
    ),
    (
        JRARaceReplaySeedEntry(0, RACE + ":entry:1", "jra:horse:1234567890", 1, 7),
        JRARaceReplaySeedEntry(1, RACE + ":entry:2", "jra:horse:1234567890", 2, 8),
    ),
    (
        JRARaceReplaySeedEntry(0, RACE + ":entry:1", "jra:horse:1234567890", 1, 7),
        JRARaceReplaySeedEntry(1, RACE + ":entry:2", "jra:horse:1234567891", 2, 7),
    ),
])
def test_entry_duplicates_or_nonascending_order_fail(entries: tuple[JRARaceReplaySeedEntry, ...]) -> None:
    with pytest.raises(JRARaceReplaySeedValidationError):
        build_seed(entries=entries)


def test_malformed_horse_identity_fails() -> None:
    with pytest.raises(JRARaceReplaySeedValidationError):
        JRARaceReplaySeedEntry(0, RACE + ":entry:1", "horse-1", 1, 7)
