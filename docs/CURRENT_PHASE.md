# Current Phase

## Status

READY_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1c - Historical input source-record to snapshot assembly

## Base Commit

`f6a72be9e9a6934cfa48c6b0ff41954fb7d51de1 feat: normalize NAR historical source records`

## Branch and Workspace

Formal branch: `feature/ver0.8-simulator`

Canonical workspace: `C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is read-only for this phase.

## Objective and Responsibility Boundary

c1c implements the smallest pure, fail-closed assembler from a caller-supplied, already validated
tuple of `HistoricalInputSourceRecord` values plus caller-owned local identity and cutoff inputs to one immutable
`HistoricalInputSnapshot`. It owns source-record grouping, external-to-internal entry mapping, deterministic child
construction, provenance construction, and source-set temporal eligibility only.

It must not fetch HTTP, decode provider HTML, query or write SQLite, call a repository, access a file or the clock,
use legacy race/horse/odds/past-race data, infer a missing source fact, or construct a simulation request. c1b keeps
normalizing supplied DebaTable bytes; later phases own provider collection, complete past-race capture, persistence,
and snapshot loading.

## Investigation Findings

`HistoricalInputSourceRecord` already validates individual schemas and deterministic `source_id` values. Its
`validate_historical_input_source_record_set()` is called first by the assembler and remains the sole
owner of duplicate-source-ID and conflicting official past-race identity checks. It does not establish a complete
race snapshot, local race-entry mapping, snapshot-level temporal eligibility, or past-race sequence.

`HistoricalInputSnapshot` requires nonempty entries, contiguous entry orders, complete and unique provenance keys,
causal `captured_at <= information_cutoff <= scheduled_start_at`, and complete past-race evidence per entry. It also
requires source stamps no later than `captured_at`. c1c must apply the stricter prediction rule that no record used
by the snapshot may be later than the caller's `information_cutoff`.

c1b currently emits only `track`, `entry`, `jockey`, and `odds_win`. It deliberately emits neither `past_race` nor
`past_race_absence`; therefore a c1b DebaTable tuple alone is insufficient and must fail closed. Missing past-race
records never mean a scoped zero-result search occurred.

## Proposed Future Public API

Future module: `scripts/simulation/historical_input_snapshot_builder.py`

The module will expose only:

    HistoricalInputSnapshotAssemblyError
    build_historical_input_snapshot

The implemented keyword-only API is:

    build_historical_input_snapshot(
        *,
        dataset_id: str,
        internal_race_id: int,
        information_cutoff: datetime,
        captured_at: datetime,
        source_records: tuple[HistoricalInputSourceRecord, ...],
        race_entry_id_by_external_entry_id: Mapping[str, int],
    ) -> HistoricalInputSnapshot

No bundle/dataclass, database connection, repository, URL, provider, optional clock, or fallback parameter is
implemented. `source_records` must be an exact tuple and every item an exact committed c1a record. The mapping must be
a `Mapping`; it is caller-owned input, is copied only as needed for validation, and is never resolved from a local
database or from `horse_no`.

## Source Family, Snapshot Identity, and URL Policy

After the committed c1a set validator succeeds, c1c requires exactly one common `(organization, source_system,
external_race_id)` across every record and exactly one `track` record. It constructs:

    HistoricalSourceIdentity(organization, source_system, external_race_id, source_url)
    HistoricalExternalRaceIdentity(organization, source_system, external_race_id)
    HistoricalExternalEntryIdentity(external_race_identity, external_entry_id, external_horse_id)
    HistoricalInputSnapshotIdentity(dataset_id, source_identity, captured_at)

The sole track record determines the snapshot-level source URL without adding a provider-neutral URL requirement:

    track.canonical_source_url is non-null -> HistoricalSourceIdentity.source_url is that exact URL
    track.canonical_source_url is None     -> HistoricalSourceIdentity.source_url is None

Both forms are valid; c1c must not fail solely because the track record has no canonical source URL. It must never
synthesize a URL from non-track records, provider_record_id, source_id, external_race_id, local database rows, or
legacy race URLs. Non-track records are not required to share the track URL. Their canonical_source_url values remain
in their immutable c1a payloads and therefore participate in each exact c1a `source_id`; provenance continues to
carry that exact `source_id`, not a duplicated URL. The committed c1a requirement that a past_race_absence record has
its own non-null canonical_source_url is unchanged; c1c consumes that already-validated record and adds no absence
URL validation algorithm.

## Complete Source-set Policy

| Scope | Required records and rule |
| --- | --- |
| Race | Exactly one track record and one common source family/race identity. |
| External entry | Exactly one entry, one jockey, and one odds_win record. Their envelope external entry ID must agree. |
| Entry values | Entry and odds_win horse number must agree; entry external horse identity comes only from entry values. |
| Past evidence | Either one or more past_race records, or exactly one past_race_absence record, never both and never neither. |
| Absence proof | The c1a absence query scope must name the same external entry, have exact zero result count, and target the track target-race date with strictly-before-target behavior. |
| Unknown/incompatible | An unknown kind, duplicate required record, inconsistent family/race/entry, extra mapping key, or unsupported record grouping raises an assembler error. |

All entry-scoped records are grouped by their envelope `external_entry_id`, never by source tuple order or local
horse identity. The committed c1a validator remains responsible for source-ID and provider-record conflicts; c1c
does not reimplement its digest or conflict algorithm.

## Explicit External-to-internal Mapping Contract

`race_entry_id_by_external_entry_id` must have a key set exactly equal to the complete external-entry set produced
from entry records. Each key must be exact `str`; every value must be an exact positive `int`, not `bool`; and mapped
internal IDs must be unique. Missing keys, extra keys, duplicate internal IDs, a nonpositive ID, or a type mismatch
fails closed before snapshot construction. There is no local lookup, no guessed ID, and no fallback from horse number.

Complete entries are sorted by `horse_no` ascending. c1c assigns contiguous zero-based `entry_order` from that sort,
independent of caller tuple order or local race-entry ID order.

## Field and Provenance Mapping

The sole track record maps its exact committed c1a values to `HistoricalRaceSnapshot`:

    target_race_date, scheduled_start_at, place, distance_m, track,
    track_condition, race_name, race_class, weather

No entry, jockey, odds, or past record may overwrite a track field. Each entry/jockey/odds triple maps to one
`HistoricalRaceEntrySnapshot` using the explicit internal race-entry ID, entry `external_horse_id`, entry and odds
horse-number agreement, direct jockey text, direct Decimal win odds, and canonical entry order.

Provenance is one-to-one with source records and always preserves exact `source_id`, `available_at`, and `observed_at`:

| c1a record kind | HistoricalInputProvenance input_type | audit_key |
| --- | --- | --- |
| track | track | `track` |
| entry | entry | `entry/{race_entry_id}` |
| jockey | jockey | `jockey/{race_entry_id}` |
| odds_win | odds | `odds/{race_entry_id}` |
| past_race | past_race | `past_race/{race_entry_id}/{past_race_index}` |
| past_race_absence | past_race | `past_race/{race_entry_id}/none` |

`HistoricalInputProvenance.source` is the exact record `source_system`; its source ID is the exact c1a `source_id`.
c1c does not create `InputAuditEntry`, `InputSnapshotAudit`, or `SimulationRaceInput`; it only obeys the same
canonical audit-key shape already enforced by `HistoricalInputSnapshot`.

## Temporal Eligibility Policy

All six API inputs are caller supplied; c1c never calls the clock. `captured_at` and `information_cutoff` must be
exact aware datetimes. Every used source record already has an aware `observed_at`; when present, `available_at` must
remain no later than its observed time. c1c requires every used temporal chain to satisfy:

    available_at <= observed_at <= captured_at <= information_cutoff <= scheduled_start_at

with the optional `available_at` term omitted only when it is `None`. Both available and observed stamps must also be
no later than the information cutoff. A newer source, an invalid ordering, or a stamp missing from a record fails
closed; captured_at is never derived from DB insertion, filesystem metadata, race start, maximum source timestamp,
or current time.

## Past-race Construction and Ordering

For each external entry with past-race records, c1c maps every c1a past-race value directly into
`HistoricalPastRaceSnapshot`. Each past date must be strictly earlier than the target race date. It sorts the entry's
past races by `race_date` descending (most recent first) and assigns contiguous zero-based `past_race_index` values.

Two past-race records for the same external entry with the same `race_date` fail closed. c1a supplies no proven
time-of-day chronology, and c1c must not use caller tuple order, database order, hash order, or lexical
`provider_record_id` as invented chronology. A valid c1a absence record yields no past snapshot and exactly the
`past_race/{race_entry_id}/none` provenance key. No record means neither history nor absence proof.

After each entry has received its chronology-derived `past_race_index`, the final
`HistoricalInputSnapshot.past_races` tuple is sorted globally by exactly `(race_entry_id, past_race_index)` ascending.
This is a serialization and object-level canonicalization rule, distinct from the within-entry `race_date` descending
chronology. It must not use horse number, external entry ID, caller source tuple order, database row order,
provider-record ID, or hash/random order.

The final `HistoricalInputSnapshot.provenance` tuple is sorted globally by exactly `audit_key` ascending using normal
Python string ordering over the already-constructed canonical keys. Every source record still maps one-to-one to its
exact provenance entry; only the final tuple ordering is canonicalized. It must not use source tuple order, source ID,
record kind, horse number, or insertion order.

## Error Ownership

The module has one assembler-owned `HistoricalInputSnapshotAssemblyError(ValueError)`. It owns exact input
type/container failures, incomplete/duplicate grouping, source-family disagreement, mapping violations, field
disagreement, temporal ineligibility, missing past evidence, and ambiguous past-race ordering. Committed c1a
`HistoricalInputSourceValidationError` and `HistoricalInputSourceConflictError` from the mandatory set validator
propagate unchanged. Direct `HistoricalInputSnapshot` domain `ValueError` values are not broadly wrapped. No
`except Exception`, retry, repair, or fallback is allowed.

## Determinism and Side-effect Boundary

The same source records, mapping, dataset ID, internal race ID, captured_at, and information cutoff must produce the
same snapshot and `content_sha256` irrespective of source tuple order. c1c freezes grouping and horse-number/past-date
ordering before constructing immutable snapshot children: entries remain horse-number ascending with contiguous
`entry_order`; final past races are `(race_entry_id, past_race_index)` ascending; final provenance is `audit_key`
ascending. It has no HTTP, parser, filesystem, database, repository, environment, random, UUID, or current-time
dependency and adds no package-root export.

## Allowed Files

    scripts/simulation/historical_input_snapshot_builder.py
    tests/test_historical_input_snapshot_builder.py
    docs/CURRENT_PHASE.md
    docs/LATEST_CODEX_REPORT.md

Existing production and tests, providers/parsers, migrations, schema, repositories, database files, logs, README,
main/CLI, and package exports are forbidden. A required change outside these four files is `REVISION_REQUIRED`.

## Implemented Tests and Verification

The dedicated suite covers the exact public surface/type hints; complete valid source set; caller tuple-order
independence; exactly one track; family/race consistency; full entry/jockey/odds triples; horse-number consistency;
mapping completeness/type/uniqueness; canonical entry order; track source URL selection with both a non-null URL and
None as valid outcomes; non-track URL nonselection and differing non-track URL invariance; exact provenance keys/source
IDs/timestamps; track/entry/past field mapping; captured/cutoff/start causal rules; multiple past races; valid absence;
past-and-absence conflict; missing evidence; same-date past ambiguity; c1b-only DebaTable rejection; deterministic
snapshot equality and content hash across materially different source-record tuple permutations; exact entries
`entry_order` ascending, global past-race `(race_entry_id, past_race_index)` ascending, and global provenance
`audit_key` ascending with two entries and multiple past races; no DB/network/filesystem/clock/legacy dependency; and
package-root non-export.

Verification runs the dedicated suite, source-record and snapshot regressions, SQLite snapshot repository and
migration regressions, full pytest, source/AST dependency checks, `git diff --check`, and `git status --short`.

## Stop Conditions and Blockers

This implementation changes only the four Allowed Files and stops at `READY_FOR_REVIEW` awaiting independent code
review and explicit commit approval. It does not authorize source collection, provider/parser changes, persistence,
or formal integration. Current c1b-only tuples are intentionally rejected as incomplete until a future source phase
provides complete official past-race records or exact c1a absence proof for every entry.

blocker: c1b supplies no past-race or past-race-absence evidence, so no complete HistoricalInputSnapshot can yet be
assembled from its DebaTable-only output.

## Implementation Review Validation-boundary Correction

The shared caller-datetime awareness helper now guards `tzinfo.utcoffset()` only for `TypeError`, `ValueError`, and
`OverflowError`. Such malformed caller-supplied timezone implementations now raise exact
`HistoricalInputSnapshotAssemblyError` for both `captured_at` and `information_cutoff`; UTC is not substituted and no
broad exception handling is used. Dedicated regressions also pin cutoff later than scheduled start, a non-Mapping
mapping, non-string mapping keys, and zero/negative mapping values.

Codex local verification with Python 3.14.5 / pytest 8.3.5 / tzdata 2026.3: dedicated c1c 12 passed; c1a 8 passed;
snapshot domain 16 passed; SQLite/migration regression 46 passed; full suite 2445 passed; forbidden source/AST check
passed; `git diff --check` passed. Status remains `READY_FOR_REVIEW` pending independent GitHub re-review.
