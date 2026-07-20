"""Pure conversion helpers for odds Provider implementations."""

from dataclasses import dataclass

from scripts.simulation.repositories.interfaces import (
    OddsSnapshotBatch,
    OddsSnapshotEntry,
    selection_key,
    validate_bet_type,
)

from .errors import ProviderValidationError
from .interfaces import ProviderBuildResult
from .models import (
    ProviderContext,
    CompletenessResult,
    CompletenessStatus,
    RaceEntryUniverse,
    RawOddsBatch,
    RawOddsEntry,
    expected_selections,
)
from .normalization import parse_decimal_odds, resolve_selection


def _build_odds_snapshot_entry(
    raw: RawOddsEntry,
    bet_type: str,
    universe: RaceEntryUniverse,
) -> OddsSnapshotEntry:
    """Convert one raw odds row into its persistence-boundary value."""

    try:
        if not isinstance(raw, RawOddsEntry):
            raise ProviderValidationError("raw must be RawOddsEntry")
        if not isinstance(universe, RaceEntryUniverse):
            raise ProviderValidationError("universe must be RaceEntryUniverse")
        validated_bet_type = validate_bet_type(bet_type)
        race_entry_ids = resolve_selection(
            raw.race_entry_ids,
            raw.horse_numbers,
            validated_bet_type,
            universe,
        )
        odds = parse_decimal_odds(raw.odds_text)
        return OddsSnapshotEntry(race_entry_ids=race_entry_ids, odds=odds)
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid odds entry") from exc


def _build_odds_snapshot_batch(
    raw: RawOddsBatch,
    context: ProviderContext,
    universe: RaceEntryUniverse,
) -> OddsSnapshotBatch:
    """Convert one raw odds table while rejecting duplicate canonical selections."""

    try:
        if not isinstance(raw, RawOddsBatch):
            raise ProviderValidationError("raw must be RawOddsBatch")
        if not isinstance(context, ProviderContext):
            raise ProviderValidationError("context must be ProviderContext")
        if not isinstance(universe, RaceEntryUniverse):
            raise ProviderValidationError("universe must be RaceEntryUniverse")

        entries = tuple(
            _build_odds_snapshot_entry(raw_entry, raw.bet_type, universe)
            for raw_entry in raw.entries
        )
        selections = tuple(entry.race_entry_ids for entry in entries)
        if len(selections) != len(set(selections)):
            raise ProviderValidationError("duplicate normalized odds selection")
        return OddsSnapshotBatch(
            race_id=context.race_id,
            bet_type=raw.bet_type,
            observed_at=context.observed_at,
            is_complete=raw.declared_complete,
            source=context.source,
            entries=entries,
            source_url=context.source_url,
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid odds batch") from exc


@dataclass(frozen=True)
class _OddsSelectionCoverage:
    """Immutable canonical expected-versus-observed odds selection facts."""

    expected_selections: tuple[tuple[int, ...], ...]
    observed_selections: tuple[tuple[int, ...], ...]
    missing_selections: tuple[tuple[int, ...], ...]
    unexpected_selections: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        try:
            fields = (
                self.expected_selections,
                self.observed_selections,
                self.missing_selections,
                self.unexpected_selections,
            )
            if any(not isinstance(values, tuple) for values in fields):
                raise ProviderValidationError("coverage collections must be tuples")
            for values in fields:
                if any(
                    not isinstance(selection, tuple)
                    or not selection
                    or tuple(sorted(selection)) != selection
                    or len(selection) != len(set(selection))
                    or any(
                        not isinstance(entry_id, int)
                        or isinstance(entry_id, bool)
                        or entry_id <= 0
                        for entry_id in selection
                    )
                    for selection in values
                ):
                    raise ProviderValidationError("coverage selections must be canonical positive tuples")
                if len(values) != len(set(values)) or tuple(sorted(values)) != values:
                    raise ProviderValidationError("coverage selections must be unique and sorted")

            expected = set(self.expected_selections)
            observed = set(self.observed_selections)
            missing = set(self.missing_selections)
            unexpected = set(self.unexpected_selections)
            if missing != expected - observed or unexpected != observed - expected:
                raise ProviderValidationError("coverage discrepancies do not match selections")
            if missing & unexpected:
                raise ProviderValidationError("coverage discrepancy categories overlap")
        except ProviderValidationError:
            raise
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ProviderValidationError("invalid odds selection coverage") from exc

    @property
    def expected_count(self) -> int:
        return len(self.expected_selections)

    @property
    def observed_count(self) -> int:
        return len(self.observed_selections)

    @property
    def has_missing(self) -> bool:
        return bool(self.missing_selections)

    @property
    def has_unexpected(self) -> bool:
        return bool(self.unexpected_selections)


def _analyze_odds_selection_coverage(
    batch: OddsSnapshotBatch,
    universe: RaceEntryUniverse,
) -> _OddsSelectionCoverage:
    """Compare batch selections against combinations of active race entries."""

    try:
        if not isinstance(batch, OddsSnapshotBatch):
            raise ProviderValidationError("batch must be OddsSnapshotBatch")
        if not isinstance(universe, RaceEntryUniverse):
            raise ProviderValidationError("universe must be RaceEntryUniverse")
        expected = expected_selections(universe.active_entries, batch.bet_type)
        observed = tuple(sorted(entry.race_entry_ids for entry in batch.entries))
        expected_set = set(expected)
        observed_set = set(observed)
        return _OddsSelectionCoverage(
            expected_selections=expected,
            observed_selections=observed,
            missing_selections=tuple(sorted(expected_set - observed_set)),
            unexpected_selections=tuple(sorted(observed_set - expected_set)),
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid odds selection coverage") from exc


def _build_odds_completeness(
    batch: OddsSnapshotBatch,
    coverage: _OddsSelectionCoverage,
) -> CompletenessResult:
    """Translate immutable selection coverage facts into completeness status."""

    try:
        if not isinstance(batch, OddsSnapshotBatch):
            raise ProviderValidationError("batch must be OddsSnapshotBatch")
        if not isinstance(coverage, _OddsSelectionCoverage):
            raise ProviderValidationError("coverage must be _OddsSelectionCoverage")

        missing_keys = tuple(
            selection_key(selection, batch.bet_type)
            for selection in coverage.missing_selections
        )
        unexpected_keys = tuple(
            selection_key(selection, batch.bet_type)
            for selection in coverage.unexpected_selections
        )
        reasons = set()
        if coverage.has_unexpected:
            reasons.add("unexpected_odds_selections")
            status = CompletenessStatus.INVALID
        elif coverage.has_missing or not batch.is_complete:
            status = CompletenessStatus.INCOMPLETE
        else:
            status = CompletenessStatus.COMPLETE
        if coverage.has_missing:
            reasons.add("missing_odds_selections")
        if not batch.is_complete:
            reasons.add("odds_not_declared_complete")

        return CompletenessResult(
            status=status,
            expected_count=coverage.expected_count,
            actual_count=coverage.observed_count,
            missing_keys=missing_keys,
            unexpected_keys=unexpected_keys,
            duplicate_keys=(),
            reasons=tuple(sorted(reasons)),
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid odds completeness") from exc


def _build_odds_provider_output(
    raw: RawOddsBatch,
    context: ProviderContext,
    universe: RaceEntryUniverse,
) -> ProviderBuildResult[OddsSnapshotBatch]:
    """Build one odds table and its coverage-derived completeness facts."""

    try:
        batch = _build_odds_snapshot_batch(raw, context, universe)
        coverage = _analyze_odds_selection_coverage(batch, universe)
        completeness = _build_odds_completeness(batch, coverage)
        return ProviderBuildResult(value=batch, completeness=completeness)
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid odds provider output") from exc


class DefaultOddsSnapshotProvider:
    """Stateless concrete Odds Provider backed by the internal pipeline."""

    __slots__ = ()

    def build_odds_batch(
        self,
        raw: RawOddsBatch,
        context: ProviderContext,
        universe: RaceEntryUniverse,
    ) -> ProviderBuildResult[OddsSnapshotBatch]:
        """Build one persistence-boundary odds batch and completeness facts."""

        return _build_odds_provider_output(raw, context, universe)
