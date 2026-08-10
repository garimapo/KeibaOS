# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6c1d3b2b2` - NAR trusted live HTTPS capture implementation.

Formal base: `5ab64c6c9401b56e4bacd5b3b4049452609ddf60 feat: archive trusted NAR response captures`.

Formal branch: `feature/ver0.8-simulator`.

Implementation review branch: `review/4c-2d3b1i6c1d3b2b2-implementation`.

## Allowed Files

```text
scripts/simulation/nar_official_response_live_capture.py
tests/test_nar_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Implemented Boundary

One supported NAR URL is canonicalized before clock, transport, or archive access. The service samples
requested_at before HTTPS, observed_at after a complete accepted byte entity, and stored_at before immutable
capture construction and archive save. It returns only after `archive.save_capture(capture=...)` succeeds.

The new public surface is exactly `NAROfficialLiveResponseCaptureService`,
`NAROfficialResponseCaptureTransportError`, and `build_nar_official_live_response_capture_service`. The sole
service operation is `capture_response(*, response_url)`. Existing capture-domain types, URL canonicalization,
and archive protocol are reused unchanged; no package-root export exists.

The private requests transport uses verified HTTPS, `stream=True`, `allow_redirects=False`,
`timeout=(10.0, 10.0)`, `Accept-Encoding: identity`, and adapters configured with zero retries. Only HTTP 200,
absent/identity content encoding, byte-streamed entities at most 4 MiB, a valid exact Content-Length when supplied,
and an effective URL identical to the requested canonical URL can produce a result. Parser-input bytes are never
decoded or text-round-tripped in transport. Unsupported encoding is a capture-domain unsupported error; networking,
status, redirect, length, URL, and stream failures are transport errors. Archive and capture-domain failures propagate
unchanged.

No SQLite, migration, DB-path composition, parser, normalizer, scheduler, retry loop, discovery, pagination, CLI, or
historical absence behavior was added. `PERSIST_BEFORE_NORMALIZATION = YES` remains the boundary.

## Required Verification and Stop Condition

Run the dedicated live-capture tests, the listed related capture/NAR/snapshot tests, full pytest, static source checks,
package-root check, global migration/capture archive/legacy provider invariance checks, `git diff --check`, and
`git status --short`. Stop after one pushed review commit for independent review; do not begin d3b2c or formal integration.
