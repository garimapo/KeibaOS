"""Repository contracts and immutable persistence-boundary values."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Protocol, Sequence

BET_TYPES = frozenset({"単勝", "馬連", "ワイド", "3連複"})

class RaceResultStatus(str, Enum):
    COMPLETE="complete"; PARTIAL="partial"; VOID="void"; UNSUPPORTED="unsupported"

class RaceResultEntryStatus(str, Enum):
    CONFIRMED="confirmed"; VOID="void"; UNSUPPORTED="unsupported"

class PayoutStatus(str, Enum):
    WINNING="winning"; REFUND="refund"; VOID="void"; UNSUPPORTED="unsupported"

def _aware(value: object, name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None: raise ValueError(f"{name} must be a timezone-aware datetime")

def validate_bet_type(value: object) -> str:
    if not isinstance(value, str) or value not in BET_TYPES: raise ValueError("unsupported bet_type")
    return value

def normalize_selection(values: Sequence[object], bet_type: object) -> tuple[int, ...]:
    kind=validate_bet_type(bet_type); expected={"単勝":1,"馬連":2,"ワイド":2,"3連複":3}[kind]
    raw=tuple(values)
    if any(not isinstance(item,int) or isinstance(item,bool) or item<=0 for item in raw): raise ValueError("race_entry_ids must be positive integers")
    result=tuple(sorted(raw))
    if len(result)!=expected or len(set(result))!=expected: raise ValueError(f"{kind} requires {expected} unique race_entry_ids")
    return result

def selection_key(values: Sequence[object], bet_type: object) -> str:
    return "-".join(str(value) for value in normalize_selection(values,bet_type))

def normalize_orders(rows: Sequence[tuple[int,int]], bet_type: object, stored_key: object) -> tuple[int,...]:
    if not isinstance(stored_key,str) or not stored_key.strip(): raise ValueError("selection_key must be non-empty")
    ordered=tuple(sorted(rows, key=lambda item:item[0]))
    if tuple(item[0] for item in ordered)!=tuple(range(1,len(ordered)+1)): raise ValueError("selection_order must be contiguous from one")
    ids=tuple(item[1] for item in ordered); normalized=normalize_selection(ids,bet_type)
    if ids!=normalized or stored_key!=selection_key(normalized,bet_type): raise ValueError("selection rows do not match normalized selection_key")
    return normalized

def _header(race_id: object, bet_type: object, observed_at: object, is_complete: object, source: object) -> None:
    if not isinstance(race_id,int) or isinstance(race_id,bool) or race_id<=0: raise ValueError("race_id must be a positive integer")
    validate_bet_type(bet_type); _aware(observed_at,"observed_at")
    if not isinstance(is_complete,bool): raise ValueError("is_complete must be bool")
    if not isinstance(source,str) or not source.strip(): raise ValueError("source must be a non-empty string")

@dataclass(frozen=True)
class PersistedRaceResultEntry:
    horse_no:int; race_entry_id:int; finish_position:int|None; result_status:RaceResultEntryStatus
    def __post_init__(self)->None:
        if any(not isinstance(x,int) or isinstance(x,bool) or x<=0 for x in (self.horse_no,self.race_entry_id)): raise ValueError("entry identifiers must be positive integers")
        if self.finish_position is not None and (not isinstance(self.finish_position,int) or isinstance(self.finish_position,bool) or self.finish_position<=0): raise ValueError("finish_position must be positive or None")
        if not isinstance(self.result_status,RaceResultEntryStatus): raise ValueError("result_status must be RaceResultEntryStatus")

@dataclass(frozen=True)
class PersistedRaceResult:
    race_id:int; result_status:RaceResultStatus; finalized_at:datetime|None; observed_at:datetime; source:str; entries:Sequence[PersistedRaceResultEntry]
    def __post_init__(self)->None:
        if not isinstance(self.race_id,int) or isinstance(self.race_id,bool) or self.race_id<=0: raise ValueError("race_id must be positive")
        if not isinstance(self.result_status,RaceResultStatus): raise ValueError("result_status must be RaceResultStatus")
        _aware(self.observed_at,"observed_at")
        if self.finalized_at is not None: _aware(self.finalized_at,"finalized_at")
        if self.finalized_at is not None and self.finalized_at>self.observed_at: raise ValueError("finalized_at must not be after observed_at")
        if self.result_status is RaceResultStatus.COMPLETE and self.finalized_at is None: raise ValueError("complete result requires finalized_at")
        if not isinstance(self.source,str) or not self.source.strip(): raise ValueError("source must be non-empty")
        entries=tuple(sorted(self.entries,key=lambda e:e.race_entry_id))
        if not all(isinstance(e,PersistedRaceResultEntry) for e in entries) or len({e.race_entry_id for e in entries})!=len(entries): raise ValueError("entries must have unique PersistedRaceResultEntry race_entry_ids")
        object.__setattr__(self,"entries",entries)

@dataclass(frozen=True)
class OddsSnapshotEntry:
    race_entry_ids:Sequence[int]; odds:Decimal
    def __post_init__(self)->None:
        if not isinstance(self.odds,Decimal) or not self.odds.is_finite() or self.odds<=0: raise ValueError("odds must be positive finite Decimal")
        object.__setattr__(self,"race_entry_ids",tuple(self.race_entry_ids))

@dataclass(frozen=True)
class OddsSnapshotBatch:
    race_id:int; bet_type:str; observed_at:datetime; is_complete:bool; source:str; entries:Sequence[OddsSnapshotEntry]; source_url:str|None=None; batch_id:int|None=None
    def __post_init__(self)->None:
        _header(self.race_id,self.bet_type,self.observed_at,self.is_complete,self.source)
        if self.batch_id is not None and (not isinstance(self.batch_id,int) or isinstance(self.batch_id,bool) or self.batch_id<=0): raise ValueError("batch_id must be positive or None")
        values=tuple(OddsSnapshotEntry(normalize_selection(item.race_entry_ids,self.bet_type),item.odds) for item in self.entries)
        if not values or len({x.race_entry_ids for x in values})!=len(values): raise ValueError("entries must be non-empty unique selections")
        object.__setattr__(self,"entries",tuple(sorted(values,key=lambda x:x.race_entry_ids)))

@dataclass(frozen=True)
class PayoutRecord:
    race_entry_ids:Sequence[int]; payout_per_100:int; payout_status:PayoutStatus
    def __post_init__(self)->None:
        if not isinstance(self.payout_status,PayoutStatus): raise ValueError("payout_status must be PayoutStatus")
        if not isinstance(self.payout_per_100,int) or isinstance(self.payout_per_100,bool) or self.payout_per_100<0: raise ValueError("payout_per_100 must be non-negative int")
        if self.payout_status is PayoutStatus.WINNING and self.payout_per_100==0: raise ValueError("winning payout must be positive")
        object.__setattr__(self,"race_entry_ids",tuple(self.race_entry_ids))

@dataclass(frozen=True)
class PayoutPublication:
    race_id:int; bet_type:str; finalized_at:datetime|None; observed_at:datetime; is_complete:bool; source:str; entries:Sequence[PayoutRecord]; source_url:str|None=None; publication_id:int|None=None
    def __post_init__(self)->None:
        _header(self.race_id,self.bet_type,self.observed_at,self.is_complete,self.source)
        if self.publication_id is not None and (not isinstance(self.publication_id,int) or isinstance(self.publication_id,bool) or self.publication_id<=0): raise ValueError("publication_id must be positive or None")
        if self.finalized_at is not None: _aware(self.finalized_at,"finalized_at")
        if self.finalized_at is not None and self.finalized_at>self.observed_at: raise ValueError("finalized_at must not be after observed_at")
        if self.is_complete and self.finalized_at is None: raise ValueError("complete publication requires finalized_at")
        values=tuple(PayoutRecord(normalize_selection(item.race_entry_ids,self.bet_type),item.payout_per_100,item.payout_status) for item in self.entries)
        if len({x.race_entry_ids for x in values})!=len(values): raise ValueError("entries must have unique selections")
        object.__setattr__(self,"entries",tuple(sorted(values,key=lambda x:x.race_entry_ids)))

class RaceResultRepository(Protocol):
    def save_race_result(self,result:PersistedRaceResult)->None: ...
    def get_race_result(self,race_id:int)->PersistedRaceResult|None: ...
    def has_complete_race_result(self,race_id:int)->bool: ...
class OddsSnapshotRepository(Protocol):
    def save_odds_batch(self,batch:OddsSnapshotBatch)->OddsSnapshotBatch: ...
    def get_odds_batch(self,batch_id:int)->OddsSnapshotBatch|None: ...
    def get_latest_odds_batch(self,race_id:int,bet_type:str,observed_at_lte:datetime,require_complete:bool=True)->OddsSnapshotBatch|None: ...
class PayoutRepository(Protocol):
    def save_payout_publication(self,publication:PayoutPublication)->PayoutPublication: ...
    def get_payout_publication(self,publication_id:int)->PayoutPublication|None: ...
    def get_latest_payout_publication(self,race_id:int,bet_type:str,observed_at_lte:datetime|None=None,require_complete:bool=True)->PayoutPublication|None: ...
