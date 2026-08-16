# Current Phase

## Status

`READY_FOR_REVIEW`

## Phase

`4C-2d3b1i6d1d5f1` — JRA accessD target prerequisites preparation.

Formal base: `776cd9123635eef3759284ff997a369857f3769e`.

Design reference inspected without merge or cherry-pick: `89239924213a1b8d2b13183155dc70d21a9344c1`.

Review branch: `review/4c-2d3b1i6d1d5f1-jra-accessd-target-prereq-prepare`.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

This is a design/investigation phase only. It authorizes no production code, tests,
capture, archive, schema, migration, or live official-response change.

## accessD Race Identity

`ACCESSD_ENDPOINT` is exactly `https://www.jra.go.jp/JRADB/accessD.html`.

The raw CNAME grammar is frozen as:

```text
pw01dde(?P<site>01|10)(?P<venue>0[1-9]|10)(?P<year>[0-9]{4})
(?P<meeting>0[1-9]|[1-9][0-9])(?P<day>0[1-9]|1[0-2])
(?P<race>0[1-9]|1[0-2])(?P<date>[0-9]{8})/(?P<tail>[0-9A-F]{2})
```

The concatenated expression is one ASCII token: there is no presentation
whitespace. `date` must be a real Gregorian date and its year must equal `year`.
`site` and `tail` are opaque URL material; neither contributes to race identity.
The identity is exactly:

```text
jra:race:<year>:<venue>:<meeting>:<day>:<race>
```

The future public parser is
`parse_jra_race_card_url_identity(value: str) -> JRAExternalRaceIdentity`. It must
validate a resolved canonical accessD URL and derive only the identity above. The
future canonicalizer accepts only the exact HTTPS host, exact `/JRADB/accessD.html`
path, one uppercase `CNAME` query key, one CNAME matching this grammar, and a raw
`%2F` delimiter representation; it renders exactly
`https://www.jra.go.jp/JRADB/accessD.html?CNAME=<CNAME-with-%2F>`. Alternate host,
path, query, CNAME spelling, delimiter, date, or case is rejected. Display text is
never an alternate identity source when this URL is available.

## accessD Trusted Capture Boundary

`ACCESSD_PAGE_KIND` is the new exact GET page kind `TARGET_RACE_CARD` with value
`target_race_card`. `ACCESSD_SUPPLIED_RESPONSE_TYPE` should reuse the existing
immutable `JRASuppliedOfficialResponse`, extended only to recognize the formal
accessD canonical URL; no duplicate supplied-byte type is justified. It remains
strict CP932 raw bytes with the actual supplied `observed_at`.

`ACCESSD_HTTP_METHOD = GET`; `ACCESSD_ENCODING = cp932` strict; and HTTP transport
must retain the formal GET byte-transport policy when a later capture phase is
approved. Existing v1 accessS/accessU and v2 accessO identities are frozen.

Current archive compatibility is **NO**: v1 accepts only accessS/accessU and v2
accepts only POST final-win odds. The narrow compatible future family is a separate
schema-v3 immutable `JRAOfficialTargetRaceCardResponseCapture`, with
`page_kind=TARGET_RACE_CARD`, `request_method=GET`, raw-byte SHA-256, canonical
accessD URL, actual requested/observed/stored timestamps, and identity:

```text
jra-capture-v3:SHA256(canonical JSON {
  canonical_source_url, observed_at_utc, page_kind: "target_race_card",
  response_sha256, schema_version: 3
})
```

This is the v1 identity material extended only with a new schema version and page
kind; it cannot alter any existing capture ID. `ACCESSD_ARCHIVE_COMPATIBILITY = NO`
and `ACCESSD_MIGRATION_REQUIRED = YES`: a dedicated v003 archive/migration PREPARE
must first freeze table/API family separation and fail-closed migration behavior.

## Row-Local Horse Identity and Target Fields

`ACCESSD_TO_ACCESSU_IDENTITY_STATUS = NOT_PROVEN`.

Read-only official page descriptions establish accessD as the race-card/horse-table
family and describe displayed single-win odds, but the evidence inspected in this
phase does not provide a preserved raw accessD entry row whose exact DOM anchor can
be verified as an official accessU URL. Consequently no selector for a stable horse
identity is frozen. A future implementation must require, in the same exact entry
row, one exact official accessU anchor whose canonical href is accepted by the
existing `parse_jra_horse_profile_url_identity(...)`; its resulting
`jra:horse:<10 ASCII digits>` is the only permitted `external_horse_id` proof.
Horse name, date of birth, trainer, pedigree, and fuzzy matching are forbidden.

For the same reason, the following accessD field selectors remain
`NOT_PROVEN`, not guessed: race date, scheduled start, place, distance, surface,
race name, race class, horse number, jockey, displayed single-win odds, and the
row-local accessU anchor. The follow-up must inspect a legally read-only, current
official accessD response and freeze exact semantic headings/row boundaries,
required unique-node cardinality, and exact direct text normalization before any
normalizer is written. Missing, duplicate, malformed, or structurally ambiguous
nodes must fail closed. Withdrawal, cancellation, scratch, and non-runner rows must
be classified from a separately proven exact official row shape; they may not be
silently omitted or converted into entries/odds.

`TARGET_ODDS_SOURCE_READY = NO`. accessD's displayed `単勝オッズ`, if later
structurally proven in an active row, is **target prediction odds**, not the
accessO historical-past-race final-odds domain. It is usable only with its actual
pre-cutoff observation; it cannot be reconstructed, selected as latest/nearest,
or replaced by race-final/settlement information.

## Complete Target Track Evidence

The neutral source contract fixes `TRACK_EVIDENCE_CARDINALITY = EXACTLY_ONE` and
requires nonempty `track_condition`. `MULTI_RESPONSE_TRACK_EVIDENCE_SUPPORTED = NO`.
accessD can at most be a conditional candidate for static race facts; no
single causally eligible official response has been proven here to provide every
required target field: `target_race_date`, `scheduled_start_at`, `place`,
`distance_m`, `track`, `track_condition`, `race_name`, and `race_class`.
Weather remains optional.

Therefore `SINGLE_RESPONSE_COMPLETE_TRACK_SOURCE = NOT_PROVEN`,
`COMPLETE_TARGET_TRACK_SOURCE = BLOCKED`, and
`TRACK_SOURCE_SCHEMA_CHANGE_REQUIRED = UNDECIDED`. No implementation may combine
accessD static facts with a second condition response under the current one-evidence
track contract, invent a condition, or use post-race/result evidence to backfill it.
If a future investigation cannot prove one eligible response, it must recommend a
separate provider-neutral multi-response track-evidence/schema PREPARE before any
JRA target-source implementation.

## Temporal and Snapshot Boundary

Source code preserves exact `observed_at`, may reject evidence later than the target
scheduled start when that value is formally available, and never invents or backdates
a timestamp. It does not decide information-cutoff eligibility unless an approved
API receives that cutoff. The snapshot boundary alone owns:

```text
observed_at <= captured_at <= information_cutoff <= scheduled_start_at
```

No later capture may impersonate historical prediction-time evidence.

## Readiness Matrix and Next Phase

```text
ACCESSD_IDENTITY_READY: YES — parser/canonicalizer contract frozen; not implemented.
ACCESSD_CAPTURE_DESIGN_READY: YES_FOR_DEDICATED_V003 — current archive is incompatible.
ACCESSD_TO_ACCESSU_IDENTITY_STATUS: NOT_PROVEN.
ACCESSD_SELECTORS_READY: NOT_PROVEN.
TARGET_ODDS_SOURCE_READY: NO.
SINGLE_RESPONSE_COMPLETE_TRACK_SOURCE: NOT_PROVEN.
TRACK_SOURCE_SCHEMA_CHANGE_REQUIRED: UNDECIDED.
TARGET_SOURCE_IMPLEMENTATION_READY: NO.
SNAPSHOT_ASSEMBLY_READY: NO.
```

The immediate recommended phase is a narrow accessD evidence investigation/capture
architecture PREPARE that obtains only read-only structural proof for the accessD
row, identity, selectors, withdrawal semantics, and a causal complete-track source.
If that proof still requires two track responses, the required predecessor is
`4C-2d3b1i6d1d5f1a — provider-neutral multi-response track evidence PREPARE`;
neither target-source normalizing nor snapshot assembly is then authorized.

## Stop Condition

Stop after the docs-only review commit is pushed. Do not implement accessD identity,
capture, target normalizers, target acquisition, multi-response track evidence,
snapshots, bridge, Predictor, or live capture.
