"""Application service for one ordered persisted multi-race simulation run."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from scripts.simulation.models import SimulationRaceInput, SimulationSummary
from scripts.simulation.persisted_bet_plan_service import PersistedSimulationBetPlanService
from scripts.simulation.persisted_executor import PersistedRaceSimulationExecutor
from scripts.simulation.persisted_simulation_bet_source import PersistedSimulationBetSource
from scripts.simulation.repository_backed_persisted_settlement_source import (
    RepositoryBackedPersistedRaceSettlementSource,
)
from scripts.simulation.simulator import Simulator
from scripts.simulation.stake_allocation import BetStakeBudget


class PersistedSimulationRunService:
    """Plan, persist, and settle one ordered multi-race simulation run."""

    __slots__ = ("_bet_plan_service", "_simulator")

    def __init__(
        self,
        *,
        bet_plan_service: PersistedSimulationBetPlanService,
        simulator: Simulator,
    ) -> None:
        self._validate_composition(bet_plan_service, simulator)
        self._bet_plan_service = bet_plan_service
        self._simulator = simulator

    def run(
        self,
        *,
        race_inputs: Sequence[SimulationRaceInput],
        budgets_by_race_id: Mapping[int, BetStakeBudget],
    ) -> SimulationSummary:
        race_input_values = self._validate_race_inputs(race_inputs)
        budgets = self._validate_budgets(budgets_by_race_id, race_input_values)
        self._validate_composition(self._bet_plan_service, self._simulator)
        ordered_inputs = tuple(
            sorted(
                race_input_values,
                key=lambda race_input: (
                    race_input.scheduled_start_at,
                    race_input.race_id,
                ),
            )
        )

        for race_input in ordered_inputs:
            self._bet_plan_service.build_and_save(
                race_input=race_input,
                budget=budgets[race_input.race_id],
            )
        return self._simulator.run(race_inputs=ordered_inputs)

    @staticmethod
    def _validate_composition(
        bet_plan_service: PersistedSimulationBetPlanService,
        simulator: Simulator,
    ) -> None:
        if type(bet_plan_service) is not PersistedSimulationBetPlanService:
            raise ValueError("bet_plan_service must be a PersistedSimulationBetPlanService")
        if type(simulator) is not Simulator:
            raise ValueError("simulator must be a Simulator")

        executor = simulator.race_executor
        if type(executor) is not PersistedRaceSimulationExecutor:
            raise ValueError(
                "simulator.race_executor must be a PersistedRaceSimulationExecutor"
            )
        settlement_source = executor.settlement_source
        if type(settlement_source) is not RepositoryBackedPersistedRaceSettlementSource:
            raise ValueError(
                "executor.settlement_source must be a "
                "RepositoryBackedPersistedRaceSettlementSource"
            )
        bet_source = settlement_source.bet_source
        if type(bet_source) is not PersistedSimulationBetSource:
            raise ValueError(
                "settlement_source.bet_source must be a PersistedSimulationBetSource"
            )
        if bet_plan_service.strategy_identity is not simulator.strategy_identity:
            raise ValueError(
                "bet_plan_service.strategy_identity must be simulator.strategy_identity"
            )
        if simulator.strategy_identity is not executor.strategy_identity:
            raise ValueError(
                "simulator.strategy_identity must be executor.strategy_identity"
            )
        if bet_plan_service.run_context is not bet_source.run_context:
            raise ValueError(
                "bet_plan_service.run_context must be bet_source.run_context"
            )

    @staticmethod
    def _validate_race_inputs(
        race_inputs: Sequence[SimulationRaceInput],
    ) -> tuple[SimulationRaceInput, ...]:
        if (
            not isinstance(race_inputs, Sequence)
            or isinstance(race_inputs, (str, bytes, bytearray, Mapping))
        ):
            raise ValueError("race_inputs must be a Sequence")
        race_input_values = tuple(race_inputs)
        if not all(
            isinstance(race_input, SimulationRaceInput)
            for race_input in race_input_values
        ):
            raise ValueError("race_inputs must contain SimulationRaceInput values")
        race_ids = tuple(race_input.race_id for race_input in race_input_values)
        if len(set(race_ids)) != len(race_ids):
            raise ValueError("race_inputs must not contain duplicate race_id values")
        return race_input_values

    @staticmethod
    def _validate_budgets(
        budgets_by_race_id: Mapping[int, BetStakeBudget],
        race_inputs: tuple[SimulationRaceInput, ...],
    ) -> dict[int, BetStakeBudget]:
        if not isinstance(budgets_by_race_id, Mapping):
            raise ValueError("budgets_by_race_id must be a Mapping")
        budgets = dict(budgets_by_race_id)
        if any(
            not isinstance(race_id, int)
            or isinstance(race_id, bool)
            or race_id <= 0
            for race_id in budgets
        ):
            raise ValueError("budget race IDs must be positive integers")
        if not all(isinstance(budget, BetStakeBudget) for budget in budgets.values()):
            raise ValueError("budgets_by_race_id must contain BetStakeBudget values")
        race_ids = {race_input.race_id for race_input in race_inputs}
        if set(budgets) != race_ids:
            raise ValueError("budget race IDs must exactly match race input IDs")
        return budgets
