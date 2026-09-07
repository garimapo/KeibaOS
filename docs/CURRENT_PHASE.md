# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity, authority and authorization

- Phase: `POST_V0_8_DAILY_REPLAY_17`
- Name: `NAR MonthlyConveneInfo Bootstrap Qualification`
- Phase type: `RESEARCH_AND_DESIGN_ONLY`
- Base Commit: `23278208c24b7c34aad4f4525aba5d429f510c5b`
- Branch: `feature/post-v0.8-daily-replay`
- Qualification outcome: `BOOTSTRAP_PROFILE_IMPLEMENTABLE`
- Production/test/fixture implementation: `NOT_AUTHORIZED`
- Stage/commit/push: `AUTHORIZED_FOR_EXACT_PHASE_DOCS`

AGENTS.md and the approved Phase 2 through Phase 6 NAR daily-target contracts are
authority. Phase 16 was committed and normally pushed; fetch confirmed local HEAD and
`origin/feature/post-v0.8-daily-replay` equal the Base Commit above before PREPARE.
This phase qualifies only the missing MonthlyConveneInfo request-identity bootstrap.
It does not change the existing Phase 6 request/capture/source domains.

## Objective and decision

The initial supported bootstrap is a composite official-source relation:

```text
exact captured NAR homepage
  -> one raw official MonthlyConveneInfo root href
exact captured MonthlyConveneInfo root
  -> one raw locator-script src + official year/month control tokens
exact captured locator script
  -> exact source-owned changePage(year, month) output grammar
target_date selects an exact offered year token and exact month token
  -> existing NARHistoricalDailyTargetRequestIdentity
```

This relation is sufficient to construct the exact MonthlyConveneInfo request identity
without deriving a URL from an undocumented convention. The target date only selects
two exact values that the captured official DOM exposes; the official captured script
owns the literal path, query names, parameter order, separators and concatenation
order. Missing or ambiguous evidence never falls back to a developer template.

Automatic bootstrap is therefore qualified **only when all exact supplier captures and
the complete relation above are supplied and valid**. A date alone remains insufficient.
If any required capture or relation is absent, v0.9 operation must require the caller's
already validated exact MonthlyConveneInfo locator/evidence or fail closed.

## Official research boundary and observations

Research used read-only GET requests to `https://www.keiba.go.jp` only, with
`User-Agent: Mozilla/5.0`, `Accept-Encoding: identity`, redirects disabled, and strict
UTF-8 decoding. Bytes were held outside the repository/in memory and were not added to
fixtures, archives or databases. The observations below are research material, not
formal replay dataset evidence.

| Role/date | Exact request URL | Requested/observed UTC | Bytes | SHA-256 |
| --- | --- | --- | ---: | --- |
| NAR homepage | `https://www.keiba.go.jp/` | `2026-09-07T13:02:28.320400+00:00` / `2026-09-07T13:02:28.575160+00:00` | 37,763 | `84c9d175fbb7e0c814639afda8fd414d62f5caf0cc625f6a1dec6ae6b8e379e4` |
| Monthly root | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop` | `2026-09-07T12:51:22.973023+00:00` / `2026-09-07T12:51:23.310186+00:00` | 194,872 | `7df5219922d696f040f6212d06c34b3c097c2b41b44a704da4b6b8ebfee79a4f` |
| Locator script | `https://www.keiba.go.jp/KeibaWeb/resources/js/monthltconveninfo.js?t=20260130_1` | `2026-09-07T12:51:23.311512+00:00` / `2026-09-07T12:51:23.320740+00:00` | 438 | `bdf86457a9c917fc8259f8b87593c9bbece72d501a95fb5d3573a93b43532515` |
| 2020-03 | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2020&k_month=3` | `2026-09-07T12:51:23.320791+00:00` / `2026-09-07T12:51:23.802876+00:00` | 210,531 | `bedc55f4eb038794b8f728435507f4d2785ab42927bbc4e92f75cd1b9f4282f7` |
| 2021-01 | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2021&k_month=1` | `2026-09-07T12:51:23.803893+00:00` / `2026-09-07T12:51:24.280311+00:00` | 209,487 | `cc4e5f919241bbc04a4c7127f02b39e1e435beaba0d6821866825ef1d259e5eb` |
| 2024-01 | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2024&k_month=1` | `2026-09-07T12:51:24.281041+00:00` / `2026-09-07T12:51:24.770478+00:00` | 209,745 | `54d2a6e3b492680637eb7047d6faaa18d789a8dfdd9797e016a0113cfa9e0e4d` |
| 2025-01 | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2025&k_month=1` | `2026-09-07T12:51:24.771211+00:00` / `2026-09-07T12:51:24.923049+00:00` | 209,768 | `74a4c479b134a831121820a69815e8eb66db0f360c5433330bf7cf61fabdddef` |
| 2026-01 | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=2026&k_month=1` | `2026-09-07T12:51:24.923767+00:00` / `2026-09-07T12:51:25.393956+00:00` | 208,198 | `59d7504b522bcd1da0e2bf8e35979f7827b3c43d46a92ed5cc0b75ed1e91a6c4` |

All responses were exact HTTP 200 responses with no effective-URL change. Homepage and
TodayRaceInfo research both exposed the exact raw root href
`/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop`. The root exposed exactly one raw
`monthltconveninfo.js` script src. Its strict bytes and digest exactly match the Phase 6
offline parser/source-contract fixture; this observation does not promote that fixture
to formal replay evidence.

The root exposed unique year options from 2026 through 1998, including every required
research year, and twelve exact month-tab tokens. Every tested historical response
selected the requested year, activated the requested month, retained twelve month
tokens, and referenced the same raw locator-script src. These checks qualify the
navigation relation; they do not expand Phase 6 supported target-date, zero-day or
exceptional-state semantics.

## Frozen supplier evidence boundary

The bootstrap resolver consumes an immutable, provider-specific supplier evidence
value containing exactly three complete captures:

1. an official NAR homepage HTML capture;
2. the MonthlyConveneInfo root HTML capture addressed by the homepage's raw href; and
3. the locator-script capture addressed by the Monthly root's raw script src.

Each capture must retain its exact request identity/material, exact resolved/effective
official URL, exact complete response bytes, response SHA-256, strict charset,
requested_at, observed_at, stored_at, HTTP status and relevant response metadata. Each
has a deterministic immutable capture identity. The aggregate evidence retains the
ordered homepage-link -> root-script -> script relation and its own deterministic
identity; it is not independent primary evidence.

The Phase 17 research bytes and timestamps above are not automatically materialized as
future fixtures. A later implementation PREPARE must freeze exact fixture paths,
provenance and digests or use synthetic parser cases. No SQLite repository, migration,
schema or durable archive is designed by this phase.

The existing `NARHistoricalDailyTargetResponseCapture` is not widened: it remains
closed to MonthlyConveneInfo and RaceList final source captures. The existing
`NARHistoricalDailyTargetRequestIdentity` is not changed. Bootstrap supplier capture
types are separate because the root HTML and JavaScript media type cannot truthfully be
represented by its existing closed page-kind/content contract.

## Frozen structural locator grammar

### Homepage to Monthly root

The strict homepage normalizer requires exactly one accepted navigation anchor whose
raw UTF-8 href lexeme is exactly:

```text
/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop
```

It resolves only that captured raw lexeme against exact origin
`https://www.keiba.go.jp`. It does not hard-code a dated Monthly URL, follow a search
result, infer a path from page existence, or accept host/path aliases. Duplicate,
missing, malformed or contradictory anchors fail closed.

### Monthly root controls and script relation

The strict root normalizer requires:

- one `select#selectedYear[name="k_year"]`;
- one unique option whose exact canonical ASCII value and collapsed text equal
  `str(target_date.year)`;
- one `ul.monthTab` containing exactly one `li#monthTabN.tab[month="N"]` for every
  canonical unpadded N in 1 through 12, with matching `N月` text;
- exactly one script `src` whose captured raw lexeme addresses the accepted official
  `monthltconveninfo.js` asset; and
- exact request/effective official URL agreement for the supplied root capture.

Selected/active current controls are not authorities. The resolver neither reads the
current date nor adopts the root page's server-selected year/month. `target_date` only
chooses the unique year and month values already exposed in the exact captured source.

### Locator-script rule

The accepted versioned JavaScript grammar must uniquely prove all of:

```text
function changePage(year, month)
window.location.href =
  "/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year="
  + year
  + "&k_month="
  + month
selectedYear change supplies e.target.value and active li.tab month
inactive month-tab click supplies selectedYear value and clicked month attribute
```

Parsing is lexical over exact strict-UTF-8 script bytes. It must reject extra competing
assignment rules, reordered/renamed query parameters, changed path/origin behavior,
implicit values, malformed concatenation and ambiguous event/control binding. It never
executes arbitrary JavaScript or consults a browser/current clock.

Given the exact official DOM tokens, evaluating only this frozen source-owned rule
produces these exact UTF-8 request-material bytes:

```text
/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year=<official year option>&k_month=<official month token>
```

The output path, `k_year`, `k_month`, `?`, `&`, `=`, parameter order and unpadded month
are owned by the captured official script. No existing NAR URL canonicalizer is called;
no decode/re-encode, sorting, padding, normalization or URL reconstruction from a local
template is allowed.

## Existing identity construction and verification

The exact output bytes are passed unchanged as
`official_supplied_request_material` to the existing
`NARHistoricalDailyTargetRequestIdentity`, with exact resolved URL formed by the
qualified official resolution rule and `supplier_evidence_identity` equal to the
deterministic identity of the complete supplier evidence aggregate. The existing
constructor remains final authority for official origin/path, exact query grammar,
target year/month and request digest.

After resolution, the existing
`NARHistoricalDailyTargetLiveCaptureService.capture_supplied_response` performs the one
exact MonthlyConveneInfo GET. The unchanged Phase 6 Monthly normalizer then requires
the captured page's selected year, active month and request identity to agree with the
requested target month. A mismatch is not retried with another URL.

## Proposed minimal API

The next implementation phase should freeze exact types/signatures around this pure
boundary, conceptually:

```python
@dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoBootstrapEvidence:
    homepage_capture: NARMonthlyBootstrapSupplierCapture
    monthly_root_capture: NARMonthlyBootstrapSupplierCapture
    locator_script_capture: NARMonthlyBootstrapSupplierCapture
    # derived immutable supplier_evidence_identity


def resolve_nar_monthly_convene_info_request_identity(
    *,
    target_date: date,
    supplier_evidence: NARMonthlyConveneInfoBootstrapEvidence,
) -> NARHistoricalDailyTargetRequestIdentity:
    ...
```

The exact supplier-capture public type names, canonical capture-ID payload and whether
capture acquisition needs a separately injected transport are deferred only to the
next implementation PREPARE. That phase may not weaken the frozen three-capture graph,
lexical grammar, honest timestamps, source-owned output or existing output type. The
resolver itself is pure and no-network.

## Failure semantics

Bootstrap returns exactly one existing request identity or raises; it never returns a
partial/guessed locator. Fail closed on:

- missing, duplicate, malformed or digest-invalid supplier capture/evidence;
- request/effective URL, host, path, media type, charset or status disagreement;
- missing/duplicate/ambiguous raw homepage anchor or raw root script src;
- target year absent or duplicated in official options;
- incomplete, duplicated, noncanonical or contradictory month controls;
- unrecognized or ambiguous locator-script grammar/control binding;
- a generated byte sequence that the existing request identity rejects;
- output target year/month disagreement; or
- any attempt to use a search result, current clock, active current tab, index position,
  undocumented convention or fallback.

A target month that cannot be resolved by this exact evidence requires an explicit
caller-supplied already validated Monthly locator/evidence. It must not be treated as a
zero-race month/day or as `SUPPORTED_COMPLETE_DAY`. Target discovery can begin only
after the final Monthly response is captured and normalized under Phase 6.

## Historical honesty and causality

Every supplier capture records actual retrieval times. The 2026 observations above are
not rewritten to 2020/2021/2024/2025. Bootstrap evidence proves the locator relation as
observed; it is not prediction data, provider availability, scheduled start,
information cutoff or settlement cutoff.

Supplier `observed_at` is never copied to
`HistoricalDailyTargetEvidenceBundle.observed_at`. The latter remains the honest
observation time of the final MonthlyConveneInfo/RaceList completeness response that
the Phase 6 bundle references. No bootstrap timestamp or bytes enter PredictionPipeline,
snapshot selection or settlement. Later acquisition of a historical Monthly response
remains allowed only under the already approved Phase 2/4/6 historical-source semantics.

## Scope and non-goals

This phase does not implement or change daily orchestration, manifest projection,
evidence resolution, replay runner, JRA, migration/schema/SQLite persistence, durable
archive, ROI/reporting or CLI. It does not alter the Phase 6 supported ordinary and exact
2025-12-26 Kanazawa profiles. Blank/zero, substitute, original-identity ambiguity,
partial cancellation and every unqualified target-discovery state remain fail closed.

No production, tests, fixtures, provider archives, database or research bytes changed
during PREPARE.

## Recommended next phase

- Phase: `POST_V0_8_DAILY_REPLAY_18`
- Name: `NAR MonthlyConveneInfo Bootstrap Implementation`
- Type: `IMPLEMENTATION`
- Purpose: freeze exact file/API/canonical supplier-capture identity/test contract and,
  only after separate review and EXECUTE authorization, implement the qualified pure
  bootstrap plus any explicitly approved injected acquisition boundary.

The next PREPARE must decide exact Allowed Files, supplier capture identity bytes,
fixture policy and required tests. It must stop if exact official-byte provenance cannot
be frozen without changing existing Phase 6 domains or introducing storage/migrations.

## Current PREPARE Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Current PREPARE Forbidden Files and actions

Every other path and action, including production, tests, fixtures, schemas, migrations,
database, archives, CLI, provider response storage, stage, commit, push,
`EXECUTE_APPROVED_PHASE` and Phase 18 transition.

## Required PREPARE verification and stop condition

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Stop at `DRAFT_FOR_REVIEW` with exactly the two docs modified and an empty index. No
test execution is required because no production/test file changes. Independent review
and explicit approval are required before commit or any next phase.
