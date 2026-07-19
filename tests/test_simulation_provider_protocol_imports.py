"""Import-boundary checks for the provider protocol module."""

import contextlib
import importlib
import io
from types import ModuleType
from typing import get_type_hints
import unittest


INTERFACES = "scripts.simulation.providers.interfaces"
MODELS = "scripts.simulation.providers.models"
NORMALIZATION = "scripts.simulation.providers.normalization"
REPOSITORY_INTERFACES = "scripts.simulation.repositories.interfaces"


class ProviderProtocolImportTest(unittest.TestCase):
    """Verify that provider contracts import without persistence side effects."""

    def _import_module(self, module_name: str) -> ModuleType:
        module = importlib.import_module(module_name)
        self.assertIsInstance(module, ModuleType)
        return module

    def _assert_import_order(self, module_names: tuple[str, ...]) -> None:
        for module_name in module_names:
            self._import_module(module_name)

    def test_interfaces_module_imports(self) -> None:
        self._import_module(INTERFACES)

    def test_models_module_imports(self) -> None:
        self._import_module(MODELS)

    def test_normalization_module_imports(self) -> None:
        self._import_module(NORMALIZATION)

    def test_repository_interfaces_module_imports(self) -> None:
        self._import_module(REPOSITORY_INTERFACES)

    def test_import_order_a_succeeds(self) -> None:
        self._assert_import_order((INTERFACES, MODELS, REPOSITORY_INTERFACES))

    def test_import_order_b_succeeds(self) -> None:
        self._assert_import_order((REPOSITORY_INTERFACES, MODELS, INTERFACES))

    def test_import_order_c_succeeds(self) -> None:
        self._assert_import_order((MODELS, NORMALIZATION, INTERFACES))

    def test_import_order_d_succeeds(self) -> None:
        self._assert_import_order((NORMALIZATION, REPOSITORY_INTERFACES, INTERFACES))

    def test_interfaces_expected_names_exist(self) -> None:
        module = self._import_module(INTERFACES)
        for name in (
            "ProviderBuildResult",
            "RaceResultProvider",
            "OddsSnapshotProvider",
            "PayoutProvider",
        ):
            self.assertTrue(hasattr(module, name), name)

    def test_models_expected_names_exist(self) -> None:
        module = self._import_module(MODELS)
        for name in (
            "ProviderContext",
            "RaceEntryUniverse",
            "CompletenessResult",
            "RawRaceResult",
            "RawOddsBatch",
            "RawPayoutPublication",
            "expected_selections",
        ):
            self.assertTrue(hasattr(module, name), name)

    def test_normalization_expected_names_exist(self) -> None:
        module = self._import_module(NORMALIZATION)
        for name in (
            "parse_positive_int",
            "parse_finish_position",
            "parse_decimal_odds",
            "parse_payout_per_100",
            "resolve_selection",
        ):
            self.assertTrue(hasattr(module, name), name)

    def test_repository_boundary_names_exist(self) -> None:
        module = self._import_module(REPOSITORY_INTERFACES)
        for name in ("PersistedRaceResult", "OddsSnapshotBatch", "PayoutPublication"):
            self.assertTrue(hasattr(module, name), name)

    def test_race_type_hints_resolve_after_imports(self) -> None:
        module = self._import_module(INTERFACES)
        hints = get_type_hints(module.RaceResultProvider.build_race_result)
        self.assertEqual(set(hints), {"raw", "context", "universe", "return"})

    def test_odds_type_hints_resolve_after_imports(self) -> None:
        module = self._import_module(INTERFACES)
        hints = get_type_hints(module.OddsSnapshotProvider.build_odds_batch)
        self.assertEqual(set(hints), {"raw", "context", "universe", "return"})

    def test_payout_type_hints_resolve_after_imports(self) -> None:
        module = self._import_module(INTERFACES)
        hints = get_type_hints(module.PayoutProvider.build_payout_publication)
        self.assertEqual(set(hints), {"raw", "context", "universe", "return"})

    def test_interfaces_globals_exclude_sqlite_repository_classes(self) -> None:
        module = self._import_module(INTERFACES)
        forbidden = {
            "SQLiteRaceResultRepository",
            "SQLiteOddsSnapshotRepository",
            "SQLitePayoutRepository",
        }
        self.assertFalse(forbidden.intersection(vars(module)))

    def test_interfaces_globals_exclude_database_objects(self) -> None:
        module = self._import_module(INTERFACES)
        forbidden = {
            "sqlite3",
            "Connection",
            "Cursor",
            "connect",
            "apply_migrations",
            "MigrationRunner",
            "repository",
            "database",
            "connection",
            "cursor",
            "session",
        }
        self.assertFalse(forbidden.intersection(vars(module)))

    def test_interfaces_globals_exclude_network_modules(self) -> None:
        module = self._import_module(INTERFACES)
        forbidden = {"requests", "httpx", "urllib", "selenium", "playwright"}
        self.assertFalse(forbidden.intersection(vars(module)))

    def test_interfaces_does_not_hold_forbidden_module_objects(self) -> None:
        module = self._import_module(INTERFACES)
        forbidden_module_names = {
            "sqlite3",
            "requests",
            "httpx",
            "urllib",
            "selenium",
            "playwright",
            "scripts.simulation.repositories.sqlite",
        }
        actual_module_names = {
            value.__name__
            for value in vars(module).values()
            if isinstance(value, ModuleType)
        }
        self.assertFalse(actual_module_names.intersection(forbidden_module_names))

    def test_imports_do_not_write_stdout_or_stderr(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            for module_name in (INTERFACES, MODELS, NORMALIZATION):
                self._import_module(module_name)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
