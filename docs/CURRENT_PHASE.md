# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c0b3` — JRA live target-navigation composition.

Formal base: `b506973ac7718126c24795af2d457b721453cc90`.

Approved prepare: `30683b3c28f3d9a39543109c3d8c775419536f9d`.

Review branch:
`review/4c-2d3b1i6d1d5f1c4c0b3-jra-live-target-navigation`.

## Implemented Contract

`JRAOfficialLiveResponseCaptureService.capture_target_race_navigation(...)` now composes
the fixed root GET, response-derived meeting POST, response-derived race-selection POST,
schema-v4 persistence, and pure target-card locator discovery. The method validates the
canonical external race ID before every clock, transport, or archive interaction. It never
derives a CNAME, opaque tail, site variant, or URL from that ID.

The frozen/slotted `JRATargetRaceNavigationCaptureResult` retains only the exact
`JRATargetRaceCardDiscovery` and the saved v4 capture ID. Its custom construction accepts
the exact v4 capture and verifies request-locator, response-SHA, and observation-time
lineage before retaining that ID.

Navigation requests are explicit prepared requests with identity encoding, the existing
User-Agent, one exact form field for POST, and no Cookie, Referer, or Origin. The session
is used only for adapters and connection pooling: a real populated `requests.Session`
cookie jar before root, meeting, and race-selection requests cannot affect any outgoing
formal navigation request. A future cookie requirement fails closed pending review of
request identity.

Root and meeting supplied responses are operational only. The race-selection response is
constructed as the frozen v4 capture, saved before target-card discovery, and discovery
uses `capture.to_supplied_official_response()` only after save succeeds. No immediate
reload, fallback, retry, target-card GET, schema/migration/repository change, or live
capture fixture is introduced.

## Allowed Files

```text
scripts/simulation/jra_official_response_live_capture.py
tests/test_jra_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification

Offline live-capture tests cover the exact public surface, canonical target-ID validation
before collaborators, response-derived locators, strict CP932 domains, v4 archive-before-
discovery behavior, result lineage, clock ordering, and cookie-/Referer-/Origin-free root
and POST requests. Existing capture, final-odds, and target-card paths remain covered.

Focused live suite: **23 passed**. Related locator/discovery/capture/repository suite:
**33 passed**. Full suite: **2718 passed**. `git diff --check` passed.

No real HTTP, read-only live observation, or trusted capture was performed.

## Stop Condition

Stop after this exact four-file review change is committed and pushed for independent
review. Do not integrate the formal branch or begin c4c.
