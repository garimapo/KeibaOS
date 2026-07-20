"""Public package exports for the concrete Result Provider."""

import inspect
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers import DefaultRaceResultProvider, RaceResultProvider
from scripts.simulation.providers import result_provider


class ResultProviderPublicApiTest(unittest.TestCase):
    def test_default_provider_is_importable_from_package_root(self) -> None:
        self.assertIs(DefaultRaceResultProvider, providers.DefaultRaceResultProvider)

    def test_default_provider_is_in_all(self) -> None:
        self.assertIn("DefaultRaceResultProvider", providers.__all__)

    def test_all_contains_30_symbols(self) -> None:
        self.assertEqual(len(providers.__all__), 30)

    def test_default_provider_matches_result_provider_object(self) -> None:
        self.assertIs(providers.DefaultRaceResultProvider, result_provider.DefaultRaceResultProvider)

    def test_protocol_and_default_provider_are_distinct(self) -> None:
        self.assertIsNot(RaceResultProvider, DefaultRaceResultProvider)

    def test_default_provider_is_concrete_class(self) -> None:
        self.assertTrue(inspect.isclass(DefaultRaceResultProvider))

    def test_default_provider_is_not_protocol(self) -> None:
        self.assertFalse(getattr(DefaultRaceResultProvider, "_is_protocol", False))

    def test_star_import_exposes_default_provider(self) -> None:
        namespace: dict[str, object] = {}
        exec("from scripts.simulation.providers import *", namespace)
        self.assertIs(namespace["DefaultRaceResultProvider"], DefaultRaceResultProvider)

    def test_star_import_does_not_expose_result_helpers(self) -> None:
        namespace: dict[str, object] = {}
        exec("from scripts.simulation.providers import *", namespace)
        self.assertFalse(any(name.startswith("_build_") or name.startswith("_analyze_") for name in namespace))

    def test_result_internal_models_are_not_in_all(self) -> None:
        forbidden = {"_ResultCoverage", "_ResultEntrySemanticIssues", "_ResultRaceStatusSemanticIssues"}
        self.assertFalse(forbidden & set(providers.__all__))

    def test_result_internal_helpers_are_not_package_attributes(self) -> None:
        helpers = (
            "_build_persisted_result_entry", "_build_persisted_race_result", "_analyze_result_coverage",
            "_build_result_completeness", "_analyze_result_entry_semantics", "_apply_result_entry_semantics",
            "_analyze_result_race_status_semantics", "_apply_result_race_status_semantics",
            "_build_race_result_provider_output",
        )
        self.assertFalse(any(hasattr(providers, helper) for helper in helpers))

    def test_package_root_does_not_expose_repository_or_database_objects(self) -> None:
        forbidden = {"SQLiteRaceResultRepository", "RaceResultRepository", "database", "connection"}
        self.assertFalse(forbidden & set(providers.__all__))

    def test_public_provider_can_be_constructed(self) -> None:
        self.assertIsInstance(DefaultRaceResultProvider(), DefaultRaceResultProvider)

    def test_public_provider_uses_empty_slots(self) -> None:
        self.assertEqual(DefaultRaceResultProvider.__slots__, ())

    def test_public_provider_build_method_is_callable(self) -> None:
        self.assertTrue(callable(DefaultRaceResultProvider().build_race_result))

    def test_package_public_api_order_is_deterministic(self) -> None:
        self.assertEqual(providers.__all__, tuple(providers.__all__))
