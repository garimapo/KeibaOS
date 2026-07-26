"""Connection-injected SQLite storage for immutable simulation bet-plan snapshots."""

from __future__ import annotations

from datetime import datetime, timezone
import sqlite3

from scripts.prediction.allocation_policy import AllocationPolicyIdentity
from scripts.simulation.bet_plan_identity import SimulationBetPlanIdentity
from scripts.simulation.bet_plan_snapshot import SimulationBetPlanSnapshot
from scripts.simulation.models import SimulationBet
from scripts.simulation.stake_allocation import BetStakeBudget

from .errors import RepositoryConflictError, RepositoryDataIntegrityError, RepositoryValidationError


class SQLiteSimulationBetPlanSnapshotRepository:
    """Save and load immutable snapshots using the v009 simulation-plan schema."""

    __slots__ = ("_connection",)

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise RepositoryValidationError("connection must be sqlite3.Connection")
        self._connection = connection
        self._ensure_foreign_keys()

    def load_snapshot(
        self,
        *,
        identity: SimulationBetPlanIdentity,
    ) -> SimulationBetPlanSnapshot | None:
        if not isinstance(identity, SimulationBetPlanIdentity):
            raise RepositoryValidationError("identity must be SimulationBetPlanIdentity")
        return self._load_snapshot(identity)

    def save_snapshot(
        self,
        *,
        snapshot: SimulationBetPlanSnapshot,
    ) -> None:
        if not isinstance(snapshot, SimulationBetPlanSnapshot):
            raise RepositoryValidationError("snapshot must be SimulationBetPlanSnapshot")
        if self._connection.in_transaction:
            raise RepositoryValidationError("repository writes require no active transaction")

        self._ensure_foreign_keys()
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            existing = self._load_snapshot(snapshot.identity)
            if existing is not None:
                if existing == snapshot:
                    self._connection.commit()
                    return
                raise RepositoryConflictError("simulation bet plan snapshot differs from existing snapshot")

            plan_id = self._insert_header(snapshot)
            for purchase_order, bet in enumerate(snapshot.bets):
                cursor = self._connection.execute(
                    """INSERT INTO simulation_bet_plan_bets
                       (plan_id,purchase_order,bet_type,stake,recommendation_rank)
                       VALUES(?,?,?,?,?)""",
                    (plan_id, purchase_order, bet.bet_type, bet.stake, bet.recommendation_rank),
                )
                bet_id = int(cursor.lastrowid)
                self._connection.executemany(
                    """INSERT INTO simulation_bet_plan_bet_selections
                       (bet_id,selection_order,race_entry_id) VALUES(?,?,?)""",
                    ((bet_id, selection_order, race_entry_id) for selection_order, race_entry_id in enumerate(bet.race_entry_ids)),
                )
            self._connection.commit()
        except sqlite3.IntegrityError as exc:
            self._connection.rollback()
            raise RepositoryDataIntegrityError("SQLite integrity constraint failed") from exc
        except Exception:
            self._connection.rollback()
            raise

    def _ensure_foreign_keys(self) -> None:
        try:
            self._connection.execute("PRAGMA foreign_keys=ON")
            enabled = self._connection.execute("PRAGMA foreign_keys").fetchone()
        except sqlite3.Error as exc:
            raise RepositoryValidationError("connection is not usable") from exc
        if enabled is None or enabled[0] != 1:
            raise RepositoryValidationError("foreign_keys could not be enabled")

    @staticmethod
    def _cutoff_to_text(value: object) -> str:
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise RepositoryValidationError("information_cutoff must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _cutoff_from_text(value: object) -> datetime:
        try:
            if not isinstance(value, str):
                raise TypeError("information_cutoff must be text")
            parsed = datetime.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise RepositoryDataIntegrityError("invalid information_cutoff") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise RepositoryDataIntegrityError("information_cutoff must be timezone-aware")
        cutoff = parsed.astimezone(timezone.utc)
        if value != cutoff.isoformat():
            raise RepositoryDataIntegrityError("information_cutoff must be canonical UTC ISO 8601")
        return cutoff

    def _load_snapshot(self, identity: SimulationBetPlanIdentity) -> SimulationBetPlanSnapshot | None:
        rows = self._connection.execute(
            """SELECT id,run_id,race_id,strategy_id,strategy_config_hash,information_cutoff,
                      allocation_policy_name,allocation_policy_version,
                      allocation_policy_config_hash,budget_total_amount
               FROM simulation_bet_plans
               WHERE run_id=? AND race_id=? AND strategy_id=?
                 AND strategy_config_hash=? AND information_cutoff=?""",
            (
                identity.run_id,
                identity.race_id,
                identity.strategy_id,
                identity.strategy_config_hash,
                self._cutoff_to_text(identity.information_cutoff),
            ),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise RepositoryDataIntegrityError("multiple simulation bet plan headers match one identity")
        return self._build_snapshot(rows[0])

    def _build_snapshot(self, header: tuple[object, ...]) -> SimulationBetPlanSnapshot:
        try:
            plan_id = header[0]
            identity = SimulationBetPlanIdentity(
                run_id=header[1],
                race_id=header[2],
                strategy_id=header[3],
                strategy_config_hash=header[4],
                information_cutoff=self._cutoff_from_text(header[5]),
            )
            policy_identity = AllocationPolicyIdentity(
                policy_name=header[6],
                policy_version=header[7],
                policy_config_hash=header[8],
            )
            budget = BetStakeBudget(total_amount=header[9])
            bet_rows = self._connection.execute(
                """SELECT id,purchase_order,bet_type,stake,recommendation_rank
                   FROM simulation_bet_plan_bets WHERE plan_id=? ORDER BY purchase_order ASC""",
                (plan_id,),
            ).fetchall()
            purchase_orders = [row[1] for row in bet_rows]
            if purchase_orders != list(range(len(bet_rows))):
                raise RepositoryDataIntegrityError("purchase_order must start at zero and be contiguous")

            bets: list[SimulationBet] = []
            for bet_id, _purchase_order, bet_type, stake, recommendation_rank in bet_rows:
                selection_rows = self._connection.execute(
                    """SELECT s.selection_order,s.race_entry_id,h.race_id
                       FROM simulation_bet_plan_bet_selections s
                       LEFT JOIN horses h ON h.id=s.race_entry_id
                       WHERE s.bet_id=? ORDER BY s.selection_order ASC""",
                    (bet_id,),
                ).fetchall()
                selection_orders = [row[0] for row in selection_rows]
                if selection_orders != list(range(len(selection_rows))):
                    raise RepositoryDataIntegrityError("selection_order must start at zero and be contiguous")
                if not selection_rows:
                    raise RepositoryDataIntegrityError("bet must contain at least one selection")
                race_entry_ids = tuple(row[1] for row in selection_rows)
                if any(row[2] != identity.race_id for row in selection_rows):
                    raise RepositoryDataIntegrityError("stored race entry does not belong to plan race")
                bet = SimulationBet(
                    race_id=identity.race_id,
                    strategy_id=identity.strategy_id,
                    bet_type=bet_type,
                    race_entry_ids=race_entry_ids,
                    stake=stake,
                    recommendation_rank=recommendation_rank,
                    placed_at_cutoff=identity.information_cutoff,
                )
                if bet.race_entry_ids != race_entry_ids:
                    raise RepositoryDataIntegrityError("stored selection order is not canonical")
                bets.append(bet)
            return SimulationBetPlanSnapshot(
                identity=identity,
                policy_identity=policy_identity,
                budget=budget,
                bets=tuple(bets),
            )
        except RepositoryDataIntegrityError:
            raise
        except (TypeError, ValueError, KeyError, AttributeError) as exc:
            raise RepositoryDataIntegrityError("stored data violates simulation bet plan invariants") from exc

    def _insert_header(self, snapshot: SimulationBetPlanSnapshot) -> int:
        identity = snapshot.identity
        policy = snapshot.policy_identity
        cursor = self._connection.execute(
            """INSERT INTO simulation_bet_plans
               (run_id,race_id,strategy_id,strategy_config_hash,information_cutoff,
                allocation_policy_name,allocation_policy_version,
                allocation_policy_config_hash,budget_total_amount)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                identity.run_id,
                identity.race_id,
                identity.strategy_id,
                identity.strategy_config_hash,
                self._cutoff_to_text(identity.information_cutoff),
                policy.policy_name,
                policy.policy_version,
                policy.policy_config_hash,
                snapshot.budget.total_amount,
            ),
        )
        return int(cursor.lastrowid)
