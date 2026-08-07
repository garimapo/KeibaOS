# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1b — NAR supplied-raw historical source normalization preparation

## Base Commit

`96e70d17f66f85689f568c7603977afdb508e31b feat: add historical input source record domain`

## Branch

`feature/ver0.8-simulator`

## Canonical Workspace

`C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is read-only for this phase.

## Objective and Frozen Boundaries

The future c1b implementation is the smallest fail-closed, no-network boundary that turns one already supplied
official NAR response into a deterministic tuple of committed c1a `HistoricalInputSourceRecord` values. It does
not fetch HTTP, write a raw-response store, read a database, use legacy records, build a
`HistoricalInputSnapshot`, or change an existing provider or parser.

`scripts/simulation/historical_input_source_records.py` is frozen exactly as committed in `96e70d1`: its six
record kinds, nine-key digest envelope, URL ownership boundary, timestamp rules, schemas, absence proof, and
conflict rules are not redesigned. c1b owns only NAR URL canonicalization, supplied-byte decoding, page dispatch,
and conversion of verified official page facts into those records.

## Investigation Findings

The tracked `horse_page.html` is a supplied official NAR DebaTable example. It declares
`<meta charset="utf-8">` and contains these official URL forms:

```text
https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable
  ?k_raceDate=2026%2F07%2F16&k_raceNo=10&k_babaCode=32

https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/OddsTanFuku
  ?k_raceDate=2026%2F07%2F16&k_raceNo=10&k_babaCode=32
```

The DebaTable fixture exposes `h4` target-date/place/race-number/start-time text,
`section.raceTitle h3`, `p.subTitle`, and `ul.dataArea > li:first-child` race facts. Its entry table uses
`td.horseNum`, `a.horseName`, `a.jockeyName`, and `td.odds_weight > span.odds_*`; it also contains a horse-detail
href and past `RaceMarkTable` links. It does **not** provide a complete past-race payload, a stable official
past-race record ID, a completed scoped zero-result search response, or provider publication time.

Existing `NARProvider` performs live requests, guesses a response encoding with `apparent_encoding`, and writes
logs. `NARParser`, `HorseParser`, and `PastRaceParser` are lossy legacy adapters: they omit official key/timing
facts, use float/zero fallbacks, and/or persist legacy values. They are evidence for selectors only and are not
reused by c1b. `horses.odds`, legacy past-race rows, results, payouts, settlements, database files, and old parser
logs are forbidden source facts.

## Exact Supplied-response Boundary

The future module defines one frozen, slotted dataclass:

```python
@dataclass(frozen=True, slots=True)
class NarSuppliedOfficialResponse:
    response_url: str
    response_body: bytes
    charset: Literal["utf-8"]
    observed_at: datetime
```

`response_url` is the final successfully supplied official response URL, not a request file name, filesystem path,
legacy DB URL, redirect chain, or generated aggregate URL. c1b validates and canonicalizes it under the policy
below. `response_body` is exact `bytes`, rather than `str`, so response identity and decoding stay at the supplied
capture boundary. `charset` must be exact lower-ASCII `"utf-8"`; c1b decodes `response_body` with strict UTF-8
and requires the parsed document to declare `meta[charset="utf-8"]`. No apparent-encoding heuristic, replacement
decode, BOM fallback, or parser-runtime timestamp is allowed. `observed_at` is exact `datetime`, timezone-aware,
and denotes successful response-byte receipt before parsing; it is normalized by c1a. There is no input
`available_at`: the supported NAR page contains no official publication instant, so every produced record has
`available_at=None`.

## NAR DebaTable URL Canonicalization and Dispatch

c1b initially supports only the official target-race page kind `DebaTable`. It accepts an absolute HTTPS URL with
host `www.keiba.go.jp` (case-insensitive input, lowercase output), absent or `443` port (absent output), no
credentials, fragment, control characters, or trailing slash. The path is exactly
`/KeibaWeb/TodayRaceInfo/DebaTable`, with exact case. Any other path, including `RaceList`, `CompeteTable`,
`DebaTableSmall`, `OddsTanFuku`, `RaceMarkTable`, and horse-detail pages, is unsupported rather than guessed.

The query has exactly one occurrence of each case-sensitive key and no other key:

```text
k_babaCode
k_raceDate
k_raceNo
```

Duplicate keys, blank keys, unknown keys, malformed percent escapes, `+`-as-space ambiguity, and values requiring
Unicode normalization are rejected. `k_raceDate` is exactly ASCII `YYYY/MM/DD` for a real calendar date.
`k_babaCode` and `k_raceNo` are positive canonical ASCII decimal tokens: no sign, whitespace, leading zero,
place-name substitution, inferred value, or zero-padding. The canonical output URL uses the exact path, lowercase
host, no port, and query ordering `k_babaCode`, `k_raceDate`, `k_raceNo`; it percent-encodes the two date slashes
as uppercase `%2F` and leaves ASCII decimal tokens unescaped. Query, path, or official displayed identity ambiguity
fails closed.

Page kind is identified only from that canonical path, never from arbitrary HTML. A valid DebaTable response must
have the same real `k_raceDate` and displayed target race number as its URL; URL/content disagreement is a source
validation failure.

## External Identity

For the canonical DebaTable URL, future c1b constructs exactly:

```text
external_race_id = nar:{YYYYMMDD}:{k_babaCode}:{k_raceNo}
external_entry_id = {external_race_id}:entry:{horseNum}
```

`YYYYMMDD` is the real URL `k_raceDate` without separators. `k_babaCode` and `k_raceNo` retain their validated
official canonical spelling. `horseNum` comes from one direct `td.horseNum`, must be a positive canonical decimal
integer, and is rendered base-10 without leading zeros. The displayed `horseNum` and URL race identity must agree;
duplicate horse numbers or a row whose official number cannot be unambiguously parsed fail closed. The horse-detail
URL is not a proven stable horse identity, so `external_horse_id` is exactly `None`; local IDs and hashes are never
substituted.

## Initial Record-kind Support Matrix

| c1a record kind | c1b status | Official supplied source and rule |
| --- | --- | --- |
| `track` | SUPPORTED | One canonical DebaTable URL plus its title/data area; one record per response. |
| `entry` | SUPPORTED | One non-cancelled DebaTable row with direct `td.horseNum`; all rows must be complete and unique. |
| `jockey` | SUPPORTED | The matching row's one `a.jockeyName`; direct display text only. |
| `odds_win` | SUPPORTED | The matching row's one `td.odds_weight > span.odds_*`, when every supported row exposes a positive decimal. |
| `past_race` | UNSUPPORTED | Existing links and legacy parser lack the required complete payload and stable official `provider_record_id`. URL must not be repurposed as that ID. |
| `past_race_absence` | UNSUPPORTED | No complete official zero-result search endpoint/scope is evidenced. Empty HTML or an empty parser result is not absence proof. |

`OddsTanFuku` is an observed official link but lacks a supplied fixture and selector contract, so it is not a c1b
page kind. Unsupported pages and unavailable/cancelled/non-numeric/zero odds fail with the explicit unsupported or
validation error; c1b never silently omits a required record.

## Exact DebaTable Extraction Policy

All display text is obtained from the prescribed node, NFC-normalized, all Unicode whitespace runs collapsed to one
ASCII space, then stripped. This is c1b-owned HTML-display cleanup; no NFKC conversion, case folding, inferred
value, or c1a trimming is used. Required normalized text must be non-empty. Japanese text is retained as supplied.

| c1a field | Required official source | Rule |
| --- | --- | --- |
| `target_race_date` | canonical URL `k_raceDate` and `article.raceCard h4` | both parse to the same real date; URL supplies the date value. |
| `scheduled_start_at` | `article.raceCard h4` target `HH:MM発走` | exact 24-hour `HH:MM`; combine with target date as `Asia/Tokyo`, preserving an aware instant. |
| `place` | `article.raceCard h4` | the normalized target-place segment between date and race number. |
| `race_name` | `section.raceTitle h3` | normalized non-empty text; c1a optional field receives text when present, otherwise `None`. |
| `race_class` | `section.raceTitle p.subTitle` | normalized text or `None`; no classification inference. |
| `distance_m`, `track`, `weather`, `track_condition` | `section.raceTitle ul.dataArea > li:first-child` | require exactly one target distance token and one each of official course, `天候：`, and `馬場：` token; distance is positive integer metres. |
| `horse_no` | row's direct `td.horseNum` | exact positive decimal; no display-order fallback. |
| `jockey` | row's one `a.jockeyName` direct text nodes excluding `span.jockeyarea` | normalized non-empty official rider text. |
| `win_odds` | row's one `td.odds_weight > span` with an `odds_*` class | exact positive ASCII decimal, parsed directly to `Decimal`; float is forbidden. |

`entry` records use `external_horse_id=None`; `jockey` and `odds_win` repeat the exact external entry ID. The
page's race/horse/detail links, trainer, popularity, weight, result tables, and prior-race snippets do not become
source records. Any missing or multiple required selector/value, malformed Japanese race header, missing required
track token, unsupported cancellation marker, URL/content race mismatch, horse-number mismatch, duplicate entry,
or invalid odds fails closed.

## Temporal Evidence, Determinism, and Errors

Each generated record has fixed `organization="NAR"`, `source_system="nar_official"`, the canonical DebaTable URL,
`provider_record_id=None`, `available_at=None`, and the response object's unchanged `observed_at`. c1a constructs
and validates the deterministic `his-v1:*` source ID; no timestamp, raw bytes, file path, local row, or parser
order joins that digest.

The normalizer returns a tuple ordered exactly as: the one `track` record first, then each validated `horse_no`
ascending with its `entry`, `jockey`, and `odds_win` records in that order. The HTML's original row order is not
observable output. The completed tuple must pass `validate_historical_input_source_record_set(...)`.

The module has only these public names:

```text
NarSuppliedOfficialResponse
NarHistoricalInputSourceError
NarHistoricalInputSourceValidationError
NarHistoricalInputSourceUnsupportedError
normalize_nar_historical_input_source_records
```

`NarHistoricalInputSourceError` is a minimal c1a-source-error subtype. Its validation subtype covers malformed
supplied response, URL, charset, HTML identity, selector, text, and odds facts. Its unsupported subtype covers a
recognized but unauthorized page kind or an official page state that cannot yield the complete supported tuple.
c1a `HistoricalInputSourceValidationError` or conflict errors from final record construction propagate unchanged;
there is no repository exception, broad wrapping, retry, fallback, or network/file/database access.

## Candidate Allowed and Forbidden Files

The only proposed c1b implementation files are:

```text
scripts/simulation/nar_historical_input_source.py
tests/test_nar_historical_input_source.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Existing providers, parsers, fetchers, migrations, schema, repositories, package `__init__`, README, main/CLI,
database files, logs, and all existing tests are forbidden. If a future implementation needs any of them changed,
the phase is `REVISION_REQUIRED`; it may not broaden scope itself.

## Required Future Tests and Verification

Dedicated deterministic UTF-8 byte fixtures must cover the exact public surface; frozen/slotted response fields;
strict URL canonicalization; required/duplicate/unknown query keys; page dispatch; external race/entry identity;
track/entry/jockey/Decimal odds extraction; Japanese whitespace cleanup; complete tuple ordering; observed-at
propagation; `available_at is None`; c1a record/set validation and deterministic IDs; missing/ambiguous selectors;
URL/content and horse-number conflicts; cancellation/unavailable/zero/non-numeric odds; unsupported page,
past-race, and absence behavior; no DB/network/filesystem/legacy fallback; and no package-root export.

One integration fixture must produce track plus at least two entries, jockeys, and odds records in deliberately
noncanonical HTML row order, then prove the canonical tuple passes the c1a set validator. No live HTTP test and no
`HistoricalInputSnapshot` construction are authorized.

The future phase must run its dedicated suite, the c1a source-record suite, historical snapshots/repository/migration
regressions, the full suite, source/AST forbidden-dependency checks, `git diff --check`, and `git status --short`.

## Stop Conditions

This is preparation only. No c1b production or test implementation is authorized. Stop for ChatGPT design review
after publishing only these two documentation files to the dedicated review branch. c1c snapshot building, provider
collection, raw persistence, JRA normalization, migration/schema work, and all database use remain out of scope.

blocker: no persisted supplied NAR raw/capture corpus exists; initial c1b is limited to caller-supplied DebaTable
responses and cannot construct past-race or absence records.
