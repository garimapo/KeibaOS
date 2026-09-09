"""Append-only SQLite repository for immutable NAR daily replay results."""

from __future__ import annotations

from datetime import date as _date
from pathlib import Path as _Path
import json as _json
import sqlite3 as _sqlite3

from scripts.migrations.versions.v016_nar_daily_replay_result_schema import (
    require_v016_schema_contract as _require_v016_schema_contract,
)

from scripts.simulation.historical_daily_evidence_resolution import (
    DailyHistoricalReplayResolutionState as _ResolutionState,
)
from scripts.simulation.models import BetTypeSummary as _BetTypeSummary
from scripts.simulation.nar_daily_replay_orchestrator import (
    NARDailyReplayExecutionState as _ExecutionState,
)
from .errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)


__all__ = ("SQLiteNARDailyReplayResultRepository",)


_HEADER_COLUMNS = (
    "persisted_content_sha256", "schema_version", "orchestration_audit_sha256",
    "target_date", "organization", "source_system", "execution_state", "resolution_state",
    "target_set_content_sha256", "supplier_evidence_identity",
    "homepage_supplier_capture_id", "monthly_root_supplier_capture_id",
    "locator_script_supplier_capture_id", "monthly_capture_id",
    "race_list_capture_ids_json", "dataset_id", "selection_policy",
    "settlement_information_cutoff_utc", "canonical_target_count", "executable_count",
    "resolution_outcomes_json", "run_id", "run_started_at_utc", "target_commit_id",
    "strategy_id", "strategy_name", "strategy_config_hash", "race_budget_total_amount",
    "database_path", "nar_settlement_capture_archive_path", "configured_manifest_source_path",
    "published_manifest_path", "manifest_sha256", "summary_strategy_id",
    "summary_strategy_name", "summary_strategy_config_hash", "summary_race_count",
    "summary_settled_race_count", "summary_unsettled_race_count",
    "summary_no_bet_race_count", "summary_void_race_count", "summary_error_race_count",
    "summary_unsupported_race_count", "summary_bet_count", "summary_settled_bet_count",
    "summary_settled_purchase_race_count", "summary_hit_bet_count", "summary_hit_race_count",
    "summary_investment", "summary_payout", "summary_profit", "summary_roi_text",
    "summary_bet_hit_rate_text", "summary_race_hit_rate_text", "summary_maximum_drawdown",
)

_BET_COLUMNS = (
    "persisted_content_sha256", "bet_type", "bet_count", "settled_bet_count",
    "hit_bet_count", "investment", "payout", "profit", "roi_text", "bet_hit_rate_text",
)

_EXPECTED_MIGRATIONS = {
    8: "v008_simulation_schema",
    9: "v009_simulation_bet_plan_schema",
    10: "v010_historical_input_snapshot_schema",
    11: "v011_historical_past_race_time_difference_schema",
    12: "v012_historical_input_evidence_schema",
    13: "v013_historical_past_race_race_time_domain_schema",
    14: "v014_historical_input_request_identity_schema",
    15: "v015_jra_race_replay_seed_schema",
    16: "v016_nar_daily_replay_result_schema",
}


class SQLiteNARDailyReplayResultRepository:
    """Exact-ID persistence in the caller's explicitly migrated main database."""

    __slots__ = ("_connection", "_database_path")

    def __init__(self, *, connection: _sqlite3.Connection, database_path: _Path) -> None:
        if type(connection) is not _sqlite3.Connection:
            raise RepositoryValidationError("connection must be exact sqlite3.Connection")
        if connection.in_transaction:
            raise RepositoryValidationError("repository construction requires no active transaction")
        if not isinstance(database_path, _Path):
            raise RepositoryValidationError("database_path must be exact Path")
        text = str(database_path)
        if not text or "\x00" in text or not database_path.is_absolute():
            raise RepositoryValidationError("database_path must be absolute, nonempty and NUL-free")
        if not database_path.exists() or not database_path.is_file():
            raise RepositoryValidationError("database_path must identify an existing file")
        self._connection = connection
        self._database_path = database_path
        self._require_connection_binding()
        self._require_schema()

    def save_result(self, *, record: _Record) -> None:
        if type(record) is not _Record:
            raise RepositoryValidationError("record must be exact PersistedNARDailyReplayResult")
        if record.persisted_content_sha256 != _content_digest(record):
            raise RepositoryValidationError("record persisted-content identity is invalid")
        if record.database_path != self._database_path:
            raise RepositoryValidationError("record database_path differs from repository authority")
        if self._connection.in_transaction:
            raise RepositoryValidationError("repository writes require no active transaction")
        self._require_schema()
        try:
            self._connection.execute("BEGIN IMMEDIATE")
            same_content = self._load_by_content(record.persisted_content_sha256)
            if same_content is not None:
                if same_content != record:
                    raise RepositoryDataIntegrityError(
                        "stored content identity reconstructs different content"
                    )
                self._connection.commit()
                return
            same_audit = self._load_by_audit(record.orchestration_audit_sha256)
            if same_audit is not None:
                if same_audit == record:
                    self._connection.commit()
                    return
                raise RepositoryConflictError(
                    "orchestration audit identity already has different immutable content"
                )
            self._insert(record)
            loaded = self._load_by_content(record.persisted_content_sha256)
            if loaded != record:
                raise RepositoryDataIntegrityError("inserted result failed exact transaction reload")
            self._connection.commit()
        except (RepositoryConflictError, RepositoryDataIntegrityError):
            self._connection.rollback()
            raise
        except _sqlite3.IntegrityError as error:
            self._connection.rollback()
            raise RepositoryDataIntegrityError("SQLite rejected daily replay result") from error
        except _sqlite3.Error as error:
            self._connection.rollback()
            raise RepositoryDataIntegrityError("SQLite failed daily replay result publication") from error
        except BaseException:
            self._connection.rollback()
            raise

    def load_result(self, *, persisted_content_sha256: str) -> _Record | None:
        if (
            type(persisted_content_sha256) is not str
            or len(persisted_content_sha256) != 64
            or any(character not in "0123456789abcdef" for character in persisted_content_sha256)
        ):
            raise RepositoryValidationError("persisted_content_sha256 is invalid")
        self._require_schema()
        try:
            return self._load_by_content(persisted_content_sha256)
        except RepositoryDataIntegrityError:
            raise
        except RepositoryValidationError as error:
            raise RepositoryDataIntegrityError("stored daily replay result is invalid") from error
        except (_sqlite3.Error, TypeError, ValueError) as error:
            raise RepositoryDataIntegrityError("stored daily replay result is invalid") from error

    def _require_connection_binding(self) -> None:
        try:
            self._connection.execute("PRAGMA foreign_keys=ON")
            if self._connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
                raise RepositoryValidationError("foreign_keys could not be enabled")
            rows = tuple(self._connection.execute("PRAGMA database_list"))
        except _sqlite3.Error as error:
            raise RepositoryValidationError("connection is not usable") from error
        if self._connection.in_transaction:
            raise RepositoryValidationError("connection binding changed transaction state")
        usable = tuple(row for row in rows if not (len(row) == 3 and row[1] == "temp" and row[2] == ""))
        if (
            len(usable) != 1
            or len(usable[0]) != 3
            or usable[0][0] != 0
            or usable[0][1] != "main"
        ):
            raise RepositoryValidationError("connection must contain one exact main database")
        filename = usable[0][2]
        if type(filename) is not str or not filename or filename == ":memory:":
            raise RepositoryValidationError("connection main database must be a filesystem file")
        reported = _Path(filename)
        try:
            same_file = reported.is_absolute() and reported.is_file() and self._database_path.samefile(reported)
        except OSError as error:
            raise RepositoryValidationError("database filesystem identity cannot be verified") from error
        if not same_file:
            raise RepositoryValidationError("connection and database_path identify different files")

    def _require_schema(self) -> None:
        if self._connection.in_transaction:
            raise RepositoryValidationError("schema validation requires no active transaction")
        try:
            applied = dict(
                self._connection.execute("SELECT version,name FROM schema_migrations")
            )
            _require_v016_schema_contract(self._connection)
        except (_sqlite3.Error, RuntimeError) as error:
            raise RepositoryDataIntegrityError("v016 daily replay result schema is unavailable") from error
        if applied != _EXPECTED_MIGRATIONS:
            raise RepositoryDataIntegrityError("registered migration state is not exact v016")

    def _insert(self, record: _Record) -> None:
        summary = record.summary
        summary_values = (None,) * 22 if summary is None else (
            summary.strategy_id, summary.strategy_name, summary.strategy_config_hash,
            summary.race_count, summary.settled_race_count, summary.unsettled_race_count,
            summary.no_bet_race_count, summary.void_race_count, summary.error_race_count,
            summary.unsupported_race_count, summary.bet_count, summary.settled_bet_count,
            summary.settled_purchase_race_count, summary.hit_bet_count, summary.hit_race_count,
            summary.investment, summary.payout, summary.profit, _decimal_text(summary.roi),
            _decimal_text(summary.bet_hit_rate), _decimal_text(summary.race_hit_rate),
            summary.maximum_drawdown,
        )
        values = (
            record.persisted_content_sha256, record.schema_version,
            record.orchestration_audit_sha256, record.target_date.isoformat(),
            record.organization, record.source_system, record.execution_state.value,
            record.resolution_state.value, record.target_set_content_sha256,
            record.supplier_evidence_identity, record.homepage_supplier_capture_id,
            record.monthly_root_supplier_capture_id, record.locator_script_supplier_capture_id,
            record.monthly_capture_id, _canonical_json(list(record.race_list_capture_ids)),
            record.dataset_id, record.selection_policy,
            _datetime_text(record.settlement_information_cutoff), record.canonical_target_count,
            record.executable_count, record.resolution_outcomes_json, record.run_id,
            _datetime_text(record.run_started_at), record.target_commit_id, record.strategy_id,
            record.strategy_name, record.strategy_config_hash, record.race_budget_total_amount,
            str(record.database_path), str(record.nar_settlement_capture_archive_path),
            str(record.configured_manifest_source_path),
            None if record.published_manifest_path is None else str(record.published_manifest_path),
            record.manifest_sha256,
            *summary_values,
        )
        placeholders = ",".join("?" for _ in _HEADER_COLUMNS)
        self._connection.execute(
            f"INSERT INTO nar_daily_replay_results ({','.join(_HEADER_COLUMNS)}) VALUES({placeholders})",
            values,
        )
        if summary is not None:
            self._connection.executemany(
                """INSERT INTO nar_daily_replay_result_bet_type_summaries
                   (persisted_content_sha256,bet_type,bet_count,settled_bet_count,
                    hit_bet_count,investment,payout,profit,roi_text,bet_hit_rate_text)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    (
                        record.persisted_content_sha256, item.bet_type, item.bet_count,
                        item.settled_bet_count, item.hit_bet_count, item.investment,
                        item.payout, item.profit, _decimal_text(item.roi),
                        _decimal_text(item.bet_hit_rate),
                    )
                    for item in (summary.by_bet_type[key] for key in sorted(summary.by_bet_type))
                ),
            )

    def _load_by_content(self, content_sha256: str) -> _Record | None:
        rows = self._connection.execute(
            f"SELECT {','.join(_HEADER_COLUMNS)} FROM nar_daily_replay_results WHERE persisted_content_sha256=?",
            (content_sha256,),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise RepositoryDataIntegrityError("multiple headers match one content identity")
        return self._reconstruct(rows[0])

    def _load_by_audit(self, audit_sha256: str) -> _Record | None:
        rows = self._connection.execute(
            f"SELECT {','.join(_HEADER_COLUMNS)} FROM nar_daily_replay_results WHERE orchestration_audit_sha256=?",
            (audit_sha256,),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise RepositoryDataIntegrityError("multiple headers match one audit identity")
        return self._reconstruct(rows[0])

    def _reconstruct(self, row: tuple[object, ...]) -> _Record:
        if len(row) != len(_HEADER_COLUMNS):
            raise RepositoryDataIntegrityError("stored header has unexpected shape")
        data = dict(zip(_HEADER_COLUMNS, row, strict=True))
        content_sha256 = data["persisted_content_sha256"]
        bet_rows = self._connection.execute(
            f"SELECT {','.join(_BET_COLUMNS)} FROM nar_daily_replay_result_bet_type_summaries WHERE persisted_content_sha256=? ORDER BY bet_type ASC",
            (content_sha256,),
        ).fetchall()
        by_bet_type: dict[str, _BetTypeSummary] = {}
        for bet_row in bet_rows:
            if len(bet_row) != len(_BET_COLUMNS) or bet_row[0] != content_sha256:
                raise RepositoryDataIntegrityError("stored bet-type child is malformed")
            try:
                item = _BetTypeSummary(
                    bet_type=bet_row[1], bet_count=bet_row[2],
                    settled_bet_count=bet_row[3], hit_bet_count=bet_row[4],
                    investment=bet_row[5], payout=bet_row[6], profit=bet_row[7],
                    roi=self._stored_decimal(bet_row[8], "bet-type roi"),
                    bet_hit_rate=self._stored_decimal(
                        bet_row[9], "bet-type hit rate"
                    ),
                )
            except RepositoryDataIntegrityError:
                raise
            except (TypeError, ValueError) as error:
                raise RepositoryDataIntegrityError(
                    "stored bet-type child violates domain invariants"
                ) from error
            if item.bet_type in by_bet_type:
                raise RepositoryDataIntegrityError("duplicate bet-type child")
            by_bet_type[item.bet_type] = item
        summary_fields = tuple(data[name] for name in _HEADER_COLUMNS[33:55])
        summary = None
        if data["execution_state"] == _ExecutionState.FULL_DAY_REPLAY_COMPLETED.value:
            summary = _summary_from_storage(summary_fields, by_bet_type)
        elif by_bet_type or any(value is not None for value in summary_fields):
            raise RepositoryDataIntegrityError("diagnostic record contains summary content")
        try:
            race_list = _validate_json_text(
                data["race_list_capture_ids_json"], "stored race_list_capture_ids_json"
            )
        except RepositoryValidationError as error:
            raise RepositoryDataIntegrityError("stored race-list JSON is invalid") from error
        if type(race_list) is not list:
            raise RepositoryDataIntegrityError("stored race-list IDs must be a JSON list")
        try:
            record = _Record(
                schema_version=data["schema_version"],
                orchestration_audit_sha256=data["orchestration_audit_sha256"],
                target_date=_date.fromisoformat(data["target_date"]),
                organization=data["organization"], source_system=data["source_system"],
                execution_state=_ExecutionState(data["execution_state"]),
                resolution_state=_ResolutionState(data["resolution_state"]),
                target_set_content_sha256=data["target_set_content_sha256"],
                supplier_evidence_identity=data["supplier_evidence_identity"],
                homepage_supplier_capture_id=data["homepage_supplier_capture_id"],
                monthly_root_supplier_capture_id=data["monthly_root_supplier_capture_id"],
                locator_script_supplier_capture_id=data["locator_script_supplier_capture_id"],
                monthly_capture_id=data["monthly_capture_id"],
                race_list_capture_ids=tuple(race_list), dataset_id=data["dataset_id"],
                selection_policy=data["selection_policy"],
                settlement_information_cutoff=_parse_utc_text(
                    data["settlement_information_cutoff_utc"], "settlement cutoff"
                ),
                canonical_target_count=data["canonical_target_count"],
                executable_count=data["executable_count"],
                resolution_outcomes_json=data["resolution_outcomes_json"],
                run_id=data["run_id"],
                run_started_at=_parse_utc_text(data["run_started_at_utc"], "run started_at"),
                target_commit_id=data["target_commit_id"], strategy_id=data["strategy_id"],
                strategy_name=data["strategy_name"],
                strategy_config_hash=data["strategy_config_hash"],
                race_budget_total_amount=data["race_budget_total_amount"],
                database_path=_Path(data["database_path"]),
                nar_settlement_capture_archive_path=_Path(
                    data["nar_settlement_capture_archive_path"]
                ),
                configured_manifest_source_path=_Path(data["configured_manifest_source_path"]),
                published_manifest_path=None if data["published_manifest_path"] is None else _Path(data["published_manifest_path"]),
                manifest_sha256=data["manifest_sha256"], summary=summary,
            )
        except RepositoryValidationError as error:
            raise RepositoryDataIntegrityError("stored result violates domain invariants") from error
        except (TypeError, ValueError) as error:
            raise RepositoryDataIntegrityError("stored result cannot be reconstructed") from error
        if record.persisted_content_sha256 != content_sha256:
            raise RepositoryDataIntegrityError("stored persisted-content digest is invalid")
        return record

    @staticmethod
    def _stored_decimal(value: object, name: str):
        from scripts.simulation.nar_daily_replay_result_persistence import _decimal_from_text

        return _decimal_from_text(value, name)


from scripts.simulation.nar_daily_replay_result_persistence import (
    PersistedNARDailyReplayResult as _Record,
    _canonical_json,
    _content_digest,
    _datetime_text,
    _decimal_text,
    _parse_utc_text,
    _summary_from_storage,
    _validate_json_text,
)


if "annotations" in globals():
    del annotations
