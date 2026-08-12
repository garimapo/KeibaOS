# Current Phase

## Status

READY_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1b3` — pure JRA official race/horse identity implementation.

Formal base: `04c0fbcad2ea13b2e325e795e6de022718edb01a`.

Implementation review branch: `review/4c-2d3b1i6d1b3-implementation`.

Approved race-identity design: `9802d37cb443c6990cacef6c4cb5650273e145b1`.

Approved bridge design: `dd87ffabd831fd9cfcf483260bce23b596511145`.

## Implemented Pure Identity Contract

```text
JRA_IDENTITY_MODULE = IMPLEMENTED_FOR_REVIEW
JRA_RACE_NATIVE_KEY_STATUS = PROVEN
JRA_RACE_NATIVE_KEY_GRAMMAR = [0-9]{4}:(?:0[1-9]|10):(?:0[1-9]|[1-9][0-9]):(?:0[1-9]|1[0-2]):(?:0[1-9]|1[0-2])
JRA_STABLE_RACE_ID = IMPLEMENTED
JRA_STABLE_HORSE_ID = IMPLEMENTED
JRA_STABLE_ENTRY_ID = IMPLEMENTED
JRA_PROVIDER_RECORD_ID = IMPLEMENTED
ACCESS_S_ALIAS_COLLAPSE = PASS
ACCESS_U_ALIAS_COLLAPSE = PASS
PHYSICAL_RACE_EXISTENCE = SEPARATE_OFFICIAL_PAGE_VALIDATION
```

`scripts/simulation/jra_official_identity.py` defines exactly the approved public API:

```text
JRAOfficialIdentityError
JRAOfficialIdentityValidationError
JRAExternalRaceIdentity
JRAExternalHorseIdentity
parse_jra_external_race_id
parse_jra_external_horse_id
parse_jra_result_url_identity
parse_jra_horse_profile_url_identity
build_jra_external_entry_id
build_jra_provider_record_id
```

The frozen/slotted race identity retains five canonical lexical strings: JRA racing year, venue code, meeting
number, meeting day, and race number. It emits only `jra:race:<YYYY>:<VV>:<MM>:<DD>:<RR>`. Venue codes are
`01` through `10`; meeting numbers use positive two-digit lexical syntax without claiming a provider-wide upper
bound; meeting days and race numbers are exactly `01` through `12`. No integer conversion, Unicode digits, signs,
whitespace, aliases, or zero-padding repair exists.

The horse identity retains only the ten-ASCII-digit accessU profile key and emits `jra:horse:<key>`. The entry ID is
race-local, `<external_race_id>:entry:<positive canonical horse_no>`, and intentionally does not contain a horse
profile key. The result ID is `jra:result:<YYYY>:<VV>:<MM>:<DD>:<RR>:horse:<key>`.

## Official URL Boundary

The accessS parser accepts only resolved HTTPS `www.jra.go.jp/JRADB/accessS.html` URLs with one `CNAME`, exact
observed `pw01sde01` or `pw01sde10` selector families, a validated five-token race segment, a valid calendar-date
token whose year agrees with the native race year, and an opaque uppercase `[0-9A-F]{2}` tail. Raw `/` and one
uppercase `%2F` spelling are accepted; `%252F`, lowercase encoding, `+`, unknown/duplicate parameters, ports,
credentials, fragments, noncanonical hosts, malformed percent encoding, and unobserved selector/tail forms fail
closed. Selector, calendar date, and tail never enter `external_race_id`.

The accessU parser has the matching strict resolved URL boundary, accepting only observed `pw01dud00` or
`pw01dud10` CNAME selector families, a ten-digit profile key, and opaque uppercase two-hex tail. Context/tail
aliases for the same key collapse to equal horse identities. The implementation never performs network access or
assumes that a lexically valid race identity proves a race exists.

## Explicitly Unchanged and Out of Scope

```text
NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN
MIXED_HISTORY_COLLECTION_READY = NO
```

There is no NAR code, cross-provider bridge, horse-name fallback, provider capture, race discovery, HTML parsing,
historical normalization, SQLite access, clock, or package-root export. The b2 conclusion remains binding: pure JRA
identity work does not attach an NAR horse to a JRA result row.

## Allowed Files

```text
scripts/simulation/jra_official_identity.py
tests/test_jra_official_identity.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Verification and Stop Condition

Dedicated, related, full-suite, static, package-export, and diff checks are required before review publication.
Stop for independent implementation review after the one review commit; do not integrate formal or begin capture,
bridge, discovery, or a JRA normalizer.
