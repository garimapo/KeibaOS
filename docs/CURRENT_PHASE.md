# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase 4C-2d3b1i6c1d3b2b — Trusted NAR official-response capture/archive preparation.

Formal base: `4af5a7ba4f18769f365ac2c934bcfd0ffcf38818 feat: normalize NAR historical past races`.

Formal branch: `feature/ver0.8-simulator`.

Review branch: `review/4c-2d3b1i6c1d3b2b-prepare`.

PREPARE changes only this file and `docs/LATEST_CODEX_REPORT.md`. It implements no capture/archive, migration,
repository, HTTP request, fixture, test, or orchestration.

## Trust Model and Causal Boundary

`TRUST_MODEL = OPERATIONALLY_TRUSTED_LOCAL_CAPTURE`. KeibaOS makes the HTTPS request, timestamps only after receiving
the complete parser-input bytes, retains those exact bytes, and verifies SHA-256 on save and retrieval. Its archive API
is application-level append-only. `CRYPTOGRAPHIC_EXTERNAL_TIMESTAMP_AUTHORITY = NOT_PROVIDED`: a host clock plus
SQLite does not prove to a hostile third party that time was never forged. External attestation is a separate phase.

`RETROACTIVE_LIVE_SITE_BACKFILL = IMPOSSIBLE_TO_TRUST`. A current page cannot be made eligible for an old cutoff using
an old `observed_at`, race/result date, provider publication date, HTTP Date, file/Git/database time, or a claim that
the current page equals an old page. Before trusted collection, `NAR_LIVE_SITE_ONLY = NO_CAUSALLY_ELIGIBLE_CAPTURE` is
expected no-data. HorseMarkInfo history is mutable; RaceMarkTable has no immutability bypass. Third-party archive
imports, manual HTML, logs, Wayback, and current live content are out of scope for trusted `nar_official` capture.

No c1a/c1b/d3b2a/c1c snapshot contract changes. `available_at = None` stays unchanged. No c1a v4, source-ID namespace
change, snapshot schema change, capture ID in evidence, provider-record parsing, or evidence-row backfill is allowed.
The archive joins operationally through:

```text
EVIDENCE_REPLAY_LOOKUP_KEY = canonical_source_url + response_sha256 + observed_at
```

Miss means `NAROfficialResponseCaptureMissingError`: no network/current/adjacent-capture fallback. Stored corruption
means `RepositoryDataIntegrityError`: no automatic repair or alternate capture selection. The existing builder remains
the final `observed_at <= captured_at <= information_cutoff` enforcer.

## Closed URL/Page Vocabulary

Initial capture supports exactly these URL-derived kinds:

| kind | HTTPS host(s) | path | exact query keys |
| --- | --- | --- | --- |
| `deba_table` | `www.keiba.go.jp` | `/KeibaWeb/TodayRaceInfo/DebaTable` | `k_babaCode`, `k_raceDate`, `k_raceNo` |
| `horse_mark_info` | `www.keiba.go.jp`, `www2.keiba.go.jp` | `/KeibaWeb/DataRoom/HorseMarkInfo` | `k_lineageLoginCode` |
| `race_mark_table` | `www.keiba.go.jp` | `/KeibaWeb/TodayRaceInfo/RaceMarkTable` | `k_babaCode`, `k_raceDate`, `k_raceNo` |

Page kind is derived from strict pre-network URL validation, never independent caller text. Reject non-HTTPS, foreign
or IP hosts, credentials, fragments, controls/whitespace, ports except absent/443, unknown paths, malformed percent
escapes, `+` ambiguity, duplicate/blank/unknown query keys, invalid dates, and noncanonical positive tokens. Race URL
canonical spelling orders `k_babaCode`, escaped `k_raceDate=YYYY%2FMM%2FDD`, then `k_raceNo`; HorseMark has only its
lineage key. The accepted HorseMark host is preserved, never silently rewritten. Capture owns an independent validator
and cross-contract tests; it does not import private normalizer helpers.

The 2026-08-10 read-only probe found direct `www` DebaTable/HorseMarkInfo/RaceMarkTable representatives returned 200,
no redirect, `text/html; charset=UTF-8`, no Content-Encoding, and 297,718 / 83,949 / 96,614 bytes respectively. The
observed `www2` HorseMarkInfo 301 is temporal transport evidence only, not a permanent domain invariant. Unit tests
pin any 3xx as transport failure/no capture, not a lasting public-site behavior.

`LEGACY_NAR_PROVIDER_TEXT_PATH = NOT_TRUSTED_EVIDENCE_ARCHIVE`: the legacy `response.text`, apparent-encoding, and
logs path cannot prove byte identity. Logs are never evidence storage.

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

No package-root export, capture-specific repository-integrity error, or capture-specific conflict error exists.
`NAROfficialResponseCaptureArchive` exactly provides:

```python
def save_capture(*, capture: NAROfficialResponseCapture) -> None: ...
def load_capture(*, capture_id: str) -> NAROfficialResponseCapture | None: ...
def load_supplied_response_for_evidence(
    *, canonical_source_url: str, response_sha256: str, observed_at: datetime,
) -> NarSuppliedOfficialResponse: ...
```

Repository errors are reused exactly: invalid caller input is `RepositoryValidationError`; a same immutable identity
with different stored content is `RepositoryConflictError`; impossible stored metadata, FK/storage failure, persisted
Content-Length mismatch, or body SHA mismatch is `RepositoryDataIntegrityError`; an exact non-archived lookup is
`NAROfficialResponseCaptureMissingError`.

`NAROfficialResponseCapture` is frozen/slotted and has schema version 1 (not init), deterministic `capture_id`,
page kind, canonical URL, response SHA, exact `bytes` body, exact `charset="utf-8"`, requested/observed/stored aware
datetimes, HTTP status, and optional Content-Type, Content-Encoding, Date, ETag, Last-Modified, Content-Length.
`capture_id` is `nar-capture-v1:` plus lowercase SHA-256 of canonical compact sorted-key UTF-8 JSON containing schema
version, kind, canonical URL, body SHA, and canonical UTC observed time. Same URL/body at a different observed time is
a distinct observation. Same ID is idempotent only if every immutable field/body is identical; otherwise conflict.

`response_body` is `EXACT_PARSER_INPUT_ENTITY_BYTES`: exact bytes saved and later passed unchanged to
`NarSuppliedOfficialResponse.response_body`. Hash is before decoding/NFC/HTML processing. It is not packet-level wire
capture. A strict UTF-8 validation decode is only a compatibility check and is never persisted/re-encoded. No text
round trip, `response.text`, apparent encoding, or replacement/fallback decode. Only absent/`identity`
Content-Encoding is accepted. `to_supplied_official_response()` and exact archive reconstruction reuse the existing
`NarSuppliedOfficialResponse`, not a duplicate type.

## Time, Transport, and d3b2b2 API

`SYSTEM_CLOCK_CORRECTNESS = OPERATIONAL_PRECONDITION`. `requested_at` is sampled immediately before request start;
`observed_at` immediately after the complete entity bytes are received and before parsing; `stored_at` is the trusted
live-capture clock sample immediately before invoking atomic archive save/finalization. A successful save returns only
after persistence completed after `stored_at`; it does not prove the exact SQLite durability instant. `stored_at` is
audit metadata, not observed/available/capture/evidence identity/cutoff.

d3b2b2's exact module-defined public API is:

```python
NAROfficialLiveResponseCaptureService
NAROfficialResponseCaptureTransportError
build_nar_official_live_response_capture_service
```

```python
class NAROfficialLiveResponseCaptureService:
    def __init__(self, *, archive: NAROfficialResponseCaptureArchive,
                 transport: _NAROfficialHTTPTransport,
                 utc_clock: Callable[[], datetime]) -> None: ...
    def capture(self, *, response_url: str) -> NAROfficialResponseCapture: ...

def build_nar_official_live_response_capture_service(
    *, archive: NAROfficialResponseCaptureArchive,
) -> NAROfficialLiveResponseCaptureService: ...
```

The public factory owns private requests transport and real aware UTC clock. Tests may inject the private collaborator
through the constructor. `D3B2C_PRIVATE_TRANSPORT_IMPORT = FORBIDDEN` and `D3B2C_HTTP_IMPLEMENTATION = FORBIDDEN`;
d3b2c uses the public factory/service only. No generic `fetch_url` API or caller-supplied observed time exists.

Policy is HTTPS GET with TLS verification, redirects disabled, HTTP 200 only, connect/read timeouts 10/30 seconds,
4 MiB maximum complete body, static identifying UA, and no automatic retry. Any 3xx/4xx/5xx, TLS/network/timeout,
partial or oversize response leaves no successful capture. `NAROfficialResponseCaptureTransportError` covers these
states and pre-persistence Content-Length mismatch. If header Content-Length is present, its parsed integer must equal
the exact body length; it is never a body identity or silently rewritten. Persisted non-null Content-Length must equal
loaded body length or repository integrity fails. Retained headers are auxiliary only; HTTP Date is never observed or
available time; control-containing header metadata is rejected. `PERSIST_BEFORE_NORMALIZATION = YES` so valid 200 strict-UTF-8 responses are archived before parser
success/unsupported/validation decisions.

## v013 Exact SQLite Contract

`VERSION = 13`; `NAME = "v013_nar_official_response_capture_schema"`. v013 is additive, has no empty-store
precondition, and does not modify/backfill existing evidence. `apply(connection)` is transaction-neutral: no BEGIN,
COMMIT, or ROLLBACK. `scripts.migrations.runner` imports/orders v013 after v012 and alone owns BEGIN IMMEDIATE,
commit, rollback, and FK activation.

All UTC columns use the existing fixed-width 32-character microsecond UTC text format
`YYYY-MM-DDTHH:MM:SS.ffffff+00:00`; lexical order is chronological. The exact intended DDL is:

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

`EVIDENCE_LOOKUP_INDEX_COUNT = ONE`; the named UNIQUE index is both constraint and lookup. A duplicate ordinary index
on the same columns is forbidden. Repository save/load still recomputes SHA-256 and parses/validates URLs/timestamps;
SQL checks do not replace cryptographic/domain verification. Body dedup and capture insertion are one repository
transaction; no row can reference a missing body. Existing evidence without a body remains `MISSING_CAPTURE`.

## Storage Decision and Future Scope

`DATABASE_LOCATION = SAME_KEIBAOS_DATABASE`. The measured representative size model is illustrative only: one DebaTable
per target race, ten HorseMarkInfo captures per target race, and one RaceMarkTable body per race before repeated
observations or extra historical RaceMark pages.

| target races/year | DebaTable | HorseMarkInfo | RaceMarkTable | total bodies |
| --- | ---: | ---: | ---: | ---: |
| 10,000 | 2.77 GiB | 7.82 GiB | 0.90 GiB | about 11.5 GiB/year |
| 15,000 | 4.16 GiB | 11.73 GiB | 1.35 GiB | about 17.2 GiB/year |

These exclude indexes/rows, WAL, backups, changed bodies that defeat dedup, and added historical coverage. Same DB
keeps archive and simulation data atomic and recoverable together under the existing v013 runner, but backups grow,
WAL/checkpoint operations include capture writes, capture bodies must never be pruned merely to shrink simulation data,
and operational disk monitoring is required. Storage separation needs a separate explicit migration/export phase.
`AUTOMATIC_CAPTURE_RETENTION_DELETE = FORBIDDEN`.

d3b2b1 allowed files are `nar_official_response_capture.py`, its SQLite repository, runner, v013, dedicated
domain/repository/migration tests, these exact migration-registry tests:

```text
tests/test_historical_input_snapshot_migration.py
tests/test_simulation_bet_plan_migration.py
tests/test_simulation_migrations.py
tests/test_sqlite_persisted_simulation_application.py
```

and both phase docs. The complete scan found no additional test with a v012 final-version expectation. d3b2b2 changes
only `scripts/simulation/nar_official_response_live_capture.py`, its dedicated test, and both docs. d3b2c later owns
discovery, scheduling, multi-race collection, and cutoff-eligible selection; no HTTP/private transport implementation.

## Stop Condition

No code blocker is hidden. Intentional limits are operational local-clock trust, no retroactive live-page backfill,
no third-party import, no retention deletion, no pagination/orchestration, and unsupported `past_race_absence`. Stop
for independent architecture re-review; do not implement d3b2b1/b2/c, v013, or live capture.
