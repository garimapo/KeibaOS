# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1c2` — JRA trusted live HTTPS capture implementation.

Formal base: `93da236d319f686fd06842b46404b780e73dff72`.

Implementation review branch: `review/4c-2d3b1i6d1c2-implementation`.

## Implemented Contract

```text
JRA_LIVE_CAPTURE = IMPLEMENTED_FOR_REVIEW
JRA_CAPTURE_SCHEMA_VERSION = 1
JRA_CAPTURE_DATABASE = SEPARATE
JRA_CAPTURE_PAGE_KINDS = RACE_RESULT + HORSE_PROFILE_HISTORY
JRA_ACCEPT_ENCODING_POLICY = identity
JRA_CONTENT_ENCODING_POLICY = absent_or_identity
JRA_REDIRECT_POLICY = DISABLED_FAIL_CLOSED
JRA_HTTP_STATUS_POLICY = EXACT_200_ONLY
JRA_TLS_POLICY = VERIFY_REQUIRED
JRA_TIMEOUT_POLICY = CONNECT_10_READ_10
JRA_AUTOMATIC_RETRY_POLICY = NONE
JRA_MAX_BODY_BYTES = 4194304
JRA_REQUEST_PACING = COMPOSITION_OWNED
RAW_RESPONSE_SHA = EXACT_CP932_PARSER_INPUT_BYTES
PERSIST_BEFORE_NORMALIZATION = YES
GLOBAL_MIGRATION_FINAL_VERSION = 13
NAR_CAPTURE = UNCHANGED
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
MIXED_HISTORY_COLLECTION_READY = NO
```

`scripts/simulation/jra_official_response_live_capture.py` exposes exactly:

```text
JRAOfficialLiveResponseCaptureService
JRAOfficialResponseCaptureTransportError
build_jra_official_live_response_capture_service
```

`capture_response(*, page_kind, response_url)` canonicalizes and validates the declared page kind before sampling
the clock, transport access, or archive access. Only canonical accessS race-result and accessU horse-profile/history
URLs are sent to the private requests transport. The transport sends `Accept-Encoding: identity`, disables redirects,
requires TLS verification, uses `(10.0, 10.0)` timeouts, and configures zero automatic retries. It reads the raw
stream with content decoding disabled, accepts only absent/identity response coding, applies canonical Content-Length
and incremental 4 MiB limits, closes every response, and retains only the complete parser-input entity bytes.

The service samples requested/observed/stored UTC times around acquisition, delegates strict CP932, media-type, raw
SHA, and capture identity construction to c1, archives the complete immutable capture before returning it, and
propagates archive failures unchanged. It does not parse racing fields, synthesize CNAME values, fetch history pages,
or own pacing, discovery, database paths, a provider bridge, or source normalization.

## Allowed Files

```text
scripts/simulation/jra_official_response_live_capture.py
tests/test_jra_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification and Stop Condition

Dedicated JRA live capture, JRA capture/archive, JRA identity, and NAR capture/live regressions pass. Full-suite,
source-boundary, package-root export, unchanged NAR/global migration, and diff checks are required before review
publication. Stop for independent implementation review. Do not integrate formal or begin d1d, JRA normalization,
JRA race-history discovery, or an NAR/JRA bridge.
