from __future__ import annotations

import ast
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
import inspect
from pathlib import Path
from typing import get_type_hints
import unittest
from unittest.mock import patch

import scripts.simulation as simulation_package
import scripts.simulation.official_settlement_acquisition as module
from scripts.prediction.allocation_policy import AllocationPolicyConfig, build_allocation_policy_identity
from scripts.prediction.bet_strategy import StrategyConfig
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.bet_plan_snapshot_repository import SimulationBetPlanSnapshotSource
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalEntryIdentity,
    HistoricalExternalRaceIdentity,
    HistoricalInputProvenance,
    HistoricalInputSnapshot,
    HistoricalInputSnapshotIdentity,
    HistoricalRaceEntrySnapshot,
    HistoricalRaceSnapshot,
    HistoricalSourceIdentity,
)
from scripts.simulation.jra_official_identity import build_jra_external_entry_id, parse_jra_result_url_identity
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialResponseCapture,
    JRAOfficialResponseCaptureArchive,
)
from scripts.simulation.models import SimulationBet, SimulationRunContext, StrategyIdentity, build_strategy_identity
from scripts.simulation.nar_official_response_capture import (
    NAROfficialResponseCapture,
    NAROfficialResponseCaptureArchive,
)
from scripts.simulation.persisted_settlement import PersistedRaceSettlementData
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutRepository,
    PayoutStatus,
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultRepository,
    RaceResultStatus,
)
from scripts.simulation.stake_allocation import BetStakeBudget


NOW = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
JRA_URL = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC"
NAR_URL = "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceMarkTable?k_babaCode=31&k_raceDate=2026%2F05%2F03&k_raceNo=1"


class _Archive:
    def __init__(self, values: dict[str, object]) -> None:
        self.values = values
        self.calls: list[str] = []
        self.error: BaseException | None = None

    def load_capture(self, *, capture_id: str) -> object | None:
        self.calls.append(capture_id)
        if self.error is not None:
            raise self.error
        return self.values.get(capture_id)


class _PlanSource:
    def __init__(self, bets: tuple[SimulationBet, ...]) -> None:
        self.bets = bets
        self.calls: list[object] = []

    def load_snapshot(self, *, identity: object) -> SimulationBetPlanSnapshot:
        self.calls.append(identity)
        return SimulationBetPlanSnapshot(
            identity=identity,  # type: ignore[arg-type]
            policy_identity=build_allocation_policy_identity(
                AllocationPolicyConfig("fixed-stake", "1", {"stake": 100})
            ),
            budget=BetStakeBudget(10_000),
            bets=self.bets,
        )


class _RaceRepository:
    def __init__(self) -> None:
        self.saved: list[PersistedRaceResult] = []
        self.error: BaseException | None = None

    def save_race_result(self, result: PersistedRaceResult) -> None:
        self.saved.append(result)
        if self.error is not None:
            raise self.error


class _PayoutRepository:
    def __init__(self) -> None:
        self.saved: list[PayoutPublication] = []
        self.error: BaseException | None = None

    def save_payout_publication(self, publication: PayoutPublication) -> PayoutPublication:
        self.saved.append(publication)
        if self.error is not None:
            raise self.error
        return publication


def _evidence(role: str) -> HistoricalInputEvidenceReference:
    return HistoricalInputEvidenceReference(role, "https://evidence.example.test", "a" * 64, None, NOW - timedelta(days=2))


def _snapshot(
    provider: str = "NAR",
    *,
    dataset_id: str = "dataset",
    organization_override: str | None = None,
) -> HistoricalInputSnapshot:
    if provider == "JRA":
        identity = parse_jra_result_url_identity(JRA_URL)
        organization, system, external_race_id, source_url = "JRA", "jra_official", identity.external_race_id, JRA_URL
        race_date, place, track = date(2025, 9, 13), "中山", "芝"
        external_entries = tuple(
            build_jra_external_entry_id(race_identity=identity, horse_no=horse_no) for horse_no in (1, 2, 3)
        )
    else:
        organization, system, external_race_id, source_url = "NAR", "nar_official", "nar:20260503:31:1", NAR_URL
        race_date, place, track = date(2026, 5, 3), "高知", "ダート"
        external_entries = tuple(f"{external_race_id}:entry:{horse_no}" for horse_no in (1, 2, 3))
    if organization_override is not None:
        organization = organization_override
    source = HistoricalSourceIdentity(organization, system, external_race_id, source_url)
    race_identity = HistoricalExternalRaceIdentity(organization, system, external_race_id)
    entries = tuple(
        HistoricalRaceEntrySnapshot(
            race_entry_id=100 + horse_no,
            external_entry_identity=HistoricalExternalEntryIdentity(race_identity, external_entries[index], None),
            horse_no=horse_no,
            jockey=f"jockey-{horse_no}",
            win_odds=Decimal("2.0"),
            entry_order=index,
        )
        for index, horse_no in enumerate((1, 2, 3))
    )
    provenance = [HistoricalInputProvenance("track", "track", system, "track", None, (_evidence("track"),))]
    for entry in entries:
        for kind, evidence_role in (("entry", "entry"), ("odds", "odds_win"), ("jockey", "jockey")):
            provenance.append(
                HistoricalInputProvenance(
                    kind,
                    f"{kind}/{entry.race_entry_id}",
                    system,
                    f"{kind}-{entry.race_entry_id}",
                    entry.race_entry_id,
                    (_evidence(evidence_role),),
                )
            )
        provenance.append(HistoricalInputProvenance("past_race", f"past_race/{entry.race_entry_id}/none", system, f"past-{entry.race_entry_id}", entry.race_entry_id, (_evidence("past_race_absence_query"),)))
    return HistoricalInputSnapshot(
        identity=HistoricalInputSnapshotIdentity(dataset_id, source, NOW - timedelta(days=1)),
        internal_race_id=700 if provider == "JRA" else 800,
        information_cutoff=NOW - timedelta(hours=2),
        race=HistoricalRaceSnapshot(race_date, NOW - timedelta(hours=1), place, 1600, track, "良"),
        entries=entries,
        past_races=(),
        provenance=tuple(provenance),
    )


def _context(snapshot: HistoricalInputSnapshot) -> SimulationRunContext:
    return SimulationRunContext("run", snapshot.identity.dataset_id, NOW - timedelta(days=1), "commit")


def _strategy() -> StrategyIdentity:
    return build_strategy_identity("strategy", StrategyConfig())


def _bets(snapshot: HistoricalInputSnapshot, strategy: StrategyIdentity, types: tuple[str, ...]) -> tuple[SimulationBet, ...]:
    return tuple(
        SimulationBet(snapshot.internal_race_id, strategy.strategy_id, bet_type, (snapshot.entries[0].race_entry_id,) if bet_type == "単勝" else (snapshot.entries[0].race_entry_id, snapshot.entries[1].race_entry_id), 100, index, snapshot.information_cutoff)
        for index, bet_type in enumerate(types)
    )


def _capture(provider: str, *, body: bytes, offset: int) -> object:
    observed = NOW - timedelta(minutes=10 - offset)
    if provider == "JRA":
        return JRAOfficialResponseCapture(JRA_URL, body, "cp932", observed - timedelta(seconds=1), observed, observed + timedelta(seconds=1), 200, "text/html; charset=cp932")
    return NAROfficialResponseCapture(NAR_URL, body, "utf-8", observed - timedelta(seconds=1), observed, observed + timedelta(seconds=1), 200, "text/html; charset=UTF-8")


def _result(snapshot: HistoricalInputSnapshot, source: str) -> PersistedRaceResult:
    return PersistedRaceResult(snapshot.internal_race_id, RaceResultStatus.COMPLETE, NOW - timedelta(minutes=1), NOW - timedelta(minutes=1), source, tuple(PersistedRaceResultEntry(entry.horse_no, entry.race_entry_id, index + 1, RaceResultEntryStatus.CONFIRMED) for index, entry in enumerate(snapshot.entries)))


def _publication(snapshot: HistoricalInputSnapshot, bet_type: str, source: str) -> PayoutPublication:
    selection = (snapshot.entries[0].race_entry_id,) if bet_type == "単勝" else (snapshot.entries[0].race_entry_id, snapshot.entries[1].race_entry_id)
    return PayoutPublication(snapshot.internal_race_id, bet_type, NOW - timedelta(minutes=1), NOW - timedelta(minutes=1), True, source, (PayoutRecord(selection, 100, PayoutStatus.WINNING),), "https://source.example.test")


class OfficialSettlementAcquisitionTests(unittest.TestCase):
    def _run(self, provider: str = "NAR", types: tuple[str, ...] = ("単勝", "馬連"), **overrides: object):
        snapshot = _snapshot(provider)
        strategy = _strategy()
        captures = tuple(_capture(provider, body=f"<html>{index}</html>".encode("cp932" if provider == "JRA" else "utf-8"), offset=index) for index in range(1 + len(types)))
        archive = _Archive({capture.capture_id: capture for capture in captures})  # type: ignore[attr-defined]
        plan_source = _PlanSource(_bets(snapshot, strategy, types))
        result_repository, payout_repository = _RaceRepository(), _PayoutRepository()
        payouts = {bet_type: captures[index + 1].capture_id for index, bet_type in enumerate(types)}  # type: ignore[attr-defined]
        calls: list[tuple[str, str]] = []
        def result_normalizer(**kwargs: object) -> PersistedRaceResult:
            calls.append(("result", kwargs["capture_id"]))
            return _result(snapshot, kwargs["capture_id"])  # type: ignore[arg-type]
        def payout_normalizer(**kwargs: object) -> PayoutPublication:
            calls.append((kwargs["bet_type"], kwargs["capture_id"]))
            return _publication(snapshot, kwargs["bet_type"], kwargs["capture_id"])  # type: ignore[arg-type]
        patches = (
            patch.object(module, "normalize_and_persist_jra_target_race_result", result_normalizer),
            patch.object(module, "normalize_and_persist_jra_target_race_payout", payout_normalizer),
            patch.object(module, "normalize_and_persist_nar_target_race_result", result_normalizer),
            patch.object(module, "normalize_and_persist_nar_target_race_payout", payout_normalizer),
        )
        for item in patches: item.start()
        self.addCleanup(lambda: [item.stop() for item in reversed(patches)])
        values: dict[str, object] = dict(
            snapshot=snapshot, run_context=_context(snapshot), strategy_identity=strategy,
            settlement_information_cutoff=NOW, bet_plan_snapshot_source=plan_source,
            result_capture_id=captures[0].capture_id, payout_capture_ids_by_bet_type=payouts,
            capture_archive=archive, race_result_repository=result_repository, payout_repository=payout_repository,
        )
        values.update(overrides)
        return values, archive, plan_source, result_repository, payout_repository, calls

    def test_public_surface_signature_hints_and_error_hierarchy_are_exact(self) -> None:
        self.assertEqual(module.__all__, ("OfficialSettlementAcquisitionError", "OfficialSettlementAcquisitionValidationError", "OfficialSettlementAcquisitionUnavailableError", "OfficialSettlementAcquisitionUnsupportedError", "acquire_and_persist_official_settlement_facts"))
        self.assertFalse(hasattr(simulation_package, "acquire_and_persist_official_settlement_facts"))
        signature = inspect.signature(module.acquire_and_persist_official_settlement_facts)
        self.assertEqual(tuple(signature.parameters), ("snapshot", "run_context", "strategy_identity", "settlement_information_cutoff", "bet_plan_snapshot_source", "result_capture_id", "payout_capture_ids_by_bet_type", "capture_archive", "race_result_repository", "payout_repository"))
        self.assertTrue(all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values()))
        hints = get_type_hints(module.acquire_and_persist_official_settlement_facts)
        self.assertEqual(hints, {
            "snapshot": HistoricalInputSnapshot,
            "run_context": SimulationRunContext,
            "strategy_identity": StrategyIdentity,
            "settlement_information_cutoff": datetime,
            "bet_plan_snapshot_source": SimulationBetPlanSnapshotSource,
            "result_capture_id": str,
            "payout_capture_ids_by_bet_type": Mapping[str, str],
            "capture_archive": JRAOfficialResponseCaptureArchive | NAROfficialResponseCaptureArchive,
            "race_result_repository": RaceResultRepository,
            "payout_repository": PayoutRepository,
            "return": PersistedRaceSettlementData,
        })
        self.assertTrue(issubclass(module.OfficialSettlementAcquisitionValidationError, module.OfficialSettlementAcquisitionError))

    def test_jra_and_nar_success_use_plan_order_cached_exact_captures_and_exact_objects(self) -> None:
        for provider in ("JRA", "NAR"):
            values, archive, source, race_repo, payout_repo, calls = self._run(provider)
            data = module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
            self.assertEqual(len(source.calls), 1)
            self.assertEqual(archive.calls, [values["result_capture_id"], *values["payout_capture_ids_by_bet_type"].values()])
            self.assertEqual(calls, [("result", values["result_capture_id"]), ("単勝", values["payout_capture_ids_by_bet_type"]["単勝"]), ("馬連", values["payout_capture_ids_by_bet_type"]["馬連"])])
            self.assertEqual(race_repo.saved, [])
            self.assertEqual(payout_repo.saved, [])
            self.assertEqual(data.bets, source.bets)
            self.assertEqual(tuple(data.payout_publications_by_bet_type), ("単勝", "馬連"))

    def test_empty_plan_requires_empty_mapping_but_still_normalizes_result(self) -> None:
        values, archive, source, _, _, calls = self._run(types=())
        data = module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual(len(source.calls), 1)
        self.assertEqual(archive.calls, [values["result_capture_id"]])
        self.assertEqual(calls, [("result", values["result_capture_id"])])
        self.assertEqual(data.payout_publications_by_bet_type, {})

    def test_dataset_and_public_input_fail_before_plan_capture_or_writes(self) -> None:
        values, archive, source, race_repo, payout_repo, _ = self._run(run_context=SimulationRunContext("run", "other", NOW, "commit"))
        with self.assertRaises(module.OfficialSettlementAcquisitionValidationError):
            module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual((source.calls, archive.calls, race_repo.saved, payout_repo.saved), ([], [], [], []))
        values, archive, source, race_repo, payout_repo, _ = self._run(result_capture_id="")
        with self.assertRaises(module.OfficialSettlementAcquisitionValidationError):
            module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual((source.calls, archive.calls, race_repo.saved, payout_repo.saved), ([], [], [], []))

    def test_required_capture_mapping_mismatch_and_unsupported_provider_fail_before_capture(self) -> None:
        values, archive, source, _, _, _ = self._run(payout_capture_ids_by_bet_type={"単勝": "x"})
        with self.assertRaises(module.OfficialSettlementAcquisitionValidationError):
            module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual(len(source.calls), 1); self.assertEqual(archive.calls, [])
        values, archive, source, _, _, _ = self._run()
        bad_snapshot = _snapshot("NAR", organization_override="OTHER")
        values["snapshot"] = bad_snapshot
        with self.assertRaises(module.OfficialSettlementAcquisitionUnsupportedError):
            module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual(len(source.calls), 1); self.assertEqual(archive.calls, [])

    def test_distinct_capture_ids_are_loaded_once_in_first_use_order_and_cutoff_is_prewrite(self) -> None:
        values, archive, _, race_repo, payout_repo, calls = self._run(types=("単勝", "馬連"))
        payouts = values["payout_capture_ids_by_bet_type"]
        payouts["馬連"] = values["result_capture_id"]
        module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual(archive.calls, [values["result_capture_id"], payouts["単勝"]])
        self.assertEqual([item[0] for item in calls], ["result", "単勝", "馬連"])
        values, archive, _, race_repo, payout_repo, calls = self._run()
        values["settlement_information_cutoff"] = NOW - timedelta(hours=1)
        with self.assertRaises(module.OfficialSettlementAcquisitionValidationError):
            module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual(calls, []); self.assertEqual((race_repo.saved, payout_repo.saved), ([], []))

    def test_missing_or_incompatible_capture_is_prewrite_and_archive_exception_propagates(self) -> None:
        values, archive, _, race_repo, payout_repo, _ = self._run()
        archive.values[values["result_capture_id"]] = None
        with self.assertRaises(module.OfficialSettlementAcquisitionUnavailableError):
            module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual((race_repo.saved, payout_repo.saved), ([], []))
        values, archive, _, _, _, _ = self._run()
        archive.error = RuntimeError("archive")
        with self.assertRaisesRegex(RuntimeError, "archive"):
            module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]

    def test_capture_type_page_kind_and_cutoff_boundaries_fail_before_provider_writes(self) -> None:
        values, archive, _, race_repo, payout_repo, calls = self._run()
        wrong = _capture("JRA", body=b"<html>wrong</html>", offset=1)
        archive.values[values["result_capture_id"]] = wrong
        with self.assertRaises(module.OfficialSettlementAcquisitionValidationError):
            module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual((race_repo.saved, payout_repo.saved, calls), ([], [], []))
        values, archive, _, race_repo, payout_repo, calls = self._run()
        observed = max(capture.observed_at for capture in archive.values.values())
        values["settlement_information_cutoff"] = observed
        module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual(calls[0][0], "result")
        self.assertEqual((race_repo.saved, payout_repo.saved), ([], []))

    def test_provider_and_repository_exceptions_propagate_without_retry_or_later_payout(self) -> None:
        values, archive, _, _, _, calls = self._run(types=("単勝", "馬連"))
        def failing_result(**kwargs: object) -> PersistedRaceResult:
            calls.append(("result", kwargs["capture_id"]))
            raise RuntimeError("result conflict")
        with patch.object(module, "normalize_and_persist_nar_target_race_result", failing_result):
            with self.assertRaisesRegex(RuntimeError, "result conflict"):
                module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual([item[0] for item in calls], ["result"])
        self.assertEqual(len(archive.calls), 3)

    def test_cache_passed_to_normalizers_never_reloads_the_underlying_archive(self) -> None:
        values, archive, _, _, _, _ = self._run(types=("単勝",))
        def result_normalizer(**kwargs: object) -> PersistedRaceResult:
            cached = kwargs["capture_archive"].load_capture(capture_id=kwargs["capture_id"])
            self.assertIsNotNone(cached)
            self.assertIsNone(kwargs["capture_archive"].load_capture(capture_id="unknown"))
            return _result(values["snapshot"], kwargs["capture_id"])  # type: ignore[arg-type]
        def payout_normalizer(**kwargs: object) -> PayoutPublication:
            self.assertIsNotNone(kwargs["capture_archive"].load_capture(capture_id=kwargs["capture_id"]))
            return _publication(values["snapshot"], kwargs["bet_type"], kwargs["capture_id"])  # type: ignore[arg-type]
        with patch.object(module, "normalize_and_persist_nar_target_race_result", result_normalizer), patch.object(module, "normalize_and_persist_nar_target_race_payout", payout_normalizer):
            module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual(len(archive.calls), 2)

    def test_partial_failure_keeps_earlier_provider_writes_and_stops_later_types(self) -> None:
        values, _, _, _, _, calls = self._run(types=("単勝", "馬連"))
        def result_normalizer(**kwargs: object) -> PersistedRaceResult:
            calls.append(("result", kwargs["capture_id"]))
            return _result(values["snapshot"], kwargs["capture_id"])  # type: ignore[arg-type]
        def failing_payout(**kwargs: object) -> PayoutPublication:
            calls.append((kwargs["bet_type"], kwargs["capture_id"]))
            if kwargs["bet_type"] == "馬連": raise RuntimeError("second payout")
            return _publication(values["snapshot"], kwargs["bet_type"], kwargs["capture_id"])  # type: ignore[arg-type]
        with patch.object(module, "normalize_and_persist_nar_target_race_result", result_normalizer), patch.object(module, "normalize_and_persist_nar_target_race_payout", failing_payout):
            with self.assertRaisesRegex(RuntimeError, "second payout"):
                module.acquire_and_persist_official_settlement_facts(**values)  # type: ignore[arg-type]
        self.assertEqual([item[0] for item in calls], ["result", "単勝", "馬連"])

    def test_static_ownership_contract_has_no_http_database_clock_or_broad_catch(self) -> None:
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertNotIn("requests", source); self.assertNotIn("httpx", source); self.assertNotIn("sqlite", source.lower())
        self.assertNotIn("datetime.now", source); self.assertNotIn("get_latest", source)
        self.assertFalse(any(isinstance(node, ast.ExceptHandler) and (node.type is None or (isinstance(node.type, ast.Name) and node.type.id in {"Exception", "BaseException"})) for node in ast.walk(tree)))


if __name__ == "__main__":
    unittest.main()
