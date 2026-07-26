"""Ver0.8 migration runner/schema regression tests (:memory: only)."""
import sqlite3
import unittest
from decimal import Decimal
from types import SimpleNamespace
from scripts.migrations.runner import apply_migrations, get_applied_versions, get_pending_migrations

UTC="2026-01-01T00:00:00+00:00"
class MigrationTests(unittest.TestCase):
    def db(self):
        c=sqlite3.connect(":memory:"); c.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)"); c.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY,race_id INTEGER)"); c.executemany("INSERT INTO races VALUES(?)",[(1,),(2,)]); c.executemany("INSERT INTO horses VALUES(?,?)",[(1,1),(2,2)]); c.commit(); return c
    def migrated(self): c=self.db(); apply_migrations(c); return c
    def batch(self,c,race=1,bet="単勝"):
        c.execute("INSERT INTO odds_snapshot_batches(race_id,bet_type,observed_at,is_complete,source) VALUES(?,?,?,?,?)",(race,bet,UTC,1,'s')); return c.execute("SELECT last_insert_rowid()").fetchone()[0]
    def snap(self,c,batch,bet="単勝"):
        c.execute("INSERT INTO odds_snapshots(batch_id,bet_type,selection_key,odds_scaled,odds_scale) VALUES(?,?,?,?,?)",(batch,bet,'a',12300,4)); return c.execute("SELECT last_insert_rowid()").fetchone()[0]
    def pub(self,c,race=1,bet="単勝"):
        c.execute("INSERT INTO payout_publications(race_id,bet_type,finalized_at,observed_at,is_complete,source) VALUES(?,?,?,?,?,?)",(race,bet,UTC,UTC,1,'s')); return c.execute("SELECT last_insert_rowid()").fetchone()[0]
    def payout(self,c,pub,bet="単勝"):
        c.execute("INSERT INTO payouts(publication_id,bet_type,selection_key,payout_per_100,payout_status) VALUES(?,?,?,?,?)",(pub,bet,'a',100,'winning')); return c.execute("SELECT last_insert_rowid()").fetchone()[0]
    def test_getter_has_no_side_effect(self):
        c=self.db(); self.assertEqual(get_applied_versions(c),{}); self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='schema_migrations'").fetchone())
    def test_apply_idempotent_and_utc_history(self):
        c=self.migrated(); apply_migrations(c); self.assertEqual(get_applied_versions(c),{8:'v008_simulation_schema',9:'v009_simulation_bet_plan_schema'}); self.assertTrue(c.execute("SELECT applied_at FROM schema_migrations").fetchone()[0].endswith('+00:00'))
    def test_foreign_keys_and_active_transaction_rejected(self):
        c=self.db(); c.execute('BEGIN');
        with self.assertRaises(RuntimeError): apply_migrations(c)
        c.rollback(); apply_migrations(c); self.assertEqual(c.execute('PRAGMA foreign_keys').fetchone()[0],1)
    def test_registry_invalid(self):
        good=SimpleNamespace(VERSION=1,NAME='x',apply=lambda c:None)
        c=self.db()
        with self.assertRaises(ValueError): get_pending_migrations(c,(good,SimpleNamespace(VERSION=1,NAME='y',apply=lambda c:None)))
        self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='schema_migrations'").fetchone()); self.assertFalse(c.in_transaction)
    def test_registry_invalid_entries_do_not_touch_database(self):
        cases=[SimpleNamespace(NAME='x',apply=lambda c:None),SimpleNamespace(VERSION=0,NAME='x',apply=lambda c:None),SimpleNamespace(VERSION=-1,NAME='x',apply=lambda c:None),SimpleNamespace(VERSION=True,NAME='x',apply=lambda c:None),SimpleNamespace(VERSION='8',NAME='x',apply=lambda c:None),SimpleNamespace(VERSION=1,apply=lambda c:None),SimpleNamespace(VERSION=1,NAME='',apply=lambda c:None),SimpleNamespace(VERSION=1,NAME=' ',apply=lambda c:None),SimpleNamespace(VERSION=1,NAME='x'),SimpleNamespace(VERSION=1,NAME='x',apply=1)]
        for bad in cases:
            with self.subTest(bad=bad):
                c=self.db()
                with self.assertRaises(ValueError): apply_migrations(c,(bad,))
                self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='schema_migrations'").fetchone()); self.assertFalse(c.in_transaction)
    def test_unknown_version_rejected(self):
        c=self.db(); c.execute("CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY,name TEXT,applied_at TEXT)"); c.execute("INSERT INTO schema_migrations VALUES(99,'x',?)",(UTC,)); c.commit()
        with self.assertRaises(RuntimeError): get_pending_migrations(c)
    def test_rollback_migration(self):
        c=self.db(); bad=SimpleNamespace(VERSION=1,NAME='bad',apply=lambda x:(x.execute('CREATE TABLE rolled(x)'),x.execute('INVALID SQL')))
        with self.assertRaises(sqlite3.OperationalError): apply_migrations(c,(bad,))
        self.assertIsNone(c.execute("SELECT 1 FROM sqlite_master WHERE name='rolled'").fetchone()); self.assertNotIn(1,get_applied_versions(c)); self.assertFalse(c.in_transaction); c.execute('CREATE TABLE recovery_check(id INTEGER)'); self.assertTrue(c.execute("SELECT 1 FROM sqlite_master WHERE name='recovery_check'").fetchone())
    def test_race_result_checks(self):
        c=self.migrated()
        for sql in ["INSERT INTO race_results VALUES(1,'complete',NULL,'"+UTC+"','s',NULL)","INSERT INTO race_results VALUES(1,'complete','2027-01-01T00:00:00+00:00','"+UTC+"','s',NULL)","INSERT INTO race_results VALUES(1,'bad','"+UTC+"','"+UTC+"','s',NULL)"]:
            with self.assertRaises(sqlite3.IntegrityError): c.execute(sql)
    def test_result_entry_insert_update_and_duplicate(self):
        c=self.migrated(); c.execute("INSERT INTO race_result_entries VALUES(1,1,1,'confirmed')")
        with self.assertRaises(sqlite3.IntegrityError): c.execute("UPDATE race_result_entries SET race_entry_id=2")
        with self.assertRaises(sqlite3.IntegrityError): c.execute("INSERT INTO race_result_entries VALUES(1,1,2,'confirmed')")
    def test_odds_constraints_and_precision(self):
        c=self.migrated(); b=self.batch(c); s=self.snap(c,b); a=c.execute('SELECT odds_scaled,odds_scale FROM odds_snapshots').fetchone(); self.assertEqual(Decimal(a[0]).scaleb(-a[1]),Decimal('1.2300'))
        for vals in [(0,4),(1,-1),(1,7)]:
            with self.assertRaises(sqlite3.IntegrityError): c.execute("INSERT INTO odds_snapshots(batch_id,bet_type,selection_key,odds_scaled,odds_scale) VALUES(?,?,?,?,?)",(b,'単勝',str(vals),*vals))
    def test_odds_type_and_selection_triggers(self):
        c=self.migrated(); b=self.batch(c); s=self.snap(c,b)
        with self.assertRaises(sqlite3.IntegrityError): c.execute("UPDATE odds_snapshots SET bet_type='馬連'")
        with self.assertRaises(sqlite3.IntegrityError): c.execute("INSERT INTO odds_snapshot_selections VALUES(?,?,?)",(s,2,1))
    def test_odds_type_insert_trigger(self):
        c=self.migrated(); b=self.batch(c)
        with self.assertRaises(sqlite3.IntegrityError): c.execute("INSERT INTO odds_snapshots(batch_id,bet_type,selection_key,odds_scaled,odds_scale) VALUES(?,?,?,?,?)",(b,'馬連','bad',100,2))
        self.assertEqual(c.execute("SELECT count(*) FROM odds_snapshots WHERE selection_key='bad'").fetchone()[0],0)
    def test_payout_constraints_and_selection_trigger(self):
        c=self.migrated(); p=self.pub(c); pay=self.payout(c,p)
        with self.assertRaises(sqlite3.IntegrityError): c.execute("INSERT INTO payouts(publication_id,bet_type,selection_key,payout_per_100,payout_status) VALUES(?,?,?,?,?)",(p,'単勝','z',0,'winning'))
        with self.assertRaises(sqlite3.IntegrityError): c.execute("INSERT INTO payout_selections VALUES(?,?,?)",(pay,2,1))
    def test_payout_type_insert_trigger(self):
        c=self.migrated(); p=self.pub(c)
        with self.assertRaises(sqlite3.IntegrityError): c.execute("INSERT INTO payouts(publication_id,bet_type,selection_key,payout_per_100,payout_status) VALUES(?,?,?,?,?)",(p,'馬連','bad',100,'winning'))
        self.assertEqual(c.execute("SELECT count(*) FROM payouts WHERE selection_key='bad'").fetchone()[0],0)

    def test_schema_objects_exist(self):
        c=self.migrated(); names={x[0] for x in c.execute("SELECT name FROM sqlite_master")}
        self.assertTrue({'race_results','race_result_entries','odds_snapshot_batches','odds_snapshots','odds_snapshot_selections','payout_publications','payouts','payout_selections','simulation_bet_plans','simulation_bet_plan_bets','simulation_bet_plan_bet_selections','rre_entry_race_insert','rre_entry_race_update','odds_snapshot_batch_race_update','payout_publication_race_update','sbpbs_entry_race_insert','sbpbs_entry_race_update','sbpb_plan_race_update'} <= names)
    def test_expected_trigger_set(self):
        c=self.migrated(); actual={row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        expected={'rre_entry_race_insert','rre_entry_race_update','oss_entry_race_insert','oss_entry_race_update','ps_entry_race_insert','ps_entry_race_update','odds_type_insert','odds_type_update','payout_type_insert','payout_type_update','odds_snapshot_batch_race_update','payout_publication_race_update','sbpbs_entry_race_insert','sbpbs_entry_race_update','sbpb_plan_race_update'}
        self.assertEqual(actual,expected)
    def test_all_update_triggers_preserve_rows(self):
        c=self.migrated(); b1=self.batch(c); s=self.snap(c,b1); c.execute("INSERT INTO odds_snapshot_selections VALUES(?,?,?)",(s,1,1)); b2=self.batch(c,2)
        with self.assertRaises(sqlite3.IntegrityError): c.execute("UPDATE odds_snapshots SET batch_id=? WHERE id=?",(b2,s))
        self.assertEqual(c.execute("SELECT batch_id FROM odds_snapshots WHERE id=?",(s,)).fetchone()[0],b1)
        p1=self.pub(c); pay=self.payout(c,p1); c.execute("INSERT INTO payout_selections VALUES(?,?,?)",(pay,1,1)); p2=self.pub(c,2)
        with self.assertRaises(sqlite3.IntegrityError): c.execute("UPDATE payouts SET publication_id=? WHERE id=?",(p2,pay))
        self.assertEqual(c.execute("SELECT publication_id FROM payouts WHERE id=?",(pay,)).fetchone()[0],p1)
    def test_result_entry_update_triggers(self):
        c=self.migrated(); c.execute("INSERT INTO race_result_entries VALUES(1,1,1,'confirmed')")
        for sql in ("UPDATE race_result_entries SET race_id=2","UPDATE race_result_entries SET race_entry_id=2"):
            with self.assertRaises(sqlite3.IntegrityError): c.execute(sql)
        self.assertEqual(c.execute('SELECT race_id,race_entry_id FROM race_result_entries').fetchone(),(1,1))
    def test_odds_selection_update_triggers(self):
        c=self.migrated(); b=self.batch(c); s=self.snap(c,b); c.execute('INSERT INTO odds_snapshot_selections VALUES(?,?,?)',(s,1,1)); b2=self.batch(c,2); s2=self.snap(c,b2)
        for sql in ("UPDATE odds_snapshot_selections SET race_entry_id=2","UPDATE odds_snapshot_selections SET odds_snapshot_id=%d"%s2):
            with self.assertRaises(sqlite3.IntegrityError): c.execute(sql)
        self.assertEqual(c.execute('SELECT odds_snapshot_id,race_entry_id FROM odds_snapshot_selections').fetchone(),(s,1))
    def test_odds_snapshot_update_triggers(self):
        c=self.migrated(); b=self.batch(c); s=self.snap(c,b); c.execute('INSERT INTO odds_snapshot_selections VALUES(?,?,?)',(s,1,1)); btype=self.batch(c,1,'馬連'); brace=self.batch(c,2)
        for sql in ("UPDATE odds_snapshots SET bet_type='馬連'","UPDATE odds_snapshots SET batch_id=%d"%btype,"UPDATE odds_snapshots SET batch_id=%d"%brace):
            with self.assertRaises(sqlite3.IntegrityError): c.execute(sql)
        self.assertEqual(c.execute('SELECT batch_id,bet_type FROM odds_snapshots').fetchone(),(b,'単勝'))
    def test_payout_update_triggers(self):
        c=self.migrated(); p=self.pub(c); pay=self.payout(c,p); c.execute('INSERT INTO payout_selections VALUES(?,?,?)',(pay,1,1)); ptype=self.pub(c,1,'馬連'); prace=self.pub(c,2)
        for sql in ("UPDATE payouts SET bet_type='馬連'","UPDATE payouts SET publication_id=%d"%ptype,"UPDATE payouts SET publication_id=%d"%prace):
            with self.assertRaises(sqlite3.IntegrityError): c.execute(sql)
        self.assertEqual(c.execute('SELECT publication_id,bet_type FROM payouts').fetchone(),(p,'単勝'))
    def test_payout_selection_update_triggers(self):
        c=self.migrated(); p=self.pub(c); pay=self.payout(c,p); c.execute('INSERT INTO payout_selections VALUES(?,?,?)',(pay,1,1)); pay2=self.payout(c,self.pub(c,2))
        for sql in ("UPDATE payout_selections SET race_entry_id=2","UPDATE payout_selections SET payout_id=%d"%pay2):
            with self.assertRaises(sqlite3.IntegrityError): c.execute(sql)
        self.assertEqual(c.execute('SELECT payout_id,race_entry_id FROM payout_selections').fetchone(),(pay,1))
