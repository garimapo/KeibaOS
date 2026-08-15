# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1d5c2` — JRA accessS final-odds locator extraction implementation.

Formal base: `d53d2df5c7f9aee91b9cbea0dda07145aefb3acf`.

Approved PREPARE: `2934b663dcdf962ccb0576d6440dc941b590716a`.

Review branch: `review/4c-2d3b1i6d1d5c2-jra-accesso-locator`.

## Implemented Boundary

Added the pure identity-domain builder:

```python
build_jra_final_win_odds_request_locator(
    *,
    cname: str,
) -> JRAOfficialFinalWinOddsRequestLocator
```

It accepts only the formal raw accessO CNAME grammar, fixes the formal
`https://www.jra.go.jp/JRADB/accessO.html` endpoint, and uses the existing private identity/fingerprint primitives to
construct the existing immutable locator. It does not parse HTML or duplicate the canonical request-fingerprint
algorithm. Existing identity behavior, including the pinned known CNAME fingerprint, remains unchanged.

Added the pure extractor:

```python
extract_jra_final_win_odds_request_locator(
    *,
    race_result_response: JRASuppliedOfficialResponse,
) -> JRAOfficialFinalWinOddsRequestLocator
```

Its only module-defined public names are
`JRAFinalWinOddsRequestLocatorExtractionError`,
`JRAFinalWinOddsRequestLocatorExtractionValidationError`, and the function. It accepts only an exact accessS
`JRASuppliedOfficialResponse`, strictly decodes supplied CP932 bytes, validates the response URL with
`parse_jra_result_url_identity(...)`, and changes neither bytes nor timestamps.

The sole accepted official navigation is exactly one `オッズ` control with `href="#"` at:

```text
div#race_result.mt20
> div.race_result_unit
> table.basic.narrow-xy.striped
> caption > div.race_header > div.right > div.race_related_link
> ul > li > a.btn-def.btn-sm.blue.btn-block
```

Its direct source `onclick` must be the approved single-quoted
`return doAction('/JRADB/accessO.html', '<raw-cname>');` form. Only explicitly approved ASCII presentation
whitespace is accepted. The extractor requires the raw source attribute spelling as well as the parsed DOM value, so
HTML entity quote recovery cannot turn an altered navigation into valid evidence. It rejects double quotes, escapes,
concatenation, extra script/arguments, altered endpoints, percent-encoded/invalid CNAMEs, duplicate controls, and all
other ambiguity. Generic page-menu odds controls and `commForm01` hidden CNAME transport plumbing are never scanned
as candidates.

The extractor calls only the public builder and requires the resulting locator's race identity to equal the supplied
accessS URL's parsed race identity. It never synthesizes a locator from accessS CNAME, race ID, date, venue, or race
number. It has no HTTP, archive, repository, filesystem, SQLite, clock, environment, random, subprocess, capture,
accessO POST, normalizer, discovery, orchestration, or bridge ownership. No package-root export is added.

The raw-onclick proof is bound to the selected DOM candidate, not a page-global substring: a quote-aware raw HTML
token scan skips comments and script bodies, retains raw anchor start tags in document order, and verifies count/order
agreement with the parsed anchors. The unique selected result-header anchor is located by identity in that parsed
sequence; only its corresponding raw start tag may contain exactly one literal lowercase `onclick` attribute whose raw
double-quoted value equals the approved parsed invocation. Entity-encoded selected values (`&#39;`, `&#x27;`, or `&apos;`)
therefore fail even when comments, scripts, generic navigation, hidden forms, or another anchor contain the decoded
text.

## Allowed Files

```text
scripts/simulation/jra_official_identity.py
scripts/simulation/jra_final_win_odds_request_locator.py
tests/test_jra_official_identity.py
tests/test_jra_final_win_odds_request_locator.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification

Fresh Python 3.14.5 / pytest 8.3.5 verification passed: identity and locator dedicated suites (17 tests), JRA
capture/archive/live plus d1d5a/d1d5b3, NAR, and provider-neutral source/snapshot/builder regressions (139 tests),
and the full suite (2,597 tests). The public-surface/purity tests pin the builder, exact extractor API, no package-root
export, and forbidden dependency boundary. Final diff, scope, unchanged-production, version, and status checks are
required before review publication.

## Stop Condition

Create and push exactly one review commit: `feat: extract JRA final-odds request locator`. Do not formally integrate,
perform real accessO capture, implement collection/orchestration, synthesize a CNAME, modify discovery or normalizer,
implement a NAR/JRA bridge, or connect Predictor. Stop for independent review.
