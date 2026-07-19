from decimal import Decimal, InvalidOperation
from scripts.simulation.repositories.interfaces import PayoutStatus, RaceResultStatus, RaceResultEntryStatus, normalize_selection
from .errors import ProviderValidationError
def parse_positive_int(v,name='value'):
    if not isinstance(name,str) or not name.strip() or isinstance(v,(bool,float,Decimal)): raise ProviderValidationError('name or value')
    text=v.strip() if isinstance(v,str) else v
    try: n=int(text) if isinstance(text,str) and text.isdigit() else v
    except (TypeError,ValueError) as e: raise ProviderValidationError(name) from e
    if not isinstance(n,int) or n<=0 or (isinstance(v,str) and (not text or not text.isascii() or not text.isdigit())): raise ProviderValidationError(name)
    return n
def parse_finish_position(v):
    if v is None or (isinstance(v,str) and v.strip() in ('','-','取消','除外','中止','競走中止')): return None
    return parse_positive_int(v,'finish_position')
def parse_decimal_odds(v):
    if isinstance(v,(float,bool)) or not isinstance(v,(str,Decimal)) or (isinstance(v,str) and v.strip() in ('','-','発売なし','取消')): raise ProviderValidationError('odds')
    try: d=Decimal(v)
    except (InvalidOperation,ValueError) as e: raise ProviderValidationError('odds') from e
    if not d.is_finite() or d<=0 or (isinstance(v,str) and ('E' in v.upper() or ',' in v)) or max(0,-d.as_tuple().exponent)>6: raise ProviderValidationError('odds')
    return d
def parse_payout_per_100(v):
    if isinstance(v,(bool,float)) or not isinstance(v,(str,int)): raise ProviderValidationError('payout')
    text=str(v).strip();
    if text[:1] in ('¥','￥'): text=text[1:]
    import re
    if not re.fullmatch(r'(?:\d+|\d{1,3}(?:,\d{3})+)',text): raise ProviderValidationError('payout')
    text=text.replace(',','')
    return int(text)
def _enum(v,cls,m):
    if isinstance(v,cls): return v
    if not isinstance(v,str): raise ProviderValidationError('status')
    try:return cls[m[v.strip().lower()]]
    except KeyError as e: raise ProviderValidationError('status') from e
def normalize_result_status(v): return _enum(v,RaceResultStatus,{'complete':'COMPLETE','partial':'PARTIAL','void':'VOID','unsupported':'UNSUPPORTED','確定':'COMPLETE','完了':'COMPLETE','一部':'PARTIAL','未確定':'PARTIAL','中止':'VOID','不成立':'VOID','対応外':'UNSUPPORTED'})
def normalize_result_entry_status(v): return _enum(v,RaceResultEntryStatus,{'confirmed':'CONFIRMED','確定':'CONFIRMED','void':'VOID','取消':'VOID','除外':'VOID','中止':'VOID','unsupported':'UNSUPPORTED','対応外':'UNSUPPORTED'})
def normalize_payout_status(v): return _enum(v,PayoutStatus,{'winning':'WINNING','refund':'REFUND','void':'VOID','unsupported':'UNSUPPORTED','払戻':'WINNING','返還':'REFUND','取消':'VOID','中止':'VOID','不成立':'VOID','対応外':'UNSUPPORTED'})
def resolve_selection(race_entry_ids,horse_numbers,bet_type,universe):
    from .models import RaceEntryUniverse
    try:
        if not isinstance(universe,RaceEntryUniverse): raise ProviderValidationError('universe')
        if (race_entry_ids is None)==(horse_numbers is None): raise ProviderValidationError('one selection source required')
        source=tuple(race_entry_ids) if race_entry_ids is not None else tuple(horse_numbers)
        if not source: raise ProviderValidationError('empty selection')
        if any(not isinstance(x,int) or isinstance(x,bool) or x<=0 for x in source): raise ProviderValidationError('selection id')
        if len(source)!=len(set(source)): raise ProviderValidationError('duplicate selection')
        values=source if race_entry_ids is not None else tuple(universe.horse_no_to_race_entry_id[x] for x in source)
        if any(x not in universe.active_race_entry_ids for x in values): raise ProviderValidationError('inactive or unknown selection')
        return normalize_selection(values,bet_type)
    except ProviderValidationError: raise
    except (ValueError,TypeError,KeyError,AttributeError) as exc: raise ProviderValidationError('selection') from exc
