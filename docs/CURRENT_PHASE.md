# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_22`
- Name: `NAR Bootstrap Staged Locator and Supplier Live Capture Implementation`
- Phase type: `IMPLEMENTATION`
- Base Commit: `e69781be682a447154b0cec3d2d3909b6d2eb86d`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `IMPLEMENTABLE`
- Production/tests implementation: `NOT_AUTHORIZED_DURING_PREPARE`
- Stage/commit/push: `NOT_AUTHORIZED`

AGENTS.md and the committed Phase 18 bootstrap, Phase 20 archive and Phase 21 split
decision are authority. The existing public
`resolve_nar_monthly_convene_info_request_identity(...)` signature, behavior and exact
identity output must remain unchanged.

## Objective and scope

Only after a later `EXECUTE_APPROVED_PHASE`, refactor the approved Phase 18 pure parser
into three source-bound staged values usable in live order, and implement a dedicated
bootstrap supplier HTTP capture service:

```text
homepage capture
  -> exact source-owned Monthly-root locator
  -> Monthly-root capture
  -> exact source-owned locator-script resolution plus target tokens
  -> pinned locator-script capture
  -> exact source-owned Monthly request material
```

Each live capture is saved immediately through the Phase 20
`save_supplier_capture` API. This phase does not construct the three-capture aggregate,
call the existing final Monthly request resolver in a live application, acquire Monthly
or RaceList pages, or build a target set. Those sequencing responsibilities remain Phase
23.

## Existing implementation audit

Phase 18 already has one strict HTML tree parser, raw double-quoted attribute grammar,
homepage relation, root year/month controls, locator-script relation and exact pinned
JavaScript grammar. They are currently private and are composed only after all three
captures exist. Their code must be refactored into the staged functions below; copying
those grammars into the new live module is forbidden.

The Phase 6 `NARHistoricalDailyTargetLiveCaptureService` is deliberately closed to an
existing Monthly/RaceList request identity and exact HTML Content-Type. It remains
read-only. Supplier acquisition uses a separate transport/service with equivalent HTTP
safety but the exact three Phase 18 supplier page kinds and MIME values.

The Phase 20 concrete archive already provides the required typed
`save_supplier_capture` method. It remains read-only and migration remains explicit
external setup.

## Immutable staged values

All three values are frozen/slots dataclasses. Constructors require exact field types,
validate their fixed schema/version/page kind, preserve bytes without normalization,
and derive a lowercase SHA-256 stage identity from canonical UTF-8 JSON using
`ensure_ascii=False`, `sort_keys=True`, `separators=(",", ":")` and no NaN. Identity
payloads use byte fields as lowercase hex and UTC/current time is never included.

### `NARMonthlyConveneInfoRootLocator`

```python
@dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoRootLocator:
    homepage_capture_id: str
    homepage_response_sha256: str
    raw_href: bytes
    resolved_url: str
    structural_locator: str
    schema_version: int = field(init=False, default=1)
    page_kind: NARMonthlyConveneInfoBootstrapPageKind = field(
        init=False,
        default=NARMonthlyConveneInfoBootstrapPageKind.MONTHLY_ROOT,
    )
    locator_identity_sha256: str = field(init=False)
    locator_identity: str = field(init=False)
```

The identity prefix is `nar-monthly-bootstrap-root-locator-v1:`. The only accepted raw
href is exact bytes
`/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop`; resolved URL is exactly
`https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop`; structural
locator is the approved unique homepage navigation relation. The value binds the exact
homepage capture ID and response digest.

### `NARMonthlyConveneInfoLocatorScriptResolution`

```python
@dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoLocatorScriptResolution:
    root_locator: NARMonthlyConveneInfoRootLocator
    monthly_root_capture_id: str
    monthly_root_response_sha256: str
    target_date: date
    raw_script_src: bytes
    resolved_script_url: str
    offered_year_token: bytes
    offered_month_token: bytes
    structural_locator: str
    schema_version: int = field(init=False, default=1)
    page_kind: NARMonthlyConveneInfoBootstrapPageKind = field(
        init=False,
        default=NARMonthlyConveneInfoBootstrapPageKind.LOCATOR_SCRIPT,
    )
    resolution_identity_sha256: str = field(init=False)
    resolution_identity: str = field(init=False)
```

The identity prefix is `nar-monthly-bootstrap-script-resolution-v1:` and includes the
root-locator identity, exact root capture ID/digest, target date, raw src/resolved URL,
source-offered tokens and structural locator. It accepts only the qualified raw script
src and URL. Year is selected only from one exact captured `selectedYear` control;
months must be exactly the twelve canonical controls `1` through `12`; the target month
token is selected from that set. Current `selected` option and active tab state remain
non-authoritative.

### `NARMonthlyConveneInfoRequestMaterialResolution`

```python
@dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoRequestMaterialResolution:
    locator_script_resolution: NARMonthlyConveneInfoLocatorScriptResolution
    locator_script_capture_id: str
    locator_script_response_sha256: str
    official_supplied_request_material: bytes
    resolved_request_url: str
    schema_version: int = field(init=False, default=1)
    resolution_identity_sha256: str = field(init=False)
    resolution_identity: str = field(init=False)
```

The identity prefix is `nar-monthly-bootstrap-request-material-v1:`. The payload includes
the Stage B identity and exact script capture ID/digest. Request material is formed only
by the pinned JS grammar's literal path/query fragments and Stage B's captured year/month
tokens. It must exactly construct the existing Monthly request URL and never use a date
template, developer URL builder, eval, browser or JavaScript runtime.

## Staged pure public API

`scripts/simulation/nar_historical_daily_target_bootstrap.py` exposes exactly:

```python
def resolve_nar_monthly_convene_info_root_locator(
    *,
    homepage_capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
) -> NARMonthlyConveneInfoRootLocator: ...

def resolve_nar_monthly_convene_info_locator_script(
    *,
    target_date: date,
    root_locator: NARMonthlyConveneInfoRootLocator,
    monthly_root_capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
) -> NARMonthlyConveneInfoLocatorScriptResolution: ...

def resolve_nar_monthly_convene_info_request_material(
    *,
    locator_script_resolution: NARMonthlyConveneInfoLocatorScriptResolution,
    locator_script_capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
) -> NARMonthlyConveneInfoRequestMaterialResolution: ...
```

Every function reconstructs and compares each supplied existing capture/value before
parsing. Stage B requires `monthly_root_capture.canonical_request_url` and page kind to
equal Stage A output. Stage C requires the script capture URL/page kind to equal Stage B
output and enforces the exact Phase 18 pin:

- URL:
  `https://www.keiba.go.jp/KeibaWeb/resources/js/monthltconveninfo.js?t=20260130_1`
- length: `438` bytes
- SHA-256:
  `bdf86457a9c917fc8259f8b87593c9bbece72d501a95fb5d3573a93b43532515`
- unique frozen `changePage(year, month)` grammar and exactly two approved bindings.

Missing, duplicate, fuzzy, alias, wrong page kind, mismatched capture ID/digest, forged
stage identity, unsupported year/month control, altered JS or cross-stage mismatch fails
closed through the existing Phase 18 validation/unsupported/integrity error families.

The existing final resolver performs existing aggregate integrity validation, then calls
Stage A, Stage B and Stage C and constructs the same
`NARHistoricalDailyTargetRequestIdentity` using Stage C material and the existing
aggregate `supplier_evidence_identity`. Old private relation/JS implementations are
removed or reduced to shared internals used by these functions; two copies are forbidden.

## Supplier live capture boundaries

New module
`scripts/simulation/nar_historical_daily_target_bootstrap_live_capture.py` defines:

```python
class NARMonthlyConveneInfoBootstrapSupplierCaptureArchive(Protocol):
    def save_supplier_capture(
        self,
        *,
        capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
    ) -> None: ...

@dataclass(frozen=True, slots=True)
class _NARMonthlyConveneInfoBootstrapHTTPResponse:
    effective_url: str
    response_body: bytes
    content_type: str
    content_encoding: str | None
    content_length: int | None

class NARMonthlyConveneInfoBootstrapHTTPTransport(Protocol):
    def fetch(
        self,
        *,
        page_kind: NARMonthlyConveneInfoBootstrapPageKind,
        canonical_request_url: str,
    ) -> _NARMonthlyConveneInfoBootstrapHTTPResponse: ...

class RequestsNARMonthlyConveneInfoBootstrapHTTPTransport: ...

class NARMonthlyConveneInfoBootstrapTransportError(
    NARMonthlyConveneInfoBootstrapCaptureError
): ...

class NARMonthlyConveneInfoBootstrapLiveCaptureService:
    def __init__(
        self,
        *,
        archive: NARMonthlyConveneInfoBootstrapSupplierCaptureArchive,
        transport: NARMonthlyConveneInfoBootstrapHTTPTransport,
        utc_clock: Callable[[], datetime],
    ) -> None: ...

    def capture_official_home(
        self,
    ) -> NARMonthlyConveneInfoBootstrapSupplierCapture: ...

    def capture_monthly_root(
        self,
        *,
        homepage_capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
        root_locator: NARMonthlyConveneInfoRootLocator,
    ) -> NARMonthlyConveneInfoBootstrapSupplierCapture: ...

    def capture_locator_script(
        self,
        *,
        monthly_root_capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
        locator_script_resolution: NARMonthlyConveneInfoLocatorScriptResolution,
    ) -> NARMonthlyConveneInfoBootstrapSupplierCapture: ...
```

No capture method accepts an arbitrary URL. `capture_official_home` owns only the exact
fixed trust-anchor `https://www.keiba.go.jp/`. Before root network access, the service
re-runs Stage A from `homepage_capture` and requires exact equality with `root_locator`.
Before script network access, it re-runs Stage B from the embedded Stage A value,
`monthly_root_capture` and the staged target date and requires exact equality. After the
script response is converted to a capture, it runs Stage C before archive save; a pin or
grammar mismatch therefore cannot be published as a successful supplier capture.

The archive Protocol is introduced here because the first real supplier acquisition
consumer now needs dependency inversion. `SQLiteNARDailyTargetEvidenceArchive` satisfies
it structurally without modification. The service never calls `load_supplier_capture`;
live mode is always fresh with no cache fallback.

## Concrete supplier HTTP contract

The concrete transport accepts exact page-kind and URL pairs only; wrong type, host,
scheme, port, path, query, fragment or cross-kind URL is rejected before network. Exact
URLs/MIME types are the existing Phase 18 capture-domain values and are not generated
from dates:

| kind | exact URL | exact Content-Type |
| --- | --- | --- |
| `official_home` | `https://www.keiba.go.jp/` | `text/html` |
| `monthly_root` | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop` | `text/html; charset=UTF-8` |
| `locator_script` | pinned Phase 18 URL above | `application/javascript; charset=UTF-8` |

One `requests.Session` uses `HTTPAdapter(max_retries=0)` on HTTP/HTTPS, exact
`User-Agent: Mozilla/5.0`, GET only, per-request `Accept-Encoding: identity`, streaming,
`allow_redirects=False`, `verify=True`, and timeout `(10.0, 10.0)`. HTTP is never an
accepted request URL despite mounting an adapter for requests behavior parity.

The response must be exact status 200 with unchanged effective URL. Content-Encoding is
absent or exact `identity`; Content-Length is absent or ASCII decimal within the 4 MiB
limit and must equal collected length. Streaming uses bytes only, ignores only empty
chunks, fails immediately beyond 4 MiB and always closes the response. Empty body,
wrong exact MIME, invalid UTF-8 or response/domain mismatch fails closed. Bytes are never
normalized, decompressed by application code, decoded/re-encoded, trimmed or repaired.

Network/request/stream/status/effective-URL/length failures raise the transport error
with the original `requests` cause where applicable. Recognized but unsupported MIME,
encoding or supplier material uses the existing unsupported error. No retries, alternate
URL, search engine, browser, eval, JavaScript execution or fallback exists.

## Clock, capture and archive sequence

Each service method performs exactly:

```text
validate fixed/staged binding
-> requested_at = injected utc_clock()
-> one transport.fetch(...)
-> observed_at = injected utc_clock()
-> stored_at = injected utc_clock()
-> construct exact existing Phase 18 supplier capture
-> Stage C pin validation when locator_script
-> archive.save_supplier_capture(capture=...)
-> return capture
```

Every sample must be an exact timezone-aware `datetime`; the existing capture constructor
enforces `requested_at <= observed_at <= stored_at` and normalizes to UTC. The module has
no `datetime.now`, `datetime.utcnow`, `time.time`, filesystem timestamp or default clock.
These timestamps are honest current acquisition audit metadata only and never prediction,
snapshot, settlement, availability, scheduled-start or backdated historical evidence.

Archive save errors, conflicts and data-integrity errors propagate unchanged and no
capture is returned. Earlier independently saved stages may remain honest audit records,
but the service makes no aggregate/completeness/target-set claim. It never applies or
inspects migration and owns no SQL/database path.

## Compatibility guarantees

- Exact existing final resolver signature and `NARHistoricalDailyTargetRequestIdentity`
  equality, raw request bytes, resolved URL and supplier evidence identity remain
  unchanged for all Phase 18 fixtures/years.
- One parser grammar owns each relation. The live module calls public staged functions
  and contains no HTML/JS grammar or date/query construction.
- Phase 18 capture domain, Phase 20 repository/migration, Phase 6 live transport/source,
  official fixtures and `.gitattributes` remain read-only.
- No production network access is performed by staged pure functions or tests.
- Phase 23 orchestration APIs/types are not implemented here.

## Allowed Files

Only these exact files may change in a later approved execution:

```text
scripts/simulation/nar_historical_daily_target_bootstrap.py
scripts/simulation/nar_historical_daily_target_bootstrap_live_capture.py
tests/test_nar_historical_daily_target_bootstrap.py
tests/test_nar_historical_daily_target_bootstrap_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The live-capture production/test files are new. The existing bootstrap production/test
files change only for the staged values/functions, shared-parser refactor and exact
regression assertions. Every other file is forbidden.

## Forbidden files and non-goals

Do not change the Phase 18 capture domain, Phase 20 archive/migration/tests, Phase 6
capture/live/source files or tests, fixtures, `.gitattributes`, main/settlement databases,
schemas/migrations, CLI, evidence resolver, manifest, replay, prediction, settlement,
betting, reporting, JRA, release tag or history. Never modify/stage `database/keiba.db` or
`logs/`.

No target-date all-day acquisition application, aggregate construction, Monthly or
RaceList live orchestration, target-set building, offline mode, cache lookup, migration
setup or Daily Orchestrator is implemented in Phase 22.

## Required Tests

`tests/test_nar_historical_daily_target_bootstrap.py` must add/retain:

1. Stage A exact raw homepage href, resolved URL, structural locator and source capture
   ID/digest;
2. Stage A missing, duplicate, fuzzy, alias and wrong-kind relation failures;
3. Stage B exact raw JS src/resolved URL and root capture binding;
4. Stage B missing/duplicate/wrong JS relation failures;
5. target years 2020, 2021, 2024, 2025 and 2026 explicitly offered;
6. absent/duplicate/malformed target year failure;
7. exactly twelve canonical month controls required;
8. exact target month token and unpadded source token preservation;
9. selected year/current active tab state is not authority;
10. staged identity deterministic repeat and byte-sensitive digest;
11. forged stage identity and cross-capture ID/digest/URL mismatch rejection;
12. Stage C exact pinned JS acceptance and exact request-material output;
13. JS URL/length/digest/grammar/duplicate function/event-binding mutation rejection;
14. no eval/browser/JS runtime/date-template request generation;
15. existing final resolver exact identity/output unchanged and all prior Phase 18 tests
    remain PASS.

`tests/test_nar_historical_daily_target_bootstrap_live_capture.py` must prove:

16. homepage performs one exact GET and archives before return;
17. root consumes matching Stage A+homepage and performs one exact staged GET;
18. script consumes matching Stage B+root and performs one exact staged GET;
19. arbitrary URL cannot be supplied through public service signatures;
20. wrong URL/page-kind/host/scheme/port/path/query/fragment rejected before network;
21. redirects disabled, TLS verify true, streaming true, exact User-Agent and
    `Accept-Encoding: identity`;
22. adapter retry count is exactly zero and only one GET occurs;
23. non-200, effective URL mismatch and requests exception fail closed/close response;
24. body limit, malformed/oversized/mismatched Content-Length and non-byte stream fail;
25. exact per-kind Content-Type and absent/identity Content-Encoding only;
26. empty or invalid UTF-8 body rejected without archive save;
27. exact bytes including CRLF/trailing whitespace reach capture/archive unchanged;
28. injected requested/observed/stored clock order is honest and normalized losslessly;
29. wrong/naive/non-datetime/out-of-order clock samples fail closed;
30. homepage, root and pinned script are each saved immediately;
31. archive save failure/conflict/integrity propagates and returns no capture;
32. Stage A/B mismatch blocks network; pinned JS mismatch blocks archive;
33. previously saved capture is never loaded as fallback and every invocation is fresh;
34. no browser, eval, direct current clock, migration, SQL or cache fallback;
35. Phase 20 supplier API works as the archive without modification.

Execution must run:

```text
python -m unittest tests.test_nar_historical_daily_target_bootstrap tests.test_nar_historical_daily_target_bootstrap_live_capture
python -m unittest tests.test_nar_historical_daily_target_bootstrap_capture tests.test_nar_daily_target_evidence_archive_migration tests.test_sqlite_nar_daily_target_evidence_archive tests.test_nar_historical_daily_target_capture tests.test_nar_historical_daily_target_live_capture tests.test_nar_historical_daily_target_source
python -m unittest discover -s tests -p "test_*.py"
```

Dedicated tests must also pass with `-W error::ResourceWarning`. Static boundary search
must prove the new live module has no browser/Selenium/Playwright, eval/exec,
`datetime.now`, `datetime.utcnow`, `time.time`, retry above zero,
`allow_redirects=True`, migration invocation, SQL, cache/load fallback, HTML/JS parser
grammar or date-derived URL construction. It must also prove existing Phase 6 live files
are unchanged.

Tests use injected fake transports/sessions/clocks and temporary or in-memory Phase 20
archives only. They perform no network and do not change official fixtures, provider
archives, databases or logs. Failures may not be skipped or relaxed.

## Stop Condition

During PREPARE stop at `DRAFT_FOR_REVIEW`, with only the two docs changed and cached
state empty. No implementation, test modification, stage, commit, push or Phase 23 work
is authorized.

During a later approved execution, stop without guessing if the existing final resolver
identity/output changes; approved parser grammar would need duplication; a staged value
cannot be bound to its exact source capture; the pinned JS differs; Phase 20 archive or
Phase 6 live code would need modification; another file is required; or any dedicated,
related, ResourceWarning, full-suite, static or Git scope check fails.

Successful execution requires all 35 behavior groups and existing regressions to pass,
only the six Allowed Files to change, `git diff --check` to pass, cached state to remain
empty, no database/log change, docs to record exact results, and Status to become
`READY_FOR_REVIEW`. Stage, commit and push remain separately gated.
