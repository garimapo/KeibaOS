# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_21`
- Name: `NAR Daily Target Live Acquisition Design`
- Phase type: `DESIGN_ONLY`
- Base Commit: `6b412f515918c955a166edb6f7dd5fdbcdccd142`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `SUPPLIER_TRANSPORT_SPLIT_REQUIRED`
- Production/tests implementation: `NOT_AUTHORIZED`
- Stage/commit/push: `NOT_AUTHORIZED`

AGENTS.md and committed Phase 6, Phase 18 and Phase 20 contracts are authority. This
phase composes them conceptually and does not change their capture, request identity,
archive, normalization or target-set semantics.

## Goal and boundary

Freeze the production path from an exact NAR `target_date` through current official
supplier acquisition and every required venue capture to one audited complete
`DailyHistoricalReplayTargetSet`:

```text
target_date
  -> official homepage capture/archive
  -> source-owned Monthly-root relation
  -> exact Monthly-root capture/archive
  -> source-owned locator-script relation
  -> exact pinned locator-script capture/archive
  -> NARMonthlyConveneInfoBootstrapEvidence
  -> existing resolve_nar_monthly_convene_info_request_identity
  -> existing Monthly live capture/archive
  -> existing strict Monthly normalization
  -> every exact envelope-supplied RaceList live capture/archive
  -> existing complete NAR target-set builder
```

The path stops after producing the audited target set and acquisition audit references.
It does not invoke the evidence resolver, schema-v1 manifest projection, historical
replay runner, prediction, settlement, betting, reporting or result persistence.

## Read-only audit findings

### Existing transport reuse

`NARHistoricalDailyTargetLiveCaptureService` and
`NARHistoricalDailyTargetHTTPTransport` already own the closed Monthly/RaceList HTML
transport boundary: supplied request identity only, GET, `requests.Session`, retries 0,
`Accept-Encoding: identity`, redirects disabled, TLS verification, explicit 10-second
connect/read timeouts, 4 MiB bounded streaming, strict Content-Length, exact effective
URL, exact HTTP 200 and `text/html; charset=UTF-8`, injected aware clock samples and
archive-before-return. They can be reused unchanged for Monthly and every RaceList.

They cannot safely acquire bootstrap supplier pages: their request type is the Phase 6
Monthly/RaceList identity and their Content-Type is closed to HTML, while the supplier
chain also needs the pinned JavaScript type. Widening that class would weaken a reviewed
closed transport and is forbidden. A separate supplier transport/service is required.

### Staged source relation gap

The Phase 18 resolver strictly validates homepage→Monthly root, root year/month controls,
root→locator JavaScript and the pinned JavaScript grammar, but its public entry point
accepts an already complete three-capture aggregate. Its reusable parsing functions are
private and do not expose a source-owned root locator before root acquisition or a
source-owned script locator before script acquisition.

The live sequence must not copy that HTML grammar into a new transport/application or
fetch root/script from developer literals before proving the preceding official
relation. Therefore a minimal Phase 18 parser refactor must expose staged read-only
locator functions while retaining the existing final resolver as authority. This is a
reviewable prerequisite to the acquisition application.

### Existing archive and target construction

`SQLiteNARDailyTargetEvidenceArchive` supplies both typed save families after explicit
external migration. It performs exact-ID append-only persistence and must remain
unchanged. `normalize_nar_monthly_convene_info` already returns exact raw RaceList hrefs,
existing `NARHistoricalDailyTargetRequestIdentity` preserves their bytes and query
order, and `build_nar_historical_daily_replay_target_set` already enforces envelope,
fragment and same-day navigation set equality. None is duplicated.

## Split decision

Outcome is `SUPPLIER_TRANSPORT_SPLIT_REQUIRED`.

The next implementation must contain only staged supplier-relation exposure and the
supplier HTTP capture service. It must receive independent code review before a later
implementation adds the all-day acquisition application. Combining a new HTTP boundary,
HTML/JS relation refactor, archive integration and multi-venue sequencing in one phase
would unnecessarily couple transport safety review to no-partial orchestration review.

Planned phases:

1. `POST_V0_8_DAILY_REPLAY_22` — `NAR Bootstrap Supplier Live Capture Implementation`.
2. `POST_V0_8_DAILY_REPLAY_23` — `NAR Daily Target Live Acquisition Application`.

Each needs separate PREPARE/review/approval/execution/commit gates. Phase 23 must not
start until Phase 22 is reviewed and remotely committed.

## Phase 22 staged relation contract

The existing `nar_historical_daily_target_bootstrap.py` will expose exactly three new
public functions by refactoring, not duplicating, its approved private grammar:

```python
def resolve_nar_monthly_root_supplier_url(
    *,
    homepage_capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
) -> str: ...

def resolve_nar_monthly_locator_script_supplier_url(
    *,
    target_date: date,
    monthly_root_capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
) -> str: ...

def validate_nar_monthly_locator_script_capture(
    *,
    locator_script_capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
) -> None: ...
```

The first function requires one exact approved raw homepage href and returns its exact
resolved official URL. The second requires the exact root URL, unique required year
control, exact offered target year, exact month set 1..12, exact target month and one raw
approved script src, then returns the exact resolved script URL. The third enforces the
Phase 18 pinned URL, 438-byte length, SHA-256 and exact `changePage`/two-event-binding
grammar.

The existing `resolve_nar_monthly_convene_info_request_identity` must call these same
functions internally and retain exact output/regression behavior. No parser grammar,
URL literal, canonicalization or identity rule is copied into the live-capture module.
No new domain value is necessary.

## Phase 22 supplier transport/capture API

New module `nar_historical_daily_target_bootstrap_live_capture.py` will define:

```python
class NARMonthlyConveneInfoBootstrapSupplierCaptureArchive(Protocol):
    def save_supplier_capture(
        self,
        *,
        capture: NARMonthlyConveneInfoBootstrapSupplierCapture,
    ) -> None: ...

class NARMonthlyConveneInfoBootstrapHTTPTransport(Protocol):
    def fetch(
        self,
        *,
        page_kind: NARMonthlyConveneInfoBootstrapPageKind,
        canonical_request_url: str,
    ) -> _NARMonthlyConveneInfoBootstrapHTTPResponse: ...

class RequestsNARMonthlyConveneInfoBootstrapHTTPTransport: ...

class NARMonthlyConveneInfoBootstrapLiveCaptureService:
    def capture_official_homepage(
        self,
    ) -> NARMonthlyConveneInfoBootstrapSupplierCapture: ...

    def capture_supplied_response(
        self,
        *,
        page_kind: NARMonthlyConveneInfoBootstrapPageKind,
        canonical_request_url: str,
    ) -> NARMonthlyConveneInfoBootstrapSupplierCapture: ...
```

`capture_official_homepage` is the only fixed starting request and uses exact
`https://www.keiba.go.jp/`. Other page kinds accept only the exact URL returned by the
staged Phase 18 relation function. Before network, the service/transport requires the
exact Phase 18 URL for the supplied page kind; no arbitrary official URL is accepted.

The concrete transport uses one GET, official HTTPS host, `requests.Session`, HTTPAdapter
retries 0, `Accept-Encoding: identity`, redirects false, TLS verify true, explicit
10-second connect/read timeouts, streamed body bounded to 4 MiB, strict Content-Length
when supplied, exact status 200 and unchanged effective URL. It accepts only the Phase
18 exact Content-Type for each kind: `text/html`, `text/html; charset=UTF-8`, or
`application/javascript; charset=UTF-8`. Content-Encoding is absent or exact `identity`.
Every response is strict UTF-8 but stored as the original bytes without decode/re-encode.

The service samples injected `utc_clock` exactly at requested, observed and stored
boundaries, constructs the existing immutable supplier capture, archives it through
`save_supplier_capture`, and returns only after save succeeds. For locator JavaScript it
also calls `validate_nar_monthly_locator_script_capture` before archive publication, so a
changed current asset fails closed and is never silently adopted.

Supplier transport/capture errors subclass the existing Phase 18 supplier capture error
family. Archive and domain exceptions retain their original types and causes. No clock,
network client, session, archive or migration is constructed globally or implicitly.

## Phase 23 acquisition application contract

After Phase 22 approval, a single new sequencing module will define:

```python
@dataclass(frozen=True, slots=True)
class NARDailyTargetLiveAcquisitionResult:
    supplier_capture_ids: tuple[str, str, str]
    supplier_evidence_identity: str
    monthly_capture_id: str
    race_list_capture_ids: tuple[str, ...]
    target_set: DailyHistoricalReplayTargetSet

class NARDailyTargetLiveAcquisitionApplication:
    def __init__(
        self,
        *,
        archive: NARDailyTargetLiveEvidenceArchive,
        supplier_transport: NARMonthlyConveneInfoBootstrapHTTPTransport,
        daily_target_transport: NARHistoricalDailyTargetHTTPTransport,
        utc_clock: Callable[[], datetime],
    ) -> None: ...

    def acquire(
        self,
        *,
        target_date: date,
    ) -> NARDailyTargetLiveAcquisitionResult: ...
```

The combined archive Protocol requires the Phase 20 supplier methods and unchanged
Phase 6 daily capture methods. The constructor composes both reviewed live services with
the same caller-supplied migrated archive and injected clock; it never opens SQLite,
applies migration or constructs a hidden transport/session/clock.

The immutable result validates the fixed supplier order `(homepage, monthly_root,
locator_script)`, non-empty unique capture IDs, Monthly ID, canonically ordered unique
RaceList IDs and exact target-set type. It is an audit result, not replay success or ROI.

## Exact Phase 23 sequence

1. Capture/archive the exact official homepage through
   `capture_official_homepage`.
2. Resolve the root URL from that capture using the staged Phase 18 function.
3. Capture/archive that exact Monthly root URL.
4. Resolve the locator-script URL and target year/month support from the root capture.
5. Capture, pin-validate and archive that exact locator JavaScript.
6. Construct `NARMonthlyConveneInfoBootstrapEvidence` from the three exact returned
   primary captures.
7. Call existing `resolve_nar_monthly_convene_info_request_identity` for the exact
   `target_date`.
8. Call existing `NARHistoricalDailyTargetLiveCaptureService` for that Monthly request;
   its archive save must finish before normalization.
9. Call existing `normalize_nar_monthly_convene_info` and retain every returned locator.
10. Require unique locator request identities/baba codes, sort only by numeric
    `baba_code` then exact request identity for deterministic acquisition order, and call
    the existing daily live service exactly once for every locator without a cap.
11. Only after every capture/save succeeds, call existing
    `build_nar_historical_daily_replay_target_set` with the Monthly capture and complete
    RaceList capture tuple.
12. Construct the result with IDs in the acquisition order and the exact target set.

The application does not parse HTML, build URLs/requests, issue HTTP directly, write SQL,
load a cache, calculate completeness, or transform target-set content.

## Live versus archived mode decision

Phase 23 selects Option A: `acquire` always performs a fresh current official acquisition
for the complete chain and appends new immutable captures. It accepts no capture IDs and
does no archive lookup. Existing stored evidence is never an implicit fallback after a
network, relation, normalization or save failure.

An offline exact-ID reconstruction API is not added in Phase 21-23. A later separately
reviewed phase may compose Phase 20 exact loads with the existing Phase 18 resolver and
Phase 6 builders. Tests may prove deterministic reconstruction explicitly through those
existing APIs, but live and offline modes must not be mixed behind one method.

Repeated live acquisition can produce new honest timestamps and capture IDs. It is not
claimed deterministic. Given the same exact archived captures, the existing resolver
and builders must reproduce the same supplier evidence identity and target-set content
digest.

## No-partial and failure semantics

Any incomplete supplier chain, transport failure, relation/parser failure, pinned-JS
mismatch, archive failure, Monthly failure, Monthly normalization failure, missing or
duplicate locator, any RaceList failure, or target-set builder failure returns no
`NARDailyTargetLiveAcquisitionResult` and no target set. Underlying reviewed domain,
transport, repository and `TargetDiscoveryIncompleteError` exceptions propagate without
retry, reduction, replacement URL or conversion to success.

Captures committed before a later failure remain honest immutable audit records. They do
not prove bootstrap completion, provider-day completeness, zero races or a partially
successful target set. The application never skips a venue, uses a successful subset,
falls back to old archived bytes, generates a missing locator, selects a nearby capture,
or retries another URL.

Only exact constructor/caller misuse needs a narrow
`NARDailyTargetLiveAcquisitionValidationError(ValueError)`. It must not wrap underlying
operational/integrity causes. Global archive corruption yields no partial application
result.

## Clock and causal isolation

Current time is permitted only through the injected aware `utc_clock` for honest live
requested/observed/stored capture timestamps. `datetime.now`, `datetime.utcnow`,
`time.time`, filesystem timestamps, backdating and inferred provider availability are
forbidden.

Supplier and daily-target acquisition timestamps are audit metadata only. They never
become prediction provenance, HistoricalInputSnapshot timestamps/information cutoff,
settlement cutoff, provider `available_at`, scheduled start or historical backdated
observation.

## Setup and ownership

The caller explicitly applies Phase 20 migration to a dedicated archive DB, constructs
`SQLiteNARDailyTargetEvidenceArchive`, supplies the supplier and daily transport objects
and one injected aware UTC clock, then constructs the application. Neither live service
nor application owns migration, SQL, database paths, archive recovery or schema repair.

The application owns sequencing only. Parsers own formal source grammar; capture domains
own immutable identities; transports own bounded HTTP; the archive owns atomic
append-only persistence; target builders own completeness. Main and settlement DBs are
never opened or modified.

## Current Phase 21 Allowed Files

PREPARE changes only:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Every production, test, fixture, schema, migration, database, archive, `.gitattributes`,
CLI and release-history file is forbidden. Stage, commit and push are forbidden during
PREPARE.

## Proposed Phase 22 Allowed Files

```text
scripts/simulation/nar_historical_daily_target_bootstrap.py
scripts/simulation/nar_historical_daily_target_bootstrap_live_capture.py
tests/test_nar_historical_daily_target_bootstrap_live_capture.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

The existing bootstrap file may change only to expose/refactor the three staged public
functions and make the existing final resolver call them. Existing bootstrap capture
domain, Phase 6, Phase 20, fixtures and tests remain read-only. Existing related tests
must still pass.

## Proposed Phase 23 Allowed Files

```text
scripts/simulation/nar_daily_target_live_acquisition.py
tests/test_nar_daily_target_live_acquisition.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

All Phase 6/18/20/22 production remains read-only in Phase 23.

## Required later tests

Phase 22 must prove:

1. exact homepage GET and archive-before-return;
2. wrong homepage URL/host/scheme and fuzzy/duplicate/missing homepage relation blocked;
3. redirect, non-200, changed effective URL, timeout/request error blocked;
4. bounded body, malformed/mismatched Content-Length and non-byte stream blocked;
5. exact root source-owned locator and one exact root GET;
6. root redirect/non-200/wrong Content-Type blocked;
7. exact target year and month 1..12 controls required;
8. exact source-owned JS locator and one exact JS GET;
9. pinned JS URL/438-byte/SHA/grammar/event binding mismatch blocked before archive;
10. per-kind exact Content-Type, absent/identity encoding and strict UTF-8;
11. raw bytes, CRLF/trailing whitespace and response length preserved;
12. injected requested/observed/stored clock order and archive save failure propagation;
13. no retry, alternate host/path, search, fallback, browser, eval or direct clock;
14. no migration/SQL and Phase 20 archive interface compatibility;
15. existing Phase 18 resolver output and all Phase 18 regressions unchanged.

Phase 23 must prove:

16. three supplier captures archived and aggregate rebuilt in exact chain order;
17. supplier relation/save failure stops before the next dependent step and returns no
    result;
18. Monthly identity is produced only by the existing Phase 18 resolver;
19. Monthly and RaceList acquisition use the existing daily live service semantics;
20. Monthly is archived before strict normalization;
21. every raw RaceList href/request identity is preserved without reconstruction;
22. all unique locators are acquired in deterministic baba-code order with no first-N,
    five-race or venue cap;
23. one RaceList transport/archive failure returns no result/target set;
24. no partial subset reaches the target-set builder;
25. earlier independently committed captures remain loadable after later failure but do
    not imply completeness;
26. duplicate/missing/extra locator and builder coverage mismatch fail closed;
27. no cache lookup, silent cached fallback, retries or alternate URL;
28. no direct HTTP, browser/eval, clock, SQL or migration in the application;
29. result contains exact unique supplier, Monthly and ordered RaceList IDs plus target
    set;
30. same exact archived captures rebuild deterministic evidence and target set through
    existing APIs;
31. live timestamps never enter prediction/settlement causal fields;
32. main/settlement databases remain untouched;
33. Phase 6, Phase 18, Phase 20 and Phase 22 regressions pass;
34. dedicated phases produce no new ResourceWarning; and
35. full unittest suite and static boundaries pass.

Tests must use injected fake transports/clocks and temporary or in-memory dedicated
archives. Unit/integration tests perform no network and never modify formal provider
archives, `database/keiba.db`, logs or frozen official fixtures.

## Remaining blocker before Daily Orchestrator

The reviewed supplier transport/staged relation boundary and the separately reviewed
all-day acquisition application are both absent. Until Phase 22 and Phase 23 complete,
date-only live target discovery is unavailable and no Daily Orchestrator implementation
may begin. Archive migration remains an explicit deployment/setup responsibility.

## Stop Condition

Stop Phase 21 at `DRAFT_FOR_REVIEW` after changing only the two docs, with cached state
empty. Do not implement, test, stage, commit, push or start Phase 22.

Any future implementation stops without guessing if staged locator exposure would alter
the Phase 18 final resolver, if the current pinned JS differs, if the existing daily live
service cannot be reused unchanged, if another file/schema/migration is needed, or if a
required dedicated/related/full/static/Git check fails. No failure may be converted into
a partial target set.
