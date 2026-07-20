"""Pure conversion helpers for race-result Provider implementations."""

from dataclasses import dataclass

from scripts.simulation.repositories.interfaces import (
    PersistedRaceResult,
    PersistedRaceResultEntry,
    RaceResultEntryStatus,
    RaceResultStatus,
)

from .errors import ProviderValidationError
from .interfaces import ProviderBuildResult
from .models import (
    CompletenessResult,
    CompletenessStatus,
    ProviderContext,
    RaceEntryUniverse,
    RawRaceResult,
    RawRaceResultEntry,
)
from .normalization import (
    normalize_result_entry_status,
    normalize_result_status,
    parse_finish_position,
)


_COMPLETENESS_RESULT_TYPE = CompletenessResult


def _build_persisted_result_entry(
    raw: RawRaceResultEntry,
    universe: RaceEntryUniverse,
) -> PersistedRaceResultEntry:
    """Convert one raw result entry after fail-closed universe validation.

    The helper deliberately does not assign meaning to active, excluded, or
    cancelled entries.  It only verifies that the raw horse and entry IDs agree
    with the supplied immutable universe.
    """

    try:
        if not isinstance(raw, RawRaceResultEntry):
            raise ProviderValidationError("raw must be RawRaceResultEntry")
        if not isinstance(universe, RaceEntryUniverse):
            raise ProviderValidationError("universe must be RaceEntryUniverse")

        mapped_race_entry_id = universe.horse_no_to_race_entry_id[raw.horse_no]
        if mapped_race_entry_id != raw.race_entry_id:
            raise ProviderValidationError("horse_no and race_entry_id mismatch")

        universe_entry_ids = (
            universe.active_race_entry_ids
            | universe.excluded_race_entry_ids
            | universe.cancelled_race_entry_ids
        )
        if raw.race_entry_id not in universe_entry_ids:
            raise ProviderValidationError("unknown race_entry_id")

        finish_position = parse_finish_position(raw.finish_text)
        result_status = normalize_result_entry_status(raw.status_text)
        if result_status is RaceResultEntryStatus.CONFIRMED and finish_position is None:
            raise ProviderValidationError("confirmed entry requires finish_position")
        if result_status is not RaceResultEntryStatus.CONFIRMED and finish_position is not None:
            raise ProviderValidationError("non-confirmed entry requires no finish_position")

        return PersistedRaceResultEntry(
            horse_no=raw.horse_no,
            race_entry_id=raw.race_entry_id,
            finish_position=finish_position,
            result_status=result_status,
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid result entry") from exc


def _build_persisted_race_result(
    raw: RawRaceResult,
    context: ProviderContext,
    universe: RaceEntryUniverse,
) -> PersistedRaceResult:
    """Convert an entire raw result table into one persistence-boundary value."""

    try:
        if not isinstance(raw, RawRaceResult):
            raise ProviderValidationError("raw must be RawRaceResult")
        if not isinstance(context, ProviderContext):
            raise ProviderValidationError("context must be ProviderContext")
        if not isinstance(universe, RaceEntryUniverse):
            raise ProviderValidationError("universe must be RaceEntryUniverse")

        result_status = normalize_result_status(raw.declared_status)
        entries = tuple(
            _build_persisted_result_entry(raw_entry, universe)
            for raw_entry in raw.entries
        )
        return PersistedRaceResult(
            race_id=context.race_id,
            result_status=result_status,
            finalized_at=raw.finalized_at,
            observed_at=context.observed_at,
            source=context.source,
            entries=entries,
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid race result") from exc


@dataclass(frozen=True)
class _ResultCoverage:
    """Immutable entry-ID coverage facts, without completeness policy."""

    expected_entry_ids: tuple[int, ...]
    observed_entry_ids: tuple[int, ...]
    missing_entry_ids: tuple[int, ...]
    unexpected_entry_ids: tuple[int, ...]
    unsupported_entry_ids: tuple[int, ...]
    missing_active_entry_ids: tuple[int, ...]
    missing_excluded_entry_ids: tuple[int, ...]
    missing_cancelled_entry_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        fields = (
            self.expected_entry_ids,
            self.observed_entry_ids,
            self.missing_entry_ids,
            self.unexpected_entry_ids,
            self.unsupported_entry_ids,
            self.missing_active_entry_ids,
            self.missing_excluded_entry_ids,
            self.missing_cancelled_entry_ids,
        )
        if any(
            not isinstance(values, tuple)
            or tuple(sorted(values)) != values
            or len(set(values)) != len(values)
            or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in values)
            for values in fields
        ):
            raise ProviderValidationError("coverage IDs must be sorted unique positive tuples")
        if set(self.missing_entry_ids) & set(self.unexpected_entry_ids):
            raise ProviderValidationError("missing and unexpected coverage overlap")
        if set(self.unsupported_entry_ids) - set(self.observed_entry_ids):
            raise ProviderValidationError("unsupported IDs must be observed")
        categorized_missing = (
            set(self.missing_active_entry_ids)
            | set(self.missing_excluded_entry_ids)
            | set(self.missing_cancelled_entry_ids)
        )
        if categorized_missing != set(self.missing_entry_ids):
            raise ProviderValidationError("missing category IDs must match missing IDs")


def _analyze_result_coverage(
    result: PersistedRaceResult,
    universe: RaceEntryUniverse,
) -> _ResultCoverage:
    """Return immutable expected/observed entry-ID coverage facts.

    This function intentionally does not decide a result's completeness or
    reconcile declared result status with the universe.  Those policy decisions
    are deferred to the next Result Provider stage.
    """

    try:
        if not isinstance(result, PersistedRaceResult):
            raise ProviderValidationError("result must be PersistedRaceResult")
        if not isinstance(universe, RaceEntryUniverse):
            raise ProviderValidationError("universe must be RaceEntryUniverse")

        active_ids = set(universe.active_race_entry_ids)
        excluded_ids = set(universe.excluded_race_entry_ids)
        cancelled_ids = set(universe.cancelled_race_entry_ids)
        expected_ids = active_ids | excluded_ids | cancelled_ids
        observed_ids = {entry.race_entry_id for entry in result.entries}
        missing_ids = expected_ids - observed_ids
        unexpected_ids = observed_ids - expected_ids
        unsupported_ids = {
            entry.race_entry_id
            for entry in result.entries
            if entry.result_status is RaceResultEntryStatus.UNSUPPORTED
        }
        return _ResultCoverage(
            expected_entry_ids=tuple(sorted(expected_ids)),
            observed_entry_ids=tuple(sorted(observed_ids)),
            missing_entry_ids=tuple(sorted(missing_ids)),
            unexpected_entry_ids=tuple(sorted(unexpected_ids)),
            unsupported_entry_ids=tuple(sorted(unsupported_ids)),
            missing_active_entry_ids=tuple(sorted(active_ids - observed_ids)),
            missing_excluded_entry_ids=tuple(sorted(excluded_ids - observed_ids)),
            missing_cancelled_entry_ids=tuple(sorted(cancelled_ids - observed_ids)),
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid result coverage") from exc


def _entry_keys(entry_ids: tuple[int, ...]) -> tuple[str, ...]:
    """Format deterministic discrepancy keys without exposing horse numbers."""

    return tuple(f"race_entry_id:{entry_id}" for entry_id in entry_ids)


def _build_result_completeness(
    result: PersistedRaceResult,
    coverage: _ResultCoverage,
) -> CompletenessResult:
    """Build completeness facts from coverage, without entry-category policy.

    ``CompletenessResult`` deliberately forbids discrepancy keys for
    ``UNSUPPORTED``.  Therefore expected unsupported entries are represented by
    their reason code only; an unsupported *unexpected* entry is represented
    once as an unexpected key, while retaining both reason codes.
    """

    try:
        if not isinstance(result, PersistedRaceResult):
            raise ProviderValidationError("result must be PersistedRaceResult")
        if not isinstance(coverage, _ResultCoverage):
            raise ProviderValidationError("coverage must be _ResultCoverage")

        expected_count = len(coverage.expected_entry_ids)
        actual_count = len(coverage.observed_entry_ids)
        missing_keys = _entry_keys(coverage.missing_entry_ids)
        unexpected_keys = _entry_keys(coverage.unexpected_entry_ids)
        unsupported_for_completeness = tuple(
            entry_id
            for entry_id in coverage.unsupported_entry_ids
            if entry_id not in coverage.unexpected_entry_ids
        )
        reasons = set()
        if coverage.unexpected_entry_ids:
            reasons.add("unexpected_result_entries")
        if result.result_status is RaceResultStatus.UNSUPPORTED:
            reasons.add("unsupported_result_status")
        if coverage.unsupported_entry_ids:
            reasons.add("unsupported_result_entries")
        if result.result_status is RaceResultStatus.PARTIAL:
            reasons.add("partial_result_status")
        if coverage.missing_entry_ids:
            reasons.add("missing_result_entries")

        if coverage.unexpected_entry_ids:
            status = CompletenessStatus.INVALID
            result_missing_keys = missing_keys
            result_unexpected_keys = unexpected_keys
        elif result.result_status is RaceResultStatus.UNSUPPORTED or unsupported_for_completeness:
            status = CompletenessStatus.UNSUPPORTED
            result_missing_keys = ()
            result_unexpected_keys = ()
        elif result.result_status is RaceResultStatus.PARTIAL or coverage.missing_entry_ids:
            status = CompletenessStatus.INCOMPLETE
            result_missing_keys = missing_keys
            result_unexpected_keys = ()
        else:
            status = CompletenessStatus.COMPLETE
            result_missing_keys = ()
            result_unexpected_keys = ()

        return CompletenessResult(
            status=status,
            expected_count=expected_count,
            actual_count=actual_count,
            missing_keys=result_missing_keys,
            unexpected_keys=result_unexpected_keys,
            reasons=tuple(sorted(reasons)),
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid result completeness") from exc


@dataclass(frozen=True)
class _ResultEntrySemanticIssues:
    """Immutable universe-category versus entry-status mismatch facts."""

    active_non_confirmed_entry_ids: tuple[int, ...]
    excluded_non_void_entry_ids: tuple[int, ...]
    cancelled_non_void_entry_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        fields = (
            self.active_non_confirmed_entry_ids,
            self.excluded_non_void_entry_ids,
            self.cancelled_non_void_entry_ids,
        )
        if any(
            not isinstance(values, tuple)
            or tuple(sorted(values)) != values
            or len(values) != len(set(values))
            or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in values)
            for values in fields
        ):
            raise ProviderValidationError("semantic issue IDs must be sorted unique positive tuples")
        categories = tuple(set(values) for values in fields)
        if any(left & right for index, left in enumerate(categories) for right in categories[index + 1:]):
            raise ProviderValidationError("semantic issue categories overlap")

    @property
    def has_issues(self) -> bool:
        return bool(self.all_issue_entry_ids)

    @property
    def all_issue_entry_ids(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                set(self.active_non_confirmed_entry_ids)
                | set(self.excluded_non_void_entry_ids)
                | set(self.cancelled_non_void_entry_ids)
            )
        )


def _analyze_result_entry_semantics(
    result: PersistedRaceResult,
    universe: RaceEntryUniverse,
) -> _ResultEntrySemanticIssues:
    """Report category/status mismatches without applying result-level policy."""

    try:
        if not isinstance(result, PersistedRaceResult):
            raise ProviderValidationError("result must be PersistedRaceResult")
        if not isinstance(universe, RaceEntryUniverse):
            raise ProviderValidationError("universe must be RaceEntryUniverse")

        active_ids = set(universe.active_race_entry_ids)
        excluded_ids = set(universe.excluded_race_entry_ids)
        cancelled_ids = set(universe.cancelled_race_entry_ids)
        active_issues = {
            entry.race_entry_id
            for entry in result.entries
            if entry.race_entry_id in active_ids
            and entry.result_status is not RaceResultEntryStatus.CONFIRMED
        }
        excluded_issues = {
            entry.race_entry_id
            for entry in result.entries
            if entry.race_entry_id in excluded_ids
            and entry.result_status is not RaceResultEntryStatus.VOID
        }
        cancelled_issues = {
            entry.race_entry_id
            for entry in result.entries
            if entry.race_entry_id in cancelled_ids
            and entry.result_status is not RaceResultEntryStatus.VOID
        }
        return _ResultEntrySemanticIssues(
            active_non_confirmed_entry_ids=tuple(sorted(active_issues)),
            excluded_non_void_entry_ids=tuple(sorted(excluded_issues)),
            cancelled_non_void_entry_ids=tuple(sorted(cancelled_issues)),
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid result entry semantics") from exc


def _apply_result_entry_semantics(
    completeness: CompletenessResult,
    issues: _ResultEntrySemanticIssues,
) -> CompletenessResult:
    """Promote existing completeness to INVALID when semantic issues exist."""

    try:
        if not isinstance(completeness, _COMPLETENESS_RESULT_TYPE):
            raise ProviderValidationError("completeness must be CompletenessResult")
        if not isinstance(issues, _ResultEntrySemanticIssues):
            raise ProviderValidationError("issues must be _ResultEntrySemanticIssues")
        if not issues.has_issues:
            return completeness

        reasons = set(completeness.reasons)
        if issues.active_non_confirmed_entry_ids:
            reasons.add("active_non_confirmed_result_entries")
        if issues.excluded_non_void_entry_ids:
            reasons.add("excluded_non_void_result_entries")
        if issues.cancelled_non_void_entry_ids:
            reasons.add("cancelled_non_void_result_entries")
        return CompletenessResult(
            status=CompletenessStatus.INVALID,
            expected_count=completeness.expected_count,
            actual_count=completeness.actual_count,
            missing_keys=completeness.missing_keys,
            unexpected_keys=completeness.unexpected_keys,
            duplicate_keys=completeness.duplicate_keys,
            reasons=tuple(sorted(reasons)),
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid semantic completeness") from exc


@dataclass(frozen=True)
class _ResultRaceStatusSemanticIssues:
    """Immutable race-level status versus entry-status mismatch facts."""

    void_race_non_void_entry_ids: tuple[int, ...]
    unsupported_race_non_unsupported_entry_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        fields = (self.void_race_non_void_entry_ids, self.unsupported_race_non_unsupported_entry_ids)
        if any(
            not isinstance(values, tuple)
            or tuple(sorted(values)) != values
            or len(values) != len(set(values))
            or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in values)
            for values in fields
        ):
            raise ProviderValidationError("race status issue IDs must be sorted unique positive tuples")
        if set(fields[0]) & set(fields[1]):
            raise ProviderValidationError("race status issue categories overlap")

    @property
    def has_issues(self) -> bool:
        return bool(self.all_issue_entry_ids)

    @property
    def all_issue_entry_ids(self) -> tuple[int, ...]:
        return tuple(sorted(set(self.void_race_non_void_entry_ids) | set(self.unsupported_race_non_unsupported_entry_ids)))


def _analyze_result_race_status_semantics(
    result: PersistedRaceResult,
) -> _ResultRaceStatusSemanticIssues:
    """Report race-level status conflicts without category or coverage analysis."""

    try:
        if not isinstance(result, PersistedRaceResult):
            raise ProviderValidationError("result must be PersistedRaceResult")
        void_issues = ()
        unsupported_issues = ()
        if result.result_status is RaceResultStatus.VOID:
            void_issues = tuple(sorted(entry.race_entry_id for entry in result.entries if entry.result_status is not RaceResultEntryStatus.VOID))
        elif result.result_status is RaceResultStatus.UNSUPPORTED:
            unsupported_issues = tuple(sorted(entry.race_entry_id for entry in result.entries if entry.result_status is not RaceResultEntryStatus.UNSUPPORTED))
        return _ResultRaceStatusSemanticIssues(void_issues, unsupported_issues)
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid race status semantics") from exc


def _apply_result_race_status_semantics(
    completeness: CompletenessResult,
    issues: _ResultRaceStatusSemanticIssues,
) -> CompletenessResult:
    """Promote completeness to INVALID when race-status issues exist."""

    try:
        if not isinstance(completeness, _COMPLETENESS_RESULT_TYPE):
            raise ProviderValidationError("completeness must be CompletenessResult")
        if not isinstance(issues, _ResultRaceStatusSemanticIssues):
            raise ProviderValidationError("issues must be _ResultRaceStatusSemanticIssues")
        if not issues.has_issues:
            return completeness
        reasons = set(completeness.reasons)
        if issues.void_race_non_void_entry_ids:
            reasons.add("void_race_non_void_result_entries")
        if issues.unsupported_race_non_unsupported_entry_ids:
            reasons.add("unsupported_race_non_unsupported_result_entries")
        return CompletenessResult(
            status=CompletenessStatus.INVALID,
            expected_count=completeness.expected_count,
            actual_count=completeness.actual_count,
            missing_keys=completeness.missing_keys,
            unexpected_keys=completeness.unexpected_keys,
            duplicate_keys=completeness.duplicate_keys,
            reasons=tuple(sorted(reasons)),
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid race status completeness") from exc


def _build_race_result_provider_output(
    raw: RawRaceResult,
    context: ProviderContext,
    universe: RaceEntryUniverse,
) -> ProviderBuildResult[PersistedRaceResult]:
    """Build one result-table value and its fully validated completeness facts.

    This package-internal helper deliberately only composes the established
    conversion, coverage, and semantic-policy helpers.  It does not persist,
    fetch, mutate, or reinterpret any of their inputs or intermediate values.
    """

    try:
        result = _build_persisted_race_result(raw, context, universe)
        coverage = _analyze_result_coverage(result, universe)
        completeness = _build_result_completeness(result, coverage)
        entry_issues = _analyze_result_entry_semantics(result, universe)
        completeness = _apply_result_entry_semantics(completeness, entry_issues)
        race_status_issues = _analyze_result_race_status_semantics(result)
        completeness = _apply_result_race_status_semantics(
            completeness,
            race_status_issues,
        )
        return ProviderBuildResult(value=result, completeness=completeness)
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid race result provider output") from exc


class DefaultRaceResultProvider:
    """Stateless concrete Result Provider backed by the internal pipeline."""

    __slots__ = ()

    def build_race_result(
        self,
        raw: RawRaceResult,
        context: ProviderContext,
        universe: RaceEntryUniverse,
    ) -> ProviderBuildResult[PersistedRaceResult]:
        """Build a persistence-boundary result and validated completeness facts."""

        return _build_race_result_provider_output(raw, context, universe)
