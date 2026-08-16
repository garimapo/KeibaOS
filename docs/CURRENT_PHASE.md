# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c2` — JRA accessD live capture.

Formal base: `94ceb4742e7fec6b758d1ceded2ffecc422c873f`.

Approved prepare: `e34e7139c0a5ed943897fd1638d6287a2b38b433`.

Review branch: `review/4c-2d3b1i6d1d5f1c2-jra-accessd-live-capture`.

## Allowed Files

```text
scripts/simulation/jra_official_response_live_capture.py
tests/test_jra_official_response_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Implemented Contract

`JRAOfficialLiveResponseCaptureService` now has the exact dedicated method:

```python
capture_target_race_card_response(
    self,
    *,
    response_url: str,
) -> JRAOfficialTargetRaceCardResponseCapture
```

It first uses the existing v3-only canonical accessD boundary. Invalid,
noncanonical, or wrong-family input consequently fails before a clock sample,
transport request, or archive write. It then performs exactly:

```text
v3 canonical accessD validation
-> requested_at clock
-> existing GET transport.fetch
-> exact transport result and URL check
-> observed_at clock
-> stored_at clock
-> JRAOfficialTargetRaceCardResponseCapture
-> save_target_race_card_capture
-> return capture
```

The new path uses only v3 domain/archive operations and preserves actual clock
samples without caller timestamps or backdating. `capture_response` remains
accessS/accessU-only and rejects `TARGET_RACE_CARD` before all collaborators;
the v2 final-odds POST method and existing GET transport configuration remain
unchanged.

## Required Verification

Run the dedicated live-capture suite, related JRA identity/capture/archive suites,
the complete pytest suite, package/public-surface and forbidden-dependency checks,
and `git diff --check`. No real trusted capture, target parser/normalizer, source
records, snapshots, schema/migration/repository change, bridge, Predictor, or
package-root export is authorized.

## Stop Condition

Stop after one review commit is pushed for independent review.
