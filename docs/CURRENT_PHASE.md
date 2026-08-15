# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5c1` — JRA accessS -> accessO final-win-odds locator extraction PREPARE.

Formal base: `d53d2df5c7f9aee91b9cbea0dda07145aefb3acf`.

Review branch: `review/4c-2d3b1i6d1d5c1-jra-accesso-locator-prepare`.

## Objective and Boundary

Freeze a pure extractor that consumes one exact trusted JRA accessS `RACE_RESULT` supplied response and returns the
already-formal `JRAOfficialFinalWinOddsRequestLocator`. It closes only the evidence-navigation boundary:

```text
JRA historical event reference
-> trusted accessS response for its canonical result URL
-> locator extracted from that response's official final-win-odds control
-> trusted accessO response
-> existing d1d5a normalizer
```

It is not acquisition, archive lookup, discovery, accessO POST transport, normalization, or orchestration. It must not
synthesize a CNAME from race identity, accessS CNAME, date, venue, meeting, day, race number, or an opaque tail.

## Frozen Proposed API

The next implementation must provide exactly:

```python
extract_jra_final_win_odds_request_locator(
    *,
    race_result_response: JRASuppliedOfficialResponse,
) -> JRAOfficialFinalWinOddsRequestLocator
```

The parser module owns a closed extraction parsing boundary. It requires
`type(race_result_response) is JRASuppliedOfficialResponse`, strict-decodes the supplied exact CP932 bytes once for
HTML parsing, and first validates the URL through `parse_jra_result_url_identity(...)`. A supplied accessU response,
malformed URL, malformed CP932, or malformed DOM is an extraction validation failure. No target record is required:
the exact accessS response identity and actual official navigation fully determine and cross-check the locator.

The function has no HTTP, archive, repository, SQLite, filesystem, environment, clock, randomness, retry, sleep, or
subprocess ownership. It must not re-encode supplied bytes and it does not compute response SHA or alter timestamps.

## Official Navigation Contract

Read-only official accessS inspection established the race-specific final-odds control in the result structure. The
required container is the unique result-table header path:

```text
div#race_result.mt20
> div.race_result_unit
> table.basic.narrow-xy.striped
> caption
> div.race_header
> div.right
> div.race_related_link
> ul > li
> a.btn-def.btn-sm.blue.btn-block
```

The unique control's normalized visible label is exactly `オッズ`; its `href` is exactly `#`; and its direct
`onclick` is the official doAction navigation. The observed official semantic form is:

```javascript
return doAction('/JRADB/accessO.html', 'pw151ou10...Z/HH');
```

The extraction grammar accepts only that direct `return doAction(` invocation with the exact relative action
`/JRADB/accessO.html`, one ordinary unescaped single-quoted raw CNAME argument, and the terminating `);`. It permits
only ASCII presentation whitespace around the JS punctuation already present in that grammar. Backslash escapes,
double quotes, entity recovery, percent-encoded CNAME material, concatenation, arbitrary script execution, alternate
action syntax, and generic form fields are not accepted.

The page-wide navigation menu contains generic `accessO` controls for other odds products (for example a generic
`pw15oli...` action). Those controls are outside the required result-table-caption path and must never be candidates.
The page's generic hidden `form#commForm01 input[name=cname]` is transport plumbing, not final-odds evidence, and
must not be used as a fallback. The direct result-header control is the sole approved source.

The raw CNAME is retained exactly as extracted: it contains raw `/`, never `%2F`, and its formal grammar retains
the uppercase two-hex opaque tail. The extractor never lowercases, percent-decodes, or repairs it.

## Endpoint, Identity, and Fingerprint

The relative action must resolve on the formal JRA origin to exactly:

```text
https://www.jra.go.jp/JRADB/accessO.html
```

No alternate host, path, query, fragment, or relative navigation is accepted. The existing formal
`JRAOfficialFinalWinOddsRequestLocator` then validates the raw CNAME and derives its race identity. The extractor
requires:

```text
locator.external_race_identity
== parse_jra_result_url_identity(race_result_response.response_url)
```

Any mismatch fails closed. Visible race-heading parsing remains d1d5a normalizer responsibility; this phase validates
official navigation and provider-native identity only, without duplicating d1d5a display parsing.

`JRAOfficialFinalWinOddsRequestLocator` deliberately requires a canonical request fingerprint while its fingerprint
algorithm is private to `jra_official_identity.py`. The next implementation therefore requires one narrow new public
identity-domain builder:

```python
build_jra_final_win_odds_request_locator(
    *,
    cname: str,
) -> JRAOfficialFinalWinOddsRequestLocator
```

It accepts only raw CNAME material, fixes the existing formal accessO endpoint, derives the race identity with the
existing private formal grammar, and computes the existing private canonical request fingerprint. The extractor must
call this builder; it must not duplicate fingerprint logic or call private identity helpers. This is the minimal API
change: locating HTML in `jra_official_identity.py` would introduce a capture-domain dependency/cycle, while exposing
the builder preserves lexical/request identity ownership there.

## Ambiguity and Failure Policy

Require exactly one complete result-caption control matching the structural selector, label, and invocation grammar.
Fail closed for no candidate, duplicate candidate (including byte-identical duplicates), multiple candidate
actions/CNAMEs, a wrong or duplicate endpoint, malformed/missing `onclick`, unsupported quoting/escaping, malformed
CNAME, selector/container contradiction, or accessS/accessO race-identity disagreement. No first-match, generic
odds-control, form-field, URL, race-ID, or accessS-CNAME fallback is allowed.

The locator applies only after an actual JRA historical start has supplied trusted accessS result evidence. It does not
create a locator for `NON_JRA_ACTUAL_START`, `PROVEN_NON_START`, or an unsupported start whose settlement path has
not later been formally approved.

## Causality and Compatibility

Extraction carries no timestamp and does not backdate anything. Causality remains with the supplied accessS
`observed_at` and the later accessO supplied response's `observed_at`; future orchestration must establish both
against the target information cutoff. Current inspection establishes parser semantics only and cannot prove historical
availability.

Keep d1d5a normalizer, d1d5b3 discovery, JRA capture/domain/archive/live behavior, NAR production, neutral evidence,
source/snapshot schemas (`4`), global migrations (`14`), JRA capture migrations (`1, 2`), package exports, and
bridge status unchanged. `NAR_LINEAGE_TO_JRA_HORSE_ID_LINK` remains `NOT_PROVEN`;
`MIXED_HISTORY_COLLECTION_READY` remains `NO`.

## Recommended Implementation Scope

Recommended next phase: `4C-2d3b1i6d1d5c2` — JRA accessS final-odds locator extraction implementation.

Exact recommended allowed files:

```text
scripts/simulation/jra_official_identity.py
scripts/simulation/jra_final_win_odds_request_locator.py
tests/test_jra_official_identity.py
tests/test_jra_final_win_odds_request_locator.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The dedicated tests must use minimal synthetic strict-CP932 accessS snippets and cover the exact result-caption control,
raw-slash/percent boundary, uppercase tail, formal fingerprint, response type/CP932/accessS validation, missing and
duplicate controls, generic-menu exclusion, wrong endpoint, malformed JS/CNAME, race mismatch, no synthesis, pure
determinism, forbidden dependencies, and no package-root export.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Create and push exactly one documentation review commit: `docs: prepare JRA final-odds locator extraction`. Do not
implement the extractor or builder, modify production/tests, acquire or archive official responses, perform accessO
POST, implement orchestration, create a bridge, or connect Predictor. Stop for independent review.
