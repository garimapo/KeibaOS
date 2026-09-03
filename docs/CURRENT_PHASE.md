# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_6`
- Name: `NAR Supported Daily Target Source Implementation`
- Base Commit: `bb9461490e59b2bfc370fb27183ac4e2f202aa8b`
- Branch: `feature/post-v0.8-daily-replay`
- Release baseline: `v0.8.0` at `c08bedb5421b44d63a8bac017699efffca2a4b73`
- Phase type: `IMPLEMENTATION`
- PREPARE activity: `DESIGN_ONLY`
- Production / test / fixture implementation during PREPARE: `NOT_AUTHORIZED`
- Stage / commit / push during PREPARE: `NOT_AUTHORIZED`
- `EXECUTE_APPROVED_PHASE`: `COMPLETED`

The approved Phase 2 through Phase 5 documents and `AGENTS.md` remain authoritative.
This PREPARE only freezes the evidence, lexical grammar, files, tests, and execution gate
needed to implement the Phase 5 NAR supported profile. It does not restate or change an
approved contract.

## Objective and boundary

A later, separately authorized `EXECUTE_APPROVED_PHASE` may implement the four Phase 5
production modules, four test modules, and only the exact reviewed official-byte fixtures
listed below. JRA, Monthly locator bootstrap, Evidence Resolver, manifest construction,
replay execution, SQLite, migrations, schemas, durable archives, and CLI remain outside
this phase.

The implementation consumes exact supplied MonthlyConveneInfo request identity and
captured evidence. It never derives that locator from `target_date`. RaceList request
identity remains the exact raw href lexeme from the captured envelope, and the pure
normalizers/builders have no network dependency.

## Exact production APIs and ownership

### `scripts/simulation/historical_daily_targets.py`

Implement exactly the provider-neutral Phase 2 values and builder named in Phase 5:

```python
HistoricalDailyProviderIdentity
DailyHistoricalReplayProviderScope
ProviderNativeDispositionEvidenceReference
DailyHistoricalReplayCompletenessEvidence
DailyHistoricalReplayTarget
HistoricalDailyTargetEvidenceBundle
DailyHistoricalReplayTargetSet
DailyTargetDiscoveryFailureCode
DailyHistoricalTargetValidationError
DailyHistoricalTargetIntegrityError
TargetDiscoveryIncompleteError

build_daily_historical_replay_target_set(
    *,
    target_date: date,
    provider_scope: DailyHistoricalReplayProviderScope,
    evidence_bundles: tuple[HistoricalDailyTargetEvidenceBundle, ...],
) -> DailyHistoricalReplayTargetSet
```

This module owns provider-neutral validation, immutability, exact scope coverage,
canonical ordering, and the already frozen Phase 5 digest bytes only. It must not import
or encode NAR/JRA coverage, URL, status, floor-date, HTML, network, or storage rules.

### `scripts/simulation/nar_historical_daily_target_capture.py`

Implement exactly:

```python
NARHistoricalDailyTargetPageKind
NARHistoricalDailyTargetRequestIdentity
NARHistoricalDailyTargetResponseCapture
NARHistoricalDailyTargetCaptureSource
NARHistoricalDailyTargetCaptureArchive
NARHistoricalDailyTargetCaptureError
NARHistoricalDailyTargetCaptureValidationError
NARHistoricalDailyTargetCaptureUnsupportedError
NARHistoricalDailyTargetCaptureMissingError
```

The request value accepts exact caller-supplied UTF-8 request material, resolved URL,
page kind, and supplier evidence identity. It has no constructor or helper taking
`target_date`, year/month, date/`babaCode`, or venue to manufacture a locator. The
response value freezes exact bytes, metadata, honest UTC acquisition times, and the
Phase 5 request/capture digests. The Source/Archive Protocols expose exact-ID load and
append-only save only; this phase supplies no SQLite implementation.

### `scripts/simulation/nar_historical_daily_target_live_capture.py`

Implement exactly:

```python
NARHistoricalDailyTargetHTTPTransport
NARHistoricalDailyTargetLiveCaptureService
NARHistoricalDailyTargetCaptureTransportError

NARHistoricalDailyTargetLiveCaptureService.capture_supplied_response(
    *,
    request_identity: NARHistoricalDailyTargetRequestIdentity,
) -> NARHistoricalDailyTargetResponseCapture
```

The service performs one exact GET for an already constructed request identity, with
redirects disabled, `Accept-Encoding: identity`, bounded exact bytes, effective-URL
equality, and archive-before-return. It neither discovers nor constructs a request.

### `scripts/simulation/nar_historical_daily_target_source.py`

Implement exactly the Phase 5 NAR-specific values and pure functions:

```python
NARHistoricalVenueIdentity
NARMonthlyConveneInfoVenueLocator
NARMonthlyConveneInfoEnvelope
NARRaceListTargetFragment
NARNativeDispositionEvidence
NARHistoricalDailyTargetSourceError
NARHistoricalDailyTargetSourceValidationError
NARHistoricalDailyTargetSourceUnsupportedError

normalize_nar_monthly_convene_info(
    *, target_date: date,
    capture: NARHistoricalDailyTargetResponseCapture,
) -> NARMonthlyConveneInfoEnvelope

normalize_nar_race_list(
    *, target_date: date,
    expected_venue: NARHistoricalVenueIdentity,
    expected_request: NARHistoricalDailyTargetRequestIdentity,
    capture: NARHistoricalDailyTargetResponseCapture,
) -> NARRaceListTargetFragment

build_nar_historical_daily_target_evidence_bundle(
    *, target_date: date,
    envelope_capture: NARHistoricalDailyTargetResponseCapture,
    race_list_captures: tuple[NARHistoricalDailyTargetResponseCapture, ...],
) -> HistoricalDailyTargetEvidenceBundle

build_nar_historical_daily_replay_target_set(
    *, target_date: date,
    envelope_capture: NARHistoricalDailyTargetResponseCapture,
    race_list_captures: tuple[NARHistoricalDailyTargetResponseCapture, ...],
) -> DailyHistoricalReplayTargetSet
```

The module may use Python standard-library lexical parsing with raw start-tag access.
It must not import the live capture service, HTTP libraries, clocks, SQLite, legacy
`NARProvider`/`NARParser`, or existing NAR URL canonicalizers. Both builders are pure
over supplied immutable captures.

## Exact official-byte fixture and provenance freeze

### Acquisition profile

All byte candidates below were read from the official `https://www.keiba.go.jp` origin
on 2026-09-03 in one read-only research session. Each request was `GET`, used
`User-Agent: Mozilla/5.0` and `Accept-Encoding: identity`, returned status 200 without an
effective-URL change, had no `Content-Encoding`, and decoded as strict UTF-8.
`observed_at` is the honest
post-response UTC observation shown below; it is not backdated and is not provider
availability or replay causality. `provider_available_at` is `None`.

The official locator-supplier script is provenance-only. Its reviewed bytes contain the
exact official expression:

```javascript
window.location.href = "/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=" + year + "&k_month=" + month;
```

The exact supplier reference is:

```text
nar-monthly-locator-supplier-research-v1:bdf86457a9c917fc8259f8b87593c9bbece72d501a95fb5d3573a93b43532515#changePage
```

It establishes research-fixture locator provenance only. Production bootstrap from a
date remains out of scope and forbidden.

### Byte files

`tests/fixtures/nar_daily_targets/provenance.json` must record, for every row, the exact
path, method, supplied lexical request material, resolved/effective URL, supplier
reference, requested/observed UTC timestamps, response headers used by the capture,
byte length, response SHA-256, strict charset result, and `provider_available_at: null`.
The metadata file uses schema version 1 and must not rewrite an observation to the
historical target date.

| Exact future fixture path | Exact requested/effective URL | observed_at UTC | bytes | SHA-256 |
| --- | --- | --- | ---: | --- |
| `tests/fixtures/nar_daily_targets/monthly_locator_supplier_monthltconveninfo_20260130_1.utf8.js` | `https://www.keiba.go.jp/KeibaWeb/resources/js/monthltconveninfo.js?t=20260130_1` | `2026-09-03T06:00:22.183779+00:00` | 438 | `bdf86457a9c917fc8259f8b87593c9bbece72d501a95fb5d3573a93b43532515` |
| `tests/fixtures/nar_daily_targets/monthly_convene_info_2025_01.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2025&k_month=1` | `2026-09-03T06:00:22.739018+00:00` | 209768 | `74a4c479b134a831121820a69815e8eb66db0f360c5433330bf7cf61fabdddef` |
| `tests/fixtures/nar_daily_targets/race_list_2025_01_01_kawasaki_baba21.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&k_babaCode=21` | `2026-09-03T06:00:22.963204+00:00` | 66307 | `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1` |
| `tests/fixtures/nar_daily_targets/race_list_2025_01_01_nagoya_baba24.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&k_babaCode=24` | `2026-09-03T06:00:23.147465+00:00` | 67210 | `ad44b47c59f962d0beb673e3c28fcdd9d9cbcbb8c6c3db229c33525aeabc6e1e` |
| `tests/fixtures/nar_daily_targets/race_list_2025_01_01_kochi_baba31.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F01%2F01&k_babaCode=31` | `2026-09-03T06:00:23.408490+00:00` | 58875 | `e8f4955552ab2d8cfba09cab5d38269a8657e48e34ec510ffedfc424662b0f4f` |
| `tests/fixtures/nar_daily_targets/monthly_convene_info_2025_12.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2025&k_month=12` | `2026-09-03T06:00:23.449635+00:00` | 214005 | `429d06b3f0c64715902704621946c3b04314a1e8518944d5660875cf351b41bc` |
| `tests/fixtures/nar_daily_targets/race_list_2025_12_26_oi_baba20.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F12%2F26&k_babaCode=20` | `2026-09-03T06:00:23.616972+00:00` | 62887 | `b54b444b3fe447814969c60797f51a13e7ee6f5141e1b7c7f76d2b07d76e1584` |
| `tests/fixtures/nar_daily_targets/race_list_2025_12_26_kanazawa_baba22.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F12%2F26&k_babaCode=22` | `2026-09-03T06:00:23.826423+00:00` | 64581 | `393f12cb80d2ed09865cc4be3e17a0e95cd1c7e16c76b64c2cb89d032ceff37a` |
| `tests/fixtures/nar_daily_targets/race_list_2025_12_26_kasamatsu_baba23.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F12%2F26&k_babaCode=23` | `2026-09-03T06:00:24.123943+00:00` | 64640 | `fe6b79d7bf30e006129279811e8d2d2cecfc7ba61fd7d77d37362938c9639a42` |
| `tests/fixtures/nar_daily_targets/monthly_convene_info_2020_03.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2020&k_month=3` | `2026-09-03T06:00:24.160941+00:00` | 210531 | `bedc55f4eb038794b8f728435507f4d2785ab42927bbc4e92f75cd1b9f4282f7` |
| `tests/fixtures/nar_daily_targets/monthly_convene_info_2017_12.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2017&k_month=12` | `2026-09-03T06:00:24.206576+00:00` | 212943 | `f694e954e3383e81295804f8c4e459acab557076719414e2363170ff87326ffc` |
| `tests/fixtures/nar_daily_targets/monthly_convene_info_2025_08.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2025&k_month=8` | `2026-09-03T06:00:24.230733+00:00` | 210385 | `ba12b089f3e8121b8c534f18c2d362dd97f3c3fc59f4a032cf36c7fcae4083ba` |
| `tests/fixtures/nar_daily_targets/race_list_2025_08_30_obihiro_baba3.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F08%2F30&k_babaCode=3` | `2026-09-03T06:00:24.508789+00:00` | 68691 | `d679e2d97bf7fcfa5d2dbf7e5870fbbd126e02d1a1fa06b61a482b1536eb4a46` |
| `tests/fixtures/nar_daily_targets/race_list_2025_08_30_funabashi_baba19.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F08%2F30&k_babaCode=19` | `2026-09-03T06:00:24.720263+00:00` | 68590 | `e624ae444b9c0c9caddaf33095a8483bb9578c4b3933da8380e26efc171ad211` |
| `tests/fixtures/nar_daily_targets/race_list_2025_08_30_saga_baba32.utf8.html` | `https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=2025%2F08%2F30&k_babaCode=32` | `2026-09-03T06:00:25.014371+00:00` | 63436 | `4e5e2388e6c463ae7330a11cc6cf3f3e4762eaaf2226579876781b51d3053fee` |

The corresponding `requested_at` values, in table order, are
`06:00:22.113654`, `06:00:22.183860`, `06:00:22.739287`,
`06:00:22.977211`, `06:00:23.161403`, `06:00:23.424025`,
`06:00:23.449963`, `06:00:23.629911`, `06:00:23.839055`,
`06:00:24.137052`, `06:00:24.161207`, `06:00:24.206915`,
`06:00:24.230982`, `06:00:24.522383`, and `06:00:24.734302`, all on
`2026-09-03` with `+00:00` and six fractional digits.

The supplier script `Content-Type` is exactly
`application/javascript; charset=UTF-8`; every HTML `Content-Type` is exactly
`text/html; charset=UTF-8`. `Content-Encoding`, `ETag`, and response `Content-Length`
are absent for every response. `Last-Modified` is
`Mon, 23 Feb 2026 08:26:41 GMT` for the supplier script and absent for all HTML.
The response `Date` is `Fri, 28 Aug 2026 06:33:49 GMT` for the supplier script;
`Thu, 03 Sep 2026 06:00:25 GMT` for Monthly 2025-01 and all three 2025-01 RaceLists;
`Thu, 03 Sep 2026 05:57:54 GMT` for Monthly 2025-12 and Monthly 2020-03;
`Thu, 03 Sep 2026 06:00:26 GMT` for all three 2025-12 RaceLists and the 2025-08
Obihiro RaceList; `Thu, 03 Sep 2026 05:57:55 GMT` for Monthly 2017-12;
`Thu, 03 Sep 2026 05:58:32 GMT` for Monthly 2025-08; and
`Thu, 03 Sep 2026 06:00:27 GMT` for the 2025-08 Funabashi and Saga RaceLists.

No byte fixture is added during PREPARE. During an approved EXECUTE, each proposed byte
must match the exact path, length, and SHA-256 above before it enters the repository. A
provider response that no longer matches is not rewritten, normalized, or substituted;
execution stops for review. Synthetic byte mutations may be generated in test memory,
but no synthetic file may replace an acceptance fixture.

### Fixture evidence boundary

The frozen official-byte fixtures are parser/source-contract test evidence only. They
are not formal historical replay dataset evidence. Their provenance retains the honest
actual `requested_at` and `observed_at` acquisition times and must never backdate either
value to `target_date`.

Fixture provenance time must not be projected into
`HistoricalDailyTargetEvidenceBundle.observed_at` and must not enter PredictionPipeline,
snapshot selection, prediction cutoff, settlement cutoff, or any other replay causality.
An approved EXECUTE may materialize fixtures only through the explicit materialization
step and only when the resulting bytes exactly match the frozen path, length, and
SHA-256. A SHA-256 mismatch stops implementation. Unit and integration tests must have
network access disabled and consume only the already materialized frozen bytes; they
must never fetch, refresh, replace, or repair a fixture.

## Frozen lexical grammar v1

### Monthly supplied locator and RaceList raw request identity

The five reviewed Monthly request materials are the exact UTF-8 relative locators shown
by removing only the official origin from their table URLs. Their parameter order is
exactly `k_year` then `k_month`, with unpadded decimal month. They are supplied fixture
inputs under the provenance reference above; production code must not generate them.

For every accepted target-date venue cell, the authoritative RaceList request material
is the exact quoted `href` attribute value from source bytes:

```text
/KeibaWeb/TodayRaceInfo/RaceList?k_raceDate=YYYY%2FMM%2FDD&amp;k_babaCode=B
```

`YYYY`, `MM`, and `DD` are exact zero-padded ASCII digits, `%2F` is uppercase, `B` is a
positive unpadded ASCII decimal, and the literal source separator is `&amp;`. The query
order is date then `babaCode`; no other attribute value, query key, alias, or encoding is
accepted. HTML character-reference decoding and exact resolution against
`https://www.keiba.go.jp` produce the effective request URL. No parse/re-emit,
reordering, slash decoding/re-encoding, padding, or reconstruction is permitted.

### MonthlyConveneInfo strict grammar

`monthly-convene-info-v1` accepts only strict UTF-8 with all of these properties:

1. exactly one `article.monthlySchedule`, one `select#selectedYear[name="k_year"]`, one
   selected option whose exact ASCII value/text equals the supplied request year, one
   `ul.monthTab`, and one active `li#monthTabM.tab[month="M"]` whose exact text is
   `M月` and equals the supplied request month;
2. exactly one `table.schedule`; its unique calendar header has empty boundary cells and
   direct day headers `1` through the real last day of the requested month exactly once
   and in increasing order;
3. every following venue row has exactly `days_in_month + 2` direct cells, non-empty
   identical first/last venue display text, and one cell for every header day; no venue
   display text is converted into provider identity;
4. every target-date cell is one of the exact supported anchor shapes
   `(class="day", text="●")`, `(class="night", text="☆")`,
   `(class="day", text="Ｄ")`, or `(class="night", text="Ｄ")`, with exactly one raw
   RaceList href matching the grammar above, or is blank/unsupported evidence;
5. `△`, an anchorless non-whitespace value, unknown class/text, multiple anchors,
   duplicate `babaCode`, duplicate raw locator, target-date mismatch, malformed table,
   or an empty accepted venue set fails closed; and
6. blank cells never establish a zero day. The 2020-03-09 all-blank case is unsupported,
   while the 2017-12-19 Kanazawa `△` cell is unsupported even though other venue cells
   on that date are ordinary/night links.

The implementation must use a lexical parser boundary which retains the raw href bytes;
a reserialized DOM href is not source authority.

### RaceList strict all-row grammar

`nar-race-list-v1` accepts only strict UTF-8 with all of these properties:

1. exactly one `nav.navWrapper`, one `div.courseArea`, and exactly one active
   `a.courseBtn` without an href for the requested venue; every non-active course anchor
   has one same-day raw RaceList href in the same date-first grammar;
2. exactly one target race table: the unnamed direct table in the unique
   `section.raceTable` whose first row is the exact date/venue `当日メニュー` heading
   and whose second row is `tr.subHeader`. Nested/adjacent `table.changeInfo` and
   `table.winnerSearch` rows are not target rows and must never be selected by a broad
   `tr.data` query;
3. every direct `tr.data` in that target table is consumed exactly once and has exactly
   ten direct `td` cells. No row is skipped and no race count/race number is inferred;
4. cell 1 is exactly `[1-9][0-9]*R`; cell 2 is exactly a real `HH:MM` ASCII time; cell 5
   contains exactly one race-title anchor whose raw start tag contains exactly the
   source locator shape
   `/KeibaWeb/TodayRaceInfo/DebaTable?k_raceDate=YYYY%2FMM%2FDD&amp;k_raceNo=R&amp;k_babaCode=B`;
5. href date, unpadded positive `R`, and unpadded positive `B` exactly equal the heading,
   row cell, supplied target date, and expected venue. Identity is
   `nar:{YYYYMMDD}:{B}:{R}`. Duplicate or contradictory identity/time is fatal; and
6. `HH:MM` is official Japan civil time at fixed UTC+09:00 for this post-2020 profile and
   is converted deterministically to an aware UTC datetime. It is not current-clock or
   observation time.

The accepted 2025-01-01 fragments contain 12 Kawasaki, 12 Nagoya, and 9 Kochi target
rows, yielding 33 exact targets. The accepted 2025-12-26 fragments contain 10 Oi, 12
Kanazawa, and 11 Kasamatsu target rows, also yielding 33 exact targets. These counts are
fixture assertions only; contiguity is never a completeness rule.

The independently parsed navigation set is the expected active request `babaCode` plus
all non-active same-day href `babaCode` values. It must equal the envelope and fragment
sets exactly as approved in Phase 5.

### 2025-12-26 Kanazawa native no-substitute grammar

The only accepted exceptional grammar is one and only one
`section.earlyWarning > div.message` in the Kanazawa `babaCode=22` fragment, with exactly
these two text nodes separated by exactly one `<br>` element:

```text
１２月２６日（金）金沢競馬は、降雪の影響により取り止めになりました。
なお、代替開催はありません。
```

Only surrounding ASCII HTML formatting whitespace may vary; the two native strings,
punctuation, full-width digits/parentheses, order, and single `<br>` boundary may not.
The exact reviewed raw inner source slice has SHA-256
`07b9b53a5a75e6b0630c03a15bf10461a3b33be9a71294acb1d7930edcee26ea`.
The implementation retains and hashes the actual raw inner UTF-8 slice without text
normalization for provider-native disposition evidence.

The other two 2025-12-26 fragments must have no `earlyWarning`. All 12 Kanazawa target
rows must remain structurally present and valid; the warning cannot manufacture a row.
The 2025-08-30 Funabashi warning about cancellation from race 10 onward is not an alias
of this grammar and must produce whole-day `UNSUPPORTED_NATIVE_DISPOSITION`. Its reviewed
raw inner source SHA-256 is
`b8946cae98ab89d5540aeb66304b6e161ca47f9479232eccc53015d4142c6004`.
Any other warning, missing row, substitute/original ambiguity, or partial status fails
closed.

## Exact failure precedence

Domain/type misuse and corrupted loaded capture state retain the validation/integrity
exceptions approved in Phase 5. For a well-formed discovery request, the NAR builder
selects one primary `DailyTargetDiscoveryFailureCode` in this deterministic order:

```text
UNSUPPORTED_TARGET_DATE
MISSING_ENVELOPE_EVIDENCE
INVALID_OFFICIAL_REQUEST_IDENTITY
DUPLICATE_EVIDENCE
MISSING_PARTITION_EVIDENCE
MALFORMED_OFFICIAL_EVIDENCE
UNSUPPORTED_ENVELOPE_STATE
UNSUPPORTED_NATIVE_DISPOSITION
CONTRADICTORY_EVIDENCE
COVERAGE_SET_MISMATCH
MISSING_SCHEDULED_START
```

The direct Monthly normalizer still rejects an observed `△` as
`UNSUPPORTED_ENVELOPE_STATE`; the high-level 2017 request first fails the approved
historical floor as `UNSUPPORTED_TARGET_DATE`. No error carries partial output.

## Allowed Files for later EXECUTE

Production:

```text
scripts/simulation/historical_daily_targets.py
scripts/simulation/nar_historical_daily_target_capture.py
scripts/simulation/nar_historical_daily_target_live_capture.py
scripts/simulation/nar_historical_daily_target_source.py
```

Tests:

```text
tests/test_historical_daily_targets.py
tests/test_nar_historical_daily_target_capture.py
tests/test_nar_historical_daily_target_live_capture.py
tests/test_nar_historical_daily_target_source.py
```

Fixtures:

```text
tests/fixtures/nar_daily_targets/provenance.json
tests/fixtures/nar_daily_targets/monthly_locator_supplier_monthltconveninfo_20260130_1.utf8.js
tests/fixtures/nar_daily_targets/monthly_convene_info_2025_01.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_01_01_kawasaki_baba21.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_01_01_nagoya_baba24.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_01_01_kochi_baba31.utf8.html
tests/fixtures/nar_daily_targets/monthly_convene_info_2025_12.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_12_26_oi_baba20.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_12_26_kanazawa_baba22.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_12_26_kasamatsu_baba23.utf8.html
tests/fixtures/nar_daily_targets/monthly_convene_info_2020_03.utf8.html
tests/fixtures/nar_daily_targets/monthly_convene_info_2017_12.utf8.html
tests/fixtures/nar_daily_targets/monthly_convene_info_2025_08.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_08_30_obihiro_baba3.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_08_30_funabashi_baba19.utf8.html
tests/fixtures/nar_daily_targets/race_list_2025_08_30_saga_baba32.utf8.html
```

Phase state/report documents:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Every other file is forbidden. In particular, existing NAR capture/source modules,
requirements/dependency files, repositories, SQLite, migrations, schemas, database,
provider archives, CLI, JRA, snapshots, manifest/replay/settlement/persistence/reporting,
`database/keiba.db`, `logs/**`, tags, and release history must not change.

## Required Tests

### `tests/test_historical_daily_targets.py`

- frozen dataclass/value validation, immutability, exact provider scope coverage,
  uniqueness, canonical `(organization, source_system, external_race_id)` target order;
- provider-neutral implementation contains no NAR/JRA assumptions;
- canonical digest known vectors and order permutations; and
- nullable exceptional time, traceability, contradictory evidence, and integrity paths.

### `tests/test_nar_historical_daily_target_capture.py`

- all frozen request/capture digest vectors and exact strict-UTF-8 fixture SHA checks;
- exact raw href preservation including literal `&amp;`, order, case, and encoding;
- rejection of URL reconstruction inputs, reversed/literal-slash/padded/duplicate/unknown
  query variants, redirects/aliases, invalid timestamps/headers/bytes, and mismatched
  effective URLs; and
- exact-ID Source/Archive behavior with no latest or fallback.

### `tests/test_nar_historical_daily_target_live_capture.py`

- one exact request, identity encoding, no redirects/retries, size/status/content checks,
  effective identity equality, honest time order, and save-before-return;
- transport/archive failure returns no capture; and
- no API constructs Monthly or RaceList URLs.

### `tests/test_nar_historical_daily_target_source.py`

- byte-for-byte provenance/SHA validation before parsing;
- official 2025-01-01 ordinary case yields exact 3-venue/33-target set, identities,
  start times, deterministic order, bundle, and target set;
- official 2025-12-26 case yields exact 3-venue/33-target set while all 12 Kanazawa rows
  retain the exact native no-substitute evidence and no normal fallback occurs;
- official 2020-03-09 blank, official 2017-12-19 `△`, and official 2025-08-30 partial
  cancellation fail closed;
- missing/extra/malformed/duplicate row or fragment, wrong date/venue/request,
  navigation mismatch, unknown mark/warning, missing time, contradictory identity, and
  malformed table each fail the whole day with no partial bundle or set;
- target-table scoping does not treat `changeInfo` rows as target races and does not skip
  any direct target row; and
- trap imports/dependencies prove both builders are no-network and consume captures only.

Required verification:

```text
python -m unittest tests.test_historical_daily_targets
python -m unittest tests.test_nar_historical_daily_target_capture
python -m unittest tests.test_nar_historical_daily_target_live_capture
python -m unittest tests.test_nar_historical_daily_target_source
python -m unittest discover -s tests -p "test_*.py"
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Search review must prove no imports from legacy NAR provider/parser or existing URL
canonicalizers, no JRA/snapshot/manifest/replay/settlement/SQLite/migration path, no
network dependency in either builder, no URL manufacturing, no silent row skip, and no
`target_race_count`.

## Blockers and EXECUTE stop condition

There is no PREPARE blocker: exact official candidate bytes, provenance, checksums, and
all three requested lexical grammars are frozen above. This does not authorize their
implementation.

`EXECUTE_APPROVED_PHASE` must stop without changing code/tests when status is not
`APPROVED_FOR_CODEX`, the branch or Base Commit differs, any official byte cannot be
materialized at its exact reviewed SHA/path, any provenance field would need guessing or
backdating, any grammar conflicts with the reviewed bytes, or any file outside Allowed
Files is needed. It must also stop on a required test failure, unexpected dirty/staged
state, need for dependency/storage/schema/migration work, or any temptation to broaden
zero, `△`, whole-cancellation, original identity, partial-cancellation, or JRA support.

If execution is later authorized and succeeds, it must update only the two documentation
files in addition to the exact Allowed implementation files, set status
`READY_FOR_REVIEW`, run every required check, leave nothing staged, and stop. It must not
commit, push, run replay, or advance to another phase.

## Current PREPARE Allowed Files

Only:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Current PREPARE Forbidden Files and actions

Every other file and every production/test/fixture implementation is forbidden during
PREPARE. Stage, commit, push, acquisition/archive persistence, database mutation,
`EXECUTE_APPROVED_PHASE`, and the next phase are forbidden.

## Required PREPARE verification

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```
