# Current Phase

Phase: `POST_V0_8_DAILY_REPLAY_44`
Name: `NAR Race-Entry Status Raw Capture Bundle Implementation`
Type: `IMPLEMENTATION`
Status: `APPROVED_FOR_COMMIT`
Formal State: `FORMALLY_COMPLETE`
Execution Result: `IMPLEMENTED`
Base: `972a1fb201ad360d1c729b120d5ac10aa1556a42`
Branch: `feature/post-v0.8-daily-replay`

## Authority, goal, and stop condition

Phase43 is the complete design authority. Phase44 implements only its state-neutral, deterministic, fail-closed, NAR-only capture boundary:

```text
exact target race
 -> deterministic DebaTable request -> exact raw DebaTable capture
 -> deterministic RaceList day request -> exact raw RaceList capture
 -> immutable closed two-document bundle
```

It does not parse HTML, infer entry status/eligibility, reconcile race entries, choose a prediction cutoff, persist data, publish fixtures, call JRA, or perform a discovery request. Phase43 was implemented literally without policy changes and without live HTTP.

Phase44 implementation review returned `PASS_FOR_INTEGRATION`. The formal integration is restricted to the exact four-file commit and normal branch push. The boundary remains state-neutral: no live HTTP, future-information inference, HTML/status parsing, or persistence occurred. The only changed files are exactly:

```text
scripts/simulation/nar_race_entry_status_raw_capture.py
tests/test_nar_race_entry_status_raw_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Everything else remains unchanged and forbidden, including Phase32/36 modules, the Phase40 parser, fixtures, manifest, `.gitattributes`, `database/**`, `logs/**`, migrations, repositories, and package metadata. Stop at `READY_FOR_REVIEW`; no staging, commit, push, integration, or subsequent-phase work is authorized.

## Audited reuse decisions

| Existing component | Decision | Phase44 use |
| --- | --- | --- |
| `scripts/simulation/nar_market_odds_capture.py` | **REUSE_PATTERN_ONLY** | Frozen dataclass, canonical payload, raw SHA, and fail-closed validation pattern. Do not import odds types, helpers, URLs, or prefixes. Its datetime text uses `+00:00`, which is not Phase44’s required `Z` serialization. |
| `scripts/simulation/nar_market_odds_raw_acquisition.py` | **REUSE_PATTERN_ONLY** | Fresh closed session, `trust_env=False`, HTTPS-only `HTTPAdapter(max_retries=0)`, raw streaming, injected clock, narrow error translation, forged-value checks, and cleanup pattern. Do not import odds symbols or modify this module. |
| `tests/test_nar_market_odds_capture.py` | **REUSE_PATTERN_ONLY** | Literal canonical JSON/digest and derived-field test structure. |
| `tests/test_nar_market_odds_raw_acquisition.py` | **REUSE_PATTERN_ONLY** | Fake transport/clock, concrete mocked requests transport, raw bytes, no-retry, static boundary, and side-effect test strategy. |
| `requests` 2.34.2 / `urllib3` 2.7.0 | **REUSE_DIRECTLY** | `requests.Session` and `HTTPAdapter`; the current `urllib3._collections.HTTPHeaderDict.getlist("Content-Length")` preserves repeated values for the required duplicate-header check. |
| `nar_official_response_capture.py` and `nar_historical_daily_target_capture.py` | **REUSE_PATTERN_ONLY** | DebaTable/RaceList canonical URL and strict raw-capture leads. Do not reuse their archive/supplier identity semantics. |
| Existing private canonical JSON/datetime helpers | **DO_NOT_REUSE** | They are private, live in disallowed modules, or serialize UTC as `+00:00`; Phase44 implements its approved `Z` serialization locally. |

## Exact public module API

The new module exports exactly these public symbols:

```text
NARRaceEntryStatusRawCaptureError
NARRaceEntryStatusRawCaptureValidationError
NARRaceEntryStatusRawCaptureTransportError
NARRaceEntryStatusRawCaptureUnsupportedResponseError
NARRaceEntryStatusRawCaptureBundleIntegrityError
NARRaceEntryStatusDayScope
NARRaceEntryStatusRaceIdentity
NARRaceEntryStatusPageKind
NARRaceEntryStatusRequestIdentity
NARRaceEntryStatusRawHTTPResponse
NARRaceEntryStatusResponseCapture
NARRaceEntryStatusRawCaptureBundle
NARRaceEntryStatusRawCaptureTransport
NARRaceEntryStatusRawCaptureClock
RequestsNARRaceEntryStatusRawCaptureTransport
build_nar_race_entry_status_request_identity
acquire_nar_race_entry_status_raw_capture_bundle
```

No new public type is needed: `NARRaceEntryStatusRaceIdentity` is the exact typed race request scope (`baba_code`, `race_date`, `race_no`), and `NARRaceEntryStatusDayScope` is the exact typed venue-day scope (`baba_code`, `race_date`). `NARRaceEntryStatusRequestIdentity` retains Phase43’s exact `page_kind`, `day_scope`, and `request_race_no` inputs. The page-kind/builder relation admits only: `DEBA_TABLE` plus a race number, or `RACE_LIST` plus `request_race_no is None`.

Both value objects are frozen/slotted. `baba_code` is exact built-in `str` matching `[1-9][0-9]*`; `race_date` is exact `date` but not `datetime`; and every `race_no` is exact positive built-in `int`, never `bool`.

```python
class NARRaceEntryStatusPageKind(StrEnum):
    DEBA_TABLE = "deba_table"
    RACE_LIST = "race_list"

@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusRequestIdentity:
    page_kind: NARRaceEntryStatusPageKind
    day_scope: NARRaceEntryStatusDayScope
    request_race_no: int | None
    canonical_request_url: str = field(init=False)
    request_identity_sha256: str = field(init=False)
    request_identity: str = field(init=False)
```

`build_nar_race_entry_status_request_identity(...)` is the sole construction authority. It validates scope/page compatibility, derives the URL, literal payload, SHA, and identity. Acquisition canonically rederives a supplied request before any clock or transport access, so forged/missing/wrong-type derived fields become `NARRaceEntryStatusRawCaptureValidationError` with zero transport calls and zero clock calls.

## Exact request, canonical JSON, and scalar contracts

Origin is exactly `https://www.keiba.go.jp`.

```text
DEBA_TABLE
/KeibaWeb/TodayRaceInfo/DebaTable
?k_babaCode={baba_code}&k_raceDate={YYYY%2FMM%2FDD}&k_raceNo={race_no}

RACE_LIST
/KeibaWeb/TodayRaceInfo/RaceList
?k_raceDate={YYYY%2FMM%2FDD}&k_babaCode={baba_code}
```

Query order, canonical decimal `baba_code`/Deba race number, `YYYY%2FMM%2FDD` query date, uppercase `%2F`, and the absence of `k_raceNo` from RaceList are exact. There is no current-date/current-race/discovery default, alternate URL, or `"race_no": null` request payload key.

All three identity domains use exactly:

```python
json.dumps(
    payload,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

It produces compact UTF-8, recursively sorted keys, and no newline. `SHA256(...).hexdigest()` is exactly 64 lowercase ASCII hexadecimal characters. No repr, locale, filesystem path, current clock, NaN, or Infinity participates. Dates are `YYYY-MM-DD`; aware datetimes are converted to UTC and serialized exactly `YYYY-MM-DDTHH:MM:SS.ffffffZ` (including `.000000Z`). Naive datetimes fail closed. Semantic integers are JSON integers and reject bool.

The literal request payloads, capture payload, bundle payload, null/omission policy, identity prefixes, and self-hash exclusions are exactly those frozen in Phase43. In particular:

```text
request: nar-race-entry-status-request-v1:{request_identity_sha256}
capture: nar-race-entry-status-capture-v1:{capture_sha256}
bundle:  nar-race-entry-status-raw-bundle-v1:{bundle_sha256}
```

No digest or prefixed identity is included in its own payload.

## Raw HTTP, response capture, and validation order

The response types and closed metadata mapping are exactly:

```python
@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusRawHTTPResponse:
    effective_url: str
    response_body: bytes
    http_status: int
    content_type: str | None
    content_encoding: str | None
    http_date: str | None
    etag: str | None
    last_modified: str | None
    content_length: int | None

@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusResponseCapture:
    request_identity: NARRaceEntryStatusRequestIdentity
    effective_url: str
    response_body: bytes
    charset: str
    requested_at: datetime
    observed_at: datetime
    captured_at: datetime
    http_status: int
    content_type: str | None = None
    content_encoding: str | None = None
    http_date: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_length: int | None = None
    response_sha256: str = field(init=False)
    byte_length: int = field(init=False)
    capture_sha256: str = field(init=False)
    capture_id: str = field(init=False)
```

The accepted entity profile is exact: status `200`; effective URL exactly equal to the canonical request URL; Content-Type exactly `text/html; charset=UTF-8` through direct exact string equality (no trim/case/MIME parameter normalization); canonical capture charset `UTF-8`; strict UTF-8 bytes; nonempty built-in `bytes`; Content-Encoding absent/`None` or exact `identity`; and at most `4 * 1024 * 1024` bytes per document.

Raw authority is exact:

```text
response_sha256 = SHA256(raw_response_bytes).hexdigest()
response_byte_length = len(raw_response_bytes)
```

No decode/re-encode precedes hashing; strict decoding validates only; no newline/HTML/Unicode normalization or semantic body inspection occurs.

The retained metadata whitelist is exactly Content-Type, Content-Encoding, Date, ETag, Last-Modified, and Content-Length, canonically keyed as `content_type`, `content_encoding`, `date`, `etag`, `last_modified`, `content_length`. The capture payload always contains those six keys; absent values are JSON `null`. Set-Cookie, Cookie, Authorization, CSRF/session material, request headers, and all other headers are dropped. HTTP Date is diagnostic only.

Concrete response validation order is fixed:

```text
1. validate/rederive request before opening a session
2. issue the one GET
3. require exact integer HTTP 200
4. require exact effective URL
5. require exact Content-Type
6. require Content-Encoding absent/identity
7. inspect raw repeated Content-Length header values; require zero or one
8. validate Content-Length grammar and pre-read 4 MiB bound when present
9. set response.raw.decode_content = False and raw-stream body in 64 KiB chunks
10. require body <= 4 MiB, nonempty bytes, and declared length equality
11. map only the six whitelisted metadata values and return the typed raw response
```

Content-Length is read from `response.raw.headers.getlist("Content-Length")`, not from the potentially folded `response.headers` mapping. The concrete raw header object must expose callable `getlist`; absence or a non-list-like result is `NARRaceEntryStatusRawCaptureTransportError`, while any count other than zero/one is `NARRaceEntryStatusRawCaptureUnsupportedResponseError`. This is observable in the installed urllib3 `HTTPHeaderDict` and is modeled in tests with a fake raw headers object. The one present raw string must full-match `(?:0|[1-9][0-9]*)\Z`, have no whitespace/sign/comma/exponent/leading zero except `0`, parse to an integer, and equal raw body length. Duplicate values fail even if textually equal. An absent header becomes metadata `content_length: null`; a valid `0` still fails later because the body itself must be nonempty.

## Exact transport and clock execution

```python
class NARRaceEntryStatusRawCaptureTransport(Protocol):
    def fetch(
        self, *, request_identity: NARRaceEntryStatusRequestIdentity
    ) -> NARRaceEntryStatusRawHTTPResponse: ...

class NARRaceEntryStatusRawCaptureClock(Protocol):
    def now_utc(self) -> datetime: ...

def acquire_nar_race_entry_status_raw_capture_bundle(
    *,
    target: NARRaceEntryStatusRaceIdentity,
    transport: NARRaceEntryStatusRawCaptureTransport,
    clock: NARRaceEntryStatusRawCaptureClock,
) -> NARRaceEntryStatusRawCaptureBundle: ...
```

`RequestsNARRaceEntryStatusRawCaptureTransport.fetch` creates and closes one new `requests.Session` for each document. It sets `trust_env=False`, clears session headers, mounts `HTTPAdapter(max_retries=0)` only for `https://`, and closes response/session in `finally`. Thus DebaTable and RaceList never share cookies, credentials, adapter state, or connection/session state.

The one GET receives exactly:

```text
User-Agent: Mozilla/5.0
Accept: text/html,application/xhtml+xml
Accept-Encoding: identity
stream=True
allow_redirects=False
verify=True
timeout=(10.0, 20.0)
```

No authentication, browser, JavaScript, HTTP origin, retry, HEAD, OPTIONS, probe, alternate endpoint, arbitrary URL, or JRA operation exists.

Before any sampling, acquisition validates target and builds both canonical request identities. It then samples exactly:

```text
1 Deba requested_at: immediately before DebaTable transport.fetch
2 Deba observed_at: immediately after the complete DebaTable raw response returns
3 Deba captured_at: immediately before DebaTable response-capture construction
4 RaceList requested_at: immediately before RaceList transport.fetch
5 RaceList observed_at: immediately after the complete RaceList raw response returns
6 RaceList captured_at: immediately before RaceList response-capture construction
```

After each observed sample, acquisition validates the typed raw response/profile; only a valid response gets its captured sample and immutable capture construction. Both successful captures must satisfy:

```text
deba.requested_at <= deba.observed_at <= deba.captured_at
    <= race_list.requested_at <= race_list.observed_at <= race_list.captured_at
```

There is no seventh clock call or bundle timestamp. Individual timestamps are authoritative; the bundle makes no provider-atomicity claim.

Failure-path clock-call counts are fixed by attempted `now_utc()` calls:

| Failure point | Clock calls | GETs | Outcome |
| --- | ---: | ---: | --- |
| target/request identity validation | 0 | 0 | validation error |
| Deba requested sample fails | 1 | 0 | validation error |
| Deba transport fails | 1 | 1 Deba | transport error; RaceList not dispatched |
| Deba observed sample/raw response profile fails | 2 | 1 Deba | validation/unsupported response; no bundle |
| Deba captured sample/capture construction fails | 3 | 1 Deba | validation/unsupported response; no bundle |
| RaceList requested sample fails | 4 | 1 Deba | validation error; no RaceList GET |
| RaceList transport fails | 4 | 2 | transport error; no bundle |
| RaceList observed sample/raw profile fails | 5 | 2 | validation/unsupported response; no bundle |
| RaceList captured sample/capture construction or bundle validation fails | 6 | 2 | validation/unsupported/bundle-integrity error; no bundle |

## Bundle and exception contract

```python
@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusRawCaptureBundle:
    target_race_identity: NARRaceEntryStatusRaceIdentity
    deba_table_capture: NARRaceEntryStatusResponseCapture
    race_list_capture: NARRaceEntryStatusResponseCapture
    bundle_sha256: str = field(init=False)
    bundle_id: str = field(init=False)
```

Its payload and identity are exactly Phase43’s literal canonical bundle schema: algorithm name `nar-race-entry-status-raw-bundle`, version `v1`, order `["deba_table", "race_list"]`, schema/version, organization/source, target triple, and each document’s request SHA, capture ID, response SHA, and three semantic timestamps. It contains no raw bytes, parser facts, horse data, eligibility, path, or bundle self-hash.

Bundle validation order is fixed:

```text
1. require exact bundle-member capture types and page kinds
2. require DebaTable request scope equals target baba_code/race_date/race_no
3. require RaceList request scope equals target baba_code/race_date and has no race number
4. require the full six-timestamp sequential relation
5. derive canonical bundle payload, SHA, and prefixed bundle ID
```

RaceList is day-scoped only. The raw bundle never claims that its RaceList body contains or proves the target race row; later qualification/parser work owns that extraction.

The public hierarchy is exact:

```text
NARRaceEntryStatusRawCaptureError(Exception)
├─ NARRaceEntryStatusRawCaptureValidationError
├─ NARRaceEntryStatusRawCaptureTransportError
├─ NARRaceEntryStatusRawCaptureUnsupportedResponseError
└─ NARRaceEntryStatusRawCaptureBundleIntegrityError
```

Validation covers target/request/typed response/capture/timestamp/clock contradictions. Transport covers requests/network, raw-header API, and raw-stream failures. Unsupported response covers HTTP/profile failures, including status, MIME, charset, content encoding, duplicate/malformed/mismatched Content-Length, empty/oversized body, and effective URL. Bundle integrity covers exact page/scope/order contradictions. Requests exceptions and named low-level `KeyError`, `IndexError`, `AttributeError`, `TypeError`, header/library errors are translated narrowly with causes retained; neither broad `Exception` nor `BaseException` is caught.

Deba failure aborts before RaceList; RaceList failure leaves only a transient in-memory Deba capture; scope/bundle mismatch returns no bundle. There is no optional/degraded authoritative result and no persistence side effect.

## Tests and verification

The exact dedicated test file is `tests/test_nar_race_entry_status_raw_capture.py`. No numeric test count is authoritative; every group below is mandatory:

```text
request URL order and literal canonical payload/hash for both documents
derived URL/SHA/identity constructor-injection and forged-field rejection
race/day scope typing, bool/zero/negative/malformed values, no defaults
same/different request/capture/bundle identity determinism
raw Japanese/CRLF/LF/one-byte preservation; response-byte/timestamp identity changes
strict HTTP/MIME/charset/effective URL/encoding/nonempty-body profile
six-key metadata whitelist and sensitive-header exclusion
Content-Length absent, valid zero/positive, each malformed grammar case,
duplicate equal/unequal raw headers, declared-length mismatch, and 4 MiB bound
exact two-GET DebaTable -> RaceList order, header/timeout/TLS/redirect/no-retry,
fresh-session cleanup, no third request, and each failure-path clock-call count
closed-bundle page/scope/timestamp failures; deterministic bundle identity
static/architecture proof of no parser, network alternatives, DB/filesystem/log/fixture/cache,
current-date default, arbitrary URL, or JRA dependency
```

Use fake transport and deterministic injected clock for acquisition tests. Concrete requests transport tests mock `requests.Session`, a raw stream, and a raw headers object whose `getlist` returns exact duplicate lists; no live HTTP is required. No-side-effect coverage combines static AST/import audit with fakes that would fail if filesystem/database methods are reached.

After execution run, at minimum:

```text
python -m pytest -q tests/test_nar_race_entry_status_raw_capture.py
python -W error::ResourceWarning -m pytest -q tests/test_nar_race_entry_status_raw_capture.py
python -m pytest -q tests/test_nar_market_odds_capture.py tests/test_nar_market_odds_raw_acquisition.py
python -m pytest -q tests/test_nar_market_odds_source_profile_fixtures.py tests/test_nar_market_odds_source_parser.py
python -m pytest -q tests/test_ranking_probability.py
python -m pytest -q tests/test_nar_daily_replay_aggregation.py tests/test_nar_daily_replay_orchestrator.py tests/test_nar_daily_replay_result_persistence.py
python -m pytest -q tests/test_nar_*.py tests/test_sqlite_nar_*.py
python -m pytest -q
python -m compileall -q scripts/simulation/nar_race_entry_status_raw_capture.py
```

Also run the dedicated static forbidden-boundary audit, deterministic repeated-identity audit, `git diff --check`, changed-path audit, cached-state audit, fixture/manifest/attribute audit, and `git status --short`.

## Implementation and verification evidence

The frozen public API, exception hierarchy, exact canonical request/capture/bundle payloads, URL ordering, derived request fields, UTC timestamp format, and immutable values are implemented in `scripts/simulation/nar_race_entry_status_raw_capture.py`. The concrete transport uses a fresh state-neutral session for each document, exact headers/options, raw undecoded streaming, the 4 MiB per-document bound, and `response.raw.headers.getlist("Content-Length")`; it rejects missing multiplicity support, duplicate headers, noncanonical header text, and length contradictions. Acquisition performs DebaTable then RaceList, produces exactly six injected clock samples on success, enforces the complete sequential relation, and exposes no partial bundle.

Verification results on the final implementation state:

```text
dedicated Phase44: 91 passed
dedicated Phase44, ResourceWarning as error: 91 passed
Phase36 / Phase32 capture-acquisition: 40 passed, 48 subtests passed
Phase38 / Phase40 fixture-parser: 56 passed
Phase30 ranking probability: 24 passed, 24 subtests passed
Phase25/27/28 daily replay core: 51 passed, 23 subtests passed
all NAR (31 explicitly expanded Windows paths): 523 passed, 584 subtests passed
full pytest: 3,597 passed, 2,841 subtests passed
focused deterministic identities: PASS
compile / static forbidden-boundary audit: PASS
```

The PREPARE-recorded literal pytest wildcard is not expanded by this Windows/PowerShell invocation; the all-NAR run therefore explicitly expands the exact `test_nar_*.py` and `test_sqlite_nar_*.py` path sets rather than changing test scope. No live HTTP or evidence persistence occurred.

## Permanent boundaries and dependencies

Phase44 must not inspect raw body content for `horseNum`, `td.horseNum`, `出走取消`, cancellation text, DOM, entries, horse names, eligibility, or race state. It imports no BeautifulSoup/parser and has no regex over HTML body. It writes no SQLite/database row, migration, filesystem archive, fixture, manifest, log evidence, or cache.

Phase40 remains `FORMALLY_COMPLETE`. Phase41 remains `DESIGN_BLOCKED`; raw capture alone does not unblock it. Still required are controlled real source-state acquisition, qualification, deterministic DebaTable/RaceList parsing, immutable provider-level entry/status evidence, then a new reconciliation preparation.

Both dependencies remain `OPEN`:

```text
COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE
NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE
```

## Git gate

Final gate: branch and local/remote HEAD remain `feature/post-v0.8-daily-replay` / `972a1fb201ad360d1c729b120d5ac10aa1556a42`; exactly the four Allowed Files differ, cache is empty, and Phase32/36/40 code, fixtures, manifest, `.gitattributes`, database, and logs are unchanged. `git diff --check` passes. All work remains unstaged, uncommitted, and unpushed.

Formal completion preserves Phase41 as `DESIGN_BLOCKED` and does not establish market eligibility. Stop after this integration; no subsequent phase is authorized.
