# Current Phase

## Status

READY_FOR_REVIEW

## Phase

`4C-2d3b1i6d1d5f1b` — JRA accessD structural prerequisites preparation.

Formal base: `776cd9123635eef3759284ff997a369857f3769e`.

Design reference inspected without merge or cherry-pick:
`353c3259fab1ad17c97040deb9522fcd66431d1f`.

Review branch:
`review/4c-2d3b1i6d1d5f1b-jra-accessd-structure-prepare`.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

This is a read-only structural investigation. It authorizes no production code,
tests, trusted capture persistence, archive, migration, schema, target normalizer,
or live-capture implementation.

## Transient Official Investigation

One transient, unauthenticated read-only GET was made at
`2026-08-16T02:56:57.442112+00:00` to the official URL:

```text
https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0107202602020920260726%2FC0
```

The server returned HTTP 200, no `Content-Encoding`, `Content-Type: text/html`,
and 58,649 raw bytes. Strict `cp932` decoding succeeded. The response represented
the official expired-publication state for the 2026-07-26 Chukyo 9R card: it said
that publication of that race's card had ended and contained no entry table, no
accessU navigation, and no target race-field/odds structure. The raw bytes were
used transiently only and were neither persisted nor committed. This response is
not trusted historical evidence and cannot be used for a snapshot or source record.

## accessD Byte and Identity Contracts

```text
ACCESSD_HTTP_METHOD: GET
ACCESSD_CONTENT_TYPE: exact observed header text/html (no charset parameter)
ACCESSD_CHARSET: cp932
ACCESSD_STRICT_DECODE: PROVEN for the transient official response
ACCESSD_CAN_REUSE_JRA_SUPPLIED_RESPONSE: YES_AFTER_ACCESSD_CANONICAL_URL_RECOGNITION
```

`JRASuppliedOfficialResponse` already has the correct immutable raw-byte, strict
CP932, and actual-observation shape, but its current URL allowlist recognizes only
accessS/accessU. A future approved capture/domain phase must add only the formal
accessD canonical URL recognition before that type can receive accessD evidence.

The exact endpoint remains `https://www.jra.go.jp/JRADB/accessD.html`. Its raw
CNAME grammar is:

```text
pw01dde(?P<site>01|10)(?P<venue>0[1-9]|10)(?P<year>[0-9]{4})
(?P<meeting>0[1-9]|[1-9][0-9])(?P<day>0[1-9]|1[0-2])
(?P<race>0[1-9]|1[0-2])(?P<date>[0-9]{8})/(?P<tail>[0-9A-F]{2})
```

The displayed lines are one concatenated ASCII token. The date must be real and
share its year with `year`. Only `year`, `venue`, `meeting`, `day`, and `race`
form the existing formal identity:

```text
jra:race:<YYYY>:<VV>:<MM>:<DD>:<RR>
```

The future `parse_jra_race_card_url_identity(value: str) ->
JRAExternalRaceIdentity` must accept only the exact HTTPS host, accessD path,
uppercase single `CNAME` key, canonical CNAME grammar, and raw `%2F` delimiter,
then render the same canonical URL. URL identity is authoritative; display text is
not an alternative race-identity source.

## Row-Local Identity, Selectors, and Non-Runners

`ACCESSD_TO_ACCESSU_IDENTITY_STATUS = NOT_PROVEN`.

The actual current retrieval contained no target entry row, so no exact row-local
horse anchor, href, or selector was available to inspect. It is therefore forbidden
to claim the required chain:

```text
exact accessD entry row
-> one row-local official accessU href
-> parse_jra_horse_profile_url_identity(...)
-> jra:horse:<10 ASCII digits>
```

All proposed selectors remain `NOT_PROVEN`: race date, scheduled start, place,
distance, surface, race name, race class, horse number, jockey, displayed single-win
odds, and row-local accessU anchor. A future investigation must obtain a currently
published official accessD card and freeze the raw response's exact row selector,
anchor selector and canonical href form, semantic heading/cardinality rules, and
direct-text parsing. Missing, duplicate, or ambiguous nodes must fail closed.

`ACCESSD_NON_RUNNER_SEMANTICS_READY = NO`. The expired response contained no
entry-state layout. Withdrawal, scratch, cancellation, exclusion, and non-runner
states remain unsupported until a direct official active-row structure or official
documentation proves each exact state. No row may be silently omitted.

Consequently `TARGET_ODDS_SOURCE_READY = NO`: the expected accessD single-win odds
cannot be target evidence until its direct positive finite value, exact horse-row
binding, and actual response observation are all proven. It remains a prediction-time
fact, never accessO past-race final odds, a settlement value, or a latest/nearest
substitute.

## One-Response Target Track Evidence

The current neutral contract remains:

```text
TRACK_EVIDENCE_CARDINALITY = EXACTLY_ONE
MULTI_RESPONSE_TRACK_EVIDENCE_SUPPORTED = NO
```

The live expired accessD response cannot establish a complete target track. No one
causally eligible official response is proven to provide all required values:
`target_race_date`, `scheduled_start_at`, `place`, `distance_m`, `track`,
`track_condition`, `race_name`, and `race_class`. Weather is optional. In
particular, this investigation found no admissible proof of a target
`track_condition` in the same single response.

```text
SINGLE_RESPONSE_COMPLETE_TRACK_SOURCE = NOT_PROVEN
TRACK_SOURCE_SCHEMA_CHANGE_REQUIRED = YES
RECOMMENDED_TRACK_PHASE = 4C-2d3b1i6d1d5f1a
```

No implementation may combine accessD static facts with a second response or invent
condition data. Phase f1a must first decide provider-neutral multi-response track
evidence/schema evolution.

## v003 Capture Readiness

```text
ACCESSD_PAGE_KIND: TARGET_RACE_CARD (target_race_card)
ACCESSD_SUPPLIED_RESPONSE_TYPE: JRASuppliedOfficialResponse after URL recognition
ACCESSD_CAPTURE_SCHEMA_VERSION: 3
ACCESSD_CAPTURE_IDENTITY:
  jra-capture-v3:SHA256(canonical JSON {
    canonical_source_url, observed_at_utc, page_kind: "target_race_card",
    response_sha256, schema_version: 3
  })
ACCESSD_MIGRATION_REQUIRED: YES
ACCESSD_CAPTURE_DESIGN_READY: YES_FOR_DEDICATED_V003
```

Current schema-v1 capture identity/semantics for accessS/accessU and schema-v2
identity/semantics for POST accessO are immutable. A later v003 capture/archive
PREPARE must define its dedicated storage/API family and migration before code.

## Readiness Matrix and Stop Condition

```text
ACCESSD_IDENTITY_READY: YES — design only.
ACCESSD_BYTE_CONTRACT_READY: YES — GET/text-html/strict-CP932 observed directly.
ACCESSD_CAPTURE_DESIGN_READY: YES_FOR_DEDICATED_V003.
ACCESSD_TO_ACCESSU_IDENTITY_STATUS: NOT_PROVEN.
ACCESSD_SELECTORS_READY: NOT_PROVEN.
ACCESSD_NON_RUNNER_SEMANTICS_READY: NO.
TARGET_ODDS_SOURCE_READY: NO.
SINGLE_RESPONSE_COMPLETE_TRACK_SOURCE: NOT_PROVEN.
TRACK_SOURCE_SCHEMA_CHANGE_REQUIRED: YES.
TARGET_SOURCE_IMPLEMENTATION_READY: NO.
SNAPSHOT_ASSEMBLY_READY: NO.
```

The active-card structural prerequisite is blocked by the current official endpoint
returning only an expired-publication response. Do not implement target sources,
accessD capture/migration, multi-response track evidence, snapshot assembly,
historical acquisition, bridge, Predictor, or real trusted capture in this phase.
