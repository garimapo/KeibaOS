# Latest Codex Report

## POST_V0_8_DAILY_REPLAY_106 — IMPLEMENTED FOR INDEPENDENT REVIEW

Phase: `POST_V0_8_DAILY_REPLAY_106`

Formal Status: `READY_FOR_REVIEW`

State: `IMPLEMENTED_FOR_REVIEW`

Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`

Design Review: `PHASE106_DIAGNOSTIC_CAMPAIGN_AND_TIMING_QUALIFICATION_DESIGN_REVIEW_PASS`

Implementation: `NAR_DIAGNOSTIC_CAMPAIGN_AND_TIMING_QUALIFICATION_IMPLEMENTED`

Starting HEAD/TREE: `d250e0954f50dfe27d6efe569f149a876b8ca684` /
`209149123f26e5962526d66d47d3ad7f69f07f02`.
Phase105 and Phase104 remain formally complete. Phase106 is **not** formally
complete pending independent implementation verification.

The implementation adds exact Git-object fixture byte authority; a fixed,
content-addressed diagnostic plan with deterministic node identities, explicit
DAG continuation and inclusive/exclusive composition; and a diagnostic
declaration bound to one current Phase104 claim. The companion schema is
installed only by explicit diagnostic bootstrap under the held campaign lock,
after Phase104 capability issuance. The ordinary Phase105 bootstrap remains
diagnostic-table-free. Narrow compatible gates accept only the exact approved
union; historical strict validators remain strict.

Documentation correction: the plan is constructed from reviewed Git objects
before entering the runner, but durable plan publication is intentionally not
before V2 activation or Phase104 authority issuance. The implemented causal
order is: enter normal Phase105 runner/archive; establish the prospectively
activated V2 session; issue Phase104 binding, one-shot claim, readiness and
current-process capability; confirm zero attempts; install the diagnostic
companion under the same lock; save/reload fixture authority; save/reload the
diagnostic plan; save/reload the declaration binding that plan and claim; then
allow the first Phase105 attempt. This preserves
`MEASUREMENT_DENOMINATOR_MUST_BE_PREDECLARED_BEFORE_FIRST_ATTEMPT` without
claiming plan persistence before the Phase104 authority chain.

The diagnostic context requires a live current-process capability and an exact
predeclared next node before calling the controlled Phase105 wrapper. Four NAR
transports retain their default adapter construction, request arguments and
Phase104 static transport-profile identity; private diagnostic adapter
injection permits fake outcomes below the actual-send guarded Session. The
sealed `python -I -B` no-network rehearsal executes real bootstrap capture
and normalization code with the real source-isolation check.

Read-only reconciliation keeps observation qualification separate from plan
completeness. A qualified fake-adapter timeout remains an inner timeout
observation, but all Phase106 evidence is structurally `DIAGNOSTIC_ONLY` for
official eligibility. Dependent absent nodes are causal nonexecution only
after a proven terminal failure; unresolved predecessors are integrity
defects, not inferred failures. Missing publication overhead is a separate
defect and does not erase a provider observation. Fixed plan slots map to
dense Phase105 sequences among executed nodes. No stage-duration sum or
concrete Delta is calculated.

Verification: Phase106 dedicated tests passed (`22 passed`); related
Phase99–105/transport regressions passed (`143 passed`, `50 subtests passed`);
the full repository suite passed (`4682 passed`, `2 skipped`, `2846 subtests
passed`). Staged-diff check and exact final-commit sealed-child smoke are run
separately before handoff and reported in the final task response. No real
provider HTTP, live
campaign, production DB write, ROI calculation or source-semantic change was
performed; tests use temporary SQLite and Git repositories only. Remaining
blockers: `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`, Phase94/95
entry-status semantics, Phase41 market eligibility, prospective live-campaign
authorization, and unresolved composite stage boundaries.

## POST_V0_8_DAILY_REPLAY_106 — PREPARED FOR ARCHITECTURAL REVIEW

Phase: `POST_V0_8_DAILY_REPLAY_106`

Status: `DRAFT_FOR_REVIEW`

Outcome: `READY_FOR_ARCHITECTURAL_REVIEW`

Audit: `NAR_DIAGNOSTIC_CAMPAIGN_AND_TIMING_QUALIFICATION_DESIGN_COMPLETE`

Starting/verified HEAD/TREE: `d250e0954f50dfe27d6efe569f149a876b8ca684` /
`209149123f26e5962526d66d47d3ad7f69f07f02` on
`feature/post-v0.8-daily-replay`; origin agrees and the initial worktree was
clean. Phase105 is reconciled as formally complete:
`PHASE105_CORRECTION_REMOTE_VERIFICATION_PASS`,
`PHASE105_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`,
`NAR_PASSIVE_TIMING_AND_ACTUAL_SEND_ENVIRONMENT_AUTHORITY = FORMALLY_INTEGRATED`,
and `CONTROLLED_TIMING_EVIDENCE_ISSUANCE = VERIFIED`. Phase104 remains
formally complete and integrated.

The audit found that Phase105 provides generic controlled measurement,
nonrecursive overhead, and actual-send guarded-Session primitives, but there
is no production call site for `measure_nar_operation`. Accordingly no V2
stage is already end-to-end wired into ordinary acquisition, snapshot, or
prediction execution. Bootstrap/daily/official/market HTTP, snapshot,
adapter, prediction, allocation, plan, and persistence have candidate
callable boundaries but need explicit diagnostic composition. Scheduler and
shadow-artifact stages are not reachable; campaign/readiness and several
raw-validation/parsing/provider-binding/freeze substage boundaries are not
currently separable without a reviewed adapter. The full stage matrix is in
`CURRENT_PHASE.md`.

The recommended Phase106 design adds a temporary diagnostic-only archive
companion, a predeclared immutable diagnostic plan, and a post-claim diagnostic
execution declaration. It leaves the Phase104 execution claim canonical
payload unchanged. A trigger requires the declaration before any diagnostic
attempt. Future official aggregation must reject a diagnostic companion or
declaration, making diagnostic rows structurally `DIAGNOSTIC_ONLY` rather than
merely caller-labelled. The harness still uses the actual sealed child, V2
session/activation, Phase104 runtime/claim/readiness/capability, and Phase105
controlled attempt/terminal/guard paths; its HTTP adapters are deterministic
fakes beneath actual `Session.send`, so it emits no NAR request.

The plan predeclares fixture instances, sequences, fixed stopping/window rule,
correlations, expected output artifacts, and a composition DAG. Reconciliation
is pure/read-only: it reports attempts, terminals, unresolved rows, environment
qualification, sequence/missing-stage errors, overhead, and exact ancestry.
It never repairs rows, calculates Delta, or authorizes a campaign. Synthetic
successes/failures/timeouts remain visible diagnostics but are not provider
timing observations. For later official work, provider failures/timeouts after
qualified preconditions remain denominator members; unresolved attempts fail
closed; and a critical path may only be calculated from proven composition, not
by summing nested durations.

Frozen distinctions: `DIAGNOSTIC_DRY_RUN != PROSPECTIVE_OFFICIAL_CAMPAIGN`,
`SYNTHETIC_TRANSPORT_TIMING != PROVIDER_OPERATIONAL_TIMING_EVIDENCE`,
`INSTRUMENTATION_COVERAGE != CONCRETE_DELTA_AUTHORITY`, and
`STAGE_DURATION_SUM != CRITICAL_PATH_DURATION_UNLESS_COMPOSITION_PROVEN`.

No production or test code was modified, no provider HTTP/live campaign/
production DB write/Delta selection occurred, and no tests were run because
this was a design-only audit. `git diff --check` and final worktree status are
recorded after this preparation. Remaining blockers are concrete-Delta audit,
Phase94/95/41 source semantics, prospective campaign authorization, and the
reviewed split boundaries required for the composite V2 stages.

### Architectural revision

`PHASE106_ARCHITECTURAL_REVIEW_REQUIRES_REVISION` is recorded with
`UPSTREAM_PROVIDER_FAILURE_MUST_NOT_CAUSE_DENOMINATOR_ERASURE` and
`DIAGNOSTIC_PLAN_MUST_DISTINGUISH_CAUSAL_NONEXECUTION_FROM_MISSING_STAGE`.
The design now freezes two independent classifications rather than one
campaign status vocabulary.

At the observation level, the closed states are
`QUALIFIED_OPERATIONAL_TIMING_OBSERVATION`,
`NONQUALIFYING_REQUEST_ENVIRONMENT`, `UNRESOLVED_ATTEMPT`,
`EXECUTION_ANCESTRY_INVALID`, and `DIAGNOSTIC_ONLY`. Terminal disposition is
separate: `SUCCESS`, provider `FAILURE`, and provider `TIMEOUT` can each be an
otherwise qualified observation. Therefore
`QUALIFIED_PROVIDER_FAILURE_REMAINS_IN_DENOMINATOR`; absence of a terminal is
instead unresolved evidence, never an inferred provider result.

Plan-node reconciliation is separately closed as `OBSERVED_AS_PLANNED`,
`EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE`, `PRECONDITION_BLOCKED`,
`MISSING_UNEXPLAINED`, or `EVIDENCE_INTEGRITY_FAILURE`. A qualified HTTP
ReadTimeout stays an observed provider timeout, while predeclared parsing,
normalization, and snapshot nodes needing successful response bytes become
expected-not-executable. This freezes
`DOWNSTREAM_CAUSAL_NONEXECUTION_DOES_NOT_ERASE_UPSTREAM_FAILURE`. Missing
parsing after an HTTP success is unexplained; terminal absence is integrity
failure. The pure reconciler reports both layers without changing observation
qualification.

`MEASUREMENT_DENOMINATOR_MUST_BE_PREDECLARED_BEFORE_FIRST_ATTEMPT`: each
deterministic diagnostic plan node binds plan/node identities, stage, operation
sequence where applicable, scope/correlation, HTTP URL digest/policy/transport,
predecessors, continuation rule, branch terminal behavior, and composition
role. The three continuation rules are `INDEPENDENT`,
`EXECUTE_AFTER_PREDECESSORS_TERMINATE_REGARDLESS_OUTCOME`, and
`REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS`. No success-count stopping or
post-outcome plan rewrite is permitted. The controlled context rejects an
unplanned attempt and reconciliation detects extras or sequence conflicts.

The plan separates operation attempts from nonrecursive publication-overhead
records and runner/readiness/freeze control evidence; it does not fabricate
attempt sequences for the latter. The DAG labels inclusive composites,
exclusive leaves, sequential siblings, and dependency-only edges, retaining
`STAGE_DURATION_SUM != CRITICAL_PATH_DURATION_UNLESS_COMPOSITION_PROVEN`.

Diagnostic installation remains explicit and temporary:
`DIAGNOSTIC_SCHEMA_INSTALLATION != NORMAL_OFFICIAL_ARCHIVE_UPGRADE`. Normal
Phase105 bootstrap remains the official-parent state. Plan save/reload,
normal Phase104 authority, then controlled declaration save/reload precede any
attempt. `DIAGNOSTIC_ONLY_OVERRIDES_INNER_OBSERVATION_QUALIFICATION`, so no
inner terminal/environment success promotes fake-adapter data. Fixture inputs
are a Git-object-derived manifest (repository, commit/tree, member blobs,
lengths, hashes) rather than worktree paths:
`FIXTURE_PATH != DIAGNOSTIC_FIXTURE_CONTENT_AUTHORITY`.

Fake adapters remain below real guarded `Session.send`; private factory
injection must preserve the default direct `_HTTPAdapter(max_retries=0)`
profile and the market-odds AST inspection, or narrowly update that inspector
with exact semantic-equivalence tests. Diagnostics remain no-network and the
adapter is not production runtime-profile authority. The revised tests cover
timeout retention/causal nonexecution, independent continuation, unexplained
omission, unresolved terminal, fixed-plan ordering, structural diagnostic
precedence, explicit bootstrap, immutable fixtures, fake adapter ordering,
static-profile equivalence, pure reconciliation, and sealed-child no-network
execution.

Recommendation: `DRAFT_FOR_REVIEW`.

Next: `CHATGPT_REVIEW_PHASE106_DIAGNOSTIC_CAMPAIGN_AND_QUALIFICATION`.

## POST_V0_8_DAILY_REPLAY_105 — CONTROLLED ISSUANCE CORRECTION FOR REVIEW

Phase: `POST_V0_8_DAILY_REPLAY_105`; Formal Status: `READY_FOR_REVIEW`;
State: `IMPLEMENTED_FOR_REVIEW`; Outcome:
`READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`. Design Review:
`PHASE105_PASSIVE_TIMING_AND_REQUEST_ENVIRONMENT_DESIGN_REVIEW_PASS`.
Implementation:
`NAR_PASSIVE_TIMING_AND_ACTUAL_SEND_ENVIRONMENT_AUTHORITY_IMPLEMENTED`.
Phase105 is **not** formally complete.

Starting HEAD/TREE: `7e82b5c870e153eefac14cc7cdfbd00c126f8983` /
`26de34ffb07f4ce88bf0645e4975173791fcd648` on
`feature/post-v0.8-daily-replay`. Independent review required correction of
`PERSISTED_TIMING_EVIDENCE_CAN_BYPASS_CURRENT_PROCESS_CAPABILITY` and
`ATTEMPT_TERMINAL_CONTROLLED_ISSUANCE_REQUIRED`. Freeze
`PERSISTED_CLAIM_ANCESTRY != CONTROLLED_TIMING_EVIDENCE_ISSUANCE` and
`TIMING_EVIDENCE_PUBLICATION_REQUIRES_CURRENT_PROCESS_CONTROLLED_ISSUANCE`.

The Phase105 attempt archive now requires a private controlled issuance marker
for `save_attempt`, `save_terminal`, and `save_overhead` before insertion or
idempotent duplicate handling. The passive wrapper supplies this marker only
after validating the live runner's exact current-process capability, including
before terminal and overhead publication. The guarded pre-network Session
continues to use its separate existing environment-verification marker; the
direct-policy guard and nonqualifying-send rejection are unchanged. These
markers enforce trusted KeibaOS API discipline, not cryptographic security.

Terminal publication and reload now verify the exact archived attempt and
require `operation_finished_at >= attempt_admitted_at`. Monotonic elapsed
microseconds remain independent of causal UTC. A focused regression closes
the runner, reopens the same archive, and rejects historical-window attempt
publication plus uncontrolled terminal/overhead direct saves. Controlled
exact duplicates remain idempotent; uncontrolled exact duplicates are also
rejected. Another regression rejects a backdated terminal on save and after
test-only corruption of the temporary archive. The normal wrapper and guarded
HTTP fake-adapter tests still succeed.

Changed paths are limited to `docs/CURRENT_PHASE.md`, this report,
`scripts/simulation/sqlite_nar_operational_timing_attempt_archive.py`,
`scripts/simulation/nar_operational_timing_passive_wrapper.py`, and
`tests/test_nar_operational_timing_passive_wrapper.py`. No Phase99–104 domain,
schema, transport, provider, cutoff, or policy implementation was changed.

Verification: corrected passive-wrapper focus `20 passed`; Phase99–105 and
freeze/cutoff/transport regressions `197 passed, 68 subtests passed`; full
repository suite `4659 passed, 2 skipped, 2846 subtests passed`.
`git diff --check` passed (line-ending notifications only). A separate
post-commit, no-network `python -I -B` sealed-child smoke against the final
correction commit is required and will be reported in the handoff, because an
uncommitted source tree cannot stand in for Git-object source authority.

No provider HTTP, live timing campaign, production DB write, Delta selection,
ROI evaluation, or Phase94/95/41 source-semantic work occurred. Tests used
temporary SQLite and Git-object fixtures. Correction remains pending
independent verification. Prospective campaign authorization and
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remain unresolved.

Next: `CHATGPT_REVIEW_PHASE105_CORRECTION`.

## Prior Phase105 implementation report

## POST_V0_8_DAILY_REPLAY_105 — IMPLEMENTED FOR REVIEW

Phase: `POST_V0_8_DAILY_REPLAY_105`

Formal Status: `READY_FOR_REVIEW`

State: `IMPLEMENTED_FOR_REVIEW`

Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`

Implementation: `NAR_PASSIVE_TIMING_AND_ACTUAL_SEND_ENVIRONMENT_AUTHORITY_IMPLEMENTED`
Design Review: `PHASE105_PASSIVE_TIMING_AND_REQUEST_ENVIRONMENT_DESIGN_REVIEW_PASS`

Starting remote HEAD/TREE: `8d6411f7d886caf70db44e1e92ccd1f5bd6711d8` /
`e6a50810b0d82cf620e975c7db8b0b12d5180ce8`. Phase104 was
independently verified and formally complete. Phase105 does not mark itself
formally complete.

The new V2 attempt identity binds exact configuration/session/execution claim,
stage, descriptive correlation, runner sequence, causal admission UTC, observed
load, and—only for HTTP—expected direct policy and safe expected URL SHA-256.
It contains no future actual-send verification identity. The V2 terminal binds
the exact attempt, causal finish UTC, explicit monotonic microseconds, coherent
closed disposition/failure classification, and optional artifact digest. The
campaign runner supplies the UTC clock, `perf_counter_ns` timer, and serial
sequence. Duration is integer `(finish_ns - start_ns) // 1000`; clock movement
does not define elapsed time.

The passive wrapper requires a live current-process capability, half-open
session admission, and durable attempt save plus exact reload before measured
work. Attempt publication failure prevents invocation. On completion or a
production exception, terminal publication is attempted without changing the
underlying value or exception; a failed terminal publication leaves the attempt
discoverable as unresolved. Exact Requests/cause types are used for conservative
timeout classification, never exception message parsing.

The guarded Session intercepts the concrete PreparedRequest and effective
`Session.send` kwargs after Requests preparation/environment merge and before
adapter I/O. It checks current capability, one send per attempt, safe exact NAR
URL, static transport profile, proxy mapping, TLS verify, client cert, auth
headers, retry descriptor, and timeout/request flags. It persists and exact-
reloads a non-secret attempt-child verification before delegating. A failed
direct policy records `NONQUALIFYING_REQUEST_ENVIRONMENT` and blocks adapter
send. Environment publication/reload is included in enclosing HTTP elapsed
time. The controlled publication marker is API discipline, not cryptographic
security. An attempt or terminal alone is not an official HTTP timing sample;
future aggregation must reject missing/nonqualifying verification. No proxy
password, CA path, authorization value, or netrc secret is serialized.

All four NAR transports have a private default-preserving Session factory;
ordinary callers still construct `requests.Session`, with unchanged request
arguments and provider behavior. A separate Phase105 companion adds exact
claim-FK attempts, attempt-FK environment and terminal rows, and nonrecursive
claim/attempt-scoped publication-overhead rows. Append-only UPDATE/DELETE
triggers, exact duplicate idempotency, contradiction checks, no backfill, and
strict State-5 archive bootstrap coexist with historical Phase99–104 rows and
validators. A real no-network Git-object sealed `python -I -B` child obtains
the Phase104 current-process capability without monkeypatching source checks.
It intentionally exercises the committed Phase104 bundle, not uncommitted
Phase105 source; future official execution must use a separately reviewed
sealed Phase105 commit.

Focused Phase105 domain, archive/bootstrap, guarded wrapper and sealed-child
E2E tests passed (24 tests). The full repository suite passed: 4,657 passed,
2 skipped, 2,846 subtests passed. An explicit Phase99–104/freeze/cutoff/
transport regression run and final diff/Git audit follow below.

No provider HTTP, live timing campaign, production-database write, Delta
selection, policy activation, ROI evaluation, or source-semantic authority
change occurred. Temporary SQLite/Git-object fixtures were used in tests.
Remaining blockers: independent Phase105 implementation review, later
prospective live-campaign authorization,
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`, and Phase94/95/41
source-semantic/market-eligibility blockers.

Next: `CHATGPT_REVIEW_PHASE105_IMPLEMENTATION`.

### Final verification and Git result

Full suite: `4657 passed, 2 skipped, 2846 subtests passed`.
Explicit Phase99–104/freeze/cutoff/transport regressions: `171 passed,
68 subtests passed`. `git diff --check`: PASS (only local CRLF conversion
warnings). Exact changed-path audit: 22 planned paths, no unrelated path;
staged files empty before the authorized commit. Remote branch still points to
the verified starting HEAD. Normal commit/push outcome is reported in the
task handoff after this document is committed.

## POST_V0_8_DAILY_REPLAY_105 — PASSIVE TIMING AND REQUEST-EFFECTIVE ENVIRONMENT DESIGN

Phase: `POST_V0_8_DAILY_REPLAY_105`

Status: `DRAFT_FOR_REVIEW`

Outcome: `READY_FOR_ARCHITECTURAL_REVIEW`

Audit: `NAR_PASSIVE_TIMING_AND_REQUEST_ENVIRONMENT_DESIGN_COMPLETE`

### Architectural revision

`PHASE105_ARCHITECTURAL_REVIEW_REQUIRES_REVISION` is accepted. The prior design incorrectly treated a precomputed URL/environment descriptor as causal proof of the configuration later used by Requests. The resolved blockers are `PRECOMPUTED_REQUEST_ENVIRONMENT_DESCRIPTOR_NOT_CAUSALLY_BOUND_TO_ACTUAL_SEND` and `ATTEMPT_ENVIRONMENT_IDENTITY_CAUSAL_ORDER_CONFLICT`.

Freeze `PRE_REQUEST_ENVIRONMENT_OBSERVATION != REQUEST_EFFECTIVE_SEND_CONFIGURATION` and `ATTEMPT_PUBLICATION_PRECEDES_ACTUAL_SEND_ENVIRONMENT_RESOLUTION`. The V2 attempt does not bind an actual request-environment verification identity. It binds only the closed expected `DIRECT_REQUEST_ENVIRONMENT_V1` policy. The actual authority is a new immutable child, `NARRequestEffectiveEnvironmentVerification` (`nar-request-effective-environment-verification-v1:<sha256>`), whose exact ancestry is claim -> attempt -> verification -> terminal.

The guard is located after normal Requests preparation/environment merge and immediately before adapter I/O: a guarded Session inspects the actual `PreparedRequest` and concrete `send` kwargs, validates attempt/capability/expected URL, persists and exact-reloads one verification, then delegates to normal `Session.send`. It does not recompute proxy state. The direct policy requires empty actual proxy mapping, `verify is True`, no client certificate, and no Authorization or Proxy-Authorization headers. It stores no credentials, paths, proxy passwords, netrc contents, or secret URLs. A violation stops the send before network I/O. This covers all four transports, including fetch-local market-odds Session creation, through a default-preserving private Session factory; global Requests monkeypatching is forbidden.

The verification is `UNIQUE(attempt_identity)`, has a restrictive FK to its attempt, and its save/reload cost is included in the enclosing HTTP monotonic duration. Publication overhead remains separately measurable but nonrecursive. The sealed `python -I -B` child E2E, exact attempt/terminal FK companion, unchanged underlying result/exception behavior, conservative timeout classification, and later campaign gate remain unchanged.

### Reconciliation and audit result

The verified Phase104 remote baseline is `8d6411f7d886caf70db44e1e92ccd1f5bd6711d8` /
`e6a50810b0d82cf620e975c7db8b0b12d5180ce8` on
`feature/post-v0.8-daily-replay`, with a clean worktree. `PHASE104_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`,
`POST_V0_8_DAILY_REPLAY_104 = FORMALLY_COMPLETE`,
`NAR_RUNTIME_BINDING_AND_CAMPAIGN_EXECUTION_AUTHORITY = FORMALLY_INTEGRATED`, and
`ONE_SHOT_CAMPAIGN_EXECUTION_PARENT = VERIFIED` are recorded. Phase103 remains formally complete.

Phase105 freezes the V2 attempt/terminal contract without implementing it. An attempt is
content-addressed as `nar-operational-timing-attempt-v2:<sha256>` and binds exact V2
configuration/session/claim ancestry, stage, correlation, runner-owned sequence, causal
`attempt_admitted_at`, closed load context, and only an expected direct-environment policy
semantic. The timestamp is an admission boundary, not callable-entry time. The archive must
enforce a restrictive claim FK and `UNIQUE(claim_identity, attempt_sequence)` from table
creation. A terminal is `nar-operational-timing-terminal-v2:<sha256>`, strictly references
the exact attempt, carries causal finish plus explicit integer monotonic duration and closed
disposition/classification, and excludes exception text, outcomes, payouts, and ROI.

Official ordering is capability validation -> UTC admission -> half-open session test ->
attempt save and exact reload -> `perf_counter_ns` start -> untouched production callable ->
monotonic finish -> UTC finish -> terminal publication. Duration is exactly
`(finish_ns - start_ns) // 1000`. Attempt-publication failure fails the official wrapper before
the callable; terminal-publication failure preserves the original result/exception and leaves
the attempt unresolved. Existing transport wrappers preserve Requests causes, so timeout
classification may use only exact direct/cause types; unrecoverable domain transport errors are
conservatively `TRANSPORT`, never message-text guesses.

`STATIC_RUNTIME_TRANSPORT_PROFILE != REQUEST_EFFECTIVE_NETWORK_ENVIRONMENT` is resolved only
at the actual pre-send boundary, not by a precomputed descriptor. The guarded Session observes
the PreparedRequest and effective send configuration after Requests has merged environment
settings, then fails closed before adapter I/O unless direct policy qualifies. `trust_env=True`
and market-odds `trust_env=False` both receive this concrete-send verification; credentials and
other secret material are never stored or exposed.

The design also requires a real no-network sealed-bundle child E2E: a minimal stdlib-only
launcher runs `python -I -B`, admits only the sealed source root, rejects import shadowing, and
obtains a real Phase104 capability using a temporary preactivated V2 archive without provider
operations or monkeypatching the source-isolation check. V2 attempt/terminal, request-environment,
publication-overhead, and exact Phase105 companion persistence are deferred to the reviewed
implementation. Publication overhead is intentionally nonrecursive and separately recorded.

Exact wrapper boundaries, schema/bootstrap State 5, diagnostics versus official evidence,
future file paths, and required test matrix are specified in `docs/CURRENT_PHASE.md`. No
provider HTTP, live campaign, production DB write, production-code/test change, staging, commit,
or push occurred. No tests were run because this was design-only. The remaining blockers are
request-effective environment implementation/review, sealed-child E2E implementation/review,
explicit prospective-campaign authorization, `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`,
and Phase94/95/41 source-semantic constraints.

Recommended disposition: `DRAFT_FOR_REVIEW`.

Next: `CHATGPT_REVIEW_PHASE105_PASSIVE_TIMING_AND_REQUEST_ENVIRONMENT`.

---

## POST_V0_8_DAILY_REPLAY_104 — RUNTIME AND EXECUTION AUTHORITY FOUNDATION

Phase: `POST_V0_8_DAILY_REPLAY_104`

Formal Status: `READY_FOR_REVIEW`

State: `IMPLEMENTED_FOR_REVIEW`

Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`

Audit: `NAR_RUNTIME_BINDING_AND_CAMPAIGN_EXECUTION_AUTHORITY_DESIGN_COMPLETE`

Design Review: `PHASE104_RUNTIME_AND_EXECUTION_AUTHORITY_DESIGN_REVIEW_PASS`

Implementation: `NAR_RUNTIME_BINDING_AND_CAMPAIGN_EXECUTION_AUTHORITY_IMPLEMENTED`

### Implementation verification

Starting HEAD/tree: `1236f1e0db84ce6025d07c052abbb3c7348aab3e` /
`7d882808308c5850b424a1ee38b710fe0df2a0d9`.

The Git-object source bundle binds exact commit/tree and ordered member bytes;
materialization is atomic outside the developer worktree and rejects corruption.
Official runner issuance checks isolated `-I -B` execution, sole sealed namespace,
critical and loaded KeibaOS module origins, and the exact Git manifest. Runtime
dependency identity and a static profile are derived locally from actual production
transport constructors/constants and fixed request-call flags, without HTTP. All
four transports retain their current 10/10 or 10/20 timeout, retry, redirect,
stream, TLS and `trust_env` behavior. Request-specific proxy/environment effects
are not claimed to be proven or sanitized as official request authority; that
requirement is explicitly deferred to Phase105 by the approved clarification.

The local Windows-compatible archive lock is held from bootstrap through authority
life. The separate Phase104 companion stores source/profile/binding/claim/readiness
parents append-only with restrictive ancestry. A unique session claim remains
consumed after normal release or failed/late readiness. The UTC readiness clock is
sampled after exact binding and claim reload; late readiness creates no official
current-process capability. The capability is valid only for the currently locked
runner and its newly issued claim. No v2 attempt/terminal schema or passive timing
wrapper was added. The top-level bootstrap accepts only exact empty/base/activation/
v2/Phase104 states and does not reinterpret historical validators.

Focused new tests: 16 passed. Phase99–103 regression tests: 70 passed. Full suite:
4,633 passed, 2 skipped, 2,846 subtests passed. Temporary test Git/SQLite writes
occurred; no production DB writes, provider HTTP, live campaign, or Delta selection.
`REQUEST_EFFECTIVE_NETWORK_ENVIRONMENT_BINDING_REQUIRED_FOR_OFFICIAL_ATTEMPTS`,
Phase105 passive wrappers, the concrete-Delta timing audit, and Phase94/95/41
source-semantic blockers remain unresolved. No scope deviation is known.

Next: `CHATGPT_REVIEW_PHASE104_IMPLEMENTATION`.

### Historical Phase104 design report

Starting HEAD/tree: `1236f1e0db84ce6025d07c052abbb3c7348aab3e` /
`7d882808308c5850b424a1ee38b710fe0df2a0d9`; branch
`feature/post-v0.8-daily-replay`. Remote branch matched this baseline. The worktree
was initially clean. This is a documentation-only design revision, not Phase104
implementation.

### Reconciliation and primary decision

Independent Phase103 verdict:
`PHASE103_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`,
`POST_V0_8_DAILY_REPLAY_103 = FORMALLY_COMPLETE`,
`NAR_V2_MEASUREMENT_CONFIG_SESSION_ACTIVATION_FOUNDATION = FORMALLY_INTEGRATED`,
`V2_PERSISTENCE_BOUNDARY_CONFIG_SESSION_ACTIVATION_ONLY = VERIFIED`, and
`V2_ATTEMPT_TERMINAL_PERSISTENCE_DEFERRED_PENDING_EXECUTION_PARENT = CONFIRMED`.
The Phase102 review pass and crash-no-resume contract remain frozen. The v2 domain
prerequisite for runtime-binding **design** is resolved, but runtime binding itself
is not implemented. Official ancestry must remain v2 configuration → session →
activation declaration → verification → runtime binding → one-shot execution claim
→ future attempt → terminal. `PROCESS_LOCK != PERSISTENT_SESSION_CONSUMPTION_AUTHORITY`.

### Phase104 authority decisions

Sealed source: `CONTROLLED_SEALED_GIT_SOURCE_BUNDLE_V1` materializes exclusively
from local exact Git commit/tree objects, then independently verifies sorted member
paths, Git types/modes, byte lengths and SHA-256 values. The manifest identity is
`nar-runtime-source-bundle-v1:<sha256>`. Initial deterministic member rule includes
tracked `scripts/**/*.py`, `main.py`, `config/**`, `prompts/**`, and
`requirements.txt`; it excludes DB/logs/tests/docs. Worktree cleanliness is an
operator preflight, not runtime-source authority. The official code runs in a new
isolated child (`-I -B` or equivalent); controlled `sys.path`, exact sole PEP420
`scripts.__path__`, and critical-module manifest origins reject worktree/PYTHONPATH
shadowing. No mutable-worktree copy is authoritative.

Dependency profile: exact Python implementation/version, Requests, urllib3,
SQLite runtime, OS release/build and architecture are timing-compatibility
material; unrelated packages are not. Effective transport profiles must derive
from actual standard collaborators, not caller numbers. Current four transports
use 10/10, 10/10, 10/10, and 10/20-second connect/read timeouts, respectively,
`HTTPAdapter(max_retries=0)`, no redirects, streaming, TLS verification, and
`Accept-Encoding: identity`. Market odds sets `trust_env=False`; the other three
do not. The v2 configuration records timeouts/retry but not proxy/redirect/TLS
details, so Phase104 adds a supplemental closed runtime-profile identity without
reinterpreting v2 canonical JSON. Future official aggregation must require exact
configuration **and** relevant runtime-profile compatibility. The initial reviewed
official mode is direct/no effective proxy or environment CA/auth override; URL-
dependent Requests environment settings require Phase105 per-request verification.
`HTTPAdapter(max_retries=0)` does not prove no kernel/network retransmission.

Concurrency and lock: the controlled runner has one workflow and HTTP operation,
no worker pool/async fan-out, and sequential RaceList; only the runner issues the
serial authority. A Windows process-held exclusive file lock keys on the existing
non-reparse archive **parent** directory's volume/file identity and normalized DB
basename, stable even before DB creation; the DB file's later ID is not part of the
key. The same scope lock is held before schema bootstrap
through campaign execution, avoiding a bootstrap-to-run gap. It excludes compliant
local runners, not copied archives or distributed actors. A separate immutable
claim with `UNIQUE(v2_session_identity)` permanently consumes the session.

Runtime binding: `nar-operational-timing-runtime-binding-v1:<sha256>` binds exact
v2 activation ancestry, sealed bundle, dependency/transport/retry/environment
profile identities, stage/version and runner-issued concurrency/scope. Mismatch or
missing proof is closed nonqualification, not a caller `matches=True`. Binding is
not campaign execution or prediction-policy authority.

Execution: `nar-operational-timing-campaign-execution-v1:<sha256>` is an immutable
one-shot claim binding session/activation/binding/bundle/lock scope. Save and exact-
reload binding, then save and exact-reload claim; only then sample a controlled UTC
`readiness_verified_at` for a separate append-only campaign-readiness receipt.
Receipt save/reload precedes any official attempt. Binding and claim must be proven
by `measurement_start_at`, with equality allowed; a late receipt-reload/launch
check also refuses official execution without moving the fixed window. The receipt
timestamp proves its **parents** were already committed and exact-reloaded, not
that the receipt itself was published then. A failed/late receipt after claim
publication leaves the session consumed. A current-process-only capability requires
the held lock and newly published claim; loading an old claim cannot recreate it.
Crash or normal shutdown releases the OS lock but never the claim:
`CRASHED_OFFICIAL_SESSION_REQUIRES_NEW_PREDECLARED_SESSION`. No mutable status or
completion receipt is required now.

Persistence: a separate same-database Phase104 companion registry adds typed
append-only bundle/profile/binding/claim/readiness families, exact FKs/contradiction
checks, one claim/session, exact reload, and no backfill. Top-level bootstrap under
the scope lock recognizes only empty, Phase99 base, Phase100 companion, Phase103
companion, and exact Phase104 union, installing missing companions in order; all
partial/unknown states fail. Historical strict validators keep their meaning.
Phase104 creates **execution parents only**. Phase105 creates attempt/terminal
domains and tables with restrictive FK to the already-existing claim/attempt at
table creation, not speculative weak text-parent tables.

Likely Phase104 production paths are new runtime-source, dependency/profile,
binding, execution/runner, bootstrap, companion-migration and SQLite repository
modules under `scripts/simulation/`; narrow read-only descriptors in the four
NAR transport files and exact compatible-schema gate extensions require explicit
Allowed Files review. Matching future tests cover Git-object bundle and import
isolation, dependency/transport/proxy mismatch, exact ancestry and timing,
cross-process lock exclusion, crash/no-resume, one-shot claim/capability, all
bootstrap transitions and malformed schemas, with no provider HTTP. The full
file-by-file test plan is in `docs/CURRENT_PHASE.md`.

Remaining blockers: runtime software/configuration proof not yet implemented;
`EFFECTIVE_REQUEST_ENVIRONMENT_BINDING_REQUIRED`; Phase105 wrappers and claim-bound
attempt/terminal persistence; separate live-campaign authorization;
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`; and Phase94/95/41
source-semantic authority. No concrete Delta, policy activation, ROI, or live timing.

Only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md` were modified.
No production/test change, provider HTTP, live campaign, production DB write,
staging, commit, or push. No tests were run for this design-only phase.

Recommended disposition: `DRAFT_FOR_REVIEW`.

Next: `CHATGPT_REVIEW_PHASE104_RUNTIME_AND_EXECUTION_AUTHORITY`.

---

## POST_V0_8_DAILY_REPLAY_103 — V2 MEASUREMENT AUTHORITY FOUNDATION

Phase: `POST_V0_8_DAILY_REPLAY_103`

Formal Status: `READY_FOR_REVIEW`

State: `IMPLEMENTED_FOR_REVIEW`

Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`

Audit: `NAR_V2_MEASUREMENT_AUTHORITY_DESIGN_COMPLETE`

Design Review: `PHASE103_V2_MEASUREMENT_AUTHORITY_DESIGN_REVIEW_PASS`

Implementation: `NAR_V2_MEASUREMENT_CONFIG_SESSION_ACTIVATION_FOUNDATION_IMPLEMENTED`

### Implementation verification

Starting HEAD/tree: `703d429113e58ddfe721dd2c1ab1297d511a6ef5` /
`79a3d36de92efcd4cb4950479d2fda7fb1fccf30`.

V2 has independent canonical configuration/session identities, closed stages and
budget roles, fixed-window half-open admission, and controlled declaration/reload
then clock-sampled verification/reload. Exact receipt retries do not resample the
clock; a declaration-only retry uses the current service clock. The new companion
adds only four V2 authority tables in the same database, with restrictive ancestry,
append-only triggers, exact schema gates and no backfill. Existing V1 domain payloads
and identities are untouched; existing Phase99/100 repositories accept only the
exact compatible union after the companion is installed. No V2 attempt/terminal,
runtime binding, execution claim, runner, or passive wrapper was implemented.

Focused new tests: 27 passed. Required regressions: 66 passed. Full suite:
4,617 passed, 2 skipped, 2,846 subtests passed. Only in-memory test SQLite was
written; no production database write, provider HTTP, or live timing campaign.
`V1_MEASUREMENT_AUTHORITY_REMAINS_IMMUTABLE` and
`V2_ATTEMPT_TERMINAL_PERSISTENCE_DEFERRED_PENDING_EXECUTION_PARENT` remain frozen.
Runtime source/configuration proof, execution authority, source-semantic blockers,
and `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remain unresolved.

Next: `CHATGPT_REVIEW_PHASE103_IMPLEMENTATION`.

### Historical Phase103 design report

### Phase102 reconciliation and V2 boundary

`PHASE102_CAMPAIGN_RUNNER_AND_RUNTIME_AUTHORITY_REVIEW_PASS`;
`POST_V0_8_DAILY_REPLAY_102 = ARCHITECTURAL_AUDIT_COMPLETE`;
`CRASH_NO_OFFICIAL_RESUME_CONTRACT = FROZEN`;
`PHASE102_V2_MEASUREMENT_AUTHORITY_EXTENSION_REQUIRED = CONFIRMED`; and
`PHASE102_RUNTIME_BINDING_IMPLEMENTATION_DEFERRED_PENDING_V2_AUTHORITY_CONTRACT = CONFIRMED`.
The Phase102 report below is historical design material.

`V1_MEASUREMENT_AUTHORITY_REMAINS_IMMUTABLE`. Phase99/100 v1 canonical payloads,
identity prefixes, domains, registries, rows, and meaning stay unchanged. No v1
class accepts v2, no conversion/backfill exists, and v1/v2 evidence never silently
aggregates. Phase103 can safely freeze config/session/activation now, but not V2
attempt/terminal persistence before Phase104 provides strict runtime/execution
parents: `V2_ATTEMPT_TERMINAL_PERSISTENCE_REQUIRES_PHASE104_EXECUTION_PARENT`.

### Frozen V2 contract

Independent canonical identities are
`nar-operational-timing-config-v2`, `session-v2`, `activation-declaration-v2`,
`activation-verification-v2`, reserved `attempt-v2`, and reserved `terminal-v2`,
each followed by SHA-256. Reserve Phase104 parent prefixes
`nar-operational-timing-runtime-binding-v1` and
`nar-operational-timing-campaign-execution-v1`. Prefixes cannot substitute for one
another. V2 uses explicit frozen/slotted domains and explicit UTF-8 NFC canonical
JSON; it does not inherit V1 serialization.

V2 configuration content-addresses schema 2, repository/provider scope, declared
commit, instrumentation schema 2, closed ordered V2 stages, exact transport/retry/
concurrency profiles, admission semantics, and execution-authority semantics. V2
stages retain acquisition/input and post-C operation boundaries and add only defined
control/provenance/observer stages: campaign execution preparation, runtime readiness,
freeze receipt construction/publication/exact reload, attempt-start publication, and
terminal publication. Closed budget roles are `PRE_C_FREEZE`, `FREEZE_PROVENANCE`,
`OBSERVABILITY_OVERHEAD`, `POST_C_COMPUTE`, and `CAMPAIGN_CONTROL`. Mandatory receipt
and synchronous attempt publication costs must remain visible to future Delta review;
the classification alone chooses no arithmetic.

V2 session remains fixed-window aware-UTC half-open admission. It renames the
pre-publication timestamp precisely as `attempt_admitted_at` /
`MEASUREMENT_ATTEMPT_ADMISSION_TIMESTAMP`; membership remains even if observer
overhead delays callable entry past end. Failures/timeouts remain denominator.
V2 activation repeats the Phase100 two-artifact declaration → exact reload → clock
sample → verification receipt → exact reload chain, with one declaration/session and
one receipt/declaration. V1 activation cannot activate V2.

Future V2 attempt requires exact session/configuration plus campaign execution claim,
stage, correlation, sequence, admission timestamp, and load context. It does not
repeat runtime binding because strict ancestry is attempt → execution claim → binding.
The existing correlation and load-context values may be reused unchanged: neither
encodes measurement schema nor asserts authority. Official/diagnostic status derives
from future execution ancestry, never an attempt boolean. V2 terminal binds the exact
attempt, finish UTC, integer elapsed microseconds, closed result/failure class,
optional artifact digest, and no outcome text. It adds V2 `INTERNAL` only for
unexpected internal errors. The pure conversion is
`(finish_ns - start_ns) // 1000`, nonnegative exact ints only; submicrosecond is 0.

### Persistence and handoff

Choose architecture A. Phase103's new same-database V2 authority companion persists
only V2 configurations, sessions, activation declarations, and activation
verifications with exact DDL, append-only triggers, strict FKs, exact reload, and no
backfill. Do not create weak attempt/terminal tables with text execution identities.
Phase104 must first persist runtime binding/readiness and campaign execution claims;
Phase105 then adds V2 attempts/terminals with restrictive execution/attempt FKs.
The final chain is V2 configuration → session → activation declaration → activation
verification → runtime binding → campaign execution claim → attempt → terminal.

Top-level bootstrap evolves by exact known unions only: Phase99 base → Phase100
activation → Phase103 V2 authority → Phase104 runtime/execution → Phase105 V2
observations. Original strict validators stay strict; partial/unknown states fail.
Phase103 excludes runner, lock, source bundle, runtime binding, execution claim,
wrappers, HTTP, timing campaign, and Delta selection.

Future tests cover V1 preservation; distinct V2 identities; canonical stage/budget
roles; V2 sessions/admission; two-artifact V2 activation; cross-ancestry rejection;
required execution identity; terminal/timer rules; no outcome material; exact
companion schema/no backfill; and preservation of Phase104's strict execution-parent
FK path. Remaining blockers are the v2 extension/runtime-binding deferral, runtime
source/configuration proof, operational Delta audit, and Phase94/95/41 semantics.
No production/test code, HTTP, live campaign, DB write, commit, or push occurred.

Recommended disposition: `DRAFT_FOR_REVIEW`.

Next: `CHATGPT_REVIEW_PHASE103_V2_MEASUREMENT_AUTHORITY`.

---

## POST_V0_8_DAILY_REPLAY_102 — CAMPAIGN RUNNER AND RUNTIME EXECUTION AUTHORITY DESIGN

Phase: `POST_V0_8_DAILY_REPLAY_102`

Status: `DRAFT_FOR_REVIEW`

Outcome: `READY_FOR_ARCHITECTURAL_REVIEW`

Audit: `NAR_CAMPAIGN_RUNNER_AND_RUNTIME_EXECUTION_AUTHORITY_DESIGN_COMPLETE`

Implementation: `NOT_STARTED_PENDING_FINAL_ARCHITECTURAL_REVIEW`

### Final architectural revision

Record `PHASE102_ARCHITECTURAL_REVIEW_REQUIRES_REVISION`: primary
`PROCESS_LIFETIME_LOCK_DOES_NOT_ENFORCE_CRASH_NO_RESUME`; secondary
`V2_MEASUREMENT_AUTHORITY_MUST_PRECEDE_RUNTIME_BINDING_IMPLEMENTATION`.
The earlier Phase102 lock proposal is superseded where it implied crash no-resume
from an OS lock alone.

`PROCESS_LOCK != PERSISTENT_SESSION_CONSUMPTION_AUTHORITY`. A process-lifetime OS
advisory lock is retained solely for simultaneous-execution exclusion and normally
releases after a crash. Add immutable append-only
`NAROperationalTimingCampaignExecutionClaim`, binding exact v2 configuration/session,
activation declaration/verification, runtime binding/readiness, runner semantic,
canonical lock scope, sealed source provenance, and instrumentation semantic. The
runtime companion schema enforces one claim per `session_identity`.
`ONE_MEASUREMENT_SESSION = AT_MOST_ONE_OFFICIAL_CAMPAIGN_EXECUTION`.

Official authority is both `PROCESS_LOCK + PERSISTENT_EXECUTION_CLAIM`. After exact
archive bootstrap and process-lock acquisition, reload exact v2 session, activation,
and runtime ancestry; prove no claim; save and exact-reload the claim; then issue a
new in-process capability. No official attempt precedes that capability.
`PERSISTED_EXECUTION_CLAIM != CURRENT_PROCESS_EXECUTION_CAPABILITY`: archive lookup
cannot resume a campaign. If the process dies after claim publication, lock release
does not permit re-entry; the same session is permanently consumed and a new,
prospectively activated session is required
(`CRASHED_OFFICIAL_SESSION_REQUIRES_NEW_PREDECLARED_SESSION`). A completion receipt
may later document closure but never makes a claim reusable.

The local lock scope is canonical repository identity plus resolved archive identity
and serial regime. It rejects relative aliases, symlinks/junctions/reparse points,
and unsafe lock locations. This is a trusted single-machine KeibaOS boundary, not
distributed cryptographic uniqueness: a copied archive elsewhere is outside its
claim. Bootstrap uses a distinct short lock; execution retains the campaign lock.

`CONTROLLED_SEALED_GIT_SOURCE_BUNDLE_V1` is strengthened:
`SEALED_BUNDLE_BYTES_MUST_DERIVE_FROM_REVIEWED_GIT_OBJECT_TREE`. The source chain is
repository → commit SHA → commit tree SHA → Git object materialization → ordered
member paths and byte SHA-256 values → canonical manifest SHA → bundle identity.
Never make the authority by copying mutable worktree bytes after a clean check.
`CONTROLLED_CLEAN_GIT_WORKTREE_V1` remains diagnostic/operator preflight for exact
HEAD/tree, clean tracked/index state, ordinary untracked files, and merge/cherry-
pick/rebase state. `DEVELOPER_WORKTREE_STATE != SEALED_RUNTIME_SOURCE_AUTHORITY`.

Critical KeibaOS modules execute from only the sealed bundle with isolated Python,
controlled `sys.path`, no mutable worktree/current-directory import root, and no
caller `PYTHONPATH`. Verify critical module origins against the manifest. Ignored
files are allowed only when absent from the bundle and unreachable from approved
import roots. Bind Python implementation/version, Requests, urllib3, SQLite runtime,
and reviewed platform compatibility material; unrelated packages remain diagnostic.

The runtime transport profile is derived from actual production composition, never
caller numbers. It records the reviewed timeouts, effective adapter retry fields,
redirect/TLS/stream behavior, `trust_env` mode, and no runner-level retry loop. It
does not claim that `HTTPAdapter(max_retries=0)` forbids TCP/DNS/proxy/lower-layer
behavior. A mismatch is nonqualifying.

Phase99/100 v1 configuration/session/activation/attempt/terminal contracts remain
immutable. Official timing needs a separately reviewed v2 family with new stages for
attempt/terminal publication, freeze-receipt publication/reload, and material runner
overhead. V2 ancestry must be configuration → session → activation declaration →
activation verification → runtime binding → execution claim → attempt → terminal;
each attempt binds the execution claim. Therefore freeze
`PHASE102_RUNTIME_BINDING_IMPLEMENTATION_DEFERRED_PENDING_V2_AUTHORITY_CONTRACT`.

Revised decomposition: Phase102 remains design only; Phase103 implements v2
measurement authority; Phase104 implements bootstrap, runner/lock, sealed source,
runtime profile/binding/readiness, claim, and capability; Phase105 implements passive
wrappers. Provider HTTP remains separately unauthorized throughout.

Required future tests include two-runner exclusion; one claim per session; crash-lock
release without same-session resume; completion non-reuse; old-claim/no-new-capability;
canonical archive alias/junction handling; exact Git object-tree member/manifest
materialization; post-bundle worktree mutation; import-origin/PYTHONPATH shadow
rejection; v1 byte/identity preservation; distinct v2 identity and claim-bound
attempts; source/profile/retry/runtime ancestry mismatches; and strict known archive
bootstrap states. `RUNTIME_SOFTWARE_COMMIT_PROVENANCE_REQUIRED`,
`RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED`,
`PHASE102_V2_MEASUREMENT_AUTHORITY_EXTENSION_REQUIRED`,
`PHASE102_RUNTIME_BINDING_IMPLEMENTATION_DEFERRED_PENDING_V2_AUTHORITY_CONTRACT`,
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`, and the Phase94/95/41
semantic blockers remain unresolved. Recommended disposition: `DRAFT_FOR_REVIEW`.

### Phase101 reconciliation and primary findings

`PHASE101_RUNTIME_BINDING_AND_WIRING_ARCHITECTURE_REVIEW_PASS`;
`POST_V0_8_DAILY_REPLAY_101 = ARCHITECTURAL_AUDIT_COMPLETE`;
`PHASE101_CAMPAIGN_RUNNER_REQUIRED_FOR_CONCURRENCY_BINDING = CONFIRMED`;
`RUNTIME_SOFTWARE_COMMIT_PROVENANCE_REQUIRED = CONFIRMED`; and
`PASSIVE_LIVE_TIMING_WIRING = DEFERRED_PENDING_RUNTIME_EXECUTION_AUTHORITY`.
Phase100 remains formally complete and integrated. The Phase101 report below is
historical audit material.

The current acquisition call graph is serial only within one invocation. It has no
campaign-wide owner, cross-process exclusion, sealed source artifact, actual-runtime
transport-profile issuer, or build identity bound to the executing code. Therefore
`LOCAL_CALL_GRAPH_SERIALITY != PROCESS_CAMPAIGN_CONCURRENCY_AUTHORITY`,
`DECLARED_SOFTWARE_COMMIT != RUNTIME_BOUND_SOFTWARE_COMMIT`, and
`GIT_HEAD_MATCH != RUNTIME_SOURCE_TREE_PROVENANCE`. The Phase99 v1 identity family
also cannot express observer-publication/runtime-overhead stages without changing
persisted v1 meaning. `RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED` remains
open; record `PHASE102_CAMPAIGN_RUNNER_REQUIRED_FOR_CONCURRENCY_BINDING`,
`CONTROLLED_RUNTIME_SOURCE_PROVENANCE_REQUIRED`, and
`PHASE102_V2_MEASUREMENT_AUTHORITY_EXTENSION_REQUIRED`.

### Proposed controlled execution authority

The narrow future `NAROperationalTimingCampaignRunner` is not a race scheduler. It
owns a single official session envelope and serially invokes one target workflow and
one HTTP operation at a time, without workers, async fan-out, or parallel venues.
Its proof is a process-lifetime OS advisory exclusive lock at a deterministic scope
of repository identity plus resolved observability-archive path and the serial
regime. The lock is held throughout source sealing, runtime binding, and official
work; a process-local UUID can be diagnostic only. Use a native lock adapter and a
regular non-reparse lock location; no clock lease. Lock release follows normal exit
or crash, but a crashed session cannot resume officially under v1: a fresh activated
future session is required. The runner is the sole issuer of serial concurrency
authority for participating official composition, not a claim about unrelated code.

Archive bootstrap uses a separate short setup lock: exact empty → Phase99 base →
Phase100 activation → runtime companion; base-only → activation → runtime;
activation-installed → runtime; runtime-installed → no-op; all partial/unknown
states fail. Strict historical base/activation gates remain strict and must never be
blindly rerun after companions exist.

### Source, runtime, and profile binding

Select `CONTROLLED_SEALED_GIT_SOURCE_BUNDLE_V1`: preflight a clean exact repository
and build an immutable source bundle from `HEAD`/`HEAD^{tree}`. Its content-addressed
provenance binds repository, commit, tree, archive-member manifest, source-isolation
semantic, and critical module origins. Execute from only that bundle under an
isolated import path, not mutable worktree/PYTHONPATH. Reject tracked/staged,
ordinary untracked, and merge/cherry-pick/rebase states. Ignored material may be
permitted only when it cannot be imported from an approved root; it is absent from
the sealed bundle. A clean pre/post worktree check alone is diagnostic, not source
provenance. No current build-manifest/source-bundle implementation exists.

Bind Python exact version, Requests, urllib3, SQLite runtime, and reviewed platform
compatibility material. The current production transports are 10s/10s for bootstrap,
daily-target, and official-response, and 10s/20s for market odds; all explicitly use
`HTTPAdapter(max_retries=0)`, no redirects, streaming, and TLS verification, while
market odds sets `trust_env=False`. These are not a complete network retry guarantee:
the runtime descriptor must represent actual effective adapter settings and the
runner's absence of app-level retries, but may not claim absence of lower-layer
retransmission/proxy behavior. Derive descriptors from actual transport composition,
not caller timeout values or duplicated literals. Mismatch fails qualification.

`NAROperationalTimingRuntimeBinding` will content-bind exact Phase100 ancestry,
source/build provenance, runtime compatibility, derived transport/retry profile,
runner concurrency scope, enabled stages, and version semantics. It is append-only
in a new same-database runtime companion with restrictive ancestry FKs, no backfill,
and exact reload. To prove readiness before a fixed session start, save/reload the
semantic binding, then issue a controlled verification receipt; require it by
session start. Do not reuse an old process's receipt after a crash. Closed
qualification separates source/tree, transport, retry, concurrency, activation, and
late-readiness failures from `OFFICIAL_RUNTIME_CONFIGURATION_MATCH`.

### V2, wrappers, and handoff

Do not mutate Phase99 v1 stage/config/session/attempt/terminal/activation semantics.
Create a separate v2 family for publication and runner overhead stages, including
attempt/terminal publication and freeze-receipt publication/reload, with distinct
canonical identities and archive tables. V1 data remains immutable and cannot enter
v2 official aggregation. This extension must be reviewed before implementation.

Phase99 `operation_started_at` is the admission timestamp, sampled before durable
attempt publication and callable entry. A pre-end admitted attempt remains in the
half-open population even if observer overhead delays the call. The runner owns one
aware UTC clock and one monotonic timer; with `perf_counter_ns`, persist
nonnegative `(finish_ns - start_ns) // 1000` microseconds, with submicrosecond spans
zero and no float/wall-clock latency calculation. Attempt/terminal overhead is a
separate v2 PRE_C cost. Preserve original operation outputs/exceptions; a terminal
write failure leaves an unresolved attempt. `freeze_completed_at` retains its Phase99
save/commit-plus-exact-reload meaning.

`DIAGNOSTIC_TIMING` stays segregated from `OFFICIAL_ACTIVATED_TIMING`, which requires
v2 activation, pre-start runtime readiness, the held runner lock, exact source/profile
match, and binding-linked admitted attempts. Phase102 authorizes neither HTTP nor a
live campaign. Phase103 may design/implement passive wrappers only after independent
review, followed by separate campaign execution approval.

Likely future paths: campaign runner, runtime source provenance, runtime profile,
runtime binding, archive bootstrap, runtime companion migration/repository, and a
separately reviewed v2 observability/activation family; Phase103 later adds passive
wrapper composition. Tests must cover source cleanliness/tree/origin/mutation,
cross-process lock and crash no-resume, derived profile mismatch, activation/runtime
ancestry, known archive topology transitions, v1/v2 non-reinterpretation, admission
and timer rules, exception preservation, unresolved attempts, and no HTTP/output
mutation.

No production/test code, HTTP, live campaign, production DB write, commit, or push
occurred. Only the phase-control docs are modified. Concrete Delta and all Phase94/
95/41 semantic blockers remain unresolved. Recommended disposition:
`DRAFT_FOR_REVIEW`.

Next: `CHATGPT_REVIEW_PHASE102_CAMPAIGN_RUNNER_AND_RUNTIME_AUTHORITY`.

---

## POST_V0_8_DAILY_REPLAY_101 — RUNTIME BINDING AND PASSIVE WIRING AUDIT

Phase: `POST_V0_8_DAILY_REPLAY_101`

Status: `DRAFT_FOR_REVIEW`

Outcome: `READY_FOR_ARCHITECTURAL_REVIEW`

Audit: `NAR_RUNTIME_MEASUREMENT_BINDING_AND_PASSIVE_WIRING_DESIGN_COMPLETE`

### Formal reconciliation and primary finding

`PHASE100_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`;
`POST_V0_8_DAILY_REPLAY_100 = FORMALLY_COMPLETE`;
`NAR_PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY = FORMALLY_INTEGRATED`.
Phase99 remains `PHASE99_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`,
`POST_V0_8_DAILY_REPLAY_99 = FORMALLY_COMPLETE`, and
`NAR_PRE_C_FREEZE_PROVENANCE_AND_TIMING_OBSERVABILITY_FOUNDATION = FORMALLY_INTEGRATED`.
The Phase100 handoff below is historical; its pending-review wording is superseded.

Primary finding: `PHASE101_CAMPAIGN_RUNNER_REQUIRED_FOR_CONCURRENCY_BINDING`.
The target-acquisition call graph is sequential within one invocation, but no
campaign-wide or cross-process exclusion establishes Phase99's declared single-worker
regime. A second independent blocker is `RUNTIME_SOFTWARE_COMMIT_PROVENANCE_REQUIRED`:
the configuration validates a declared Git SHA, not the identity of the executing
artifact. `RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED` remains open.

### Runtime authority and actual profile

The future immutable, content-addressed runtime binding must bind the exact archived
configuration → session → activation declaration → verification receipt chain to a
trusted build identity, effective transport/retry descriptors, campaign concurrency
authority, enabled stages, and instrumentation version. Official attempts must be
traceable to that binding; the existing attempt's session identity alone is not
enough. No caller boolean or detached commit string may assert runtime equality.
`DECLARED_SOFTWARE_COMMIT != RUNTIME_BOUND_SOFTWARE_COMMIT`; a reviewed build/deployment
manifest bound to the executing artifact is required, without runtime GitHub access.

The inspected bootstrap, daily-target, and official-response transports use
connect/read `10s/10s`; market-odds raw uses `10s/20s`. All configure
`HTTPAdapter(max_retries=0)`, disable redirects, and stream responses; market odds
also sets `trust_env=False`. These are local implementation facts, not a global
request deadline or proof that an injected transport uses them. Official composition
must derive the effective runtime profile from actual closed collaborators and
compare it exactly with the Phase99 configuration. Adapter `max_retries=0` does not
alone prove the entire retry/environment regime. Local sequential RaceList capture
does not prove process-wide seriality or absence of another worker/venue.

### Composition, observers, and causal ordering

The historical Phase99 strict base-v1 migration rejects a companion-installed DB.
A future top-level bootstrap must accept only four exact states: empty → base plus
activation; base-only → activation; exact companion-installed → no-op; partial or
unknown → fail. Keep historical validators strict. A later runtime-binding
companion would preserve Phase99/100 rows, use exact ancestry FKs, and require exact
archived reload before official timing attempts. No backfill.

The Phase99 stage taxonomy lacks attempt-publication, terminal-publication, and
freeze-receipt publication/reload overhead. Recommend a versioned instrumentation
schema v2 and new configuration identity rather than silently changing v1. One
campaign-owned aware-UTC clock supplies causal timestamps; one monotonic provider
(candidate `time.perf_counter_ns()`) supplies elapsed nanoseconds, converted to
microseconds by nonnegative floor division by 1000. Wall-clock differences do not
define latency.

Official wrapper ordering is: verify activation/runtime/campaign authority; sample
UTC attempt start; durably publish the attempt and binding ancestry; start monotonic
timer; invoke the unchanged operation; stop monotonic timer; sample UTC finish;
publish terminal. Attempt publication is separately measured overhead, not hidden
inside operation latency. A start admitted under the half-open session window stays
in the denominator even if publication or completion runs past its end. If the
attempt cannot be published, do not fabricate an official sample; diagnostic
continuation requires a separate composition rule. A terminal-write failure leaves
an unresolved attempt and must not replace the production result or exception.

Use closed timeout, transport, validation, persistence, and unsupported mappings;
unexpected internal failure needs a reviewed v2 class. Preserve original exceptions
and never backdate a terminal after a wall-clock reversal. Derive correlation from
actual provider, target-set, race, plan, and policy objects as they become available;
pre-target-set stages need a runner-bound workflow/request identity, not a later
invented target-set SHA.

The audited wrapper seams are the bootstrap/home/monthly/RaceList acquisition
services, official-response and market-odds capture functions, snapshot builder and
SQLite save/reload, Phase99 freeze-receipt issuer, and post-C bet-plan execution.
Injected transport/archive composition can observe most boundaries without changing
URLs, headers, timeouts, retry, parsing, artifacts, or model output. Concrete type
checks in prediction orchestration limit fine-grained proxying and require later
review. Phase99 `freeze_completed_at` stays the UTC sample after snapshot commit and
exact reload, before receipt publication; those receipt stages require separate
timing. Post-C wrappers may consume only the frozen input.

### Disposition and future scope

Distinguish `DIAGNOSTIC_TIMING` from `OFFICIAL_ACTIVATED_TIMING`. The latter needs
exact Phase100 predeclaration, trusted runtime build/profile, campaign exclusivity,
attempt-to-binding ancestry, and half-open admission. A completed Phase101 design or
implementation would not itself authorize provider HTTP or a live campaign.

Recommend split **C — campaign runner first**: review and build a bounded serial
campaign composition, trusted runtime build/profile provenance, and exact archive
bootstrap before separately reviewed runtime-binding persistence and passive
wrappers. Do not create a full race scheduler. Likely first production paths are new
`scripts/simulation/nar_operational_timing_campaign_runner.py`,
`scripts/simulation/nar_operational_timing_runtime_profile.py`,
`scripts/simulation/nar_operational_timing_archive_bootstrap.py`, plus a reviewed
build-manifest producer/loader. Later paths are new runtime-binding domain,
companion migration/repository, and passive-wrapper modules, with narrow composed
archive-gate and versioned observability changes only after review. No existing
production or test path is changed in this PREPARE.

Future tests must cover exact ancestry, build/profile/retry/concurrency mismatch,
exact archive bootstrap states, cross-process exclusion and crash recovery, attempt
before operation, monotonic/UTC independence, observer overhead, exception and
timeout preservation, unresolved attempts, after-window completion, correlation,
v1/v2 separation, and unchanged provider requests/prediction outputs.
Likely new paths are `tests/test_nar_operational_timing_campaign_runner.py`,
`tests/test_nar_operational_timing_runtime_profile.py`,
`tests/test_nar_operational_timing_archive_bootstrap.py`,
`tests/test_nar_operational_timing_runtime_binding.py`,
`tests/test_nar_operational_timing_runtime_archive_migration.py`,
`tests/test_sqlite_nar_operational_timing_runtime_archive.py`, and
`tests/test_nar_operational_timing_passive_wrappers.py`. Regressions should include
existing Phase99/100 domain/archive/migration tests and current acquisition,
snapshot-freeze, and bet-plan execution tests; each implementation subphase must
freeze its own exact test commands.

`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remains unresolved, as do
the Phase94/95 entry-status source-semantic blockers and the Phase41 market gate.
No Delta selection, scheduler, provider HTTP, live sample, production DB write,
implementation, tests, stage, commit, or push occurred. Only the two phase-control
docs are modified. Recommended Phase101 disposition: `DRAFT_FOR_REVIEW`.

Next: `CHATGPT_REVIEW_PHASE101_RUNTIME_BINDING_AND_WIRING`.

---

## POST_V0_8_DAILY_REPLAY_100 — CAMPAIGN ACTIVATION AND PASSIVE WIRING DESIGN

Phase: `POST_V0_8_DAILY_REPLAY_100`

Formal Status: `READY_FOR_REVIEW`

State: `IMPLEMENTED_FOR_REVIEW`

Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`

Audit: `NAR_TIMING_CAMPAIGN_ACTIVATION_AND_PASSIVE_WIRING_DESIGN_COMPLETE`

Implementation: `NAR_PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY_IMPLEMENTED`

Design Review: `PHASE100_CAMPAIGN_ACTIVATION_DESIGN_REVIEW_PASS`

### Implementation result

Phase100 adds a canonical immutable activation declaration, a separate verification
receipt, closed official/late/unavailable qualification, a same-database companion
schema with its own v1 registry, an exact activation repository, and controlled
issuance. It modifies only the normal Phase99 archive schema gate to accept either
exact historical base v1 or exact base plus exact companion v1. The original Phase99
strict base-v1 validator, tables, registry, rows, and record meanings are unchanged.

The declaration references the exact archived Phase99 session and configuration;
its canonical SHA identity contains no timestamp. The receipt references the exact
declaration and service-sampled UTC `activation_verified_at`. Issuance saves and
exact-reloads declaration before sampling UTC, then saves and exact-reloads receipt.
Exact retries reuse the receipt without a new clock sample. A declaration-only retry
uses the current clock, so it cannot reconstruct an earlier verified time. Official
qualification requires exact archived ancestry and verification no later than session
start. No existing session was backfilled or synthesized.

Companion migration is atomic and idempotent from exact base v1. Its tables prohibit
UPDATE/DELETE, enforce restrictive ancestry and one declaration/verification per
parent, and the Phase100 gate rejects partial/unknown objects. Existing Phase99
configuration, session, attempt, terminal, unresolved-attempt, and freeze-receipt
operations continue after companion installation. No live wiring or runtime-binding
claim is made; `RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED` remains Phase101
work. The concrete offset remains subject to the operational timing audit.

Changed production paths: new
`scripts/simulation/nar_operational_timing_session_activation.py`,
`scripts/simulation/nar_operational_timing_activation_archive_migration.py`,
`scripts/simulation/sqlite_nar_operational_timing_activation_archive.py`; modified
`scripts/simulation/sqlite_nar_operational_timing_observability_archive.py`.
Added three matching focused test files and updated the two phase-control docs.

Focused activation tests: `14 passed`. Focused plus required Phase99 and
snapshot/cutoff regressions: `91 passed, 30 subtests passed`. Full suite:
`4590 passed, 2 skipped, 2846 subtests passed`. Provider HTTP / live campaigns /
production DB writes: `0 / 0 / 0`; temporary in-memory SQLite writes occurred only
in tests. No Phase101 passive wrappers, concrete Delta, scheduler, policy activation,
or ROI work was undertaken. This historical handoff was subsequently superseded by
`PHASE100_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`.

### Final architectural revision

Phase99 remains formally reconciled: `PHASE99_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`,
`POST_V0_8_DAILY_REPLAY_99 = FORMALLY_COMPLETE`, and
`NAR_PRE_C_FREEZE_PROVENANCE_AND_TIMING_OBSERVABILITY_FOUNDATION = FORMALLY_INTEGRATED`.

Record `PHASE100_ARCHITECTURAL_REVIEW_REQUIRES_REVISION`: primary
`V1_OBSERVABILITY_REGISTRY_CANNOT_DIRECTLY_ACCEPT_V2_MIGRATION`; secondary
`ACTIVATION_TIMESTAMP_DOES_NOT_YET_PROVE_PRESTART_ACTIVATION_PUBLICATION`.

The existing Phase99 observability registry is exact v1: its `version` check permits
only `1`, its registered migration name is v001, and its gate requires the exact v1
object set. The prior in-place v2 proposal is superseded. Preserve every base-v1
registry/table/row/trigger/payload/validator unchanged; do not add a base-registry v2
row, backfill, or synthesize activation.

Phase100 instead adds a same-database companion registry,
`nar_operational_timing_activation_schema_migrations`, with exact companion-v1
identity and append-only declaration/verification-receipt tables. Its migration first
verifies exact base v1, then atomically creates its registry, tables, restrictive FKs,
and immutability triggers. Declarations reference
`nar_operational_timing_sessions(identity)` with `ON UPDATE RESTRICT ON DELETE
RESTRICT`; receipts reference declarations. The Phase99 gate remains base-v1 only; a
new Phase100 gate validates the exact base-v1-plus-companion-v1 union. Idempotent exact
upgrade succeeds; malformed base, partial companion, changed existing objects, or
unknown extras fail closed.

The authority is a two-artifact chain. Immutable content-addressed
`NAROperationalTimingMeasurementSessionActivationDeclaration` binds only schema,
exact archived session/configuration identities, and a closed activation semantic; it
has no timestamp or outcome material. The controlled issuer reloads session/config,
saves and exact-reloads the declaration, and only then samples service-owned UTC time.
It saves/reloads a verification receipt binding declaration/session/config identities,
closed verification semantic, and `activation_verified_at`.

The timestamp proves the declaration already committed and exact-reload verified no
later than the sample; it does not prove receipt publication by then. Therefore
`ACTIVATION_DECLARATION_IDENTITY != VERIFIED_PRESTART_ACTIVATION_AUTHORITY`.
`OFFICIAL_PREDECLARED_MEASUREMENT_SESSION` requires the exact archived chain and
`activation_verified_at <= measurement_start_at` (equality is eligible). A late record
is `ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START`; missing/contradictory provenance is
`ACTIVATION_PROVENANCE_UNAVAILABLE`. Retrospective semantic values, session SHA,
declaration construction time, and row/filesystem metadata never qualify.

Activation only predeclares a timing campaign. It does not authorize Delta, Phase97
policy activation, status/market eligibility, ROI, or runtime reality. Preserve
`MEASUREMENT_SESSION_IDENTITY != PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY`,
`DECLARED_SOFTWARE_COMMIT != RUNTIME_BOUND_SOFTWARE_COMMIT`, and
`RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED`. Phase100 is activation-only;
Phase101 must review runtime binding, UTC/monotonic composition, attempt wiring, and
passive wrappers. The first official Delta campaign remains unavailable, and
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remains unresolved.

Expected Phase100 paths are new
`scripts/simulation/nar_operational_timing_session_activation.py`, new
`scripts/simulation/nar_operational_timing_activation_archive_migration.py`, and a
narrow archive-repository change or dedicated activation repository wrapper, plus
focused activation/companion-migration/archive tests. Required tests include exact
v1-to-companion upgrade without base-registry v2, exact-union validation, no backfill,
controlled declaration→reload→clock→receipt ordering, before/equal/after-start states,
append-only idempotency/conflict behavior, and authority separation. No production
code, tests, provider HTTP, DB writes, staging, commit, or push occurred.

### Phase99 reconciliation

`PHASE99_IMPLEMENTATION_REMOTE_VERIFICATION_PASS` is recorded. Phase99 is formally
complete and `NAR_PRE_C_FREEZE_PROVENANCE_AND_TIMING_OBSERVABILITY_FOUNDATION` is
formally integrated. The prior measurement-session review requirement is resolved.

Phase99 establishes timing record identity, but its session SHA remains semantic
identity only. It does not prove the session was declared before observation begins:

`MEASUREMENT_SESSION_IDENTITY != PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY`.

### Historical preliminary Phase100 design — superseded

Everything in this historical preliminary block through the Phase99 separator records
the replaced single-record/in-place-v2 proposal only. The final architectural revision
above is the sole current Phase100 contract.

`PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY_REQUIRED`.

The minimum new authority is a content-addressed
`NAROperationalTimingMeasurementSessionActivation`. It binds the exact archived
session, its exact measurement configuration, a closed
`PREDECLARED_BEFORE_MEASUREMENT_WINDOW` semantic, and a service-owned UTC
`activated_at`. Its canonical NFC UTF-8 JSON SHA is exposed as
`nar-operational-timing-session-activation-v1:<sha256>`.

The controlled issuer reloads the exact configuration/session, samples its injected
centralized UTC clock, requires `activated_at <= measurement_start_at`, writes the
record append-only, and exactly reloads it. Equality at session start qualifies. A
late activation fails issuance; no nonofficial activation variant, backfill, or
synthetic activation for existing sessions is created.

This authority proves only campaign declaration. It does not activate a Phase97 policy,
select Delta, establish entry-status or market authority, determine race eligibility,
or authorize ROI. Therefore:

`SESSION_ACTIVATION_AUTHORITY != SESSION_IDENTITY`

`SESSION_ACTIVATION_AUTHORITY != POLICY_ACTIVATION_AUTHORITY`

`SESSION_ACTIVATION_AUTHORITY != PREDICTION_CUTOFF_POLICY`

### Archive and official aggregation design

Use a v2 migration of the existing isolated observability archive. It retains exact v1
tables, rows, triggers, and payloads; adds one immutable activation table with a
one-to-one session foreign key and restrictive foreign-key actions; and rejects
partial, altered, or unregistered v2 schemas. Migration starts only from exact v1,
runs atomically, and is idempotent. V1-only archives remain diagnostic and receive no
retroactive authority.

Official timing aggregation will require exact configuration compatibility, one timely
activation per selected session, Phase99 half-open attempt membership, the whole
attempt denominator, terminal records where present, and unresolved-attempt counts.
The eligible state is `OFFICIAL_PREDECLARED_MEASUREMENT_SESSION`; missing or
contradictory activation is `DIAGNOSTIC_UNAUTHORIZED_MEASUREMENT_SESSION`. Diagnostic
sessions cannot silently contribute to official Delta selection. Session SHA may differ
across campaigns; configuration SHA must match.

### Passive wiring contract

Live composition must validate a configuration from executing collaborators rather than
trust a caller-written description. It must bind current timeout/retry constants,
serial RaceList behavior, worker regime, enabled stages, and a deployment-provided
immutable runtime commit. `DECLARED_SOFTWARE_COMMIT` and
`RUNTIME_BOUND_SOFTWARE_COMMIT` must match for official evidence. A process lacking a
runtime-bound commit remains diagnostic. No runtime GitHub lookup is needed.

Wrappers use one centralized injected UTC clock for causal timestamps and a separate
injected monotonic timer for elapsed spans. Each stage publishes its attempt start
before measured work starts, then measures the underlying operation, and publishes a
closed terminal result. A missing terminal after failure/crash stays unresolved.
Underlying production exceptions are rethrown. Required attempt/receipt archival
overhead is recorded as observability overhead and included in later PRE_C envelope
review; its cost cannot disappear from Delta evidence.

The existing composition boundaries are supplier bootstrap capture methods, supplied
daily-target/RaceList capture, the outer daily acquisition application, official
response capture, raw market-odds acquisition, snapshot building, the existing
save→reload→receipt service, and post-C historical bet-plan execution. Phase99
`freeze_completed_at` remains sampled after snapshot save/reload and before receipt
archive publication. Receipt archive persistence/reload therefore requires separate
timing stages and does not redefine the Phase99 freeze semantic.

### Implementation decomposition

Recommend two implementation phases:

1. **Phase100:** activation authority only. Modify the observability archive migration
   and repository, add the controlled activation service, tests, and phase documents.
2. **Phase101:** passive live adapters after Phase100 review. Add an adapter/composition
   module and only the reviewed capture/snapshot/post-C composition changes necessary
   to install it.

This split avoids publishing timing samples before the authority used to judge them
has its own reviewed archive contract. A full scheduler is not required for the Phase100
foundation; it becomes a separate prerequisite if future operation exceeds the existing
single-worker serial regime.

The first official campaign sequence is exact configuration/runtime binding; archive
configuration and fixed future session; timely activation; durable attempt starts;
terminal/reconciliation evidence; read-only timing statistics; independent Delta
review. An unactivated diagnostic dry run may test adapters but cannot enter official
Delta evidence.

### Remaining blockers

`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remains unresolved. So do
the independent entry-status and market-eligibility blockers. No provider HTTP, live
campaign, production DB write, test, staging, commit, or push occurred in this Phase100
PREPARE. Only the two phase-control documents changed.

Next: `CHATGPT_REVIEW_PHASE100_CAMPAIGN_ACTIVATION_AND_WIRING`

---

## POST_V0_8_DAILY_REPLAY_99 — IMPLEMENTATION HANDOFF

Formal Status: `READY_FOR_REVIEW`

State: `IMPLEMENTED_FOR_REVIEW`

Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`

Implementation: `NAR_PRE_C_FREEZE_PROVENANCE_AND_TIMING_OBSERVABILITY_FOUNDATION_IMPLEMENTED`

Design Review: `PHASE99_TIMING_OBSERVABILITY_DESIGN_REVIEW_PASS`

Measurement Contract Review: `PHASE99_MEASUREMENT_SESSION_CONTRACT_REVIEW_PASS`

Starting HEAD/tree: `7ec5afbe89d65803ba63d357a1d07e68c4c7e30a` /
`f4c53ab670bfd52fdc1f581e6baae63a7ae5d154`.

The accepted prior stop `PHASE99_IMPLEMENTATION_STOP_CONDITION_ACCEPTED` remains in
the record; `PHASE99_MEASUREMENT_SESSION_CONTRACT_REQUIRES_REVIEW = RESOLVED`.

Implemented four new production modules:

* `scripts/simulation/nar_operational_timing_observability.py` — frozen/slotted
  canonical configuration and session; closed PRE_C/POST_C stages, HTTP profiles,
  retry and serial concurrency regime; provider-scoped correlation and closed load
  context; independent attempt-start and terminal observations.
* `scripts/simulation/nar_operational_timing_observability_archive_migration.py` —
  isolated v1 exact-schema migration with immutable tables and restrictive foreign
  keys.
* `scripts/simulation/sqlite_nar_operational_timing_observability_archive.py` —
  connection-injected, explicit-schema-gated append-only publication and exact reload
  for configurations, sessions, attempts, terminals, and freeze receipts.
* `scripts/simulation/historical_input_snapshot_freeze_receipt.py` — controlled
  snapshot save/commit, exact reload/content validation, injected UTC sample, receipt
  archive publication and exact reload, then NAR cutoff qualification.

Added four corresponding focused tests and updated the two phase-control documents.
No existing production, migration, transport, snapshot repository, Phase96, or
prediction module was changed.

Configuration identity is SHA-256 of canonical NFC UTF-8 JSON for exact repository
`garimapo/KeibaOS`, lowercase 40-hex software commit, NAR/nar_official scope,
instrumentation version, enabled closed stages, exact profiles, `NO_RETRY` with zero
retries/backoff, and `CONTROLLED_SINGLE_WORKER_SERIAL_V1` with one workflow/HTTP
request and sequential RaceList acquisition. Reviewed current timeout profiles are
bootstrap/daily-target/official-response `10_000_000/10_000_000` microseconds and
market-odds raw `10_000_000/20_000_000`. Profile and stage order canonicalize
independently of caller order; enabled transport families require profiles. The
public identity is `nar-operational-timing-config-v1:<sha256>`.

The session binds that exact configuration, aware normalized UTC start/end, the
half-open attempt-start admission rule, and `FIXED_WALL_CLOCK_END`. It is
content-addressed as `nar-operational-timing-session-v1:<sha256>` and requires
`start < end`. Attempts beginning at start are admitted; attempts beginning at end
are excluded; attempts finishing after end remain admitted. Attempt starts are saved
independently of terminal success/failure/timeout, and the archive can list unresolved
starts. Elapsed duration is an explicit monotonic measurement in microseconds and is
not calculated by subtracting UTC samples. Closed correlation/load fields prevent
arbitrary metadata bags. No result, payout, ROI, or policy authorization fields exist.

The receipt clock is sampled only after `save_snapshot()` returns and the exact
snapshot is reloaded and verified. Existing repository reconstruction normalizes
provenance order; exact identity, source URL, race ID, cutoff, stored content SHA, and
recomputed content SHA are compared instead of relying on incidental tuple order.
Archive publication is restricted to controlled issuance and exact reload. A failure
after snapshot commit leaves the stored snapshot intact but provides no qualifying
receipt. The semantic is `COMMITTED_AND_EXACT_RELOAD_VERIFIED`; power-loss durability
is not claimed. An existing identical snapshot without an earlier receipt is stamped
at its present successful verification time. NAR qualification reloads the receipt
from the archive, binds the exact target/plan/policy identity, enforces Phase96
snapshot cutoff constraints, and qualifies only when `freeze_completed_at <= C`.

Required receipt archive persistence/reload overhead belongs to the PRE_C freeze
budget. Optional timing metric write failure must not change prediction contents;
live metric observers and timing aggregation remain future work. A session identity
is not pre-measurement activation authority. Neither observability records nor policy
identity activate a concrete Delta policy. The concrete offset, source status
semantics, official shadow eligibility, and ROI remain separately unresolved.

Focused tests: `29 passed`. Required snapshot/cutoff/resolver regressions: `108
passed, 95 subtests passed`. Full suite: `4576 passed, 2 skipped, 2846 subtests
passed`. Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Production DB writes: `0`;
temporary in-memory SQLite writes occurred only in focused and regression tests.

Next: `CHATGPT_REVIEW_PHASE99_IMPLEMENTATION`.

---

## Historical design record — POST_V0_8_DAILY_REPLAY_99 MEASUREMENT SESSION CONTRACT REVISION

**Status:** DRAFT_FOR_REVIEW

**Outcome:** READY_FOR_ARCHITECTURAL_REVIEW

**Audit:** NAR_PRE_C_FREEZE_AND_TIMING_OBSERVABILITY_DESIGN_COMPLETE
**Implementation:** NOT_STARTED_STOP_CONDITION_RESOLVED_IN_DESIGN

Accepted stop condition: `PHASE99_IMPLEMENTATION_STOP_CONDITION_ACCEPTED`.
The earlier halt, `PHASE99_MEASUREMENT_SESSION_CONTRACT_UNDERSPECIFIED`, was correct:
a content-addressed observability archive cannot safely invent the population whose
measurements will later inform Delta. This revision freezes the missing contract only:
`PHASE99_MEASUREMENT_SESSION_CONTRACT_REQUIRES_REVIEW`.

### Configuration and session are separate

`NAROperationalTimingMeasurementConfiguration` answers **what operational regime is
measured**. `NAROperationalTimingMeasurementSession` answers **when one fixed
campaign under that exact configuration admits attempts**. They have separate,
versioned, immutable content identities. Future aggregation may combine different
sessions only with an exact matching measurement-configuration identity and a later
reviewed aggregation rule.

Configuration v1 binds only: schema version; repository identity `garimapo/KeibaOS`;
an exact lowercase 40-hex Git commit SHA; closed NAR/nar_official scope;
instrumentation schema/version; a nonempty canonical enabled stage set; canonical
closed transport profiles; closed retry/backoff semantics; closed concurrency regime;
and sample-admission semantic version. It excludes campaign dates, observed latency,
results, payouts, ROI, profitability, prediction/replay outcomes, and executability.
Branch names are not software identity; a timing-relevant code change requires a new
commit and configuration identity.

Canonical configuration bytes are NFC UTF-8 JSON with `ensure_ascii=False`,
`allow_nan=False`, `sort_keys=True`, compact separators, and exact integers. SHA-256
produces `measurement_configuration_sha256` and only
`nar-operational-timing-config-v1:<sha256>`; callers cannot supply the SHA separately.

### Exact v1 transport and execution regime

Closed, unique, canonically ordered profiles use positive integer microseconds:

* `NAR_BOOTSTRAP_HTTP`: connect/read `10_000_000` / `10_000_000`;
* `NAR_DAILY_TARGET_HTTP`: connect/read `10_000_000` / `10_000_000`;
* `NAR_OFFICIAL_RESPONSE_HTTP`: connect/read `10_000_000` / `10_000_000`; and
* `NAR_MARKET_ODDS_RAW_HTTP`: connect/read `10_000_000` / `20_000_000`.

Each included transport family has exactly one profile. V1 supports only `NO_RETRY`,
which requires `max_retries=0` and `backoff_microseconds=0`; this describes the
current measured regime, not an eternal production retry decision.

The only initial concurrency regime is `CONTROLLED_SINGLE_WORKER_SERIAL_V1`: one
campaign worker, one active target workflow, one concurrent HTTP request, sequential
RaceList acquisition, and no cross-race/venue parallel scheduler. Stage coverage is a
nonempty canonical tuple of closed Phase99 stage values; duplicate or unknown values
are invalid. Serial measurement data never authorizes a parallel operational Delta;
parallel operation requires a new configuration and compatible campaign.

### Fixed-window session and denominator

Session v1 binds schema version, exact configuration identity, aware UTC-normalized
fixed-microsecond start/end timestamps,
`OPERATION_STARTED_IN_HALF_OPEN_SESSION_WINDOW`, and `FIXED_WALL_CLOCK_END`. It
requires `start < end`, has no open-ended form, and yields only
`nar-operational-timing-session-v1:<sha256>` from canonical JSON. Changing either
window bound or configuration changes the identity.

An attempt is admitted exactly when `start <= operation_started_at < end`, regardless
of success, explicit failure, timeout, or unsupported terminal disposition. An
attempt started inside the window remains admitted when it finishes later. The end is
chosen before sample evaluation: success-count, executable-race, stable-percentile,
no-timeout, and result/profitability-dependent completion rules are forbidden.

Every admitted attempt needs a stable identity and a recorded start boundary before or
at execution. Terminal observations bind to it. A started-in-window attempt without a
terminal observation after drain/reconciliation is incomplete evidence and cannot
silently disappear. Failures/timeouts remain in the denominator; success-only latency
statistics are supplementary. The session identity binds the admission window only,
not the later drain/finalization time.

### Provenance, compatibility, and revised foundation scope

`MEASUREMENT_SESSION_IDENTITY != PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY`.
Session SHA is semantic identity, not proof of prior declaration. A controlled
service-owned activation receipt is deferred: only a later exact archive write/reload
with `activated_at <= measurement_start_at` could prove a predeclared campaign, and
callers may not supply that time. Official predeclared campaign provenance therefore
remains unresolved.

The following remain frozen: `CAUSAL_FREEZE_PROVENANCE_BOUNDARY_REQUIRED`,
`DECLARED_CAPTURED_AT != INDEPENDENT_FREEZE_COMPLETION_PROVENANCE`,
`PHASE98_PRE_C_SNAPSHOT_FREEZE_REQUIRED`, `INFORMATION_FREEZE_DEADLINE = C`,
`POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY`, and
`OBSERVABILITY_RECORD != POLICY_ACTIVATION_AUTHORITY`.

After review, the narrow foundation may create:

* `scripts/simulation/nar_operational_timing_observability.py`;
* `scripts/simulation/nar_operational_timing_observability_archive_migration.py`;
* `scripts/simulation/sqlite_nar_operational_timing_observability_archive.py`;
* `scripts/simulation/historical_input_snapshot_freeze_receipt.py`;
* four corresponding focused tests, including migration/archive/freeze-receipt tests;
* and the two phase-control documents.

It must use the existing snapshot save/reload API through a controlled wrapper; it
must not modify generic snapshot semantics/repository behavior, live transports,
timeouts, retries, concurrency, scheduler, Phase96, live capture wiring, Delta policy,
or policy/session activation authority.

Required future tests cover canonical identities; commit/profile/stage/retry/concurrency
validation; the exact 10/10 and 10/20 profiles; fixed UTC windows and half-open
admission; failure/timeout denominator retention; late completion retention;
configuration-only compatibility; and, if later approved, service-owned activation
timing. No production/test file changed, and no Provider HTTP, Phase44, GET, DB write,
test, stage, commit, or push occurred in this revision.

---

## Historical design record — POST_V0_8_DAILY_REPLAY_99 NAR PRE-C FREEZE AND TIMING OBSERVABILITY

**Formal Status:** DRAFT_FOR_REVIEW

**State:** DRAFT_FOR_REVIEW

**Outcome:** READY_FOR_ARCHITECTURAL_REVIEW

**Audit:** NAR_PRE_C_FREEZE_AND_TIMING_OBSERVABILITY_DESIGN_COMPLETE

**Authorization:** NONE_REQUIRED_AUDIT_ONLY

### Phase98 reconciliation and finding

`PHASE98_OPERATIONAL_TIMING_ARCHITECTURE_REVIEW_PASS` is frozen. The Phase98 section below is retained as historical design record. `OPERATIONAL_TIMING_INSTRUMENTATION_REQUIRED`, `PHASE98_PRE_C_SNAPSHOT_FREEZE_REQUIRED`, and `INFORMATION_FREEZE_DEADLINE = C` remain current. Phase96 is unchanged: the selected snapshot must satisfy `identity.captured_at <= C` and `information_cutoff <= C`; post-C assembly or backdating remains prohibited. `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remains unresolved.

Primary Phase99 finding: `CAUSAL_FREEZE_PROVENANCE_BOUNDARY_REQUIRED`. Performance telemetry answers duration only. It cannot prove which exact immutable prediction input existed by C. A snapshot's declared `identity.captured_at` is not independent persistence-completion evidence. Freeze: `DECLARED_CAPTURED_AT != INDEPENDENT_FREEZE_COMPLETION_PROVENANCE` unless a reviewed persistence boundary proves the relationship.

### Observability and freeze-provenance contract

The future design separates three immutable, content-addressed records:

* `NAROperationalTimingObservation`: versioned closed stage/scope, canonical correlation, UTC start/finish, monotonic elapsed duration, closed outcome classification, safe load context, and artifact identity/SHA when created.
* `NARSnapshotFreezeProvenance`: NAR race/provider identity, dataset ID, exact snapshot identity/content SHA, C, policy identity, plan SHA where applicable, persistence boundary, freeze completion time, exact-reload verification, and record SHA.
* `NAROperationalMeasurementSession`: versioned campaign configuration: software commit, provider scope, timeout/retry and concurrency configuration, instrumentation version, start, intended duration/sample rule, and SHA.

All use canonical NFC UTF-8 JSON with sorted keys, compact separators, `ensure_ascii=False`, `allow_nan=False`, fixed-microsecond UTC datetimes, and SHA-256. No arbitrary metadata, results, payouts, ROI, or future outcome information is admitted.

The narrow supported freeze boundary is a successful SQLite commit followed by exact repository reload. `freeze_completed_at` is an injected UTC sample immediately after `commit()` returns; it is a conservative upper bound, never copied from `captured_at`, evidence time, C, or request start. Reload must reconstruct the same snapshot identity and content SHA. This proves the existing SQLite commit contract, not an unproven stronger media-durability property.

Current `SQLiteHistoricalInputSnapshotRepository.save_snapshot()` owns the transaction but returns no receipt. Future work must add a repository-owned immutable receipt, emitted only after commit. A new provenance record requires `NEW_COMMITTED` plus exact reload. `EXISTING_IDENTICAL` cannot be renamed as a new historic freeze; without prior matching provenance its state is `SNAPSHOT_FREEZE_PROVENANCE_UNAVAILABLE`. Qualification requires exact plan/policy/target binding, Phase96 snapshot validity, receipt/reload agreement, and `freeze_completed_at <= C`; a later completion is `SNAPSHOT_FREEZE_COMPLETED_AFTER_PREDICTION_CUTOFF`.

### Timing, correlation, and current boundaries

Causal events use injected timezone-aware UTC clocks; elapsed durations use injected monotonic timers. Wall-clock subtraction is prohibited for latency distributions. The closed pre-C taxonomy is scheduler dispatch; bootstrap-home, monthly-root, locator-script, monthly-schedule, RaceList, and official-response acquisition; raw validation/persistence; parsing; normalization; source-record construction; provider identity binding; snapshot construction/persistence; and exact reload confirmation. Post-C taxonomy is snapshot adapter, prediction pipeline, allocation, bet-plan construction/persistence, and shadow artifact publication.

Current daily acquisition exposes synchronous bootstrap → monthly → normalization → sequential RaceList composition; its injectable transport/archive protocols can be decorated without changing transport behavior. Official-response and odds boundaries also take injectable collaborators. Fine-grained raw-validation/persistence, parser/source-record, and internal prediction/allocation spans are not all independently hookable today; public grouped boundaries are snapshot building, Phase88 identity binding, exact snapshot reload, snapshot adapter, and historical bet-plan execution. No current timeout, retry, concurrency, target-discovery, model, or Phase96 contract change is proposed.

Correlation binds the measurement session plus applicable target-set SHA, plan SHA, policy identity, and NAR race identity; a process-local ID alone is insufficient. `OBSERVABILITY_CORRELATION_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY` and `OBSERVABILITY_RECORD != POLICY_ACTIVATION_AUTHORITY` are frozen.

### Archive, failure, measurement, and Δ-review decisions

Recommended storage is a separate connection-injected append-only SQLite observability archive, using its own exact schema gate and content-addressed rows. It stores sessions, timing observations, and freeze provenance without mutating Phase96 snapshot tables/artifacts or `resolution_outcomes_json`. Snapshot commit happens first; provenance is then independently recorded and verified. A failed required provenance append leaves prediction behavior unchanged but blocks official shadow/ROI qualification. Optional timing-write failure likewise must not alter inputs, C, or output, but makes that metric sample unusable. Failures/timeouts remain in every timing denominator.

The read-only aggregation layer groups only by measurement configuration/session, stage, request/source type, venue where applicable, and measured concurrency regime. It reports count, median, p90/p95/p99 where statistically supported, maximum, timeout/failure rate, and never filters unfavorable samples. Incompatible timeout/retry/concurrency regimes have distinct measurement identities and cannot be pooled.

Later Δ review requires exact session configuration, sample interval, race/venue coverage, full failure denominator, pre-C distributions, concurrency/load coverage, clock-skew evidence, and safety-margin rule. It must not use outcomes, payout, ROI, odds, status, executability, or favorable-latency selection. Δ approval and policy activation remain separate immutable authorities.

Phase99 does not resolve `HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS`, `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`, or `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`. Timing campaigns may proceed; official strict shadow eligibility and ROI remain separately blocked.

Likely future paths, pending approval: create `scripts/simulation/nar_operational_timing_observability.py`, `scripts/simulation/nar_operational_timing_observability_archive_migration.py`, `scripts/simulation/sqlite_nar_operational_timing_observability_archive.py`, `tests/test_nar_operational_timing_observability.py`, and `tests/test_sqlite_nar_operational_timing_observability_archive.py`; modify `scripts/simulation/historical_input_snapshots.py`, `scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py`, `tests/test_historical_input_snapshots.py`, and `tests/test_sqlite_historical_input_snapshot_repository.py`. Decorator composition should cover acquisition and post-C public boundaries without changing their semantics.

Required eventual tests cover canonical identities, closed taxonomy, UTC/monotonic independence, no outcome/ROI inputs, receipt/reload binding, C-bound qualification, anti-forgery from captured time, optional-vs-required write failure, timeout/retry/after-C behavior, correlation separation, configuration-compatible aggregation, immutable artifacts, and concurrent-race isolation.

Explicit non-goals: Δ selection, live HTTP/sampling, scheduler/retry/concurrency/timeout changes, snapshot semantic changes/backdating, policy activation, status/market semantics, ROI, or historical rescue.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. DB writes: `0`. Tests: not run. Production code, tests, fixtures, staging, commit, and push: none. Modified paths: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`; staged/untracked: empty.

Recommended formal disposition: remain `DRAFT_FOR_REVIEW`; no implementation is authorized. Next classification is `CAUSAL_FREEZE_PROVENANCE_BOUNDARY_REQUIRED`, then `OPERATIONAL_TIMING_INSTRUMENTATION_REQUIRED` after review.

Next: `CHATGPT_REVIEW_PHASE99_TIMING_OBSERVABILITY`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_98 — NAR PROSPECTIVE SHADOW OPERATIONAL TIMING

**Formal Status:** DRAFT_FOR_REVIEW

**State:** DRAFT_FOR_REVIEW

**Outcome:** READY_FOR_ARCHITECTURAL_REVIEW

**Audit:** NAR_PROSPECTIVE_OPERATIONAL_TIMING_ARCHITECTURE_AUDIT_COMPLETE

**Authorization:** NONE_REQUIRED_AUDIT_ONLY

### Phase97 reconciliation

`PHASE97_IMPLEMENTATION_REMOTE_VERIFICATION_PASS` is frozen. `POST_V0_8_DAILY_REPLAY_97 = FORMALLY_COMPLETE` and `NAR_FIXED_OFFSET_PREDICTION_CUTOFF_POLICY_AND_PLAN_PRODUCER = FORMALLY_INTEGRATED`.

Phase97 supplied deterministic policy semantics and plan production. It did not select an operational Δ or prove policy activation time. `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`, `POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY`, and `PREDICTION_CUTOFF_POLICY_PROVENANCE_UNAVAILABLE` remain current.

### Primary finding and deadline model

Primary classification: `OPERATIONAL_TIMING_INSTRUMENTATION_REQUIRED`. The repository has bounded requests but no independently auditable latency distributions, concurrency envelope, retry budget, scheduler-jitter evidence, or activation-period timing data. A concrete Δ would be arbitrary.

The revised architecture is `PHASE98_PRE_C_SNAPSHOT_FREEZE_REQUIRED`. Phase96 selects only snapshots with `identity.captured_at <= C` and `information_cutoff <= C`; `HistoricalInputSnapshot` itself enforces `captured_at <= information_cutoff <= scheduled_start_at`, and all admitted evidence is observed/available by `captured_at`. Thus `INFORMATION_FREEZE_DEADLINE = C`: the complete immutable `HistoricalInputSnapshot`, including all prediction material, must be built and persisted by C. No timestamp may be backdated and no after-C evidence may repair the snapshot.

`OPERATIONAL_COMPLETION_DEADLINE` is separate and remains for later design. After the exact snapshot freezes by C, pure prediction, stake-plan construction, and shadow-artifact publication may occur after C only from that snapshot and pre-approved deterministic strategy/configuration, with no new prediction-time provider input, and before the eventual action/shadow deadline. A future architecture that assembles a snapshot after C from another pre-C freeze artifact would need separately reviewed provenance and likely a changed meaning or use of `identity.captured_at`; Phase98 preserves Phase96 unchanged and makes no such recommendation.

### Pre-C dependency graph

```text
schedule/target discovery → canonical target set → approved policy/plan
→ pre-C raw source captures → validation, parsing, normalization
→ source-record production and identity binding → complete HistoricalInputSnapshot
→ immutable snapshot persistence/freeze by C
→ post-C prediction and stake-plan generation from that exact snapshot
→ shadow artifact publication
→ later result/payout/settlement comparison
```

The `PRE_C_FREEZE_CRITICAL_PATH` includes dispatch/jitter, request sequencing, provider throttle/retry/timeout budget, raw validation and append-only persistence, parsing, normalization, source-record derivation, identity binding, complete snapshot construction/persistence, contention/concurrency, and clock-skew allowance. All must finish by C. `POST_C_COMPUTE_CRITICAL_PATH` includes snapshot adaptation, model inference, stake allocation, bet-plan construction, and artifact publication; it is governed by the later completion deadline, not automatically by Δ. Settlement is separate and post-race.

### Existing timing facts, concurrency, retry, and clock contracts

`NARDailyTargetLiveAcquisitionApplication.acquire` in `scripts/simulation/nar_daily_target_live_acquisition.py` captures bootstrap resources, the monthly schedule, then venue RaceList pages sequentially. `normalize_nar_race_list` in `scripts/simulation/nar_historical_daily_target_source.py` converts each JST scheduled start to UTC. The day target domain represents multiple venues/races but no current component owns worker limits, concurrent meeting handling, provider throttling, or race priority. Those conditions need prospective load tests before Δ selection.

Verified implementation facts: historical daily-target transport, bootstrap transport, and official-response live capture each use connect/read 10s/10s with `max_retries=0`; market-odds raw acquisition uses 10s/20s with `max_retries=0`. These are transport facts, not an approved future retry policy. A future contract must predeclare attempts, timeouts, backoff, and total deadline budget. A request started by C but fully observed after C is not eligible for that snapshot: `requested_at <= C` is insufficient. Late responses may be diagnostic only if a later archive contract permits; they must not enter the C-frozen snapshot, move C, or cause an older/newer response substitution merely to make a target executable.

Evidence timestamps require timezone-aware UTC-compatible wall-clock values. Future duration telemetry must use an injected monotonic timer, not subtraction of independently sampled wall clocks that could be affected by clock adjustments. Observability must not alter causal timestamps or prediction behavior. Clock synchronization and a skew bound remain activation prerequisites.

### Measurement and Δ selection methodology

Collect prospective, outcome-independent distributions separately for `PRE_C_FREEZE_CRITICAL_PATH` (dispatch-to-request, connect/read, validation/persistence, parsing, normalization, source records, identity binding, snapshot build/persist); `POST_C_COMPUTE_CRITICAL_PATH` (snapshot adapter, model, stake, bet plan, artifact persistence); and `SHARED_ENVIRONMENT` (startup, SQLite/filesystem contention, concurrent venues, throttle, worker availability, clock skew). Record count, median, p90, p95, p99 where sample size permits, maximum, and failure/timeout rate. Group only by provider/source, request type, venue, concurrent-meeting count, and operational time window where justified.

After independently reviewed normal-and-stressed prospective measurement, select Δ only from the full pre-C freeze envelope, reviewed safety margin, and clock-skew allowance. Model/bet-plan duration is excluded unless a later action contract requires it before C. Results, payout, ROI, odds, later status, executability, and evidence convenience are forbidden inputs. A Δ change creates a new Phase97 policy identity and distinct activation/analytical period; periods must not be silently merged.

### Activation and shadow-operation handoff

Future activation provenance must bind exact policy identity/canonical SHA, provider scope, activation timestamp, effective-from time, optional effective-until time, reason/audit identity, and its own immutable content SHA. It must precede covered outcomes; a caller-provided authorization flag cannot establish that fact.

The planned sequence is: design passive timing instrumentation; collect prospective measurements; review them; freeze Δ; create the policy instance and activation provenance; derive cutoff plans before races; run shadow capture/prediction; preserve raw prediction-time evidence; compare to outcomes only later.

The source-semantic blockers do not all have the same operational effect. Passive timing instrumentation is not blocked. Measuring current acquisition/parsing/snapshot construction timing may proceed without official-admissibility claims, and structurally constructing a current `HistoricalInputSnapshot` is not categorically blocked solely by the Phase94/95 status-authority blockers. In contrast, complete authoritative entry status remains blocked by `HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS` and `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`; market/positive-market claims remain blocked by `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`; official strict prospective shadow eligibility and official ROI evaluation remain blocked pending all required semantic authorities. A snapshot itself never implies status or market authority.

Candidate future paths, pending an approved instrumentation design: new `scripts/simulation/nar_operational_timing_observability.py` and test; `nar_daily_target_live_acquisition.py`, `nar_historical_daily_target_live_capture.py`, `nar_historical_daily_target_bootstrap_live_capture.py`, `nar_official_response_live_capture.py`; optional odds timing in `nar_market_odds_raw_acquisition.py`; pre-C input/snapshot boundaries `nar_historical_input_source.py` and `historical_input_snapshot_builder.py`; post-C compute at `historical_prediction_bet_plan_execution.py`; artifact persistence at `persisted_bet_plan_service.py`; and later scheduler/activation modules. Required tests cover injected monotonic measurement with UTC audit timestamps, snapshot freeze by exact C, late-response isolation, timeout/retry behavior, concurrency isolation, fixed policy identity, telemetry noninterference, and no outcome dependencies.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. DB writes: `0`. Production code, tests, fixtures, staging, commit, and push: none. Modified paths: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`; staged and untracked sets are empty.

Recommended formal disposition: remain `DRAFT_FOR_REVIEW`; no implementation is authorized. Recommended next classification: `OPERATIONAL_TIMING_INSTRUMENTATION_REQUIRED`.

Next: `CHATGPT_REVIEW_PHASE98_OPERATIONAL_TIMING`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_97 — FIXED NAR PREDICTION-CUTOFF POLICY IMPLEMENTATION

### Implementation and validation

The new immutable/slotted fixed-offset policy content-addresses the exact NAR/nar_official rule, positive exact integer `offset_microseconds`, closed scheduled-start basis, and versioned boundary semantics. Canonical UTF-8 JSON uses sorted keys, compact separators, `ensure_ascii=False`, and `allow_nan=False`; SHA-256 derives the public policy identity. The pure keyword-only producer computes each canonical target's `C = scheduled_start_at - offset`, derives the plan's policy identity from that policy, and returns the existing validated Phase96 plan. Arithmetic overflow and absent starts fail closed. No concrete Δ or operational maximum is frozen.

Focused policy test: `19 passed`. Regressions: Phase96 cutoff plan `4 passed`; eligibility `8 passed, 5 subtests`; SQLite daily resolver `27 passed, 38 subtests`; daily orchestrator `23 passed, 11 subtests`. Full suite: `4,547 passed, 2 skipped, 2,846 subtests passed`. Production changes are exactly the new policy module; the new focused test and two phase-control documents are the other changes. Phase96 production modules, migrations, fixtures, and database schemas remain unchanged. Policy module network, filesystem, current-clock, and DB activity: `0`; Provider HTTP / Phase44 / GET: `0 / 0 / 0`.

`POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY`. A policy SHA or newly generated deterministic retrospective plan does not prove pre-outcome selection; strict historical use without separately reviewed provenance remains `PREDICTION_CUTOFF_POLICY_PROVENANCE_UNAVAILABLE`. `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remains open. Phase41 and Phase94/95 source-semantic blockers remain unresolved. Phase97 is implemented for review, not formally complete.

Final Git commit/push identity and worktree state are reported in the execution handoff after integration; this document makes no claim of remote independent implementation review.

Next: `CHATGPT_REVIEW_PHASE97_IMPLEMENTATION`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_97 — POLICY DESIGN AUDIT

**Formal Status:** DRAFT_FOR_REVIEW

**State:** DRAFT_FOR_REVIEW

**Outcome:** READY_FOR_ARCHITECTURAL_REVIEW

**Audit:** OUTCOME_INDEPENDENT_PREDICTION_CUTOFF_POLICY_DESIGN_COMPLETE

**Authorization:** NONE_REQUIRED_AUDIT_ONLY

### Phase96 reconciliation

`PHASE96_IMPLEMENTATION_REMOTE_VERIFICATION_PASS` is frozen. `POST_V0_8_DAILY_REPLAY_96 = FORMALLY_COMPLETE`, `NAR_PREDICTION_CUTOFF_PLAN_AND_V017_PROVENANCE = FORMALLY_INTEGRATED`, and `PHASE93_CUTOFF_CONTRACT_REQUIRES_HARDENING = RESOLVED_BY_PHASE96`. The retained Phase96 implementation narrative below is historical. Its pre-implementation statement that Phase93 required hardening is no longer current.

### Finding and recommended policy family

Primary finding: `OUTCOME_INDEPENDENT_FIXED_OFFSET_POLICY_REQUIRES_OPERATIONAL_PARAMETER_APPROVAL`. Architecture verdict: a pure fixed-offset policy/producer is implementable, but policy authorization for strict historical use remains future-gated. The recommended policy family is one immutable fixed offset for all canonical NAR targets: `C = scheduled_start_at - Δ`. It is the smallest deterministic policy compatible with the completed Phase96 plan domain.

Concrete blocker: `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`. No concrete initial `Δ` can safely be frozen now. The repository has no independently reviewed, pre-outcome operational measurements for provider latency, complete deterministic acquisition, prediction/bet-plan duration, concurrency under overlapping races, provider throttling/retry behavior, clock synchronization, or required delivery margin. Selecting a number now would be an unreviewed operational policy. A later timing audit must select a positive fixed duration before prospective shadow operation is approved.

Evidence-adaptive/latest-executable, withdrawal-adjusted, result/ROI-adjusted, or per-race discretionary policies are rejected: they introduce outcome or evidence-availability selection bias. Variable policy families also lack reviewed inputs in the present repository.

### Fixed-offset policy semantics, identity, and offset representation

Future `NARHistoricalReplayPredictionCutoffPolicy` is a frozen/slotted semantic specification, content-addressed by canonical UTF-8 NFC JSON (`ensure_ascii=False`, `allow_nan=False`, sorted keys, compact separators). Exact material: `schema_version`; `organization=NAR`; `source_system=nar_official`; closed `policy_kind=FIXED_OFFSET_BEFORE_SCHEDULED_START`; exact `offset_microseconds`; closed `scheduled_start_basis=DAILY_HISTORICAL_REPLAY_TARGET_SCHEDULED_START_AT_V1`; and versioned `boundary_semantics=C_EQUALS_SCHEDULED_START_AT_MINUS_OFFSET`. Its public identity is `nar-prediction-cutoff-policy-v1:<SHA256(canonical bytes)>`. Results, payouts, odds, evidence/status availability, ROI, database state, current clock, run IDs, and target-specific overrides are excluded.

`offset_microseconds` accepts only exact built-in `int`, rejects `bool`, and is strictly positive. Float, `Decimal`, free-form duration strings, per-target offsets, arbitrary maxima, and a concrete Δ are out of scope. Any material policy change changes the identity; the integer representation is timezone-independent.

Frozen invariant: `POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY`. The identity proves what content-addressed rule exists, not when it was approved. A SHA may be computed after results and cannot prove pre-outcome authorization.

The pure future producer `build_nar_historical_replay_prediction_cutoff_plan(*, target_set, policy)` accepts only the exact Phase96 target set and exact policy, retains canonical order, derives `C = target.scheduled_start_at - timedelta(microseconds=policy.offset_microseconds)`, and emits the existing Phase96 plan. The plan's `cutoff_policy_identity` comes exclusively from the policy object; no caller supplies a detached identity plus offset. Missing start, invalid policy/provider, target-set contradiction, and coverage/order violation fail closed. It performs no filesystem, network, clock, database, evidence, snapshot, status, odds, result, payout, or settlement I/O and has no target override/fallback. Same target set plus same policy yields the same plan bytes/SHA.

### Authorization provenance and historical admissibility

The Phase97 object is a deterministic semantic policy, not historical admissibility authority. A valid newly derived plan is only `DETERMINISTIC_RETROSPECTIVE_PLAN` until independently auditable pre-outcome policy authorization/activation provenance, or equivalent previously frozen pre-outcome plan provenance, is supplied. Otherwise strict use remains `PREDICTION_CUTOFF_POLICY_PROVENANCE_UNAVAILABLE`. Valid SHA, fixed offset, eventual executability, and ROI cannot retrospectively authorize it.

Policy and plan must never be selected, adjusted, or rescued according to evidence convenience, later withdrawal/status knowledge, odds, results, payouts, profitability, replay success, or executable status. This policy-provenance boundary remains future-gated; Phase97 does not falsely claim that the existing historical replay path is fully anti-hindsight for policy selection.

For prospective shadow operation, approve Δ first, obtain target schedule, generate and freeze the exact plan before resolver/acquisition work, then let a future scheduler acquire/predict to the precomputed C before outcomes arrive. That later scheduler must retain activation provenance. Phase97 neither implements it nor acquires live data.

### Orchestrator decision

Architecture **A** is the narrowest safe implementation: add only the policy/producer. Phase96 `run_nar_daily_replay(...)` already accepts an exact target-set-bound plan and passes it through eligibility, resolution, audit, persistence, and aggregation. Adding a policy object to that API would not establish pre-outcome authorization and would broaden a finished contract. A separate reviewed provenance/shadow phase must enforce activation before a plan may support official strict historical/ROI use.

Phase94/95 remain blocked by source semantics: `HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS` and `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`. Phase41 remains `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`; market eligibility, positive market eligibility, odds authority, whole-meeting cancellation, and ROI evaluation remain out of scope.

### Expected future scope and tests

Expected implementation paths are exactly: create `scripts/simulation/nar_historical_replay_prediction_cutoff_policy.py` and `tests/test_nar_historical_replay_prediction_cutoff_policy.py`; modify `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. Existing Phase96 resolver, eligibility, orchestration, persistence, aggregation, target discovery, migrations, and schema require no modification because the producer emits their existing validated plan type and does not integrate authorization provenance.

Required matrix: deterministic canonical bytes/SHA/public identity; timezone-independent offset representation; int-only offset with bool/zero/negative/float/free-form rejection; material offset change; same target set/policy equal plan; different offset different plan; exact arithmetic; target order/missing-start failure; no network/DB/clock/snapshot/status/odds/result/payout/settlement access; no target override; derived plan identity equality; no contradictory detached identity input; no producer authorization claim; deterministic scheduler-facing consumption.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. DB writes: `0`. Production code, tests, fixtures, database contents, staging, commit, and push: none. Modified paths are only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`; staged and untracked sets are empty.

Recommended formal Phase97 disposition: remain `DRAFT_FOR_REVIEW` pending independent architectural review. Any later approval may authorize only the policy semantic producer; neither a policy SHA nor a retrospective plan is pre-outcome authorization, and Δ remains unfrozen pending the operational timing audit.

Next: `CHATGPT_REVIEW_PHASE97_PREDICTION_CUTOFF_POLICY`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_96 — NAR PREDICTION-CUTOFF PLAN IMPLEMENTATION

**Formal Status:** READY_FOR_REVIEW

**State:** IMPLEMENTED_FOR_REVIEW

**Outcome:** READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

**Audit:** PREDICTION_CUTOFF_COHERENCE_AUDIT_COMPLETE

**Implementation:** NAR_PREDICTION_CUTOFF_PLAN_AND_V017_PROVENANCE_IMPLEMENTED

**Design Review:** PHASE96_PREDICTION_CUTOFF_DESIGN_REVIEW_PASS

**Authorization:** NONE_REQUIRED_NO_NETWORK_IMPLEMENTATION

The reviewed contract is implemented in a separate immutable cutoff-plan domain. Its exact target-set binding, canonical per-target C values, policy identity, and SHA-256 feed Phase93 eligibility, SQLite prediction selection, the retained orchestration result, audit identity, atomic v016-parent/v017-companion publication, and strict aggregation. Capture-time-only status does not automatically prove validity through a later C. The approved current target remains blocked; no issuer or T-minus-N policy was created.

Focused results: plan 4 passed; Phase93 8 passed/5 subtests; resolver 27 passed/38 subtests; orchestrator 23 passed/11 subtests; persistence 12 passed/12 subtests; SQLite result repository 26 passed/19 subtests; aggregation 22 passed; historical migration 11 passed; simulation migrations 22 passed/10 subtests. Full suite: 4,528 passed, 2 skipped, 2,846 subtests passed. The two skips are pre-existing platform-conditional cases. Three extra regression-test files change only v017 registry expectations: official-capture migration, simulation-bet-plan migration, and persisted-simulation application.

`PHASE95_PROSPECTIVE_STATUS_CAPTURE_REVIEW_PASS` is recorded with `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`. The current target remains blocked; this phase addresses temporal coherence only and does not alter source semantics.

### Reviewed pre-implementation temporal contract

`scheduled_start_at` is a race-start upper bound, not a prediction observation time. `HistoricalInputSnapshot` already has its own `information_cutoff` and enforces `captured_at <= information_cutoff <= scheduled_start_at`, with all prediction evidence observed/available by that cutoff. However, the SQLite NAR resolver selects the latest snapshot whose capture and own cutoff are merely before `scheduled_start_at`, and invokes its snapshot source with the scheduled start as bound. Phase93 likewise accepts status authority whenever `available_at` and `observed_at` are merely before the scheduled start.

The resulting frozen model is “everything causally known before start.” It is deterministic for a fixed dataset, but not a reproducible single decision at C: a status from T-5 and snapshot inputs from T-1 may be combined. T-5 status cannot be asserted to remain true at T-1 or at start without a source-proved validity interval. Settlement evidence remains correctly separate under `settlement_information_cutoff`.

### Final architectural contract

Historical pre-Phase96 finding: the former “latest causal before scheduled start” model combined potentially different information moments and was not strict single-cutoff replay. Its architecture verdict was `PREDICTION_CUTOFF_MODEL_REQUIRES_EXPLICIT_CUTOFF`, with `PHASE93_CUTOFF_CONTRACT_REQUIRES_HARDENING`; Phase96 subsequently resolved that requirement.

Target-set identity stays provider denominator/acquisition evidence and does not carry C. The separate `NARHistoricalReplayPredictionCutoffPlan` content-addresses schema/version, target-set SHA, closed policy identity, exact canonical target coverage, and target-set-ordered `(organization, source_system, external_race_id, C)` decisions. Its UTF-8 JSON is canonical (`ensure_ascii=False`, `allow_nan=False`, sorted keys, compact separators) and serializes UTC datetimes with fixed microseconds; SHA-256 of those bytes is the plan identity. Missing/extra/duplicate/out-of-order targets, target-set mismatch, absent start/C, and C after start fail closed. Same target set plus different C necessarily produces a different plan SHA. Phase96 chooses no timing policy; Phase97 must design its outcome-independent producer.

Resolver selection uses exact C for snapshot capture and information-cutoff bounds and repository lookup; scheduled start remains identity validation only. Settlement stays under its separate settlement cutoff. Phase93 must compare authority availability/observation against C. `STATUS_OBSERVED_AT_CAPTURE_TIME` does not imply `STATUS_VALID_THROUGH_PREDICTION_CUTOFF`: a T-5 observation cannot establish a T-1 state. Only exact capture-time replay or separately reviewed immutable validity-through-C proof can qualify; no issuer/provider semantic is invented here, and Phase94/95 blockers remain frozen.

`run_nar_daily_replay` must take and retain the exact plan. It validates exact binding to the acquisition target set before eligibility and resolution. The orchestration audit binds at least the content-addressing plan SHA, so same target set and snapshots but different C have different audit SHA. `resolution_outcomes_json` remains outcomes-only.

v017 must be a companion, not a v016 rewrite: a one-to-one append-only child keyed by parent `persisted_content_sha256`, with restrict FK, canonical `prediction_cutoff_plan_json`, and non-unique `prediction_cutoff_plan_sha256`; UPDATE/DELETE are rejected. Repository validation reproduces plan SHA and requires plan/parent target-set SHA agreement. The existing repository's exact-8-through-16 migration guard must become exact-through-v017 while independently preserving `require_v016_schema_contract` and verifying v017. Parent and companion publish atomically, roll back together, are idempotent only when identical, reject conflicts, and exact-reload together. Legacy v016-only rows remain immutable, have `PREDICTION_CUTOFF_PROVENANCE_UNAVAILABLE`, and cannot participate in strict consumers or aggregation.

Strict aggregation requires every selected result's exact v017 companion and traces parent → companion → plan SHA → per-target C. Compatibility adds `cutoff_policy_identity`, not plan SHA: different daily plan SHAs under the same policy may aggregate; different policies may not.

Expected production scope: new cutoff-plan module and v017 migration; resolver, Phase93 eligibility, orchestrator, result persistence, aggregation, existing result repository, and migration runner. Expected tests: new cutoff-plan test plus eligibility, resolver, orchestrator, persistence, aggregation, SQLite repository, and migration tests. No new companion repository is needed because the existing repository must own the one transaction. Target discovery/denominator semantics, snapshot schema, and settlement semantics stay out of scope.

The eventual matrix explicitly covers same-target/different-C plan SHA and same-snapshot/different-C audit SHA; canonical ordering and timezone-equivalent times; missing/extra/duplicate coverage, missing start, and C-after-start rejection; C-bound resolver lookup/capture/cutoff and Phase93 non-promotion; settlement independence; untouched v016 schema/table/triggers; idempotent runner and repository acceptance of an exact v017 database; malformed v017 and companion corruption/immutability/parent mismatch; atomic rollback, idempotent publication, and conflict rejection; strict legacy aggregation rejection; same-policy/different-plan acceptance; mixed-policy rejection; and full regression.

Phase41 remains unresolved: `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`. Prospective source semantics remain `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`; market eligibility, positive-market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Production DB writes: `0`; test-only in-memory/temporary SQLite writes exercised migration and publication. No fixture, provider-denominator, snapshot-domain, settlement-domain, or acquisition change. Final commit/push identity and worktree state are authoritative in the execution handoff; this report does not claim remote independent verification.

Historical next action at that time: `CHATGPT_REVIEW_PHASE96_IMPLEMENTATION`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_95 — PROSPECTIVE NAR ENTRY-STATUS AUTHORITY CAPTURE CONTRACT

**Formal Status:** DRAFT_FOR_REVIEW

**State:** DRAFT_FOR_REVIEW

**Outcome:** READY_FOR_ARCHITECTURAL_REVIEW

**Audit:** PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_AUDIT_COMPLETE

**Authorization:** NONE_REQUIRED_AUDIT_ONLY

`PHASE94_AUTHORITY_ISSUANCE_REVIEW_PASS` is recorded with `HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS`. Phase94 has no authorized production implementation. This prospective design does not repair `NAR / 21 / 2025-01-01 / 6`, which remains `HISTORICAL_REPLAY_BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`.

### Proposed identity and status boundaries

The provider entry-universe identity must be a versioned SHA-256 over canonical UTF-8 JSON containing provider scope, external race ID, and the horse-number-ascending tuple `(external_entry_id, external_horse_id, horse_no)`. It excludes names, internal race-entry IDs, status, odds, and market fields. Phase88 supplies target-specific identity material but its extractor is hard-coded to the Phase83 fixture and `1..14`; it cannot be reused unchanged for prospective targets. A future generic extractor requires an independent reviewed contract and must remain identity-only.

Observed status is a separate immutable, capture-time-bounded universe. It must preserve exact observed dispositions and capture identities, and must never convert blank status to `ACTIVE`. Market eligibility is a third separate domain and remains unsupported.

### Official-source findings

DebaTable has a per-entry `td.info` current field, but the reviewed contract recognizes a positive `出走取消` marker only; blank means only no explicit withdrawal evidence. RaceList `changeInfo` identifies exceptional changes by race/horse, not a complete status row for every entry. RaceMarkTable is a post-race result/payout source, and HorseMarkInfo has no reviewed race-scoped complete-status contract. No known official source establishes that blank/absence means normal/active, lists all cancellation forms with closed semantics, or proves a complete positive status disposition across the race. Whole-race/meeting cancellation is separate and unsupported.

### Capture timing and raw boundary

Every prospective observation must be append-only and retain canonical request/source identity, target identity, exact bytes, SHA-256, requested/observed/stored timestamps, HTTP status, charset/encoding, and received metadata. Existing `NAROfficialResponseCapture` already satisfies this raw-byte boundary for DebaTable, RaceMarkTable, and HorseMarkInfo; its closed URL set excludes RaceList, so a future approved design must extend that boundary or define a separate status-capture boundary. HTTP `Date` and `Last-Modified` are not provider-publication proof.

Capture acceptance must be tied to an explicit prediction information cutoff `C <= scheduled_start_at`, using actual `observed_at`. A T-5 capture proves only what was known at T-5; a T-1 withdrawal does not make it final pre-start status. Repeated immutable captures are appropriate operational evidence, but only an independently reviewed terminal/complete provider publication could support a final-pre-start claim. No such source is known.

### Decision

Primary classification: `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`.

The raw capture contract is defined, but the source cannot currently establish `COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE`. No authority may be issued and no implementation scope is proposed. The minimum next step is a separately reviewed official-source semantics discovery effort for a complete per-entry pre-start status roster or provider-defined complete disposition feed, including normal/non-withdrawn and whole-race/meeting semantics.

Phase41 remains `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`. A future complete status capture would be only a prerequisite; independent market-eligibility and market-odds authority would still be required.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. DB writes: `0`. Production code, tests, fixtures, capture archives, replay, staging, commit, and push: none. Modified paths: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md` only; staged and untracked sets are empty.

Next: `CHATGPT_REVIEW_PHASE95_PROSPECTIVE_STATUS_CAPTURE`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_94 — NAR HISTORICAL ENTRY-STATUS AUTHORITY ISSUANCE BOUNDARY

**Formal Status:** DRAFT_FOR_REVIEW

**State:** DRAFT_FOR_REVIEW

**Outcome:** READY_FOR_ARCHITECTURAL_REVIEW

**Audit:** HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUANCE_AUDIT_COMPLETE

**Authorization:** NONE_REQUIRED_AUDIT_ONLY

### Phase93 reconciliation

`PHASE93_IMPLEMENTATION_REMOTE_VERIFICATION_PASS` is recorded. `POST_V0_8_DAILY_REPLAY_93 = FORMALLY_COMPLETE` and `STRICT_HISTORICAL_REPLAY_ENTRY_STATUS_ELIGIBILITY_GATE = FORMALLY_INTEGRATED`. The remote-verified integration is commit `3a8bb363838110d5b918829e19e97fef1718fdaf`, tree `19986e75e450150032e631fe4dac111d3e59e581`, parent `01524006b23a0496d084f0d605f31cba8e6b87f9`, message `feat: gate NAR replay on historical entry status authority`.

### Issuance-input audit

`NAROfficialResponseCapture` and its archive provide immutable raw NAR response bytes, canonical request URL, response SHA-256, capture identity, and exact request/observation/storage times. They do not authenticate a provider publication/availability time, and their model has no semantic proving complete entry-status coverage. `HistoricalInputEvidenceReference` can carry a response hash, `available_at`, and `observed_at`, but is a generic supplied reference; it has neither an entry-status source-record kind nor an issuer provenance boundary.

Phase85's V3 bundle has frozen bytes and Phase88 supplies the exact fourteen provider identities for the target. Phase90 proves only current observation: horse 14 has an explicit withdrawal marker, while horses 1–13 have `NO_EXPLICIT_WITHDRAWAL_EVIDENCE`, not `ACTIVE`. The V3 observations/captures are in 2026 and explicitly concern a historical target; they cannot be issued as 2025 prediction-time authority. Daily-target fixtures are also 2026 retrievals with no `provider_available_at`. Results, payouts, settlement, and replay outcomes are post-race and prohibited as status evidence. Phase92 found no independently timestamped pre-cutoff archive candidate.

### Required future issuer contract

An issuer may emit `NARHistoricalEntryStatusAuthority` only after independently proving exact NAR/nar_official target identity, immutable source bytes/reference, digest, trusted availability proof, availability no later than `target.scheduled_start_at`, complete target entry identity universe, complete status coverage for that same universe, and deterministic derivation. No caller-created dataclass, free-text semantic, filename date, race date, later HTTP header, current page, name link, odds, result, payout, or settlement state is evidence.

`entry_universe_identity` must be versioned and deterministic: a digest of canonical UTF-8 JSON for provider scope, external race ID, and the horse-number-ascending exact provider tuple `(external_entry_id, external_horse_id, horse_no)`. Phase88's `1..14` universe can supply identity material only; a source must independently cover that same universe before complete-status semantics can be issued.

Permitted future timestamp provenance is limited to reviewed `PROVIDER_PUBLICATION_AVAILABILITY` that binds provider-controlled publication metadata to exact content, or reviewed `INDEPENDENT_ARCHIVE_OBSERVATION` that binds immutable archive capture identity/time, original-source identity, and exact content/digest. Neither form is presently available for the target.

### Decision

Primary classification: `HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS`.

The known NAR documents cannot prove a complete status disposition for every entry: an explicit withdrawal is positive evidence only, and the absence of a marker cannot be promoted to active/non-withdrawn. Their timestamps are also post-cutoff. Therefore no Phase94 authority is issued for `NAR / 21 / 2025-01-01 / 6`; its Phase93 block remains `HISTORICAL_REPLAY_BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`.

The minimum next step is a separately reviewed discovery/source-contract phase for an official versioned complete entry-status publication or immutable independent archive snapshot available by the scheduled start. Only after that source semantics and timestamp proof exist may an issuer implementation be proposed. Phase41 remains unresolved: `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`; market eligibility, positive-market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. DB writes: `0`. Production code, tests, fixtures, archives, replay, staging, commit, and push: none. Modified paths: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md` only; staged and untracked sets are empty.

Next: `CHATGPT_REVIEW_PHASE94_AUTHORITY_ISSUANCE`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_93 — STRICT HISTORICAL REPLAY ELIGIBILITY POLICY

**Formal Status:** READY_FOR_REVIEW

**State:** IMPLEMENTED_FOR_REVIEW

**Outcome:** READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

**Implementation:** STRICT_HISTORICAL_REPLAY_ENTRY_STATUS_ELIGIBILITY_GATE_IMPLEMENTED

**Audit:** STRICT_HISTORICAL_REPLAY_ELIGIBILITY_POLICY_DESIGN_COMPLETE

**Design Review:** PHASE93_REPLAY_ELIGIBILITY_POLICY_DESIGN_REVIEW_PASS

Phase92 is frozen as `PHASE92_ARCHIVE_DISCOVERY_REVIEW_PASS` with exact result `HISTORICAL_ENTRY_STATUS_ARCHIVE_NOT_FOUND`. No independently timestamped pre-cutoff archive was found for `NAR / 21 / 2025-01-01 / 6` that could prove the horse-14 cancellation was available no later than 2025-01-01 13:50 JST. The Phase90 current observation remains distinct: horse 14 is `EXPLICIT_WITHDRAWAL_PRESENT`, horses 1–13 have only `NO_EXPLICIT_WITHDRAWAL_EVIDENCE`, and the capture semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`.

### Design decision

The correct integration point is an explicit NAR target-level readiness policy in `nar_daily_replay_orchestrator`, after audited target-set validation and before connection binding or `resolve_sqlite_nar_daily_evidence`. It prevents a blocked target from reaching snapshot selection, manifest projection, or replay. The generic `DailyHistoricalReplayEvidenceDisposition.UNSUPPORTED` can carry the complete diagnostic outcome and stable cause codes without changing generic snapshot, resolver, audit, execution-state, or persistence contracts.

The exact required new input is `historical_entry_status_authorities: NARHistoricalEntryStatusAuthoritySet`, a frozen canonical-target-set-bound tuple of explicit `NARHistoricalEntryStatusAuthority` values. Each authority carries the target, authority identity, canonical source identity, response digest, immutable availability-proof identity/kind, causally authoritative `available_at`, and observation identity; it must prove availability no later than the target prediction cutoff. Duplicates or out-of-denominator authority fail validation, and absence for a target means blocked. The frozen output is `NARHistoricalReplayEligibilityResolution`, which retains the exact target set and a target-order tuple of immutable `NARHistoricalReplayEligibilityDecision` values with only target, eligibility, blocker classification, missing authority, and causal reason.

Approval fixes the completeness requirement: only a closed `COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE` for the exact target's full entry universe can make an authority eligible. A single withdrawal fact, one change row, later absence of withdrawal text, or odds cannot substitute for complete status authority. The causal bound is `authority.available_at` or authoritative observation no later than `target.scheduled_start_at`; a missing start time blocks, and exact equality is eligible under `<=`. No arbitrary free-text semantic may grant eligibility.

The only eligibility states are `ELIGIBLE_WITH_PRE_CUTOFF_ENTRY_STATUS_AUTHORITY` and `BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`. The gate accepts only the exact target set plus explicit reviewed authority; it does not inspect a current status, horse 14, later page, result, payout, settlement, odds, or a database table to decide whether authority is required. No supplied cutoff-qualified authority means blocked.

For the frozen target, the decision is `BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE` with exact blocker `HISTORICAL_REPLAY_BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`. The missing authority is a provider-scoped exact-race/entry status publication with immutable raw bytes, stable identity, and independently verifiable availability/publication time at or before the prediction cutoff. Current 2026 status, results, payouts, settlement, odds absence, and horse-name inference are categorically excluded. Horse 14 remains an identity; it is neither removed nor treated active, and horses 1–13 are not promoted to eligible.

The existing orchestrator is whole-day deterministic: only `ALL_TARGETS_RESOLVED` reaches replay, while a partial resolution already returns without manifest or replay. The new policy blocks the entire day whenever any target lacks qualifying authority; it never removes a target. If blocked, `_resolve_evidence()` is not called. Instead the orchestrator constructs a complete deterministic `DailyHistoricalReplayEvidenceResolution` for the unchanged denominator: every target is `UNSUPPORTED`; targets lacking authority have exact reason `ENTRY_STATUS_AUTHORITY_UNAVAILABLE`, while otherwise-authorized targets blocked only by another target have exact reason `WHOLE_DAY_BLOCKED_BY_ENTRY_STATUS_AUTHORITY`. The resulting day state is `NO_EXECUTABLE_TARGETS`, and the existing execution state remains `NOT_RUN_NO_EXECUTABLE_TARGETS`; manifest, replay, and summary are absent.

`NARDailyReplayOrchestrationResult`, its audit identity, and production result persistence therefore need no structural change. Existing persistence already stores and validates each outcome's complete `reason_codes` in `resolution_outcomes_json`; the new reason codes survive via the existing contract. The future persistence test must update its direct `run_nar_daily_replay()` helper for the required authority input and prove the diagnostic codes round-trip unchanged.

The exhaustive direct-call audit found exactly two direct callers: `tests/test_nar_daily_replay_orchestrator.py` and `tests/test_nar_daily_replay_result_persistence.py`. The final future implementation scope is seven paths: create `scripts/simulation/nar_historical_replay_eligibility.py` and `tests/test_nar_historical_replay_eligibility.py`; modify `scripts/simulation/nar_daily_replay_orchestrator.py`, `tests/test_nar_daily_replay_orchestrator.py`, `tests/test_nar_daily_replay_result_persistence.py`, and the two phase-control documents. No production persistence-schema/module change is needed.

Future tests require the normal resolver path only when every target has valid pre-cutoff authority; one or multiple omissions must bypass `_resolve_evidence()`, preserve the entire denominator, and produce the exact per-target reason codes and `NO_EXECUTABLE_TARGETS` / `NOT_RUN_NO_EXECUTABLE_TARGETS` state without manifest, replay, or summary. They must also reject after-cutoff, target-mismatched, duplicate, or malformed authority, prove deterministic audit identity, and verify persisted diagnostic reason-code round trips.

`NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE` remains unresolved. Market eligibility, positive-market eligibility, whole-meeting cancellation, historical availability, and snapshot inclusion remain `UNSUPPORTED`.

The new pure authority module has frozen/slotted authority, authority-set, decision, and resolution types. The closed semantic is `COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE`; the cutoff is each `target.scheduled_start_at`, and both availability and observation must be no later. The orchestrator requires the explicit keyword-only `historical_entry_status_authorities` input. A blocked target creates an exact whole-day diagnostic resolution with `UNSUPPORTED` dispositions and the approved `ENTRY_STATUS_AUTHORITY_UNAVAILABLE` / `WHOLE_DAY_BLOCKED_BY_ENTRY_STATUS_AUTHORITY` reasons, while preserving `NOT_RUN_NO_EXECUTABLE_TARGETS` and bypassing the resolver, manifest writer, and replay runner. The production persistence module/schema is unchanged; an exact SQLite round trip retained the diagnostic reason code.

Required tests passed in order: eligibility `7 passed, 5 subtests passed`; orchestrator `23 passed, 11 subtests passed`; persistence `11 passed, 12 subtests passed`; SQLite NAR resolver `26 passed, 38 subtests passed`; Phase90 interpretation `27 passed`; daily aggregation `20 passed`; full suite `4515 passed, 2 skipped, 2846 subtests passed`.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. New policy DB writes: `0`. Phase41 remains unresolved. The exact seven approved paths were changed; final Git commit and push state is authoritative in the execution handoff.

Next: `CHATGPT_REVIEW_PHASE93_IMPLEMENTATION`.

## Historical Record — POST_V0_8_DAILY_REPLAY_91 — HISTORICAL NAR ENTRY-STATUS AUTHORITY DISCOVERY

**Status:** DRAFT_FOR_REVIEW

**Outcome:** READY_FOR_ARCHITECTURAL_REVIEW

**Audit:** HISTORICAL_NAR_ENTRY_STATUS_AUTHORITY_DISCOVERY_COMPLETE

Phase90 is reconciled as independently verified: `PHASE90_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`; `POST_V0_8_DAILY_REPLAY_90 = FORMALLY_COMPLETE`; `NAR_CURRENT_ENTRY_STATUS_INTERPRETATION = FORMALLY_INTEGRATED`. Its committed state is `01524006b23a0496d084f0d605f31cba8e6b87f9` / `149cc925cc296726c1d8e92e5d3faa207b9ad9eb`, parent `115cd9489d1a13a6cffc99e85d1c79b8cca72194`, message `feat: add NAR current entry status interpretation`.

### Candidate authorities and causal result

- The frozen V3 DebaTable/RaceList, Phase85 bundle, Phase88 binding, and Phase90 interpreter establish only current observation: the manifest identifies Deba and RaceList observations/captures on 2026-09-21. They exactly associate horse 14's `出走取消`, but the manifest expressly says `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; it has no provider-publication `available_at`. They cannot establish 2025 prediction-time status.
- The older daily-target RaceList fixture is the same target RaceList byte family, but its `provenance.json` records a 2026-09-03 request/observation and `provider_available_at: null`. The target date encoded in the URL and filename is race identity, not historical publication-time authority.
- `HistoricalInputEvidenceReference` and the historical snapshot provenance schema can represent `available_at` and `observed_at`, and `build_historical_input_snapshot` rejects either timestamp when later than the information cutoff. They contain no target-specific entry-status record; `HistoricalInputSourceRecord` has no entry-status kind.
- The NAR official/daily capture domains retain exact capture timing, but do not supply a pre-cutoff target status capture. Read-only inspection of the local persisted database found only `races` and `horses`; it has no NAR capture, historical-target capture, snapshot, or provenance-evidence table.
- NAR `RACE_MARK_TABLE` result/payout persistence and settlement/replay-result records are post-race outcome domains. They are excluded from identity/status reconstruction by the causal firewall and cannot prove withdrawal at the prediction cutoff.

### Architectural decision

Primary classification: **`HISTORICAL_ENTRY_STATUS_AUTHORITY_REQUIRES_NEW_CAPTURE_SOURCE`**.

The missing authority is a provider-scoped, immutable pre-cutoff status publication for exact target `NAR / 21 / 2025-01-01 / 6`, with exact raw bytes, canonical request/race-entry identity, response hash, and a verifiable provider publication/availability timestamp no later than the historical prediction cutoff. It must evidence status directly—not a later result, payout, settlement, odds absence, current page, or name-based association.

`NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE` remains unresolved. No historical entry status, market eligibility, positive-market eligibility, whole-meeting cancellation, or snapshot-inclusion claim is made; all remain `UNSUPPORTED` as applicable.

The smallest next step is a separately reviewed research design for an official historical NAR archive/version that can show target `changeInfo` (or an equivalent entry-status publication) with a provider-verifiable pre-cutoff timestamp. A current-only provider page is insufficient. A third-party archive requires a new explicit provenance/timestamp contract before it could be admitted; if neither source exists, the historical period remains unsupported. This Phase91 performed no acquisition and grants no live authorization.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. DB writes: `0` (one read-only local schema/archive inspection only). Tests, staging, commit, and push: none. Modified paths are exactly the two phase-control documents; staged and untracked sets are empty.

Next: `CHATGPT_REVIEW_PHASE91_HISTORICAL_STATUS_AUTHORITY`.

## Historical Record — POST_V0_8_DAILY_REPLAY_90 — NAR ENTRY-STATUS INTERPRETATION AUTHORITY AUDIT

**Formal Status:** READY_FOR_REVIEW

**State:** IMPLEMENTED_FOR_REVIEW

**Outcome:** READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

**Implementation:** NAR_CURRENT_ENTRY_STATUS_INTERPRETATION_IMPLEMENTED

**Audit:** NAR_ENTRY_STATUS_INTERPRETATION_AUTHORITY_AUDIT_COMPLETE

**Design Review:** PHASE90_ENTRY_STATUS_DESIGN_REVIEW_PASS

**Authorization:** NONE_REQUIRED_NO_NETWORK_NO_DB

Phase90 started at HEAD/tree `115cd9489d1a13a6cffc99e85d1c79b8cca72194` / `6044d07ceb3e843fa43e7370a637dd1bc1040b14`. Implementation changed exactly the approved new interpreter, focused test, and two phase-control docs. The final Git integration result is authoritative in the execution handoff after commit and push.

### Prior-state reconciliation

Phase89's actual integration is commit `115cd9489d1a13a6cffc99e85d1c79b8cca72194`, tree `6044d07ceb3e843fa43e7370a637dd1bc1040b14`, parent `2e420a911e2cdeeb81f32214e5ba4d01fb4b0a7d`, message `test: complete Phase88 bundle authenticity coverage`, with exactly the focused binder test and two phase-control docs committed. Normal push succeeded and local/remote-tracking HEAD both reached the commit. This supersedes the stale former current/final statement that Phase89 staging, commit, and push were `NONE`, while preserving the historical PREPARE/APPROVE chronology.

Independent review now fixes `PHASE88_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`, `POST_V0_8_DAILY_REPLAY_88 = FORMALLY_COMPLETE`, `STRICT_READ_ONLY_NAR_REPLAY_IDENTITY_BINDING = FORMALLY_INTEGRATED`, `PHASE89_TEST_HARDENING_REMOTE_VERIFICATION_PASS`, and `POST_V0_8_DAILY_REPLAY_89 = FORMALLY_COMPLETE`.

### Status evidence and temporal conclusion

The frozen DebaTable contains one explicit `出走取消` marker in the reviewed current change/status area of horse 14's target-entry block. The interpreter must not search arbitrary/global occurrences of `取消` or `出走取消`, because historical past-race text in the same document is not current target-entry status evidence. The frozen RaceList has one exact target `changeInfo` row: race `6R`, horse number `14`, category `出走取消`, reason `疾病`. Profile-A v3 proves one entry table and fourteen listed identities but no active-status meaning. Profile-B v2 formally proves `EXPLICIT_WITHDRAWAL_PRESENT`, the exact target schedule/change-row shape, and one horse-14 association. Phase66 proves the schedule row and nested `changeInfo` row are distinct structural candidates. The V3 manifest freezes those results, while Phase85 retains their exact bytes/metadata and Phase88 maps all fourteen identities—including horse 14—to internal race-entry IDs without adding status.

The capture timestamps are post-target: Deba requested/observed/captured at `2026-09-21T23:27:42.093809Z` / `2026-09-21T23:27:42.678776Z` / `2026-09-21T23:27:42.678947Z`; RaceList at `2026-09-21T23:27:42.679272Z` / `2026-09-21T23:27:43.165338Z` / `2026-09-21T23:27:43.165400Z`, for a `2025-01-01` target. No metadata proves the status was published or available by the historical prediction cutoff. The exact source semantic remains `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`.

The four questions therefore have separate answers:

- Current observed status: horse 14 has explicit withdrawal evidence corroborated by both documents. Horses 1–13 have only `NO_EXPLICIT_WITHDRAWAL_EVIDENCE`; they are not proven `ACTIVE`.
- Historical status: unavailable. Current evidence cannot be backdated; `HISTORICAL_ENTRY_STATUS_AUTHORITY_BLOCKED` remains exact.
- Market eligibility: unsupported. Phase41's `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE` remains unresolved, and `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`.
- Snapshot inclusion: unsupported. This evidence cannot justify dropping horse 14 or including the other thirteen in a historical snapshot.

Existing result/settlement status enums are post-race domains, not a safe entry-status vocabulary. `HistoricalInputSourceRecord` has no status record kind, `HistoricalRaceEntrySnapshot` has no status field, and the snapshot builder rejects evidence observed after its information cutoff. The audit therefore rejects forcing status into those domains.

### Architectural decision

Primary classification: **`ENTRY_STATUS_INTERPRETATION_IMPLEMENTABLE`**, but only for current-observed evidence. Historical entry-status authority remains blocked.

The minimum future no-network implementation is one production module, one focused test, and these two docs: create `scripts/simulation/nar_race_entry_status_interpretation.py` and `tests/test_nar_race_entry_status_interpretation.py`. Its exact trusted inputs should be the Phase85 bundle plus the Phase88 identity binding; no DB mapping is rediscovered. It returns a separate frozen/slotted interpretation with target, fixed acquisition semantic, temporal scope `CURRENT_OBSERVATION_ONLY`, and an immutable horse-number-ordered tuple of identity-bound entry evidence. The only current-observation classifications are `EXPLICIT_WITHDRAWAL_OBSERVED` and `NO_EXPLICIT_WITHDRAWAL_EVIDENCE`; there is no `ACTIVE` inference.

The future interpreter must join only by reviewed race/horse/external-entry identity, parse only the reviewed Deba current change/status area and exact RaceList `changeInfo` association `(6, 14, 出走取消)`, and require complete entry-set equality plus Deba/RaceList/Profile-B agreement. Profile-B must retain `EXPLICIT_WITHDRAWAL_PRESENT`, a passing horse-14 association, `withdrawn_provider_horse_no = 14`, and `withdrawal_label_match = true`. It retains horse 14 and fails the complete race for unsupported bundle/binding, target or entry-set contradiction, missing/ambiguous evidence, Deba/RaceList or Profile-B contradiction, horse association contradiction, unavailable temporal authority, or unsupported status representation. It must not use names, odds, result/settlement data, construct a snapshot, apply market rules, persist data, or run replay.

### Phase90 implementation verification

The keyword-only `interpret_nar_race_entry_status_v3(*, bundle, binding)` returns exact frozen/slotted race, entry, and timestamp evidence values. Frozen Phase85 bytes and manifest authority, the complete fourteen-entry Phase88 binding, target/entry identity, Deba current `td.info`, RaceList target `changeInfo`, and Profile-B are checked before a result is constructed. Horse 14 is `EXPLICIT_WITHDRAWAL_PRESENT`; horses 1–13 are `NO_EXPLICIT_WITHDRAWAL_EVIDENCE`. The output records 2026 observed/captured timestamps and `HISTORICAL_ENTRY_STATUS_AUTHORITY_BLOCKED`; it never declares active, market eligible, snapshot included, or replay ready.

Required verification passed in order: Phase90 focused `27 passed`; Phase88 identity binding `51 passed`; Phase85 fixture consumer `40 passed, 2 skipped`; V3 fixture `4 passed`; historical snapshot builder `14 passed, 15 subtests passed`; full repository suite `4505 passed, 2 skipped, 2841 subtests passed`. Frozen fixture byte identities remain Deba `313317` / `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`, RaceList `66307` / `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`, and manifest `4254` / `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d`.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`; DB access/writes: `0 / 0`. Phase41's `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE` remains unresolved. Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`.

Next: `CHATGPT_REVIEW_PHASE90_IMPLEMENTATION`.

## Historical Record — POST_V0_8_DAILY_REPLAY_89 — BUNDLE-AUTHENTICITY NEGATIVE-TEST COMPLETION DESIGN

**Formal Status:** READY_FOR_REVIEW

**State:** IMPLEMENTED_FOR_REVIEW

**Outcome:** READY_FOR_INDEPENDENT_TEST_HARDENING_REVIEW

**Implementation:** PHASE88_BUNDLE_AUTHENTICITY_NEGATIVE_TEST_COMPLETION_IMPLEMENTED

**Design Contract:** PHASE88_BUNDLE_AUTHENTICITY_NEGATIVE_TEST_COMPLETION_CONTRACT_COMPLETE

**Design Review:** PHASE89_TEST_HARDENING_DESIGN_REVIEW_PASS

**Authorization:** NONE_REQUIRED_TEST_ONLY

**Prior Review:** PHASE88_IMPLEMENTATION_REMOTE_VERIFICATION_PASS_WITH_BUNDLE_AUTHENTICITY_TEST_GAP

**Primary Blocker:** PHASE88_BUNDLE_AUTHENTICITY_NEGATIVE_TEST_COVERAGE_INCOMPLETE

Phase89 completed test hardening at HEAD/tree `2e420a911e2cdeeb81f32214e5ba4d01fb4b0a7d` / `399e45fb6bcfab31ef703d2a827fa3bdee6a597f`. Phase88 production remains independently frozen; its binder SHA-256 was verified before and after as `6e98bc204141ed9e64d6e100d7a42e5ee78e5cd5c5bba7dffa26e01afba19904`. The three focused negative-test gaps were forged manifest member, FixtureSetV3 identity mismatch, and QualificationV3 identity mismatch. No production defect was revealed.

Phase89 changed exactly `tests/test_nar_race_entry_status_replay_identity_binding.py`, `docs/CURRENT_PHASE.md`, and `docs/LATEST_CODEX_REPORT.md`. The binder and all fixtures remain immutable. The forged-manifest test uses test-only `object.__new__` / `object.__setattr__` to retain the exact public bundle type and authentic bytes while replacing `manifest` with a wrong exact type. The FixtureSet and Qualification cases retain authentic raw bytes and manifest authority, then narrowly monkeypatch the binder's expected identity constants to isolate their comparison gates. Each passes a deliberately invalid connection value and returns `UNSUPPORTED_BUNDLE`, proving authenticity fails before any SQLite inspection.

The binder SHA above and frozen Deba `313317` / `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`, RaceList `66307` / `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`, and manifest `4254` / `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d` identities all matched before and after testing. Required order passed: focused binder `51 passed`; Phase85 consumer `40 passed, 2 skipped`; V3 fixture `4 passed`; migration `11 passed`; SQLite snapshot repository `25 passed, 30 subtests passed`; snapshot builder `14 passed, 15 subtests passed`; full suite `4478 passed, 2 skipped, 2841 subtests passed`.

Phase88 is now a candidate for final independent completion review; Phase89 does not claim that review has occurred. Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; market eligibility, positive market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`. No production changes, provider HTTP, Phase44, GET, DB writes, staging, commit, or push occurred during test execution.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. DB writes: `0`. The changed paths are exactly the focused test and two phase-control documents; staged and untracked sets are empty before Git integration. Next: `CHATGPT_REVIEW_PHASE89_TEST_HARDENING`.

## POST_V0_8_DAILY_REPLAY_88 — STRICT READ-ONLY NAR IDENTITY BINDING IMPLEMENTATION

**State:** IMPLEMENTED_FOR_REVIEW

**Outcome:** READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

**Implementation:** STRICT_READ_ONLY_NAR_REPLAY_IDENTITY_BINDING_IMPLEMENTED

**Design Review:** PHASE88_IDENTITY_BINDING_DESIGN_REVIEW_PASS
**Authorization:** NONE_REQUIRED_NO_NETWORK_READ_ONLY_SQLITE

At the approved starting HEAD/tree `33d8c755c862c073f5783c3645ac0958376afa2c` / `70d040a7c90b5029b090d6aabce56974b3366a5a`, Phase88 created only `scripts/simulation/nar_race_entry_status_replay_identity_binding.py` and `tests/test_nar_race_entry_status_replay_identity_binding.py`, and updated only the two phase-control documents. The public keyword-only API `bind_nar_race_entry_status_v3_identity(bundle, connection)` returns a frozen/slotted race binding with `(target, organization, source_system, external_race_id, internal_race_id, entry_bindings)`; each frozen/slotted entry binding has `(external_entry_id, external_horse_id, horse_no, race_entry_id)`. Failure classifications are stable and fail closed.

The binder checks exact published bundle type, target/path tuple, frozen raw/manifest byte identities, canonical manifest, provider, semantics, and FixtureSet/Qualification identities before source parsing or SQLite access. Its identity-only Deba extractor finds exactly horses `1..14`, retains horse 14 despite `出走取消` and unusable odds, derives `nar:20250101:21:6` and provider-scoped entry IDs, and validates provider-local `nar:horse:` links without using names or statuses. No historical normalizer fallback is used.

The caller-owned exact SQLite connection must already have `foreign_keys=1`, `query_only=1`, no transaction, and no attached database. One owned read transaction is rolled back on success or failure. The binder validates V010 tables, column types, PK/unique/FK authority and foreign-key integrity, then requires exact forward/reverse race mapping, all 14 V010 entry mappings, source/DB set equality, distinct internal entry IDs, and mapped horses rows with horse numbers checked only after ID mapping. External horse IDs are audit evidence only, never database lookup keys or cross-provider identity. The production module contains no database writes, provider access, snapshot/result/payout/odds lookup, status application, or replay.

Required tests passed in order: focused binder `48 passed`; Phase85 consumer `40 passed, 2 skipped`; V3 dedicated fixture `4 passed`; migration `11 passed`; SQLite snapshot repository `25 passed, 30 subtests passed`; snapshot builder `14 passed, 15 subtests passed`; full suite `4475 passed, 2 skipped, 2841 subtests passed`. The skips are platform-conditional symlink tests. Published Deba `313317` / `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`, RaceList `66307` / `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`, and manifest `4254` / `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d` were unchanged before and after testing.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Production DB writes: `0`. Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; market eligibility, positive market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`. Identity binding does not claim replay readiness. The final scoped Git result is supplied in the execution handoff; this report records implementation evidence for independent review.

Next action: `CHATGPT_REVIEW_PHASE88_IMPLEMENTATION`.

## POST_V0_8_DAILY_REPLAY_88 — STRICT READ-ONLY NAR IDENTITY-BINDING DESIGN

**Formal Status:** APPROVED_FOR_CODEX
**Outcome:** APPROVED_STRICT_READ_ONLY_NAR_REPLAY_IDENTITY_BINDING
**Design Contract:** STRICT_READ_ONLY_NAR_REPLAY_IDENTITY_BINDING_CONTRACT_COMPLETE
**Design Review:** PHASE88_IDENTITY_BINDING_DESIGN_REVIEW_PASS
**Authorization:** NONE_REQUIRED_NO_NETWORK_READ_ONLY_SQLITE

Phase88 is approved for the next no-network, no-write identity-binding implementation at HEAD/tree `33d8c755c862c073f5783c3645ac0958376afa2c` / `70d040a7c90b5029b090d6aabce56974b3366a5a`. This approval made no production/test/fixture changes, provider requests, Phase44 calls, GETs, snapshot/replay/status/market actions, database writes, staging, commit, or push.

### Exact entry-identity decision

The V010 external-race and external-entry tables remain the only persisted provider-scoped mapping authority. The NAR target is closed to `NAR` / `nar_official` / `21` / `2025-01-01` / `6`, with external race ID exactly `nar:20250101:21:6`, derived from the Phase85 target—not caller text. The existing NAR normalizer and daily target source prove the race grammar; the normalizer and NAR result/payout persistence prove external entry IDs are exactly `{external_race_id}:entry:{horse_no}`.

`DEDICATED_ENTRY_IDENTITY_EXTRACTION_REQUIRED` is the correct classification. Profile-A/B, Phase66, raw capture, and V3 manifest authority are all deliberately bounded diagnostics/capture authority, not a complete all-entry identity universe. The frozen DebaTable has exactly fourteen unique entry identities with horse numbers `1..14`; horse 14 has its canonical provider horse link and contains `出走取消`. The future private extractor must retain all fourteen from the Deba entry table without parsing odds or interpreting status. It may reuse only independently identity-only helpers such as `_horse_rows` for row selection and `_canonical_horse_identity` for link validation; it must never invoke the whole-record normalizer or `_row_values`, which impose cancellation/odds/jockey behavior.

`external_horse_id` stays supporting NAR-local evidence, not a database lookup key or cross-provider bridge. `EXTERNAL_HORSE_ID_DATABASE_BINDING = UNSUPPORTED` and `CROSS_PROVIDER_HORSE_IDENTITY = UNSUPPORTED`. Horse number is never a global lookup key; after exact V010 mapping it is a required consistency check against the selected `horses` row only.

### Read-only binding contract

The future exact API is `bind_nar_race_entry_status_v3_identity(*, bundle: NARRaceEntryStatusSourceProfileFixtureBundleV3, connection: sqlite3.Connection) -> NARRaceEntryStatusReplayIdentityBinding`. It returns frozen target/provider/external/internal race identity plus a tuple of frozen external-entry/external-horse/horse-number/race-entry bindings, or raises. No connection, mapping, status, market, snapshot, replay, or settlement object is returned.

The explicit caller-owned connection must be an exact `sqlite3.Connection`, have no active caller transaction or attached database, and already report `foreign_keys == 1` and `query_only == 1`. These are caller preconditions: the binder may not alter or leave changed caller-visible PRAGMAs. It opens only one owned deferred read transaction and rolls it back on every exit; it never commits, closes, or discovers a database path. A private schema inspector follows the existing resolver's PRAGMA read-validation pattern without importing replay logic; it validates required V010 tables, columns/types, primary keys, unique keys, `ux_horses_race_id_id` (or exact equivalent), RESTRICT foreign keys, and consumed `foreign_key_check` results.

Race lookup requires exactly one forward and matching reverse V010 map plus one `races.id`. Entry lookup requires every extracted source entry to map exactly once to that race and a positive entry ID, then requires exact equality of the entire source and database external-entry sets. Each selected `horses` row must match both the internal race and source horse number. Missing, additional, ambiguous, contradictory, duplicate, or structurally invalid rows fail closed. No DDL/DML/upsert/repair, outcome/payout/odds/result/settlement lookup, or post-cutoff inference is permitted.

The future implementation remains exactly four paths: create `scripts/simulation/nar_race_entry_status_replay_identity_binding.py` and `tests/test_nar_race_entry_status_replay_identity_binding.py`, and modify the two phase-control documents. The status-neutral private extractor belongs inside the new binder, so no fifth support path is required. A fifth path is `PHASE88_IDENTITY_BINDING_SUPPORT_SCOPE_REQUIRES_DESIGN_REVISION`.

Focused tests are defined for complete valid binding including retained horse 14, exact mappings and set closure, all race/entry/internal-row/horse-number contradictions, V010 PK/unique/FK corruption, connection/attachment/query-only/no-write enforcement, deterministic behavior, CWD independence, no replay/market/settlement dependency, and no partial return.

Future execution is ordered: focused binder, Phase85 fixture consumer, committed V3 fixture, historical snapshot migration, SQLite snapshot repository, snapshot builder, then the established full suite. All are local/no-network and must pass.

The Phase85 bundle authenticity gate is mandatory before parsing: exact type, target/path tuple, three frozen byte identities, canonical manifest-byte equality, exact provider/acquisition semantics, and frozen FixtureSetV3/QualificationV3 identities. Any failure is `UNSUPPORTED_BUNDLE` without reloading fixtures or using network. Readiness A–V: **YES**. Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; market eligibility, positive market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`. Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Only the two phase-control docs are modified; staged/untracked sets remain empty.

Next action: `EXECUTE_APPROVED_PHASE`.

## POST_V0_8_DAILY_REPLAY_87 — REPLAY IDENTITY-BINDING AUTHORITY AUDIT

**Status:** DRAFT_FOR_REVIEW
**Outcome:** READY_FOR_ARCHITECTURAL_REVIEW
**Audit:** NAR_REPLAY_IDENTITY_BINDING_AUTHORITY_AUDIT_COMPLETE

Phase87 audited the repository at HEAD/tree `33d8c755c862c073f5783c3645ac0958376afa2c` / `70d040a7c90b5029b090d6aabce56974b3366a5a` without implementation, tests, database writes, replay, provider HTTP, Phase44, GET, staging, commit, or push. Phase85 and Phase86 are frozen formally complete; the strict local V3 consumer remains formally integrated.

### Evidence-backed identity map

Phase85's `scripts/simulation/nar_race_entry_status_source_profile_fixture_consumer.py::load_nar_race_entry_status_source_profile_v3_fixture` returns a validated V3 source-profile bundle only. Its `NARRaceEntryStatusRaceIdentity` from `nar_race_entry_status_raw_capture.py` carries exact `(baba_code, race_date, race_no)`, raw source bytes, manifest authority, Phase66 ancestry, and publication plan—not an external race ID, external-entry collection, internal race ID, race-entry ID, DB repository, snapshot, or replay input.

The repository's existing NAR normalizer, `scripts/simulation/nar_historical_input_source.py::normalize_nar_historical_input_source_records`, derives stable provider-scoped identifiers from a canonical NAR Deba URL and row evidence: organization/source system `NAR` / `nar_official`, race `nar:{YYYYMMDD}:{baba_code}:{race_no}`, entry `{race}:entry:{horse_no}`, and provider-local horse `nar:horse:{k_lineageLoginCode}`. `HistoricalInputSourceRecord` in `historical_input_source_records.py` retains those external identifiers only. The same race-ID grammar is used by `nar_historical_daily_target_source.py` after a RaceList link has proven its date/venue/race identity.

This existing normalizer is not a neutral all-row binder dependency: it rejects cancellation-marked rows and unsupported odds before producing records. It would therefore turn identity binding into entry/status/market interpretation and risks dropping a required source row. Phase87 preserves the rule that a binder must bind every source entry or fail the entire race; it must not silently omit withdrawn/cancelled rows.

`historical_input_snapshots.py` requires internal `internal_race_id` and `race_entry_id`, with `HistoricalExternalRaceIdentity` keyed by `(organization, source_system, external_race_id)` and `HistoricalExternalEntryIdentity` adding `external_entry_id`. Its `external_horse_id` is explicitly non-key metadata. `historical_input_snapshot_builder.py::build_historical_input_snapshot` takes internal IDs and complete external-entry mapping from its caller; it is not a resolver and enforces causal evidence eligibility.

Migration `scripts/migrations/versions/v010_historical_input_snapshot_schema.py` is the only formal persisted mapping authority:

- `historical_input_external_races` is exactly keyed by organization/source-system/external-race and has a reverse uniqueness constraint for internal race IDs within the source.
- `historical_input_external_entries` is exactly keyed by organization/source-system/external-race/external-entry and has reverse uniqueness for `(internal_race_id, race_entry_id)` within the source.
- both reference the exact race mapping/race-entry relationship; `ux_horses_race_id_id` exists, but there is no formal `(race_id, horse_no)` uniqueness constraint.

`sqlite_nar_daily_evidence_resolver.py::_prediction` proves the intended read-side failure model: exact forward and reverse race-map queries are required; absent mapping returns `INTERNAL_RACE_MAPPING_MISSING`; ambiguous/contradictory rows are integrity failures. `SQLiteHistoricalInputSnapshotRepository` validates the same rows during snapshot load, but its mapping helpers are write-side persistence paths and cannot be repurposed for a no-write binder. Legacy `database.py` uses date/organization/place/race-number and `(race_id, horse_no)` `LIMIT 1` lookups without schema uniqueness; those are not binding authority.

### Audit conclusion

`RACE_BINDING_AUTHORITY_PARTIAL` and `ENTRY_BINDING_AUTHORITY_PARTIAL` are proven: V010 maps are sufficient only when exact existing rows are present, while Phase85 has no read-only adapter and no typed source entry-identity projection. `horse_no` is valid only as an exact-race consistency check after the provider-scoped map; it is never a global horse identity. `external_horse_id` is provider-local/non-key and `CROSS_PROVIDER_HORSE_IDENTITY = UNSUPPORTED`. Name, jockey, display text, fuzzy/normalized matching, race names, row order, outcomes, and settlement evidence are prohibited.

The single primary blocker is **`REPLAY_IDENTITY_BINDING_SUPPORT_REQUIRED`**. The proposed next phase is a small no-network, read-only SQLite-backed authority: create `scripts/simulation/nar_race_entry_status_replay_identity_binding.py` and `tests/test_nar_race_entry_status_replay_identity_binding.py`, then modify the two phase-control docs. It should take the Phase85 bundle and an explicit read-only mapping repository, produce a separate immutable complete binding object, query only V010 mappings, and fail closed for missing, ambiguous, contradictory, duplicate, unsupported-provider, cross-provider, or causally ineligible identity evidence. It must not write mappings, apply status, promote markets, construct snapshots, or run replay.

The ordered next dependency is: validated V3 consumer (complete) → provider-scoped race/entry binding (missing read-side authority; no-network/read-only DB implementation possible) → entry/status interpretation → complete causal snapshot → market/odds/settlement authority. Later live authorization is not implied by Phase87; it depends on the later evidence requirement.

Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; market eligibility, positive market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`. Readiness A–R: **YES**. Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Only the two phase-control documents are modified; staged and untracked sets remain empty.

Next action: `CHATGPT_REVIEW_PHASE87_IDENTITY_BINDING_AUDIT`.

## POST_V0_8_DAILY_REPLAY_86 — DOCUMENTATION RECONCILIATION

**Formal Status:** READY_FOR_REVIEW
**State:** IMPLEMENTED_FOR_REVIEW
**Outcome:** READY_FOR_INDEPENDENT_DOCUMENTATION_REVIEW
**Implementation:** PHASE85_POST_COMMIT_DOCUMENTATION_RECONCILIATION_IMPLEMENTED
**Design Contract:** PHASE85_POST_COMMIT_DOCUMENTATION_RECONCILIATION_CONTRACT_COMPLETE
**Design Review:** PHASE86_DOCUMENTATION_RECONCILIATION_DESIGN_REVIEW_PASS
**Primary blocker resolved:** PHASE85_LATEST_REPORT_POST_COMMIT_STATE_STALE
**Authorization:** NONE_REQUIRED_DOCS_ONLY

Phase86 inspected the independently verified Phase85 integration without changing production code, tests, or fixtures. Phase85's actual commit is `496d581120be5bda5326ed6a95b17169e92adbdc`, tree `2ad0df638e31b4275a63b8a1fa63e408bca4ee0d`, parent `c6e06ac5331b2f056534efa58756383e587ec27e`, and message `feat: add strict local NAR V3 fixture consumer`. Before Phase86 integration, the local and remote-tracking heads both equaled that commit.

The exact four committed Phase85 paths are `scripts/simulation/nar_race_entry_status_source_profile_fixture_consumer.py`, `tests/test_nar_race_entry_status_source_profile_fixture_consumer.py`, `docs/CURRENT_PHASE.md`, and `docs/LATEST_CODEX_REPORT.md`. The frozen remote review confirms the API, immutable bundle, strict local filesystem/manifest/formal-authority validation, Phase83 identity gate, absence of network/database/replay authority, and all reported tests. Published Deba/RaceList/manifest Git blobs remain `e0da768cb7c5cb98c4ae060e463581f829d2eb79`, `57bb0d763b30401080cc577251e53fc9335f05ad`, and `63d6f05cb7807d25e3ea84118e24ffee6ded0e5e`; their frozen content identities remain unchanged.

The independently identified Phase85 reporting defect was its outdated final integration status and missing commit identity. The Phase85 final implementation result below now records its actual commit, normal push, and clean final local state. Historical PREPARE and APPROVE records retain their original chronology.

The completed reconciliation records `PHASE85_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`, `POST_V0_8_DAILY_REPLAY_85 = FORMALLY_COMPLETE`, and `STRICT_LOCAL_V3_SOURCE_PROFILE_FIXTURE_CONSUMER = FORMALLY_INTEGRATED`. Phase86 changed only the two phase-control documents; Phase85 production code, tests, fixtures, and historical semantics are unchanged. Phase85 tests were not rerun.

Frozen Phase85 verification: consumer `40 passed, 2 skipped`; dedicated V3 `4 passed`; publication contract `49 passed`; publication plan `45 passed`; Profile-A `17 passed`; Profile-B diagnostics `38 passed`; Phase66 `152 passed`; full suite `4427 passed, 2 skipped, 2841 subtests passed`. The skips were platform-conditional symlink creation cases. Provider HTTP / Phase44 / GET: `0 / 0 / 0`.

Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`. No historical availability or replay readiness is inferred.

Next action: `CHATGPT_REVIEW_PHASE86_DOCUMENTATION_RECONCILIATION`.

## POST_V0_8_DAILY_REPLAY_85 — IMPLEMENTATION

**Formal Status:** READY_FOR_REVIEW
**State:** IMPLEMENTED_FOR_REVIEW
**Outcome:** READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW
**Implementation:** STRICT_LOCAL_V3_SOURCE_PROFILE_FIXTURE_CONSUMER_IMPLEMENTED
**Design Review:** PHASE85_FIXTURE_CONSUMER_DESIGN_REVIEW_PASS
**Authorization:** NONE_REQUIRED_NO_NETWORK_IMPLEMENTATION

Phase85 implemented `load_nar_race_entry_status_source_profile_v3_fixture(*, repository_root: Path, target: NARRaceEntryStatusRaceIdentity) -> NARRaceEntryStatusSourceProfileFixtureBundleV3` in the approved production module. The exact immutable bundle fields are `target`, `deba_table_bytes`, `race_list_bytes`, `manifest_bytes`, `manifest`, `phase66_ancestry`, `publication_plan`, and `repository_relative_paths`; the path tuple is exactly `(EXPECTED_DEBA_TABLE_PATH_V3, EXPECTED_RACE_LIST_PATH_V3, EXPECTED_MANIFEST_PATH_V3)`.

The implementation accepts only the exact published target and canonical explicit repository root, closes the fixture directory to exactly three files, rejects link/reparse/path-escape and unstable-read conditions, reads each file once, and parses only strict UTF-8 canonical JSON without duplicate keys or non-finite values. It then validates raw SHA/length against manifest metadata, reconstructs capture metadata, and recomputes existing Profile-A v3, Profile-B v2, Safety v3, Phase66, FixtureSetV3, QualificationV3, ManifestV3, and PublicationPlanV3 authority before applying the final frozen Phase83 byte and identity gate. No provider/network, Phase44, subprocess/socket, database, historical normalizer, snapshot, or replay authority is imported or invoked.

The fail-closed public base is `NARRaceEntryStatusSourceProfileFixtureConsumerError`, with unsupported, filesystem, manifest, and formal-authority subclasses. Stable classifications cover `UNSUPPORTED_TARGET`, `FILESYSTEM_VIOLATION`, `MISSING_FIXTURE`, `UNEXPECTED_FIXTURE_DIRECTORY_CONTENT`, `MANIFEST_INVALID`, `DOCUMENT_IDENTITY_MISMATCH`, `TARGET_OR_PATH_CONTRADICTION`, `FORMAL_AUTHORITY_VALIDATION_FAILURE`, and `FROZEN_PHASE83_IDENTITY_MISMATCH`.

Verification results:

- focused consumer: `40 passed, 2 skipped` (the skips are platform-conditional symlink creation cases)
- committed V3 fixture: `4 passed`
- publication contract: `49 passed`
- publication plan: `45 passed`
- Profile-A: `17 passed`
- Profile-B diagnostics: `38 passed`
- Phase66 structural diagnostics: `152 passed`
- full repository suite: `4427 passed, 2 skipped, 2841 subtests passed`

The committed Phase83 artifacts were read-only throughout. Before and after tests, DebaTable remained 313317 bytes / `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`, RaceList remained 66307 bytes / `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`, and manifest remained 4254 bytes / `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d`. FixtureSetV3 and QualificationV3 remain `nar-race-entry-status-source-profile-fixture-set-v3:11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225` and `nar-race-entry-status-source-profile-qualification-v3:a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff`.

Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; market, positive-market, and whole-meeting-cancellation eligibility remain `UNSUPPORTED`. Provider HTTP / Phase44 / GET: `0 / 0 / 0`.

The Phase85 commit and normal push succeeded. Commit `496d581120be5bda5326ed6a95b17169e92adbdc` has tree `2ad0df638e31b4275a63b8a1fa63e408bca4ee0d`, parent `c6e06ac5331b2f056534efa58756383e587ec27e`, and message `feat: add strict local NAR V3 fixture consumer`. Its exact four paths are `scripts/simulation/nar_race_entry_status_source_profile_fixture_consumer.py`, `tests/test_nar_race_entry_status_source_profile_fixture_consumer.py`, `docs/CURRENT_PHASE.md`, and `docs/LATEST_CODEX_REPORT.md`. After Phase85 push, both local and remote-tracking HEAD equaled that commit; the worktree was clean, with empty staged and untracked sets. Provider HTTP / Phase44 / GET remained `0 / 0 / 0`.

Independent verification: `PHASE85_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`. Formal verdict: `POST_V0_8_DAILY_REPLAY_85 = FORMALLY_COMPLETE`; `STRICT_LOCAL_V3_SOURCE_PROFILE_FIXTURE_CONSUMER = FORMALLY_INTEGRATED`.

Next action: `CHATGPT_REVIEW_PHASE85_IMPLEMENTATION`.

## POST_V0_8_DAILY_REPLAY_85 — APPROVE

**Formal Status:** APPROVED_FOR_CODEX
**Outcome:** APPROVED_STRICT_LOCAL_V3_SOURCE_PROFILE_FIXTURE_CONSUMER
**Design Review:** PHASE85_FIXTURE_CONSUMER_DESIGN_REVIEW_PASS
**Design Contract:** STRICT_LOCAL_V3_SOURCE_PROFILE_FIXTURE_CONSUMER_CONTRACT_COMPLETE
**Authorization:** NONE_REQUIRED_NO_NETWORK_IMPLEMENTATION

This approval records the Phase85 executable contract only. It is bound to branch `feature/post-v0.8-daily-replay` and HEAD/tree `c6e06ac5331b2f056534efa58756383e587ec27e` / `e5ae14c7d4da34f83afb32e5d83c06bc30471167`; it creates no authorization and performs no provider HTTP, Phase44, GET, implementation, test implementation, staging, commit, or push.

Future execution is closed to four paths: create `scripts/simulation/nar_race_entry_status_source_profile_fixture_consumer.py` and `tests/test_nar_race_entry_status_source_profile_fixture_consumer.py`, then modify only the two phase-control documents. Any fifth path is `PHASE85_APPROVED_CONTRACT_SUPPORT_MISMATCH`. Existing V3 fixtures, contract/plan/Profile-A/Profile-B/Phase66/Phase50, historical/replay/snapshot code, database, logs, and `.gitattributes` are forbidden.

The approved API accepts only an exact `NARRaceEntryStatusRaceIdentity` for `NAR / 21 / 2025-01-01 / 6` and an explicit, absolute, existing, NUL-free concrete `Path` repository root. It returns the frozen/slotted `NARRaceEntryStatusSourceProfileFixtureBundleV3` containing exactly target, Deba bytes, RaceList bytes, manifest bytes, validated manifest, Phase66 ancestry, V3 publication plan, and the ordered tuple `(EXPECTED_DEBA_TABLE_PATH_V3, EXPECTED_RACE_LIST_PATH_V3, EXPECTED_MANIFEST_PATH_V3)`. Profile and safety objects remain accessible only through the validated manifest authority.

The target directory is closed to exactly `deba_table.html`, `race_list.html`, and `manifest.json`; no glob, version scan, V1/V2 fallback, arbitrary path, link/reparse redirect, path escape, or unstable replacement is accepted. Each artifact is binary-read once with before/opened-handle/after identity checks. Strict manifest parsing, metadata reconstruction, raw-to-manifest validation, existing Profile-A/Profile-B/Safety/FixtureSet/Qualification/Manifest/Plan/Phase66 recomputation, canonical-manifest equality, and only then frozen Phase83 SHA/length and FixtureSet/Qualification identity checks are mandatory. This preserves independent formal-authority failure gates.

The semantic firewall remains fixed: current acquisition concerning a historical target only; market, positive-market, and whole-meeting-cancellation eligibility are `UNSUPPORTED`. The consumer cannot expose historical availability/bytes, replay readiness, or market eligibility, and cannot import or invoke network/provider/Phase44/subprocess/socket/DB/snapshot/replay authority.

Focused consumer, committed-V3, V3 contract/plan, Profile-A, Profile-B diagnostics, Phase66, and full-suite tests are required. They must cover the approved target/type/path/filesystem/manifest/raw/identity/semantic mutations, no-fallback behavior, bundle immutability, static forbidden imports, CWD independence, and committed-fixture identity before and after test execution. All mutations use temporary repository-shaped copies.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Modified paths are only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`; staging, commit, and push remain `NONE / NONE / NONE`.

Next action: `EXECUTE_APPROVED_PHASE`.

## POST_V0_8_DAILY_REPLAY_85 — PREPARE / DESIGN

**Status:** DRAFT_FOR_REVIEW
**Outcome:** READY_FOR_APPROVAL
**Design Contract:** STRICT_LOCAL_V3_SOURCE_PROFILE_FIXTURE_CONSUMER_CONTRACT_COMPLETE

Phase85 preparation freezes `PHASE84_REPLAY_CONSUMER_DEPENDENCY_AUDIT_REVIEW_PASS` and the repository-evidenced primary dependency `V3_FIXTURE_CONSUMER_SUPPORT_REQUIRED`. It designs, but does not implement, the first production read-side for the exact committed target `NAR / 21 / 2025-01-01 / 6` at HEAD/tree `c6e06ac5331b2f056534efa58756383e587ec27e` / `e5ae14c7d4da34f83afb32e5d83c06bc30471167`.

The proposed exact API is `load_nar_race_entry_status_source_profile_v3_fixture(*, repository_root: Path, target: NARRaceEntryStatusRaceIdentity) -> NARRaceEntryStatusSourceProfileFixtureBundleV3`. It uses existing V3 publication path constants, accepts only the exact frozen target, closes the target fixture directory to exactly DebaTable/RaceList/manifest, rejects symlink/reparse/path escape or unstable file identity, and reads each artifact once without writes or normalization.

Manifest handling is strict UTF-8 canonical JSON with duplicate-key and non-finite-number rejection. The consumer reconstructs only existing capture metadata fields, checks raw SHA/length against the manifest, recomputes Profile-A v3, Profile-B v2, Safety v3, FixtureSetV3, QualificationV3, ManifestV3, PublicationPlanV3, and Phase66, then requires canonical manifest byte equality and the exact frozen Phase83 artifact/FixtureSet/Qualification identities. No self-consistent replacement fixture is accepted.

The immutable bundle is limited to target, the three exact byte payloads, validated `SourceProfileManifestV3`, Phase66 ancestry, V3 publication plan, and the exact three relative paths. Nested fixture-set, qualification, safety, and Profile-A/B authority remain reachable through the manifest rather than duplicated. The type is explicitly source-profile-scoped and cannot claim historical snapshot, replay readiness, or market eligibility.

Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; market, positive-market, and whole-meeting-cancellation eligibility remain `UNSUPPORTED`. The module is forbidden from importing/calling historical normalization, snapshot, replay, DB, provider, network, Phase44, subprocess, clock, randomness, environment, or CWD authority. Missing local content fails closed without fallback.

Future implementation is exactly four paths: create the consumer and its focused test, then modify the two phase docs. The focused contract covers deterministic valid load; exact target/version/path closure; filesystem substitution; all manifest/raw/identity/semantic contradictions; Profile-A/Profile-B/Safety/Phase66 failures; static forbidden-authority audit; CWD independence; and before/after committed-fixture byte identity. Related V3 contract/plan/diagnostic/Profile-A/Phase66 tests and the full suite remain required. Any fifth path or weakening of existing authority is a stop condition.

Readiness A–U: **YES**. Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Production implementation/tests: `NO / NO`. Staging/commit/push: `NONE / NONE / NONE`.

Next action: `CHATGPT_REVIEW_PHASE85_FIXTURE_CONSUMER_DESIGN`.

## POST_V0_8_DAILY_REPLAY_84 — PREPARE / AUDIT

**Status:** DRAFT_FOR_REVIEW
**Outcome:** READY_FOR_ARCHITECTURAL_REVIEW
**Audit:** POST_V3_PUBLICATION_REPLAY_CONSUMER_DEPENDENCY_AUDIT_COMPLETE

Phase84 audited the repository at HEAD/tree `c6e06ac5331b2f056534efa58756383e587ec27e` / `e5ae14c7d4da34f83afb32e5d83c06bc30471167` after `PHASE83_INTEGRATION_REMOTE_VERIFICATION_PASS`. The formally integrated V3 DebaTable, RaceList, manifest, and dedicated-test byte identities remain unchanged, as do FixtureSetV3 `nar-race-entry-status-source-profile-fixture-set-v3:11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225` and QualificationV3 `nar-race-entry-status-source-profile-qualification-v3:a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff`.

The audit found no production historical replay consumer that discovers or reads `tests/fixtures/nar_race_entry_status/source_profiles/*`. V3 is explicitly supported by the publication contract/plan, Phase50 journal authority, deterministic generator/preflight, and committed dedicated test. Those components validate or publish fixtures but do not provide a replay read side. The actual replay path—`run_nar_daily_replay` → `resolve_sqlite_nar_daily_evidence` → historical snapshot adapter—uses SQLite snapshot and official settlement-capture evidence and never discovers the V3 source profile.

The hypothetical no-network replay of `NAR / 21 / 2025-01-01 / 6` therefore stops at its first step: fixture discovery. Manifest validation exists only inside the dedicated test/reconstruction logic; no reusable consumer exposes a validated local bundle. External-to-internal identity binding, entry/status interpretation, causal snapshot completion, market odds, and official payout evidence are ordered later dependencies. The NAR source normalizer rejects cancellation/status rows as unsupported, `SourceRecordKind` has no entry-status member, and the snapshot builder requires explicit race-entry mapping, so unsupported history is not silently promoted or name-linked.

The single primary next blocker is `V3_FIXTURE_CONSUMER_SUPPORT_REQUIRED`.

The proposed Phase85 is a no-network, four-file implementation: create `scripts/simulation/nar_race_entry_status_source_profile_fixture_consumer.py` and `tests/test_nar_race_entry_status_source_profile_fixture_consumer.py`, and update the two phase-control docs. It should add only strict canonical V3 target/version discovery and immutable local-bundle validation using existing V3/Profile-A/Profile-B/Safety authority. It must reject V1/V2/unknown/fallback candidates and all byte/manifest/identity contradictions, preserve current-acquisition and `UNSUPPORTED` semantics, and perform no identity binding, status application, snapshot construction, market promotion, replay, database write, or network access.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Authorization: `NONE`. Production/tests/fixtures/.gitattributes were not changed; no staging, commit, or push occurred.

Next action: `CHATGPT_REVIEW_PHASE84_REPLAY_CONSUMER_DEPENDENCY_AUDIT`.

## POST_V0_8_DAILY_REPLAY_83 — INTEGRATION

**Formal Status:** READY_FOR_REVIEW
**State:** IMPLEMENTED_FOR_REVIEW
**Outcome:** READY_FOR_INDEPENDENT_INTEGRATION_REVIEW
**Integration:** V3_SOURCE_PROFILE_PUBLICATION_COMMITTED_AND_PUSHED
**Authorization:** NONE_REQUIRED_NO_NETWORK_INTEGRATION

Phase83 locally revalidated and integrated the exact independently reviewed Phase82 six-path publication delta without provider HTTP, Phase44, GET, acquisition, refetch, or artifact regeneration. Phase82 review remains `PHASE82_PUBLICATION_EVIDENCE_AND_DELTA_REVIEW_PASS`; its consumed authorization and historical evidence remain unchanged.

The four frozen artifacts passed pre-test and post-test byte-identity checks. Manifest V3 authority, dedicated-test UTF-8/LF/BOM/compile properties, the single V3 `.gitattributes` rule, and `text: unset` / `diff: unset` for both HTML fixtures all passed.

No-network tests passed in the approved order: dedicated V3 fixture `4`; generator `17`; preflight `17`; publication plan `45`; publication contract `49`; Profile-B diagnostics `38`; Profile-A `17`; Phase66 structural recovery `152`; Phase50 observability `367`; full repository suite `4387` plus `2841` subtests. The full-suite total is mechanically four above the Phase82 baseline because it includes the four dedicated V3 tests in addition to their separate step-1 execution.

The integration commit uses expected parent `0c3e7577c5df44ffeee2ff9339f10272193bc7de`, exact message `feat: publish qualified NAR V3 source-profile fixtures`, and exactly the four frozen artifacts plus the two phase-control docs. It is pushed normally to `origin/feature/post-v0.8-daily-replay`; no broad staging, amend, reset, rebase, or force push is permitted.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; market, positive-market, and whole-meeting-cancellation eligibility remain `UNSUPPORTED`.

Next action: `CHATGPT_REVIEW_PHASE83_INTEGRATION`.

## POST_V0_8_DAILY_REPLAY_83 — APPROVE

**Formal Status:** APPROVED_FOR_CODEX
**Outcome:** APPROVED_NO_NETWORK_V3_PUBLICATION_INTEGRATION
**Design Review:** PHASE83_INTEGRATION_DESIGN_REVIEW_PASS
**Authorization:** NONE_REQUIRED_NO_NETWORK_INTEGRATION

This is local contract approval only: it creates no approval-tracking commit because the final Phase83 integration commit must retain parent `0c3e7577c5df44ffeee2ff9339f10272193bc7de` and contain the exact reviewed six-path delta. The four CREATE_ONLY artifacts remain byte-frozen; the two documentation files remain phase-control mutable only. No Phase82 evidence is changed.

Future execution must first revalidate the four frozen bytes, manifest authority, generated-test compilation, HTML attributes, and the specified ten no-network test stages. It may stage only the four artifacts and these two documentation files individually, make exactly one commit with message `feat: publish qualified NAR V3 source-profile fixtures`, then push normally to `origin/feature/post-v0.8-daily-replay`. `git diff --check` is authoritative only by zero return code; stderr is diagnostic evidence. A post-commit push failure preserves the exact local commit as `LOCAL_PHASE83_PUBLICATION_COMMIT_PUSH_PENDING_REVIEW`.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Staging / commit / push: `NONE / NONE / NONE`. No provider access, Phase44, GET, acquisition, refetch, artifact regeneration, or production-support change is approved.

Next action: `EXECUTE_APPROVED_PHASE`.

## POST_V0_8_DAILY_REPLAY_83 — PREPARE

**Status:** DRAFT_FOR_REVIEW
**Outcome:** READY_FOR_APPROVAL
**Design Contract:** NO_NETWORK_V3_PUBLICATION_INTEGRATION_CONTRACT_COMPLETE

Phase83 prepares only no-network integration of the independently reviewed Phase82 publication delta. The path set remains exactly six paths: four byte-frozen CREATE_ONLY artifacts and two phase-control-mutable documentation files. The artifact bytes were re-read without mutation and match the frozen Phase82 values: Deba `313317` / `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`; RaceList `66307` / `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`; manifest `4254` / `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d`; dedicated test `10467` / `a7339350be7e0724bd75408534a094c544bf6776eb57118e70ae6dd314e7b3ff`.

The manifest is strict UTF-8 and canonical; it confirms target `NAR / 21 / 2025-01-01 / 6`, `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, market eligibility `UNSUPPORTED`, FixtureSetV3 `nar-race-entry-status-source-profile-fixture-set-v3:11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225`, and QualificationV3 `nar-race-entry-status-source-profile-qualification-v3:a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff`. The generated test remains UTF-8, LF-only, BOM-absent, and compilable. Both V3 HTML paths have `text: unset` and `diff: unset`.

Phase82 remains `READY_FOR_REVIEW` with review `PHASE82_PUBLICATION_EVIDENCE_AND_DELTA_REVIEW_PASS`, permanently consumed external authorization `PHASE82_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`, Phase50 `CONSUMED_CONFIRMED`, and semantic `V3_SOURCE_PROFILE_PUBLICATION_DELTA_READY_FOR_CHATGPT_REVIEW`. It must never reacquire or publish again.

Future Phase83 execution is constrained to local artifact validation; the ten specified no-network suites; exact six-path staging; one commit with parent `0c3e7577c5df44ffeee2ff9339f10272193bc7de` and message `feat: publish qualified NAR V3 source-profile fixtures`; then a normal push to `origin/feature/post-v0.8-daily-replay`. No HTTP, provider access, Phase44, GET, reacquisition, refetch, regeneration, production-support change, or `.gitattributes` change is permitted. `git diff --check` is PASS on return code zero; stderr is diagnostic only. A push failure after commit retains the exact local commit in `LOCAL_PHASE83_PUBLICATION_COMMIT_PUSH_PENDING_REVIEW` without reset, amend, or reacquisition.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Staging / commit / push: `NONE / NONE / NONE`. Historical market, positive-market, and whole-meeting-cancellation eligibility remain `UNSUPPORTED`; no historical availability inference is permitted.

Next action: `CHATGPT_REVIEW_PHASE83_INTEGRATION_DESIGN`.

## POST_V0_8_DAILY_REPLAY_82 — LIVE PUBLICATION

State: READY_FOR_REVIEW

Phase50 Outcome: READY_FOR_REVIEW

External Authorization: `PHASE82_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`

Phase50 Authorization: `CONSUMED_CONFIRMED`

Semantic: `V3_SOURCE_PROFILE_PUBLICATION_DELTA_READY_FOR_CHATGPT_REVIEW`

Phase82 completed a fresh current one-Phase44/two-GET acquisition, same-byte qualification and publication, dedicated test generation through the reviewed Phase79 renderer, all ten regression stages, and the corrected exit-status-based Git success audit. The exact six paths remain unstaged for independent review; commit and push are `NO / NO`.

FixtureSetV3: `nar-race-entry-status-source-profile-fixture-set-v3:11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225`. QualificationV3: `nar-race-entry-status-source-profile-qualification-v3:a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff`. Manifest SHA/length: `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d` / `4254`. Generated test SHA/length: `a7339350be7e0724bd75408534a094c544bf6776eb57118e70ae6dd314e7b3ff` / `10467`.

Profile-B v2 and Profile-A v3 are QUALIFIED; Safety v3 is SAFE; structural consistency passed. Market eligibility, positive market eligibility, and whole-meeting cancellation remain UNSUPPORTED. No historical inference is permitted.

Next action: `CHATGPT_REVIEW_PHASE82_PUBLICATION_EVIDENCE_AND_DELTA`.

## POST_V0_8_DAILY_REPLAY_82 — APPROVE

**Formal Status:** APPROVED_FOR_CODEX

**Outcome:** APPROVED_FRESH_V3_PUBLICATION_WITH_CORRECTED_GIT_SUCCESS_AUDIT

**Design Review:** PHASE82_PUBLICATION_DESIGN_REVIEW_PASS

**Authorization Tracking State:** APPROVED_UNCONSUMED_TRACKED

**Authorization:** `PHASE82_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED`

This docs-only approval tracks the one-shot Phase82 authorization after successful creation and normal push of this tracking commit. It binds only to executable support `321868ac827677700da2c2ec41fded860eb464cc` / `0c422b45118131b8e3bb8ce5dd7189f2368e683e`, target `NAR / 21 / 2025-01-01 / 6`, purpose `FRESH_CURRENT_V3_SOURCE_PROFILE_PUBLICATION_WITH_CORRECTED_GIT_SUCCESS_AUDIT`, and `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET` semantics.

The authorization is `APPROVED_UNCONSUMED_TRACKED`; the boundary is **NOT WRITTEN** and authorization consumption is **NO**. Its permanent post-boundary state remains `PHASE82_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. This does not execute Phase82, perform provider HTTP, enter Phase44, perform GET, acquire, publish, or alter executable support.

The final Git audit is authoritative solely by `git diff --check` process return code: zero is PASS and nonzero is FAIL. Stdout/stderr are bounded diagnostic evidence only; an LF/CRLF conversion warning on stderr cannot override zero status. Future execution must pass the four classifier cases and the actual clean-baseline return-code gate before its real boundary, then audit the exact six-path unstaged success delta before review.

Phase79 actual isolated pytest preflight and every Phase80 safety, identity, same-byte, qualification, request-cap, regression-order, and rollback gate remain mandatory. The dedicated V3 fixture test runs exactly once as regression step 1. Phase80 remains terminal consumed/rollback-complete with its proven final-audit-runner defect; Phase81 remains `NOT_ENTERED_NO_PUBLICATION_DELTA`; a successful Phase82 delta requires later Phase83-or-later no-network integration.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Boundary: `NOT WRITTEN`. Publication: `NO`. Only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md` are changed by approval tracking.

Next action: `INDEPENDENT_REMOTE_VERIFICATION_BEFORE_PHASE82_EXECUTE`.

## POST_V0_8_DAILY_REPLAY_82 — PREPARE

**Status:** DRAFT_FOR_REVIEW

**Outcome:** READY_FOR_APPROVAL

**Design Contract:** V3_PUBLICATION_WITH_CORRECTED_GIT_SUCCESS_AUDIT_CONTRACT_COMPLETE

Phase82 preparation is documentation-only. Provider HTTP / Phase44 / GET were `0 / 0 / 0`; no authorization was issued; no synthetic or live execution, publication, staging, commit, or push occurred.

The worktree/branch is `C:\Users\garim\Desktop\KeibaOS-post-v0.8` / `feature/post-v0.8-daily-replay`; tracking HEAD/tree is `d54676e5c4e568bbc883d1a119dd632c653c1526` / `ae9baf3edfedc5c78eb35b03132903ca9d17530e`; executable support remains `321868ac827677700da2c2ec41fded860eb464cc` / `0c422b45118131b8e3bb8ce5dd7189f2368e683e`.

Phase80 is frozen `TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE` with review `PHASE80_CONSUMED_BLOCKED_RESULT_REVIEW_PASS_WITH_FINAL_AUDIT_RUNNER_DEFECT`; its authorization remains permanently consumed. The proven cause was `GIT_DIFF_CHECK_ZERO_EXIT_WITH_EOL_WARNING_STDERR_MISCLASSIFIED_AS_FAILURE`: `git diff --check` exited zero, but CRLF/LF conversion warnings on stderr were incorrectly treated as failure. The bounded error-message digest is `ca4d4fc7d257fdf647d7a7f7653c66e459cec40b46327221e5ec9ac02d5b331a`.

All Phase80 qualification and regression evidence remains frozen PASS: Phase79 preflight, dedicated fixture test, generator, preflight, plan, contract, Profile-B, Profile-A, Phase66, Phase50, and full suite (`4383 passed`, `2841 subtests`). The failure is not attributed to fixtures, manifest, renderer, dedicated test, contracts, profile checks, Safety v3, Phase50, or regressions. Phase81 remains `NOT_ENTERED_NO_PUBLICATION_DELTA` and is not repurposed.

Phase82 corrects only final Git success-audit semantics. `git diff --check` passes if and only if its return code is zero. Stderr is bounded diagnostic evidence, not a pass/fail override. The frozen future runner must self-test zero/nonzero classifier cases, pass a clean-baseline exit-status gate, and retain command/stream/path-set evidence before a genuine final-audit rollback.

The Phase79 isolated actual-pytest gate, import and support isolation, exact LF/frozen-runner parity, CREATE_ONLY/gitattributes, V3 authority, Phase50, Profile-B, Phase63/66, Safety, Profile-A, capture-metadata, same-byte, no-network, and rollback gates remain mandatory. Phase82 defines but does not issue `PHASE82_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED`; future success remains an exact six-path unstaged delta and requires later Phase83-or-later no-network integration after review.

Readiness A through U: **YES**. Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET` with market, positive-market, and whole-meeting-cancellation eligibility `UNSUPPORTED`.

Modified paths: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`. Staged/untracked: empty / empty. Next action: `CHATGPT_REVIEW_PHASE82_PUBLICATION_DESIGN`.

## POST_V0_8_DAILY_REPLAY_80 — TRACKING CORRECTION

**State:** AUTHORIZATION_TRACKING_CORRECTED_FOR_REMOTE_REVIEW

Independent remote review reported `PHASE80_AUTHORIZATION_STATE_REMOTE_VERIFICATION_BLOCKED_STALE_READINESS_E`. The current-authority Readiness E stale PREPARE wording was corrected to: `E. Phase80 authorization issued and tracked as APPROVED_UNCONSUMED_TRACKED; boundary not crossed and authorization remains UNCONSUMED.` Historical PREPARE records remain unchanged.

The same token remains `PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED` with tracking state `APPROVED_UNCONSUMED_TRACKED`. Boundary: **NOT WRITTEN**. Authorization consumed: **NO**. Provider HTTP / Phase44 / GET: **0 / 0 / 0**. Synthetic/live execution: **NOT RUN**. Publication: **NO**.

The executable support binding remains HEAD `321868ac827677700da2c2ec41fded860eb464cc`, tree `0c422b45118131b8e3bb8ce5dd7189f2368e683e`; this docs correction does not rebind authorization or change executable support.

Next action: `INDEPENDENT_REMOTE_VERIFICATION_BEFORE_PHASE80_EXECUTE`.

## POST_V0_8_DAILY_REPLAY_80 — APPROVE

**Formal Status:** APPROVED_FOR_CODEX
**Outcome:** APPROVED_FRESH_V3_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT
**Design Review:** PHASE80_PUBLICATION_DESIGN_REVIEW_PASS_WITH_REGRESSION_ORDER_CORRECTION
**Design Contract:** V3_FRESH_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT_CONTRACT_COMPLETE

This approval records a docs-only executable contract for branch `feature/post-v0.8-daily-replay`, executable support HEAD `321868ac827677700da2c2ec41fded860eb464cc`, tree `0c422b45118131b8e3bb8ce5dd7189f2368e683e`, and target `NAR / 21 / 2025-01-01 / 6` under `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET` semantics.

The Phase80 authorization is issued only after this exact approval contract is committed in the two documentation files, normally pushed, and local HEAD equals remote-tracking HEAD. Upon those conditions it is `PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED` with tracking state `APPROVED_UNCONSUMED_TRACKED`; it is one-shot, phase/target/purpose/support-specific, nontransferable, and permanently changes to `PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED` only after the durable real boundary. The approval commit is tracking evidence only; its executable support remains the stated Phase79 commit.

The Phase79 end-to-end preflight remains mandatory before any live boundary: the committed preflight must produce `V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS` through actual isolated `python -I -B` generated pytest, PEP 420 and module-origin isolation, and an external mirror. It must perform Provider HTTP / actual Phase44 / GET equal to `0 / 0 / 0`. The existing profile, safety, observability, plan, V3 contract, attribute, create-only, metadata, identity, runner-parity, LF, and clean-baseline gates remain mandatory.

Future Phase80 uses exactly four CREATE_ONLY paths (V3 Deba, RaceList, manifest, and dedicated test) and the two documentation paths as MODIFY_EXISTING. It writes no Git index entries, commit, or push during live execution. The sole renderer is the committed Phase79 `render_nar_race_entry_status_source_profile_v3_fixture_test`; the same newly acquired bytes must flow through all diagnostics, V3 authority construction, renderer input, and fixture writes. The sole boundary is durable `PHASE44_CALL_ABOUT_TO_ENTER`; request caps are one Phase44 and two GETs, Deba then RaceList.

Correction applied: the dedicated V3 fixture test runs **exactly once**, as regression step #1. The exact order is dedicated V3 fixture test; generator tests; preflight tests; publication-plan tests; publication-contract tests; diagnostics tests; Profile-A tests; Phase66 structural-recovery tests; Phase50 observability tests; then the full suite. Dedicated-test failure retains and durably validates bounded source/manifest/hash/identity/pytest evidence before rollback. Any later regression failure retains bounded command/result evidence before rollback. No raw HTML is diagnostic evidence.

Phase76 remains `TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE` with permanently consumed authorization and `UNKNOWN_AFTER_BOUNDED_EVIDENCE_GAP`; Phase78 remains `NOT_ENTERED_NO_PUBLICATION_DELTA`; Phase79 is formally complete with `PHASE79_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`. Market eligibility, positive market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`; fixture existence does not establish historical availability.

This approval performed Provider HTTP / Phase44 / GET: **0 / 0 / 0**. Authorization consumed: **NO**. Publication: **NO**. Synthetic/live preflight: **NOT RUN**. No production/test changes were made.

Next action after a successful tracking push: `INDEPENDENT_REMOTE_VERIFICATION_BEFORE_PHASE80_EXECUTE`.

## POST_V0_8_DAILY_REPLAY_80 — PREPARE

**Status:** DRAFT_FOR_REVIEW
**Outcome:** READY_FOR_APPROVAL
**Design Contract:** V3_FRESH_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT_CONTRACT_COMPLETE

Phase80 is a documentation-only preparation for a new one-shot fresh-current V3 source-profile publication transaction. It is bound in design, but not authorization, to branch `feature/post-v0.8-daily-replay`, executable support HEAD `321868ac827677700da2c2ec41fded860eb464cc`, tree `0c422b45118131b8e3bb8ce5dd7189f2368e683e`, and target `NAR / 21 / 2025-01-01 / 6` under `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET` semantics.

Frozen history:

- Phase76: `TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE`; review `PHASE76_CONSUMED_BLOCKED_RESULT_REVIEW_PASS`; authorization permanently `PHASE76_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`; blocker `REGRESSION_FAILURE_AT_DEDICATED_V3_FIXTURE_TEST`; exact cause `UNKNOWN_AFTER_BOUNDED_EVIDENCE_GAP`.
- Phase78: `NOT_ENTERED_NO_PUBLICATION_DELTA`; it is not reused or repurposed.
- Phase79: `FORMALLY_COMPLETE`; verification `PHASE79_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`; support `V3_DEDICATED_FIXTURE_TEST_EXECUTION_AND_FAILURE_EVIDENCE_AUTHORITY_IMPLEMENTED`.

The future, unissued authorization is `PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED`, bound only to Phase80, the stated target, purpose `FRESH_CURRENT_V3_SOURCE_PROFILE_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT`, and the reviewed Phase79 support. After the sole durable `PHASE44_CALL_ABOUT_TO_ENTER` boundary is appended, flushed, and fsynced, it permanently becomes `PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. Phase50 reconstruction remains a separate state domain and reports `CONSUMED_CONFIRMED` only after `PHASE44_FUNCTION_ENTERED`.

Before any future boundary, Phase80 must obtain `V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS` using the exact committed Phase79 preflight support: an external synthetic mirror, actual generated pytest, `python -I -B`, PEP 420 namespace and production-origin isolation, and no Provider HTTP, actual Phase44, or GET. Its bounded evidence must include generated-source and manifest hashes/lengths, command and return code, sanitized process output, and import-isolation result. The complete historical Phase76 gates remain required as well: publication-plan and V3-contract dry runs, Phase50 V3 test-path and blocked-payload integration, Profile-B/Phase73, Profile-A, Safety, Phase71 target contract, exact metadata, closed-bundle identity, runner parity, gitattributes, create-only absence, clean baseline, and LF preflight.

The only planned future delta remains six paths: CREATE_ONLY Deba HTML, RaceList HTML, manifest, and dedicated V3 fixture test under `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/`, plus the two current documentation files as MODIFY_EXISTING. The V3 `.gitattributes` binary rule is validate-only and must be present exactly once. The four CREATE_ONLY targets must be absent before a boundary.

Future live execution must call only the committed Phase79 renderer `render_nar_race_entry_status_source_profile_v3_fixture_test`; no inline or duplicate template is permitted. Exactly one Phase44 and two GETs are allowed, DebaTable then RaceList. The same acquired bytes must supply every diagnostic, V3 authority object, renderer input, and raw fixture write. Publication follows only complete Profile-B v2, Safety v3, Profile-A v3, identity, metadata, and V3 authority validation.

The dedicated V3 test runs before broader regressions. If it fails, `build_v3_fixture_test_failure_evidence` and `retain_v3_fixture_test_failure_evidence_durably` must preserve and validate bounded source/manifest/identity/hash/pytest diagnostic evidence before `ROLLBACK_BEGIN`; raw HTML is never retained. A successful Phase80 leaves the exact six-path unstaged delta for independent review, with no staging, commit, or push. A post-publication failure rolls back only those six paths to the clean Phase80 pre-live baseline. A later new no-network Phase81-or-later phase, not Phase78, may perform Git integration after review.

Readiness A–U: **YES**. The design fixes support identity, a new unissued authorization, preflight, closed paths, attributes, one-shot boundary and request caps, same-byte qualification, renderer-only generation, failure-before-rollback evidence, exact review delta, rollback, future integration, and historical non-inference. Market eligibility, positive market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`.

This PREPARE activity performed Provider HTTP / Phase44 / GET: **0 / 0 / 0**. Authorization issued: **NONE**. Publication: **NO**. No tests, staging, commit, or push were performed.

Next action: `CHATGPT_REVIEW_PHASE80_PUBLICATION_DESIGN`.

## POST_V0_8_DAILY_REPLAY_79 — IMPLEMENTED

**State:** IMPLEMENTED_FOR_REVIEW
**Outcome:** READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW
**Support:** V3_DEDICATED_FIXTURE_TEST_EXECUTION_AND_FAILURE_EVIDENCE_AUTHORITY_IMPLEMENTED

Implementation is confined to the approved six paths. The pure renderer implements `render_nar_race_entry_status_source_profile_v3_fixture_test(*, deba_table_bytes, race_list_bytes, manifest, publication_plan) -> bytes`, exact V3 type/authority and raw-byte validation, portable local-only generated tests, and the 65536-byte source limit.

The preflight constructs deterministic qualified synthetic authority with Phase63/Phase66 counts 2 / 2, direct schedule 1, changeInfo 1, and structural consistency 1 == 1. It writes only to a temporary external mirror, runs the generated test through `python -I -B` and actual pytest, validates the sole PEP 420 namespace and all module origins, disables ambient plugin/PYTHONPATH influence, and cleans the mirror.

Actual preflight result:

- Gate: V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS.
- Generated pytest tests: 4 passed; return code 0.
- Import isolation: PASS.
- Generated source SHA/length: `447535319ad465f44df2fd1e03cab6988d284ea5431e9badc01454e3de7264ef` / 10462.
- Manifest SHA/length: `0be206f04b8a7a4a6bffa3bc83e6eb8527a034870ecf82366b995f8be338eb46` / 4247.
- Command identity: `phase79-pytest-command-v1:db816856de1217bc1e9ea068fd4724be62baed2e09df19931dbe4ecd664725db`.
- Process output used Phase50 sanitization; stdout was bounded/redacted with full digest/length and stderr was EMPTY.

The focused suite proves exact-type/V2/dict/duck rejection, raw hash/length consistency, formal authority rejection, repeatable UTF-8 LF-only compilable output, nine actual-pytest mutations, missing/alternate/import-origin/namespace fail-closed behavior, no provider-network calls, bounded manifest retention, safe failure-node extraction, and durable exclusive-write/flush/fsync/readback evidence before rollback.

Final required test counts:

- generator 17 passed
- preflight 17 passed
- publication plan 45 passed
- publication contract 49 passed
- Profile-B diagnostics 38 passed
- Profile-A 17 passed
- Phase66 structural recovery 152 passed
- Phase50 observability 367 passed
- full suite 4383 passed, 2841 subtests passed

Phase76 remains TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE with cause UNKNOWN_AFTER_BOUNDED_EVIDENCE_GAP. Phase78 remains NOT_ENTERED_NO_PUBLICATION_DELTA. Provider HTTP / Phase44 / GET are 0 / 0 / 0; authorization is NONE; publication is NO. A future Phase80-or-later live phase requires a new reviewed one-shot authorization and the committed preflight gate.

Next action: `CHATGPT_REVIEW_PHASE79_IMPLEMENTATION`.

## POST_V0_8_DAILY_REPLAY_79 — APPROVE

**Formal Status:** APPROVED_FOR_CODEX
**Outcome:** APPROVED_V3_DEDICATED_FIXTURE_TEST_HARDENING_IMPLEMENTATION
**Design Review:** PHASE79_DEDICATED_TEST_HARDENING_DESIGN_REVIEW_PASS

The executable contract is recorded for branch `feature/post-v0.8-daily-replay`, base commit `e1e176291e0a79ad79f807c64b35d67da4851469`, and base tree `d2d1593adfa95835ed59d37cb0e35f33945e118b`. The future execution scope is exactly the two new source modules, their two focused tests, and these two documents; all other paths are forbidden.

The approved renderer is `render_nar_race_entry_status_source_profile_v3_fixture_test(*, deba_table_bytes, race_list_bytes, manifest, publication_plan) -> bytes`. It validates exact V3 authority and raw-byte consistency, generates bounded portable UTF-8/LF source, and remains pure. The approved preflight runs the committed renderer against an external synthetic mirror through isolated `python -I -B` pytest with PEP 420/module-origin checks and bounded evidence retention before any future rollback.

Phase76 remains TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE with permanently consumed authorization and an UNKNOWN_AFTER_BOUNDED_EVIDENCE_GAP; Phase78 remains NOT_ENTERED_NO_PUBLICATION_DELTA. This approval performed no code/test implementation, tests, provider HTTP, Phase44, GET, authorization, publication, staging, commit, or push.

Next action: `EXECUTE_APPROVED_PHASE`.

## POST_V0_8_DAILY_REPLAY_79 — IMPLEMENTATION CONTRACT BLOCKED

Implementation did not start.

- Requested review: `PHASE79_DEDICATED_TEST_HARDENING_DESIGN_REVIEW_PASS`
- Requested state: `APPROVED_FOR_IMPLEMENTATION`
- Contract blocker: `PHASE79_EXECUTION_CONTRACT_NOT_APPROVED_FOR_CODEX`
- Current `docs/CURRENT_PHASE.md` status: `DRAFT_FOR_REVIEW`
- Current allowed scope remains the PREPARE-only two-document scope and explicitly forbids production/test implementation.
- The current phase document does not yet declare the approved Base Commit and Branch, exact six implementation Allowed Files, Forbidden Files, and Required Tests as an `APPROVED_FOR_CODEX` execution contract.
- The prepared renderer API also differs from the newly requested implementation API and must be resolved in the approved phase contract rather than inferred during implementation.
- No production code, tests, staging, commit, push, network, Phase44, GET, authorization, or publication activity occurred.

Required next action: approve/correct `docs/CURRENT_PHASE.md` using the repository workflow, then issue `EXECUTE_APPROVED_PHASE`.

## POST_V0_8_DAILY_REPLAY_79 — PREPARE

**Status:** DRAFT_FOR_REVIEW
**Outcome:** READY_FOR_APPROVAL
**Design contract:** V3_DEDICATED_FIXTURE_TEST_EXECUTION_AND_FAILURE_EVIDENCE_AUTHORITY_COMPLETE

Phase79 is documentation-only preparation. It performed no provider HTTP, Phase44, GET, acquisition authorization, reacquisition, publication, staging, commit, or push.

### Frozen Phase76 result

- Review: PHASE76_CONSUMED_BLOCKED_RESULT_REVIEW_PASS.
- Terminal semantic: TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE.
- Phase50 outcome: RECOVERY_PREFLIGHT_BLOCKED.
- External authorization is permanently PHASE76_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED; Phase50 reconstructed CONSUMED_CONFIRMED.
- Live evidence retained only: Phase44 1; Deba GET 1; RaceList GET 1; total GET 2; retry 0.
- Deba SHA/length: `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727` / 313317.
- RaceList SHA/length: `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1` / 66307.
- Profile-B v2 QUALIFIED; Safety v3 SAFE; Profile-A v3 QUALIFIED.
- FixtureSetV3 identity: `nar-race-entry-status-source-profile-fixture-set-v3:20d14faad781a11dddba49f364745d302365bc639f5092d82f255597f8e75a90`.
- QualificationV3 identity: `nar-race-entry-status-source-profile-qualification-v3:ca0a3022ade5cf661018b226f69e0bba3a88d747dd205838122d191cf4d7e2d9`.

The exact blocker was REGRESSION_FAILURE_AT_DEDICATED_V3_FIXTURE_TEST. Its cause is UNKNOWN_AFTER_BOUNDED_EVIDENCE_GAP: generated source, pytest output/node, and manifest SHA/length were unavailable after rollback. No cause or patch is inferred. PUBLICATION_BEGIN through DEDICATED_TEST_WRITTEN were reached, REGRESSIONS_PASS was not, and rollback completed. Phase78 is NOT_ENTERED_NO_PUBLICATION_DELTA.

### Proposed reviewed authority

Later implementation is expected to add a pure deterministic V3 test-source renderer at `scripts/simulation/nar_race_entry_status_source_profile_fixture_test_generator.py`, plus a separate no-network external-mirror/evidence harness at `scripts/simulation/nar_race_entry_status_source_profile_fixture_test_preflight.py`, focused tests, and documents. The renderer accepts exact `FixtureSetV3`, `QualificationV3`, and `SourceProfileManifestV3`, validates existing authority, derives canonical values, and returns canonical UTF-8 LF-only source bytes. It is pure: no filesystem writes, network, clock, environment lookup, randomness, subprocess, or provider access.

The renderer must derive requirements solely from `FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS_V3` and existing V3 fixture, qualification, manifest, and publication-plan authority. The generated portable test uses `Path(__file__)`, approved relative paths, and local files only.

### End-to-end and evidence plan

The required future `V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS` uses the same renderer as live publication in an external deterministic synthetic mirror and executes actual pytest. A deterministic `python -I -B` wrapper injects only reviewed KeibaOS support and validates PEP 420 `scripts` namespace and authority-module origins; it rejects ambient PYTHONPATH, KeibaAI, site-package shadows, and alternate worktrees. If this cannot be proven, stop with DESIGN_BLOCKED_IMPORT_ISOLATION_FOR_EXTERNAL_PYTEST.

Renderer tests will prove exact-type rejection, determinism, canonical source, compilation, and no time/random/environment influence. End-to-end mutation tests will prove failure for independently changed fixture bytes, manifest bytes, expected hash/length, target, fixture/qualification identity, and market eligibility.

Before a future rollback, bounded evidence must be retained and fsynced: safe generated source; source/fixture/manifest hashes and lengths; V3 identities; command/return-code; milestone; and safe bounded pytest diagnostics. Valid canonical V3 manifest bytes are retainable only when at most 16384 bytes because their reviewed schema contains metadata, identities, hashes, and lengths—not raw HTML, URLs, cookies, or credentials. Otherwise only a safe projection is retained and publication blocks pending review. Raw process streams are not retained wholesale: use digest, length, classification, conservative test-node extraction, and a mechanically safe excerpt only where permitted.

Phase79 has no authorization. A new one-shot Phase80 authorization is required after formal Phase79 review, and Phase80 must pass the end-to-end preflight before any live boundary. Historical non-inference remains fixed: market_eligibility, positive_market_eligibility, and WHOLE_MEETING_CANCELLATION are UNSUPPORTED.

### Readiness

Readiness A–U: YES. No blocker was identified for the design. The next action is CHATGPT_REVIEW_PHASE79_DEDICATED_TEST_HARDENING_DESIGN.

## Phase76 approval report

Phase: `POST_V0_8_DAILY_REPLAY_76`

State: `APPROVED_UNCONSUMED_TRACKED`

Authorization Tracking State: `APPROVED_UNCONSUMED_TRACKED`

Formal Status: `APPROVED_FOR_CODEX`

Design Review: `PHASE76_CORRECTED_PUBLICATION_DESIGN_REVIEW_PASS`

Outcome: `APPROVED_V3_PUBLICATION_DELTA_GENERATION`

Authorization: `PHASE76_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED`

Support HEAD/tree: `cd9a728d04aab69a2330ee7f23583318c1901386` / `ce7e18d940fac243766f24237b6cc54d956c94d0`

Approval Base HEAD: `cd9a728d04aab69a2330ee7f23583318c1901386`

Executable Support HEAD: `cd9a728d04aab69a2330ee7f23583318c1901386`

Executable Support Tree: `ce7e18d940fac243766f24237b6cc54d956c94d0`

The authorization is one-shot, phase/target/purpose/support-HEAD-specific, nontransferable, and permanently becomes `PHASE76_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED` only after durable Phase44 boundary evidence. Its external state is intentionally distinct from Phase50's reconstructed journal state: the expected normal run has external consumed fail-closed state and journal `CONSUMED_CONFIRMED` after observing `PHASE44_FUNCTION_ENTERED`.

Phase77 is `FORMALLY_COMPLETE` with `PHASE77_IMPLEMENTATION_REMOTE_VERIFICATION_PASS` and exact V3 dedicated-test-path support. Phase75 is `FORMALLY_COMPLETE` with its V3 publication-plan authority. Phase74 authorization remains permanently consumed fail-closed. The approved design retains the no-Git Phase76 publication delta and separate Phase78 integration model, all pre-live gates, exact six paths, same-byte authority/qualification/readback controls, rollback before completion, bounded evidence, and historical non-inference.

This APPROVE activity performed no provider HTTP, Phase44, GET, synthetic/live run, publication, boundary write, staging, commit, or push. Authorization consumed: `NO`. The only modified paths are the two Phase documents; staged and untracked remain empty.

Next permitted action: `INDEPENDENT_REMOTE_VERIFICATION_BEFORE_PHASE76_EXECUTE`.

---

## Phase76 corrected publication-design report

Phase: `POST_V0_8_DAILY_REPLAY_76`

Status: `DRAFT_FOR_REVIEW`

Outcome: `READY_FOR_APPROVAL`

Design Contract: `V3_PUBLICATION_DELTA_REVIEW_BEFORE_GIT_INTEGRATION_CONTRACT_COMPLETE`

Current support HEAD/tree: `cd9a728d04aab69a2330ee7f23583318c1901386` / `ce7e18d940fac243766f24237b6cc54d956c94d0`

Phase77 is `FORMALLY_COMPLETE` with `PHASE77_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`. Its exact Phase50 V3 dedicated-test path support resolves `PHASE50_V3_DEDICATED_TEST_PATH_ALLOWLIST_MISSING`; the corrected Phase76 binding is now support-HEAD-specific to the Phase77 commit. No Phase76 authorization has been issued.

The corrected transaction model is `PUBLICATION_DELTA_AND_GIT_INTEGRATION_SPLIT`: Phase76 creates and validates the exact six-path unstaged V3 publication delta, retains bounded evidence, and stops for independent review. It never stages, commits, or pushes. Phase78 later performs no-network integration. If a Phase78 commit succeeds but push fails, it preserves the immutable local commit as `LOCAL_PUBLICATION_COMMIT_PUSH_PENDING_REVIEW`; it never resets, amends, force-pushes, reacquires, or reruns Phase76.

Phase76 preserves all existing synthetic gates and adds the actual `PHASE50_V3_DEDICATED_TEST_PATH_INTEGRATION_PASS`, V3 plan/contract/template/rollback gates, exact attribute validation, and CREATE_ONLY absence gates. A future publication requires one durable authorization boundary, exactly one Phase44, ordered Deba/RaceList GETs capped at two, same-byte qualification and V3 object validation, readback verification, generated no-network dedicated test, and passing regressions. Any pre-commit publication failure rolls back only the six live paths.

Semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; market eligibility, positive market eligibility, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`. No historical inference is allowed.

Readiness A–U: `YES`. Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Authorization issued: `NONE`. Publication: `NOT PERFORMED`. Staged: empty. Untracked: empty.

Next recommended action: `CHATGPT_REVIEW_CORRECTED_PHASE76_PUBLICATION_DESIGN`.

---

## Phase77 implementation report

Phase: `POST_V0_8_DAILY_REPLAY_77`

State: `IMPLEMENTED_FOR_REVIEW`

Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`

Support Repair: `PHASE50_V3_DEDICATED_TEST_PATH_SUPPORT_ADDED`

Starting HEAD/tree: `c6522eacf46f03036e1171f14f634983c1f73479` / `e5df986b4788afb3a22507767767580ad399a880`

Phase76 is frozen `DESIGN_BLOCKED_ADDITIONAL_SUPPORT_REQUIRED`. Its primary blocker was `PHASE50_V3_DEDICATED_TEST_PATH_ALLOWLIST_MISSING`; the separate `PUBLICATION_COMMIT_PUSH_ROLLBACK_BOUNDARY_REQUIRES_DESIGN_CORRECTION` remains for the corrected later publication design. Before commit the live publication delta remains rollback-capable; after a successful commit, push failure must preserve the local commit and enter integration recovery rather than reset, amend, force, reacquire, or restart the publication transaction.

Phase50 now accepts exactly the historical V1 path, V2 path, and `tests/test_nar_race_entry_status_source_profile_v3_fixtures.py`. It rejects all malformed V3 variants and arbitrary paths. Journal schema `1`, milestone order, `{test_path}` detail shape, size limits, outcomes, authorization states, and existing V3 manifest identity-pair support are unchanged. A successful V3 publication journal using V3 fixture/qualification identities and the V3 dedicated path passes syntax, semantic validation, and reconstruction with publication begun and no rollback.

Verification: Phase50 `367 passed`; publication plan `45 passed`; publication contract `49 passed`; full repository `4349 passed, 2841 subtests passed`. Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Acquisition authorization: `NONE`. Publication authorization: `NONE`. Publication: `NO`.

Phase75 remains `FORMALLY_COMPLETE`; Phase74 authorization remains permanently consumed fail-closed. Market eligibility remains `UNSUPPORTED`; no historical inference is made.

Next permitted action: `CHATGPT_REVIEW_PHASE77_IMPLEMENTATION`.

---

## Phase76 publication preparation report

Phase: `POST_V0_8_DAILY_REPLAY_76`

Status: `DRAFT_FOR_REVIEW`

Outcome: `READY_FOR_APPROVAL`

Design Contract: `V3_FRESH_CURRENT_ACQUISITION_AND_PUBLICATION_CONTRACT_COMPLETE`

Worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`

Current support HEAD/tree: `c6522eacf46f03036e1171f14f634983c1f73479` / `e5df986b4788afb3a22507767767580ad399a880`

Phase75 is frozen `FORMALLY_COMPLETE` with `PHASE75_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`; its V3 publication-plan authority, exact six-path plan, closed FixtureSetV3 validation, `VALIDATE_ONLY` attribute policy, and tracked V3 binary rule are available. Phase74 remains final with permanently consumed Phase74 authorization; its raw bytes were cleaned and cannot be reconstructed or reused.

Preparation found no additional support gap. The exact four V3 CREATE_ONLY targets are absent, and the committed V3 `.gitattributes` rule is present. Phase76 reserves, but does not issue, `PHASE76_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED` bound only to `NAR / 21 / 2025-01-01 / 6`, purpose `FRESH_CURRENT_V3_SOURCE_PROFILE_ACQUISITION_AND_PUBLICATION`, current-acquisition semantics, and the current support HEAD. Its sole post-boundary state is permanent consumed fail-closed.

The reviewed future execution uses a one-time frozen external runner; namespace-package import isolation; complete synthetic qualification, Phase50 blocked-payload, V3 contract, test-template, rollback, attribute, and CREATE_ONLY absence gates; then exactly one Phase44 and at most two ordered GETs. It retains the same fresh raw bytes through all qualification and V3 authority construction. Only fully qualified same-byte evidence may reach `PUBLICATION_BEGIN`, raw fixture readback, manifest readback, deterministic dedicated test generation, documentation update, regression tests, six-path staging, commit, and normal push. Any post-publication failure rolls back exactly the six live paths and does not retry.

Current-acquisition semantics are preserved throughout: no historical bytes, provider availability, timing, cutoff, or market eligibility are inferred. `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`.

Readiness A–T: `YES`. Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Authorization issued: `NONE`. Publication: `NOT PERFORMED`. Staged: empty. Untracked: empty.

Next recommended action: `CHATGPT_REVIEW_PHASE76_PUBLICATION_DESIGN`.

---

## Phase75 implementation report

Phase: `POST_V0_8_DAILY_REPLAY_75`

State: `IMPLEMENTED_FOR_REVIEW`

Outcome: `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`

Support: `V3_SOURCE_PROFILE_PUBLICATION_PLAN_AUTHORITY_IMPLEMENTED`

The implementation adds additive, deterministic, fail-closed V3 publication-plan authority while preserving all V2 constants, types, paths, builders, validators, and tests. It introduces `SourceProfilePublicationPlanV3`, exact `FixtureSetV3` input validation, exact V3 NAR target/path authority, ordered six-role plans, future `VALIDATE_ONLY` gitattributes policy, exact rollback scope, and the frozen V3 fixture-test requirement tuple. V2 and V3 inputs and plan types cross-reject; the V3 plan has no independent identity.

The V3 HTML binary rule is now tracked exactly once: `tests/fixtures/nar_race_entry_status/source_profiles/v3/**/*.html -text -diff`; the V2 rule remains exactly once. The plan module remains pure: no network, subprocess, filesystem write, raw bytes, arbitrary URLs, or live acquisition capability.

Phase74 remains `FORMALLY_COMPLETE` with evidence review `PHASE74_VERSIONED_VALIDATION_EVIDENCE_REVIEW_PASS`; its authorization remains permanently consumed fail-closed. Raw V3 fixtures and manifests are `NOT_PUBLISHED`. Future publication requires a new one-shot authorization bound to the reviewed post-Phase75 support. Market eligibility remains `UNSUPPORTED`; no historical inference is made.

Verification completed: publication-plan tests `45 passed`; publication-contract tests `49 passed`; specified related diagnostics/Profile-A/Phase66/Phase50 regressions `562 passed`; full repository suite `4337 passed, 2841 subtests passed`. Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Acquisition authorization: `NONE`. Publication: `NO`.

Next permitted action: `CHATGPT_REVIEW_PHASE75_IMPLEMENTATION`.

---

## Phase75 preparation report

Phase: `POST_V0_8_DAILY_REPLAY_75`

Status: `DRAFT_FOR_REVIEW`

Outcome: `READY_FOR_APPROVAL`

Design Contract: `V3_SOURCE_PROFILE_PUBLICATION_PLAN_CONTRACT_COMPLETE`

Worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`

Starting tracking HEAD: `11e1aace4aae68640d0d38f88b38873d1bac5abd`

Validated executable support HEAD/tree: `b2355113f969f6af713a254355e67a9feab5cc45` / `24b4f37391039e1ece2d573b4a0ea3f0de65e4cd`

Phase74 is frozen `FORMALLY_COMPLETE` with evidence review `PHASE74_VERSIONED_VALIDATION_EVIDENCE_REVIEW_PASS`, outcome `READY_FOR_REVIEW`, and permanently consumed authorization `PHASE74_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. Its current-only Profile-B v2 `QUALIFIED`, Safety v3 `SAFE`, Profile-A v3 `QUALIFIED`, durable boundary, Phase44 `1`, total GET `2`, retry `0`, and no-publication result remain evidence only. Raw bytes are unavailable and must not be reconstructed or substituted.

Preparation confirmed that V3 contract authority already exists: exact `FixtureSetV3`, `QualificationV3`, `SourceProfileManifestV3`, `RawFixturePublicationSafetyV3`, their V3 builders/validators, deterministic V3 paths, semantics `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, and market eligibility `UNSUPPORTED`.

The existing publication plan is strictly V2-only: it accepts only exact `FixtureSetV2`, uses V2 fixture paths and requirements, and preserves Phase57 V2 authority. `.gitattributes` presently preserves only V2 source-profile HTML. A direct V3 publication is therefore not authorized.

The reviewed additive Phase75 implementation is limited to five paths:

1. `scripts/simulation/nar_race_entry_status_source_profile_publication_plan.py`
2. `tests/test_nar_race_entry_status_source_profile_publication_plan.py`
3. `.gitattributes`
4. `docs/CURRENT_PHASE.md`
5. `docs/LATEST_CODEX_REPORT.md`

It will retain every V2 type, constant, path, builder, validator, and golden behavior unchanged; add a distinct exact-FixtureSetV3 `Phase75PublicationPlan` with its V3 builder/validator; require the exact six V3 paths and ordered roles; add exactly `tests/fixtures/nar_race_entry_status/source_profiles/v3/**/*.html -text -diff`; and set future live `.gitattributes` behavior to `VALIDATE_ONLY`. The publication-plan module remains pure: no network, subprocess, database, clock, randomness, filesystem write, raw bytes, or arbitrary URLs.

V3 plan authority is fixed to `NAR / 21 / 2025-01-01 / 6`, with V3 Deba/RaceList/manifest paths under `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/`, dedicated test `tests/test_nar_race_entry_status_source_profile_v3_fixtures.py`, four `CREATE_ONLY` entries, and two documentation `MODIFY_EXISTING` entries. The future fixture-test requirements include exact hashes/lengths/target/roles; V3 fixture/qualification/manifest recomputation and validation; Safety-v3 SAFE; Profile-A-v3 and Profile-B-v2 qualification; all six Profile-B predicates; corrected Profile-B/Phase66 direct-schedule consistency; current-acquisition semantics; unsupported market eligibility; and no network.

Readiness A–R: `YES`. No additional support is required. Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Acquisition authorization issued: `NONE`. Publication: `NOT PERFORMED`. Staged: empty. Untracked: empty.

Next recommended action: `CHATGPT_REVIEW_PHASE75_PUBLICATION_PLAN_DESIGN`.

---

## Phase74 approval report

Phase: `POST_V0_8_DAILY_REPLAY_74`

State: `APPROVED_UNCONSUMED_TRACKED`

Authorization Tracking State: `APPROVED_UNCONSUMED_TRACKED`

Formal Status: `APPROVED_FOR_CODEX`

Design Review: `PHASE74_VALIDATION_DESIGN_REVIEW_PASS`

Outcome: `APPROVED_PROFILE_B_V2_REPAIRED_FRESH_CURRENT_VALIDATION`

Validation Contract: `PROFILE_B_V2_REPAIRED_FRESH_CURRENT_VALIDATION_CONTRACT_COMPLETE`

Authorization: `PHASE74_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_UNCONSUMED`

Worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`

Executable support HEAD/tree: `b2355113f969f6af713a254355e67a9feab5cc45` / `24b4f37391039e1ece2d573b4a0ea3f0de65e4cd`

Approval Base HEAD: `b2355113f969f6af713a254355e67a9feab5cc45`

### Authorization binding

This is a new Phase74 one-shot authorization, not a retry or reuse of Phase72. It binds to target `NAR / 21 / 2025-01-01 / 6`, purpose `FRESH_CURRENT_VALIDATION_AFTER_PHASE73_PROFILE_B_V2_REPAIR`, semantics `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, and the stated executable support HEAD. The reserved permanent consumed state is `PHASE74_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`.

At approval time: Provider HTTP / Phase44 / GET are `0 / 0 / 0`; synthetic and live execution are `NOT RUN`; the boundary is not written; and authorization is not consumed.

### Frozen authority

Phase73 is `FORMALLY_COMPLETE`, with `PROFILE_B_V2_CHANGEINFO_CLASS_TOKEN_REPAIRED` and review `PHASE73_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`.

Phase72 remains final: `POST_AUTHORIZATION_STOP` / `RECOVERY_PREFLIGHT_BLOCKED` / `PHASE72_VERSIONED_SOURCE_PROFILE_VALIDATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. Its durable boundary, one Phase44, two GETs, zero retry, no publication, and blocker `PROFILE_B_STRUCTURAL_CONSISTENCY` remain unchanged. It is permanently unusable.

### Future Phase74 controls

Only Profile-B v2 schema `2`, Profile-A v3 schema `3`, and Safety v3 schema `3` qualify Phase74. Phase50 retains journal schema `1`, supported nested schema versions, and the schema-3 Profile-A target/TARGET_CONSTRUCTED equality contract. Phase63 and Phase66 are supplemental only.

The synthetic success path must reproduce the Phase72 sibling schedule/changeInfo topology and prove: Profile-B v2 target count `1`, all six predicates `PASS`, `QUALIFIED`; Phase63 candidates `2`; Phase66 candidates `2`, direct schedule `1`, changeInfo `1`. Corrected structural consistency compares only Profile-B v2 count to the Phase66 direct-schedule count. It expressly does not compare against Phase63 or Phase66 total candidates.

Mandatory gates include `PHASE73_PROFILE_B_V2_CHANGEINFO_TOKEN_INTEGRATION_PASS`, `PHASE71_PROFILE_A_V3_TARGET_CONTRACT_INTEGRATION_PASS`, both blocked-v3 Phase50 probes, Profile-B/Profile-A/Safety dry-run gates, full Phase50 reconstruction, no-network proof, runner-byte parity, and capture metadata/bundle identity proof.

The hardened runner remains one generated external file with shared synthetic/live logic, fresh `-I -B` imports, KeibaAI exclusion, origin checks, and exact LF preflight bytes. The sole future boundary is durable `PHASE44_CALL_ABOUT_TO_ENTER`; caps remain Phase44 `1`, Deba GET `1`, RaceList GET `1`, total GET `2`, in order, with no retry/fallback/discovery.

Publication is prohibited. Safe-final is bounded; raw/provider artifacts are removed after parent validation. Current-byte matches remain `CURRENT_ACQUISITION_BYTES_REPRODUCED` only and do not establish historical availability, state, timing, cutoff, or market eligibility. Market eligibility remains `UNSUPPORTED`.

No production or test file changed in approval. No authorization was consumed.

Next permitted action: `TRACK_PHASE74_AUTHORIZATION_STATE_THEN_INDEPENDENT_REMOTE_VERIFICATION`.
