# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d4a1` — request-aware historical evidence implementation.

Formal base: `41f2298820fe029bc06f024ff6da028f21ed5c7c`.

Approved PREPARE: `ff3010b77991e666e7325562a920a22e3382bd84`.

Implementation review branch: `review/4c-2d3b1i6d1d4a1-request-evidence-implementation`.

## Implemented Contract

`HistoricalInputEvidenceReference` now has one final optional field,
`request_identity_sha256: str | None = None`. It preserves the existing five positional fields and construction
behavior. `None` remains the legacy URL-only request identity. A non-null value must be exactly lowercase
64-character SHA-256 hex and requires a non-null canonical HTTPS endpoint URL.

The provider-neutral layer stores and validates only that fingerprint. It does not know an HTTP method, form field,
request body, JRA `cname`, or any provider-specific request preimage. The provider owns canonical request material
and fingerprint calculation. Same-response timestamp coherence now keys exactly on:

```text
(canonical_source_url, request_identity_sha256, response_sha256)
```

Different request fingerprints are distinct even when endpoint and response bytes are equal. Equal full identities
continue to require equal available/observed timestamps. Causality remains the unchanged builder responsibility.

Source schema stays `4`; source IDs stay `his-v4`. Snapshot schema stays `4`. Legacy evidence omits
`request_identity_sha256` entirely from source and snapshot canonical payloads, preserving frozen formal-base payloads,
source IDs, and content hashes byte-for-byte. Request-aware evidence serializes the non-null fingerprint, changing
the corresponding source ID and snapshot digest. Timestamps remain excluded from c1a source IDs and included in
snapshot provenance/digests.

## Persistence

Global v014, `v014_historical_input_request_identity_schema`, adds only nullable strict-lowercase-SHA-256
`request_identity_sha256` to `historical_input_snapshot_provenance_evidence`. It is additive and transaction-neutral,
works for empty and nonempty v013 stores, preserves all existing rows as NULL, and performs no rebuild, rewrite,
repair, or deletion. The global migration order is exactly `(8, 9, 10, 11, 12, 13, 14)`.

The SQLite snapshot repository writes and reconstructs the nullable field. Legacy NULL and request-aware non-null
values round trip with the snapshot content SHA unchanged. Malformed stored non-null values fail closed as
`RepositoryDataIntegrityError`; no defaulting or fallback occurs.

```text
SOURCE_SCHEMA_VERSION = 4 UNCHANGED
SOURCE_NAMESPACE = his-v4 UNCHANGED
SNAPSHOT_SCHEMA_VERSION = 4 UNCHANGED
GLOBAL_MIGRATION_FINAL_VERSION = 14
BUILDER_PRODUCTION_CHANGED = NO
NAR_PRODUCTION_CHANGED = NO
JRA_EXISTING_GET_PRODUCTION_CHANGED = NO
JRA_ACCESSO_CAPTURE_STARTED = NO
```

## Verification and Stop Condition

Focused source/snapshot/builder/repository/migration verification passed 101 tests, scope-extension migration
regressions passed 6 tests, current NAR historical-source plus JRA capture/live regressions passed 47 tests, and the
complete migration-related suite passed 33 tests. The fresh full suite passed 2561 tests under Python 3.14.5 and
pytest 8.3.5. The approved scope extension changed only three stale version-13 assertions to recognize v014; no
production behavior changed after it. Do not implement JRA accessO, JRA archive v002, live POST transport, a JRA
normalizer, an NAR/JRA bridge, acquisition, or any next phase.

## Allowed Files

```text
scripts/simulation/historical_input_evidence.py
scripts/simulation/historical_input_source_records.py
scripts/simulation/historical_input_snapshots.py
scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py
scripts/migrations/runner.py
scripts/migrations/versions/v014_historical_input_request_identity_schema.py
tests/test_historical_input_source_records.py
tests/test_historical_input_snapshots.py
tests/test_historical_input_snapshot_builder.py
tests/test_sqlite_historical_input_snapshot_repository.py
tests/test_historical_input_snapshot_migration.py
tests/test_simulation_migrations.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```
