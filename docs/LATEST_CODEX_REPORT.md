# Latest Codex Report

## Phase 36 — NAR Official Market Odds Raw Acquisition Harness Implementation

Status: `READY_FOR_REVIEW`
Base: `7f62cd0e0e91fd3fb2acdb62ad490d345c72a097`
Branch: `feature/post-v0.8-daily-replay`
Blockers: none

### Implementation

Implemented the Phase35-frozen public API in
`scripts/simulation/nar_market_odds_raw_acquisition.py`: the exact acquisition error hierarchy,
`NARMarketOddsRawAcquisitionTarget`, `NARMarketOddsRawHTTPResponse`, transport and clock Protocols,
`RequestsNARMarketOddsRawAcquisitionTransport`, and
`acquire_nar_market_odds_raw_response(...)`.

One invocation validates one exact Phase32 request identity, samples the injected clock immediately
before one transport call and twice after receipt, and constructs the exact Phase32
`NARMarketOddsResponseCapture`. Raw response bytes are passed unchanged; Phase32 remains the sole
response-SHA, length, request-identity, and capture-identity authority.

The concrete transport uses one fresh non-persistent session, disables environment credentials,
clears default headers, configures no retries, performs one verified HTTPS GET with no redirects and
`(10.0, 20.0)` timeout, requests identity transfer encoding, disables response decoding, and enforces
the 4 MiB bound. It requires the exact canonical/effective URL, HTTP 200,
`text/html; charset=UTF-8`, and absent/exact `identity` content encoding. Only Content-Type,
Content-Encoding, Date, ETag, Last-Modified, and Content-Length are mapped. Cookies, authorization,
session/CSRF values, and all other headers are discarded.

The module performs no source-state or HTML inspection, parsing, Decimal odds work, fixture publication,
database/archive persistence, replay/manifest integration, EV, strategy, scheduling, or JRA work.
Phase33 and Phase34 remain `DESIGN_BLOCKED` pending a separately approved Phase37 fixture acquisition
and qualification step. `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE` remains open.

### Verification

```text
Phase36 dedicated, ResourceWarning-as-error: 28 passed
Phase32/NAR/Phase30/Phase25/27/28 related: 204 passed
full unittest discovery: 3231 passed
focused compilation: passed
static forbidden-boundary audit: passed
official one-target read-only smoke: passed
```

The live smoke returned HTTP 200, UTF-8, no content encoding, a non-empty body, and the exact effective
URL. Its body was neither displayed nor saved. Existing unrelated SQLite `ResourceWarning`s were
observed in the related/full suites; the dedicated Phase36 suite remained clean.

The final-review exception-taxonomy finding is corrected. Malformed target structures are validated
before clock or transport use; target-derived Phase32 request errors, missing nested fields, and wrong
exact types are translated to `NARMarketOddsRawAcquisitionValidationError` with their cause retained.
The previous forged-page-kind Phase32 error and forged-race-identity `AttributeError` now both produce
the exact acquisition validation error, with zero clock samples and zero transport calls. A forged
exact race identity with missing fields is covered by the same fail-closed regression.

The focused re-review's exact remaining reproducer was a Phase32 request whose
`canonical_request_url` slot had been removed with low-level mutation. The final narrow request
boundary now safely retrieves and exact-type-checks all derived Phase32 request fields before guarded
equality with a builder-rederived authoritative request. Missing canonical URL, missing request digest,
and wrong-type canonical URL regressions all return exact
`NARMarketOddsRawAcquisitionValidationError`, with zero clock and transport calls. Transport, clock,
HTTP/source, and Phase32 response-capture error mapping remains outside this translation boundary.

### Git state

The exact four Allowed Files are changed and remain unstaged:

```text
scripts/simulation/nar_market_odds_raw_acquisition.py
tests/test_nar_market_odds_raw_acquisition.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No fixture, database, or log file changed. Nothing was staged, committed, or pushed.
