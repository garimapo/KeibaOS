# Current Phase

Status: `READY_FOR_REVIEW`

## Identity

- Phase: `POST_V0_8_DAILY_REPLAY_36`
- Name: `NAR Official Market Odds Raw Acquisition Harness Implementation`
- Phase type: `IMPLEMENTATION`
- Base Commit: `7f62cd0e0e91fd3fb2acdb62ad490d345c72a097`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `IMPLEMENTED`
- Open dependency: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`

Phase 33 and Phase 34 remain `DESIGN_BLOCKED`: neither qualified exact OPEN raw source grammar.
Phase 36 implements the Phase35-approved raw acquisition boundary without classifying OPEN, FINAL,
suspended, unavailable, cancelled, scratched, or unknown HTML. Classification occurs only after exact
raw bytes exist. No parser, Decimal, EV, archive write, fixture write, resolver, scheduler, or JRA work
is authorized here.

## Implementation scope

Only the exact four files listed below may change. No fixtures, migrations, `database/**`, or `logs/**`
may change. No stage, commit, or push is authorized.

## Read-only source qualification

Read-only direct retrieval from the Phase32 canonical official URL succeeded: HTTP 200, exact effective
URL, `Content-Type: text/html; charset=UTF-8`, no `Content-Encoding`, and strict UTF-8 Japanese bytes.
No body was saved. A `Set-Cookie` response header was observed and is excluded from all capture/fixture
metadata. Direct official HTTPS transport, Phase32 UTF-8, no compression, and exact effective-URL
contracts are therefore compatible. This says nothing about source state or selector grammar.

## Implemented Phase36 public API

The implementation is library-only:
no CLI, automatic crawl, filesystem publication, SQLite archive write, or live request in tests.

```python
class NARMarketOddsRawAcquisitionError(Exception): pass
class NARMarketOddsRawAcquisitionValidationError(NARMarketOddsRawAcquisitionError): pass
class NARMarketOddsRawAcquisitionTransportError(NARMarketOddsRawAcquisitionError): pass
class NARMarketOddsRawAcquisitionUnsupportedError(NARMarketOddsRawAcquisitionError): pass

@dataclass(frozen=True, slots=True)
class NARMarketOddsRawAcquisitionTarget:
    request_identity: NARMarketOddsRequestIdentity

@dataclass(frozen=True, slots=True)
class NARMarketOddsRawHTTPResponse:
    effective_url: str
    response_body: bytes
    http_status: int
    content_type: str | None
    content_encoding: str | None
    http_date: str | None
    etag: str | None
    last_modified: str | None
    content_length: int | None

class NARMarketOddsRawAcquisitionTransport(Protocol):
    def fetch(self, *, request_identity: NARMarketOddsRequestIdentity,
              requested_at: datetime) -> NARMarketOddsRawHTTPResponse: ...

class NARMarketOddsRawAcquisitionClock(Protocol):
    def now_utc(self) -> datetime: ...

def acquire_nar_market_odds_raw_response(
    *, target: NARMarketOddsRawAcquisitionTarget,
    transport: NARMarketOddsRawAcquisitionTransport,
    clock: NARMarketOddsRawAcquisitionClock,
) -> NARMarketOddsResponseCapture: ...

class RequestsNARMarketOddsRawAcquisitionTransport:
    def fetch(self, *, request_identity: NARMarketOddsRequestIdentity,
              requested_at: datetime) -> NARMarketOddsRawHTTPResponse: ...
```

`target.request_identity` is the exact Phase32 type; the harness reconstructs it from its page kind and
race identity and requires equality. It accepts no arbitrary URL/path/host, horse name, current date,
race discovery result, or JRA target. Consequently only Phase32 `ODDS_TAN_FUKU`, `ODDS_UM_LEN_FUKU`,
`ODDS_WIDE`, and `ODDS_3_LEN_FUKU` can be requested. The returned object is constructed exactly as
Phase32 `NARMarketOddsResponseCapture`; no alternative URL/body SHA/request/capture identity exists.

`ValidationError` is malformed target, clock, transport value, or impossible harness input.
`TransportError` is network/timeout/redirect/non-200/size failure. `UnsupportedError` is a syntactically
valid official response outside the frozen raw profile. Phase32 errors map to validation or unsupported
as appropriate; repository/parser error types never appear here.

## Frozen one-request and timestamp contract

One invocation makes exactly one canonical request, gets exactly one HTTP response, and returns one
Phase32 capture. There is no retry, pagination, multi-request assembly, sleep, timestamp rewriting, or
backdating. The injected clock is called exactly three times: immediately before dispatch
(`requested_at`), immediately after full body/metadata return (`observed_at`), and immediately before
Phase32 construction (`captured_at`). It must return exact timezone-aware datetimes already satisfying
`requested_at <= observed_at <= captured_at`; Phase32 remains free of a hidden current clock.

## Frozen HTTP, bytes, charset, and header contract

`RequestsNARMarketOddsRawAcquisitionTransport` is the only concrete HTTP implementation. Per call it
uses a fresh non-persistent `requests.Session`, `GET`, TLS verification, `stream=True`,
`allow_redirects=False`, `HTTPAdapter(max_retries=0)`, and timeout `(10.0, 20.0)` seconds. It sends
exactly `User-Agent: Mozilla/5.0`, `Accept: text/html,application/xhtml+xml`, and
`Accept-Encoding: identity`; it sends no Cookie, Authorization, Referer, Origin, conditional request,
authentication, POST, browser, or JavaScript state. It reads no more than `4 * 1024 * 1024` bytes with
content decoding disabled.

The only accepted URL is the regenerated Phase32 canonical URL at exact origin
`https://www.keiba.go.jp`; the effective URL must equal it exactly. Any redirect, URL variation, or
non-200 response is `TransportError`. Only exact `Content-Type: text/html; charset=UTF-8` and absent
`Content-Encoding` or exact `identity` are accepted. Other encoding fails `UnsupportedError` before
decode, preventing decompressed-byte/header contradiction. Body bytes pass unchanged to Phase32, which
strictly validates UTF-8 and computes the authoritative SHA/length; no decode/re-encode, normalization,
HTML parsing, or content transformation is permitted. `Content-Length`, if present, is a canonical
non-negative decimal integer and must equal raw byte count.

Only these headers are retained: `Content-Type`, `Content-Encoding`, `Date`, `ETag`, `Last-Modified`,
and `Content-Length`, mapped to the identically intended Phase32 metadata fields. `Set-Cookie`, Cookie,
Authorization, session/CSRF/request IDs, and all other headers are discarded and never written/logged.

## Deferred fixture publication and state qualification

Fixture publication is not in Phase36, so no fixture API, identity/prefix, manifest, path, or raw file
is yet authorized. The acquisition function has no filesystem side effect. A separately prepared Phase37
will review captured public bytes, publish immutable parser-source-profile fixtures, and qualify only
then OPEN/FINAL/UNKNOWN state/profile grammar. Fixtures must not be auto-promoted to historical replay,
prediction, T-5, EV, or settlement evidence. State cannot be inferred from filename, race date, or clock.

## Allowed Files and verification

```text
scripts/simulation/nar_market_odds_raw_acquisition.py
tests/test_nar_market_odds_raw_acquisition.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Tests use a fake transport and deterministic injected clock. They prove exact Phase32 request forwarding;
one fetch/no retry; raw Japanese/non-ASCII preservation; timestamps; 200 acceptance; non-200,
URL/redirect, content type/encoding, content-length, malformed clock, and transport failure rejection;
whitelist mapping and Set-Cookie non-retention; no arbitrary URL/current target/backdating; and no
parser, Decimal, EV, repository/archive, JRA, fixture, database, or log side effects.

Verification results:

```text
dedicated Phase36 with ResourceWarning-as-error: 28 passed
Phase32/NAR/Phase30/Phase25/27/28 related suite: 204 passed
full unittest discovery: 3231 passed
focused compilation/static audit: passed
official one-target read-only smoke: passed (200, utf-8, no encoding, URL exact)
```

The smoke body was neither displayed nor saved. The full/related suites emit pre-existing unrelated
SQLite `ResourceWarning`s; the dedicated Phase36 suite is clean.

Final review correction: `_canonical_request` now validates the exact Phase32 page-kind and race
identity structure before reading nested fields or invoking the Phase32 builder. Target-derived
Phase32 validation and malformed/missing race fields map to exact
`NARMarketOddsRawAcquisitionValidationError`. Forged page-kind, forged race identity, and forged exact
race identity with missing fields all fail before clock sampling or transport invocation; both counts
remain zero.

Focused re-review correction: the exact remaining reproducer removed
`canonical_request_url` from the frozen Phase32 request object, causing dataclass equality to leak
`AttributeError`. The narrow request boundary now safely reads and exact-type-checks every Phase32
derived request field, then compares the supplied value with the independently re-derived Phase32
request under structural error translation. Missing canonical URL, missing request digest, and a
wrong-type canonical URL all produce exact `NARMarketOddsRawAcquisitionValidationError` before clock
or transport use, with the original structural failure retained as cause where applicable.

## Blocker-resolution sequence

```text
Phase35 design -> Phase36 fake-transport-tested harness -> Phase37 controlled official fixture review
and source-state qualification -> revised Phase33 parser design -> pure parser implementation
```

OPEN selector grammar is not a Phase36 blocker. Transport blockers would only be inaccessible official
HTTPS, non-UTF-8 bytes, incompatible effective URL, or unavoidable non-identity compression; none were
found. Phase33/34 stay blocked pending actual fixture qualification.

## Stop condition

Before stopping: exact branch/base; exact four Allowed Files only; cached empty; `database/**`,
`logs/**`, and fixture paths unchanged; `git diff --check` passes. The Phase34 blocker is bypassed by
state-neutral raw acquisition. Phase33 and Phase34 remain `DESIGN_BLOCKED` pending Phase37's controlled
fixture acquisition and qualification. The dependency remains open.

Stop at `READY_FOR_REVIEW`; do not stage, commit, push, or prepare Phase37.
