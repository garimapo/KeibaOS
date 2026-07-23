"""Contract tests for the Phase 4C-2c settlement data boundary."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import inspect
from pathlib import Path
import textwrap
from types import MappingProxyType
from typing import get_type_hints
import unittest

from scripts.simulation.models import SimulationBet
from scripts.simulation.providers.models import (
    ProviderContext,
    RaceEntryUniverse,
    RawPayoutPublication,
    RawRaceResult,
)
from scripts.simulation.settlement import RaceSettlementData, RaceSettlementSource
import scripts.simulation.settlement as settlement_module
from scripts.simulation.validation import SimulationValidationError


UTC = timezone.utc
CUTOFF = datetime(2026, 7, 24, 9, 0, tzinfo=UTC)
_UNSET = object()


def bet(*, race_id: int = 101) -> SimulationBet:
    return SimulationBet(
        race_id=race_id,
        strategy_id="strategy",
        bet_type="単勝",
        race_entry_ids=(11,),
        stake=100,
        recommendation_rank=0,
        placed_at_cutoff=CUTOFF,
    )


def universe(*, race_id: int = 101) -> RaceEntryUniverse:
    return RaceEntryUniverse(
        race_id=race_id,
        active_race_entry_ids=frozenset({11}),
        excluded_race_entry_ids=frozenset(),
        cancelled_race_entry_ids=frozenset(),
        horse_no_to_race_entry_id={1: 11},
    )


def context(*, race_id: int = 101, bet_type: str | None = None, cutoff: datetime = CUTOFF) -> ProviderContext:
    return ProviderContext(
        race_id=race_id,
        observed_at=CUTOFF,
        source="source",
        source_url=None,
        captured_at=CUTOFF,
        information_cutoff=cutoff,
        bet_type=bet_type,
    )


def raw_result() -> RawRaceResult:
    return RawRaceResult(declared_status="確定", finalized_at=CUTOFF, entries=())


def raw_publication(*, bet_type: str = "単勝") -> RawPayoutPublication:
    return RawPayoutPublication(
        bet_type=bet_type,
        finalized_at=CUTOFF,
        entries=(),
        declared_complete=True,
        table_complete=True,
        capture_succeeded=True,
    )


def settlement_data(
    *,
    race_id: int = 101,
    bets: object = _UNSET,
    raw_race_result: object = _UNSET,
    race_result_context: object = _UNSET,
    publications: object = _UNSET,
    contexts: object = _UNSET,
    race_universe: object = _UNSET,
) -> RaceSettlementData:
    return RaceSettlementData(
        race_id=race_id,
        bets=(bet(),) if bets is _UNSET else bets,  # type: ignore[arg-type]
        raw_race_result=raw_result() if raw_race_result is _UNSET else raw_race_result,  # type: ignore[arg-type]
        race_result_context=context() if race_result_context is _UNSET else race_result_context,  # type: ignore[arg-type]
        raw_payout_publications_by_bet_type={"単勝": raw_publication()} if publications is _UNSET else publications,  # type: ignore[arg-type]
        payout_contexts_by_bet_type={"単勝": context(bet_type="単勝")} if contexts is _UNSET else contexts,  # type: ignore[arg-type]
        universe=universe() if race_universe is _UNSET else race_universe,  # type: ignore[arg-type]
    )


class RaceSettlementDataTests(unittest.TestCase):
    def test_constructs_complete_bundle(self) -> None:
        value = settlement_data()
        self.assertEqual(value.race_id, 101)
        self.assertEqual(value.bets, (bet(),))
        self.assertEqual(set(value.raw_payout_publications_by_bet_type), {"単勝"})

    def test_is_frozen(self) -> None:
        value = settlement_data()
        with self.assertRaises(FrozenInstanceError):
            value.race_id = 102  # type: ignore[misc]

    def test_uses_slots(self) -> None:
        value = settlement_data()
        with self.assertRaises(TypeError):
            value.unexpected = "value"  # type: ignore[attr-defined]

    def test_copies_bets_to_tuple(self) -> None:
        supplied = [bet()]
        value = settlement_data(bets=supplied)
        supplied.clear()
        self.assertEqual(value.bets, (bet(),))
        self.assertIsInstance(value.bets, tuple)

    def test_allows_empty_bets(self) -> None:
        self.assertEqual(settlement_data(bets=()).bets, ())

    def test_allows_complete_race_result_pair(self) -> None:
        value = settlement_data(raw_race_result=raw_result(), race_result_context=context())
        self.assertIsInstance(value.raw_race_result, RawRaceResult)
        self.assertIsInstance(value.race_result_context, ProviderContext)

    def test_allows_absent_race_result_pair(self) -> None:
        value = settlement_data(raw_race_result=None, race_result_context=None)
        self.assertIsNone(value.raw_race_result)
        self.assertIsNone(value.race_result_context)

    def test_rejects_raw_result_without_context(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(raw_race_result=raw_result(), race_result_context=None)

    def test_rejects_context_without_raw_result(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(raw_race_result=None, race_result_context=context())

    def test_rejects_mismatched_payout_mapping_keys(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(publications={"単勝": raw_publication()}, contexts={})

    def test_defensively_copies_payout_publication_mapping(self) -> None:
        publications = {"単勝": raw_publication()}
        contexts = {"単勝": context(bet_type="単勝")}
        value = settlement_data(publications=publications, contexts=contexts)
        publications.clear()
        contexts.clear()
        self.assertEqual(set(value.raw_payout_publications_by_bet_type), {"単勝"})
        self.assertEqual(set(value.payout_contexts_by_bet_type), {"単勝"})

    def test_payout_publication_mapping_is_read_only(self) -> None:
        value = settlement_data()
        self.assertIsInstance(value.raw_payout_publications_by_bet_type, MappingProxyType)
        with self.assertRaises(TypeError):
            value.raw_payout_publications_by_bet_type["単勝"] = raw_publication()  # type: ignore[index]

    def test_payout_context_mapping_is_read_only(self) -> None:
        value = settlement_data()
        self.assertIsInstance(value.payout_contexts_by_bet_type, MappingProxyType)
        with self.assertRaises(TypeError):
            value.payout_contexts_by_bet_type["単勝"] = context(bet_type="単勝")  # type: ignore[index]

    def test_rejects_invalid_race_id(self) -> None:
        for value in (0, -1, True, "101"):
            with self.subTest(value=value), self.assertRaises(SimulationValidationError):
                settlement_data(race_id=value)  # type: ignore[arg-type]

    def test_rejects_invalid_bet_element(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(bets=(object(),))

    def test_rejects_bet_from_another_race(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(bets=(bet(race_id=102),))

    def test_rejects_invalid_universe(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(race_universe=object())

    def test_rejects_universe_for_another_race(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(race_universe=universe(race_id=102))

    def test_rejects_invalid_payout_mapping_keys_and_values(self) -> None:
        cases = (
            ( {1: raw_publication()}, {1: context()} ),
            ( {"単勝": object()}, {"単勝": context(bet_type="単勝")} ),
            ( {"単勝": raw_publication()}, {"単勝": object()} ),
        )
        for publications, contexts in cases:
            with self.subTest(publications=publications, contexts=contexts), self.assertRaises(SimulationValidationError):
                settlement_data(publications=publications, contexts=contexts)

    def test_rejects_publication_bet_type_mismatch(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(
                publications={"単勝": raw_publication(bet_type="馬連")},
                contexts={"単勝": context(bet_type="単勝")},
            )

    def test_rejects_payout_context_race_id_mismatch(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(contexts={"単勝": context(race_id=102, bet_type="単勝")})

    def test_rejects_race_result_context_race_id_mismatch(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(race_result_context=context(race_id=102))

    def test_rejects_payout_context_bet_type_mismatch(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(contexts={"単勝": context(bet_type="馬連")})

    def test_rejects_contexts_with_different_information_cutoffs(self) -> None:
        later = datetime(2026, 7, 24, 10, 0, tzinfo=UTC)
        with self.assertRaises(SimulationValidationError):
            settlement_data(contexts={"単勝": context(bet_type="単勝", cutoff=later)})

    def test_rejects_non_mapping_payout_inputs(self) -> None:
        for publications, contexts in (((), {}), ({}, ())):
            with self.subTest(publications=publications, contexts=contexts), self.assertRaises(SimulationValidationError):
                settlement_data(publications=publications, contexts=contexts)

    def test_uses_simulation_validation_error_for_all_contract_failures(self) -> None:
        with self.assertRaises(SimulationValidationError) as caught:
            settlement_data(publications={"単勝": raw_publication()}, contexts={})
        self.assertEqual(caught.exception.input_identifier, "race_settlement_data")


class RaceSettlementSourceTests(unittest.TestCase):
    def test_is_protocol(self) -> None:
        self.assertTrue(RaceSettlementSource._is_protocol)

    def test_is_not_runtime_checkable(self) -> None:
        self.assertFalse(RaceSettlementSource._is_runtime_protocol)

    def test_has_only_load_method(self) -> None:
        methods = [
            name
            for name, value in RaceSettlementSource.__dict__.items()
            if inspect.isfunction(value) and name != "__init__"
        ]
        self.assertEqual(methods, ["load_settlement_data"])

    def test_load_method_has_keyword_only_race_input(self) -> None:
        signature = inspect.signature(RaceSettlementSource.load_settlement_data)
        self.assertEqual(tuple(signature.parameters), ("self", "race_input"))
        self.assertIs(signature.parameters["race_input"].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_load_method_type_hints_use_boundary_models(self) -> None:
        hints = get_type_hints(RaceSettlementSource.load_settlement_data)
        from scripts.simulation.models import SimulationRaceInput

        self.assertIs(hints["race_input"], SimulationRaceInput)
        self.assertIs(hints["return"], RaceSettlementData)

    def test_protocol_method_is_declaration_only(self) -> None:
        tree = ast.parse(textwrap.dedent(inspect.getsource(RaceSettlementSource.load_settlement_data)))
        expression = tree.body[0].body[0]
        self.assertIsInstance(expression, ast.Expr)
        self.assertIsInstance(expression.value, ast.Constant)
        self.assertIs(expression.value.value, Ellipsis)

    def test_settlement_module_has_no_repository_or_external_io_dependencies(self) -> None:
        path = Path(__file__).parents[1] / "scripts/simulation/settlement.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        forbidden_prefixes = (
            "sqlite3",
            "requests",
            "httpx",
            "urllib",
            "scripts.simulation.repositories",
            "scripts.migrations",
        )
        self.assertFalse(any(name.startswith(forbidden_prefixes) for name in imports))

    def test_settlement_module_does_not_import_provider_implementations(self) -> None:
        path = Path(__file__).parents[1] / "scripts/simulation/settlement.py"
        source = path.read_text(encoding="utf-8")
        for forbidden in ("result_provider", "payout_provider", "odds_provider", "sqlite"):
            self.assertNotIn(forbidden, source)

    def test_settlement_module_does_not_reference_simulator_or_builders(self) -> None:
        source = inspect.getsource(settlement_module)
        for forbidden in (
            "Simulator",
            "ProviderBackedRaceSimulationExecutor",
            "_build_simulation_result_for_race",
            "_build_simulation_summary",
        ):
            self.assertNotIn(forbidden, source)

    def test_models_remain_outside_settlement_module(self) -> None:
        from scripts.simulation.models import SimulationRaceInput

        self.assertEqual(SimulationRaceInput.__module__, "scripts.simulation.models")
        self.assertFalse(hasattr(RaceSettlementData, "target_race_count"))


if __name__ == "__main__":
    unittest.main()
