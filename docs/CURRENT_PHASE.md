Exit code: 0
Wall time: 0.2 seconds
Total output lines: 3584
Output:
# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase and Base

Phase `4C-2d3b1i6d1` 窶・JRA trusted historical source architecture preparation.

Formal branch/base: `feature/ver0.8-simulator` at
`7b4a0f5e28311c2d64685f6d3309f68556e67f8b`.

Review branch: `review/4c-2d3b1i6d1-prepare`.

## Current JRA State

| Area | Status | Finding |
| --- | --- | --- |
| Current JRA fetch | PLACEHOLDER | `scripts/fetch_jra.py` contains one hard-coded sample `Race`; it makes no official request. |
| Current JRA parser | UNSUPPORTED | No JRA parser or official URL parser exists. `HorseParser` and `PastRaceParser` are legacy NAR/DB code. |
| Current JRA official source | PARTIAL | Official JRA page families are reachable and have been probed, but no trusted JRA supplied-response, capture, archive, or normalizer boundary exists. |
| Current JRA external identity | PARTIAL | Official opaque race and horse CNAMEs are present on JRA pages, but KeibaOS has no approved implementation or NAR-to-JRA bridge. |
| Current JRA historical source | UNSUPPORTED | No causally eligible JRA capture can create a c1a `past_race` record. |

Legacy `scripts/fetch_races.py` selects `JRAFetcher` on weekends and writes legacy `Race` data through
`scripts/database.py`. The legacy `races`, `horses`, and `past_races` tables use local IDs and `REAL` values;
they are not trusted historical evidence and are forbidden as a JRA fallback.

## Official Page and Identity Findings

Official probes used `https://www.jra.go.jp` only and retained no probe body. Valid representative pages returned
`200`, did not redirect, had `Content-Type: text/html`, no `Content-Encoding`, no declared charset, and decoded as
CP932. A bare `JRADB/accessD.html`, `accessS.html`, or `accessU.html` request redirected to
`/error/error013.html`; a canonical CNAME is therefore required.

| Family | Exact approved investigation form | Observed semantic evidence |
| --- | --- | --- |
| Target entry / race card | `https://www.jra.go.jp/JRADB/accessD.html?CNAME=<opaque-accessD-cname>` | Page title `蜃ｺ鬥ｬ陦ｨ`; it is the prospective target track/entry/jockey/odds family, not complete history. |
| Historical result | `https://www.jra.go.jp/JRADB/accessS.html?CNAME=<opaque-accessS-cname>` | Page title `繝ｬ繝ｼ繧ｹ邨先棡`; its result table labels include finish, horse number, horse link, time, textual 逹蟾ｮ, row-local corner order, body weight, and win popularity. |
| Horse profile/history | `https://www.jra.go.jp/JRADB/accessU.html?CNAME=<opaque-accessU-cname>` | Page title `遶ｶ襍ｰ鬥ｬ諠・ｱ`; its `蜃ｺ襍ｰ繝ｬ繝ｼ繧ｹ` table links rows to `accessS.html`. |
| Odds | `https://www.jra.go.jp/JRADB/accessO.html?...` | The result page navigation points to this distinct family. It is not yet an approved historical source. |

The observed result CNAME family is `pw01sde10` + 20 ASCII digits + `/` + two uppercase hexadecimal characters;
the observed profile CNAME family is `pw01dud10` + 10 ASCII digits + `/` + two uppercase hexadecimal characters.
These are provider-native opaque keys. No field decomposition, generation, date/place inference, case folding,
trailing-token removal, query reordering, or token re-encoding is approved. The same result response bytes were
observed for the official raw `/` and `%2F` CNAME spellings. Future accepted inputs may use either spelling, must
decode exactly one CNAME value, and must canonicalize only that URL delimiter to uppercase `%2F`; the opaque decoded
token is otherwise byte-for-byte lexical identity. A future URL validator must require HTTPS, host exactly
`www.jra.go.jp`, no credentials/fragment/non-default port, exact path, exactly one nonblank `CNAME` query pair, no
unknown query pair, no `+`, and no malformed percent escape. Redirect following is not approved.

`JRA_STABLE_RACE_ID = PROVEN`: once a supplied `accessS` URL passes its future closed validator, its exact opaque
CNAME is the race key and the proposed identity is `jra:race:<accessS-CNAME>`. The `accessD` token is a separate
official page token and must not be assumed interchangeable with the result CNAME. `JRA_STABLE_HORSE_ID = PROVEN`:
a result-row horse link to `accessU` supplies the opaque profile CNAME, with proposed identity
`jra:horse:<accessU-CNAME>`. `JRA_STABLE_ENTRY_ID = PROVEN`: a positive canonical row-local `鬥ｬ逡ｪ`, scoped by the
approved race identity and accompanied by the exact horse link, gives `jra:race:<accessS-CNAME>:entry:<horseNo>`.

`NAR_JRA_EVENT_TO_JRA_RESULT_RESOLUTION = NOT_PROVEN`. c1 discovery currently emits only
`jra:event:{YYYYMMDD}:{NAR-display-place}:{raceNo}`, which cannot derive an opaque JRA accessS CNAME.
`NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN`: neither NAR lineage nor horse-name matching establishes the JRA
profile key. A bridge must prove both mappings from official supplied evidence; no fuzzy name, date/place-only, or
local-ID fallback is allowed.

`JRA_HORSE_HISTORY_PAGE = accessU.html?CNAME=<profile-CNAME>`. Its `蜃ｺ襍ｰ繝ｬ繝ｼ繧ｹ` table has row-local accessS links,
and an inspected horse showed its career list, but general completeness across JRA/local/overseas starts and
pagination semantics are not proven. `JRA_HORSE_HISTORY_COMPLETENESS = UNPROVEN`.
`JRA_DEBATABLE_RECENT_COLUMNS_AS_COMPLETE_HISTORY = FORBIDDEN`: accessD窶冱 prior-four-race display is only recent
display context and never proof of `ALL_CAUSALLY_AVAILABLE_ACTUAL_PRIOR_STARTS`.

## Result Field Authority and Blocking Domain Finding

| c1a past-race field | JRA authority/status |
| --- | --- |
| `race_date`, `place` | accessS visible race header, cross-checked to the opaque accessS identity only when an approved decoder exists; otherwise identity remains opaque. |
| `race_name`, `race_class` | Separate accessS title and condition/class nodes are required; a single combined heading must not be regex-split. Selector contract remains unimplemented. |
| `distance_m`, `track`, `weather`, `track_condition` | accessS race facts: course/surface/distance and displayed weather/going. Direct parsing is plausible but unapproved pending a closed selector contract. |
| `finish`, `race_time`, `weight`, `weight_diff`, `jockey`, `popularity`, `passing_order` | accessS matched horse row: `逹鬆・`, `繧ｿ繧､繝`, `鬥ｬ菴馴㍾・亥｢玲ｸ幢ｼ噂`, `鬨取焔蜷構`, `蜊伜享 莠ｺ豌予`, and `繧ｳ繝ｼ繝翫・騾夐℃鬆・ｽ構`. Body weight is not assigned weight; jockey allowance marks require preservation pending an exact grammar. |
| `fourth_corner_position` | accessS row-local order plus its labelled race-level `1繧ｳ繝ｼ繝翫・`窶ｦ`4繧ｳ繝ｼ繝翫・` table could support positional mapping only after the same uniqueness/count contract as NAR is separately proven. Current status: NOT_PROVEN. |
| `odds` | accessS exposes popularity but not exact per-horse win odds. Historical odds require a separate authoritative JRA page or an explicit unsupported result state. Final historical result odds must never backfill prediction-time target odds. |
| `reference_time_difference_seconds` | BLOCKED. accessS displays exact horse/winner times and textual `逹蟾ｮ` (e.g. 繧ｯ繝・ 繝上リ, fractions), but no directly displayed official Decimal time-difference field was found. Textual margin must not be converted to seconds. |

`REFERENCE_TIME_DIFFERENCE_STATUS = FIELD_DOMAIN_CONTRACT_GAP` and
`HISTORICAL_PAST_RACE_DOMAIN_CHANGE_REQUIRED = YES`. A deterministic subtraction from displayed times would be a
new provider-neutral semantic contract, not a direct official field, and JRA's reference semantics have not been
shown equivalent to NAR's. No JRA `past_race` implementation is authorized until that independent domain design is
reviewed. Textual margin conversion remains forbidden.

For initial JRA support, cancellation/exclusion/non-start, stopped/disqualified, missing time/body-weight/odds,
nonnumeric popularity, or ambiguous corner state must be explicitly classified and never skipped. Current
`ABNORMAL_RESULT_STATUS = UNPROVEN / IMPLEMENTATION_BLOCKED`.

## Evidence, Capture, and Causality

The final evidence cardinality is blocked but its minimum vocabulary consequence is clear: accessS lacks exact
per-horse odds, while c1a requires `odds`. A truthful JRA source would require accessS plus an authoritative separate
odds response if one exists. Therefore `JRA_PAST_RACE_EVIDENCE_COUNT = AT_LEAST_2_NOT_YET_SOURCE_PROVEN` and
`C1A_EVIDENCE_ROLE_EXTENSION_REQUIRED = YES`: existing `historical_race_context` and
`historical_race_result` cannot truthfully label a third odds response. This is a blocker report, not authorization
to change c1a.

`JRA_SPECIFIC_SUPPLIED_RESPONSE = REQUIRED`: introduce a JRA-specific supplied-response value later rather than
reuse `NarSuppliedOfficialResponse` or refactor stable NAR APIs. It must preserve exact bytes, canonical JRA URL,
explicit charset, and supplied `observed_at`; raw SHA-256 is over bytes before decoding. CP932 is the presently
observed parser charset. `JRA_CHARSET_POLICY = EXPLICIT_CP932_ONLY_UNTIL_A_FUTURE_PROBE_PROVES_ANOTHER_OFFICIAL
FAMILY`; no byte conversion occurs before archival hashing. `JRA_CONTENT_ENCODING_POLICY = INITIAL_IDENTITY_ONLY`:
the probes had no content encoding, and a compressed response needs an independently designed byte-preserving rule.

`CAPTURE_ARCHITECTURE_DECISION = JRA_SPECIFIC`. Keep the NAR capture/archive/live modules frozen: their page-kind
vocabulary, UTF-8 rule, and host policy are NAR-specific. `CAPTURE_DATABASE_DECISION = SEPARATE_JRA_CAPTURE_DATABASE`
is selected for the same reason; a shared multi-provider archive is a later architecture proposal, not a DRY
refactor. `JRA_CAPTURE_REUSE_OF_NAR_DOMAIN = FORBIDDEN`.

`JRA_REDIRECT_POLICY = DISALLOW_UNTIL_SEPARATELY_APPROVED`: capture must issue a no-redirect request and reject
3xx or any effective URL different from the requested canonical URL. `JRA_AVAILABLE_AT_POLICY = None`; neither
page date, HTTP date, nor current time is reliable publication availability. Preserve
`requested_at <= observed_at <= stored_at`; only `observed_at <= information_cutoff` establishes later historical
eligibility. A live page fetched today is not historical evidence for an earlier cutoff.

`JRA_REQUEST_PACING_POLICY = SERIAL_SINGLE_REQUESTS_WITHOUT_RETRY_OR_CONCURRENCY_IN_THE_FIRST_CAPTURE_BOUNDARY`.
No official numeric rate limit was found in these probes, so no invented rate is frozen. Caller orchestration must
remain explicit and conservative.

## Target Inputs, Bridge, and Scope

The first JRA route is only: NAR target entry + NAR HorseMark-discovered JRA actual start 竊・trusted JRA past-race
source. It is blocked by both the opaque-event bridge and the time-difference domain gap. It must not expand to JRA
target-race collection. A later JRA target source may use accessD for track/entry/jockey/odds only with pre-cutoff
capture; `JRA_TARGET_ODDS_HISTORICAL_BACKFILL_FROM_FINAL = FORBIDDEN`.

The future JRA source record would use `organization="JRA"`, `source_system="jra_official"`, and, only after bridge
proof, `provider_record_id = jra:result:<accessS-CNAME>:horse:<accessU-CNAME>`. It must use the same JRA race
identity grammar for target and historical races. The future API is intentionally not frozen until its required
bridge and evidence inputs are proven; a candidate module is
`scripts/simulation/jra_historical_past_race_source.py` with a provider-specific response type and normalizer.

`ABILITY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION`.
`JOCKEY_REFERENCE_DATE_STATUS = FUTURE_LEAKAGE_BLOCKER_IN_CURRENT_PERSISTED_COMPOSITION`.
`TIME_DIFFERENCE_TO_PREDICTION_ADAPTER_STATUS = NO_ADAPTER_CONTRACT_GAP`.

## Recommended Sequence and Exact Future Scope

1. `4C-2d3b1i6d1a` 窶・JRA/provider-neutral time-difference compatibility PREPARE: only
   `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. It must decide whether a c1a domain extension is
   truthful before any JRA parser is authorized.
2. `4C-2d3b1i6d1b` 窶・NAR-discovered JRA opaque-identity bridge PREPARE: only
   `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. It must prove JRA event-CNAME and NAR-lineage to
   JRA-horse-CNAME linkage from supplied official pages.
3. `4C-2d3b1i6d1c` 窶・JRA capture/archive design and implementation, after the preceding approvals:
   `scripts/simulation/jra_official_response_capture.py`,
   `scripts/simulation/jra_official_response_capture_migration.py`,
   `scripts/simulation/jra_official_response_capture_migration_runner.py`,
   `scripts/simulation/jra_official_response_live_capture.py`,
   `scripts/simulation/repositories/sqlite_jra_official_response_capture_repository.py`,
   `tests/test_jra_official_response_capture.py`,
   `tests/test_jra_official_response_capture_migration.py`,
   `tests/test_jra_official_response_live_capture.py`,
   `tests/test_sqlite_jra_official_response_capture_repository.py`, and the two phase docs. It uses a new dedicated
   archive DB.
4. `4C-2d3b1i6d1d` 窶・JRA historical result normalizer implementation, only after all blockers are closed:
   `scripts/simulation/jra_historical_past_race_source.py`,
   `tests/test_jra_historical_past_race_source.py`, approved authentic JRA fixtures under `tests/fixtures/jra/`,
   and the two phase docs. No NAR, c1a, builder, SQLite snapshot, or migration change is pre-approved here.
5. Only then may `4C-2d3b1i6c1d3b2c2` design mixed-history NAR collection.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Stop Condition

Stop after the docs-only review commit and independent architecture review. Do not implement JRA source, capture,
bridge, fixtures, acquisition, c1a changes, NAR changes, or d3b2c2 collection.

## Design Review Correction — Identity and Source Contract

This correction supersedes only the earlier CNAME-as-identity and evidence-count conclusions. All retained status,
time-difference, capture-separation, source-system, and recent-column conclusions above remain unchanged.

`EXACT_CNAME_AS_STABLE_ENTITY_ID = REJECTED`. Officially observed accessS families include `pw01sde010...` and
`pw01sde100...`; accessU families include `pw01dud002...` and `pw01dud102...`. The investigation did not prove
whether their leading variants, digit runs, or final `/XX` suffix are native entity identity, view/navigation mode,
or integrity context. They must not become an external identity by visual inference.

The same sampled race retained one accessS CNAME through direct access, the official accessU history link, and
race-page navigation. Raw `/` and `%2F` are equivalent URL-delimiter spellings, not distinct CNAMEs. No independent
official navigation form yielding a second valid CNAME for that physical race was obtained:
`SAME_JRA_RACE_MULTIPLE_ACCESS_S_CNAME = INCONCLUSIVE`. The result-row horse link and direct accessU profile likewise
retained one CNAME only, so `SAME_JRA_HORSE_MULTIPLE_ACCESS_U_CNAME = INCONCLUSIVE`.

Accordingly, `JRA_STABLE_RACE_ID = NOT_PROVEN`, `JRA_STABLE_HORSE_ID = NOT_PROVEN`, and
`JRA_STABLE_ENTRY_ID = NOT_APPROVED`. A future entry spelling may be
`{stable-external-race-id}:entry:{horseNo}` only after stable race identity and separate horse identity are proven.
`JRA_PROVIDER_RECORD_ID = PROVISIONAL`; no CNAME-based provider-record spelling is approved.

`ACCESS_S_CNAME_COMPONENTS = page-family prefix pw01sde; leading variant/digit run/final slash-hex suffix unknown`.
`ACCESS_U_CNAME_COMPONENTS = page-family prefix pw01dud; leading variant/digit run/final slash-hex suffix unknown`.
The exact result-row horse anchor is `https://www.jra.go.jp/JRADB/accessU.html?CNAME=<accessU-CNAME>`; it proves
official row-to-profile navigation, but not yet stable JRA horse identity across accessU variants.

`NAR_JRA_EVENT_TO_JRA_RESULT_RESOLUTION = NOT_PROVEN`: the current NAR HorseMark JRA row has only date, display
place, race number, and display/result fields; it has no JRA accessS link, CNAME, or JRA horse token.
`NAR_LINEAGE_TO_JRA_HORSE_ID_LINK = NOT_PROVEN` remains unchanged. No name, local-ID, date/place-only, or fuzzy bridge
is allowed.

The official accessU `出走レース` note distinguishes populations. It states domestic registered horses include JRA,
local, and overseas race results, so `JRA_DOMESTIC_REGISTERED_HORSE_HISTORY_COMPLETENESS = PROVEN_FOR_CURRENT_PAGE_CONTENT`
(still subject to supplied observed-at causality and later parser validation). It says foreign horses are generally
limited to their latest four starts, so `JRA_FOREIGN_HORSE_HISTORY_COMPLETENESS = NOT_COMPLETE_ALL_HISTORY` and
`FOREIGN_HORSE_COMPLETE_HISTORY_POLICY = UNSUPPORTED_FAIL_CLOSED`.

The direct probes freeze `JRA_ACCESS_D_CHARSET = CP932`, `JRA_ACCESS_S_CHARSET = CP932`,
`JRA_ACCESS_U_CHARSET = CP932`, and `JRA_ACCESS_O_CHARSET = CP932`: each had `Content-Type: text/html`, HTML
`meta charset=Shift_JIS`, no content encoding when explicitly requesting identity, and successful strict CP932 decode.
Thus `JRA_CHARSET_POLICY = CP932` for these four approved page families. SHA-256 remains over exact bytes before
decoding. The accessO POST navigation reached current `オッズ 開催選択`, not historical per-horse odds.

`JRA_HISTORICAL_ODDS_AUTHORITY = NOT_PROVEN`, `MINIMUM_JRA_PAST_RACE_RESPONSE_SET = UNRESOLVED`, and
`C1A_EVIDENCE_ROLE_EXTENSION_REQUIRED = UNRESOLVED`. A third evidence role is not approved until the exact truthful
official response set is proven.

`JRA_FOURTH_CORNER_MAPPING = LAYOUT_DEPENDENT`: use row-local passing order only where same-page labelled corner rows
prove ordered component alignment and exactly one fourth corner; pages that omit that proof are unsupported. No
blind final-component rule is permitted. `ABNORMAL_RESULT_TAXONOMY = normal_start: positive numeric finish with
required fields; non_start: recognised cancellation/exclusion; started_abnormal: recognised stopped, disqualified,
demoted, or related result state`. A later selector/state design must freeze exact provider spellings; none may skip.

The recommended next phase is `4C-2d3b1i6d1a` — historical time/reference comparison domain contract PREPARE;
it remains ahead of identity bridge (`d1b`), capture (`d1c`), and normalization (`d1d`).
