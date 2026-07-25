"""Contracts for allocation-policy configuration and strategy-hash integration."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from datetime import date, datetime
from decimal import Decimal
import hashlib
import inspect
import json
from types import MappingProxyType
import unittest

from scripts.prediction.allocation_policy import (
    AllocationPolicyConfig,
    AllocationPolicyIdentity,
    allocation_policy_config_hash,
    allocation_policy_config_payload,
    build_allocation_policy_identity,
    canonicalize_allocation_policy_parameters,
)
from scripts.prediction.bet_strategy import StrategyConfig
from scripts.simulation.models import (
    build_strategy_identity,
    strategy_config_hash,
    strategy_config_payload,
)


def policy_config(**overrides: object) -> AllocationPolicyConfig:
    values: dict[str, object] = {
        "policy_name": "fixed-stake",
        "policy_version": "1.0",
        "parameters": {"stake": 100, "enabled": True, "tiers": [100, {"max": 300}]},
    }
    values.update(overrides)
    return AllocationPolicyConfig(**values)  # type: ignore[arg-type]


def legacy_payload(config: StrategyConfig, schema_version: int = 1) -> dict[str, object]:
    from scripts.simulation.models import _normalize_json

    return {
        "schema_version": schema_version,
        "allowed_bet_types": _normalize_json(config.allowed_bet_types),
        "max_bet_count": config.max_bet_count,
        "selection_style": _normalize_json(config.selection_style),
        "min_combination_score": _normalize_json(config.min_combination_score),
        "max_candidates": config.max_candidates,
        "sort_condition": _normalize_json(config.sort_condition),
    }


class AllocationPolicyConfigTests(unittest.TestCase):
    def test_config_has_contract_fields_in_order(self) -> None:
        self.assertEqual(
            tuple(item.name for item in fields(AllocationPolicyConfig)),
            ("policy_name", "policy_version", "parameters"),
        )

    def test_config_preserves_valid_text_without_normalization(self) -> None:
        value = policy_config(policy_name=" policy ", policy_version=" v1 ")
        self.assertEqual(value.policy_name, " policy ")
        self.assertEqual(value.policy_version, " v1 ")

    def test_config_rejects_invalid_policy_name(self) -> None:
        for value in ("", "   ", 3, b"policy"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    policy_config(policy_name=value)

    def test_config_rejects_invalid_policy_version(self) -> None:
        for value in ("", "   ", 3, b"1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    policy_config(policy_version=value)

    def test_config_rejects_non_mapping_parameters(self) -> None:
        for value in (None, (), [], "parameters", 1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    policy_config(parameters=value)

    def test_config_freezes_nested_mutable_inputs(self) -> None:
        nested = {"items": [1, {"limit": 2}]}
        value = policy_config(parameters=nested)
        nested["items"][1]["limit"] = 999
        nested["items"].append(3)
        nested["other"] = "late"
        self.assertEqual(value.parameters["items"], (1, MappingProxyType({"limit": 2})))
        self.assertNotIn("other", value.parameters)

    def test_config_parameters_are_read_only(self) -> None:
        value = policy_config()
        self.assertIsInstance(value.parameters, MappingProxyType)
        with self.assertRaises(TypeError):
            value.parameters["stake"] = 200  # type: ignore[index]

    def test_config_is_frozen_and_slotted(self) -> None:
        value = policy_config()
        with self.assertRaises(FrozenInstanceError):
            value.policy_name = "other"  # type: ignore[misc]
        self.assertFalse(hasattr(value, "__dict__"))

    def test_config_preserves_sequence_order_as_tuple(self) -> None:
        value = policy_config(parameters={"sequence": [3, 1, 2]})
        self.assertEqual(value.parameters["sequence"], (3, 1, 2))

    def test_config_sorts_mapping_keys_deterministically(self) -> None:
        value = policy_config(parameters={"z": 1, "a": {"y": 2, "b": 3}})
        self.assertEqual(tuple(value.parameters), ("a", "z"))
        self.assertEqual(tuple(value.parameters["a"]), ("b", "y"))

    def test_config_rejects_non_string_mapping_key(self) -> None:
        with self.assertRaises(ValueError):
            policy_config(parameters={1: "value"})  # type: ignore[dict-item]

    def test_config_rejects_unsupported_scalar_and_container_types(self) -> None:
        unsupported = (
            1.25,
            Decimal("1.25"),
            datetime(2026, 1, 1),
            date(2026, 1, 1),
            b"x",
            bytearray(b"x"),
            {1, 2},
            frozenset({1, 2}),
            lambda: None,
            object(),
        )
        for value in unsupported:
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(ValueError):
                    policy_config(parameters={"value": value})

    def test_config_accepts_bool_without_treating_it_as_int(self) -> None:
        value = policy_config(parameters={"enabled": True, "disabled": False, "count": 1})
        self.assertIs(value.parameters["enabled"], True)
        self.assertIs(value.parameters["disabled"], False)
        self.assertEqual(value.parameters["count"], 1)

    def test_config_rejects_direct_circular_mapping(self) -> None:
        parameters: dict[str, object] = {}
        parameters["self"] = parameters
        with self.assertRaises(ValueError):
            policy_config(parameters=parameters)

    def test_config_rejects_indirect_circular_container(self) -> None:
        values: list[object] = []
        nested = {"values": values}
        values.append(nested)
        with self.assertRaises(ValueError):
            policy_config(parameters=nested)

    def test_config_allows_shared_non_circular_container(self) -> None:
        shared = [1, 2]
        value = policy_config(parameters={"a": shared, "b": shared})
        self.assertEqual(value.parameters["a"], (1, 2))
        self.assertEqual(value.parameters["b"], (1, 2))


class AllocationPolicyCanonicalizationTests(unittest.TestCase):
    def test_canonicalization_returns_plain_json_tree(self) -> None:
        value = policy_config()
        plain = canonicalize_allocation_policy_parameters(value.parameters)
        self.assertEqual(plain, {"enabled": True, "stake": 100, "tiers": [100, {"max": 300}]})
        self.assertIsInstance(plain, dict)
        self.assertIsInstance(plain["tiers"], list)
        self.assertIsInstance(plain["tiers"][1], dict)
        self.assertEqual(json.loads(json.dumps(plain)), plain)

    def test_canonicalization_sorts_mapping_keys_without_mutating_input(self) -> None:
        raw = {"z": 1, "a": {"y": 2, "b": 3}}
        plain = canonicalize_allocation_policy_parameters(raw)
        self.assertEqual(tuple(plain), ("a", "z"))
        self.assertEqual(tuple(plain["a"]), ("b", "y"))
        self.assertEqual(raw, {"z": 1, "a": {"y": 2, "b": 3}})

    def test_canonicalization_converts_tuple_and_list_to_plain_lists(self) -> None:
        plain = canonicalize_allocation_policy_parameters({"tuple": (1, 2), "list": [3, 4]})
        self.assertEqual(plain, {"list": [3, 4], "tuple": [1, 2]})

    def test_canonicalization_rejects_unsupported_values(self) -> None:
        with self.assertRaises(ValueError):
            canonicalize_allocation_policy_parameters({"value": Decimal("1")})

    def test_canonicalization_rejects_circular_mapping(self) -> None:
        parameters: dict[str, object] = {}
        parameters["self"] = parameters
        with self.assertRaises(ValueError):
            canonicalize_allocation_policy_parameters(parameters)

    def test_canonicalization_rejects_non_mapping_root(self) -> None:
        with self.assertRaises(ValueError):
            canonicalize_allocation_policy_parameters([])  # type: ignore[arg-type]


class AllocationPolicyPayloadAndIdentityTests(unittest.TestCase):
    def test_payload_has_fixed_schema_and_plain_parameters(self) -> None:
        payload = allocation_policy_config_payload(policy_config())
        self.assertEqual(
            payload,
            {
                "schema_version": 1,
                "policy_name": "fixed-stake",
                "policy_version": "1.0",
                "parameters": {"enabled": True, "stake": 100, "tiers": [100, {"max": 300}]},
            },
        )

    def test_payload_rejects_wrong_config_type(self) -> None:
        with self.assertRaises(ValueError):
            allocation_policy_config_payload("config")  # type: ignore[arg-type]

    def test_policy_hash_matches_specification(self) -> None:
        config = policy_config()
        payload = allocation_policy_config_payload(config)
        expected = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
        ).hexdigest()
        self.assertEqual(allocation_policy_config_hash(config), expected)

    def test_policy_hash_is_deterministic_across_mapping_order(self) -> None:
        first = policy_config(parameters={"z": 1, "a": {"d": 4, "c": 3}})
        second = policy_config(parameters={"a": {"c": 3, "d": 4}, "z": 1})
        self.assertEqual(allocation_policy_config_hash(first), allocation_policy_config_hash(second))

    def test_policy_hash_changes_for_each_identity_component(self) -> None:
        base = policy_config()
        hashes = {
            allocation_policy_config_hash(base),
            allocation_policy_config_hash(policy_config(policy_name="other")),
            allocation_policy_config_hash(policy_config(policy_version="2.0")),
            allocation_policy_config_hash(policy_config(parameters={"stake": 200})),
        }
        self.assertEqual(len(hashes), 4)

    def test_policy_hash_handles_unicode_deterministically(self) -> None:
        first = policy_config(policy_name="均等配分", parameters={"名称": "固定", "金額": 100})
        second = policy_config(policy_name="均等配分", parameters={"金額": 100, "名称": "固定"})
        self.assertEqual(allocation_policy_config_hash(first), allocation_policy_config_hash(second))

    def test_identity_builder_derives_values_from_config(self) -> None:
        config = policy_config()
        identity = build_allocation_policy_identity(config)
        self.assertEqual(identity.policy_name, config.policy_name)
        self.assertEqual(identity.policy_version, config.policy_version)
        self.assertEqual(identity.policy_config_hash, allocation_policy_config_hash(config))

    def test_identity_has_contract_fields_and_is_frozen(self) -> None:
        identity = build_allocation_policy_identity(policy_config())
        self.assertEqual(
            tuple(item.name for item in fields(AllocationPolicyIdentity)),
            ("policy_name", "policy_version", "policy_config_hash"),
        )
        with self.assertRaises(FrozenInstanceError):
            identity.policy_version = "2"  # type: ignore[misc]
        self.assertFalse(hasattr(identity, "__dict__"))

    def test_identity_rejects_invalid_hashes(self) -> None:
        for value in ("", "0" * 63, "0" * 65, "A" * 64, "g" * 64, 1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    AllocationPolicyIdentity("fixed", "1", value)  # type: ignore[arg-type]

    def test_identity_rejects_invalid_name_and_version(self) -> None:
        digest = "0" * 64
        for name, version in (("", "1"), ("fixed", " "), (1, "1"), ("fixed", 1)):
            with self.subTest(name=name, version=version):
                with self.assertRaises(ValueError):
                    AllocationPolicyIdentity(name, version, digest)  # type: ignore[arg-type]


class StrategyConfigIntegrationTests(unittest.TestCase):
    def test_strategy_config_adds_optional_final_field(self) -> None:
        self.assertEqual(tuple(item.name for item in fields(StrategyConfig))[-1], "allocation_policy")
        self.assertIsNone(StrategyConfig().allocation_policy)

    def test_strategy_config_accepts_policy_config(self) -> None:
        config = StrategyConfig(allocation_policy=policy_config())
        self.assertIsInstance(config.allocation_policy, AllocationPolicyConfig)

    def test_strategy_config_rejects_wrong_policy_type(self) -> None:
        for value in ({}, "fixed", 1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    StrategyConfig(allocation_policy=value)  # type: ignore[arg-type]

    def test_strategy_config_existing_positional_constructor_remains_valid(self) -> None:
        base = StrategyConfig()
        value = StrategyConfig(
            base.allowed_bet_types,
            base.max_bet_count,
            base.selection_style,
            base.min_combination_score,
            base.max_candidates,
            base.sort_condition,
        )
        self.assertIsNone(value.allocation_policy)
        self.assertEqual(value.allowed_bet_types, base.allowed_bet_types)

    def test_legacy_payload_is_exactly_preserved_without_policy(self) -> None:
        config = StrategyConfig()
        self.assertEqual(strategy_config_payload(config), legacy_payload(config))
        self.assertNotIn("allocation_policy", strategy_config_payload(config))

    def test_legacy_hash_is_exactly_preserved_without_policy(self) -> None:
        config = StrategyConfig()
        encoded = json.dumps(legacy_payload(config), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.assertEqual(strategy_config_hash(config), hashlib.sha256(encoded).hexdigest())

    def test_legacy_custom_schema_payload_is_preserved_without_policy(self) -> None:
        config = StrategyConfig()
        self.assertEqual(strategy_config_payload(config, schema_version=2), legacy_payload(config, schema_version=2))

    def test_strategy_payload_contains_nested_policy_contract(self) -> None:
        config = StrategyConfig(allocation_policy=policy_config())
        policy_payload = allocation_policy_config_payload(config.allocation_policy)
        identity = build_allocation_policy_identity(config.allocation_policy)
        self.assertEqual(
            strategy_config_payload(config)["allocation_policy"],
            {
                "schema_version": 1,
                "policy_name": identity.policy_name,
                "policy_version": identity.policy_version,
                "policy_config_hash": identity.policy_config_hash,
                "parameters": policy_payload["parameters"],
            },
        )

    def test_strategy_hash_changes_when_policy_is_set_or_changed(self) -> None:
        base = strategy_config_hash(StrategyConfig())
        first = strategy_config_hash(StrategyConfig(allocation_policy=policy_config()))
        changed = strategy_config_hash(StrategyConfig(allocation_policy=policy_config(parameters={"stake": 200})))
        self.assertNotEqual(base, first)
        self.assertNotEqual(first, changed)

    def test_strategy_hash_ignores_policy_mapping_key_order(self) -> None:
        first = StrategyConfig(allocation_policy=policy_config(parameters={"z": 1, "a": {"d": 4, "c": 3}}))
        second = StrategyConfig(allocation_policy=policy_config(parameters={"a": {"c": 3, "d": 4}, "z": 1}))
        self.assertEqual(strategy_config_hash(first), strategy_config_hash(second))

    def test_build_strategy_identity_uses_extended_policy_hash(self) -> None:
        config = StrategyConfig(allocation_policy=policy_config())
        identity = build_strategy_identity("strategy", config)
        self.assertEqual(identity.strategy_config_hash, strategy_config_hash(config))
        self.assertEqual(identity.strategy_config, config)

    def test_prediction_contract_does_not_import_simulation_modules(self) -> None:
        import scripts.prediction.allocation_policy as module

        tree = ast.parse(inspect.getsource(module))
        imports = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ] + [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        self.assertFalse(any(name.startswith("scripts.simulation") for name in imports))

    def test_prediction_package_root_export_remains_unchanged(self) -> None:
        import scripts.prediction as package

        self.assertFalse(hasattr(package, "AllocationPolicyConfig"))
        self.assertFalse(hasattr(package, "AllocationPolicyIdentity"))


if __name__ == "__main__":
    unittest.main()
