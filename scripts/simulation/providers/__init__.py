"""Public contracts and pure normalization helpers for simulation providers."""

from .errors import (
    ProviderCompletenessError,
    ProviderUnsupportedError,
    ProviderValidationError,
    SimulationProviderError,
)
from .models import (
    CompletenessResult,
    CompletenessStatus,
    ProviderContext,
    RaceEntryUniverse,
    RawOddsBatch,
    RawOddsEntry,
    RawPayoutPublication,
    RawPayoutRecord,
    RawRaceResult,
    RawRaceResultEntry,
    expected_selections,
)
from .interfaces import (
    OddsSnapshotProvider,
    PayoutProvider,
    ProviderBuildResult,
    RaceResultProvider,
)
from .normalization import (
    normalize_payout_status,
    normalize_result_entry_status,
    normalize_result_status,
    parse_decimal_odds,
    parse_finish_position,
    parse_payout_per_100,
    parse_positive_int,
    resolve_selection,
)
from .result_provider import DefaultRaceResultProvider
from .odds_provider import DefaultOddsSnapshotProvider

__all__ = (
    "SimulationProviderError",
    "ProviderValidationError",
    "ProviderCompletenessError",
    "ProviderUnsupportedError",
    "ProviderContext",
    "RaceEntryUniverse",
    "CompletenessStatus",
    "CompletenessResult",
    "RawRaceResultEntry",
    "RawRaceResult",
    "RawOddsEntry",
    "RawOddsBatch",
    "RawPayoutRecord",
    "RawPayoutPublication",
    "ProviderBuildResult",
    "RaceResultProvider",
    "OddsSnapshotProvider",
    "PayoutProvider",
    "parse_positive_int",
    "parse_finish_position",
    "parse_decimal_odds",
    "parse_payout_per_100",
    "normalize_result_status",
    "normalize_result_entry_status",
    "normalize_payout_status",
    "resolve_selection",
    "expected_selections",
    "DefaultRaceResultProvider",
    "DefaultOddsSnapshotProvider",
)
