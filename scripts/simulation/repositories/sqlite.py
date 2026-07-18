"""Connection-injected, fail-closed SQLite repositories."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
import sqlite3
from typing import Callable, TypeVar
from .errors import RepositoryConflictError, RepositoryDataIntegrityError, RepositoryValidationError
from .interfaces import BET_TYPES, OddsSnapshotBatch, OddsSnapshotEntry, PayoutPublication, PayoutRecord, PayoutStatus, PersistedRaceResult, PersistedRaceResultEntry, RaceResultEntryStatus, RaceResultStatus, normalize_orders, selection_key, validate_bet_type
T=TypeVar("T")

def decimal_to_scaled(value:Decimal)->tuple[int,int]:
    if not isinstance(value,Decimal) or not value.is_finite() or value<=0: raise RepositoryValidationError("odds must be a positive finite Decimal")
    scale=max(0,-value.as_tuple().exponent)
    if scale>6: raise RepositoryValidationError("odds supports at most six decimal places")
    return int(value.scaleb(scale)),scale
def scaled_to_decimal(scaled:int,scale:int)->Decimal:
    if not isinstance(scaled,int) or isinstance(scaled,bool) or scaled<=0: raise RepositoryDataIntegrityError("odds_scaled must be positive int")
    if not isinstance(scale,int) or isinstance(scale,bool) or not 0<=scale<=6: raise RepositoryDataIntegrityError("odds_scale must be from zero to six")
    return Decimal(scaled).scaleb(-scale).quantize(Decimal(1).scaleb(-scale))
def _positive(value:object,name:str)->int:
    if not isinstance(value,int) or isinstance(value,bool) or value<=0: raise RepositoryValidationError(f"{name} must be positive int")
    return value
def _utc(value:object,name:str)->str:
    if not isinstance(value,datetime) or value.tzinfo is None or value.utcoffset() is None: raise RepositoryValidationError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()
def _from_utc(value:object,name:str)->datetime:
    try: parsed=datetime.fromisoformat(value)
    except (TypeError,ValueError) as exc: raise RepositoryDataIntegrityError(f"invalid {name}") from exc
    if parsed.tzinfo is None or parsed.utcoffset()!=timezone.utc.utcoffset(parsed) or not value.endswith("+00:00"): raise RepositoryDataIntegrityError(f"{name} must be UTC ISO 8601")
    return parsed
def _complete(value:object)->bool:
    if value not in (0,1) or isinstance(value,bool): raise RepositoryDataIntegrityError("is_complete must be integer 0 or 1")
    return value==1
def _data(call:Callable[[],T])->T:
    try:return call()
    except RepositoryDataIntegrityError: raise
    except (TypeError,ValueError,KeyError) as exc: raise RepositoryDataIntegrityError("stored data violates repository invariants") from exc

class _SQLiteRepository:
    def __init__(self,connection:sqlite3.Connection)->None:
        if not isinstance(connection,sqlite3.Connection): raise TypeError("connection must be sqlite3.Connection")
        self._connection=connection; self._foreign_keys()
    def _foreign_keys(self)->None:
        self._connection.execute("PRAGMA foreign_keys=ON")
        if self._connection.execute("PRAGMA foreign_keys").fetchone()[0]!=1: raise RepositoryDataIntegrityError("foreign_keys could not be enabled")
    def _write(self,action:Callable[[],T])->T:
        if self._connection.in_transaction: raise RepositoryValidationError("repository writes require no active transaction")
        self._foreign_keys(); self._connection.execute("BEGIN IMMEDIATE")
        try: result=action(); self._connection.commit(); return result
        except sqlite3.IntegrityError as exc: self._connection.rollback(); raise RepositoryDataIntegrityError("SQLite integrity constraint failed") from exc
        except Exception: self._connection.rollback(); raise

class SQLiteRaceResultRepository(_SQLiteRepository):
    def save_race_result(self,result:PersistedRaceResult)->None:
        if not isinstance(result,PersistedRaceResult): raise TypeError("result must be PersistedRaceResult")
        def action()->None:
            existing=self.get_race_result(result.race_id)
            if existing is not None:
                if existing==result:return
                raise RepositoryConflictError("race result is insert-only and differs from existing result")
            self._connection.execute("INSERT INTO race_results (race_id,result_status,finalized_at,observed_at,source) VALUES (?,?,?,?,?)",(result.race_id,result.result_status.value,_utc(result.finalized_at,"finalized_at") if result.finalized_at else None,_utc(result.observed_at,"observed_at"),result.source))
            self._connection.executemany("INSERT INTO race_result_entries (race_id,race_entry_id,finish_position,result_status) VALUES (?,?,?,?)",[(result.race_id,e.race_entry_id,e.finish_position,e.result_status.value) for e in result.entries])
        self._write(action)
    def get_race_result(self,race_id:int)->PersistedRaceResult|None:
        _positive(race_id,"race_id"); row=self._connection.execute("SELECT race_id,result_status,finalized_at,observed_at,source FROM race_results WHERE race_id=?",(race_id,)).fetchone()
        if row is None:return None
        def build()->PersistedRaceResult:
            status=RaceResultStatus(row[1]); entries=[]
            for horse_no,eid,finish,entry_status in self._connection.execute("SELECT h.horse_no,e.race_entry_id,e.finish_position,e.result_status FROM race_result_entries e JOIN horses h ON h.id=e.race_entry_id WHERE e.race_id=? ORDER BY e.race_entry_id",(race_id,)):
                entries.append(PersistedRaceResultEntry(horse_no,eid,finish,RaceResultEntryStatus(entry_status)))
            return PersistedRaceResult(row[0],status,_from_utc(row[2],"finalized_at") if row[2] else None,_from_utc(row[3],"observed_at"),row[4],tuple(entries))
        return _data(build)
    def has_complete_race_result(self,race_id:int)->bool:
        _positive(race_id,"race_id"); return self._connection.execute("SELECT 1 FROM race_results WHERE race_id=? AND result_status='complete'",(race_id,)).fetchone() is not None

class SQLiteOddsSnapshotRepository(_SQLiteRepository):
    def save_odds_batch(self,batch:OddsSnapshotBatch)->OddsSnapshotBatch:
        if not isinstance(batch,OddsSnapshotBatch): raise TypeError("batch must be OddsSnapshotBatch")
        def action()->OddsSnapshotBatch:
            row=self._connection.execute("SELECT id FROM odds_snapshot_batches WHERE race_id=? AND bet_type=? AND observed_at=? AND source=?",(batch.race_id,batch.bet_type,_utc(batch.observed_at,"observed_at"),batch.source)).fetchone()
            if row:
                old=self.get_odds_batch(row[0]); same=OddsSnapshotBatch(**{**batch.__dict__,"batch_id":row[0]})
                if old==same:return old
                raise RepositoryConflictError("odds batch differs from existing batch")
            c=self._connection.execute("INSERT INTO odds_snapshot_batches (race_id,bet_type,observed_at,is_complete,source,source_url) VALUES (?,?,?,?,?,?)",(batch.race_id,batch.bet_type,_utc(batch.observed_at,"observed_at"),int(batch.is_complete),batch.source,batch.source_url)); bid=int(c.lastrowid)
            for entry in batch.entries:
                scaled,scale=decimal_to_scaled(entry.odds); c=self._connection.execute("INSERT INTO odds_snapshots (batch_id,bet_type,selection_key,odds_scaled,odds_scale) VALUES (?,?,?,?,?)",(bid,batch.bet_type,selection_key(entry.race_entry_ids,batch.bet_type),scaled,scale)); self._connection.executemany("INSERT INTO odds_snapshot_selections (odds_snapshot_id,race_entry_id,selection_order) VALUES (?,?,?)",[(c.lastrowid,v,i) for i,v in enumerate(entry.race_entry_ids,1)])
            return OddsSnapshotBatch(**{**batch.__dict__,"batch_id":bid})
        return self._write(action)
    def get_odds_batch(self,batch_id:int)->OddsSnapshotBatch|None:
        _positive(batch_id,"batch_id"); header=self._connection.execute("SELECT id,race_id,bet_type,observed_at,is_complete,source,source_url FROM odds_snapshot_batches WHERE id=?",(batch_id,)).fetchone()
        if not header:return None
        def build()->OddsSnapshotBatch:
            validate_bet_type(header[2]); entries=[]
            for oid,kind,key,scaled,scale in self._connection.execute("SELECT id,bet_type,selection_key,odds_scaled,odds_scale FROM odds_snapshots WHERE batch_id=? ORDER BY id",(batch_id,)):
                if kind!=header[2]: raise ValueError("child bet_type mismatch")
                rows=self._connection.execute("SELECT selection_order,race_entry_id FROM odds_snapshot_selections WHERE odds_snapshot_id=?",(oid,)).fetchall()
                entries.append(OddsSnapshotEntry(normalize_orders(rows,kind,key),scaled_to_decimal(scaled,scale)))
            return OddsSnapshotBatch(header[1],header[2],_from_utc(header[3],"observed_at"),_complete(header[4]),header[5],tuple(entries),header[6],header[0])
        return _data(build)
    def get_latest_odds_batch(self,race_id:int,bet_type:str,observed_at_lte:datetime,require_complete:bool=True)->OddsSnapshotBatch|None:
        _positive(race_id,"race_id")
        try: validate_bet_type(bet_type)
        except ValueError as exc: raise RepositoryValidationError(str(exc)) from exc
        if not isinstance(require_complete,bool): raise RepositoryValidationError("require_complete must be bool")
        cutoff=_utc(observed_at_lte,"observed_at_lte"); sql="SELECT id FROM odds_snapshot_batches WHERE race_id=? AND bet_type=? AND observed_at<=?"+(" AND is_complete=1" if require_complete else "")+" ORDER BY observed_at DESC,id DESC LIMIT 1"; row=self._connection.execute(sql,(race_id,bet_type,cutoff)).fetchone(); return self.get_odds_batch(row[0]) if row else None

class SQLitePayoutRepository(_SQLiteRepository):
    def save_payout_publication(self,publication:PayoutPublication)->PayoutPublication:
        if not isinstance(publication,PayoutPublication): raise TypeError("publication must be PayoutPublication")
        def action()->PayoutPublication:
            row=self._connection.execute("SELECT id FROM payout_publications WHERE race_id=? AND bet_type=? AND observed_at=? AND source=?",(publication.race_id,publication.bet_type,_utc(publication.observed_at,"observed_at"),publication.source)).fetchone()
            if row:
                old=self.get_payout_publication(row[0]); same=PayoutPublication(**{**publication.__dict__,"publication_id":row[0]})
                if old==same:return old
                raise RepositoryConflictError("payout publication differs from existing publication")
            c=self._connection.execute("INSERT INTO payout_publications (race_id,bet_type,finalized_at,observed_at,is_complete,source,source_url) VALUES (?,?,?,?,?,?,?)",(publication.race_id,publication.bet_type,_utc(publication.finalized_at,"finalized_at") if publication.finalized_at else None,_utc(publication.observed_at,"observed_at"),int(publication.is_complete),publication.source,publication.source_url)); pid=int(c.lastrowid)
            for entry in publication.entries:
                c=self._connection.execute("INSERT INTO payouts (publication_id,bet_type,selection_key,payout_per_100,payout_status) VALUES (?,?,?,?,?)",(pid,publication.bet_type,selection_key(entry.race_entry_ids,publication.bet_type),entry.payout_per_100,entry.payout_status.value)); self._connection.executemany("INSERT INTO payout_selections (payout_id,race_entry_id,selection_order) VALUES (?,?,?)",[(c.lastrowid,v,i) for i,v in enumerate(entry.race_entry_ids,1)])
            return PayoutPublication(**{**publication.__dict__,"publication_id":pid})
        return self._write(action)
    def get_payout_publication(self,publication_id:int)->PayoutPublication|None:
        _positive(publication_id,"publication_id"); h=self._connection.execute("SELECT id,race_id,bet_type,finalized_at,observed_at,is_complete,source,source_url FROM payout_publications WHERE id=?",(publication_id,)).fetchone()
        if not h:return None
        def build()->PayoutPublication:
            validate_bet_type(h[2]); entries=[]
            for pid,kind,key,money,status in self._connection.execute("SELECT id,bet_type,selection_key,payout_per_100,payout_status FROM payouts WHERE publication_id=? ORDER BY id",(publication_id,)):
                if kind!=h[2]: raise ValueError("child bet_type mismatch")
                rows=self._connection.execute("SELECT selection_order,race_entry_id FROM payout_selections WHERE payout_id=?",(pid,)).fetchall()
                entries.append(PayoutRecord(normalize_orders(rows,kind,key),money,PayoutStatus(status)))
            return PayoutPublication(h[1],h[2],_from_utc(h[3],"finalized_at") if h[3] else None,_from_utc(h[4],"observed_at"),_complete(h[5]),h[6],tuple(entries),h[7],h[0])
        return _data(build)
    def get_latest_payout_publication(self,race_id:int,bet_type:str,observed_at_lte:datetime|None=None,require_complete:bool=True)->PayoutPublication|None:
        _positive(race_id,"race_id")
        try:validate_bet_type(bet_type)
        except ValueError as exc:raise RepositoryValidationError(str(exc)) from exc
        if not isinstance(require_complete,bool):raise RepositoryValidationError("require_complete must be bool")
        terms=["race_id=?","bet_type=?"]; args=[race_id,bet_type]
        if observed_at_lte is not None:terms.append("observed_at<=?");args.append(_utc(observed_at_lte,"observed_at_lte"))
        if require_complete:terms.append("is_complete=1")
        row=self._connection.execute("SELECT id FROM payout_publications WHERE "+" AND ".join(terms)+" ORDER BY observed_at DESC,id DESC LIMIT 1",args).fetchone(); return self.get_payout_publication(row[0]) if row else None
