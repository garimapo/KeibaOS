from typing import Protocol,TypeVar,Generic
from dataclasses import dataclass
from .models import CompletenessResult, ProviderContext, RaceEntryUniverse, RawRaceResult, RawOddsBatch, RawPayoutPublication
from .errors import ProviderValidationError
from scripts.simulation.repositories.interfaces import PersistedRaceResult, OddsSnapshotBatch, PayoutPublication
T=TypeVar('T')
@dataclass(frozen=True)
class ProviderBuildResult(Generic[T]):
 value:T; completeness:CompletenessResult
 def __post_init__(self):
  if self.value is None or not isinstance(self.completeness,CompletenessResult): raise ProviderValidationError('value and completeness')
class RaceResultProvider(Protocol):
 def build_race_result(self,raw:RawRaceResult,context:ProviderContext,universe:RaceEntryUniverse)->ProviderBuildResult[PersistedRaceResult]:...
class OddsSnapshotProvider(Protocol):
 def build_odds_batch(self,raw:RawOddsBatch,context:ProviderContext,universe:RaceEntryUniverse)->ProviderBuildResult[OddsSnapshotBatch]:...
class PayoutProvider(Protocol):
 def build_payout_publication(self,raw:RawPayoutPublication,context:ProviderContext,universe:RaceEntryUniverse)->ProviderBuildResult[PayoutPublication]:...
