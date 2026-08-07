# Current Phase

## Status

APPROVED_FOR_COMMIT

## Phase

Phase 4C-2d3b1i6b3b — Historical input snapshot SQLite repository eligible latest load and reconstruction

## Base Commit

`6c844e943b408074e6269858887846ff31233661 test: support Python 3.14 verification`

## Branch

`feature/ver0.8-simulator`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Objective

Implement only the read side of the committed V3d historical-input snapshot repository by adding this exact
method to `SQLiteHistoricalInputSnapshotRepository`:

```python
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

The committed `save_snapshot(*, snapshot)` behavior is frozen. This phase performs no V3c source construction,
migration/schema/runner work, bootstrap, package export, or service/CLI composition.

## Caller Validation

Before querying, validate only caller-controlled values and raise `RepositoryValidationError` on failure:

- `dataset_id` is an exact non-empty NFC-normalized `str`.
- `race_id` is an exact positive `int` (not `bool`).
- `information_cutoff` is an exact timezone-aware `datetime`; normalize it to UTC for the SQL parameter. No
  current-time fallback is allowed.
- `source_identity` is exactly `HistoricalExternalRaceIdentity`; its existing constructor supplies the
  normalized non-empty organization, source system, and external race ID contract.

Do not classify stored malformed data as caller validation and do not reconstruct a substitute source identity.

## Eligible Latest Selection

The header query is constrained exactly by the requested dataset, internal race ID, and source identity:

```sql
WHERE dataset_id = ?
  AND internal_race_id = ?
  AND organization = ?
  AND source_system = ?
  AND external_race_id = ?
  AND captured_at_utc <= ?
  AND information_cutoff_utc <= ?
ORDER BY captured_at_utc DESC
LIMIT 1
```

Both eligibility predicates are mandatory. There is no cross-dataset, cross-race, cross-source, external-race,
or older-snapshot fallback. `ORDER BY captured_at_utc DESC` is the only ordering term. The committed unique
natural identity `(dataset_id, organization, source_system, external_race_id, captured_at_utc)` makes a tie at
one requested source/dataset/captured instant impossible, so no tie-breaker is needed.

Latest-header selection occurs from `historical_input_snapshots` only, before and independently of every race,
entry, past-race, provenance, or mapping query. It must not inner-join any child or mapping table: an incomplete
newest eligible header is binding and must fail closed rather than be skipped in favor of an older header.

No eligible header returns `None`. Once a header is selected, every parse, join, cardinality, domain, or digest
failure is `RepositoryDataIntegrityError`; an older eligible snapshot must not be queried or returned.

## Read-only Transaction Behavior

`load_latest_snapshot` is read-only. It permits an active caller transaction, does not issue `BEGIN`,
`COMMIT`, or `ROLLBACK`, and does not apply migrations, create schema, alter mappings, or open another
connection. The already committed constructor foreign-key validation remains unchanged; load itself does not
change `PRAGMA foreign_keys`.

## Header and Mapping Integrity

Read the selected header's exact `snapshot_id`, dataset/source identity, internal race ID, source URL,
captured-at UTC text, information-cutoff UTC text, and content SHA-256. Require exact stored SQLite types and
the selected header's fields to equal the lookup dimensions.

The reader needs no source-identity table data to reconstruct the domain object. It must, however, verify the
minimum persisted mappings that bind reconstruction to the selected header:

- exactly one `historical_input_external_races` row matches the header organization, source system, external
  race ID, and internal race ID; and
- each snapshot entry has exactly one matching `historical_input_external_entries` row with the same source,
  external race ID, internal race ID, external entry ID, and race-entry ID.

These checks mirror the committed FK/trigger linkage for fail-closed reading of directly tampered data. They do
not introduce reverse lookup, mapping repair, or new source policy.

## Strict Stored Parsers

All parser and domain-construction failures from stored rows, including `ValueError`, `TypeError`,
`KeyError`, `AttributeError`, `decimal.InvalidOperation`, and SQLite read errors, become
`RepositoryDataIntegrityError` without repair.

- UTC datetime columns must be exact `str` values that parse as aware UTC and equal
  `parsed.astimezone(timezone.utc).isoformat(timespec="microseconds")` byte-for-byte. Reject missing
  microseconds, `Z`, non-UTC offsets, whitespace, invalid calendar/time values, and non-text SQLite storage.
- Date columns must be exact `str` values that parse through `date.fromisoformat()` and equal
  `parsed.isoformat()` exactly.
- Decimal TEXT columns (`win_odds_text`, `margin_text`, `weight_text`, `weight_diff_text`, `odds_text`) must
  be exact finite `str` values. Parse with `Decimal` only, never float; canonicalize zero to `Decimal("0")`,
  otherwise normalize, and require `format(canonical, "f") == stored_text`. Thus reject `2.50`, `02.5`, `-0`,
  NaN, Infinity, whitespace, and integer SQLite storage.
- Required integers must be exact `int` SQLite values; optional integers are `None` or exact `int` values.
  Required/optional text must be exact `str`/`None` as applicable and must already be NFC-canonical; only
  `passing_order` may be empty.
- Header `content_sha256` is exact lower-case hexadecimal text of length 64. Nullable source URL and external
  horse ID are `None` or non-empty NFC-canonical `str`.

The V3a constructors remain the final authority for ranges, contiguity, causal timing, required provenance, and
audit-key shapes.

## Reconstruction and Digest

Reconstruct the complete committed V3a object graph: `HistoricalSourceIdentity`,
`HistoricalExternalRaceIdentity`, `HistoricalExternalEntryIdentity`, `HistoricalInputSnapshotIdentity`,
`HistoricalRaceSnapshot`, ordered `HistoricalRaceEntrySnapshot` values, ordered
`HistoricalPastRaceSnapshot` values, ordered `HistoricalInputProvenance` values, and the final
`HistoricalInputSnapshot`.

Retrieve children in deterministic order: entries by `entry_order ASC`; past races by
`race_entry_id ASC, past_race_index ASC`; provenance by `audit_key ASC`. Require exactly one race child, at
least one entry, valid references from past races/provenance to entries, and the complete provenance key set
through the final V3a constructor. Missing child rows, malformed values, duplicate/inconsistent rows available
through DB tampering, or a constructor rejection are `RepositoryDataIntegrityError`.

The final `HistoricalInputSnapshot` recomputes its canonical V3a content digest. Compare that computed digest
to the selected header's stored `content_sha256`; a mismatch is `RepositoryDataIntegrityError`. Do not reload,
retry, repair, or fall back to an older eligible header.

## Allowed Files

- `scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py`
- `tests/test_sqlite_historical_input_snapshot_repository.py`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

No additional production, test, migration, schema, package, or requirements file is required. Shared private
parser helpers may be added in the repository module only when they leave save behavior byte-for-byte equivalent
in result and observable side effects.

## Forbidden Files

- V3a historical domain, v010 migration, migration runner, legacy schema/bootstrap, composition, services,
  CLI, README, package `__init__.py`, and all unrelated production/tests.
- `database/keiba.db`, `logs/`, external fetch/source construction, V3c mapping/policy, and b3a save semantics.
- b3b fallback, retry, mutation, repair, update/delete/upsert, or an additional connection.

## Required Tests

Dedicated real-`:memory:` SQLite tests must cover:

1. Exact public API, keyword-only arguments, type hints, no package-root export, and no migration/bootstrap/V3c
   behavior.
2. No eligible snapshot; dual eligibility; future capture; exact dataset/race/source boundaries; and the only
   allowed `captured_at_utc DESC` ordering.
3. Full round-trip reconstruction of source URL, external horse IDs, internal race ID, UTC datetimes, date,
   canonical Decimal values, empty `passing_order`, nullable provenance fields, and all child ordering.
4. Strict stored datetime/date/Decimal/type parsing failures, missing race/entry/provenance rows, malformed
   mapping relationships, and V3a constructor failure, each as `RepositoryDataIntegrityError`.
5. Stored digest mismatch and each malformed latest case with an older valid eligible snapshot, proving no
   fallback, including missing race child, malformed mapping reconstruction, and non-canonical parseable
   datetime/date/Decimal text.
6. Caller invalid dataset/race/cutoff/source as `RepositoryValidationError`; active caller transaction read
   behavior; successful load and `RepositoryDataIntegrityError` leave its uncommitted work active and neither
   commit nor roll it back; and no mutation/transaction SQL from load.
7. Existing b3a atomic save tests unchanged and green.

Use the committed migration chain and controlled direct SQLite tampering only in tests; do not weaken schema.

## Verification Plan

Use the current reproducible Windows baseline: Python 3.14.5, pytest 8.3.5, and tzdata 2026.3. Run the
dedicated repository suite, historical domain/v010 migration regression, existing SQLite repository/migration
regression, and `python -m pytest -q`; acceptance is zero failures. Run `git diff --check` and verify only the
four allowed files changed.

## Stop Condition

Implementation is complete and Phase 4C-2d3b1i6b3b is `READY_FOR_REVIEW`, awaiting ChatGPT implementation
review and explicit commit approval. Do not stage, commit, push, or begin V3c; V3c remains deferred and
unimplemented.
