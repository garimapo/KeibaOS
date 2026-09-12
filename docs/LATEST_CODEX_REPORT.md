# Latest Codex Report

## POST_V0_8_DAILY_REPLAY_44 — NAR Race-Entry Status Raw Capture Bundle Implementation

Status: `APPROVED_FOR_COMMIT`
Formal State: `FORMALLY_COMPLETE`
Base: `972a1fb201ad360d1c729b120d5ac10aa1556a42`
Branch: `feature/post-v0.8-daily-replay`

Implementation review verdict: `PASS_FOR_INTEGRATION`.

Phase44 is formally integrated within its exact four-file scope. No live HTTP, parsing, future-information or eligibility inference, reconciliation, persistence, fixture publication, or subsequent-phase work occurred.

### Implemented boundary

`scripts/simulation/nar_race_entry_status_raw_capture.py` implements the complete frozen public API: exact race/day scopes, DebaTable and RaceList page kinds, derived request identities, raw HTTP response and immutable capture evidence, closed two-document bundle, transport/clock protocols, concrete requests transport, request builder, bundle acquisition, and the five-class exception hierarchy.

DebaTable uses ordered `k_babaCode`, `k_raceDate`, `k_raceNo`. RaceList uses ordered `k_raceDate`, `k_babaCode`, is venue-day scoped, and contains no `k_raceNo` or fake null race number. Request, capture, and bundle identities use the approved literal canonical JSON, UTC six-digit `Z` timestamps, lowercase SHA-256 digests, and exact prefixes:

```text
nar-race-entry-status-request-v1:
nar-race-entry-status-capture-v1:
nar-race-entry-status-raw-bundle-v1:
```

The concrete transport creates one fresh `requests.Session` per document, disables environment/session inheritance and retries, uses exact HTTPS GET headers/options, disables redirects and transfer decoding, and reads raw bytes in bounded chunks. Raw Content-Length multiplicity comes only from `response.raw.headers.getlist`; duplicate equal or unequal values, unavailable multiplicity, noncanonical text, and byte-length mismatch fail closed. Only the six approved metadata fields survive. Low-level acquisition and cleanup failures map to the frozen hierarchy.

Acquisition performs DebaTable then RaceList, at most two GETs, and exactly six injected clock samples on success. Deba failure suppresses RaceList; later failure never exposes an authoritative partial bundle. Individual timestamps remain authoritative and the bundle makes no atomic-provider-state claim.

### Verification

```text
dedicated Phase44: 91 passed
dedicated Phase44, ResourceWarning as error: 91 passed
Phase36 / Phase32 capture-acquisition: 40 passed, 48 subtests passed
Phase38 / Phase40 fixture-parser: 56 passed
Phase30 ranking probability: 24 passed, 24 subtests passed
Phase25/27/28 daily replay core: 51 passed, 23 subtests passed
all NAR: 523 passed, 584 subtests passed (31 paths)
full pytest: 3,597 passed, 2,841 subtests passed
deterministic identity audit: PASS
compile/static forbidden-boundary audit: PASS
git diff --check: PASS
```

The frozen all-NAR wildcard did not expand when passed literally to pytest on Windows. The same two frozen filename patterns were then explicitly expanded by PowerShell to 31 paths; that complete scope passed. The production module contains no BeautifulSoup/DOM/body-semantic parser, filesystem/database writer, current wall-clock sampling, alternate network client, or JRA dependency.

### State and Git gate

Phase41 remains `DESIGN_BLOCKED`. Raw capture alone does not establish market eligibility. Both dependencies remain `OPEN`:

```text
COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE
NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE
```

The exact changed paths are:

```text
scripts/simulation/nar_race_entry_status_raw_capture.py
tests/test_nar_race_entry_status_raw_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The integration commit is restricted to the exact four paths above. Phase32/36/40, fixtures, manifest, `.gitattributes`, `database/**`, and `logs/**` remain excluded. Commit, tree, parent, and remote verification are captured in the integration result. Blockers: none. Stop after formal integration; do not begin another phase.
