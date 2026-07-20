"""Public package exports for the concrete Odds Provider."""

import inspect
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers import (
    DefaultOddsSnapshotProvider,
    DefaultRaceResultProvider,
    OddsSnapshotProvider,
)
from scripts.simulation.providers import odds_provider


class OddsProviderPublicApiTest(unittest.TestCase):
    def test_default_odds_provider_is_importable_from_package_root(self) -> None:
        self.assertIs(DefaultOddsSnapshotProvider, providers.DefaultOddsSnapshotProvider)
    def test_default_odds_provider_is_in_all(self) -> None:
        self.assertIn("DefaultOddsSnapshotProvider", providers.__all__)
    def test_all_contains_30_symbols(self) -> None:
        self.assertEqual(len(providers.__all__), 30)
    def test_default_odds_provider_matches_odds_provider_object(self) -> None:
        self.assertIs(providers.DefaultOddsSnapshotProvider, odds_provider.DefaultOddsSnapshotProvider)
    def test_protocol_and_default_odds_provider_are_distinct(self) -> None:
        self.assertIsNot(OddsSnapshotProvider, DefaultOddsSnapshotProvider)
    def test_default_odds_provider_is_concrete_class(self) -> None:
        self.assertTrue(inspect.isclass(DefaultOddsSnapshotProvider))
    def test_default_odds_provider_is_not_protocol(self) -> None:
        self.assertFalse(getattr(DefaultOddsSnapshotProvider, "_is_protocol", False))
    def test_default_odds_provider_is_not_runtime_protocol(self) -> None:
        self.assertFalse(getattr(DefaultOddsSnapshotProvider, "_is_runtime_protocol", False))
    def test_star_import_exposes_default_odds_provider(self) -> None:
        namespace: dict[str, object] = {}; exec("from scripts.simulation.providers import *", namespace)
        self.assertIs(namespace["DefaultOddsSnapshotProvider"], DefaultOddsSnapshotProvider)
    def test_star_import_keeps_default_result_provider(self) -> None:
        namespace: dict[str, object] = {}; exec("from scripts.simulation.providers import *", namespace)
        self.assertIs(namespace["DefaultRaceResultProvider"], DefaultRaceResultProvider)
    def test_star_import_does_not_expose_odds_helpers(self) -> None:
        namespace: dict[str, object] = {}; exec("from scripts.simulation.providers import *", namespace)
        self.assertFalse(any(name.startswith(("_build_odds", "_analyze_odds")) for name in namespace))
    def test_odds_internal_model_is_not_in_all(self) -> None:
        self.assertNotIn("_OddsSelectionCoverage", providers.__all__)
    def test_odds_internal_helpers_are_not_package_attributes(self) -> None:
        names = ("_build_odds_snapshot_entry", "_build_odds_snapshot_batch", "_analyze_odds_selection_coverage", "_build_odds_completeness", "_build_odds_provider_output")
        self.assertFalse(any(hasattr(providers, name) for name in names))
    def test_result_internal_helpers_remain_unexposed(self) -> None:
        self.assertFalse(hasattr(providers, "_build_race_result_provider_output"))
    def test_package_root_does_not_expose_repository_or_database_objects(self) -> None:
        self.assertFalse({"SQLiteOddsSnapshotRepository", "database", "connection"} & set(providers.__all__))
    def test_public_odds_provider_can_be_constructed(self) -> None:
        self.assertIsInstance(DefaultOddsSnapshotProvider(), DefaultOddsSnapshotProvider)
    def test_public_odds_provider_uses_empty_slots(self) -> None:
        self.assertEqual(DefaultOddsSnapshotProvider.__slots__, ())
    def test_public_odds_provider_build_method_is_callable(self) -> None:
        self.assertTrue(callable(DefaultOddsSnapshotProvider().build_odds_batch))
    def test_package_public_api_order_is_deterministic(self) -> None:
        self.assertEqual(providers.__all__, tuple(providers.__all__))
