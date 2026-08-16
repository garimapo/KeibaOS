# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c2` — JRA accessD live capture boundary preparation.

Formal base: `94ceb4742e7fec6b758d1ceded2ffecc422c873f`.

Review branch: `review/4c-2d3b1i6d1d5f1c2-jra-accessd-live-capture-prepare`.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

This is design only. Production, tests, archive/schema/migration changes, and real trusted
capture are forbidden.

## Frozen Live-Capture Contract

Add one method to the existing `JRAOfficialLiveResponseCaptureService`, without adding a
module-level or package-root export:

```python
capture_target_race_card_response(
    self,
    *,
    response_url: str,
) -> JRAOfficialTargetRaceCardResponseCapture
```

`capture_response(*, page_kind, response_url)` remains exactly its existing v1 public
API and accessS/accessU-only behavior. It must continue to reject
`TARGET_RACE_CARD` before clock, transport, or archive use. The existing
`capture_final_win_odds_response(*, request_locator)` remains the separate v2 POST
API.

The new method accepts only an already canonical accessD URL. Its first operation is the
existing v3-only accessD canonical boundary, which validates
`parse_jra_race_card_url_identity(response_url)` and requires the canonical
`https://www.jra.go.jp/JRADB/accessD.html?CNAME=...%2F..` spelling. A malformed,
noncanonical, wrong-family, or wrong-type URL raises the existing capture validation
error before clock, transport, or archive work. It never calls the v1 canonicalizer.

The exact collaborator order is:

```text
v3 accessD canonical validation
-> requested_at = existing injected UTC clock
-> existing transport.fetch(canonical_source_url=canonical_accessD_url)
-> verify exact _JRAOfficialHTTPResponse and exact canonical URL
-> observed_at = existing injected UTC clock
-> stored_at = existing injected UTC clock
-> JRAOfficialTargetRaceCardResponseCapture(...)
-> archive.save_target_race_card_capture(capture=...)
-> return that v3 capture
```

The existing `_JRAOfficialHTTPTransport.fetch` contract is reused unchanged. It remains
the sole GET transport: HTTPS, `www.jra.go.jp`, TLS verification, redirects disabled,
HTTP 200 only, zero retries, 10s/10s timeout, `Accept-Encoding: identity`, compressed
response rejection, raw undecoded bytes, exact optional `Content-Length`, 4 MiB limit,
and response closure on every path. No `fetch_target_race_card` transport method is
added. The existing injected UTC clock and its exact-aware validation are also reused
unchanged.

`JRAOfficialTargetRaceCardResponseCapture` owns strict CP932 bytes, content/status/
encoding/length validation, raw SHA-256, and
`requested_at <= observed_at <= stored_at`. No archive write occurs after a transport
failure, contradictory transport result, post-fetch clock error, or v3 domain
construction failure. `save_target_race_card_capture` is mandatory before return; its
conflict/integrity/runtime failure propagates without a partial capture value. Neither
`save_capture` (v1) nor `save_final_win_odds_capture` (v2) may be called.

The live method has no caller-supplied timestamp. It preserves only its three actual
clock samples; it cannot backdate a response or establish historical availability.
Target cutoff eligibility remains downstream snapshot/source policy. Thus
`NO_BACKDATED_LIVE_RESPONSE` and `NO_FUTURE_LEAKAGE` are preserved: a live capture is
evidence only at the actual observed instant returned by this service.

## Family Separation

```text
accessS/accessU -> capture_response -> JRAOfficialResponseCapture -> jra-capture-v1
accessO          -> capture_final_win_odds_response -> JRAFinalWinOddsResponseCapture -> jra-capture-v2
accessD          -> capture_target_race_card_response -> JRAOfficialTargetRaceCardResponseCapture -> jra-capture-v3
```

No broad family-union method, no accessD-to-v1/v2 conversion, no parser/source-record/
snapshot work, and no live HTTP call in this preparation phase are authorized.

## Next Implementation Scope

The smallest implementation changes only:

```text
scripts/simulation/jra_official_response_live_capture.py
tests/test_jra_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Required tests include exact service signature/public surface; canonical accessD success
with exact transport URL, timestamps, v3 capture, and v3-only archive-before-return;
legacy v1 and v2 APIs unchanged; v1 rejection of `TARGET_RACE_CARD` before all
collaborators; malformed/noncanonical accessD rejection before all collaborators;
transport contradiction/failure and invalid strict-CP932/content/encoding/length/domain
inputs with no archive; archive failure propagation/no return; GET transport configuration
and raw-byte behavior unchanged; no package-root export or forbidden dependencies; and no
real capture.

## Stop Condition

Stop after the two documentation files are reviewed, one review commit is pushed, and no
production/test/archive/schema/migration or real-capture action has occurred.
