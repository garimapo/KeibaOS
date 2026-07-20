"""Public package exports for the concrete Payout Provider."""

import inspect
import unittest

import scripts.simulation.providers as providers
from scripts.simulation.providers import (
    DefaultOddsSnapshotProvider,
    DefaultPayoutProvider,
    DefaultRaceResultProvider,
    PayoutProvider,
)
from scripts.simulation.providers import payout_provider


class PayoutProviderPublicApiTest(unittest.TestCase):
    def test_default_payout_provider_is_importable_from_package_root(self) -> None:
        self.assertIs(DefaultPayoutProvider, providers.DefaultPayoutProvider)

    def test_default_payout_provider_is_in_all(self) -> None:
        self.assertIn("DefaultPayoutProvider", providers.__all__)

    def test_all_contains_30_symbols(self) -> None:
        self.assertEqual(len(providers.__all__), 30)

    def test_default_payout_provider_matches_payout_provider_object(self) -> None:
        self.assertIs(providers.DefaultPayoutProvider, payout_provider.DefaultPayoutProvider)

    def test_protocol_and_default_payout_provider_are_distinct(self) -> None:
        self.assertIsNot(PayoutProvider, DefaultPayoutProvider)

    def test_default_payout_provider_is_concrete_class(self) -> None:
        self.assertTrue(inspect.isclass(DefaultPayoutProvider))

    def test_default_payout_provider_is_not_protocol_or_runtime_protocol(self) -> None:
        self.assertFalse(getattr(DefaultPayoutProvider, "_is_protocol", False))
        self.assertFalse(getattr(DefaultPayoutProvider, "_is_runtime_protocol", False))

    def test_star_import_exposes_all_default_providers(self) -> None:
        namespace: dict[str, object] = {}
        exec("from scripts.simulation.providers import *", namespace)
        self.assertIs(namespace["DefaultPayoutProvider"], DefaultPayoutProvider)
        self.assertIs(namespace["DefaultOddsSnapshotProvider"], DefaultOddsSnapshotProvider)
        self.assertIs(namespace["DefaultRaceResultProvider"], DefaultRaceResultProvider)

    def test_star_import_does_not_expose_payout_helpers(self) -> None:
        namespace: dict[str, object] = {}
        exec("from scripts.simulation.providers import *", namespace)
        self.assertFalse(any(name.startswith(("_build_payout", "_analyze_payout")) for name in namespace))

    def test_payout_internal_model_is_not_in_all(self) -> None:
        self.assertNotIn("_PayoutPublicationStatusFacts", providers.__all__)

    def test_payout_internal_helpers_are_not_package_attributes(self) -> None:
        helpers = (
            "_build_payout_record",
            "_build_payout_publication",
            "_analyze_payout_publication_status_facts",
            "_build_payout_completeness",
            "_build_payout_provider_output",
        )
        self.assertFalse(any(hasattr(providers, helper) for helper in helpers))

    def test_other_provider_helpers_remain_unexposed(self) -> None:
        self.assertFalse(hasattr(providers, "_build_odds_provider_output"))
        self.assertFalse(hasattr(providers, "_build_race_result_provider_output"))

    def test_package_root_does_not_expose_repository_or_database_objects(self) -> None:
        self.assertFalse({"SQLitePayoutRepository", "PayoutRepository", "database", "connection"} & set(providers.__all__))

    def test_public_payout_provider_can_be_constructed(self) -> None:
        self.assertIsInstance(DefaultPayoutProvider(), DefaultPayoutProvider)

    def test_public_payout_provider_uses_empty_slots(self) -> None:
        self.assertEqual(DefaultPayoutProvider.__slots__, ())

    def test_public_payout_provider_build_method_is_callable(self) -> None:
        self.assertTrue(callable(DefaultPayoutProvider().build_payout_publication))

    def test_package_public_api_order_is_deterministic(self) -> None:
        self.assertEqual(providers.__all__, tuple(providers.__all__))

    def test_provider_default_class_order_is_consistent(self) -> None:
        names = providers.__all__
        self.assertLess(names.index("DefaultRaceResultProvider"), names.index("DefaultOddsSnapshotProvider"))
        self.assertLess(names.index("DefaultOddsSnapshotProvider"), names.index("DefaultPayoutProvider"))
