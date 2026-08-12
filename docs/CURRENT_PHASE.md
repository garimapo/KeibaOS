# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1b1` — JRA race native-key and canonical result-URL investigation.

Formal base: `04c0fbcad2ea13b2e325e795e6de022718edb01a`.

Review branch: `review/4c-2d3b1i6d1b1-prepare`.

Parent investigation: `1238018a41fd3336663e31a856f8887d0bb6d45c`.

## Frozen Investigation Conclusions

```text
JRA_RACE_NATIVE_KEY_STATUS = PROVEN
JRA_VENUE_CODE_MAPPING_STATUS = PROVEN_ALL_10_CENTRAL_VENUES
JRA_VENUE_CODE_GRAMMAR = (?:0[1-9]|10)
JRA_MEETING_NUMBER_GRAMMAR = (?:0[1-9]|[1-9][0-9])
JRA_MEETING_DAY_GRAMMAR = (?:0[1-9]|1[0-2])
JRA_RACE_NUMBER_GRAMMAR = (?:0[1-9]|1[0-2])
JRA_RACE_NATIVE_KEY_GRAMMAR = [0-9]{4}:(?:0[1-9]|10):(?:0[1-9]|[1-9][0-9]):(?:0[1-9]|1[0-2]):(?:0[1-9]|1[0-2])
JRA_STABLE_RACE_ID = jra:race:<YYYY>:<VV>:<MM>:<DD>:<RR>
JRA_RACE_KEY_RECONSTRUCTION = IDENTITY_PROVEN_CAPTURE_CNAME_NOT_RECONSTRUCTABLE
SAME_RACE_DIFFERENT_CNAME_FORM = PROVEN
SAME_RACE_ACCESS_S_CNAME_COUNT = 2
ACCESS_S_VIEW_SELECTOR_IDENTITY_STATUS = NOT_ENTITY_IDENTITY
ACCESS_S_TAIL_IDENTITY_STATUS = NOT_ENTITY_IDENTITY_OPAQUE_NAVIGATION_MATERIAL
```

Official `accessS` and `accessD` pages prove that the stable native race identity is the lexical five-token
tuple `YYYY:VV:MM:DD:RR`: JRA racing year, JRA central venue code, meeting number, meeting day number, and
race number. `DD` is a meeting day, not a calendar day of month. Preserve every token lexically; do not parse
through `int()` or strip zeroes. The calendar race date is not part of canonical entity identity because the
proven provider tuple identifies the physical race; it remains an independent mandatory official consistency
cross-check and is not assumed mathematically reconstructable from the tuple.

```text
RACE_DATE_IDENTITY_COMPONENT = NO
RACE_DATE_VALIDATION_CROSSCHECK = REQUIRED
LEXICAL_IDENTITY_VALIDITY = STRICT_ASCII_TOKEN_DOMAIN_ONLY
PHYSICAL_RACE_EXISTENCE = SEPARATE_OFFICIAL_PAGE_VALIDATION
```

The pure future parser must reject invalid token width, zeroes, signs, whitespace, Unicode digits, missing
zero padding, extra separators, venue `00`/`11`/`99`, meeting `00`, meeting day `00`/`13`/`99`, and race
`00`/`13`/`99`. A lexically valid key does not itself prove that a physical race existed.

For the same 2025-09-13 Nakayama 4R, official accessS CNAMEs with `sde01` and `sde10` prefixes and different
opaque tails rendered the same race, while an accessD CNAME rendered the same race too. The selector and tail
therefore identify navigation/capture context, never the race entity. A complete raw CNAME is forbidden as
`external_race_id` or as a provider-record identity.

```text
01 = 札幌
02 = 函館
03 = 福島
04 = 新潟
05 = 東京
06 = 中山
07 = 中京
08 = 京都
09 = 阪神
10 = 小倉
MEETING_NUMBER_ZERO = REJECTED
MEETING_NUMBER_UPPER_BOUND = NOT_PROVEN_PROVIDER_WIDE
MEETING_DAY_ZERO_OR_ABOVE_12 = REJECTED
RACE_NUMBER_ZERO_OR_ABOVE_12 = REJECTED
DATE_VENUE_RACE_NO_LOOKUP_UNIQUENESS = NOT_PROVEN_AS_A_GENERAL_DISCOVERY_CONTRACT
```

Official JRA/JRADB evidence establishes the complete central-venue map above. No code outside `01` through `10`
is accepted. The meeting-number grammar is deliberately lexical-positive two-digit syntax, not a claim that a
meeting `99` exists. Official programs establish meeting days and races through 12; only `01` through `12` are
currently supported for those two tokens.

## Resolved accessS Capture URL

The capture URL is a validated resolved URL only; it is not reconstructable from `jra:race`. Accept HTTPS,
`www.jra.go.jp`, exact path `/JRADB/accessS.html`, and exactly one `CNAME` parameter. Reject credentials,
fragments, whitespace/control characters, malformed percent encoding, `+`, duplicate or unknown query keys, and
double decoding. Both raw `/` and single `%2F` input forms were officially observed; canonical rendering uses an
uppercase `%2F`. Preserve uppercase two-hex tail text and the supplied official host. Do not synthesize a CNAME
from the stable key.

```text
CANONICAL_ACCESS_S_URL = https://www.jra.go.jp/JRADB/accessS.html?CNAME=<resolved-CNAME-with-uppercase-%2F>
```

## Horse Identity and NAR Bridge

```text
JRA_HORSE_NATIVE_KEY_STATUS = PROVEN_FOR_ACCESSU_PROFILE_LINKS
JRA_HORSE_NATIVE_KEY_GRAMMAR = [0-9]{10}
JRA_STABLE_HORSE_ID = jra:horse:<10-digit>
ACCESS_S_ROW_TO_STABLE_HORSE_ID = PROVEN_FOR_OFFICIAL_ROW_LOCAL_ACCESSU_ANCHOR
NAR_JRA_PLACE_DISPLAY_GRAMMAR = ^Ｊ中山$ PROVEN_FOR_OBSERVED_FIXTURE_ONLY
NAR_JRA_RACE_DATE_EQUIVALENCE = PROVEN_FOR_2025-09-13_Ｊ中山_R4_ONLY
NAR_JRA_RACE_NO_EQUIVALENCE = PROVEN_FOR_2025-09-13_Ｊ中山_R4_ONLY
NAR_JRA_EVENT_TO_JRA_RESULT_RESOLUTION = NOT_PROVEN_AS_A_GENERAL_OFFICIAL_DISCOVERY_CONTRACT
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
```

The existing NAR JRA event fixture is equivalent to the inspected JRA Nakayama 4R only as one observed case.
It does not prove a general NAR-to-JRA race resolver, and it does not bridge an NAR lineage identity to a JRA
accessU profile key. Horse-name linkage remains forbidden.

## Future Identity Shapes

```text
external_race_id = jra:race:<YYYY>:<VV>:<MM>:<DD>:<RR>
external_entry_id = <external_race_id>:entry:<positive canonical decimal horse_no>
external_horse_id = jra:horse:<10 ASCII digits>
provider_record_id = jra:result:<YYYY>:<VV>:<MM>:<DD>:<RR>:horse:<10 ASCII digits>
```

These are pure future identity contracts only. No JRA parser, normalizer, capture, network request, fixture,
schema, migration, builder, or package export is approved in this phase. CP932 handling remains frozen pending a
separate response-decoding/capture contract; it must not be guessed from this URL investigation.

## Readiness and Recommended Next Work

```text
JRA_IDENTITY_IMPLEMENTATION_READY = YES
MIXED_HISTORY_COLLECTION_READY = NO
RECOMMENDED_NEXT_PHASE = 4C-2d3b1i6d1b2 — NAR-lineage to JRA-stable-horse bridge investigation PREPARE
```

The smallest possible pure identity implementation, if separately authorized, would be limited to
`scripts/simulation/jra_official_identity.py`, `tests/test_jra_official_identity.py`, and these documentation
files. It must not perform HTTP inside the identity parser. General JRA historical-race discovery needs a separate
future boundary and cannot be inferred from date/place/R text.

## Allowed Files for This PREPARE

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

This is documentation-only PREPARE work. Stop for independent design review; do not implement identity parsing,
NAR/JRA bridging, JRA collection, capture, CP932 decoding, fixtures, or any next phase.
