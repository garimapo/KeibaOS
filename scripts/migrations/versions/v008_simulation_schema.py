"""Ver0.8 schema. selection_key の内容照合は後続Providerの責務。"""
VERSION = 8
NAME = "v008_simulation_schema"
UTC = "substr(%s,-6) = '+00:00'"
BET = "'単勝','馬連','ワイド','3連複'"

STATEMENTS = (
f"""CREATE TABLE race_results (race_id INTEGER PRIMARY KEY REFERENCES races(id), result_status TEXT NOT NULL CHECK(result_status IN ('complete','partial','void','unsupported')), finalized_at TEXT, observed_at TEXT NOT NULL CHECK({UTC % 'observed_at'}), source TEXT NOT NULL CHECK(trim(source)<>''), source_url TEXT, CHECK(finalized_at IS NULL OR (substr(finalized_at,-6)='+00:00' AND finalized_at<=observed_at)), CHECK(result_status<>'complete' OR finalized_at IS NOT NULL))""",
"""CREATE TABLE race_result_entries (race_id INTEGER NOT NULL REFERENCES races(id), race_entry_id INTEGER NOT NULL REFERENCES horses(id), finish_position INTEGER CHECK(finish_position IS NULL OR finish_position>0), result_status TEXT NOT NULL CHECK(result_status IN ('confirmed','void','unsupported')), PRIMARY KEY(race_id,race_entry_id))""",
f"""CREATE TABLE odds_snapshot_batches (id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL REFERENCES races(id), bet_type TEXT NOT NULL CHECK(bet_type IN ({BET})), observed_at TEXT NOT NULL CHECK({UTC % 'observed_at'}), is_complete INTEGER NOT NULL CHECK(is_complete IN (0,1)), source TEXT NOT NULL CHECK(trim(source)<>''), source_url TEXT, UNIQUE(race_id,bet_type,observed_at,source))""",
f"""CREATE TABLE odds_snapshots (id INTEGER PRIMARY KEY, batch_id INTEGER NOT NULL REFERENCES odds_snapshot_batches(id), bet_type TEXT NOT NULL CHECK(bet_type IN ({BET})), selection_key TEXT NOT NULL CHECK(trim(selection_key)<>''), odds_scaled INTEGER NOT NULL CHECK(odds_scaled>0), odds_scale INTEGER NOT NULL CHECK(odds_scale BETWEEN 0 AND 6), UNIQUE(batch_id,bet_type,selection_key))""",
"""CREATE TABLE odds_snapshot_selections (odds_snapshot_id INTEGER NOT NULL REFERENCES odds_snapshots(id), race_entry_id INTEGER NOT NULL REFERENCES horses(id), selection_order INTEGER NOT NULL CHECK(selection_order>0), PRIMARY KEY(odds_snapshot_id,race_entry_id), UNIQUE(odds_snapshot_id,selection_order))""",
f"""CREATE TABLE payout_publications (id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL REFERENCES races(id), bet_type TEXT NOT NULL CHECK(bet_type IN ({BET})), finalized_at TEXT, observed_at TEXT NOT NULL CHECK({UTC % 'observed_at'}), is_complete INTEGER NOT NULL CHECK(is_complete IN (0,1)), source TEXT NOT NULL CHECK(trim(source)<>''), source_url TEXT, CHECK(finalized_at IS NULL OR (substr(finalized_at,-6)='+00:00' AND finalized_at<=observed_at)), CHECK(is_complete=0 OR finalized_at IS NOT NULL), UNIQUE(race_id,bet_type,observed_at,source))""",
f"""CREATE TABLE payouts (id INTEGER PRIMARY KEY, publication_id INTEGER NOT NULL REFERENCES payout_publications(id), bet_type TEXT NOT NULL CHECK(bet_type IN ({BET})), selection_key TEXT NOT NULL CHECK(trim(selection_key)<>''), payout_per_100 INTEGER NOT NULL CHECK(payout_per_100>=0), payout_status TEXT NOT NULL CHECK(payout_status IN ('winning','refund','void','unsupported')), CHECK(payout_status<>'winning' OR payout_per_100>0), UNIQUE(publication_id,bet_type,selection_key))""",
"""CREATE TABLE payout_selections (payout_id INTEGER NOT NULL REFERENCES payouts(id), race_entry_id INTEGER NOT NULL REFERENCES horses(id), selection_order INTEGER NOT NULL CHECK(selection_order>0), PRIMARY KEY(payout_id,race_entry_id), UNIQUE(payout_id,selection_order))""",
"CREATE INDEX idx_rre_race ON race_result_entries(race_id)", "CREATE INDEX idx_osb_race ON odds_snapshot_batches(race_id,bet_type,observed_at)", "CREATE INDEX idx_os_batch ON odds_snapshots(batch_id,bet_type)", "CREATE INDEX idx_pp_race ON payout_publications(race_id,bet_type,observed_at)", "CREATE INDEX idx_payout_pub ON payouts(publication_id,bet_type)",
)

def _trigger(name, table, timing, condition):
    return f"CREATE TRIGGER {name} BEFORE {timing} ON {table} WHEN {condition} BEGIN SELECT RAISE(ABORT,'integrity violation'); END"

TRIGGERS = tuple(_trigger(f"rre_entry_race_{op.lower()}", "race_result_entries", op, "(SELECT race_id FROM horses WHERE id=NEW.race_entry_id) != NEW.race_id") for op in ("INSERT","UPDATE")) + tuple(_trigger(f"oss_entry_race_{op.lower()}", "odds_snapshot_selections", op, "(SELECT h.race_id FROM horses h WHERE h.id=NEW.race_entry_id) != (SELECT b.race_id FROM odds_snapshots o JOIN odds_snapshot_batches b ON b.id=o.batch_id WHERE o.id=NEW.odds_snapshot_id)") for op in ("INSERT","UPDATE")) + tuple(_trigger(f"ps_entry_race_{op.lower()}", "payout_selections", op, "(SELECT h.race_id FROM horses h WHERE h.id=NEW.race_entry_id) != (SELECT q.race_id FROM payouts p JOIN payout_publications q ON q.id=p.publication_id WHERE p.id=NEW.payout_id)") for op in ("INSERT","UPDATE")) + tuple(_trigger(f"odds_type_{op.lower()}", "odds_snapshots", op, "NEW.bet_type != (SELECT bet_type FROM odds_snapshot_batches WHERE id=NEW.batch_id)") for op in ("INSERT","UPDATE")) + tuple(_trigger(f"payout_type_{op.lower()}", "payouts", op, "NEW.bet_type != (SELECT bet_type FROM payout_publications WHERE id=NEW.publication_id)") for op in ("INSERT","UPDATE"))
TRIGGERS += (
    _trigger("odds_snapshot_batch_race_update", "odds_snapshots", "UPDATE", "NEW.batch_id != OLD.batch_id AND EXISTS(SELECT 1 FROM odds_snapshot_selections s JOIN horses h ON h.id=s.race_entry_id WHERE s.odds_snapshot_id=OLD.id AND h.race_id != (SELECT race_id FROM odds_snapshot_batches WHERE id=NEW.batch_id))"),
    _trigger("payout_publication_race_update", "payouts", "UPDATE", "NEW.publication_id != OLD.publication_id AND EXISTS(SELECT 1 FROM payout_selections s JOIN horses h ON h.id=s.race_entry_id WHERE s.payout_id=OLD.id AND h.race_id != (SELECT race_id FROM payout_publications WHERE id=NEW.publication_id))"),
)

def apply(connection):
    for statement in STATEMENTS + TRIGGERS:
        connection.execute(statement)
