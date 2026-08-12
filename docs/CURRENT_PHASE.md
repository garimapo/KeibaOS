Exit code: 0
Wall time: 0.2 seconds
Output:
Exit code: 0
Wall time: 0.2 seconds
Output:
# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1c` 遯ｶ繝ｻJRA trusted official-response capture architecture preparation.

Formal branch/base: `feature/ver0.8-simulator` at `7632a1381c77403e55284e027392d0fbc1f5a346`.

Preparation review branch: `review/4c-2d3b1i6d1c-prepare`.

## Frozen Architecture

```text
JRA_CAPTURE_ARCHITECTURE = JRA_SPECIFIC_CAPTURE_DOMAIN + DEDICATED_APPEND_ONLY_SQLITE_ARCHIVE + JRA_SPECIFIC_LIVE_HTTPS_SERVICE
KEEP_NAR_CAPTURE_FROZEN = YES
JRA_CAPTURE_DATABASE = SEPARATE_COMPOSITION_OWNED_SQLITE_DATABASE
JRA_CAPTURE_SCHEMA_VERSION = 1
GLOBAL_MIGRATION_FINAL_VERSION = 13
JRA_CAPTURE_MIGRATION_REGISTRY = jra_official_response_capture_schema_migrations
JRA_CAPTURE_PAGE_KINDS = RACE_RESULT(accessS), HORSE_PROFILE_HISTORY(accessU)
ACCESS_D_AND_ACCESS_O = DEFERRED_NOT_IN_INITIAL_CAPTURE_SCOPE
```

The capture boundary is provider-specific. NAR capture, its database, its registry, and its schema remain frozen.
There is no provider-neutral refactor: DRYness is not a correctness reason to join the two archival trust domains.
The JRA archive database is a distinct composition-supplied SQLite file (recommended operational path:
`database/jra_official_response_captures.sqlite3`), never `database/keiba.db` and never the NAR-capture database.

JRA entity identity remains separate from capture URL identity. The established `jra:race:<YYYY>:<VV>:<MM>:<DD>:<RR>`,
`jra:horse:<10 ASCII digits>`, and `jra:result:<...>:horse:<10 ASCII digits>` contracts remain unchanged. An accessS
capture must use an already-resolved URL accepted by `parse_jra_result_url_identity`; an accessU capture must use one
accepted by `parse_jra_horse_profile_url_identity`. Capture must not synthesize a CNAME from a stable entity identity.
Selector, CNAME calendar date, and opaque tail remain part of retrieval URL identity, not entity identity.

## Future Public Capture Surface

`scripts/simulation/jra_official_response_capture.py` will own exactly the JRA capture-domain surface:

```text
JRAOfficialPageKind
  RACE_RESULT = "race_result"
  HORSE_PROFILE_HISTORY = "horse_profile_history"
JRAOfficialResponseCaptureError
JRAOfficialResponseCaptureValidationError
JRAOfficialResponseCaptureUnsupportedError
JRAOfficialResponseCaptureMissingError
JRASuppliedOfficialResponse
JRAOfficialResponseCapture
JRAOfficialResponseCaptureArchive
canonicalize_jra_official_capture_url(*, page_kind, response_url) -> str
```

`JRASuppliedOfficialResponse` is a frozen/slotted parser-input value with exactly `response_url`, `response_body`,
`charset`, and `observed_at`. It accepts exact nonempty `bytes`, exact charset spelling `"cp932"`, a canonical
supported JRA response URL, and an aware timestamp canonicalized to UTC. It strictly decodes those same bytes once
with CP932 before becoming parser input; it has no requested/stored timestamps, HTTP metadata, decoded text, or
availability timestamp.

`JRAOfficialResponseCapture` is frozen/slotted and owns exactly `canonical_source_url`, `response_body`, `charset`,
`requested_at`, `observed_at`, `stored_at`, `http_status`, `content_type`, `content_encoding`, `http_date`,
`etag`, `last_modified`, and `content_length`; derived fields are `schema_version=1`, `capture_id`, `page_kind`,
and `response_sha256`. It reconstructs the supplied-response value without re-encoding. Capture-domain invalid input
is validation/unsupported error; exact archive absence is `JRAOfficialResponseCaptureMissingError`. Repository
conflict, validation, and corruption use the existing repository error vocabulary where appropriate.

The future live module owns only `JRAOfficialLiveResponseCaptureService`,
`JRAOfficialResponseCaptureTransportError`, and `build_jra_official_live_response_capture_service`. Its service method
is `capture_response(*, page_kind: JRAOfficialPageKind, response_url: str) -> JRAOfficialResponseCapture`: the caller
must state page kind and the canonicalizer must prove the URL matches it before network access. The factory alone owns
the real requests transport and UTC clock; the core service receives injected archive, transport, and clock for
deterministic tests. No package-root export is planned.

## URL and Parser-Input Byte Contract

`canonicalize_jra_official_capture_url` first invokes the applicable public pure-identity URL validator, then applies
only capture-specific canonicalization. It accepts the exact current accessS/accessU host, HTTPS path, one `CNAME`, and
established selector/key/tail grammar; it rejects URL/page-kind mismatch, credentials, port, fragment, malformed
encoding, unknown/duplicate query keys, and any form rejected by the identity parser. It preserves the valid CNAME
selector and opaque tail. Its sole spelling normalization is the one CNAME delimiter: a raw `/` or exactly one uppercase
`%2F` becomes exactly one uppercase `%2F` in the stored URL. It never double-decodes or converts `%252F`.
Thus raw-slash and `%2F` aliases have one capture URL identity while distinct valid CNAME selectors/tails remain
distinct capture URLs even when they collapse to one entity identity.

```text
RAW_RESPONSE_SHA_SEMANTICS = lowercase SHA-256 over exact raw parser-input entity bytes before decode or normalization
PARSER_INPUT_BYTE_SEMANTICS = complete HTTP entity bytes after HTTP framing, with no transfer/content transcoding
JRA_CHARSET_POLICY = exact "cp932" + strict CP932 decode only
```

No UTF-8 transcode, apparent encoding, charset fallback, `errors="ignore"`, `errors="replace"`, NFC body normalization,
or decoded-text hash is permitted. `PERSIST_BEFORE_NORMALIZATION = YES` applies to later racing-field parsing only:
valid URL/HTTP/encoding/CP932 bytes are archived before a field normalizer sees them. Invalid URL, non-200 response,
unsupported encoding, incomplete/oversize body, or strict-CP932 failure creates no successful capture and is not saved.

The live probes on 2026-08-12, using `Accept-Encoding: identity`, `allow_redirects=False`, and TLS verification,
reported the following official observations; no bodies were persisted:

| Page | Status / effective URL | Content-Type | Content-Encoding | Content-Length | Raw entity bytes | CP932 |
| --- | --- | --- | --- | --- | ---: | --- |
| accessS | 200 / supplied resolved accessS URL; no redirect | `text/html` | absent | absent | 94,570 | strict pass; HTML meta `Shift_JIS` |
| accessU | 200 / supplied resolved accessU URL; no redirect | `text/html` | absent | absent | 55,797 | strict pass; HTML meta `Shift_JIS` |

`JRA_CONTENT_TYPE_POLICY` is exact HTML media type `text/html`, case-insensitive after ASCII OWS trimming; it may
carry at most one `charset` parameter only when the normalized value is `shift_jis` or `cp932`. The HTTP header may
omit charset, as the probes did; strict CP932 decoding is authoritative. `JRA_CONTENT_ENCODING_POLICY` accepts only
absent or `identity`; any nonempty content coding fails closed. Because the service sends
`JRA_ACCEPT_ENCODING_POLICY = identity` and accepts no compressed coding, the raw bytes read with transport decoding
disabled are exactly the archive hash bytes and parser bytes. `CONTENT_LENGTH_POLICY`: an absent header is allowed; a
present header must be canonical ASCII decimal, be prechecked at or below 4 MiB, and exactly equal the final byte
count. `JRA_MAX_BODY_BYTES = 4,194,304`; the observed 94,570-byte maximum leaves substantial headroom without
accepting unbounded bodies.

```text
JRA_REDIRECT_POLICY = DISABLED_FAIL_CLOSED
JRA_TLS_POLICY = HTTPS_CERTIFICATE_VERIFICATION_REQUIRED
JRA_HTTP_STATUS_POLICY = EXACT_200_ONLY
JRA_TIMEOUT_POLICY = CONNECT_10_SECONDS + READ_10_SECONDS
JRA_AUTOMATIC_RETRY_POLICY = NONE
```

## Time, Capture Identity, and Archive Semantics

`requested_at` is sampled immediately before the single request; `observed_at` immediately after the complete body
is received; `stored_at` immediately before archive finalization. Every value must be aware and normalized to UTC,
with `requested_at <= observed_at <= stored_at`. `available_at = None`; neither the HTTP `Date` header nor page/race
dates establish availability. `observed_at` remains the later evidence causality value and must satisfy
`observed_at <= prediction/information cutoff`. A current live page cannot be backdated into trusted evidence for an
older cutoff.

`JRA_CAPTURE_ID_POLICY` is exact:

```text
jra-capture-v1:sha256(UTF-8 JSON, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
{
  "canonical_source_url": canonical_source_url,
  "observed_at_utc": canonical UTC microsecond text,
  "page_kind": page_kind.value,
  "response_sha256": lowercase SHA-256(raw parser-input bytes),
  "schema_version": 1
}
```

Decoded text, mutable SQLite row IDs, requested/stored timestamps, and HTTP auxiliary metadata do not participate.
Capture ID timestamps are intentionally distinct from c1a source-ID semantics, where evidence timestamps can remain
excluded by the existing source-record contract.

`BODY_DEDUP_POLICY = exact response_sha256`: `jra_official_response_bodies` stores one exact BLOB and byte length for
each SHA-256. The same raw body at different URL or observation time may share its body row, while every capture
observation remains separate. `EVIDENCE_LOOKUP_KEY` is exactly `(canonical_source_url, response_sha256, observed_at
UTC microsecond text)`. `load_supplied_response_for_evidence` reconstructs only that exact captured response;
`ARCHIVE_MISS_POLICY = stable JRAOfficialResponseCaptureMissingError with no network, nearest, latest, same-URL, or
same-SHA fallback`.

The dedicated v001 registry is `jra_official_response_capture_schema_migrations`; it is not global
`schema_migrations` and not the NAR registry. The v001 DDL is transaction-neutral and the dedicated runner owns
`BEGIN IMMEDIATE`/commit/rollback. The registry must be the exact approved schema before it is trusted; pre-existing
unregistered/malformed tables, unknown versions, version-name mismatch, malformed rows, or schema collision fail
closed without adoption or repair. There is no global v014.

```sql
CREATE TABLE jra_official_response_capture_schema_migrations (
  version INTEGER PRIMARY KEY CHECK (typeof(version) = 'integer' AND version > 0),
  name TEXT NOT NULL UNIQUE CHECK (typeof(name) = 'text' AND length(name) > 0)
) WITHOUT ROWID;

CREATE TABLE jra_official_response_bodies (
  response_sha256 TEXT PRIMARY KEY CHECK (typeof(response_sha256) = 'text' AND length(response_sha256) = 64
    AND response_sha256 NOT GLOB '*[^0-9a-f]*'),
  response_body BLOB NOT NULL CHECK (typeof(response_body) = 'blob'),
  byte_length INTEGER NOT NULL CHECK (typeof(byte_length) = 'integer' AND byte_length > 0
    AND byte_length = length(response_body))
) WITHOUT ROWID;

CREATE TABLE jra_official_response_captures (
  capture_id TEXT PRIMARY KEY,
  schema_version INTEGER NOT NULL CHECK (typeof(schema_version) = 'integer' AND schema_version = 1),
  page_kind TEXT NOT NULL CHECK (page_kind IN ('race_result', 'horse_profile_history')),
  canonical_source_url TEXT NOT NULL,
  response_sha256 TEXT NOT NULL REFERENCES jra_official_response_bodies(response_sha256)
    ON UPDATE RESTRICT ON DELETE RESTRICT,
  charset TEXT NOT NULL CHECK (charset = 'cp932'),
  requested_at_utc TEXT NOT NULL, observed_at_utc TEXT NOT NULL, stored_at_utc TEXT NOT NULL,
  http_status INTEGER NOT NULL CHECK (typeof(http_status) = 'integer' AND http_status = 200),
  content_type TEXT, content_encoding TEXT, http_date TEXT, etag TEXT, last_modified TEXT,
  content_length INTEGER,
  CHECK (requested_at_utc <= observed_at_utc AND observed_at_utc <= stored_at_utc)
) WITHOUT ROWID;
CREATE UNIQUE INDEX ux_jra_official_response_captures_evidence
  ON jra_official_response_captures(canonical_source_url, response_sha256, observed_at_utc);
```

Domain and repository reconstruction additionally prove every stored raw SHA, body length, capture ID, canonical
URL/page kind, charset, UTC timestamp spelling/order, HTTP status, metadata type, and evidence uniqueness. Missing
or duplicated related rows, SHA/length/identity mismatch, SQLite read/write errors, and corrupted archive state raise
repository data-integrity errors. `APPEND_ONLY_POLICY = no update/delete/replace/prune API; exact reinsert is
idempotent only when every immutable field agrees`. A save must not insert a missing body to repair pre-existing
corruption. Administrative SQLite tampering is not cryptographically prevented, but it is detected fail-closed on the
validated read/save paths. `RETENTION_POLICY = no automatic retention deletion`; the separate archive needs its own
backup and is a required companion to main data for replay.

## Operations, Capacity, and Causality Limits

`JRA_REQUEST_PACING_POLICY = serialized requests, no service sleep, no retry; composition owns a conservative
minimum one-second interval`. This is KeibaOS operational pacing, not a claim about a JRA published rate limit.

Using the observed raw sizes and a planning assumption of 14 target entries plus five historical starts per entry,
one target race initially needs 14 accessU responses and 70 accessS responses: about 7,401,058 raw bytes
(approximately 7.06 MiB) before metadata/SQLite overhead and body deduplication. At 100 / 1,000 / 10,000 target races
per year this is approximately 0.74 / 7.40 / 74.01 GB of raw bytes (0.69 / 6.89 / 68.93 GiB). Real use varies by page
size, start count, overlapping horses, and deduplication. accessU history grows over time; a later capture cannot
reconstruct the complete response available at an older cutoff. Result pages are not assumed immutable: replay still
requires an archived raw observation no later than the applicable cutoff.

```text
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
MIXED_HISTORY_COLLECTION_READY = NO
JRA_HISTORICAL_REPLAY_WITHOUT_PRE_CUTOFF_CAPTURE = NOT_TRUSTED
```

No bridge, Wayback/import backfill, raw-body persistence in `keiba.db`, acquisition orchestration, collection
pagination, JRA field normalizer, or retroactive timestamp fabrication is designed here.

## Recommended Implementation Split

```text
RECOMMENDED_PHASE_SPLIT = d1c1_CAPTURE_DOMAIN_AND_DEDICATED_ARCHIVE, THEN_d1c2_LIVE_HTTPS_SERVICE, THEN_d1d_RESULT_NORMALIZER_PREPARE
```

`4C-2d3b1i6d1c1` 遯ｶ繝ｻJRA supplied-response/capture domain plus dedicated SQLite archive:

```text
scripts/simulation/jra_official_response_capture.py
scripts/simulation/jra_official_response_capture_migration.py
scripts/simulation/jra_official_response_capture_migration_runner.py
scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py
tests/test_jra_official_response_capture.py
tests/test_jra_official_response_capture_migration.py
tests/test_sqlite_jra_official_response_capture_repository.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

`4C-2d3b1i6d1c2` 遯ｶ繝ｻJRA live HTTPS capture service, after c1 is formal:

```text
scripts/simulation/jra_official_response_live_capture.py
tests/test_jra_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Then `4C-2d3b1i6d1d` may prepare the JRA historical result-source contract/normalizer. It must not start until c1/c2
and the separate JRA result design are independently approved.

## Allowed Files and Stop Condition

This PREPARE changes only:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Stop for independent architecture review after the docs-only review commit. Do not implement capture, create a
database, add fixtures/tests/migrations, change NAR capture, begin d1c1/c2/d1d, or attempt the NAR-to-JRA bridge.
