# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `POST_V0_8_DAILY_REPLAY_28`
- Name: `NAR Daily Replay Explicit Selection and Read-Only Aggregation`
- Phase type: `DESIGN_ONLY`
- Base Commit: `49733e7e4563d25b36d7183a13b282749ff0ac7a`
- Branch: `feature/post-v0.8-daily-replay`
- Preparation outcome: `IMPLEMENTABLE`

Phase 28 is the first multi-day analytical layer over Phase 27 immutable results. It consumes
only exact-ID, integrity-validated `PersistedNARDailyReplayResult` values and returns an
in-memory immutable aggregate. It never executes replay, acquires or resolves evidence, writes a
manifest, settles a bet, persists a daily result or aggregate, selects an attempt implicitly, or
creates a feedback dependency into prediction/value/strategy input layers.

## PREPARE scope

Only these two documentation files may change in this PREPARE:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No production, test, migration, database/**, logs/**, fixture, archive, stage, commit or push
change is authorized. The implementation scope below is a future proposal only.

## Read-only audit findings

- Phase 27 is present at the base commit. Its only public retrieval primitive is
  `SQLiteNARDailyReplayResultRepository.load_result(*, persisted_content_sha256: str)`, returning
  one integrity-reconstructed `PersistedNARDailyReplayResult` or `None`. It has no date, latest,
  newest, list, update, delete, repair, or aggregate API.
- `PersistedNARDailyReplayResult` fixes provider to `NAR` / `nar_official`, retains immutable
  target/acquisition/run/strategy/budget/cutoff provenance, and separates configured manifest
  input from a completed-only published manifest artifact. Valid diagnostic results have no
  `SimulationSummary`; completed results have an exact summary.
- `SimulationSummary` and `BetTypeSummary` already define the authoritative integer and Decimal
  arithmetic: `profit = payout - investment`; ROI is `None` for zero investment and otherwise
  `Decimal(payout) * Decimal("100") / Decimal(investment)`; bet and race hit rates use their
  settled denominators and `Decimal("100")`. Their constructors validate both rates and exact
  by-bet-type totals.
- The existing simulator aggregates individual `SimulationResult` values and computes a true
  drawdown from an ordered race-level settlement sequence. It is not a reusable multi-day daily
  summary helper. No existing daily-result aggregation module, cumulative-result table, or
  canonical multi-day selection helper exists.
- Phase 27 result persistence has no imports from historical snapshot/evidence resolution,
  prediction, value or strategy modules, and those input-side modules do not import the result
  persistence boundary. Phase 28 preserves this one-way analysis-output boundary.

## Explicit selection contract

Phase 28 creates `scripts/simulation/nar_daily_replay_aggregation.py` with the following exact
public surface:

```python
@dataclass(frozen=True, slots=True)
class NARDailyReplayAggregationSelection:
    schema_version: int
    persisted_content_sha256s: tuple[str, ...]
    selection_sha256: str = field(init=False)

@dataclass(frozen=True, slots=True)
class NARDailyReplayAggregationResult:
    schema_version: int
    selection: NARDailyReplayAggregationSelection
    organization: str
    source_system: str
    dataset_id: str
    selection_policy: str
    settlement_information_cutoff: datetime
    strategy_id: str
    strategy_name: str
    strategy_config_hash: str
    target_commit_id: str
    race_budget_total_amount: int
    first_target_date: date
    last_target_date: date
    selected_record_count: int
    completed_day_count: int
    partial_resolution_diagnostic_day_count: int
    no_executable_diagnostic_day_count: int
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
    max_single_day_maximum_drawdown: int | None
    selection_sha256: str = field(init=False)
    aggregate_content_sha256: str = field(init=False)

def aggregate_nar_daily_replay_selection(
    *,
    selection: NARDailyReplayAggregationSelection,
    repository: SQLiteNARDailyReplayResultRepository,
) -> NARDailyReplayAggregationResult:
    ...
```

`schema_version` is exactly `1`. A selection is nonempty and contains only lowercase 64-character
SHA-256 content identities. It retains the caller-supplied tuple as the analytical order; no
sorting, deduplication, date lookup or alternative-attempt choice is performed. The application
loads every identity only through the concrete Phase 27 repository's exact `load_result` method,
then validates all records before producing any result. It performs no raw SQLite query and no
direct reconstruction from rows.

The caller must supply records in strictly ascending `target_date` order. Phase 28 rejects an
out-of-order tuple rather than silently changing its meaning. IDs must be unique, every ID must
resolve exactly, and target dates must be unique after load. Thus competing immutable attempts for
one date remain legal in Phase 27 but cannot coexist in one analytical selection. Missing IDs,
invalid identity text, duplicate IDs, duplicate dates, invalid ordering and incompatible records
are caller-selection validation failures; a Phase 27 load integrity error propagates unchanged.

Selection identity is the lowercase SHA-256 of canonical UTF-8 JSON payload:

```text
version = "nar-daily-replay-aggregation-selection-v1"
schema_version = 1
persisted_content_sha256s = caller tuple in its validated ascending-date order
```

JSON has NFC text, lexical object-key sorting, `ensure_ascii=False`, `allow_nan=False`, compact
separators `(',', ':')`, no trailing LF, and no floats. This canonical encoding is scoped only to
the new Phase 28 identity; Phase 27's private persisted-record serializer is not imported,
copied, or used as an alternate Phase 27 digest algorithm.

## Compatible analytical-series contract

After exact load, every selected record must have schema version 1 and the same:

- provider identity (`NAR` / `nar_official`);
- `dataset_id`, `selection_policy`, and UTC settlement-information cutoff;
- `strategy_id`, `strategy_name`, and `strategy_config_hash`;
- `target_commit_id`; and
- uniform `race_budget_total_amount`.

`run_id`, run-start timestamp, content identity, capture identities, configured paths and manifest
artifact identity are audit facts, not series-selection keys. Different run IDs are therefore
permitted when every compatibility value above agrees. No database row order, insertion time,
filesystem state, current time, random value, UUID or locale is a selection or compatibility
authority.

## Aggregate result and arithmetic

`NARDailyReplayAggregationResult` is frozen and contains exactly:

- `schema_version = 1`, the complete selection object, `selection_sha256`, and derived
  `aggregate_content_sha256`;
- selected identity tuple; selected-record count; first and last target dates; provider and all
  compatible analytical-series fields listed above;
- `completed_day_count`, `partial_resolution_diagnostic_day_count`, and
  `no_executable_diagnostic_day_count`;
- cumulative `race_count`, `settled_race_count`, `unsettled_race_count`, `no_bet_race_count`,
  `void_race_count`, `error_race_count`, `unsupported_race_count`, `bet_count`,
  `settled_bet_count`, `settled_purchase_race_count`, `hit_bet_count`, `hit_race_count`,
  `investment`, `payout`, and `profit`;
- exact recomputed `roi`, `bet_hit_rate`, and `race_hit_rate` (`Decimal | None`);
- lexically ordered immutable `Mapping[str, BetTypeSummary]` aggregated across completed days;
- `max_single_day_maximum_drawdown: int | None`.

Only `FULL_DAY_REPLAY_COMPLETED` records contribute a `SimulationSummary` to financial/count
totals. Both diagnostic states remain in the selected tuple and state counts but contribute no
synthetic summary or monetary denominator. A completed zero-investment/no-bet result is a
completed day and remains distinct from either diagnostic state. A nonempty diagnostic-only
selection is valid: completed totals are exact zero, all ratios are `None`, the by-bet-type map is
empty, and `max_single_day_maximum_drawdown` is `None`.

All additive integer fields are summed over selected completed summaries. `profit` is then
recomputed as aggregate payout minus aggregate investment. Ratios are never averaged:

```text
ROI            = None if investment == 0 else Decimal(payout) * 100 / Decimal(investment)
bet hit rate   = None if settled_bet_count == 0
                 else Decimal(hit_bet_count) * 100 / Decimal(settled_bet_count)
race hit rate  = None if settled_purchase_race_count == 0
                 else Decimal(hit_race_count) * 100 / Decimal(settled_purchase_race_count)
```

The implementation uses `Decimal("100")` and the exact `SimulationSummary` semantics; no float,
rounding policy or daily percentage averaging is allowed. For each supported validated bet type,
Phase 28 unions completed-day keys, sums `bet_count`, `settled_bet_count`, `hit_bet_count`,
investment and payout, computes profit as payout minus investment, and recomputes ROI and bet hit
rate from those sums. Mapping keys are lexical and no synthetic/unsupported bet type is created.

Plain or cumulative `maximum_drawdown` is deliberately absent. Phase 28 has no chronological
intra-day equity sequence, so it may expose only
`max_single_day_maximum_drawdown`: the maximum daily `SimulationSummary.maximum_drawdown` over
completed selected records, or `None` with no completed record. It must never be labelled or
represented as a cumulative/race-level maximum drawdown.

`aggregate_content_sha256` is a second lowercase SHA-256 identity over a canonical payload with
version `nar-daily-replay-aggregation-result-v1`. It binds every aggregate result field above,
including selection SHA/ordered members, compatibility key, day-state counts, totals, exact
Decimal text, lexical by-bet-type values and the explicitly named drawdown statistic. The same
records in the same validated selection order always produce the same result identity; changing a
member or any resultant semantic field changes it.

## Read-only and isolation boundaries

The Phase 28 application only calls `repository.load_result` once per supplied identity. It must
not write SQL, begin or end transactions, invoke a migration, modify an input record, create a
table/cache/export, or persist an aggregate. It must contain no network client, replay,
acquisition, evidence resolver, manifest writer, settlement, prediction, value, strategy,
allocation, `datetime.now`, `datetime.utcnow`, `time.time`, random or UUID behavior. Phase 28
modules are analysis outputs and must not be imported by HistoricalInputSnapshot construction,
evidence resolution, PredictionPipeline, engines, Predictor, ValueEngine, BetGenerator,
BetStrategy or stake allocation.

## Exact future implementation scope

Only the following files are proposed for a separately approved Phase 28 implementation:

```text
scripts/simulation/nar_daily_replay_aggregation.py
tests/test_nar_daily_replay_aggregation.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

All Phase 27 persistence/repository files, models, migrations, runner, replay/orchestrator,
prediction/value/strategy code, CLI, database/** and logs/** are forbidden. If implementation
requires another file, it must stop for a scope decision.

## Required later verification

The future implementation must prove:

1. selection requires a nonempty explicit SHA tuple, rejects malformed/duplicate IDs, missing
   exact IDs, noncanonical caller order and duplicate target dates, and never performs latest,
   date, row-order or fallback selection;
2. exact Phase 27 `load_result` is the only persistence read boundary; no raw-row shortcut,
   write, migration, replay, acquisition, evidence resolution, manifest generation, clock,
   network or output-feedback dependency exists;
3. one/multiple completed days, diagnostic-only days and mixed states retain exact selected-state
   accounting; diagnostics do not enter financial totals; completed no-bet remains distinct;
4. every additive total, profit, Decimal ratio and zero-denominator `None` behavior is exact;
   daily ROI/hit rates are never averaged;
5. by-bet-type union, lexical order, exact sums and recomputed Decimal values are exact;
6. incompatible provider/schema/dataset/policy/cutoff/strategy/commit/budget records fail closed,
   while different compatible run IDs are accepted;
7. `max_single_day_maximum_drawdown` is exact, the aggregate has no plain `maximum_drawdown`, and
   no cumulative MDD is synthesized;
8. selection and aggregate SHA values are deterministic, independent of database row order, and
   change when a member or semantic result changes; and
9. Phase 27 repository/persistence regressions and the full suite pass with database/** and
   logs/** unchanged.

## Stop condition

Phase 28 implementation is complete and stops at `READY_FOR_REVIEW`. Review and explicit commit
approval are required before any stage, commit or push. No Phase 29 preparation is authorized.

## EXECUTE result

The exact frozen API is implemented in one new read-only module. It loads each selected identity
once through the concrete Phase 27 exact-ID repository, rejects missing, duplicate, descending,
duplicate-date or incompatible selection, and never sorts or chooses an attempt. Completed-day
integer totals and bet-type totals are summed; all Decimal rates are recomputed from final totals.
Diagnostics remain in selection/state accounting without summary values. Only
`max_single_day_maximum_drawdown` is exposed, and both selection/result identities use the frozen
versioned canonical payloads.

Verification completed:

```text
Dedicated Phase 28 with ResourceWarning-as-error: 18 passed
Phase 27 repository regression: 22 passed
Phase 27 persistence regression: 10 passed
Related models/summary/repository regression: 178 passed
Combined Phase 27 and related regression: 210 passed
Full unittest discovery: 3,142 passed
Python compilation and static boundary checks: passed
```

The dedicated suite is warning-clean. Full-suite output contains only the pre-existing unrelated
unclosed-SQLite `ResourceWarning` class already reported in prior phases. No relevant pytest-only
Phase 28 test exists outside unittest discovery. All modifications remain unstaged and confined to
the exact four Allowed Files; database/** and logs/** are unchanged. Blockers: none.

## Final-review correction result

The result-construction trust boundary now rejects ordinary direct construction of
`NARDailyReplayAggregationResult`. The only implementation path is a private validated factory
fed the exact records returned by the Phase 27 repository; it derives coverage dates, state
counts, all integer and Decimal aggregates, bet-type totals, drawdown statistic, selection SHA and
result SHA from those records. Focused negative coverage proves forged first/last dates, forged
state counts and `dataclasses.replace(...)` cannot produce a trusted result.

The multi-day arithmetic fixture now uses completed days with race-hit inputs of `1/1` and `1/4`.
The aggregate asserts exact total-first `2/5 * 100 = Decimal("40")`, which differs from the daily
rate arithmetic mean of `62.5`. The existing ROI, bet-hit, bet-type, diagnostic, selection,
compatibility, drawdown and read-only boundaries remain unchanged.

Final correction verification:

```text
Dedicated Phase 28: 20 passed (ResourceWarning-as-error clean)
Phase 27 repository: 22 passed
Phase 27 persistence: 10 passed
Phase 25 orchestrator: 21 passed
Related model/repository suites: 206 passed
Full unittest discovery: 3,144 passed
Compilation and static boundaries: passed
```

The broad related/full commands retain only the previously reported unrelated unclosed-SQLite
warnings. No relevant pytest-only Phase 28 test exists. Status remains `READY_FOR_REVIEW`;
blockers are none.
