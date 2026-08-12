# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d2` — historical final-odds evidence-role PREPARE.

Formal base: `0135cee4ad8e578e6bd20940b16198a576172c04`.

Approved references:

```text
d1d  = 3e7de6780c9fb8af6169d015b942bd4d72dde576
d1d1 = 669b59e1955f389fc067afc6d8eaaee3c39a09ba
```

Review branch: `review/4c-2d3b1i6d1d2-evidence-prepare`.

## Selected Provider-Neutral Evidence Extension

`historical_race_final_odds` means the immutable official response that directly supplies final odds used for a historical race's `past_race.record_values["odds"]`.  It is neither target-race prediction odds, popularity, payout, implied probability, nor a model estimate.  The role is provider-neutral; any provider may use it only when it has genuinely separate direct final-odds evidence.

The only approved `past_race` evidence-role sets are:

```text
EXISTING_TWO_ROLE_SET =
    historical_race_context
    historical_race_result

EXTENDED_THREE_ROLE_SET =
    historical_race_context
    historical_race_final_odds
    historical_race_result
```

The actual canonical lexical order is exactly the order shown: `historical_race_context`, then
`historical_race_final_odds`, then `historical_race_result`.  It follows the existing sort by `evidence_role`, not a
provider or presentation order.

All non-`past_race` role contracts remain exactly unchanged.  A past race may have exactly one of the two approved
sets, never a partial, four-role, unknown-role, or duplicate-role combination.  Context and result are always
required; final odds is optional only as the complete third role.  Evidence remains a nonempty exact tuple of exact
`HistoricalInputEvidenceReference` values, canonically sorted, and same-underlying-response reuse remains valid only
when `(canonical_source_url, response_sha256)` has identical `available_at` and `observed_at` for every reused role.

This keeps NAR's existing two-response/two-role past-race records valid without organization branching.  A future
JRA normalizer may bind accessS to context and result and an independently captured official final-odds response to
final odds, subject to the separately designed JRA capture extension.

## Source Record and Conflict Semantics

Only `_EVIDENCE_ROLES["past_race"]` and its validator need a neutral extension to accept either exact tuple.  The
canonical source payload already serializes `evidence` as an ordered list of `{evidence_role, canonical_source_url,
response_sha256}`; timestamps are deliberately excluded.  No payload key, encoding, existing role spelling, record
value, or source-ID namespace changes.

```text
HistoricalInputSourceRecord.schema_version = 4 (unchanged)
source ID namespace = his-v4 (unchanged)
```

For every existing valid record, the role tuple and canonical payload are unchanged byte-for-byte; its source ID is
unchanged.  A new final-odds reference changes the new record's canonical evidence list and therefore source ID.
Changing only either evidence timestamp remains source-ID invariant.

`validate_historical_input_source_record_set` remains unchanged.  Its existing conflict identity is
`(source_system, external_race_id, external_entry_id, provider_record_id)`.  Thus two records for the same official
past result that differ only in final-odds evidence URL/SHA have distinct source IDs and correctly raise existing
`HistoricalInputSourceConflictError` if supplied in one source set.  It must not choose a latest evidence record or
silently discard either one.

## Snapshot, Builder, and SQLite Impact

`HistoricalInputProvenance` already stores a nonempty tuple of evidence references and serializes every member into
the snapshot canonical payload, including role, URL, raw SHA, `available_at`, and `observed_at`.  Only its
past-race required-role validator must accept the same two exact role sets.  It must continue to sort lexically and
enforce duplicate-role rejection and coherent timestamps for same-response role reuse.

The snapshot canonical payload has an existing nested evidence-list representation and schema version 4.  It needs
no structural change.  An existing snapshot constructed from an unchanged NAR record retains exactly the same
canonical payload and `content_sha256`.  A snapshot that contains a final-odds evidence reference includes it in
provenance, including timestamps, and therefore intentionally has a different content digest.

The builder already passes each `record.evidence` unchanged into provenance and checks causality by iterating every
evidence item.  It has no two-role literal, role-specific switch, or evidence-cardinality assumption.  It must not
be changed.  The new final-odds observation will be independently checked by the existing builder and snapshot
causality boundaries.

SQLite `historical_input_snapshot_provenance_evidence` stores role as nonempty TEXT and uses generic evidence order
plus unique `(snapshot_id, audit_key, evidence_role)`.  The SQLite repository reads and writes the full ordered tuple
without an evidence-role enum.  Therefore role acceptance changes in the source and snapshot domains require no
global DDL, source-repository DDL, snapshot-repository DDL, or repository production change.

```text
EVIDENCE_ROLE_EXTENSION_READY = YES
SOURCE_SCHEMA_VERSION_BUMP_REQUIRED = NO
SNAPSHOT_SCHEMA_VERSION_BUMP_REQUIRED = NO
BUILDER_PRODUCTION_CHANGE_REQUIRED = NO
GLOBAL_MIGRATION_REQUIRED = NO
SOURCE_REPOSITORY_MIGRATION_REQUIRED = NO
SNAPSHOT_REPOSITORY_MIGRATION_REQUIRED = NO
EXISTING_NAR_SOURCE_IDS_PRESERVED = YES
EXISTING_SNAPSHOT_HASHES_PRESERVED = YES
NEW_FINAL_ODDS_CHANGES_SOURCE_ID = YES
NEW_FINAL_ODDS_CHANGES_SNAPSHOT_DIGEST = YES
```

The separate JRA accessO capture/archive v002 requirement remains outside this provider-neutral phase.

## Required Implementation Contract

The narrow implementation changes only the two validators:

```text
scripts/simulation/historical_input_source_records.py
scripts/simulation/historical_input_snapshots.py
```

It must add regression coverage for both exact role sets; deterministic lexical order; all rejected partial,
unknown, duplicate, and over-complete sets; same-response timestamp coherence; preserved source ID/payload for
existing NAR two-role records; new role source-ID change without timestamp source-ID change; preserved existing
snapshot payload/digest; changed digest with final odds; builder propagation/causality of the third role; and existing
conflicting-past-race behavior for competing final-odds evidence.  No NAR normalizer, source producer, snapshot
builder production file, repository, migration, capture, fixture, package-root export, or JRA normalizer changes are
authorized.

## Next Phase

Recommended next phase: `4C-2d3b1i6d1d3 — historical final-odds evidence-role IMPLEMENTATION`.

Its exact allowed files are:

```text
scripts/simulation/historical_input_source_records.py
scripts/simulation/historical_input_snapshots.py
tests/test_historical_input_source_records.py
tests/test_historical_input_snapshots.py
tests/test_historical_input_snapshot_builder.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Implementation is not authorized by this PREPARE.  After formalizing d1d3, a separate JRA accessO capture PREPARE
and implementation can address the official POST capture extension.  Do not begin either work now.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop for independent review.  Do not implement d1d3, accessO capture, JRA historical normalization, NAR changes,
fixtures, migration, bridge, or acquisition orchestration.
