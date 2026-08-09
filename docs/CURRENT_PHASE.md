# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d3b - Historical multi-source evidence/provenance contract preparation

## Base Commit

3cd5f2916213f32340782f1c069d9093a4e75499 feat: define historical time-difference contract

## Branch and Workspace

Formal branch: feature/ver0.8-simulator

Preparation review branch: review/4c-2d3b1i6c1d3b-prepare

Canonical workspace: C:\Users\garim\Desktop\KeibaAI-review-1i5b2b

The original workspace, C:\Users\garim\Desktop\KeibaAI, is read-only for this phase.

## Objective and Boundary

This PREPARE freezes the smallest provider-neutral contract that permits one logical past_race source record to be
supported by multiple immutable official responses without falsely representing one URL or one timestamp as proof of
all facts. It covers evidence identity, field authority, source IDs, snapshot provenance, deterministic ordering,
cutoff eligibility, and the required persistence-migration policy.

It does not implement a provider normalizer, HorseMarkInfo parsing, RaceMarkTable parsing, HTTP collection,
fixtures, tests, SQLite DDL, or migration. Only this document and docs/LATEST_CODEX_REPORT.md may change.

## Frozen Prerequisites

The following approved conclusions are inputs to this design:

- c1a is globally schema version 2 and every current record uses his-v2:{record_kind}:{sha256}.
- Historical snapshot canonical payloads are version 2.
- The past-race time-difference field is exact Decimal reference_time_difference_seconds, never margin.
- HorseMarkInfo is the future official authority for race_name, race_class, and
  reference_time_difference_seconds.
- RaceMarkTable remains required for the historical result row, lineage-row confirmation, official historical odds,
  passing order, and corner evidence.
- SINGLE_RESPONSE_COMPLETE_SOURCE = NO, MULTI_RESPONSE_EVIDENCE_REQUIRED = YES, and
  C1A_PROVENANCE_EXTENSION_REQUIRED = YES.
- past_race_absence remains UNSUPPORTED. This phase does not change that decision.

## Investigation Findings

### Current contract gap

HistoricalInputSourceRecord currently owns exactly one canonical_source_url, available_at, and observed_at.
HistoricalInputProvenance mirrors that scalar metadata. That is truthful for a single response but not for a logical
past-race fact set requiring both a history/context response and a result response. Selecting one as a primary URL,
concatenating URLs, putting JSON in a URL field, or collapsing timestamps would make an audit claim that the model
cannot support.

The committed c1c builder maps one source record to one provenance item, and SQLite stores the same scalar shape.
The logical audit key must remain past_race/{race_entry_id}/{index}; creating two provenance rows with that same key
is not an acceptable workaround.

### Official NAR linkage re-check

The official NAR pages inspected for d1/d2/d3 establish the following provider evidence chain:

1. A verified target DebaTable row supplies external_horse_id = nar:horse:{k_lineageLoginCode}.
2. HorseMarkInfo for that lineage presents a historical race navigation link with provider-native race identity.
3. The corresponding RaceMarkTable URL identifies the historical race by its official date, venue code, and race
   number query family.
4. The selected RaceMarkTable row has a HorseMarkInfo anchor with the same lineage code.

The future normalizer must require every link. It rejects missing or duplicate matching lineage, historical-race
identity disagreement, horse-name matching, target-race substitution, and facts from another response or horse. This
chain proves the need for two factual response roles; it does not authorize parser implementation in d3b.

## Selected Architecture

Outcome A is selected: a uniform provider-neutral evidence tuple, global c1a schema version 3, nested snapshot
provenance, and normalized SQLite evidence children. A past-race-only secondary URL extension is rejected because it
leaves an ambiguous primary source. Splitting one fact set into provider fragments is rejected because c1c must
continue to receive one logical past_race record with one provider-record identity.

Layering is frozen:

1. A caller/capture boundary owns exact supplied bytes and explicit response observations.
2. A provider normalizer validates supplied pages and constructs provider-neutral evidence references plus facts.
3. One c1a source record owns one logical fact set and its ordered evidence tuple.
4. c1c creates one logical snapshot provenance item for that record and preserves every evidence reference.

No layer fetches HTTP, reads files, queries SQLite, uses the clock, or derives missing official evidence.

## Evidence Domain

The future shared module is:

    scripts/simulation/historical_input_evidence.py

Its only public type is a frozen/slotted HistoricalInputEvidenceReference:

    evidence_role: str
    canonical_source_url: str | None
    response_sha256: str
    available_at: datetime | None
    observed_at: datetime

source_system is not duplicated in a reference; it is already the exact parent c1a record source system. Evidence
contains no raw body, HTML, filesystem path, database ID, HTTP headers, request object, or mutable capture object.
The capture boundary retains bytes if replay storage is later authorized; d3b retains their immutable identity.

canonical_source_url remains provider-neutrally optional for ordinary evidence, preserving the committed valid case
where track has no URL. When present it uses the existing canonical HTTPS URL validation. A
past_race_absence evidence item still requires a non-null canonical URL. Every reference requires lowercase,
exactly 64-character ASCII hexadecimal response_sha256.

There is no evidence_id. The canonical identity tuple
(evidence_role, canonical_source_url, response_sha256) is sufficient, and a second hash namespace would add an
unneeded identity layer.

### Raw response digest and byte rule

response_sha256 is RAW_RESPONSE_SHA256: SHA-256 of the exact caller-supplied response-body bytes before decoding,
newline normalization, Unicode normalization, or HTML parsing. It is not a decoded-text, transport-header, URL, or
extracted-field digest. URL and digest are both identity inputs: identical bytes at different canonical URLs are
distinct evidence; changed irrelevant HTML changes the digest by design. This intentionally favors exact audit/replay
identity over semantic deduplication.

Raw bodies are not persisted by c1a or the snapshot repository in this phase. A later capture-retention boundary may
retain an artifact keyed by this digest; until then it proves identity comparison and tamper detection, not
self-contained body recovery.

### Evidence roles, cardinality, and field authority

The c1a v3 constructor canonicalizes evidence by ascending evidence_role and rejects duplicate roles, duplicate
(canonical_source_url, response_sha256) identities, unrecognized roles, missing roles, and extra roles. The exact
role sets are:

| record kind | required evidence roles |
| --- | --- |
| track | track |
| entry | entry |
| jockey | jockey |
| odds_win | odds_win |
| past_race | historical_race_context, historical_race_result |
| past_race_absence | past_race_absence_query |

The names express factual responsibility, not NAR page names. For the initial NAR past-race contract, authority is
fixed in the generic contract so an auditor need not reread provider code:

| role | authoritative facts |
| --- | --- |
| historical_race_context | race_name, race_class, reference_time_difference_seconds, plus history-side lineage/race-link evidence |
| historical_race_result | historical race identity, matching lineage row, race_date, place, distance_m, track, weather, track_condition, finish, race_time, weight, weight_diff, jockey, popularity, odds, passing_order, and fourth_corner_position |

provider_record_id identifies the one logical horse-result fact, never a response. Its frozen NAR semantic form is:

    nar:result:{YYYYMMDD}:{k_babaCode}:{k_raceNo}:horse:{k_lineageLoginCode}

The normalizer may construct that text only after each native component is independently validated. It excludes an
evidence role, target entry ID, source ID, URL alone, horse name, local IDs, hashes, and UUIDs.

## c1a v3 and Source-ID Policy

HistoricalInputSourceRecord becomes global schema version 3 for all six record kinds. Its scalar
canonical_source_url, available_at, and observed_at fields are removed and replaced by:

    evidence: tuple[HistoricalInputEvidenceReference, ...]

The canonical c1a payload contains schema_version 3, the existing logical identity and record_values, and ordered
evidence entries containing only evidence_role, canonical_source_url, and response_sha256. Evidence timestamps are
intentionally excluded from source_id.

Every new record therefore uses:

    his-v3:{record_kind}:{sha256}

This deliberate global public break changes every record ID, including track, entry, jockey, odds_win, and absence
records whose facts are otherwise unchanged. The d1 invariant remains: within v3, changing one entry lineage changes
only that entry source ID; other records retain their own v3 IDs.

| change | logical source_id |
| --- | --- |
| record values, provider ID, URL, role, or response digest changes | changes |
| same evidence/facts in a different supplied tuple order | unchanged |
| only observed_at and/or available_at changes | unchanged |
| same URL/facts but raw bytes change, including irrelevant markup | changes |

For every evidence observation, available_at <= observed_at when available. c1c must enforce every item separately:

    available_at <= observed_at <= captured_at <= information_cutoff <= scheduled_start_at

where available exists. A late evidence item fails the whole record; it is never dropped or aggregated away.

## Snapshot Provenance and Digest

HistoricalInputProvenance remains one item per logical audit key and retains input_type, audit_key, source (the
source system), source_id, race_entry_id, and past_race_index. It removes scalar timestamps and gains:

    evidence: tuple[HistoricalInputEvidenceReference, ...]

The builder copies the record evidence into that one provenance item. It never creates two audit keys or two
provenance rows for one logical past race. Evidence is role ordered.

Historical snapshot provenance is no longer structurally interchangeable with the generic runtime InputAuditEntry:
a scalar aggregate timestamp would hide per-response facts. InputAuditEntry and all existing simulation consumers
remain unchanged. A later adapter, if required, must be separately scoped and may not silently collapse evidence.

The snapshot canonical payload becomes version 3. Each provenance entry contains source, source ID, linkage, and an
evidence array including role, URL, raw-body digest, available time, and observed time. Provenance remains ordered by
audit_key; evidence remains ordered by role. content_sha256 therefore represents facts, immutable evidence identity,
and observation metadata. A timestamp-only evidence change preserves logical c1a source_id but changes snapshot
content_sha256.

HistoricalSourceIdentity.source_url remains provider-neutral: c1c selects the sole track record singleton evidence
URL exactly. A None track URL yields source_url None; no non-track URL is selected.

## SQLite and Migration Design

The logical historical_input_snapshot_provenance row remains keyed by (snapshot_id, audit_key) and retains logical
source/linkage columns, but no longer stores scalar observation timestamps. A new normalized child is required:

    historical_input_snapshot_provenance_evidence

It contains at least snapshot_id, audit_key, evidence_order, evidence_role, canonical_source_url, response_sha256,
available_at_utc, and observed_at_utc. It has a foreign key to the logical provenance row, unique role per
provenance item, unique response identity per provenance item, and canonical evidence order. Save/load validates URL,
SHA-256, timestamps, role/cardinality, ordering, and all foreign-key relations; corruption fails closed and cannot
fall back to an older snapshot.

This requires append-only v012 and runner registration. v012 first requires historical_input_snapshots to be empty.
If nonempty it raises deterministic RuntimeError before any schema mutation or migration registration. If empty it
replaces the scalar provenance layout with the logical parent plus evidence child layout. It must not reinterpret v2
scalar past-race provenance as a complete multi-response fact set. Even singleton candidates lack raw response digest,
so all v2 snapshot rows are fail-closed and none are migrated. Identity/linkage mappings may remain when the snapshot
store is empty.

## c1b, c1c, and Provider Boundaries

c1b mechanically constructs singleton evidence for track, entry, jockey, and odds records from exact supplied
DebaTable bytes, canonical target URL, and response observation. Its parsing semantics, public API, d1 lineage
behavior, and record payloads do not otherwise change. d1 selective source-ID isolation is re-pinned in his-v3.

c1c consumes evidence tuples, enforces cutoff eligibility per evidence item, uses the track singleton URL for source
identity, and maps one logical record to one nested provenance item. It has no provider-specific role branch and no
database or capture responsibility.

No HorseMarkInfo/RaceMarkTable normalizer is authorized. Future multi-response NAR normalization must enforce the
approved HorseMarkInfo-to-RaceMarkTable lineage/race identity chain, use the fixed two past-race roles, and fail
closed if evidence, digest, field, or cross-response identity is missing.

## Recommended Next Phase and Allowed Files

The contract is atomic across source records, snapshot provenance, c1b construction, c1c assembly, and persistence.
Splitting these representations would leave a non-working boundary. The recommended next implementation phase is:

Phase 4C-2d3b1i6c1d3b1 - Uniform historical evidence contract implementation

    scripts/simulation/historical_input_evidence.py
    scripts/simulation/historical_input_source_records.py
    scripts/simulation/historical_input_snapshots.py
    scripts/simulation/historical_input_snapshot_builder.py
    scripts/simulation/nar_historical_input_source.py
    scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py
    scripts/migrations/versions/v012_historical_input_evidence_schema.py
    scripts/migrations/runner.py
    tests/test_historical_input_source_records.py
    tests/test_historical_input_snapshots.py
    tests/test_historical_input_snapshot_builder.py
    tests/test_nar_historical_input_source.py
    tests/test_sqlite_historical_input_snapshot_repository.py
    tests/test_historical_input_snapshot_migration.py
    tests/test_simulation_migrations.py
    docs/CURRENT_PHASE.md
    docs/LATEST_CODEX_REPORT.md

No HorseMarkInfo/RaceMarkTable parser, fixture, provider, package-root export, legacy model, database file, log, or
README change is authorized. A later d3b2 PREPARE may design NAR multi-response normalization after this contract is
formally approved and integrated.

The future suite must prove: exact public surfaces; v3 payloads and his-v3 IDs for all kinds; canonical evidence
ordering; duplicate/missing/extra role rejection; strict SHA-256/URL validation; raw-byte hash semantics; timestamps
and cutoff eligibility per evidence; ID stability under timestamp-only change and change under URL/role/body/fact
change; c1b singleton evidence; d1 isolation in v3; one logical past-race provenance with two evidence refs;
snapshot v3 digest behavior; SQLite exact nested round trip; corrupt child rejection; no older-snapshot fallback;
v012 empty-store success and nonempty-store atomic failure; and the full suite.

## Blockers and Stop Condition

past_race_absence remains UNSUPPORTED. No normalizer may infer absence from an empty list, incomplete pagination, or
a missing response. HorseMarkInfo-to-RaceMarkTable linkage is proven at provider-native lineage/race-identity level,
but future parser work must still validate supplied bytes and all required result-field forms. Capture-body retention
is not implemented: this contract retains the exact raw-byte digest only.

Stop at DRAFT_FOR_REVIEW. Do not implement, merge, or begin d3b1 without separate ChatGPT approval.
