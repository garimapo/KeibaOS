from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from itertools import combinations
from types import MappingProxyType
from typing import Mapping, Sequence
from decimal import Decimal
from .errors import ProviderValidationError

class CompletenessStatus(str,Enum): COMPLETE='complete'; INCOMPLETE='incomplete'; UNSUPPORTED='unsupported'; INVALID='invalid'
@dataclass(frozen=True)
class CompletenessResult:
    status:CompletenessStatus; expected_count:int; actual_count:int; missing_keys:frozenset[tuple[int,...]]=frozenset(); unexpected_keys:frozenset[tuple[int,...]]=frozenset(); duplicate_keys:frozenset[tuple[int,...]]=frozenset(); reasons:tuple[str,...]=()
    def __post_init__(self):
        if not isinstance(self.status,CompletenessStatus): raise ValueError('status')
        if any(not isinstance(x,int) or isinstance(x,bool) or x<0 for x in (self.expected_count,self.actual_count)): raise ValueError('counts')
        groups=[]
        for values in (self.missing_keys,self.unexpected_keys,self.duplicate_keys):
            cleaned=tuple(x.strip() for x in values)
            if any(not isinstance(x,str) or not x.strip() for x in values) or len(cleaned)!=len(set(cleaned)): raise ValueError('keys')
            groups.append(tuple(sorted(cleaned)))
        if set(groups[0])&set(groups[1]) or set(groups[0])&set(groups[2]) or set(groups[1])&set(groups[2]): raise ValueError('key categories overlap')
        reasons=tuple(sorted(set(x.strip() for x in self.reasons)))
        if any(not isinstance(x,str) or not x.strip() for x in self.reasons): raise ValueError('reasons')
        if len(groups[0])>self.expected_count or (self.actual_count==0 and groups[2]): raise ValueError('count contradiction')
        if self.status is CompletenessStatus.COMPLETE and (self.expected_count!=self.actual_count or any(groups) or reasons): raise ValueError('complete invariant')
        if self.status is CompletenessStatus.INCOMPLETE and (not(groups[0] or reasons) or groups[1] or groups[2]): raise ValueError('incomplete invariant')
        if self.status in (CompletenessStatus.INVALID,CompletenessStatus.UNSUPPORTED) and not reasons: raise ValueError('reason required')
        if self.status is CompletenessStatus.UNSUPPORTED and any(groups): raise ValueError('unsupported discrepancies')
        object.__setattr__(self,'missing_keys',groups[0]); object.__setattr__(self,'unexpected_keys',groups[1]); object.__setattr__(self,'duplicate_keys',groups[2]); object.__setattr__(self,'reasons',reasons)
@dataclass(frozen=True)
class ProviderContext:
    race_id:int; observed_at:datetime; source:str; source_url:str|None; captured_at:datetime; information_cutoff:datetime; bet_type:str|None=None
    def __post_init__(self):
        if not isinstance(self.race_id,int) or isinstance(self.race_id,bool) or self.race_id<=0: raise ValueError('race_id')
        if not isinstance(self.source,str) or not self.source.strip(): raise ValueError('source')
        for v in (self.observed_at,self.captured_at,self.information_cutoff):
            if not isinstance(v,datetime) or v.tzinfo is None or v.utcoffset() is None: raise ValueError('aware datetime required')
        if self.observed_at>self.information_cutoff or self.captured_at>self.information_cutoff: raise ValueError('future input')
@dataclass(frozen=True)
class RaceEntryUniverse:
    race_id:int; active_race_entry_ids:frozenset[int]; excluded_race_entry_ids:frozenset[int]; cancelled_race_entry_ids:frozenset[int]; horse_no_to_race_entry_id:Mapping[int,int]
    def __post_init__(self):
        groups=tuple(frozenset(x) for x in (self.active_race_entry_ids,self.excluded_race_entry_ids,self.cancelled_race_entry_ids))
        if any(a&b for i,a in enumerate(groups) for b in groups[i+1:]): raise ValueError('universe sets overlap')
        all_ids=set().union(*groups)
        if not all(isinstance(x,int) and not isinstance(x,bool) and x>0 for x in all_ids): raise ValueError('invalid entry id')
        copied=dict(self.horse_no_to_race_entry_id)
        if not all(isinstance(k,int) and not isinstance(k,bool) and k>0 and isinstance(v,int) and not isinstance(v,bool) and v in all_ids for k,v in copied.items()) or len(set(copied.values()))!=len(copied): raise ValueError('invalid horse mapping')
        object.__setattr__(self,'active_race_entry_ids',groups[0]); object.__setattr__(self,'excluded_race_entry_ids',groups[1]); object.__setattr__(self,'cancelled_race_entry_ids',groups[2])
        object.__setattr__(self,'horse_no_to_race_entry_id',MappingProxyType(copied))

    @property
    def active_entries(self)->tuple[int,...]: return tuple(sorted(self.active_race_entry_ids))
def expected_selections(ids:Sequence[int],bet_type:str)->tuple[tuple[int,...],...]:
    from .errors import ProviderValidationError
    from scripts.simulation.repositories.interfaces import validate_bet_type
    try:
        if isinstance(ids,(str,bytes,bytearray,Mapping)): raise TypeError('collection')
        values=tuple(ids); validate_bet_type(bet_type)
        if any(not isinstance(x,int) or isinstance(x,bool) or x<=0 for x in values) or len(values)!=len(set(values)): raise ValueError('ids')
        size={'単勝':1,'馬連':2,'ワイド':2,'3連複':3}[bet_type]
        return tuple(combinations(tuple(sorted(values)),size))
    except (TypeError,ValueError,AttributeError) as exc: raise ProviderValidationError('expected selections') from exc
@dataclass(frozen=True)
class RawRaceResultEntry:
    horse_no:int; race_entry_id:int; finish_text:str|int|None; status_text:str
    def __post_init__(self):
        try:
            for value in (self.horse_no,self.race_entry_id):
                if not isinstance(value,int) or isinstance(value,bool) or value<=0: raise ProviderValidationError('result entry id')
            if self.finish_text is not None:
                if isinstance(self.finish_text,bool) or not isinstance(self.finish_text,(str,int)): raise ProviderValidationError('finish_text')
                if isinstance(self.finish_text,int) and self.finish_text<=0: raise ProviderValidationError('finish_text')
                if isinstance(self.finish_text,str): object.__setattr__(self,'finish_text',self.finish_text.strip())
            if not isinstance(self.status_text,str) or not self.status_text.strip(): raise ProviderValidationError('status_text')
            object.__setattr__(self,'status_text',self.status_text.strip())
        except ProviderValidationError: raise
        except (TypeError,AttributeError) as exc: raise ProviderValidationError('result entry') from exc
@dataclass(frozen=True)
class RawRaceResult:
    declared_status:str; finalized_at:datetime|None; entries:Sequence[RawRaceResultEntry]
    def __post_init__(self):
        try:
            if not isinstance(self.declared_status,str) or not self.declared_status.strip(): raise ProviderValidationError('declared_status')
            object.__setattr__(self,'declared_status',self.declared_status.strip())
            if self.finalized_at is not None and (not isinstance(self.finalized_at,datetime) or self.finalized_at.tzinfo is None or self.finalized_at.utcoffset() is None): raise ProviderValidationError('finalized_at')
            entries=tuple(self.entries)
            if not all(isinstance(x,RawRaceResultEntry) for x in entries): raise ProviderValidationError('entries')
            if len({x.race_entry_id for x in entries})!=len(entries) or len({x.horse_no for x in entries})!=len(entries): raise ProviderValidationError('duplicate entries')
            object.__setattr__(self,'entries',entries)
        except ProviderValidationError: raise
        except (TypeError,AttributeError) as exc: raise ProviderValidationError('result') from exc
@dataclass(frozen=True)
class RawOddsEntry:
    race_entry_ids:Sequence[int]|None; horse_numbers:Sequence[int]|None; odds_text:str|Decimal
    def __post_init__(self):
        try:
            if (self.race_entry_ids is None)==(self.horse_numbers is None): raise ProviderValidationError('selection source')
            name='race_entry_ids' if self.race_entry_ids is not None else 'horse_numbers'; values=tuple(getattr(self,name))
            if not values or any(not isinstance(x,int) or isinstance(x,bool) or x<=0 for x in values) or len(values)!=len(set(values)): raise ProviderValidationError('selection')
            object.__setattr__(self,name,values)
            if not isinstance(self.odds_text,(str,Decimal)) or isinstance(self.odds_text,bool): raise ProviderValidationError('odds_text')
            if isinstance(self.odds_text,str): object.__setattr__(self,'odds_text',self.odds_text.strip())
        except ProviderValidationError: raise
        except (TypeError,AttributeError,ValueError) as exc: raise ProviderValidationError('odds entry') from exc
@dataclass(frozen=True)
class RawOddsBatch:
    bet_type:str; entries:Sequence[RawOddsEntry]; declared_complete:bool
    def __post_init__(self):
        try:
            from scripts.simulation.repositories.interfaces import validate_bet_type
            validate_bet_type(self.bet_type)
            if not isinstance(self.declared_complete,bool): raise ProviderValidationError('declared_complete')
            entries=tuple(self.entries)
            if not all(isinstance(x,RawOddsEntry) for x in entries): raise ProviderValidationError('entries')
            object.__setattr__(self,'entries',entries)
        except ProviderValidationError: raise
        except (TypeError,AttributeError,ValueError) as exc: raise ProviderValidationError('odds batch') from exc
@dataclass(frozen=True)
class RawPayoutRecord:
    race_entry_ids:Sequence[int]|None; horse_numbers:Sequence[int]|None; payout_text:str|int; status_text:str
    def __post_init__(self):
        try:
            if (self.race_entry_ids is None)==(self.horse_numbers is None): raise ProviderValidationError('selection source')
            name='race_entry_ids' if self.race_entry_ids is not None else 'horse_numbers'; values=tuple(getattr(self,name))
            if not values or any(not isinstance(x,int) or isinstance(x,bool) or x<=0 for x in values) or len(values)!=len(set(values)): raise ProviderValidationError('selection')
            object.__setattr__(self,name,values)
            if isinstance(self.payout_text,bool) or not isinstance(self.payout_text,(str,int)) or (isinstance(self.payout_text,int) and self.payout_text<0): raise ProviderValidationError('payout_text')
            if isinstance(self.payout_text,str): object.__setattr__(self,'payout_text',self.payout_text.strip())
            if not isinstance(self.status_text,str) or not self.status_text.strip(): raise ProviderValidationError('status_text')
            object.__setattr__(self,'status_text',self.status_text.strip())
        except ProviderValidationError: raise
        except (TypeError,AttributeError,ValueError) as exc: raise ProviderValidationError('payout record') from exc
@dataclass(frozen=True)
class RawPayoutPublication:
    bet_type:str; finalized_at:datetime|None; entries:Sequence[RawPayoutRecord]; declared_complete:bool; table_complete:bool; capture_succeeded:bool
    def __post_init__(self):
        try:
            from scripts.simulation.repositories.interfaces import validate_bet_type
            validate_bet_type(self.bet_type)
            if self.finalized_at is not None and (not isinstance(self.finalized_at,datetime) or self.finalized_at.tzinfo is None or self.finalized_at.utcoffset() is None): raise ProviderValidationError('finalized_at')
            if not all(isinstance(x,bool) for x in (self.declared_complete,self.table_complete,self.capture_succeeded)): raise ProviderValidationError('complete flags')
            entries=tuple(self.entries)
            if not all(isinstance(x,RawPayoutRecord) for x in entries): raise ProviderValidationError('entries')
            object.__setattr__(self,'entries',entries)
        except ProviderValidationError: raise
        except (TypeError,AttributeError,ValueError) as exc: raise ProviderValidationError('payout publication') from exc
