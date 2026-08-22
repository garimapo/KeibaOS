# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1c4c0b1` — JRA target navigation / locator discovery.

Formal base: `06b7d6df7ea57fab04a9abe70d67c580963ea3d2`.

Approved prepare: `b14aaf56f29fff717fea998ab9c412e354763d13`.

Review branch: `review/4c-2d3b1i6d1d5f1c4c0b1-jra-target-navigation-discovery`.

## Implemented Contract

The implementation is pure and closes the supplied-navigation chain:

```text
strict CP932 JRA root-menu bytes
-> exact meeting-selection POST locator
-> strict CP932 meeting-selection bytes
-> exact race-selection POST locator
-> strict CP932 race-selection bytes
-> exact canonical accessD target-card locator
```

`canonicalize_jra_race_card_href(value)` is the sole public raw-href bridge in the JRA
identity module. It accepts only direct official accessD material, resolves an approved
relative path against the fixed HTTPS JRA host, accepts one raw `/` or canonical `%2F`
CNAME delimiter, and produces a canonical `%2F` URL without changing its site variant or
opaque tail. It never constructs navigation material from an external race ID.

`jra_target_race_card_locator` owns frozen/slotted supplied response domains, the two
distinct immutable POST locator types, lexical builders/fingerprints, the strict raw
root quick-menu control proof, and meeting-to-race request discovery. The root domain is
fixed to `https://www.jra.go.jp/`, GET, and exact `cp932`; the meeting request grammar is
`\Apw01dli00/[0-9A-F]{2}\Z`. Both POST locators use lower-case SHA-256 of sorted,
compact, `ensure_ascii=True` JSON UTF-8 material, but remain distinct types.

`jra_target_race_card_discovery` owns only strict CP932 race-selection parsing. It
requires the exact race-list table and two matching direct anchors in every row, binds
all row identities to the supplied race-selection request’s year/venue/meeting/day, and
returns a frozen locator/provenance result only for one exact target. Missing target is a
dedicated unavailable error; malformed, ambiguous, duplicate, mismatched, or
site-variant-conflicting evidence is validation failure. No display-text identity, URL
synthesis, tail inference, raw target-card parsing, or neutral-record URL field exists.

No HTTP, archive, repository, SQLite, migration, filesystem, clock, live capture, or
real trusted capture was added. V004 capture work and live navigation composition remain
separate future phases.

## Allowed Files

```text
scripts/simulation/jra_official_identity.py
scripts/simulation/jra_target_race_card_locator.py
scripts/simulation/jra_target_race_card_discovery.py
tests/test_jra_official_identity.py
tests/test_jra_target_race_card_locator.py
tests/test_jra_target_race_card_discovery.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification

- Dedicated identity/locator/discovery: 23 passed.
- Related JRA target-source, accessU, historical collector, final-odds, capture, and live-capture tests: 95 passed.
- Dedicated plus related selection: 118 passed.
- Full suite: 2702 passed.
- Public-surface, forbidden-dependency, no-broad-catch, no-package-export, diff, and scope checks passed.

## Stop Condition

Stop after one pushed review commit for independent review. Do not implement target-race
selection capture v004, live navigation composition, accessD causal resolution, target
normalization, persistence, or a real trusted capture.
