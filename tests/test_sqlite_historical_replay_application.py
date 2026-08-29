from __future__ import annotations

import ast
from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import inspect
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import get_type_hints
import unittest
from unittest.mock import patch

import scripts.simulation as simulation_package
import scripts.simulation.sqlite_historical_replay_application as module
from scripts.prediction.allocation_policy import (
    AllocationPolicyConfig,
    build_allocation_policy_identity,
)
from scripts.prediction.bet_strategy import StrategyConfig
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.historical_input_snapshots import HistoricalInputSnapshot
from scripts.simulation.historical_replay_request_document import (
    HistoricalReplayRaceRequest,
    HistoricalReplayRequestDocument,
)
from scripts.simulation.models import (
    SimulationBet,
    SimulationRunContext,
    SimulationSummary,
    StrategyIdentity,
    build_strategy_identity,
)
from scripts.simulation.stake_allocation import BetStakeBudget
from tests.test_official_settlement_acquisition import _snapshot as provider_snapshot


NOW = datetime(2026, 8, 29, 12, tzinfo=UTC)


class _Cursor:
    def __init__(self, row: object) -> None:
        self._row = row

    def fetchone(self) -> object:
        return self._row


class _Connection:
    def __init__(
        self,
        *,
        name: str,
        events: list[str],
        query_only_row: object = (1,),
        close_error: BaseException | None = None,
    ) -> None:
        self.name = name
        self.events = events
        self.query_only_row = query_only_row
        self.close_error = close_error
        self.closed = False

    def execute(self, statement: str) -> _Cursor:
        self.events.append(f"{self.name}:{statement}")
        if statement == "PRAGMA query_only":
            return _Cursor(self.query_only_row)
        return _Cursor(None)

    def close(self) -> None:
        self.events.append(f"close:{self.name}")
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class _SnapshotRepository:
    def __init__(self, *, connection: object, snapshots: Mapping[object, object], events: list[str]) -> None:
        self.connection = connection
        self._snapshots = snapshots
        self.events = events
        self.calls: list[object] = []
        self.events.append("snapshot-repository")

    def load_snapshot_by_identity(self, *, identity: object) -> object:
        self.calls.append(identity)
        self.events.append("snapshot-load")
        return self._snapshots.get(identity)

    def load_latest_snapshot(self, **_: object) -> object:
        raise AssertionError("latest snapshot lookup is forbidden")


class _PlanRepository:
    def __init__(self, *, connection: object, events: list[str]) -> None:
        self.connection = connection
        self.events = events
        self.events.append("plan-repository")


class _ResultRepository:
    def __init__(self, connection: object, events: list[str]) -> None:
        self.connection = connection
        self.events = events
        self.events.append("result-repository")


class _PayoutRepository:
    def __init__(self, connection: object, events: list[str]) -> None:
        self.connection = connection
        self.events = events
        self.events.append("payout-repository")


class _CaptureRepository:
    def __init__(self, *, connection: object, events: list[str], kind: str) -> None:
        self.connection = connection
        self.events = events
        self.kind = kind
        self.events.append(f"{kind}-capture-repository")

    def load_capture(self, **_: object) -> object:
        raise AssertionError("C4i2 must not load captures")

    def save_capture(self, **_: object) -> None:
        raise AssertionError("C4i2 must not save captures")


class SQLiteHistoricalReplayApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.jra = self._snapshot("JRA", race_id=700, start_offset=20)
        self.nar = self._snapshot("NAR", race_id=800, start_offset=10)
        self.document = self._document((self.jra, self.nar))

    def _snapshot(self, provider: str, *, race_id: int, start_offset: int) -> HistoricalInputSnapshot:
        snapshot = provider_snapshot(provider)
        race = replace(
            snapshot.race,
            scheduled_start_at=snapshot.race.scheduled_start_at + timedelta(minutes=start_offset),
        )
        return replace(snapshot, internal_race_id=race_id, race=race)

    def _strategy(self) -> StrategyIdentity:
        return build_strategy_identity(
            "RuleBasedBetStrategy",
            StrategyConfig(
                max_bet_count=4,
                allocation_policy=AllocationPolicyConfig(
                    policy_name="fixed_stake_per_recommendation",
                    policy_version="1",
                    parameters={"stake_amount": 100},
                ),
            ),
        )

    def _document(
        self,
        snapshots: tuple[HistoricalInputSnapshot, ...],
        *,
        catalogs: Mapping[int, Mapping[str, str]] | None = None,
    ) -> HistoricalReplayRequestDocument:
        context = SimulationRunContext(
            run_id="run",
            dataset_id=snapshots[0].identity.dataset_id,
            started_at=NOW,
            target_commit_id="commit",
        )
        supplied_catalogs = catalogs or {
            snapshot.internal_race_id: {
                "単勝": f"{snapshot.internal_race_id}-win",
                "馬連": f"{snapshot.internal_race_id}-pair",
                "ワイド": f"{snapshot.internal_race_id}-wide",
                "3連複": f"{snapshot.internal_race_id}-triple",
            }
            for snapshot in snapshots
        }
        races = tuple(
            HistoricalReplayRaceRequest(
                snapshot_identity=snapshot.identity,
                internal_race_id=snapshot.internal_race_id,
                settlement_information_cutoff=NOW + timedelta(hours=1),
                result_capture_id=f"{snapshot.internal_race_id}-result",
                payout_capture_catalog_by_bet_type=supplied_catalogs[snapshot.internal_race_id],
            )
            for snapshot in snapshots
        )
        archive_paths = {
            "JRA/jra_official": self.root / "jra archive %.sqlite",
            "NAR/nar_official": self.root / "nar archive %.sqlite",
        }
        return HistoricalReplayRequestDocument(
            schema_version=1,
            source_path=self.root / "request.json",
            database_path=self.root / "main.sqlite",
            capture_archive_paths_by_provider=archive_paths,
            run_context=context,
            strategy_identity=self._strategy(),
            budgets_by_race_id={
                snapshot.internal_race_id: BetStakeBudget(total_amount=1_000)
                for snapshot in snapshots
            },
            races=races,
        )

    def _plan(
        self,
        snapshot: HistoricalInputSnapshot,
        *,
        bet_types: tuple[str, ...] = (),
        run_id: str | None = None,
        strategy_id: str | None = None,
        strategy_config_hash: str | None = None,
        information_cutoff: datetime | None = None,
        race_id: int | None = None,
    ) -> SimulationBetPlanSnapshot:
        strategy = self.document.strategy_identity
        selections = {
            "単勝": (snapshot.entries[0].race_entry_id,),
            "馬連": (snapshot.entries[0].race_entry_id, snapshot.entries[1].race_entry_id),
            "ワイド": (snapshot.entries[0].race_entry_id, snapshot.entries[1].race_entry_id),
            "3連複": tuple(entry.race_entry_id for entry in snapshot.entries[:3]),
        }
        bets: list[SimulationBet] = []
        pair_selections = (
            (snapshot.entries[0].race_entry_id, snapshot.entries[1].race_entry_id),
            (snapshot.entries[0].race_entry_id, snapshot.entries[2].race_entry_id),
            (snapshot.entries[1].race_entry_id, snapshot.entries[2].race_entry_id),
        )
        for index, bet_type in enumerate(bet_types):
            selection = selections[bet_type]
            if bet_type == "単勝":
                selection = (snapshot.entries[index % len(snapshot.entries)].race_entry_id,)
            elif bet_type in {"馬連", "ワイド"}:
                selection = pair_selections[index % len(pair_selections)]
            bets.append(
                SimulationBet(
                    race_id=snapshot.internal_race_id,
                    strategy_id=strategy.strategy_id,
                    bet_type=bet_type,
                    race_entry_ids=selection,
                    stake=100,
                    recommendation_rank=index,
                    placed_at_cutoff=snapshot.information_cutoff,
                )
            )
        return SimulationBetPlanSnapshot(
            identity=SimulationBetPlanIdentity(
                run_id=self.document.run_context.run_id if run_id is None else run_id,
                race_id=snapshot.internal_race_id if race_id is None else race_id,
                strategy_id=strategy.strategy_id if strategy_id is None else strategy_id,
                strategy_config_hash=(
                    strategy.strategy_config_hash
                    if strategy_config_hash is None
                    else strategy_config_hash
                ),
                information_cutoff=(
                    snapshot.information_cutoff
                    if information_cutoff is None
                    else information_cutoff
                ),
            ),
            policy_identity=build_allocation_policy_identity(
                strategy.strategy_config.allocation_policy,
            ),
            budget=self.document.budgets_by_race_id[snapshot.internal_race_id],
            bets=tuple(bets),
        )

    def _run(
        self,
        *,
        document: HistoricalReplayRequestDocument | None = None,
        snapshots: Mapping[object, object] | None = None,
        returned_plans: object | None = None,
        c4g1_error: BaseException | None = None,
        acquire_error_at: int | None = None,
        final_error: BaseException | None = None,
        archive_query_only_rows: tuple[object, ...] = ((1,), (1,)),
        close_errors: Mapping[str, BaseException] | None = None,
        observed: dict[str, object] | None = None,
    ) -> tuple[object, dict[str, object], list[str]]:
        replay_document = self.document if document is None else document
        canonical = tuple(
            sorted(
                (self.jra, self.nar),
                key=lambda snapshot: (
                    snapshot.race.scheduled_start_at,
                    snapshot.internal_race_id,
                ),
            )
        )
        snapshot_values = snapshots or {
            self.jra.identity: self.jra,
            self.nar.identity: self.nar,
        }
        coherent_plans = tuple(self._plan(snapshot) for snapshot in canonical)
        plan_values = coherent_plans if returned_plans is None else returned_plans
        events: list[str] = []
        errors = dict(close_errors or {})
        main = _Connection(name="main", events=events, close_error=errors.get("main"))
        archive_connections = [
            _Connection(
                name=f"archive-{index}",
                events=events,
                query_only_row=row,
                close_error=errors.get(f"archive-{index}"),
            )
            for index, row in enumerate(archive_query_only_rows)
        ]
        connection_values = [main, *archive_connections]
        calls: dict[str, object] = {
            "connections": connection_values,
            "migrations": [],
            "c4g1": [],
            "acquisition": [],
            "final": [],
            "snapshot_repositories": [],
            "plan_repositories": [],
            "result_repositories": [],
            "payout_repositories": [],
            "capture_repositories": [],
        }
        if observed is not None:
            observed["calls"] = calls
            observed["events"] = events

        def connect(*args: object, **kwargs: object) -> _Connection:
            events.append("connect")
            if not connection_values:
                raise AssertionError("unexpected connection")
            return connection_values.pop(0)

        def migrate(connection: object) -> None:
            calls["migrations"].append(connection)  # type: ignore[union-attr]
            events.append("migrate")

        def snapshot_factory(*, connection: object) -> _SnapshotRepository:
            repository = _SnapshotRepository(
                connection=connection,
                snapshots=snapshot_values,
                events=events,
            )
            calls["snapshot_repositories"].append(repository)  # type: ignore[union-attr]
            return repository

        def plan_factory(*, connection: object) -> _PlanRepository:
            repository = _PlanRepository(connection=connection, events=events)
            calls["plan_repositories"].append(repository)  # type: ignore[union-attr]
            return repository

        def result_factory(connection: object) -> _ResultRepository:
            repository = _ResultRepository(connection, events)
            calls["result_repositories"].append(repository)  # type: ignore[union-attr]
            return repository

        def payout_factory(connection: object) -> _PayoutRepository:
            repository = _PayoutRepository(connection, events)
            calls["payout_repositories"].append(repository)  # type: ignore[union-attr]
            return repository

        def capture_factory(kind: str):
            def factory(*, connection: object) -> _CaptureRepository:
                repository = _CaptureRepository(connection=connection, events=events, kind=kind)
                calls["capture_repositories"].append(repository)  # type: ignore[union-attr]
                return repository
            return factory

        def c4g1(**kwargs: object) -> object:
            calls["c4g1"].append(kwargs)  # type: ignore[union-attr]
            events.append("c4g1")
            if c4g1_error is not None:
                raise c4g1_error
            return plan_values

        def acquire(**kwargs: object) -> object:
            calls["acquisition"].append(kwargs)  # type: ignore[union-attr]
            events.append("acquire")
            if acquire_error_at is not None and len(calls["acquisition"]) == acquire_error_at:  # type: ignore[arg-type]
                raise RuntimeError("acquisition failure")
            return object()

        summary = object()

        def final(**kwargs: object) -> object:
            calls["final"].append(kwargs)  # type: ignore[union-attr]
            events.append("final")
            if final_error is not None:
                raise final_error
            return summary

        with ExitStack() as stack:
            stack.enter_context(patch.object(module.sqlite3, "connect", side_effect=connect))
            stack.enter_context(patch.object(module, "apply_migrations", side_effect=migrate))
            stack.enter_context(patch.object(module, "SQLiteHistoricalInputSnapshotRepository", side_effect=snapshot_factory))
            stack.enter_context(patch.object(module, "SQLiteSimulationBetPlanSnapshotRepository", side_effect=plan_factory))
            stack.enter_context(patch.object(module, "SQLiteRaceResultRepository", side_effect=result_factory))
            stack.enter_context(patch.object(module, "SQLitePayoutRepository", side_effect=payout_factory))
            stack.enter_context(patch.object(module, "SQLiteJRAOfficialResponseCaptureRepository", side_effect=capture_factory("jra")))
            stack.enter_context(patch.object(module, "SQLiteNAROfficialResponseCaptureRepository", side_effect=capture_factory("nar")))
            stack.enter_context(patch.object(module, "execute_and_persist_historical_bet_plans", side_effect=c4g1))
            stack.enter_context(patch.object(module, "acquire_and_persist_official_settlement_facts", side_effect=acquire))
            stack.enter_context(patch.object(module, "execute_final_historical_settlement_simulation", side_effect=final))
            result = module.run_sqlite_historical_replay(document=replay_document)
        calls["summary"] = summary
        return result, calls, events

    def test_public_surface_signature_hints_and_error_hierarchy_are_exact(self) -> None:
        self.assertEqual(
            module.__all__,
            ("SQLiteHistoricalReplayApplicationError", "run_sqlite_historical_replay"),
        )
        self.assertFalse(hasattr(simulation_package, "run_sqlite_historical_replay"))
        self.assertFalse(hasattr(simulation_package, "SQLiteHistoricalReplayApplicationError"))
        self.assertTrue(issubclass(module.SQLiteHistoricalReplayApplicationError, ValueError))
        signature = inspect.signature(module.run_sqlite_historical_replay)
        self.assertEqual(tuple(signature.parameters), ("document",))
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )
        self.assertEqual(
            get_type_hints(module.run_sqlite_historical_replay),
            {
                "document": HistoricalReplayRequestDocument,
                "return": SimulationSummary,
            },
        )

    def test_invalid_document_fails_before_connection_open(self) -> None:
        with patch.object(module.sqlite3, "connect") as connect:
            with self.assertRaises(module.SQLiteHistoricalReplayApplicationError):
                module.run_sqlite_historical_replay(document=object())  # type: ignore[arg-type]
        connect.assert_not_called()

    def test_full_canonical_composition_preserves_shared_objects_and_returns_final_identity(self) -> None:
        result, calls, events = self._run()
        canonical = (self.nar, self.jra)
        self.assertIs(result, calls["summary"])
        self.assertEqual(len(calls["migrations"]), 1)
        self.assertEqual(len(calls["c4g1"]), 1)
        c4g1 = calls["c4g1"][0]  # type: ignore[index]
        self.assertEqual(c4g1["snapshots"], canonical)
        self.assertIs(c4g1["run_context"], self.document.run_context)
        self.assertIs(c4g1["strategy_identity"], self.document.strategy_identity)
        plan_repository = calls["plan_repositories"][0]  # type: ignore[index]
        self.assertIs(c4g1["snapshot_repository"], plan_repository)
        self.assertEqual(len(calls["acquisition"]), 2)
        self.assertEqual(len(calls["final"]), 1)
        final = calls["final"][0]  # type: ignore[index]
        self.assertEqual(final["snapshots"], canonical)
        self.assertIs(final["bet_plan_snapshot_source"], plan_repository)
        self.assertIs(final["race_result_repository"], calls["result_repositories"][0])  # type: ignore[index]
        self.assertIs(final["payout_repository"], calls["payout_repositories"][0])  # type: ignore[index]
        self.assertEqual(
            tuple(final["settlement_cutoffs_by_race_id"]),
            (self.nar.internal_race_id, self.jra.internal_race_id),
        )
        self.assertLess(events.index("c4g1"), events.index("result-repository"))
        self.assertLess(events.index("payout-repository"), events.index("jra-capture-repository"))
        self.assertLess(events.index("jra-capture-repository"), events.index("acquire"))
        self.assertLess(events.index("nar-capture-repository"), events.index("acquire"))

    def test_manifest_lookup_order_precedes_canonical_execution_order(self) -> None:
        result, calls, _ = self._run()
        self.assertIs(result, calls["summary"])
        repository = calls["snapshot_repositories"][0]  # type: ignore[index]
        self.assertEqual(repository.calls, [self.jra.identity, self.nar.identity])
        c4g1 = calls["c4g1"][0]  # type: ignore[index]
        self.assertEqual(c4g1["snapshots"], (self.nar, self.jra))

    def test_preplanning_snapshot_failures_are_owned_and_block_every_settlement_action(self) -> None:
        scenarios: tuple[tuple[str, Mapping[object, object]], ...] = (
            ("missing", {self.jra.identity: self.jra}),
            ("wrong_type", {self.jra.identity: object(), self.nar.identity: self.nar}),
            (
                "identity_mismatch",
                {self.jra.identity: self.nar, self.nar.identity: self.nar},
            ),
            (
                "internal_id_mismatch",
                {self.jra.identity: replace(self.jra, internal_race_id=999), self.nar.identity: self.nar},
            ),
        )
        for label, values in scenarios:
            with self.subTest(label=label):
                with self.assertRaises(module.SQLiteHistoricalReplayApplicationError):
                    self._run(snapshots=values)

    def test_c4g1_failure_propagates_unchanged_before_archives_or_settlement_repositories(self) -> None:
        error = RuntimeError("planning")
        observed: dict[str, object] = {}
        with self.assertRaises(RuntimeError) as raised:
            self._run(c4g1_error=error, observed=observed)
        self.assertIs(raised.exception, error)
        calls = observed["calls"]
        self.assertEqual(len(calls["c4g1"]), 1)  # type: ignore[index]
        self.assertEqual(calls["result_repositories"], [])  # type: ignore[index]
        self.assertEqual(calls["payout_repositories"], [])  # type: ignore[index]
        self.assertEqual(calls["capture_repositories"], [])  # type: ignore[index]
        self.assertEqual(calls["acquisition"], [])  # type: ignore[index]
        self.assertEqual(calls["final"], [])  # type: ignore[index]

    def test_returned_plan_batch_incoherence_fails_before_archive_open(self) -> None:
        canonical = (self.nar, self.jra)
        invalid_values = (
            [self._plan(canonical[0]), self._plan(canonical[1])],
            (self._plan(canonical[0]),),
            (object(), self._plan(canonical[1])),
            (self._plan(canonical[1]), self._plan(canonical[0])),
            (self._plan(canonical[0], run_id="other"), self._plan(canonical[1])),
            (self._plan(canonical[0], strategy_id="other"), self._plan(canonical[1])),
            (self._plan(canonical[0], information_cutoff=NOW), self._plan(canonical[1])),
        )
        for returned_plans in invalid_values:
            with self.subTest(kind=type(returned_plans).__name__):
                with self.assertRaises(module.SQLiteHistoricalReplayApplicationError):
                    self._run(returned_plans=returned_plans)

    def test_whole_batch_catalog_preflight_uses_returned_plan_bets_only_and_blocks_archives(self) -> None:
        canonical = (self.nar, self.jra)
        plans = (
            self._plan(canonical[0], bet_types=("ワイド", "単勝", "ワイド")),
            self._plan(canonical[1], bet_types=("馬連",)),
        )
        catalogs = {
            self.nar.internal_race_id: {"ワイド": "wide", "単勝": "win", "3連複": "unused"},
            self.jra.internal_race_id: {},
        }
        document = self._document((self.jra, self.nar), catalogs=catalogs)
        observed: dict[str, object] = {}
        with self.assertRaises(module.SQLiteHistoricalReplayApplicationError):
            self._run(document=document, returned_plans=plans, observed=observed)
        calls = observed["calls"]
        self.assertEqual(calls["result_repositories"], [])  # type: ignore[index]
        self.assertEqual(calls["payout_repositories"], [])  # type: ignore[index]
        self.assertEqual(calls["capture_repositories"], [])  # type: ignore[index]
        self.assertEqual(calls["acquisition"], [])  # type: ignore[index]

    def test_required_only_payout_mapping_capture_value_reuse_and_no_bet_are_exact(self) -> None:
        canonical = (self.nar, self.jra)
        plans = (
            self._plan(canonical[0], bet_types=()),
            self._plan(canonical[1], bet_types=("馬連", "単勝", "馬連")),
        )
        catalogs = {
            self.nar.internal_race_id: {"単勝": "unused"},
            self.jra.internal_race_id: {"馬連": "shared", "単勝": "shared", "ワイド": "unused"},
        }
        document = self._document((self.jra, self.nar), catalogs=catalogs)
        result, calls, _ = self._run(document=document, returned_plans=plans)
        self.assertIs(result, calls["summary"])
        acquisition = calls["acquisition"]  # type: ignore[assignment]
        self.assertEqual(acquisition[0]["payout_capture_ids_by_bet_type"], {})
        self.assertEqual(
            acquisition[1]["payout_capture_ids_by_bet_type"],
            {"馬連": "shared", "単勝": "shared"},
        )

    def test_provider_archives_open_in_canonical_first_occurrence_order_and_are_selected_exactly(self) -> None:
        _, calls, events = self._run()
        self.assertEqual(events.index("connect"), 0)
        self.assertLess(events.index("archive-0:PRAGMA query_only=ON"), events.index("archive-1:PRAGMA query_only=ON"))
        acquisition = calls["acquisition"]  # type: ignore[assignment]
        capture_repositories = calls["capture_repositories"]  # type: ignore[assignment]
        self.assertIs(acquisition[0]["capture_archive"], capture_repositories[0])
        self.assertIs(acquisition[1]["capture_archive"], capture_repositories[1])

    def test_c4h4a_first_failure_stops_later_calls_and_blocks_final(self) -> None:
        observed: dict[str, object] = {}
        with self.assertRaisesRegex(RuntimeError, "acquisition failure"):
            self._run(acquire_error_at=1, observed=observed)
        calls = observed["calls"]
        self.assertEqual(len(calls["acquisition"]), 1)  # type: ignore[index]
        self.assertEqual(calls["final"], [])  # type: ignore[index]

    def test_c4h4b_exception_propagates_unchanged(self) -> None:
        error = RuntimeError("final")
        with self.assertRaises(RuntimeError) as raised:
            self._run(final_error=error)
        self.assertIs(raised.exception, error)

    def test_query_only_invalid_state_is_owned_and_connection_still_closes(self) -> None:
        with self.assertRaises(module.SQLiteHistoricalReplayApplicationError):
            self._run(archive_query_only_rows=((0,),))

    def test_close_order_attempts_all_connections_and_primary_error_wins(self) -> None:
        primary = RuntimeError("planning")
        close_error = RuntimeError("close")
        with self.assertRaises(RuntimeError) as raised:
            self._run(c4g1_error=primary, close_errors={"main": close_error})
        self.assertIs(raised.exception, primary)

    def test_close_failures_without_primary_raise_first_reverse_order_error_after_all_attempts(self) -> None:
        events: list[str] = []
        first = RuntimeError("archive close")
        second = RuntimeError("main close")
        main = _Connection(name="main", events=events, close_error=second)
        archive = _Connection(name="archive", events=events, close_error=first)
        with self.assertRaises(RuntimeError) as raised:
            module._close_owned_connections([main, archive])
        self.assertIs(raised.exception, first)
        self.assertEqual(events, ["close:archive", "close:main"])

    def test_wrong_strategy_hash_is_rejected_before_archive_open(self) -> None:
        canonical = (self.nar, self.jra)
        observed: dict[str, object] = {}
        plans = (
            self._plan(canonical[0], strategy_config_hash="b" * 64),
            self._plan(canonical[1]),
        )
        with self.assertRaises(module.SQLiteHistoricalReplayApplicationError):
            self._run(returned_plans=plans, observed=observed)
        calls = observed["calls"]
        self.assertEqual(calls["capture_repositories"], [])  # type: ignore[index]

    def test_read_only_uri_allows_read_rejects_write_and_does_not_create_missing_target(self) -> None:
        for name in ("archive with space %.sqlite", "archive?reserved.sqlite"):
            if os.name == "nt" and "?" in name:
                continue
            with self.subTest(name=name):
                path = self.root / name
                writer = sqlite3.connect(path)
                writer.execute("CREATE TABLE facts(value INTEGER)")
                writer.execute("INSERT INTO facts VALUES(1)")
                writer.commit()
                writer.close()
                connection = sqlite3.connect(module._read_only_archive_uri(path), uri=True)
                self.assertEqual(connection.execute("SELECT value FROM facts").fetchone(), (1,))
                with self.assertRaises(sqlite3.OperationalError):
                    connection.execute("INSERT INTO facts VALUES(2)")
                connection.close()
        missing = self.root / "missing archive.sqlite"
        with self.assertRaises(sqlite3.OperationalError):
            sqlite3.connect(module._read_only_archive_uri(missing), uri=True)
        self.assertFalse(missing.exists())

    @unittest.skipUnless(os.name == "nt", "Windows drive URI assertion")
    def test_windows_path_is_a_valid_file_uri(self) -> None:
        uri = module._read_only_archive_uri(self.root / "windows archive.sqlite")
        self.assertTrue(uri.startswith("file:///"))
        self.assertTrue(uri.endswith("?mode=ro"))

    def test_static_ownership_excludes_network_capture_io_clock_pipeline_and_direct_capture_load(self) -> None:
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = (
            "import requests",
            "import httpx",
            "PredictionPipeline",
            "build_historical_prediction_pipeline",
            "load_latest_snapshot(",
            "save_capture(",
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "ATTACH",
            "load_capture(",
        )
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, source)
        cleanup_function = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_close_owned_connections"
        )
        base_exception_handlers = [
            node
            for node in ast.walk(cleanup_function)
            if isinstance(node, ast.ExceptHandler)
            and isinstance(node.type, ast.Name)
            and node.type.id == "BaseException"
        ]
        self.assertEqual(len(base_exception_handlers), 1)
