"""Contract tests for the immutable simulation bet plan identity."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
import unittest

from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity


UTC = timezone.utc
JST = timezone(timedelta(hours=9))
HASH = "0123456789abcdef" * 4


def identity(**overrides: object) -> SimulationBetPlanIdentity:
    values: dict[str, object] = {
        "run_id": "run-001",
        "race_id": 101,
        "strategy_id": "strategy-a",
        "strategy_config_hash": HASH,
        "information_cutoff": datetime(2026, 7, 24, 9, 0, tzinfo=UTC),
    }
    values.update(overrides)
    return SimulationBetPlanIdentity(**values)  # type: ignore[arg-type]


class SimulationBetPlanIdentityTest(unittest.TestCase):
    def test_constructs_with_valid_fields(self) -> None:
        value = identity()
        self.assertEqual(value.run_id, "run-001")
        self.assertEqual(value.race_id, 101)
        self.assertEqual(value.strategy_id, "strategy-a")
        self.assertEqual(value.strategy_config_hash, HASH)
        self.assertEqual(value.information_cutoff, datetime(2026, 7, 24, 9, 0, tzinfo=UTC))

    def test_preserves_nonempty_run_id_without_normalization(self) -> None:
        value = identity(run_id=" run-001 ")
        self.assertEqual(value.run_id, " run-001 ")

    def test_preserves_nonempty_strategy_id_without_normalization(self) -> None:
        value = identity(strategy_id=" Strategy-A ")
        self.assertEqual(value.strategy_id, " Strategy-A ")

    def test_accepts_non_uuid_run_id(self) -> None:
        self.assertEqual(identity(run_id="local-run").run_id, "local-run")

    def test_rejects_empty_or_blank_run_id(self) -> None:
        for value in ("", "   "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    identity(run_id=value)

    def test_rejects_non_string_run_id(self) -> None:
        with self.assertRaises(ValueError):
            identity(run_id=123)

    def test_accepts_positive_integer_race_id(self) -> None:
        self.assertEqual(identity(race_id=1).race_id, 1)

    def test_rejects_zero_and_negative_race_id(self) -> None:
        for value in (0, -1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    identity(race_id=value)

    def test_rejects_boolean_race_id(self) -> None:
        with self.assertRaises(ValueError):
            identity(race_id=True)

    def test_rejects_non_integer_race_id(self) -> None:
        for value in ("101", 101.0, None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    identity(race_id=value)

    def test_rejects_empty_or_blank_strategy_id(self) -> None:
        for value in ("", "   "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    identity(strategy_id=value)

    def test_rejects_non_string_strategy_id(self) -> None:
        with self.assertRaises(ValueError):
            identity(strategy_id=123)

    def test_accepts_lowercase_sha256_hex(self) -> None:
        self.assertEqual(identity(strategy_config_hash="0" * 64).strategy_config_hash, "0" * 64)

    def test_rejects_empty_blank_and_non_string_config_hash(self) -> None:
        for value in ("", "   ", 123, b"0" * 64):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    identity(strategy_config_hash=value)

    def test_rejects_wrong_length_config_hash(self) -> None:
        for value in ("0" * 63, "0" * 65):
            with self.subTest(length=len(value)):
                with self.assertRaises(ValueError):
                    identity(strategy_config_hash=value)

    def test_rejects_non_hex_uppercase_and_prefixed_config_hash(self) -> None:
        for value in ("g" * 64, "A" * 64, f"sha256:{HASH}"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    identity(strategy_config_hash=value)

    def test_accepts_utc_information_cutoff(self) -> None:
        cutoff = datetime(2026, 7, 24, 9, 0, tzinfo=UTC)
        self.assertIs(identity(information_cutoff=cutoff).information_cutoff, cutoff)

    def test_preserves_non_utc_aware_information_cutoff(self) -> None:
        cutoff = datetime(2026, 7, 24, 18, 0, tzinfo=JST)
        self.assertIs(identity(information_cutoff=cutoff).information_cutoff, cutoff)

    def test_rejects_naive_information_cutoff(self) -> None:
        with self.assertRaises(ValueError):
            identity(information_cutoff=datetime(2026, 7, 24, 9, 0))

    def test_rejects_non_datetime_information_cutoff(self) -> None:
        with self.assertRaises(ValueError):
            identity(information_cutoff="2026-07-24T09:00:00+00:00")

    def test_is_frozen(self) -> None:
        value = identity()
        with self.assertRaises(FrozenInstanceError):
            value.run_id = "other"  # type: ignore[misc]

    def test_uses_slots_and_rejects_new_attributes(self) -> None:
        value = identity()
        self.assertFalse(hasattr(value, "__dict__"))
        with self.assertRaises(TypeError):
            value.extra = "forbidden"  # type: ignore[attr-defined]

    def test_field_order_matches_contract(self) -> None:
        self.assertEqual(
            tuple(field.name for field in fields(SimulationBetPlanIdentity)),
            ("run_id", "race_id", "strategy_id", "strategy_config_hash", "information_cutoff"),
        )


if __name__ == "__main__":
    unittest.main()
