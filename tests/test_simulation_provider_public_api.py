"""Public API contract tests for ``scripts.simulation.providers``."""

import importlib
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers import errors, interfaces, models, normalization


REQUIRED_NAMES = (
    "SimulationProviderError", "ProviderValidationError", "ProviderCompletenessError",
    "ProviderUnsupportedError", "ProviderContext", "RaceEntryUniverse", "CompletenessStatus",
    "CompletenessResult", "RawRaceResultEntry", "RawRaceResult", "RawOddsEntry", "RawOddsBatch",
    "RawPayoutRecord", "RawPayoutPublication", "ProviderBuildResult", "RaceResultProvider",
    "OddsSnapshotProvider", "PayoutProvider", "parse_positive_int", "parse_finish_position",
    "parse_decimal_odds", "parse_payout_per_100", "normalize_result_status",
    "normalize_result_entry_status", "normalize_payout_status", "resolve_selection",
    "expected_selections", "DefaultRaceResultProvider", "DefaultOddsSnapshotProvider",
    "DefaultPayoutProvider",
)


class ProviderPublicApiTest(unittest.TestCase):
    def test_provider_package_imports(self) -> None:
        self.assertIs(importlib.import_module("scripts.simulation.providers"), providers)

    def test_all_is_defined(self) -> None:
        self.assertIsInstance(providers.__all__, tuple)

    def test_all_contains_required_names(self) -> None:
        self.assertEqual(providers.__all__, REQUIRED_NAMES)

    def test_all_has_no_duplicates(self) -> None:
        self.assertEqual(len(providers.__all__), len(set(providers.__all__)))

    def test_all_contains_only_nonblank_strings(self) -> None:
        self.assertTrue(all(isinstance(name, str) and name.strip() for name in providers.__all__))

    def test_all_names_exist(self) -> None:
        self.assertTrue(all(hasattr(providers, name) for name in providers.__all__))

    def test_all_names_are_not_none(self) -> None:
        self.assertTrue(all(getattr(providers, name) is not None for name in providers.__all__))

    def test_errors_are_public(self) -> None:
        self.assertIs(providers.ProviderValidationError, errors.ProviderValidationError)

    def test_core_models_are_public(self) -> None:
        self.assertIs(providers.ProviderContext, models.ProviderContext)
        self.assertIs(providers.RaceEntryUniverse, models.RaceEntryUniverse)
        self.assertIs(providers.CompletenessResult, models.CompletenessResult)

    def test_raw_models_are_public(self) -> None:
        self.assertIs(providers.RawRaceResult, models.RawRaceResult)
        self.assertIs(providers.RawOddsBatch, models.RawOddsBatch)
        self.assertIs(providers.RawPayoutPublication, models.RawPayoutPublication)

    def test_contracts_are_public(self) -> None:
        self.assertIs(providers.ProviderBuildResult, interfaces.ProviderBuildResult)
        self.assertIs(providers.RaceResultProvider, interfaces.RaceResultProvider)

    def test_default_race_result_provider_is_public(self) -> None:
        from scripts.simulation.providers.result_provider import DefaultRaceResultProvider
        self.assertIs(providers.DefaultRaceResultProvider, DefaultRaceResultProvider)

    def test_default_odds_snapshot_provider_is_public(self) -> None:
        from scripts.simulation.providers.odds_provider import DefaultOddsSnapshotProvider
        self.assertIs(providers.DefaultOddsSnapshotProvider, DefaultOddsSnapshotProvider)

    def test_default_payout_provider_is_public(self) -> None:
        from scripts.simulation.providers.payout_provider import DefaultPayoutProvider
        self.assertIs(providers.DefaultPayoutProvider, DefaultPayoutProvider)

    def test_normalization_functions_are_public(self) -> None:
        self.assertIs(providers.parse_positive_int, normalization.parse_positive_int)
        self.assertIs(providers.normalize_payout_status, normalization.normalize_payout_status)

    def test_selection_helpers_are_public(self) -> None:
        self.assertIs(providers.expected_selections, models.expected_selections)
        self.assertIs(providers.resolve_selection, normalization.resolve_selection)

    def test_public_objects_match_source_modules(self) -> None:
        self.assertIs(providers.ProviderBuildResult, interfaces.ProviderBuildResult)
        self.assertIs(providers.parse_decimal_odds, normalization.parse_decimal_odds)
        self.assertIs(providers.ProviderUnsupportedError, errors.ProviderUnsupportedError)

    def test_internal_helpers_are_not_in_all(self) -> None:
        forbidden = {"T", "dataclass", "Generic", "Mapping", "Decimal", "_enum"}
        self.assertFalse(forbidden.intersection(providers.__all__))

    def test_repository_sqlite_types_are_not_public(self) -> None:
        forbidden = {"SQLiteRaceResultRepository", "SQLiteOddsSnapshotRepository", "SQLitePayoutRepository"}
        self.assertFalse(forbidden.intersection(providers.__all__))

    def test_star_import_exposes_exactly_all_names(self) -> None:
        namespace: dict[str, object] = {}
        exec("from scripts.simulation.providers import *", namespace)
        self.assertEqual(set(namespace) - {"__builtins__"}, set(providers.__all__))

    def test_public_api_order_is_deterministic(self) -> None:
        self.assertEqual(providers.__all__, tuple(providers.__all__))
