"""Simulation bet-plan snapshot schema migration."""

VERSION = 9
NAME = "v009_simulation_bet_plan_schema"


STATEMENTS = (
    """CREATE TABLE simulation_bet_plans (
        id INTEGER PRIMARY KEY,
        run_id TEXT NOT NULL,
        race_id INTEGER NOT NULL REFERENCES races(id),
        strategy_id TEXT NOT NULL,
        strategy_config_hash TEXT NOT NULL,
        information_cutoff TEXT NOT NULL,
        allocation_policy_name TEXT NOT NULL,
        allocation_policy_version TEXT NOT NULL,
        allocation_policy_config_hash TEXT NOT NULL,
        budget_total_amount INTEGER NOT NULL,
        UNIQUE (run_id, race_id, strategy_id, strategy_config_hash, information_cutoff),
        CHECK (budget_total_amount >= 0),
        CHECK (budget_total_amount % 100 = 0)
    )""",
    """CREATE TABLE simulation_bet_plan_bets (
        id INTEGER PRIMARY KEY,
        plan_id INTEGER NOT NULL REFERENCES simulation_bet_plans(id) ON DELETE CASCADE,
        purchase_order INTEGER NOT NULL,
        bet_type TEXT NOT NULL,
        stake INTEGER NOT NULL,
        recommendation_rank INTEGER NOT NULL,
        UNIQUE (plan_id, purchase_order),
        CHECK (purchase_order >= 0),
        CHECK (stake > 0),
        CHECK (stake % 100 = 0),
        CHECK (recommendation_rank >= 0)
    )""",
    """CREATE TABLE simulation_bet_plan_bet_selections (
        bet_id INTEGER NOT NULL REFERENCES simulation_bet_plan_bets(id) ON DELETE CASCADE,
        selection_order INTEGER NOT NULL,
        race_entry_id INTEGER NOT NULL REFERENCES horses(id),
        PRIMARY KEY (bet_id, selection_order),
        UNIQUE (bet_id, race_entry_id),
        CHECK (selection_order >= 0)
    )""",
)


def _trigger(name: str, table: str, timing: str, condition: str) -> str:
    return f"CREATE TRIGGER {name} BEFORE {timing} ON {table} WHEN {condition} BEGIN SELECT RAISE(ABORT,'integrity violation'); END"


TRIGGERS = tuple(
    _trigger(
        f"sbpbs_entry_race_{operation.lower()}",
        "simulation_bet_plan_bet_selections",
        operation,
        "(SELECT h.race_id FROM horses h WHERE h.id=NEW.race_entry_id) != "
        "(SELECT p.race_id FROM simulation_bet_plan_bets b "
        "JOIN simulation_bet_plans p ON p.id=b.plan_id WHERE b.id=NEW.bet_id)",
    )
    for operation in ("INSERT", "UPDATE")
) + (
    _trigger(
        "sbpb_plan_race_update",
        "simulation_bet_plan_bets",
        "UPDATE",
        "NEW.plan_id != OLD.plan_id AND EXISTS(SELECT 1 "
        "FROM simulation_bet_plan_bet_selections s JOIN horses h ON h.id=s.race_entry_id "
        "WHERE s.bet_id=OLD.id AND h.race_id != "
        "(SELECT race_id FROM simulation_bet_plans WHERE id=NEW.plan_id))",
    ),
)


def apply(connection) -> None:
    for statement in STATEMENTS + TRIGGERS:
        connection.execute(statement)
