# Current Phase

## Status

APPROVED_FOR_COMMIT

## Phase

Phase 4C-2d3b1i6b1 — Historical input snapshot domain implementation

## Base Commit

`0ab53e57adaf4971cd8c576024d90647a6d1bf09 docs: approve historical input snapshot v3 contract`

## Branch

`feature/ver0.8-simulator`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is not a modification target.

## Objective

Implement only the approved V3a historical-input snapshot domain and Protocol contract in one module:
`scripts.simulation.historical_input_snapshots`. The authoritative design is the approved V3a plus V3d
contract in `docs/VER0.8_SIMULATOR_DESIGN.md`; this phase must not redesign it.

## Completed Dependencies

- Phase 4C-2d3b1i6a V3a domain/identity/digest contract is approved.
- V3b executable eight-table DDL contract is approved but is not implemented by this phase.
- V3c source mapping and policy contract is approved but is not implemented by this phase.
- V3d consolidation is approved and establishes V3a + V3b + V3c + V3d as the authoritative contract.
- Existing `InputAuditEntry` establishes the compatible provenance field shape and temporal-audit convention.

## Allowed Files

- `scripts/simulation/historical_input_snapshots.py`
- `tests/test_historical_input_snapshots.py`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

## Forbidden Files

- `scripts/simulation/__init__.py` and every package-root export.
- All other production modules, existing tests, `README.md`, CLI, settings, provider/parser/collector code,
  repository implementations, migrations, schema, and `scripts/database.py`.
- Database files, including `database/keiba.db`, and `logs/`.
- SQLite adapters, concrete repositories, source implementations, services, factories, list/fallback APIs,
  ABCs, and runtime Protocol checks.
- V3b DDL, V3c source-record digests, persistence behavior, loader selection, import/backfill work, and
  `SimulationRaceInput` assembly from historical snapshots.

## Exact Public API

The module-defined public contract is exactly these nine frozen, slotted dataclasses:

1. `HistoricalSourceIdentity`
2. `HistoricalExternalRaceIdentity`
3. `HistoricalExternalEntryIdentity`
4. `HistoricalInputSnapshotIdentity`
5. `HistoricalRaceSnapshot`
6. `HistoricalRaceEntrySnapshot`
7. `HistoricalPastRaceSnapshot`
8. `HistoricalInputProvenance`
9. `HistoricalInputSnapshot`

It also defines exactly these two `Protocol` classes:

1. `HistoricalInputSnapshotSource`
2. `HistoricalInputSnapshotRepository`

It also defines exactly these two public functions:

1. `build_historical_input_snapshot_content_payload`
2. `compute_historical_input_snapshot_content_sha256`

All helpers are private. No additional public class, function, concrete repository, SQLite adapter,
collector, parser, migration, service, factory, `ABC`, `runtime_checkable`, package export, list API, or
fallback API may be added.

## Domain Invariants

All nine values use `@dataclass(frozen=True, slots=True)` and preserve their approved V3a field order,
defaults, and equality/hash policy. `HistoricalSourceIdentity.source_url` and
`HistoricalExternalEntryIdentity.external_horse_id` are metadata fields with `compare=False, hash=False`.
The snapshot natural identity is `dataset_id`, organization, source system, external race ID, and
`captured_at`; no surrogate identity is permitted.

Construction uses exact-type validation: required integers reject `bool`; exact tuples are required with no
list-to-tuple coercion; string values are NFC-normalized; datetimes are normalized to UTC; dates must be
`date` exactly rather than `datetime`; decimals must be finite and canonically normalized; and approved
positive/non-negative constraints apply. `passing_order` accepts an exact `str`, including `""`, and retains
the empty string after NFC normalization. Optional text follows the approved optional-text rules. Direct
construction failures are `ValueError`; invalid values are never repaired silently.

`HistoricalInputProvenance` remains field-for-field compatible with
`scripts.simulation.models.InputAuditEntry`. Its only input types are `track`, `entry`, `odds`, `jockey`, and
`past_race`; its only audit keys are `track`, `entry/{race_entry_id}`, `odds/{race_entry_id}`,
`jockey/{race_entry_id}`, `past_race/{race_entry_id}/{past_race_index}`, and
`past_race/{race_entry_id}/none`. `odds_win` and `past_race_absence` are V3c source-record names, not
provenance input types. At least one of `available_at` and `observed_at` is required.

Snapshots require non-empty entries and reject duplicate race-entry IDs, horse numbers, external-entry natural
identities, entry orders, audit keys, and `(race_entry_id, past_race_index)` pairs. Entry order is zero-based
and contiguous. Past-race indexes are zero-based and contiguous for each entry; every past race references a
current entry and precedes the target date. Each external entry's race identity equals the snapshot
organization, source system, and external race ID. Numbered past races forbid `/none`; no past races require
exactly one `/none` audit. Causal times obey
`available_at <= observed_at <= captured_at <= information_cutoff <= scheduled_start_at` subject to the
approved nullable timestamp rules.

## Digest Contract

Digest schema version is `1`. `HistoricalInputSnapshot.content_sha256` is derived with
`init=False, compare=False, hash=False`. Post-initialization validates and canonicalizes values, builds a
private unchecked payload, canonicalizes JSON, computes SHA-256, and assigns the digest with
`object.__setattr__`; it must not call either public payload/digest function.

Canonical JSON is UTF-8 with `ensure_ascii=False`, `sort_keys=True`, and separators `(",", ":")`.
Datetimes serialize as `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`, dates as `YYYY-MM-DD`, and canonical decimals as
strings without redundant zeroes or negative zero. Entries sort by `entry_order`, past races by
`race_entry_id` then `past_race_index`, and provenance by `audit_key`. The payload includes source URL,
external horse ID, information cutoff, internal linkage fields, and provenance; it excludes
`content_sha256`. `passing_order=""` remains an empty JSON string.

## Protocol Contract

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


class HistoricalInputSnapshotRepository(Protocol):
    def save_snapshot(
        self,
        *,
        snapshot: HistoricalInputSnapshot,
    ) -> None:
        ...
```

Both methods are keyword-only, have no defaults, and use ellipsis bodies. `source_identity` is mandatory.
There is no `runtime_checkable`, concrete implementation, fallback, or list API. Existing
`RaceEntrySelectionResolver` Protocol tests are the local style reference.

## Source/AST Boundary

The new domain module may use only required standard-library dependencies: `dataclasses`, `datetime`,
`decimal`, `hashlib`, `json`, `typing.Protocol`, and `unicodedata`, plus existing simulation domain types only
where approved compatibility requires them. It must not import or depend on SQLite, requests, providers,
parsers, migrations, repository implementations, prediction engines, CLI/config/database code, network,
filesystem, clock APIs, random, or subprocess.

## Required Tests

Create a real unit/contract suite without mocks, patching, or monkeypatching. It must cover the nine
dataclass field/signature contracts; frozen/slotted behavior; identity equality/hash exclusions; strict
constructor rejection; NFC and UTC normalization; exact date and Decimal canonicalization; empty
`passing_order`; provenance key/type relations and `InputAuditEntry` field compatibility; structural
completeness, duplicates, contiguous orders, external race linkage, causal time rules, past-before-target,
and `/none` XOR; derived digest and exact canonical payload keys/order; digest determinism and sensitivity;
both public functions; both Protocol signatures; lack of runtime Protocol support/package export; and the
forbidden dependency/AST boundary.

Digest sensitivity includes equal canonical numerics; metadata-only source URL and external horse-ID changes
that leave equality unchanged but change the digest; cutoff changes with captured-at held equal; approved
canonical-order permutations; and the preserved empty `passing_order` JSON value.

## Verification Commands

Use the repository-approved Python runtime:

```powershell
& "C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest tests/test_historical_input_snapshots.py -q
& "C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest tests/test_simulation_models.py tests/test_persisted_simulation_race_inputs.py tests/test_race_entry_selection_resolver_contract.py -q
& "C:\Users\garim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest -q
git diff --check
git status --short
```

## Stop Condition

Preparation only.

Do not modify production code or tests.

Do not stage, commit, or push.

Stop for ChatGPT review.
