"""Explicit, read-only aggregation of immutable NAR daily replay results."""

from __future__ import annotations

from collections.abc import Mapping as _Mapping
from dataclasses import dataclass as _dataclass, field as _field
from datetime import date as _date, datetime as _datetime, timezone as _timezone
from decimal import Decimal as _Decimal
from hashlib import sha256 as _sha256
import json as _json
import re as _re
from types import MappingProxyType as _MappingProxyType
from unicodedata import normalize as _normalize

from scripts.simulation.models import BetTypeSummary as _BetTypeSummary
from scripts.simulation.nar_daily_replay_orchestrator import (
    NARDailyReplayExecutionState as _ExecutionState,
)
from scripts.simulation.nar_daily_replay_result_persistence import (
    PersistedNARDailyReplayResult as _PersistedResult,
)
from scripts.simulation.repositories.errors import (
    RepositoryDataIntegrityError as _RepositoryDataIntegrityError,
    RepositoryValidationError as _RepositoryValidationError,
)
from scripts.simulation.repositories.interfaces import validate_bet_type as _validate_bet_type
from scripts.simulation.repositories.sqlite_nar_daily_replay_result_repository import (
    SQLiteNARDailyReplayResultRepository as _SQLiteNARDailyReplayResultRepository,
)


__all__ = (
    "NARDailyReplayAggregationSelection",
    "NARDailyReplayAggregationResult",
    "aggregate_nar_daily_replay_selection",
)


_SELECTION_VERSION = "nar-daily-replay-aggregation-selection-v1"
_RESULT_VERSION = "nar-daily-replay-aggregation-result-v1"
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_PROVIDER = ("NAR", "nar_official")


def _text(value: object, name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or value != _normalize("NFC", value)
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise _RepositoryValidationError(f"{name} must be nonempty exact NFC text")
    return value


def _digest(value: object, name: str) -> str:
    value = _text(value, name)
    if _SHA256.fullmatch(value) is None:
        raise _RepositoryValidationError(f"{name} must be lowercase SHA-256")
    return value


def _utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime or value.tzinfo is None or value.utcoffset() is None:
        raise _RepositoryValidationError(f"{name} must be an exact aware datetime")
    return value.astimezone(_timezone.utc)


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _decimal_text(value: _Decimal | None) -> str | None:
    if value is None:
        return None
    if type(value) is not _Decimal or not value.is_finite():
        raise _RepositoryValidationError("aggregate rate must be finite Decimal or None")
    return "0" if value == 0 else format(value.normalize(), "f")


def _canonical_json(value: object) -> str:
    try:
        return _json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, UnicodeError) as error:
        raise _RepositoryValidationError("aggregate identity payload is not canonical JSON") from error


def _rate(numerator: int, denominator: int) -> _Decimal | None:
    if denominator == 0:
        return None
    return _Decimal(numerator) * _Decimal("100") / _Decimal(denominator)


def _selection_payload(value: NARDailyReplayAggregationSelection) -> dict[str, object]:
    return {
        "persisted_content_sha256s": list(value.persisted_content_sha256s),
        "schema_version": value.schema_version,
        "version": _SELECTION_VERSION,
    }


def _selection_digest(value: NARDailyReplayAggregationSelection) -> str:
    return _sha256(_canonical_json(_selection_payload(value)).encode("utf-8")).hexdigest()


@_dataclass(frozen=True, slots=True)
class NARDailyReplayAggregationSelection:
    schema_version: int
    persisted_content_sha256s: tuple[str, ...]
    selection_sha256: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise _RepositoryValidationError("selection schema_version must be exact version 1")
        if (
            type(self.persisted_content_sha256s) is not tuple
            or not self.persisted_content_sha256s
        ):
            raise _RepositoryValidationError("selection identities must be a nonempty tuple")
        for value in self.persisted_content_sha256s:
            _digest(value, "selected persisted_content_sha256")
        if len(set(self.persisted_content_sha256s)) != len(
            self.persisted_content_sha256s
        ):
            raise _RepositoryValidationError("selection identities must be unique")
        object.__setattr__(self, "selection_sha256", _selection_digest(self))


def _bet_type_payload(value: _BetTypeSummary) -> dict[str, object]:
    return {
        "bet_count": value.bet_count,
        "bet_hit_rate": _decimal_text(value.bet_hit_rate),
        "bet_type": value.bet_type,
        "hit_bet_count": value.hit_bet_count,
        "investment": value.investment,
        "payout": value.payout,
        "profit": value.profit,
        "roi": _decimal_text(value.roi),
        "settled_bet_count": value.settled_bet_count,
    }


def _result_payload(value: NARDailyReplayAggregationResult) -> dict[str, object]:
    return {
        "aggregate": {
            "bet_count": value.bet_count,
            "bet_hit_rate": _decimal_text(value.bet_hit_rate),
            "by_bet_type": [
                _bet_type_payload(value.by_bet_type[key])
                for key in sorted(value.by_bet_type)
            ],
            "error_race_count": value.error_race_count,
            "hit_bet_count": value.hit_bet_count,
            "hit_race_count": value.hit_race_count,
            "investment": value.investment,
            "max_single_day_maximum_drawdown": value.max_single_day_maximum_drawdown,
            "no_bet_race_count": value.no_bet_race_count,
            "payout": value.payout,
            "profit": value.profit,
            "race_count": value.race_count,
            "race_hit_rate": _decimal_text(value.race_hit_rate),
            "roi": _decimal_text(value.roi),
            "settled_bet_count": value.settled_bet_count,
            "settled_purchase_race_count": value.settled_purchase_race_count,
            "settled_race_count": value.settled_race_count,
            "unsettled_race_count": value.unsettled_race_count,
            "unsupported_race_count": value.unsupported_race_count,
            "void_race_count": value.void_race_count,
        },
        "compatibility": {
            "dataset_id": value.dataset_id,
            "organization": value.organization,
            "race_budget_total_amount": value.race_budget_total_amount,
            "selection_policy": value.selection_policy,
            "settlement_information_cutoff_utc": _datetime_text(
                value.settlement_information_cutoff
            ),
            "source_system": value.source_system,
            "strategy_config_hash": value.strategy_config_hash,
            "strategy_id": value.strategy_id,
            "strategy_name": value.strategy_name,
            "target_commit_id": value.target_commit_id,
        },
        "coverage": {
            "completed_day_count": value.completed_day_count,
            "first_target_date": value.first_target_date.isoformat(),
            "last_target_date": value.last_target_date.isoformat(),
            "no_executable_diagnostic_day_count": value.no_executable_diagnostic_day_count,
            "partial_resolution_diagnostic_day_count": value.partial_resolution_diagnostic_day_count,
            "selected_record_count": value.selected_record_count,
        },
        "schema_version": value.schema_version,
        "selection": {
            "persisted_content_sha256s": list(
                value.selection.persisted_content_sha256s
            ),
            "selection_sha256": value.selection_sha256,
        },
        "version": _RESULT_VERSION,
    }


def _result_digest(value: NARDailyReplayAggregationResult) -> str:
    return _sha256(_canonical_json(_result_payload(value)).encode("utf-8")).hexdigest()


@_dataclass(frozen=True, slots=True, init=False)
class NARDailyReplayAggregationResult:
    schema_version: int
    selection: NARDailyReplayAggregationSelection
    organization: str
    source_system: str
    dataset_id: str
    selection_policy: str
    settlement_information_cutoff: _datetime
    strategy_id: str
    strategy_name: str
    strategy_config_hash: str
    target_commit_id: str
    race_budget_total_amount: int
    first_target_date: _date
    last_target_date: _date
    selected_record_count: int
    completed_day_count: int
    partial_resolution_diagnostic_day_count: int
    no_executable_diagnostic_day_count: int
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
    roi: _Decimal | None
    bet_hit_rate: _Decimal | None
    race_hit_rate: _Decimal | None
    by_bet_type: _Mapping[str, _BetTypeSummary]
    max_single_day_maximum_drawdown: int | None
    selection_sha256: str = _field(init=False)
    aggregate_content_sha256: str = _field(init=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise _RepositoryValidationError(
            "aggregation results must be produced by aggregate_nar_daily_replay_selection"
        )

    @classmethod
    def _from_records(
        cls,
        *,
        selection: NARDailyReplayAggregationSelection,
        records: tuple[_PersistedResult, ...],
    ) -> NARDailyReplayAggregationResult:
        if type(selection) is not NARDailyReplayAggregationSelection:
            raise _RepositoryValidationError("selection must be exact aggregation selection")
        if type(records) is not tuple or len(records) != len(
            selection.persisted_content_sha256s
        ):
            raise _RepositoryDataIntegrityError(
                "selected records disagree with the exact selection"
            )

        previous_date: _date | None = None
        compatibility: tuple[object, ...] | None = None
        for identity, record in zip(selection.persisted_content_sha256s, records):
            if (
                type(record) is not _PersistedResult
                or record.persisted_content_sha256 != identity
            ):
                raise _RepositoryDataIntegrityError(
                    "selected record identity disagrees with the exact selection"
                )
            if previous_date is not None and record.target_date <= previous_date:
                if record.target_date == previous_date:
                    raise _RepositoryValidationError(
                        "selection contains duplicate target_date"
                    )
                raise _RepositoryValidationError(
                    "selection must be strictly target-date ascending"
                )
            current_compatibility = _compatibility(record)
            if compatibility is None:
                compatibility = current_compatibility
            elif current_compatibility != compatibility:
                raise _RepositoryValidationError(
                    "selected results are analytically incompatible"
                )
            previous_date = record.target_date

        completed = tuple(
            record
            for record in records
            if record.execution_state is _ExecutionState.FULL_DAY_REPLAY_COMPLETED
        )
        partial_count = sum(
            record.execution_state is _ExecutionState.NOT_RUN_PARTIAL_RESOLUTION
            for record in records
        )
        no_executable_count = sum(
            record.execution_state
            is _ExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS
            for record in records
        )
        if len(completed) + partial_count + no_executable_count != len(records):
            raise _RepositoryDataIntegrityError(
                "selected result execution state is invalid"
            )
        summaries = tuple(record.summary for record in completed)
        if any(summary is None for summary in summaries):
            raise _RepositoryDataIntegrityError("completed record has no summary")

        def total(name: str) -> int:
            return sum(
                getattr(summary, name)
                for summary in summaries
                if summary is not None
            )

        investment = total("investment")
        payout = total("payout")
        settled_bet_count = total("settled_bet_count")
        settled_purchase_race_count = total("settled_purchase_race_count")
        hit_bet_count = total("hit_bet_count")
        hit_race_count = total("hit_race_count")
        first = records[0]
        values = {
            "schema_version": 1,
            "selection": selection,
            "organization": first.organization,
            "source_system": first.source_system,
            "dataset_id": first.dataset_id,
            "selection_policy": first.selection_policy,
            "settlement_information_cutoff": first.settlement_information_cutoff,
            "strategy_id": first.strategy_id,
            "strategy_name": first.strategy_name,
            "strategy_config_hash": first.strategy_config_hash,
            "target_commit_id": first.target_commit_id,
            "race_budget_total_amount": first.race_budget_total_amount,
            "first_target_date": first.target_date,
            "last_target_date": records[-1].target_date,
            "selected_record_count": len(records),
            "completed_day_count": len(completed),
            "partial_resolution_diagnostic_day_count": partial_count,
            "no_executable_diagnostic_day_count": no_executable_count,
            "race_count": total("race_count"),
            "settled_race_count": total("settled_race_count"),
            "unsettled_race_count": total("unsettled_race_count"),
            "no_bet_race_count": total("no_bet_race_count"),
            "void_race_count": total("void_race_count"),
            "error_race_count": total("error_race_count"),
            "unsupported_race_count": total("unsupported_race_count"),
            "bet_count": total("bet_count"),
            "settled_bet_count": settled_bet_count,
            "settled_purchase_race_count": settled_purchase_race_count,
            "hit_bet_count": hit_bet_count,
            "hit_race_count": hit_race_count,
            "investment": investment,
            "payout": payout,
            "profit": payout - investment,
            "roi": _rate(payout, investment),
            "bet_hit_rate": _rate(hit_bet_count, settled_bet_count),
            "race_hit_rate": _rate(
                hit_race_count, settled_purchase_race_count
            ),
            "by_bet_type": _aggregate_bet_types(completed),
            "max_single_day_maximum_drawdown": (
                None
                if not completed
                else max(
                    record.summary.maximum_drawdown
                    for record in completed
                    if record.summary is not None
                )
            ),
        }
        result = object.__new__(cls)
        for name, value in values.items():
            object.__setattr__(result, name, value)
        result._validate()
        return result

    def _validate(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise _RepositoryValidationError("result schema_version must be exact version 1")
        if type(self.selection) is not NARDailyReplayAggregationSelection:
            raise _RepositoryValidationError("selection must be exact aggregation selection")
        if (self.organization, self.source_system) != _PROVIDER:
            raise _RepositoryValidationError("aggregate provider must be exact NAR/nar_official")
        for name in (
            "dataset_id",
            "selection_policy",
            "strategy_id",
            "strategy_name",
            "target_commit_id",
        ):
            _text(getattr(self, name), name)
        _digest(self.strategy_config_hash, "strategy_config_hash")
        object.__setattr__(
            self,
            "settlement_information_cutoff",
            _utc(self.settlement_information_cutoff, "settlement_information_cutoff"),
        )
        if (
            type(self.race_budget_total_amount) is not int
            or self.race_budget_total_amount < 0
            or self.race_budget_total_amount % 100
        ):
            raise _RepositoryValidationError("race budget is invalid")
        if type(self.first_target_date) is not _date or type(self.last_target_date) is not _date:
            raise _RepositoryValidationError("aggregate target-date coverage is invalid")
        if self.first_target_date > self.last_target_date:
            raise _RepositoryValidationError("aggregate target-date coverage is reversed")

        day_counts = (
            self.selected_record_count,
            self.completed_day_count,
            self.partial_resolution_diagnostic_day_count,
            self.no_executable_diagnostic_day_count,
        )
        additive = (
            self.race_count,
            self.settled_race_count,
            self.unsettled_race_count,
            self.no_bet_race_count,
            self.void_race_count,
            self.error_race_count,
            self.unsupported_race_count,
            self.bet_count,
            self.settled_bet_count,
            self.settled_purchase_race_count,
            self.hit_bet_count,
            self.hit_race_count,
            self.investment,
            self.payout,
        )
        if any(type(value) is not int or value < 0 for value in (*day_counts, *additive)):
            raise _RepositoryValidationError("aggregate counts and money must be nonnegative ints")
        if self.selected_record_count != len(self.selection.persisted_content_sha256s):
            raise _RepositoryValidationError("selected count disagrees with selection")
        if (
            self.completed_day_count
            + self.partial_resolution_diagnostic_day_count
            + self.no_executable_diagnostic_day_count
            != self.selected_record_count
        ):
            raise _RepositoryValidationError("aggregate day-state counts are inconsistent")
        if (
            self.settled_race_count
            + self.unsettled_race_count
            + self.no_bet_race_count
            + self.void_race_count
            + self.error_race_count
            + self.unsupported_race_count
            != self.race_count
            or self.settled_bet_count > self.bet_count
            or self.hit_bet_count > self.settled_bet_count
            or self.hit_race_count > self.settled_purchase_race_count
            or self.settled_purchase_race_count > self.settled_race_count
        ):
            raise _RepositoryValidationError("aggregate counts are inconsistent")
        if type(self.profit) is not int or self.profit != self.payout - self.investment:
            raise _RepositoryValidationError("aggregate profit is inconsistent")
        if self.settled_bet_count == 0 and any(
            value != 0 for value in (self.investment, self.payout, self.profit)
        ):
            raise _RepositoryValidationError("unsettled aggregate must have zero money")
        if self.settled_bet_count > 0 and (
            self.investment <= 0 or self.investment % 100
        ):
            raise _RepositoryValidationError("settled aggregate investment is invalid")
        expected_roi = _rate(self.payout, self.investment)
        expected_bet_rate = _rate(self.hit_bet_count, self.settled_bet_count)
        expected_race_rate = _rate(
            self.hit_race_count, self.settled_purchase_race_count
        )
        if (
            self.roi != expected_roi
            or self.bet_hit_rate != expected_bet_rate
            or self.race_hit_rate != expected_race_rate
        ):
            raise _RepositoryValidationError("aggregate rates disagree with totals")

        if not isinstance(self.by_bet_type, _Mapping):
            raise _RepositoryValidationError("by_bet_type must be a Mapping")
        copied: dict[str, _BetTypeSummary] = {}
        for key, value in self.by_bet_type.items():
            try:
                bet_type = _validate_bet_type(key)
            except (TypeError, ValueError) as error:
                raise _RepositoryValidationError("aggregate bet type is unsupported") from error
            if type(value) is not _BetTypeSummary or value.bet_type != bet_type:
                raise _RepositoryValidationError("aggregate bet-type entry is invalid")
            copied[bet_type] = value
        copied = {key: copied[key] for key in sorted(copied)}
        if (self.bet_count == 0) != (not copied):
            raise _RepositoryValidationError("aggregate bet-type emptiness is inconsistent")
        if copied and (
            sum(value.bet_count for value in copied.values()) != self.bet_count
            or sum(value.settled_bet_count for value in copied.values())
            != self.settled_bet_count
            or sum(value.hit_bet_count for value in copied.values()) != self.hit_bet_count
            or sum(value.investment for value in copied.values()) != self.investment
            or sum(value.payout for value in copied.values()) != self.payout
            or sum(value.profit for value in copied.values()) != self.profit
        ):
            raise _RepositoryValidationError("aggregate bet-type totals are inconsistent")
        object.__setattr__(self, "by_bet_type", _MappingProxyType(copied))

        if self.completed_day_count == 0:
            if self.max_single_day_maximum_drawdown is not None or any(additive):
                raise _RepositoryValidationError("diagnostic-only aggregate has completed totals")
        elif (
            type(self.max_single_day_maximum_drawdown) is not int
            or self.max_single_day_maximum_drawdown < 0
        ):
            raise _RepositoryValidationError("single-day drawdown statistic is invalid")

        object.__setattr__(self, "selection_sha256", self.selection.selection_sha256)
        object.__setattr__(self, "aggregate_content_sha256", _result_digest(self))


def _compatibility(record: _PersistedResult) -> tuple[object, ...]:
    return (
        record.schema_version,
        record.organization,
        record.source_system,
        record.dataset_id,
        record.selection_policy,
        record.settlement_information_cutoff,
        record.strategy_id,
        record.strategy_name,
        record.strategy_config_hash,
        record.target_commit_id,
        record.race_budget_total_amount,
    )


def _aggregate_bet_types(
    completed: tuple[_PersistedResult, ...],
) -> _Mapping[str, _BetTypeSummary]:
    grouped: dict[str, list[_BetTypeSummary]] = {}
    for record in completed:
        if record.summary is None:
            raise _RepositoryDataIntegrityError("completed record has no summary")
        for bet_type, value in record.summary.by_bet_type.items():
            grouped.setdefault(bet_type, []).append(value)
    result: dict[str, _BetTypeSummary] = {}
    for bet_type in sorted(grouped):
        values = grouped[bet_type]
        bet_count = sum(value.bet_count for value in values)
        settled_bet_count = sum(value.settled_bet_count for value in values)
        hit_bet_count = sum(value.hit_bet_count for value in values)
        investment = sum(value.investment for value in values)
        payout = sum(value.payout for value in values)
        result[bet_type] = _BetTypeSummary(
            bet_type=bet_type,
            bet_count=bet_count,
            settled_bet_count=settled_bet_count,
            hit_bet_count=hit_bet_count,
            investment=investment,
            payout=payout,
            profit=payout - investment,
            roi=_rate(payout, investment),
            bet_hit_rate=_rate(hit_bet_count, settled_bet_count),
        )
    return result


def aggregate_nar_daily_replay_selection(
    *,
    selection: NARDailyReplayAggregationSelection,
    repository: _SQLiteNARDailyReplayResultRepository,
) -> NARDailyReplayAggregationResult:
    """Load one explicit compatible series and aggregate completed-day summaries."""

    if type(selection) is not NARDailyReplayAggregationSelection:
        raise _RepositoryValidationError("selection must be exact aggregation selection")
    if type(repository) is not _SQLiteNARDailyReplayResultRepository:
        raise _RepositoryValidationError(
            "repository must be exact SQLiteNARDailyReplayResultRepository"
        )

    loaded: list[_PersistedResult] = []
    for identity in selection.persisted_content_sha256s:
        record = repository.load_result(persisted_content_sha256=identity)
        if record is None:
            raise _RepositoryValidationError("selected persisted result does not exist")
        if type(record) is not _PersistedResult or record.persisted_content_sha256 != identity:
            raise _RepositoryDataIntegrityError("exact-ID load returned contradictory result")
        loaded.append(record)
    return NARDailyReplayAggregationResult._from_records(
        selection=selection,
        records=tuple(loaded),
    )


if "annotations" in globals():
    del annotations
