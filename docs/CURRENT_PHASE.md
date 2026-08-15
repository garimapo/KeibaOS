# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d4b2` — JRA final-odds live POST transport.

Formal base: `d91063fade86cfcc19b7dbd05bad3ed6172fde58`.

Review branch: `review/4c-2d3b1i6d1d4b2-final-odds-live-post`.

## Implemented Contract

`JRAOfficialLiveResponseCaptureService` retains its existing GET-only public method:

```text
capture_response(*, page_kind, response_url) -> JRAOfficialResponseCapture
```

It continues to accept only accessS/accessU. `FINAL_WIN_ODDS` remains rejected by that GET boundary, and its GET
transport call shape remains unchanged.

The same service now provides exactly one separate final-odds operation:

```text
capture_final_win_odds_response(
    *,
    request_locator: JRAOfficialFinalWinOddsRequestLocator,
) -> JRAFinalWinOddsSuppliedOfficialResponse
```

It accepts only an exact already-validated locator before sampling the clock, using HTTP, or calling the archive. It
does not discover races, reconstruct endpoints/CNAMEs, decode response text, parse odds, build neutral evidence, or
perform a real official capture in tests.

## POST Transport

The private final-odds transport uses only the locator endpoint
`https://www.jra.go.jp/JRADB/accessO.html` with a POST form containing exactly `cname=<raw locator CNAME>`. Standard
form encoding is used, including encoding the raw CNAME slash as `%2F`; CNAME is never sent as a query parameter.

The prepared request is independent of persistent session state: it uses `Accept-Encoding: identity` and
`Content-Type: application/x-www-form-urlencoded`, while `Cookie`, `Referer`, and `Origin` are removed before the
actual send. Redirects are disabled, TLS verification is required, retries remain zero, and the timeout remains
`(10.0, 10.0)`.

It retains the GET transport's exact raw-byte safeguards: HTTP 200 only, exact effective endpoint, absent or identity
content encoding, canonical ASCII Content-Length, 4 MiB preflight/incremental limit, raw streaming with
`decode_content=False`, no text/decode/re-encode path, and response closure on all outcomes. Transport
contradictions fail closed.

## Capture Sequence and Boundaries

The final-odds service sequence is:

```text
validated locator -> requested_at -> POST bytes -> observed_at -> stored_at
-> JRAFinalWinOddsResponseCapture -> archive.save_final_win_odds_capture -> supplied response
```

The separate b1 final-odds capture domain remains the sole owner of strict CP932 validation and immutable v2 capture
identity. Failed clock sampling, transport result, capture-domain validation, or archive persistence returns no
supplied response; archive failures propagate. Supplied observation timestamps are preserved without temporal
backdating or aggregation.

The archive/domain, repositories, dedicated migrations, global migration registry (still ending at 14), neutral
request evidence, NAR production, normalizers, historical acquisition, and the NAR/JRA bridge are unchanged.

## Allowed Files

```text
scripts/simulation/jra_official_response_live_capture.py
tests/test_jra_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop for independent implementation review. Do not integrate formal, perform real accessO capture, or begin a
normalizer, discovery, bridge, or subsequent phase.
