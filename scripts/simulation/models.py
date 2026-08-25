"""回収率シミュレーションの不変ドメインモデル。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from scripts.models import PastRace
from scripts.prediction.allocation_policy import (
    allocation_policy_config_payload,
    build_allocation_policy_identity,
)
from scripts.prediction.bet_strategy import StrategyConfig
from scripts.prediction.prediction_pipeline import RacePredictionInput
from scripts.prediction.track_engine import RaceTrackConditions
from scripts.simulation.repositories.interfaces import normalize_selection, validate_bet_type


WIN_BET_TYPE = "単勝"
STRATEGY_CONFIG_SCHEMA_VERSION = 1


def _aware(value: datetime, name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware datetime")


def _positive(value: int, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _non_negative_int(value: object, name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise TypeError(f"{name} must be a non-negative int")


def _selection(values: Sequence[int], name: str) -> tuple[int, ...]:
    normalized = tuple(sorted(values))
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{name} must not contain duplicate race_entry_id values")
    for value in normalized:
        _positive(value, f"{name} item")
    return normalized


def _freeze_mapping(mapping: Mapping[Any, Any]) -> Mapping[Any, Any]:
    return MappingProxyType(dict(mapping))


def _normalize_json(value: object) -> object:
    """Enum、集合および数値を設定ハッシュ向けの決定的な値へ正規化する。"""
    if isinstance(value, Enum):
        return _normalize_json(value.value)
    if isinstance(value, frozenset | set | tuple | list):
        normalized = [_normalize_json(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("strategy config contains a non-finite float")
        return value.hex()
    return value


def strategy_config_payload(
    config: StrategyConfig,
    *,
    schema_version: int = STRATEGY_CONFIG_SCHEMA_VERSION,
) -> dict[str, object]:
    """省略済みデフォルトを含む ``StrategyConfig`` の完全なハッシュ入力を返す。"""
    if not isinstance(config, StrategyConfig):
        raise TypeError("config must be a StrategyConfig")
    _positive(schema_version, "schema_version")
    payload: dict[str, object] = {
        "schema_version": schema_version,
        "allowed_bet_types": _normalize_json(config.allowed_bet_types),
        "max_bet_count": config.max_bet_count,
        "selection_style": _normalize_json(config.selection_style),
        "min_combination_score": _normalize_json(config.min_combination_score),
        "max_candidates": config.max_candidates,
        "sort_condition": _normalize_json(config.sort_condition),
    }
    if config.allocation_policy is not None:
        policy_payload = allocation_policy_config_payload(config.allocation_policy)
        policy_identity = build_allocation_policy_identity(config.allocation_policy)
        payload["allocation_policy"] = {
            "schema_version": policy_payload["schema_version"],
            "policy_name": policy_identity.policy_name,
            "policy_version": policy_identity.policy_version,
            "policy_config_hash": policy_identity.policy_config_hash,
            "parameters": policy_payload["parameters"],
        }
    return payload


def strategy_config_hash(config: StrategyConfig, *, schema_version: int = STRATEGY_CONFIG_SCHEMA_VERSION) -> str:
    """決定的 UTF-8 JSON の SHA-256 を返す。"""
    encoded = json.dumps(
        strategy_config_payload(config, schema_version=schema_version),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def generate_strategy_id(strategy_name: str, config_hash: str) -> str:
    """名前と設定ハッシュから再現可能な Strategy ID を生成する。"""
    if not strategy_name.strip():
        raise ValueError("strategy_name must not be empty")
    if len(config_hash) != 64 or any(char not in "0123456789abcdef" for char in config_hash):
        raise ValueError("config_hash must be a SHA-256 hexadecimal digest")
    return f"{strategy_name}:{config_hash[:16]}"


@dataclass(frozen=True)
class StrategyIdentity:
    """同じ Strategy クラスでも設定ごとに識別するための値オブジェクト。"""

    strategy_id: str
    strategy_name: str
    strategy_config: StrategyConfig
    strategy_config_hash: str

    def __post_init__(self) -> None:
        expected = strategy_config_hash(self.strategy_config)
        if self.strategy_config_hash != expected:
            raise ValueError("strategy_config_hash does not match strategy_config")
        if self.strategy_id != generate_strategy_id(self.strategy_name, expected):
            raise ValueError("strategy_id does not match strategy_name and strategy_config_hash")


def build_strategy_identity(strategy_name: str, config: StrategyConfig) -> StrategyIdentity:
    """既存の ``StrategyConfig`` から完全な StrategyIdentity を構築する。"""
    config_hash = strategy_config_hash(config)
    return StrategyIdentity(generate_strategy_id(strategy_name, config_hash), strategy_name, config, config_hash)


class SettlementStatus(str, Enum):
    """レース・Strategy 単位の精算状態。"""

    SETTLED = "settled"
    NO_BET = "no_bet"
    UNSETTLED = "unsettled"
    VOID = "void"
    ERROR = "error"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class PastRaceSnapshot:
    horse_id: int; race_date: str; place: str; race_name: str; race_class: str
    distance: int; track: str; weather: str; track_condition: str; finish: int
    time: str; weight: float; weight_diff: float; jockey: str
    popularity: int; odds: float; passing_order: str; fourth_corner_position: int

    @classmethod
    def from_past_race(cls, value: PastRace) -> "PastRaceSnapshot":
        return cls(**{name: getattr(value, name) for name in cls.__dataclass_fields__})


@dataclass(frozen=True)
class TrackConditionsSnapshot:
    place: str
    distance: int
    track: str
    track_condition: str

    @classmethod
    def from_track_conditions(cls, value: RaceTrackConditions) -> "TrackConditionsSnapshot":
        return cls(value.place, value.distance, value.track, value.track_condition)


@dataclass(frozen=True)
class ImmutableRacePredictionInput:
    """既存 ``RacePredictionInput`` を時点監査用に防御的コピーした不変スナップショット。"""

    horse_past_races: Mapping[int, tuple[PastRaceSnapshot, ...]]
    jockey_names_by_horse: Mapping[int, str]
    track_conditions: TrackConditionsSnapshot
    odds_by_horse: Mapping[int, object]
    race_horse_count: int
    race_id: int
    prediction_time: str

    @classmethod
    def from_race_prediction_input(
        cls,
        value: RacePredictionInput,
    ) -> "ImmutableRacePredictionInput":
        """可変 Mapping/Sequence をコピーし、以後の外部変更を遮断する。"""
        if not isinstance(value, RacePredictionInput):
            raise TypeError("value must be a RacePredictionInput")
        return cls(
            horse_past_races=_freeze_mapping(
                {horse_id: tuple(PastRaceSnapshot.from_past_race(item) for item in races) for horse_id, races in value.horse_past_races.items()}
            ),
            jockey_names_by_horse=_freeze_mapping(value.jockey_names_by_horse),
            track_conditions=TrackConditionsSnapshot.from_track_conditions(value.track_conditions),
            odds_by_horse=_freeze_mapping(value.odds_by_horse),
            race_horse_count=value.race_horse_count,
            race_id=value.race_id,
            prediction_time=value.prediction_time,
        )

    def __post_init__(self) -> None:
        entries = set(self.horse_past_races)
        if not entries:
            raise ValueError("horse_past_races must not be empty")
        if self.race_horse_count != len(entries):
            raise ValueError("race_horse_count must equal horse_past_races entry count")
        if set(self.jockey_names_by_horse) != entries:
            raise ValueError("jockey_names_by_horse keys must match horse_past_races keys")
        if set(self.odds_by_horse) != entries:
            raise ValueError("odds_by_horse keys must match horse_past_races keys")
        for race_entry_id in self.horse_past_races:
            _positive(race_entry_id, "race_entry_id")
        if not isinstance(self.track_conditions, TrackConditionsSnapshot):
            raise TypeError("track_conditions must be TrackConditionsSnapshot")
        object.__setattr__(self, "horse_past_races", _freeze_mapping(
            {key: tuple(value) for key, value in self.horse_past_races.items()}
        ))
        object.__setattr__(self, "jockey_names_by_horse", _freeze_mapping(self.jockey_names_by_horse))
        object.__setattr__(self, "odds_by_horse", _freeze_mapping(self.odds_by_horse))


@dataclass(frozen=True)
class InputAuditEntry:
    """時点監査対象となる一つの入力の来歴。"""

    input_type: str
    audit_key: str
    source: str
    source_id: str
    race_entry_id: int | None
    available_at: datetime | None = None
    observed_at: datetime | None = None
    past_race_index: int | None = None

    def __post_init__(self) -> None:
        if not self.input_type or not self.audit_key or not self.source or not self.source_id:
            raise ValueError("input_type, audit_key, source, and source_id must not be empty")
        if self.available_at is None and self.observed_at is None:
            raise ValueError("InputAuditEntry requires available_at or observed_at")
        for name, value in (("available_at", self.available_at), ("observed_at", self.observed_at)):
            if value is not None:
                _aware(value, name)
        if self.input_type == "track":
            if self.race_entry_id is not None:
                raise ValueError("track audit entry must not have race_entry_id")
        elif self.race_entry_id is None:
            raise ValueError("race_entry_id is required for non-track audit entries")
        else:
            _positive(self.race_entry_id, "race_entry_id")
        if self.past_race_index is not None and (isinstance(self.past_race_index, bool) or self.past_race_index < 0):
            raise ValueError("past_race_index must be non-negative")


@dataclass(frozen=True)
class InputSnapshotAudit:
    """一レースの予想入力スナップショットに対する時点監査。"""

    dataset_id: str
    source: str
    captured_at: datetime
    entries: Sequence[InputAuditEntry]
    is_complete: bool

    def __post_init__(self) -> None:
        if not self.dataset_id or not self.source:
            raise ValueError("dataset_id and source must not be empty")
        _aware(self.captured_at, "captured_at")
        if not isinstance(self.is_complete, bool):
            raise TypeError("is_complete must be bool")
        entries = tuple(self.entries)
        if not entries:
            raise ValueError("InputSnapshotAudit entries must not be empty")
        if not all(isinstance(item, InputAuditEntry) for item in entries):
            raise TypeError("entries must contain InputAuditEntry values")
        if len({item.audit_key for item in entries}) != len(entries):
            raise ValueError("InputSnapshotAudit audit_key values must be unique")
        object.__setattr__(self, "entries", entries)


@dataclass(frozen=True)
class SimulationRaceInput:
    """予想済み一レースを再現するための入力と監査情報。"""

    race_id: int
    target_race_date: date
    scheduled_start_at: datetime
    information_cutoff: datetime
    pipeline_input: RacePredictionInput | ImmutableRacePredictionInput
    input_snapshot_audit: InputSnapshotAudit

    def __post_init__(self) -> None:
        _positive(self.race_id, "race_id")
        if not isinstance(self.target_race_date, date) or isinstance(self.target_race_date, datetime):
            raise TypeError("target_race_date must be a date")
        _aware(self.scheduled_start_at, "scheduled_start_at")
        _aware(self.information_cutoff, "information_cutoff")
        if self.information_cutoff > self.scheduled_start_at:
            raise ValueError("information_cutoff must be earlier than or equal to scheduled_start_at")
        if isinstance(self.pipeline_input, RacePredictionInput):
            object.__setattr__(
                self,
                "pipeline_input",
                ImmutableRacePredictionInput.from_race_prediction_input(self.pipeline_input),
            )
        elif not isinstance(self.pipeline_input, ImmutableRacePredictionInput):
            raise TypeError("pipeline_input must be a RacePredictionInput or ImmutableRacePredictionInput")
        if not isinstance(self.input_snapshot_audit, InputSnapshotAudit):
            raise TypeError("input_snapshot_audit must be an InputSnapshotAudit")
        from .validation import validate_simulation_race_input

        validate_simulation_race_input(self)


@dataclass(frozen=True)
class SimulationBet:
    """一つの購入候補を 100 円単位で記録する監査用モデル。"""

    race_id: int
    strategy_id: str
    bet_type: str
    race_entry_ids: Sequence[int]
    stake: int
    recommendation_rank: int
    placed_at_cutoff: datetime

    def __post_init__(self) -> None:
        _positive(self.race_id, "race_id")
        if not self.strategy_id:
            raise ValueError("strategy_id must not be empty")
        kind = validate_bet_type(self.bet_type)
        selected = normalize_selection(self.race_entry_ids, kind)
        if not isinstance(self.stake, int) or isinstance(self.stake, bool) or self.stake <= 0 or self.stake % 100:
            raise ValueError("stake must be a positive multiple of 100")
        if not isinstance(self.recommendation_rank, int) or isinstance(self.recommendation_rank, bool) or self.recommendation_rank < 0:
            raise ValueError("recommendation_rank must be non-negative")
        _aware(self.placed_at_cutoff, "placed_at_cutoff")
        object.__setattr__(self, "bet_type", kind)
        object.__setattr__(self, "race_entry_ids", selected)


@dataclass(frozen=True)
class SimulationResult:
    """一つの Strategy と一つのレースの精算前後の結果。"""

    race_id: int
    strategy_id: str
    bets: Sequence[SimulationBet]
    settlement_status: SettlementStatus
    exclusion_reason: str | None
    planned_investment: int
    settled_investment: int | None = None
    payout: int | None = None
    profit: int | None = None
    hit_bet_count: int = 0
    settled_at: datetime | None = None
    by_bet_type: Mapping[str, BetTypeSummary] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _positive(self.race_id, "race_id")
        if not self.strategy_id:
            raise ValueError("strategy_id must not be empty")
        bets = tuple(self.bets)
        if not all(isinstance(bet, SimulationBet) for bet in bets):
            raise TypeError("bets must contain SimulationBet values")
        if any(bet.race_id != self.race_id or bet.strategy_id != self.strategy_id for bet in bets):
            raise ValueError("bets must belong to this race_id and strategy_id")
        if not isinstance(self.settlement_status, SettlementStatus):
            raise TypeError("settlement_status must be SettlementStatus")
        _non_negative_int(self.planned_investment, "planned_investment")
        _non_negative_int(self.hit_bet_count, "hit_bet_count")
        if self.planned_investment != sum(bet.stake for bet in bets):
            raise ValueError("planned_investment must equal the sum of bet stakes")
        if self.planned_investment < 0:
            raise ValueError("planned_investment must not be negative")
        if not 0 <= self.hit_bet_count <= len(bets):
            raise ValueError("hit_bet_count must be between zero and the bet count")
        if self.settlement_status is SettlementStatus.NO_BET and (bets or self.planned_investment != 0):
            raise ValueError("NO_BET requires no bets and planned_investment=0")
        if self.settlement_status is SettlementStatus.NO_BET and self.hit_bet_count != 0:
            raise ValueError("NO_BET requires hit_bet_count=0")
        needs_reason = {SettlementStatus.UNSETTLED, SettlementStatus.ERROR, SettlementStatus.VOID, SettlementStatus.UNSUPPORTED}
        if self.settlement_status in needs_reason and not self.exclusion_reason:
            raise ValueError(f"{self.settlement_status.value} requires exclusion_reason")
        if self.settlement_status not in needs_reason and self.exclusion_reason is not None:
            raise ValueError("only UNSETTLED, ERROR, VOID, and UNSUPPORTED may have exclusion_reason")
        if self.settlement_status is SettlementStatus.SETTLED:
            if not bets or self.planned_investment <= 0:
                raise ValueError("SETTLED requires at least one bet and positive planned_investment")
            if None in (self.settled_investment, self.payout, self.profit, self.settled_at):
                raise ValueError("SETTLED requires settled_investment, payout, profit, and settled_at")
            _aware(self.settled_at, "settled_at")
            if not isinstance(self.settled_investment, int) or isinstance(self.settled_investment, bool) or self.settled_investment <= 0:
                raise TypeError("settled_investment must be a positive int")
            _non_negative_int(self.payout, "payout")
            if not isinstance(self.profit, int) or isinstance(self.profit, bool):
                raise TypeError("profit must be an int")
            if self.profit != self.payout - self.settled_investment:
                raise ValueError("profit must equal payout minus settled_investment")
            if self.settled_investment != self.planned_investment:
                raise ValueError("SETTLED settled_investment must equal planned_investment")
            if any(self.settled_at < bet.placed_at_cutoff for bet in bets):
                raise ValueError("settled_at must not precede placed_at_cutoff")
        elif any(value is not None for value in (self.settled_investment, self.payout, self.profit, self.settled_at)):
            raise ValueError("non-SETTLED results must have no settlement amounts or settled_at")
        if self.settlement_status is not SettlementStatus.SETTLED and self.hit_bet_count != 0:
            raise ValueError("non-SETTLED results require hit_bet_count=0")
        if len({(bet.bet_type, bet.race_entry_ids) for bet in bets}) != len(bets):
            raise ValueError("bets must not contain duplicate selections")
        summaries = _normalize_result_bet_type_summaries(self.by_bet_type)
        bet_types = {bet.bet_type for bet in bets}
        if self.settlement_status is SettlementStatus.SETTLED:
            if not summaries or set(summaries) != bet_types:
                raise ValueError("SETTLED by_bet_type keys must exactly match bet types")
            if (sum(item.bet_count for item in summaries.values()) != len(bets)
                    or sum(item.settled_bet_count for item in summaries.values()) != len(bets)
                    or sum(item.hit_bet_count for item in summaries.values()) != self.hit_bet_count
                    or sum(item.investment for item in summaries.values()) != self.settled_investment
                    or sum(item.payout for item in summaries.values()) != self.payout
                    or sum(item.profit for item in summaries.values()) != self.profit):
                raise ValueError("SETTLED by_bet_type totals must match SimulationResult")
            for bet_type, item in summaries.items():
                matching_bets = tuple(bet for bet in bets if bet.bet_type == bet_type)
                if (item.bet_count != len(matching_bets)
                        or item.settled_bet_count != item.bet_count
                        or item.investment != sum(bet.stake for bet in matching_bets)):
                    raise ValueError("SETTLED by_bet_type entries must match bets and stakes")
        elif self.settlement_status is SettlementStatus.NO_BET:
            if summaries:
                raise ValueError("NO_BET requires an empty by_bet_type mapping")
        elif not bets and self.settlement_status is not SettlementStatus.ERROR:
            raise ValueError("non-ERROR non-SETTLED results require at least one bet")
        elif bets:
            if not summaries or set(summaries) != bet_types:
                raise ValueError("non-SETTLED by_bet_type keys must exactly match bet types")
            for bet_type, item in summaries.items():
                matching_bets = tuple(bet for bet in bets if bet.bet_type == bet_type)
                if (item.bet_count != len(matching_bets)
                        or item.settled_bet_count != 0
                        or item.hit_bet_count != 0
                        or any(value != 0 for value in (item.investment, item.payout, item.profit))
                        or item.roi is not None
                        or item.bet_hit_rate is not None):
                    raise ValueError("non-SETTLED by_bet_type entries must be zero-money un-settled summaries")
        elif summaries:
            raise ValueError("empty non-SETTLED results require an empty by_bet_type mapping")
        object.__setattr__(self, "bets", bets)
        object.__setattr__(self, "by_bet_type", summaries)


@dataclass(frozen=True)
class BetTypeSummary:
    """券種別の確定済み集計値。"""

    bet_type: str
    bet_count: int
    settled_bet_count: int
    hit_bet_count: int
    investment: int
    payout: int
    profit: int
    roi: Decimal | None
    bet_hit_rate: Decimal | None

    def __post_init__(self) -> None:
        if not self.bet_type:
            raise ValueError("bet_type must not be empty")
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in (self.bet_count, self.settled_bet_count, self.hit_bet_count, self.investment, self.payout)):
            raise ValueError("counts and money must be non-negative integers")
        if not isinstance(self.profit, int) or isinstance(self.profit, bool):
            raise TypeError("profit must be an int")
        if any(value is not None and not isinstance(value, Decimal) for value in (self.roi, self.bet_hit_rate)):
            raise TypeError("rates must be Decimal or None")
        if not (0 <= self.hit_bet_count <= self.settled_bet_count <= self.bet_count) or self.profit != self.payout - self.investment:
            raise ValueError("BetTypeSummary values are inconsistent")
        if self.settled_bet_count == 0 and any(value != 0 for value in (self.investment, self.payout, self.profit)):
            raise ValueError("unsettled BetTypeSummary must have zero money amounts")
        if self.settled_bet_count > 0 and (self.investment <= 0 or self.investment % 100 != 0):
            raise ValueError("settled BetTypeSummary investment must be a positive multiple of 100")
        expected_roi = None if self.investment == 0 else Decimal(self.payout) * Decimal("100") / Decimal(self.investment)
        expected_hit_rate = None if self.settled_bet_count == 0 else Decimal(self.hit_bet_count) * Decimal("100") / Decimal(self.settled_bet_count)
        if self.roi != expected_roi or self.bet_hit_rate != expected_hit_rate:
            raise ValueError("BetTypeSummary rates must match their denominators")


def _normalize_result_bet_type_summaries(value: object) -> Mapping[str, BetTypeSummary]:
    """Copy, validate, and canonically order a result-level bet-type mapping."""
    if not isinstance(value, Mapping):
        raise TypeError("by_bet_type must be a Mapping")
    normalized: dict[str, BetTypeSummary] = {}
    for key, summary in value.items():
        if not isinstance(key, str) or not key:
            raise TypeError("by_bet_type keys must be non-empty bet_type strings")
        try:
            bet_type = validate_bet_type(key)
        except (TypeError, ValueError) as exc:
            raise ValueError("by_bet_type keys must be supported bet types") from exc
        if not isinstance(summary, BetTypeSummary):
            raise TypeError("by_bet_type values must be BetTypeSummary")
        if summary.bet_type != bet_type:
            raise ValueError("by_bet_type keys must match BetTypeSummary.bet_type")
        normalized[bet_type] = summary
    return _freeze_mapping({key: normalized[key] for key in sorted(normalized)})


@dataclass(frozen=True)
class SimulationSummary:
    """一 Strategy の集計結果。未精算分は ROI へ含めない。"""

    strategy_id: str
    strategy_name: str
    strategy_config_hash: str
    race_count: int
    settled_race_count: int
    unsettled_race_count: int
    no_bet_race_count: int
    void_race_count: int
    error_race_count: int
    unsupported_race_count: int
    bet_count: int
    settled_bet_count: int
    settled_purchase_race_count: int
    hit_bet_count: int
    hit_race_count: int
    investment: int
    payout: int
    profit: int
    roi: Decimal | None
    bet_hit_rate: Decimal | None
    race_hit_rate: Decimal | None
    maximum_drawdown: int
    by_bet_type: Mapping[str, BetTypeSummary] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.strategy_id or not self.strategy_name:
            raise ValueError("strategy_id and strategy_name must not be empty")
        counts = (self.settled_race_count, self.unsettled_race_count, self.no_bet_race_count, self.void_race_count, self.error_race_count, self.unsupported_race_count)
        if not self.strategy_config_hash or len(self.strategy_config_hash) != 64 or any(char not in "0123456789abcdef" for char in self.strategy_config_hash):
            raise ValueError("strategy_config_hash must be a SHA-256 digest")
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in (self.race_count, *counts, self.bet_count, self.settled_bet_count, self.settled_purchase_race_count, self.hit_bet_count, self.hit_race_count, self.investment, self.payout, self.maximum_drawdown)):
            raise ValueError("summary counts and money must be non-negative integers")
        if not isinstance(self.profit, int) or isinstance(self.profit, bool):
            raise TypeError("profit must be an int")
        if (sum(counts) != self.race_count or self.settled_bet_count > self.bet_count
                or self.hit_bet_count > self.settled_bet_count
                or self.hit_race_count > self.settled_purchase_race_count
                or self.settled_purchase_race_count > self.settled_race_count
                or self.profit != self.payout - self.investment):
            raise ValueError("SimulationSummary values are inconsistent")
        if self.settled_bet_count == 0 and any(value != 0 for value in (self.investment, self.payout, self.profit)):
            raise ValueError("unsettled SimulationSummary must have zero money amounts")
        if self.settled_bet_count > 0 and (self.investment <= 0 or self.investment % 100 != 0):
            raise ValueError("settled SimulationSummary investment must be a positive multiple of 100")
        if any(value is not None and not isinstance(value, Decimal) for value in (self.roi, self.bet_hit_rate, self.race_hit_rate)):
            raise TypeError("rates must be Decimal or None")
        if (self.bet_count > 0 and not self.by_bet_type) or (self.bet_count == 0 and self.by_bet_type):
            raise ValueError("by_bet_type emptiness must match bet_count")
        expected_roi = None if self.investment == 0 else Decimal(self.payout) * Decimal("100") / Decimal(self.investment)
        expected_bet_rate = None if self.settled_bet_count == 0 else Decimal(self.hit_bet_count) * Decimal("100") / Decimal(self.settled_bet_count)
        expected_race_rate = None if self.settled_purchase_race_count == 0 else Decimal(self.hit_race_count) * Decimal("100") / Decimal(self.settled_purchase_race_count)
        if self.roi != expected_roi or self.bet_hit_rate != expected_bet_rate or self.race_hit_rate != expected_race_rate:
            raise ValueError("SimulationSummary rates must match their denominators")
        copied = dict(self.by_bet_type)
        if any(key != value.bet_type for key, value in copied.items()):
            raise ValueError("by_bet_type keys must match BetTypeSummary.bet_type")
        if copied and (sum(item.bet_count for item in copied.values()) != self.bet_count
                       or sum(item.settled_bet_count for item in copied.values()) != self.settled_bet_count
                       or sum(item.hit_bet_count for item in copied.values()) != self.hit_bet_count
                       or sum(item.investment for item in copied.values()) != self.investment
                       or sum(item.payout for item in copied.values()) != self.payout
                       or sum(item.profit for item in copied.values()) != self.profit):
            raise ValueError("by_bet_type totals must match SimulationSummary")
        object.__setattr__(self, "by_bet_type", _freeze_mapping(copied))


@dataclass(frozen=True)
class SimulationRunContext:
    """Simulator 入力用の実行文脈。completed_at は含めない。"""

    run_id: str
    dataset_id: str
    started_at: datetime
    target_commit_id: str

    def __post_init__(self) -> None:
        if not self.run_id or not self.dataset_id or not self.target_commit_id:
            raise ValueError("run_id, dataset_id, and target_commit_id must not be empty")
        _aware(self.started_at, "started_at")


@dataclass(frozen=True)
class SimulationRunMetadata:
    """Simulator 出力用の実行来歴。完了時刻は実行側が生成する。"""

    run_id: str
    dataset_id: str
    started_at: datetime
    completed_at: datetime
    target_commit_id: str

    def __post_init__(self) -> None:
        if not self.run_id or not self.dataset_id or not self.target_commit_id:
            raise ValueError("run_id, dataset_id, and target_commit_id must not be empty")
        _aware(self.started_at, "started_at")
        _aware(self.completed_at, "completed_at")
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")


@dataclass(frozen=True)
class RaceResultEntry:
    """確定着順表の一行。race_entry_id は Provider が horse_no から変換する。"""

    horse_no: int
    race_entry_id: int
    finish_position: int | None
    result_status: str

    def __post_init__(self) -> None:
        _positive(self.horse_no, "horse_no")
        _positive(self.race_entry_id, "race_entry_id")
        if self.finish_position is not None:
            _positive(self.finish_position, "finish_position")
        if not self.result_status:
            raise ValueError("result_status must not be empty")


@dataclass(frozen=True)
class RaceResultTable:
    """race_id 単位の確定着順表。完全表は finalized_at を必須とする。"""

    race_id: int
    is_complete: bool
    finalized_at: datetime | None
    observed_at: datetime
    source: str
    entries: Sequence[RaceResultEntry]

    def __post_init__(self) -> None:
        _positive(self.race_id, "race_id")
        _aware(self.observed_at, "observed_at")
        if not self.source:
            raise ValueError("source must not be empty")
        if self.finalized_at is not None:
            _aware(self.finalized_at, "finalized_at")
        if self.is_complete and self.finalized_at is None:
            raise ValueError("complete RaceResultTable requires finalized_at")
        entries = tuple(self.entries)
        if not all(isinstance(entry, RaceResultEntry) for entry in entries):
            raise TypeError("entries must contain RaceResultEntry values")
        if len({item.horse_no for item in entries}) != len(entries) or len({item.race_entry_id for item in entries}) != len(entries):
            raise ValueError("RaceResultTable entries must have unique horse_no and race_entry_id")
        object.__setattr__(self, "entries", entries)


@dataclass(frozen=True)
class PayoutEntry:
    """的中組み合わせと 100 円当たりの払戻額。返還とは別型にする。"""

    race_entry_ids: Sequence[int]
    payout_per_100: int
    payout_status: str = "winning"

    def __post_init__(self) -> None:
        if not isinstance(self.payout_per_100, int) or self.payout_per_100 < 0:
            raise ValueError("payout_per_100 must be a non-negative integer")
        if self.payout_status != "winning":
            raise ValueError("PayoutEntry payout_status must be 'winning'")
        object.__setattr__(self, "race_entry_ids", _selection(self.race_entry_ids, "race_entry_ids"))


@dataclass(frozen=True)
class RefundEntry:
    """返還組み合わせ。的中には数えない。"""

    race_entry_ids: Sequence[int]
    refund_per_100: int
    reason: str
    payout_status: str = "refund"

    def __post_init__(self) -> None:
        if not isinstance(self.refund_per_100, int) or self.refund_per_100 < 0:
            raise ValueError("refund_per_100 must be a non-negative integer")
        if not self.reason:
            raise ValueError("reason must not be empty")
        if self.payout_status != "refund":
            raise ValueError("RefundEntry payout_status must be 'refund'")
        object.__setattr__(self, "race_entry_ids", _selection(self.race_entry_ids, "race_entry_ids"))


@dataclass(frozen=True)
class PayoutTable:
    """race_id・券種単位の完全性を表す払戻表。"""

    race_id: int
    bet_type: str
    is_complete: bool
    finalized_at: datetime | None
    observed_at: datetime
    source: str
    payouts: Sequence[PayoutEntry] = ()
    refunds: Sequence[RefundEntry] = ()

    def __post_init__(self) -> None:
        _positive(self.race_id, "race_id")
        if not self.bet_type or not self.source:
            raise ValueError("bet_type and source must not be empty")
        _aware(self.observed_at, "observed_at")
        if self.finalized_at is not None:
            _aware(self.finalized_at, "finalized_at")
        if self.is_complete and self.finalized_at is None:
            raise ValueError("complete PayoutTable requires finalized_at")
        payouts, refunds = tuple(self.payouts), tuple(self.refunds)
        if not all(isinstance(entry, PayoutEntry) for entry in payouts):
            raise TypeError("payouts must contain PayoutEntry values")
        if not all(isinstance(entry, RefundEntry) for entry in refunds):
            raise TypeError("refunds must contain RefundEntry values")
        keys = [entry.race_entry_ids for entry in payouts] + [entry.race_entry_ids for entry in refunds]
        if len(keys) != len(set(keys)):
            raise ValueError("PayoutTable selections must not overlap or duplicate")
        object.__setattr__(self, "payouts", payouts)
        object.__setattr__(self, "refunds", refunds)


@dataclass(frozen=True)
class SimulationReport:
    """複数 Strategy のレース別明細と集計を保持する出力コンテナ。"""

    metadata: SimulationRunMetadata
    strategy_identities: Sequence[StrategyIdentity]
    race_results: Sequence[SimulationResult]
    strategy_summaries: Mapping[str, SimulationSummary]
    official_roi_valid: bool
    validation_errors: Sequence[str] = ()

    def __post_init__(self) -> None:
        identities, results, errors = tuple(self.strategy_identities), tuple(self.race_results), tuple(self.validation_errors)
        if not isinstance(self.metadata, SimulationRunMetadata):
            raise TypeError("metadata must be SimulationRunMetadata")
        if not isinstance(self.official_roi_valid, bool):
            raise TypeError("official_roi_valid must be bool")
        if not all(isinstance(identity, StrategyIdentity) for identity in identities):
            raise TypeError("strategy_identities must contain StrategyIdentity values")
        if not all(isinstance(result, SimulationResult) for result in results):
            raise TypeError("race_results must contain SimulationResult values")
        if not all(isinstance(error, str) and error.strip() for error in errors):
            raise ValueError("validation_errors must contain non-empty strings")
        ids = {item.strategy_id for item in identities}
        if not identities:
            raise ValueError("strategy_identities must not be empty")
        if len(ids) != len(identities):
            raise ValueError("strategy_identities must have unique strategy_id values")
        if any(result.strategy_id not in ids for result in results):
            raise ValueError("race_results contain an unknown strategy_id")
        summaries = dict(self.strategy_summaries)
        if (set(summaries) != ids
                or any(not isinstance(summary, SimulationSummary) for summary in summaries.values())
                or any(key != summary.strategy_id for key, summary in summaries.items())):
            raise ValueError("strategy_summaries must exactly match strategy identities")
        identity_names = {identity.strategy_id: identity.strategy_name for identity in identities}
        identity_hashes = {identity.strategy_id: identity.strategy_config_hash for identity in identities}
        if any(summary.strategy_name != identity_names[strategy_id] for strategy_id, summary in summaries.items()):
            raise ValueError("strategy summary name must match StrategyIdentity")
        if any(summary.strategy_config_hash != identity_hashes[strategy_id] for strategy_id, summary in summaries.items()):
            raise ValueError("strategy summary hash must match StrategyIdentity")
        if len({(result.strategy_id, result.race_id) for result in results}) != len(results):
            raise ValueError("race_results must be unique per strategy_id and race_id")
        for strategy_id, summary in summaries.items():
            scoped = [result for result in results if result.strategy_id == strategy_id]
            counts = {status: sum(result.settlement_status is status for result in scoped) for status in SettlementStatus}
            if (summary.race_count != len(scoped)
                    or summary.settled_race_count != counts[SettlementStatus.SETTLED]
                    or summary.unsettled_race_count != counts[SettlementStatus.UNSETTLED]
                    or summary.no_bet_race_count != counts[SettlementStatus.NO_BET]
                    or summary.void_race_count != counts[SettlementStatus.VOID]
                    or summary.error_race_count != counts[SettlementStatus.ERROR]
                    or summary.unsupported_race_count != counts[SettlementStatus.UNSUPPORTED]):
                raise ValueError("SimulationSummary status counts must match race_results")
            settled = [result for result in scoped if result.settlement_status is SettlementStatus.SETTLED]
            if (summary.bet_count != sum(len(result.bets) for result in scoped)
                    or summary.settled_bet_count != sum(len(result.bets) for result in settled)
                    or summary.settled_purchase_race_count != sum(bool(result.bets) for result in settled)
                    or summary.hit_bet_count != sum(result.hit_bet_count for result in settled)
                    or summary.hit_race_count != sum(result.hit_bet_count > 0 for result in settled)
                    or summary.investment != sum(result.settled_investment or 0 for result in settled)
                    or summary.payout != sum(result.payout or 0 for result in settled)
                    or summary.profit != sum(result.profit or 0 for result in settled)):
                raise ValueError("SimulationSummary totals must match settled race_results")
        if self.official_roi_valid and (errors or any(result.settlement_status is SettlementStatus.ERROR for result in results)):
            raise ValueError("official_roi_valid cannot be true when validation errors or ERROR results exist")
        object.__setattr__(self, "strategy_identities", identities)
        object.__setattr__(self, "race_results", results)
        object.__setattr__(self, "strategy_summaries", _freeze_mapping(summaries))
        object.__setattr__(self, "validation_errors", errors)
