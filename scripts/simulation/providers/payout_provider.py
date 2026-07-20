"""Pure conversion and status-fact helpers for payout Provider implementations."""

from dataclasses import dataclass

from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutRecord,
    PayoutStatus,
    validate_bet_type,
)

from .errors import ProviderValidationError
from .interfaces import ProviderBuildResult
from .models import (
    CompletenessResult,
    CompletenessStatus,
    ProviderContext,
    RaceEntryUniverse,
    RawPayoutPublication,
    RawPayoutRecord,
)
from .normalization import (
    normalize_payout_status,
    parse_payout_per_100,
    resolve_selection,
)


def _build_payout_record(
    raw: RawPayoutRecord,
    bet_type: str,
    universe: RaceEntryUniverse,
) -> PayoutRecord:
    """Convert one raw payout row into its persistence-boundary value.

    Publication-level duplicate detection, completeness, and settlement
    semantics intentionally remain outside this one-record conversion helper.
    """

    try:
        if not isinstance(raw, RawPayoutRecord):
            raise ProviderValidationError("raw must be RawPayoutRecord")
        if not isinstance(universe, RaceEntryUniverse):
            raise ProviderValidationError("universe must be RaceEntryUniverse")
        validated_bet_type = validate_bet_type(bet_type)
        race_entry_ids = resolve_selection(
            raw.race_entry_ids,
            raw.horse_numbers,
            validated_bet_type,
            universe,
        )
        payout_per_100 = parse_payout_per_100(raw.payout_text)
        payout_status = normalize_payout_status(raw.status_text)
        return PayoutRecord(
            race_entry_ids=race_entry_ids,
            payout_per_100=payout_per_100,
            payout_status=payout_status,
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid payout record") from exc


def _build_payout_publication(
    raw: RawPayoutPublication,
    context: ProviderContext,
    universe: RaceEntryUniverse,
) -> PayoutPublication:
    """Convert one raw payout table while rejecting duplicate selections.

    Completeness, expected combinations, and publication-level status rules are
    intentionally deferred to the next Payout Provider stage.
    """

    try:
        if not isinstance(raw, RawPayoutPublication):
            raise ProviderValidationError("raw must be RawPayoutPublication")
        if not isinstance(context, ProviderContext):
            raise ProviderValidationError("context must be ProviderContext")
        if not isinstance(universe, RaceEntryUniverse):
            raise ProviderValidationError("universe must be RaceEntryUniverse")

        entries = tuple(
            _build_payout_record(raw_record, raw.bet_type, universe)
            for raw_record in raw.entries
        )
        identities = tuple((raw.bet_type, entry.race_entry_ids) for entry in entries)
        if len(identities) != len(set(identities)):
            raise ProviderValidationError("duplicate normalized payout selection")
        return PayoutPublication(
            race_id=context.race_id,
            bet_type=raw.bet_type,
            finalized_at=raw.finalized_at,
            observed_at=context.observed_at,
            is_complete=raw.declared_complete,
            source=context.source,
            entries=entries,
            source_url=context.source_url,
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid payout publication") from exc


@dataclass(frozen=True)
class _PayoutPublicationStatusFacts:
    """Immutable, disjoint selection partitions grouped by payout status."""

    observed_selections: tuple[tuple[int, ...], ...]
    winning_selections: tuple[tuple[int, ...], ...]
    refund_selections: tuple[tuple[int, ...], ...]
    void_selections: tuple[tuple[int, ...], ...]
    unsupported_selections: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        try:
            fields = (
                self.observed_selections,
                self.winning_selections,
                self.refund_selections,
                self.void_selections,
                self.unsupported_selections,
            )
            if any(not isinstance(values, tuple) for values in fields):
                raise ProviderValidationError("status fact collections must be tuples")
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
                    raise ProviderValidationError("status fact selections must be canonical positive tuples")
                if len(values) != len(set(values)) or tuple(sorted(values)) != values:
                    raise ProviderValidationError("status fact selections must be unique and sorted")

            observed = set(self.observed_selections)
            partitions = (
                set(self.winning_selections),
                set(self.refund_selections),
                set(self.void_selections),
                set(self.unsupported_selections),
            )
            if any(left & right for index, left in enumerate(partitions) for right in partitions[index + 1 :]):
                raise ProviderValidationError("status partitions must be disjoint")
            if set().union(*partitions) != observed:
                raise ProviderValidationError("status partitions must equal observed selections")
        except ProviderValidationError:
            raise
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ProviderValidationError("invalid payout publication status facts") from exc

    @property
    def observed_count(self) -> int:
        return len(self.observed_selections)

    @property
    def winning_count(self) -> int:
        return len(self.winning_selections)

    @property
    def refund_count(self) -> int:
        return len(self.refund_selections)

    @property
    def void_count(self) -> int:
        return len(self.void_selections)

    @property
    def unsupported_count(self) -> int:
        return len(self.unsupported_selections)

    @property
    def has_records(self) -> bool:
        return bool(self.observed_selections)

    @property
    def has_unsupported(self) -> bool:
        return bool(self.unsupported_selections)


def _analyze_payout_publication_status_facts(
    publication: PayoutPublication,
) -> _PayoutPublicationStatusFacts:
    """Partition canonical publication selections by their persisted status."""

    try:
        if not isinstance(publication, PayoutPublication):
            raise ProviderValidationError("publication must be PayoutPublication")

        observed = tuple(sorted(record.race_entry_ids for record in publication.entries))
        winning = tuple(
            sorted(record.race_entry_ids for record in publication.entries if record.payout_status is PayoutStatus.WINNING)
        )
        refund = tuple(
            sorted(record.race_entry_ids for record in publication.entries if record.payout_status is PayoutStatus.REFUND)
        )
        void = tuple(
            sorted(record.race_entry_ids for record in publication.entries if record.payout_status is PayoutStatus.VOID)
        )
        unsupported = tuple(
            sorted(record.race_entry_ids for record in publication.entries if record.payout_status is PayoutStatus.UNSUPPORTED)
        )
        return _PayoutPublicationStatusFacts(
            observed_selections=observed,
            winning_selections=winning,
            refund_selections=refund,
            void_selections=void,
            unsupported_selections=unsupported,
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid payout publication status facts") from exc


def _build_payout_completeness(
    publication: PayoutPublication,
    facts: _PayoutPublicationStatusFacts,
) -> CompletenessResult:
    """Build completeness from observed payout status facts only.

    Expected payout combinations and selection discrepancy analysis are deferred
    to a later Provider stage, so observed selections provide both counts here.
    """

    try:
        if not isinstance(publication, PayoutPublication):
            raise ProviderValidationError("publication must be PayoutPublication")
        if not isinstance(facts, _PayoutPublicationStatusFacts):
            raise ProviderValidationError("facts must be _PayoutPublicationStatusFacts")

        reasons: list[str] = []
        if facts.has_unsupported:
            status = CompletenessStatus.UNSUPPORTED
            reasons.append("unsupported_payout_records")
        elif not publication.is_complete:
            status = CompletenessStatus.INCOMPLETE
        else:
            status = CompletenessStatus.COMPLETE
        if not publication.is_complete:
            reasons.append("payout_not_declared_complete")

        return CompletenessResult(
            status=status,
            expected_count=facts.observed_count,
            actual_count=facts.observed_count,
            missing_keys=(),
            unexpected_keys=(),
            duplicate_keys=(),
            reasons=tuple(reasons),
        )
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid payout completeness") from exc


def _build_payout_provider_output(
    raw: RawPayoutPublication,
    context: ProviderContext,
    universe: RaceEntryUniverse,
) -> ProviderBuildResult[PayoutPublication]:
    """Run the payout conversion pipeline in its single prescribed order."""

    try:
        publication = _build_payout_publication(raw, context, universe)
        facts = _analyze_payout_publication_status_facts(publication)
        completeness = _build_payout_completeness(publication, facts)
        return ProviderBuildResult(value=publication, completeness=completeness)
    except ProviderValidationError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ProviderValidationError("invalid payout provider output") from exc


class DefaultPayoutProvider:
    """Stateless concrete Payout Provider backed by the internal pipeline."""

    __slots__ = ()

    def build_payout_publication(
        self,
        raw: RawPayoutPublication,
        context: ProviderContext,
        universe: RaceEntryUniverse,
    ) -> ProviderBuildResult[PayoutPublication]:
        """Build one persistence-boundary payout publication and completeness facts."""

        return _build_payout_provider_output(raw, context, universe)
