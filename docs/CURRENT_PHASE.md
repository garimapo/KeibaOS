# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d3` — historical final-odds evidence-role implementation.

Formal base: `0135cee4ad8e578e6bd20940b16198a576172c04`.

Approved PREPARE: `0593b015be355ed42c61f25b0c2ee4d8132dc27a`.

Implementation review branch: `review/4c-2d3b1i6d1d3-evidence-implementation`.

## Implemented Provider-Neutral Evidence Contract

`historical_race_final_odds` is the immutable official response that directly supplies a historical past-race final
odds fact. It is not target-race odds, popularity, payout, implied probability, or a model value.

The only accepted `past_race` evidence role tuples are lexically canonicalized to exactly:

```text
historical_race_context + historical_race_result
historical_race_context + historical_race_final_odds + historical_race_result
```

All non-past-race role rules remain unchanged. Partial, duplicate, unknown, and over-complete tuples fail closed.
Same underlying response reuse remains valid only when the URL/SHA pair has exactly equal available and observed
timestamps across every reused role.

`HistoricalInputSourceRecord.schema_version` remains `4`, its namespace remains `his-v4`, and the canonical source
payload format is unchanged. Existing two-role NAR records retain their exact source payload and source ID. Adding a
final-odds role changes the new record's source ID; changing only timestamps does not.

`HistoricalInputProvenance` accepts the identical two-or-three role contract. Snapshot schema version remains `4`.
Existing two-role snapshots retain their exact payload and digest. A final-odds reference is persisted in the nested
provenance evidence list, including its timestamps, and therefore changes the new snapshot digest.

The unchanged builder already transfers every evidence reference and independently rejects any causally late final
odds observation. It remains the sole causality owner. Existing source-set conflict behavior rejects competing past
records with the same official result identity and different final-odds evidence; it never selects a latest record.

```text
SOURCE_SCHEMA_VERSION = 4 UNCHANGED
SNAPSHOT_SCHEMA_VERSION = 4 UNCHANGED
BUILDER_PRODUCTION_CHANGED = NO
EVIDENCE_DOMAIN_CHANGED = NO
REPOSITORIES_CHANGED = NO
MIGRATIONS_CHANGED = NO
NAR_PRODUCTION_CHANGED = NO
```

## Allowed Files

```text
scripts/simulation/historical_input_source_records.py
scripts/simulation/historical_input_snapshots.py
tests/test_historical_input_source_records.py
tests/test_historical_input_snapshots.py
tests/test_historical_input_snapshot_builder.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification and Stop Condition

Regression coverage freezes the formal-base two-role source ID, source payload, and snapshot digest; validates both
approved tuples and every rejected role shape; confirms timestamp-only source-ID invariance, same-response timestamp
coherence, source-set conflicts, builder propagation, and final-odds causality rejection. Stop for independent
implementation review. Do not integrate formal, start accessO capture, or start a JRA historical normalizer.
