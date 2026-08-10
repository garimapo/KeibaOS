# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6c1d3b2b` — Trusted NAR official-response capture/archive preparation.

Formal base: `4af5a7ba4f18769f365ac2c934bcfd0ffcf38818 feat: normalize NAR historical past races`.

Formal branch: `feature/ver0.8-simulator`.

Review branch: `review/4c-2d3b1i6c1d3b2b-prepare`.

This PREPARE changes only this file and `docs/LATEST_CODEX_REPORT.md`. It implements no capture/archive, database, migration, repository, HTTP request, fixture, test, or orchestration.

## Trust Model and Causal Boundary

`TRUST_MODEL = OPERATIONALLY_TRUSTED_LOCAL_CAPTURE`. KeibaOS makes the HTTPS request, timestamps only after receiving complete parser-input bytes, retains those bytes, and verifies SHA-256 on save and retrieval. `CRYPTOGRAPHIC_EXTERNAL_TIMESTAMP_AUTHORITY = NOT_PROVIDED`; host clock plus SQLite is not proof to a hostile third party.

`RETROACTIVE_LIVE_SITE_BACKFILL = IMPOSSIBLE_TO_TRUST`. A current page cannot become eligible for an old cutoff by old `observed_at`, race/result/publication date, HTTP Date, file/Git/database time, or claims of equality with old content. Before collection, `NAR_LIVE_SITE_ONLY = NO_CAUSALLY_ELIGIBLE_CAPTURE` is expected no-data. HorseMarkInfo is mutable. Third-party archive imports, manual HTML, logs, Wayback, and current live content are outside trusted `nar_official` capture.

No c1a/c1b/d3b2a/c1c changes: `available_at = None`; no c1a v4, source-ID namespace or snapshot schema change, capture ID in evidence, provider-record parsing, or evidence backfill. The logical link is exactly:

```text
CROSS_DATABASE_LINKAGE = EXISTING_EVIDENCE_IDENTITY_TUPLE
EVIDENCE_REPLAY_LOOKUP_KEY = canonical_source_url + response_sha256 + observed_at
```

Persist valid received bytes before later normalization. An unused capture after normalizer failure is safe; capture persistence failure means no trusted operational evidence. Archive miss is `NAROfficialResponseCaptureMissingError`, with no network/current/adjacent fallback. Stored corruption is `RepositoryDataIntegrityError`, with no repair or alternate selection. Builder retains final `observed_at <= captured_at <= information_cutoff` ownership.

## Closed URL/Page Vocabulary

| kind | HTTPS host(s) | path | exact query keys |
| --- | --- | --- | --- |
| `deba_table` | `www.keiba.go.jp` | `/KeibaWeb/TodayRaceInfo/DebaTable` | `k_babaCode`, `k_raceDate`, `k_raceNo` |
| `horse_mark_info` | `www.keiba.go.jp`, `www2.keiba.go.jp` | `/KeibaWeb/DataRoom/HorseMarkInfo` | `k_lineageLoginCode` |
| `race_mark_table` | `www.keiba.go.jp` | `/KeibaWeb/TodayRaceInfo/RaceMarkTable` | `k_babaCode`, `k_raceDate`, `k_raceNo` |

Page kind is URL-derived before network access, never caller text. Reject non-HTTPS, foreign/IP host, credentials, fragment, controls/whitespace, port other than absent/443, unknown path, malformed percent escape, `+` ambiguity, duplicate/blank/unknown keys, invalid date, and noncanonical positive tokens. Canonical race query order is `k_babaCode`, escaped `k_raceDate=YYYY%2FMM%2FDD`, `k_raceNo`; HorseMark has only lineage. Accepted HorseMark host is preserved; no www/www2 rewrite. Capture owns independent validation and does not import private normalizer helpers.

The 2026-08-10 read-only probe saw direct `www` representatives return 200, `text/html; charset=UTF-8`, no Content-Encoding, and 297,718 / 83,949 / 96,614 byte bodies. Observed `www2` HorseMarkInfo 301 is temporal only; tests treat every 3xx under disabled redirects as transport failure/no capture. Legacy NARProvider `response.text`, apparent encoding, and logs are `NOT_TRUSTED_EVIDENCE_ARCHIVE`.

## Exact d3b2b1 Public and Error Surface

Only these definitions are module-defined public names in `scripts/simulation/nar_official_response_capture.py`:

```python
NAROfficialPageKind
NAROfficialResponseCapture
NAROfficialResponseCaptureArchive
NAROfficialResponseCaptureError
NAROfficialResponseCaptureValidationError
NAROfficialResponseCaptureUnsupportedError
NAROfficialResponseCaptureMissingError
canonicalize_nar_official_capture_url
```

No package-root export or capture-specific repository conflict/integrity error. `NAROfficialResponseCaptureArchive` exactly provides:

```python
def save_capture(*, capture: NAROfficialResponseCapture) -> None: ...
def load_capture(*, capture_id: str) -> NAROfficialResponseCapture | None: ...
def load_supplied_response_for_evidence(*, canonical_source_url: str, response_sha256: str, observed_at: datetime) -> NarSuppliedOfficialResponse: ...
```

Reuse repository errors: invalid caller input is `RepositoryValidationError`; same immutable identity/different content is `RepositoryConflictError`; impossible metadata, FK/storage failure, persisted Content-Length mismatch, or body SHA mismatch is `RepositoryDataIntegrityError`; exact non-archived lookup is the capture-domain missing error.

`NAROfficialResponseCapture` is frozen/slotted, schema version 1 (not init), and has deterministic `capture_id`, kind, canonical URL, body SHA, exact `bytes` body, exact `charset="utf-8"`, requested/observed/stored aware datetimes, HTTP status, and optional Content-Type/Encoding/Date/ETag/Last-Modified/Length. `capture_id` is `nar-capture-v1:` plus lowercase SHA-256 of canonical compact sorted-key UTF-8 JSON of schema version, kind, canonical URL, body SHA, and canonical UTC observed time. Same URL/body at another observed time is a distinct observation; same ID is idempotent only with identical immutable fields/body, otherwise conflict.

`response_body = EXACT_PARSER_INPUT_ENTITY_BYTES`: exact saved bytes later passed unchanged to `NarSuppliedOfficialResponse.response_body`; hash precedes decode/NFC/HTML. Strict UTF-8 decode is only compatibility validation, never persisted/re-encoded. No text round-trip, `response.text`, apparent encoding, or fallback. Only absent/`identity` Content-Encoding is accepted. Reconstruction reuses `NarSuppliedOfficialResponse`.

## Time, Transport, and d3b2b2 API

`SYSTEM_CLOCK_CORRECTNESS = OPERATIONAL_PRECONDITION`. `requested_at` is immediately before request start; `observed_at` immediately after complete entity receipt before parsing; `stored_at` immediately before atomic archive save/finalization. Save returns after persistence completed after `stored_at`, not an exact SQLite durability instant. `stored_at` is audit metadata, not observed/available/capture/evidence identity/cutoff.

d3b2b2 public definitions are exactly `NAROfficialLiveResponseCaptureService`, `NAROfficialResponseCaptureTransportError`, and `build_nar_official_live_response_capture_service`.

```python
class NAROfficialLiveResponseCaptureService:
    def __init__(self, *, archive: NAROfficialResponseCaptureArchive, transport: _NAROfficialHTTPTransport, utc_clock: Callable[[], datetime]) -> None: ...
    def capture(self, *, response_url: str) -> NAROfficialResponseCapture: ...

def build_nar_official_live_response_capture_service(*, archive: NAROfficialResponseCaptureArchive) -> NAROfficialLiveResponseCaptureService: ...
```

The public factory owns private requests transport and real aware UTC clock. `D3B2C_PRIVATE_TRANSPORT_IMPORT = FORBIDDEN` and `D3B2C_HTTP_IMPLEMENTATION = FORBIDDEN`; d3b2c uses only the public factory/service. HTTPS GET uses TLS verification, disabled redirects, HTTP 200 only, 10/30-second connect/read timeouts, 4 MiB complete-body maximum, static identifying UA, and no retry. 3xx/4xx/5xx, TLS/network/timeout, partial/oversize, and Content-Length mismatch fail before persistence. HTTP Date is never observed/available time; retained headers are auxiliary and controls are rejected. `PERSIST_BEFORE_NORMALIZATION = YES`.

## Separate Capture Database and Dedicated Migration

`DATABASE_LOCATION = SEPARATE_NAR_CAPTURE_DATABASE`.

The illustrative collection model (one DebaTable per target race, ten HorseMarkInfo captures per target race, one RaceMarkTable body per race before repeat/extra coverage) projects:

| target races/year | DebaTable | HorseMarkInfo | RaceMarkTable | total bodies |
| --- | ---: | ---: | ---: | ---: |
| 10,000 | 2.77 GiB | 7.82 GiB | 0.90 GiB | about 11.5 GiB/year |
| 15,000 | 4.16 GiB | 11.73 GiB | 1.35 GiB | about 17.2 GiB/year |

These exclude rows/indexes, WAL, backups, changed bodies defeating dedup, and added history. Blob/WAL/checkpoint/backup/vacuum and retention lifecycle materially differ from the main simulation DB. Separation confines capture failure/maintenance and prevents archive growth from burdening main backup/vacuum; main failure likewise cannot corrupt the archive. `AUTOMATIC_CAPTURE_RETENTION_DELETE = FORBIDDEN`.

`CAPTURE_DATABASE_PATH = COMPOSITION_OWNED`. d3b2c later owns a distinct `capture_database_path`, separate from existing main `database_path`; d3b2b1 repository and d3b2b2 archive/service take neither path nor connection selection. Repository receives an injected capture SQLite connection, knows no main/simulation path/tables, and must never `ATTACH`. `CROSS_DATABASE_ATOMIC_TRANSACTION = NOT_REQUIRED`: capture precedes normalization and the evidence tuple supplies linkage without cross-DB FKs/distributed transaction.

Backups are the pair `main KeibaOS SQLite db` and `NAR trusted capture SQLite db`, recommended main then capture. Backup skew has no web fallback; restoration uses available independent DBs and exact archive lookup fail-closes.

`GLOBAL_MIGRATION_REQUIRED = NO`. No main/global `v013`; do not modify `scripts/migrations/runner.py`, add `scripts/migrations/versions/v013_*`, or change global migration order. Formal global sequence remains `8, 9, 10, 11, 12`. `GLOBAL_MIGRATION_REGISTRY_SCAN = COMPLETE`; these existing expectation tests are unchanged:

```text
tests/test_historical_input_snapshot_migration.py
tests/test_simulation_bet_plan_migration.py
tests/test_simulation_migrations.py
tests/test_sqlite_persisted_simulation_application.py
```

`GLOBAL_MIGRATION_REGISTRY_AFFECTED_TESTS = NONE`.

`CAPTURE_SCHEMA_MIGRATION_REQUIRED = YES`; dedicated version 1 is exactly `v001_nar_official_response_capture_schema` in:

```text
scripts/simulation/nar_official_response_capture_migration.py
scripts/simulation/nar_official_response_capture_migration_runner.py
```

The migration module owns `VERSION`, `NAME`, and transaction-neutral `apply(connection)` (no begin/commit/rollback). Runner operates on capture DB only: rejects active transaction, enables/verifies FKs, validates registry, rejects duplicate/malformed/unknown-future/name-mismatch, creates registry if absent, applies ascending pending versions, and performs `BEGIN IMMEDIATE` plus registry insertion atomically. It rolls back failure and leaves transaction-neutral. It must not import/invoke `scripts.migrations.runner.MIGRATIONS` or create/inspect global simulation tables. Dedicated registry is exactly:

```sql
CREATE TABLE nar_official_response_capture_schema_migrations (
  version INTEGER PRIMARY KEY CHECK (typeof(version) = 'integer' AND version > 0),
  name TEXT NOT NULL CHECK (typeof(name) = 'text' AND name <> '')
) WITHOUT ROWID;
```

Dedicated v001 creates only the body table, capture table, and named unique index. UTC text is 32-character `YYYY-MM-DDTHH:MM:SS.ffffff+00:00`; lexical order is chronological. Exact body/capture DDL remains:

```sql
CREATE TABLE nar_official_response_bodies (
    response_sha256 TEXT PRIMARY KEY CHECK (typeof(response_sha256) = 'text' AND length(response_sha256) = 64 AND response_sha256 NOT GLOB '*[^0-9a-f]*'),
    response_body BLOB NOT NULL CHECK (typeof(response_body) = 'blob'),
    byte_length INTEGER NOT NULL CHECK (typeof(byte_length) = 'integer' AND byte_length > 0 AND byte_length = length(response_body))
) WITHOUT ROWID;

CREATE TABLE nar_official_response_captures (
    capture_id TEXT PRIMARY KEY CHECK (typeof(capture_id) = 'text' AND length(capture_id) = 79 AND substr(capture_id, 1, 15) = 'nar-capture-v1:' AND substr(capture_id, 16) NOT GLOB '*[^0-9a-f]*'),
    schema_version INTEGER NOT NULL CHECK (typeof(schema_version) = 'integer' AND schema_version = 1),
    page_kind TEXT NOT NULL CHECK (page_kind IN ('deba_table', 'horse_mark_info', 'race_mark_table')),
    canonical_source_url TEXT NOT NULL CHECK (typeof(canonical_source_url) = 'text' AND canonical_source_url <> ''),
    response_sha256 TEXT NOT NULL CHECK (typeof(response_sha256) = 'text' AND length(response_sha256) = 64 AND response_sha256 NOT GLOB '*[^0-9a-f]*'),
    charset TEXT NOT NULL CHECK (typeof(charset) = 'text' AND charset = 'utf-8'),
    requested_at_utc TEXT NOT NULL CHECK (typeof(requested_at_utc) = 'text' AND length(requested_at_utc) = 32 AND requested_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'),
    observed_at_utc TEXT NOT NULL CHECK (typeof(observed_at_utc) = 'text' AND length(observed_at_utc) = 32 AND observed_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'),
    stored_at_utc TEXT NOT NULL CHECK (typeof(stored_at_utc) = 'text' AND length(stored_at_utc) = 32 AND stored_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'),
    http_status INTEGER NOT NULL CHECK (typeof(http_status) = 'integer' AND http_status = 200),
    content_type TEXT NULL CHECK (content_type IS NULL OR typeof(content_type) = 'text'),
    content_encoding TEXT NULL CHECK (content_encoding IS NULL OR content_encoding = 'identity'),
    http_date TEXT NULL CHECK (http_date IS NULL OR typeof(http_date) = 'text'),
    etag TEXT NULL CHECK (etag IS NULL OR typeof(etag) = 'text'),
    last_modified TEXT NULL CHECK (last_modified IS NULL OR typeof(last_modified) = 'text'),
    content_length INTEGER NULL CHECK (content_length IS NULL OR (typeof(content_length) = 'integer' AND content_length >= 0)),
    CHECK (requested_at_utc <= observed_at_utc AND observed_at_utc <= stored_at_utc),
    FOREIGN KEY (response_sha256) REFERENCES nar_official_response_bodies (response_sha256) ON UPDATE RESTRICT ON DELETE RESTRICT
) WITHOUT ROWID;

CREATE UNIQUE INDEX ux_nar_official_response_captures_evidence
    ON nar_official_response_captures (canonical_source_url, response_sha256, observed_at_utc);
```

`EVIDENCE_LOOKUP_INDEX_COUNT = ONE`; the named UNIQUE index is constraint and lookup. Duplicate ordinary index is forbidden. Repository recomputes SHA-256 and validates URL/timestamps; SQL does not replace domain/cryptographic verification. Body dedup/capture insertion are one repository transaction; no capture references a missing body. Existing evidence without body remains `MISSING_CAPTURE`.

## Future Scope and Stop Condition

d3b2b1 future allowed files are exactly:

```text
scripts/simulation/nar_official_response_capture.py
scripts/simulation/repositories/sqlite_nar_official_response_capture_repository.py
scripts/simulation/nar_official_response_capture_migration.py
scripts/simulation/nar_official_response_capture_migration_runner.py
tests/test_nar_official_response_capture.py
tests/test_sqlite_nar_official_response_capture_repository.py
tests/test_nar_official_response_capture_migration.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

d3b2b2 future allowed files are exactly:

```text
scripts/simulation/nar_official_response_live_capture.py
tests/test_nar_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

d3b2c later owns composition, distinct `capture_database_path`, discovery, scheduling, multi-race collection, and cutoff-eligible selection. It may not implement private transport/HTTP, repair backup skew through the web, or introduce automatic retention deletion. Pagination/orchestration and `past_race_absence` remain out of scope.

Stop for independent architecture re-review. Do not implement d3b2b1/b2/c, capture storage, dedicated migration, global migration, live capture, or acquisition.
