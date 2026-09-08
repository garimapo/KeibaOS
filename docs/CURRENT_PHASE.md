# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity, authority and authorization

- Phase: `POST_V0_8_DAILY_REPLAY_18`
- Name: `NAR MonthlyConveneInfo Bootstrap Implementation`
- Phase type: `IMPLEMENTATION`
- Base Commit: `8d13983751dec3460d903a98d605c632700cc4b8`
- Branch: `feature/post-v0.8-daily-replay`
- Preparation outcome: `IMPLEMENTABLE`
- Network boundary: `SUPPLIED_CAPTURE_ONLY`
- Production/test/fixture implementation: `COMPLETED_READY_FOR_REVIEW`
- Stage/commit/push: `AUTHORIZED_FOR_EXACT_PHASE_FILES`

AGENTS.md, the committed Phase 17 qualification and approved Phase 2 through Phase 6
NAR contracts are authority. Phase 17 was normally pushed and fetched; local HEAD and
`origin/feature/post-v0.8-daily-replay` were both the Base Commit above and the worktree
and index were clean before PREPARE.

This PREPARE freezes only the implementation contract. Production, tests and fixtures
may change only after separate ChatGPT approval and an explicit
`EXECUTE_APPROVED_PHASE POST_V0_8_DAILY_REPLAY_18`.

## Objective

Implement the Phase 17 qualified source-owned chain as a pure fail-closed bootstrap:

```text
exact supplied NAR homepage capture
  -> exact raw MonthlyConveneInfo root href
exact supplied Monthly root capture
  -> exact raw locator-script src + exact offered year/month tokens
exact supplied locator-script capture
  -> frozen official changePage(year, month) grammar
target_date selects source-exposed tokens
  -> exact source-owned MonthlyConveneInfo locator bytes
  -> existing NARHistoricalDailyTargetRequestIdentity
```

The resolver never acquires a response, executes JavaScript, consults a browser/current
page, or constructs a locator from a developer-owned date template. It returns exactly
the existing request-identity type and does not modify the existing Phase 6 request,
capture, live-capture or source modules.

## Exact future Allowed Files

Production:

```text
scripts/simulation/nar_historical_daily_target_bootstrap_capture.py
scripts/simulation/nar_historical_daily_target_bootstrap.py
```

Tests:

```text
tests/test_nar_historical_daily_target_bootstrap_capture.py
tests/test_nar_historical_daily_target_bootstrap.py
```

New offline parser/source-contract fixtures:

```text
tests/fixtures/nar_daily_target_bootstrap/provenance.json
tests/fixtures/nar_daily_target_bootstrap/nar_home_supplier.utf8.html
tests/fixtures/nar_daily_target_bootstrap/monthly_convene_info_root_supplier.utf8.html
```

Existing read-only fixture and provenance:

```text
tests/fixtures/nar_daily_targets/provenance.json
tests/fixtures/nar_daily_targets/monthly_locator_supplier_monthltconveninfo_20260130_1.utf8.js
```

Docs:

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Repository byte-preservation metadata:

```text
.gitattributes
```

Only these ten paths, including the two docs and `.gitattributes`, may be changed. The
two existing Phase 6 fixture paths are read-only dependencies and must retain their
committed byte length and SHA-256.

## Forbidden Files and scope

Every other path, especially existing NAR daily-target capture/source/live-capture
files, historical daily shared domains, evidence resolver, manifest projection, replay
runner, JRA, providers/parsers, schemas, migrations, SQLite repositories, database/**,
logs/**, archives, CLI, dependencies and release history.

No live supplier acquisition, durable archive, storage Protocol, database persistence,
Daily Orchestrator, target discovery execution, evidence resolution, manifest change,
replay, ROI/reporting or unsupported-state expansion is permitted. Never stage
`database/keiba.db` or `logs/`.

## Supplier capture domain

### Public values and errors

`nar_historical_daily_target_bootstrap_capture.py` exports exactly:

```python
class NARMonthlyConveneInfoBootstrapPageKind(StrEnum):
    OFFICIAL_HOME = "official_home"
    MONTHLY_ROOT = "monthly_root"
    LOCATOR_SCRIPT = "locator_script"


class NARMonthlyConveneInfoBootstrapCaptureError(Exception): ...
class NARMonthlyConveneInfoBootstrapCaptureValidationError(
    NARMonthlyConveneInfoBootstrapCaptureError
): ...
class NARMonthlyConveneInfoBootstrapCaptureUnsupportedError(
    NARMonthlyConveneInfoBootstrapCaptureError
): ...


@dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoBootstrapSupplierCapture:
    page_kind: NARMonthlyConveneInfoBootstrapPageKind
    canonical_request_url: str
    effective_url: str
    response_body: bytes
    charset: str
    requested_at: datetime
    observed_at: datetime
    stored_at: datetime
    http_status: int
    content_type: str
    content_encoding: str | None = None
    content_length: int | None = None
    schema_version: int = field(init=False, default=1)
    response_sha256: str = field(init=False)
    capture_id: str = field(init=False)
```

No source/archive/list/latest/save/load Protocol is added. This value represents an
already supplied complete capture and cannot fetch or persist anything.

Homepage and Monthly-root bodies are dynamic supplied captures. Their individual
`response_sha256` values immutably identify the exact supplied bytes, but no Phase 17
whole-response SHA is a global accepted-version pin. Unrelated official body changes
are allowed only when the exact request/effective URL, capture integrity and every
frozen structural relation below still validate. Arbitrary whole-page digest allowlists
are forbidden. Only the locator JavaScript asset has a globally pinned URL, length,
SHA-256 and semantic grammar.

### Exact URL and response contract

The page-kind URL vocabulary is closed:

| Kind | Exact accepted request/effective URL |
| --- | --- |
| OFFICIAL_HOME | `https://www.keiba.go.jp/` |
| MONTHLY_ROOT | `https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop` |
| LOCATOR_SCRIPT | `https://www.keiba.go.jp/KeibaWeb/resources/js/monthltconveninfo.js?t=20260130_1` |

Both URL fields must be exact equal strings. No redirect, case/port/host/path/query
alias, fragment, credential, extra query or normalization is accepted. URL parsing is
validation only; values are not re-emitted through the existing NAR URL canonicalizer.

`response_body` is nonempty exact bytes and must decode with strict UTF-8. `charset` is
exact `utf-8`; HTTP status is exact integer 200. Exact content types are:

```text
OFFICIAL_HOME: text/html
MONTHLY_ROOT: text/html; charset=UTF-8
LOCATOR_SCRIPT: application/javascript; charset=UTF-8
```

`content_encoding` is None or exact `identity`. A present non-bool nonnegative
`content_length` must equal the exact body length. The three exact aware datetimes are
converted to UTC and must satisfy `requested_at <= observed_at <= stored_at`; none is
defaulted or derived from target_date/current time.

### Capture digest and identity

Canonical bytes use exactly:

```python
json.dumps(
    payload,
    ensure_ascii=False,
    allow_nan=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
```

Aware times use UTC ISO-8601 with exactly six fractional digits and `+00:00`.
`response_sha256` is SHA-256 of exact response bytes. Capture identity payload is:

```json
{
  "canonical_request_url": "<exact URL>",
  "observed_at_utc": "<UTC microseconds +00:00>",
  "page_kind": "official_home|monthly_root|locator_script",
  "response_sha256": "<64 lowercase hex>",
  "schema_version": 1
}
```

`capture_id` is exactly
`nar-monthly-bootstrap-capture-v1:<sha256(canonical payload bytes)>`.
requested_at, stored_at, HTTP headers, filesystem metadata and current time are audit/
validation fields only and do not enter identity.

## Aggregate supplier evidence

`nar_historical_daily_target_bootstrap.py` exports:

```python
class NARMonthlyConveneInfoBootstrapError(Exception): ...
class NARMonthlyConveneInfoBootstrapValidationError(
    NARMonthlyConveneInfoBootstrapError
): ...
class NARMonthlyConveneInfoBootstrapUnsupportedError(
    NARMonthlyConveneInfoBootstrapError
): ...
class NARMonthlyConveneInfoBootstrapIntegrityError(
    NARMonthlyConveneInfoBootstrapError
): ...


@dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoBootstrapEvidence:
    homepage_capture: NARMonthlyConveneInfoBootstrapSupplierCapture
    monthly_root_capture: NARMonthlyConveneInfoBootstrapSupplierCapture
    locator_script_capture: NARMonthlyConveneInfoBootstrapSupplierCapture
    schema_version: int = field(init=False, default=1)
    supplier_evidence_identity: str = field(init=False)


def resolve_nar_monthly_convene_info_request_identity(
    *,
    target_date: date,
    supplier_evidence: NARMonthlyConveneInfoBootstrapEvidence,
) -> NARHistoricalDailyTargetRequestIdentity:
    ...
```

The aggregate constructor requires exact capture types in exact distinct page-kind
slots and unique capture IDs. Its canonical identity payload is exactly:

```json
{
  "homepage_capture_id": "<exact capture ID>",
  "locator_script_capture_id": "<exact capture ID>",
  "monthly_root_capture_id": "<exact capture ID>",
  "schema_version": 1
}
```

Its identity is exactly
`nar-monthly-bootstrap-evidence-v1:<sha256(canonical payload bytes)>`. This is an
audited projection of the three primary captures, not independent source evidence.

Before parsing, the resolver recomputes every body digest, capture ID and aggregate
identity from exact frozen fields. Any mismatch is an integrity error and returns no
request identity. This explicitly catches mutated/forged frozen instances in addition
to normal constructor validation.

## Exact relation chain and lexical HTML boundary

The implementation uses a private strict lexical HTML parser over the supplied UTF-8
bytes. It may use Python's standard-library HTML parser with raw start-tag text, or an
equivalent narrow parser, only if it retains the exact quoted attribute lexeme. It must
not use a normalized DOM href/src as request authority, silently recover malformed
markup, or accept an entity-rewritten near match.

### A. Homepage -> Monthly root

Inside the qualified official navigation structure, require exactly one anchor whose
raw double-quoted href bytes are exactly:

```text
/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop
```

Resolve only those exact bytes against the exact official origin and require equality
with the supplied MONTHLY_ROOT capture's canonical/effective URL. Missing, duplicate,
single-quoted, entity-altered, whitespace-altered, fuzzy, wrong-structure or competing
href evidence is unsupported and fails closed. Document order and first index are not
authorities.

### B. Monthly root -> locator script

Require exactly one script element in the root head whose raw double-quoted src bytes
are exactly:

```text
/KeibaWeb/resources/js/monthltconveninfo.js?t=20260130_1
```

Resolve only those exact bytes against the official origin and require equality with
the supplied LOCATOR_SCRIPT capture URL. Missing, duplicate, wrong host/path/query,
single-quoted, entity-altered or competing script relations fail closed.

### C. Official year/month tokens

Within exactly one Monthly schedule article/form, require exactly one
`select#selectedYear[name="k_year"]`. Its option values must be unique canonical
four-digit ASCII years with matching collapsed decimal display text. `target_date.year`
must occur exactly once. Do not use a selected/current option as target authority.

Require exactly one `ul.monthTab` and exactly twelve direct month items. For every N
from 1 through 12 there must be exactly one
`li#monthTabN.tab[month="N"]` with exact collapsed `N月` text. Values are unpadded
canonical ASCII decimals. `target_date.month` selects exactly one token. Active/current
class state is ignored as an authority and may not affect output.

The initial operational floor remains `target_date >= 2020-01-01`. Exact date type is
required; datetime/subclass/string is rejected. The day is retained only as caller
context; this bootstrap selects the target year and month and does not claim day-level
completeness.

## Frozen locator-JavaScript contract

The sole qualifying asset is:

```text
URL: https://www.keiba.go.jp/KeibaWeb/resources/js/monthltconveninfo.js?t=20260130_1
byte length: 438
SHA-256: bdf86457a9c917fc8259f8b87593c9bbece72d501a95fb5d3573a93b43532515
strict charset: utf-8
```

The exact existing Phase 6 official-byte fixture is the byte authority for tests. A
the approved EXECUTE had to verify its committed byte length and SHA before production edits;
mismatch stops implementation.

The private parser accepts only one exact `changePage(year, month)` definition and one
unambiguous location assignment whose lexical concatenation sequence is:

```text
literal "/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year="
parameter year
literal "&k_month="
parameter month
```

It also requires the exact two event bindings qualified in Phase 17: selected-year
change supplies the event value plus active month attribute, and inactive month click
supplies selected-year value plus the clicked month attribute. The accepted complete
script bytes must have the qualifying SHA-256 above. Parsing independently proves the
tokens; SHA alone is not treated as semantic parsing.

Any byte alteration, duplicate function/assignment/binding, different variable,
literal, query name/order/encoding, alternate branch, dynamic origin, extra output,
missing EOF shape or otherwise unrecognized syntax fails closed. Do not invoke a
JavaScript runtime, `eval`, browser, Selenium, current page or current time.

## Exact output construction

The resolver constructs output only by concatenating the literal UTF-8 byte slices
extracted from the qualified script with the exact raw year option and month attribute
tokens extracted from the root capture:

```text
<script prefix bytes> + <official year token> +
<script separator bytes> + <official month token>
```

No separately typed path/query template is permitted. The resulting bytes must equal
the qualified grammar, including path, `?`, `k_year`, `&`, `k_month`, parameter order,
`=` characters and unpadded month. Percent encode/decode, sorting, normalization,
padding and the existing general NAR URL canonicalizer are forbidden.

Resolve against exact `https://www.keiba.go.jp`, then construct the existing
`NARHistoricalDailyTargetRequestIdentity` with:

- page_kind exact `MONTHLY_CONVENE_INFO`;
- official_supplied_request_material equal to the exact constructed bytes;
- resolved_request_url equal to the exact official resolution; and
- supplier_evidence_identity equal to the aggregate's exact derived identity.

Require the resulting identity's target_year/month to equal target_date and its raw
material, resolved URL and supplier identity to remain exact. Existing constructor
exceptions propagate through the bootstrap failure boundary without fallback.

## Network and responsibility boundary

Phase 18 is exactly `SUPPLIED_CAPTURE_ONLY`:

- no HTTP transport, requests/httpx/urllib/socket, retry, redirect or live service;
- no clock callback or default timestamp;
- no filesystem/archive/database read in production;
- no capture save/load/latest/list API; and
- no acquisition of homepage/root/script.

The caller supplies all three immutable bootstrap captures. After the resolver returns
the existing Monthly request identity, the already implemented
`NARHistoricalDailyTargetLiveCaptureService.capture_supplied_response` remains the
separate final Monthly page acquisition boundary. It is not called by the resolver.

Live supplier acquisition has **not** been qualified. Before a date-only networked
Daily Orchestrator can own homepage/root/script acquisition, a separately reviewed
phase must qualify exact trust anchor, transports, redirect/content bounds, archive-
before-use semantics and capture provenance. Until then, operation must receive the
exact supplier evidence aggregate from its caller or receive an already validated exact
Monthly locator/evidence.

## Historical honesty and fixture boundary

Supplier requested/observed/stored times are honest acquisition metadata. They may be
later than target_date and are never backdated, replaced by target_date or filled from
current time. They do not become provider_available_at, scheduled_start_at, prediction
information cutoff, settlement cutoff or replay start.

Bootstrap capture/evidence timestamps are not copied into
`HistoricalDailyTargetEvidenceBundle.observed_at`; that field remains owned by the
final Monthly/RaceList response captures. Bootstrap bytes/identity do not flow into
PredictionPipeline, snapshot selection or settlement.

All bootstrap fixtures are parser/source-contract test evidence only. They are not
formal replay dataset evidence and their provenance timestamps cannot be instantiated
as a runtime bundle observation. Unit/integration tests are offline and may construct
capture values using the recorded fixture timestamps only to test the capture/bootstrap
contract.

### Fixture provenance correction

The Phase 17 homepage/root observations recorded requested_at and observed_at but did
not preserve complete materialization/capture provenance including exact stored_at.
During the rejected execution preflight, a current Monthly-root candidate had:

```text
exact URL: https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop
requested_at: 2026-09-07T15:05:23.854790+00:00
observed_at: 2026-09-07T15:05:23.975374+00:00
effective URL unchanged; HTTP 200
Content-Type: text/html; charset=UTF-8
Content-Encoding: absent
byte length: 194872
SHA-256: 55648fea20ab88b481e4beae166a07c22f052807c5a8591a75d8fa61247510dd
```

No honest stored_at was captured. Therefore its formal status is exactly
`ROOT_FIXTURE_PROVENANCE_MISSING`. Those bytes are not adopted, are not the Phase 17
research capture, and are not formal historical replay evidence. File timestamps or
current time must not repair the missing field. The earlier Phase 17 root digest
`7df5219922d696f040f6212d06c34b3c097c2b41b44a704da4b6b8ebfee79a4f`
is also not a permanent version pin and need not match a future valid supplied capture.

The homepage candidate matched the Phase 17 digest, but it likewise lacks a complete
stored_at-bearing capture record suitable for the new fixture manifest. Both new HTML
fixtures therefore require one controlled acquisition under the policy below.

### One-time controlled fixture acquisition

The explicitly approved EXECUTE was authorized to make exactly one acquisition
attempt for each missing HTML fixture, solely to materialize offline parser/source-
contract evidence. This is not production live supplier acquisition and no acquisition
code may enter production or tests.

The exact profile for each attempt is:

```text
method: GET
User-Agent: Mozilla/5.0
Accept-Encoding: identity
redirects: disabled
TLS verification: enabled
retry count: zero
connect/read timeout: explicit bounded values
maximum complete body: 4 MiB
required HTTP status: exact integer 200
required effective URL: exact request URL
charset: strict UTF-8
content encoding: absent or exact identity
requested_at/observed_at/stored_at: honestly sampled aware UTC instants
```

The only request URLs are:

```text
https://www.keiba.go.jp/
https://www.keiba.go.jp/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop
```

No alternate host/path, search engine, cached copy, query variant, retry or fallback is
allowed. The future materializer must read the bounded body completely, record all exact
response metadata, compute byte length/SHA-256, and construct the immutable supplier
capture using those same bytes and timestamps.

Before publication, the homepage capture must prove the exact unique raw Monthly-root
href. The Monthly-root capture must prove the unique year control, exact offered target
year, all exact month tokens 1 through 12, exact target month and one raw script src
which resolves exactly to the pinned JavaScript asset URL. The pinned existing JS
fixture must independently pass its exact URL/438-byte/SHA/grammar checks.

Only after all structural and capture-integrity checks pass may the invocation create
the two exact fixture paths and one provenance manifest. Use exclusive creation; do not
overwrite or repair an existing file. On any acquisition, integrity, structure or
publication failure, stop without a second attempt or alternate source. Cleanup may
remove only a newly created same-identity file from that invocation.

The new provenance manifest is schema version 1 and records fixture boundary, exact
method/request/effective URL, no redirect/retry, TLS verification, timeouts/body bound,
content type/encoding/charset, byte length, SHA-256, honest requested/observed/stored
times, materialization time, capture ID and a reference to the existing exact JS
fixture/provenance. It must not label either new capture as a Phase 17 capture.

Tests begin only after materialization and perform no network. The homepage/root fixture
SHA values are whatever the exact one-time captures produce and are verified against
the new provenance; they are not hard-coded production version allowlists. The existing
JS fixture remains the only version-pinned asset and must remain exactly 438 bytes with
its frozen SHA. Synthetic mutations may supplement but not replace the three accepted
full official fixture bodies in the successful integration test.

## Failure taxonomy

Type/value/timestamp misuse raises the matching capture/bootstrap ValidationError.
Recognizable but unqualified official URL/media/HTML/JavaScript/date profile raises the
matching UnsupportedError. A derived digest/identity mismatch in supplied immutable
captures/evidence raises BootstrapIntegrityError globally.

Every failure returns no request identity. There is no first/last link selection,
nearby year/month, default active tab, alternate asset, URL convention, search result,
current response, retry or caller-string fallback. An absent target year or changed
asset is not zero-day evidence and cannot advance to Monthly capture or target discovery.

## Required tests during EXECUTE

### Capture/evidence domain

1. Exact page-kind URL/content-type/strict-UTF-8 capture construction and deterministic
   response digest/capture ID.
2. Exact UTC timestamp retention/order; None/naive/current-clock inference rejected.
3. Redirect/effective mismatch, host/scheme/path/query alias, wrong status/content type/
   encoding/length and malformed bytes rejected.
4. Aggregate exact three-kind slots, unique IDs and deterministic evidence identity.
5. Mutated response/digest/capture/evidence identity fails globally with no resolver
   output.

### Relation and resolver

6. Qualified official homepage -> exact raw Monthly root relation.
7. Missing, duplicate, single-quoted, entity/fuzzy/altered or wrong-structure root href
   fails closed.
8. Qualified Monthly root -> exact raw JS relation.
9. Missing/duplicate JS src and wrong scheme/host/path/query fail closed.
10. Exact qualifying 438-byte JavaScript, digest, one function, one assignment and two
    event bindings accepted.
11. Any altered script byte/grammar and duplicate changePage/assignment/binding rejected.
12. Exact year option and twelve month tokens; missing/duplicate/malformed year or month
    and selected/active fallback rejected.
13. Exact source-extracted query name/order/encoding/unpadded output; URL canonicalizer
    and developer direct-template fallback trapped and unused.
14. 2020-03, 2021-01, 2024-01, 2025-01 and 2026-01 produce exact request material and
    existing request identities from the same supplied evidence.
15. Output has exact existing type, page kind, target year/month, resolved URL and
    aggregate supplier identity.
16. Deterministic repeats and irrelevant caller/object ordering cannot change output.
17. Date before 2020, datetime/string/subclass and absent source-offered year fail closed.

### Boundaries

18. Supplier observed_at remains honest and is never backdated or substituted into
    target/bundle/prediction/settlement causality.
19. Resolver has no network, clock, eval/browser, filesystem, SQLite, migration,
    archive, target-source, live-capture, runner or manifest call.
20. Existing Phase 6 request/capture/live/source behavior and fixture bytes remain
    unchanged.
21. Official fixture manifest lengths/SHA/provenance all match before tests; corrupted
    fixture identity fails rather than being regenerated.
22. Public exports/signatures are exact, keyword-only, immutable where specified, and
    introduce no storage/live API.

No test may skip or relax an error to pass. Network access is prohibited during all test
commands.

## Exact verification commands during EXECUTE

Dedicated:

```text
python -m unittest tests.test_nar_historical_daily_target_bootstrap_capture tests.test_nar_historical_daily_target_bootstrap
```

Related regression:

```text
python -m unittest tests.test_nar_historical_daily_target_capture tests.test_nar_historical_daily_target_live_capture tests.test_nar_historical_daily_target_source
```

Full suite:

```text
python -m unittest discover -s tests -p "test_*.py"
```

Static boundary search over both new production modules must prove no import/call of:

```text
requests|httpx|urllib.request|socket|datetime.now|datetime.today|utcnow|time.time|
eval|exec|selenium|playwright|sqlite3|apply_migrations|save_|load_|archive|repository|
NARProvider|NARParser|build_nar_historical_daily|run_sqlite_historical_replay|Path.resolve
```

The exact search may be split to avoid matching explanatory docstrings or validated
field names; any semantic match is a failure. Final Git checks are:

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

## Blockers and stop condition

No source-contract blocker remains for the supplied-capture-only implementation. The
fixture path is fully defined by the one-time controlled acquisition below. Failure of
either single attempt, structural validation, exact publication/provenance, or the
existing pinned JS fixture requires stopping without implementation or substitution.

A need to alter the existing Phase 6 request/capture/source/live service, qualify live
supplier acquisition, add storage/migration/schema, loosen the exact asset/HTML grammar,
or change any file outside Allowed Files also requires stopping for ChatGPT review.

Successful EXECUTE sets Status to `READY_FOR_REVIEW`, updates the report, leaves the
index empty and does not commit/push/start another phase. The completed EXECUTE stops
now in that state with only the exact Allowed Files changed.

## Execution result

The approved implementation is complete. The supplied-capture domain, strict pure
bootstrap resolver, two exact dynamically captured HTML fixtures, provenance manifest
and the required tests were added only in the exact Allowed Files. The pinned existing
locator JavaScript remains unchanged at 438 bytes and SHA-256
`bdf86457a9c917fc8259f8b87593c9bbece72d501a95fb5d3573a93b43532515`.

The one authorized controlled acquisition attempt per dynamic fixture succeeded and
passed every structural gate before fixture publication. The homepage fixture is 37,763
bytes with SHA-256
`84c9d175fbb7e0c814639afda8fd414d62f5caf0cc625f6a1dec6ae6b8e379e4`;
the Monthly-root fixture is 194,872 bytes with SHA-256
`55648fea20ab88b481e4beae166a07c22f052807c5a8591a75d8fa61247510dd`.
Their honest timestamps and exact request/response metadata are frozen in the new
provenance manifest. They remain offline parser/source-contract evidence only.

Dedicated Phase 18 tests: 26 PASS. Related Phase 6 regression tests: 22 PASS. Full
unittest discovery: 3,013 PASS. The exact static boundary search is clean. Full-suite
ResourceWarning output is from pre-existing SQLite tests/modules; neither dedicated nor
related Phase 18 commands emit it. No test was skipped or relaxed.

No file is staged. No commit, push or later phase transition was performed.

## Review stop

Execution is complete. No further file modification, stage, commit, push or later phase
transition is authorized before independent review.

## Phase 18 byte-exact fixture whitespace exception

ChatGPT explicitly approved a Phase 18-only pre-commit exception for original official-
response trailing-whitespace bytes in exactly these two Allowed Files:

```text
tests/fixtures/nar_daily_target_bootstrap/nar_home_supplier.utf8.html
tests/fixtures/nar_daily_target_bootstrap/monthly_convene_info_root_supplier.utf8.html
```

The full cached whitespace check is expected to fail only on those exact bytes and exact
paths. They are part of the captured official responses; changing them would invalidate
the frozen byte lengths and SHA-256 digests. Every other staged file must pass the cached
whitespace check. This is not a global fixture or whitespace exception and does not cover
another path, diagnostic type, normalization, formatting or line-ending rewrite.

The Phase 18 commit-gate amendment expands Allowed Files from nine to ten solely for
`.gitattributes`. Exactly the two official-response fixtures above are marked by exact
path with `-text -diff` so their captured bytes survive index and checkout without text
normalization. The earlier homepage index LF normalization was rejected. Original
trailing-whitespace, space-before-tab and line-ending bytes are retained as evidence;
no wildcard or global whitespace/diff exception is created.
