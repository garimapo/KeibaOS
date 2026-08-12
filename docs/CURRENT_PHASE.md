# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d4a` — provider-neutral request-aware evidence locator PREPARE.

Formal base: `41f2298820fe029bc06f024ff6da028f21ed5c7c`.

Approved d1d4 PREPARE: `d35e234adbb44ccbaf876b8dca8ff8b9c998c6d2`.

Review branch: `review/4c-2d3b1i6d1d4a-request-evidence-prepare`.

## Selected Provider-Neutral Model

`HistoricalInputEvidenceReference` gains one optional field:

```text
request_identity_sha256: str | None = None
```

It is a lowercase 64-character SHA-256 digest of provider-owned canonical request identity material. The neutral
layer validates only the optional digest shape. It neither receives nor interprets HTTP method, form fields, request
bodies, JRA `cname`, or any other provider request preimage. A non-null request identity requires a non-null actual
HTTPS `canonical_source_url`; that URL remains the actual request endpoint/resource, never a synthetic GET locator.

The provider owns canonical request material and its digest computation. For a future JRA accessO response, the
provider-owned preimage covers at least the actual POST method, the actual accessO endpoint, and the validated form
material. It must not contain observation timestamps. The neutral layer stores only the resulting fingerprint.

Model A (one optional fingerprint) is selected. A generic nested method/request object would expose unneeded request
structure; a capture/evidence ID can embed observed time and would couple source identity to archival topology; and a
synthetic locator URL would falsely describe an HTTP request as GET. None of those alternatives improves the neutral
identity boundary.

## Request-Aware Identity and Compatibility

The underlying-response identity is exactly:

```text
(canonical_source_url, request_identity_sha256, response_sha256)
```

`None` is the legacy URL-only request identity. Same-response reuse across roles is permitted only when this complete
triple is equal and both `available_at` and `observed_at` are equal. Equal endpoint and raw bytes with different
request identities are distinct responses and never collapse. Timestamp coherence and causal eligibility remain
unchanged.

Legacy GET producers construct `request_identity_sha256=None`; they require no source changes. In canonical c1a and
snapshot evidence payloads, the new key is omitted when its value is `None`. Therefore every existing valid source
payload and `his-v4` source ID, and every existing snapshot payload and digest, remains byte-for-byte unchanged. For
new request-aware evidence, the key is included and changes both the source ID and snapshot digest. Available and
observed timestamps remain excluded from the c1a source ID and included in snapshot provenance/digest.

Schema versions remain `4`: this is an optional backward-compatible payload extension, not a reinterpretation of an
existing value. Existing two- and three-role past-race contracts are unchanged.

## Persistence and Archive Lookup

Add global migration v014:

```text
VERSION = 14
NAME = v014_historical_input_request_identity_schema
```

It uses one additive, non-destructive SQLite operation on
`historical_input_snapshot_provenance_evidence`:

```sql
ALTER TABLE historical_input_snapshot_provenance_evidence
ADD COLUMN request_identity_sha256 TEXT NULL CHECK (
  request_identity_sha256 IS NULL OR (
    typeof(request_identity_sha256) = 'text'
    AND length(request_identity_sha256) = 64
    AND request_identity_sha256 NOT GLOB '*[^0-9a-f]*'
  )
)
```

v014 applies to empty and nonempty snapshot stores. It preserves every pre-v014 row with a NULL field and does not
rebuild, rewrite, reinterpret, or delete snapshots. The global migration final version becomes `14`. Repository write
and reconstruction paths must persist/read the nullable field; malformed stored non-null values, orphan evidence, or
an invalid reconstructed reference fail closed with `RepositoryDataIntegrityError`. No fallback or repair is allowed.

A future provider archive resolves request-aware evidence exactly by canonical endpoint URL, request identity SHA,
raw response SHA, and observed timestamp. Legacy GET lookup remains URL, raw response SHA, and observed timestamp.
`available_at` is not archive-capture identity.

## Builder and Provider Scope

The existing builder already forwards complete evidence and validates every evidence timestamp. It requires no
production change. Existing NAR producers and existing JRA accessS/accessU GET producers remain URL-only and require
no production changes. The later JRA accessO capture domain owns its POST locator, raw request details, request
fingerprint derivation, archive v002 lookup, and live transport; it must not place `cname` in the neutral domain.

```text
REQUEST_AWARE_EVIDENCE_READY = YES
SELECTED_MODEL = OPTIONAL_REQUEST_IDENTITY_SHA256
REQUEST_IDENTITY_FIELD = HistoricalInputEvidenceReference.request_identity_sha256
LEGACY_GET_REQUEST_IDENTITY = None
SOURCE_SCHEMA_VERSION_BUMP_REQUIRED = NO
SNAPSHOT_SCHEMA_VERSION_BUMP_REQUIRED = NO
GLOBAL_MIGRATION_REQUIRED = YES
GLOBAL_MIGRATION_FINAL_VERSION = 14
SNAPSHOT_REPOSITORY_CHANGE_REQUIRED = YES
BUILDER_PRODUCTION_CHANGE_REQUIRED = NO
EXISTING_SOURCE_IDS_PRESERVED = YES
EXISTING_SNAPSHOT_HASHES_PRESERVED = YES
REQUEST_IDENTITY_CHANGES_SOURCE_ID = YES
REQUEST_IDENTITY_CHANGES_SNAPSHOT_DIGEST = YES
NAR_PRODUCTION_CHANGE_REQUIRED = NO
JRA_EXISTING_GET_CHANGE_REQUIRED = NO
```

## Next Implementation Phase

Recommended next phase: `4C-2d3b1i6d1d4a1` — provider-neutral request-aware evidence implementation. Its exact
allowed files should be:

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

It must add explicit legacy source/snapshot hash regressions, request-aware source-ID/digest regressions,
same-response coherence tests that include the request fingerprint, nullable v014 preservation on nonempty stores,
repository round trip/corruption tests, and global migration order `(8, 9, 10, 11, 12, 13, 14)`. It must not begin
JRA accessO capture, JRA archive v002, live POST transport, a JRA normalizer, an NAR/JRA bridge, or acquisition.

## Allowed Files and Stop Condition

This PREPARE changes only:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Stop for independent design review. Do not implement production code, tests, migrations, or schemas.
