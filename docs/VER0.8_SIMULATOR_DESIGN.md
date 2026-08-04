# KeibaOS Ver0.8 回収率シミュレーター設計

## 目的

過去レースを当時の情報だけで時系列再現し、既存の予想パイプラインと購入戦略を用いて購入結果を精算する。Strategyごとに回収率、的中率、券種別成績、最大ドローダウンを比較できる再現可能な検証基盤を設計する。

今回は設計のみを対象とする。実装、DB変更、既存の予想・候補生成・戦略ロジックの複製は行わない。既存の `PredictionPipeline`、`BetGenerator`、`BetStrategy` を再利用する。

初期実装の対象券種は単勝のみとする。馬連、ワイド、3連複は、予想時点の実組み合わせオッズと確定した完全な払戻表を取得・保存できるまで購入対象にしない。現行 `BetGenerator` の `combination_score` は実オッズによる期待値ではなく候補比較値であるため、組み合わせ券種のEVとして扱わない。

## 基本方針

- 購入額は1点あたり100円単位とする。初期実装は固定100円で、資金配分は対象外とする。
- 実現ROIの検証は確定払戻表だけを使用する。仮想EV、後知恵のオッズ、候補比較値から払戻を推定しない。
- 予想時点の実オッズを用いたEV戦略の検証は、単勝または完全な組み合わせオッズスナップショットが保存される券種だけで行う。
- 未来情報を検証できない入力は受け入れない（Fail Closed）。検証不能なデータセットでは正式ROIを算出しない。
- 取消、除外、同着、返還、降着、不成立の精算ルールは、仕様確定まで推測実装しない。対応外状態は `VOID` または `UNSUPPORTED` 相当として明示的に記録する。

## 用語とID

現行コードの `horse_id` は血統上の恒久的な馬IDではなく、`horses.id`、すなわち特定レースの出走行IDを表す。シミュレーター設計ではこの意味を明確にするため、外部公開モデルでは `race_entry_id` を使用する。既存モデルとの接続境界でのみ `horse_id`（=`race_entry_id`）へ変換する。

- 外部払戻・結果データの `horse_no` はレース内の馬番である。
- Providerは `race_id + horse_no` から内部 `race_entry_id` への対応を解決する。
- 単勝の選択は重複なし1件、馬連・ワイドは重複なし2件、3連複は重複なし3件とする。
- 組み合わせの `race_entry_id` は常に昇順タプルへ正規化する。

## 時刻モデルと未来情報遮断

すべての日時はtimezone-awareな `datetime` を使用する。DBにはUTC ISO 8601形式で保存し、CLI・レポート表示はAsia/Tokyoを基本とする。

## Phase 4C-2d3b1a: Simulation bet plan persistence boundary

### Scope and existing persistence conventions

The persistence unit is `SimulationBetPlanSnapshot`, not prediction,
allocation, Resolver, Provider, or configuration objects.  A stored snapshot
must reconstruct the same identity, policy identity, budget, tuple order, and
`SimulationBet` values without synthesizing fields.  This section supersedes
the earlier design-only `SimulationBetRepository` placeholder and its
`save_plan(...)->SimulationBetPlanSnapshot` signature.

The existing facts are:

* `scripts/database.py` is the legacy helper: `get_connection()` opens
  `database/keiba.db`; `_connection()` commits on normal exit and rolls back on
  exception.  `create_tables()` only manages legacy base tables and does not
  enable foreign keys or own the simulation schema.
* Simulation tables use `scripts.migrations.runner`: `schema_migrations`
  records versions, `PRAGMA foreign_keys = ON` is verified, and each migration
  runs in `BEGIN IMMEDIATE` with commit-or-rollback semantics.  The current
  registered migrations are `v008_simulation_schema` and
  `v009_simulation_bet_plan_schema`.
* Existing connection-injected simulation repositories reject caller-owned
  active transactions, enable foreign keys, use `BEGIN IMMEDIATE`, roll back
  every failed write, use `RepositoryConflictError` for immutable conflicts,
  and use `RepositoryDataIntegrityError` for SQLite integrity failures.
* Existing simulation rows serialize aware timestamps as UTC ISO-8601 text.
  Repository tests use injected `:memory:` SQLite connections and migrations;
  they do not use `database/keiba.db`.
* `horses` is the current race-entry table.  `horses.id` is the persisted
  `race_entry_id`, while `horses.race_id` scopes it to a race.
  `database.get_horse_id()` returns that ID for `(race_id, horse_no)`.  There
  is no separate stable horse-entity table and no existing race-entry lookup
  Repository API.

### Authoritative v009 schema

The formal tables are `simulation_bet_plans`,
`simulation_bet_plan_bets`, and `simulation_bet_plan_bet_selections`.
The new migration is `v009_simulation_bet_plan_schema`, registered after v008.
It uses `INTEGER PRIMARY KEY`, not `AUTOINCREMENT`, `WITHOUT ROWID`, or a
domain-visible database ID.

```sql
CREATE TABLE simulation_bet_plans (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL CHECK (trim(run_id) <> ''),
    race_id INTEGER NOT NULL REFERENCES races(id),
    strategy_id TEXT NOT NULL CHECK (trim(strategy_id) <> ''),
    strategy_config_hash TEXT NOT NULL CHECK (length(strategy_config_hash) = 64),
    information_cutoff TEXT NOT NULL,
    allocation_policy_name TEXT NOT NULL CHECK (trim(allocation_policy_name) <> ''),
    allocation_policy_version TEXT NOT NULL CHECK (trim(allocation_policy_version) <> ''),
    allocation_policy_config_hash TEXT NOT NULL CHECK (length(allocation_policy_config_hash) = 64),
    budget_total_amount INTEGER NOT NULL
        CHECK (budget_total_amount >= 0)
        CHECK (budget_total_amount % 100 = 0),
    UNIQUE (run_id, race_id, strategy_id, strategy_config_hash, information_cutoff)
);

CREATE TABLE simulation_bet_plan_bets (
    id INTEGER PRIMARY KEY,
    plan_id INTEGER NOT NULL,
    purchase_order INTEGER NOT NULL CHECK (purchase_order >= 0),
    bet_type TEXT NOT NULL,
    stake INTEGER NOT NULL CHECK (stake > 0) CHECK (stake % 100 = 0),
    recommendation_rank INTEGER NOT NULL CHECK (recommendation_rank >= 0),
    UNIQUE (plan_id, purchase_order),
    FOREIGN KEY (plan_id) REFERENCES simulation_bet_plans(id) ON DELETE CASCADE
);

CREATE TABLE simulation_bet_plan_bet_selections (
    bet_id INTEGER NOT NULL,
    selection_order INTEGER NOT NULL CHECK (selection_order >= 0),
    race_entry_id INTEGER NOT NULL REFERENCES horses(id),
    PRIMARY KEY (bet_id, selection_order),
    UNIQUE (bet_id, race_entry_id),
    FOREIGN KEY (bet_id) REFERENCES simulation_bet_plan_bets(id) ON DELETE CASCADE
);
```

The natural identity is exactly `(run_id, race_id, strategy_id,
strategy_config_hash, information_cutoff)`.  Policy identity, budget, saved
time, and surrogate IDs are immutable content, not alternate identity fields.
The unique constraint is the identity lookup and the final concurrency defence.
The header maps one-for-one to `SimulationBetPlanIdentity`,
`AllocationPolicyIdentity`, and `BetStakeBudget`; the bet child maps
`purchase_order`, `bet_type`, `stake`, and `recommendation_rank`; the selection
child maps each `race_entry_id` and its zero-based tuple index.

`purchase_order` is the zero-based `snapshot.bets` index, never a rank, row ID,
selection order, or timestamp.  `selection_order` is the zero-based
`SimulationBet.race_entry_ids` index.  Repository load orders by these columns
and verifies that each begins at zero and is contiguous.  Recommendation ranks
are non-negative and may repeat.

Selections are normalized rows, not JSON.  This permits foreign keys,
race-entry searching, explicit ordering, and integrity checks without JSON1 or
malformed-JSON handling.  Current selections are canonicalized by
`SimulationBet`, but the repository still stores and restores their tuple
order without sorting.

### Foreign keys, checks, and indexes

The header references `races.id`; selection rows reference `horses.id`; the two
internal parent-child relationships use `ON DELETE CASCADE` solely to prevent
orphans if a future maintenance path deletes a plan.  No delete API is added.
Race and horse source rows retain restrictive SQLite behaviour.  The migration
also adds insert/update triggers, following the existing odds/payout pattern,
to prove that a selection's `horses.race_id` equals the plan header's race.

Database checks enforce coarse integer and non-empty-text invariants.  Domain
constructors remain authoritative for bool rejection, complete hash validation,
aware datetime validation, supported bet types, selection cardinality,
canonicalization, duplicate bet identity, budget total, and all snapshot
invariants.  SQL has no fixed bet-type enumeration, avoiding migration churn
when a supported type changes.  Hash checks use length 64 only; lowercase hex
is revalidated by domain constructors.

No redundant first-version indexes are added: natural identity, the bet unique
constraint, and the selection primary key cover source lookup and ordered child
reads.  A direct `race_entry_id` lookup index is deferred until a measured query
requires it.

### Empty plans and serialization

An empty snapshot saves one header and zero bet/selection rows.  It means a
plan was generated and fixed with no purchases; it is distinct from no header,
save failure, and load failure.  Loading that header returns an ordinary empty
`SimulationBetPlanSnapshot`, retaining policy identity and budget.

`information_cutoff` accepts every timezone-aware `datetime`, including a
non-UTC offset such as `Asia/Tokyo`; only a naive input is rejected.  Save first
converts the aware value to UTC and stores canonical ISO-8601 TEXT with
microseconds and `+00:00`, conceptually
`information_cutoff.astimezone(timezone.utc).isoformat(timespec="microseconds")`.
Load parses that text, rejects malformed or naive values, and reconstructs a
UTC-aware `datetime`; it neither substitutes the current time nor converts to a
local timezone.  `Z` normalizes to `+00:00`.  The original display offset is
not part of persisted identity, while instant equality is preserved: a saved
`+09:00` value and its loaded `+00:00` value compare equal when they denote the
same instant.  Datetime text is never used for semantic sorting.
Strategy and policy hashes are stored as supplied TEXT and never regenerated,
trimmed, or case-normalized by the repository.

### Source and repository contracts

Read and write are separate contracts in a new independent module
`scripts/simulation/bet_plan_snapshot_repository.py`.  They must not be added
to `repositories/interfaces.py`, because `simulation.models` already imports
that module and snapshot values depend on simulation models, creating a cycle.

```python
class SimulationBetPlanSnapshotSource(Protocol):
    def load_snapshot(
        self,
        *,
        identity: SimulationBetPlanIdentity,
    ) -> SimulationBetPlanSnapshot | None:
        ...


class SimulationBetPlanSnapshotRepository(Protocol):
    def save_snapshot(
        self,
        *,
        snapshot: SimulationBetPlanSnapshot,
    ) -> None:
        ...
```

The concrete SQLite implementation is
`scripts/simulation/repositories/sqlite_bet_plan_snapshot_repository.py`; it
receives an injected connection and implements both protocols.  It exposes
neither DB IDs nor update/delete/list/async APIs.  `None` is exclusively
not-found.

Saving is insert-only and idempotent: in the write transaction, reconstruct an
existing snapshot by natural identity and compare full dataclass equality.
Equal content succeeds as a no-op; different policy, budget, count, tuple
order, type, stake, rank, selection, or cutoff raises existing
`RepositoryConflictError`.  Silent overwrite, delete-and-reinsert, and partial
child updates are forbidden.

`RepositoryConflictError` and `RepositoryDataIntegrityError` already exist in
`scripts/simulation/repositories/errors.py`.  Existing SQLite repositories use
the former for immutable insert-only content conflicts and the latter for
SQLite constraint failures and corrupt stored data.  The Snapshot Repository
reuses both existing classes: caller/key errors use `RepositoryValidationError`;
stored-data and SQLite constraint corruption use
`RepositoryDataIntegrityError` with causes retained; unexpected SQLite
operational errors are not broadly wrapped.  No new snapshot-specific exception
is introduced.

### Transaction, concurrency, and fail-closed load

Save rejects caller-owned active transactions, enables/verifies foreign keys,
then performs identity lookup, header insert, all bet inserts, and all selection
inserts in one `BEGIN IMMEDIATE` transaction.  Empty plans commit only their
header.  Any validation, conflict, or SQL failure rolls back all rows.  The
second concurrent writer sees the first committed plan and resolves through the
same equality decision; a defensive unique race rolls back, rereads, and
returns no-op only for identical content.

Loading is strictly:

```text
one header by natural identity
-> bets ORDER BY purchase_order ASC
-> selections ORDER BY selection_order ASC
-> contiguous-order and relation checks
-> SimulationBet construction
-> SimulationBetPlanSnapshot construction
```

The loader rejects multiple headers, orphan bet/selection rows, race-mismatched
selection, duplicate/gapped/non-zero-start orders, empty bet selections,
malformed timestamp/hash/policy/budget, invalid type/stake/rank/selection,
duplicate bet identity, and budget overflow.  It never skips, repairs, fills
gaps, reorders IDs, coerces stake, invents cutoff/policy data, or turns corrupt
data into an empty plan.

### SimulationBetSource adapter and race-entry resolver

The later adapter keeps the existing `SimulationBetSource.load_bets()` API:

```python
class PersistedSimulationBetSource:
    def __init__(
        self,
        *,
        snapshot_source: SimulationBetPlanSnapshotSource,
        run_context: SimulationRunContext,
    ) -> None:
        ...
```

It can construct the identity entirely from existing objects: `run_id` from
`SimulationRunContext`, race/cutoff from `SimulationRaceInput`, and strategy ID
plus hash from `StrategyIdentity`.  A missing snapshot is fail-closed, not
`()`; only a stored empty snapshot returns empty bets.  No existing Source
signature gains a run ID.

### Phase 4C-2d3b1e0: Race-entry source and concrete Resolver design

This subsection supersedes the earlier design-only `load_race_entry_ids()`
proposal.  It fixes the concrete boundary required before a SQLite source or a
Resolver implementation is written.

#### Established identities and existing APIs

`BetRecommendation.horse_ids` is produced from the `horse_id` values carried
by `ValueEvaluation` and `Prediction`; `BetGenerator` preserves those values
for single-horse recommendations and uses them to form combinations.  The
normal CLI prediction path constructs `RacePredictionInput` by loading
`Horse` rows for a race and calling `database.get_horse_id(horse)`.  That
helper looks up `horses.id` by `(horses.race_id, horses.horse_no)`.  Therefore
the current concrete origin of prediction `horse_ids` is **`horses.id`**.

`horses.id` is an SQLite `INTEGER PRIMARY KEY AUTOINCREMENT` row identifier,
not a stable horse-master ID or an externally supplied horse ID.  The legacy
`horses` table has `race_id`, `frame_no`, `horse_no`, `horse_name`,
`horse_detail_url`, jockey/trainer, odds, popularity, and weight columns.  It
has no dedicated external horse-ID column, no horse-master table, and no
declared foreign key from `horses.race_id` to `races.id`; the existing helper
and simulation migration enforce the intended race association.  `save_horse`
and `horse_exists` identify a row by `(race_id, horse_no)`, so a horse entered
in another race is represented by another `horses` row and another `horses.id`.
The same generic table and identity model is used for JRA and local data; no
separate source-specific identity model exists in current code.

The simulation persistence boundary names that same physical value
`race_entry_id`: v008 result/odds/payout selections and v009
`simulation_bet_plan_bet_selections.race_entry_id` all reference
`horses(id)`.  v009 triggers also verify that the selected row's
`horses.race_id` equals the plan race.  Thus a prediction ID and a persisted
race-entry ID currently have the same storage value, but they retain distinct
domain meanings.  The Resolver remains mandatory: it verifies race membership
and makes that conversion explicit.  It must never implement the unchecked
identity function `return tuple(horse_ids)`.

There is no existing batch API that resolves prediction horse IDs to entries.
`database.get_horse_id(Horse)` is a legacy, per-`Horse` lookup by race and
horse number, and is not a suitable Resolver/Repository contract.  Existing
odds, payout, and result repositories consume already-resolved `horses.id`
values; they do not provide this lookup.

#### Adopted source contract

Three forms were compared.  An input-position tuple makes SQL row order part
of the Source contract; a resolution-record tuple introduces an otherwise
unused domain model.  The adopted form is a mapping, which makes the
horse-to-entry association explicit and lets the Resolver reconstruct the
caller order independently of SQLite row order:

```python
class RaceEntrySource(Protocol):
    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        ...
```

The mapping means `prediction_horse_id -> race_entry_id`.  It contains an entry
only for each requested horse that belongs to `race_id`; it does not use
`None`, an empty tuple sentinel, or a synthetic identity.  A missing key is the
only Source-level representation of both an unknown horse and a horse belonging
to another race.  This avoids an extra race-existence query and does not expose
which condition occurred.  The public Resolver converts either case into the
same `ValueError("race entry selection cannot be resolved")`-class failure.

The Source may return an immutable mapping, but immutability is not required by
the Protocol: the Resolver treats it as read-only, validates it, and constructs
its own result tuple.  Mapping was selected because it validates completeness
and correspondence without trusting `IN (...)` result order.  The input-order
tuple alternative is rejected because it gives the Source unnecessary ordering
responsibility.  The record-tuple alternative is rejected because no current
consumer needs metadata beyond the two IDs.

The concrete Resolver name is fixed as:

```python
class RepositoryBackedRaceEntrySelectionResolver:
    def __init__(self, *, race_entry_source: RaceEntrySource) -> None:
        ...

    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        ...
```

It structurally satisfies the existing `RaceEntrySelectionResolver` Protocol;
neither that Protocol nor `SimulationBetPlanBuilder` changes.  The Builder
calls it once per allocation, and zero times for an empty plan.

#### Validation, error, and order contracts

The Resolver is the public domain boundary.  It accepts ordinary `Sequence`
inputs such as list or tuple, copies once to a tuple, rejects `str`, `bytes`,
`bytearray`, `Mapping`, non-Sequences, and generators, and does not mutate the
caller collection.  `race_id` and every horse ID must be a positive non-`bool`
`int`; duplicate horse IDs and an empty horse selection are rejected.  Empty
input is not a meaningful public resolution request.  This is stricter than
the Protocol type annotation but is compatible with the Builder, whose actual
allocations derive from non-empty recommendations.

The Source validates enough of the same direct input contract to be safe when
used without the Resolver: usable SQLite connection, positive non-`bool`
`race_id`, an ordinary non-empty Sequence of unique positive non-`bool` IDs,
and parameter binding.  It owns no bet-type/cardinality/canonicalization rules.
The Resolver owns the public-input validation and validates the Source response:
it must be a Mapping with exactly the requested keys, no extras, positive
non-`bool` integer values, and no duplicate race-entry values.  It then returns
`tuple(mapping[horse_id] for horse_id in requested_horse_ids)`.  It never sorts,
sets, deduplicates, or canonicalizes.  `SimulationBet` alone canonicalizes the
race-entry selection for its bet type.

Resolver public input errors and unresolved requested IDs raise `ValueError`.
Source constructor/direct input or connection-condition errors raise existing
`RepositoryValidationError`; malformed or contradictory rows/source output
raise existing `RepositoryDataIntegrityError`; existing repository exceptions
are propagated unchanged by the Resolver.  Unexpected SQLite operational
errors are not broadly wrapped.  No new exception type is introduced.

For the current SQL query, duplicate source rows for one requested ID are
structurally impossible because `horses.id` is an `INTEGER PRIMARY KEY`; the
Source nevertheless fail-closes with `RepositoryDataIntegrityError` if its
fetched rows or constructed mapping violate uniqueness or type expectations.
Duplicate `horse_no` rows are not used as this lookup key and do not alter the
contract.

#### SQLite source, query, and transaction policy

The concrete source is named `SQLiteRaceEntrySource` and is placed at
`scripts/simulation/repositories/sqlite_race_entry_source.py`:

```python
class SQLiteRaceEntrySource:
    def __init__(self, *, connection: sqlite3.Connection) -> None:
        ...
```

It retains the injected `sqlite3.Connection` object, never closes it, creates
no schema or migrations, changes no row factory or isolation level, and follows
the existing connection-injected simulation repositories by enabling/verifying
foreign keys at construction.  It does not use `database/keiba.db` or a fixed
path.  A read operation neither begins, commits, nor rolls back a transaction;
an active caller read transaction is allowed, matching existing load behavior.

One Resolver invocation performs one parameter-bound batch query for its whole
selection, conceptually:

```sql
SELECT h.id AS prediction_horse_id, h.id AS race_entry_id
FROM horses AS h
WHERE h.race_id = ?
  AND h.id IN (?, ?, ...)
```

Both selected columns are formally `horses.id` in the current schema; retaining
both aliases documents the conversion boundary.  SQLite row order is ignored
while constructing the mapping.  No separate `races` lookup is made: a
nonexistent race and a missing/wrong-race horse leave requested keys unresolved
and fail closed at the Resolver.  Current supported bet selections contain at
most three horses, so SQLite parameter limits do not require chunking.

This baseline prevents horse-by-horse N+1 queries, but it does **not** promise
one query for an entire plan.  Multiple allocations produce multiple Resolver
calls and therefore multiple batch queries.  A plan-wide query needs an
explicit future Protocol/Builder change.  The first implementation has no
cache: global, module-level, persistent, connection-spanning, and incomplete
race-only caches are prohibited.  A measured, explicitly scoped per-instance
or per-race cache can only be designed later.

#### Placement, imports, composition, and next phases

`RaceEntrySource` is a simulation boundary Protocol and belongs in
`scripts/simulation/race_entry_source.py`, alongside the existing
`selection_resolver.py` Protocol rather than in legacy repository interfaces.
`RepositoryBackedRaceEntrySelectionResolver` belongs in
`scripts/simulation/repository_backed_selection_resolver.py`.  It imports only
the two Protocol modules.  `SQLiteRaceEntrySource` imports the Source Protocol,
SQLite, and existing repository errors; it does not import Builder, prediction,
Pipeline, Snapshot Repository, or the Resolver.  Concrete modules are imported
directly rather than exported through `scripts.simulation.repositories.__init__`
if an export would create a cycle, following the Snapshot Repository precedent.

The future composition root is only:

```python
source = SQLiteRaceEntrySource(connection=connection)
resolver = RepositoryBackedRaceEntrySelectionResolver(race_entry_source=source)
builder = SimulationBetPlanBuilder(selection_resolver=resolver)
```

No composition is implemented in this phase.  The remaining work is deliberately
split into `Phase 4C-2d3b1e1` (Source Protocol), `1e2` (SQLite Source), `1e3`
(Repository-backed Resolver), `1f` (PersistedSimulationBetSource adapter), and
`1g` (Builder/Repository/Executor composition tests).  The identity origin,
mapping column, complete Source API, missing representation, validation/error
split, ordering, query, cache, transaction, placement, and import decisions
are now fixed: **Phase 4C-2d3b1e1 may proceed.**

### Follow-up phases

```text
Phase 4C-2d3b1b  Snapshot Source and Repository Protocols
Phase 4C-2d3b1c  v009 SQLite schema and migration tests
Phase 4C-2d3b1d  SQLite SimulationBetPlanSnapshot Repository
Phase 4C-2d3b1e0 RaceEntrySource and concrete Resolver boundary design
Phase 4C-2d3b1e1 RaceEntrySource Protocol contract
Phase 4C-2d3b1e2 SQLite RaceEntrySource implementation
Phase 4C-2d3b1e3 Repository-backed Resolver implementation
Phase 4C-2d3b1f  PersistedSimulationBetSource adapter
Phase 4C-2d3b1g  Builder-to-Repository composition and integration tests
```

Migration and repository tests use temporary or `:memory:` databases.
`database/keiba.db` is never committed, restored, deleted, or used as a test
fixture.  Concrete SQL, Resolver implementation, composition-root wiring,
persistence timing, Pipeline, and CLI remain deferred.

### SimulationRaceInput

```python
@dataclass(frozen=True)
class SimulationRaceInput:
    race_id: int
    target_race_date: date
    scheduled_start_at: datetime
    information_cutoff: datetime
    pipeline_input: RacePredictionInput
    input_snapshot_audit: InputSnapshotAudit
```

制約は以下のとおり。

- `information_cutoff <= scheduled_start_at`
- 予想・購入処理順は `scheduled_start_at, race_id` の昇順
- 最大ドローダウン用の精算順は `settled_at, race_id` の昇順
- `input_snapshot_audit` はデータセット識別子、取得時刻、情報源、各入力の `available_at` / `observed_at` を保持する

初期実装から次を必須検証とする。

1. 各過去走について `past_race.race_date < target_race_date` であること。
2. 出走情報、過去走、オッズ、Strategyに渡す入力のすべてで `available_at` または `observed_at <= information_cutoff` であること。
3. 対象レースの確定着順、払戻、確定後オッズを予想・候補生成・戦略選定へ渡さないこと。
4. 欠損した当時のオッズを後日取得値で補完しないこと。

上記の検証に失敗した場合は `SimulationValidationError` とする。該当のStrategy・レースは `ERROR` または除外結果として記録し、正式ROIの分母・分子へ含めない。現行データに時点情報がなく検証不能な場合、そのデータセットは正式ROI検証に使用しない。

### InputSnapshotAudit と監査明細

```python
@dataclass(frozen=True)
class InputAuditEntry:
    input_type: str
    source: str
    source_id: str
    available_at: datetime | None
    observed_at: datetime | None
    race_entry_id: int | None

@dataclass(frozen=True)
class InputSnapshotAudit:
    dataset_id: str
    source: str
    captured_at: datetime
    entries: tuple[InputAuditEntry, ...]
```

すべての日時はtimezone-awareでなければならない。`available_at` と `observed_at` のどちらもない監査明細、または `race_entry_id` 変換に失敗した外部結果・払戻明細はFail Closedで拒否する。

## ファイル構成案

```text
scripts/
  simulation/
    __init__.py
    models.py                 # 入力、購入、結果、集計、監査モデル
    simulator.py              # Simulator
    providers/                # RawデータをRepository境界モデルへ変換するProvider契約
    database_providers.py     # SQLite実装（後続）
    validation.py             # 時点・ID・券種のFail Closed検証
    metrics.py                # 集計・最大ドローダウン
  cli/
    run_simulation.py         # 過去検証CLI（後続）
tests/
  test_simulator.py
  test_simulation_validation.py
  test_simulation_metrics.py
  test_simulation_providers.py
  test_simulation_migrations.py
  test_run_simulation_cli.py
```

`prediction` パッケージの評価・候補・戦略モジュールは変更せず、シミュレーション固有の責務を `simulation` パッケージに閉じ込める。

## 主要モデル

### StrategyIdentity

同一のStrategyクラスに異なる設定を適用した実行を区別する。

```python
@dataclass(frozen=True)
class StrategyIdentity:
    strategy_id: str
    strategy_name: str
    strategy_config: StrategyConfig
    strategy_config_hash: str
```

- `strategy_name` はStrategyクラス名または人間向け名称。
- `strategy_id` は `strategy_name` と `strategy_config_hash` から生成する安定識別子。任意の明示IDを許す場合も、設定ハッシュは必ず保持する。
- `strategy_config_hash` は、StrategyConfigを決定的にシリアライズしてSHA-256を計算する。
- 決定的シリアライズは、省略されたデフォルト値を展開した完全な設定、設定スキーマバージョン、列挙値を文字列へ変換した値、ソート済み配列化した集合を含め、キーをソートしたUTF-8 JSON（空白なし）とする。ハッシュ対象に実行日時や環境依存値を含めない。
- 同じ意味の設定（既定値の省略と明示を含む）が同じハッシュになることをテストする。

### SimulationBet

1Strategy・1レース内で計上する購入点。

```python
@dataclass(frozen=True)
class SimulationBet:
    race_id: int
    strategy_id: str
    bet_type: str
    race_entry_ids: tuple[int, ...]
    stake: int
    recommendation_rank: int
    placed_at_cutoff: datetime
```

- `stake` は正の100円倍数のみ許可する。
- `race_entry_ids` は券種の必要件数・重複なし・昇順正規化を検証する。
- 監査用に候補順位・設定ハッシュ・予測スコアを別明細へ保持してよいが、精算時に書き換えない。

### SettlementStatus

```python
class SettlementStatus(str, Enum):
    SETTLED = "settled"      # 必要な結果・払戻表が完全で、購入を精算済み
    NO_BET = "no_bet"        # Strategyが購入候補を選ばなかった
    UNSETTLED = "unsettled"  # 払戻・結果が未取得または不完全
    VOID = "void"            # 取消・返還・不成立等で精算仕様が未対応
    ERROR = "error"          # 時点検証・Provider・実行エラー
    UNSUPPORTED = "unsupported"  # 券種または精算仕様が未対応
```

### SimulationResult

必ず**1Strategy・1レース単位**で記録する。1購入単位でも複数Strategy横断でもない。

```python
@dataclass(frozen=True)
class SimulationResult:
    race_id: int
    strategy_id: str
    bets: tuple[SimulationBet, ...]
    settlement_status: SettlementStatus
    exclusion_reason: str | None
    planned_investment: int
    settled_investment: int | None
    payout: int | None
    profit: int | None
    hit_bet_count: int
    settled_at: datetime | None
    by_bet_type: Mapping[str, BetTypeSummary]
```

- `planned_investment` は生成済み買い目の合計であり、全状態で監査可能とする。`NO_BET` は必ず0。
- `SETTLED` の場合のみ `settled_investment`、`payout`、`profit` を整数で保持し、ROI集計へ含める。
- `UNSETTLED`、`VOID`、`ERROR`、`UNSUPPORTED` は精算金額をすべて `None` とする。不明な払戻を0円として保存しない。
- `NO_BET` は `planned_investment=0`、精算金額は0ではなく `None` とし、ROIの購入分母へ含めない。
- `UNSETTLED` は必要な結果または払戻表が未取得・不完全であることを表す。
- 複数券種を購入し、1券種でも必要な払戻表が不完全なら、初期方針ではレース全体を `UNSETTLED` としてROI集計から除外する。部分精算は行わない。
- `VOID` と `ERROR` は原因を `exclusion_reason` に必ず記録する。
- `by_bet_type` は `BetTypeSummary` を券種キーで保持する不変Mappingであり、原子評価の払戻status・照合明細・odds等は保持しない。
- `SETTLED` では `by_bet_type` が購入券種集合と完全一致し、各券種の生成数・精算数・投資額と全体の `bets`／`planned_investment` に一致する。券種別の的中数・投資額・払戻額・収支の合計も、結果全体の値と一致する。
- `NO_BET` の `by_bet_type` は空とする。購入がある `UNSETTLED`、`VOID`、`ERROR`、`UNSUPPORTED` は購入券種ごとの件数を保持するが、券種別の精算数・的中数・投資額・払戻額・収支はすべて0、率は `None` とする。購入がない `ERROR` は空Mappingを許可し、空の `UNSETTLED`、`VOID`、`UNSUPPORTED` は許可しない。
- `SimulationSummary` は各 `SimulationResult.by_bet_type` を再集計できる。`SimulationResult` 自身は集計済みの券種別値だけを保持し、原子評価の詳細を再構築しない。

### BetTypeSummary

券種別成績を表す正式な主要モデル。`SimulationResult` と `SimulationSummary` の双方で再利用する。

```python
@dataclass(frozen=True)
class BetTypeSummary:
    bet_type: str
    bet_count: int
    settled_bet_count: int
    hit_bet_count: int
    investment: int
    payout: int
    profit: int
    roi: Decimal | None
    bet_hit_rate: Decimal | None
```

`bet_count` は生成した全買い目数、`settled_bet_count` は正常精算された買い目数、`hit_bet_count` は精算済み買い目のうち winning となった点数とする。`bet_hit_rate` の分母は `settled_bet_count` とする。

初期対応券種は `単勝`、`馬連`、`ワイド`、`3連複` とし、各 `SimulationBet` は1つの券種・1つの正規化済み選択組合せを表す原子的な買い目とする。

### SimulationSummary

1つの `StrategyIdentity` と対象期間に対する集計。

```python
@dataclass(frozen=True)
class SimulationSummary:
    strategy_id: str
    strategy_name: str
    strategy_config_hash: str
    race_count: int
    settled_race_count: int
    unsettled_race_count: int
    no_bet_race_count: int
    void_race_count: int
    error_race_count: int
    unsupported_race_count: int
    bet_count: int
    settled_bet_count: int
    settled_purchase_race_count: int
    hit_bet_count: int
    hit_race_count: int
    investment: int
    payout: int
    profit: int
    roi: Decimal | None
    bet_hit_rate: Decimal | None
    race_hit_rate: Decimal | None
    by_bet_type: Mapping[str, BetTypeSummary]
    maximum_drawdown: int
```

`SimulationSummary` は、strategy identityを明示入力として受け取る純粋な `_build_simulation_summary()` が `SimulationResult` 列から構築する。

```python
def _build_simulation_summary(
    *,
    strategy_id: str,
    strategy_name: str,
    strategy_config_hash: str,
    results: Sequence[SimulationResult],
) -> SimulationSummary:
    ...
```

`target_race_count` は実モデルの `race_count` に対応し、全statusの結果数とする。`settled_purchase_race_count` は `SETTLED` かつ買い目を持つレース数、`bet_count` は全statusの `bets` 件数、`settled_bet_count`・金額・ROI・的中率は `SETTLED` のみを集計対象とする。

率はすべて `Decimal | None` で、ROIは `payout / investment × 100`、券種別的中率は `hit_bet_count / settled_bet_count × 100`、レース的中率は `hit_race_count / settled_purchase_race_count × 100` とする。分母が0なら `None` とし、floatへ変換しない。

最大ドローダウンは `SETTLED` 結果だけを新しい列へ抽出して `(settled_at, race_id)` 昇順で並べ、初期peakを0として累積収支の最大下落幅を計算する。NO_BETと非精算statusは含めず、入力列をin-placeで並べ替えない。`by_bet_type` は各結果の同名Mappingを券種ごとに再集計し、全体の件数・金額・収支と一致しなければならない。原子評価の照合明細はSummaryへ保持しない。

### SimulationRunContext、SimulationRunMetadata と SimulationReport

複数Strategy比較とレース別明細を保持する実行結果モデル。

```python
@dataclass(frozen=True)
class SimulationRunContext:
    run_id: str
    dataset_id: str
    started_at: datetime
    target_commit_id: str

@dataclass(frozen=True)
class SimulationRunMetadata:
    run_id: str
    dataset_id: str
    started_at: datetime
    completed_at: datetime
    target_commit_id: str

@dataclass(frozen=True)
class SimulationReport:
    metadata: SimulationRunMetadata
    strategy_identities: tuple[StrategyIdentity, ...]
    race_results: tuple[SimulationResult, ...]
    strategy_summaries: Mapping[str, SimulationSummary]
    official_roi_valid: bool
    validation_errors: tuple[SimulationValidationError, ...]
```

`SimulationRunContext` は入力専用であり、`run_id`、`dataset_id`、`started_at`、`target_commit_id`を持つ。`completed_at`、stake、対応券種、対象期間は現行正式モデルのフィールドではない。`SimulationRunMetadata` は実行完了後の`completed_at`を追加する。`SimulationReport` は全Strategy・全レースの明細を保持する設計上の出力コンテナである。

## Simulatorの入出力と既存パイプライン連携

### 実行境界（第4C-2b1 / 2b2）

`Simulator` は一つの `StrategyIdentity` と、一レースを最終 `SimulationResult` に変換する注入済みexecutorを保持する。`run()` は全 `SimulationRaceInput` を実行前に検証した後、入力順のままexecutorを各レースに一回だけ呼び、全結果を `_build_simulation_summary()` へ一回だけ渡す。これにより、Provider・Repository・外部I/Oを `Simulator` へ直接持ち込まない。

```python
class RaceSimulationExecutor(Protocol):
    def __call__(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> SimulationResult:
        ...


class Simulator:
    def __init__(
        self,
        *,
        strategy_identity: StrategyIdentity,
        race_executor: RaceSimulationExecutor,
    ) -> None:
        ...
```

constructorは`StrategyIdentity`を再生成・分解・補正せず、同一のimmutable objectを保持する。`race_executor`はcallableであることだけをFail Closedで検証し、signature検査・試験実行・wrapper化を行わない。`run()`はexecutorを各`SimulationRaceInput`に一回だけ呼び、保持した`strategy_id`、`strategy_name`、`strategy_config_hash`を`_build_simulation_summary()`へ明示的に渡す。外部取得・保存・CLI出力はさらに上位層の責務とする。

## Provider接続境界（第4C-2c1）

### Simulatorは変更しない

Providerを`Simulator`へ直接注入しない。`Simulator.__init__`、`Simulator.run()`、`RaceSimulationExecutor`、`SimulationRaceInput`、`SimulationResult`、`SimulationSummary`、`models.py`の契約は変更しない。`Simulator`は注入された`RaceSimulationExecutor`だけを認識し、Provider・Repository・SQLite・DB・HTTP・network・retry・logging・現在時刻取得へ依存しない。

### 既存Providerは変換Providerである

既存の`RaceResultProvider`、`OddsSnapshotProvider`、`PayoutProvider`は、Rawモデル、`ProviderContext`、`RaceEntryUniverse`からRepository境界モデルを構築する変換Providerである。取得・DB照会・外部I/Oを行うProviderではない。

```text
Rawデータ
  → 変換Provider
  → PersistedRaceResult / OddsSnapshotBatch / PayoutPublication
```

これらのProviderへ、DB接続、Repository実装、SQLite、HTTP、network、retry、logging、現在時刻取得を追加しない。Phase 4C-2cの最小接続対象は確定結果と払戻であり、`OddsSnapshotProvider`は予測入力・EVの後続責務としてこのadapterへ追加しない。

### 現行型・Result builderの実装可能性

次表は、Provider接続executorが必要とする情報を現行型が実際に保持するかを示す。存在しないフィールドを補完・推測しない。

| 型 | 実在フィールドと利用可能な情報 | Provider接続上の不足または注意点 |
| --- | --- | --- |
| `SimulationRaceInput` | `race_id`、`scheduled_start_at`、`information_cutoff`、`pipeline_input`、`input_snapshot_audit` | 購入内容、購入券種、`strategy_id`を保持しない。`pipeline_input`から`SimulationBet`を復元する契約も存在しない。 |
| `SimulationBet` | `race_id`、`strategy_id`、`bet_type`、正規化済み`race_entry_ids`、`stake`、`recommendation_rank`、`placed_at_cutoff` | 購入券種の正規情報源になれるが、`SimulationRaceInput`から取得できない。 |
| `RawRaceResult` | `declared_status`、`finalized_at`、`entries` | `race_id`、監査時刻、sourceを持たない。`ProviderContext`と`RaceEntryUniverse`が必要。 |
| `RawPayoutPublication` | `bet_type`、`finalized_at`、`entries`、3つの完全性フラグ | 一券種一publicationであり、`race_id`、監査時刻、sourceを持たない。券種ごとの`ProviderContext`と`RaceEntryUniverse`が必要。 |
| `ProviderContext` | `race_id`、`observed_at`、`source`、`source_url`、`captured_at`、`information_cutoff`、任意の`bet_type` | 結果用と券種ごとの払戻用を区別して保持する必要がある。ここでの`information_cutoff`はRaw取得・変換時のSource境界であり、`SimulationRaceInput.information_cutoff`とは別の時点である。 |
| `RaceEntryUniverse` | `race_id`、active/excluded/cancelledのentry ID集合、`horse_no_to_race_entry_id` | 結果・払戻の両Providerへ共通に渡せる。`race_id`は入力と一致しなければならない。 |
| `PersistedRaceResult` | `race_id`、`result_status`、`finalized_at`、`observed_at`、`entries` | COMPLETEなら`finalized_at`が必須。結果確定時刻の正式な取得元になる。 |
| `PayoutPublication` | `race_id`、`bet_type`、`finalized_at`、`observed_at`、`is_complete`、`entries` | COMPLETEなら`finalized_at`が必須。必要券種ごとの払戻確定時刻の正式な取得元になる。 |
| `ProviderBuildResult` | `value`と`CompletenessResult` | 結果・払戻を変換した後、値と完全性を一組で保持できる。 |
| `CompletenessResult` | `status`、件数、missing/unexpected/duplicate keys、reasons | `COMPLETE`、`INCOMPLETE`、`INVALID`、`UNSUPPORTED`をResult builderへ渡す事実になる。 |
| `_build_simulation_result_for_race(...)` | `race_id`、`strategy_id`、`bets`、`publications_by_bet_type`、`settled_at`、完全性status、結果status、払戻status、欠損券種、結果欠損、`error_reason` | `RaceSettlementData`とexecutorが供給する値で構成する。`SimulationRaceInput`単独から購入内容やstrategy identityは構成できない。 |

したがって、Raw Provider経路の`ProviderBackedRaceSimulationExecutor`は`RaceSettlementData`を供給するSourceと組み合わせて使用する。一方、既存Repositoryが返すPersistedモデルだけから同bundleを構成することはできない。購入内容、Raw監査情報、Universe、時点選択の取得境界はRepository経路で別途設計する。

### Source戻り値bundleとRaceSettlementSource

購入内容とRawデータを別々に取得すると、同一レース・同一時点・同一購入計画であることを保証できない。このため、新規のimmutable bundleを導入する。仮称は`RaceSettlementData`、配置候補は新規の`scripts/simulation/settlement.py`である。既存の変換Provider契約を保つため、`providers/interfaces.py`には追加しない。

```python
@dataclass(frozen=True)
class RaceSettlementData:
    race_id: int
    bets: tuple[SimulationBet, ...]
    raw_race_result: RawRaceResult | None
    race_result_context: ProviderContext | None
    raw_payout_publications_by_bet_type: Mapping[str, RawPayoutPublication]
    payout_contexts_by_bet_type: Mapping[str, ProviderContext]
    universe: RaceEntryUniverse
```

bundleはtupleと不変Mappingへfreezeし、Repository、DB接続、SQLite実装、外部clientを保持しない。validation責務は次のとおりとする。

- `race_id`、`universe.race_id`、呼出し元`SimulationRaceInput.race_id`が一致する。
- `bets`の全要素は`SimulationBet`であり、各`race_id`がbundleの`race_id`と一致する。
- `raw_race_result`と`race_result_context`は両方存在するか両方`None`である。存在時のcontextは対象`race_id`と一致する。
- 払戻Mappingのkeyは正規化済み券種で、各`RawPayoutPublication.bet_type`と一致する。各券種に対応する`ProviderContext`が存在し、対象`race_id`と一致する。contextの`bet_type`が存在する場合はMapping keyと一致する。
- bundle内の結果・払戻Contextは同じRaw取得・変換時点の`information_cutoff`を共有する。ただし、その値を`SimulationRaceInput.information_cutoff`と一致させてはならない。
- 払戻Mappingに存在しない購入券種は欠損として表し、空の偽publicationや推測データで補完しない。

`RaceSettlementSource`の次フェーズ実装候補は以下である。

```python
class RaceSettlementSource(Protocol):
    def load_settlement_data(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> RaceSettlementData:
        ...
```

SourceはRaw結果、券種単位のRaw払戻、各ProviderContext、Universe、購入内容を同一レース・同一時点のデータとして供給する取得境界である。DB取得・外部取得の実装を持つことは許容するが、変換Providerへその依存を移さない。

### ProviderBackedRaceSimulationExecutorのAPI

`SimulationRaceInput`には`strategy_id`がないため、NO_BETを含む全Result builder呼出しに必要なidentityをexecutor自身が保持する。composition rootは、`Simulator`とexecutorへ同一の`StrategyIdentity` objectを渡す。

```python
class ProviderBackedRaceSimulationExecutor:
    def __init__(
        self,
        *,
        strategy_identity: StrategyIdentity,
        settlement_source: RaceSettlementSource,
        race_result_provider: RaceResultProvider,
        payout_provider: PayoutProvider,
    ) -> None:
        ...

    def __call__(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> SimulationResult:
        ...
```

Result builderは追加注入しない。`_build_simulation_result_for_race(...)`は現在の正式な一レース組立境界であり、module-level helperを直接一回だけ呼ぶ。Callable注入は、既存のprivate helperを新たな公開契約へ昇格させ、責務とテスト境界を不必要に広げるため採用しない。

### 購入券種と購入なしの処理

購入対象は`RaceSettlementData.bets`である。`SimulationRaceInput`単独からは取得できない。必要券種は、入力順を保つ最初の出現順で次のように抽出する。

```text
tuple(dict.fromkeys(bet.bet_type for bet in bets))
```

`SimulationBet`は正規化済みの対応券種しか保持できない。Sourceが`SimulationBet`以外、対象外券種、別race、またはexecutorの`strategy_identity.strategy_id`と異なるbetを返した場合はfail-closedで例外を伝播し、Providerを呼ばない。券種の順序はpublication Mappingの意味には影響しないが、Provider呼出しと監査を決定的にするため最初の出現順を維持する。

`bets == ()`は購入なしである。ただし、購入内容はSource bundleからしか得られないため、まずSourceを一回呼ぶ。空であると確定した後は結果・払戻Providerを呼ばず、`_build_simulation_result_for_race(...)`へ空betsを一回だけ渡してNO_BETを生成する。Source呼出し自体を省略する契約にはしない。

現行helperはNO_BET分岐で`settled_at`を使わない一方、引数型は非optionalな`datetime`である。意味のない時刻を渡さないため、実装前にhelperの`settled_at`を`datetime | None`へ変更し、SETTLED分岐だけでtimezone-awareな値を必須検証する最小修正が必要である。

### 完全性状態と現行Result builderの制約

executorはSource／Provider例外をResultへ変換せず、そのまま伝播する。partial settlementは常に禁止する。Providerが正常に`ProviderBuildResult`を返した場合の現行Result builderの実際の挙動は次表のとおりである。

| 条件 | Result builderを呼ぶか | 非精算Resultへ変換 | 例外を伝播 | 部分精算 | 現行契約上の結論 |
| --- | --- | --- | --- | --- | --- |
| result COMPLETE、必要payout全てCOMPLETE | 呼ぶ | しない | 評価・時刻が正常ならしない | 不可 | SETTLED可能。 |
| result INCOMPLETE | 条件付きで呼ぶ | 評価成功時のみUNSETTLED | 必要publication欠損・評価不能時はする | 不可 | 非精算判定より評価が先のため、確実には表現不能。 |
| result INVALID | 条件付きで呼ぶ | 評価成功時のみERROR | 評価不能時はする | 不可 | 同上。 |
| result UNSUPPORTED | 条件付きで呼ぶ | 評価成功時のみUNSUPPORTED | 評価不能時はする | 不可 | 同上。 |
| 必要payoutがINCOMPLETE | 条件付きで呼ぶ | 全betが評価可能な場合のみUNSETTLED | 未一致betは評価例外を伝播 | 不可 | 不完全払戻の不的中と欠損を安全に区別できない。 |
| 必要payoutがINVALID | 条件付きで呼ぶ | 評価成功時のみERROR | 評価不能時はする | 不可 | 同上。 |
| 必要payoutがUNSUPPORTED | 条件付きで呼ぶ | 評価成功時のみUNSUPPORTED | 購入selectionがunsupported recordに一致すると評価例外を伝播 | 不可 | 同上。 |
| 必要な払戻publicationがない | 呼ぶと評価前に失敗 | できない | する | 不可 | publication key集合の完全一致を評価helperが要求するため、現行モデルではUNSETTLEDを表現不能。 |
| 未購入券種だけの払戻がない | 呼ぶ | しない | しない | 不可 | 必要券種集合に含めないため影響しない。 |
| Source例外 | 呼ばない | しない | する | 不可 | 例外をそのまま伝播。 |
| Provider例外 | 呼ばない | しない | する | 不可 | 例外をそのまま伝播。 |
| Result builder例外 | 呼んだ後に返さない | しない | する | 不可 | 例外をそのまま伝播。 |

`_build_simulation_result_for_race(...)`は、空betsでNO_BETを返し、それ以外は非精算statusを評価より先に判定し、SETTLED時だけ`_evaluate_simulation_race_bets(...)`を呼ぶ。`settled_at`は`datetime | None`であり、SETTLED分岐だけがtimezone-awareな値を必須とする。この前提修正はPhase 4C-2c2の実装前に完了している。

### `settled_at`の実装可能性

正式な確定時刻は変換後の値から取得する。

- 結果: `PersistedRaceResult.finalized_at`
- 必要券種の払戻: 各`PayoutPublication.finalized_at`

COMPLETEな`PersistedRaceResult`とCOMPLETEな`PayoutPublication`は、いずれも`finalized_at`を必須とする。したがって、全ての必要情報がCOMPLETEであるSETTLED候補では次を決定できる。

```text
max(
    persisted_race_result.finalized_at,
    required_payout_publication.finalized_at for each required bet type,
)
```

一つでも欠ける場合は`settled_at`を決定できない。`datetime.now()`、`observed_at`、`captured_at`、`information_cutoff`で代用しない。欠損時刻の追加先はSourceではなく、既に正式フィールドを持つ変換後の`PersistedRaceResult`／`PayoutPublication`を構築するProvider入力・変換境界である。

### Result builder引数の構成

前提フェーズ後、`_build_simulation_result_for_race(...)`の各引数は次の実在値から構成する。

| Result builder引数 | 構成元 |
| --- | --- |
| `race_id` | `race_input.race_id`。bundleの`race_id`およびUniverseの`race_id`と一致を確認する。 |
| `strategy_id` | executorへ注入された`strategy_identity.strategy_id`。bundleの全betとも一致を確認する。 |
| `bets` | `RaceSettlementData.bets`。 |
| `publications_by_bet_type` | 正常に変換できた必要券種の各`ProviderBuildResult[PayoutPublication].value`。欠損券種を偽publicationで補完しない。 |
| `settled_at` | SETTLED候補でのみ、結果と必要払戻の`finalized_at`の最大値。その他は`None`。 |
| `completeness_statuses` | 存在する結果・必要払戻の各`ProviderBuildResult.completeness.status`。 |
| `race_result_status` | 結果が存在する場合は`ProviderBuildResult[PersistedRaceResult].value.result_status`、結果未取得時は`None`。 |
| `payout_statuses` | 必要券種の各変換済み`PayoutPublication.entries`に含まれる`PayoutRecord.payout_status`。 |
| `missing_payout_bet_types` | 必要券種のうち、Raw publicationまたは対応contextが存在しない券種。 |
| `missing_race_result` | `raw_race_result`と`race_result_context`がともに`None`であること。 |
| `error_reason` | Source／Provider／builder例外は伝播する方針のため、通常経路では常に`None`。 |

この対応表のうち、空または欠損の`publications_by_bet_type`を安全に受け入れるためには、前節で記したResult builderの判定順変更が必要である。

### 1レースの正式処理フロー

購入ありの場合は、次の順序とする。

```text
race_input受付
→ RaceSettlementSourceを一回呼ぶ
→ RaceSettlementDataとrace_input、strategy_identityを検証
→ betsから必要券種を最初の出現順で決定
→ RaceResultProviderで結果を一回変換（結果Rawが存在する場合）
→ 必要券種ごとにPayoutProviderで払戻を一回変換（Rawが存在する場合）
→ publication Mapping、完全性status、結果status、払戻status、欠損券種を構成
→ SETTLED候補だけでsettled_atを決定
→ _build_simulation_result_for_race(...)を一回呼ぶ
→ SimulationResult返却
```

購入なしの場合は次の順序とする。

```text
race_input受付
→ RaceSettlementSourceを一回呼ぶ
→ RaceSettlementDataとstrategy_identityを検証
→ betsが空であることを確認
→ ResultProviderとPayoutProviderを呼ばない
→ _build_simulation_result_for_race(...)を一回呼ぶ
→ NO_BET SimulationResult返却
```

この購入なしフローには、上記の`settled_at: datetime | None`への最小変更が前提となる。

### 実装可能性の結論

Raw Provider経路の契約と`ProviderBackedRaceSimulationExecutor`は実装済みである。残る実装可能性の課題は、具体的なRaw SourceまたはRepositoryからのPersisted経路が購入bet・結果・払戻を安全に供給する境界である。詳細は次節のPrediction cutoffとSettlement pathで定義する。Odds、Summary builder、`Simulator.run()`、`models.py`の契約はこの境界設計では変更しない。

## Prediction cutoffとSettlement path（Phase 4C-2d1a）

この節は、上記Provider接続境界における時点の意味と、Raw Provider経路／Persisted Repository経路を正式に分離する。`SimulationRaceInput.information_cutoff`と`ProviderContext.information_cutoff`を同一視する従来の記述は、この節の決定で置き換える。

### 予測cutoffと精算cutoffは別境界である

`SimulationRaceInput.information_cutoff`は予測・購入判断の情報上限である。能力、展開、騎手、馬場・コース、odds snapshot、bet生成、strategy判断には、この時点以後の情報を使わない。

確定着順、結果status、払戻、結果の`finalized_at`、払戻の`finalized_at`はレース終了後の精算事実であり、予測cutoffで制限しない。したがって、精算に用いる値の`observed_at > SimulationRaceInput.information_cutoff`は通常の正常状態である。未来情報遮断とは、精算事実を予測・bet生成へ逆流させないことであり、精算処理がレース後の確定事実を使うことを禁止する意味ではない。

`ProviderContext.information_cutoff`は、Raw結果／Raw払戻を取得して変換したSource側の情報上限である。ProviderContext自身の`observed_at <= information_cutoff`および`captured_at <= information_cutoff`という契約は維持するが、そのcutoffは通常レース終了後であり、`SimulationRaceInput.information_cutoff`との一致を要求しない。

このため、次の整合性は維持する。

- bundle、Provider出力、`SimulationRaceInput`の`race_id`整合性。
- bundleのbetとexecutorの`StrategyIdentity.strategy_id`整合性。
- bundle内部の結果・払戻ProviderContext同士のRaw取得・変換境界としての整合性。
- Provider出力の型、監査時刻、券種、確定時刻の整合性。

一方、`ProviderBackedRaceSimulationExecutor`が現在行う、Provider Context cutoffまたはProvider出力の`observed_at`を`race_input.information_cutoff`と比較して拒否する検証は正式設計と矛盾する。次のコードフェーズで廃止する。精算情報が予測cutoffより後でも拒否せず、ProviderContext自身の時点契約だけを検証する。

### Raw Provider経路

Raw Provider経路は、取得直後の監査可能なRawデータを既存Providerで一度だけ変換する経路である。

```text
RawRaceResult / RawPayoutPublication
  → RaceResultProvider / PayoutProvider
  → PersistedRaceResult / PayoutPublication
  → SimulationResult
```

使用クラスは`ProviderBackedRaceSimulationExecutor`である。この経路はRaw ingestion接続、Raw fixtureを用いる統合試験、Provider変換契約を含む精算に使用する。RawからPersistedへの変換・完全性判定はこの経路で一度だけ実行する。

### Persisted Repository経路

Repositoryから読み出した正規化済みデータは、Rawへ逆変換しない別経路で精算する。

```text
PersistedRaceResult / PayoutPublication
  → SimulationResult
```

この経路では、PersistedモデルからRawモデルへの逆変換、RaceResultProvider／PayoutProviderの再実行、完全性判定の二重実行、原文statusの推測復元、欠落したRaw監査情報の補完を行わない。これらはRaw監査情報を失わせ、変換責務を二重化するため禁止する。

### Persisted settlement bundleとSource

Persisted経路のimmutable bundle候補は`settlement.py`に配置する。実在型のimport元は`SimulationBet`、`SimulationRaceInput`、`StrategyIdentity`が`simulation.models`、`PersistedRaceResult`と`PayoutPublication`が`simulation.repositories.interfaces`である。

```python
@dataclass(frozen=True, slots=True)
class PersistedRaceSettlementData:
    race_id: int
    bets: tuple[SimulationBet, ...]
    race_result: PersistedRaceResult | None
    payout_publications_by_bet_type: Mapping[str, PayoutPublication]
```

このbundleはRawモデル、ProviderContext、RaceEntryUniverse、Provider、Repository、DB／SQLite connection、logger、HTTP client、現在時刻生成関数を保持しない。`bets`はtupleへ固定し、Mappingは防御的コピー後のread-only Mappingへfreezeするため、元のMapping変更の影響を受けない。

validation候補は以下とする。

- `race_id`は正の非bool int。
- 全betは`SimulationBet`であり、各`bet.race_id`はbundleの`race_id`と一致する。
- `race_result`が存在するとき、その`race_id`はbundleの`race_id`と一致する。
- 払戻Mappingの全valueは`PayoutPublication`であり、各`race_id`はbundleの`race_id`と一致する。
- Mapping keyは各`PayoutPublication.bet_type`と一致する。

StrategyIdentityとの一致はbundleではなくexecutorが検証する。

```python
class PersistedRaceSettlementSource(Protocol):
    def load_settlement_data(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> PersistedRaceSettlementData:
        ...
```

このProtocolはrace inputとstrategy identityをkeyword-onlyで受ける。対象strategyのbetsと、Repositoryから読んだ正規化済み結果・必要払戻をbundleとして供給する。Rawへ戻さず、Providerを呼ばず、Repository／DBの具体実装をProtocolへ露出させない。既存の`RaceSettlementSource`はRaw Provider経路専用として維持し、名前を共有しない。

### 購入betの取得境界

既存Repositoryには`SimulationBet`取得契約も永続化schemaもない。最小の論理境界は次とする。

```python
class SimulationBetSource(Protocol):
    def load_bets(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> tuple[SimulationBet, ...]:
        ...
```

このSourceはraceとstrategyを限定し、stake、selection、bet typeを完全に復元し、正式な購入順を維持する。別race／別strategyのbetを返さず、prediction cutoff以後に新規生成されたbetを混入させない。

betをDBへ永続化するか、上位層から実行時に供給するか、prediction pipelineの出力を保持するか、購入順をどのフィールドで固定するか、bet生成時刻またはcutoffをどこに保存するかは未確定である。この節ではschemaを確定・追加しない。

### Persisted executor

Persisted経路の推奨名は`PersistedRaceSimulationExecutor`とする。`RepositoryBackedRaceSimulationExecutor`よりも、具体的なSQLite／Repository実装をexecutorから隔離し、入力がPersisted境界モデルである事実を明確に表せるためである。

```python
class PersistedRaceSimulationExecutor:
    def __init__(
        self,
        *,
        strategy_identity: StrategyIdentity,
        settlement_source: PersistedRaceSettlementSource,
    ) -> None:
        ...

    def __call__(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> SimulationResult:
        ...
```

このexecutorはSourceを一回呼び、race・strategy整合性を検証し、betsから必要券種を抽出する。Persisted結果・必要払戻を既存の`_build_simulation_result_for_race(...)`へ最大一回だけ渡し、SETTLED候補では結果と必要払戻の`finalized_at`の最大値を`settled_at`とする。Provider呼出し、Raw再構成、SQL、DB接続、Summary集計、atomic evaluatorの直接呼出し、個別Result builderの直接呼出しを行わない。

### Final settlement方針と再現性

Ver0.8のRepository経路は最終確定情報による精算を対象とする。

- `SimulationRaceInput.information_cutoff`はbet生成までにだけ使用する。
- 精算は最終の確定結果・確定払戻を使用し、予測cutoffより後の確定は正常である。
- SETTLEDでは結果および必要払戻の`finalized_at`を必須とする。
- 欠損・非確定statusはfail-closedで非精算とし、必要券種の払戻が欠ける場合は非精算とする。
- 未購入券種の払戻は不要であり、結果・払戻を予測処理へ戻さない。

結果revision／払戻revisionの時点再現、レース終了後何分で精算可能だったかの再現、correction前の結果による精算、settlement as-ofによるtime travelは今回の対象外である。現行DB snapshotが変われば再計算結果も変わり得るため、厳密な再現性にはDB snapshotまたはversion管理が必要になる。

### Repository境界の不足と責務分担

現時点で必須なのは`SimulationBetSource`、Persisted settlement bundle／Source、Raw Provider経路をRepositoryへ接続する場合の正式なRaceEntryUniverse取得境界である。Repository経路では、既存の`get_race_result(race_id)`の最終情報取得としての利用可否、券種ごとの最新complete payout取得、bet取得、strategy identityによる絞り込みを設計する。後続の検討対象はresult revision、`observed_at_lte`結果lookup、Raw監査情報保存、cancelled／excluded entry情報、source_url／captured_at保存である。

| 層 | 責務 |
| --- | --- |
| `SimulationBetSource` | race・strategy別betの取得 |
| Repository | SQLとPersistedモデル復元 |
| `PersistedRaceSettlementSource` | bet・結果・払戻を1レースbundleへ構成 |
| `PersistedRaceSimulationExecutor` | 必要券種、非精算判定、`settled_at`、Result builder接続 |
| Raw Provider | RawからPersistedモデルへの変換 |
| `ProviderBackedRaceSimulationExecutor` | Raw Provider経路のオーケストレーション |
| `Simulator` | 複数raceの順序実行とSummary一回集計 |

### 次フェーズの依存順

```text
Phase 4C-2d1b
ProviderBackedRaceSimulationExecutorのcutoff整合性修正

Phase 4C-2d1c
PersistedRaceSettlementData／PersistedRaceSettlementSource契約追加

Phase 4C-2d1d
SimulationBetSource契約追加

Phase 4C-2d1e
PersistedRaceSimulationExecutor実装

Phase 4C-2d3
必要なbet永続化／Repository境界

Phase 4C-2d2
Repository-backed Sourceの具体設計・実装

Phase 4C-2e
composition root／CLI接続
```

`PersistedRaceSimulationExecutor`はdummy Sourceを用いて`Phase 4C-2d1e`で実装・検証できる。一方、実際のRepository-backed Sourceはbetを取得できなければ構成できないため、当初案の2d2より先に2d3を置く。

### Simulation bet plan identity／変換境界（Phase 4C-2d3b0）

#### bet plan は run 単位の immutable snapshot

永続化する単位は独立したbetの集合ではなく、**一つのsimulation run・一つのrace・一つのstrategy・一つのprediction cutoff**に対応する購入計画snapshotである。正式な概念名を`SimulationBetPlanSnapshot`とする。

snapshotはinsert-onlyであり、保存後に置換・上書きしない。同じrace・strategy・prediction cutoffであっても、異なるrunで生成されたplanは別snapshotとして保存する。DB内部のsurrogate primary keyは許容するが、domain上のidentityを置き換えない。

現行の`SimulationRunContext`は次の正式フィールドを持つ。

```python
@dataclass(frozen=True)
class SimulationRunContext:
    run_id: str
    dataset_id: str
    started_at: datetime
    target_commit_id: str
```

`run_id`、`dataset_id`、`target_commit_id`は非空、`started_at`はtimezone-awareである。bet plan identityへ必須で入るrun情報は`run_id`であり、dataset、commit、開始時刻はrunの来歴として`SimulationRunContext`に保持する。新しいrun ID生成ロジックはこの境界で追加しない。

#### `SimulationBetPlanIdentity`

後続実装で追加するdomain contractは次とする。

```python
@dataclass(frozen=True, slots=True)
class SimulationBetPlanIdentity:
    run_id: str
    race_id: int
    strategy_id: str
    strategy_config_hash: str
    information_cutoff: datetime
```

validationは以下を満たす。

- `run_id`と`strategy_id`は非空の`str`。
- `race_id`は正の非bool `int`。
- `strategy_config_hash`は既存`StrategyIdentity.strategy_config_hash`と同じ、64文字の小文字SHA-256 digest。
- `information_cutoff`はtimezone-aware `datetime`。
- 呼出し側は`StrategyIdentity.strategy_id`と`strategy_config_hash`、`SimulationRaceInput.race_id`と`information_cutoff`からidentityを構成し、推測・補正しない。

後続migrationでは、この五つの複合identityにunique constraintを置く。同一run内で同一race・strategy・設定・cutoffのplanを二つ保存することは許可しない。

#### Source への run identity 供給

既存Protocolの`load_bets()`および`load_settlement_data()`の引数にrun IDを追加しない。Repository-backed Sourceをrun単位で構築し、constructorで固定する。

```python
class RepositoryBackedSimulationBetSource:
    def __init__(
        self,
        *,
        run_context: SimulationRunContext,
        bet_repository: SimulationBetRepository,
    ) -> None:
        ...
```

`run_id`だけではなく`SimulationRunContext`全体をconstructorへ注入する案を採用する。既存の不変・検証済みrun境界を保持し、Sourceがrun IDを再生成せず、将来のdataset/commit監査にも同じobjectを使えるためである。`load_bets(race_input=..., strategy_identity=...)`は、固定された`run_context.run_id`と引数のrace・strategy・cutoffから`SimulationBetPlanIdentity`を一意に構成する。

`PersistedRaceSettlementSource`の具体実装も、同一`run_context`で構築済みの`SimulationBetSource`を合成するか、同じ`run_context`をconstructor注入する。`Simulator.run()`、`RaceSimulationExecutor`、既存Source Protocolのsignatureは変更しない。

#### `SimulationBetPlanSnapshot` と空plan

```python
@dataclass(frozen=True, slots=True)
class SimulationBetPlanSnapshot:
    identity: SimulationBetPlanIdentity
    policy_identity: AllocationPolicyIdentity
    budget: BetStakeBudget
    bets: tuple[SimulationBet, ...]
```

snapshotは次を検証する。

- `identity`は`SimulationBetPlanIdentity`。
- `policy_identity`は`AllocationPolicyIdentity`。strategy config hashだけからはpolicy name/version/config hashを復元できず、空planでも使用policyの監査が必要なため保持する。
- `budget`は`BetStakeBudget`。run・raceごとの入力budget、空plan時のbudget、allocated/unallocated amountの監査のため保持する。
- `bets`は防御的にtuple化し、外部の元Sequence変更の影響を受けない。
- `str`、`bytes`、`bytearray`をbetsのSequenceとして受理しない。bet object自体はcopy・wrapせずobject identityを保持する。
- 空tupleを許可する。
- 各betの`race_id`、`strategy_id`、`placed_at_cutoff`はidentityの`race_id`、`strategy_id`、`information_cutoff`と完全一致する。
- plan内のbet identity `(bet_type, canonical race_entry_ids)` は重複不可。
- `sum(bet.stake for bet in bets) <= budget.total_amount`を必須とする。
- frozenおよびslotsとし、betの順序そのものをsnapshotの正式なpurchase orderとする。

`allocated_amount`と`unallocated_amount`はfieldとして二重保存せず、次のread-only propertyで導出する。これによりallocation監査値とbudgetの不整合を持ち込まない。

```python
@property
def allocated_amount(self) -> int:
    return sum(bet.stake for bet in self.bets)

@property
def unallocated_amount(self) -> int:
    return self.budget.total_amount - self.allocated_amount
```

`bets == ()`は、対象run・race・strategy・cutoffについて購入計画が正式に確定したが、購入betが0件だったことを表す。これはplan未生成、未保存、取得失敗とは異なる。後続schemaはbet子行が0件でもplan headerを保存しなければならない。

#### prediction cutoff、recommendation rank、purchase order

`SimulationBet.placed_at_cutoff`は実時計の購入時刻ではなく、購入判断で使用した情報上限である。snapshotでは必ず次を満たす。

```text
bet.placed_at_cutoff == snapshot.identity.information_cutoff
```

これにより、異なるprediction cutoffのplanを区別し、後から生成されたbetの混入を拒否する。保存時刻や`datetime.now()`で代用しない。実際の購入実行時刻が必要になった場合は、別フィールド・別境界として設計する。

`recommendation_rank`は候補評価順位であり、purchase orderではない。正式なpurchase orderは、`BetStrategy`が確定した`BetPlan.recommendations`のtuple順を先頭から列挙した0-based index (`0, 1, 2, ...`) とする。後続schemaではplan子行に`purchase_order INTEGER NOT NULL CHECK(purchase_order >= 0)`を保存し、plan内unique constraintと読取時の`ORDER BY purchase_order ASC`で順序を再現する。surrogate bet IDをtie-breakerに使わない。

同じplan内ではstake、rank、purchase orderが異なっても`(bet_type, canonical race_entry_ids)`が同じbetを拒否する。別plan・別run間では同一identityを許可する。この方針は既存`SimulationResult`と`RuleBasedBetStrategy`の重複排除契約に合わせる。

#### `BetPlan` から snapshot への変換

実在するpredictionモデルは以下である。

```python
@dataclass(frozen=True)
class BetPlan:
    strategy_name: str
    recommendations: tuple[BetRecommendation, ...]
    candidate_count: int

@dataclass(frozen=True)
class BetRecommendation:
    rank: int
    bet_type: str
    horse_ids: tuple[int, ...]
    estimated_probability: float
    expected_value: float | None
    combination_score: float | None
    prediction_score: float
```

`BetPlan`にも`BetRecommendation`にもstake、amount、purchase order、race ID、strategy ID、prediction cutoffは存在しない。`StrategyConfig`および`SimulationRunContext`にもstake allocationの正式フィールドはない。したがって、stakeを均等配分・100円固定・既定値から推測することは禁止する。

最終的な純粋変換は`SimulationBetPlanBuilder`とする。BuilderはDB、Repository、Provider、現在時刻、strategy再実行、recommendationの再ソートへ依存せず、確定済みstake allocationとrace entry selection resolverを受けてsnapshotを返す。完全APIは次とする。

```python
class SimulationBetPlanBuilder:
    def __init__(
        self,
        *,
        selection_resolver: RaceEntrySelectionResolver,
    ) -> None:
        ...

    def build(
        self,
        *,
        allocation_plan: BetAllocationPlan,
    ) -> SimulationBetPlanSnapshot:
        ...
```

constructorは`resolve_race_entry_ids` attributeがcallableであることだけを明示検証し、不正なら`ValueError`とする。既存Protocolは`runtime_checkable`ではないため、runtime Protocol判定を追加しない。constructorではresolverを呼ばない。`build()`は`BetAllocationPlan`型だけを受け、run/race/strategy/cutoff、budget、policy identityを重複した別引数で受けない。少なくとも以下の責務を持つ。

```text
BetPlanのtuple順を保持
→ 各recommendationのhorse_idsをresolve
→ 確定済みallocationからstakeを取得
→ SimulationBetを構築
→ plan内重複を拒否
→ SimulationBetPlanSnapshotを返す
```

`BetStakeAllocator`または`BetAllocationPlan`の設計が、変換実装の前提フェーズとして必要である。allocationはrecommendationごとのstakeを損失なく表し、最終`BetPlan`のtuple順との対応を明示しなければならない。

#### horse IDs から race entry IDs への変換

`BetRecommendation.horse_ids`と`SimulationBet.race_entry_ids`は別境界である。現在のCLI実装では両者が`horses.id`由来に見えるが、Builderが暗黙に同一IDとして扱ってはならない。

```python
class RaceEntrySelectionResolver(Protocol):
    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        ...
```

resolverは指定race内でhorse IDをrace entry IDへ変換し、別race、欠損ID、重複IDを拒否する。Builderはrecommendation由来の順序をそのままresolverへ渡し、券種別canonicalizationは最終的な`SimulationBet` constructorへ一元化する。Repository/DB依存はresolverの具体実装に閉じ込め、純粋Builderへ直接埋め込まない。上位層で変換済み`BetPlan`を生成する案は既存`BetPlan`の型を変える必要があるため、今回の最小方針には採用しない。

現行schemaでは`horses.id`がsimulation persistence上の`race_entry_id`として参照され、`horses.race_id`との整合はmigration triggerで守られる。一方、predictionの`BetRecommendation.horse_ids`はprediction pipelineが受け取る`RacePredictionInput.horse_past_races`のkey（CLIでは`database.get_horse_id()`の戻り値）であり、公開domain contractは両者の意味上の同一性を保証していない。horse IDからrace entry IDをrace ID付きで変換するRepository Protocol、helper、具象Resolverは現時点で存在しない。将来の具象Resolverは値が偶然同じでも暗黙同一視せず、race-scoped mappingをRepository/DB境界で検証しなければならない。

resolverはinput `horse_ids`順に対応するrace entry IDsを返し、無条件sortを行わない。これによりhorse-to-entry対応を監査でき、後段の`SimulationBet` constructorだけが券種別規則に従ってcanonicalizeする。Protocolは例外classを定めない。将来の具象Resolverはpublic入力・解決不能を`ValueError`でfail-closedとし、Repositoryが送出する`RepositoryValidationError`、`RepositoryDataIntegrityError`、`RepositoryConflictError`等はwrapせず伝播する。`SimulationValidationError`は`SimulationRaceInput`の時点監査用であり、このID変換境界には使用しない。新例外は追加しない。

#### 将来の Repository API

`SimulationBetRepository`は個別betではなくplan snapshotを保存・取得する。

```python
class SimulationBetRepository(Protocol):
    def save_plan(
        self,
        *,
        snapshot: SimulationBetPlanSnapshot,
    ) -> SimulationBetPlanSnapshot:
        ...

    def get_plan(
        self,
        *,
        identity: SimulationBetPlanIdentity,
    ) -> SimulationBetPlanSnapshot | None:
        ...
```

Repositoryはidentityを生成しない。insert-onlyで同一identityの再保存を拒否し、空planも保存する。読取時はpurchase orderを維持し、DB行をdomain constructor validationへ通して復元する。Repository読取時刻をprediction cutoffとして使用しない。

#### Phase 4C-2d3b の進行判定と分割

**Phase 4C-2d3b1の前に追加設計が必要**である。identity、run供給、空plan、purchase order、`placed_at_cutoff`不変条件、selection resolver、変換責務は設計済みだが、`SimulationBetPlanIdentity` はまだproduction contractとして未実装であり、recommendationごとのstakeの正式取得元も存在しない。

次の順序とする。

```text
Phase 4C-2d3b0a
BetStakeAllocator / BetAllocationPlan の入力・出力・順序対応を設計する。

Phase 4C-2d3b0a0
stake allocationの前提identity、validation例外、policy configuration hash境界を設計する。

Phase 4C-2d3b0a0a
SimulationBetPlanIdentity contractを追加する。

Phase 4C-2d3b0a0b
race非依存allocation value objectのvalidation方針を反映する。

Phase 4C-2d3b0a0c
allocation policy configurationをStrategyConfig hashへ統合する。

Phase 4C-2d3b0a1
BetStakeBudget、BetAllocationPlan、BetStakeAllocator、allocation policy設定の
domain / Protocol契約を追加する。

Phase 4C-2d3b0a2a
最初の具体的BetStakeAllocator policyであるFixed Stakeの設計だけを確定する。

Phase 4C-2d3b0a2b
確定済みFixed Stake設計に従い、concrete allocatorと専用テストを実装する。

Phase 4C-2d3b0b1
SimulationBetPlanSnapshot contractを追加する。

Phase 4C-2d3b0b2
RaceEntrySelectionResolver Protocolを追加する。

Phase 4C-2d3b0c
確定済みallocationを使うSimulationBetPlanBuilderを実装する。

Phase 4C-2d3b1
bet plan schema / migration を追加する。

Phase 4C-2d3b2
SimulationBetRepository と SQLite実装を追加する。

Phase 4C-2d3b3
Repository-backed SimulationBetSource を実装する。

Phase 4C-2d3b4
PredictionPipeline の最終BetPlanをsnapshotとして保存する上位接続を実装する。
```

stake allocationの入力・境界はPhase 4C-2d3b0a0aから0a0cで先にproduction contractへ反映する。schema、Repository、Sourceの実装は、その後のbudget、allocation policy設定、run contextのcomposition root供給を含む0a1以降の契約が完了するまで開始しない。

#### BetStakeAllocator／BetAllocationPlan（Phase 4C-2d3b0a）

##### Phase 4C-2d3b0a0: stake allocation前提契約の整合

Phase 4C-2d3b0a1の実装前確認で、次の三つが未解決だった。

1. `SimulationBetPlanIdentity` は設計書にだけ存在し、production codeには存在しない。
2. `SimulationValidationError(race_id, input_identifier, reason)` はrace単位の入力・境界エラーであり、race IDを持たないbudgetやpolicy identityへ架空のrace IDを渡せない。
3. 現在の`StrategyConfig`と`strategy_config_hash()`はallocation policyを含まないため、異なるallocation policyを同じstrategy hashで識別してしまう。

この節は上記を解消するための設計であり、ここで示す新規contract、`StrategyConfig`変更、hash変更、CLI/settings変更はまだ実装しない。

###### 実在するidentity・設定境界

現行production codeで確認した型と経路は次のとおりである。

| 対象 | 実在するfieldまたは処理 | allocation前提としての扱い |
| --- | --- | --- |
| `SimulationRunContext` | `run_id: str`、`dataset_id: str`、`started_at: datetime`、`target_commit_id: str` | `run_id`だけをplan identityへコピーする。run context objectそのものは保持しない。 |
| `StrategyIdentity` | `strategy_id: str`、`strategy_name: str`、`strategy_config: StrategyConfig`、`strategy_config_hash: str` | `strategy_id`と`strategy_config_hash`だけをplan identityへコピーする。 |
| `SimulationRaceInput` | `race_id: int`、`information_cutoff: datetime`、`scheduled_start_at`、prediction input、audit | `race_id`と`information_cutoff`だけをplan identityへコピーする。 |
| `StrategyConfig` | `allowed_bet_types`、`max_bet_count`、`selection_style`、`min_combination_score`、`max_candidates`、`sort_condition` | allocation policy fieldは未実装である。 |
| `strategy_config_payload()` | 上記6 fieldとschema versionをdict化する | set/frozenset等を正規化しているが、allocation設定payloadは未実装である。 |
| `strategy_config_hash()` | canonical JSON（sorted keys、compact UTF-8）をSHA-256化する | policy設定を含まないため、現時点ではallocation再現性のhashに使用できない。 |
| `build_strategy_identity()` | `strategy_config_hash()`から`StrategyIdentity`を生成する唯一の現行helper | 0a0cでhash対象を拡張すれば、生成経路を別途増やさずpolicyをidentityへ反映できる。 |

`RuleBasedBetStrategy`は`StrategyConfig`からrecommendation集合と順序を決めるだけで、stakeまたはbudgetを扱わない。prediction CLIは`--bet-types`、`--max-bets`、`--max-candidates`、style、score、sortを`StrategyConfig`へ渡すが、allocation option、settings JSON、race単位budgetの経路は存在しない。

###### `SimulationBetPlanIdentity` の正式API案

`SimulationBetPlanIdentity`はallocationより先に、独立したproduction contractとして追加する。配置候補は **`scripts/simulation/bet_plan_identity.py`** とする。このmoduleは`datetime`以外のsimulation model、Repository、Provider、DB、現在時刻へ依存しない。

```python
@dataclass(frozen=True, slots=True)
class SimulationBetPlanIdentity:
    run_id: str
    race_id: int
    strategy_id: str
    strategy_config_hash: str
    information_cutoff: datetime
```

fieldの構成元は固定する。

```text
run_id               <- SimulationRunContext.run_id
race_id              <- SimulationRaceInput.race_id
strategy_id          <- StrategyIdentity.strategy_id
strategy_config_hash <- StrategyIdentity.strategy_config_hash
information_cutoff   <- SimulationRaceInput.information_cutoff
```

このtypeは上記の依存object自体を保持しない。run ID生成、config hash生成、Repository/DBアクセス、現在時刻取得、`SimulationRaceInput`の再validation、strategy validation、race input取得を行わない。composition rootまたは後続Builderが、すでに構築・検証済みの値をコピーして構築する。

validationは以下を正式とする。

- `run_id`と`strategy_id`は空文字・空白のみを拒否する`str`。入力をtrim、case変換、再生成しない。
- `race_id`は正の非bool`int`。bool、0、負数、その他の型を拒否する。
- `strategy_config_hash`は64文字の小文字SHA-256 hexadecimal digest。hashは外部から受け取り、このtypeは生成・補正しない。
- `information_cutoff`はtimezone-aware `datetime`。naive datetime、UTCへの暗黙変換、時刻の丸めを行わない。

このidentityは後続snapshot、allocation plan、Repository keyの共通identityになる。`SimulationRunContext`の`dataset_id`、`started_at`、`target_commit_id`および`StrategyIdentity.strategy_name`はrun/strategy来歴であり、plan identityのfieldへ重複させない。

###### validation例外の正式適用範囲

`SimulationValidationError`は既存の三引数APIを変更しない。race IDを持たないpure value objectへダミーの`race_id`を渡すこと、または`SimulationBetEvaluationError`を一般domain validationへ流用することを禁止する。

| 対象 | race ID | 正式なvalidation例外 | 理由 |
| --- | ---: | --- | --- |
| `SimulationRaceInput` | あり | `SimulationValidationError` | 予測時点・監査を含むrace入力境界である。 |
| `RaceSettlementData` | あり | `SimulationValidationError` | Sourceが供給するrace単位bundleである。 |
| `PersistedRaceSettlementData` | あり | `SimulationValidationError` | 永続化済み精算情報のrace単位bundleである。 |
| `SimulationBetPlanIdentity` | fieldとして保持 | `ValueError` | 独立したidentity value objectであり、未構築または不正なrace fieldに対してrace境界エラーを偽装しない。 |
| `BetStakeBudget` | なし | `ValueError` | race非依存のpure value objectである。 |
| `AllocationPolicyIdentity` | なし | `ValueError` | race非依存のpolicy identityである。 |
| `AllocatedBetRecommendation` | なし | `ValueError` | race非依存のallocation明細である。 |
| `BetAllocationPlan` | identityを保持 | `ValueError` | pure aggregateであり、子valueの不正とaggregate整合性を同じdomain validationとしてFail Closedにする。 |

既存の`StrategyIdentity`、`SimulationRunContext`、`SimulationBet`、Repository境界modelもconstructor validationに`ValueError`を用いる。この既存規約に合わせ、案A（race非依存pure value objectは`ValueError`）を正式採用する。案Bの新しいrace非依存例外contractは不要であり、案Cの`SimulationValidationError`をrace ID optionalへ変更する必要もない。`SimulationBetEvaluationError`は単一bet／race精算のFail Closed評価だけに残す。

従って、0a1での例外方針は次のとおりである。

- `BetStakeBudget`: 非`int`、bool、負数、100円単位違反は`ValueError`。
- `AllocationPolicyIdentity`: 非`str`、空文字、空白のみは`ValueError`。入力文字列はtrimして受理しない。
- `AllocatedBetRecommendation`: `BetRecommendation`型不正、`purchase_order`の非負非bool`int`違反、stakeの正の非bool100円単位違反は`ValueError`。
- `BetAllocationPlan`: identity型、`BetPlan`型、allocation tuple、allocation件数・object identity・purchase order・recommendation identity・budget上限の整合性違反は`ValueError`。子value objectが既に送出する`ValueError`もそのまま伝播する。

exception messageだけで契約を区別しない。field名と不変条件をテストし、例外typeは上表に従う。

###### allocation policy configuration と strategy hash（Phase 4C-2d3b0a0c）

allocation policyの名前・version・決定的設定をstrategy hashへ含める必要がある。現行の`StrategyConfig`は`@dataclass(frozen=True)`であり、`allowed_bet_types`、`max_bet_count`、`selection_style`、`min_combination_score`、`max_candidates`、`sort_condition`の六fieldを持つ。slotsは使用していない。現在の直接constructor利用は既定値またはkeyword指定であり、現行sourceに位置引数利用はない。

現行`strategy_config_payload()`はschema versionと六fieldをdict化し、`_normalize_json()`がEnum、set/frozenset、tuple/list、`Decimal`、有限floatを正規化する。`strategy_config_hash()`は`sort_keys=True`、`separators=(",", ":")`、`ensure_ascii=False`のUTF-8 JSONをSHA-256化し、`build_strategy_identity()`がこのhashだけを使って既存`StrategyIdentity`を作る。settings JSONは全体設定だけでStrategyConfigを復元せず、config loader・strategy factoryは存在しない。prediction CLIは引数から`StrategyConfig`を直接構築し、`PipelineConfig`は`StrategyConfig()`をdefault factoryとして保持する。

`StrategyConfig`はprediction packageのtypeであり、`scripts/simulation/models.py`が既にこれをimportする。このためprediction側からsimulation側のstake moduleをimportすると循環importになる。allocation policy configuration contractの配置は **`scripts/prediction/allocation_policy.py`** とする。後続の`scripts/simulation/stake_allocation.py`はpredictionの`BetPlan`／`BetRecommendation`とpolicy contractをimportしてよいが、prediction側はsimulation allocation contractをimportしない。

##### 正式APIとidentity/configの分離

`AllocationPolicyConfig`が`AllocationPolicyIdentity`を保持すると、identityの`policy_config_hash`をconfigから作る際にconstructor循環となる。したがって、configは入力値、identityはconfigからの派生値として分離する案を正式採用する。

```python
JsonScalar = str | int | bool | None
JsonValue = JsonScalar | tuple[JsonValue, ...] | Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True)
class AllocationPolicyConfig:
    policy_name: str
    policy_version: str
    parameters: Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True)
class AllocationPolicyIdentity:
    policy_name: str
    policy_version: str
    policy_config_hash: str
```

`AllocationPolicyConfig`はpolicy name、version、parametersだけを保持する。`AllocationPolicyIdentity`はconfigのcanonical payloadから得た派生値であり、allocator object、callable、budget、BetPlan、recommendation、DB、Repository、現在時刻を保持しない。両typeのintrinsic validationは`ValueError`とし、name/versionは非`str`、空文字、空白のみを拒否してtrimやcase変換をしない。identityの`policy_config_hash`は64文字の小文字SHA-256 hexadecimal digestで、identity自身はhashを生成しない。

##### parametersの正式型、freeze、nested範囲

最初のVer0.8 contractでは、案Bの限定JSON valueを採用する。scalarは`str`、非bool`int`、`bool`、`None`だけとする。nested structureは文字列keyのMappingとsequenceだけを再帰的に許し、内部表現とJSON serialize用表現を明確に分離する。`bool`は`int`より先に判定し、boolを非bool`int`として誤受理しない。

```text
Mapping[str, input value] -> 文字列keyを固定順で新しいdictへ防御的copyし、MappingProxyType化
list/tuple input          -> 再帰的にtuple
scalar                    -> 許可された同一scalar
```

Mapping keyは`str`だけを受理する。listとdictは入力mutable containerから防御的にcopyするため、生成後の変更はconfigへ影響しない。tupleの順序は意味を持つため保持し、mapping key順は意味を持たないため内部freeze時とcanonical JSON変換時の両方で辞書順にする。循環参照するcontainerは検出して拒否する。`datetime`、`date`、`bytes`、`bytearray`、set/frozenset、任意object、callable、allocator instance、`Decimal`、floatを拒否する。policy固有の数値制約（100円単位、basis points範囲など）は具体policy configまたは具体allocatorへ一度だけ置く。

floatは初期contractで禁止する。Python floatをhash入力にすると、binary表現、入力経路、外部JSON実装による再現性リスクを持つためである。score比率、Kelly係数、最大投資比率、confidence thresholdが必要になった場合は、整数basis pointsまたは明示的なdecimal文字列をpolicy parametersへ入れる。decimal文字列の数値意味・桁数・範囲は具体policyだけが検証し、generic configは文字列を数値へ暗黙変換しない。

固定field dataclass（案A）は具体policyの個別制約に適しており、後続policyが必要なら`AllocationPolicyConfig.parameters`を受け取るfactory内部で使用してよい。しかし共通contract自体をpolicyごとのclassへ固定せず、限定JSON valueによる安全な拡張性を優先する。flat parameter tuple（案C）は初期fixed stakeには十分だが、将来の券種別・nested設定を早期に排除するため採用しない。

##### canonical JSON変換、serialization と policy hash生成境界

`MappingProxyType`はPython標準の`json.dumps()`でJSON objectとして直接serializeできないため、immutable内部表現を直接JSON化してはならない。policy hash生成はconstructorでもcomposition rootでもなく、既存strategy identity生成規約と同型の純粋関数へ置く。次のAPIを`AllocationPolicyConfig`と同じprediction moduleへ追加する。

```python
def allocation_policy_config_payload(
    config: AllocationPolicyConfig,
) -> dict[str, object]:
    ...


def allocation_policy_config_hash(
    config: AllocationPolicyConfig,
) -> str:
    ...


def build_allocation_policy_identity(
    config: AllocationPolicyConfig,
) -> AllocationPolicyIdentity:
    ...
```

加えて、immutable `parameters`を**plain JSON tree**へ変換する純粋関数を置く。

```python
def canonicalize_allocation_policy_parameters(
    parameters: Mapping[str, JsonValue],
) -> dict[str, object]:
    ...
```

この関数は、`str`を`str`、非bool`int`を`int`、`bool`を`bool`、`None`を`None`として返す。tupleは順序を保ったJSON listへ、`MappingProxyType`を含むMappingはkeyを辞書順にした通常のdictへ再帰変換する。出力は`dict`、`list`、`str`、`int`、`bool`、`None`だけからなるplain JSON treeである。入力を変更せず、数値変換、`datetime`の文字列化、任意objectへの`str()`、key trim、値の暗黙補正、hash生成を行わない。

payloadは次の四要素を必ず含む。

```json
{
  "schema_version": 1,
  "policy_name": "...",
  "policy_version": "...",
  "parameters": { "...": "..." }
}
```

policy hashの正式順序は、`AllocationPolicyConfig` → immutable parameters → `canonicalize_allocation_policy_parameters()`によるplain JSON tree → allocation policy payload → `json.dumps()` → UTF-8 encode → SHA-256 → lowercase hexdigestである。payload builderがparameters型・recursive freeze後のJSON可能性を一度だけ検証する。hash functionは次のJSON規則を使う。

```python
json.dumps(
    payload,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
)
```

NaN／Infinityを含む型はgeneric parametersで受理しないためcanonical JSONへ到達しない。policy payloadの`schema_version=1`はこのphaseで固定し、callerが変更できる引数を公開しない。`allocation_policy_config_payload()`、`allocation_policy_config_hash()`、`build_allocation_policy_identity()`だけがconfigからidentityを派生する。`AllocationPolicyConfig` constructorはhashを受け取らず、callerが任意hashをconfigへ注入する経路を作らない。

##### StrategyConfigとstrategy payloadへの統合

案Bのnested configを`StrategyConfig`の**末尾default field**として追加する。

```python
allocation_policy: AllocationPolicyConfig | None = None
```

末尾かつdefault付きのfield追加は、現行の既定値・keyword指定・将来の位置引数constructor互換を保つ。`None`はlegacy/default allocation policyではなく、**allocation policy未設定でありstake allocation実行不可**を表す。既存prediction-only Pipeline、CLI、settings JSONはallocationを実行しないため`None`をそのまま許容する。後続allocation composition boundaryだけが`None`をFail Closedで拒否する。settings JSONにfieldがない場合も`None`となり、暗黙のallocation policyを導入しない。

`allocation_policy is None`のとき、`strategy_config_payload()`は新しい`"allocation_policy"` keyを**追加しない**。既存payloadの構造と既存strategy schema versionを完全に保持するため、既存prediction-only `StrategyConfig`の`strategy_config_hash()`は変更しない。`None`は「stake allocation未設定」を表し、default policyを意味しない。

設定済みの場合は次の値を含める。

```python
{
    # existing StrategyConfig fields
    "allocation_policy": {
        "schema_version": 1,
        "policy_name": config.allocation_policy.policy_name,
        "policy_version": config.allocation_policy.policy_version,
        "policy_config_hash": allocation_policy_config_hash(config.allocation_policy),
        "parameters": canonical_parameters,
    },
}
```

hashだけではparameters詳細を監査できず、parametersだけではpolicy hashの独立した整合確認ができない。よって設定済みstrategy payloadには**policy hashとcanonical parametersの両方**を含める。`policy_config_hash`はpayload builderがconfigから計算するため、外部入力値との不整合を持ち込まない。nested allocation policy payloadは独自の`schema_version=1`を持つ。このpayloadを既存`strategy_config_hash()`がhash化し、`build_strategy_identity()`は引き続き唯一のidentity生成経路とする。policy name、policy version、parameters値の変更は必ずstrategy hashとstrategy IDを変更し、mapping key順だけの違いは変更しない。

末尾default fieldの追加は**constructor互換性**を保つ。一方、`allocation_policy is None`でkeyを追加しないことは、既存strategy payloadとhashを保つ**hash互換性**である。二つは別の契約として回帰テストで検証する。

raceごとの`BetStakeBudget.total_amount`、run ID、race ID、information cutoffはallocation policy設定ではないためstrategy payload/hashへ含めない。budgetは後続`BetAllocationPlan.total_budget`とplan header監査値へ保存する。

##### validation責務、後続実装範囲、進行判定

| 対象 | 一度だけ置く責務 |
| --- | --- |
| `AllocationPolicyConfig` | name/versionとparameters containerのintrinsic validation、defensive freeze |
| concrete policy | parameterの数値意味・範囲・policy固有制約 |
| policy payload builder | recursive JSON可能性とcanonical payload構築 |
| policy hash function | canonical payloadのSHA-256化 |
| identity builder | configからderived identityを組み立てる |
| `StrategyConfig` | `AllocationPolicyConfig | None`だけを受理する |
| `strategy_config_payload()` | `None`なら既存payloadを完全維持し、設定済みならpolicy hash＋canonical parametersを含める |
| `strategy_config_hash()` | 拡張済みstrategy payloadだけをhash化する |

Phase 4C-2d3b0a0c1のproduction実装対象は、`scripts/prediction/allocation_policy.py`、`scripts/prediction/bet_strategy.py`、および既存`scripts/simulation/models.py`の`strategy_config_payload()`、`strategy_config_hash()`、`build_strategy_identity()`（必要なら同じhash経路の`_normalize_json()`）だけである。`AllocationPolicyConfig`と`AllocationPolicyIdentity`はともにprediction側の`allocation_policy.py`に置き、simulation側はそのidentityをimportするだけで複製しない。`SimulationBet`、`SimulationSummary`、`race_count`、Result/Summary contractなど既存simulation model全体は変更しない。`scripts/simulation/strategy_identity.py`は追加しない。このphaseでは具体allocator、BetStakeBudget、BetAllocationPlan、SimulationBetPlanBuilder、Repository、schema、CLI接続、settings JSON、budget入力を実装しない。

`Phase 4C-2d3b0a0c1`、`0a1`、`0a2a`、`0a2b`は完了済みである。parameters型、freeze、canonical serialization、派生identity、StrategyConfig integration、allocation contract、Fixed Stake policy実装までを確定した。次の未実装範囲はsnapshot、Resolver、Builder、永続化schemaと接続である。

###### 修正後の実装順と進行判定

```text
Phase 4C-2d3b0a0a
SimulationBetPlanIdentity contractを scripts/simulation/bet_plan_identity.py に追加する。

Phase 4C-2d3b0a0b
新しい例外classおよびSimulationValidationError API変更は不要である。
0a0aおよび0a1のconstructor testsで上表のValueError方針を検証する。

Phase 4C-2d3b0a0c
scripts/prediction/allocation_policy.py のpolicy configuration contract、
StrategyConfig末尾field、canonical payload/hash、StrategyIdentity回帰testsを追加する。

Phase 4C-2d3b0a1
scripts/simulation/stake_allocation.py にBetStakeBudget、
AllocatedBetRecommendation、BetAllocationPlan、BetStakeAllocator Protocolを追加する。

Phase 4C-2d3b0a2a
Fixed Stake allocation policyの設定、identity、予算、失敗時の契約を設計だけで確定する。

Phase 4C-2d3b0a2b
FixedStakeBetAllocatorと専用テストを実装する。

Phase 4C-2d3b0b1
SimulationBetPlanSnapshot contractを追加する。

Phase 4C-2d3b0b2
RaceEntrySelectionResolver Protocolを追加する。

Phase 4C-2d3b0c
SimulationBetPlanBuilderを実装する。
```

`Phase 4C-2d3b0a0a`から`0a2b`までは完了済みである。identity、policy configurationのhash統合、budget/allocation contract、Fixed Stakeの具体実装を確定した。後続はsnapshot、Resolver、Builderの順に進める。

##### 既存のbudget・stake境界

現行の`BetPlan`は`strategy_name`、順序付き`recommendations`、`candidate_count`だけを持ち、`BetRecommendation`は`rank`、`bet_type`、`horse_ids`、確率・score・expected value関連値だけを持つ。stake、amount、budget、purchase orderは存在しない。`RuleBasedBetStrategy`と`StrategyConfig`も購入対象と`max_bet_count`を決めるだけで、資金配分を持たない。

prediction CLIには`--max-bets`があるが、これは購入点数上限でありbudgetやstakeではない。設定JSON、race単位budget、stake allocation処理は存在しない。旧`models.Bet.amount`はsimulation planや`BetPlan`に接続されない別モデルであり、allocationの入力に使用しない。

##### stake allocation の責務と処理順

stake allocationは`BetStrategy`の後、race entry selection解決と`SimulationBet`構築の前に行う。

```text
PredictionPipeline
→ BetGenerator
→ BetStrategy
→ 最終 BetPlan
→ BetStakeAllocator
→ BetAllocationPlan
→ RaceEntrySelectionResolver
→ SimulationBetPlanBuilder
→ SimulationBetPlanSnapshot
```

| 層 | 責務 |
| --- | --- |
| `BetStrategy` | 最終recommendation集合と順序を確定する。 |
| `BetStakeAllocator` | 既存recommendationごとのstakeを配分し、budgetを検証する。 |
| `BetAllocationPlan` | allocation結果をimmutableに表す。 |
| `RaceEntrySelectionResolver` | horse IDをrace entry IDへ変換する。 |
| `SimulationBetPlanBuilder` | allocationから`SimulationBet`を構築しsnapshot化する。 |
| Repository | 完成したsnapshotとplan headerのallocation監査値を保存・復元する。 |
| `SimulationBetSource` | run・race・strategyに対応する保存済みbetsを供給する。 |

Allocatorはrecommendationの追加、削除、並べ替え、再評価、rank再採番、券種変更、selection変更、race entry解決、`SimulationBet`構築を行わない。budget不足時に下位候補を黙って削除せず、fail-closedで拒否する。候補数削減が必要なpolicyは、Allocatorではなく後続のbudget-aware selection責務として別設計する。

##### budget の正式入力契約

既存型にrace単位budgetはないため、後続契約で次を追加する。

```python
@dataclass(frozen=True, slots=True)
class BetStakeBudget:
    total_amount: int
```

`total_amount`は非負の非bool `int`かつ100円単位である。budgetはcomposition rootから明示的に渡す不変入力であり、現在時刻、Repository読取時刻、外部口座残高、Allocatorの隠れたmutable stateから取得しない。空planには0円または正の100円単位budgetを許可する。

recommendation件数を`N`とすると、購入候補がある場合の最低必要額は`N × 100円`である。`total_amount < N × 100円`なら、0円stake、100円未満stake、部分allocation、NO_BETへの変換を行わず、allocation不能としてfail-closedにする。

budgetはplan identityの構成要素にしない。同一identityは一つのimmutable snapshotだけを許すため、そのsnapshotに対応するallocationのbudgetは一意である。budgetは`BetAllocationPlan.total_budget`および後続schemaのplan header監査値として保存する。これにより、runをまたぐ同一strategyでも異なるbudgetを明示的に監査でき、actual stakeはsnapshot内の`SimulationBet.stake`から再現できる。

##### allocated recommendation と allocation plan

`BetRecommendation`と`BetPlan`はいずれもfrozen dataclassであり、recommendationsはtupleである。したがって、allocationはrecommendationをdeep copyせず、同じimmutable objectを参照してよい。

```python
@dataclass(frozen=True, slots=True)
class AllocatedBetRecommendation:
    recommendation: BetRecommendation
    purchase_order: int
    stake: int


@dataclass(frozen=True, slots=True)
class BetAllocationPlan:
    identity: SimulationBetPlanIdentity
    bet_plan: BetPlan
    allocations: tuple[AllocatedBetRecommendation, ...]
    total_budget: int

    @property
    def allocated_amount(self) -> int: ...

    @property
    def unallocated_amount(self) -> int: ...
```

`AllocatedBetRecommendation`は正式な`BetRecommendation`、0以上の非bool`purchase_order`、正の非bool100円単位`stake`を持つ。recommendationの内容・rankを変更しない。

`BetAllocationPlan`は`identity`、`bet_plan`、tuple化した`allocations`、非負100円単位の`total_budget`を保持する。`allocated_amount`と`unallocated_amount`はfieldではなくread-only propertyとし、前者を`sum(allocation.stake ...)`、後者を`total_budget - allocated_amount`から算出する。重複した集計fieldによる不整合を避けるためである。両値は100円単位で、`allocated_amount <= total_budget`を必須とする。

allocationは入力`BetPlan`を保持して1対1対応をdomain boundaryでも検証する。次を必須とする。

```text
len(allocations) == len(bet_plan.recommendations)
allocations[index].recommendation is bet_plan.recommendations[index]
allocations[index].purchase_order == index
```

`BetPlan`と`BetRecommendation`はfrozenであるため、object identityを使うことは可変オブジェクトへの依存ではなく、Allocatorが別のrecommendationを再構築・差し替えしていないことの明示的な保証になる。各allocationの順序・件数・recommendation内容は不変である。

plan内のrecommendation identityは`(bet_type, canonical horse_ids)`とする。`BetRecommendation`の`horse_ids`は`BetGenerator`で組合せを昇順化するが、allocation contractは入力`BetPlan`を再ソートしない。allocation planは重複identityを拒否し、後続Builderがrace entry IDsへ変換後に行う`SimulationBet`側の重複検証も維持する。

空`BetPlan`ではallocationも空とし、`allocated_amount == 0`、`unallocated_amount == total_budget`とする。これは正常なNO_BET候補であり、allocation失敗とは区別する。

##### `BetStakeAllocator` Protocol とpolicy再現性

```python
class BetStakeAllocator(Protocol):
    def allocate(
        self,
        *,
        identity: SimulationBetPlanIdentity,
        bet_plan: BetPlan,
        budget: BetStakeBudget,
    ) -> BetAllocationPlan:
        ...
```

同一入力・同一policy設定では決定的な結果を返す。DB、Repository、Provider、HTTP/network、logger、現在時刻、odds再取得、Result/Summary builder、Simulator、結果・払戻には依存しない。

allocation policyの名称、version、決定的設定はsimulation再現性に影響するため、具体Allocatorのクラス名だけで表現してはならない。`Phase 4C-2d3b0a0c1`で、`StrategyConfig.allocation_policy`の`AllocationPolicyConfig`を正式なstrategy configuration payloadへ含め、`strategy_config_hash()`および`StrategyIdentity.strategy_config_hash`へ統合済みである。allocation policyが設定されている場合、同じstrategy_config_hashで異なるallocation policyまたは設定を使用することは許可しない。`allocation_policy is None`はprediction-only設定として保持できるが、allocatorを構成するcomposition rootは具体policy設定を明示的に渡す。

budget値はpolicy設定ではなくrunごとの明示入力であるため、strategy config hashには含めない。budgetはallocation planと後続のplan header監査値へ保存する。

固定stake、均等配分、score比例、expected value比例、confidence比例、Kelly系、券種別上限は後続policyの比較対象である。Phase 4C-2d3b0aではいずれも採用しない。

##### Builder と次フェーズの進行判定

`SimulationBetPlanBuilder`は`BetAllocationPlan`からrecommendation、purchase order、stake、plan identityを取得する。stakeを再計算せず、allocationの一部を除外せず、recommendationを再ソートしない。

`Phase 4C-2d3b0a0a`、`0a0c1`、`0a1`は完了済みである。budget入力、budget不足、未使用budget、空plan、1対1対応、purchase order、allocation Protocolは既存contractで定義済みであり、次の`0a2a`は最初の具体policyの設計のみを確定する。具体allocation algorithmの実装は`0a2b`まで開始しない。

##### Phase 4C-2d3b0a2a: Fixed stake allocation policy design

この段階はFixed Stake policyの**設計だけ**を確定する。production code、テスト、settings JSON、CLI、Repository、DBを変更しない。次段階で実装する最初の具体policyは、各recommendationに同一の100円単位stakeを割り当てる`FixedStakeBetAllocator`である。

###### Policy configuration と identity

正式なpolicy識別子は次の固定値とする。

```text
policy_name    = "fixed_stake_per_recommendation"
policy_version = "1"
```

設定parameterは`stake_amount`だけとする。`AllocationPolicyConfig.parameters`は正確に`{"stake_amount": int}`の一key mappingでなければならない。`stake_amount`はboolではない`int`、正、かつ100円単位である。0、負数、bool、float、`Decimal`、`None`、文字列、list、tuple、nested mappingを許可しない。欠損key、余分key、空key、非文字列keyも拒否し、coercion、default、trim、丸め、切捨て・切上げは行わない。

```python
policy_config = AllocationPolicyConfig(
    policy_name="fixed_stake_per_recommendation",
    policy_version="1",
    parameters={"stake_amount": 100},
)
policy_identity = build_allocation_policy_identity(policy_config)
```

`StrategyConfig`自身はallocator constructorへ渡さない。composition rootが`StrategyConfig.allocation_policy`をそのまま`AllocationPolicyConfig`としてallocatorへ渡す。これにより、strategy hashへ統合済みのpolicy設定とallocatorが使う設定を一つの正式configuration境界に揃える。

###### Concrete allocator の契約

次段階の実装候補は以下である。

```python
class FixedStakeBetAllocator:
    def __init__(self, *, policy_config: AllocationPolicyConfig) -> None: ...

    def allocate(
        self,
        *,
        identity: SimulationBetPlanIdentity,
        policy_identity: AllocationPolicyIdentity,
        bet_plan: BetPlan,
        budget: BetStakeBudget,
    ) -> BetAllocationPlan: ...
```

constructorは`AllocationPolicyConfig`の正確な型、上記policy name/version、正確なparameter mapping、`stake_amount`の全規則を検証する。不正はすべて`ValueError`とし、`AttributeError`等を直接漏らさない。constructorは渡された`policy_config` objectを同一objectとして保持し、そのconfigから`build_allocation_policy_identity()`で導出したexpected identityを保持する。configの再構築、default補完、設定の置換、hashの独自生成は行わない。

`allocate()`は既存`BetStakeAllocator` Protocolのkeyword-only契約を拡張せず、その全入力を検証する。callerの`policy_identity`はconstructorで導出したexpected identityと完全一致しなければならない。name、version、hash、stake由来hash、callerが独自にmintしたidentityのいずれかが異なれば`ValueError`とする。allocatorはidentityを黙って置換しない。`identity`、`policy_identity`、`bet_plan`、`budget`の不正、policy identity不一致、budget不足はいずれも`ValueError`でfail closedする。最終出力は既存`BetAllocationPlan` constructorにも検証させる。

###### Allocation algorithm と budget

`N = len(bet_plan.recommendations)`、`S = policy_config.parameters["stake_amount"]`とする。allocationは入力順で次を構成する。

```python
allocations = tuple(
    AllocatedBetRecommendation(
        recommendation=bet_plan.recommendations[index],
        purchase_order=index,
        stake=S,
    )
    for index in range(N)
)
```

recommendation objectはdeep copyせず同一objectを保持する。順序、rank、selection、recommendation内容を変更せず、sort、filter、deduplicate、再計算を行わない。必要予算は`required = N * S`であり、`budget.total_amount < required`なら`ValueError`とする。部分allocation、stake引下げ、recommendation除外、fallbackは許可しない。

出力は`BetAllocationPlan(identity=identity, policy_identity=policy_identity, bet_plan=bet_plan, allocations=allocations, budget=budget)`として構築する。`budget.total_amount >= required`なら未使用budgetを許可する。allocated amountは`required`、unallocated amountは`budget.total_amount - required`である。空`BetPlan`ではallocationは空tuple、required/allocated amountは0、budget 0を含む全ての正当budgetを許可し、unallocated amountはbudget全額となる。

###### Pure boundary と実装範囲

Fixed Stake policyはpolicy configと`allocate()`の4入力だけから決定的に出力を作る。現在時刻、乱数、mutable state、Provider、Repository、DB、network、odds、race result、payout、Result/Summary builder、Simulator、loggingを参照しない。入力を変更しない。

次段階`Phase 4C-2d3b0a2b`では、次の二ファイルだけを候補として実装・検証する。

```text
scripts/simulation/fixed_stake_allocator.py
tests/test_fixed_stake_bet_allocator.py
```

production moduleは`stake_allocation`、`bet_plan_identity`、`prediction.allocation_policy`、`prediction.bet_strategy`だけへ依存する。prediction側からsimulation側へのimportは追加しない。今回の設計により`0a2b`は現行contractのまま実装可能であり、残る将来範囲はsnapshot、RaceEntrySelectionResolver、SimulationBetPlanBuilder、永続化schemaとそれらの接続である。

##### Phase 4C-2d3b0b: Simulation bet plan snapshot / resolver / builder boundary

この段階は`SimulationBetPlanSnapshot`、`RaceEntrySelectionResolver`、`SimulationBetPlanBuilder`の**正式設計だけ**を確定する。実装、テスト、schema、migration、Repository、DB、CLIは変更しない。snapshotはprediction domain object（`BetPlan`、`BetRecommendation`、`AllocatedBetRecommendation`、`BetAllocationPlan`）を保持せず、永続化可能なsimulation domainだけを保持する。

###### Snapshot contract と purchase order

完全なsnapshot API、field順、導出propertyは次とする。

```python
@dataclass(frozen=True, slots=True)
class SimulationBetPlanSnapshot:
    identity: SimulationBetPlanIdentity
    policy_identity: AllocationPolicyIdentity
    budget: BetStakeBudget
    bets: tuple[SimulationBet, ...]

    @property
    def allocated_amount(self) -> int: ...

    @property
    def unallocated_amount(self) -> int: ...
```

intrinsic validationは`ValueError`とする。`identity`、`policy_identity`、`budget`は各正式型だけを受理する。betsは防御的にtuple化し、str/bytes/bytearrayを拒否し、各itemが`SimulationBet`であることを確認する。各betはidentityのrace ID、strategy ID、information cutoffと一致し、stake合計はbudget以下でなければならない。同一`(bet.bet_type, bet.race_entry_ids)`はstake、rank、tuple位置が違っても拒否する。`SimulationBet.race_entry_ids`は既に券種別にcanonicalなtupleである。

snapshot tuple順が正式な0-based purchase orderである。`SimulationBet.recommendation_rank`は候補順位でありpurchase orderではない。後続Repository schemaはchild rowへ明示的な`purchase_order`を保存し、復元時に`ORDER BY purchase_order ASC`でtuple順へ戻す。snapshotは空betsを許可し、budget 0または正のbudgetを保持できる。空snapshotは購入計画が確定済みで対象betが0件の意味であり、未生成・未保存・取得失敗を表さない。

`allocated_amount`は`sum(bet.stake for bet in bets)`、`unallocated_amount`は`budget.total_amount - allocated_amount`である。二つをfieldとして保存しない。`policy_identity`はpolicy name/version/config hashと空planでのpolicy監査を、`budget`は入力budgetおよび空planを含むallocated/unallocated監査を損失なく保持する。

###### RaceEntrySelectionResolver contract

```python
class RaceEntrySelectionResolver(Protocol):
    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        ...
```

既存simulation Protocolに合わせ、`runtime_checkable`は付けない。全引数はkeyword-onlyであり、追加public methodは持たない。具象Resolverは正の非bool race IDと、重複のない正のhorse ID sequenceを受け、指定race内の各horse IDを一対一でrace entry IDへ解決する。存在しないhorse、別raceのhorse、重複horse ID、重複race entry ID、解決不能はfail-closedで拒否する。Phase 4C-2d3b1e0で確定した具体境界では、空inputは解決要求として`ValueError`で拒否する。空planはBuilderがResolverを呼ばずに表現する。入力horse ID順に対応するtupleを返し、無条件sortをしない。

Resolverはbet type/selection頭数、stake allocation、recommendation選択・並べ替え、`SimulationBet`/snapshot/Result/Summary構築、policy identity照合、budget検証を行わない。現行実装にはhorse IDとrace IDからrace entry IDを供給するRepository API、helper、具象Resolverは存在しない。現行DBでは`horses.id`がrace-scoped `race_entry_id`として参照されるが、prediction horse IDと意味上同一である公開保証はない。よって将来のRepository-backed concrete Resolverはrace-scoped mappingを明示的に検証し、ID値の偶然の一致を同一視しない。

Protocolは例外classを定義しない。具象Resolverの直接入力不正・未解決は`ValueError`、Repository由来の`RepositoryValidationError`、`RepositoryDataIntegrityError`、`RepositoryConflictError`は同一objectで伝播する。`SimulationValidationError`はprediction cutoff/audit向けであるためResolverには使用しない。

###### Builder contract と validation 分担

```python
class SimulationBetPlanBuilder:
    def __init__(
        self,
        *,
        selection_resolver: RaceEntrySelectionResolver,
    ) -> None:
        ...

    def build(
        self,
        *,
        allocation_plan: BetAllocationPlan,
    ) -> SimulationBetPlanSnapshot:
        ...
```

constructorは`selection_resolver.resolve_race_entry_ids`がcallableであることだけを検証し、満たさなければ`ValueError`とする。既存Protocolは`runtime_checkable`ではないため、runtime Protocol判定を追加しない。constructorではresolverを呼ばない。buildは`BetAllocationPlan`型だけを受け、identity、budget、policy identityを別引数として重複受領しない。

Builderはallocation tuple順に、各allocationについてちょうど一度だけ次を行う。

```python
recommendation = allocation.recommendation
race_entry_ids = selection_resolver.resolve_race_entry_ids(
    race_id=allocation_plan.identity.race_id,
    horse_ids=recommendation.horse_ids,
)
bet = SimulationBet(
    race_id=allocation_plan.identity.race_id,
    strategy_id=allocation_plan.identity.strategy_id,
    bet_type=recommendation.bet_type,
    race_entry_ids=race_entry_ids,
    stake=allocation.stake,
    recommendation_rank=recommendation.rank,
    placed_at_cutoff=allocation_plan.identity.information_cutoff,
)
```

最後に`SimulationBetPlanSnapshot(identity=allocation_plan.identity, policy_identity=allocation_plan.policy_identity, budget=allocation_plan.budget, bets=bets)`を構築する。Builderはallocation件数・順序・purchase order・recommendation rank・bet type・stake・plan identity・policy identity・budget・prediction cutoffを維持する。空allocation planではResolverを0回呼び、空snapshotを返す。

`BetRecommendation.bet_type`と`SimulationBet.bet_type`はともに`str`で、現行の対応券種は`単勝`、`馬連`、`ワイド`、`3連複`である。alias、大文字小文字変換、JRA名から内部名へのmappingは実装されていないため、Builderは`bet_type=recommendation.bet_type`として直接渡す。未知値とselection頭数は既存`SimulationBet`がRepository境界の`validate_bet_type()`および`normalize_selection()`を通じて検証する。converterは不要であり、Builderへ推測mappingを直書きしない。

Builderはallocation plan型、resolver outputがtupleであること、resolver output件数が入力horse IDs件数と一致することだけを明示検証する。非tupleはProtocol違反としてfail-closedにする。実allocationのhorse IDsは非空であり、具体Resolverも空解決要求を拒否する。券種別のselection妥当性は`SimulationBet`に委譲する。別race mappingはBuilderがIDだけから検証できないためResolverの責務である。snapshotのidentity整合、budget上限、bet重複identity、tuple化・空planはSnapshotへ委譲する。Resolver例外、`SimulationBet`例外、Snapshot例外はwrapせず直ちに伝播し、後続allocationを処理せず部分snapshotを返さない。

Builderはstake再計算・budget再配分・recommendation追加/削除/再ソート・rank再採番・policy identity再生成・strategy hash再計算・run/cutoff生成を行わず、DB/Repository/Provider/Result/Summary/payout/race result/current timeにも依存しない。policy identityとidentity.strategy_config_hashの整合を再計算・照合しない。allocation planは既に使用policy identityを固定し、Builderには`AllocationPolicyConfig`もstrategy payloadもないため、同じconfigを`StrategyConfig`とallocatorへ供給するcomposition rootの責務である。

###### 配置、永続化、後続フェーズ

contract配置は次とする。

```text
scripts/simulation/bet_plan_snapshot.py       # SimulationBetPlanSnapshot
scripts/simulation/selection_resolver.py      # RaceEntrySelectionResolver Protocol
scripts/simulation/bet_plan_builder.py        # SimulationBetPlanBuilder
```

snapshotから後続永続化へ、plan headerとしてrun identity、race ID、strategy ID、strategy config hash、prediction cutoff、allocation policy identity、budgetを、child rowとしてpurchase order、bet type、stake、recommendation rank、race entry selectionを損失なく渡せる。具象ResolverはRepository/DB境界を要するためこの純粋contract phaseでは実装しない。

後続は`Phase 4C-2d3b0b1`でSnapshot contract、`Phase 4C-2d3b0b2`でResolver Protocol、`Phase 4C-2d3b0c`でBuilder実装の順とする。Snapshot API、policy/budget保持、purchase order、validation、Resolver順序・意味分離、bet type直接変換、Builder API・validation分担・例外伝播を確定したため、**Phase 4C-2d3b0b1へ進行可能**である。残る未確定事項はRepository-backed concrete Resolver、schema/migration、snapshot Repository、composition/Pipeline接続である。

## 集計指標と分母

| 指標 | 定義 |
| --- | --- |
| 対象レース数 (`race_count`) | 全 `SimulationRaceInput` 件数。 |
| 精算済みレース数 | `SETTLED` のレース数。 |
| 未精算レース数 | `UNSETTLED` のレース数。 |
| 購入なしレース数 | `NO_BET` のレース数。 |
| Voidレース数 | `VOID` のレース数。 |
| Errorレース数 | `ERROR` のレース数。 |
| Unsupportedレース数 | `UNSUPPORTED` のレース数。 |
| 購入レース数 | `SETTLED` かつ購入点が1点以上のレース数。 |
| 購入点数 | 精算済み購入の全点数。 |
| 的中購入点数 | 精算済み購入のうち払戻額が0円超の点数。 |
| 的中レース数 | 精算済み購入レースのうち1点以上的中したレース数。 |
| 投資額 | `SETTLED` かつ購入ありの投資額合計。 |
| 払戻額 | `SETTLED` かつ購入ありの払戻額合計。 |
| 収支 | `払戻額 - 投資額`。 |
| ROI | `払戻額 ÷ 投資額 × 100`。投資額0の場合は `None`、表示は `N/A`。 |
| bet_hit_rate | `的中購入点数 ÷ 精算済み購入点数 × 100`。分母0なら `None`。 |
| race_hit_rate | `1点以上的中した精算済み購入レース数 ÷ 精算済み購入レース数 × 100`。分母0なら `None`。 |
| 最大ドローダウン | `settled_at, race_id` 順の累積収支で計算する最大下落額。初期peakは0円。 |

`hit_bet_count` は `payout_status == winning` の購入点だけを数える。返還、Void、Unsupportedは払戻額が正でも的中点に含めない。`hit_race_count` はwinning購入点が1件以上ある精算済み購入レース数とする。

各状態は排他的であり、`SETTLED + NO_BET + UNSETTLED + VOID + ERROR + UNSUPPORTED` の件数合計は必ず `race_count` と一致する。未精算・Void・Error・Unsupportedレースの精算金額はROI、的中率、ドローダウンへ混入させない。各件数は隠さずレポートとCLIへ表示する。

最大ドローダウンは精算済みレースだけを順に処理し、初期 `equity = 0`、初期 `peak = 0` とする。各精算後に `equity += profit`、`peak = max(peak, equity)`、`drawdown = peak - equity` を計算し、その最大値を保持する。

## 実現ROIとEV戦略の区別

- **実現ROI検証**：確定した完全な払戻表により、実際に購入した点を精算する。初期実装は単勝だけを対象とする。
- **EV戦略検証**：予想時点の実オッズスナップショットと校正済みまたは明示的に暫定である確率を用いる。組み合わせ券種のEV条件は、予想時点の実組み合わせオッズが取得・監査可能になるまで実行しない。
- `combination_score` は候補比較値であり、実現ROI・EVのどちらにも直接代入しない。

## DBマイグレーション案

既存テーブルを破壊せず、取得単位の完全性を親テーブルで、組み合わせと選択馬を関連テーブルで表す。接続作成時に `PRAGMA foreign_keys = ON` を必須とする。

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE race_results (
    race_id INTEGER PRIMARY KEY,
    result_status TEXT NOT NULL,
    finalized_at TEXT,
    observed_at TEXT NOT NULL,
    source TEXT NOT NULL,
    source_url TEXT,
    CHECK (result_status IN ('complete', 'partial', 'void', 'unsupported')),
    FOREIGN KEY (race_id) REFERENCES races(id)
);

CREATE TABLE race_result_entries (
    race_id INTEGER NOT NULL,
    race_entry_id INTEGER NOT NULL,
    finish_position INTEGER,
    result_status TEXT NOT NULL,
    PRIMARY KEY (race_id, race_entry_id),
    FOREIGN KEY (race_id) REFERENCES races(id),
    FOREIGN KEY (race_entry_id) REFERENCES horses(id),
    CHECK (finish_position IS NULL OR finish_position > 0),
    CHECK (result_status IN ('finished', 'cancelled', 'excluded', 'void', 'unsupported'))
);

CREATE TABLE odds_snapshot_batches (
    id INTEGER PRIMARY KEY,
    race_id INTEGER NOT NULL,
    bet_type TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    is_complete INTEGER NOT NULL,
    source TEXT NOT NULL,
    source_url TEXT,
    CHECK (is_complete IN (0, 1)),
    FOREIGN KEY (race_id) REFERENCES races(id),
    UNIQUE (race_id, bet_type, observed_at, source)
);

CREATE TABLE odds_snapshots (
    id INTEGER PRIMARY KEY,
    batch_id INTEGER NOT NULL,
    bet_type TEXT NOT NULL,
    selection_key TEXT NOT NULL,
    odds_decimal TEXT NOT NULL,
    FOREIGN KEY (batch_id) REFERENCES odds_snapshot_batches(id),
    CHECK (length(odds_decimal) > 0),
    UNIQUE (batch_id, bet_type, selection_key)
);

CREATE TABLE odds_snapshot_selections (
    odds_snapshot_id INTEGER NOT NULL,
    race_entry_id INTEGER NOT NULL,
    selection_order INTEGER NOT NULL,
    PRIMARY KEY (odds_snapshot_id, race_entry_id),
    FOREIGN KEY (odds_snapshot_id) REFERENCES odds_snapshots(id),
    FOREIGN KEY (race_entry_id) REFERENCES horses(id),
    CHECK (selection_order > 0),
    UNIQUE (odds_snapshot_id, selection_order)
);

CREATE TABLE payout_publications (
    id INTEGER PRIMARY KEY,
    race_id INTEGER NOT NULL,
    bet_type TEXT NOT NULL,
    finalized_at TEXT,
    observed_at TEXT NOT NULL,
    is_complete INTEGER NOT NULL,
    source TEXT NOT NULL,
    source_url TEXT,
    CHECK (is_complete IN (0, 1)),
    FOREIGN KEY (race_id) REFERENCES races(id),
    UNIQUE (race_id, bet_type, observed_at, source)
);

CREATE TABLE payouts (
    id INTEGER PRIMARY KEY,
    publication_id INTEGER NOT NULL,
    bet_type TEXT NOT NULL,
    selection_key TEXT NOT NULL,
    payout_per_100 INTEGER NOT NULL,
    payout_status TEXT NOT NULL,
    FOREIGN KEY (publication_id) REFERENCES payout_publications(id),
    CHECK (payout_per_100 >= 0),
    CHECK (payout_status IN ('winning', 'refund', 'void', 'unsupported')),
    UNIQUE (publication_id, bet_type, selection_key)
);

CREATE TABLE payout_selections (
    payout_id INTEGER NOT NULL,
    race_entry_id INTEGER NOT NULL,
    selection_order INTEGER NOT NULL,
    PRIMARY KEY (payout_id, race_entry_id),
    FOREIGN KEY (payout_id) REFERENCES payouts(id),
    FOREIGN KEY (race_entry_id) REFERENCES horses(id),
    CHECK (selection_order > 0),
    UNIQUE (payout_id, selection_order)
);

CREATE INDEX idx_result_entries_race ON race_result_entries(race_id);
CREATE INDEX idx_odds_batches_race_time ON odds_snapshot_batches(race_id, observed_at);
CREATE INDEX idx_payout_publications_race_time ON payout_publications(race_id, observed_at);
CREATE INDEX idx_payouts_publication_type ON payouts(publication_id, bet_type);
```

払戻なし（完全な払戻表に該当組み合わせが存在しない）と、払戻データ未取得・不完全（publicationなしまたは `is_complete=0`）を明確に区別する。

`odds_snapshot_batches` と `payout_publications` は券種単位の親レコードであるため、単勝は完全・馬連は未取得のような状態を表現できる。`PayoutPublication` の `race_id + bet_type` 境界は、Provider接続executorが必要な払戻情報を解決する単位と一致する。`selection_key` は関連テーブルの昇順 `race_entry_id` 列から決定的に生成し、監査と一意制約に使う。参照整合性は関連テーブルで維持し、selection_keyだけに依存しない。

`race_result_entries`、`odds_snapshot_selections`、`payout_selections` の `race_entry_id` が対象 `race_id` に属することは、複合外部キーを導入できる場合はDB制約で、できない場合はProviderのFail Closed検証で保証する。別レースの出走行IDを関連付けた場合は登録・精算を拒否する。

オッズは浮動小数点REALで保存せず、Decimal互換の正規化TEXT（`odds_decimal`）または明示的な整数スケール値で保存する。Pythonでは `Decimal` として読み書きし、往復精度をテストする。

マイグレーションは連番の `schema_migrations` で管理し、各バージョンをトランザクションで適用する。マイグレーションテストは本番 `database/keiba.db` を直接使わず、一時DBパスまたは注入可能なConnection Factoryを使用する。

## CLI実行案

```bash
python -m scripts.cli.run_simulation \
  --from 2025-01-01T00:00:00+09:00 \
  --to 2025-12-31T23:59:59+09:00 \
  --strategy-config config/strategy/default.json \
  --stake 100 \
  --bet-types "単勝" \
  --output reports/simulation-v0.8.json
```

CLIは以下を行う。

1. 期間、StrategyConfig、購入単位、券種、時点検証可能なデータセットを検証する。
2. 未対応券種が指定された場合は明確なエラーまたは `unsupported` を返す。初期実装では単勝以外を実行しない。
3. ProviderからFail Closed条件を満たす `SimulationRaceInput` を取得する。
4. `Simulator` を実行し、未精算・Void・Error・Unsupported件数と、正式ROIが無効かを黙って捨てず表示する。
5. JSON/CSVへレポートとレース別明細を出力する。

出力JSON/CSVには最低限、`strategy_id`、`strategy_config_hash`、対象コミットID、データセット識別子、`information_cutoff`、`settlement_status`、除外理由を含める。ROI・的中率の分母が0なら `null` / `N/A` とする。

## テスト方針

### 単体テスト

- 100円単位以外の購入額、券種ごとの選択件数、重複選択を拒否する。
- 完全な払戻表に購入組み合わせがない不的中と、払戻表未取得を区別する。
- `is_complete=False` の払戻表、または複数券種の一部払戻表欠損がROIへ含まれない。
- 同じStrategyクラス・異なるStrategyConfigが異なる `strategy_id` / `strategy_config_hash` / 集計へ分離される。
- `scheduled_start_at` と `settled_at` の順序が異なる場合、予想順とドローダウン順がそれぞれの規則に従う。
- 初期peak=0円を含む最大ドローダウンを検証する。
- 未来情報を1件でも検出した場合、Fail Closedで `SimulationValidationError` とし、ERRORまたは除外結果になる。
- `horse_no` から `race_entry_id` への変換と、組み合わせ昇順正規化を検証する。
- 同着、返還、不成立は仕様確定まで `VOID` または `unsupported` と明示し、推測精算しない。
- 投資額0・精算済み購入点数0のROI・各的中率が `None` になる。
- Simulatorが `completed_at` を生成し、入力のRunContextが完了時刻を持たない。
- UNSETTLEDの `payout` / `profit` が `None` となる。
- UNSUPPORTEDとERRORが別集計となる。
- 返還を的中扱いしない。
- 券種ごとの払戻・オッズ完全性を独立して判定する。
- 同一組み合わせの重複登録を拒否する。
- 別レースの `race_entry_id` 関連付けを拒否する。
- Pipeline内部の現在時刻・現在DB参照を検出し、as-of契約違反を拒否する。
- ERRORが1件以上あるReportで `official_roi_valid=False` になる。
- DecimalオッズをDBから往復して精度を失わない。

### 統合テスト

- 固定Fixtureで `PredictionPipeline` → 内部 `BetGenerator` / `BetStrategy` → `Simulator` → 完全払戻表の一連を検証する。
- SimulatorがPipeline内の `BetPlan` を使用し、候補生成・戦略判定を重複実行しないことを確認する。
- 同一入力へ複数StrategyConfigを適用し、明細・集計・資金曲線が独立することを確認する。
- 時点監査情報のないデータセットで正式ROIが拒否されることを確認する。
- DBマイグレーションは一時DBまたはConnection Factoryを使い、本番 `database/keiba.db` を変更しないことを確認する。
- CLIの終了コード、unsupported券種、未精算・除外表示、JSON/CSV監査列をE2Eで確認する。

## 実装順序

1. timezone-awareな時点監査モデル、StrategyIdentity、SimulationResult、SimulationReport、Fail Closed検証を実装する。
2. 結果・払戻・オッズの親子テーブルと一時DBによるマイグレーションテストを追加する。
3. Rawデータ取得境界（`RaceSettlementSource`）と、既存変換Providerを使うProvider接続executorを追加する。
4. 単勝のみを対象に、100円購入、完全払戻表による精算、集計、最大ドローダウンを実装する。
5. 複数StrategyConfigの比較実行、決定的設定ハッシュ、JSON/CSV監査出力を追加する。
6. CLIとSQLite Providerを追加し、データ不足・未対応券種を明示する。
7. 実組み合わせオッズ・完全払戻表の取得後、馬連、ワイド、3連複を順に追加する。

## 未確定事項

- オッズ・払戻・確定結果の公式取得元、利用規約、保存頻度、再取得方針。
- 予想時点を発走直前、出馬表公開時、または固定時刻のどれに定義するか。
- 取消、除外、同着、返還、降着、不成立の券種別精算規則。
- 払戻表の完全性を情報源ごとにどのように判定するか。
- 未精算レースを将来部分精算するか、常にレース全体除外とするか。
- 複数Strategy比較時の資金曲線を独立資金とするか、共通資金とするか。
- 現行データへ `available_at` / `observed_at` をどの履歴から補完可能か。

未確定の精算ルールは、実装時に推測で補わない。仕様が確定するまで `VOID`、`UNSETTLED`、または `unsupported` として明示的に扱う。

## Phase 4C-2d3b1i6a preliminary note — superseded

### Purpose and non-goals

An official historical simulation must prove which prediction inputs were available at its information
cutoff. This phase approves the prospective persistence design needed to retain that proof. It does not
add a schema, migration, repository, DB-backed request source, provider, CLI behavior, or data backfill.

The former canonical sample-request candidate is `REJECTED_AS_NEXT_PHASE`. A sample request can document
an already auditable source later, but cannot manufacture historical provenance.

### Canonical time semantics

All prospective persisted timestamps are timezone-aware UTC ISO timestamps.

| Field | Meaning | Prediction-input use |
| --- | --- | --- |
| `available_at` | Time the source made the exact information publicly usable. | Proves source availability before the cutoff. |
| `observed_at` | Time KeibaOS observed or stored that exact source value. | Proves KeibaOS had the exact value before the cutoff. |
| `captured_at` | Time one complete race-level prediction-input snapshot was recorded. | Identifies and orders an immutable complete snapshot. |
| `finalized_at` | Time settlement information became final. | Settlement only; never prediction-input audit evidence. |

`available_at`, `observed_at`, and `captured_at` are distinct facts and must not be substituted.
`available_at` is a fact generated by, or explicitly attested by, the source record; `observed_at` is a
fact generated by KeibaOS capture of that exact record. A stored database row time is not `observed_at`
unless the capture process establishes that provenance. Unknown or timezone-unknown timestamps fail
closed.

Every `InputAuditEntry` must have `available_at` or `observed_at` (or both):

- **Observed only:** valid only when KeibaOS recorded the exact source value at or before the cutoff and
  can identify the source record. It does not assert a known source publication time.
- **Available only:** valid only when the source attests the exact value was public at or before the cutoff
  and the full snapshot was captured no later than that cutoff. It cannot be a later reconstruction.
- **Both:** both facts must describe the same source value and require
  `available_at <= observed_at <= captured_at`; any contrary ordering fails closed.
- **Neither:** invalid. The input cannot be selected for an official historical simulation.

### Approved snapshot unit and normalized persistence boundary

The official future persistence unit is one **complete race-level prediction-input snapshot**. It has a
stable `snapshot_id`, logical provenance for one `race_id`, one `information_cutoff`, one `dataset_id`,
and one `captured_at`. Normalized child rows reconstruct its prediction input; a schemaless JSON blob is
not approved.

The prospective snapshot contains these normalized groups, each with the applicable `InputAuditEntry`,
source metadata, stable source ID, source URL where supplied, relation to race/race entry, timestamps,
and completeness evidence:

| Content group | Natural relation / identity | Completeness and ordering |
| --- | --- | --- |
| Race metadata | `race_id` in the snapshot | Complete race audit, canonical race date, and scheduled start are required. |
| Race entries | `(snapshot_id, race_entry_id)` | Complete non-empty set in deterministic `race_entry_id` order. |
| Jockey data | one row per race entry | Audited source record for the exact race entry. |
| Track conditions | one row per snapshot | Audited `track` record. |
| Win odds | one batch per race, bet type, and snapshot | Complete batch with auditable selection-to-entry mapping. |
| Past races | `(snapshot_id, race_entry_id, past_race_index)` | Full fields and deterministic past-race index. |
| Past-race absence evidence | `(snapshot_id, race_entry_id)` | Audited statement of an empty applicable history. |

`source_id` must be a provider external ID, canonical URL, or a later-approved canonical content digest.
It must never use `hash()`, insertion order, or a random UUID. The later schema/repository approval must
define insert-only behavior, idempotency identity, conflicts, data-integrity errors, foreign keys, unique
constraints, indexes, and transactional writes while retaining IDs and explicit order fields.

### Cutoff selection and fail-closed rule

A future DB-backed source selects by `race_id`, `information_cutoff`, input type, and approved source
policy. It may select only one complete snapshot when its header `captured_at` and every relevant non-null
`available_at` and `observed_at` are no later than the cutoff. All required groups and audit records must
be valid and belong to that same snapshot. Components must never be mixed from another snapshot, later
record, or fallback.

When several complete candidates remain, a future repository selects deterministically by latest
`captured_at`, then `snapshot_id` descending. Missing, incomplete, invalid, conflicting, or future-dated
provenance is unresolved and fails closed.

### Existing data, odds, and provider identity

Legacy `races`, `horses`, and `past_races` lack the required source provenance and historical audit
timestamps. They may remain references or prospective capture sources, but cannot be backfilled or used
as formal historical prediction input for DB-backed simulation.

v008 `odds_snapshot_batches`, `odds_snapshots`, and `odds_snapshot_selections` retain `observed_at`,
`is_complete`, `source`, and `source_url`, but not `available_at`. Until a later phase approves the
authoritative observed-only policy, the missing `available_at` means these rows cannot support official
historical odds validation. That later phase must decide whether odds require `available_at`, complete
batch granularity for each race/bet type, and the exact win-odds selection-to-entry mapping. Legacy
`horses.odds` has no auditable timestamp and is prohibited for official historical odds validation.

A future source contract must distinguish organization, source system, provider race and entry IDs,
canonical source URL, internal race/race-entry map, and horse number. Existing `horses.id` is an internal
race-scoped race-entry ID, and `horse_no` is a local race number; neither is a provider external identity.
No JRA/local provider implementation is approved in this phase.

### Settlement separation and follow-up split

`race_results`, `race_result_entries`, `payout_publications`, and `payouts` are settlement data. Their
`finalized_at`, `observed_at`, source, and source URL must never establish prediction-input availability.

The approved follow-up sequence is: schema/domain design approval, migration, repository contracts,
SQLite repository implementation, then request-source integration. Each phase preserves the normalized
race-level snapshot and fail-closed cutoff policy above.

The preceding preliminary note is superseded by the approved contracts below.

## Phase 4C-2d3b1i6a — Revised historical input snapshot and audit persistence design

### Boundary and natural identity

An official historical input is one immutable, complete, normalized race-level `HistoricalInputSnapshot`.
It is neither request JSON nor a schemaless blob, and it never contains settlement evidence. Its natural
content identity is `(organization, source_system, external_race_id, captured_at, content_sha256)`.
`dataset_id`, internal `race_id`, and `information_cutoff` are required recorded facts but are not identity
components; a SQLite surrogate ID is storage-only.

### Field-to-source and audit mapping

| Request field group | Snapshot/source field | Source ID and audit key | Completeness / legacy policy |
| --- | --- | --- | --- |
| race ID, date, scheduled start | `HistoricalRaceSnapshot` source-race fields | `race:{organization}:{source_system}:{external_race_id}`; `race` | Canonical date and aware start required; legacy `races` is reference-only. |
| track place, distance, type, condition | race snapshot track fields | provider record ID, canonical URL, or digest; `track` | All fields plus provenance required; legacy fields alone fail closed. |
| race entry ID | `HistoricalRaceEntrySnapshot` plus source-entry map | `entry:{organization}:{source_system}:{external_race_id}:{external_entry_id}`; `entry/{race_entry_id}` | Non-empty unique mapped entry set; legacy `horses` alone fails closed. |
| jockey name | entry `jockey_name` | provider entry/jockey record; `jockey/{race_entry_id}` | Required once per entry. |
| win odds | entry `win_odds` plus batch metadata | approved odds record identity; `odds/{race_entry_id}` | One complete WIN batch covering every entry; `horses.odds` is always ineligible. |
| past-race date/place/distance/finish/odds/jockey/passing order | `HistoricalPastRaceSnapshot` | provider past-race record; `past_race/{race_entry_id}/{past_race_index}` | Full record and unique canonical index; legacy `past_races` is reference-only. |
| no past race | explicit absence provenance | source query/batch identity; `past_race/{race_entry_id}/none` | Required exactly once only when that entry has no past-race child. |

`source_url` is stored when supplied by the provider. It is optional only when a stable provider external ID
exists; otherwise a canonical URL or canonical digest is mandatory. The canonical digest is SHA-256
lowercase hex of UTF-8 JSON with sorted keys, compact separators, and `ensure_ascii=False`. Python
`hash()`, random UUIDs, insertion order, local row IDs, and filenames are forbidden source identity.

### Audit and time contract

Each source field yields one `InputAuditEntry` containing `input_type`, `audit_key`, `source`, `source_id`,
`race_entry_id`, `available_at`, `observed_at`, and `past_race_index`. Keys are unique per snapshot;
race/track keys omit entry ID, past-race index occurs only on a past-race record, and absence cannot coexist
with a past-race record for the same entry.

`available_at` is the provider-attested public time for the exact record; `observed_at` is KeibaOS's
collection-boundary observation time for that exact record; `captured_at` records the complete snapshot;
`finalized_at` is settlement-only and prohibited here. All are aware UTC ISO values. At least one of
`available_at` and `observed_at` is required; when both exist, `available_at <= observed_at` is required.
`captured_at` is no earlier than every included observation. Malformed, naive, unknown, or future-for-
cutoff timestamps fail closed.

Observed-only is official only for an immutable insert-only approved collection boundary with stable source
identity, complete batch membership, and `observed_at <= cutoff`. Available-only is official only when the
provider attests the exact public record and `available_at <= cutoff`; later reconstruction is forbidden.

### Domain values and Protocols

The later domain-values phase defines frozen exact-type dataclasses with no package-root export:
`HistoricalSourceIdentity`, `HistoricalInputProvenance`, `HistoricalPastRaceSnapshot`,
`HistoricalRaceEntrySnapshot`, `HistoricalRaceSnapshot`, `HistoricalInputSnapshotIdentity`, and
`HistoricalInputSnapshot`. Sequence fields are tuples, mappings immutable, IDs positive non-bool integers,
identity text non-empty, and construction owns canonicalization and validation.

```python
class HistoricalInputSnapshotSource(Protocol):
    def load_latest_snapshot(
        self,
        *,
        race_id: int,
        information_cutoff: datetime,
        source_identity: HistoricalSourceIdentity | None = None,
    ) -> HistoricalInputSnapshot | None:
        ...


class HistoricalInputSnapshotRepository(Protocol):
    def save_snapshot(
        self,
        *,
        snapshot: HistoricalInputSnapshot,
    ) -> None:
        ...
```

Both APIs are keyword-only. There is no list API, runtime Protocol check, request-JSON creation,
prediction/settlement call, or package export. `None` means no eligible snapshot; malformed stored data is
an integrity error, never `None`.

### SQLite normalized schema

The migration phase creates the following tables and does not copy legacy rows into them.

| Table | Required columns and natural identity | Constraints and indexes |
| --- | --- | --- |
| `historical_input_source_races` | organization, source system, external race ID, internal race ID, source URL; PK `(organization, source_system, external_race_id)` | FK internal race; unique source-system mapping; index `(race_id, organization, source_system)`. |
| `historical_input_source_entries` | source-race identity, external entry ID, internal race-entry ID, external horse ID, horse number | PK source-race identity plus external entry ID; FK source race/internal entry; unique mapped entry; index internal entry. |
| `historical_input_snapshots` | snapshot ID, dataset, source-race identity, internal race ID, information cutoff UTC, captured UTC, content SHA-256, complete flag | unique `(organization, source_system, external_race_id, captured_at_utc, content_sha256)`; FKs; index `(race_id, is_complete, captured_at_utc DESC, snapshot_id DESC)`. |
| `historical_input_snapshot_races` | snapshot ID, race/track values, source ID/URL, availability and observation values | PK/FK snapshot ID; required race/track values and audit-time checks. |
| `historical_input_snapshot_entries` | snapshot ID, race-entry ID, external entry ID, jockey, win odds, entry order, source fields/times | PK `(snapshot_id, race_entry_id)`; unique entry order and external entry; FKs; reconstruction index. |
| `historical_input_snapshot_past_races` | snapshot ID, race-entry ID, past-race index, full past fields, source order, source fields/times | PK `(snapshot_id, race_entry_id, past_race_index)`; FK entry; unique source order per entry; reconstruction index. |
| `historical_input_snapshot_audits` | snapshot ID, audit key, input type, source/source ID, optional entry/index, availability/observation | PK `(snapshot_id, audit_key)`; FK snapshot; audit relation and timestamp checks; index `(snapshot_id, audit_key)`. |

SQLite checks require positive internal IDs, non-empty source/source-ID text, `is_complete IN (0,1)`, UTC
ISO shape, at least one audit time, and `available_at <= observed_at` when both exist. Domain construction
and repository loads enforce full ISO parsing, canonical dates, cross-table relation, audit correspondence,
and query-cutoff validation; no trigger is approved. Child order is explicit, never insertion order.

### Repository write and read responsibility

The SQLite writer accepts a caller-owned injected connection, verifies foreign keys, uses one
`BEGIN IMMEDIATE` transaction, validates the complete immutable snapshot, and atomically inserts header,
race, entry, past-race, and audit rows. It is insert-only: same natural identity plus same canonical content
is an idempotent no-op; same identity plus different content raises `RepositoryConflictError`; validation
raises the existing validation error; constraint/corruption raises `RepositoryDataIntegrityError`. Any error
rolls back all writes. Update, delete, repair, retry, and fallback are forbidden.

The read source accepts the Protocol query, considers only complete snapshots whose header and all relevant
audit timestamps are no later than the inclusive cutoff, then orders by `captured_at_utc DESC, snapshot_id
DESC`. It loads children in explicit deterministic order and validates duplicates, orphans, race mismatch,
timestamp parsing, audit correspondence, and corruption. Not found returns `None`; invalid stored data
raises `RepositoryDataIntegrityError`.

### Odds, JRA, and NAR policy

Future sources do not read v008 odds rows directly, and migration never copies them automatically. An
approved future importer/capture boundary may create a new snapshot from a v008 WIN batch only if its
`observed_at` comes from the immutable approved collection boundary, the batch is complete,
`observed_at <= cutoff`, source plus canonical URL/digest identity exists, and each selection maps exactly
once to a snapshot entry. In exactly that observed-only case, missing `available_at` is permitted. Every
other v008 batch and every `horses.odds` record fails closed. Candidate v008 batches tie-break by
`observed_at DESC, batch_id DESC` before import.

Organizations are exactly `JRA` and `NAR`. Provider race identity is
`(source_system, external_race_id)`; provider entry identity is
`(source_system, external_race_id, external_entry_id)`. External horse ID is optional provider metadata.
The source-map tables bind them to internal `race_id` and race-scoped `race_entry_id`; `horse_no` is a local
race number, never an external entry or horse identity.

### Completeness, reconstruction, and phase split

`is_complete=True` requires every entry, each jockey and WIN odds value, one track record, past-race
children or one valid absence record per entry, every required audit key, stable source identity, and
cutoff-eligible provenance. Missing, duplicate, orphaned, or mismatched content cannot be selected.
Reconstruction uses entries `race_entry_id ASC`, past races canonical race date descending then
`source_order ASC`, audits `audit_key ASC`, and odds selections `race_entry_id ASC`.

The minimal follow-up sequence is `1i6b1` domain values and Protocols, `1i6b2` migration/schema, `1i6b3`
SQLite write repository, `1i6b4` SQLite read source, then `1i6c` audited DB-backed request source. No
implementation is authorized by this design. All 1i6a criteria are complete; the phase-level blocker is
`none`.

## Phase 4C-2d3b1i6a — Final contract revision (authoritative)

This section supersedes every earlier 1i6a statement that conflicts with it.

### Identity and domain contract

The sole snapshot identity, used by `HistoricalInputSnapshotIdentity.__eq__`, `__hash__`, repository
idempotency, and SQLite `UNIQUE`, is `(dataset_id, organization, source_system, external_race_id,
captured_at_utc, content_sha256)`. Internal `race_id` and `race_entry_id` are FK linkage only; cutoff is a
lookup condition only; `snapshot_id INTEGER PRIMARY KEY` is a surrogate only.

All domain values live in `scripts.simulation.historical_input_snapshots`, are
`@dataclass(frozen=True, slots=True)`, reject subclasses, use UTC-aware `datetime`, canonical `YYYY-MM-DD`
dates, non-empty NFC-normalized identity strings, positive non-bool internal IDs, tuples for sequences,
and `MappingProxyType` for mappings. The required values are `HistoricalSourceIdentity(organization,
source_system, external_race_id, source_url)`, `HistoricalExternalRaceIdentity(organization,
source_system, external_race_id)`, `HistoricalExternalEntryIdentity(external_race_identity,
external_entry_id, external_horse_id)`, `HistoricalInputSnapshotIdentity(dataset_id, source_identity,
captured_at, content_sha256)`, `HistoricalRaceSnapshot`, `HistoricalRaceEntrySnapshot`,
`HistoricalPastRaceSnapshot`, `HistoricalInputProvenance`, and `HistoricalInputSnapshot`. Derived fields
are never stored as identity fields; DB serialization is direct scalar ISO/text/integer/real conversion.

### DDL contract

The migration must create exactly these normalized tables: `historical_input_source_identities`,
`historical_input_external_races`, `historical_input_external_entries`, `historical_input_snapshots`,
`historical_input_snapshot_races`, `historical_input_snapshot_entries`,
`historical_input_snapshot_past_races`, and `historical_input_snapshot_provenance`.

All IDs are `INTEGER NOT NULL`; all identity/source text is `TEXT NOT NULL`; URLs and external horse IDs
are nullable; UTC values are `TEXT NOT NULL` in canonical `...Z` form; optional availability/observation
times are nullable TEXT; ordering columns are `INTEGER NOT NULL`; monetary/odds values are canonical TEXT.
Each child FK uses `ON DELETE RESTRICT`. Header has `UNIQUE(dataset_id, organization, source_system,
external_race_id, captured_at_utc, content_sha256)`. Source race has
`UNIQUE(source_system, external_race_id)`; source entry has
`UNIQUE(source_system, external_race_id, external_entry_id)`; snapshot entry has
`UNIQUE(snapshot_id, race_entry_id)`, `UNIQUE(snapshot_id, horse_no)`, and
`UNIQUE(snapshot_id, entry_order)`; past race has `UNIQUE(snapshot_id, race_entry_id, past_race_index)`;
provenance has `UNIQUE(snapshot_id, audit_key)`.

`CHECK` requires organizations `JRA`/`NAR`, positive IDs/orders, non-empty source/source ID, complete flag
in `(0,1)`, one audit time, and `available_at_utc <= observed_at_utc` when both exist. Triggers reject a
complete header without its race row, source/external mapping, every entry's jockey/odds/provenance, and
past-race-or-absence evidence; they also reject orphan/mismatched child and provenance rows. Required
indexes cover identity lookup, source-race lookup, `(race_id,is_complete,captured_at_utc)`, external entry,
ordered children, audit key, and cutoff selection. Canonical ISO parsing and cross-row request-field checks
remain domain/repository validation.

### Field and provenance crosswalk

Race metadata and track fields map to `historical_input_snapshot_races`; entry ID/horse number/jockey/WIN
odds map to `historical_input_snapshot_entries`; every listed past-race field maps to
`historical_input_snapshot_past_races`; absence maps to one provenance row. Every such field has a
provenance row mapping one-to-one to `InputAuditEntry(input_type,audit_key,source,source_id,race_entry_id,
available_at,observed_at,past_race_index)`. Source fields must explicitly say provider-supplied,
not-provided, not-persisted, or forbidden-to-infer; only an approved capture boundary may write
`observed_at`. Legacy rows are reference-only and never snapshot input.

Source IDs are NFC-normalized, case-sensitive, percent-escape `:` and `/`, and use exactly
`{source_system}:race:{external_race_id}`, `{source_system}:race:{external_race_id}:entry:{external_entry_id}`,
or `{source_system}:race:{external_race_id}:odds:win:{batch_digest}`. A null URL requires provider record
identity or SHA-256 digest of canonical UTF-8, sorted-key, compact, Decimal-as-fixed-string batch payload.

### Repository and selection contract

Repository constructor accepts a caller-owned `sqlite3.Connection`, verifies `foreign_keys=ON`, never
closes it, and raises `RepositoryDataIntegrityError` if unavailable. `save_snapshot` rejects an active
caller transaction with `RepositoryValidationError`; it then owns `BEGIN IMMEDIATE`, identity lookup, and
commit/rollback. Same identity plus byte-for-byte canonical reconstructed content commits no new rows;
different content raises `RepositoryConflictError`; validation, corruption, SQLite integrity, and
unexpected operational errors retain their respective existing exception identities.

`load_latest_snapshot` is inclusive at cutoff, selects complete rows only, applies the optional source
filter, and ties by `captured_at_utc DESC, organization ASC, source_system ASC, external_race_id ASC,
content_sha256 ASC`—never surrogate ID. Not found is `None`; corrupt rows are integrity errors. It loads
entries by `race_entry_id ASC`, past races by date DESC then source order ASC, and audits by key ASC.

`is_complete` requires complete header/external/internal mapping, race metadata, track, every entry and
jockey/odds, every required audit, and either past races or one absence evidence per entry. Scratched,
excluded, unannounced jockey, unpublished track, unavailable odds, incomplete source, and mismatch are
explicit incomplete states and fail closed.

## Phase 4C-2d3b1i6a — Cross-contract revision V2 (authoritative)

This section supersedes all prior 1i6a identity, API, DDL, timestamp, order, provenance, organization,
and v008 statements.

**Identity.** Snapshot natural identity is exactly `(dataset_id, organization, source_system,
external_race_id, captured_at_utc)`. `content_sha256` is not identity: same identity plus same recomputed
digest and canonical reconstruction is an idempotent no-op; different digest/content is
`RepositoryConflictError`; stored-digest mismatch is `RepositoryDataIntegrityError`. Internal race IDs are
FK linkage only. External race identity is `(organization, source_system, external_race_id)` and external
entry identity adds `external_entry_id`; SQLite PK/UNIQUE fields match exactly. `source_url` is not equality
or snapshot identity (`compare=False`).

**Organization.** `organization="JRA"` requires `source_system="jra_official"`. Local organizers use a
provider-independent canonical organizer code (not `NAR`) with `source_system="nar_official"`; `NAR` is the
source-system family, never the local organizer's identity.

**Exact source API.**
```python
class HistoricalInputSnapshotSource(Protocol):
    def load_latest_snapshot(self, *, dataset_id: str, race_id: int,
        information_cutoff: datetime,
        source_identity: HistoricalExternalRaceIdentity | None = None,
    ) -> HistoricalInputSnapshot | None: ...
```
Dataset is mandatory and there is no cross-dataset fallback. Cutoff is inclusive; source filtering uses the
complete external identity; none means not found only.

**Canonical storage.** Every UTC timestamp is exactly
`YYYY-MM-DDTHH:MM:SS.ffffff+00:00`; save uses UTC `isoformat(timespec="microseconds")`, load requires the
same text after aware UTC parsing. `entry_order`, `past_race_index`, and `source_order` are zero-based,
contiguous sequences; checks use `>= 0`, never `> 0`.

**DDL and transaction.** The migration contains executable `CREATE TABLE`, `CREATE INDEX`, and only
child-linkage `CREATE TRIGGER` statements for the eight normalized tables already named. Each DDL states
types/nullability/PK/FK `ON DELETE RESTRICT`/UNIQUE/CHECK/default/order/domain crosswalk. No trigger checks
complete header child existence on header insertion; domain save validation validates complete snapshots
before write, FK/UNIQUE/CHECK/triggers protect links, and load validates full completeness/corruption.
Writer rejects `connection.in_transaction` with `RepositoryValidationError`, then owns `BEGIN IMMEDIATE`,
lookup, atomic inserts, commit, and rollback; it never closes the caller connection.

**Provenance.** One `HistoricalInputProvenance` maps one-to-one to one logical `InputAuditEntry`, not scalar
fields. `track` covers all track scalars; one past-race key covers its full record. Required keys are entry,
jockey, odds, track, past race, and absence. The source matrix explicitly names provider field or one of
`not provided by provider`, `not persisted`, `forbidden to infer`, `supplied by approved capture boundary`
for every availability/observation input.

**v008.** Every pre-154c04d odds row is untrusted. Trusted import is prospective only from a new capture
boundary carrying collector contract ID/version, observed time, source identity, canonical digest, complete
batch identity, and no-backfill evidence. Null URL requires provider identity or SHA-256 of canonical batch
payload: schema version, external race/entry identities, WIN type, observed/available times, source/URL,
complete flag, selections in canonical order, Decimal fixed strings, UTF-8, `ensure_ascii=False`, sorted
keys, compact separators, and `+00:00` datetimes. `horses.odds` is always forbidden.

### v008 odds and boundaries

A v008 batch is trusted only when created by the approved immutable insert-only collector, has valid UTC
`observed_at`, complete WIN selections mapping once to entries, stable source identity or canonical digest,
and no post-cutoff backfill. It is otherwise untrusted; `horses.odds` is always forbidden. Missing
`available_at` is permitted only for such trusted observed-only batches. A later migration may add nullable
`available_at` to odds batches, but its authoritative use is only through the historical snapshot linkage.
Settlement tables never contribute provenance. The later split remains 1i6b1 domain/Protocols, 1i6b2 DDL,
1i6b3 writer, 1i6b4 reader, 1i6c request source.
## Phase 4C-2d3b1i6a — Historical input snapshot and audit persistence working contract

Overall 1i6a remains `REVISION_REQUIRED` and is not approved for implementation. This section replaces
earlier 1i6a draft wording only where V3a explicitly defines domain values, identity, digest, and Protocol
API. Production is not authorized. The snapshot identity is dataset, organization, source system, external
race ID, and captured UTC time; digest validates content only. V3b must define executable DDL, V3c must
define source mapping and observed-only policy, and V3d must consolidate the complete contract. Existing
v008 rows remain untrusted in this V3a slice; no observed-only eligibility decision is made here.
### V3a — Domain, identity, digest, and Protocol contract

V3a is authoritative only for the future domain values, identity, digest, and Protocol API. It does not
approve executable DDL, source mapping or observed-only policy, repository behavior, or any production
implementation. Those remain V3b, V3c, and V3d work.

#### Nine frozen domain values and construction contract

The future module is `scripts.simulation.historical_input_snapshots`. Its public construction contract is
executable Python-equivalent design, not an API sketch. Every direct construction failure below raises
`ValueError`; no constructor coerces a list to a tuple, accepts a subclass for an exact domain field, or
silently repairs malformed input.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Protocol
from unicodedata import normalize
```

The private helpers have these exact contracts. Each rejects an invalid value with `ValueError`. The helpers
are private to the future module and do not create a package-root export.

```python
def _require_exact(value: object, expected: type[object], name: str) -> object: ...
def _normalize_required_text(value: object, name: str) -> str: ...
def _normalize_text_allow_empty(value: object, name: str) -> str: ...
def _normalize_optional_text(value: object, name: str) -> str | None: ...
def _normalize_utc_datetime(value: object, name: str) -> datetime: ...
def _normalize_optional_utc_datetime(value: object, name: str) -> datetime | None: ...
def _normalize_date(value: object, name: str) -> date: ...
def _canonical_decimal(value: Decimal) -> Decimal: ...
def _normalize_decimal(value: object, name: str, *, positive: bool = False,
                       non_negative: bool = False) -> Decimal: ...
def _positive_int(value: object, name: str) -> int: ...
def _non_negative_int(value: object, name: str) -> int: ...
def _require_tuple(value: object, name: str) -> tuple[object, ...]: ...
def _require_unique(values: tuple[object, ...], name: str) -> None: ...
def _validate_provenance_shape(provenance: HistoricalInputProvenance) -> None: ...
def _validate_snapshot_children(*, entries: tuple[object, ...],
    past_races: tuple[object, ...], provenance: tuple[object, ...],
    race: HistoricalRaceSnapshot, identity: HistoricalInputSnapshotIdentity,
    information_cutoff: datetime) -> None: ...
def _build_unchecked_historical_input_snapshot_content_payload(
    *,
    snapshot: HistoricalInputSnapshot,
) -> dict[str, object]: ...
def _sha256_canonical_payload(payload: dict[str, object]) -> str: ...
```

`_require_exact` uses `type(value) is expected`. Text helpers require a `str`, normalize with
`normalize(\"NFC\", value)`, and reject empty normalized text; the optional version accepts only `None` or
such a string. Integer helpers reject `bool` and require exact `int`. The datetime helpers require exact
`datetime`, a non-`None` offset, convert with `astimezone(timezone.utc)`, and return the converted value.
The date helper requires exact `date` rather than `datetime`. Decimal validation requires exact `Decimal`,
`is_finite()`, then uses `_canonical_decimal()`: zero (including negative zero) becomes `Decimal(\"0\")`;
every non-zero value becomes `value.normalize()`. `_normalize_decimal()` performs its positive or
non-negative check before returning that canonical Decimal. The tuple helper requires
`type(value) is tuple`. Every `__post_init__` below uses these helpers and records normalized immutable
values only through `object.__setattr__`.

`_normalize_text_allow_empty()` is the sole exception to the non-empty-text rule:

```python
def _normalize_text_allow_empty(value: object, name: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be str")
    return normalize("NFC", value)
```

It is used only for `HistoricalPastRaceSnapshot.passing_order`, because the existing `PastRace` contract
defines its missing value as `""`.

```python
@dataclass(frozen=True, slots=True)
class HistoricalSourceIdentity:
    organization: str
    source_system: str
    external_race_id: str
    source_url: str | None = field(default=None, compare=False, hash=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, \"organization\",
                           _normalize_required_text(self.organization, \"organization\"))
        object.__setattr__(self, \"source_system\",
                           _normalize_required_text(self.source_system, \"source_system\"))
        object.__setattr__(self, \"external_race_id\",
                           _normalize_required_text(self.external_race_id, \"external_race_id\"))
        object.__setattr__(self, \"source_url\",
                           _normalize_optional_text(self.source_url, \"source_url\"))
```

`source_url` is nullable final-field metadata and never participates in identity, equality, or hashing.

```python
@dataclass(frozen=True, slots=True)
class HistoricalExternalRaceIdentity:
    organization: str
    source_system: str
    external_race_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, \"organization\",
                           _normalize_required_text(self.organization, \"organization\"))
        object.__setattr__(self, \"source_system\",
                           _normalize_required_text(self.source_system, \"source_system\"))
        object.__setattr__(self, \"external_race_id\",
                           _normalize_required_text(self.external_race_id, \"external_race_id\"))
```

```python
@dataclass(frozen=True, slots=True)
class HistoricalExternalEntryIdentity:
    external_race_identity: HistoricalExternalRaceIdentity
    external_entry_id: str
    external_horse_id: str | None = field(default=None, compare=False, hash=False)

    def __post_init__(self) -> None:
        _require_exact(self.external_race_identity, HistoricalExternalRaceIdentity,
                       \"external_race_identity\")
        object.__setattr__(self, \"external_entry_id\",
                           _normalize_required_text(self.external_entry_id, \"external_entry_id\"))
        object.__setattr__(self, \"external_horse_id\",
                           _normalize_optional_text(self.external_horse_id, \"external_horse_id\"))
```

The external-entry natural identity is exactly `(organization, source_system, external_race_id,
external_entry_id)`. `external_horse_id` is optional provider metadata only: it is excluded from equality
and hashing, and duplicate-entry validation uses the natural identity without it.

```python
@dataclass(frozen=True, slots=True)
class HistoricalInputSnapshotIdentity:
    dataset_id: str
    source_identity: HistoricalSourceIdentity
    captured_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, \"dataset_id\",
                           _normalize_required_text(self.dataset_id, \"dataset_id\"))
        _require_exact(self.source_identity, HistoricalSourceIdentity, \"source_identity\")
        object.__setattr__(self, \"captured_at\",
                           _normalize_utc_datetime(self.captured_at, \"captured_at\"))
```

The equality and hash key is exactly `(dataset_id, organization, source_system, external_race_id,
captured_at)`. `source_url`, content digest, internal IDs, cutoff, and future SQLite surrogates are
excluded.

`HistoricalInputSnapshotIdentity` equality is the natural-identity comparison above.
`HistoricalInputSnapshot.content_sha256` is the canonical immutable-content comparison. Repository
idempotency and conflict detection must never use the snapshot dataclass equality: same natural identity and
same digest is an idempotent no-op, while same natural identity and different digest raises
`RepositoryConflictError`. `source_url` and `external_horse_id` are excluded from identity/equality/hash,
but are present in canonical content payload and therefore change the digest when their metadata changes.

```python
@dataclass(frozen=True, slots=True)
class HistoricalRaceSnapshot:
    target_race_date: date
    scheduled_start_at: datetime
    place: str
    distance_m: int
    track: str
    track_condition: str
    race_name: str | None = None
    race_class: str | None = None
    weather: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, \"target_race_date\",
                           _normalize_date(self.target_race_date, \"target_race_date\"))
        object.__setattr__(self, \"scheduled_start_at\",
                           _normalize_utc_datetime(self.scheduled_start_at, \"scheduled_start_at\"))
        object.__setattr__(self, \"place\", _normalize_required_text(self.place, \"place\"))
        object.__setattr__(self, \"distance_m\", _positive_int(self.distance_m, \"distance_m\"))
        object.__setattr__(self, \"track\", _normalize_required_text(self.track, \"track\"))
        object.__setattr__(self, \"track_condition\",
                           _normalize_required_text(self.track_condition, \"track_condition\"))
        object.__setattr__(self, \"race_name\", _normalize_optional_text(self.race_name, \"race_name\"))
        object.__setattr__(self, \"race_class\", _normalize_optional_text(self.race_class, \"race_class\"))
        object.__setattr__(self, \"weather\", _normalize_optional_text(self.weather, \"weather\"))
```

`target_race_date` and `scheduled_start_at` are required to reconstruct `SimulationRaceInput`. Optional
`race_name`, `race_class`, and `weather` are retained as historical content only; they are not required by
the current prediction-input constructor.

```python
@dataclass(frozen=True, slots=True)
class HistoricalRaceEntrySnapshot:
    race_entry_id: int
    external_entry_identity: HistoricalExternalEntryIdentity
    horse_no: int
    jockey: str
    win_odds: Decimal
    entry_order: int

    def __post_init__(self) -> None:
        object.__setattr__(self, \"race_entry_id\", _positive_int(self.race_entry_id, \"race_entry_id\"))
        _require_exact(self.external_entry_identity, HistoricalExternalEntryIdentity,
                       \"external_entry_identity\")
        object.__setattr__(self, \"horse_no\", _positive_int(self.horse_no, \"horse_no\"))
        object.__setattr__(self, \"jockey\", _normalize_required_text(self.jockey, \"jockey\"))
        object.__setattr__(self, \"win_odds\",
                           _normalize_decimal(self.win_odds, \"win_odds\", positive=True))
        object.__setattr__(self, \"entry_order\",
                           _non_negative_int(self.entry_order, \"entry_order\"))
```

```python
@dataclass(frozen=True, slots=True)
class HistoricalPastRaceSnapshot:
    race_entry_id: int
    past_race_index: int
    race_date: date
    place: str
    race_name: str
    race_class: str
    distance_m: int
    track: str
    weather: str
    track_condition: str
    finish: int
    margin: Decimal
    race_time: str
    weight: Decimal
    weight_diff: Decimal
    jockey: str
    popularity: int
    odds: Decimal
    passing_order: str
    fourth_corner_position: int

    def __post_init__(self) -> None:
        object.__setattr__(self, \"race_entry_id\", _positive_int(self.race_entry_id, \"race_entry_id\"))
        object.__setattr__(self, \"past_race_index\",
                           _non_negative_int(self.past_race_index, \"past_race_index\"))
        object.__setattr__(self, \"race_date\", _normalize_date(self.race_date, \"race_date\"))
        for name in (\"place\", \"race_name\", \"race_class\", \"track\", \"weather\", \"track_condition\",
                     \"race_time\", \"jockey\"):
            object.__setattr__(self, name, _normalize_required_text(getattr(self, name), name))
        object.__setattr__(
            self,
            \"passing_order\",
            _normalize_text_allow_empty(self.passing_order, \"passing_order\"),
        )
        object.__setattr__(self, \"distance_m\", _positive_int(self.distance_m, \"distance_m\"))
        object.__setattr__(self, \"finish\", _positive_int(self.finish, \"finish\"))
        object.__setattr__(self, \"margin\", _normalize_decimal(self.margin, \"margin\"))
        object.__setattr__(self, \"weight\",
                           _normalize_decimal(self.weight, \"weight\", non_negative=True))
        object.__setattr__(self, \"weight_diff\", _normalize_decimal(self.weight_diff, \"weight_diff\"))
        object.__setattr__(self, \"popularity\", _non_negative_int(self.popularity, \"popularity\"))
        object.__setattr__(self, \"odds\",
                           _normalize_decimal(self.odds, \"odds\", non_negative=True))
        object.__setattr__(self, \"fourth_corner_position\",
                           _non_negative_int(self.fourth_corner_position, \"fourth_corner_position\"))
```

```python
@dataclass(frozen=True, slots=True)
class HistoricalInputProvenance:
    input_type: str
    audit_key: str
    source: str
    source_id: str
    race_entry_id: int | None
    available_at: datetime | None = None
    observed_at: datetime | None = None
    past_race_index: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, \"input_type\",
                           _normalize_required_text(self.input_type, \"input_type\"))
        object.__setattr__(self, \"audit_key\",
                           _normalize_required_text(self.audit_key, \"audit_key\"))
        object.__setattr__(self, \"source\", _normalize_required_text(self.source, \"source\"))
        object.__setattr__(self, \"source_id\", _normalize_required_text(self.source_id, \"source_id\"))
        if self.race_entry_id is not None:
            object.__setattr__(self, \"race_entry_id\",
                               _positive_int(self.race_entry_id, \"race_entry_id\"))
        object.__setattr__(self, \"available_at\",
                           _normalize_optional_utc_datetime(self.available_at, \"available_at\"))
        object.__setattr__(self, \"observed_at\",
                           _normalize_optional_utc_datetime(self.observed_at, \"observed_at\"))
        if self.past_race_index is not None:
            object.__setattr__(self, \"past_race_index\",
                               _non_negative_int(self.past_race_index, \"past_race_index\"))
        _validate_provenance_shape(self)
```

`_validate_provenance_shape(provenance: HistoricalInputProvenance) -> None` raises `ValueError` unless
`input_type` is exactly one of `track`, `entry`, `odds`, `jockey`, or `past_race`; its `audit_key` is
exactly one of `track`, `entry/{race_entry_id}`, `odds/{race_entry_id}`,
`jockey/{race_entry_id}`, `past_race/{race_entry_id}/{past_race_index}`, or
`past_race/{race_entry_id}/none`; and its entry/index fields agree. `track` has no entry or past index;
other types require a positive entry ID. A numbered past race requires an index, while `none` requires no
index. It also requires one timestamp and `available_at <= observed_at` when both exist. Thus every
instance can be passed field-for-field to the existing `InputAuditEntry` constructor with no information
loss. There is no `race_metadata` category, `track_conditions` category, `win_odds` type,
`past_race_absence` type, or colon-delimited audit key.

```python
@dataclass(frozen=True, slots=True)
class HistoricalInputSnapshot:
    identity: HistoricalInputSnapshotIdentity
    internal_race_id: int
    information_cutoff: datetime
    race: HistoricalRaceSnapshot
    entries: tuple[HistoricalRaceEntrySnapshot, ...]
    past_races: tuple[HistoricalPastRaceSnapshot, ...]
    provenance: tuple[HistoricalInputProvenance, ...]
    content_sha256: str = field(init=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        _require_exact(self.identity, HistoricalInputSnapshotIdentity, \"identity\")
        object.__setattr__(self, \"internal_race_id\",
                           _positive_int(self.internal_race_id, \"internal_race_id\"))
        object.__setattr__(self, \"information_cutoff\",
                           _normalize_utc_datetime(self.information_cutoff, \"information_cutoff\"))
        _require_exact(self.race, HistoricalRaceSnapshot, \"race\")
        entries = _require_tuple(self.entries, \"entries\")
        past_races = _require_tuple(self.past_races, \"past_races\")
        provenance = _require_tuple(self.provenance, \"provenance\")
        _validate_snapshot_children(entries=entries, past_races=past_races, provenance=provenance,
                                    race=self.race, identity=self.identity,
                                    information_cutoff=self.information_cutoff)
        object.__setattr__(self, \"entries\", entries)
        object.__setattr__(self, \"past_races\", past_races)
        object.__setattr__(self, \"provenance\", provenance)
        payload = _build_unchecked_historical_input_snapshot_content_payload(snapshot=self)
        object.__setattr__(self, \"content_sha256\", _sha256_canonical_payload(payload))
```

`_validate_snapshot_children` requires exact child dataclass types; non-empty entries; unique
`race_entry_id`, `horse_no`, external-entry natural identity, `entry_order`, audit key, and
`(race_entry_id, past_race_index)`; contiguous entry orders and per-entry past indices from zero; every
past child to name a current entry; and exactly the compatible provenance set described above. For each
entry, it also requires:

```python
entry.external_entry_identity.external_race_identity == HistoricalExternalRaceIdentity(
    organization=identity.source_identity.organization,
    source_system=identity.source_identity.source_system,
    external_race_id=identity.source_identity.external_race_id,
)
```

This comparison uses only organization, source system, and external race ID; `source_url` is not a
comparison value. It further
requires `available_at <= observed_at <= identity.captured_at <= information_cutoff <=
race.scheduled_start_at` where both provenance timestamps exist. With only `available_at`, it requires
`available_at <= identity.captured_at`; with only `observed_at`, it requires
`observed_at <= identity.captured_at`. A past race must satisfy
`past_race.race_date < race.target_race_date`. An entry with no past child requires exactly one
`past_race/{race_entry_id}/none` record; an entry with children forbids that record.

The digest is computed only after structural validation from canonicalized fields. Construction is therefore:
(1) validate/canonicalize identity, race, children, provenance, and time relations; (2) build the private
unchecked payload; (3) compute SHA-256; (4) set the derived digest with `object.__setattr__`. The public
builder/digest functions must not be called by `__post_init__` because they perform public full validation
and would re-enter construction. A repository load reads stored `content_sha256`, constructs the domain
snapshot to recompute the derived digest, compares stored and derived values, and raises
`RepositoryDataIntegrityError` on mismatch. A repository save writes the derived value only and never
accepts a caller-supplied digest.

#### Canonical content payload and digest

Content schema version is exactly `1`. `content_sha256` is a derived field computed from the canonical
payload. It is neither constructor input nor identity component, and it is not inserted into its own payload.
The complete canonical Python payload shape is:

```python
{
    \"schema_version\": 1,
    \"snapshot_identity\": {
        \"dataset_id\": str,
        \"organization\": str,
        \"source_system\": str,
        \"external_race_id\": str,
        \"captured_at\": str,
    },
    \"source_identity\": {
        \"organization\": str,
        \"source_system\": str,
        \"external_race_id\": str,
        \"source_url\": str | None,
    },
    \"internal_race_id\": int,
    \"information_cutoff\": str,
    \"race\": {
        \"target_race_date\": str,
        \"scheduled_start_at\": str,
        \"place\": str,
        \"distance_m\": int,
        \"track\": str,
        \"track_condition\": str,
        \"race_name\": str | None,
        \"race_class\": str | None,
        \"weather\": str | None,
    },
    \"entries\": [
        {
            \"race_entry_id\": int,
            \"external_entry_identity\": {
                \"organization\": str,
                \"source_system\": str,
                \"external_race_id\": str,
                \"external_entry_id\": str,
                \"external_horse_id\": str | None,
            },
            \"horse_no\": int,
            \"jockey\": str,
            \"win_odds\": str,
            \"entry_order\": int,
        },
    ],
    \"past_races\": [
        {
            \"race_entry_id\": int,
            \"past_race_index\": int,
            \"race_date\": str,
            \"place\": str,
            \"race_name\": str,
            \"race_class\": str,
            \"distance_m\": int,
            \"track\": str,
            \"weather\": str,
            \"track_condition\": str,
            \"finish\": int,
            \"margin\": str,
            \"race_time\": str,
            \"weight\": str,
            \"weight_diff\": str,
            \"jockey\": str,
            \"popularity\": int,
            \"odds\": str,
            \"passing_order\": str,
            \"fourth_corner_position\": int,
        },
    ],
    \"provenance\": [
        {
            \"input_type\": str,
            \"audit_key\": str,
            \"source\": str,
            \"source_id\": str,
            \"available_at\": str | None,
            \"observed_at\": str | None,
            \"race_entry_id\": int | None,
            \"past_race_index\": int | None,
        },
    ],
}
```

`passing_order` remains a JSON string. When unavailable it is represented exactly as
`{"passing_order":""}`: it is never converted to `null`, omitted, or inferred.

The only builder and digest APIs are:

```python
def build_historical_input_snapshot_content_payload(
    *,
    snapshot: HistoricalInputSnapshot,
) -> dict[str, object]:
    ...
```

```python
def compute_historical_input_snapshot_content_sha256(
    *,
    snapshot: HistoricalInputSnapshot,
) -> str:
    ...
```

The public builder requires an exact `HistoricalInputSnapshot`, delegates only to the private unchecked
canonical payload helper, and returns no caller-supplied or derived `content_sha256` value. The public digest
function uses that public builder. Neither function is called by `HistoricalInputSnapshot.__post_init__`.
Serialization is UTF-8 JSON with `ensure_ascii=False`,
`sort_keys=True`, and `separators=(\",\", \":\")`. A Decimal is first canonicalized as specified above,
then serialized as `format(canonical_value, \"f\")` without exponent notation: `Decimal(\"2\")`,
`Decimal(\"2.0\")`, and `Decimal(\"2.00\")` all become `\"2\"`; `Decimal(\"0.00\")` and
`Decimal(\"-0\")` become `\"0\"`; and `Decimal(\"12.3400\")` becomes `\"12.34\"`. A `date` is
`YYYY-MM-DD`; a datetime is UTC `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`; and `None` is JSON `null`.
`bool` is never accepted as an integer. Entries are emitted by `entry_order ASC`; past races by
`race_entry_id ASC, past_race_index ASC`; provenance by `audit_key ASC`. The digest is SHA-256 of those
UTF-8 bytes, encoded as lowercase hexadecimal.

#### Exact Protocol API

The future Protocols use the following exact, keyword-only signatures. Their `source_identity` argument is
non-optional; there is no structural runtime Protocol check, fallback source, list API, or package-root
export.

```python
class HistoricalInputSnapshotSource(Protocol):
    def load_latest_snapshot(
        self,
        *,
        dataset_id: str,
        race_id: int,
        information_cutoff: datetime,
        source_identity: HistoricalExternalRaceIdentity,
    ) -> HistoricalInputSnapshot | None:
        ...
```

```python
class HistoricalInputSnapshotRepository(Protocol):
    def save_snapshot(
        self,
        *,
        snapshot: HistoricalInputSnapshot,
    ) -> None:
        ...
```

`None` means that no complete, eligible matching snapshot exists. It must not stand for malformed stored
data. Exact error, DDL, source-mapping, selection, and policy semantics remain unapproved V3b/V3c/V3d
work.

### V3b — Executable SQLite DDL and domain crosswalk

V3b is the complete DDL and storage crosswalk design for the approved V3a values. Its planned migration
identity is `v010_historical_input_snapshot_schema`. No module is created, registered, or executed in this
phase. The existing migration runner must verify `PRAGMA foreign_keys = ON` and own one per-migration
`BEGIN IMMEDIATE` transaction, the commit, rollback, and `schema_migrations` insert. The future migration
must only execute its DDL statements through `connection.execute()` within that runner-owned transaction;
it never backfills legacy records. Existing legacy observations are: `races.id` and `horses.id` are
`INTEGER PRIMARY KEY`, `horses.race_id` provides the internal-race link, and legacy tables do not declare
all required foreign keys.

#### SQL ownership boundary

There are exactly eight historical-input tables. `source_url` is snapshot content and is stored on the
snapshot header, not in a global mapping table. `external_horse_id` is snapshot-entry content and is not an
external-entry identity field. V3a permits only complete domain snapshots, so no `is_complete` column is
created; a permanent always-true flag would have no meaning.

The future migration creates one helper unique index on legacy `horses`. It is safe for existing data because
`horses.id` is already a primary key, so no two rows can have the same `(race_id, id)` pair. That index
makes the race-entry/race composite foreign key executable rather than merely documented.

```sql
CREATE UNIQUE INDEX ux_horses_race_id_id
ON horses (race_id, id);

CREATE TABLE historical_input_source_identities (
    organization TEXT NOT NULL CHECK (typeof(organization) = 'text' AND organization <> ''),
    source_system TEXT NOT NULL CHECK (typeof(source_system) = 'text' AND source_system <> ''),
    PRIMARY KEY (organization, source_system)
) WITHOUT ROWID;

CREATE TABLE historical_input_external_races (
    organization TEXT NOT NULL,
    source_system TEXT NOT NULL,
    external_race_id TEXT NOT NULL CHECK (typeof(external_race_id) = 'text' AND external_race_id <> ''),
    internal_race_id INTEGER NOT NULL CHECK (typeof(internal_race_id) = 'integer' AND internal_race_id > 0),
    PRIMARY KEY (organization, source_system, external_race_id),
    UNIQUE (organization, source_system, external_race_id, internal_race_id),
    UNIQUE (organization, source_system, internal_race_id),
    FOREIGN KEY (organization, source_system)
        REFERENCES historical_input_source_identities (organization, source_system)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (internal_race_id)
        REFERENCES races (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) WITHOUT ROWID;

CREATE TABLE historical_input_external_entries (
    organization TEXT NOT NULL,
    source_system TEXT NOT NULL,
    external_race_id TEXT NOT NULL,
    external_entry_id TEXT NOT NULL CHECK (typeof(external_entry_id) = 'text' AND external_entry_id <> ''),
    internal_race_id INTEGER NOT NULL CHECK (typeof(internal_race_id) = 'integer' AND internal_race_id > 0),
    race_entry_id INTEGER NOT NULL CHECK (typeof(race_entry_id) = 'integer' AND race_entry_id > 0),
    PRIMARY KEY (organization, source_system, external_race_id, external_entry_id),
    UNIQUE (organization, source_system, internal_race_id, race_entry_id),
    FOREIGN KEY (organization, source_system, external_race_id, internal_race_id)
        REFERENCES historical_input_external_races
            (organization, source_system, external_race_id, internal_race_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (internal_race_id, race_entry_id)
        REFERENCES horses (race_id, id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) WITHOUT ROWID;

CREATE TABLE historical_input_snapshots (
    snapshot_id INTEGER PRIMARY KEY,
    dataset_id TEXT NOT NULL CHECK (typeof(dataset_id) = 'text' AND dataset_id <> ''),
    organization TEXT NOT NULL,
    source_system TEXT NOT NULL,
    external_race_id TEXT NOT NULL,
    internal_race_id INTEGER NOT NULL CHECK (typeof(internal_race_id) = 'integer' AND internal_race_id > 0),
    source_url TEXT NULL CHECK (source_url IS NULL OR (typeof(source_url) = 'text' AND source_url <> '')),
    captured_at_utc TEXT NOT NULL CHECK (
        typeof(captured_at_utc) = 'text' AND length(captured_at_utc) = 32
        AND substr(captured_at_utc, 11, 1) = 'T'
        AND substr(captured_at_utc, 20, 1) = '.'
        AND substr(captured_at_utc, -6) = '+00:00'
        AND captured_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    information_cutoff_utc TEXT NOT NULL CHECK (
        typeof(information_cutoff_utc) = 'text' AND length(information_cutoff_utc) = 32
        AND substr(information_cutoff_utc, 11, 1) = 'T'
        AND substr(information_cutoff_utc, 20, 1) = '.'
        AND substr(information_cutoff_utc, -6) = '+00:00'
        AND information_cutoff_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    content_sha256 TEXT NOT NULL CHECK (
        typeof(content_sha256) = 'text' AND length(content_sha256) = 64
        AND content_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    UNIQUE (dataset_id, organization, source_system, external_race_id, captured_at_utc),
    FOREIGN KEY (organization, source_system, external_race_id, internal_race_id)
        REFERENCES historical_input_external_races
            (organization, source_system, external_race_id, internal_race_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (internal_race_id)
        REFERENCES races (id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE TABLE historical_input_snapshot_races (
    snapshot_id INTEGER PRIMARY KEY,
    target_race_date TEXT NOT NULL CHECK (
        typeof(target_race_date) = 'text' AND length(target_race_date) = 10
        AND target_race_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
    ),
    scheduled_start_at_utc TEXT NOT NULL CHECK (
        typeof(scheduled_start_at_utc) = 'text' AND length(scheduled_start_at_utc) = 32
        AND substr(scheduled_start_at_utc, 11, 1) = 'T'
        AND substr(scheduled_start_at_utc, 20, 1) = '.'
        AND substr(scheduled_start_at_utc, -6) = '+00:00'
        AND scheduled_start_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
    ),
    place TEXT NOT NULL CHECK (typeof(place) = 'text' AND place <> ''),
    distance_m INTEGER NOT NULL CHECK (typeof(distance_m) = 'integer' AND distance_m > 0),
    track TEXT NOT NULL CHECK (typeof(track) = 'text' AND track <> ''),
    track_condition TEXT NOT NULL CHECK (typeof(track_condition) = 'text' AND track_condition <> ''),
    race_name TEXT NULL CHECK (race_name IS NULL OR (typeof(race_name) = 'text' AND race_name <> '')),
    race_class TEXT NULL CHECK (race_class IS NULL OR (typeof(race_class) = 'text' AND race_class <> '')),
    weather TEXT NULL CHECK (weather IS NULL OR (typeof(weather) = 'text' AND weather <> '')),
    FOREIGN KEY (snapshot_id)
        REFERENCES historical_input_snapshots (snapshot_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE TABLE historical_input_snapshot_entries (
    snapshot_id INTEGER NOT NULL,
    race_entry_id INTEGER NOT NULL CHECK (typeof(race_entry_id) = 'integer' AND race_entry_id > 0),
    external_entry_id TEXT NOT NULL CHECK (typeof(external_entry_id) = 'text' AND external_entry_id <> ''),
    external_horse_id TEXT NULL CHECK (external_horse_id IS NULL OR (typeof(external_horse_id) = 'text' AND external_horse_id <> '')),
    horse_no INTEGER NOT NULL CHECK (typeof(horse_no) = 'integer' AND horse_no > 0),
    jockey TEXT NOT NULL CHECK (typeof(jockey) = 'text' AND jockey <> ''),
    win_odds_text TEXT NOT NULL CHECK (typeof(win_odds_text) = 'text' AND win_odds_text <> ''),
    entry_order INTEGER NOT NULL CHECK (typeof(entry_order) = 'integer' AND entry_order >= 0),
    PRIMARY KEY (snapshot_id, race_entry_id),
    UNIQUE (snapshot_id, external_entry_id),
    UNIQUE (snapshot_id, horse_no),
    UNIQUE (snapshot_id, entry_order),
    FOREIGN KEY (snapshot_id)
        REFERENCES historical_input_snapshots (snapshot_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) WITHOUT ROWID;

CREATE TABLE historical_input_snapshot_past_races (
    snapshot_id INTEGER NOT NULL,
    race_entry_id INTEGER NOT NULL CHECK (typeof(race_entry_id) = 'integer' AND race_entry_id > 0),
    past_race_index INTEGER NOT NULL CHECK (typeof(past_race_index) = 'integer' AND past_race_index >= 0),
    race_date TEXT NOT NULL CHECK (
        typeof(race_date) = 'text' AND length(race_date) = 10
        AND race_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
    ),
    place TEXT NOT NULL CHECK (typeof(place) = 'text' AND place <> ''),
    race_name TEXT NOT NULL CHECK (typeof(race_name) = 'text' AND race_name <> ''),
    race_class TEXT NOT NULL CHECK (typeof(race_class) = 'text' AND race_class <> ''),
    distance_m INTEGER NOT NULL CHECK (typeof(distance_m) = 'integer' AND distance_m > 0),
    track TEXT NOT NULL CHECK (typeof(track) = 'text' AND track <> ''),
    weather TEXT NOT NULL CHECK (typeof(weather) = 'text' AND weather <> ''),
    track_condition TEXT NOT NULL CHECK (typeof(track_condition) = 'text' AND track_condition <> ''),
    finish INTEGER NOT NULL CHECK (typeof(finish) = 'integer' AND finish > 0),
    margin_text TEXT NOT NULL CHECK (typeof(margin_text) = 'text' AND margin_text <> ''),
    race_time TEXT NOT NULL CHECK (typeof(race_time) = 'text' AND race_time <> ''),
    weight_text TEXT NOT NULL CHECK (typeof(weight_text) = 'text' AND weight_text <> ''),
    weight_diff_text TEXT NOT NULL CHECK (typeof(weight_diff_text) = 'text' AND weight_diff_text <> ''),
    jockey TEXT NOT NULL CHECK (typeof(jockey) = 'text' AND jockey <> ''),
    popularity INTEGER NOT NULL CHECK (typeof(popularity) = 'integer' AND popularity >= 0),
    odds_text TEXT NOT NULL CHECK (typeof(odds_text) = 'text' AND odds_text <> ''),
    passing_order TEXT NOT NULL CHECK (typeof(passing_order) = 'text'),
    fourth_corner_position INTEGER NOT NULL CHECK (
        typeof(fourth_corner_position) = 'integer' AND fourth_corner_position >= 0
    ),
    PRIMARY KEY (snapshot_id, race_entry_id, past_race_index),
    FOREIGN KEY (snapshot_id, race_entry_id)
        REFERENCES historical_input_snapshot_entries (snapshot_id, race_entry_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) WITHOUT ROWID;

CREATE TABLE historical_input_snapshot_provenance (
    snapshot_id INTEGER NOT NULL,
    input_type TEXT NOT NULL CHECK (input_type IN ('track', 'entry', 'odds', 'jockey', 'past_race')),
    audit_key TEXT NOT NULL CHECK (typeof(audit_key) = 'text' AND audit_key <> ''),
    source TEXT NOT NULL CHECK (typeof(source) = 'text' AND source <> ''),
    source_id TEXT NOT NULL CHECK (typeof(source_id) = 'text' AND source_id <> ''),
    race_entry_id INTEGER NULL CHECK (
        race_entry_id IS NULL OR (typeof(race_entry_id) = 'integer' AND race_entry_id > 0)
    ),
    available_at_utc TEXT NULL CHECK (
        available_at_utc IS NULL OR (
            typeof(available_at_utc) = 'text' AND length(available_at_utc) = 32
            AND substr(available_at_utc, 11, 1) = 'T'
            AND substr(available_at_utc, 20, 1) = '.'
            AND substr(available_at_utc, -6) = '+00:00'
            AND available_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
        )
    ),
    observed_at_utc TEXT NULL CHECK (
        observed_at_utc IS NULL OR (
            typeof(observed_at_utc) = 'text' AND length(observed_at_utc) = 32
            AND substr(observed_at_utc, 11, 1) = 'T'
            AND substr(observed_at_utc, 20, 1) = '.'
            AND substr(observed_at_utc, -6) = '+00:00'
            AND observed_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
        )
    ),
    past_race_index INTEGER NULL CHECK (
        past_race_index IS NULL OR (typeof(past_race_index) = 'integer' AND past_race_index >= 0)
    ),
    PRIMARY KEY (snapshot_id, audit_key),
    CHECK (available_at_utc IS NOT NULL OR observed_at_utc IS NOT NULL),
    CHECK (
        (input_type = 'track' AND race_entry_id IS NULL AND past_race_index IS NULL)
        OR (input_type IN ('entry', 'odds', 'jockey') AND race_entry_id IS NOT NULL AND past_race_index IS NULL)
        OR (input_type = 'past_race' AND race_entry_id IS NOT NULL)
    ),
    FOREIGN KEY (snapshot_id)
        REFERENCES historical_input_snapshots (snapshot_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (snapshot_id, race_entry_id)
        REFERENCES historical_input_snapshot_entries (snapshot_id, race_entry_id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    FOREIGN KEY (snapshot_id, race_entry_id, past_race_index)
        REFERENCES historical_input_snapshot_past_races (snapshot_id, race_entry_id, past_race_index)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) WITHOUT ROWID;

CREATE INDEX idx_his_external_races_internal
ON historical_input_external_races (internal_race_id, organization, source_system);

CREATE INDEX idx_his_external_entries_internal
ON historical_input_external_entries (internal_race_id, race_entry_id, organization, source_system);

CREATE INDEX idx_his_snapshots_latest_eligible
ON historical_input_snapshots (
    dataset_id,
    internal_race_id,
    organization,
    source_system,
    external_race_id,
    captured_at_utc DESC
);

CREATE TRIGGER trg_his_snapshot_entry_mapping_insert
BEFORE INSERT ON historical_input_snapshot_entries
FOR EACH ROW
WHEN NOT EXISTS (
    SELECT 1
    FROM historical_input_snapshots AS s
    JOIN historical_input_external_entries AS e
      ON e.organization = s.organization
     AND e.source_system = s.source_system
     AND e.external_race_id = s.external_race_id
     AND e.internal_race_id = s.internal_race_id
     AND e.external_entry_id = NEW.external_entry_id
     AND e.race_entry_id = NEW.race_entry_id
    WHERE s.snapshot_id = NEW.snapshot_id
)
BEGIN
    SELECT RAISE(ABORT, 'historical snapshot entry mapping mismatch');
END;

CREATE TRIGGER trg_his_snapshot_entry_mapping_update
BEFORE UPDATE OF snapshot_id, external_entry_id, race_entry_id
ON historical_input_snapshot_entries
FOR EACH ROW
WHEN NOT EXISTS (
    SELECT 1
    FROM historical_input_snapshots AS s
    JOIN historical_input_external_entries AS e
      ON e.organization = s.organization
     AND e.source_system = s.source_system
     AND e.external_race_id = s.external_race_id
     AND e.internal_race_id = s.internal_race_id
     AND e.external_entry_id = NEW.external_entry_id
     AND e.race_entry_id = NEW.race_entry_id
    WHERE s.snapshot_id = NEW.snapshot_id
)
BEGIN
    SELECT RAISE(ABORT, 'historical snapshot entry mapping mismatch');
END;

CREATE TRIGGER trg_his_snapshot_header_mapping_update
BEFORE UPDATE OF organization, source_system, external_race_id, internal_race_id
ON historical_input_snapshots
FOR EACH ROW
WHEN EXISTS (
    SELECT 1
    FROM historical_input_snapshot_entries AS se
    WHERE se.snapshot_id = OLD.snapshot_id
      AND NOT EXISTS (
          SELECT 1
          FROM historical_input_external_entries AS e
          WHERE e.organization = NEW.organization
            AND e.source_system = NEW.source_system
            AND e.external_race_id = NEW.external_race_id
            AND e.internal_race_id = NEW.internal_race_id
            AND e.external_entry_id = se.external_entry_id
            AND e.race_entry_id = se.race_entry_id
      )
)
BEGIN
    SELECT RAISE(ABORT, 'historical snapshot header mapping mismatch');
END;

CREATE TRIGGER trg_his_external_entry_referenced_update
BEFORE UPDATE OF organization, source_system, external_race_id, external_entry_id, internal_race_id, race_entry_id
ON historical_input_external_entries
FOR EACH ROW
WHEN EXISTS (
    SELECT 1
    FROM historical_input_snapshots AS s
    JOIN historical_input_snapshot_entries AS se
      ON se.snapshot_id = s.snapshot_id
    WHERE s.organization = OLD.organization
      AND s.source_system = OLD.source_system
      AND s.external_race_id = OLD.external_race_id
      AND s.internal_race_id = OLD.internal_race_id
      AND se.external_entry_id = OLD.external_entry_id
      AND se.race_entry_id = OLD.race_entry_id
)
BEGIN
    SELECT RAISE(ABORT, 'referenced historical external entry is immutable');
END;

CREATE TRIGGER trg_his_external_entry_referenced_delete
BEFORE DELETE ON historical_input_external_entries
FOR EACH ROW
WHEN EXISTS (
    SELECT 1
    FROM historical_input_snapshots AS s
    JOIN historical_input_snapshot_entries AS se
      ON se.snapshot_id = s.snapshot_id
    WHERE s.organization = OLD.organization
      AND s.source_system = OLD.source_system
      AND s.external_race_id = OLD.external_race_id
      AND s.internal_race_id = OLD.internal_race_id
      AND se.external_entry_id = OLD.external_entry_id
      AND se.race_entry_id = OLD.race_entry_id
)
BEGIN
    SELECT RAISE(ABORT, 'referenced historical external entry cannot be deleted');
END;
```

`CREATE TABLE count: 8.` `CREATE INDEX count: 4` (including the required legacy composite-parent
index). `CREATE TRIGGER count: 5.` All new-table foreign keys explicitly use `ON DELETE RESTRICT ON UPDATE
RESTRICT`. No trigger checks completeness or child counts, so a header and its children can be inserted in
one transaction in normal parent-first order.

The external-race `UNIQUE (organization, source_system, internal_race_id)` is adopted: within one provider
identity, an internal race cannot have ambiguous external-race mappings. Different source systems remain
independent. The external-entry composite FK to `horses (race_id, id)` proves that every mapped
`race_entry_id` belongs to its `internal_race_id`. The five linkage triggers restrict only immediate
cross-table mapping changes that an FK cannot express; they do not create impossible future-child
completeness rules.

#### Storage and invariant allocation

All dates use `TEXT` `YYYY-MM-DD`. All UTC datetimes use `TEXT`
`YYYY-MM-DDTHH:MM:SS.ffffff+00:00`. The repeated `typeof`, `length`, separator, suffix, and `GLOB` checks
above prove SQL shape; calendar validity and semantic ordering are revalidated by the domain constructor and
repository load. Decimal fields (`win_odds_text`, `margin_text`, `weight_text`, `weight_diff_text`, and
`odds_text`) use canonical fixed-point `TEXT`, never `REAL`. The DDL proves only nonempty text; decimal
canonicality, NFC text, calendar validity, required audit-key completeness, contiguity, past/absence XOR,
full digest reconstruction, and time semantics belong to repository/domain load validation.

`passing_order` is `TEXT NOT NULL` with no nonempty check: empty string is valid and `NULL` is forbidden.
`entry_order` and `past_race_index` are explicit zero-based integer columns. Their contiguity starts at zero
only at repository/domain load time; SQL provides coarse non-negative and uniqueness constraints.

The existing runner already enables and verifies foreign keys before migrations. It owns a per-migration
`BEGIN IMMEDIATE` transaction, commit, rollback, and migration-record insert. The future v010
`apply(connection)` only iterates `STATEMENTS + INDEXES + TRIGGERS` with `connection.execute(statement)`;
it must not call `BEGIN`, `BEGIN IMMEDIATE`, `COMMIT`, `ROLLBACK`, `connection.commit()`,
`connection.rollback()`, or `connection.executescript()`. It must not access or backfill `database/keiba.db`
as part of this design activity.

The future migration module has this exact transaction-neutral boundary:

```python
def apply(connection: sqlite3.Connection) -> None:
    for statement in STATEMENTS + INDEXES + TRIGGERS:
        connection.execute(statement)
```

The migration neither opens a transaction nor calls `connection.commit()`, `connection.rollback()`, or
`connection.executescript()`; those operations remain exclusively runner-owned.

#### Query-index rationale and trigger/FK proof

| Invariant/query | SQL mechanism | Why no duplicate index/trigger |
| --- | --- | --- |
| External race to internal race | external-race primary key | The primary key begins with the three external-race identity columns. |
| Internal race to provider race | `idx_his_external_races_internal` | Primary key cannot serve an internal-race-led lookup. |
| External entry to internal race entry | external-entry primary key | It begins with all four external-entry identity columns. |
| Internal race entry to external entry | `idx_his_external_entries_internal` | The primary key is external-identity-led. |
| Latest eligible snapshot | `idx_his_snapshots_latest_eligible` | Its exact prefix supports the dataset/race/source path and capture descending order. |
| Entries by order | `UNIQUE(snapshot_id, entry_order)` | SQLite uses this unique index; a duplicate index is redundant. |
| Past races by entry/index | past-race primary key | It is `(snapshot_id, race_entry_id, past_race_index)`. |
| Provenance by key | provenance primary key | It is `(snapshot_id, audit_key)`. |
| Entry mapping matches header/external mapping | 3 snapshot-entry/header triggers | No FK can join a child to values stored only in its header. |
| Referenced external entry cannot drift | 2 external-entry triggers | Snapshot entries do not duplicate source identity, so direct FK cannot protect mapping updates/deletes. |
| External entry belongs to internal race | composite FK to `horses(race_id,id)` | `ux_horses_race_id_id` provides the required unique parent key. |

#### V3a domain-to-column crosswalk

The following table is exhaustive. `SQL` means DDL constraints above; `Domain` means the approved V3a
constructor or repository-load validation.

| Domain class | Domain field | SQLite table.column | Storage / NULL | Classification | SQL validation | Repository/domain validation |
| --- | --- | --- | --- | --- | --- | --- |
| HistoricalSourceIdentity | organization | historical_input_snapshots.organization; historical_input_source_identities.organization | TEXT / NOT NULL | identity | PK/FK/nonempty | NFC text |
| HistoricalSourceIdentity | source_system | historical_input_snapshots.source_system; historical_input_source_identities.source_system | TEXT / NOT NULL | identity | PK/FK/nonempty | NFC text |
| HistoricalSourceIdentity | external_race_id | historical_input_snapshots.external_race_id | TEXT / NOT NULL | identity | UNIQUE/FK/nonempty | NFC text |
| HistoricalSourceIdentity | source_url | historical_input_snapshots.source_url | TEXT / NULL | content | nonempty if present | NFC optional text |
| HistoricalExternalRaceIdentity | organization | historical_input_external_races.organization | TEXT / NOT NULL | linkage | PK/FK | exact/NFC |
| HistoricalExternalRaceIdentity | source_system | historical_input_external_races.source_system | TEXT / NOT NULL | linkage | PK/FK | exact/NFC |
| HistoricalExternalRaceIdentity | external_race_id | historical_input_external_races.external_race_id | TEXT / NOT NULL | linkage | PK/nonempty | NFC text |
| HistoricalExternalEntryIdentity | external_race_identity | historical_input_external_entries.organization/source_system/external_race_id | TEXT / NOT NULL | linkage identity | PK/FK | exact external-race object |
| HistoricalExternalEntryIdentity | external_entry_id | historical_input_external_entries.external_entry_id; historical_input_snapshot_entries.external_entry_id | TEXT / NOT NULL | linkage identity | PK/UNIQUE/trigger | NFC text |
| HistoricalExternalEntryIdentity | external_horse_id | historical_input_snapshot_entries.external_horse_id | TEXT / NULL | content metadata | nonempty if present | NFC optional text; excluded from identity |
| HistoricalInputSnapshotIdentity | dataset_id | historical_input_snapshots.dataset_id | TEXT / NOT NULL | identity | UNIQUE/nonempty | NFC text |
| HistoricalInputSnapshotIdentity | source_identity | historical_input_snapshots.organization/source_system/external_race_id | TEXT / NOT NULL | identity | UNIQUE/FK | exact V3a source identity |
| HistoricalInputSnapshotIdentity | captured_at | historical_input_snapshots.captured_at_utc | TEXT / NOT NULL | identity | UTC-shape/UNIQUE | UTC/calendar/causal order |
| HistoricalRaceSnapshot | target_race_date | historical_input_snapshot_races.target_race_date | TEXT / NOT NULL | content | date shape | canonical date |
| HistoricalRaceSnapshot | scheduled_start_at | historical_input_snapshot_races.scheduled_start_at_utc | TEXT / NOT NULL | content | UTC shape | UTC/causal order |
| HistoricalRaceSnapshot | place | historical_input_snapshot_races.place | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalRaceSnapshot | distance_m | historical_input_snapshot_races.distance_m | INTEGER / NOT NULL | content | > 0 | exact positive int |
| HistoricalRaceSnapshot | track | historical_input_snapshot_races.track | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalRaceSnapshot | track_condition | historical_input_snapshot_races.track_condition | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalRaceSnapshot | race_name | historical_input_snapshot_races.race_name | TEXT / NULL | content | nonempty if present | NFC optional text |
| HistoricalRaceSnapshot | race_class | historical_input_snapshot_races.race_class | TEXT / NULL | content | nonempty if present | NFC optional text |
| HistoricalRaceSnapshot | weather | historical_input_snapshot_races.weather | TEXT / NULL | content | nonempty if present | NFC optional text |
| HistoricalRaceEntrySnapshot | race_entry_id | historical_input_snapshot_entries.race_entry_id | INTEGER / NOT NULL | linkage/content | PK/>0/trigger | exact positive int |
| HistoricalRaceEntrySnapshot | external_entry_identity | historical_input_snapshot_entries.external_entry_id plus historical_input_external_entries mapping | TEXT / NOT NULL | linkage | UNIQUE/trigger | exact identity; metadata excluded |
| HistoricalRaceEntrySnapshot | horse_no | historical_input_snapshot_entries.horse_no | INTEGER / NOT NULL | content | UNIQUE/>0 | exact positive int |
| HistoricalRaceEntrySnapshot | jockey | historical_input_snapshot_entries.jockey | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalRaceEntrySnapshot | win_odds | historical_input_snapshot_entries.win_odds_text | TEXT / NOT NULL | content | nonempty | canonical Decimal |
| HistoricalRaceEntrySnapshot | entry_order | historical_input_snapshot_entries.entry_order | INTEGER / NOT NULL | ordering | UNIQUE/>=0 | zero-based contiguous |
| HistoricalPastRaceSnapshot | race_entry_id | historical_input_snapshot_past_races.race_entry_id | INTEGER / NOT NULL | linkage | PK/FK/>0 | exact positive int |
| HistoricalPastRaceSnapshot | past_race_index | historical_input_snapshot_past_races.past_race_index | INTEGER / NOT NULL | ordering | PK/>=0 | zero-based contiguous |
| HistoricalPastRaceSnapshot | race_date | historical_input_snapshot_past_races.race_date | TEXT / NOT NULL | content | date shape | canonical date; before target |
| HistoricalPastRaceSnapshot | place | historical_input_snapshot_past_races.place | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalPastRaceSnapshot | race_name | historical_input_snapshot_past_races.race_name | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalPastRaceSnapshot | race_class | historical_input_snapshot_past_races.race_class | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalPastRaceSnapshot | distance_m | historical_input_snapshot_past_races.distance_m | INTEGER / NOT NULL | content | >0 | exact positive int |
| HistoricalPastRaceSnapshot | track | historical_input_snapshot_past_races.track | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalPastRaceSnapshot | weather | historical_input_snapshot_past_races.weather | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalPastRaceSnapshot | track_condition | historical_input_snapshot_past_races.track_condition | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalPastRaceSnapshot | finish | historical_input_snapshot_past_races.finish | INTEGER / NOT NULL | content | >0 | exact positive int |
| HistoricalPastRaceSnapshot | margin | historical_input_snapshot_past_races.margin_text | TEXT / NOT NULL | content | nonempty | canonical Decimal |
| HistoricalPastRaceSnapshot | race_time | historical_input_snapshot_past_races.race_time | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalPastRaceSnapshot | weight | historical_input_snapshot_past_races.weight_text | TEXT / NOT NULL | content | nonempty | canonical Decimal |
| HistoricalPastRaceSnapshot | weight_diff | historical_input_snapshot_past_races.weight_diff_text | TEXT / NOT NULL | content | nonempty | canonical Decimal |
| HistoricalPastRaceSnapshot | jockey | historical_input_snapshot_past_races.jockey | TEXT / NOT NULL | content | nonempty | NFC text |
| HistoricalPastRaceSnapshot | popularity | historical_input_snapshot_past_races.popularity | INTEGER / NOT NULL | content | >=0 | exact non-negative int |
| HistoricalPastRaceSnapshot | odds | historical_input_snapshot_past_races.odds_text | TEXT / NOT NULL | content | nonempty | canonical Decimal |
| HistoricalPastRaceSnapshot | passing_order | historical_input_snapshot_past_races.passing_order | TEXT / NOT NULL | content | text; empty allowed | NFC string, including empty |
| HistoricalPastRaceSnapshot | fourth_corner_position | historical_input_snapshot_past_races.fourth_corner_position | INTEGER / NOT NULL | content | >=0 | exact non-negative int |
| HistoricalInputProvenance | input_type | historical_input_snapshot_provenance.input_type | TEXT / NOT NULL | content/audit | enum CHECK | exact V3a type/key relation |
| HistoricalInputProvenance | audit_key | historical_input_snapshot_provenance.audit_key | TEXT / NOT NULL | ordering/audit | PK/nonempty | slash-key relation/completeness |
| HistoricalInputProvenance | source | historical_input_snapshot_provenance.source | TEXT / NOT NULL | audit | nonempty | NFC text |
| HistoricalInputProvenance | source_id | historical_input_snapshot_provenance.source_id | TEXT / NOT NULL | audit | nonempty | NFC text/formats deferred to V3c |
| HistoricalInputProvenance | race_entry_id | historical_input_snapshot_provenance.race_entry_id | INTEGER / NULL | linkage | FK/coarse check | input-type relation |
| HistoricalInputProvenance | available_at | historical_input_snapshot_provenance.available_at_utc | TEXT / NULL | audit time | UTC shape/one time | UTC causal order |
| HistoricalInputProvenance | observed_at | historical_input_snapshot_provenance.observed_at_utc | TEXT / NULL | audit time | UTC shape/one time | UTC causal order |
| HistoricalInputProvenance | past_race_index | historical_input_snapshot_provenance.past_race_index | INTEGER / NULL | linkage | FK/coarse check | audit-key relation/XOR |
| HistoricalInputSnapshot | identity | historical_input_snapshots.dataset_id/organization/source_system/external_race_id/captured_at_utc | mixed / NOT NULL | natural identity | exact UNIQUE | V3a identity object |
| HistoricalInputSnapshot | internal_race_id | historical_input_snapshots.internal_race_id | INTEGER / NOT NULL | linkage | FK/>0 | exact positive int |
| HistoricalInputSnapshot | information_cutoff | historical_input_snapshots.information_cutoff_utc | TEXT / NOT NULL | content | UTC shape | UTC causal order |
| HistoricalInputSnapshot | race | historical_input_snapshot_races row | normalized row / NOT NULL by repository | content | FK | exact V3a race object |
| HistoricalInputSnapshot | entries | historical_input_snapshot_entries rows | normalized rows / non-empty repository | content | FK/UNIQUE | tuple-only/order/completeness |
| HistoricalInputSnapshot | past_races | historical_input_snapshot_past_races rows | normalized rows / may be empty | content | FK | tuple-only/index/absence XOR |
| HistoricalInputSnapshot | provenance | historical_input_snapshot_provenance rows | normalized rows / non-empty repository | audit | FK/PK | tuple-only/key completeness |
| HistoricalInputSnapshot | content_sha256 | historical_input_snapshots.content_sha256 | TEXT / NOT NULL | derived content | 64 lowercase hex | recomputed digest equality |

#### V3b self-review

1. PASS — exactly eight historical-input tables are specified.
2. PASS — every V3a field has one or more explicit storage columns.
3. PASS — snapshot `UNIQUE(dataset_id, organization, source_system, external_race_id, captured_at_utc)` exactly matches V3a natural identity.
4. PASS — `source_url` is content on snapshots, not identity.
5. PASS — `external_horse_id` is snapshot content, not entry identity.
6. PASS — all Decimal values use `TEXT` and never `REAL`.
7. PASS — `passing_order` is `TEXT NOT NULL` and permits `''`.
8. PASS — every UTC column has executable TEXT/length/separator/suffix/digit-shape checks.
9. PASS — external races FK to `races(id)`.
10. PASS — external entries use the executable composite FK to `horses(race_id,id)`.
11. PASS — snapshot entries use mapping-consistency triggers.
12. PASS — no completeness or child-count trigger exists.
13. PASS — child order columns and supporting unique/primary indexes are explicit.
14. PASS — provenance stores every `InputAuditEntry` field.
15. PASS — every new-table FK declares `ON DELETE RESTRICT ON UPDATE RESTRICT`.
16. PASS — query indexes are either explicit or satisfied by listed PK/UNIQUE indexes without duplication.
17. PASS — the exhaustive domain-to-column crosswalk is present.
18. PASS — provider/source/JRA/v008 policy is deferred to V3c.
19. PASS — overall 1i6a remains `REVISION_REQUIRED`.

V3b status is `READY_FOR_REVIEW`. V3c source mapping/policy and V3d consolidation remain incomplete;
production implementation remains unauthorized.

### V3c — Source mapping, provenance, and eligibility policy

V3c supplies the source and policy contract for the approved V3a values and approved V3b schema. It does
not alter the eight historical-input tables, their columns, indexes, foreign keys, triggers, or the
runner-owned transaction boundary. It also creates no provider, parser, collector, repository, importer, or
migration implementation.

#### Source-system and organization contract

| Source family | `source_system` | `organization` | Current official historical capture eligibility | Evidence and rule |
| --- | --- | --- | --- | --- |
| JRA official | `jra_official` | `JRA` | `CURRENTLY_UNSUPPORTED` | Current `JRAFetcher` is hard-coded sample data. No JRA record may be represented until a real official capture boundary exists. |
| NAR official | `nar_official` | `NAR` | `CURRENTLY_UNSUPPORTED` | `NARProvider` reaches `https://www.keiba.go.jp/`, but lacks the approved observed-at, canonical-record-digest, and stable source-ID boundary. |
| Legacy KeibaOS DB | none | none | `INELIGIBLE` | `races`, `horses`, and `past_races` may supply internal linkage only, never snapshot content/provenance. |
| v008 odds tables | none | none | `UNTRUSTED_FOR_OFFICIAL_HISTORICAL_INPUT` | Existing rows predate the V3c collector attestation/capture boundary. |
| `horses.odds` | none | none | `FORBIDDEN` | It is mutable legacy `REAL` data with no source-record evidence. |

The NAR parser's current display string `"地方"` is not an organization identity and is forbidden in
historical-input source identity. `k_babaCode` identifies the NAR venue only inside the NAR external-race
identity; it neither changes `organization="NAR"` nor becomes a local database ID. The display place may be
snapshot content only after it is captured from the same official record.

#### External identity contract

For an eligible NAR official record, `k_raceDate` must be `YYYY/MM/DD`, `k_babaCode` must be an ASCII
decimal integer with no sign and canonical decimal spelling, and `k_raceNo` must be a decimal integer in
the provider record with canonical decimal spelling. The approved external race ID is exactly:

```text
nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}
```

`YYYYMMDD` is `k_raceDate` with the two `/` characters removed. The provider's venue display text is not an
identity component. A missing, duplicated, noncanonical, or out-of-record URL parameter fails closed; local
`races.id`, URL order, database row order, Python `hash()`, random UUIDs, filenames, and time-derived IDs
are forbidden.

For an eligible NAR official entry record, `horseNum` must be a positive canonical decimal integer. Its
external entry ID is exactly:

```text
nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}:entry:{horseNum}
```

It is scoped by the matching NAR external race identity and must not be derived from `horses.id` or display
order. `external_horse_id` is optional provider metadata only. The current horse-detail href is not proven
to be a stable provider horse ID, so current capture writes `None`; it must never substitute local horse IDs.
JRA external race and entry IDs remain unsupported until a real official JRA source contract is approved.

#### Source URL and source-ID contract

`source_url` is the canonical HTTPS official primary race-record URL for a snapshot, not a log path,
temporary filename, `file:` URL, or a generated aggregate URL. Each provenance entry describes its exact
source record separately. Canonicalization is versioned as `url-v1`:

1. Parse an absolute HTTPS URL; reject credentials, a non-default port, an empty host, and any fragment.
2. NFC-normalize Unicode components, lowercase the scheme and ASCII host, and remove the default `:443`.
3. Preserve the path except for uppercasing percent-escape hex digits; reject dot segments and malformed
   percent escapes.
4. Parse query pairs without loss; NFC-normalize names/values, preserve duplicate pairs, sort pairs by
   `(name, value, original-occurrence-index)`, then encode with uppercase percent escapes and `%20` for a
   space.
5. Emit `https://{lowercase-host}{path}?{canonical-query}` with no trailing `?` for an empty query.

The `source_id` grammar is exact and does not use URL text, local IDs, timestamps, or paths as the identity:

```text
his-v1:{record_kind}:{sha256}
```

`record_kind` is one of `track`, `entry`, `jockey`, `odds_win`, `past_race`, or `past_race_absence`; `sha256`
is 64 lowercase hexadecimal characters. It is SHA-256 over the UTF-8 bytes of this canonical JSON payload:

```text
schema_version: 1
source_system
record_kind
organization
external_race_id
external_entry_id: string or null
canonical_source_url: string or null
provider_record_id: string or null
record_values: exact parsed source values with Decimal fixed-point strings
```

The JSON uses NFC strings, `ensure_ascii=False`, `sort_keys=True`, `separators=(",", ":")`, canonical UTC
microsecond `+00:00` strings, and `null` for absent optionals. Raw HTML is not the payload; the exact parsed
record values are. A future implementation must specify a provider-record-ID grammar before using a
provider-ID-backed record. Until then, a canonical official URL is required.

#### Provenance-time contract

`available_at` is an exact provider-publication timestamp only when the same source record contains one that
can be parsed as aware UTC time. HTTP receipt time, database insert time, file mtime, race start, page date,
and snapshot capture time are forbidden substitutes; otherwise it is `None`.

`observed_at` is created at the approved collector boundary immediately after successful response bytes are
received and before parsing. It is an aware UTC datetime with microseconds and binds the exact response to
the canonical record payload. Existing NAR code has no such boundary; it therefore cannot produce official
historical provenance without a later collector implementation.

`captured_at` is the aware UTC timestamp at successful assembly of a complete `HistoricalInputSnapshot`.
It is not race start, database-save time, simulation time, migration time, or settlement time. All populated
timestamps must satisfy `available_at <= observed_at <= captured_at <= information_cutoff <=
scheduled_start_at`; nullable `available_at` and `observed_at` each must not be after `captured_at`.

#### Field-level source matrix

The following 64 rows cover every V3a scalar/normalized value. `unsupported` means a future official source
may only populate the field after it satisfies the preceding capture and source-ID rules; it is never filled
from legacy data or inference. Every JRA row is currently unsupported because the present fetcher is sample
data only.

| Domain value.field | JRA official origin | NAR official origin / derivation | Current rule |
| --- | --- | --- | --- |
| HistoricalSourceIdentity.organization | unsupported | fixed `NAR`, never parser display `地方` | source-system rule |
| HistoricalSourceIdentity.source_system | unsupported | fixed `nar_official` | source-system rule |
| HistoricalSourceIdentity.external_race_id | unsupported | `k_raceDate`, `k_babaCode`, `k_raceNo` → exact NAR format | URL parameters only |
| HistoricalSourceIdentity.source_url | unsupported | canonical primary official race URL | `url-v1` |
| HistoricalExternalRaceIdentity.organization | unsupported | fixed `NAR` | no venue/local-ID substitution |
| HistoricalExternalRaceIdentity.source_system | unsupported | fixed `nar_official` | exact literal |
| HistoricalExternalRaceIdentity.external_race_id | unsupported | exact NAR external-race ID | URL parameters only |
| HistoricalExternalEntryIdentity.external_race_identity | unsupported | matching NAR external-race identity | exact parent identity |
| HistoricalExternalEntryIdentity.external_entry_id | unsupported | `horseNum` → exact NAR entry format | no local ID/order |
| HistoricalExternalEntryIdentity.external_horse_id | unsupported | none unless future provider supplies stable explicit ID | current value is `None` |
| HistoricalInputSnapshotIdentity.dataset_id | caller/run context | caller/run context | not provider-derived |
| HistoricalInputSnapshotIdentity.source_identity | unsupported | approved source identity above | exact object fields |
| HistoricalInputSnapshotIdentity.captured_at | unsupported | successful complete snapshot assembly UTC time | capture boundary |
| HistoricalRaceSnapshot.target_race_date | unsupported | `k_raceDate` from primary official race record | canonical date |
| HistoricalRaceSnapshot.scheduled_start_at | unsupported | official scheduled start field with explicit source timezone | no naive parser string |
| HistoricalRaceSnapshot.place | unsupported | official race/meeting place field | content, not identity |
| HistoricalRaceSnapshot.distance_m | unsupported | official race course/distance field | exact positive integer |
| HistoricalRaceSnapshot.track | unsupported | official race course field | no inference |
| HistoricalRaceSnapshot.track_condition | unsupported | official race condition field | no inference |
| HistoricalRaceSnapshot.race_name | unsupported | official race-name field | optional exact text |
| HistoricalRaceSnapshot.race_class | unsupported | official race-class field | optional exact text |
| HistoricalRaceSnapshot.weather | unsupported | official weather field | optional exact text |
| HistoricalRaceEntrySnapshot.race_entry_id | mapped internal linkage | mapped internal linkage | external-entry mapping, not source content |
| HistoricalRaceEntrySnapshot.external_entry_identity | unsupported | exact NAR `horseNum` entry identity | no local ID/order |
| HistoricalRaceEntrySnapshot.horse_no | unsupported | official `horseNum` | exact positive integer |
| HistoricalRaceEntrySnapshot.jockey | unsupported | official entry jockey field | exact record text |
| HistoricalRaceEntrySnapshot.win_odds | unsupported | exact official WIN-odds source text → Decimal | float parser/0.0 forbidden |
| HistoricalRaceEntrySnapshot.entry_order | unsupported | canonical ascending `horseNum` after validated complete entry set | not HTML/DB display order |
| HistoricalPastRaceSnapshot.race_entry_id | mapped internal linkage | matching snapshot-entry mapping | not provider field |
| HistoricalPastRaceSnapshot.past_race_index | unsupported | zero-based order after sorting by `(race_date, source_id)` ascending | independent of provider display order |
| HistoricalPastRaceSnapshot.race_date | unsupported | official horse-history record | exact canonical date |
| HistoricalPastRaceSnapshot.place | unsupported | official horse-history record | exact text |
| HistoricalPastRaceSnapshot.race_name | unsupported | official horse-history record | exact text |
| HistoricalPastRaceSnapshot.race_class | unsupported | official horse-history record | exact text |
| HistoricalPastRaceSnapshot.distance_m | unsupported | official horse-history record | exact positive integer |
| HistoricalPastRaceSnapshot.track | unsupported | official horse-history record | exact text |
| HistoricalPastRaceSnapshot.weather | unsupported | official horse-history record | exact text |
| HistoricalPastRaceSnapshot.track_condition | unsupported | official horse-history record | exact text |
| HistoricalPastRaceSnapshot.finish | unsupported | official horse-history record | exact positive integer |
| HistoricalPastRaceSnapshot.margin | unsupported | exact source text → Decimal | no float conversion |
| HistoricalPastRaceSnapshot.race_time | unsupported | official horse-history record | exact text |
| HistoricalPastRaceSnapshot.weight | unsupported | exact source text → Decimal | no float conversion |
| HistoricalPastRaceSnapshot.weight_diff | unsupported | exact source text → Decimal | no float conversion |
| HistoricalPastRaceSnapshot.jockey | unsupported | official horse-history record | exact text |
| HistoricalPastRaceSnapshot.popularity | unsupported | official horse-history record | exact non-negative integer |
| HistoricalPastRaceSnapshot.odds | unsupported | exact source text → Decimal | no float conversion |
| HistoricalPastRaceSnapshot.passing_order | unsupported | official horse-history record | empty string remains allowed |
| HistoricalPastRaceSnapshot.fourth_corner_position | unsupported | official horse-history record | exact non-negative integer |
| HistoricalInputProvenance.input_type | derived | derived from record kind/audit key | V3a enum |
| HistoricalInputProvenance.audit_key | derived | V3a fixed key grammar | no new category |
| HistoricalInputProvenance.source | unsupported | `nar_official` | exact literal |
| HistoricalInputProvenance.source_id | unsupported | `his-v1:{record_kind}:{sha256}` | canonical payload |
| HistoricalInputProvenance.race_entry_id | mapped internal linkage | matching snapshot entry or `None` for track | no provider/local-ID substitution |
| HistoricalInputProvenance.available_at | unsupported | exact provider publication time or `None` | no inferred time |
| HistoricalInputProvenance.observed_at | unsupported | approved response-byte receipt UTC time | current provider lacks it |
| HistoricalInputProvenance.past_race_index | unsupported | matching validated past row or `None` | absence uses `/none` |
| HistoricalInputSnapshot.identity | unsupported | `dataset_id` plus approved NAR source identity/captured_at | natural identity only |
| HistoricalInputSnapshot.internal_race_id | mapped internal linkage | external-race mapping to `races.id` | not provider-derived |
| HistoricalInputSnapshot.information_cutoff | caller request | caller request | not source-derived |
| HistoricalInputSnapshot.race | unsupported | exactly one validated official race record | no legacy reconstruction |
| HistoricalInputSnapshot.entries | unsupported | complete validated official entry records | non-empty, sorted canonical order |
| HistoricalInputSnapshot.past_races | unsupported | validated official horse-history records | or exact `/none` evidence |
| HistoricalInputSnapshot.provenance | unsupported | one exact record per V3a audit key | source-ID contract |
| HistoricalInputSnapshot.content_sha256 | derived | canonical V3a payload after validation | never supplied by provider |

Past-race order is source-independent and deterministic: after each complete past-race record has its exact
`source_id`, V3c sorts records by `(race_date, source_id)` ascending and assigns zero-based
`past_race_index`. No provider display order, database row order, local ID, or inferred chronology is used.
This preserves V3b DDL while keeping current NAR capture fail-closed until a collector can construct each
exact source record.

#### Legacy, v008, and support policy

Legacy `races`, `horses`, and `past_races` are ineligible as official historical snapshot content because
their historical provenance timestamps and source-record identity cannot be reconstructed. They may be used
only for the internal `races.id`/`horses.id` linkage established by V3b. Existing v008 odds rows are
`UNTRUSTED_FOR_OFFICIAL_HISTORICAL_INPUT`: their `observed_at` is not collector-attested, no exact original
capture boundary can be proven, and automatic import/backfill is prohibited. `horses.odds` is always
forbidden. Missing jockeys, track conditions, odds, and past-race absence must never be inferred from legacy
rows or current refetches.

| Source | Race metadata | Entries/jockey | WIN odds | Past races/absence | External IDs | `available_at` | `observed_at` | Official snapshot now? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JRA official current code | no | no | no | no | no | no | no | no — hard-coded sample |
| NAR official current code | partial parser fields only | partial parser fields only | no — float/0.0 boundary | no | no approved contract | no | no | no — capture boundary absent |
| Legacy DB | linkage only | linkage only | forbidden | forbidden | forbidden | absent | absent | no |
| v008 odds | no | no | untrusted | n/a | n/a | absent | untrusted | no |

#### V3c self-review

1. PASS — source-system values are exact.
2. PASS — organization derivation is deterministic and does not use `"地方"`.
3. PASS — the NAR external race ID format is exact.
4. PASS — the NAR external entry ID format is exact.
5. PASS — `external_horse_id` is never entry identity.
6. PASS — source-ID grammar and canonical payload are complete.
7. PASS — Python hash, random, local IDs, paths, and time-alone IDs are forbidden.
8. PASS — canonical source-record digest schema version is fixed.
9. PASS — every V3a source-relevant scalar has one of 64 matrix rows.
10. PASS — every matrix row states JRA and NAR origin or explicit unsupported status.
11. PASS — `available_at` origin is exact.
12. PASS — `observed_at` origin is exact.
13. PASS — `captured_at` origin is exact.
14. PASS — legacy DB values cannot become provenance.
15. PASS — past-race absence requires exact source evidence.
16. PASS — existing v008 rows are untrusted.
17. PASS — `horses.odds` is forbidden.
18. PASS — hard-coded `JRAFetcher` is not official provenance.
19. PASS — the float odds parser is not historical odds evidence.
20. PASS — V3b DDL is unchanged.
21. PASS — V3d has not started.
22. PASS — overall 1i6a remains `REVISION_REQUIRED`.

V3a status: `APPROVED`. V3b status: `APPROVED`. V3c status: `READY_FOR_REVIEW`. Overall 1i6a remains
`REVISION_REQUIRED` with approval disposition `NOT_APPROVED`; V3c review and V3d consolidation remain
incomplete.
