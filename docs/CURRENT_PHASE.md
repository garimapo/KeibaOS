# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d3b2b — Trusted NAR official-response capture/archive preparation

## Base and Scope

Formal base: `4af5a7ba4f18769f365ac2c934bcfd0ffcf38818 feat: normalize NAR historical past races`.

Formal branch: `feature/ver0.8-simulator`.

Preparation review branch: `review/4c-2d3b1i6c1d3b2b-prepare`.

This phase is design only. Its only changed files are `docs/CURRENT_PHASE.md` and
`docs/LATEST_CODEX_REPORT.md`. It does not implement capture, HTTP, SQLite, migration, tests, fixtures,
or orchestration.

## Trust Claim and Its Limit

`TRUST_MODEL = OPERATIONALLY_TRUSTED_LOCAL_CAPTURE`.

KeibaOS itself makes a strictly validated HTTPS request, records `observed_at` only after the complete
parser-input body is received, saves those exact bytes, and verifies SHA-256 on both save and load. The
future application API is append-only: it exposes no update, replacement, or delete operation. This is an
operational audit claim, not a cryptographic one: `CRYPTOGRAPHIC_EXTERNAL_TIMESTAMP_AUTHORITY = NOT_PROVIDED`.
A local clock and SQLite cannot prove to a hostile third party that a timestamp was not forged after the fact.
External timestamp attestation is a separate future design if required.

`RETROACTIVE_LIVE_SITE_BACKFILL = IMPOSSIBLE_TO_TRUST`. A current page cannot be assigned an older
`observed_at`, a race/result date, a file time, a Git time, a database insertion time, or HTTP `Date` to make it
eligible for a past prediction cutoff. HorseMarkInfo is especially mutable as later history rows are appended;
RaceMarkTable has no immutability bypass either. For target races before trusted collection begins,
`NAR_LIVE_SITE_ONLY = NO_CAUSALLY_ELIGIBLE_CAPTURE`; this is expected no-data, not a fallback opportunity.
Third-party archives, manual downloads, Wayback, current provider logs, and the current live site are out of scope
for `source_system="nar_official"` trusted capture.

The same requirement applies to the existing c1b DebaTable target input as well as d3b2a's HorseMarkInfo and
RaceMarkTable evidence. A reproducible deployment backup ultimately includes the snapshot database and this capture
archive; provenance digest metadata alone cannot recreate a body.

## Existing Contracts Preserved

No c1a/c1b/c1c/d3b2a contract changes. In particular, this work does not redesign
`HistoricalInputEvidenceReference`, `HistoricalInputSourceRecord`, `NarSuppliedOfficialResponse`, either NAR
normalizer, `HistoricalInputSnapshot`, or snapshot persistence. `available_at` remains `None`; no capture timestamp,
HTTP `Date`, or `Last-Modified` becomes c1a `available_at`. There is no c1a v4, `his-v4`, snapshot schema v4, or
`capture_id` field in historical snapshot evidence.

The archive is joined operationally, not by provider-record parsing, through the exact existing tuple:

```text
EVIDENCE_REPLAY_LOOKUP_KEY = canonical_source_url + response_sha256 + observed_at
```

An archive miss raises a stable capture-missing error. It never fetches the web, substitutes a current page, or
selects an older/newer capture. A stored body whose computed SHA-256 differs from its identity raises a repository
integrity error and is never returned.

## Supported Official URL Vocabulary

Initial trusted NAR capture supports exactly these URL-derived page kinds:

| page kind | canonical HTTPS host(s) | exact path | exact query keys |
| --- | --- | --- | --- |
| `deba_table` | `www.keiba.go.jp` | `/KeibaWeb/TodayRaceInfo/DebaTable` | `k_babaCode`, `k_raceDate`, `k_raceNo` |
| `horse_mark_info` | `www.keiba.go.jp`, `www2.keiba.go.jp` | `/KeibaWeb/DataRoom/HorseMarkInfo` | `k_lineageLoginCode` |
| `race_mark_table` | `www.keiba.go.jp` | `/KeibaWeb/TodayRaceInfo/RaceMarkTable` | `k_babaCode`, `k_raceDate`, `k_raceNo` |

`page_kind` is derived by strict canonical URL validation and cannot be supplied independently. Validation happens
before network access. It rejects non-HTTPS URLs, other hosts, IP literals, credentials, fragments, controls,
whitespace, ports other than absent/443, unknown paths, duplicate/blank/unknown query keys, malformed percent
escapes, `+` query ambiguity, noncanonical positive numeric tokens, and non-real/noncanonical race dates. Query
canonical spelling is the current NAR contract: `k_babaCode`, escaped `k_raceDate=YYYY%2FMM%2FDD`, then `k_raceNo`
for race pages; HorseMarkInfo has its one lineage key. The accepted HorseMarkInfo host is preserved, never rewritten.
This is an independently owned capture URL validator with cross-contract tests; private normalizer helpers are not
imported or refactored.

Official investigation on 2026-08-10 found direct `www` representatives returned HTTP 200, no redirect,
`Content-Type: text/html; charset=UTF-8`, no `Content-Encoding`, and approximate parser-body sizes: DebaTable
297,718 bytes, HorseMarkInfo 83,949 bytes, RaceMarkTable 96,614 bytes. `www2` HorseMarkInfo returned a 301 to `www`.
Therefore syntactic `www2` support remains aligned with d3b2a supplied-response validation, but live capture is
redirect-disabled and a current `www2` request fails closed rather than silently rewriting it.

`LEGACY_NAR_PROVIDER_TEXT_PATH = NOT_TRUSTED_EVIDENCE_ARCHIVE`: its `requests` response-to-`text`, apparent-encoding,
and UTF-8 log write path cannot establish exact parser bytes. `logs/` are never evidence storage.

## Capture Domain and Byte Semantics

The selected d3b2b1 module is `scripts/simulation/nar_official_response_capture.py`. Its public surface is limited to:

```python
class NAROfficialPageKind(StrEnum):
    DEBA_TABLE = "deba_table"
    HORSE_MARK_INFO = "horse_mark_info"
    RACE_MARK_TABLE = "race_mark_table"

@dataclass(frozen=True, slots=True)
class NAROfficialResponseCapture: ...

class NAROfficialResponseCaptureArchive(Protocol): ...

def canonicalize_nar_official_capture_url(response_url: str) -> tuple[NAROfficialPageKind, str]: ...
```

The archive protocol signatures are frozen as:

```python
def save_capture(*, capture: NAROfficialResponseCapture) -> None: ...
def load_capture(*, capture_id: str) -> NAROfficialResponseCapture | None: ...
def load_supplied_response_for_evidence(
    *, canonical_source_url: str, response_sha256: str, observed_at: datetime,
) -> NarSuppliedOfficialResponse: ...
```

The immutable capture fields are: `schema_version: int = 1` (not init), `capture_id: str`, `page_kind`,
`canonical_source_url: str`, `response_sha256: str`, `response_body: bytes`, `charset: Literal["utf-8"]`,
`requested_at: datetime`, `observed_at: datetime`, `stored_at: datetime`, `http_status: int`, and optional
transport metadata `content_type`, `content_encoding`, `http_date`, `etag`, `last_modified`, and
`content_length: int | None`. All timestamps are exact aware datetimes normalized to canonical UTC microsecond text
for persistence; `requested_at <= observed_at <= stored_at` is required.

`response_body` means `EXACT_PARSER_INPUT_ENTITY_BYTES`: the exact byte sequence saved by KeibaOS and subsequently
passed unchanged as `NarSuppliedOfficialResponse.response_body`. SHA-256 is computed over those bytes before UTF-8
decoding, NFC, parsing, normalization, or extraction. This is not a claim to preserve TCP/TLS packets or raw transfer
framing. Initial live capture reads the complete HTTP entity stream with content decoding disabled and accepts only
absent/`identity` Content-Encoding; it never performs `content -> str -> bytes`, `response.text`, apparent-encoding,
or a replacement/fallback decode. A strict UTF-8 validation decode is allowed solely to prove compatibility and is
not persisted or re-encoded. Non-UTF-8 and non-identity encoded entities are unsupported.

`capture_id` is deterministic: `nar-capture-v1:` plus lowercase SHA-256 of UTF-8 canonical JSON (sorted keys,
compact separators) containing exactly schema version, page kind, canonical source URL, response SHA-256, and
canonical UTC `observed_at`. Thus changed observation time yields a distinct capture even for equal URL/body. A same
ID reinsert is idempotent only when every immutable field, including the exact body and metadata, is equal; otherwise
it is a conflict.

`NAROfficialResponseCapture.to_supplied_official_response()` and archive
`load_supplied_response_for_evidence(...)` reconstruct the existing `NarSuppliedOfficialResponse` without a fetch or
text conversion. No near-duplicate supplied-response type is introduced.

## Clock, HTTP, and Persistence Order

`SYSTEM_CLOCK_CORRECTNESS = OPERATIONAL_PRECONDITION`. d3b2b2's composition-owned live service receives an explicit
UTC clock callable; production composition supplies a real aware UTC clock and tests inject a deterministic callable.
Its public capture method never accepts caller-supplied `observed_at`.

`requested_at` is recorded immediately before request start. `observed_at` is recorded immediately after the complete
entity byte stream has been received and before any domain parser/normalizer. `stored_at` is generated immediately
before the archive's atomic commit/finalization; a successful return proves the commit completed after that timestamp.
It is durability audit metadata, never a substitute for `observed_at`.

Initial acquisition policy is HTTPS GET only, certificate verification enabled, redirects disabled, connect timeout
10 seconds, read timeout 30 seconds, maximum complete entity size 4 MiB, static identifying user agent, and no
automatic retry. HTTP 200 is the only successful-capture status. 3xx/4xx/5xx, TLS/transport exceptions, timeout,
partial/oversize body, and network failure create no successful evidence capture. HTTP headers are auxiliary metadata
only: retain Content-Type, Content-Encoding, Date, ETag, Last-Modified, and parsed Content-Length if present; reject
control-containing metadata. `HTTP_DATE_IS_OBSERVED_AT = NO`.

`PERSIST_BEFORE_NORMALIZATION = YES`: a complete, strict-UTF-8, HTTP-200 response is archived before any racing-field
normalizer runs, so a later normalizer validation/unsupported result can still be audited. Successful HTTP capture and
successful domain normalization are deliberately distinct.

## Archive Persistence

`PERSISTENCE_ARCHITECTURE = SQLITE_CONTENT_ADDRESSED_BLOB_PLUS_APPEND_ONLY_CAPTURE_OBSERVATIONS` in the existing
KeibaOS SQLite database. The observed sub-300 KiB official pages and 4 MiB limit make an initial SQLite BLOB archive
reasonable; one transaction and one backup avoid DB/filesystem split-brain. It is application-level append-only, not
cryptographically immutable against a database administrator.

v013 is additive only; existing v008-v012 data remains valid and historical evidence without a body remains a valid
`MISSING_CAPTURE` legacy state. Proposed migration:

```text
VERSION = 13
NAME = "v013_nar_official_response_capture_schema"
```

`nar_official_response_bodies` has `response_sha256 TEXT PRIMARY KEY`, `response_body BLOB NOT NULL`, and
`byte_length INTEGER NOT NULL`, with lowercase-hex, blob-type, nonnegative-length, and `length(response_body) =
byte_length` checks. SHA-to-body equality is verified in domain/repository code.

`nar_official_response_captures` has `capture_id TEXT PRIMARY KEY`, page-kind enum, canonical URL, body SHA foreign
key with restrictive update/delete behavior, exact `utf-8` charset, requested/observed/stored UTC texts, status 200,
the selected nullable header metadata, and checks for canonical text/types and timestamp order. It has
`UNIQUE(canonical_source_url, response_sha256, observed_at_utc)` plus an exact lookup index on the same tuple.
Foreign keys are enabled and verified. Body insertion/deduplication and capture-observation insertion occur in one
`BEGIN IMMEDIATE` transaction; no capture can reference a missing body.

The concrete d3b2b1 repository is
`scripts/simulation/repositories/sqlite_nar_official_response_capture_repository.py`. Its public operations are only
`save_capture`, `load_capture(capture_id=...)`, and
`load_supplied_response_for_evidence(canonical_source_url=..., response_sha256=..., observed_at=...)`. It exposes no
update/delete/list API. Loads recompute SHA-256, validate the canonical URL/page kind and timestamps, and fail closed
without fallback on malformed metadata, missing body, body/hash mismatch, or duplicate/conflicting rows.

Error taxonomy is stable and minimal: `NAROfficialResponseCaptureValidationError` for invalid input/domain/URL,
`NAROfficialResponseCaptureUnsupportedError` for recognized unsupported encoding/page state,
`NAROfficialResponseCaptureTransportError` for no completed acceptable HTTP response, and
`NAROfficialResponseCaptureRepositoryIntegrityError` (a repository data-integrity family error) for stored/archive
corruption. `NAROfficialResponseCaptureMissingError` identifies an exact archive miss. No raw body is logged; logs are
diagnostic only and never evidence.

## Recommended Decomposition

`4C-2d3b1i6c1d3b2b1 — NAR official-response capture domain + SQLite archive implementation` owns URL/page-kind
contract, capture domain/ID/digest, v013, archive repository, exact evidence lookup, reconstruction, and corruption
handling. It has no network or racing-field parsing.

`4C-2d3b1i6c1d3b2b2 — NAR trusted live HTTP capture implementation` owns the injected-clock/transport service,
pre-request URL validation, HTTPS GET/timeouts/redirect/TLS policy, exact entity read, timestamp creation, selected
metadata, and save-before-normalization. It has no race-field parsing, pagination, capture selection, or historical
row logic.

`4C-2d3b1i6c1d3b2c` later owns target and historical page discovery, capture scheduling, retry-before-cutoff policy,
multi-race/horse collection, and selection of eligible archive captures. It must still let the existing builder enforce
the final `observed_at <= captured_at <= information_cutoff` causal rule. `past_race_absence` remains unsupported.

Its only module-defined public capture boundary is:

```python
class NAROfficialLiveResponseCaptureService:
    def __init__(
        self,
        *,
        archive: NAROfficialResponseCaptureArchive,
        transport: _NAROfficialHTTPTransport,
        utc_clock: Callable[[], datetime],
    ) -> None: ...

    def capture(self, *, response_url: str) -> NAROfficialResponseCapture: ...
```

`_NAROfficialHTTPTransport` is a private injected test/composition collaborator whose complete-response method returns
only after reading exact entity bytes; no caller can pass an `observed_at`. Production composition supplies the real
requests-backed transport and aware UTC clock. The service has no generic `fetch_url` API and no package-root export.

## Future Allowed Files and Tests

The exact d3b2b1 allowed files are:

```text
scripts/simulation/nar_official_response_capture.py
scripts/simulation/repositories/sqlite_nar_official_response_capture_repository.py
scripts/migrations/runner.py
scripts/migrations/versions/v013_nar_official_response_capture_schema.py
tests/test_nar_official_response_capture.py
tests/test_sqlite_nar_official_response_capture_repository.py
tests/test_nar_official_response_capture_migration.py
tests/test_historical_input_snapshot_migration.py
tests/test_simulation_bet_plan_migration.py
tests/test_simulation_migrations.py
tests/test_sqlite_persisted_simulation_application.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The four named existing tests are every current migration-registry expectation that hard-codes the v012 endpoint and
therefore needs the v013 update. No snapshot/c1a/c1b/d3b2a production module is authorized.

The exact d3b2b2 allowed files are:

```text
scripts/simulation/nar_official_response_live_capture.py
tests/test_nar_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Its fake-transport tests must prove pre-network URL rejection, 200-only persistence, raw byte identity, timestamp
order after complete read, disabled redirects/TLS verification, no `response.text`/apparent encoding, non-UTF-8 and
partial/timeout failure without a capture, no retry, and immediate byte-identical reconstruction. d3b2b1 tests must
cover deterministic IDs, body dedup, separate observations, exact tuple lookup/miss, idempotent and conflicting
reinserts, atomic failure, corruption fail-closed, foreign keys, append-only API, v013, and no c1a/snapshot schema
change.

## Blockers and Stop Condition

No code blocker was found for the proposed archive. The known limitations are intentional: operational local-clock
trust is not third-party attestation; pre-collection historical replay is no-data; current pages cannot backfill it;
and `www2` currently redirects while redirects are disabled. Begin trusted collection as soon as this primitive is
implemented, but do not start d3b2b1, d3b2b2, acquisition orchestration, v013, or any live production capture in this
phase. Stop for independent architecture review.
