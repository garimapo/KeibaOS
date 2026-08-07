"""Contract tests for the persisted one-race settlement boundary."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import inspect
from pathlib import Path
import textwrap
from types import MappingProxyType
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
from scripts.prediction.bet_strategy import StrategyConfig
from scripts.simulation.models import (
    InputAuditEntry,
    InputSnapshotAudit,
    SimulationBet,
    SimulationRaceInput,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.prediction.prediction_pipeline import RacePredictionInput
from scripts.prediction.track_engine import RaceTrackConditions
from scripts.simulation.persisted_settlement import (
    PersistedRaceSettlementData,
    PersistedRaceSettlementSource,
)
import scripts.simulation.persisted_settlement as persisted_settlement_module
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutStatus,
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)
from scripts.simulation.validation import SimulationValidationError


UTC = timezone.utc
OBSERVED_AT = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)
FINALIZED_AT = OBSERVED_AT - timedelta(minutes=1)
_UNSET = object()


def bet(*, race_id: int = 101, strategy_id: str = "strategy") -> SimulationBet:
    return SimulationBet(
        race_id=race_id,
        strategy_id=strategy_id,
        bet_type="単勝",
        race_entry_ids=(11,),
        stake=100,
        recommendation_rank=0,
        placed_at_cutoff=FINALIZED_AT,
    )


def race_result(
    *,
    race_id: int = 101,
    finalized_at: datetime = FINALIZED_AT,
    observed_at: datetime = OBSERVED_AT,
) -> PersistedRaceResult:
    return PersistedRaceResult(
        race_id,
        RaceResultStatus.COMPLETE,
        finalized_at,
        observed_at,
        "source",
        (PersistedRaceResultEntry(1, 11, 1, RaceResultEntryStatus.CONFIRMED),),
    )


def publication(
    *,
    race_id: int = 101,
    bet_type: str = "単勝",
    finalized_at: datetime = FINALIZED_AT,
    observed_at: datetime = OBSERVED_AT,
) -> PayoutPublication:
    selection = (11, 12) if bet_type in {"馬連", "ワイド"} else (11,)
    return PayoutPublication(
        race_id,
        bet_type,
        finalized_at,
        observed_at,
        True,
        "source",
        (PayoutRecord(selection, 200, PayoutStatus.WINNING),),
    )


def settlement_data(
    *,
    race_id: object = 101,
    bets: object = _UNSET,
    persisted_result: object = _UNSET,
    publications: object = _UNSET,
) -> PersistedRaceSettlementData:
    return PersistedRaceSettlementData(
        race_id=race_id,  # type: ignore[arg-type]
        bets=(bet(),) if bets is _UNSET else bets,  # type: ignore[arg-type]
        race_result=race_result() if persisted_result is _UNSET else persisted_result,  # type: ignore[arg-type]
        payout_publications_by_bet_type={"単勝": publication()} if publications is _UNSET else publications,  # type: ignore[arg-type]
    )


def strategy_identity() -> StrategyIdentity:
    return build_strategy_identity("persisted-settlement", StrategyConfig())


def race_input() -> SimulationRaceInput:
    cutoff = FINALIZED_AT
    pipeline_input = RacePredictionInput(
        {11: []},
        {11: "Jockey"},
        RaceTrackConditions("Tokyo", 1600, "turf", "firm"),
        {11: 2.0},
        1,
        101,
    )
    audit = InputSnapshotAudit(
        "dataset",
        "source",
        cutoff,
        (
            InputAuditEntry("entry", "entry/11", "source", "entry/11", 11, observed_at=cutoff),
            InputAuditEntry("odds", "odds/11", "source", "odds/11", 11, observed_at=cutoff),
            InputAuditEntry("jockey", "jockey/11", "source", "jockey/11", 11, observed_at=cutoff),
            InputAuditEntry("track", "track", "source", "track", None, observed_at=cutoff),
            InputAuditEntry("past_race", "past_race/11/none", "source", "past_race/11/none", 11, observed_at=cutoff),
        ),
        True,
    )
    return SimulationRaceInput(101, OBSERVED_AT.date(), cutoff, cutoff, pipeline_input, audit)


class PersistedRaceSettlementDataTests(unittest.TestCase):
    def test_constructs_complete_bundle(self) -> None:
        value = settlement_data()
        self.assertEqual(value.race_id, 101)
        self.assertEqual(value.bets, (bet(),))
        self.assertIsInstance(value.race_result, PersistedRaceResult)
        self.assertEqual(set(value.payout_publications_by_bet_type), {"単勝"})

    def test_is_frozen(self) -> None:
        value = settlement_data()
        with self.assertRaises(FrozenInstanceError):
            value.race_id = 102  # type: ignore[misc]

    def test_uses_slots(self) -> None:
        value = settlement_data()
        self.assertFalse(hasattr(value, "__dict__"))
        with self.assertRaises((TypeError, FrozenInstanceError)):
            value.unexpected = "value"  # type: ignore[attr-defined]

    def test_copies_bets_to_tuple(self) -> None:
        supplied = [bet()]
        value = settlement_data(bets=supplied)
        supplied.clear()
        self.assertEqual(value.bets, (bet(),))
        self.assertIsInstance(value.bets, tuple)

    def test_allows_empty_bets(self) -> None:
        self.assertEqual(settlement_data(bets=()).bets, ())

    def test_allows_absent_race_result(self) -> None:
        self.assertIsNone(settlement_data(persisted_result=None).race_result)

    def test_allows_persisted_race_result(self) -> None:
        value = settlement_data(persisted_result=race_result())
        self.assertIsInstance(value.race_result, PersistedRaceResult)

    def test_defensively_copies_payout_publication_mapping(self) -> None:
        supplied = {"単勝": publication()}
        value = settlement_data(publications=supplied)
        supplied.clear()
        self.assertEqual(set(value.payout_publications_by_bet_type), {"単勝"})

    def test_payout_publication_mapping_is_read_only(self) -> None:
        value = settlement_data()
        self.assertIsInstance(value.payout_publications_by_bet_type, MappingProxyType)
        with self.assertRaises(TypeError):
            value.payout_publications_by_bet_type["単勝"] = publication()  # type: ignore[index]

    def test_rejects_invalid_race_id(self) -> None:
        for value in (0, -1, True, "101"):
            with self.subTest(value=value), self.assertRaises(SimulationValidationError):
                settlement_data(race_id=value)

    def test_rejects_non_sequence_bets(self) -> None:
        for value in (None, "bet", {"bet": bet()}, (item for item in (bet(),))):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(SimulationValidationError):
                settlement_data(bets=value)

    def test_rejects_invalid_bet_element(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(bets=(object(),))

    def test_rejects_bet_from_another_race(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(bets=(bet(race_id=102),))

    def test_does_not_require_uniform_bet_strategy(self) -> None:
        value = settlement_data(bets=(bet(strategy_id="strategy-a"), bet(strategy_id="strategy-b")))
        self.assertEqual(tuple(item.strategy_id for item in value.bets), ("strategy-a", "strategy-b"))

    def test_rejects_invalid_race_result_type(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(persisted_result=object())

    def test_rejects_race_result_from_another_race(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(persisted_result=race_result(race_id=102))

    def test_rejects_non_mapping_publications(self) -> None:
        for value in (None, (), "単勝"):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(SimulationValidationError):
                settlement_data(publications=value)

    def test_rejects_invalid_publication_mapping_key(self) -> None:
        for key in (1, "", "unsupported"):
            with self.subTest(key=key), self.assertRaises(SimulationValidationError):
                settlement_data(publications={key: publication()})

    def test_rejects_invalid_publication_mapping_value(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(publications={"単勝": object()})

    def test_rejects_publication_from_another_race(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(publications={"単勝": publication(race_id=102)})

    def test_rejects_publication_bet_type_mismatch(self) -> None:
        with self.assertRaises(SimulationValidationError):
            settlement_data(publications={"単勝": publication(bet_type="馬連")})

    def test_accepts_empty_publications(self) -> None:
        self.assertEqual(dict(settlement_data(publications={}).payout_publications_by_bet_type), {})

    def test_does_not_impose_prediction_cutoff_constraints(self) -> None:
        finalized_at = OBSERVED_AT + timedelta(minutes=10)
        observed_at = OBSERVED_AT + timedelta(minutes=20)
        value = settlement_data(
            persisted_result=race_result(finalized_at=finalized_at, observed_at=observed_at),
            publications={
                "単勝": publication(finalized_at=finalized_at, observed_at=observed_at)
            },
        )
        self.assertEqual(value.race_result.finalized_at, finalized_at)  # type: ignore[union-attr]
        self.assertEqual(value.payout_publications_by_bet_type["単勝"].observed_at, observed_at)

    def test_uses_simulation_validation_error_for_contract_failure(self) -> None:
        with self.assertRaises(SimulationValidationError) as caught:
            settlement_data(publications={"単勝": object()})
        self.assertEqual(caught.exception.input_identifier, "persisted_race_settlement_data")


class PersistedRaceSettlementSourceTests(unittest.TestCase):
    def test_is_protocol(self) -> None:
        self.assertTrue(PersistedRaceSettlementSource._is_protocol)

    def test_is_not_runtime_checkable(self) -> None:
        self.assertFalse(PersistedRaceSettlementSource._is_runtime_protocol)

    def test_has_only_load_method(self) -> None:
        methods = [
            name
            for name, value in PersistedRaceSettlementSource.__dict__.items()
            if inspect.isfunction(value) and name != "__init__"
        ]
        self.assertEqual(methods, ["load_settlement_data"])

    def test_load_method_has_keyword_only_arguments(self) -> None:
        signature = inspect.signature(PersistedRaceSettlementSource.load_settlement_data)
        self.assertEqual(tuple(signature.parameters), ("self", "race_input", "strategy_identity"))
        self.assertIs(signature.parameters["race_input"].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(signature.parameters["strategy_identity"].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_load_method_type_hints_use_boundary_models(self) -> None:
        hints = get_type_hints(PersistedRaceSettlementSource.load_settlement_data)
        self.assertIs(hints["race_input"], SimulationRaceInput)
        self.assertIs(hints["strategy_identity"], StrategyIdentity)
        self.assertIs(hints["return"], PersistedRaceSettlementData)

    def test_protocol_method_is_declaration_only(self) -> None:
        tree = ast.parse(textwrap.dedent(inspect.getsource(PersistedRaceSettlementSource.load_settlement_data)))
        expression = tree.body[0].body[0]
        self.assertIsInstance(expression, ast.Expr)
        self.assertIsInstance(expression.value, ast.Constant)
        self.assertIs(expression.value.value, Ellipsis)

    def test_protocol_has_no_concrete_source_implementation(self) -> None:
        source = inspect.getsource(persisted_settlement_module)
        self.assertNotIn("class PersistedRaceSimulationExecutor", source)
        self.assertNotIn("class RepositoryBacked", source)

    def test_module_has_no_repository_implementation_or_external_io_dependency(self) -> None:
        path = Path(__file__).parents[1] / "scripts/simulation/persisted_settlement.py"
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
            "scripts.simulation.repositories.sqlite",
            "scripts.migrations",
        )
        self.assertFalse(any(name.startswith(forbidden_prefixes) for name in imports))

    def test_module_does_not_import_raw_models_or_providers(self) -> None:
        source = inspect.getsource(persisted_settlement_module)
        for forbidden in (
            "RawRaceResult",
            "RawPayoutPublication",
            "ProviderContext",
            "RaceEntryUniverse",
            "result_provider",
            "payout_provider",
            "odds_provider",
        ):
            self.assertNotIn(forbidden, source)

    def test_module_does_not_reference_executors_or_builders(self) -> None:
        source = inspect.getsource(persisted_settlement_module)
        for forbidden in (
            "ProviderBackedRaceSimulationExecutor",
            "_build_simulation_result_for_race",
            "_build_simulation_summary",
            "Simulator",
        ):
            self.assertNotIn(forbidden, source)

    def test_persisted_boundary_is_not_package_exported(self) -> None:
        self.assertFalse(hasattr(simulation_package, "PersistedRaceSettlementData"))
        self.assertFalse(hasattr(simulation_package, "PersistedRaceSettlementSource"))

    def test_models_remain_outside_persisted_settlement_module(self) -> None:
        self.assertEqual(SimulationRaceInput.__module__, "scripts.simulation.models")
        self.assertFalse(hasattr(PersistedRaceSettlementData, "target_race_count"))

    def test_protocol_types_can_be_used_without_a_source_instance(self) -> None:
        self.assertIsInstance(strategy_identity(), StrategyIdentity)
        self.assertIsInstance(race_input(), SimulationRaceInput)


if __name__ == "__main__":
    unittest.main()
