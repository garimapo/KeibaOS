# Current Phase

## POST_V0_8_DAILY_REPLAY_103

Title: NAR V2 Measurement Authority Foundation

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Audit: NAR_V2_MEASUREMENT_AUTHORITY_DESIGN_COMPLETE

Design Review: PHASE103_V2_MEASUREMENT_AUTHORITY_DESIGN_REVIEW_PASS

Implementation: NAR_V2_MEASUREMENT_CONFIG_SESSION_ACTIVATION_FOUNDATION_IMPLEMENTED

Authorization: POST_V0_8_DAILY_REPLAY_103 = APPROVED_FOR_IMPLEMENTATION

Base Commit and Branch: `703d429113e58ddfe721dd2c1ab1297d511a6ef5` / `feature/post-v0.8-daily-replay`

### Implementation result (pending independent verification)

The separate V2 configuration/session and stage/budget-role domains, controlled
two-artifact V2 activation, and exact same-database V2 authority companion are
implemented. The companion persists only V2 configuration, session, activation
declaration, and activation verification. It creates no runtime-binding,
campaign-execution, attempt, or terminal table. Phase99/100 canonical payloads,
identities, rows, and historical strict validators remain unchanged; narrow
compatible gates accept only the exact Phase103 union for existing repositories.
The migration performs no backfill. `V1_MEASUREMENT_AUTHORITY_REMAINS_IMMUTABLE` and
`V2_ATTEMPT_TERMINAL_PERSISTENCE_DEFERRED_PENDING_EXECUTION_PARENT` remain explicit.

Four new focused test files: 27 passed. Required Phase99/100, snapshot-freeze,
and Phase96/97 cutoff regression files: 66 passed. Full repository suite:
4,617 passed, 2 skipped, 2,846 subtests passed. No provider HTTP, live campaign,
production timing collection, or production database write occurred; in-memory
SQLite writes were used by tests. `PHASE102_RUNTIME_BINDING_IMPLEMENTATION_DEFERRED_PENDING_V2_AUTHORITY_CONTRACT`
remains pending independent verification, along with runtime source/configuration
proof, execution authority, and `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`.

Next: `CHATGPT_REVIEW_PHASE103_IMPLEMENTATION`.

### Historical Phase103 PREPARE contract

Allowed Files in PREPARE: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`.
Forbidden Files: all production code, tests, migrations, archive/database files,
and logs. Required Tests: none (static design audit); run `git diff --check` and
inspect Git status. Stop Condition: v2 ancestry needs a speculative parent,
existing v1 semantics would need reinterpretation, a non-document path needs
mutation, or baseline/scope differs.

### Phase102 reconciliation and primary finding

`PHASE102_CAMPAIGN_RUNNER_AND_RUNTIME_AUTHORITY_REVIEW_PASS`;
`POST_V0_8_DAILY_REPLAY_102 = ARCHITECTURAL_AUDIT_COMPLETE`;
`CRASH_NO_OFFICIAL_RESUME_CONTRACT = FROZEN`;
`PHASE102_V2_MEASUREMENT_AUTHORITY_EXTENSION_REQUIRED = CONFIRMED`; and
`PHASE102_RUNTIME_BINDING_IMPLEMENTATION_DEFERRED_PENDING_V2_AUTHORITY_CONTRACT = CONFIRMED`.
Phase101 remains architectural-audit complete and Phase100 remains formally complete
with `NAR_PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY = FORMALLY_INTEGRATED`.
The Phase102 material below is historical architectural audit.

Primary finding: `V2_CONFIG_SESSION_ACTIVATION_AUTHORITY_CAN_BE_FROZEN_NOW`, but
`V2_ATTEMPT_TERMINAL_PERSISTENCE_REQUIRES_PHASE104_EXECUTION_PARENT`. Phase103 must
freeze a new immutable authority family, not reinterpret Phase99/100. The safe
implementation boundary is configuration/session/activation only; attempt/terminal
tables wait until Phase104 creates their exact runtime-binding/campaign-execution
parents with restrictive foreign keys.

Freeze `V1_MEASUREMENT_AUTHORITY_REMAINS_IMMUTABLE`. Existing Phase99 v1
configuration, session, attempt, terminal and Phase100 v1 declaration/verification
types, canonical JSON, identities, archive rows, registries, and qualification
meanings are unchanged. No v1 class accepts schema version 2, no v1 identity migrates,
and no backfill/conversion exists. V1 and v2 are never interchangeable or silently
aggregated.

### V2 domains, identities, and canonical configuration

Use separate frozen/slotted types with independent explicit serialization; do not
inherit a v1 dataclass serializer. Public V2 identities are:

* `nar-operational-timing-config-v2:<sha256>`
* `nar-operational-timing-session-v2:<sha256>`
* `nar-operational-timing-activation-declaration-v2:<sha256>`
* `nar-operational-timing-activation-verification-v2:<sha256>`
* reserved `nar-operational-timing-attempt-v2:<sha256>`
* reserved `nar-operational-timing-terminal-v2:<sha256>`

Phase104 parent namespaces are frozen as
`nar-operational-timing-runtime-binding-v1:<sha256>` and
`nar-operational-timing-campaign-execution-v1:<sha256>`. Prefixes are exact and may
not substitute for one another even where human-readable fields coincide. All V2
payloads use NFC exact text, UTF-8, `ensure_ascii=False`, `allow_nan=False`, sorted
keys, compact separators, fixed-microsecond UTC datetime text, and SHA-256 of exact
canonical bytes.

`NAROperationalTimingMeasurementConfigurationV2` binds exactly: schema version 2;
repository identity; declared lowercase 40-hex software commit; NAR/nar_official
scope; instrumentation schema version 2; ordered nonempty closed V2 stage set;
canonical transport profiles; closed retry/backoff profile; closed concurrency regime;
sample-admission semantic version; and execution-authority semantic version. The
existing immutable low-level HTTP transport-profile, retry, and concurrency values
may be reused only where their exact semantics are unchanged. V2 has its own payload
writer/reader and configuration identity; it does not call v1 serialization.

### V2 stages and budget roles

V2 preserves the Phase99 acquisition/input operation boundaries: runner dispatch;
bootstrap home, monthly root, and locator-script acquisition; monthly schedule and
RaceList acquisition; official-response and market-odds acquisition; raw validation
and persistence; parsing; normalization; source-record construction; provider
identity binding; snapshot construction, persistence, and exact reload; snapshot
adapter; prediction pipeline; allocation; bet-plan construction/persistence; and
shadow artifact publication. Boundary meaning remains the existing production
operation, not a new provider semantic.

Add only Phase102-required boundaries with exact meanings:

* `CAMPAIGN_EXECUTION_PREPARATION`: controlled runner setup before it may publish
  official attempts; no provider call.
* `RUNTIME_BINDING_READINESS`: save/reload/verification work establishing Phase104
  runtime readiness; no provider call.
* `FREEZE_RECEIPT_CONSTRUCTION`: construction after snapshot save/commit and exact
  snapshot reload, preserving Phase99 `freeze_completed_at` semantics.
* `FREEZE_RECEIPT_PUBLICATION` and `FREEZE_RECEIPT_EXACT_RELOAD`: distinct receipt
  archive operations, never folded into snapshot persistence.
* `ATTEMPT_START_PUBLICATION` and `TERMINAL_PUBLICATION`: observability writes around
  an operation, not that operation's elapsed time.

Each stage has one wrapper/call boundary; no generic/free-text stage exists. Use a
closed V2 budget role separate from the stage name:
`PRE_C_FREEZE`, `FREEZE_PROVENANCE`, `OBSERVABILITY_OVERHEAD`, `POST_C_COMPUTE`, and
`CAMPAIGN_CONTROL`. `PRE_C_FREEZE` is always part of the future pre-C envelope.
`FREEZE_PROVENANCE` enters it whenever strict official qualification requires the
receipt. Synchronous pre-call attempt publication is mandatory overhead and must be
included in the operational budget; terminal publication is separately measured and
does not automatically become a pre-C condition. `POST_C_COMPUTE` is excluded from
Delta unless a later action-deadline contract says otherwise. `CAMPAIGN_CONTROL` is
reported separately; this classification defines no aggregation arithmetic by itself.

### Session, activation, attempt, and terminal contracts

`NAROperationalTimingMeasurementSessionV2` retains exact fixed-window semantics:
aware UTC, canonical fixed-microsecond text, `measurement_start_at <
measurement_end_at`, closed fixed-wall-clock completion, and the half-open rule.
Its V2 `attempt_admitted_at` explicitly means
`MEASUREMENT_ATTEMPT_ADMISSION_TIMESTAMP`: sampled before durable attempt publication
and before callable entry. Membership is exactly `start <= attempt_admitted_at < end`.
An admitted attempt remains a member even when publication or callable entry finishes
after the window; failures/timeouts remain in the denominator. No adaptive completion
or success-count rule is allowed.

V2 activation is a separate two-artifact chain. A timestamp-free declaration binds
only exact V2 session/configuration and a closed declaration semantic; it is
saved/reloaded before a controlled UTC sample. A verification receipt binds exact
declaration/session/configuration, closed verification semantic, and that sampled
time, then is saved/reloaded. One declaration per V2 session and one verification per
declaration are enforced; exact retry reuses an existing receipt, while a
declaration-only retry samples current time and never reconstructs/backdates it.
Official predeclaration requires verification time no later than session start.
`SESSION_IDENTITY != PRE_MEASUREMENT_ACTIVATION_AUTHORITY` and
`ACTIVATION_DECLARATION_IDENTITY != VERIFIED_PRESTART_ACTIVATION_AUTHORITY` remain
true. A v1 activation cannot activate a V2 session.

The future V2 attempt is content-addressed from exact V2 session/configuration,
**required** campaign-execution identity, stage, schema-independent exact correlation,
attempt sequence, `attempt_admitted_at`, and closed load context.
`V2_ATTEMPT_REQUIRES_CAMPAIGN_EXECUTION_ANCESTRY`. It does not redundantly store the
runtime-binding identity: strict ancestry is attempt → execution claim → runtime
binding, and the future database FK chain plus reload validation detect contradictions.
Correlation stays a provider/race/target-set/plan join only and grants no authority.
The existing `NARTimingCorrelation` can be reused unchanged because its payload does
not encode measurement version or authority; V2 must not extend it with detached
execution text. Existing closed load context can also be reused as an observation
(`active_target_workflows`, `active_http_requests`, `process_cold_start`), never as
self-asserted serial-concurrency authority.

The future V2 terminal binds one exact V2 attempt, causal finish UTC,
nonnegative exact elapsed microseconds, closed disposition, closed failure
classification, and optional produced-artifact content SHA. It includes no exception
text, outcome, payout, or ROI. Retain `SUCCESS`, `FAILURE`, `TIMEOUT`, and
`UNSUPPORTED`; add only V2 `INTERNAL` failure classification for unexpected internal
error. A clock-order failure is not backdated into a terminal; it leaves the attempt
unresolved under a separately surfaced clock failure. The pure V2 domain owns
`elapsed_microseconds_from_perf_counter_ns(start_ns, finish_ns)`: exact `int` inputs,
`finish >= start`, `(finish_ns - start_ns) // 1000`, no float, and sub-microsecond
duration equal to zero. Wrappers later own timer sampling and pass its result.

### Persistence boundary and Phase104 handoff

Choose architecture **A**: Phase103 persists only V2 configurations, V2 sessions,
V2 activation declarations, and V2 activation verification receipts in a new
same-database Phase103 V2-authority companion registry. It has independent exact DDL,
append-only records/triggers, restrictive configuration/session/declaration FKs,
exact reload, idempotent exact duplicates, conflict rejection, no backfill, and no
runtime/execution placeholders.

Do **not** create V2 attempt/terminal tables yet. A weak text
`campaign_execution_identity` without a Phase104 parent FK would require rebuilding
immutable tables later. Phase104 must first create exact runtime-binding, readiness,
and campaign-execution tables/identities; Phase105 then creates V2 attempt/terminal
tables with restrictive `campaign_execution_identity` and attempt-parent FKs. This
preserves the required ancestry without speculative writable authority tables.

The archive bootstrap state machine evolves only through exact union gates: empty →
Phase99 base v1 → Phase100 activation companion v1 → Phase103 V2 authority companion
→ Phase104 runtime/execution companion → Phase105 V2 observation companion. Existing
strict validators stay strict for the topology they own; a top-level bootstrap alone
recognizes exact extended unions. Unknown or partial objects always fail closed.

Official/diagnostic classification belongs to the future execution authority, not an
attempt `official=True` field. V2 attempts derive their classification from exact
archived execution ancestry; diagnostics use a distinct future execution authority
and are excluded from official Delta aggregation. Future aggregation requires exact
compatible V2 configuration identity or a separately reviewed compatibility rule;
stage-name comparison alone is insufficient.

Phase103 does not implement sealed source, process lock, runtime profile/binding,
readiness, execution claim, passive wrappers, HTTP, campaign execution, or Delta
selection. Phase104 consumes the persisted V2 parent identities in the strict chain:
V2 session → V2 activation verification → runtime binding → campaign execution claim.
Phase105 alone may add attempt/terminal persistence and passive wrapper composition.

Likely Phase103 paths: new V2 observability domain, V2 activation domain, V2
authority companion migration, V2 authority repository, and their focused tests;
narrow top-level bootstrap changes only if required to recognize the V2 union. Phase104
adds runner/source/profile/runtime/execution modules and companion; Phase105 adds
passive wrappers plus the V2 attempt/terminal observation companion. No existing
Phase99/100 production path is authorized to change semantically.

Required future tests: V1 canonical bytes/identities/rows unchanged; exact V2
prefixes and distinct equivalent-content identities; canonical V2 configuration and
stage order; closed stage/budget roles; fixed UTC session window and half-open
admission; no adaptive termination; V2 declaration-before-clock/reload chain;
late/nonofficial verification; V1 activation rejection; V2 config/session
contradictions; no detached identity; attempt execution identity required and
cross-session/config rejection; V2 terminal ancestry, integer timing conversion,
closed disposition/internal class and no outcome fields; exact V2 companion schema,
no Phase99/100 changes/backfill, and partial/unknown union rejection; preservation of
the Phase104 strict execution-parent FK path. No tests run in this PREPARE.

Remaining blockers: `PHASE102_V2_MEASUREMENT_AUTHORITY_EXTENSION_REQUIRED`,
`PHASE102_RUNTIME_BINDING_IMPLEMENTATION_DEFERRED_PENDING_V2_AUTHORITY_CONTRACT`,
`RUNTIME_SOFTWARE_COMMIT_PROVENANCE_REQUIRED`,
`RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED`,
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`, and the Phase94/95/41
source/market-semantic blockers. Recommended disposition: `DRAFT_FOR_REVIEW`.

Next: `CHATGPT_REVIEW_PHASE103_V2_MEASUREMENT_AUTHORITY`.

---

## POST_V0_8_DAILY_REPLAY_102

Title: NAR Campaign Runner and Runtime Execution Authority Architecture

Formal Status: DRAFT_FOR_REVIEW

State: DRAFT_FOR_REVIEW

Outcome: READY_FOR_ARCHITECTURAL_REVIEW

Audit: NAR_CAMPAIGN_RUNNER_AND_RUNTIME_EXECUTION_AUTHORITY_DESIGN_COMPLETE

Authorization: NONE_REQUIRED_AUDIT_ONLY

Base Commit and Branch: `703d429113e58ddfe721dd2c1ab1297d511a6ef5` / `feature/post-v0.8-daily-replay`

Allowed Files in PREPARE: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`.
Forbidden Files: all production code, tests, migrations, archive/database files,
and logs. Required Tests: none (static architectural audit); run
`git diff --check` and inspect Git status. Stop Condition: a required runtime
authority needs an unreviewed semantic, a non-document path needs mutation, or the
baseline/scope differs.

### Formal reconciliation and findings

`PHASE101_RUNTIME_BINDING_AND_WIRING_ARCHITECTURE_REVIEW_PASS`;
`POST_V0_8_DAILY_REPLAY_101 = ARCHITECTURAL_AUDIT_COMPLETE`;
`PHASE101_CAMPAIGN_RUNNER_REQUIRED_FOR_CONCURRENCY_BINDING = CONFIRMED`;
`RUNTIME_SOFTWARE_COMMIT_PROVENANCE_REQUIRED = CONFIRMED`; and
`PASSIVE_LIVE_TIMING_WIRING = DEFERRED_PENDING_RUNTIME_EXECUTION_AUTHORITY`.
Record `PHASE102_ARCHITECTURAL_REVIEW_REQUIRES_REVISION`: primary
`PROCESS_LIFETIME_LOCK_DOES_NOT_ENFORCE_CRASH_NO_RESUME`; secondary
`V2_MEASUREMENT_AUTHORITY_MUST_PRECEDE_RUNTIME_BINDING_IMPLEMENTATION`.
The Phase101 section below is historical audit material. Phase100 remains
`PHASE100_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`,
`POST_V0_8_DAILY_REPLAY_100 = FORMALLY_COMPLETE`, and
`NAR_PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY = FORMALLY_INTEGRATED`.

Primary findings are `CONTROLLED_RUNTIME_SOURCE_PROVENANCE_REQUIRED`,
`PHASE102_CAMPAIGN_RUNNER_REQUIRED_FOR_CONCURRENCY_BINDING`, and
`PHASE102_V2_MEASUREMENT_AUTHORITY_EXTENSION_REQUIRED`. The present code has no
process-wide campaign owner, source-bundle/build provenance, or runtime profile
issuer. The Phase99 v1 configuration/session/activation identities cannot express
the additional observer-publication and runtime-overhead stage meanings required for
official passive wiring. Thus `RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED`
remains unresolved until a reviewed controlled composition is implemented.

Preserve `LOCAL_CALL_GRAPH_SERIALITY != PROCESS_CAMPAIGN_CONCURRENCY_AUTHORITY`,
`DECLARED_SOFTWARE_COMMIT != RUNTIME_BOUND_SOFTWARE_COMMIT`, and
`GIT_HEAD_MATCH != RUNTIME_SOURCE_TREE_PROVENANCE`. Also preserve
`MEASUREMENT_SESSION_IDENTITY != PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY`,
`ACTIVATION_DECLARATION_IDENTITY != VERIFIED_PRESTART_ACTIVATION_AUTHORITY`,
`OBSERVABILITY_RECORD != POLICY_ACTIVATION_AUTHORITY`,
`POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY`, and
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`.
Freeze `PROCESS_LOCK != PERSISTENT_SESSION_CONSUMPTION_AUTHORITY`,
`LOCK_RELEASE_AFTER_CRASH_MUST_NOT_ENABLE_SAME_SESSION_OFFICIAL_RESUME`, and
`OFFICIAL_CAMPAIGN_EXECUTION_AUTHORITY = PROCESS_LOCK + PERSISTENT_EXECUTION_CLAIM`.

### Controlled runner and serial concurrency authority

The proposed narrow `NAROperationalTimingCampaignRunner` is an execution envelope,
not a race scheduler. In official v1 it owns exactly one activated measurement
session, invokes one target workflow at a time, exposes no worker pool or async
fan-out, performs no intentionally parallel provider HTTP, and calls the existing
RaceList sequence only serially. Its authority is limited to official compositions
that enter through this runner; it cannot prove unrelated external processes have
not ignored the contract.

Use a process-lifetime OS advisory exclusive lock at a deterministic canonical local
scope: repository identity, resolved observability-archive identity, and the serial
regime. The lock location is a regular, non-reparse/non-symlink file under a reviewed
archive-control directory. A narrow platform adapter holds it without a time lease;
release on normal process exit or crash is expected. It prevents two compliant
runners entering simultaneously but cannot itself consume a session, because the OS
normally releases it after a crash.

Add immutable, append-only `NAROperationalTimingCampaignExecutionClaim`. It
content-addresses exact v2 configuration/session, activation declaration/verification,
runtime binding/readiness, runner semantic, canonical lock-scope identity, sealed
source provenance, and instrumentation version. It has no outcome or timing-quality
material. The archive enforces exactly one claim per session (`UNIQUE(session_identity)`).
`ONE_MEASUREMENT_SESSION = AT_MOST_ONE_OFFICIAL_CAMPAIGN_EXECUTION`: an existing
claim consumes the session regardless of normal completion or crash. No status row,
claim deletion, backfill, or reconstructed continuation is allowed.

Exact official-start order is: bootstrap exact known archive state; acquire process
campaign lock; exact-reload v2 configuration/session, activation chain, and runtime
binding/readiness; prove no claim exists; construct, save, and exact-reload claim;
issue a new in-process execution capability; only then allow official attempt
publication. The capability is trusted API discipline issued only while the current
process holds the lock and has just created the claim. It is not a cryptographic
primitive, and `PERSISTED_EXECUTION_CLAIM != CURRENT_PROCESS_EXECUTION_CAPABILITY`:
loading an old claim never resumes a campaign. If claim persistence succeeds then the
process dies, the OS lock may release but the session remains consumed; unresolved
attempts remain unresolved and a new prospective activated session is required
(`CRASHED_OFFICIAL_SESSION_REQUIRES_NEW_PREDECLARED_SESSION`). A future append-only
completion receipt may document closure but cannot permit reuse.

The canonical local archive scope resolves absolute paths and rejects aliases,
symlinks/junctions, and reparse points before lock acquisition. It does not claim to
prevent an adversary running a copied archive elsewhere: the trust boundary is the
controlled single-machine KeibaOS composition, not distributed cryptographic
uniqueness. Acquire a short bootstrap lock for topology transitions, release it after
success, then acquire and retain the execution lock. Setup/migration and active
execution authority remain distinct.

### Runtime source and import provenance

Select `CONTROLLED_SEALED_GIT_SOURCE_BUNDLE_V1`, built from reviewed Git object-tree
material rather than copied mutable worktree bytes. `SEALED_BUNDLE_BYTES_MUST_DERIVE_FROM_REVIEWED_GIT_OBJECT_TREE`.
The causal chain is repository → exact commit SHA → exact commit tree SHA → Git
object/tree materialization → ordered included-member paths and byte SHA-256 values
→ canonical manifest SHA → sealed-bundle identity. File mtimes and a post-check copy
from the developer tree are not authority.

`CONTROLLED_CLEAN_GIT_WORKTREE_V1` is still an operator preflight: verify repository
identity/root and approved branch where composition binds it; exact lowercase
40-hex `HEAD` matching configuration; `HEAD^{tree}`; no staged/unstaged tracked
change; no ordinary untracked file; and no merge, cherry-pick, or rebase state. It
does not prove runtime source. Ignored files may be tolerated only when excluded from
the materialized bundle and unreachable from approved runtime import roots; ignored
executable/source candidates reachable from those roots fail closed.

The official process runs critical KeibaOS modules from the sealed bundle under an
isolated Python invocation and controlled `sys.path`; mutable worktree current
directory and caller `PYTHONPATH` are excluded. The runner verifies resolved
`__file__`/origin for operational-timing, activation/archive, snapshot, prediction,
and live NAR acquisition modules against the sealed-bundle manifest. This blocks
namespace/package shadowing without claiming to attest every stdlib/dependency file.
Later developer worktree mutation cannot alter running official source:
`DEVELOPER_WORKTREE_STATE != SEALED_RUNTIME_SOURCE_AUTHORITY`. Pre/post worktree
checks are diagnostic only. No such bundle/build authority exists today.

The runtime source provenance identity binds repository, HEAD, HEAD tree SHA, sealed
bundle/manifest SHA, source-isolation semantic, and critical-module origin manifest.
Because the process runs the bundle, later worktree mutation cannot change its
measurement code. A clean pre/post worktree check is diagnostic defense only, not a
substitute for sealed execution. `GIT_HEAD_MATCH` alone never qualifies.

Python implementation and major/minor/micro version, `requests`, `urllib3`, and
SQLite runtime versions are material timing compatibility values. Bind them to the
runtime compatibility profile; platform/architecture and storage location may be
recorded as reviewed timing-context material. A mismatch is nonqualifying for the
official population. This does not content-address an entire installed environment
or claim dependency-source attestation.

### Runtime transport/retry profile and binding

The four inspected transport factories currently construct these local profiles:
bootstrap/daily-target/official-response `10s/10s`; market-odds raw `10s/20s`;
each configures `HTTPAdapter(max_retries=0)`, no redirects, streaming, and TLS
verification. Market odds explicitly has `trust_env=False`; the other factories use
Requests' default environment behavior. Public services accept injected protocols,
so private constants and sequential source do not prove the actual collaborator.

Introduce a pure `NAROperationalTimingRuntimeProfile` builder fed only by closed
descriptors from the actual standard transport composition. Do not let a campaign
caller provide timeout values. The later implementation should promote narrow
read-only production transport descriptors rather than duplicate literals. A v2
descriptor must bind transport kind, integer-microsecond connect/read timeouts,
adapter effective retry fields, redirect/TLS/stream mode, environment/proxy mode,
and the absence of a runner-level retry loop. `HTTPAdapter(max_retries=0)` proves
the adapter construction argument, not the absence of TCP retransmission, DNS work,
proxy behavior, pooling behavior, or every lower-layer retry. The binding therefore
claims only the reviewed application/Requests-adapter regime. Any exact mismatch to
the declared v2 profile is nonqualifying.

The immutable, content-addressed `NAROperationalTimingRuntimeBinding` must bind
exact **v2** configuration/session, v2 activation declaration/verification, source
bundle identity, runtime dependency compatibility, actual transport/retry profile,
runner concurrency authority, enabled v2 stages, and schema semantics. It has no
outcome, payout, ROI, policy authorization, or `runtime_matches` caller flag. The
issuer reloads exact archived ancestry, holds the campaign lock, validates the sealed
runtime/imports, derives actual profile material, reconstructs expected v2
configuration, saves/reloads the binding, then issues a controlled readiness receipt
no later than session start. The execution claim is created only after that chain.

Persist binding, readiness receipt, and execution claim in a separate same-database
runtime companion registry/table family with restrictive ancestry FKs. Phase99/100
historical schemas/rows remain immutable; no backfill or synthetic authority. The
existing Phase99/100 v1 family is not a safe target for this implementation. Freeze
`PHASE102_RUNTIME_BINDING_IMPLEMENTATION_DEFERRED_PENDING_V2_AUTHORITY_CONTRACT`.

Closed qualification must distinguish at least
`OFFICIAL_RUNTIME_CONFIGURATION_MATCH`, `RUNTIME_SOURCE_PROVENANCE_UNAVAILABLE`,
`RUNTIME_SOFTWARE_OR_TREE_MISMATCH`, `RUNTIME_TRANSPORT_PROFILE_MISMATCH`,
`RUNTIME_RETRY_PROFILE_MISMATCH`, `RUNTIME_CONCURRENCY_AUTHORITY_UNAVAILABLE`,
`RUNTIME_ACTIVATION_ANCESTRY_MISMATCH`, and `RUNTIME_BINDING_VERIFIED_AFTER_SESSION_START`.
Missing or contradictory ancestry fails closed; do not collapse it into a vague
failure state.

### Archive bootstrap and versioned measurement contract

Add one top-level archive bootstrap, not a call to the historical strict base
migration on every open. It recognizes only explicitly reviewed transitions: empty →
Phase99 base v1 → Phase100 activation companion v1 → future v2/runtime companions;
base-only → activation → future v2/runtime; activation-installed → future v2/runtime;
and exact final union → no-op. Partial, malformed, or unknown states fail closed.
Existing strict Phase99 base and Phase100 union validators remain strict and
unmodified in meaning.

Phase99 v1 has no closed stages for `ATTEMPT_START_PUBLICATION`,
`TERMINAL_PUBLICATION`, `FREEZE_RECEIPT_PUBLICATION`,
`FREEZE_RECEIPT_EXACT_RELOAD`, or runner/runtime overhead, and its configuration,
session, attempt, terminal, and Phase100 activation identities explicitly bind v1
semantic formats. Use a separate `NAROperationalTimingMeasurementConfigurationV2`
family with v2 session/attempt/terminal and v2 activation authority, canonical
identity prefixes, parallel archive tables, and a new configuration identity. V2
execution ancestry is configuration → session → activation declaration → activation
verification → runtime binding → campaign execution claim → attempt → terminal; the
v2 attempt payload binds the exact execution claim identity. Do not extend or
reinterpret v1 JSON, rows, stages, or activation ancestry. Existing v1 data remains
diagnostic/historical and cannot silently join v2 official timing aggregation. This
V2 authority extension requires its own reviewed implementation contract before
runtime binding or wrapper work.

### Attempt, clocks, modes, and Phase103 handoff

`operation_started_at` is frozen as the
`MEASUREMENT_ATTEMPT_ADMISSION_TIMESTAMP`: it is sampled before durable attempt
publication and before the underlying callable, not claimed as exact callable-entry
time. Half-open membership remains based on this timestamp, so an attempt admitted
before session end remains a member even when publication overhead delays callable
entry/completion until afterward.

The controlled runner owns one injected aware-UTC causal clock and one monotonic
provider for the whole official campaign. A later wrapper must write/reload the
attempt before sampling monotonic start, then invoke the unchanged operation, sample
monotonic finish, sample UTC finish, and publish a closed terminal while preserving
the original return/exception. With `time.perf_counter_ns()`, store
`(finish_ns - start_ns) // 1000`: negative differences reject, sub-microsecond spans
become zero, and no float or wall-clock subtraction is used. Attempt-publication and
terminal-publication cost are v2 overhead stages and must enter later PRE_C budgeting;
terminal write failure leaves an unresolved attempt without changing production
behavior. Snapshot construction, save/commit, exact reload, receipt publication,
and receipt reload remain separate; Phase99 `freeze_completed_at` is unchanged.
Post-C wrappers may only consume the frozen snapshot and approved configuration.

`DIAGNOSTIC_TIMING` may run without the complete official chain but is permanently
segregated from official Delta evidence. `OFFICIAL_ACTIVATED_TIMING` requires the
exact v2 activated session, pre-start runtime readiness, held campaign lock, runtime
profile/source equality, execution claim/capability, and admitted binding-linked
attempts. Phase102 never authorizes HTTP. Revised decomposition is fixed:

1. Phase102 is this architectural revision only.
2. Phase103 designs and implements the v2 configuration/session/activation/attempt/
   terminal authority, stage taxonomy, and archive foundation.
3. Phase104 implements archive bootstrap, controlled runner/lock, sealed source,
   runtime profile/binding/readiness, execution claim, and in-process capability.
4. Phase105 implements passive timing wrappers.
5. Only then may diagnostic dry-run, review, and separately authorized prospective
   official campaign be considered.

Likely future paths are new v2 observability/activation domain and archive modules
(Phase103); new `scripts/simulation/nar_operational_timing_campaign_runner.py`,
`scripts/simulation/nar_operational_timing_runtime_source_provenance.py`,
`scripts/simulation/nar_operational_timing_runtime_profile.py`,
`scripts/simulation/nar_operational_timing_runtime_binding.py`,
`scripts/simulation/nar_operational_timing_archive_bootstrap.py`, and runtime
companion migration/repository modules (Phase104); and a passive-wrapper module plus
only reviewed composition changes (Phase105). No live transport or prediction module
is authorized to change in this PREPARE.

Future tests require: two concurrent compliant runners permit one authority only;
one session permits one immutable execution claim; crash/released lock and normal
completion cannot resume that session; old claim cannot issue a new-process
capability; new preactivated session can execute; canonical archive path alias/
symlink handling; exact commit/tree materialization; worktree mutation after bundle
creation cannot alter bundled code; member/manifest/origin/PYTHONPATH shadow mismatch
rejection; clean/dirty/staged/untracked/merge/rebase source checks; exact actual
profile derivation and timeout/retry/config mismatches; full v2 activation/runtime
ancestry and no caller authority/outcome fields; all bootstrap topology transitions
while historical validators stay strict; v1 immutability, v2 distinct identity, and
exact claim-bound attempt ancestry; admission boundary, clock/timer conversion,
wrapper exception preservation, unresolved terminal failure, no HTTP mutation, and
no prediction-output mutation. No tests run in this PREPARE.

Remaining blockers: `RUNTIME_SOFTWARE_COMMIT_PROVENANCE_REQUIRED`,
`RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED`,
`PHASE102_CAMPAIGN_RUNNER_REQUIRED_FOR_CONCURRENCY_BINDING`,
`PHASE102_V2_MEASUREMENT_AUTHORITY_EXTENSION_REQUIRED`,
`PHASE102_RUNTIME_BINDING_IMPLEMENTATION_DEFERRED_PENDING_V2_AUTHORITY_CONTRACT`,
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`,
`HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS`,
`PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`, and
`NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.
Recommended disposition: `DRAFT_FOR_REVIEW`; independently review the sealed-source,
runner lock, and v2 authority contracts before any implementation.

Next: `CHATGPT_REVIEW_PHASE102_CAMPAIGN_RUNNER_AND_RUNTIME_AUTHORITY`.

---

## POST_V0_8_DAILY_REPLAY_101

Title: NAR Runtime Measurement Binding and Passive Wiring Architecture

Formal Status: DRAFT_FOR_REVIEW

State: DRAFT_FOR_REVIEW

Outcome: READY_FOR_ARCHITECTURAL_REVIEW

Audit: NAR_RUNTIME_MEASUREMENT_BINDING_AND_PASSIVE_WIRING_DESIGN_COMPLETE

Authorization: NONE_REQUIRED_AUDIT_ONLY

Base Commit and Branch: `703d429113e58ddfe721dd2c1ab1297d511a6ef5` / `feature/post-v0.8-daily-replay`

Allowed Files in PREPARE: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`.
Forbidden Files: all production code, tests, migrations, archives/database files,
and logs. Required Tests: none (static design audit); run `git diff --check` and
inspect Git status. Stop Condition: a required runtime authority cannot be proved
from existing contracts, an extra path needs mutation, or baseline/scope differs.

### Formal reconciliation and primary finding

`PHASE100_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`;
`POST_V0_8_DAILY_REPLAY_100 = FORMALLY_COMPLETE`;
`NAR_PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY = FORMALLY_INTEGRATED`.
Phase99 likewise remains `PHASE99_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`,
`POST_V0_8_DAILY_REPLAY_99 = FORMALLY_COMPLETE`, and
`NAR_PRE_C_FREEZE_PROVENANCE_AND_TIMING_OBSERVABILITY_FOUNDATION = FORMALLY_INTEGRATED`.
The Phase100 section below is its historical implementation handoff; its then-pending
remote review is superseded by these formal verdicts.

Primary finding: `PHASE101_CAMPAIGN_RUNNER_REQUIRED_FOR_CONCURRENCY_BINDING`.
The existing `NARDailyTargetLiveAcquisitionApplication.acquire()` calls supplier
home, monthly root, locator script, monthly capture/normalization, and RaceList
captures sequentially inside one invocation. No repository campaign runner or
cross-process exclusion proves that only one invocation, HTTP request, race, or venue
is active globally. Therefore `LOCAL_CALL_GRAPH_SERIALITY !=
PROCESS_CAMPAIGN_CONCURRENCY_AUTHORITY`. A declared
`CONTROLLED_SINGLE_WORKER_SERIAL_V1` value does not establish execution reality.
`RUNTIME_SOFTWARE_COMMIT_PROVENANCE_REQUIRED` is a second blocker: the repository
has a validated declared Git SHA in the Phase99 configuration, but no reviewed
build/deployment identity bound to the executing process. Thus
`RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED` remains unresolved.

### Runtime binding and authority chain

Preserve configuration identity → session identity → Phase100 declaration →
verification receipt → future runtime binding → future attempts/terminals. A proposed
frozen, versioned `NAROperationalTimingRuntimeBinding` would content-address the
exact four existing ancestry identities; the runtime build manifest/commit identity;
actual closed transport descriptors (timeouts and request mode); retry/backoff
descriptor; process campaign exclusivity claim; enabled stages; instrumentation
schema/version; and canonical binding SHA/identity. It contains no result, payout,
ROI, policy authorization, or caller-supplied `runtime_matches` flag. Exact archived
activation qualification must be official before binding issuance. Bind attempts to
the exact runtime binding with a reviewed append-only per-attempt companion link or
a versioned attempt contract; session identity alone is insufficient because the
existing Phase99 attempt repository can publish independently of runtime binding.
Neither linkage is approved for implementation yet.

`MEASUREMENT_SESSION_IDENTITY != PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY`;
`ACTIVATION_DECLARATION_IDENTITY != VERIFIED_PRESTART_ACTIVATION_AUTHORITY`;
`DECLARED_SOFTWARE_COMMIT != RUNTIME_BOUND_SOFTWARE_COMMIT`;
`OBSERVABILITY_RECORD != POLICY_ACTIVATION_AUTHORITY`;
`POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY`.

The future runtime commit must come from a reviewed, immutable build/deployment
manifest produced by the trusted build, loaded once at process composition, bound to
the actual deployed artifact, and compared with the configuration's lowercase
40-hex `software_commit_sha`. Mutable branch names, a per-attempt caller string,
runtime `git rev-parse`, or GitHub lookup do not establish this provenance. No such
manifest issuer/runtime binding exists today; fail closed rather than treating a
declared SHA as an executing-code attestation.

### Actual transport, retry, and concurrency profile

The bootstrap, daily-target, and official-response transports each use connect/read
timeouts `10s/10s`, `HTTPAdapter(max_retries=0)`, `allow_redirects=False`, streamed
body reads, and their own `requests.Session`. Market-odds raw uses `10s/20s`, the
same explicit adapter/redirect settings, and `trust_env=False`; the other three do
not set `trust_env=False`. These are verified implementation facts, not a complete
future retry or total-duration guarantee. A connect/read timeout is not an overall
request deadline. There is no explicit application retry loop in these boundaries;
external proxy/environment and library behavior still need a reviewed runtime
descriptor. `max_retries=0` proves only the configured adapter setting.

Official composition must instantiate exact closed transport collaborators and
derive a canonical runtime profile from their production constants/descriptors and
effective adapter/session settings. It must compare that profile with Phase99's
configuration, including enabled transport families, exact integer-microsecond
timeouts, `NO_RETRY/0/0`, redirect mode, environment/proxy mode, and execution class.
Reading constants alone is insufficient when public service constructors accept
injected transport protocols. Do not duplicate numeric values in a second
authoritative table. Transport/profile mismatch is nonqualifying. A controlled
runner must additionally prove one active workflow and HTTP operation across the
campaign's intended process scope; sequential source syntax alone cannot do this.
The exclusion/lease mechanism, crash recovery, and scope across processes/venues
require separate review before a formal single-worker claim can be issued.

### Bootstrap, schema, and persistence plan

The historical Phase99 base migration is intentionally exact-v1 and rejects a DB
after Phase100 companion installation. A future top-level bootstrap must inspect the
exact known object set: empty → apply base v1 then activation companion v1;
base-only → apply companion; exact companion-installed → no-op; partial/unknown →
fail. It must not rerun the strict base migration on an installed companion DB or
weaken the historical base validator.

Runtime binding should use another append-only, same-database companion with its
own exact registry and restrictive foreign keys to the Phase100 verification receipt
and session, plus any separately reviewed attempt-binding records. Preserve all
Phase99/100 rows and validators; no backfill or synthetic runtime binding. A new
composed schema gate must distinguish exact base, base+activation, and
base+activation+runtime states according to caller capability, rejecting malformed,
partial, and unknown objects. The controlled issuer must reload exact activated
ancestry, obtain the trusted build identity, inspect actual transport/retry profile,
obtain a runner exclusivity claim, compare the reconstructed configuration identity,
save the binding, exact-reload it, and only then admit official attempts.

### Stage version, clocks, and passive observer contract

Phase99 stage/version 1 includes snapshot persistence and exact reload but lacks
attempt-start publication, terminal publication, and freeze-receipt archive
publication/reload stages. Its failure enum also lacks an `INTERNAL` class. Reusing
v1 names for these new meanings would corrupt configuration compatibility. Recommend
an explicit instrumentation schema v2 and new content-addressed configuration
identity for the expanded closed stage/failure taxonomy. Existing v1 rows remain
immutable and must not silently aggregate with v2. Activation/runtime setup costs
outside per-race PRE_C may be measured separately; mandatory per-race observer and
freeze-receipt overhead must enter the PRE_C envelope.

One campaign-owned injected causal clock returns aware UTC-compatible timestamps;
one campaign-owned injected monotonic provider measures elapsed time. Candidate
production monotonic source is `time.perf_counter_ns()`. For nonnegative nanosecond
differences, store exact integer microseconds by floor division `elapsed_ns // 1000`
(sub-microsecond spans become zero); reject negative samples. Wall-clock subtraction
must not determine latency. Do not let each wrapper choose its own clock.

Future official wrapper order: verify archived official activation, exact runtime
binding, and campaign claim; sample UTC attempt start; construct and durably save the
Phase99 attempt together with its reviewed runtime-binding ancestry; exact-reload
if required; sample monotonic start; call the unchanged operation; sample monotonic
finish and causal UTC finish; publish a closed terminal. Phase99's
`operation_started_at` denotes the attempt-admission boundary before observer
publication, while the measured invocation begins after publication; even if
publication delays invocation past session end, that admitted attempt remains in
the denominator. Attempt publication cost is its own v2 overhead stage. An
attempt-write failure creates no official sample; the underlying operation may
proceed only as diagnostic behavior under an explicit composition contract.
Terminal publication failure must preserve the operation's value/exception and
leave the archived attempt unresolved for reconciliation.

Preserve original exception propagation. Map requests connect/read timeout causes
to `TIMEOUT/TIMEOUT`, other known transport failures to `FAILURE/TRANSPORT`, source
validation to `FAILURE/VALIDATION`, archive/SQLite persistence failures to
`FAILURE/PERSISTENCE`, and unsupported profiles to `UNSUPPORTED/UNSUPPORTED`.
An unexpected internal exception needs a reviewed v2 closed classification;
do not mislabel it as transport or swallow it. Transport services wrap requests
errors with causes, so wrappers must inspect the stable cause chain without
persisting unstable exception text. If UTC jumps backward so a terminal would
violate Phase99's time ordering, retain the unresolved attempt and surface clock
failure; never adjust its timestamp to pass validation.

### Audited composition boundaries

| Stage | Existing exact boundary | Current wrapper feasibility and correlation |
| --- | --- | --- |
| Bootstrap home/root/script | `NARMonthlyConveneInfoBootstrapLiveCaptureService.capture_official_home/capture_monthly_root/capture_locator_script` | Injected transport/archive wrappers can time fetch and persistence; pre-target-set provider/workflow correlation must be derived by the runner. |
| Monthly/RaceList | `NARHistoricalDailyTargetLiveCaptureService.capture_supplied_response`; outer `NARDailyTargetLiveAcquisitionApplication.acquire` | Transport wrapper can time one exact request; outer workflow captures sequential order. Target-set SHA does not yet exist at initial capture; do not attach it retrospectively. |
| Official response | `NAROfficialLiveResponseCaptureService.capture_response` | Wrap injected transport/archive at canonical URL; record capture `capture_id` and raw `response_sha256` from returned capture. |
| Market odds raw | `acquire_nar_market_odds_raw_response` | Wrap injected transport/function, derive exact request/race identity and returned capture digest; this alone grants no odds or market authority. |
| Snapshot | `build_historical_input_snapshot`; `SQLiteHistoricalInputSnapshotRepository.save_snapshot/load_snapshot_by_identity`; `issue_historical_input_snapshot_freeze_receipt` | Pure builder and repository protocol can be wrapped. Time construction, commit, exact reload, receipt publication, and receipt reload separately. Bind snapshot `content_sha256` and receipt identity. |
| Post-C compute | `execute_and_persist_historical_bet_plan`; `PersistedSimulationBetPlanService.build_and_save` | Outer call can be timed without changing output. Fine-grained pipeline/plan-builder proxies are constrained by concrete `isinstance` checks; any hooks require later review. Bind bet-plan snapshot identity/content where available. |

Phase99 `freeze_completed_at` remains the service-owned UTC sample after snapshot
save/commit and exact reload, before receipt archive publication. Time receipt
publication and reload separately; do not redefine that timestamp or backdate it.
Post-C wrappers consume only the frozen snapshot and approved strategy/configuration;
no new provider evidence may enter through timing code. For correlation, use exact
provider objects before target-set construction, then exact target set, race,
cutoff plan, and policy objects when available. The current Phase99 correlation
domain has no pre-target-set workflow/request scope; v2 must add a closed identity
or runner-bound link rather than accept detached free text. Correlation is not
eligibility or policy authority.

### Diagnostic/official population and implementation split

`DIAGNOSTIC_TIMING` can inspect wrappers without qualifying for concrete Delta
selection. `OFFICIAL_ACTIVATED_TIMING` requires exact Phase100 activation, trusted
runtime commit, actual profile equality, process campaign exclusivity, exact
attempt-to-binding ancestry, and Phase99 half-open admission. Missing any element
blocks the whole selected timing population from official Delta review; no silent
sample filtering. No provider HTTP or live campaign is authorized by completing
this design or a future implementation. A separate reviewed campaign execution
approval remains required.

Choose decomposition **C: campaign runner must come first**. Phase101 should
design/implement only a bounded serial campaign composition and trusted runtime
build/profile provenance, with exact bootstrap and exclusion contracts reviewed
before live operation. Runtime binding companion issuance and passive wrappers
follow in separately reviewed work; adding wrappers before runner authority would
mislabel concurrency. This is not permission to implement a full race scheduler.

Likely future production paths for the first boundary: new
`scripts/simulation/nar_operational_timing_campaign_runner.py`,
`scripts/simulation/nar_operational_timing_runtime_profile.py`,
`scripts/simulation/nar_operational_timing_archive_bootstrap.py`, and a reviewed
build-manifest producer/loader path (not present today). Later runtime issuance:
new `scripts/simulation/nar_operational_timing_runtime_binding.py`,
`scripts/simulation/nar_operational_timing_runtime_archive_migration.py`,
`scripts/simulation/sqlite_nar_operational_timing_runtime_archive.py`, with narrow
composed-gate changes to the Phase100 activation/archive repository paths. Later
wrappers: new `scripts/simulation/nar_operational_timing_passive_wrappers.py` and,
only if reviewed hooks prove necessary, the exact live/snapshot/post-C files in the
table above and a versioned extension of
`scripts/simulation/nar_operational_timing_observability.py`.

Future tests should cover: exact activated ancestry; software commit/profile/retry/
concurrency mismatches; no caller authority flag or outcome input; exact runtime
archive roundtrip and attempt ancestry; empty/base/companion bootstrap and malformed
rejection while keeping the base validator strict; process-wide single-workflow
exclusion including a second process and crash recovery; attempt persisted before
operation and monotonic start; floor-ns conversion and wall-clock jumps; success,
timeout, validation, persistence, unsupported, and internal failures preserving
production exceptions; terminal-write failure leaving unresolved attempts;
attempt-write failure producing no official sample; post-window completion retained;
unchanged HTTP request and prediction output; exact correlation; and v1/v2
configuration separation. No tests are run in this PREPARE.

Likely new tests: `tests/test_nar_operational_timing_campaign_runner.py`,
`tests/test_nar_operational_timing_runtime_profile.py`,
`tests/test_nar_operational_timing_archive_bootstrap.py`,
`tests/test_nar_operational_timing_runtime_binding.py`,
`tests/test_nar_operational_timing_runtime_archive_migration.py`,
`tests/test_sqlite_nar_operational_timing_runtime_archive.py`, and
`tests/test_nar_operational_timing_passive_wrappers.py`. Required regressions include
the existing Phase99/100 observability/activation tests plus
`tests/test_nar_daily_target_live_acquisition.py`,
`tests/test_nar_official_response_live_capture.py`,
`tests/test_nar_market_odds_raw_acquisition.py`,
`tests/test_historical_input_snapshot_freeze_receipt.py`, and
`tests/test_historical_prediction_bet_plan_execution.py`. Each implementation
subphase must specify its own exact focused/regression/full-suite commands.

Remaining blockers: `RUNTIME_SOFTWARE_COMMIT_PROVENANCE_REQUIRED`,
`PHASE101_CAMPAIGN_RUNNER_REQUIRED_FOR_CONCURRENCY_BINDING`,
`RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED`,
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`,
`HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS`,
`PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`, and
`NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.
Recommended disposition: `DRAFT_FOR_REVIEW`; review the runner/build authority
boundary before authorizing implementation. Next:
`CHATGPT_REVIEW_PHASE101_RUNTIME_BINDING_AND_WIRING`.

---

## POST_V0_8_DAILY_REPLAY_100

Title: NAR Timing Campaign Activation and Passive Wiring Architecture

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Audit: NAR_TIMING_CAMPAIGN_ACTIVATION_AND_PASSIVE_WIRING_DESIGN_COMPLETE

Authorization: POST_V0_8_DAILY_REPLAY_100_APPROVED_FOR_IMPLEMENTATION

Design Review: PHASE100_CAMPAIGN_ACTIVATION_DESIGN_REVIEW_PASS

Implementation: NAR_PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY_IMPLEMENTED

### Phase100 implementation for independent review

The same-database companion has its own exact v1 registry, two immutable record
families, restrictive foreign keys, a one-declaration-per-session constraint, and a
one-verification-per-declaration constraint. The historical Phase99 v1 DDL and
registry remain unchanged. The original strict base-v1 validator remains available;
the ordinary Phase99 archive now accepts only exact base v1 or exact base plus exact
companion v1, while the activation archive requires the latter. Migration does not
backfill any activation rows.

Controlled issuance exact-reloads the archived configuration/session, saves and
exact-reloads a canonical declaration, samples injected UTC only afterward, then
saves and exact-reloads its verification receipt. An exact retry reuses the existing
receipt without sampling time; a declaration-only retry samples the current time.
Qualification reloads the entire archived chain and compares
`activation_verified_at <= measurement_start_at`. The timestamp proves the
declaration commit/reload boundary, not receipt publication or stronger crash
durability. These are trusted API boundaries, not cryptographic protection against
arbitrary Python callers.

No transport, scheduler, prediction, Phase96, snapshot, or Phase99 base migration
semantics changed. Phase101 still owns runtime binding and live passive timing
wrappers. `RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED` and
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remain unresolved.

Focused tests: 14 passed. Focused plus Phase99/snapshot/cutoff regressions:
91 passed, 30 subtests passed. Full repository suite: 4590 passed, 2 skipped,
2846 subtests passed. Provider HTTP/live campaigns/production DB writes: zero;
temporary in-memory SQLite writes occurred in tests only. Independent remote
implementation verification is pending.

Approved implementation contract: activation declaration and verification receipt,
same-database companion schema, exact archive compatibility, controlled issuance,
qualification, focused tests, and documentation. Allowed Files:
`scripts/simulation/nar_operational_timing_session_activation.py`,
`scripts/simulation/nar_operational_timing_activation_archive_migration.py`,
`scripts/simulation/sqlite_nar_operational_timing_activation_archive.py`,
`scripts/simulation/sqlite_nar_operational_timing_observability_archive.py`,
`tests/test_nar_operational_timing_session_activation.py`,
`tests/test_nar_operational_timing_activation_archive_migration.py`,
`tests/test_sqlite_nar_operational_timing_activation_archive.py`,
`docs/CURRENT_PHASE.md`, and `docs/LATEST_CODEX_REPORT.md`.
Forbidden Files: Phase99 base migration DDL/registry, live capture/prediction modules,
Phase96/99 snapshot semantics, database files, and logs. Required Tests: new focused
tests, all four Phase99 focused tests, specified snapshot/cutoff regressions, full
repository pytest, `git diff --check`, and changed-path audit. Stop Condition:
baseline drift, unexpected files, schema coexistence failure, historical-row rewrite,
unreviewed live/runtime changes, out-of-scope test failure, or force-push need.

Base Commit and Branch: `d3c355e5bfae6dac375ad212cae77549d098a8d9` / `feature/post-v0.8-daily-replay`

### Phase99 formal reconciliation

`PHASE99_IMPLEMENTATION_REMOTE_VERIFICATION_PASS` is frozen.
`POST_V0_8_DAILY_REPLAY_99 = FORMALLY_COMPLETE` and
`NAR_PRE_C_FREEZE_PROVENANCE_AND_TIMING_OBSERVABILITY_FOUNDATION = FORMALLY_INTEGRATED`.
`PHASE99_MEASUREMENT_SESSION_CONTRACT_REQUIRES_REVIEW = RESOLVED`.

Phase99 provides configuration/session identity, started-at denominator records,
terminal observations, an isolated append-only archive, and snapshot freeze receipts.
It deliberately does not turn a session identity into evidence that its measurement
window was declared in advance:

`MEASUREMENT_SESSION_IDENTITY != PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY`.

### Final architectural revision

Record `PHASE100_ARCHITECTURAL_REVIEW_REQUIRES_REVISION`. Primary finding:
`V1_OBSERVABILITY_REGISTRY_CANNOT_DIRECTLY_ACCEPT_V2_MIGRATION`. Secondary finding:
`ACTIVATION_TIMESTAMP_DOES_NOT_YET_PROVE_PRESTART_ACTIVATION_PUBLICATION`.
`PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY_REQUIRED` remains the Phase100 need;
the preliminary one-record/v2 proposal below is historical and superseded.

The Phase99 registry is structurally v1-only: its `version` check permits only `1`,
its registered migration name is fixed to v001, and its exact gate requires the exact
v1 object set. Phase100 therefore preserves the base-v1 registry, DDL, rows, tables,
triggers, payloads, and validator unchanged. It must not insert a version-2 row,
rewrite historical evidence, backfill, or synthesize activation.

#### Companion schema and exact validation

Use the same SQLite database but add a distinct v1 companion registry named
`nar_operational_timing_activation_schema_migrations`, with typed immutable activation
declarations and verification receipts. Its migration first verifies exact Phase99
base v1, then atomically adds its registry, tables, restrictive foreign keys, and
UPDATE/DELETE-rejecting triggers. Declaration ancestry references
`nar_operational_timing_sessions(identity)` with `ON UPDATE RESTRICT ON DELETE RESTRICT`;
receipts reference their exact declaration identity.

The historical Phase99 validator retains its exact base-v1 meaning. A separate
Phase100-capable gate validates the exact union of base v1 and activation-companion v1.
Pristine base v1 upgrades idempotently; malformed base, partial companion, changed
existing objects, or unknown extras fail closed.

#### Declaration, verification receipt, and eligibility

`NAROperationalTimingMeasurementSessionActivationDeclaration` is immutable and
content-addressed from only schema version, exact session identity, exact measurement
configuration identity, and a closed activation semantic/version. It has no caller
timestamp and no outcome/result/payout/ROI material. A controlled issuer exact-reloads
the archived configuration and session, saves the declaration append-only, and exactly
reloads it before sampling its injected service-owned UTC clock.

It then creates, persists, and exact-reloads a verification receipt containing schema
version, declaration/session/configuration identities, a closed verification semantic,
and `activation_verified_at`. The time proves that the declaration had already
committed and exact-reload verified no later than that sample; it does not claim the
receipt itself was published by then. Thus
`ACTIVATION_DECLARATION_IDENTITY != VERIFIED_PRESTART_ACTIVATION_AUTHORITY`.

`OFFICIAL_PREDECLARED_MEASUREMENT_SESSION` requires the exact archived declaration and
receipt chain plus `activation_verified_at <= measurement_start_at`; equality is
eligible because declaration persistence/reload precedes the sample. Later verification
is `ACTIVATION_VERIFIED_AFTER_MEASUREMENT_START`; absent or contradictory evidence is
`ACTIVATION_PROVENANCE_UNAVAILABLE`. Session SHA, declaration construction time,
filesystem/database metadata, and retrospective Python values never substitute.

#### Scope split, blockers, and future paths

Activation authorizes only predeclaring a timing campaign. It does not authorize Delta,
a Phase97 policy, status/market eligibility, ROI, or the executing runtime. Preserve
`MEASUREMENT_SESSION_IDENTITY != PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY`,
`SESSION_ACTIVATION_AUTHORITY != POLICY_ACTIVATION_AUTHORITY`, and
`DECLARED_SOFTWARE_COMMIT != RUNTIME_BOUND_SOFTWARE_COMMIT`.
`RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED` remains a Phase101 blocker.

Phase100 is activation-only: declaration/receipt domain, companion migration/schema,
archive support or a narrow activation repository wrapper, controlled issuance,
qualification, tests, and docs. Phase101 is deferred for runtime binding,
UTC/monotonic composition, attempt wiring, and passive live wrappers. The first
official Delta-selection campaign remains unavailable; preserve
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` and independent status/market
semantic blockers.

Likely Phase100 paths: create
`scripts/simulation/nar_operational_timing_session_activation.py`; create
`scripts/simulation/nar_operational_timing_activation_archive_migration.py`; and either
narrowly modify `scripts/simulation/sqlite_nar_operational_timing_observability_archive.py`
or create an activation repository wrapper. Create focused activation, companion
migration, and companion archive tests. Required tests cover exact v1-to-companion
upgrade/no base-registry v2 row, exact union rejection, no backfill, controlled
declaration→reload→clock→receipt issuance, before/equal/after-start states,
append-only idempotency/conflicts, and authority separation.

Allowed Files for this PREPARE: `docs/CURRENT_PHASE.md` and
`docs/LATEST_CODEX_REPORT.md`. Forbidden: production/test/migration edits, archive or
DB writes, provider/network activity, staging, commit, and push. Required Tests: not
run (documentation-only). Next: `CHATGPT_REVIEW_PHASE100_CAMPAIGN_ACTIVATION_AND_WIRING`.

### Historical preliminary Phase100 design — superseded

Everything in this historical preliminary block through the Phase99 separator records
the replaced single-record/in-place-v2 proposal only. The final architectural revision
above is the sole current Phase100 contract.

Primary finding: `PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY_REQUIRED`.
Official evidence for selecting a future fixed Delta requires an immutable record that
the exact archived configuration and exact archived fixed-window session were declared
before the session begins. A later session SHA cannot provide that proof.

Recommended decomposition: **Phase100 activation authority first; Phase101 passive
wrappers after activation receives independent review.** This keeps the authority
schema and controlled clock boundary auditable before live composition can publish
timing evidence. No prospective scheduler contract is required for the Phase100
activation foundation. A scheduler becomes a separate prerequisite only if a later
live campaign needs more than the reviewed single-worker serial execution regime.

### Session activation authority contract

Future `NAROperationalTimingMeasurementSessionActivation` is a frozen/slotted,
content-addressed record with exactly:

* `schema_version`;
* exact Phase99 `session_identity`;
* exact Phase99 `measurement_configuration_identity`;
* `PREDECLARED_BEFORE_MEASUREMENT_WINDOW` activation semantic/version;
* service-owned UTC `activated_at`; and
* SHA-256 of canonical NFC UTF-8 JSON, exposed as
  `nar-operational-timing-session-activation-v1:<sha256>`.

The session/configuration pair is reloaded exactly from the archive before issuance.
The controlled issuer then samples an injected centralized UTC clock and requires
`activated_at <= measurement_start_at`; equality is eligible. If the sample is later,
issuance fails closed. It does not publish a diagnostic activation row, because a
nonofficial row with the same authority shape would add an avoidable interpretation
path. Existing sessions receive no synthetic activation and no backfill.

Freeze:

`SESSION_ACTIVATION_AUTHORITY != SESSION_IDENTITY`

`SESSION_ACTIVATION_AUTHORITY != POLICY_ACTIVATION_AUTHORITY`

`SESSION_ACTIVATION_AUTHORITY != PREDICTION_CUTOFF_POLICY`

An activation authorizes only the timing campaign definition. It does not select or
activate Delta, establish race/market/status authority, or authorize ROI evaluation.

### Archive extension and aggregation eligibility

Use an explicit **v2 migration of the existing isolated observability archive**. V2
adds one append-only activation table keyed by activation identity, with a one-to-one
unique foreign key to the existing session identity, immutable UPDATE/DELETE triggers,
and `ON UPDATE RESTRICT ON DELETE RESTRICT`. It preserves every v1 table, row, trigger,
and canonical payload unchanged. The migration first accepts only an exact v1 archive,
then creates the v2 objects and records version 2 atomically. Reapplying it is
idempotent; partial or modified v2 objects fail the exact schema gate. V1-only archives
remain readable diagnostic archives but cannot qualify sessions for official Delta
evidence until a real pre-start activation is issued, which will normally be impossible
after the fact.

Later official aggregation requires all of the following for every selected session:

* exact matching measurement-configuration identity;
* one exact qualifying activation record;
* membership under the Phase99 half-open started-at rule;
* all admitted attempts, including failures/timeouts;
* terminal observations where present; and
* explicit unresolved-attempt count after drain/reconciliation.

The closed session classification is `OFFICIAL_PREDECLARED_MEASUREMENT_SESSION` only
when that activation is exact and timely. Missing activation, activation absence in a
legacy v1 archive, or any activation contradiction is
`DIAGNOSTIC_UNAUTHORIZED_MEASUREMENT_SESSION` for timing-review purposes. Such data
may inform instrumentation debugging but must not silently join official Delta
selection. Different session identities may aggregate later only when configuration
identity matches under a reviewed aggregation contract.

### Runtime configuration, clocks, and correlation

The live composition must build or verify its measurement configuration from actual
closed collaborators: current transport constants, `max_retries=0`, serial RaceList
iteration, selected worker regime, enabled stages, and a deployment-provided immutable
software commit. A caller-written configuration object alone is insufficient.

`DECLARED_SOFTWARE_COMMIT` is the value in Phase99 configuration.
`RUNTIME_BOUND_SOFTWARE_COMMIT` must be an immutable build/deployment commit identity
injected once into the live composition and required to equal the declared value. A
runtime that cannot supply this value is diagnostic only; it cannot produce official
campaign evidence. No GitHub/network lookup is required at runtime.

Use one centralized injected UTC clock provider for causal timestamps and one injected
monotonic timer for elapsed spans. Wrappers must not accept independently chosen event
clocks. Clock-skew bounds remain evidence required before a concrete Delta review.
Provider, target-set, race, cutoff-plan, and policy correlations must be derived from
their exact domain objects, never from contradictory detached strings. Correlation
does not create target, policy, or eligibility authority.

### Passive instrumentation order and overhead

For each instrumented stage, the future wrapper must:

1. sample centralized causal UTC operation start;
2. construct and durably publish the exact attempt start;
3. start the monotonic timer for the measured operation;
4. execute the underlying operation;
5. stop the monotonic timer and sample causal UTC finish; and
6. publish the terminal observation.

Attempt publication occurs before the measured-operation timer. Its durable-write cost
is observer bookkeeping and must be measured as a closed observability-overhead stage
when it is synchronously on the PRE_C path. The measured span excludes that bookkeeping
but later Delta review must include required attempt/receipt publication overhead in
its complete PRE_C envelope. Terminal publication failure does not alter the operation
result; the started attempt remains unresolved. The wrapper rethrows the underlying
operation exception after best-effort closed failure/timeout terminal publication and
never swallows it to produce a metric. If required start publication fails, the wrapper
does not fabricate a sample; production/shadow behavior may continue diagnostically
only under its existing error contract.

### Audited wiring boundaries

The narrow future composition points are:

| Stage family | Existing boundary | Passive wrapper placement |
| --- | --- | --- |
| Bootstrap HTTP | `NARMonthlyConveneInfoBootstrapLiveCaptureService.capture_*` | transport/service composition around each supplier fetch |
| Daily target / RaceList HTTP | `NARHistoricalDailyTargetLiveCaptureService.capture_supplied_response` | service composition around exact supplied-response capture |
| Daily acquisition sequence | `NARDailyTargetLiveAcquisitionApplication.acquire` | one outer serial workflow wrapper; retain current sequential RaceList tuple iteration |
| Official response HTTP | `NAROfficialResponseLiveCaptureService.capture_response` | service composition around one exact response URL |
| Market odds raw HTTP | `acquire_nar_market_odds_raw_response` | function-level adapter around injected transport/clock |
| Snapshot construction | `build_historical_input_snapshot` | outer builder adapter, without changing builder semantics |
| Snapshot persistence / reload | `issue_historical_input_snapshot_freeze_receipt` | wrapper stages around its existing save/reload/receipt sequence |
| Post-C prediction / bet plan | `execute_and_persist_historical_bet_plan` and `PersistedSimulationBetPlanService.build_and_save` | outer execution service adapter |

The snapshot freeze decomposition is fixed: snapshot repository save/commit;
snapshot exact reload; receipt construction; receipt archive persistence; receipt exact
reload. Phase99 `freeze_completed_at` remains the UTC sample after the first two steps
and before receipt archive publication. If a future operating policy needs receipt
publication by C, it needs a separate qualification/timestamp; Phase100 does not
change the existing receipt meaning.

### Campaign lifecycle and remaining gates

The first official prospective campaign must follow this order:

1. bind exact runtime software/configuration from executing collaborators;
2. create and archive Phase99 configuration and a fixed future session;
3. issue and reload timely activation before the window begins;
4. publish attempt starts before operations; publish terminals or retain unresolved
   attempts after the fixed window;
5. freeze the campaign evidence set and compute read-only timing statistics; and
6. submit complete evidence for independent Delta review.

A diagnostic dry run may validate adapters, but without exact timely activation it is
not official evidence and cannot be pooled into the official population, even under
the same configuration.

Phase100 does not select Delta, perform provider HTTP, collect campaign data, change
transport/retry/timeout/concurrency behavior, create a full scheduler, alter Phase96
or Phase99 semantics, activate a prediction policy, resolve status semantics, market
eligibility, or ROI. Preserve
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`,
`HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS`,
`PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`, and
`NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`.

### Expected implementation paths and tests

Recommended Phase100 activation-only implementation:

* modify `scripts/simulation/nar_operational_timing_observability_archive_migration.py`;
* modify `scripts/simulation/sqlite_nar_operational_timing_observability_archive.py`;
* create `scripts/simulation/nar_operational_timing_measurement_session_activation.py`;
* modify the focused observability migration/archive tests;
* create `tests/test_nar_operational_timing_measurement_session_activation.py`; and
* modify the two phase-control documents.

Phase101 may create a passive adapter/composition module and focused tests, then modify
only the selected live capture, snapshot-freeze, and post-C execution composition
boundaries above after its own review. It must use actual runtime-profile validation
and injected centralized clocks; it must not alter underlying protocol behavior.

Required future activation tests cover controlled `activated_at`, exact session/config
binding, before/equal-start qualification, after-start rejection, no backfill,
legacy-v1 classification, v2 schema idempotency and exactness, append-only reload, and
one activation per session. Required later wrapper tests cover durable attempt start
before execution, preserved exceptions, closed timeout/failure terminals, unresolved
crash-like starts, late terminal membership, independent monotonic/UTC clocks, runtime
configuration/commit mismatch, observer failure noninterference, and separately
observable receipt publication/reload overhead.

Recommended Phase100 disposition: `DRAFT_FOR_REVIEW` pending architectural review of
the v2 activation authority. Next:
`CHATGPT_REVIEW_PHASE100_CAMPAIGN_ACTIVATION_AND_WIRING`.

---

## POST_V0_8_DAILY_REPLAY_99

Title: NAR Pre-C Freeze and Timing Observability Architecture

Formal Status: READY_FOR_REVIEW

Design Review: PHASE99_TIMING_OBSERVABILITY_DESIGN_REVIEW_PASS

Measurement Contract Review: PHASE99_MEASUREMENT_SESSION_CONTRACT_REVIEW_PASS

Base Commit and Branch: `7ec5afbe89d65803ba63d357a1d07e68c4c7e30a` / `feature/post-v0.8-daily-replay`

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Audit: NAR_PRE_C_FREEZE_AND_TIMING_OBSERVABILITY_DESIGN_COMPLETE

Authorization: POST_V0_8_DAILY_REPLAY_99_REAPPROVED_FOR_IMPLEMENTATION

Implementation: NAR_PRE_C_FREEZE_PROVENANCE_AND_TIMING_OBSERVABILITY_FOUNDATION_IMPLEMENTED

### Phase99 implementation result

`PHASE99_TIMING_OBSERVABILITY_DESIGN_REVIEW_PASS` and
`PHASE99_MEASUREMENT_SESSION_CONTRACT_REVIEW_PASS` authorized the narrow substrate.
`PHASE99_IMPLEMENTATION_STOP_CONDITION_ACCEPTED` remains the accurate record of the
prior halt; `PHASE99_MEASUREMENT_SESSION_CONTRACT_REQUIRES_REVIEW = RESOLVED`.

The implementation adds frozen/slotted content-addressed configuration, fixed-window
session, closed stage/correlation/load context, separate attempt-start and terminal
observation records, an isolated v1 SQLite archive, and a controlled snapshot
save→commit→exact reload→UTC sample→archive write→archive reload receipt service.
Qualification uses an archived receipt plus exact NAR target and Phase96 cutoff plan;
`freeze_completed_at <= C` qualifies and later completion does not. The receipt
claims only `COMMITTED_AND_EXACT_RELOAD_VERIFIED`, not crash durability. Existing
snapshot `captured_at` is never used as freeze-completion proof. An identical stored
snapshot without a prior receipt receives a new verification time, never an inferred
historical time.

The archive is connection-injected, explicitly migrated, exact-schema gated, and
append-only. Configurations, sessions, attempts, terminals, and freeze receipts are
separate record families. Every started attempt remains queryable until it has a
terminal record, including a slow attempt finishing after the fixed session end.
Direct caller-created receipts cannot be archived through the public save method
without the controlled issuance marker. Optional metric failure cannot affect
prediction values; required receipt publication failure leaves the snapshot intact
and prevents official freeze qualification. Required receipt persistence and reload
belong to future PRE_C timing budgets.

Focused tests: `29 passed`. Required existing regressions: `108 passed, 95
subtests passed`. Full suite: `4576 passed, 2 skipped, 2846 subtests passed`.
Only four new production modules, four new focused tests, and the two phase-control
documents changed. Provider HTTP / Phase44 / GET: `0 / 0 / 0`. Production DB writes:
`0`; test-only in-memory SQLite writes exercised the archive and snapshot repository.

Still unresolved: `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`,
`MEASUREMENT_SESSION_IDENTITY != PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY`,
`POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY`, and the independent Phase94/95/41
source-semantic blockers. Phase99 is not formally complete before independent review.

Next: `CHATGPT_REVIEW_PHASE99_IMPLEMENTATION`.

### Phase99 execution contract

Allowed Files: create `scripts/simulation/nar_operational_timing_observability.py`, `scripts/simulation/nar_operational_timing_observability_archive_migration.py`, `scripts/simulation/sqlite_nar_operational_timing_observability_archive.py`, `scripts/simulation/historical_input_snapshot_freeze_receipt.py`, `tests/test_nar_operational_timing_observability.py`, `tests/test_nar_operational_timing_observability_archive_migration.py`, `tests/test_sqlite_nar_operational_timing_observability_archive.py`, and `tests/test_historical_input_snapshot_freeze_receipt.py`; modify `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`.

Forbidden Files: every other production/test path, especially live capture/transports, generic snapshot repository/domain, Phase96 resolver/cutoff plan, scheduler, prediction pipeline, database, and logs.

Required Tests: all four new focused test files; `tests/test_sqlite_historical_input_snapshot_repository.py`, `tests/test_historical_input_snapshots.py`, `tests/test_historical_input_snapshot_builder.py`, `tests/test_nar_historical_replay_prediction_cutoff.py`, `tests/test_nar_historical_replay_prediction_cutoff_policy.py`, `tests/test_sqlite_nar_daily_evidence_resolver.py`; then the full repository pytest suite, `git diff --check`, and exact changed-path audit.

Stop Condition: stop if the remote baseline advanced, unexpected non-doc changes exist, a new source/activation semantic or concrete Delta is required, the existing snapshot repository cannot safely support controlled wrapper issuance, a live transport or Phase96 change is required, tests fail outside scope, or normal push cannot succeed without force. Only after all checks pass may the one authorized commit and normal push occur.

### Historical design record — measurement-session contract revision

Implementation at the design-revision checkpoint: `NOT_STARTED_STOP_CONDITION_RESOLVED_IN_DESIGN`.

The prior stop is accepted: `PHASE99_IMPLEMENTATION_STOP_CONDITION_ACCEPTED` and
`PHASE99_MEASUREMENT_SESSION_CONTRACT_REQUIRES_REVIEW = RESOLVED`.  The earlier
`PHASE99_MEASUREMENT_SESSION_CONTRACT_UNDERSPECIFIED` halt was correct: an immutable
timing archive must not invent its population contract.  This revision freezes that
contract was independently reviewed as `PHASE99_MEASUREMENT_SESSION_CONTRACT_REVIEW_PASS`.

`NAROperationalTimingMeasurementConfiguration` answers **what operational regime is
measured**. `NAROperationalTimingMeasurementSession` answers **when one campaign
under that exact configuration admits operation attempts**. They are distinct,
versioned, frozen/slotted content-addressed values. Aggregation may combine sessions
only under a later reviewed contract and only with exact matching configuration
identity.

Configuration v1 canonical material is exactly: schema version; repository identity
`garimapo/KeibaOS`; an exact lowercase 40-hex Git commit SHA (not branch name); closed
NAR/nar_official provider scope; instrumentation schema/version; a nonempty canonical
closed enabled-stage tuple; canonical closed HTTP profiles; closed retry/backoff
semantics; closed concurrency regime; and sample-admission semantic version. It must
exclude session time bounds, observed latency, result, payout, ROI, profitability,
prediction/replay outcome, and eventual executability. NFC UTF-8 JSON with
`ensure_ascii=False`, `allow_nan=False`, sorted keys, compact separators, and exact
integers produces `measurement_configuration_sha256` and only
`nar-operational-timing-config-v1:<sha256>`; callers cannot supply a detached SHA.

Closed transport profiles are unique and canonical regardless of caller order:
`NAR_BOOTSTRAP_HTTP`, `NAR_DAILY_TARGET_HTTP`, and
`NAR_OFFICIAL_RESPONSE_HTTP` each have connect/read timeout
`10_000_000/10_000_000` microseconds; `NAR_MARKET_ODDS_RAW_HTTP` has
`10_000_000/20_000_000`. Each included family has exactly one profile. V1 supports
only `NO_RETRY`, requiring `max_retries=0` and `backoff_microseconds=0`; this records
the measured current regime rather than approving an eternal retry policy.

The controlled v1 concurrency regime is `CONTROLLED_SINGLE_WORKER_SERIAL_V1`: one
campaign worker, one active target workflow, one HTTP request, sequential RaceList
acquisition, and no approved cross-race/venue parallel scheduler. Enabled stages are
nonempty closed Phase99 enum values in canonical enum order, with no duplicate or
unknown value. A serial campaign cannot authorize parallel Delta; any later bounded
parallel regime requires a new configuration and compatible campaign.

Session v1 canonical material is schema version, exact configuration identity,
UTC-normalized fixed-microsecond `measurement_start_at`/`measurement_end_at`,
`OPERATION_STARTED_IN_HALF_OPEN_SESSION_WINDOW`, and `FIXED_WALL_CLOCK_END`.
Timestamps must be aware and `start < end`; sessions are not open-ended. Canonical
JSON SHA produces only `nar-operational-timing-session-v1:<sha256>`. Admission is
exactly `start <= operation_started_at < end`, irrespective of success, failure,
timeout, or unsupported terminal disposition. A pre-end attempt remains admitted if
it finishes after end; a post-window drain reconciles it without moving the end.

Every admitted attempt needs a stable identity and recorded start boundary before or
at execution. Terminal data binds to it. A start-in-window attempt without terminal
data after reconciliation is unresolved/incomplete evidence, never silently removed.
Failures and timeouts remain in the denominator; success-only percentiles are
supplementary. V1 forbids success-count, executable-race, stable-percentile, timeout,
or outcome/profitability-dependent completion rules.

`MEASUREMENT_SESSION_IDENTITY != PRE_MEASUREMENT_SESSION_ACTIVATION_AUTHORITY`.
An optional controlled activation receipt is deferred: only a future archive/service
owned `activated_at <= measurement_start_at` could prove predeclaration, and callers
may never supply that timestamp. Thus official predeclared-campaign provenance remains
unresolved. Preserve `POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY` and
`OBSERVABILITY_RECORD != POLICY_ACTIVATION_AUTHORITY`.

### Historical pre-implementation audit — Phase98 reconciliation and primary finding

`PHASE98_OPERATIONAL_TIMING_ARCHITECTURE_REVIEW_PASS` is frozen. The retained Phase98 section below is historical design record. `OPERATIONAL_TIMING_INSTRUMENTATION_REQUIRED`, `PHASE98_PRE_C_SNAPSHOT_FREEZE_REQUIRED`, and `INFORMATION_FREEZE_DEADLINE = C` remain current. Phase96 is unchanged: a selected snapshot requires `identity.captured_at <= C` and `information_cutoff <= C`; no post-C assembly or backdating is authorized. `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remains unresolved.

Primary finding: `CAUSAL_FREEZE_PROVENANCE_BOUNDARY_REQUIRED`. Timing samples alone prove duration, not that a specific immutable prediction input existed by C. Conversely, `HistoricalInputSnapshot.identity.captured_at` is a declared semantic timestamp, not independent proof that persistence completed by C. Freeze `DECLARED_CAPTURED_AT != INDEPENDENT_FREEZE_COMPLETION_PROVENANCE` unless the reviewed persistence boundary proves their relationship.

### Historical pre-implementation observability proposal

Future Phase99 must separate frozen/slotted, content-addressed values:

* `NAROperationalTimingObservation`: schema/version; closed stage; closed scope/correlation identity; causal UTC start/finish; monotonic elapsed duration; success/failure/timeout disposition and stable classification; only safely measurable load context; and an immutable artifact identity/SHA when the stage creates one.
* `NARSnapshotFreezeProvenance`: provider race identity; dataset ID; exact `HistoricalInputSnapshotIdentity`; snapshot content SHA-256; exact C; cutoff-policy identity; cutoff-plan SHA when present; persistence boundary identity; `freeze_completed_at`; exact-reload verification identity/time; and canonical provenance SHA-256.
* `NAROperationalTimingMeasurementConfiguration`: canonical, content-addressed
  operational-regime identity. It binds the reviewed software/provider,
  instrumentation, transport/retry, concurrency, and enabled-stage contracts, but no
  campaign window or observed data.
* `NAROperationalTimingMeasurementSession`: canonical, content-addressed fixed
  campaign-window identity bound to one exact configuration plus the closed v1
  admission/completion rules. It contains no outcome data.

Canonical JSON for session, observation, and freeze provenance is UTF-8, NFC text, `ensure_ascii=False`, `allow_nan=False`, sorted keys, compact separators, UTC timestamps with fixed microseconds, and SHA-256 of exact bytes. No arbitrary metadata bags, exception strings, result, payout, ROI, or future outcome fields are permitted.

### Snapshot-freeze authority contract

The narrow truthful persistence boundary is: successful SQLite transaction commit followed by exact repository reload. `freeze_completed_at` is sampled by an injected, UTC-aware clock only **after** existing `save_snapshot()` returns and `load_snapshot_by_identity()` reconstructs the exact identity, content SHA, and value. It is a conservative upper bound for verified availability, never a caller-supplied `captured_at`, evidence time, C, or request time. Phase99 does not claim stronger physical-media crash durability than the existing SQLite contract provides.

The current `SQLiteHistoricalInputSnapshotRepository.save_snapshot()` owns `BEGIN IMMEDIATE`/commit and returns only after it completes; it also treats an identical existing row as idempotent. A controlled wrapper uses that existing public boundary, exact-reloads the snapshot, samples its own clock, and persists/reloads the receipt in the separate archive. For an identical existing snapshot without an earlier authoritative receipt, the wrapper records the **current verification time**, never a guessed earlier freeze. An exact earlier archived receipt may be reused only under deterministic exact identity/content validation.

The closed decision is `SNAPSHOT_FROZEN_BY_PREDICTION_CUTOFF` only when: exact target/plan/policy binding holds; Phase96 snapshot constraints hold; repository receipt and exact reload agree with the identity/SHA; and `freeze_completed_at <= C`. A completion after C is `SNAPSHOT_FREEZE_COMPLETED_AFTER_PREDICTION_CUTOFF`. Instantiation before C, request start before C, or `identity.captured_at <= C` alone never qualifies.

### Clock, stage, and correlation contracts

Use injected timezone-aware UTC wall clocks for `requested_at`, `observed_at`, persistence/freeze timestamps, activation times, and C comparison. Use injected monotonic timers only for elapsed request, parse, build, persist, prediction, jitter, and contention durations; do not derive distributions by subtracting wall-clock samples. Instrumentation must not modify causal timestamps, C, inputs, or outputs.

`PRE_C` closed/versioned stages are: `SCHEDULER_DISPATCH`; `BOOTSTRAP_HOME_ACQUISITION`; `MONTHLY_ROOT_ACQUISITION`; `LOCATOR_SCRIPT_ACQUISITION`; `MONTHLY_SCHEDULE_ACQUISITION`; `RACE_LIST_ACQUISITION`; `OFFICIAL_RESPONSE_ACQUISITION`; `RAW_CAPTURE_VALIDATION`; `RAW_CAPTURE_PERSISTENCE`; `PARSING`; `NORMALIZATION`; `SOURCE_RECORD_CONSTRUCTION`; `PROVIDER_IDENTITY_BINDING`; `SNAPSHOT_CONSTRUCTION`; `SNAPSHOT_PERSISTENCE`; and `SNAPSHOT_EXACT_RELOAD_CONFIRMATION`. `POST_C` stages are `SNAPSHOT_ADAPTER`, `PREDICTION_PIPELINE`, `ALLOCATION`, `BET_PLAN_CONSTRUCTION`, `BET_PLAN_PERSISTENCE`, and `SHADOW_ARTIFACT_PUBLICATION`.

The daily acquisition application currently exposes synchronous bootstrap/home → monthly-root → locator-script → monthly request/capture → normalization → sequential RaceList capture composition. Its transport/archive protocols can be decorated without changing transport semantics. Official-response and odds functions likewise accept injectable transport/clock collaborators. Raw validation/persistence, parser internals, generic source-record construction, and inner prediction/allocation calls are not all independently hookable today; their detailed spans are conceptual until a reviewed wrapper or hook is introduced. Existing `build_historical_input_snapshot`, the Phase88 binder, `load_snapshot_by_identity`, `build_simulation_race_input_from_historical_snapshot`, and `execute_and_persist_historical_bet_plan` are the narrow public boundaries for grouped spans.

Correlation must use canonical measurement-session identity plus the applicable target-set SHA, cutoff-plan SHA, policy identity, and provider/race identity; fields are required only when their closed scope requires them. It must never use mutable process IDs as the sole join key. Freeze `OBSERVABILITY_CORRELATION_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY` and `OBSERVABILITY_RECORD != POLICY_ACTIVATION_AUTHORITY`.

### Persistence, failure, and aggregation architecture

Recommended architecture: a **separate connection-injected append-only SQLite observability archive**, following existing NAR capture-archive schema-gate conventions. It stores canonical sessions, timing observations, and freeze-provenance rows with content-addressed primary identities, immutable UPDATE/DELETE rejection, exact read reconstruction, and independent schema verification. It must not alter Phase96 snapshot tables or artifacts and must not use `resolution_outcomes_json`. Cross-database atomicity is intentionally not claimed: the source snapshot first commits through its existing repository, then the archive records/verifies provenance. A failed required provenance append leaves the prediction artifact unchanged but makes that target ineligible for official shadow qualification; it is not repairable by inventing a later freeze time.

Metric-only observation failure must not change prediction inputs, C, or model output; its sample is unusable/explicitly absent. Required freeze-provenance persistence or exact-reload failure likewise must not mutate prediction behavior, but it fails closed for official shadow/ROI qualification. Every timeout/failure observation stays in the timing denominator. A read-only aggregation/report layer groups only by session/configuration identity, stage, request/source type, venue where applicable, and measured concurrency regime; it reports count, median, p90, p95, p99 when statistically supported, maximum, timeout/failure rate, and never drops unfavorable samples.

### Δ-review handoff, blockers, and future scope

A later Δ review needs an immutable package proving measurement-session configuration, sample period, race/venue count, timeout/failure denominator, pre-C distributions, concurrency/load coverage, clock-skew assumption/evidence, and reviewed safety-margin rule. Only that independent review can resolve `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`. Different timeout/retry/concurrency regimes produce different session/configuration identities and cannot be silently pooled.

Phase99 does not resolve `HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS`, `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`, or `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`. Timing campaigns can proceed independently, but official strict shadow eligibility and ROI remain separately gated. Policy activation remains a later immutable authority: a concrete policy activation must consume reviewed timing evidence without treating a session, correlation, or provenance record as authorization.

Revised future implementation scope, subject to another approval: create
`scripts/simulation/nar_operational_timing_observability.py`,
`scripts/simulation/nar_operational_timing_observability_archive_migration.py`,
`scripts/simulation/sqlite_nar_operational_timing_observability_archive.py`, and
`scripts/simulation/historical_input_snapshot_freeze_receipt.py`; create focused
tests `tests/test_nar_operational_timing_observability.py`,
`tests/test_nar_operational_timing_observability_archive_migration.py`,
`tests/test_sqlite_nar_operational_timing_observability_archive.py`, and
`tests/test_historical_input_snapshot_freeze_receipt.py`; and modify only the two
phase-control documents. The controlled freeze-receipt service must compose existing
snapshot `save_snapshot` and exact `load_snapshot_by_identity` boundaries, without
changing generic snapshot/repository semantics. No live timing adapter, transport
timeout/retry change, concurrency/scheduler change, target-discovery change, Phase96
change, model change, or policy/session activation authority is in scope. No path is
authorized in this PREPARE.

Required eventual tests: canonical immutable payload/SHA and closed stages; monotonic duration unaffected by UTC adjustment; exact UTC causal timestamps; no outcome/result/payout/ROI inputs; receipt/reload identity-SHA binding; completion at/before C qualification and after-C rejection; no forged freeze time from `captured_at`; metric failure noninterference; required provenance failure official-qualification block; timeout/failure denominator retention; retry/C and after-C evidence exclusion; correlation-not-authorization; incompatible-session aggregation rejection; no artifact mutation; and race-concurrency isolation.

Explicit non-goals: choose Δ; provider HTTP/live sampling; scheduler/retry/concurrency/timeout changes; Phase96 snapshot changes or backdating; policy activation; status-source semantics; market eligibility; ROI evaluation; or historical-race rescue.

At the historical PREPARE checkpoint, the recommended Phase99 disposition was `DRAFT_FOR_REVIEW` for independent architectural review. That review and the measurement-contract revision later passed; the current implementation state is recorded at the top of this document.

### Phase99 PREPARE scope

Modified only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. Tests, network/provider activity, DB writes, staging, commit, and push are absent.

Historical PREPARE next action was `CHATGPT_REVIEW_PHASE99_TIMING_OBSERVABILITY`.

---

## Historical Record — POST_V0_8_DAILY_REPLAY_98

Title: NAR Prospective Shadow Operational Timing Architecture

Formal Status: DRAFT_FOR_REVIEW

Design Review: PENDING

Base Commit and Branch: `7ec5afbe89d65803ba63d357a1d07e68c4c7e30a` / `feature/post-v0.8-daily-replay`

State: DRAFT_FOR_REVIEW

Outcome: READY_FOR_ARCHITECTURAL_REVIEW

Audit: NAR_PROSPECTIVE_OPERATIONAL_TIMING_ARCHITECTURE_AUDIT_COMPLETE

Authorization: NONE_REQUIRED_AUDIT_ONLY

### Phase97 formal reconciliation

`PHASE97_IMPLEMENTATION_REMOTE_VERIFICATION_PASS` is frozen. `POST_V0_8_DAILY_REPLAY_97 = FORMALLY_COMPLETE` and `NAR_FIXED_OFFSET_PREDICTION_CUTOFF_POLICY_AND_PLAN_PRODUCER = FORMALLY_INTEGRATED`.

`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remains unresolved. `POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY` and `PREDICTION_CUTOFF_POLICY_PROVENANCE_UNAVAILABLE` remain current strict-historical safeguards. The retained Phase97 content below is historical implementation record.

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `7ec5afbe89d65803ba63d357a1d07e68c4c7e30a` / `f4c53ab670bfd52fdc1f581e6baae63a7ae5d154`

### Primary operational timing finding

Primary classification: `OPERATIONAL_TIMING_INSTRUMENTATION_REQUIRED`. No independently auditable measurement series exists for provider latency, request volume, retries, local processing, SQLite/filesystem contention, scheduler jitter, or simultaneous venue load. The repository therefore cannot justify a concrete fixed Δ.

Architecture verdict: `PHASE98_PRE_C_SNAPSHOT_FREEZE_REQUIRED`. Phase96 requires selected prediction snapshots to satisfy `identity.captured_at <= C` and `information_cutoff <= C`; the snapshot domain already enforces `captured_at <= information_cutoff <= scheduled_start_at` and evidence `observed_at`/`available_at <= captured_at`. Therefore `INFORMATION_FREEZE_DEADLINE = C`: the complete immutable `HistoricalInputSnapshot` must be constructed and persisted no later than C. A post-C assembly is not a pre-C capture and must never be backdated.

`OPERATIONAL_COMPLETION_DEADLINE` is a separate, future-reviewed action/shadow deadline. After the exact snapshot has frozen by C, pure prediction, stake-plan computation, and shadow-artifact publication may occur after C only from that snapshot and pre-approved deterministic strategy/configuration, with no new prediction-time provider input or after-C evidence. Phase98 does not select that deadline. Allowing later snapshot assembly from a separately frozen evidence bundle would require a separately reviewed pre-C freeze artifact/provenance contract and likely a change to the meaning or use of `HistoricalInputSnapshot.identity.captured_at`; it is explicitly not recommended or implemented here.

### Prospective pre-C dependency graph

```text
schedule/target discovery
  → canonical target set
  → activated fixed policy + cutoff plan
  → pre-C source request and immutable raw capture
  → raw validation, parsing, normalization, source-record production, identity binding
  → complete HistoricalInputSnapshot construction
  → snapshot persistence and immutable freeze by C
  → post-C, pre-action prediction and stake-plan generation from that snapshot
  → immutable shadow prediction/provenance publication
  → later settlement/result comparison
```

`PRE_C_FREEZE_CRITICAL_PATH` comprises dispatch/jitter, all prediction-relevant acquisition and request sequencing, provider throttle/retry/timeout budget, immutable raw persistence, validation, parsing, normalization, source-record derivation, identity binding, complete snapshot construction, snapshot persistence, contention/concurrency effects, and clock-skew allowance. It must complete by C. `POST_C_COMPUTE_CRITICAL_PATH` comprises snapshot-to-model adaptation, inference, stake allocation, bet-plan construction, and artifact publication; it is sized against the later operational completion deadline, not automatically against Δ. Results/payouts/settlement remain post-race.

### Current acquisition, concurrency, and retry facts

`scripts/simulation/nar_daily_target_live_acquisition.py::NARDailyTargetLiveAcquisitionApplication.acquire` obtains bootstrap resources, monthly schedule, then iterates venue RaceList captures sequentially. `scripts/simulation/nar_historical_daily_target_source.py::normalize_nar_race_list` derives per-race scheduled starts in JST and normalizes them to UTC. The domain can represent all venues/races for one day, but it provides no worker count, concurrency limit, priority rule, throttle contract, or meeting-load guarantee. Near-simultaneous races across venues and overlap between one race's capture and another race's preparation must be load-tested before Δ is selected.

Existing bootstrap, daily-target, and general official NAR transports use bounded HTTPS requests with connect/read timeouts of 10/10 seconds and `max_retries=0`; current odds raw acquisition uses 10/20 seconds and `max_retries=0`. There is no reviewed retry/backoff budget. A future capture policy must predeclare attempt count, timeout, backoff, and deadline budget. A response observed after C may be retained only as diagnostic append-only raw evidence; it must be excluded from the C prediction snapshot and cannot move C or trigger an evidence-dependent retry choice.

The verified transport facts are exact: historical daily-target transport 10s/10s with `HTTPAdapter(max_retries=0)`; bootstrap transport 10s/10s with `max_retries=0`; official response live capture 10s/10s with `max_retries=0`; and market-odds raw acquisition 10s/20s with `max_retries=0`. These describe current code only, not an approved operational retry policy. A request begun by C but fully observed after C is not prediction-eligible: `requested_at <= C` is insufficient. A retry never moves C, and a late response must not be substituted merely to make a target executable.

### Timing inventory, clock, and measurement protocol

Measure `PRE_C_FREEZE_CRITICAL_PATH` separately: dispatch-to-request, connect/read, raw validation/persistence, parsing, normalization, source-record derivation, identity binding, snapshot construction, and snapshot persistence. Measure `POST_C_COMPUTE_CRITICAL_PATH` separately: snapshot adapter, model/prediction, stake allocation, bet-plan construction, and artifact persistence. Record `SHARED_ENVIRONMENT` effects separately: process startup, SQLite/filesystem contention, concurrent venues, provider throttling, worker availability, and clock skew. Local work is deterministic/local but measurable; transport/throttling/shared-resource behavior is externally variable and currently unknown.

Future timing records need timezone-aware UTC-compatible wall-clock timestamps for causal evidence/scheduler audit and an injected monotonic timer for elapsed durations. Do not derive latency distributions by subtracting independently sampled wall clocks. Instrumentation must not alter evidence timestamps or prediction behavior. Clock synchronization/skew needs a reviewed bound before activation. Measurements must be prospective and outcome-independent, grouped by provider/source, request type, venue, concurrent-meeting count, and operational time window only where relevant. Record count, median, p90, p95, p99 when sample size supports it, maximum, and timeout/failure rate; never group or tune by result, payout, ROI, profitability, or later status.

### Future Δ selection and activation handoff

After an independently reviewed normal-and-stressed prospective sample period, a later policy may select Δ only from the full `PRE_C_FREEZE_CRITICAL_PATH` envelope plus reviewed safety margin and clock-skew allowance. The selection inputs are measured timing distributions, required request inventory, concurrency/throttle policy, timeout/retry policy, clock-skew bound, and declared safety/confidence criteria. Post-C pure inference is excluded unless a later action contract requires it before C. Outcomes, evidence convenience, executability, odds, status changes, and replay performance are prohibited inputs. Any Δ change creates a new Phase97 policy identity and distinct activation/analytical period; periods must not be silently merged.

Future immutable policy activation provenance must bind the exact policy identity and canonical policy SHA, provider scope, activation timestamp, effective-from time, optional effective-until time, reason/audit identity, and its own content SHA. It must be finalized before every covered target outcome; a caller-set authorization flag is insufficient. This future authority is separate from the Phase97 policy object.

### Source-semantic impact and candidate instrumentation boundaries

Timing work cannot make NAR source semantics complete. The blockers have distinct effects:

| Activity or claim | Effect |
| --- | --- |
| Passive timing instrumentation | Not blocked. |
| Measuring current acquisition, parsing, and snapshot construction timing without official-admissibility claims | May proceed safely. |
| Structurally constructing a current `HistoricalInputSnapshot` | Not categorically blocked solely by the Phase94/95 status-authority blockers. |
| Claiming complete authoritative entry status | Blocked by `HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS` and `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`. |
| Claiming market or positive-market eligibility | Blocked by `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`. |
| Official strict prospective shadow eligibility and official ROI evaluation | Blocked until all required independent semantic authorities are reviewed. |

Candidate future paths, subject to a separate approved instrumentation design, are: instrumentation-only `scripts/simulation/nar_operational_timing_observability.py` and focused test; acquisition boundaries `scripts/simulation/nar_daily_target_live_acquisition.py`, `scripts/simulation/nar_historical_daily_target_live_capture.py`, `scripts/simulation/nar_historical_daily_target_bootstrap_live_capture.py`, `scripts/simulation/nar_official_response_live_capture.py`, and optional `scripts/simulation/nar_market_odds_raw_acquisition.py`; pre-C freeze boundaries `scripts/simulation/nar_historical_input_source.py` and `scripts/simulation/historical_input_snapshot_builder.py`; post-C compute `scripts/simulation/historical_prediction_bet_plan_execution.py`; artifact persistence `scripts/simulation/persisted_bet_plan_service.py`; and later scheduler/activation modules. No path is approved for change in Phase98.

Required eventual tests include injected monotonic-clock duration measurement and UTC audit timestamps; exact C preservation under retries; rejection of responses observed after C; after-C diagnostic isolation; timeout fail-closed behavior; no outcome/result/payout/settlement dependencies; concurrency isolation between races; stable policy identity during one activation period; snapshot completion by C; and proof that observability failures cannot change causal admission or predictions.

Explicit non-goals: selecting Δ, timing benchmarking, scheduler implementation, live acquisition, policy activation persistence, status/odds authority, market eligibility, whole-meeting cancellation, ROI evaluation, historical rescue, or outcome/evidence-adaptive timing.

Recommended formal Phase98 disposition: remain `DRAFT_FOR_REVIEW` for independent architectural review. Recommended next step: `OPERATIONAL_TIMING_INSTRUMENTATION_REQUIRED` — design passive prospective instrumentation and its causal telemetry boundary before collecting measurements; do not design the shadow scheduler until that instrumentation contract determines the full pre-C freeze envelope.

### Phase98 PREPARE scope

Modified only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. Tests, network/provider activity, DB writes, staging, commit, and push are absent.

Next: `CHATGPT_REVIEW_PHASE98_OPERATIONAL_TIMING`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_97

### Phase96 formal reconciliation

`PHASE96_IMPLEMENTATION_REMOTE_VERIFICATION_PASS` is frozen. `POST_V0_8_DAILY_REPLAY_96 = FORMALLY_COMPLETE`; `NAR_PREDICTION_CUTOFF_PLAN_AND_V017_PROVENANCE = FORMALLY_INTEGRATED`; and `PHASE93_CUTOFF_CONTRACT_REQUIRES_HARDENING = RESOLVED_BY_PHASE96`.

The completed Phase96 contract already owns exact C validation, resolver propagation, Phase93 temporal comparison, orchestration/audit binding, v017 companion provenance, and strict aggregation. It does not select C. The historical material below is explicitly a pre-Phase96 architecture record and is not a current Phase93 defect.

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `974808ee888de36bbdbf5f409922ccb21038ba67` / `d18e8350781ed05b9322e59f76737cdbee4c00ac`

### Phase97 implementation result

The immutable/slotted `NARHistoricalReplayPredictionCutoffPolicy` fixes NAR/nar_official, `FIXED_OFFSET_BEFORE_SCHEDULED_START`, the reviewed scheduled-start basis, and versioned boundary semantics. One positive exact integer `offset_microseconds` is validated for exact `timedelta` representability; no operational value or maximum is selected. Canonical UTF-8 JSON uses sorted keys, compact separators, `ensure_ascii=False`, and `allow_nan=False`. SHA-256 of those bytes derives `nar-prediction-cutoff-policy-v1:<digest>`; callers cannot supply a detached identity.

The pure keyword-only producer creates the existing Phase96 `NARHistoricalReplayPredictionCutoffPlan` for the exact canonical target set, using `C = scheduled_start_at - timedelta(microseconds=offset_microseconds)` for every target. It reuses Phase96 validation. No network, filesystem, clock, SQLite, snapshot, odds, status, result, payout, settlement, replay, or persistence authority was added.

`POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY` remains explicit. The policy and producer prove semantics and deterministic derivation, not authorization time. A retrospective plan without separately reviewed pre-outcome activation provenance remains `PREDICTION_CUTOFF_POLICY_PROVENANCE_UNAVAILABLE` for strict historical use. Phase96 orchestrator, resolver, eligibility, persistence, aggregation, and v017 contracts are unchanged. `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remains unresolved.

Validation: new focused policy test `19 passed`; Phase96 cutoff-plan `4 passed`; historical replay eligibility `8 passed, 5 subtests`; SQLite daily evidence resolver `27 passed, 38 subtests`; NAR daily replay orchestrator `23 passed, 11 subtests`; full repository suite `4,547 passed, 2 skipped, 2,846 subtests passed`. The skips are existing platform-conditional cases. Phase97 changed paths are exactly the new policy module, its focused test, and these two phase-control documents. Production policy DB writes and Provider HTTP / Phase44 / GET are `0` / `0 / 0 / 0`.

### Phase97 finding and policy boundary

Primary finding: `OUTCOME_INDEPENDENT_FIXED_OFFSET_POLICY_REQUIRES_OPERATIONAL_PARAMETER_APPROVAL`. The approved policy family is a fixed offset: `C = scheduled_start_at - Δ`, where one immutable policy applies to every target in the exact canonical target set. It is deterministic, outcome-independent, race-order independent, and fits Phase96 without changing provider target/denominator identity.

Architecture verdict: the fixed-offset policy mechanism is implementable as a pure plan producer, while strict historical admissibility authorization remains future-gated. Concrete blocker: `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`. No concrete initial `Δ` is frozen in Phase97. The repository proves schedule identity and C propagation but contains no pre-outcome operational measurement of capture latency, prediction/bet-plan duration, concurrency under overlapping races, provider throttling/retry behavior, clock synchronization, or provider delivery margin. An arbitrary offset would be a disguised unreviewed operating policy. A later operational timing audit must choose a positive fixed duration before a prospective shadow scheduler is authorized.

### Fixed-offset policy semantics and canonical identity

Future `NARHistoricalReplayPredictionCutoffPolicy` is frozen/slotted and is only a deterministic semantic specification. Its canonical UTF-8 NFC JSON contains exactly versioned semantic material: `schema_version`; `organization=NAR`; `source_system=nar_official`; closed `policy_kind=FIXED_OFFSET_BEFORE_SCHEDULED_START`; `offset_microseconds`; closed `scheduled_start_basis=DAILY_HISTORICAL_REPLAY_TARGET_SCHEDULED_START_AT_V1`; and a versioned `boundary_semantics=C_EQUALS_SCHEDULED_START_AT_MINUS_OFFSET`. It excludes race result, payout, odds, evidence availability, status change, ROI, database state, current clock, run ID, and race-specific overrides. JSON uses `ensure_ascii=False`, `allow_nan=False`, sorted keys, and compact separators. `SHA256(canonical policy JSON bytes)` produces the sole public identity `nar-prediction-cutoff-policy-v1:<policy_sha256>`.

`offset_microseconds` is an exact built-in `int`, with `bool` rejected, and must be strictly greater than zero. Float, `Decimal`, free-form duration text, and a per-target value are invalid. Phase97 defines neither an operational maximum nor a concrete offset. Any material semantic change, including the offset, changes the policy SHA/identity; duration is timezone-independent because its canonical representation is integer microseconds.

Frozen invariant: `POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY`. Policy semantics answer what rule computes C; policy identity content-addresses that rule; authorization/activation provenance independently proves when it was frozen for a relevant use. A SHA can be computed after results are known and never proves pre-outcome selection by itself.

The pure producer `build_nar_historical_replay_prediction_cutoff_plan(*, target_set, policy)` accepts only the exact canonical `DailyHistoricalReplayTargetSet` and exact NAR policy. It traverses exact canonical target order and produces the existing Phase96 plan with each `C = target.scheduled_start_at - timedelta(microseconds=policy.offset_microseconds)`. Its `cutoff_policy_identity` is derived from that policy object; callers never independently supply an opaque identity string plus offset. Missing start, nonpositive/malformed duration, unsupported provider/policy, target omission, extra/duplicate target, or target-set contradiction fails closed. It reads no database, snapshot, status authority, odds, result, payout, settlement, wall clock, or network source; it has no target-specific override or evidence-dependent fallback. Same target set plus same policy produces identical plan bytes/SHA; a material policy difference yields a different policy identity and, when its offset differs, a different C/plan SHA.

### Historical authorization is a separate later gate

The Phase97 policy and producer do not issue pre-outcome policy authority. A newly derived valid plan is `DETERMINISTIC_RETROSPECTIVE_PLAN` unless it carries independently auditable pre-outcome policy authorization/activation provenance or equivalent previously frozen pre-outcome plan provenance. Without either, strict historical use stays fail closed as `PREDICTION_CUTOFF_POLICY_PROVENANCE_UNAVAILABLE`. Determinism, a valid SHA, fixed offset, executable resolution, or favorable ROI cannot retrospectively authorize it.

### Anti-hindsight, shadow, and historical-admissibility rules

The policy and resulting plan must be frozen before resolver invocation and before any outcome information. They may not be selected or adjusted using evidence availability, later withdrawals, later odds, result, payout, profitability, replay success, or executable status. “Use a different C when a preferred snapshot is absent” is prohibited.

For prospective shadow operation, an operational Δ is approved first; target schedule is obtained; target set plus approved policy deterministically produce C and the plan; the plan is frozen before evidence resolution; then a future scheduler acquires and predicts within the precomputed deadline window before outcomes arrive. The scheduler must retain its separate activation/provenance record. Phase97 neither designs that scheduler nor performs capture. Historical use is admissible only with independently auditable pre-outcome policy activation or previously frozen plan provenance. Constructing a new plan after inspecting archives cannot make a replay eligible.

### Orchestrator integration decision

Phase97 chooses architecture **A**: add only the pure policy plus plan producer. The completed Phase96 `run_nar_daily_replay(...)` already accepts and retains an exact, target-set-bound cutoff plan; its resolver, eligibility, audit, persistence, and aggregation contracts consume that plan. Requiring an extra policy object there would not establish its pre-outcome authorization and would expand established APIs without closing the missing provenance boundary. A later reviewed policy-provenance/shadow-operation phase must enforce activation provenance before an official strict historical/ROI path can rely on a plan. Thus a syntactically valid Phase96 plan is not, by itself, historical admissibility authority.

Phase94/95 remain `HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS` and `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`. Phase41 remains `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`; market eligibility, positive market eligibility, odds authority, and whole-meeting cancellation remain unsupported.

### Expected Phase97 implementation scope

Create `scripts/simulation/nar_historical_replay_prediction_cutoff_policy.py` and `tests/test_nar_historical_replay_prediction_cutoff_policy.py`; modify only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. The policy module produces the existing fully validated Phase96 plan type and does not assert authorization provenance. Therefore no resolver, orchestrator, persistence, aggregation, target-discovery, scheduler, migration, or database path changes are required for this narrow semantic mechanism.

Required eventual tests: deterministic canonical policy bytes/SHA/public identity; timezone irrelevance to offset representation; exact `int` required with bool/zero/negative/float/free-form duration rejection; material offset change changes policy SHA/identity; same exact target set/policy produces identical plan; changed offset changes plan SHA; every C is exact start-minus-offset; canonical target order and missing start failure; no network, DB, clock, snapshot, status, odds, result, payout, or settlement access; no per-target override/fallback; plan identity exactly equals the derived policy identity; no API permits contradictory detached identity/offset; producer does not claim pre-outcome authorization; and deterministic scheduler-facing consumption.

### Historical Phase97 PREPARE scope

At the PREPARE stage, the audit changed only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. The subsequent independent architectural review passed and authorized the narrow implementation recorded above.

The earlier recommendation was to request architectural review of the pure semantic producer while leaving Δ and pre-outcome authorization unresolved. That review passed; Phase97 now awaits independent implementation review.

### Phase97 Approved Implementation Contract (executed)

The independent architectural review passed: `PHASE97_PREDICTION_CUTOFF_POLICY_DESIGN_REVIEW_PASS`. The approved implementation is the pure fixed-offset policy domain and deterministic Phase96 plan producer only. Concrete Δ, policy activation provenance, scheduler, and live acquisition remain outside this implementation.

### Phase97 Allowed Files

- `scripts/simulation/nar_historical_replay_prediction_cutoff_policy.py`
- `tests/test_nar_historical_replay_prediction_cutoff_policy.py`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

### Phase97 Forbidden Files

Every other path, including Phase96 orchestrator, resolver, eligibility, persistence, aggregation, result repository, v017 migration, migration runner, provider target discovery, database, fixtures, and logs.

### Phase97 Required Tests and Checks

Run the new focused policy test; existing Phase96 cutoff-plan, historical replay eligibility, SQLite daily evidence resolver, and NAR daily replay orchestrator tests; then the full repository pytest suite. All must pass. Run `git diff --check`, inspect `git status --short`, and verify exact changed paths before the approved commit and normal push.

### Phase97 Stop Condition

Stop if the baseline advances, an unexpected non-doc change exists, an out-of-scope production path is required, the pure contract cannot be implemented without a forbidden dependency, a concrete Δ or historical authority would need to be fabricated, a required test fails outside approved scope, or push would require force.

### Historical pre-Phase96 architecture record (superseded)

### Phase95 reconciliation

`PHASE95_PROSPECTIVE_STATUS_CAPTURE_REVIEW_PASS` and `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS` are frozen. This audit changes neither the unresolved status-source semantics nor the current target's `HISTORICAL_REPLAY_BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE` result.

### Reviewed pre-implementation cutoff semantics

| Contract | Represented moment | Current causal rule | Coherence finding |
| --- | --- | --- | --- |
| `DailyHistoricalReplayTarget.scheduled_start_at` | Scheduled race start; may be absent | Upper bound only, not an observation or decision time | It is not an explicit prediction information cutoff. |
| `HistoricalInputSnapshot.information_cutoff` and `captured_at` | Snapshot's logical prediction boundary and its assembly/capture time | `captured_at <= information_cutoff <= scheduled_start_at`; every prediction evidence `observed_at` and, when present, `available_at` is no later than capture/cutoff | The snapshot domain already supports a true per-snapshot cutoff. |
| SQLite NAR daily evidence resolver | Latest stored NAR snapshot under the start-time bound | It accepts snapshots whose capture and own cutoff are each `<= scheduled_start_at`, then selects the greatest `captured_at`; it calls the repository with `information_cutoff=target.scheduled_start_at` | It defines “latest causal before start,” not one reviewed race-level decision moment. |
| `NARHistoricalEntryStatusAuthority` / Phase93 eligibility | Status source availability and observation | Both `available_at` and `observed_at` need only be `<= target.scheduled_start_at` | A T-5 status authority is accepted even if other replay inputs are selected at T-1. |
| `settlement_information_cutoff` | Later settlement/result/payout selection boundary | Result/payout capture observation must be `<= settlement_information_cutoff` | Separate and correctly not a prediction-time cutoff. |
| NAR daily orchestration | Eligibility then evidence resolution | It passes the same target set to Phase93 and the resolver but supplies no prediction cutoff C | No component binds all prediction evidence to one explicit C. |

The frozen contract is therefore model **A**: deterministically select everything causally known at any time before `scheduled_start_at`. It is reproducible for an unchanged dataset, but insufficient for strict single-decision-time replay because the selected status and prediction inputs need not describe the same information universe.

### Final architectural revision — separate cutoff-plan authority

Historical pre-Phase96 classification: `PREDICTION_CUTOFF_MODEL_REQUIRES_EXPLICIT_CUTOFF`; its Phase93 compatibility finding was `PHASE93_CUTOFF_CONTRACT_REQUIRES_HARDENING`. Both are superseded by the completed Phase96 implementation: `PHASE93_CUTOFF_CONTRACT_REQUIRES_HARDENING = RESOLVED_BY_PHASE96`.

`DailyHistoricalReplayTarget` and `DailyHistoricalReplayTargetSet` remain provider-discovered denominator/acquisition authority. They must not gain `prediction_information_cutoff`: the same exact target-set content SHA remains reusable under independently selected replay policies. Target-set identity answers *which provider races form the denominator*; cutoff-plan identity answers *which causal evidence boundary an experiment applies to that denominator*.

#### Canonical cutoff-plan contract

The new immutable domain is `NARHistoricalReplayPredictionCutoffPlan` with exact versioned, content-addressed canonical JSON. Its content contains:

- `schema_version`
- `target_set_content_sha256`
- closed `cutoff_policy_identity`
- exact canonical target coverage
- target-set-order-preserving per-target decisions, each `(organization, source_system, external_race_id, prediction_information_cutoff)`

Canonical plan bytes are UTF-8 JSON with `ensure_ascii=False`, `allow_nan=False`, `sort_keys=True`, and `separators=(",", ":")`. Every datetime is normalized to UTC and encoded with fixed microseconds (`+00:00`). `prediction_cutoff_plan_sha256 = SHA-256(canonical plan JSON bytes)`.

Validation fails closed for a target-set SHA mismatch; missing, extra, duplicate, or incorrectly ordered target coverage; a missing scheduled start or C; and `C > target.scheduled_start_at`. Same target-set content with any different C must yield a different plan SHA. Phase96 defines no T-minus-N rule, capture schedule, or other C-selection policy; Phase97 alone may design that outcome-independent producer.

#### Temporal status-authority contract

`STATUS_OBSERVED_AT_CAPTURE_TIME` does **not** imply `STATUS_VALID_THROUGH_PREDICTION_CUTOFF`. A complete status universe observed at T cannot automatically authorize a later C: for example, an observation at T-5 cannot prove that no change occurred before C at T-1. A capture-time semantic can reproduce knowledge at its exact observation boundary only; it must not be called provider state valid through a later C. `STATUS_VALID_THROUGH_PREDICTION_CUTOFF` requires separate reviewed immutable source/archival proof of that validity interval and may never be inferred from timestamp ordering.

Phase93 must receive the validated plan and compare authority `available_at` and `observed_at` with exact target C, not scheduled start. Unless reviewed authority semantics explicitly prove coverage through C (or exactly represent C as the capture-time decision boundary), the target remains `BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`. Phase94/95 source-semantics blockers and the current target's block remain unchanged.

#### Resolver and orchestration contract

For prediction snapshots, every selection-bound use of `target.scheduled_start_at` changes to exact target C: require `snapshot.identity.captured_at <= C`, `snapshot.information_cutoff <= C`, and repository lookup with `information_cutoff=C`. Scheduled start remains target/race identity validation only. `HistoricalInputSnapshot` already content-binds its local cutoff and receives no new field. Settlement remains governed exclusively by `settlement_information_cutoff`.

`run_nar_daily_replay(...)` must receive the exact plan as a required keyword-only argument, validate that it binds exactly to `acquisition_result.target_set` before Phase93 eligibility and SQLite evidence resolution, and pass the same plan to both. `NARDailyReplayOrchestrationResult` must retain the exact plan, not a detached SHA. The canonical orchestration audit must bind at least `prediction_cutoff_plan_sha256`; because that SHA content-addresses policy identity and all C values, same target set plus same selected snapshots plus different C must yield different `orchestration_audit_sha256`.

#### v017 companion persistence and migration compatibility

`resolution_outcomes_json` remains a closed outcomes-only projection. The required v017 design is an append-only one-to-one companion table/projection, owned by the existing `SQLiteNARDailyReplayResultRepository` rather than a split repository, with at least:

- `persisted_content_sha256` as companion primary key and FK to `nar_daily_replay_results.persisted_content_sha256`, with `ON DELETE RESTRICT` and `ON UPDATE RESTRICT`
- `prediction_cutoff_plan_sha256` (explicitly **not** UNIQUE; one plan may support many runs/strategies/configurations)
- canonical `prediction_cutoff_plan_json`

The companion rejects UPDATE and DELETE. Repository/domain validation must reconstruct canonical plan bytes, reproduce its SHA, and require its target-set SHA to equal the parent v016 row's `target_set_content_sha256`; all disagreement fails closed. A v017-backed persisted-content identity must bind the exact companion plan payload as well as parent content. Legacy v016-only identities remain their original immutable v016 values; they are never rewritten, deleted, inferred from scheduled start, synthesized, or backfilled, and are exposed only as `PREDICTION_CUTOFF_PROVENANCE_UNAVAILABLE` / fail-closed for strict consumers.

The existing repository currently requires exact registered migrations 8–16 and would reject a valid v017 database. Its future schema verifier must require the exact registry through v017, continue to validate untouched v016 table/schema/triggers through `require_v016_schema_contract`, and independently validate v017 companion columns, key/FK, canonical payload contract, and immutability triggers. v016 objects themselves stay byte-for-byte/structurally unchanged.

Publication must insert the v016 parent and v017 companion in one SQLite transaction. A committed success cannot contain a parent without its companion. The transaction must roll back on companion failure, support exact idempotent re-publication, reject conflicting companions, and exact-reload the combined authority after commit. No repair/backfill path is permitted.

#### Aggregation contract

Strict aggregation must require a valid v017 companion for every selected persisted result and reject a legacy v016-only row. It must trace each selected `persisted_content_sha256` through its exact companion, plan SHA, and canonical per-target C. It must add `cutoff_policy_identity` to analytical compatibility, while allowing different `prediction_cutoff_plan_sha256` values across different target dates. Different policy identities must fail compatibility rather than aggregate silently.

#### Exact eventual implementation scope and test matrix

Expected production paths are:

- create `scripts/simulation/nar_historical_replay_prediction_cutoff.py`
- modify `scripts/simulation/sqlite_nar_daily_evidence_resolver.py`
- modify `scripts/simulation/nar_historical_replay_eligibility.py`
- modify `scripts/simulation/nar_daily_replay_orchestrator.py`
- modify `scripts/simulation/nar_daily_replay_result_persistence.py`
- modify `scripts/simulation/nar_daily_replay_aggregation.py`
- modify `scripts/simulation/repositories/sqlite_nar_daily_replay_result_repository.py`
- create `scripts/migrations/versions/v017_nar_daily_replay_prediction_cutoff_schema.py`
- modify `scripts/migrations/runner.py`

No new companion repository is needed: the existing result repository must own one parent-plus-companion transaction. Expected tests are new `tests/test_nar_historical_replay_prediction_cutoff.py` plus changes to `tests/test_nar_historical_replay_eligibility.py`, `tests/test_sqlite_nar_daily_evidence_resolver.py`, `tests/test_nar_daily_replay_orchestrator.py`, `tests/test_nar_daily_replay_result_persistence.py`, `tests/test_nar_daily_replay_aggregation.py`, `tests/test_sqlite_nar_daily_replay_result_repository.py`, and `tests/test_historical_input_snapshot_migration.py`.

Required eventual coverage includes: same target set plus different C gives different plan SHA; deterministic canonical target order; timezone-equivalent timestamps canonicalize identically; missing, extra, or duplicate targets; missing scheduled start; C after scheduled start; resolver rejection of `captured_at > C` and `information_cutoff > C`; repository lookup at C; Phase93 comparison at C; non-promotion of a capture-time status observation into valid-through-C; same snapshots plus different C gives different audit SHA; prediction-cutoff independence from settlement cutoff; untouched v016 table/schema/triggers; idempotent v017 runner; updated repository acceptance of an exact v017 database; malformed v017 rejection; unchanged legacy v016 values; companion UPDATE/DELETE rejection; corrupt plan SHA, noncanonical plan JSON, and parent/target-set mismatch rejection; atomic rollback on companion failure; identical idempotent publication; conflicting companion rejection; strict aggregation rejection of a legacy row; same `cutoff_policy_identity` with different daily plan SHAs accepted; mixed policy identities rejected; and a green full regression suite.

`historical_daily_targets.py`, provider target discovery, target-set denominator semantics, `HistoricalInputSnapshot` schema, snapshot builder, and settlement-cutoff semantics remain out of scope unless a later reviewed contradiction proves otherwise.

Phase41 remains unresolved: `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`. `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`, `market_eligibility = UNSUPPORTED`, `positive_market_eligibility = UNSUPPORTED`, and `WHOLE_MEETING_CANCELLATION = UNSUPPORTED` remain unchanged.

### Historical Phase96 Allowed Files

- `scripts/simulation/nar_historical_replay_prediction_cutoff.py`
- `scripts/simulation/sqlite_nar_daily_evidence_resolver.py`
- `scripts/simulation/nar_historical_replay_eligibility.py`
- `scripts/simulation/nar_daily_replay_orchestrator.py`
- `scripts/simulation/nar_daily_replay_result_persistence.py`
- `scripts/simulation/nar_daily_replay_aggregation.py`
- `scripts/simulation/repositories/sqlite_nar_daily_replay_result_repository.py`
- `scripts/migrations/versions/v017_nar_daily_replay_prediction_cutoff_schema.py`
- `scripts/migrations/runner.py`
- `tests/test_nar_historical_replay_prediction_cutoff.py`
- `tests/test_nar_historical_replay_eligibility.py`
- `tests/test_sqlite_nar_daily_evidence_resolver.py`
- `tests/test_nar_daily_replay_orchestrator.py`
- `tests/test_nar_daily_replay_result_persistence.py`
- `tests/test_sqlite_nar_daily_replay_result_repository.py`
- `tests/test_nar_daily_replay_aggregation.py`
- `tests/test_historical_input_snapshot_migration.py`
- `tests/test_simulation_migrations.py`
- `tests/test_nar_official_response_capture_migration.py`
- `tests/test_simulation_bet_plan_migration.py`
- `tests/test_sqlite_persisted_simulation_application.py`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

### Historical Phase96 Forbidden Files

Every other path, including provider target discovery, historical target identity, snapshot schemas, settlement domains, fixtures, capture archives, `database/**`, and `logs/**`.

### Historical Phase96 Required Tests and Checks

Run the new cutoff-plan test and focused Phase93, resolver, orchestrator, persistence, SQLite repository, aggregation, v017 migration and simulation migration tests; then run the full repository pytest suite. All must pass. Require `git diff --check`, exact scope audit, and `git status --short` before the approved one-commit normal push.

### Historical Phase96 Stop Condition

Stop if the remote baseline advances, an unapproved path or provider-denominator change is required, a fail-closed invariant cannot be represented, or a required test fails outside the approved scope. No Phase97 policy, authority issuer, or live acquisition is included.

Current next action: `CHATGPT_REVIEW_PHASE97_IMPLEMENTATION`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_95

Title: Prospective NAR Entry-Status Authority Capture Contract

Formal Status: DRAFT_FOR_REVIEW

State: DRAFT_FOR_REVIEW

Outcome: READY_FOR_ARCHITECTURAL_REVIEW

Audit: PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_AUDIT_COMPLETE

Authorization: NONE_REQUIRED_AUDIT_ONLY

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `3a8bb363838110d5b918829e19e97fef1718fdaf` / `19986e75e450150032e631fe4dac111d3e59e581`

### Phase94 reconciliation

`PHASE94_AUTHORITY_ISSUANCE_REVIEW_PASS` and `HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS` are frozen. No Phase94 production implementation is authorized. The historical target `NAR / 21 / 2025-01-01 / 6` remains `HISTORICAL_REPLAY_BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`; Phase95 does not repair or issue authority for it.

### Separate prospective domains

1. **Entry identity universe** is provider-scoped identity only. Its canonical content is UTF-8 canonical JSON containing `organization`, `source_system`, `external_race_id`, and a `horse_no`-ascending entries tuple. Each entry contains only `external_entry_id`, `external_horse_id`, and `horse_no`. The result is a versioned SHA-256 identity. It contains no name, internal `race_entry_id`, status, odds, or market field.
2. **Observed entry-status universe** is a time-bounded interpretation of one or more immutable captures against that exact identity universe. It must retain explicit observed dispositions and supporting capture identities; it may not infer `ACTIVE` from an empty field.
3. **Market eligibility** is separate and remains unsupported. Neither identity coverage nor observed status coverage can itself authorize a market decision.

Phase88's entry extractor cannot be reused unchanged for prospective races: it intentionally hard-codes the published target and the `1..14` fixture invariant. Its reviewed structural primitives—one canonical `td.horseNum` and one canonical `a.horseName[href]` per entry—can only be reconsidered by a future generic identity-extraction contract. That future contract must derive provider identities without names, status, or odds and must fail closed for missing, duplicate, or ambiguous rows.

### Official-source semantics

| Existing official source | Current repository use | What it can prove | Complete positive status universe? |
| --- | --- | --- | --- |
| DebaTable | Exact entry rows and each five-row target block's current `td.info` field | An explicit recognized marker such as `出走取消`; an empty field is only no-explicit-withdrawal evidence | No. The reviewed parser deliberately never maps an empty field to `ACTIVE`; unknown non-empty values fail closed. |
| RaceList `changeInfo` | Exact changed-race/horse association | Exceptional change rows such as `(race_no, horse_no, 出走取消)` | No. It is a change/exception list, not an explicit status record for every entry; multiple/other changes require separately reviewed semantics. |
| RaceMarkTable | Normal final-result and payout persistence | Post-race result/settlement material | No. It is causally ineligible for pre-race status. |
| HorseMarkInfo | Provider-local horse-detail capture | Individual horse detail only | No reviewed race-scoped complete-status contract exists. |

No existing official source contract proves that an empty DebaTable status or absence from `changeInfo` means normal/active, proves that all cancellation/scratch forms are enumerated, or gives a complete positive disposition for every entry. Whole-race or meeting cancellation is also separate and remains unsupported.

### Prospective capture and timing contract

A future raw capture service must preserve one append-only immutable record for every observation: canonical source/request identity, exact response bytes, SHA-256, target identity, `requested_at`, `observed_at`, `stored_at`, HTTP status, charset/content-encoding, and received HTTP metadata. It must not overwrite an earlier capture. `NAROfficialResponseCapture` already supplies this raw-byte boundary for DebaTable, RaceMarkTable, and HorseMarkInfo, but its closed URL vocabulary does **not** include RaceList; a future reviewed capture design would need either a carefully extended common capture boundary or a separate RaceList/status boundary. HTTP `Date` and `Last-Modified` remain received metadata, not publication-time proof.

Prospective capture timing must use the actual capture `observed_at`, never the page's race date. A future policy must declare an explicit prediction information cutoff `C` with `C <= target.scheduled_start_at`, accept only immutable observations at or before `C`, and retain their exact capture identities. Repeated captures before `C`, including after explicitly detected changes, are operationally useful but never replace a missing source-semantics proof.

A capture at T-5 minutes can establish only the state known at that exact observation/cutoff. A withdrawal published at T-1 does not retrospectively invalidate that narrower claim, but it prevents any assertion that T-5 was the final pre-start state. Final-pre-race status may be claimed only if a reviewed source offers an explicit terminal/complete pre-start publication guarantee; none is known. The scheduler must therefore model the information cutoff explicitly rather than treating scheduled start as an observed-information time.

### Issuance decision

An eventual issuer may emit `COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE` only if it proves exact target identity; the complete canonical provider identity universe; complete explicit status interpretation over that identical universe; mutually consistent source captures; immutable raw capture identity/digest; an actual observation no later than the declared prediction cutoff and scheduled start; deterministic derivation; and absence of post-race evidence. Any missing predicate means **do not issue**.

Primary classification: `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS`.

The raw prospective-capture shape is definable, but no known official source gives the complete positive per-entry status semantics necessary to issue the closed Phase93 authority. Accordingly, no implementation path is proposed in this phase. The minimum next step is a separately reviewed official-source semantics discovery effort that can establish an authoritative per-entry status roster (including the meaning of normal/non-withdrawn) or a provider-defined complete pre-start disposition feed. It must also define any whole-race/meeting cancellation semantics separately.

Phase41 remains unresolved: `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`. Even a future successful status-capture prerequisite would not by itself resolve market eligibility: independent market-eligibility and market-odds authority would still require their own reviewed contracts.

### Allowed Files

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

### Forbidden Files

Every other path, including live acquisition, production code, tests, fixtures, capture archives, databases, replay domains, `database/**`, and `logs/**`.

### Required Checks

Static repository inspection only. Do not run tests, provider requests, Phase44, GET, replay, database writes, staging, commit, or push. Require `git diff --check` and `git status --short` before stopping.

### Stop Condition

Stop without implementing capture or issuing synthetic authority unless a reviewed official source contract proves complete positive pre-start status coverage for the exact provider entry universe. Any live acquisition, new capture boundary, generic identity extractor, status interpreter, or market work requires a separately approved phase.

Next: `CHATGPT_REVIEW_PHASE95_PROSPECTIVE_STATUS_CAPTURE`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_94

Title: NAR Historical Entry-Status Authority Issuance Boundary

Formal Status: DRAFT_FOR_REVIEW

State: DRAFT_FOR_REVIEW

Outcome: READY_FOR_ARCHITECTURAL_REVIEW

Audit: HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUANCE_AUDIT_COMPLETE

Authorization: NONE_REQUIRED_AUDIT_ONLY

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `3a8bb363838110d5b918829e19e97fef1718fdaf` / `19986e75e450150032e631fe4dac111d3e59e581`

### Phase93 reconciliation

`PHASE93_IMPLEMENTATION_REMOTE_VERIFICATION_PASS` is frozen. `POST_V0_8_DAILY_REPLAY_93 = FORMALLY_COMPLETE` and `STRICT_HISTORICAL_REPLAY_ENTRY_STATUS_ELIGIBILITY_GATE = FORMALLY_INTEGRATED`. The verified integration commit is `3a8bb363838110d5b918829e19e97fef1718fdaf`, with tree `19986e75e450150032e631fe4dac111d3e59e581`, parent `01524006b23a0496d084f0d605f31cba8e6b87f9`, and message `feat: gate NAR replay on historical entry status authority`.

### Candidate issuance inputs

| Candidate | Immutable-byte and target authority | Status-universe authority | Time authority | Issuance result |
| --- | --- | --- | --- | --- |
| `NAROfficialResponseCapture` plus its append-only SQLite archive | Exact canonical official URL, strict UTF-8 body, SHA-256, capture ID, and reloadable capture body | The capture domain has no complete entry-status coverage semantic; a captured Deba/RaceList may expose a positive withdrawal only | `requested_at`, `observed_at`, and `stored_at` are retrieval/archive times. Optional HTTP headers are unqualified text, not reviewed provider-publication proof | Insufficient |
| `HistoricalInputEvidenceReference` and snapshot provenance | Can retain URL, response digest, optional `available_at`, and `observed_at` | `HistoricalInputSourceRecord` has no entry-status record kind or complete-status-universe contract | Values are supplied metadata; this domain is not an issuer and does not independently authenticate availability | Insufficient |
| Phase85 V3 bundle, Phase88 binding, and Phase90 interpretation | Exact frozen Deba/RaceList/manifest bytes and a complete 14-entry provider identity set | Horse 14 has current explicit withdrawal evidence; horses 1–13 have only no-explicit-withdrawal evidence, never `ACTIVE` | Manifest observations/captures are in 2026 and explicitly `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET` | Categorically ineligible for issuance |
| Daily target evidence archive | Can identify the target day/race denominator and freeze response bytes | Does not prove complete exact-race entry-status coverage | Target fixture retrieval is in 2026 and `provider_available_at` is absent | Insufficient |
| Result, payout, settlement, and replay-result evidence | May identify the completed race and immutable outcome records | Post-race outcome, not prediction-time entry status | Finalization/observation is after the prediction boundary | Categorically prohibited by the causal firewall |
| Independently timestamped historical archive or provider version | No qualifying repository-held candidate exists | Would be eligible only if it explicitly covers every canonical entry's status | Must bind immutable content and trusted capture/publication time at or before the scheduled start | Required new source, not presently issuable |

### Issuance boundary

`NARHistoricalEntryStatusAuthority` remains a policy input, not self-authenticating evidence. A future reviewed issuer may construct it only from a source package that proves all of the following together: exact `NAR` / `nar_official` target identity; immutable canonical source bytes or an immutable archival reference; a lowercase SHA-256 digest of that exact content; an independently verified availability proof; availability at or before `target.scheduled_start_at`; the complete target entry universe; complete status coverage for that same universe; and deterministic source-to-authority derivation. Name matching, results, payouts, settlement, odds, current pages, or a caller-supplied timestamp may not repair a missing predicate. Failure of any predicate means no authority is issued.

The canonical future `entry_universe_identity` must not be free text. It should be a versioned SHA-256 identity over canonical UTF-8 JSON containing `(organization, source_system, external_race_id)` and the horse-number-ascending tuple of exact provider entry identities `(external_entry_id, external_horse_id, horse_no)`. Phase88 supplies the only currently reviewed canonical target universe: fourteen `nar:20250101:21:6:entry:<horse_no>` identities for horse numbers 1 through 14. It is identity-only evidence. A future historical-status source must independently bind its complete status coverage to the same canonical universe; Phase88 cannot promote current status into historical status.

Two timestamp provenance forms are potentially acceptable, but neither exists for this target: (1) `PROVIDER_PUBLICATION_AVAILABILITY`, requiring reviewed provider-controlled version/publication metadata that binds the exact content/digest to its publication time; or (2) `INDEPENDENT_ARCHIVE_OBSERVATION`, requiring an immutable archive capture identity, canonical original-source identity, exact captured content/digest, and independently verifiable archive time. Each time must be no later than the exact target scheduled start. A filename date, race date, a later retrieval's HTTP `Date`, current historical-page availability, or an arbitrary caller datetime is not a causal availability proof.

### Classification and current target

Primary classification: `HISTORICAL_ENTRY_STATUS_AUTHORITY_ISSUER_BLOCKED_SOURCE_SEMANTICS`.

The known NAR documents support a positive current withdrawal marker, but do not support a positive non-withdrawn/active disposition for every other entry. Consequently they cannot establish `COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE`, even apart from their post-cutoff timestamps. Phase92 also found no qualifying pre-cutoff archive. For `NAR / 21 / 2025-01-01 / 6`, no authority is issued and the Phase93 outcome remains `HISTORICAL_REPLAY_BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`.

The smallest next step is a separately reviewed source-contract/discovery phase for an official versioned status publication or independently timestamped archive whose exact document both predates the target scheduled start and explicitly provides complete status coverage for the canonical entry universe. It must determine source semantics before any issuer implementation is proposed; this phase authorizes no network research or authority publication.

Phase41 remains unresolved: `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`. `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, `market_eligibility = UNSUPPORTED`, `positive_market_eligibility = UNSUPPORTED`, and `WHOLE_MEETING_CANCELLATION = UNSUPPORTED` remain unchanged.

### Allowed Files

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

### Forbidden Files

Every other path, including production code, tests, fixtures, databases, archives, replay domains, `database/**`, and `logs/**`.

### Required Checks

Static repository inspection only. Do not run tests, provider requests, Phase44, GET, replay, database writes, staging, commit, or push. Require `git diff --check` and `git status --short` before stopping.

### Stop Condition

Stop without issuing synthetic authority or proposing an issuer implementation if complete pre-cutoff status coverage cannot be proven from an existing reviewed source contract. Any needed source acquisition, archive research, implementation, test, or schema work belongs to a separately reviewed phase.

Next: `CHATGPT_REVIEW_PHASE94_AUTHORITY_ISSUANCE`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_93

Title: Strict Historical Replay Eligibility Policy for Missing Entry-Status Authority

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Implementation: STRICT_HISTORICAL_REPLAY_ENTRY_STATUS_ELIGIBILITY_GATE_IMPLEMENTED

Audit: STRICT_HISTORICAL_REPLAY_ELIGIBILITY_POLICY_DESIGN_COMPLETE

Design Review: PHASE93_REPLAY_ELIGIBILITY_POLICY_DESIGN_REVIEW_PASS

Authorization: NONE_REQUIRED_NO_NETWORK_READ_ONLY_POLICY

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `01524006b23a0496d084f0d605f31cba8e6b87f9` / `149cc925cc296726c1d8e92e5d3faa207b9ad9eb`

### Frozen findings

`PHASE91_HISTORICAL_STATUS_AUTHORITY_REVIEW_PASS` and `PHASE92_ARCHIVE_DISCOVERY_REVIEW_PASS` are frozen. Phase92's fail-closed result is `HISTORICAL_ENTRY_STATUS_ARCHIVE_NOT_FOUND`: no independently timestamped entry-status record for `NAR / 21 / 2025-01-01 / 6` was found at or before the 2025-01-01 13:50 JST prediction cutoff.

Phase90 proves only a current 2026 observation: horse 14 is `EXPLICIT_WITHDRAWAL_PRESENT`, while horses 1–13 are `NO_EXPLICIT_WITHDRAWAL_EVIDENCE`. Phase85 and Phase88 prove local source and identity authority only. None of those facts proves historical prediction-time status.

### Correct integration boundary

The narrowest safe boundary is an explicit NAR target-level replay-readiness gate in the NAR daily replay orchestration path, after audited target-set validation and before SQLite connection binding or `resolve_sqlite_nar_daily_evidence`. A blocked decision must prevent evidence resolution, snapshot selection, manifest projection, and replay execution.

`DailyHistoricalReplayEvidenceDisposition.UNSUPPORTED` can carry a final non-executable outcome with stable reason codes without changing the execution-state, audit, or persistence contracts. `historical_input_snapshot_builder` is intentionally provider-neutral and must not encode current-only NAR status; the SQLite resolver selects existing prediction/settlement evidence and is not the owner of a new source-evidence policy; manifest projection is downstream and too late.

### Proposed immutable policy decision

The future dedicated immutable input is `NARHistoricalEntryStatusAuthoritySet`, containing the exact canonical `DailyHistoricalReplayTargetSet` plus a tuple of explicit `NARHistoricalEntryStatusAuthority` values. Each authority is target-bound and carries an authority identity, canonical source identity, response SHA-256, availability-proof identity/kind, causally authoritative `available_at`, and immutable observation identity. It must prove availability at or before that target's prediction cutoff. The set rejects duplicate or out-of-denominator authority; an omitted target has no authority and is a blocking decision, not an implicit exemption.

An authority is eligible only when its closed semantics prove `COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE` for the exact target's full entry universe. A single withdrawal fact, one `changeInfo` row, a lack of later withdrawal markers, or odds presence/absence is insufficient. Arbitrary free-text semantics cannot grant eligibility. If `target.scheduled_start_at` is unavailable, or if authoritative availability/observation is later than that timestamp, the target is blocked. Equality at the cutoff is causally eligible under the approved `<=` rule.

The corresponding immutable output is `NARHistoricalReplayEligibilityResolution`, containing the exact target set and a canonical target-order tuple of `NARHistoricalReplayEligibilityDecision`. Each decision contains only `target`, `eligibility`, `blocker_classification`, `missing_authority`, and `causal_reason`. Its closed policy states are exactly:

- `ELIGIBLE_WITH_PRE_CUTOFF_ENTRY_STATUS_AUTHORITY`: exact reviewed entry-status authority is independently verified as available at or before the prediction cutoff.
- `BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`: no such authority is supplied or it is causally ineligible.

The gate consumes only the exact target set and explicit, separately reviewed historical entry-status authority input. It does not consume Phase90 current-observation output, horse 14, any current page, later historical page, result, payout, settlement, odds, or database query. No supplied authority means `BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`; only a separately reviewed, cutoff-qualified authority can produce `ELIGIBLE_WITH_PRE_CUTOFF_ENTRY_STATUS_AUTHORITY`.

For the frozen target, the decision is `BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`, with exact blocker classification `HISTORICAL_REPLAY_BLOCKED_ENTRY_STATUS_AUTHORITY_UNAVAILABLE`. The missing authority is provider-scoped, immutable exact-race/entry status evidence with raw bytes, stable identity, and independently verifiable provider publication or availability time no later than the prediction cutoff. Horse 14 is neither removed nor treated active; horses 1–13 are not promoted to market eligible. Those Phase90 observations are audit facts only and never selection inputs.

### Whole-day diagnostic resolution and public API

`run_nar_daily_replay` already runs replay only for `ALL_TARGETS_RESOLVED`; its `PARTIALLY_RESOLVED` branch deliberately returns without a manifest or replay. The new gate must be stricter still: if any exact daily target lacks qualifying historical entry-status authority, it returns a complete target-denominator decision set and the orchestration stops for the entire day. It must not remove the blocked race and replay the remainder.

The public keyword-only API gains one required argument: `historical_entry_status_authorities: NARHistoricalEntryStatusAuthoritySet`. It has no default and no hidden registry, page, or database fallback. After acquisition target-set validation and eligibility validation, but before `_resolve_evidence()`, the orchestrator evaluates this input.

If any decision is blocked, the orchestrator must not call `_resolve_evidence()`. It instead constructs one complete, deterministic `DailyHistoricalReplayEvidenceResolution` for the original target set, using `UNSUPPORTED` for every target. A target lacking authority receives exactly `ENTRY_STATUS_AUTHORITY_UNAVAILABLE`; a target otherwise authorized but blocked by another target receives exactly `WHOLE_DAY_BLOCKED_BY_ENTRY_STATUS_AUTHORITY`. The resolution has no executable outcomes, so `day_state` is `NO_EXECUTABLE_TARGETS` and the existing execution state remains `NARDailyReplayExecutionState.NOT_RUN_NO_EXECUTABLE_TARGETS`. There is no manifest, replay, or summary.

This preserves the existing immutable orchestration result, audit identity, and execution-state/resolution-state mapping. The current result-persistence implementation already serializes and validates every outcome's sorted `reason_codes` in `resolution_outcomes_json`; therefore no production persistence schema or module change is required. Future tests must prove a persisted diagnostic round trip preserves these reason codes unchanged.

### Minimum future scope

The exhaustive direct-call audit found only `tests/test_nar_daily_replay_orchestrator.py` and `tests/test_nar_daily_replay_result_persistence.py`; both invoke `run_nar_daily_replay()` and must supply the new required authority input. The final future scope is exactly seven paths: create `scripts/simulation/nar_historical_replay_eligibility.py` and `tests/test_nar_historical_replay_eligibility.py`; modify `scripts/simulation/nar_daily_replay_orchestrator.py`, `tests/test_nar_daily_replay_orchestrator.py`, `tests/test_nar_daily_replay_result_persistence.py`, and these two phase-control documents. It is pure, no-network, no-DB, and no-replay. It must not modify generic snapshot, generic evidence-resolution, or production persistence semantics.

### Allowed Files

- `scripts/simulation/nar_historical_replay_eligibility.py` (create)
- `tests/test_nar_historical_replay_eligibility.py` (create)
- `scripts/simulation/nar_daily_replay_orchestrator.py`
- `tests/test_nar_daily_replay_orchestrator.py`
- `tests/test_nar_daily_replay_result_persistence.py`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

### Forbidden Files

Every other path, including production replay-result persistence, repositories, migrations, generic historical evidence/snapshot domains, Phase90 interpretation, fixtures, `database/**`, and `logs/**`.

### Required Tests

In order, run `python -m pytest -q` on the focused eligibility, daily orchestrator, daily persistence, SQLite daily evidence resolver, Phase90 interpretation, and daily aggregation test files, then run the established full repository pytest suite. Require every result to pass; also run `git diff --check` and `git status --short`.

### Stop Condition

Stop without broadening scope if any eighth path is required (`PHASE93_APPROVED_SCOPE_INSUFFICIENT`), a required test fails, a contract contradicts the approved design, or the remote branch advances (`PHASE93_REMOTE_ADVANCED`). Preserve any local commit if push fails; do not retry automatically.

Future tests must prove: complete valid authority takes the normal `_resolve_evidence()` path; one or many missing authorities prevent that call; the original denominator is preserved; missing targets receive `ENTRY_STATUS_AUTHORITY_UNAVAILABLE`; otherwise-authorized targets receive `WHOLE_DAY_BLOCKED_BY_ENTRY_STATUS_AUTHORITY`; the resulting state is `NO_EXECUTABLE_TARGETS` / `NOT_RUN_NO_EXECUTABLE_TARGETS` with no manifest, replay, or summary; after-cutoff, target-mismatched, duplicated, or malformed authority fails closed; audit identity is deterministic; and persisted diagnostic reason codes round-trip unchanged.

Phase41 remains unresolved: `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`. `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, `market_eligibility = UNSUPPORTED`, `positive_market_eligibility = UNSUPPORTED`, and `WHOLE_MEETING_CANCELLATION = UNSUPPORTED` remain unchanged.

### Phase93 implementation verification

The new pure module implements exact frozen/slotted `NARHistoricalEntryStatusAuthority`, `NARHistoricalEntryStatusAuthoritySet`, `NARHistoricalReplayEligibilityDecision`, and `NARHistoricalReplayEligibilityResolution`. Its closed coverage semantic is `COMPLETE_PRE_CUTOFF_ENTRY_STATUS_UNIVERSE`; closed timestamp provenance accepts only provider-publication availability or independent archive observation. For every target, both availability and observation must be no later than `target.scheduled_start_at`. Missing authority, incomplete coverage, or a later timestamp blocks the target.

The orchestrator now requires the explicit keyword-only `historical_entry_status_authorities` input. When any target blocks, it creates the complete unchanged-denominator diagnostic resolution with `UNSUPPORTED`, exact per-target reason codes, `NO_EXECUTABLE_TARGETS`, and the existing `NOT_RUN_NO_EXECUTABLE_TARGETS` execution state. `_resolve_evidence`, manifest generation, and replay are bypassed. The existing production persistence module and schema are unchanged; the new persistence test verifies the diagnostic reason survives an exact SQLite round trip.

Required tests passed in order: focused eligibility `7 passed, 5 subtests passed`; orchestrator `23 passed, 11 subtests passed`; persistence `11 passed, 12 subtests passed`; SQLite NAR evidence resolver `26 passed, 38 subtests passed`; Phase90 interpretation `27 passed`; daily aggregation `20 passed`; full repository suite `4515 passed, 2 skipped, 2846 subtests passed`.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`. New policy DB writes: `0`. No market-eligibility, snapshot, or replay domain was changed. The seven approved paths are the only changed paths; final Git integration facts belong to the execution handoff.

Next: `CHATGPT_REVIEW_PHASE93_IMPLEMENTATION`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_91

Title: Historical NAR Entry-Status Authority Discovery

Formal Status: DRAFT_FOR_REVIEW

State: DRAFT_FOR_REVIEW

Outcome: READY_FOR_ARCHITECTURAL_REVIEW

Audit: HISTORICAL_NAR_ENTRY_STATUS_AUTHORITY_DISCOVERY_COMPLETE

Authorization: NONE_REQUIRED_AUDIT_ONLY

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `01524006b23a0496d084f0d605f31cba8e6b87f9` / `149cc925cc296726c1d8e92e5d3faa207b9ad9eb`

### Phase90 reconciliation

`PHASE90_IMPLEMENTATION_REMOTE_VERIFICATION_PASS` is recorded. `POST_V0_8_DAILY_REPLAY_90 = FORMALLY_COMPLETE` and `NAR_CURRENT_ENTRY_STATUS_INTERPRETATION = FORMALLY_INTEGRATED`. The integrated Phase90 commit is `01524006b23a0496d084f0d605f31cba8e6b87f9`, with tree `149cc925cc296726c1d8e92e5d3faa207b9ad9eb`, parent `115cd9489d1a13a6cffc99e85d1c79b8cca72194`, and message `feat: add NAR current entry status interpretation`.

### Candidate-authority audit

| Candidate | What it proves | Timestamp semantics | Historical-cutoff eligibility |
| --- | --- | --- | --- |
| Phase83 V3 DebaTable/RaceList manifest and Phase90 interpreter | Exact target and horse-14 current withdrawal observation; Phase88 supplies identity only | Deba observed/captured `2026-09-21T23:27:42.678776Z` / `2026-09-21T23:27:42.678947Z`; RaceList `2026-09-21T23:27:43.165338Z` / `2026-09-21T23:27:43.165400Z` | Ineligible: explicitly `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, not a 2025 availability proof |
| `tests/fixtures/nar_daily_targets/race_list_2025_01_01_kawasaki_baba21.utf8.html` and `provenance.json` | Exact date/venue RaceList and a visible withdrawal label | The fixture was requested/observed on `2026-09-03`; `provider_available_at` is `null` | Ineligible: filename target date is not provider-publication time; the page may not be backdated |
| `HistoricalInputEvidenceReference` and snapshot provenance schema | A contract can carry `available_at`, `observed_at`, URL, and response hash | `available_at` is optional; only a value at/before the cutoff is causal | No target status record exists; `SourceRecordKind` has no entry-status member |
| NAR official/daily capture archives and persisted DB | Capture domains and append-only archive contracts exist | They retain request/observation/storage times, not an inferred publication time | No target historical status capture is present. The read-only local DB contains only `races` and `horses`; no NAR capture, target-capture, snapshot, or provenance-evidence tables are present |
| NAR result, payout, settlement, and replay-result domains | Post-race result/settlement semantics | Finalization and observation are post-race | Categorically ineligible: outcome/settlement data cannot repair prediction-time withdrawal evidence |

`historical_input_snapshot_builder.py::build_historical_input_snapshot` independently enforces the firewall: source `observed_at` and, when present, `available_at` must not be later than the information cutoff. The current captures cannot enter that boundary for the 2025 target.

### Decision

Primary classification: `HISTORICAL_ENTRY_STATUS_AUTHORITY_REQUIRES_NEW_CAPTURE_SOURCE`.

The missing authority is an immutable, provider-scoped pre-cutoff status document or archived provider version for exact target `NAR / 21 / 2025-01-01 / 6`, linked to each affected entry by stable race/horse or provider-entry identity, with exact raw bytes, canonical request identity, response hash, and a verifiable provider-publication/availability timestamp at or before the historical prediction cutoff. It must represent entry-status information rather than result, payout, odds absence, or settlement outcome.

Phase41 remains unresolved: `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE`. `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`; this audit establishes neither historical availability nor snapshot inclusion.

### Smallest next step

Perform a separately reviewed, no-inference research phase to determine whether an official NAR historical archive/version exposes the target's pre-cutoff `changeInfo` or equivalent status publication together with verifiable publication time. A current-only page is insufficient. A third-party archive would require an explicit provenance and timestamp contract before it could be considered; if no such official or independently timestamped archive exists for the period, the historical-status dependency remains unsupported. This phase authorizes no network action.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`.

DB activity: read-only schema/archive inspection only; writes `0`.

Modified paths: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md` only. Staged and untracked sets remain empty.

Next: `CHATGPT_REVIEW_PHASE91_HISTORICAL_STATUS_AUTHORITY`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_90

Title: NAR Entry Status Interpretation Authority

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Implementation: NAR_CURRENT_ENTRY_STATUS_INTERPRETATION_IMPLEMENTED

Audit: NAR_ENTRY_STATUS_INTERPRETATION_AUTHORITY_AUDIT_COMPLETE

Design Review: PHASE90_ENTRY_STATUS_DESIGN_REVIEW_PASS

Authorization: NONE_REQUIRED_NO_NETWORK_NO_DB

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `115cd9489d1a13a6cffc99e85d1c79b8cca72194` / `6044d07ceb3e843fa43e7370a637dd1bc1040b14`

### Phase88/89 reconciliation

Phase89 was integrated as commit `115cd9489d1a13a6cffc99e85d1c79b8cca72194`, tree `6044d07ceb3e843fa43e7370a637dd1bc1040b14`, parent `2e420a911e2cdeeb81f32214e5ba4d01fb4b0a7d`, with exact message `test: complete Phase88 bundle authenticity coverage`. Its committed paths were exactly `tests/test_nar_race_entry_status_replay_identity_binding.py`, `docs/CURRENT_PHASE.md`, and `docs/LATEST_CODEX_REPORT.md`; normal push succeeded and local/remote-tracking HEAD both reached that commit. This post-integration fact supersedes the former current/final Phase89 statement that staging, commit, and push were `NONE`; the historical PREPARE/APPROVE chronology remains unchanged.

Independent verdicts are now frozen as `PHASE88_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`, `POST_V0_8_DAILY_REPLAY_88 = FORMALLY_COMPLETE`, `STRICT_READ_ONLY_NAR_REPLAY_IDENTITY_BINDING = FORMALLY_INTEGRATED`, `PHASE89_TEST_HARDENING_REMOTE_VERIFICATION_PASS`, and `POST_V0_8_DAILY_REPLAY_89 = FORMALLY_COMPLETE`.

### Exact source-status evidence map

- Frozen DebaTable bytes contain exactly one explicit `出走取消` marker in the target entry's reviewed current change/status area, structurally associated with horse 14's entry block. The future interpreter must not search arbitrary/global `取消` or `出走取消` text: the same document contains historical past-race cancellation text that is not target-entry status evidence. The horse-14 identity comes from the validated horse-number row and canonical provider horse link, never from name, odds, display order, result, or settlement data. `nar_race_entry_status_source_profile_profile_a.py::diagnose_nar_race_entry_status_profile_a_v3` proves one entry table, fourteen ordinary horse rows, and `ENTRY_LISTING_PRESENT`; Profile-A does **not** prove that unmarked entries are active and is not itself a status interpreter.
- Frozen RaceList bytes contain exactly one target `table.changeInfo` row with race `6R`, horse number `14`, change category `出走取消`, and reason `疾病`. `nar_race_entry_status_source_profile_diagnostics.py::diagnose_nar_race_entry_status_profile_b_v2` formally proves `EXPLICIT_WITHDRAWAL_PRESENT`, one target schedule row, one shaped change row, and one horse-14 withdrawal association. Association authority is race number plus horse number; horse name is not used.
- `nar_race_entry_status_source_profile_structural_recovery_diagnostics.py::diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery` distinguishes the two target candidates as one direct schedule row and one nested `changeInfo` row. This prevents topology confusion but does not independently create a status semantic.
- The V3 manifest freezes Profile-A/Profile-B results and the acquisition boundary. Deba was requested/observed/captured at `2026-09-21T23:27:42.093809Z` / `2026-09-21T23:27:42.678776Z` / `2026-09-21T23:27:42.678947Z`; RaceList at `2026-09-21T23:27:42.679272Z` / `2026-09-21T23:27:43.165338Z` / `2026-09-21T23:27:43.165400Z`. It explicitly states `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET` and `market_eligibility = UNSUPPORTED`.
- `nar_race_entry_status_source_profile_fixture_consumer.py::NARRaceEntryStatusSourceProfileFixtureBundleV3` preserves exact raw bytes, manifest, Phase66 ancestry, and publication-plan authority. It adds no historical timestamp or status inference.
- `nar_race_entry_status_replay_identity_binding.py::NARRaceEntryStatusReplayIdentityBinding` maps all fourteen source identities, including horse 14, to internal race-entry IDs. It has no status field and neither filters nor reinterprets an entry.

### Four separate semantic decisions

1. `CURRENT_OBSERVED_ENTRY_STATUS`: **supported only as bounded evidence.** At the 2026 capture boundary, horse 14 has corroborating explicit withdrawal evidence in DebaTable and RaceList. For horses 1–13 the only safe conclusion is `NO_EXPLICIT_WITHDRAWAL_EVIDENCE`; absence of the marker does not prove `ACTIVE`.
2. `HISTORICAL_ENTRY_STATUS`: **unsupported / blocked.** The documents were captured more than a year after the 2025-01-01 target. They contain no provider publication time or other authority proving that the status was available at the historical prediction cutoff. Current observation must not be backdated. Exact blocker: `HISTORICAL_ENTRY_STATUS_AUTHORITY_BLOCKED`.
3. `MARKET_ELIGIBILITY`: **unsupported.** Neither explicit current withdrawal nor absence of a marker proves market or positive-market eligibility. Phase41 dependency `NAR_MARKET_ELIGIBILITY_REQUIRES_INDEPENDENT_ENTRY_STATUS_CAPTURE` remains unresolved; `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`.
4. `SNAPSHOT_ENTRY_INCLUSION`: **unsupported.** Current post-target status evidence cannot justify including or excluding any entry from a historical snapshot. Horse 14 remains in the identity universe. No other entry becomes snapshot-eligible merely because it lacks an explicit withdrawal marker.

### Existing-domain audit and temporal firewall

`historical_input_source_records.py::SourceRecordKind` is closed to `track`, `entry`, `jockey`, `odds_win`, `past_race`, and `past_race_absence`; its entry payload carries identity only. `historical_input_snapshots.py::HistoricalRaceEntrySnapshot` has identity, horse number, jockey, positive win odds, and order, but no status field. `historical_input_snapshot_builder.py::build_historical_input_snapshot` requires every source observation to be causally eligible at `information_cutoff`; the 2026 observations cannot satisfy a 2025 historical cutoff. Result/settlement enums such as `RaceResultEntryStatus`, `SettlementStatus`, and payout status describe post-race outcome or settlement domains and are not reusable as prediction-time entry-status evidence.

Accordingly, Phase90 must not add a status record to `HistoricalInputSourceRecord` or alter snapshot models. A separate immutable evidence domain is the smallest safe boundary. The closed current-observation vocabulary is `EXPLICIT_WITHDRAWAL_OBSERVED` and `NO_EXPLICIT_WITHDRAWAL_EVIDENCE`; it deliberately contains no `ACTIVE`, market, or replay-ready value. A race-level temporal scope is fixed to `CURRENT_OBSERVATION_ONLY`.

### Proposed next no-network authority

The primary classification is `ENTRY_STATUS_INTERPRETATION_IMPLEMENTABLE`, limited strictly to current-observed evidence. Historical status remains independently `HISTORICAL_ENTRY_STATUS_AUTHORITY_BLOCKED`.

The future keyword-only interpreter should accept the exact trusted `NARRaceEntryStatusSourceProfileFixtureBundleV3` and exact `NARRaceEntryStatusReplayIdentityBinding`, verify identical target and complete fourteen-entry sets, and return a frozen/slotted `NARRaceEntryStatusInterpretation`. It should contain the exact target, acquisition semantic, `CURRENT_OBSERVATION_ONLY`, an explicit historical-status-authority state, and a horse-number-ordered tuple of frozen entry evidence. Each entry evidence carries source/internal entry identity, horse number, one of the two closed classifications, and immutable supporting document evidence (role, capture identity, observed/captured timestamp, and exact supported label where present). It retains horse 14 and performs no database lookup because Phase88 has already supplied identity binding.

The interpreter must parse only the reviewed target Deba current change/status area and target RaceList `changeInfo` table; it must require RaceList association by exact `race_no = 6`, `horse_no = 14`, and withdrawal label `出走取消`, never by horse name. It must require Deba, RaceList, and frozen Profile-B authority to agree on the explicit horse-14 withdrawal set; Profile-B must retain terminal semantic `EXPLICIT_WITHDRAWAL_PRESENT`, a passing `HORSE_14_WITHDRAWAL_ASSOCIATION`, withdrawn provider horse number `14`, and `withdrawal_label_match = true`. The set must be a subset of the complete Phase88 identity set. Missing, ambiguous, unsupported, or contradictory evidence fails the whole race; no partial result or silent skip is allowed. Stable failures must distinguish `UNSUPPORTED_BUNDLE_OR_BINDING`, `TARGET_CONTRADICTION`, `ENTRY_SET_CONTRADICTION`, `STATUS_EVIDENCE_MISSING`, `STATUS_EVIDENCE_AMBIGUOUS`, `DEBA_RACELIST_CONTRADICTION`, `PROFILE_B_CONTRADICTION`, `HORSE_ASSOCIATION_CONTRADICTION`, `TEMPORAL_AUTHORITY_UNAVAILABLE`, and `UNSUPPORTED_STATUS_REPRESENTATION`. `TEMPORAL_AUTHORITY_UNAVAILABLE` applies whenever a caller attempts to consume this current-observation result as historical-cutoff authority; the basic current-observation interpretation remains valid.

Minimum future implementation scope is exactly four paths:

- create `scripts/simulation/nar_race_entry_status_interpretation.py`
- create `tests/test_nar_race_entry_status_interpretation.py`
- modify `docs/CURRENT_PHASE.md`
- modify `docs/LATEST_CODEX_REPORT.md`

That future phase is pure and no-network. It may parse only the already validated frozen bundle and join by horse number/external entry identity already fixed by Phase88. It must not rediscover DB mapping, use names, construct snapshots, apply market rules, persist anything, invoke replay, or consume results/settlement/payout/odds as status authority.

### Approved Phase90 execution contract

Base Commit and Branch: `115cd9489d1a13a6cffc99e85d1c79b8cca72194` / `feature/post-v0.8-daily-replay`.

Allowed Files: create `scripts/simulation/nar_race_entry_status_interpretation.py` and `tests/test_nar_race_entry_status_interpretation.py`; modify `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. No fifth path is permitted.

Forbidden Files: published fixtures, Phase85 consumer, Phase88 binder, `.gitattributes`, database, logs, historical normalizer, snapshot, replay, market, provider, and every path outside Allowed Files.

Required Tests, in order: Phase90 focused interpretation; Phase88 identity binding; Phase85 fixture consumer; dedicated V3 fixture; historical snapshot builder; full repository suite. Every required run must pass. Also require branch/HEAD/tree/remote identity before integration, exact four-path scope, empty unexpected staged/untracked sets, and `git diff --check` return code zero.

Stop Condition: fail closed with `PHASE90_IMPLEMENTATION_CONTRACT_BLOCKED` if approved semantics cannot be implemented safely; stop for any scope or test failure. On success, record `IMPLEMENTED_FOR_REVIEW` and `READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW`, integrate only the four approved paths with the user-approved exact commit and normal push, then stop for `CHATGPT_REVIEW_PHASE90_IMPLEMENTATION`.

### Phase90 implementation result

The approved keyword-only `interpret_nar_race_entry_status_v3(*, bundle, binding)` now returns frozen/slotted `NARRaceEntryStatusInterpretation`, `NARRaceEntryCurrentStatusEvidence`, and `NARRaceEntryStatusEvidenceTimestamp` values. It independently validates the frozen Phase85 bundle and the complete exact Phase88 binding without accessing SQLite. It reads only the fifth direct row's `td.info` in each validated Deba entry block and the exact target RaceList `changeInfo` row. It requires frozen Profile-B agreement and the exact 2026 acquisition timestamps. All fourteen identities are retained in horse-number order.

Horse 14 has `EXPLICIT_WITHDRAWAL_PRESENT`; horses 1–13 have `NO_EXPLICIT_WITHDRAWAL_EVIDENCE`. The race result explicitly marks current observation `SUPPORTED` and historical status `HISTORICAL_ENTRY_STATUS_AUTHORITY_BLOCKED`. It contains no market, snapshot-inclusion, odds, prediction, replay, settlement, or persistence field. Phase41's independent entry-status capture dependency remains unresolved.

Required tests passed in order: Phase90 focused `27 passed`; Phase88 binding `51 passed`; Phase85 consumer `40 passed, 2 skipped`; dedicated V3 fixture `4 passed`; historical snapshot builder `14 passed, 15 subtests passed`; full repository suite `4505 passed, 2 skipped, 2841 subtests passed`. The published Deba/RaceList/manifest remain byte-identical to Phase83: `313317` / `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`, `66307` / `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`, and `4254` / `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d`.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`.

DB access / writes: `0 / 0`.

The exact commit and push result are authoritative in the execution handoff after Git integration; this document records implementation evidence for independent review.

Next: `CHATGPT_REVIEW_PHASE90_IMPLEMENTATION`

---

## POST_V0_8_DAILY_REPLAY_89

Title: Phase88 Bundle-Authenticity Negative-Test Completion

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_TEST_HARDENING_REVIEW

Implementation: PHASE88_BUNDLE_AUTHENTICITY_NEGATIVE_TEST_COMPLETION_IMPLEMENTED

Design Review: PHASE89_TEST_HARDENING_DESIGN_REVIEW_PASS

Authorization: NONE_REQUIRED_TEST_ONLY

Design Contract: PHASE88_BUNDLE_AUTHENTICITY_NEGATIVE_TEST_COMPLETION_CONTRACT_COMPLETE

Prior Review: PHASE88_IMPLEMENTATION_REMOTE_VERIFICATION_PASS_WITH_BUNDLE_AUTHENTICITY_TEST_GAP

Primary Blocker: PHASE88_BUNDLE_AUTHENTICITY_NEGATIVE_TEST_COVERAGE_INCOMPLETE

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `2e420a911e2cdeeb81f32214e5ba4d01fb4b0a7d` / `399e45fb6bcfab31ef703d2a827fa3bdee6a597f`

### Frozen Phase88 implementation verdict

Phase88 production is frozen as passing remote verification. Its binder remains byte-identical at SHA-256 `6e98bc204141ed9e64d6e100d7a42e5ee78e5cd5c5bba7dffa26e01afba19904`; Phase89 must not modify it. The only verified deficiency is focused negative-test coverage for the existing bundle manifest-object, FixtureSetV3 identity, and QualificationV3 identity gates. This is not a production defect finding.

### Allowed and forbidden scope

Phase89 may modify exactly:

- `tests/test_nar_race_entry_status_replay_identity_binding.py`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

No fourth path is permitted. The production binder, all fixtures, schema/migrations, consumer, database, snapshot, status, market, replay, provider, and Git integration are forbidden. The execution performs no provider HTTP, Phase44, GET, database write, staging, commit, or push.

### Required negative-test completion

The focused test file added these independently isolated rejection checks:

1. A bundle constructed only in test code with `object.__new__` / `object.__setattr__`, retaining the exact bundle type and authentic raw bytes but replacing `manifest` with a wrong exact type. It failed `UNSUPPORTED_BUNDLE` with a deliberately non-SQLite connection.
2. A bundle retaining all authentic raw bytes and the authentic manifest object, while test-only monkeypatching the binder's exact expected FixtureSetV3 identity to a different value. It failed `UNSUPPORTED_BUNDLE` with a deliberately unusable connection.
3. The equivalent isolated QualificationV3 expected-identity mismatch. It failed `UNSUPPORTED_BUNDLE` before the deliberately unusable connection could be inspected.

The expected-identity monkeypatches are narrowly limited to the focused tests. They isolate the existing production gates after canonical manifest-byte equality has passed, without modifying production contract objects or frozen raw bytes. All three assertions returned `UNSUPPORTED_BUNDLE`, not `SQLITE_CONNECTION_INVALID`, proving bundle authenticity precedes SQLite validation.

Before and after Phase89 tests, recompute the production binder SHA-256 and require the frozen value above. Recompute and require the published fixture identities unchanged: Deba `313317` / `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`; RaceList `66307` / `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`; manifest `4254` / `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d`.

Required execution test order passed: focused binder `51 passed`; Phase85 fixture consumer `40 passed, 2 skipped`; V3 fixture `4 passed`; historical migration `11 passed`; SQLite snapshot repository `25 passed, 30 subtests passed`; snapshot builder `14 passed, 15 subtests passed`; full repository suite `4478 passed, 2 skipped, 2841 subtests passed`. A failure that proves a production defect is `PHASE89_TEST_REVEALS_PHASE88_PRODUCTION_DEFECT`; no such failure occurred and the binder was not patched.

Phase88 may be declared formally complete only after a successful Phase89 implementation and independent remote review. Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; market eligibility, positive market eligibility, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`. Identity binding stays identity-only.

### Readiness matrix

| Item | Ready |
| --- | --- |
| A. Phase88 production frozen as passing review | YES |
| B. Exact three missing negative cases identified | YES |
| C. Forged manifest test defined | YES |
| D. FixtureSet identity test defined | YES |
| E. Qualification identity test defined | YES |
| F. Bundle-before-database ordering test defined | YES |
| G. Production binder byte-freeze defined | YES |
| H. Fixture byte-freeze defined | YES |
| I. Exact three-path scope defined | YES |
| J. Required test order defined | YES |
| K. Phase88 final verdict gated on Phase89 | YES |
| L. Semantic firewall preserved | YES |
| M. No production implementation during PREPARE | YES |
| N. No network/DB writes/stage/commit/push | YES |

Provider HTTP / Phase44 / GET: `0 / 0 / 0`

DB writes: `0`

Tests: `PASS` as recorded above

Staging / commit / push: `NONE / NONE / NONE`

Future Scope: test file + two docs only

Next: `CHATGPT_REVIEW_PHASE89_TEST_HARDENING`

---

## Historical Record — POST_V0_8_DAILY_REPLAY_88

Title: Strict Read-Only NAR Replay Identity Binding Contract

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Implementation: STRICT_READ_ONLY_NAR_REPLAY_IDENTITY_BINDING_IMPLEMENTED

Review Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Outcome: APPROVED_STRICT_READ_ONLY_NAR_REPLAY_IDENTITY_BINDING

Design Contract: STRICT_READ_ONLY_NAR_REPLAY_IDENTITY_BINDING_CONTRACT_COMPLETE

Design Review: PHASE88_IDENTITY_BINDING_DESIGN_REVIEW_PASS

Authorization: NONE_REQUIRED_NO_NETWORK_READ_ONLY_SQLITE

Entry Extraction: DEDICATED_ENTRY_IDENTITY_EXTRACTION_REQUIRED

Future Scope: exact four paths

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `33d8c755c862c073f5783c3645ac0958376afa2c` / `70d040a7c90b5029b090d6aabce56974b3366a5a`

Prior review: `PHASE87_IDENTITY_BINDING_AUDIT_REVIEW_PASS`

Primary dependency: `REPLAY_IDENTITY_BINDING_SUPPORT_REQUIRED`

### Phase88 implementation result

The exact four-path implementation is complete for independent review: the new read-only binder, its focused tests, and these two phase-control documents. The binder independently checks frozen Phase83 bundle bytes and manifest authority, extracts all 14 identity-only Deba rows including horse 14, validates V010 tables/keys/foreign keys, and binds the complete source-entry set to existing internal race/entry rows under a caller-owned `query_only` SQLite connection. It does not infer withdrawal status or market eligibility, write mappings, build snapshots, run replay, or access a provider.

Tests passed in required order: focused binder `48 passed`; Phase85 consumer `40 passed, 2 skipped`; dedicated V3 fixture `4 passed`; migration `11 passed`; SQLite snapshot repository `25 passed, 30 subtests passed`; snapshot builder `14 passed, 15 subtests passed`; full repository suite `4475 passed, 2 skipped, 2841 subtests passed`. The two skips are platform-conditional symlink tests. Frozen Deba/RaceList/manifest byte lengths and SHA-256 values were unchanged before and after testing. Provider HTTP / Phase44 / GET: `0 / 0 / 0`; production database writes: `0`.

Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`. Successful identity binding alone does not establish historical availability, status, snapshot completeness, or replay readiness.

Next action: `CHATGPT_REVIEW_PHASE88_IMPLEMENTATION`.

### Frozen Phase85 bundle-authenticity gate

The binder must not trust the publicly constructible Phase85 dataclass merely because it has the expected type. Before it parses an entry identity or queries SQLite, it requires the exact `NARRaceEntryStatusSourceProfileFixtureBundleV3` type, exact target `NAR / 21 / 2025-01-01 / 6`, and exact path tuple `(EXPECTED_DEBA_TABLE_PATH_V3, EXPECTED_RACE_LIST_PATH_V3, EXPECTED_MANIFEST_PATH_V3)`. It independently requires these exact bundle bytes:

- DebaTable: `313317` / `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`
- RaceList: `66307` / `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`
- manifest: `4254` / `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d`.

It also requires exact manifest type, `bundle.manifest.canonical_bytes() == bundle.manifest_bytes`, exact manifest provider/target/acquisition semantics, FixtureSetV3 identity `nar-race-entry-status-source-profile-fixture-set-v3:11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225`, and QualificationV3 identity `nar-race-entry-status-source-profile-qualification-v3:a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff`. Any failure is `UNSUPPORTED_BUNDLE`; the binder does not call the filesystem loader again, recover from network, or accept a self-constructed substitute.

### Fixed V010 mapping and provider authority

The persisted authority remains V010, not a replacement mapping design. `historical_input_external_races` has primary key `(organization, source_system, external_race_id)`, maps to `internal_race_id`, has reverse uniqueness `(organization, source_system, internal_race_id)`, and references both `historical_input_source_identities` and `races(id)`. `historical_input_external_entries` has primary key `(organization, source_system, external_race_id, external_entry_id)`, maps to `(internal_race_id, race_entry_id)`, has reverse uniqueness `(organization, source_system, internal_race_id, race_entry_id)`, and references the exact race mapping and `(horses.race_id, horses.id)`. V015 validates these V010 keys and foreign keys before adding JRA-only seed objects; it does not replace the NAR mapping authority.

The future binder supports exactly organization `NAR`, source system `nar_official`, and Phase85's only target `NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)`. It derives—not accepts from a caller—the exact external race ID `nar:20250101:21:6`. This grammar is already used by `scripts/simulation/nar_historical_input_source.py::normalize_nar_historical_input_source_records` and `scripts/simulation/nar_historical_daily_target_source.py`; it must agree with the bundle target and the SQLite mapping row.

### Complete entry-identity extraction decision

Classification: `DEDICATED_ENTRY_IDENTITY_EXTRACTION_REQUIRED`.

No existing public production authority exposes every Phase85 source row as `(horse_no, external_entry_id, external_horse_id)` without status or market semantics. Profile-A v3 retains only bounded counts plus one selected non-14 horse number; Profile-B v2 retains a bounded horse-14 withdrawal association; Phase66 retains two RaceList candidate ancestry records; raw capture and the V3 manifest retain document/capture identity only. None is a complete entry universe.

Remote verification fixes a target-specific structural invariant: the published DebaTable has exactly fourteen entry rows, whose unique horse numbers are exactly `1..14`; horse 14 has one canonical `a.horseName[href]` link and its row contains `出走取消`. The future binding authority must derive membership solely from the unique validated Deba entry-table row set, retain all fourteen identities including horse 14, and never use the withdrawal text, RaceList `changeInfo`, odds, or other status-bearing values to remove, mark, or otherwise interpret an entry. If a required identity cannot be structurally recovered, binding fails; no row is skipped.

The extractor is a private, status-neutral part of the future binder—not a fifth production module. It may safely reuse only a helper independently limited to identity-only validation; `nar_historical_input_source._horse_rows` is eligible only for entry-table row selection and `_canonical_horse_identity` only for strict provider-local link validation. It must not call `normalize_nar_historical_input_source_records` or `_row_values`, because those require odds/jockey handling and reject cancellation-marked rows. For each extracted row it requires exactly one positive `horseNum` and exactly one canonical `horseName` link, then derives:

- external entry ID: `{external_race_id}:entry:{horse_no}`
- frozen-target grammar: `nar:20250101:21:6:entry:<horse_no>`
- external horse ID: the provider-local `nar:horse:{k_lineageLoginCode}`.

This entry-ID convention is approved because it is the current NAR normalizer convention and is independently used by NAR target-result/payout persistence for provider-scoped entry reconstruction. It never uses row order. `external_horse_id` is supporting provider-local evidence only, is not the V010 lookup key, and has no reviewed cross-provider database binding: `EXTERNAL_HORSE_ID_DATABASE_BINDING = UNSUPPORTED` and `CROSS_PROVIDER_HORSE_IDENTITY = UNSUPPORTED`.

### Explicit read-only connection and schema contract

The preferred public boundary is:

```python
def bind_nar_race_entry_status_v3_identity(
    *,
    bundle: NARRaceEntryStatusSourceProfileFixtureBundleV3,
    connection: sqlite3.Connection,
) -> NARRaceEntryStatusReplayIdentityBinding:
    ...
```

`bundle` and `connection` must be exact types. The caller owns the connection; the binder accepts no database path, global connection, CWD lookup, environment lookup, connection creation, or attached database. No separate path binding is required: `PRAGMA database_list` must prove a single approved `main` database and no auxiliary attachment; this permits an explicit in-memory connection in isolated tests without hidden path discovery. A transaction-free caller connection with pre-existing `PRAGMA foreign_keys == 1` and `PRAGMA query_only == 1` is a hard precondition. The binder must not enable, disable, or otherwise leave caller-visible PRAGMA state changed. Only after those checks may it begin one owned deferred read transaction, which it rolls back in `finally` on every success or failure; it never commits or closes the connection.

The future module must use a private schema inspector based on the read-only pattern in `sqlite_nar_daily_evidence_resolver.py::_schema`, without importing replay resolution. Before querying mappings it must inspect exact required tables, column names/types, V010 primary keys, relevant unique keys, and `RESTRICT` foreign keys for `historical_input_source_identities`, `historical_input_external_races`, `historical_input_external_entries`, `races`, and `horses`; it must require `ux_horses_race_id_id` or its exact `(race_id, id)` unique equivalent and run `foreign_key_check` for consumed mapping tables. Similar names or SELECT-compatible views are insufficient. It must contain no DDL/DML or database-control statement (`INSERT`, `UPDATE`, `DELETE`, `REPLACE`, `CREATE`, `DROP`, `ALTER`, `ATTACH`, `DETACH`, `VACUUM`, `REINDEX`) and no mapping repair/upsert path.

### Closed lookup, set closure, and horse-number rules

The race lookup is exactly `(NAR, nar_official, nar:20250101:21:6)`. It requires one forward mapping, one matching reverse mapping for the selected `internal_race_id`, and exactly one referenced `races.id`. No row is `INTERNAL_RACE_MAPPING_MISSING`; duplicate rows are `INTERNAL_RACE_MAPPING_AMBIGUOUS`; mismatches are `INTERNAL_RACE_MAPPING_CONTRADICTION`.

For every extracted external entry ID, the binder requires exactly one V010 mapping to the already-bound internal race and one positive `race_entry_id`. It also loads the full database entry-map set for the external race and requires exact equality with the complete source entry-ID set: missing source entries, unexpected DB entries, duplicate identities, or inconsistent internal race IDs fail closed. There is no historical-schema exception that permits extra entries.

`horses.horse_no` is an existing race-scoped field and may be used only after exact V010 entry mapping has selected `(internal_race_id, race_entry_id)`. The binder must load that exact `horses` row, require `race_id` equality, a positive integer `horse_no`, and equality with the source horse number; this is an additional `HORSE_NUMBER_CONTRADICTION` check, not a lookup or uniqueness substitute. The legacy schema does not prove `(race_id, horse_no)` unique, so horse number can never independently resolve a `race_entry_id`.

### Immutable result and semantic firewall

The new module may define only these immutable result values:

```python
@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusReplayIdentityEntryBinding:
    external_entry_id: str
    external_horse_id: str
    horse_no: int
    race_entry_id: int

@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusReplayIdentityBinding:
    target: NARRaceEntryStatusRaceIdentity
    organization: str
    source_system: str
    external_race_id: str
    internal_race_id: int
    entry_bindings: tuple[NARRaceEntryStatusReplayIdentityEntryBinding, ...]
```

All values must be exact immutable types; `entry_bindings` is canonicalized by numeric `horse_no` only after set validation, never inferred from source row order. The binding retains no database connection, mapping, status, eligibility, market, snapshot, replay, or settlement field. It returns every extracted source entry exactly once or raises—never a partial tuple, a best-effort result, or a skipped withdrawn entry.

The public base error should be `NARRaceEntryStatusReplayIdentityBindingError`, with stable classifications: `UNSUPPORTED_BUNDLE`, `SQLITE_CONNECTION_INVALID`, `SQLITE_SCHEMA_INVALID`, `EXTERNAL_RACE_IDENTITY_CONTRADICTION`, `INTERNAL_RACE_MAPPING_MISSING`, `INTERNAL_RACE_MAPPING_AMBIGUOUS`, `INTERNAL_RACE_MAPPING_CONTRADICTION`, `SOURCE_ENTRY_IDENTITY_INVALID`, `ENTRY_MAPPING_MISSING`, `ENTRY_MAPPING_AMBIGUOUS`, `ENTRY_MAPPING_CONTRADICTION`, `DATABASE_ENTRY_SET_CONTRADICTION`, `DUPLICATE_RACE_ENTRY_ID`, `INTERNAL_ENTRY_ROW_MISSING`, `HORSE_NUMBER_CONTRADICTION`, and `CROSS_PROVIDER_IDENTITY_UNSUPPORTED`.

Binding may consume only the validated Phase85 fixture, preexisting V010 mapping rows, and internal race/entry rows. It cannot query outcomes, payouts, settlement captures, odds, future snapshots, or other post-cutoff evidence to repair identity. Withdrawal status, market eligibility, positive market eligibility, and `WHOLE_MEETING_CANCELLATION` remain separate and `UNSUPPORTED`; no status application, filtering, snapshot construction, replay, or persistence is in scope.

### Exact future scope, tests, and stop condition

The dedicated private extractor can live inside the binder, so no support-file change is required. Future implementation scope is exactly:

- CREATE `scripts/simulation/nar_race_entry_status_replay_identity_binding.py`
- CREATE `tests/test_nar_race_entry_status_replay_identity_binding.py`
- MODIFY `docs/CURRENT_PHASE.md`
- MODIFY `docs/LATEST_CODEX_REPORT.md`

Any fifth path is `PHASE88_IDENTITY_BINDING_SUPPORT_SCOPE_REQUIRES_DESIGN_REVISION`. Existing fixture consumer, V3 bytes, normalizer, schema/migrations, replay, snapshots, market, result, and payout authorities are validate-only or out of scope.

Focused tests must cover valid complete fourteen-entry binding; horse numbers exactly `1..14`; horse 14 retained despite `出走取消`; extraction without odds; forged Deba/RaceList/manifest/formal-identity bundles; wrong type/target; derived race/entry IDs; duplicate source horse number or entry identity; absent/malformed provider-horse link; non-SQLite/active/foreign-keys-off/query-only-off/attached connections; missing tables/columns/types; V010 PK/unique/FK mutations; missing/contradictory race map or internal race; missing/wrong-race entry map; duplicate mapped `race_entry_id`; unexpected DB entry; missing internal horses row; horse-number mismatch and non-lookup behavior; external-horse non-lookup behavior; exact source/DB set equality; deterministic horse-number order/repeat equality; no partial result; owned rollback on success/failure; no connection close or caller-PRAGMA mutation; static no-write/no-network audit; no snapshot/result/payout/odds/settlement dependency; and CWD independence. Tests use temporary SQLite databases and copied/local fixture bytes only; committed V3 fixtures remain untouched.

Required future execution order is: `tests/test_nar_race_entry_status_replay_identity_binding.py`; `tests/test_nar_race_entry_status_source_profile_fixture_consumer.py`; `tests/test_nar_race_entry_status_source_profile_v3_fixtures.py`; `tests/test_historical_input_snapshot_migration.py`; `tests/test_sqlite_historical_input_snapshot_repository.py`; `tests/test_historical_input_snapshot_builder.py`; then the established full repository suite. Every stage must pass and record its actual count.

Stop without implementation if the private extractor cannot preserve every structurally recoverable source row, V010 schema cannot be proven, a mapping is absent/ambiguous/contradictory, a fifth path is needed, or any proposed behavior requires status, market, replay, write, or provider authority.

### Readiness matrix

| Item | Ready |
| --- | --- |
| A. Phase87 review frozen | YES |
| B. V010 race mapping authority fixed | YES |
| C. V010 entry mapping authority fixed | YES |
| D. Complete source entry identity extraction classified | YES |
| E. Cancelled-row identity handling defined | YES |
| F. External race ID contract defined | YES |
| G. External entry ID contract defined | YES |
| H. horse_no scope defined | YES |
| I. external_horse_id scope defined | YES |
| J. SQLite connection safety defined | YES |
| K. Schema validation defined | YES |
| L. Race lookup closed | YES |
| M. Entry lookup closed | YES |
| N. Source/DB entry-set closure defined | YES |
| O. Internal row validation defined | YES |
| P. Immutable result defined | YES |
| Q. Error model defined | YES |
| R. No partial result defined | YES |
| S. No-write rule defined | YES |
| T. Causal boundary defined | YES |
| U. Status/market/replay remains out of scope | YES |
| V. Future implementation scope classified | YES |

Provider HTTP / Phase44 / GET: `0 / 0 / 0`.

Modified paths: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`. Staged/untracked: `EMPTY / EMPTY`.

Next: `EXECUTE_APPROVED_PHASE`.

## Historical current-phase records

### POST_V0_8_DAILY_REPLAY_87

Title: NAR Replay Identity Binding Authority Audit

Status: DRAFT_FOR_REVIEW

Outcome: READY_FOR_ARCHITECTURAL_REVIEW

Audit: NAR_REPLAY_IDENTITY_BINDING_AUTHORITY_AUDIT_COMPLETE

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `33d8c755c862c073f5783c3645ac0958376afa2c` / `70d040a7c90b5029b090d6aabce56974b3366a5a`

Prior formal state: `POST_V0_8_DAILY_REPLAY_85 = FORMALLY_COMPLETE`; `POST_V0_8_DAILY_REPLAY_86 = FORMALLY_COMPLETE`; `STRICT_LOCAL_V3_SOURCE_PROFILE_FIXTURE_CONSUMER = FORMALLY_INTEGRATED`.

### Frozen source-profile authority and semantic boundary

The published target remains exactly `NAR / 21 / 2025-01-01 / 6`. Phase85's `load_nar_race_entry_status_source_profile_v3_fixture` in `scripts/simulation/nar_race_entry_status_source_profile_fixture_consumer.py` returns only `NARRaceEntryStatusSourceProfileFixtureBundleV3`: exact target, Deba/RaceList/manifest bytes, rebuilt manifest, Phase66 ancestry, publication plan, and canonical relative paths. It deliberately contains no internal race ID, internal race-entry ID, external race ID, external entry-ID collection, database handle, snapshot, or replay object.

The consumer's `target` is `NARRaceEntryStatusRaceIdentity` from `scripts/simulation/nar_race_entry_status_raw_capture.py`, whose exact fields are `baba_code: str`, `race_date: date`, and `race_no: int`. Raw capture supplies provider NAR and request/capture identities for `deba_table` and `race_list`; it does not provide an internal KeibaOS identity. The frozen source-profile bytes and identities remain unchanged.

This audit preserves `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`. It establishes no historical availability, replay readiness, or market-eligibility claim.

### Source identity map

`scripts/simulation/nar_historical_input_source.py` contains the existing NAR source-normalizer identity grammar. `normalize_nar_historical_input_source_records` canonicalizes a Deba URL and constructs:

- provider identity: `organization="NAR"`, `source_system="nar_official"`
- external race: `nar:{YYYYMMDD}:{baba_code}:{race_no}`
- external entry: `{external_race_id}:entry:{horse_no}`
- external horse: `nar:horse:{k_lineageLoginCode}` from the provider-local horse-link query parameter.

Its `NarSuppliedOfficialResponse` is the only current typed route from raw official Deba HTML to `HistoricalInputSourceRecord` in `scripts/simulation/historical_input_source_records.py`. A source record has provider/source-system/external-race/external-entry fields, but no internal IDs. The normalizer requires positive unique `horse_no` values within its exact Deba race, and it rejects cancellation-marked rows and unsupported odds before it returns records. Consequently it cannot be used unchanged as a neutral all-row identity projector: doing so would silently make the later entry/status and market domains preconditions of identity binding.

`scripts/simulation/nar_historical_daily_target_source.py` independently uses the same NAR race-ID grammar when a RaceList title link is proven to match its exact date, venue, and race number. This supports the grammar's existing repository scope, but it is a target-discovery component rather than a binding authority and does not read the Phase85 V3 bundle.

### Internal identity map and existing mapping authority

`scripts/simulation/historical_input_snapshots.py` requires `HistoricalInputSnapshot.internal_race_id: int` and `HistoricalRaceEntrySnapshot.race_entry_id: int`. Its `HistoricalExternalRaceIdentity` key is `(organization, source_system, external_race_id)`; `HistoricalExternalEntryIdentity` adds `external_entry_id`. `external_horse_id` is explicitly non-key metadata (`compare=False`, `hash=False`). Snapshot validation requires unique internal race-entry IDs, unique horse numbers, and unique external-entry identities only inside the one exact snapshot/race identity.

`scripts/simulation/historical_input_snapshot_builder.py::build_historical_input_snapshot` does not resolve identities: its caller must already supply `internal_race_id` and a complete, one-to-one `race_entry_id_by_external_entry_id` mapping. It also enforces causal source-evidence timing, so identity binding must not substitute post-cutoff status, result, or settlement evidence.

The exact persisted authority is migration `scripts/migrations/versions/v010_historical_input_snapshot_schema.py`:

- `historical_input_external_races` is keyed by `(organization, source_system, external_race_id)` and maps to `internal_race_id`; it also has `UNIQUE (organization, source_system, internal_race_id)` and an FK to `races(id)`.
- `historical_input_external_entries` is keyed by `(organization, source_system, external_race_id, external_entry_id)` and maps to `(internal_race_id, race_entry_id)`; it has `UNIQUE (organization, source_system, internal_race_id, race_entry_id)`, an FK to the exact external-race mapping, and an FK to `(horses.race_id, horses.id)`.
- the same migration defines `ux_horses_race_id_id`; neither this schema nor the legacy `scripts/database.py` table establishes a database uniqueness constraint for `(race_id, horse_no)`.

`scripts/simulation/sqlite_nar_daily_evidence_resolver.py::_prediction` is the existing read-side proof of race-map semantics: it queries the exact provider-scoped external-race key, requires exactly one forward result, exactly one matching reverse result, and an existing `races.id`; absent rows yield `INTERNAL_RACE_MAPPING_MISSING`, while multiple or contradictory rows are integrity failures. `SQLiteHistoricalInputSnapshotRepository` validates the same rows when loading snapshots, but `_ensure_external_race` and `_ensure_external_entry` are write-side persistence helpers and are not suitable as the future no-write binder.

The legacy `scripts/database.py::race_exists`, `save_race`, `horse_exists`, and `get_horse_id` query date/organization/place/race number or `(race_id, horse_no)` with `LIMIT 1`, but their table definitions do not make those combinations formal unique mapping authority. They must not replace the V010 provider-scoped external-map tables.

### Binding classifications and fail-closed conclusion

Race binding is `RACE_BINDING_AUTHORITY_PARTIAL`: the schema and daily resolver prove a deterministic exact mapping *when an existing `historical_input_external_races` row is present*, but no Phase85-to-read-only-mapping adapter exists and absence must remain a hard missing-mapping failure.

Entry binding is `ENTRY_BINDING_AUTHORITY_PARTIAL`: the V010 table proves an exact provider-scoped entry-to-`race_entry_id` mapping *when rows already exist*, but the Phase85 bundle has no typed external-entry projection and no public read-only bulk resolver. The existing whole-source normalizer is not an acceptable substitute because it rejects cancellation rows and parses odds/jockey semantics. A future binder must bind every source entry identity or fail the entire race; it may not drop withdrawn/cancelled/unsupported rows or return a partial set.

`horse_no` is safe only as a race-scoped consistency check after the exact external-race mapping; it is not a global horse identity and legacy `LIMIT 1` queries do not prove unique authority. `external_horse_id` is NAR-provider-local, is not a persisted map key, and has no reviewed cross-provider mapping. Therefore `CROSS_PROVIDER_HORSE_IDENTITY = UNSUPPORTED`, and horse name, jockey name, display text, fuzzy/normalized matching, race-name matching, row position, outcomes, or settlement data are prohibited as binding evidence.

The exact primary blocker is `REPLAY_IDENTITY_BINDING_SUPPORT_REQUIRED`.

### Proposed next architecture (design only)

The next implementation should be a small, no-network, read-only SQLite-backed identity-binding authority, conventionally named `scripts/simulation/nar_race_entry_status_replay_identity_binding.py`, with focused tests at `tests/test_nar_race_entry_status_replay_identity_binding.py`, plus the two phase-control documents. It should accept the Phase85 `NARRaceEntryStatusSourceProfileFixtureBundleV3` and an explicit read-only identity-mapping repository/connection; no DB/session object belongs inside the Phase85 bundle.

It must create a distinct immutable identity-projection/result object containing only the NAR provider-scoped external race identity, the complete source entry-identity set, exact internal race ID, and one-to-one internal race-entry bindings. It must query V010 mapping tables only; it must distinguish unsupported provider/target, race map missing/ambiguous/contradictory, entry map missing/ambiguous/duplicate, duplicate internal entry, horse-number contradiction, cross-provider unsupported, and temporally ineligible identity evidence. It must neither write mappings nor build snapshots, apply entry/status meanings, promote market eligibility, construct betting/replay inputs, run replay, or use network.

The binder must separately retain identity evidence from status, market, and settlement evidence. It may not use result/settlement data or evidence acquired after the prediction cutoff to create a binding. If a source-row identity cannot be established without entering status semantics, that is a fail-closed binder error—not permission to omit the row. The next blocker after a reviewed identity-binder implementation must be re-audited; Phase87 does not select an entry/status or market implementation.

### Ordered dependency graph

1. **Published V3 bytes and Phase85 local consumer — complete.** Existing V3/Phase85 authority is no-network and read-only, but ends at a validated source-profile bundle.
2. **Provider-scoped external-to-internal race/entry binding — missing read-side authority.** V010 schema supplies stored mapping evidence, so implementation can be no-network/read-only SQLite when maps pre-exist; it requires no new live authorization. Missing/ambiguous rows must fail closed.
3. **Entry/status semantic application — not audited as implementable.** The normalizer's cancellation rejection confirms this cannot be silently folded into binding; it needs a later dedicated authority and may remain no-network if the local source is sufficient.
4. **Complete causally eligible historical snapshot — unavailable until identity and status/input completeness are resolved.** Snapshot builder requires all mapped entries and cutoff-eligible source records.
5. **Market eligibility, odds, and official payout/settlement — unresolved later dependencies.** Their data authority may require distinct review and, if fresh provider data is necessary, a future one-shot live authorization.

### Readiness matrix

| Item | Ready |
| --- | --- |
| A. Phase85/86 formal completion frozen | YES |
| B. Source race identity mapped | YES |
| C. Source entry identity mapped | YES |
| D. Internal race identity requirements mapped | YES |
| E. Internal entry identity requirements mapped | YES |
| F. Existing mapping authorities exhausted | YES |
| G. SQLite schema inspected | YES |
| H. Race-binding availability classified | YES |
| I. Entry-binding availability classified | YES |
| J. horse_no safety classified | YES |
| K. external_horse_id scope classified | YES |
| L. Cross-provider name/horse linking prohibited | YES |
| M. Causal identity boundary defined | YES |
| N. No partial binding rule defined | YES |
| O. Future implementation architecture proposed | YES |
| P. Status/replay/market remains out of scope | YES |
| Q. No network/Phase44/GET | YES |
| R. Docs-only PREPARE scope preserved | YES |

Provider HTTP / Phase44 / GET: `0 / 0 / 0`.

Modified paths: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`. Staged/untracked: `EMPTY / EMPTY`.

Next: `CHATGPT_REVIEW_PHASE87_IDENTITY_BINDING_AUDIT`.

## Historical current-phase records

### POST_V0_8_DAILY_REPLAY_86

Title: Phase85 Post-Commit Documentation Reconciliation

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_DOCUMENTATION_REVIEW

Implementation: PHASE85_POST_COMMIT_DOCUMENTATION_RECONCILIATION_IMPLEMENTED

Design Contract: PHASE85_POST_COMMIT_DOCUMENTATION_RECONCILIATION_CONTRACT_COMPLETE

Design Review: PHASE86_DOCUMENTATION_RECONCILIATION_DESIGN_REVIEW_PASS

Primary blocker resolved: PHASE85_LATEST_REPORT_POST_COMMIT_STATE_STALE

Authorization: NONE_REQUIRED_DOCS_ONLY

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `496d581120be5bda5326ed6a95b17169e92adbdc` / `2ad0df638e31b4275a63b8a1fa63e408bca4ee0d`

Phase85 implementation review: `PHASE85_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`

Phase85 code state/formal state: `IMPLEMENTATION_VERIFIED` / `POST_V0_8_DAILY_REPLAY_85 = FORMALLY_COMPLETE`

Integrated authority: `STRICT_LOCAL_V3_SOURCE_PROFILE_FIXTURE_CONSUMER = FORMALLY_INTEGRATED`

### Frozen proven state and exact reconciliation

The independently verified Phase85 commit is `496d581120be5bda5326ed6a95b17169e92adbdc`, with tree `2ad0df638e31b4275a63b8a1fa63e408bca4ee0d`, parent `c6e06ac5331b2f056534efa58756383e587ec27e`, and message `feat: add strict local NAR V3 fixture consumer`. At the start of Phase86, local and remote-tracking branch heads equaled that commit. Its exact committed paths were:

- `scripts/simulation/nar_race_entry_status_source_profile_fixture_consumer.py`
- `tests/test_nar_race_entry_status_source_profile_fixture_consumer.py`
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

The Phase85 implementation report now records the actual commit and normal push. Its final worktree was clean, with empty staged and untracked sets. The documentation defect identified by independent remote review is resolved. Phase86 changed no Phase85 code, test, or fixture bytes.

Phase86 modified exactly `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. The final Phase85 implementation result is reconciled without changing historical PREPARE and APPROVE chronology or rerunning tests. The formal Phase85 verdict rests on the existing independent remote verification.

The frozen test evidence is focused consumer `40 passed, 2 skipped`; dedicated V3 fixture `4 passed`; publication contract `49 passed`; publication plan `45 passed`; Profile-A `17 passed`; Profile-B diagnostics `38 passed`; Phase66 `152 passed`; full suite `4427 passed, 2 skipped, 2841 subtests passed`. The two skips are platform-conditional symlink creation cases. The published Deba/RaceList/manifest Git blobs remain `e0da768cb7c5cb98c4ae060e463581f829d2eb79`, `57bb0d763b30401080cc577251e53fc9335f05ad`, and `63d6f05cb7807d25e3ea84118e24ffee6ded0e5e`; content identities remain 313317 / `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`, 66307 / `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`, and 4254 / `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d`.

Historical semantics remain `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`; market eligibility, positive market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`. Provider HTTP / Phase44 / GET: `0 / 0 / 0`.

### Readiness matrix

| Item | Ready |
| --- | --- |
| A. Phase85 code review result frozen | YES |
| B. Actual Phase85 commit identity frozen | YES |
| C. Remote branch state frozen | YES |
| D. Exact stale documentation statement identified | YES |
| E. No production correction required | YES |
| F. No test correction required | YES |
| G. No fixture correction required | YES |
| H. Exact docs-only two-path scope defined | YES |
| I. Post-commit facts defined | YES |
| J. Historical PREPARE/APPROVE chronology preserved | YES |
| K. Phase85 final formal verdict defined after reconciliation | YES |
| L. No network/Phase44/GET | YES |
| M. No stage/commit/push during PREPARE | YES |

Production code changes / test changes / fixture changes: `NONE / NONE / NONE`

Phase86 integration: one docs-only commit and normal push as authorized by `EXECUTE_APPROVED_PHASE`.

Next Action: `CHATGPT_REVIEW_PHASE86_DOCUMENTATION_RECONCILIATION`

## Historical current-phase records

### POST_V0_8_DAILY_REPLAY_85

Title: Strict Local V3 Source-Profile Fixture Consumer Authority

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Implementation: STRICT_LOCAL_V3_SOURCE_PROFILE_FIXTURE_CONSUMER_IMPLEMENTED

Design Contract: STRICT_LOCAL_V3_SOURCE_PROFILE_FIXTURE_CONSUMER_CONTRACT_COMPLETE

Design Review: PHASE85_FIXTURE_CONSUMER_DESIGN_REVIEW_PASS

Authorization: NONE_REQUIRED_NO_NETWORK_IMPLEMENTATION

Branch: `feature/post-v0.8-daily-replay`

Base Commit/tree: `c6e06ac5331b2f056534efa58756383e587ec27e` / `e5ae14c7d4da34f83afb32e5d83c06bc30471167`

Prior review: `PHASE84_REPLAY_CONSUMER_DEPENDENCY_AUDIT_REVIEW_PASS`

Primary dependency: `V3_FIXTURE_CONSUMER_SUPPORT_REQUIRED`

Phase85 implemented the approved strict local V3 fixture consumer and focused tests without provider HTTP, Phase44, GET, database access, replay, or snapshot construction.

### Closed purpose and published authority

Phase85 designs the first production read-side authority for the one committed NAR V3 source profile. Its boundary is exactly: canonical local location → stable byte reads → strict manifest/raw validation → existing Profile-A v3, Profile-B v2, Safety v3, FixtureSetV3, QualificationV3, ManifestV3, PublicationPlanV3, and Phase66 recomputation → immutable local bundle.

The only supported target is exact `NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)`. The three paths are derived from existing `EXPECTED_DEBA_TABLE_PATH_V3`, `EXPECTED_RACE_LIST_PATH_V3`, and `EXPECTED_MANIFEST_PATH_V3`; callers cannot supply paths and the loader cannot glob, choose a highest version, or fall back to V1/V2/provider data.

The published bytes remain frozen:

- DebaTable: 313317 bytes / `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`
- RaceList: 66307 bytes / `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`
- manifest: 4254 bytes / `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d`
- FixtureSetV3: `nar-race-entry-status-source-profile-fixture-set-v3:11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225`
- QualificationV3: `nar-race-entry-status-source-profile-qualification-v3:a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff`

The loader must require both deterministic recomputation and these frozen identities. A self-consistent replacement for the same target is not the published Phase83 fixture and must fail closed.

### Exact proposed API and immutable result

```python
def load_nar_race_entry_status_source_profile_v3_fixture(
    *,
    repository_root: Path,
    target: NARRaceEntryStatusRaceIdentity,
) -> NARRaceEntryStatusSourceProfileFixtureBundleV3:
    ...
```

`target` must be the exact production type and exact frozen value; dict, tuple, and duck-typed targets are rejected. `repository_root` must be the exact concrete `Path` type on the running platform, absolute, NUL-free, and an existing directory. The implementation must not use `Path.cwd()`, ambient relative opens, environment variables, or repository searching.

`NARRaceEntryStatusSourceProfileFixtureBundleV3` is a frozen, slotted, exact-type dataclass with the minimized fields:

- `target`
- `deba_table_bytes`
- `race_list_bytes`
- `manifest_bytes`
- `manifest` (`SourceProfileManifestV3`)
- `phase66_ancestry` (`ProfileBCandidateAncestryRecoveryDiagnostics`)
- `publication_plan` (`SourceProfilePublicationPlanV3`)
- `repository_relative_paths` (exact three-string tuple in Deba, RaceList, manifest order)

Separate fixture-set, qualification, safety, Profile-A, and Profile-B fields are intentionally omitted because the validated `manifest` already owns `fixture_set`, `qualification`, `publication_safety`, and the qualification owns both profiles. Bytes and tuples are immutable; all nested formal authorities are existing frozen objects. The result contains no DB, HTTP, session, replay, or historical-snapshot object and is not named as replay-ready or historical evidence.

### Filesystem and stable-read contract

The resolved repository root and each expected path must be absolute, contained beneath the resolved root, and free of `..` escape. Every path component from the root through the target directory and files is checked with non-following metadata; symbolic links and Windows reparse points are rejected wherever the platform exposes them. If the platform cannot establish the required regular-file/no-substitution property, loading fails rather than weakening the check.

The target V3 directory is closed and must contain exactly the set `{deba_table.html, race_list.html, manifest.json}`. Enumeration order is irrelevant; missing, extra, directory-substituted, symlinked, or reparse entries fail. This exact-set rule is cross-platform and intentionally rejects hidden or backup siblings.

Each artifact is opened once for binary read. Pre-open `lstat`, opened-handle `fstat`, post-read `fstat`, and post-close `lstat` identities are compared using available device/inode, regular-file mode, size, and nanosecond modification time. The exact bytes from that single read are retained; there is no second semantic read, rewrite, normalization, or temporary replacement.

### Strict manifest and raw validation

Manifest parsing requires exact bytes, strict UTF-8, one JSON object, duplicate-key rejection, non-finite-number rejection, and byte equality with canonical JSON (`ensure_ascii=False`, sorted keys, compact separators, `allow_nan=False`). Unknown schema/version/content cannot fall back. Exact formal reconstruction plus final canonical-byte equality rejects missing and unknown keys.

Before constructing formal objects, require provider `NAR`, exact target, acquisition semantics `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, market eligibility `UNSUPPORTED`, exactly two documents in `deba_table`, `race_list` order, and their exact V3 publication paths. Recompute SHA-256 and byte length from the single-read raw bytes and require agreement with document metadata.

`CaptureDocumentMetadata` is reconstructed only from the existing fields `document_role`, `request_identity`, `capture_identity`, `response_sha256`, `response_byte_length`, `requested_at`, `observed_at`, `captured_at`, and `effective_url_matches_canonical`; `CaptureMetadataSummary` adds only `closed_bundle_identity`. No URL, timestamp, capture, or identity is inferred.

### Formal recomputation and semantic firewall

The fail-closed validation order is fixed: filesystem/path closure → stable single reads → strict manifest parse/basic provider-target-semantics-path checks → raw SHA/length against manifest metadata → capture-metadata reconstruction → Profile-A/Profile-B/Safety recomputation → FixtureSet/Qualification/Manifest/Plan/Phase66 reconstruction → rebuilt canonical manifest equality → frozen Phase83 SHA/length and identity checks → immutable bundle construction. Thus profile, safety, and Phase66 formal-authority failures remain independently observable rather than being hidden by an early frozen-hash rejection.

Using the original loaded bytes, exact target, and reconstructed capture summary, the consumer runs existing production functions to obtain Profile-A v3, Profile-B v2, Safety v3, FixtureSetV3, QualificationV3, ManifestV3, PublicationPlanV3, and Phase66 ancestry. It requires:

- Profile-A exact V3, `QUALIFIED`, all three predicates PASS
- Profile-B exact V2, `QUALIFIED`, all six predicates PASS, target schedule count 1
- Safety exact V3, `SAFE`, all five categories SAFE with zero findings
- Phase66 one race scope, two target candidates, complete details, direct schedule 1, changeInfo 1
- Profile-B schedule count equals Phase66 direct schedule count
- rebuilt FixtureSetV3 and QualificationV3 identities equal both loaded manifest values and frozen Phase83 values
- rebuilt `SourceProfileManifestV3.canonical_bytes()` is byte-identical to the loaded manifest
- `validate_nar_race_entry_status_manifest_v3` and the exact V3 publication-plan validator both PASS

The bundle preserves `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`, `market_eligibility = UNSUPPORTED`, `positive_market_eligibility = UNSUPPORTED`, and `WHOLE_MEETING_CANCELLATION = UNSUPPORTED`. It exposes no `historical_available`, `historical_bytes`, `market_eligible`, `positive_market_eligible`, or equivalent promoted field.

The consumer must not import or call `normalize_nar_historical_input_source_records`, `build_historical_input_snapshot`, `resolve_sqlite_nar_daily_evidence`, `run_nar_daily_replay`, repository/database modules, requests/httpx/urllib openers/socket, provider acquisition, Phase44, or subprocess. A missing local fixture is a hard local failure with no network/provider fallback.

### Failure authority

The proposed module defines one base `NARRaceEntryStatusSourceProfileFixtureConsumerError` and four exact subclasses:

- `NARRaceEntryStatusSourceProfileFixtureUnsupportedError`
- `NARRaceEntryStatusSourceProfileFixtureFilesystemError`
- `NARRaceEntryStatusSourceProfileFixtureManifestError`
- `NARRaceEntryStatusSourceProfileFixtureAuthorityError`

Stable internal classifications distinguish `UNSUPPORTED_TARGET`, `FILESYSTEM_VIOLATION`, `MISSING_FIXTURE`, `UNEXPECTED_FIXTURE_DIRECTORY_CONTENT`, `MANIFEST_INVALID`, `DOCUMENT_IDENTITY_MISMATCH`, `TARGET_OR_PATH_CONTRADICTION`, `FORMAL_AUTHORITY_VALIDATION_FAILURE`, and `FROZEN_PHASE83_IDENTITY_MISMATCH`. No failure is recovered, skipped, or converted to an empty bundle.

### Implementation and verification result

The production module now implements the approved exact loader, frozen/slotted bundle, stable single-read filesystem authority, strict canonical-manifest parsing, existing Profile-A/Profile-B/Safety/FixtureSet/Qualification/Manifest/Plan/Phase66 recomputation, and final Phase83 frozen-identity gate. Its public error hierarchy exposes stable fail-closed classifications for unsupported targets, filesystem and missing-fixture violations, unexpected directory content, manifest errors, raw-document contradictions, target/path contradictions, formal-authority failures, and frozen-identity mismatch.

The focused test module covers valid and repeat loads, bundle type/immutability/path order, wrong type and target, relative/missing roots, missing files, V1/V2 no fallback, extra siblings, symlink/path escape/unstable identity, strict UTF-8/canonical/duplicate/non-finite JSON, manifest and raw mutations, independently reachable Profile-A/Profile-B/Safety/Phase66 failures, frozen alternate-identity rejection, CWD independence, and static no-network/no-DB/no-replay authority. Two symlink tests were conditionally skipped because link creation is unavailable in the current Windows environment; production rejection remains implemented and statically covered.

Required results, in approved order:

1. fixture consumer: `40 passed, 2 skipped`
2. committed V3 fixture: `4 passed`
3. publication contract: `49 passed`
4. publication plan: `45 passed`
5. Profile-A: `17 passed`
6. Profile-B diagnostics: `38 passed`
7. Phase66 structural diagnostics: `152 passed`
8. full repository suite: `4427 passed, 2 skipped, 2841 subtests passed`

The committed DebaTable, RaceList, and manifest were hashed before and after verification and remain exactly 313317 / 66307 / 4254 bytes with their frozen Phase83 SHA-256 values. Provider HTTP / Phase44 / GET remained `0 / 0 / 0`.

### Allowed Files, Forbidden Files, Required Tests, Stop Condition

Future implementation may change exactly:

- CREATE `scripts/simulation/nar_race_entry_status_source_profile_fixture_consumer.py`
- CREATE `tests/test_nar_race_entry_status_source_profile_fixture_consumer.py`
- MODIFY `docs/CURRENT_PHASE.md`
- MODIFY `docs/LATEST_CODEX_REPORT.md`

Everything else is forbidden, including existing authority modules, all committed fixtures, the dedicated V3 fixture test, `.gitattributes`, database files, and logs. A need for a fifth path is `PHASE85_APPROVED_CONTRACT_SUPPORT_MISMATCH` and stops implementation.

Required future test order:

1. `python -m pytest -q tests/test_nar_race_entry_status_source_profile_fixture_consumer.py`
2. `python -m pytest -q tests/test_nar_race_entry_status_source_profile_v3_fixtures.py`
3. `python -m pytest -q tests/test_nar_race_entry_status_source_profile_publication_contract.py`
4. `python -m pytest -q tests/test_nar_race_entry_status_source_profile_publication_plan.py`
5. `python -m pytest -q tests/test_nar_race_entry_status_source_profile_diagnostics.py`
6. `python -m pytest -q tests/test_nar_race_entry_status_source_profile_profile_a.py`
7. `python -m pytest -q tests/test_nar_race_entry_status_source_profile_structural_recovery_diagnostics.py`
8. full repository suite using the established command

Focused coverage must include the valid committed load, repeated deterministic equality, exact target, V1/V2/no-fallback rejection, every missing file, unexpected sibling, manifest/raw/target/order/path/hash/length/identity/semantic mutations, Profile-A/Profile-B/Safety/Phase66 blocked cases, path escape/symlink/reparse/substitution where testable, static no-network/no-DB/no-replay imports, and CWD independence. Mutations use temporary repository-shaped copies only. Before and after tests, all committed fixture hashes/lengths must remain frozen.

Implementation stops without staging/commit/push if any required check fails, a fifth path is needed, filesystem no-substitution cannot be proven, committed fixture identity changes, an existing authority must be weakened, or the consumer would need network, DB, replay, snapshot, identity-binding, or status-application behavior.

### Readiness matrix

| Item | Ready |
| --- | --- |
| A. Phase84 review frozen | YES |
| B. Primary blocker fixed as V3_FIXTURE_CONSUMER_SUPPORT_REQUIRED | YES |
| C. Exact published target closed | YES |
| D. Canonical V3 path authority defined | YES |
| E. No glob/version fallback | YES |
| F. Stable filesystem read contract defined | YES |
| G. Strict manifest parsing defined | YES |
| H. Raw hash/length recomputation defined | YES |
| I. Capture metadata reconstruction defined | YES |
| J. Profile-A/B/Safety recomputation defined | YES |
| K. FixtureSet/Qualification/Manifest recomputation defined | YES |
| L. Phase66 structural check defined | YES |
| M. Immutable bundle boundary defined | YES |
| N. Historical semantic firewall defined | YES |
| O. Historical normalizer/snapshot/replay excluded | YES |
| P. Network/provider access excluded | YES |
| Q. DB writes excluded | YES |
| R. Negative mutation coverage defined | YES |
| S. Committed fixture mutation prohibited | YES |
| T. CWD independence defined | YES |
| U. Future implementation exact four-path scope defined | YES |

Provider HTTP / Phase44 / GET: `0 / 0 / 0`

Production implementation: `YES`

Tests implemented: `YES`

Final Phase85 staging / commit / push: `EMPTY / SUCCESS / SUCCESS`; local and remote-tracking HEAD after Phase85 were both `496d581120be5bda5326ed6a95b17169e92adbdc`, and the worktree and untracked set were clean and empty.

Next Action: `CHATGPT_REVIEW_PHASE85_IMPLEMENTATION`

### Earlier historical records

## POST_V0_8_DAILY_REPLAY_84

Title: Post-V3 Publication Replay-Consumer Dependency Audit

Status: DRAFT_FOR_REVIEW

Outcome: READY_FOR_ARCHITECTURAL_REVIEW

Audit: POST_V3_PUBLICATION_REPLAY_CONSUMER_DEPENDENCY_AUDIT_COMPLETE

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `c6e06ac5331b2f056534efa58756383e587ec27e` / `e5ae14c7d4da34f83afb32e5d83c06bc30471167`

Prior verification/state: `PHASE83_INTEGRATION_REMOTE_VERIFICATION_PASS`; `POST_V0_8_DAILY_REPLAY_83 = FORMALLY_COMPLETE`; `V3_SOURCE_PROFILE_PUBLICATION = FORMALLY_INTEGRATED`.

This phase is a documentation-only architectural audit. It performs no provider HTTP, Phase44, GET, acquisition, fixture regeneration, live authorization, production/test implementation, staging, commit, or push.

### Frozen V3 publication authority

The integrated V3 artifacts remain unchanged:

- DebaTable: 313317 bytes, SHA-256 `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`
- RaceList: 66307 bytes, SHA-256 `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`
- manifest: 4254 bytes, SHA-256 `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d`
- dedicated V3 test: 10467 bytes, SHA-256 `a7339350be7e0724bd75408534a094c544bf6776eb57118e70ae6dd314e7b3ff`
- FixtureSetV3: `nar-race-entry-status-source-profile-fixture-set-v3:11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225`
- QualificationV3: `nar-race-entry-status-source-profile-qualification-v3:a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff`

The authority remains `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`. `market_eligibility`, `positive_market_eligibility`, and `WHOLE_MEETING_CANCELLATION` remain `UNSUPPORTED`. The committed current-byte fixture does not establish historical provider availability or historical bytes.

### Consumer path and symbol map

| Path / symbol | Role | Accepted fixture / manifest versions | V3 support and fallback | Fail-closed / leakage finding |
| --- | --- | --- | --- | --- |
| `tests/test_nar_race_entry_status_source_profile_v3_fixtures.py::_recompute` | The only code that discovers the committed target paths, reads both HTML files and `manifest.json`, and recomputes the formal authority | Exact V3 paths and schema 3 manifest | V3 is explicit; no V1/V2 or network fallback; not accidental | Test-only. It preserves unsupported semantics and rejects contradictions, but is not a replay consumer. |
| `scripts/simulation/nar_race_entry_status_source_profile_fixture_test_generator.py::render_nar_race_entry_status_source_profile_v3_fixture_test` | Generates the dedicated test from already supplied bytes plus formal V3 authority | Exact `SourceProfileManifestV3` and `SourceProfilePublicationPlanV3` | Explicit V3; no discovery or fallback | Pure renderer; cannot feed replay. |
| `scripts/simulation/nar_race_entry_status_source_profile_fixture_test_preflight.py::run_nar_race_entry_status_source_profile_v3_fixture_test_preflight` | Runs the generated test against a synthetic external mirror | Synthetic V3 only | Explicit V3; no provider fallback | Validates renderer execution, not committed fixture consumption. |
| `scripts/simulation/nar_race_entry_status_source_profile_publication_contract.py::{FixtureSetV3,QualificationV3,SourceProfileManifestV3,validate_nar_race_entry_status_manifest_v3}` | Formal V3 object and validation authority | V3 objects; separate V2 authority also exists | V3 explicit; caller must already construct the objects | No repository discovery, deserialization-to-replay, or fallback. |
| `scripts/simulation/nar_race_entry_status_source_profile_publication_plan.py::{build_nar_race_entry_status_source_profile_publication_plan_v3,validate_nar_race_entry_status_source_profile_publication_plan_v3}` | Exact publication-path authority | V3 plan; separate V2 plan | V3 explicit | Publication authority only, not a read-side consumer. |
| `scripts/simulation/nar_race_entry_status_reacquisition_observability.py::{validate_journal_bytes,validate_journal_semantics,reconstruct_execution}` | Phase50 durable evidence validation | Journal identities and dedicated-test paths for V1/V2/V3 | V3 explicitly allowed; no fixture-content fallback | Reconstructs acquisition/publication evidence, not replay input. |
| `scripts/simulation/nar_daily_replay_orchestrator.py::run_nar_daily_replay` | Current NAR daily replay entry point | No source-profile fixture or manifest version | V3 is neither accepted nor accidentally discovered; no fixture fallback | Requires a daily-target acquisition result plus SQLite historical snapshot and settlement-capture stores. It never searches `source_profiles`. |
| `scripts/simulation/sqlite_nar_daily_evidence_resolver.py::resolve_sqlite_nar_daily_evidence` | Resolves replay prediction and settlement evidence | SQLite snapshot/capture schemas, not source-profile fixtures | No V1/V2/V3 fixture support or fallback | Read-only and fail-closed for missing, ambiguous, noncausal, or mismatched evidence; prediction capture/cutoff must not exceed scheduled start. |
| `scripts/simulation/historical_input_snapshot_simulation_adapter.py::build_simulation_race_input_from_historical_snapshot` | Converts a persisted historical snapshot to `SimulationRaceInput` | `HistoricalInputSnapshot`, not fixture manifests | No fixture support | Requires already bound internal race-entry IDs, odds, jockey, track, and past-race evidence. |
| `scripts/simulation/nar_historical_input_source.py::normalize_nar_historical_input_source_records` | Pure normalization of a caller-supplied DebaTable response | Raw supplied response only; no source-profile manifest | No directory/version selection and no RaceList/manifest binding | Emits track/entry/jockey/win-odds records. Cancellation/status markers raise `NarHistoricalInputSourceUnsupportedError`; they are not silently skipped. Direct historical use without snapshot/cutoff authority would risk future leakage. |
| `scripts/simulation/historical_input_snapshot_builder.py::build_historical_input_snapshot` | Builds a formal snapshot from normalized records and explicit external-to-internal mapping | Source-record contract, not fixtures | No fixture support | Requires complete `race_entry_id_by_external_entry_id`; record kinds have no entry-status member. |
| `scripts/simulation/historical_input_source_records.py::SourceRecordKind` | Defines normalized historical source-record kinds | `track`, `entry`, `jockey`, `odds_win`, `past_race`, `past_race_absence` | No V3 concept | No withdrawal/non-run/status record exists, so status cannot silently become replay authority. |

No production replay consumer currently reads NAR source-profile fixture directories. Consequently, no runtime consumer is merely V1/V2-only: the runtime read side is absent. V3 is explicit only in publication, validation, observability, generator, preflight, and the dedicated test. Repository search found no accidental runtime acceptance and no network fallback from replay to these artifacts.

### Local-only trace for NAR / 21 / 2025-01-01 / 6

1. **Fixture discovery — BLOCKED.** The four committed paths exist and the dedicated test knows their literal locations, but there is no production catalog/loader selecting a target and source-profile version.
2. **Manifest validation — TEST-ONLY.** The dedicated V3 test reconstructs and validates V3 authority, but no reusable runtime loader exposes that result to replay.
3. **Identity binding — NOT REACHED.** Existing snapshot construction requires an explicit mapping from NAR external race/entry identities to internal `race_id`/`race_entry_id`; the V3 fixture consumer path supplies none.
4. **Entry/status consumption — NOT REACHED.** The current historical source record contract has no status kind, and the NAR normalizer fails closed on cancellation markers.
5. **Replay input construction — NOT REACHED.** The replay adapter accepts only a complete historical snapshot with causal odds, jockey, track, and past-race evidence. Source-profile current bytes cannot be promoted to a historical snapshot.

The first exact blocker is therefore:

`V3_FIXTURE_CONSUMER_SUPPORT_REQUIRED`

Identity binding, entry/status replay semantics, market eligibility, market-odds evidence, and official settlement evidence remain real later dependencies, but none precedes the missing read-side fixture consumer in this local-only trace.

### Ordered dependency graph

| Order | Node | Current status / existing authority | Missing authority and implementation dependency | Network / authorization |
| --- | --- | --- | --- | --- |
| 0 | Integrated V3 source profile | COMPLETE; exact four artifacts, manifest/test authority, binary attributes, and Phase83 integration are committed | None for publication | No network; no authorization |
| 1 | Strict V3 fixture discovery and loading | MISSING; only the dedicated test uses literal paths | Repo-owned target/version catalog plus strict V3 loader that validates canonical manifest, roles, hashes, lengths, identities, and unsupported semantics and returns an immutable local bundle | No-network implementation possible first; no one-shot authorization |
| 2 | Replay identity binding | PARTIAL; NAR external identities and snapshot builder mapping checks exist | Explicit authoritative binding from `NAR / 21 / 2025-01-01 / 6` and external entry IDs to internal race/race-entry IDs; no name matching | Can be designed/tested no-network; live authorization not inherently required |
| 3 | Entry/status replay interpretation | MISSING; cancellation is explicitly unsupported and no status record kind exists | Approved status domain, mapping rules, withdrawal/non-run effect on entries and replay, and fail-closed tests | No-network contract/implementation possible first; no live authorization until new evidence is sought |
| 4 | Causal historical replay input | PARTIAL; snapshot builder, repository, resolver, and adapter exist | Complete causal snapshot evidence for all required entries, odds, jockeys, track, and past races after applying approved status semantics | Local persisted evidence can be used no-network; acquiring absent evidence would need a separately authorized live phase |
| 5 | Market eligibility and prediction odds | CLOSED AS UNSUPPORTED for this V3 profile; separate NAR market-odds capture/parser authorities exist | A future approved eligibility contract and causal captured market evidence; current fixture must not promote eligibility | No-network parser/adapter work may precede acquisition; any fresh capture needs authorization/network |
| 6 | Official result/payout settlement evidence | Resolver and capture repositories exist; replay expects an eligible official capture | Exact target settlement capture must exist and pass cutoff/identity checks; source-profile fixture is not payout evidence | Existing archive is no-network; absent official evidence requires separately authorized acquisition |
| 7 | Deterministic NAR replay | Orchestrator and simulation adapter exist | Nodes 1–6 must provide a complete executable resolution without fallback or future leakage | Replay itself can be no-network once evidence is complete |

### Proposed Phase85 scope

Phase85 should be a **no-network implementation phase** named `POST_V0_8_DAILY_REPLAY_85 — Strict Local V3 Source-Profile Fixture Consumer Authority`. It should close only node 1 and must not claim replay readiness.

Proposed exact files:

- CREATE `scripts/simulation/nar_race_entry_status_source_profile_fixture_consumer.py`
- CREATE `tests/test_nar_race_entry_status_source_profile_fixture_consumer.py`
- MODIFY `docs/CURRENT_PHASE.md`
- MODIFY `docs/LATEST_CODEX_REPORT.md`

The proposed module should expose an immutable V3 local bundle and one strict loader accepting an explicit repository root and exact target. It must select only the canonical V3 path, reject V1/V2/unknown/fallback candidates, read bytes once, validate strict UTF-8 canonical manifest bytes through existing V3 authority, recompute roles/hashes/lengths/Profile-A/Profile-B/Safety/FixtureSetV3/QualificationV3, preserve `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET` and all `UNSUPPORTED` fields, and return original bytes plus validated identities. It must perform no network, database writes, identity binding, snapshot creation, entry-status interpretation, market promotion, or replay execution.

Tests should cover exact target discovery, missing/extra/ambiguous paths, V1/V2/unknown rejection, manifest/raw mutation, role/path/target/identity mismatch, no fallback, no network, unchanged raw bytes, and explicit unsupported semantics. Any need to modify an existing authority module should stop as a design-support mismatch.

Provider HTTP / Phase44 / GET: `0 / 0 / 0`

Authorization issued: `NONE`

Next Action: `CHATGPT_REVIEW_PHASE84_REPLAY_CONSUMER_DEPENDENCY_AUDIT`

## Historical current-phase records

## POST_V0_8_DAILY_REPLAY_83

Title: No-Network Integration of Reviewed Phase82 V3 Publication Delta

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_INTEGRATION_REVIEW

Integration: V3_SOURCE_PROFILE_PUBLICATION_COMMITTED_AND_PUSHED

Design Review: PHASE83_INTEGRATION_DESIGN_REVIEW_PASS

Authorization: NONE_REQUIRED_NO_NETWORK_INTEGRATION

Phase82 Review: PHASE82_PUBLICATION_EVIDENCE_AND_DELTA_REVIEW_PASS

Design Contract: NO_NETWORK_V3_PUBLICATION_INTEGRATION_CONTRACT_COMPLETE

Authorized worktree / branch: `C:\Users\garim\Desktop\KeibaOS-post-v0.8` / `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `0c3e7577c5df44ffeee2ff9339f10272193bc7de` / `cdcc60051414ddf3089693be67f741e3eaf709b5`

Phase82 review: `PHASE82_PUBLICATION_EVIDENCE_AND_DELTA_REVIEW_PASS`

Phase82 is frozen `READY_FOR_NO_NETWORK_INTEGRATION`. Its external authorization is permanently `PHASE82_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`; Phase50 reconstructed `CONSUMED_CONFIRMED` with outcome `READY_FOR_REVIEW`. Phase82 acquisition must never be rerun.

### Delta freeze

The six-path path set is fixed. The following CREATE_ONLY artifacts are byte-frozen through Phase83 until the one approved integration commit:

- `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/deba_table.html` — 313317 bytes, `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727`
- `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/race_list.html` — 66307 bytes, `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1`
- `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/manifest.json` — 4254 bytes, `3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d`
- `tests/test_nar_race_entry_status_source_profile_v3_fixtures.py` — 10467 bytes, `a7339350be7e0724bd75408534a094c544bf6776eb57118e70ae6dd314e7b3ff`

`docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md` are phase-control mutable only. They may record Phase83 state and the closed integration contract, but must not alter Phase82 historical evidence. No seventh path is permitted.

The manifest is strict UTF-8 canonical V3 JSON and freezes FixtureSetV3 `nar-race-entry-status-source-profile-fixture-set-v3:11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225`, QualificationV3 `nar-race-entry-status-source-profile-qualification-v3:a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff`, target `NAR / 21 / 2025-01-01 / 6`, and `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET` with market eligibility `UNSUPPORTED`.

The dedicated V3 test is strict UTF-8, LF-only, BOM-absent, and compiles. It must not be regenerated. The V3 HTML attributes remain validate-only: `text` and `diff` are both unset.

### Integration result and frozen contract

Phase83 is no-network Git integration only. It performed local byte/manifest/test validation and the exact no-network regression order, and its approved final operation stages the exact six paths, creates one commit, and pushes normally. It performed no provider HTTP, Phase44, GET, acquisition, refetch, fixture/manifest/test regeneration, or production-support/.gitattributes modification.

Validated suites in order: dedicated V3 fixture `4 passed`; generator `17 passed`; preflight `17 passed`; publication plan `45 passed`; publication contract `49 passed`; Profile-B diagnostics `38 passed`; Profile-A `17 passed`; Phase66 structural recovery `152 passed`; Phase50 observability `367 passed`; full repository suite `4387 passed, 2841 subtests passed`. The full-suite test count is four higher than the Phase82 baseline because it includes the four dedicated V3 tests already run as step 1. `git diff --check` passes solely when its return code is zero; stderr remains diagnostic evidence only.

The only permitted staged paths are the four byte-frozen CREATE_ONLY artifacts and these two docs. Expected commit parent: `0c3e7577c5df44ffeee2ff9339f10272193bc7de`. Commit message: `feat: publish qualified NAR V3 source-profile fixtures`. Never use broad staging, amend, reset, rebase, force push, or stage `database/**` or `logs/**`. Push only normally to `origin/feature/post-v0.8-daily-replay`.

If the one local commit succeeds but push fails, preserve it unchanged and report `LOCAL_PHASE83_PUBLICATION_COMMIT_PUSH_PENDING_REVIEW`; do not reset, amend, reacquire, or reconstruct Phase82.

Historical non-inference remains mandatory: `market_eligibility = UNSUPPORTED`, `positive_market_eligibility = UNSUPPORTED`, and `WHOLE_MEETING_CANCELLATION = UNSUPPORTED`. Current fixture bytes do not establish historical availability or historical bytes.

Provider HTTP / Phase44 / GET: 0 / 0 / 0

Authorization: NONE_REQUIRED_NO_NETWORK_INTEGRATION

Next Action: CHATGPT_REVIEW_PHASE83_INTEGRATION

## Historical current-phase records

## POST_V0_8_DAILY_REPLAY_82

Title: Fresh Current V3 Publication with Corrected Final Git Success-Audit Semantics

Formal Status: APPROVED_FOR_CODEX

Authorization Tracking State: APPROVED_UNCONSUMED_TRACKED

Outcome: APPROVED_FRESH_V3_PUBLICATION_WITH_CORRECTED_GIT_SUCCESS_AUDIT

Design Contract: V3_PUBLICATION_WITH_CORRECTED_GIT_SUCCESS_AUDIT_CONTRACT_COMPLETE

Design Review: PHASE82_PUBLICATION_DESIGN_REVIEW_PASS

### Authority and PREPARE scope

Authorized worktree: `C:\Users\garim\Desktop\KeibaOS-post-v0.8`

Branch: `feature/post-v0.8-daily-replay`

Current tracking HEAD/tree: `d54676e5c4e568bbc883d1a119dd632c653c1526` / `ae9baf3edfedc5c78eb35b03132903ca9d17530e`

Executable support HEAD/tree: `321868ac827677700da2c2ec41fded860eb464cc` / `0c422b45118131b8e3bb8ce5dd7189f2368e683e`

Target: `NAR / 21 / 2025-01-01 / 6`

Future purpose: `FRESH_CURRENT_V3_SOURCE_PROFILE_PUBLICATION_WITH_CORRECTED_GIT_SUCCESS_AUDIT`

Semantics: `CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET`

This approval tracking activity changes only the two documentation files. The authorization is issued and tracked only upon successful creation and normal push of this exact documentation commit with local HEAD equal to remote-tracking HEAD. No provider HTTP, Phase44, GET, acquisition, publication, or live execution occurs in this approval activity.

### Frozen Phase80 and Phase81

Phase80 is terminal: `TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE`. Its review is `PHASE80_CONSUMED_BLOCKED_RESULT_REVIEW_PASS_WITH_FINAL_AUDIT_RUNNER_DEFECT`; its external authorization remains permanently `PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`; Phase50 reconstructed `CONSUMED_CONFIRMED` with outcome `RECOVERY_PREFLIGHT_BLOCKED`. Phase80 cannot be retried.

The exact Phase80 root cause is proven: `GIT_DIFF_CHECK_ZERO_EXIT_WITH_EOL_WARNING_STDERR_MISCLASSIFIED_AS_FAILURE`. `git diff --check` returned code zero but emitted CRLF/LF conversion warnings on stderr. The frozen runner incorrectly required both zero exit status and empty stderr, converting a successful final audit into a rollback. The bounded safe-final error-message digest is `ca4d4fc7d257fdf647d7a7f7653c66e459cec40b46327221e5ec9ac02d5b331a`.

This defect must not be attributed to fixture bytes, V3 manifest, renderer, dedicated test, publication contract, Profile-A, Profile-B, Safety v3, Phase50, or regressions. Before that final audit, Phase80 passed the Phase79 executable pytest preflight, completed one Phase44, Deba GET, and RaceList GET with zero retries, qualified Profile-B v2 and Profile-A v3, assessed Safety v3 SAFE, and reached `REGRESSIONS_PASS`.

Frozen Phase80 evidence includes Deba SHA-256/length `6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727` / `313317`; RaceList `1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1` / `66307`; Phase63 candidates `2`; Phase66 total/direct/changeInfo `2 / 1 / 1`; and structural consistency PASS. FixtureSetV3 was `nar-race-entry-status-source-profile-fixture-set-v3:2660a568e455c5d2f3f430b0b57297e0c725e73ba5c4d78b9fa211010831f2c7`; QualificationV3 was `nar-race-entry-status-source-profile-qualification-v3:0932ef780af0cebc76d4c411531fe12508544fe1ca103dc18286201fde63093c`; manifest SHA/length was `9e089a0f75e8c57cdd37a994e7d210ca2c941d1209f2bf486091fb2ad754add3` / `4254`; generated-test SHA/length was `82047976daba97c6262b44fa52d9232bdfc29fdb285fcb0f605344a9d85382e9` / `10467`.

Frozen PASS results: dedicated V3 fixture `4`; generator `17`; preflight `17`; publication plan `45`; publication contract `49`; Profile-B diagnostics `38`; Profile-A `17`; Phase66 `152`; Phase50 `367`; full suite `4383` plus `2841` subtests. `PUBLICATION_BEGIN`, `REGRESSIONS_PASS`, `ROLLBACK_BEGIN`, and `ROLLBACK_COMPLETE` were reached. The repository ended clean with no surviving delta, commit, or push.

Phase81 is `NOT_ENTERED_NO_PUBLICATION_DELTA`; it remains reserved and must not be repurposed. A reviewed Phase82 success requires a separately numbered no-network integration phase, `POST_V0_8_DAILY_REPLAY_83` or later. No Phase79 production/test support repair is required.

### Corrected final Git success audit

The Phase82 runner must classify `git -C "C:\Users\garim\Desktop\KeibaOS-post-v0.8" diff --check` solely from its exit status:

- `returncode == 0` means `DIFF_CHECK_PASS`.
- `returncode != 0` means `DIFF_CHECK_FAIL`.
- Nonempty stderr is bounded diagnostic evidence only and cannot override zero exit status.

For every audit, retain command identity, return code, stdout/stderr SHA-256, original lengths, and sanitized bounded streams. This preserves EOL conversion warnings without treating them as a pass/fail authority.

The frozen external runner must pass `PHASE82_GIT_DIFF_CHECK_EXIT_STATUS_CLASSIFIER_PASS` before any boundary using deterministic classifier cases: (A) zero code with empty streams => PASS; (B) zero code and representative LF/CRLF warning stderr => PASS; (C) nonzero code with empty or nonempty stderr => FAIL; (D) nonzero code and whitespace-error stdout => FAIL. These tests perform no provider access or Git mutation.

The actual read-only clean-baseline `git diff --check` is mandatory before a boundary. Its gate is `PHASE82_BASELINE_GIT_DIFF_CHECK_PASS`; its sole success criterion is return code zero. Stderr remains evidence only.

After all publication regressions, final audit must require unchanged local and remote-tracking HEADs, empty staging, exactly the two modified docs, exactly the four V3 CREATE_ONLY untracked files, and existence of all four CREATE_ONLY files. It must record `git_diff_check_return_code`, `git_diff_check_passed`, `git_diff_check_stdout`, `git_diff_check_stderr`, `success_delta_exact`, `staged_empty`, `head_unchanged`, and `remote_tracking_unchanged`.

If a final audit genuinely fails after publication, bounded evidence must be retained before rollback: command identity, return code, stream digests/lengths/sanitized streams, parsed modified/untracked/staged path sets, expected and actual sets, and classification. Only then may `ROLLBACK_BEGIN` and `ROLLBACK_COMPLETE` run.

### Planned Phase82 live contract

Authorization: `PHASE82_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED`

Phase82 authorization is issued and tracked as `APPROVED_UNCONSUMED_TRACKED`; boundary not crossed and authorization remains UNCONSUMED. Its permanent post-boundary token is `PHASE82_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED`. It binds only to this Phase82, the executable support above, the stated target, purpose, and historical-target/current-acquisition semantics.

Boundary: `NOT WRITTEN`

Authorization consumed: `NO`

The sole real authorization boundary remains durable `PHASE44_CALL_ABOUT_TO_ENTER`: append, flush, fsync, then external consumption. No retry follows the boundary. Caps remain one Phase44, one Deba GET, one RaceList GET, two total, Deba then RaceList, with no fallback, discovery, or alternate target.

Before the boundary, Phase82 preserves the actual Phase79 isolated pytest preflight (`V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS`) and every Phase80 gate: import and support identity isolation; exact LF runner and hash/length parity; CREATE_ONLY absence; gitattributes; V3 plan/contract; Phase50 V3 dedicated path and blocked-payload gates; Profile-B; Phase63/66; Safety; Profile-A; Phase71 target contract; exact 11-key capture metadata; closed-bundle propagation; same-byte authority; no-network synthetic gates; and rollback dry-run. The Phase79 preflight must produce actual pytest PASS with Provider HTTP / actual Phase44 / GET equal to `0 / 0 / 0`.

Fresh Phase82 bytes flow unchanged through capture, Profile-B, Phase63/66, Safety, Profile-A, FixtureSetV3, QualificationV3, ManifestV3, the Phase79 renderer, and fixtures. No Phase76/80 substitution, re-fetch, decode/re-encode, or HTML serialization is permitted. Reproduced bytes remain current acquisition and do not establish historical availability or historical bytes.

The exact six future paths are the V3 Deba HTML, RaceList HTML, manifest, and dedicated fixture test as CREATE_ONLY, plus `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md` as MODIFY_EXISTING. The dedicated V3 fixture test runs exactly once as regression step 1, followed by generator, preflight, publication plan, publication contract, Profile-B diagnostics, Profile-A, Phase66, Phase50, and full-suite regressions. All pass before `REGRESSIONS_PASS`.

Success stops for review with precisely this unstaged six-path delta, empty index, no commit, and no push. It reports `READY_FOR_REVIEW`, Phase50 `READY_FOR_REVIEW`, external authorization consumed fail-closed, Phase50 `CONSUMED_CONFIRMED`, and `V3_SOURCE_PROFILE_PUBLICATION_DELTA_READY_FOR_CHATGPT_REVIEW`.

Historical non-inference remains mandatory: `market_eligibility = UNSUPPORTED`, `positive_market_eligibility = UNSUPPORTED`, and `WHOLE_MEETING_CANCELLATION = UNSUPPORTED`.

### Readiness matrix

| Item | Ready |
| --- | --- |
| A. Phase80 terminal consumed state frozen | YES |
| B. Phase80 exact root cause proven | YES |
| C. Phase80 all ten regressions frozen PASS | YES |
| D. Phase80 rollback frozen complete | YES |
| E. Phase81 not entered and reserved | YES |
| F. No repository support defect required | YES |
| G. Corrected exit-status semantics defined | YES |
| H. Stderr diagnostic-only rule defined | YES |
| I. Pre-live classifier self-tests defined | YES |
| J. Baseline diff-check probe defined | YES |
| K. Final six-path audit defined | YES |
| L. Final-audit evidence before rollback defined | YES |
| M. Phase79 actual-pytest preflight preserved | YES |
| N. All Phase80 safety gates preserved | YES |
| O. Phase82 authorization issued and tracked as APPROVED_UNCONSUMED_TRACKED; boundary not crossed and authorization remains UNCONSUMED | YES |
| P. Sole durable boundary preserved | YES |
| Q. One Phase44/two GET caps preserved | YES |
| R. Same-byte authority preserved | YES |
| S. Exact regression order preserved | YES |
| T. Exact unstaged success delta preserved | YES |
| U. Historical non-inference preserved | YES |

### Approval tracking activity

Provider HTTP / Phase44 / GET: `0 / 0 / 0`

Authorization: `PHASE82_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED`

Publication: `NO`

Synthetic/live execution: `NOT RUN`

Publication: `NO`

Staging and commit: documentation-only tracking activity; no publication path is staged

Next action: `INDEPENDENT_REMOTE_VERIFICATION_BEFORE_PHASE82_EXECUTE`

## Historical current-phase records

## POST_V0_8_DAILY_REPLAY_80

Title: Fresh Current V3 Source-Profile Publication After Executable Dedicated-Test Preflight

Formal Status: APPROVED_FOR_CODEX

Authorization Tracking State: APPROVED_UNCONSUMED_TRACKED

Outcome: APPROVED_FRESH_V3_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT

Design Contract: V3_FRESH_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT_CONTRACT_COMPLETE

Design Review: PHASE80_PUBLICATION_DESIGN_REVIEW_PASS_WITH_REGRESSION_ORDER_CORRECTION

### Authorized baseline

Branch: feature/post-v0.8-daily-replay

Executable Support HEAD: 321868ac827677700da2c2ec41fded860eb464cc

Executable Support Tree: 0c422b45118131b8e3bb8ce5dd7189f2368e683e

Target: NAR / 21 / 2025-01-01 / 6

Future Purpose: FRESH_CURRENT_V3_SOURCE_PROFILE_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT

Semantics: CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET

### Frozen prior phases

Phase76: TERMINAL_CONSUMED_BLOCKED_ROLLBACK_COMPLETE

Phase76 Review: PHASE76_CONSUMED_BLOCKED_RESULT_REVIEW_PASS

Phase76 Authorization: PHASE76_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED

Phase76 blocker: REGRESSION_FAILURE_AT_DEDICATED_V3_FIXTURE_TEST

Phase76 underlying cause: UNKNOWN_AFTER_BOUNDED_EVIDENCE_GAP

Phase78: NOT_ENTERED_NO_PUBLICATION_DELTA. It remains unused and must not be repurposed.

Phase79: FORMALLY_COMPLETE

Phase79 Verification: PHASE79_IMPLEMENTATION_REMOTE_VERIFICATION_PASS

Phase79 Support: V3_DEDICATED_FIXTURE_TEST_EXECUTION_AND_FAILURE_EVIDENCE_AUTHORITY_IMPLEMENTED

### Phase80 authorization and approval tracking

The approval tracking commit succeeded, was normally pushed, and local HEAD equals remote-tracking HEAD. It performed no live execution.

The issued one-shot token is PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_UNCONSUMED and its tracking state is APPROVED_UNCONSUMED_TRACKED. Its permanent post-boundary state is PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED. It binds only to POST_V0_8_DAILY_REPLAY_80, support HEAD 321868ac827677700da2c2ec41fded860eb464cc, support tree 0c422b45118131b8e3bb8ce5dd7189f2368e683e, target NAR / 21 / 2025-01-01 / 6, purpose FRESH_CURRENT_V3_SOURCE_PROFILE_PUBLICATION_AFTER_EXECUTABLE_TEST_PREFLIGHT, and CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET semantics. It is one-shot, nontransferable, support-specific, target-specific, purpose-specific, and phase-specific; it cannot be reused after its durable boundary.

Boundary: NOT WRITTEN

Authorization consumed: NO

Provider HTTP / Phase44 / GET: 0 / 0 / 0

Synthetic/live execution: NOT RUN

Publication: NO

### Mandatory pre-live gates

No authorization boundary may be crossed unless every gate passes:

- IMPORT_ISOLATION_PASS, including PEP 420 `scripts` namespace validation and all Phase80 authority-module origins under the approved worktree and support identity.
- V3_DEDICATED_FIXTURE_TEST_END_TO_END_PREFLIGHT_PASS by calling the exact committed `run_nar_race_entry_status_source_profile_v3_fixture_test_preflight` support. It must use `python -I -B`, an external mirror outside the repository, `--import-mode=importlib`, controlled plugin autoload, authorized production origins only, and an actual generated pytest PASS.
- The preflight evidence must retain generated-source and manifest SHA-256/length, pytest command identity and return code, Phase50-sanitized stdout/stderr evidence, and import-isolation result. It must report `test_passed = true` with Provider HTTP / actual Phase44 / GET equal to 0 / 0 / 0.
- PUBLICATION_PLAN_V3_DRY_RUN_PASS, V3 publication-contract validation, Phase50 V3 dedicated-test-path integration, Profile-B v2 and sibling `table.changeInfo` topology gates, Profile-A v3, Safety v3, Phase50 versioned/blocked-payload gates, Phase71 target-contract integration, exact 11-key metadata, closed-bundle identity propagation, runner parity, no-network and live-logic parity gates.
- CREATE_ONLY_TARGETS_ABSENT_PASS, repository clean, staged empty, untracked empty, exact LF preflight, and `GITATTRIBUTES_V3_VALIDATE_ONLY_PASS`.

Any failed pre-live gate is PRE_AUTHORIZATION_STOP: no Phase80 authorization consumption, provider HTTP, Phase44, GET, publication, or automatic retry.

### Closed publication authority

The exact future six-path delta is:

- CREATE_ONLY: `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/deba_table.html`
- CREATE_ONLY: `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/race_list.html`
- CREATE_ONLY: `tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/manifest.json`
- CREATE_ONLY: `tests/test_nar_race_entry_status_source_profile_v3_fixtures.py`
- MODIFY_EXISTING: `docs/CURRENT_PHASE.md`
- MODIFY_EXISTING: `docs/LATEST_CODEX_REPORT.md`

All four CREATE_ONLY paths must be absent before the live boundary. The tracked V3 binary rule must occur exactly once: `tests/fixtures/nar_race_entry_status/source_profiles/v3/**/*.html -text -diff`. The two future HTML paths must have `text` and `diff` unset; `.gitattributes` is VALIDATE_ONLY and must not be changed.

The committed Phase79 renderer `render_nar_race_entry_status_source_profile_v3_fixture_test` is the sole dedicated-test generation authority. The future live runner must not contain an inline template or a duplicate renderer.

### Future transaction

The sole durable authorization boundary is `PHASE44_CALL_ABOUT_TO_ENTER`, appended, flushed, and fsynced. Only after that succeeds does the external token become PHASE80_V3_SOURCE_PROFILE_PUBLICATION_AUTHORIZATION_CONSUMED_FAIL_CLOSED. Phase50 separately reconstructs `UNCONSUMED`, `CONSUMED_FAIL_CLOSED`, or, after `PHASE44_FUNCTION_ENTERED`, `CONSUMED_CONFIRMED`.

The request caps are one Phase44 invocation, one Deba transport/GET, one RaceList transport/GET, and two GETs total, in DebaTable then RaceList order. Retries, fallback, alternate targets, and discovery are forbidden.

The exact same new response-body bytes must be used for capture metadata, Profile-B v2, Phase63/66, Safety v3, Profile-A v3, FixtureSetV3, QualificationV3, SourceProfileManifestV3, renderer input, and repository raw fixtures. Refetching, Phase74/76 substitution, decoding/re-encoding, and HTML serialization are forbidden.

Before `PUBLICATION_BEGIN`, require the exact 11-key metadata contract, closed-bundle identity propagation, identity verification, Profile-B v2 QUALIFIED with all six predicates and target schedule count one, Phase66 direct schedule count one and structural consistency, Safety v3 SAFE with five SAFE categories and zero findings, Profile-A v3 QUALIFIED with three predicates, and validated FixtureSetV3, QualificationV3, SourceProfileManifestV3, and SourceProfilePublicationPlanV3.

Only then append durable `PUBLICATION_BEGIN` with `planned_path_count: 6`. Raw fixtures must be written as original bytes and read back for exact equality, SHA-256, length, and attributes. The manifest must be exact canonical bytes, read back, and validated. The dedicated test must be generated only by the Phase79 renderer, be UTF-8/LF/no-BOM, compile, be at most 65536 bytes, and be read back exactly.

The dedicated V3 fixture test executes exactly once, as regression step #1. On its failure, first build and durably retain bounded evidence using `build_v3_fixture_test_failure_evidence` and `retain_v3_fixture_test_failure_evidence_durably`; receipt must confirm flush, fsync, and validated readback. Evidence includes generated source, validated bounded manifest or safe projection, identities, fixture SHA/length, command/return code, and Phase50-sanitized output, never raw HTML. Only then may `ROLLBACK_BEGIN` occur. If a later regression fails, retain bounded command/result evidence sufficient to identify that regression before the same rollback sequence.

The exact regression order is: (1) `tests/test_nar_race_entry_status_source_profile_v3_fixtures.py`; (2) `tests/test_nar_race_entry_status_source_profile_fixture_test_generator.py`; (3) `tests/test_nar_race_entry_status_source_profile_fixture_test_preflight.py`; (4) `tests/test_nar_race_entry_status_source_profile_publication_plan.py`; (5) `tests/test_nar_race_entry_status_source_profile_publication_contract.py`; (6) `tests/test_nar_race_entry_status_source_profile_diagnostics.py`; (7) `tests/test_nar_race_entry_status_source_profile_profile_a.py`; (8) `tests/test_nar_race_entry_status_source_profile_structural_recovery_diagnostics.py`; (9) `tests/test_nar_race_entry_status_reacquisition_observability.py`; and (10) the full repository suite. All must pass before `REGRESSIONS_PASS`.

### Success, rollback, and integration split

A successful Phase80 stops for review with only the two documentation files modified and the four CREATE_ONLY artifacts untracked; the index is empty and there is no commit or push. `git diff --check` must pass. The result is `V3_SOURCE_PROFILE_PUBLICATION_DELTA_READY_FOR_CHATGPT_REVIEW` with external authorization consumed fail-closed and Phase50 authorization `CONSUMED_CONFIRMED`.

Any failure after `PUBLICATION_BEGIN` retains required evidence first, appends `ROLLBACK_BEGIN`, deletes only the four Phase80 CREATE_ONLY artifacts, restores the two documents byte-exact to the Phase80 pre-live baseline, verifies a clean repository, and appends `ROLLBACK_COMPLETE`. No reset, restore, checkout, stash, clean, or retry is allowed.

Git integration is explicitly separate. Phase78 remains unused. Only after independent review of a successful Phase80 delta may a new no-network Phase81-or-later integration phase stage exactly the six paths, commit once, and push normally. It must not acquire, refetch, invoke Phase44, or use GET.

### Historical interpretation

Market eligibility, positive market eligibility, and WHOLE_MEETING_CANCELLATION remain UNSUPPORTED. Current-byte reproduction or fixture existence never proves historical bytes, historical availability, or historical market eligibility.

### Readiness matrix

A–U: YES.

A. Phase79 formally complete. B. Phase76 permanently consumed and frozen. C. Phase78 frozen not entered. D. Phase79 support HEAD/tree fixed. E. Phase80 authorization issued and tracked as APPROVED_UNCONSUMED_TRACKED; boundary not crossed and authorization remains UNCONSUMED. F. Phase79 executable pytest preflight mandatory. G. Six paths fixed. H. CREATE_ONLY absence gate defined. I. Exact gitattributes gate defined. J. Sole durable boundary defined. K. One-Phase44/two-GET caps defined. L. Same-byte authority defined. M. Qualification gates defined. N. Repo-owned renderer is sole generator. O. Dedicated pytest precedes broader regressions. P. Failure evidence is durable before rollback. Q. Manifest/source/hash evidence is preserved. R. Exact success unstaged delta is defined. S. Rollback restores the clean baseline. T. New no-network Phase81-or-later integration is defined. U. Historical non-inference is preserved.

### APPROVE activity scope and record

This approval changes only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`. It performs no production/test change, provider HTTP, Phase44, GET, acquisition, publication, synthetic/live preflight execution, fixture-delta creation, or staging of publication artifacts.

Provider HTTP / Phase44 / GET: 0 / 0 / 0

Authorization consumed: NO

Publication: NO

Next action after successful approval tracking: INDEPENDENT_REMOTE_VERIFICATION_BEFORE_PHASE80_EXECUTE
