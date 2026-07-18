from datetime import datetime, timedelta, timezone
from decimal import Decimal
import sqlite3
import unittest

from scripts.migrations.runner import apply_migrations
from scripts.simulation.repositories import (
    OddsSnapshotBatch, OddsSnapshotEntry, PayoutPublication, PayoutRecord,
    RepositoryConflictError, RepositoryDataIntegrityError, RepositoryValidationError,
    SQLiteOddsSnapshotRepository, SQLitePayoutRepository, SQLiteRaceResultRepository,
    decimal_to_scaled, scaled_to_decimal, PayoutStatus, PersistedRaceResult, PersistedRaceResultEntry, RaceResultEntryStatus, RaceResultStatus,
)

UTC = timezone.utc
NOW = datetime(2026, 1, 2, 12, tzinfo=UTC)


class RepositoryTestCase(unittest.TestCase):
    def _corrupt_connection(self, payout: bool, mutate) -> sqlite3.Connection:
        c=sqlite3.connect(":memory:"); c.execute("CREATE TABLE horses (id INTEGER PRIMARY KEY, horse_no INTEGER, race_id INTEGER)"); c.executemany("INSERT INTO horses VALUES (?,?,?)",[(11,1,1),(12,2,1)])
        if payout:
            c.execute("CREATE TABLE payout_publications (id INTEGER PRIMARY KEY,race_id INTEGER,bet_type TEXT,finalized_at TEXT,observed_at TEXT,is_complete INTEGER,source TEXT,source_url TEXT)"); c.execute("CREATE TABLE payouts (id INTEGER PRIMARY KEY,publication_id INTEGER,bet_type TEXT,selection_key TEXT,payout_per_100 INTEGER,payout_status TEXT)"); c.execute("CREATE TABLE payout_selections (payout_id INTEGER,selection_order INTEGER,race_entry_id INTEGER)"); c.execute("INSERT INTO payout_publications VALUES (1,1,'馬連','2026-01-02T12:00:00+00:00','2026-01-02T12:00:00+00:00',1,'s',NULL)"); c.execute("INSERT INTO payouts VALUES (1,1,'馬連','11-12',100,'winning')"); c.executemany("INSERT INTO payout_selections VALUES (1,?,?)",[(1,11),(2,12)])
        else:
            c.execute("CREATE TABLE odds_snapshot_batches (id INTEGER PRIMARY KEY,race_id INTEGER,bet_type TEXT,observed_at TEXT,is_complete INTEGER,source TEXT,source_url TEXT)"); c.execute("CREATE TABLE odds_snapshots (id INTEGER PRIMARY KEY,batch_id INTEGER,bet_type TEXT,selection_key TEXT,odds_scaled INTEGER,odds_scale INTEGER)"); c.execute("CREATE TABLE odds_snapshot_selections (odds_snapshot_id INTEGER,selection_order INTEGER,race_entry_id INTEGER)"); c.execute("INSERT INTO odds_snapshot_batches VALUES (1,1,'馬連','2026-01-02T12:00:00+00:00',1,'s',NULL)"); c.execute("INSERT INTO odds_snapshots VALUES (1,1,'馬連','11-12',200,2)"); c.executemany("INSERT INTO odds_snapshot_selections VALUES (1,?,?)",[(1,11),(2,12)])
        mutate(c); c.commit(); return c
    def setUp(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("CREATE TABLE races (id INTEGER PRIMARY KEY)")
        self.connection.execute("CREATE TABLE horses (id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL, horse_no INTEGER NOT NULL)")
        self.connection.executemany("INSERT INTO races VALUES (?)", [(1,), (2,)])
        self.connection.executemany("INSERT INTO horses VALUES (?,?,?)", [(11,1,1),(12,1,2),(13,1,3),(14,1,4),(21,2,1),(22,2,2),(23,2,3)])
        self.connection.commit()
        apply_migrations(self.connection)

    def tearDown(self) -> None:
        self.connection.close()

    def test_decimal_scaling_preserves_trailing_zeroes_and_rejects_invalid(self) -> None:
        self.assertEqual(decimal_to_scaled(Decimal("1.2300")), (12300, 4))
        self.assertEqual(scaled_to_decimal(12300, 4), Decimal("1.2300"))
        for value in (Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(value=value):
                with self.assertRaises(RepositoryValidationError): decimal_to_scaled(value)
        with self.assertRaises(RepositoryValidationError): decimal_to_scaled(Decimal("1.0000001"))

    def test_race_result_round_trip_complete_and_idempotent(self) -> None:
        repo=SQLiteRaceResultRepository(self.connection)
        result=PersistedRaceResult(1,RaceResultStatus.COMPLETE,NOW,NOW,"official",(PersistedRaceResultEntry(1,11,1,RaceResultEntryStatus.CONFIRMED),PersistedRaceResultEntry(2,12,None,RaceResultEntryStatus.VOID)))
        repo.save_race_result(result)
        self.assertEqual(repo.get_race_result(1),result)
        self.assertTrue(repo.has_complete_race_result(1))
        repo.save_race_result(result)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM race_results").fetchone()[0],1)

    def test_race_result_conflict_and_atomic_rollback(self) -> None:
        repo=SQLiteRaceResultRepository(self.connection)
        original=PersistedRaceResult(1,RaceResultStatus.PARTIAL,None,NOW,"source",(PersistedRaceResultEntry(1,11,1,RaceResultEntryStatus.CONFIRMED),))
        repo.save_race_result(original)
        with self.assertRaises(RepositoryConflictError):
            repo.save_race_result(PersistedRaceResult(1,RaceResultStatus.PARTIAL,None,NOW,"other",(PersistedRaceResultEntry(1,11,1,RaceResultEntryStatus.CONFIRMED),)))
        bad=PersistedRaceResult(2,RaceResultStatus.PARTIAL,None,NOW,"source",(PersistedRaceResultEntry(1,11,1,RaceResultEntryStatus.CONFIRMED),))
        with self.assertRaises(RepositoryDataIntegrityError): repo.save_race_result(bad)
        self.assertIsNone(repo.get_race_result(2))
        self.assertFalse(self.connection.in_transaction)

    def test_race_result_missing_and_active_transaction_rejected(self) -> None:
        repo=SQLiteRaceResultRepository(self.connection)
        self.assertIsNone(repo.get_race_result(99))
        self.connection.execute("BEGIN")
        with self.assertRaises(RepositoryValidationError): repo.save_race_result(PersistedRaceResult(1,RaceResultStatus.PARTIAL,None,NOW,"x",()))
        self.connection.rollback()

    def test_odds_round_trip_latest_filters_and_selection_normalization(self) -> None:
        repo=SQLiteOddsSnapshotRepository(self.connection)
        incomplete=repo.save_odds_batch(OddsSnapshotBatch(1,"馬連",NOW,False,"market",(OddsSnapshotEntry((12,11),Decimal("1.2300")),)))
        complete=repo.save_odds_batch(OddsSnapshotBatch(1,"馬連",NOW+timedelta(seconds=1),True,"market",(OddsSnapshotEntry((11,12),Decimal("2.00")),)))
        self.assertEqual(repo.get_odds_batch(incomplete.batch_id).entries[0].race_entry_ids,(11,12))
        self.assertEqual(repo.get_odds_batch(incomplete.batch_id).entries[0].odds,Decimal("1.2300"))
        self.assertEqual(repo.get_latest_odds_batch(1,"馬連",NOW+timedelta(days=1)),complete)
        self.assertIsNone(repo.get_latest_odds_batch(1,"馬連",NOW))

    def test_odds_invalid_input_conflict_rollback_and_foreign_keys(self) -> None:
        repo=SQLiteOddsSnapshotRepository(self.connection)
        with self.assertRaises(ValueError): OddsSnapshotBatch(1,"単勝",NOW,True,"m",(OddsSnapshotEntry((11,12),Decimal("2")),))
        bad=OddsSnapshotBatch(2,"単勝",NOW,True,"m",(OddsSnapshotEntry((11,),Decimal("2")),))
        with self.assertRaises(RepositoryDataIntegrityError):repo.save_odds_batch(bad)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM odds_snapshot_batches").fetchone()[0],0)
        saved=repo.save_odds_batch(OddsSnapshotBatch(1,"単勝",NOW,True,"m",(OddsSnapshotEntry((11,),Decimal("2")),)))
        self.assertEqual(repo.save_odds_batch(saved),saved)
        with self.assertRaises(RepositoryConflictError):
            repo.save_odds_batch(OddsSnapshotBatch(1,"単勝",NOW,True,"m",(OddsSnapshotEntry((11,),Decimal("3")),)))
        self.assertFalse(self.connection.in_transaction)

    def test_payout_round_trip_all_statuses_and_latest_filters(self) -> None:
        repo=SQLitePayoutRepository(self.connection)
        publication=PayoutPublication(1,"単勝",NOW,NOW,True,"official",(
            PayoutRecord((11,),200,PayoutStatus.WINNING),PayoutRecord((12,),0,PayoutStatus.REFUND),PayoutRecord((13,),0,PayoutStatus.VOID),
        ))
        saved=repo.save_payout_publication(publication)
        self.assertEqual(repo.get_payout_publication(saved.publication_id),saved)
        self.assertEqual(repo.save_payout_publication(saved),saved)
        self.assertEqual(repo.get_latest_payout_publication(1,"単勝"),saved)
        self.assertIsNone(repo.get_latest_payout_publication(1,"単勝",NOW-timedelta(seconds=1)))

    def test_payout_atomic_rollback_and_invalid_selection(self) -> None:
        repo=SQLitePayoutRepository(self.connection)
        bad=PayoutPublication(2,"単勝",NOW,NOW,True,"official",(PayoutRecord((11,),100,PayoutStatus.WINNING),))
        with self.assertRaises(RepositoryDataIntegrityError):repo.save_payout_publication(bad)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM payout_publications").fetchone()[0],0)
        with self.assertRaises(ValueError): PayoutRecord((11,),0,PayoutStatus.WINNING)
        self.assertFalse(self.connection.in_transaction)

    def test_repository_does_not_apply_migrations_or_open_global_database(self) -> None:
        connection=sqlite3.connect(":memory:")
        try:
            repo=SQLiteRaceResultRepository(connection)
            with self.assertRaises(sqlite3.OperationalError): repo.get_race_result(1)
        finally:
            connection.close()

    def test_race_all_header_statuses_round_trip(self) -> None:
        repo=SQLiteRaceResultRepository(self.connection)
        for index,status in enumerate(RaceResultStatus, 1):
            result=PersistedRaceResult(index,status,NOW if status is RaceResultStatus.COMPLETE else None,NOW,"s",())
            if index > 2: self.connection.execute("INSERT OR IGNORE INTO races VALUES (?)",(index,)); self.connection.commit()
            repo.save_race_result(result); self.assertEqual(repo.get_race_result(index).result_status,status)

    def test_race_normalizes_entry_order(self) -> None:
        repo=SQLiteRaceResultRepository(self.connection)
        value=PersistedRaceResult(1,RaceResultStatus.PARTIAL,None,NOW,"s",(PersistedRaceResultEntry(2,12,2,RaceResultEntryStatus.CONFIRMED),PersistedRaceResultEntry(1,11,1,RaceResultEntryStatus.CONFIRMED)))
        repo.save_race_result(value); self.assertEqual(repo.get_race_result(1).entries,(PersistedRaceResultEntry(1,11,1,RaceResultEntryStatus.CONFIRMED),PersistedRaceResultEntry(2,12,2,RaceResultEntryStatus.CONFIRMED)))

    def test_race_old_and_new_different_observed_at_conflict(self) -> None:
        repo=SQLiteRaceResultRepository(self.connection); repo.save_race_result(PersistedRaceResult(1,RaceResultStatus.PARTIAL,None,NOW,"s",()))
        for when in (NOW-timedelta(seconds=1),NOW+timedelta(seconds=1)):
            with self.subTest(when=when):
                with self.assertRaises(RepositoryConflictError): repo.save_race_result(PersistedRaceResult(1,RaceResultStatus.PARTIAL,None,when,"s",()))

    def test_write_reenables_foreign_keys(self) -> None:
        repo=SQLiteOddsSnapshotRepository(self.connection); self.connection.execute("PRAGMA foreign_keys=OFF")
        repo.save_odds_batch(OddsSnapshotBatch(1,"単勝",NOW,True,"s",(OddsSnapshotEntry((11,),Decimal("2")),)))
        self.assertEqual(self.connection.execute("PRAGMA foreign_keys").fetchone()[0],1)

    def test_odds_all_bet_types_round_trip(self) -> None:
        repo=SQLiteOddsSnapshotRepository(self.connection)
        for index,(kind,ids) in enumerate((("単勝",(11,)),("馬連",(11,12)),("ワイド",(11,12)),("3連複",(11,12,13))),1):
            saved=repo.save_odds_batch(OddsSnapshotBatch(1,kind,NOW+timedelta(seconds=index),True,"s",(OddsSnapshotEntry(ids,Decimal("2")),)))
            self.assertEqual(repo.get_odds_batch(saved.batch_id).entries[0].race_entry_ids,ids)

    def test_odds_incomplete_available_only_when_requested(self) -> None:
        repo=SQLiteOddsSnapshotRepository(self.connection); saved=repo.save_odds_batch(OddsSnapshotBatch(1,"単勝",NOW,False,"s",(OddsSnapshotEntry((11,),Decimal("2")),)))
        self.assertIsNone(repo.get_latest_odds_batch(1,"単勝",NOW,True)); self.assertEqual(repo.get_latest_odds_batch(1,"単勝",NOW,False),saved)

    def test_odds_invalid_get_arguments_rejected(self) -> None:
        repo=SQLiteOddsSnapshotRepository(self.connection)
        for value in (True,0,"1"):
            with self.subTest(value=value):
                with self.assertRaises(RepositoryValidationError): repo.get_odds_batch(value)

    def test_payout_all_statuses_round_trip(self) -> None:
        repo=SQLitePayoutRepository(self.connection); saved=repo.save_payout_publication(PayoutPublication(1,"単勝",NOW,NOW,True,"s",(PayoutRecord((11,),1,PayoutStatus.WINNING),PayoutRecord((12,),0,PayoutStatus.REFUND),PayoutRecord((13,),0,PayoutStatus.VOID))))
        self.assertEqual([item.payout_status for item in repo.get_payout_publication(saved.publication_id).entries],[PayoutStatus.WINNING,PayoutStatus.REFUND,PayoutStatus.VOID])

    def test_payout_incomplete_available_only_when_requested(self) -> None:
        repo=SQLitePayoutRepository(self.connection); saved=repo.save_payout_publication(PayoutPublication(1,"単勝",None,NOW,False,"s",()))
        self.assertIsNone(repo.get_latest_payout_publication(1,"単勝")); self.assertEqual(repo.get_latest_payout_publication(1,"単勝",require_complete=False),saved)

    def test_payout_normalizes_entry_order(self) -> None:
        repo=SQLitePayoutRepository(self.connection); saved=repo.save_payout_publication(PayoutPublication(1,"馬連",NOW,NOW,True,"s",(PayoutRecord((12,11),100,PayoutStatus.WINNING),)))
        self.assertEqual(repo.get_payout_publication(saved.publication_id).entries[0].race_entry_ids,(11,12))

    def test_float_odds_is_rejected(self) -> None:
        with self.assertRaises(RepositoryValidationError): decimal_to_scaled(1.2)  # type: ignore[arg-type]

    def test_scaled_bool_values_are_rejected(self) -> None:
        for args in ((True,1),(1,True)):
            with self.subTest(args=args):
                with self.assertRaises(RepositoryDataIntegrityError): scaled_to_decimal(*args)

    def test_decimal_scientific_notation(self) -> None:
        self.assertEqual(decimal_to_scaled(Decimal("1E+2")),(100,0))

    def test_active_transaction_rejects_odds_and_payout(self) -> None:
        for repo,value,method in ((SQLiteOddsSnapshotRepository(self.connection),OddsSnapshotBatch(1,"単勝",NOW,True,"s",(OddsSnapshotEntry((11,),Decimal("2")),)),"save_odds_batch"),(SQLitePayoutRepository(self.connection),PayoutPublication(1,"単勝",NOW,NOW,True,"s",()),"save_payout_publication")):
            self.connection.execute("BEGIN")
            with self.assertRaises(RepositoryValidationError): getattr(repo,method)(value)
            self.connection.rollback()

    def test_unknown_bet_type_is_rejected_by_lookup(self) -> None:
        with self.assertRaises(RepositoryValidationError):
            SQLiteOddsSnapshotRepository(self.connection).get_latest_odds_batch(1,"未知",NOW)

    def test_payout_not_found_returns_none(self) -> None:
        self.assertIsNone(SQLitePayoutRepository(self.connection).get_payout_publication(999))

    def test_corrupt_race_header_status_is_rejected(self) -> None:
        repo=SQLiteRaceResultRepository(self.connection); repo.save_race_result(PersistedRaceResult(1,RaceResultStatus.PARTIAL,None,NOW,"s",()))
        self.connection.execute("PRAGMA ignore_check_constraints=ON"); self.connection.execute("UPDATE race_results SET result_status='bad' WHERE race_id=1"); self.connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError): repo.get_race_result(1)

    def test_corrupt_odds_scale_and_selection_key_are_rejected(self) -> None:
        repo=SQLiteOddsSnapshotRepository(self.connection); saved=repo.save_odds_batch(OddsSnapshotBatch(1,"単勝",NOW,True,"s",(OddsSnapshotEntry((11,),Decimal("2")),)))
        self.connection.execute("PRAGMA ignore_check_constraints=ON"); self.connection.execute("UPDATE odds_snapshots SET odds_scale=7 WHERE batch_id=?",(saved.batch_id,)); self.connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError): repo.get_odds_batch(saved.batch_id)

    def test_corrupt_race_entry_status_is_rejected(self) -> None:
        repo=SQLiteRaceResultRepository(self.connection); repo.save_race_result(PersistedRaceResult(1,RaceResultStatus.PARTIAL,None,NOW,"s",(PersistedRaceResultEntry(1,11,1,RaceResultEntryStatus.CONFIRMED),)))
        self.connection.execute("PRAGMA ignore_check_constraints=ON"); self.connection.execute("UPDATE race_result_entries SET result_status='bad' WHERE race_id=1"); self.connection.commit()
        with self.assertRaises(RepositoryDataIntegrityError): repo.get_race_result(1)

    def test_finalized_after_observed_is_rejected(self) -> None:
        with self.assertRaises(ValueError): PersistedRaceResult(1,RaceResultStatus.COMPLETE,NOW+timedelta(seconds=1),NOW,"s",())

    def test_odds_not_found_and_latest_cutoff(self) -> None:
        repo=SQLiteOddsSnapshotRepository(self.connection); first=repo.save_odds_batch(OddsSnapshotBatch(1,"単勝",NOW,True,"a",(OddsSnapshotEntry((11,),Decimal("2")),))); second=repo.save_odds_batch(OddsSnapshotBatch(1,"単勝",NOW+timedelta(seconds=2),True,"b",(OddsSnapshotEntry((11,),Decimal("3")),)))
        self.assertIsNone(repo.get_odds_batch(999)); self.assertEqual(repo.get_latest_odds_batch(1,"単勝",NOW+timedelta(seconds=1)),first); self.assertEqual(repo.get_latest_odds_batch(1,"単勝",NOW+timedelta(days=1)),second)

    def test_odds_same_time_id_desc(self) -> None:
        repo=SQLiteOddsSnapshotRepository(self.connection); repo.save_odds_batch(OddsSnapshotBatch(1,"単勝",NOW,True,"a",(OddsSnapshotEntry((11,),Decimal("2")),))); last=repo.save_odds_batch(OddsSnapshotBatch(1,"単勝",NOW,True,"b",(OddsSnapshotEntry((11,),Decimal("3")),)))
        self.assertEqual(repo.get_latest_odds_batch(1,"単勝",NOW),last)

    def test_payout_same_time_id_desc_and_no_synthetic_loss(self) -> None:
        repo=SQLitePayoutRepository(self.connection); repo.save_payout_publication(PayoutPublication(1,"単勝",NOW,NOW,True,"a",())); last=repo.save_payout_publication(PayoutPublication(1,"単勝",NOW,NOW,True,"b",()))
        self.assertEqual(repo.get_latest_payout_publication(1,"単勝"),last); self.assertEqual(last.entries,())

    def test_invalid_repository_lookup_arguments(self) -> None:
        odds=SQLiteOddsSnapshotRepository(self.connection); payout=SQLitePayoutRepository(self.connection)
        for value in (0,-1,True,"1"):
            with self.subTest(value=value):
                with self.assertRaises(RepositoryValidationError): odds.get_odds_batch(value)
                with self.assertRaises(RepositoryValidationError): payout.get_payout_publication(value)
        for value in (0,1,None,"yes"):
            with self.subTest(value=value):
                with self.assertRaises(RepositoryValidationError): odds.get_latest_odds_batch(1,"単勝",NOW,value)

    def test_naive_cutoff_rejected(self) -> None:
        with self.assertRaises(RepositoryValidationError): SQLiteOddsSnapshotRepository(self.connection).get_latest_odds_batch(1,"単勝",datetime(2026,1,1))

    def test_publication_id_validation(self) -> None:
        for value in (0,-1,True,"1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError): PayoutPublication(1,"単勝",NOW,NOW,True,"s",(),publication_id=value)

    def test_odds_entry_order_idempotent_and_recovery(self) -> None:
        repo=SQLiteOddsSnapshotRepository(self.connection)
        first=OddsSnapshotBatch(1,"馬連",NOW,True,"s",(OddsSnapshotEntry((11,12),Decimal("2")),))
        saved=repo.save_odds_batch(first); self.assertEqual(repo.save_odds_batch(OddsSnapshotBatch(1,"馬連",NOW,True,"s",tuple(reversed(first.entries)))),saved)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM odds_snapshot_batches").fetchone()[0],1)
        with self.assertRaises(RepositoryDataIntegrityError): repo.save_odds_batch(OddsSnapshotBatch(2,"単勝",NOW,True,"bad",(OddsSnapshotEntry((11,),Decimal("2")),)))
        self.assertFalse(self.connection.in_transaction); ok=repo.save_odds_batch(OddsSnapshotBatch(1,"単勝",NOW+timedelta(seconds=1),True,"ok",(OddsSnapshotEntry((11,),Decimal("2")),))); self.assertEqual(repo.get_odds_batch(ok.batch_id),ok)

    def test_payout_entry_order_idempotent_recovery_and_all_statuses(self) -> None:
        repo=SQLitePayoutRepository(self.connection); entries=(PayoutRecord((11,),100,PayoutStatus.WINNING),PayoutRecord((12,),0,PayoutStatus.REFUND),PayoutRecord((13,),0,PayoutStatus.VOID),PayoutRecord((14,),0,PayoutStatus.UNSUPPORTED))
        saved=repo.save_payout_publication(PayoutPublication(1,"単勝",NOW,NOW,True,"s",entries)); self.assertEqual(repo.save_payout_publication(PayoutPublication(1,"単勝",NOW,NOW,True,"s",tuple(reversed(entries)))),saved)
        self.assertEqual(self.connection.execute("SELECT COUNT(*) FROM payout_publications").fetchone()[0],1); self.assertFalse(self.connection.in_transaction)
        loaded=repo.get_payout_publication(saved.publication_id); self.assertEqual({item.payout_status for item in loaded.entries},{PayoutStatus.WINNING,PayoutStatus.REFUND,PayoutStatus.VOID,PayoutStatus.UNSUPPORTED}); self.assertTrue(all(isinstance(item.payout_status,PayoutStatus) for item in loaded.entries))

    def test_payout_failure_rolls_back_and_connection_recovers(self) -> None:
        repo=SQLitePayoutRepository(self.connection); bad=PayoutPublication(2,"単勝",NOW,NOW,True,"bad",(PayoutRecord((11,),100,PayoutStatus.WINNING),))
        with self.assertRaises(RepositoryDataIntegrityError): repo.save_payout_publication(bad)
        self.assertFalse(self.connection.in_transaction)
        for table in ("payout_publications","payouts","payout_selections"): self.assertEqual(self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0],0)
        good=repo.save_payout_publication(PayoutPublication(1,"単勝",NOW,NOW,True,"good",(PayoutRecord((11,),100,PayoutStatus.WINNING),))); self.assertEqual(repo.get_payout_publication(good.publication_id),good)

    def test_repositories_preserve_caller_transaction(self) -> None:
        cases=((SQLiteRaceResultRepository(self.connection),"save_race_result",PersistedRaceResult(1,RaceResultStatus.PARTIAL,None,NOW,"s",())),(SQLiteOddsSnapshotRepository(self.connection),"save_odds_batch",OddsSnapshotBatch(1,"単勝",NOW,True,"s",(OddsSnapshotEntry((11,),Decimal("2")),))),(SQLitePayoutRepository(self.connection),"save_payout_publication",PayoutPublication(1,"単勝",NOW,NOW,True,"s",())))
        for repo,method,value in cases:
            self.connection.execute("BEGIN"); self.connection.execute("INSERT INTO races VALUES (99)")
            with self.assertRaises(RepositoryValidationError): getattr(repo,method)(value)
            self.assertTrue(self.connection.in_transaction); self.assertIsNotNone(self.connection.execute("SELECT 1 FROM races WHERE id=99").fetchone()); self.connection.rollback(); self.assertIsNone(self.connection.execute("SELECT 1 FROM races WHERE id=99").fetchone())

    def test_corrupt_odds_rows_are_rejected(self) -> None:
        cases={"order":("UPDATE odds_snapshot_selections SET selection_order=3 WHERE race_entry_id=12",),"key":("UPDATE odds_snapshots SET selection_key='11-13'",),"type":("UPDATE odds_snapshots SET bet_type='単勝'",),"complete":("UPDATE odds_snapshot_batches SET is_complete=2",),"naive":("UPDATE odds_snapshot_batches SET observed_at='2026-01-02T12:00:00'",),"jst":("UPDATE odds_snapshot_batches SET observed_at='2026-01-02T21:00:00+09:00'",),"scale_neg":("UPDATE odds_snapshots SET odds_scale=-1",),"scale_high":("UPDATE odds_snapshots SET odds_scale=7",)}
        for name,(sql,) in cases.items():
            with self.subTest(name=name):
                c=self._corrupt_connection(False,lambda db,q=sql:db.execute(q))
                try:
                    with self.assertRaises(RepositoryDataIntegrityError): SQLiteOddsSnapshotRepository(c).get_odds_batch(1)
                finally:c.close()

    def test_corrupt_payout_rows_are_rejected(self) -> None:
        cases={"order":"UPDATE payout_selections SET selection_order=3 WHERE race_entry_id=12","key":"UPDATE payouts SET selection_key='11-13'","type":"UPDATE payouts SET bet_type='単勝'","status":"UPDATE payouts SET payout_status='unknown'","complete":"UPDATE payout_publications SET is_complete=2","naive":"UPDATE payout_publications SET observed_at='2026-01-02T12:00:00'","jst":"UPDATE payout_publications SET observed_at='2026-01-02T21:00:00+09:00'","finalized":"UPDATE payout_publications SET finalized_at='2026-01-02T12:00:00'"}
        for name,sql in cases.items():
            with self.subTest(name=name):
                c=self._corrupt_connection(True,lambda db,q=sql:db.execute(q))
                try:
                    with self.assertRaises(RepositoryDataIntegrityError): SQLitePayoutRepository(c).get_payout_publication(1)
                finally:c.close()



if __name__ == "__main__":
    unittest.main()
