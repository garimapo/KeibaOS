# Current Phase

## POST_V0_8_DAILY_REPLAY_113

Title: NAR Production PRE_C Claim-Bound Prestaged Authority Binding

Status: `APPROVED_FOR_COMMIT`

State: `FORMAL_CLOSURE_APPROVED`

Outcome: `READY_FOR_FORMAL_CLOSURE_COMMIT`

Implementation: `REMOTELY_VERIFIED`

Base Commit: `9c1bd2b643826bd62551a326c61884a161672f8e`

Base Tree: `e67ec5d76cbc59e0f6ebb026047efc82b49206bd`

Branch: `feature/post-v0.8-daily-replay`

Architectural disposition:
`CHATGPT_REVIEW_PHASE113_DESIGN = PASS_WITH_REQUIRED_CONTRACT_CORRECTIONS`.
The six required contract corrections below have been applied.
`PHASE113_ARCHITECTURAL_REVIEW_PASS`.
`PHASE113_IMPLEMENTATION_DESIGN_APPROVED`.
`PHASE113_ALLOWED_FILES = 10_PATH_SCOPE`.
`PHASE113_DESIGN_APPROVAL_VERIFICATION_PASS` and `PHASE113_EXECUTION_APPROVED`
were supplied by ChatGPT for this execution. The approved binding-only contract
has been implemented and verified. ChatGPT independently passed implementation
review, post-commit verification and GitHub remote implementation verification.
The implementation is remotely accepted and this docs-only local formal closure
commit is approved. Closure-commit verification, its push and remote verification,
and Phase113 formal completion remain pending.

### Remote implementation accepted — current formal closure disposition

`CHATGPT_REVIEW_PHASE113_IMPLEMENTATION = PASS`.
`PHASE113_IMPLEMENTATION_REVIEW_PASS`.
`PHASE113_COMMIT_APPROVED`.
`PHASE113_POST_COMMIT_VERIFICATION_PASS`.
`PHASE113_REMOTE_IMPLEMENTATION_VERIFICATION_PASS`.
`PHASE113_IMPLEMENTATION_REMOTE_ACCEPTED`.
`PHASE113_FORMAL_CLOSURE_APPROVED`.

Implementation Commit: `3fb0d719d2688cd9cb42d7b854b4bee40dc2cc75`.
Implementation Tree: `245692d709482926e58977af0d13975f812bb870`.
Implementation Parent: `9c1bd2b643826bd62551a326c61884a161672f8e`.
Implementation Subject: `feat: add NAR PRE_C claim-bound prestaging authority`.

The implementation was pushed normally without force. ChatGPT independently
verified GitHub branch HEAD, tree and parent at those exact identities, exactly
ten approved paths, ahead 1 / behind 0 / total commits 1 from the implementation
parent, and 2288 additions / 0 deletions. This independent acceptance was supplied
by ChatGPT; local Git observations do not substitute for that review.
This activity fetched origin at the accepted implementation commit and verified
local HEAD/tree/branch, 0 / 0 relation, CLEAN working tree and EMPTY index.

Accepted tests: focused **100 passed**; focused + related **231 passed / 2 skipped**;
full **4998 passed / 4 skipped / 2846 subtests passed**; static production audit
**PASS**. No tests were rerun for this docs-only closure bookkeeping, and no
production/test bytes changed.

Phase113 grants durable claim <-> Phase112 prestaging binding only. It does NOT
grant current-process execution capability, campaign-lock ownership, complete
production root scope, target-set/cutoff-plan/dataset authority, one-shot root
consumption, root.started_at, provider-work permission, prediction/betting/live
authority or Operational Delta authority. Those Phase114 concerns remain deferred.

Phase113 is NOT formally complete. Formal closure remote verification, closure
remote acceptance, formal completion approval and final documentation remote
verification are NOT YET GRANTED. Create only one local docs-only commit,
`docs: record Phase113 formal closure`, with the accepted implementation as parent;
then stop for independent ChatGPT closure-commit verification before any push.
Provider HTTP = 0; production DB access = 0; KeibaAI changes = 0;
production/test changes = 0; push = 0; force push = 0 during this activity.

### Historical independent implementation review and local commit approval

`CHATGPT_REVIEW_PHASE113_IMPLEMENTATION = PASS`.
`PHASE113_IMPLEMENTATION_REVIEW_PASS`.
`PHASE113_COMMIT_APPROVED`.
The accepted review evidence is the external
`phase113_implementation_review_bundle.txt`, SHA-256
`6111ba23860138268560355be9d678b1e7a1435992aaa37945d6af342dbcd914`,
257774 bytes / 3304 lines. It is not a repository or commit path.

Accepted verification: focused **100 passed**; focused + all fourteen approved
related modules **231 passed / 2 skipped**; full **4998 passed / 4 skipped /
2846 subtests passed**; static production audit **PASS**. The review-evidence
rerun retained `100 passed in 27.05s`, `231 passed, 2 skipped in 1063.03s`, and
`4998 passed, 4 skipped, 2846 subtests passed in 1321.56s`. The full-suite
environment remained
`KEIBAOS_PHASE106_SEALED_COMMIT_SMOKE=9c1bd2b643826bd62551a326c61884a161672f8e`.
No tests were rerun solely for this review-bookkeeping documentation edit.

Before bookkeeping, exact local HEAD/tree/branch, fetched origin at the reviewed
base, exact ten dirty/untracked paths and EMPTY index were verified. All eight
production/test raw SHA-256 values match the independently reviewed manifest.
Only these two documents change after review; production and test bytes remain
frozen. Stage only the exact ten approved paths, check the staged set and diff,
then create one normal local commit with subject
`feat: add NAR PRE_C claim-bound prestaging authority`. No amend or push.
Committed production/test blobs must match all eight reviewed hashes exactly.
Local structural checks and an external post-commit verification bundle are
evidence only; independent ChatGPT post-commit verification is still required.

Phase113 is NOT formally complete. No push, remote implementation acceptance,
formal closure, root execution permission, current-process capability, status/
eligibility, prediction/betting/live authority or Phase114 integration is granted.
Provider HTTP = 0; production DB access = 0; KeibaAI changes = 0; push = 0;
force push = 0. Next: approved local commit and independent post-commit review.

### Historical Phase113 execution evidence — before independent implementation review

`PHASE113_IMPLEMENTATION_READY_FOR_CHATGPT_REVIEW`.
Preflight matched exact HEAD/tree/branch and fetched origin at the base above;
initial dirty paths were exactly the two approved documentation files and index
EMPTY. Existing approval/audit work was preserved; no reset or destructive Git
operation occurred. All implementation/test changes are additive within the
eight new approved paths; no predecessor production/test API or registry changed.

The frozen 13-field `NARPreCProductionClaimBindingV1` uses canonical JSON and
`nar-pre-c-production-claim-binding-v1:<64 lowercase hex>`. Issuance exact-loads
claim/binding/session/configuration/readiness, requires readiness <= session
start (equality accepted), then exact-loads Phase112's complete pair through its
existing Phase109 repository. No clock, caller mapping, horse IDs, copied
lineage/times, root scope, process capability or execution permission is added.

The injected version-1 companion has registry/binding tables, five semantic
unique keys (identity, manifest, availability, external target/cutoff, internal
target/cutoff) and four immutable registry/binding UPDATE/DELETE triggers.
Claim/session/runtime-binding/readiness columns are NONUNIQUE. One genuine
claim was proved to bind two independently valid Phase112 targets. A manifest
cannot be transferred to another claim. Absent/active/corrupt topology, literal
`name NOT GLOB 'sqlite_*'` filtering, visible sqliteXunreviewed and FK-OFF guards
are tested. No main migration is registered.

Publication uses one companion BEGIN IMMEDIATE, checks every collision key,
inserts once or exact-adopts idempotently, commits, then exact-reloads the binding
and all upstream authority before success. Genuine post-write COMMIT denial
observed SQLite total_changes +1 and one uncommitted row, followed by zero rows,
no open transaction and byte-for-byte equivalent upstream dumps. Postcommit
local/upstream reload failures return no success and retain the immutable row.
Two independent file-backed connections proved one exact immutable winner plus
exact loser reload, or one winner plus permanent contradictory-claim conflict.

Successful verification (exact commands/module set in LATEST_CODEX_REPORT):

- Focused: `100 passed in 27.71s`; no skipped tests/subtests reported.
- Focused + all 14 approved related modules: `231 passed, 2 skipped in 1066.14s`;
  no subtests reported.
- Full: `4998 passed, 4 skipped, 2846 subtests passed in 1320.27s`.
- Related/full environment: `KEIBAOS_PHASE106_SEALED_COMMIT_SMOKE=9c1bd2b643826bd62551a326c61884a161672f8e`.
- Static production audit: PASS. SQL receivers write only the Phase113 companion;
  upstream stores use existing exact-load APIs. Prohibited transport/parser/
  Phase111/fixed-path/clock/internal-ID/replace calls and patterns: zero.
- Final `git diff --check`: PASS; exactly 10 approved dirty paths; index EMPTY.

The first test-construction run was 86 passed / 8 failed. New tests were corrected
to expect existing upstream-specific domain exceptions and to inject upstream
reread failure only after the binding was actually committed. No predecessor or
production behavior was changed to satisfy those tests. The new fixture reuses
one exact immutable existing Git-object bundle only to avoid repeated fixture IO;
authoritative Phase113/upstream reloads are never cached.

Provider HTTP = 0; production DB access = 0; KeibaAI changes = 0; stage = 0;
commit = 0; push = 0. Runtime/main/Phase112 mutation, new race/horse IDs, denial
clearing, current-clock samples, status/eligibility promotion, root/start/live
authority, INSERT OR REPLACE and silent repair = 0. No cross-store atomicity or
rollback is claimed. This precommit suite is not final sealed-source verification
for older phases. Phase114 execution/root-scope/consumption remains deferred.
Historical next step at EXECUTE completion: independent ChatGPT implementation
review; no commit or push authorization had then been supplied. The current
independent PASS and local-only commit approval above supersede that disposition.

### Historical predecessor reconciliation and approval-activity boundary

ChatGPT independently accepted the Phase112 final documentation on the remote:
`POST_V0_8_DAILY_REPLAY_112 = FORMALLY_COMPLETE` and
`PHASE112_FINAL_DOCUMENTATION_REMOTE_VERIFICATION_PASS`.
Final documentation commit/tree are the Phase113 base above; its parent is
`7a7f6a20679347fa1ff332ba36f4bc9862907a77`. This acceptance is supplied by
ChatGPT, not a new Codex remote-verification claim. Earlier Phase112 reports
below remain historical, including their then-pending push/verification wording.

Historical PREPARE: initial HEAD/tree/branch matched, working tree was CLEAN
and index EMPTY. AGENTS.md and the detailed Ver0.8 design's identity/time/
immutable repository boundaries were consulted; the architecture was drafted
as DRAFT_FOR_REVIEW / NOT_AUTHORIZED. The preparation report is preserved.
This activity is APPROVE_PHASE only: preflight matched the same base/branch,
only the two existing dirty phase-control documents and empty index.
Only those two documents are writable now. No implementation, tests, migrations,
database inspection, provider work, stage, commit or push during this activity.
Wait for ChatGPT verification before a later EXECUTE_APPROVED_PHASE.

### Audit finding 1 — campaign claim cardinality is B, not one race

The existing claim is campaign/session-scoped and supports multiple sequential
race targets; it is not a one-race claim. Evidence is structural and executable
contract evidence, not inference from its name:

- `nar_operational_timing_runtime_execution.py`,
  `NAROperationalTimingCampaignExecutionClaim`, binds configuration, session,
  activation declaration/verification, runtime binding, bundle and lock scope;
  it has no race ID or prediction cutoff.
- `nar_operational_timing_runtime_execution_archive_migration.py:40` gives
  claims UNIQUE session and UNIQUE runtime binding, not UNIQUE race. Readiness
  is one per claim. `CONTROLLED_ONE_SHOT_CAMPAIGN_RUNNER_V1` means one issued
  campaign claim per session, not one operation/race per campaign.
- `nar_operational_timing_campaign_runner.py:149`, `next_attempt_sequence()`,
  increments for each operation under the same current capability.
  `nar_operational_timing_passive_wrapper.py:74`, `measure_nar_operation()`,
  accepts a separate correlation on each call. `NARTimingCorrelation` in
  `nar_operational_timing_observability.py` supports PROVIDER, TARGET_SET and
  RACE scopes. `nar_operational_timing_attempt_archive_migration.py:29` uses
  UNIQUE(claim_identity, attempt_sequence), not UNIQUE claim.
- Configuration V2's `max_concurrent_target_workflows = 1` is simultaneous
  serial-workflow capacity, not a limit of one total target for the session.
- Even diagnostic Phase108 has UNIQUE(claim_identity, scope_identity) for
  manifests and per-manifest roots, not a globally UNIQUE root claim. Its
  `publish()` replay check is claim + scope. This is supporting cardinality
  evidence only, not authority to reuse the diagnostic root in production.
- `test_claim_and_readiness_precede_process_capability_and_old_claim_cannot_resume`
  proves one claim/session and inability to resurrect saved claims;
  passive-wrapper tests and diagnostic PRESTAGED/GENERATED tests exercise
  multiple operations under one claim. The inspected tests do not themselves
  prove an end-to-end live multi-race scheduler; Phase113 does not add one.

Approved correction 1: `ONE_CAMPAIGN_EXECUTION_CLAIM_MAY_COVER_MULTIPLE_TARGETS`.
Approved binding cardinality: one manifest -> at most one claim binding;
one availability receipt -> the same binding ancestry; same pair + same exact
claim -> original binding idempotently; same pair + different claim -> conflict.
One claim may bind multiple distinct accepted target/cutoff manifests.
`claim_identity`, `session_identity`, `runtime_binding_identity` and
`campaign_readiness_receipt_identity` MUST NOT be UNIQUE in Phase113.
All four may repeat across distinct target bindings under the same claim,
including the same readiness receipt. No claim-global or readiness-global
uniqueness, or equivalent constraint collapsing a campaign to one target.
Same external or internal target/cutoff
with contradictory content must fail closed, even across different claims.
No target or execution permission follows from a claim's correlation alone.

### Audit finding 2 — exact upstream authority and readiness qualification

Approved issuer inputs: injected exact runtime archive, exact Phase112 archive,
existing exact Phase109 repository, session identity, expected claim identity,
Phase112 manifest identity and expected availability-receipt identity. Optional
external-target/cutoff expectations are equality constraints only. No caller
value/mapping/internal race ID, clock, available_at, capability or Phase111
archive may be an authority input. These are already trusted/reviewed upstream
archive boundaries; Phase113 does not create or independently remote-approve a
runtime claim/source bundle.

Use the unchanged existing runtime APIs:

1. `SQLiteNAROperationalTimingRuntimeExecutionArchive.load_claim_for_session()`;
   require present and exact requested claim/session equality. There is no
   public claim-by-ID loader; session lookup plus exact claim check suffices.
2. `load_binding(binding_identity=claim.binding_identity)`; require exact
   claim/binding/session/configuration/declaration/verification/bundle/lock
   agreement. Explicitly exact-load the measurement session through the
   runtime archive's V2 `load_session()` and require session/configuration
   agreement. The binding's existing ancestry validator reloads the V2 session,
   activation declaration/verification, bundle, dependency and transport
   profiles and requires qualifying activation and declared source agreement.
3. `load_readiness_for_claim(claim_identity=claim.claim_identity)`; require
   exact canonical receipt, claim/binding/session/configuration agreement.
   Explicitly require `readiness_verified_at <= session.measurement_start_at`.
   Ordinary runtime readiness reload verifies ancestry, NOT this timing gate.
   `test_equality_qualifies_and_late_readiness_consumes_session` proves that a
   late failed issuance can leave claim/readiness rows; those must not qualify
   Phase113. Equality qualifies, as in the existing runner/attempt contracts.
4. `SQLiteNARPreCProductionPrestagedManifestArchive.load_authority()` with
   the existing Phase109 repository; require exact manifest and availability
   identities, complete pair and expected target/cutoff. This reloads Phase109,
   reconstructs the full manifest and validates mapping equality. Phase109's
   ordinary reload verifies V019, Phase110 population and V010 consistency;
   it does NOT directly reopen Phase111 archives.
5. Require NAR/nar_official throughout. Missing/corrupt/contradictory upstream
   evidence fails closed. Reject upstream connections with caller-owned active
   transactions so uncommitted upstream rows cannot qualify; no upstream writes.

Approved correction 2: readiness must match exact claim, runtime binding,
session and configuration; before/equal session start qualifies, after start
is NONQUALIFYING even when claim/readiness are durably present. No clock sample.

Approved correction 3:
`PERSISTED_RUNTIME_CLAIM != CURRENT_PROCESS_EXECUTION_CAPABILITY`.
`PHASE113_CLAIM_BINDING != CURRENT_PROCESS_EXECUTION_CAPABILITY`.
`PHASE113_CLAIM_BINDING != ROOT_EXECUTION_PERMISSION`.
Phase113 does not create, reconstruct, consume or substitute for
`NARCurrentProcessExecutionCapability`; runner/process/lock liveness is not
Phase113 authority. A durable binding remains execution-inert when the original
capability disappears, even if its immutable ancestry continues to exact-load.
Archived claims may prove the binding relationship but cannot revive execution.
Neither timely readiness nor successful Phase113 reload proves a current lock,
live process capability, an unconsumed root, or current session admission.
Phase111 direct reload, provider capture/refetch and HTML parsing remain zero.

### Approved value and canonical content

Distinct frozen value: `NARPreCProductionClaimBindingV1`, schema version 1,
content identity `nar-pre-c-production-claim-binding-v1:<64 lowercase hex>`.
Canonical UTF-8 JSON and exact field set bind:

```text
claim_identity
runtime_binding_identity
session_identity
campaign_readiness_receipt_identity
phase112_manifest_identity
phase112_availability_receipt_identity
phase109_receipt_id
organization = NAR
source_system = nar_official
external_race_id
internal_race_id
prediction_cutoff
schema_version = 1
```

All fields derive from exact upstream loads. Use exact identity prefix/digest
shapes, strict positive internal ID type and canonical aware UTC cutoff.
No arbitrary caller JSON is issuance authority. No entry_mapping, horse IDs,
copied Phase110/111 ancestry, generic authorized flag, issued_at, bound_at,
available_at copy, started_at, new service-clock timestamp, root/claim-consumption
state or execution capability in the value.
The Phase112 identities already content-bind complete mapping and availability.
Raw value construction/JSON parsing establishes canonical content only, not
qualified authority; authoritative issuance/load always revalidates upstream.

### Audit finding 3 — separate exact companion persistence

New explicitly injected SQLite companion connection; own version-1 registry
and one immutable binding table. No main migration (no V020), no objects in
runtime, Phase108 or Phase112 archives, no fixed filename or self-opened DB.
Their exact topology validators prohibit adding Phase113 there. Cross-store
references are canonical identities verified by loaders, not cross-DB FKs.

Approved persistence model, with objects: `nar_pre_c_production_claim_binding_schema_migrations` and
`nar_pre_c_production_claim_bindings`, exact registry VERSION=1 and reviewed
DDL; immutable UPDATE/DELETE guards on registry and bindings independently of
foreign_keys. Identity PK, manifest identity UNIQUE, availability identity
UNIQUE, external target/cutoff UNIQUE and internal target/cutoff UNIQUE, each
target constraint including organization/source_system. Claim, session, runtime
binding and campaign readiness receipt are all nonunique in this archive.
Full payload plus scalar projection must agree exactly on reload; no entry
projection table is necessary because Phase112 exact reload owns population.

Distinguish NOT_INSTALLED (empty uninstalled companion), ACTIVE (exact registry,
objects, canonical/projection integrity) and INTEGRITY_FAILURE (partial/unknown/
drifted schema). Literal internal-prefix exclusion, e.g.
`name NOT GLOB 'sqlite_*'`, must expose legal sqliteX... objects. Corruption is
never absence. Unexpected SQLite operational/lock errors propagate unchanged.
No INSERT OR REPLACE, UPDATE-to-fit, DELETE-to-fit or silent repair.

### Approved publication, exact load, idempotence and failure contract

Approved correction 4: manifest-to-claim binding is permanent. The exact
claim + manifest + availability + target/cutoff may reload idempotently.
Same manifest + different claim fails closed permanently, even if the first
process exited, capability was lost, no production root started or the original
claim became unusable. Do not delete/rewrite/transfer/rebind the manifest,
repair onto another session, or rescue it after failure. Root consumption is
still deferred; loss of execution capability does not release the binding.

Approved correction 6: exact-reload runtime claim/binding/session/readiness and
qualify readiness, then exact Phase112 complete authority (therefore Phase109),
before deriving content and publication. No new time authority.
Exact-reload upstream runtime/readiness and Phase112/109 first, derive value;
then one companion-owned `BEGIN IMMEDIATE`. Require exact Phase113 schema,
look up identity/manifest/availability/external+cutoff/internal+cutoff collisions.
Exact existing full content returns the original binding; any contradiction
fails closed. Otherwise insert once. COMMIT, exact-reload the binding scalar
projection/JSON/content identity, exact-reload runtime claim/binding/session/
readiness again, enforce readiness qualification again, exact-reload Phase112
complete authority again (therefore reverify Phase109), and require the same
derived value before returning success.
Idempotent return must also perform final exact upstream validation.

Own write transaction only: no upstream writes, locks or cross-store atomicity
claim. Reject caller-owned transactions. Roll back every pre-commit failure,
including a genuine post-INSERT/pre-COMMIT failure, leaving no new binding and
`in_transaction=False`. Post-commit load/upstream failure returns no qualified
success, but does not delete the committed immutable row; a later exact load
may qualify it only if all upstream checks succeed. Concurrent publishers
serialize by SQLite and uniqueness, not a process-local lock: exact losers
reload the same binding, contradictory losers fail closed. Immutable upstream
rows plus final revalidation support this split; it is not an atomic snapshot
of all stores nor root execution admission.

`NO_CROSS_STORE_ATOMICITY_CLAIMED`.
`NO_CROSS_STORE_ROLLBACK`.
`NO_SILENT_REPAIR`.
`NO_INSERT_OR_REPLACE`.
Post-commit upstream reload failure means `RETURN_SUCCESS = NO`, not deletion
or rewrite of the committed row; exact retry requires all upstream reloads.

### Clock model and deferred Phase114 boundary

NO NEW CLOCK SAMPLE. No existing binding ancestry contract requires a new
Phase113 timestamp. Static readiness qualification uses stored upstream times;
Phase112's availability receipt remains the only prestaging availability time.
Do not require Phase112 availability <= cutoff or invent binding-issued time.
Phase113 need not decide whether a root could start now or in a past session.
`PHASE113_CLOCK_SAMPLES = 0`.
Reference the exact availability receipt identity; only authoritative Phase112
reload supplies `availability_receipt.available_at`, not a copied binding time.

Approved correction 5:
`PHASE113_BINDING != COMPLETE_PRODUCTION_ROOT_SCOPE_AUTHORITY`.
`PREDICTION_CUTOFF_VALUE != PREDICTION_CUTOFF_PLAN_AUTHORITY`.
Phase113 verifies only Phase112's NAR/source/external race/internal race/cutoff
projection. Diagnostic Phase108 scope also includes target-set content SHA,
cutoff-plan SHA, canonical cutoff-plan JSON, cutoff-policy ancestry and dataset
identity; Phase112 does not supply that complete authority. Do not copy, invent
or infer it in Phase113. A separately reviewed successor must exact-bind accepted
target-set/cutoff-plan/dataset authorities before production root construction.
Phase113 closes runtime claim <-> Phase112 mapping authority only.

Future separately reviewed Phase114 must own: exact Phase113 and upstream
reload immediately before root start; current locked process capability for
the same claim; one binding -> at most one production root; consumption/replay
protection; saved rows never recreate permission; strict
`availability_receipt.available_at < root.started_at` on an accepted clock/order
basis; accepted half-open session admission at root.started_at; durable root
publication and exact reload BEFORE all causal provider work. No request before
that boundary. Recording these invariants is not a Phase114 implementation
design or authorization. Complete production root-scope authority, target-set/
cutoff-plan/dataset binding, production root identity, campaign-lock ownership
and current-process capability validation also belong to that successor.
Existing diagnostic Phase108 V1 remains untouched.

Phase113 establishes binding only, NOT root execution permission, request-family
authorization, provider work, historical snapshot/freeze/prediction/bets, entry
status, market/prediction/betting eligibility, live campaign, Operational Delta,
provider historical availability or prediction-source availability. Phase110
identity-only denials remain intact; mapped/bound identity is not ACTIVE.

`MAPPING_AUTHORITY != ENTRY_STATUS_AUTHORITY`.
`MAPPING_AUTHORITY != MARKET_ELIGIBILITY`.
`MAPPING_AUTHORITY != PREDICTION_SELECTION_AUTHORITY`.
`MAPPING_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.
`MAPPING_AUTHORITY != OPERATIONAL_DELTA_AUTHORITY`.

### Historical Allowed Files — the preceding APPROVE activity

`docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md` only.

### Allowed Files — executed approved 10-path scope

1. `scripts/simulation/nar_pre_c_production_claim_binding.py` — new value.
2. `scripts/simulation/nar_pre_c_production_claim_binding_issuance.py` — new controlled issuer.
3. `scripts/simulation/nar_pre_c_production_claim_binding_archive_migration.py` — new standalone version-1 schema.
4. `scripts/simulation/sqlite_nar_pre_c_production_claim_binding_archive.py` — new exact persistence/reload.
5. `tests/test_nar_pre_c_production_claim_binding.py` — new value tests.
6. `tests/test_nar_pre_c_production_claim_binding_issuance.py` — new authority tests.
7. `tests/test_nar_pre_c_production_claim_binding_archive_migration.py` — new topology tests.
8. `tests/test_sqlite_nar_pre_c_production_claim_binding_archive.py` — new transactional tests.
9. `docs/CURRENT_PHASE.md`.
10. `docs/LATEST_CODEX_REPORT.md`.

Audit finds these additive paths sufficient; no existing API modification is
required. `PHASE113_ALLOWED_FILES = 10_PATH_SCOPE`: exact set above, no 11th path.
Historical approval was documentation-only. The subsequent explicit
EXECUTE_APPROVED_PHASE authorized these exact ten paths; implementation is now
uncommitted, independently reviewed and approved for a local commit without
expanding that scope. The implementation/test bytes remain unchanged.

### Forbidden Files

Every other repository path, particularly runtime/session/attempt/lock modules,
all Phase108 V1/harness/archive/bootstrap/reconciliation, Phase109/V019,
Phase110/V018, Phase111, V010/snapshot, migration runner, database, prediction,
betting, live-campaign and all existing tests. Related tests are run-only.
`C:\Users\garim\Desktop\KeibaAI`, production DBs, logs and external review
bundles are forbidden. The preceding APPROVE activity did not edit implementation.

### Required Tests — approved implementation contract

1. Exact archived claim/session mandatory; caller claim/value/mapping is not authority.
2. Missing/corrupt runtime binding, activation, bundle/profile or mismatched claim fails.
3. Exact readiness mandatory; wrong claim/session/binding/configuration fails;
   before and equality at session start both PASS, after start FAIL CLOSED
   without a clock sample; persisted late claim/readiness presence alone rejects.
4. Exact Phase112 complete pair mandatory; orphan manifest/availability alone rejects.
5. Corrupt Phase112 or V018/V019/V010/Phase109, wrong availability/receipt ancestry rejects.
6. Target/cutoff/NAR/source equality and full upstream-derived scalar agreement.
7. Canonical deterministic JSON/content ID; malformed identities/types/naive cutoff,
   extra fields/noncanonical JSON and stored projection/identity mismatch reject.
8. Exact repeated pair + claim returns original identity; all upstream reloads repeat.
9. Same manifest/availability with different claim rejects; contradictory external
   and internal target/cutoff conflicts reject independently (forward/reverse).
   Different-claim rejection is permanent even when the first binding has no
   root and the first process/capability is gone; delete/rewrite/rebind cannot rescue it.
10. Same real claim accepts two distinct, independently valid Phase112 targets;
    the SAME claim/session/runtime binding/readiness identities across both
    rows are accepted. Prove each of these four identities is NOT globally
    unique; no root or target scheduling implied.
11. Empty absent, exact active and partial/corrupt schema; exact registry/objects,
    missing/extra objects and legal sqliteXunreviewed presence -> integrity failure.
12. Immutable registry/binding UPDATE/DELETE rejected with foreign_keys OFF.
13. Caller transactions/uncommitted upstream rejected; missing schema not repaired.
14. Genuine post-write rollback: allow binding INSERT, observe completed write,
    deny COMMIT; zero bindings and no open transaction, upstream unchanged.
15. Two independent file-backed publishers: exact race yields one binding and
    exact winner reload; contradictory claim race yields one winner + conflict.
16. Post-commit binding reload AND upstream reread failures never return success;
    durable row remains immutable and retry requires complete validation.
17. Operational SQLite/lock errors propagate; no broad error-to-absence conversion.
18. No clock argument/sample, caller time, available_at/started_at or root capability.
    Also no issued_at/bound_at/time copy, no capability reconstruction/consumption,
    root/root start/provider request/attempt creation, or complete root-scope claims.
19. Zero provider transport/refetch/parser/Phase111 direct archive load.
20. Zero main/runtime/Phase112 DB mutation, new race/horse IDs or denial clearing.
21. Zero status/market/prediction/live/Operational Delta promotion or fixed DB path.
22. Phase108 V1 remains diagnostic-only, untouched, including sealed-child regression.

Executed focused command: `python -m pytest -q --tb=short` followed by the four
new test modules listed above. Executed focused + related command adds all:

```text
tests/test_nar_pre_c_production_prestaged_manifest.py
tests/test_nar_pre_c_production_prestaged_manifest_issuance.py
tests/test_nar_pre_c_production_prestaged_manifest_archive_migration.py
tests/test_sqlite_nar_pre_c_production_prestaged_manifest_archive.py
tests/test_nar_operational_timing_runtime_execution_archive.py
tests/test_nar_operational_timing_campaign_runner.py
tests/test_nar_operational_timing_observability_v2.py
tests/test_nar_operational_timing_session_activation_v2.py
tests/test_nar_operational_timing_v2_authority_archive_migration.py
tests/test_sqlite_nar_operational_timing_v2_authority_archive.py
tests/test_nar_operational_timing_attempt_archive_migration.py
tests/test_nar_operational_timing_passive_wrapper.py
tests/test_nar_pre_c_operational_envelope.py
tests/test_nar_pre_c_operational_envelope_sealed_child.py
```

Then full `python -m pytest -q --tb=short` was executed. Existing
`test_real_sealed_child_rehearses_production_capture_and_normalization_without_network`
requires the sealed-smoke env commit equal HEAD. At this unchanged approved
preparation base the required value is
`KEIBAOS_PHASE106_SEALED_COMMIT_SMOKE=9c1bd2b643826bd62551a326c61884a161672f8e`;
this follows the committed test, not a new source identity. Phase108's separately
approved reviewed-commit env gate remains unchanged; do not relabel precommit
mechanics as final sealed-source verification or invent that approval.
Static audit all four new modules for transport/parser/Phase111/fixed path/main
write/ID issuance/clock/caller mapping/status/root/live/replace/repair. Final
diff check, exact dirty-scope and empty-index audits; no stage/commit/push.
No pytest or SQLite experiment was run during the historical architecture-only
activity. The subsequent authorized implementation verification is recorded above.

### Stop Condition and review disposition

Stop for ChatGPT if cardinality cannot be proven or one-race contracts conflict;
binding needs execution consumption atomically; any predecessor exact topology,
API or semantics must change; any path outside the approved 10 needs edits;
new ambiguous timestamp, cross-DB atomicity, fixed path, provider/parser/Phase111
reload, ID issuance, status/eligibility/prediction/Operational Delta/root/live
authority becomes necessary; tests fail out of scope; or unexpected dirty paths
appear. No migration implementation or additional authority may be guessed.

No concrete repository blocker found for this additive binding-only contract.
Historical preparation stopped for `CHATGPT_REVIEW_PHASE113_DESIGN`. ChatGPT
returned PASS_WITH_REQUIRED_CONTRACT_CORRECTIONS; all six corrections were
recorded and the design approved. At that historical approval point implementation
had not been executed; the current execution/review disposition supersedes it.
Historical EXECUTE disposition: no implementation review PASS, commit approval
or Phase113 formal completion had then been supplied. Independent implementation
PASS and local commit approval are now recorded above; formal completion is not.
APPROVE final checks: git diff --check PASS; only the two documentation files
dirty; index EMPTY; HEAD/tree/branch unchanged. Provider HTTP = 0; production DB
access = 0; live campaign = 0; KeibaAI changes = 0; stage = 0; commit = 0; push = 0.
Historical next step was approval verification and separate EXECUTE_APPROVED_PHASE.
That execution authorization was supplied and executed. Its historical next step
was independent ChatGPT implementation review, without stage/commit/push.
ChatGPT has since passed that review and authorized the exact local commit only.
After local commit and structural evidence collection, stop for independent
ChatGPT post-commit verification; push remains unauthorized.

---

## Historical Record — Phase112 finalization before final remote acceptance

## POST_V0_8_DAILY_REPLAY_112

Title: NAR Production PRE_C Prestaged Mapping Manifest Authority

Status: `WAITING_FOR_PHASE_INSTRUCTION`

Formal Status: `FORMALLY_COMPLETE`

State: `FORMALLY_COMPLETE`

Outcome: `PHASE112_NAR_PRODUCTION_PRE_C_MAPPING_PRESTAGING_AUTHORITY_FORMALLY_INTEGRATED`

Implementation: `REMOTELY_VERIFIED`

Base Commit: `fa648f7d17aa9f79dc21e9ed51d6c01d0d2e6a84`

Base Tree: `d53ff1859a03d725251faec0d8ad681c97a241f3`

Branch: `feature/post-v0.8-daily-replay`

`PHASE112_ARCHITECTURAL_REVIEW_CORRECTIONS_REQUIRED = RESOLVED`.
`PHASE112_ARCHITECTURAL_REVIEW_PASS`.
`PHASE112_IMPLEMENTATION_DESIGN_APPROVED`.
`PHASE112_IMPLEMENTATION_APPROVAL = GRANTED`.
`PHASE112_ALLOWED_FILES = 10_PATH_SCOPE`.

Historical first implementation review:
`CHATGPT_REVIEW_PHASE112_IMPLEMENTATION = CHANGES_REQUIRED`.
The three findings were repaired within the same 10-path scope:

1. The companion schema's SQLite-internal object exclusion now uses literal
   `name NOT GLOB 'sqlite_*'`. A `sqliteXunreviewed` table is shown present in
   `sqlite_schema` and makes the exact schema state `INTEGRITY_FAILURE`.
2. Separate Stage A and Stage B tests allow the respective INSERT to succeed,
   then deny COMMIT. Each records one completed SQLite change at the COMMIT
   authorizer callback and proves rollback of that stage's write. Stage A
   leaves 0 manifest/0 availability rows and samples no clock. Stage B leaves
   the original exact inert manifest and 0 availability rows; a normal retry
   publishes one truthful receipt, and a completed repeat does not resample.
3. Availability receipt manifest identity now requires exactly the canonical
   prefix followed by 64 lowercase hexadecimal characters. Direct tests
   reject an extra colon segment, 63/65-character digests, and uppercase hex.

Independent re-review disposition:
`CHATGPT_REVIEW_PHASE112_IMPLEMENTATION = PASS`.
`PHASE112_IMPLEMENTATION_REVIEW_PASS`.
`PHASE112_COMMIT_APPROVED`.
`PHASE112_POST_COMMIT_VERIFICATION_PASS`.
`PHASE112_REMOTE_IMPLEMENTATION_VERIFICATION_PASS`.
`PHASE112_IMPLEMENTATION_REMOTE_ACCEPTED`.
`PHASE112_FORMAL_CLOSURE_APPROVED`.
`PHASE112_CLOSURE_COMMIT_VERIFICATION_PASS`.
`PHASE112_FORMAL_CLOSURE_REMOTE_VERIFICATION_PASS`.
`PHASE112_CLOSURE_REMOTE_VERIFIED`.
`PHASE112_FORMAL_COMPLETION_APPROVED`.
The accepted repair verification is 35 focused passes; 170 passed, 2 skipped,
55 subtests passed in focused plus related; 4898 passed, 4 skipped, 2846
subtests passed in the full suite; and static production audit PASS. The
first-review `CHANGES_REQUIRED` disposition above remains historical.

`POST_V0_8_DAILY_REPLAY_112 = FORMALLY_COMPLETE`.
The implementation was pushed normally and independently verified on GitHub;
ChatGPT accepted it and approved documentation-only formal closure.

Implementation Commit: `cb71b8482105017aaa362221513db10e42a27f14`

Implementation Tree: `4db5c9b0e1655f4f2cecef35da474e94e28643cd`

Implementation Parent: `fa648f7d17aa9f79dc21e9ed51d6c01d0d2e6a84`

Formal Closure Commit: `7a7f6a20679347fa1ff332ba36f4bc9862907a77`

Formal Closure Tree: `63c2820fbd28c4a9f9724f6d01af2bcceacb544e`

Formal Closure Parent: `cb71b8482105017aaa362221513db10e42a27f14`

The docs-only closure commit was independently verified, pushed normally,
and independently verified on GitHub. ChatGPT approved formal completion.
This final documentation activity changes only `docs/CURRENT_PHASE.md` and
`docs/LATEST_CODEX_REPORT.md`. Its own local commit is authorized, but its
push is not authorized and its own remote verification remains pending.
Next: `WAITING_FOR_PHASE_INSTRUCTION`; the final documentation commit must
first receive independent ChatGPT verification. The Phase109 formal-completion
record below remains historical and unchanged.

Phase112 grants only production PRE_C mapping-prestaging authority. It does
not grant root execution permission, claim/session binding or consumption,
entry status authority, market eligibility, prediction-selection authority,
live campaign authorization, or Operational Delta authority.
A future separately reviewed phase owns production PRE_C execution
integration. No tests were rerun for docs-only closure or this finalization;
the accepted implementation verification below remains the evidence.

### Implementation verification for independent review

The four approved production modules implement a content-addressed manifest
derived solely from exact Phase109 receipt reload, a separate controlled-UTC
availability receipt, and an injected, standalone SQLite companion archive.
The archive has its own version-1 registry, exact absent/active/corrupt schema
classification, both external and internal target/cutoff uniqueness, and
immutable UPDATE/DELETE guards. Stage A commits and exact-reloads the mapping
manifest before Stage B may sample the clock. Stage B uses a second
`BEGIN IMMEDIATE`, reuses an existing exact availability receipt without
resampling, or commits one new receipt and exact-reloads the complete pair
plus Phase109 before returning. An orphan manifest is inert. Phase108 V1 and
the main simulation DB remain unchanged.

New test modules:
`tests/test_nar_pre_c_production_prestaged_manifest.py`,
`tests/test_nar_pre_c_production_prestaged_manifest_issuance.py`,
`tests/test_nar_pre_c_production_prestaged_manifest_archive_migration.py`, and
`tests/test_sqlite_nar_pre_c_production_prestaged_manifest_archive.py`.
Repair focused run: **35 passed**. Combined focused plus the ten approved,
unchanged related regression modules: **170 passed, 2 skipped, 55 subtests passed**.
Full repository `python -m pytest -q --tb=short` with
`KEIBAOS_PHASE106_SEALED_COMMIT_SMOKE=fa648f7d17aa9f79dc21e9ed51d6c01d0d2e6a84`:
**4898 passed, 4 skipped, 2846 subtests passed**. The prior pre-review
baseline was 28 focused, 163 combined, and 4891 full-suite passes; those
counts are historical, not the repair verification. The static Phase112
production audit found no provider transport, Deba parser/refetch, Phase111
archive load, fixed DB path, main-DB write, internal-ID issuance,
status/eligibility/root/live authority, or `INSERT OR REPLACE`. The only new
inserts target the injected companion archive registry, manifest, and
availability tables. Provider HTTP = 0; production DB access = 0; KeibaAI
changes = 0; stage = 0; commit = 0; push = 0 during implementation verification.
The index remained empty through the review evidence collection.

### Objective

Establish a durable, exact-reloadable production PRE_C *mapping-prestaging*
authority from one accepted `NARProductionMappingReceiptV1`. End Phase112 at
the value, controlled issuance, durable publication, exact reload, and
availability proof. A later separately reviewed production PRE_C adapter must
bind that proof to an execution claim and root before any root starts. Phase112
does not start a root, send a provider request, build a historical input
snapshot, or authorize live execution.

### Verified Base

The branch, HEAD, and tree above matched the clean, empty-index repository at
preparation start. The current main-DB standard migration chain ends at V019.
`POST_V0_8_DAILY_REPLAY_111`, `_110`, and `_109` are formally complete;
`PHASE109_FINAL_DOCUMENTATION_REMOTE_VERIFICATION_PASS` is recorded. This is
source-contract inspection only, not a claim about deployed database contents.

### Current Architecture Audit

- `NARProductionMappingReceiptV1` binds one external/internal race, canonical
  Deba URL, Phase110 receipt, Phase111 ancestry, prediction cutoff, Phase109
  `issued_at`, and a horse-number-ordered, forward/reverse-unique complete
  entry relation. Its SHA-256 receipt ID binds canonical JSON and its
  `mapping_population_sha256` binds the ordered entry projection.
- `SQLiteNARProductionMappingRepository.load_receipt()` requires exact V018 and
  V019 schema, parses the canonical receipt, checks SQL header/entry projections,
  exact-reloads Phase110, and verifies both directions of the V010 mirror.
  This is the Phase112 input authority. V010 rows and caller tuples are not.
- V019 provides immutable receipt/entry tables and covered V010 drift guards.
  Phase109 **publication** directly verified the Phase111 declaration, claim,
  acquisition receipt, and official capture ancestry. Ordinary Phase109
  `load_receipt()` does not reopen those separate archives: it checks its
  immutable V019 projection, Phase110 complete population, and V010 mapping
  consistency. Phase112 consumes that formally accepted Phase109 authority,
  without Phase111 archive parameters, Deba refetch, HTML re-extraction, or
  copying Phase111 fields into its manifest.
- `NARPreCPrestagedInputManifestV1` instead requires a diagnostic fixture JSON,
  fixture-member `mapping_content_authority`, claim, mapping, and history.
  `issue_target_pre_c_root()` checks actual fixture bytes and an AST-reviewed
  fixture mapping literal. The V1 plan/root and archive `_TABLES` accept that
  exact class/identity prefix, and the Phase108 archive validates an exact
  approved topology. They cannot be treated as a production mapping issuer.
- `HistoricalInputSnapshotBuilder` takes a caller mapping and requires a
  complete source-record entry set; the snapshot repository may write V010.
  Neither source supplies Phase112 origin or prestaging time. The snapshot
  freeze receipt explicitly distinguishes exact reload from crash durability.

### Authority Model

`PHASE109_MAPPING_RECEIPT != PHASE108_V1_FIXTURE_MAPPING`.
`PHASE108_V1_FIXTURE_MAPPING != PRODUCTION_MAPPING_AUTHORITY`.
`PRODUCTION_PHASE109_AUTHORITY_MUST_NOT_BE_LAUNDERED_THROUGH_FIXTURE_V1`.
`V010_MAPPING_ROW_EXISTENCE != PHASE112_PRESTAGED_AUTHORITY`.
`CURRENT_DB_MAPPING_EXISTENCE != HISTORICAL_MAPPING_AVAILABILITY_PROOF`.
`PHASE112_MANIFEST_EXISTENCE != ROOT_START_PERMISSION`.
`MANIFEST_EXISTENCE != PRESTAGE_AVAILABILITY`.
`MANIFEST_PLUS_AVAILABILITY_RECEIPT = PHASE112_PRESTAGED_AUTHORITY`.
`PHASE112_PRESTAGED_AUTHORITY != ROOT_EXECUTION_PERMISSION`.
`PHASE111_DIRECT_RELOAD_AT_PHASE109_PUBLICATION = REQUIRED_AND_COMPLETE`.
`PHASE111_DIRECT_RELOAD_AT_PHASE112_PRESTAGE = NOT_REQUIRED`.
`PHASE112_TRUSTS_FORMALLY_ACCEPTED_PHASE109_AUTHORITY`.

`MAPPING_AUTHORITY != ENTRY_STATUS_AUTHORITY`.
`MAPPING_AUTHORITY != MARKET_ELIGIBILITY`.
`MAPPING_AUTHORITY != PREDICTION_SELECTION_AUTHORITY`.
`MAPPING_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.
`MAPPING_AUTHORITY != PHASE108_ROOT_AUTHORITY`.
`MAPPING_AUTHORITY != OPERATIONAL_DELTA_AUTHORITY`.
Phase110-issued denied entries remain in the full mapping and remain denied.

### Recommended Manifest Semantic

Use a distinct `NARPreCProductionPrestagedInputManifestV1` semantic,
not `NARPreCPrestagedInputManifestV2`: V1 is diagnostic, claim-bound, and
fixture-authorized, whereas production mapping origin is a V019 receipt. Use
a new canonical identity prefix/schema version. The manifest contains exactly
the Phase109 receipt ID, `NAR/nar_official`, external/internal race IDs,
prediction cutoff, Phase109 `issued_at`, complete canonical ordered
`(external_entry_id, race_entry_id, horse_no)` relation, count, and mapping
SHA-256. Its content ID covers the full canonical payload and does not include
`available_at`. The separate immutable
`NARPreCProductionPrestagedAvailabilityReceiptV1` names that manifest and
records the controlled availability time. Copying Phase110/111 lineage fields
is unnecessary; every successful Phase112 load exact-reloads the accepted
Phase109 receipt, which verifies Phase110 and V010 but does not reopen Phase111
archives. Additional caller-provided target/cutoff
values are equality expectations only, not mapping facts. No caller mapping,
horse-number matching, V010 adoption, or new internal ID issuance is permitted.

The mapping manifest is target/cutoff-specific, claim-independent, and
session-independent. Neither record contains a claim/session execution
capability or grants reusable execution permission. A future production adapter must
make a separately durable one-claim binding/consumption decision, exact-reload
the manifest plus availability evidence, verify the claim's target/cutoff, and
reject second-claim/replayed root use. That later reviewed phase also owns the
production plan/root semantic, pre-root reload, root-start causal ordering,
and acceptable clock basis. Phase112 cannot issue that claim or root.

### Persistence / Availability Model

Use a *separate injected SQLite companion archive* with its own version-1
registry, exact topology validator, append-only/content-addressed manifest
table, and append-only availability-receipt table. Do not register a V020 main
DB migration or add objects to the exact Phase108 timing archive. The issuer
receives existing read-only Phase109 repository access and an explicitly
injected companion archive connection; it must not open a fixed production DB
path. An exact production filesystem path is intentionally outside Phase112,
not an architecture blocker. Only this new archive may be mutated by Phase112.

The companion schema must enforce at least unique manifest identity, unique
Phase109 receipt ID, both unique target/cutoff keys
`(organization, source_system, external_race_id, prediction_cutoff)` and
`(organization, source_system, internal_race_id, prediction_cutoff)`, unique
availability receipt identity, and one availability receipt per manifest.
Forward or reverse target conflict fails closed; no `INSERT OR REPLACE`,
destructive repair, or second timestamp for a completed authority.

Publication has two causal companion-archive transactions, without assumed
cross-DB atomicity. **Stage A:** exact-reload Phase109, compare expected
target/cutoff, and derive the manifest solely from it. Acquire `BEGIN
IMMEDIATE`; check both target/cutoff directions and the Phase109 receipt key.
For exact existing content, close the transaction and exact-reload the
committed manifest; reject contradictory content. Otherwise insert the exact
manifest, commit, and exact-reload it. Sample no clock before this commit and
reload. **Stage B:** acquire a second `BEGIN IMMEDIATE`. If the exact manifest
already has an availability receipt, close the transaction *without sampling*
and exact-reload the original pair and Phase109. Otherwise, while holding the
write transaction, sample the controlled aware-UTC service clock, reject
naive/invalid time and time earlier than Phase109 issuance, insert one immutable
`NARPreCProductionPrestagedAvailabilityReceiptV1`, commit, then exact-reload
the pair and Phase109 before returning qualified Phase112 authority. A racing
loser returns the winner's original exact receipt, never a second time.

The manifest alone is inert. A Stage A commit followed by Stage B failure or
crash leaves an exact recoverable manifest but no availability authority; retry
may attach its first receipt using a newly sampled truthful time. Do not delete
or rewrite the inert row. A completed exact repeat returns the original
receipt and timestamp unchanged. Unexpected SQLite lock/operational errors
propagate unchanged.

The UTC clock is a controlled publication observation, not a provider
`available_at` or cryptographic timestamp. Clock reversal, naive time, or a
time before Phase109 issuance fails. Future root integration must rely on an
exact pre-start reload and ordering, not on a timestamp alone. A crash before
the first commit publishes nothing; after the first commit it may leave only
an inert manifest; after the second commit, retry exact-reloads the immutable
authority. Failed post-commit reload never returns success and never invents
an earlier time. Main-DB/V019 absence, corruption, or drift makes the pair
unusable even if the companion bytes persist. No cross-store rollback is
claimed.

### Temporal Contract

Retain `Phase111.observed_at <= prediction_information_cutoff` and
`Phase110.issued_at <= Phase109.issued_at`. Add only
`Phase109.issued_at <= availability_receipt.available_at`. The latter is
sampled after the manifest's committed exact reload and persisted in the
separate receipt; the manifest payload has no `available_at`. Future
production root integration must prove the Phase112 pair was committed and
exact-reloaded before root issuance and
`availability_receipt.available_at < root.started_at` on a separately reviewed
acceptable clock/order basis. The timestamp alone is insufficient. Neither
Phase109 issuance nor Phase112 prestaging is
required to precede the prediction-information cutoff. This availability
semantic must not be substituted for prediction-source availability.

### Exact Reload Contract

For issuance and every authoritative load: require active exact companion
schema, exact Phase109 `load_receipt(receipt_id=...)` (thus active V018/V019,
Phase110 and V010 equality), receipt ID/content and target/cutoff equality,
canonical manifest JSON/ID and SQL projection equality, complete ordered
entry-set and count/digest equality, forward/reverse uniqueness, and canonical
availability receipt/ID/time/projection equality. Reject absent Phase109,
missing/extra/reordered/duplicate entries, wrong race/cutoff, contradictory
target publication, and corrupt/partial schema. Distinguish companion schema
NOT_INSTALLED, ACTIVE, and INTEGRITY_FAILURE; corruption never falls back to
absence. Propagate unexpected SQLite lock/operational errors unchanged.
Exact repeat returns the already published pair; it does not resample or
backdate availability. Post-availability commit reload failure never returns
qualified success. If Phase109 authority differs between preflight and final
reload, fail closed; a persisted companion pair is unusable until the exact
upstream authority is verified. No silent repair or `INSERT OR REPLACE`.
Phase112's issuer has no Phase111 archive/capture input, and ordinary Phase109
load does not need those parameters.

### V1 Compatibility

Keep `NARPreCPrestagedInputManifestV1`, `fixture_bundle_json`,
`mapping_content_authority`, AST-reviewed fixture mapping,
`DIAGNOSTIC_ONLY_NO_NETWORK`, `run_phase108_no_network_rehearsal()`, and the
existing Phase108 `_TABLES`/`_TYPES` and exact archive topology unchanged.
Production manifest storage is separate; the current V1 plan/root/reconciler
must continue rejecting it. Later production PRE_C integration requires a
reviewed production adapter/plan/root semantic, one-claim binding, and
pre-root exact reload. It is deferred, not implied by Phase112.

### Reader / Writer Inventory

- Phase109 origin: `nar_production_mapping_authority.py` defines the receipt;
  `sqlite_nar_production_mapping_repository.py` publishes and reloads it;
  `v019_nar_production_mapping_authority_schema.py` owns V019 topology.
  Phase109 tests and `test_simulation_migrations.py` cover those boundaries.
  They are read-only inputs/regressions in Phase112.
- Phase108 diagnostic: `nar_pre_c_operational_envelope.py` defines V1 and its
  plan/root; `sqlite_nar_pre_c_operational_envelope_archive.py` reads/writes
  the exact V1 class; its archive migration/bootstrap own topology;
  `nar_pre_c_operational_envelope_harness.py` issues fixture roots and runs
  rehearsal; reconciliation reads V1/start. Their Phase108 tests are run-only.
- `historical_input_snapshot_builder.py` accepts a caller mapping;
  `sqlite_historical_input_snapshot_repository.py` reads/writes V010 and
  snapshots; `historical_input_snapshot_freeze_receipt.py` issues a separate
  snapshot proof. None is a Phase112 writer. The `entry_mapping` references
  in V010 migration and JRA/snapshot/race-entry tests are compatibility
  assertions. `nar_daily_replay_orchestrator.py` uses an unrelated snapshot
  `manifest_identity`, not Phase108's fixture manifest or Phase112 authority.
- No existing production reader consumes a production prestaged manifest.
  Phase112 adds only its own controlled issuer/archive reader; root consumption
  is deferred. No generic prediction, betting, Phase95, Phase41, or live
  campaign module is in the proposed write set.

### Allowed Files — APPROVED 10-PATH IMPLEMENTATION SCOPE

New production files:

- `scripts/simulation/nar_pre_c_production_prestaged_manifest.py`
- `scripts/simulation/nar_pre_c_production_prestaged_manifest_issuance.py`
- `scripts/simulation/nar_pre_c_production_prestaged_manifest_archive_migration.py`
- `scripts/simulation/sqlite_nar_pre_c_production_prestaged_manifest_archive.py`

Modified production files: none. New tests:

- `tests/test_nar_pre_c_production_prestaged_manifest.py`
- `tests/test_nar_pre_c_production_prestaged_manifest_issuance.py`
- `tests/test_nar_pre_c_production_prestaged_manifest_archive_migration.py`
- `tests/test_sqlite_nar_pre_c_production_prestaged_manifest_archive.py`

Existing regression-test modifications: none approved; existing
Phase109/V019, Phase110/V018, V010 snapshot, Phase108 V1/archive/rehearsal,
and historical freeze tests are run-only. Documentation files:

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

Approved total: **10 exact paths**. No 11th path is authorized. If
implementation proves another path necessary, stop for scope review before
editing it.

### Forbidden Files

During implementation, every file except the ten approved paths above was
forbidden for modification. Implementation kept
the current Phase108 value, harness, archive, migration, bootstrap,
reconciliation and tests; Phase109/V019; Phase110/V018; Phase111 acquisition;
V010/historical snapshot; prediction/betting; live campaign, database files;
and KeibaAI paths read-only unless ChatGPT separately changes the contract.
No main DB
backfill, provider HTTP, Deba refetch, HTML extraction, races/horses ID
issuance, status or eligibility promotion, or Phase108 root issuance.

### Required Tests — approved implementation contract

Focused new tests: exact Phase109 receipt and active V018/V019 required;
caller mapping cannot authorize; external/internal race and cutoff mismatch;
complete ordering/count/digest, missing/extra/reordered/duplicate entries,
forward/reverse uniqueness; deterministic canonical manifest and availability
receipt IDs; Phase109 issuance <= availability; no backdating; exact repeat
preserves the original availability time; conflicting same-target receipt
rejected; companion schema absent/active/corrupt and exact topology; append-only
enforcement even with foreign keys OFF; real post-write rollback in each
transaction; orphan manifest is inert; post-commit exact reload; two independent
issuers racing the same target; lock/operational-error propagation; no
network/parser/Phase111 refetch, main-DB mutation, or internal-ID issuance.
Also require: ordinary Phase109 load needs no Phase111 archive parameters;
the Phase112 issuer exposes no Phase111 archive/capture input; the manifest
payload excludes `available_at` and the availability receipt includes it;
completed exact repeat samples the UTC clock zero additional times; orphan
manifest retry samples once for its first receipt; two independent issuers
cannot create two timestamps/receipts and the loser returns the winner's
original exact authority; both external and internal target/cutoff reverse
conflicts and different Phase109 receipts for one target/cutoff fail closed;
availability insertion failure leaves only an inert exact manifest;
post-availability commit reload failure never returns qualified success.

Run-related regressions (unmodified):
`tests/test_nar_production_mapping_authority.py`,
`tests/test_sqlite_nar_production_mapping_repository.py`,
`tests/test_v019_nar_production_mapping_authority_schema.py`,
`tests/test_v018_nar_identity_complete_entry_schema.py`,
`tests/test_simulation_migrations.py`,
`tests/test_historical_input_snapshot_builder.py`,
`tests/test_historical_input_snapshot_freeze_receipt.py`,
`tests/test_sqlite_historical_input_snapshot_repository.py`,
`tests/test_nar_pre_c_operational_envelope.py`, and
`tests/test_nar_pre_c_operational_envelope_sealed_child.py`.
Then full `python -m pytest -q --tb=short` with the existing sealed-commit
environment contract, not an invented value. The completed implementation
verification and actual counts are recorded near the top of this section.

### Stop Condition

Stop if Phase109 exact reload cannot prove the complete mapping; the archive
cannot establish honest post-commit availability; trusted UTC clock ordering
cannot be specified; concurrent publication cannot be made unique; existing
Phase108 V1/its exact topology would need reinterpretation or destructive
replacement; cross-database atomicity would be assumed; root/live permission,
Phase95/41 status/eligibility, provider HTTP/HTML, new internal race/entry IDs,
main-DB repair, or an unreviewed file is required. Preserve the draft for
ChatGPT scope correction; do not implement around a conflict. Also stop if the
two-stage publication cannot preserve the completed original timestamp,
implementation needs `available_at` in the mapping manifest, Phase109 load
needs modification, Phase111 archive input, claim/session/root code, or a
fixed production archive path must be invented, or an 11th file is required.

### Architectural decisions resolved by review

1. The separate companion archive and two-record manifest plus availability
   receipt are approved. The exact filesystem path is injected by future
   composition, not a Phase112 architecture gap.
2. A later separately reviewed phase owns one-claim binding/consumption,
   production root semantics, and acceptable root clock/order evidence.
3. Phase109 publication directly verified Phase111 ancestry. Phase112
   exact-reloads the accepted Phase109 authority but does not directly reload
   Phase111 archives or copy their fields.

`PHASE112_IMPLEMENTATION_APPROVAL = GRANTED`.

---

## POST_V0_8_DAILY_REPLAY_109

Title: NAR Production External/Internal Mapping Authority

Status: `WAITING_FOR_PHASE_INSTRUCTION`

Formal Status: `FORMALLY_COMPLETE`

State: `FORMALLY_COMPLETE`

Outcome: `PHASE109_NAR_PRODUCTION_MAPPING_AUTHORITY_FORMALLY_INTEGRATED`

Base Commit: `bc47f59f0372b0de65b2786b6003c55acfda9e02`

Base Tree: `ab22ebda36667a6698d47cc824637d8036c30564`

Branch: `feature/post-v0.8-daily-replay`

`PHASE109_POST_PHASE110_REENTRY_AUDIT_COMPLETE`.
`PHASE109_POST_PHASE110_REENTRY_DESIGN_REVIEW_PASS`.
`PHASE109_IMPLEMENTATION_DESIGN_APPROVED`.
`PHASE109_IMPLEMENTATION_APPROVAL = GRANTED`.
`PHASE109_ALLOWED_FILES = 16_PATH_SCOPE`.
`PHASE109_TEST_SCOPE_EXTENSION_APPROVED`.
`PHASE109_IMPLEMENTATION_RESUME_APPROVED`.
`PHASE109_V010_MODEL = B`.
`PHASE109_V019_REQUIRED`.
`CHATGPT_REVIEW_PHASE109_IMPLEMENTATION = PASS`.
`PHASE109_IMPLEMENTATION_REVIEW_PASS`.
`PHASE109_COMMIT_APPROVED`.
`PHASE109_COMMITTED_BLOB_MISMATCH_ACCEPTED_EOL_ONLY`.
`REVIEWED_LOGICAL_CONTENT_PRESERVED = YES`.
`PHASE109_POST_COMMIT_VERIFICATION_PASS`.
`PHASE109_REMOTE_IMPLEMENTATION_VERIFICATION_PASS`.
`PHASE109_IMPLEMENTATION_REMOTE_ACCEPTED`.
`PHASE109_FORMAL_CLOSURE_APPROVED`.
`PHASE109_CLOSURE_COMMIT_VERIFICATION_PASS`.
`PHASE109_FORMAL_CLOSURE_REMOTE_VERIFICATION_PASS`.
`PHASE109_CLOSURE_REMOTE_VERIFIED`.
`PHASE109_FINAL_DOCUMENTATION_REMOTE_VERIFICATION_PASS`.
`POST_V0_8_DAILY_REPLAY_109 = FORMALLY_COMPLETE`.
The former `PHASE109_PRODUCTION_ENTRY_MAPPING_BLOCKED_BY_IDENTITY_COMPLETE_INGESTION`
and `PHASE109_IMPLEMENTATION = BLOCKED_NOT_AUTHORIZED` remain in the historical
audit below. Their *identity-ingestion prerequisite* is now satisfied by remotely
verified `POST_V0_8_DAILY_REPLAY_110 = FORMALLY_COMPLETE`. The Phase109 design
passed independent architectural review before implementation.
Implementation began within the original 15-path scope and stopped at the first
proven out-of-scope regression. That stop and its work preservation are historical;
the approved 16-path implementation later passed review, was committed, and was
independently verified at the remote branch.

`PHASE109_IMPLEMENTATION_STOPPED_FOR_SCOPE_EXTENSION`.
The V019 standard-runner registration changed `MIGRATIONS[:-1]` in the then-forbidden
`tests/test_v018_nar_identity_complete_entry_schema.py` from a through-V017
prefix into a through-V018 prefix. Its
`test_v018_installs_exact_registered_topology_and_rerun_is_noop` now expects
`PHASE110_SCHEMA_NOT_INSTALLED` but correctly observes `PHASE110_SCHEMA_ACTIVE`.
This is a historical-prefix fixture contract, not a reason to weaken V018 or
remove V019 from the standard registry. ChatGPT approved exactly that test file
as a 16th path. Its helper now selects `VERSION <= 17` explicitly; no V018
assertion was weakened. Direct new Phase109 tests before resumption: `17 passed`.
At that historical stop, the related regression run was interrupted for
classification; the full suite and final static audit had not run. No stage,
commit, or push occurred.

### Phase109 implementation and verification history

Historical state: `PHASE109_IMPLEMENTATION_REPAIR_READY_FOR_REVIEW`. The first independent
implementation review returned the historical result
`CHATGPT_REVIEW_PHASE109_IMPLEMENTATION = CHANGES_REQUIRED`; its two findings
were repaired within the existing 16-path scope. Independent re-review of the
exact repaired bytes passed and the local implementation commit was approved.
Finding 1 closed reverse-side V010 drift: covered V010 race/entry triggers now
guard both external and internal race identities (including OLD and NEW on
UPDATE) even with foreign keys OFF. Publication preflight and exact reload
compare the full four-field V010 entry relation selected by either race side
against the complete Phase110/V019 population. A reverse-side extra row fails
closed before publication or on reload. Finding 2 makes V019 `apply()` compare
the exact V010 mapping table/column/FK/index topology, including the prior V015
exact-mapping index, against a reference before creating any V019 object.
Pre-existing V010 drift leaves V019 unregistered, no V019 object, and the drift
unchanged after runner rollback. The genuine post-write failure test also
proves the transactionally inserted NAR source-identity row is rolled back.

V019 is registered in the standard migration runner and installs the immutable
`nar_production_mapping_receipts` and `nar_production_mapping_entries` authority
with exact schema-state validation, uniqueness, append-only triggers, and covered
V010 race/entry drift guards. The controlled publisher reloads exact Phase111
archive ancestry read-only, then under `BEGIN IMMEDIATE` exact-reloads the Phase110
receipt, validates the complete ordered mapping (including denied identities),
reconciles V010 only as consistency/mirror data, publishes V019 atomically, and
requires exact authority reload. Exact repeat is idempotent; contradictory or
partial publication fails closed. No internal race/horse ID is issued and no Deba
HTTP or HTML re-extraction is performed.

The one-file scope extension changes only `through_v017` from the positional
`MIGRATIONS[:-1]` to an explicit `VERSION <= 17` boundary; V018 assertions remain
unchanged. V018 direct regression: `5 passed`. Final Phase109 direct tests:
`27 passed`. Final related regression (all 17 required modules):
`261 passed / 127 subtests passed`. Final full repository suite:
`4863 passed / 4 skipped / 2846 subtests passed` using
`KEIBAOS_PHASE106_SEALED_COMMIT_SMOKE=bc47f59f0372b0de65b2786b6003c55acfda9e02`
and `python -m pytest -q --tb=short`. Static production audit: PASS; no provider
transport, production DB path, internal ID issuance, destructive V010 repair,
`INSERT OR REPLACE`, Phase95/41 authority, Phase108 fixture promotion, or live
campaign authorization. At the pre-commit implementation verification,
`git diff --check` passed, dirty paths were exactly the approved 16, and the
index was empty. Provider HTTP = 0; production DB access = 0;
KeibaAI changes = 0 for that verification. The subsequent approved local commit
and normal push are recorded below.
The prior independent-review baseline (`23 passed` direct, `257 passed / 127
subtests passed` related, `4859 passed / 4 skipped / 2846 subtests passed` full)
is historical evidence and does not substitute for these post-repair results.

Implementation Commit: `47723c1229b8c3c9c8df80b64a1088a3ea3e1e0f`.
Implementation Tree: `654db28bc3b78effb146b1c423accb2d9c4308f4`.
Implementation Parent: `bc47f59f0372b0de65b2786b6003c55acfda9e02`.
Formal Closure Commit: `9a20238584e4f3db3a02c8d8d4e2516b433d7cc4`.
Formal Closure Tree: `1a8289f87d02725d8d17ef26763087102d4fecf5`.
Formal Closure Parent: `47723c1229b8c3c9c8df80b64a1088a3ea3e1e0f`.
Final Documentation Commit: `f4d5451b2e7bc5bf6e217263d64ed3cc3bbdb649`.
Final Documentation Tree: `7145ad4e8ed04fe534f85e093078628d22f1a79b`.
Final Documentation Parent: `9a20238584e4f3db3a02c8d8d4e2516b433d7cc4`.
Independent post-commit review accepted Git's LF-normalized blobs: 14 reviewed
non-documentation files,
8/14 raw blob SHA-256 matches, 6/14 EOL-only mismatches, zero non-EOL byte
differences, and 14/14 exact matches after only CRLF-to-LF normalization.
`REVIEWED_LOGICAL_CONTENT_PRESERVED = YES`. The implementation commit was
pushed without force, and ChatGPT independently verified the remote branch at
that exact commit/tree, ahead one and behind zero from the base, with exactly
the approved 16 paths. The docs-only formal-closure commit was then verified,
pushed normally without force, and independently verified on the remote at the
exact closure commit/tree, ahead one and behind zero from the implementation
commit, with only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`
changed. `PHASE109_FORMAL_CLOSURE_REMOTE_VERIFICATION_PASS` and
`PHASE109_CLOSURE_REMOTE_VERIFIED` establish Phase109 formal completion. The
accepted direct/related/full-suite results and static audit above were not
rerun for docs-only closure or this finalization. Provider HTTP = 0; production
DB access = 0; KeibaAI changes = 0 for this activity.

Phase109 completion grants only the reviewed production NAR external/internal
mapping authority. It does not grant Phase95 status authority, Phase41 market
eligibility, prediction-selection authority, live campaign authorization,
Operational Delta, or Phase108 production root authority. Future production
Phase108 integration requires a separately reviewed production prestaged
manifest/version/adapter that exact-reloads the Phase109 receipt before root
availability. ChatGPT independently verified the final documentation commit
`f4d5451b2e7bc5bf6e217263d64ed3cc3bbdb649` on the remote at tree
`7145ad4e8ed04fe534f85e093078628d22f1a79b`, parent
`9a20238584e4f3db3a02c8d8d4e2516b433d7cc4`: ahead one, behind zero,
one commit, and only `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`
changed. `PHASE109_FINAL_DOCUMENTATION_REMOTE_VERIFICATION_PASS` is recorded.

### Re-entry evidence and exact input

Committed V018 stores one Phase110 receipt per exact existing internal race and
external race. `SQLiteNARIdentityCompleteEntryRepository.load_receipt(receipt_id=...)`
reconstructs canonical JSON/content ID, compares its SQL projection and every
ordered entry row, and verifies the issuance-denial topology. The receipt carries
`NAR/nar_official`, canonical `nar:YYYYMMDD:babaCode:raceNo`, canonical Deba URL,
one pre-existing `races.id`, every derived `nar-entry-v1` identity, canonical
horse number, optional canonical external horse identity, exact `horses.id`,
Phase111 declaration/receipt/capture IDs, response SHA-256, observation/cutoff,
`issued_at`, population count and SHA-256. Its constructor rejects duplicate
external IDs, internal IDs, and horse numbers, noncanonical ordering, and post-cutoff
observation. V018 entry keys/FKs and Phase110's `BEGIN IMMEDIATE` issuance bind
the complete population, including Phase110-issued denied identities. Thus the
old missing-identity prerequisite is satisfied; receipt existence is not yet
Phase109 mapping authority.

The future issuer accepts an *exact Phase110 receipt ID*, exact expected target and
cutoff for comparison, and the reviewed read-only Phase110/Phase111 archives. It
does not accept caller mappings or internal IDs as authority. It exact-reloads the
Phase110 receipt under active V018, and directly exact-reloads the Phase111
declaration/claim/controlled receipt/capture ancestry to prove the referenced
prospective qualified acquisition, digest, URL, target, and cutoff still agree.
Phase110 receipt fields alone name that lineage but do not prove the Phase111
archive is present. Direct reload adds that property; no provider HTTP, response
body copy, or second HTML identity extraction is required. Any target/cutoff
argument is an expected equality constraint, never a self-authorizing input.

`PHASE110_COMPLETE_IDENTITY_PERSISTENCE != PHASE109_MAPPING_AUTHORITY`.
`PERSISTED_RELATION != PROVENANCE_OF_RELATION`.
`V010_MAPPING_ROW_EXISTENCE != INDEPENDENT_PRODUCTION_MAPPING_AUTHORITY`.
`CURRENT_DB_MAPPING_EXISTENCE != HISTORICAL_MAPPING_AVAILABILITY_PROOF`.
`PHASE109_MUST_NOT_CREATE_PROVIDER_REQUEST`.
`PHASE109_MUST_NOT_REEXTRACT_PROVIDER_HTML_IF_PHASE110_RECEIPT_IS_SUFFICIENT`.

### Complete relation and chosen V010 Model B

The canonical relation is exactly one `external_race_id <-> races.id` and the
complete ordered set `external_entry_id <-> horses.id` for that parent. Require
set equality to the Phase110 receipt, forward and reverse uniqueness, same
horse-number/parent membership, no extra or missing entry, no fuzzy/name/position
matching, and no internal-ID issuance. Denied, cancelled, excluded, and otherwise
nonselected identities remain mapped without any status interpretation.

Choose **Model B**: Phase109's controlled publisher may reconcile/populate missing
V010 `historical_input_source_identities`,
`historical_input_external_races`, and `historical_input_external_entries`
from *only* the exact Phase110 population, then publish an independent immutable
Phase109 authority receipt in the **same main SQLite transaction**. Existing
snapshot repository `save_snapshot() -> _ensure_mappings()` and the JRA replay
seed repository can already write V010. Therefore V010 cannot be origin evidence.
Exact matching pre-existing V010 rows may be adopted as consistency data, never
as proof of origin; missing rows may be inserted only by the Phase109 publisher;
conflicting, reverse-colliding, extra, or malformed rows fail closed with no
repair. A snapshot-created exact row does not launder authority: only the new
receipt issued after Phase110/Phase111 verification is authoritative. A
snapshot-created *incomplete* V010 set may be completed atomically from Phase110,
but an extra entry blocks publication. V010 may not remain wholly read-only if
downstream snapshot compatibility needs the complete production relation.

`SNAPSHOT_CREATED_V010_ROW != PHASE109_ORIGIN_AUTHORITY`.
`ENTRY_IDENTITY_UNIVERSE != ENTRY_STATUS_AUTHORITY`.
`IDENTITY_ONLY_DENIED_ENTRY != UNMAPPABLE_ENTRY`.
`MAPPED_ENTRY != ACTIVE_ENTRY`.
`MAPPED_ENTRY != PREDICTION_ELIGIBLE_ENTRY`.
`MAPPED_ENTRY != MARKET_ELIGIBLE_ENTRY`.
`MAPPING_AUTHORITY != ENTRY_STATUS_AUTHORITY`.
`MAPPING_AUTHORITY != MARKET_ELIGIBILITY`.
`MAPPING_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.
`MAPPING_AUTHORITY != PREDICTION_SELECTION_AUTHORITY`.

### Approved V019 and publication transaction

`PHASE109_V019_REQUIRED`. V010 has relational rows but
no Phase110-origin or complete-population authority receipt. Proposed V019 is
additive: `nar_production_mapping_receipts` (content ID, schema/version,
NAR/nar_official, external/internal race, Phase110 receipt ID/count/digest,
Phase111 declaration/receipt/capture IDs and response digest, observed/cutoff,
canonical ordered mapping JSON/count/digest, `issued_at`) and
`nar_production_mapping_entries` (receipt ID, external entry ID, internal
`horses.id`, horse number, optional external horse ID, exact Phase110-entry
reference). Unique forward/reverse keys, parent/entry FKs to Phase110 and V010,
immutable row triggers, an exact V019 schema gate, and V010 update/delete/extra
insert guards for Phase109-bound NAR mappings are required. The JSON and entry
table must be exact projections of each other; neither may be a second source of
truth. No response body or new internal ID is stored. V019 must reject partial or
contradictory topology, run under migration-runner transaction ownership, and
perform no destructive repair or `INSERT OR REPLACE`.

One idle main-DB SQLite connection with foreign keys enabled acquires
`BEGIN IMMEDIATE`; it exact-reloads Phase110 and compares preflighted Phase111 ancestry, verifies
V018/V019/V010 topology and complete bijection, checks every existing V010 row,
inserts only missing exact V010 rows, verifies no extra V010 row, then publishes
the receipt and all entries. Any failure rolls back V010 and V019 together.
Commit precedes exact receipt reload and qualified return. A crash after commit
is recovered only by exact idempotent reload, never by rewriting. Same Phase110
receipt can return the exact existing authority; a different receipt for the
same external or internal race, a conflicting entry, or a different
republication is rejected. Concurrency is serialized by `BEGIN IMMEDIATE`
plus database uniqueness, not process-local locks.

The Phase111 ancestry preflight is read-only and precedes the main-DB write
transaction: exact-load its controlled receipt, declaration, claim, and capture;
verify their mutual lineage and agreement with Phase110 on declaration/receipt/
capture IDs, external race, canonical URL, response digest, observed time, and
cutoff. It never invokes acquisition, provider HTTP, HorseParser, or another
Deba extraction. Inside `BEGIN IMMEDIATE`, exact-reload Phase110 again before
publication. The exact NAR/nar_official V010 source-identity row may be inserted
transactionally as namespace scaffolding only, never as origin authority.
`HISTORICAL_INPUT_SOURCE_IDENTITY_ROW != PHASE109_ORIGIN_AUTHORITY`.

V019 must install triggers protecting Phase109-covered V010 race/entry rows
from UPDATE/DELETE and rejecting extra covered entry INSERT even when foreign
keys are OFF. Every successful Phase109 reload must independently compare the
exact V010 source/race/entry set, V019 projection, and Phase110 population; drift
fails closed. Its shared schema gate distinguishes `PHASE109_SCHEMA_NOT_INSTALLED`,
`PHASE109_SCHEMA_ACTIVE`, and `PHASE109_SCHEMA_INTEGRITY_FAILURE`; corruption
never becomes absence, while unexpected SQLite operational errors propagate.

### Time, Phase108 handoff, and non-authorities

Phase111 already proves `observed_at <= prediction_information_cutoff`.
Phase109 must preserve that exact cutoff ancestry and require
`Phase110 issued_at <= Phase109 issued_at`. Do **not** require Phase109 issuance
before the prediction cutoff; that stronger rule is not approved. Phase109
authority becomes available at its controlled `issued_at`, never at a
caller-supplied backdated time. After commit, a downstream pre-root component
must exact-reload the Phase109 receipt and record `available_at` no earlier
than that reload; future production integration must prove receipt availability
before manifest availability and manifest availability before Phase108 root start.
Current DB presence, a backdated timestamp, or the root's current Deba capture
cannot prove historical pre-root availability. The future manifest must bind
the exact Phase109 receipt ID/content and target/cutoff before the root starts.

Current `NARPreCPrestagedInputManifestV1` requires a reviewed Git fixture bundle,
fixture-member `mapping_content_authority`, and a mapping literal verified by
`nar_pre_c_operational_envelope_harness.py`. That is a diagnostic V1 fixture
authority, not production mapping. Phase109 changes no Phase108 module. A later
separately reviewed **production prestaged manifest version/adapter** must
exact-reload the Phase109 receipt before root, bind its complete mapping and
availability, and replace (not promote) the V1 fixture proof. A production root
path is deferred; the existing Phase108 rehearsal remains unchanged.

`ROOT_CURRENT_DEBA_CAPTURE != PRE_ROOT_MAPPING_AUTHORITY`.
`POST_C_CAPTURE != PRE_C_IDENTITY_MAPPING_AUTHORITY`.
`MAPPING_LOOKUP_AFTER_ENVELOPE_START != PRESTAGED_MAPPING_AUTHORITY`.
`PHASE109_MAPPING_RECEIPT_MUST_PRECEDE_PHASE108_ROOT_START`.
`PHASE108_V1_FIXTURE_MAPPING != PRODUCTION_MAPPING_AUTHORITY`.
`MAPPING_RECEIPT != PHASE108_ROOT_AUTHORITY`.

### Current reader/writer and V019 regression impact

Required production changes: standard migration registry; new V019 migration;
new Phase109 value/issuance module; new SQLite publication/reload repository.
Existing snapshot repository is a V010 writer from caller snapshots, JRA replay
seed is a separately authorized JRA writer, and V010 is read by the snapshot
repository, NAR daily evidence resolver, and status-replay identity binder.
Those paths are **read-only/forbidden to modify** for Phase109; future production
Phase108 manifest/root integration is **deferred**. Optional convenience adapter
or generic prediction changes are not needed. Phase111, Phase110, Phase95, Phase41,
legacy fetch/parser, database writers, and current Phase108 harness are forbidden.
No existing production reader is promoted to consume Phase109 authority merely
because it can read V010.

Whole-test-tree static scan before scope selection found unrestricted
`apply_migrations(connection)` users in CLI/simulation/JRA/NAR repositories,
Phase108 rehearsal, V010/V015/V016/V018 tests, and their fixtures. V018-compatible
base races/horses shapes are already present for the full-chain fixtures; V019
must add no new base-column prerequisite beyond exact V018/V010. Exact full
registry expectations ending in V018 occur in
`test_historical_input_snapshot_migration.py`,
`test_simulation_bet_plan_migration.py`,
`test_simulation_migrations.py`,
`test_nar_official_response_capture_migration.py`,
`test_sqlite_persisted_simulation_application.py`, and
`test_sqlite_nar_daily_replay_result_repository.py` (including its terminal
version assertion and `MIGRATIONS[-1]` use). Only current/full-registry assertions
may be extended to V019; intentional historical `_through(11/13/15/17)`
tests remain historical. Other unrestricted users are regressions to run, not
preauthorized fixture edits. No blanket test-file permission is inferred.

### Allowed Files

This is the exact approved 16-path implementation scope, including the later
one-file historical-prefix test extension. The prior 15-path stop remains
recorded above.

NEW FILES:
- `scripts/migrations/versions/v019_nar_production_mapping_authority_schema.py`
- `scripts/simulation/nar_production_mapping_authority.py`
- `scripts/simulation/repositories/sqlite_nar_production_mapping_repository.py`

MODIFIED FILES:
- `scripts/migrations/runner.py`

TEST FILES (new):
- `tests/test_v019_nar_production_mapping_authority_schema.py`
- `tests/test_nar_production_mapping_authority.py`
- `tests/test_sqlite_nar_production_mapping_repository.py`

TEST FILES (existing, exact current-registry expectations only):
- `tests/test_historical_input_snapshot_migration.py`
- `tests/test_simulation_bet_plan_migration.py`
- `tests/test_simulation_migrations.py`
- `tests/test_nar_official_response_capture_migration.py`
- `tests/test_sqlite_persisted_simulation_application.py`
- `tests/test_sqlite_nar_daily_replay_result_repository.py`
- `tests/test_v018_nar_identity_complete_entry_schema.py` (the `through_v017`
  helper only; explicit `VERSION <= 17`, with assertions preserved)

DOCUMENTATION FILES:
- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

### Forbidden Files

Every path not listed in Allowed Files is forbidden, notably Phase111/110 authority,
V010/V018 migration sources, existing snapshot/JRA/NAR evidence repositories,
Phase108 fixture/manifest/root/harness, Phase95/41, generic prediction, provider,
fetcher/parser, `database/**`, `logs/**`, and unrelated existing tests.
The six existing test files may change only for actual V019 current-registry or
topology compatibility; historical-prefix assertions must remain historical.

### Required Tests

Focused tests must prove: (1) exact Phase110 receipt mandatory and
missing/corrupt V018 rejected; (2) caller/forged mapping cannot authorize;
(3) direct Phase111 reload catches declaration/receipt/capture/digest/target/cutoff
contradiction without refetch or HTML re-extraction; (4) full Phase110 population
equality including cancelled/denied identities; (5) forward/reverse uniqueness,
parent membership, horse-number agreement and no synthesized IDs; (6) snapshot
V010 rows alone never authorize; (7) exact existing V010 rows are consistency
only, missing rows inserted exactly, extra/conflicting rows fail; (8) deterministic
content ID, canonical ordering/count/digest, exact JSON/table projection and
reload; (9) exact repeat idempotence and conflicting repeat/race/entry rejection;
(10) rollback after partial V010/V019 publication and two-connection concurrent
publisher exclusion; (11) Phase111 observed-at cutoff, Phase110-issued-at <=
Phase109-issued-at, and rejection of backdated publication; (12) post-commit reload before
downstream availability; (13) V019 clean migration, exact topology, partial-schema
and migration rollback; (14) V010/current-registry regressions and historical
prefix preservation; (15) no Phase108 fixture promotion, status/eligibility
interpretation, denial clearing, provider HTTP, production DB, or ID issuance;
(16) related regressions and full repository pytest. Use temporary/in-memory DBs
and deterministic fakes only.

Direct coverage must additionally prove Phase111 declaration/claim/capture exact
reload; no HTML re-extraction; race and entry forward/reverse uniqueness;
cross-race and horse-number-only rejection; transactional source-identity handling;
V019 and covered V010 UPDATE/DELETE prevention, covered extra-entry INSERT
prevention with foreign keys OFF; genuine post-write rollback leaving no partial
V010 or V019 rows; same-exact publication idempotence; no Phase110 denial
mutation; absent/active/corrupt V019 classification; unexpected SQLite locking
error propagation; V010 snapshot repository compatibility; and no new internal
race/entry IDs. Run the focused V019 tests, the exact related regression modules
specified in the implementation instruction (including Phase111/110, V010,
migration and Phase108 tests), then full `python -m pytest -q --tb=short` under
the existing sealed-commit environment requirement. Finish with static audit,
`git diff --check`, exact 16-path audit, and empty-index check.

### Stop Condition

STOP rather than broaden implementation if Phase110 or Phase111 exact reload is
insufficient, the mapping is incomplete/non-bijective, status/eligibility or
provider HTTP is needed, a second provider Deba load or HTML re-extraction is
needed, production DB inspection is needed, Phase108 fixture authority must be
promoted, V010 must be origin evidence, V010/V019 cannot publish atomically,
arbitrary caller mapping can enter the authority path, destructive repair or
new `races.id`/`horses.id` is needed, the scope cannot remain bounded, or any
failing regression needs a 17th path. Preserve existing work and return the
exact failure/path for scope review; do not stage, commit, or push.

Next: `WAITING_FOR_PHASE_INSTRUCTION`.

---

## Historical record — POST_V0_8_DAILY_REPLAY_110

Title: NAR Identity-Complete Entry Persistence

Status: `WAITING_FOR_PHASE_INSTRUCTION`

Formal Status: `FORMALLY_COMPLETE`

State: `FORMALLY_COMPLETE`

Outcome: `PHASE110_NAR_IDENTITY_COMPLETE_ENTRY_PERSISTENCE_FORMALLY_INTEGRATED`

Independent implementation review: `CHATGPT_REVIEW_PHASE110_IMPLEMENTATION = PASS`.
`PHASE110_IMPLEMENTATION_REVIEW_PASS`.
`PHASE110_COMMIT_APPROVED`.
`PHASE110_POST_COMMIT_VERIFICATION_PASS`.
`PHASE110_REMOTE_IMPLEMENTATION_VERIFICATION_PASS`.
`PHASE110_IMPLEMENTATION_REMOTE_ACCEPTED`.
`PHASE110_FORMAL_CLOSURE_APPROVED`.
`PHASE110_FORMAL_CLOSURE_REMOTE_VERIFICATION_PASS`.
`PHASE110_FINAL_DOCUMENTATION_REMOTE_VERIFICATION_PASS`.
`POST_V0_8_DAILY_REPLAY_110 = FORMALLY_COMPLETE`.
The first independent review returned `CHANGES_REQUIRED`; its four findings were
repaired and independently re-reviewed within the approved 38-path scope. The
implementation commit was then independently post-commit verified, pushed without
force, and independently verified on the GitHub remote branch before formal closure.

Implementation Commit: `9500a7d4d4bbb0b9cc5e20df1a8dcce8921c2f75`

Implementation Tree: `1b9b1c5cdee549f31879b20af8cd077b58b1f38b`

Implementation Parent: `48dcc0a359a9b48b7f32fbe3fef846db1da31009`

Formal Closure Commit: `4e9f5b0081764cbd51460050b2d3d1bf87434dfd`

Formal Closure Tree: `48e61f3fa2a7f0b8ea73118f467a1990f6e03215`

Formal Closure Parent: `9500a7d4d4bbb0b9cc5e20df1a8dcce8921c2f75`

The closure commit was pushed without force. Independent GitHub verification found
the remote branch at that exact commit/tree, with the implementation commit as its
parent and exactly `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md` changed.

Review disposition: `PHASE110_REVISED_ARCHITECTURAL_REVIEW_PASS`.

`PHASE110_IMPLEMENTATION_DESIGN_APPROVED`.
`PHASE110_IMPLEMENTATION_READY`.
`PHASE110_IMPLEMENTATION_APPROVAL = GRANTED`.
`PHASE110_DESIGN_APPROVED_FOR_CODEX`.
`PHASE110_IMPLEMENTATION_SCOPE_CORRECTION_APPROVED`.
`PHASE110_REQUIRED_MIGRATION_REGRESSION_FILES_ADDED_TO_ALLOWED_SET`.
`PHASE110_FINAL_TEST_SCOPE_APPROVED`.
`PHASE110_V018_REGRESSION_IMPACT_AUDIT_APPROVED`.
`PHASE110_ALLOWED_FILES = 35_PATH_FINAL_SCOPE`.
`PHASE110_IMPLEMENTATION_RESUME_APPROVED`.
`PHASE110_V018_REPOSITORY_COMPATIBILITY_SCOPE_APPROVED`.
`PHASE110_ALLOWED_FILES = 36_PATH_SCOPE`.
`PHASE110_PHASE108_HARNESS_V018_COMPATIBILITY_SCOPE_APPROVED`.
`PHASE110_ALLOWED_FILES = 37_PATH_SCOPE`.
`PHASE110_FINAL_FIXTURE_COMPATIBILITY_SCOPE_APPROVED`.
`PHASE110_ALLOWED_FILES = 38_PATH_SCOPE`.
`PHASE110_IMPLEMENTATION_REPAIR_VERIFIED_FOR_REVIEW`.
`PHASE110_IMPLEMENTATION_READY_FOR_CHATGPT_REVIEW`.
`PHASE110_IMPLEMENTATION_TESTS_PASS`.
`PHASE110_IMPLEMENTATION_STATIC_AUDIT_PASS`.

Base Commit: `48dcc0a359a9b48b7f32fbe3fef846db1da31009`

Base Tree: `67bf7387f189ba6ce40d6578aeaa7b5ccfdad79f`

Branch: `feature/post-v0.8-daily-replay`

Phase111 predecessor: `POST_V0_8_DAILY_REPLAY_111 = FORMALLY_COMPLETE`;
`PHASE111_FINAL_DOCUMENTATION_REMOTE_VERIFICATION_PASS`.

Phase111's trusted single-send Deba acquisition prerequisite is satisfied. Phase110
is formally complete within the approved 38-path scope. Its implementation commit
and tree were independently verified on the remote branch. The docs-only closure
commit was also pushed and independently verified remotely. Phase110 waits for the
next phase instruction and grants no Phase109 mapping, Phase95 status, Phase41
market, Phase108 root, live-campaign, or
Operational Delta authority. Provider HTTP, production DB access, and KeibaAI
changes remain zero.

### Objective and frozen authority boundaries

Design a status-independent identity universe from only the exact bytes exposed by a
Phase111 qualified result. Preserve every structurally identity-bearing NAR Deba row,
including cancelled, withdrawn, excluded, and otherwise nonselected rows. Identity
existence does not interpret status and does not create prediction/betting eligibility.

Retain:

`IDENTITY_PERSISTENCE_AUTHORITY != ENTRY_STATUS_AUTHORITY`.
`IDENTITY_PERSISTENCE_AUTHORITY != MARKET_ELIGIBILITY`.
`IDENTITY_PERSISTENCE_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.
`IDENTITY_COMPLETE_POPULATION != PREDICTION_ELIGIBLE_POPULATION`.
`PERSISTED_ENTRY != SELECTABLE_ENTRY`.
`STATUS_FILTERED_HORSE_ROWS != COMPLETE_NAR_ENTRY_IDENTITY_UNIVERSE`.
`CANCELLED_ENTRY != NONEXISTENT_ENTRY_IDENTITY`.
`ENTRY_STATUS_INTERPRETATION != ENTRY_IDENTITY_BINDING`.
`OMITTED_CANCELLED_HORSE_ROW != AUTHORIZED_MAPPING_ABSENCE`.
`HORSES_TABLE_POPULATION != COMPLETE_MAPPING_POPULATION_UNLESS_PROVEN`.
`IDENTITY_ONLY_ENTRY != ACTIVE_ENTRY`.
`IDENTITY_ONLY_ENTRY != PREDICTION_ELIGIBLE_ENTRY`.
`LOCAL_RACE_NATURAL_KEY_UNIQUENESS != EXTERNAL_RACE_BINDING_AUTHORITY`.
`PLACE_TEXT != NAR_BABA_CODE_AUTHORITY`.
`V010_RACE_MAPPING_ROW != PHASE110_PARENT_BINDING_AUTHORITY`.
`PHASE110_PARENT_RACE_MUST_PREEXIST`.
`PHASE110_PARENT_BINDING_REQUIRES_EXACT_PHASE111_DEBA_ANCESTRY`.
`SAVE_RACE_ATOMICITY != PHASE110_PARENT_RACE_AUTHORITY`.
`V018_ABSENT != V018_CORRUPT`.
`V018_CORRUPT_MUST_NOT_FALL_BACK_TO_LEGACY_SELECTION`.
`LEGACY_COMPATIBILITY_REQUIRES_PROVEN_PHASE110_SCHEMA_ABSENCE`.
`DENIED_ENTRY_EXCLUDED_FROM_ROWS != DENIED_ENTRY_EXCLUDED_FROM_EFFECTIVE_PREDICTION_POPULATION`.
`PHASE110_NEW_INTERNAL_ENTRY_ID => PHASE110_SELECTION_DENIED`.
`PHASE110_SELECTION_DENIAL != NULL_ENRICHMENT_STATE`.
`ENRICHMENT_COMPLETION != SELECTION_AUTHORITY`.
`PHASE110_ISSUED_ENTRY_REMAINS_DENIED_AFTER_ENRICHMENT`.
`LEGACY_ENRICHMENT_MATCH != IDENTITY_ADOPTION_AUTHORITY`.
`LEGACY_ENRICHMENT_MAY_UPDATE_NONIDENTITY_FIELDS_ONLY`.
`PHASE110_ID_ISSUANCE_AND_PROVENANCE_MUST_SHARE_ONE_TRANSACTION`.
`DERIVED_NAR_ENTRY_IDENTITY != PROVIDER_ISSUED_ENTRY_IDENTIFIER`.
`IDENTITY_PERSISTENCE_PRECEDES_ENRICHMENT_WITHOUT_IDENTITY_REPLACEMENT`.
`IDENTITY_ONLY_DENIAL_MUST_BE_DURABLE_NOT_INFERRED`.
`IDENTITY_EXTRACTION != STATUS_INTERPRETATION`.
`PHASE110_IMPLEMENTATION != PHASE95_STATUS_AUTHORITY`.
`PHASE109_PRODUCTION_ENTRY_MAPPING_BLOCKED_BY_IDENTITY_COMPLETE_INGESTION`.
`PHASE109_MAPPING_AUTHORITY_REQUIRES_STATUS_INDEPENDENT_ENTRY_IDENTITY_PERSISTENCE`.
`PHASE110_COMPLETE_IDENTITY_PERSISTENCE != PHASE109_MAPPING_AUTHORITY`.
`GENERIC_WRITER_CHECK_AND_WRITE_MUST_SHARE_ONE_SQLITE_WRITE_TRANSACTION`.
`APPLICATION_LEVEL_CHECK_THEN_INSERT != ATOMIC_IDENTITY_AUTHORITY`.
`PHASE110_MUST_NOT_RACE_UNREVIEWED_LEGACY_WRITER`.

### Approved implementation boundary

Phase110 implements only complete identity persistence from Phase111's read-only,
same-byte qualified result: exact existing parent adoption; existing `horses.id`
namespace reuse; SQLite-generated missing-entry IDs; immutable Phase111-to-Phase110
provenance/receipt; durable denial for Phase110-issued IDs; controlled in-place legacy
enrichment; and negative database-backed prediction/bet gates. It does not establish
ACTIVE/CANCELLED authority, Phase95 status semantics, Phase41 market eligibility,
Phase109 mapping authority, live campaign authorization, operational Delta, or complete
production betting readiness.

`save_race()` and `save_horse()` must perform lookup plus insertion/adoption or permitted
enrichment through one SQLite connection under `BEGIN IMMEDIATE`; public compatibility
helpers may remain, but cannot supply this safety proof. V018 must preflight duplicates
before enforcing the reviewed natural-key uniqueness. A conflict raises and leaves no
V018 registration, partial Phase110 object, or partial unique index: it is never
selected, deleted, merged, renumbered, updated, or silently repaired.

### Repository authority inventory

| Area | Committed evidence | Finding / Phase110 consequence |
| --- | --- | --- |
| `races.id` origin | `scripts/database.py`: `races.id INTEGER PRIMARY KEY AUTOINCREMENT`; `save_race()` checks `race_exists()` then inserts on another connection. `scripts/parsers/nar_parser.py` retains a Deba URL from the RaceList title link. `scripts/simulation/repositories/sqlite_jra_race_replay_seed_repository.py` is another race writer, protected by its own `BEGIN IMMEDIATE` transaction and JRA seed proof. | `races.id` is a local surrogate race key, not provider identity. `(race_date, organization, place, race_no)` is only a local natural/concurrency key: `LOCAL_RACE_NATURAL_KEY_UNIQUENESS != EXTERNAL_RACE_BINDING_AUTHORITY`; `PLACE_TEXT != NAR_BABA_CODE_AUTHORITY`. Phase110 never issues `races.id`; the parent must preexist. Adoption requires exactly one natural-key candidate, NAR organization, exact date/race number, nonempty stored Deba URL canonicalized with the existing reviewed NAR URL semantics, exact equality to the Phase111 declaration/receipt/result canonical URL, and agreement of date/babaCode/raceNo parsed from that URL with the Phase111 external race identity. Missing/duplicate natural-key candidates, URL-less, noncanonical, or contradictory ancestry stops. V010 is not a substitute: `V010_RACE_MAPPING_ROW != PHASE110_PARENT_BINDING_AUTHORITY`. `SAVE_RACE_ATOMICITY != PHASE110_PARENT_RACE_AUTHORITY`. |
| Race uniqueness / concurrency | Legacy `races` has no unique natural-key constraint. `save_race()` performs its existence read and insert in distinct transactions. JRA seed inserts races directly under `BEGIN IMMEDIATE`. | Proposed additive migration may add a unique partial index over populated `(race_date, organization, place, race_no)` values after duplicate preflight, and narrow `save_race()` check/insert serialization may be considered for compatibility. This only prevents local duplicate races; it does not authorize external binding. Existing conflicts are not merged/deleted; migration fails closed. Phase110 parent authority always requires exact Phase111 Deba ancestry. |
| `horses.id` origin / meaning | `scripts/database.py` defines `horses.id INTEGER PRIMARY KEY AUTOINCREMENT`; `race_id` scopes it. `get_horse_id()` queries `(race_id, horse_no)`. `PastRace.horse_id`, prediction `horse_id`, V008/V009 `race_entry_id`, V010 and the Phase88 binder use `horses.id`. | In this architecture `horses.id` is effectively a per-race entry identity, not a global biological horse identity. Keep that existing ID namespace so downstream foreign keys and Phase109 can use it; do not create a second incompatible ID namespace or synthesize IDs. `horse_no` is only race-local. |
| Existing entry writers / constraints | Legacy `save_horse()` calls `horse_exists()` on one connection and inserts on another. Base `horses` has no unique `(race_id, horse_no)` constraint. V010 supplies unique `(race_id,id)`, not race/number uniqueness. The JRA seed repository inserts minimal `horses(race_id,horse_no)` rows and binds them under an atomic JRA-specific seed; that is not NAR Phase110 origin. | Current legacy writer is not safe to race with Phase110. Add a migration-time unique partial index for populated `(race_id,horse_no)` keys, and make legacy save/create paths acquire one `BEGIN IMMEDIATE` before read/check/write. The Phase110 repository also uses one `BEGIN IMMEDIATE` for exact parent adoption, all entry allocations, origin/denial records, and receipt. The Phase110 repository—not generic `save_horse()`—inserts a missing ID and its origin/provenance/denial in one transaction. No process-local lock or likely-serial assumption. |
| Legacy NAR parser | `scripts/parsers/horse_parser.py` advances over rows with `horseNum`, but `_is_cancelled()` skips rows containing cancellation/exclusion markers. `_parse_horse_block()` can return `None` and requires a nonempty horse name; optional fields default to zero/empty values. | It cannot define identity completeness and must remain unchanged. Phase110 runs the unchanged parser on the same qualified bytes only to obtain optional legacy enrichment for rows it already parses. A separate identity-only extractor enumerates the complete structural row set without reading status/odds/jockey/trainer/weight. No parser defaults are used to manufacture identity. |
| Existing identity extraction candidates | `scripts/simulation/nar_historical_input_source.py` derives `external_entry_id = external_race_id + ':entry:' + horse_no` and canonical provider horse URLs, but its historical normalizer rejects cancellation markers and requires odds/jockey. Phase88's `_extract_source_entries()` uses the identity-bearing DOM primitives but freezes one fixture, one target, a 1..14 population, and fixed hashes. | Neither is a generic production extractor. Phase110 adds a generic extractor over Phase111 bytes, reusing only the reviewed low-level row selection and canonical horse-URL rules where compatible. It derives all rows from the exact supplied capture, has no frozen target/count/hash, and fails closed on malformed or duplicate identity structure. It does not import historical status semantics. |
| Production prediction/read paths | `scripts/database.py:get_horses_by_race()` selects every horse row for a race. `scripts/cli/run_prediction.py:DatabaseRaceInputProvider.load()` places every returned row into `RacePredictionInput` and sets `race_horse_count = race.horse_count or len(horses)`; that count reaches `BetGenerator` and affects bet-type branches. `scripts/simulation/repositories/sqlite_race_entry_source.py` directly maps requested IDs from `horses` without a nonselection check; it feeds `RepositoryBackedRaceEntrySelectionResolver` / `SimulationBetPlanBuilder`. | These are the two discovered DB-backed candidate/selection boundaries. Row filtering alone is insufficient: when Phase110 denials exist, effective prediction/bet population count must be computed from post-gate candidate rows and must not use nominal persisted `races.horse_count` to expose a bet type. A narrow `run_prediction.py` change is required, but generic pipeline/predictor/strategy/value/bet-generator modules remain forbidden. Schema-absent compatibility may retain legacy count behavior only after the shared validator proves V018 is genuinely absent and no Phase110 objects exist. |
| Other pipeline paths | `PredictionPipeline`, `BetGenerator`, and `BetStrategy` consume caller-supplied in-memory `RacePredictionInput`; persisted simulation request assembly also consumes a caller-authored request document rather than querying `horses`. | Phase110 must never feed the identity-complete universe into those inputs. These pure input APIs do not read the Phase110 registry and cannot infer persisted-row denial. Future composition that derives such inputs from Phase110 IDs must use an approved eligibility/status source; Phase95/41 remain blockers. No pipeline responsibility boundary is changed in Phase110. |
| Existing mapping schemas | V010 external race/entry rows are used by snapshot save paths and can be snapshot-derived. V015's JRA seed schema has a distinct JRA provenance/seed contract. | `PERSISTED_RELATION != PROVENANCE_OF_RELATION`; `V010_MAPPING_ROW_EXISTENCE != INDEPENDENT_PRODUCTION_MAPPING_AUTHORITY`. Phase110 adds its own append-only NAR identity-origin evidence. It neither writes V010 nor converts V010/JRA rows into NAR authority. |

No production database was queried. Existing duplicates in the deployed data are unknown; the future migration must detect conflicts and abort without cleanup or silent repair.

### Answers to required implementation questions

1. **Where extraction occurs.** A new pure `nar_identity_complete_entry_source.py` receives bytes returned by `read_qualified_deba_bytes(result=..., lineage_archive=..., capture_archive=...)`. It requires the exact Phase111 result/receipt and uses its external race identity. It strictly UTF-8 decodes the exact archive bytes. A generic row walk uses the reviewed Deba entry-table structure, collects every direct identity-bearing row, and never examines cancellation/status, odds, jockey, trainer, popularity, or weight.
2. **How cancelled/excluded identities remain.** `horse_no` plus the exact parent external race yields derived `external_entry_id = <external_race_id>:entry:<canonical horse_no>`. Versioned algorithm `nar-entry-v1` concatenates the exact canonical Phase111 external race ID, literal `:entry:`, and the canonical ASCII decimal horse-number token matching `[1-9][0-9]*` (no sign, whitespace, zero, or leading zero). This is derived, not provider-issued: `DERIVED_NAR_ENTRY_IDENTITY != PROVIDER_ISSUED_ENTRY_IDENTIFIER`. The complete sorted set is built from every source row, including status-marked rows. Duplicate/malformed/zero/ambiguous horse numbers or ambiguous/missing row structure fail the whole extraction; no subset is silently accepted. A canonical horse-detail identity is recorded when exposed and remains optional if absent. It is not used to infer status.
3. **Who issues an internal entry ID.** Only the Phase110 persistence application/repository, after validating Phase111 receipt and exact existing race parent. For genuinely absent `(race_id, horse_no)` it inserts one minimal identity-only row into the existing `horses` ID namespace and obtains SQLite's `lastrowid`; no enumeration/hash/external ID is used as an internal ID. Existing exact rows are adopted only after exact parent and canonical provider-horse identity agreement. Horse-number-only adoption is forbidden.
4. **Atomicity/concurrency.** New migration `v018_nar_identity_complete_entry_schema` adds uniqueness for populated legacy race/number keys and Phase110 binding/origin tables. An all-or-nothing `BEGIN IMMEDIATE` transaction validates the complete population, exact parent, existing-row matches, allocates missing `horses.id` values, records every origin/denial binding, and publishes the immutable receipt. The unique index is the final defense against all writers; transaction locking serializes Phase110 against the repaired legacy writers and the already-transactional JRA seed writer. There is no row/receipt separation after crash.
5. **Legacy writer coexistence.** `scripts/database.py:save_horse()` is changed narrowly to perform check and insert/update inside one `BEGIN IMMEDIATE` transaction. It receives no Phase111 identity authority. On an exact `(race_id, horse_no)` collision with a Phase110-issued row, it may update reviewed nonidentity enrichment columns only; it must not replace `horses.id`, change race membership or horse number, alter Phase110 external identity/provenance, or clear denial. Canonical horse-detail identity is checked against companion evidence where available; mismatch fails closed. `LEGACY_ENRICHMENT_MATCH != IDENTITY_ADOPTION_AUTHORITY` and `LEGACY_ENRICHMENT_MAY_UPDATE_NONIDENTITY_FIELDS_ONLY`.
6. **Later enrichment.** A Phase110-issued ID is durably selection-denied even if the same Phase111 bytes also allow unchanged `HorseParser` to provide immediate enrichment. Later `save_horse()` enrichment stays on the same `horses.id`; it cannot mutate identity, provenance, or denial. `PHASE110_NEW_INTERNAL_ENTRY_ID => PHASE110_SELECTION_DENIED`; denial is not a null-field state, enrichment completion is not selection authority, and only a separately reviewed authority may supersede denial. `PHASE110_ISSUED_ENTRY_REMAINS_DENIED_AFTER_ENRICHMENT`.
7. **Durable nonselection.** The companion model distinguishes an exact pre-existing/adopted legacy entry from a Phase110-issued entry. Every newly issued ID is explicitly marked `IDENTITY_ONLY_DENIED` (or an exactly equivalent fixed negative marker), even when optional enrichment is available immediately. This denial attaches to issuance, not to missing/null enrichment fields, and cannot be cleared by `save_horse()` or enrichment completion. It is never inferred from NULL/zero fields, name, cancellation text, or past-race count. Only a different, separately reviewed eligibility authority could supersede it; Phase110 cannot grant positive selection permission.
8. **Readers.** One exact V018 schema-state validator is shared by `database.get_horses_by_race()` / relevant database helpers and `SQLiteRaceEntrySource`. It yields exactly: (A) `PHASE110_SCHEMA_NOT_INSTALLED` only when V018 registration is absent and no reserved Phase110 objects exist; legacy behavior is allowed only in this proven-absence compatibility mode. (B) `PHASE110_SCHEMA_ACTIVE` only when V018 is registered and every required table/index/constraint matches the reviewed topology; all denial gates are mandatory. (C) `PHASE110_SCHEMA_INTEGRITY_FAILURE` for any partial or contradictory state, including registered-but-missing objects, unregistered Phase110 objects, or wrong columns/keys/indexes/constraints; every reader fails closed and never falls back. Missing-table errors are not swallowed. `V018_ABSENT != V018_CORRUPT`; `V018_CORRUPT_MUST_NOT_FALL_BACK_TO_LEGACY_SELECTION`; `LEGACY_COMPATIBILITY_REQUIRES_PROVEN_PHASE110_SCHEMA_ABSENCE`. `get_horses_by_race()` excludes denied rows, while the CLI derives effective `race_horse_count` from post-gate candidate rows whenever active Phase110 denial rows exist. `SQLiteRaceEntrySource.load_race_entry_id_map()` rejects a requested identity-only ID. Historical artifact reads remain intact; pure pipeline/request-document APIs do not query `horses` and Phase110 never supplies identity-only candidates to them.
9. **No additional provider send.** Phase110 accepts an already qualified Phase111 result and calls only its read-only archive byte accessor. The Phase110 source/application has no capture service, transport, provider, or `fetch_deba_table()` dependency. The same returned bytes feed strict decode/HorseParser enrichment and the identity extractor. Tests inject offline archives and assert zero transport calls; code must not call Phase111 `acquire()`.
10. **Phase109 evidence.** Phase110 stores immutable receipt/entry bindings with organization/source system, canonical external race and entry IDs, internal `race_id`/`race_entry_id`, horse number, canonical external horse ID where observed, Phase111 declaration/receipt/capture IDs, exact Deba response digest, observation time/cutoff, source schema/version, complete population digest/count, and issuance disposition. Phase109 later exact-reloads Phase111 ancestry and Phase110 receipt and verifies both forward/reverse uniqueness and full entry-set equality. No V010 shortcut is permitted.

### Proposed authority, persistence, and transaction contract

| Option | Decision | Reason |
| --- | --- | --- |
| Put all identities directly into legacy `horses` and rely on nullable/default fields | Reject as a complete design. The row alone cannot preserve Phase111 provenance or durable negative selection authority, and current readers pass every row to prediction. It also leaves the uniqueness race open. |
| Allocate Phase110 IDs in a separate identity-only table/namespace | Reject. Phase109 and existing result/plan foreign keys require the same internal `horses.id`/race-entry ID basis; a parallel ID namespace would require a second unreviewed mapping. |
| Change `HorseParser` to include every cancellation row as a normal `Horse` | Reject. It couples identity existence to legacy enrichment/status behavior and risks default values entering prediction. Phase111 bytes instead feed a separate status-independent extractor plus unchanged optional parser enrichment. |
| Add a provenance/denial companion registry while retaining `horses.id`, with unique natural keys and atomic legacy-writer compatibility | Recommend for review. It preserves the established ID namespace, makes origin and identity-only denial durable, permits exact adoption/enrichment in place, and can fail closed on legacy collisions without inventing IDs. |

Input causal chain:

`Phase111 qualified result -> exact archive byte reload -> strict UTF-8 -> complete status-independent identity extraction + unchanged optional HorseParser enrichment -> exact canonical parent-race adoption -> exact existing-entry adoption or controlled missing horses.id issuance -> immutable Phase110 provenance/denial rows + receipt -> exact reload`.

The parent race must already exist; Phase110 cannot issue `races.id`. The local `(race_date, organization, place, race_no)` key is only a candidate/concurrency key, never external authority. Phase110 requires exactly one candidate, `organization=NAR`, exact date and race number, a nonempty stored `deba_table_url`, canonicalization through the existing reviewed NAR URL semantics, exact equality with the Phase111 declaration/receipt/result canonical URL, and exact date/babaCode/raceNo agreement between that URL and the Phase111 external race identity. Missing or duplicate candidate, URL-less/noncanonical value, wrong host/page, or contradiction stops. Place text is not baba-code evidence; no V010 row can replace this contract. Atomic `save_race()` is compatibility hardening only, not Phase110 parent authority.

For each captured entry, exact existing `horses` candidates are scoped to that exact parent plus horse number. More than one is ambiguous. Adoption requires the row's canonical `horse_detail_url` to equal the captured canonical provider-horse identity whenever that identity is present; a missing/malformed URL cannot be adopted by horse number. If a row is absent, create an identity-only row only when the complete exact parent/entry identity is valid and the unique key is free. If the row exists but identity cannot be proved, stop rather than issue a second ID.

The immutable companion receipt binds Phase111 declaration/receipt/capture IDs, external race/entry/horse identities, internal IDs, canonical parent ancestry, source digest/observed_at/cutoff, complete canonical ordered population and its digest, schema version and issuance time. The companion registry is append-only/restrictive. Same exact receipt replay may be idempotent; conflicting content or ancestry is rejected. No response body is copied from the Phase111 archive. Cross-archive lineage is stored as exact identities/digests and revalidated via Phase111 read APIs; no cross-database foreign key is assumed.

Migration `v018` is additive and registered in `scripts/migrations/runner.py`. It validates the exact prior v017 registry, creates restrictive append-only race/entry/receipt provenance tables, and adds unique populated legacy-key indexes. Before index creation it detects duplicate `(race_date, organization, place, race_no)` and `(race_id, horse_no)` groups and aborts with bounded classification; it never merges, deletes, renumbers, or repairs existing rows. Migration is explicit; constructors/readers never install it implicitly. One exact shared schema-state validator is used by database helper reads and `SQLiteRaceEntrySource`, distinguishing proven V018 absence from exact activation and integrity failure. Runtime Phase110 writer requires exact V018 topology; it does not use V010 as parent authority.

`save_race()` and `save_horse()` must put key lookup plus write in one SQLite `BEGIN IMMEDIATE` transaction where approved compatibility changes apply. Unique indexes close races against direct writers and concurrent connections; race-key uniqueness is not parent authority. For a newly issued entry, the Phase110 repository itself inserts the SQLite-generated `horses.id` and, in that same transaction, writes external identity, Phase111 ancestry, explicit selection denial, complete bindings, and immutable receipt. It must not call generic `save_horse()` to issue IDs. Any failure rolls back every newly allocated ID and authority row: `PHASE110_ID_ISSUANCE_AND_PROVENANCE_MUST_SHARE_ONE_TRANSACTION`.

### Approved Allowed Files

The following is the complete authorized Phase110 implementation set. Any additional
path requires a contract amendment and a stop before modification.

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`
- `scripts/migrations/runner.py`
- `scripts/migrations/versions/v018_nar_identity_complete_entry_schema.py`
- `scripts/database.py`
- `scripts/cli/run_prediction.py`
- `scripts/simulation/nar_identity_complete_entry_source.py`
- `scripts/simulation/nar_identity_complete_entry_persistence.py`
- `scripts/simulation/repositories/sqlite_nar_identity_complete_entry_repository.py`
- `scripts/simulation/repositories/sqlite_race_entry_source.py`
- `scripts/simulation/repositories/sqlite_nar_daily_replay_result_repository.py`
- `scripts/simulation/nar_pre_c_operational_envelope_harness.py`
- `tests/test_v018_nar_identity_complete_entry_schema.py`
- `tests/test_nar_identity_complete_entry_source.py`
- `tests/test_nar_identity_complete_entry_persistence.py`
- `tests/test_sqlite_nar_identity_complete_entry_repository.py`
- `tests/test_database_identity_only_entries.py`
- `tests/test_nar_identity_only_prediction_gate.py`
- `tests/test_simulation_migrations.py`
- `tests/test_historical_input_snapshot_migration.py`
- `tests/test_simulation_bet_plan_migration.py`
- `tests/test_nar_official_response_capture_migration.py`
- `tests/test_cli_run_persisted_simulation.py`
- `tests/test_historical_replay_mixed_provider_acceptance.py`
- `tests/test_jra_race_historical_replay.py`
- `tests/test_nar_daily_replay_result_persistence.py`
- `tests/test_nar_pre_c_operational_envelope.py`
- `tests/test_persisted_simulation_integration.py`
- `tests/test_simulation_repositories.py`
- `tests/test_sqlite_historical_input_snapshot_repository.py`
- `tests/test_sqlite_jra_race_replay_seed_repository.py`
- `tests/test_sqlite_nar_daily_evidence_resolver.py`
- `tests/test_sqlite_nar_daily_replay_result_repository.py`
- `tests/test_sqlite_persisted_simulation_application.py`
- `tests/test_sqlite_persisted_simulation_composition.py`
- `tests/test_sqlite_race_entry_source.py`
- `tests/test_sqlite_simulation_bet_plan_snapshot_repository.py`
- `tests/test_persisted_simulation_request_application.py`

The existing regression-test additions are limited to V018 full-migration fixture
compatibility, exact unrestricted registry/schema-object expectations, and the
SQLiteRaceEntrySource schema-validation structural contract. Schema-authority reads
do not count as selection queries; one batched `FROM horses AS h` selection query
remains required. Historical-prefix migration tests retain their historical scope.
No existing assertion may be removed or weakened. This correction does not alter
the approved Phase110 architecture or V018 migration requirements.

The NAR daily replay result repository must compare its complete applied application
migration mapping with the current standard `scripts.migrations.runner.MIGRATIONS`
registry. It retains independent exact V016 and V017 schema checks. Missing, renamed,
and unknown migration registrations fail closed; V018 is not treated as an unknown
future migration merely because V017 was previously the terminal version.

The Phase108 no-network rehearsal harness's synthetic main-DB fixture uses the same
canonical 2026-07-04 NAR race 11 Deba target and the existing 101/102 mapping for
horse numbers 1/2. It supplies V018's required parent columns while retaining the
normal unrestricted application migration runner. This fixture compatibility does
not give Phase110 any Phase108 timing or root authority.

The empty file-backed persisted-request test retains the real application chain and
unrestricted migration runner while declaring V018-compatible empty parent tables.
Other repository fixture tests may insert a parent ID through an explicit `races(id)`
column list; such a test row is not Phase110 external race binding authority.

### Approved Forbidden Files

Every repository path not listed in the Approved Allowed Files is forbidden. In
particular, Phase110 must not modify:

- `scripts/parsers/horse_parser.py`, `scripts/parsers/nar_parser.py`,
  `scripts/providers/nar_provider.py`, `scripts/fetch_local.py`,
  `scripts/fetch_races.py`, or `scripts/models.py`;
- Phase111 transport/capture/declaration/archive modules;
- Phase109 mapping/receipt modules or Phase108 timing/root modules;
- V010 schema/meaning or V015 JRA seed schema/repository;
- Phase95 status, Phase41 market-eligibility, prediction engine/generator/strategy,
  value engine, generic `scripts/prediction/prediction_pipeline.py`, other generic
  prediction modules, or strategy responsibility boundaries;
- `scripts/simulation/repositories/sqlite_bet_plan_snapshot_repository.py` and
  V008/V009/V010/V011/V012/V013/V014/V015/V016/V017 migrations;
- `database/**`, `logs/**`, production database files, and every test not listed in
  Approved Allowed Files.

Existing modules outside the exact Allowed Files may be read/imported through their
existing APIs only; no parser/provider/transport semantics may be altered.

### Required Tests

Add focused offline tests in the approved new modules and require:

1. Phase111 result and exact Phase111 archive reload are mandatory; forged/manual result, receipt or capture cannot authorize persistence.
2. Phase110 performs zero provider/capture-service calls and never invokes legacy `fetch_deba_table()`.
3. Exact same archive bytes are used for strict decode, unchanged HorseParser enrichment and generic identity extraction.
4. Status-like text does not affect row identity; cancelled/withdrawn/excluded fixture rows remain in the complete identity set without status assertions.
5. Odds, popularity, jockey, trainer, weight and positive status are not required for identity existence.
6. Missing/malformed number, duplicate number, ambiguous table/horse link, duplicate canonical horse identity where disallowed, malformed URL, wrong target ancestry, and any silently dropped identity-bearing row fail closed.
7. Entry IDs are exactly `<external_race_id>:entry:<horse_no>`; no enumeration, row index, hash, or synthetic internal-ID derivation occurs.
8. Canonical race URL resolves to exactly one NAR race row; missing, duplicate, wrong URL/date/race number/organization are rejected; approximate place/name matching is never used.
9. Existing entry adoption requires exact parent race, exact horse number under that parent, and canonical provider-horse identity agreement; horse-number-only, wrong-race, missing-URL, and conflicting URL adoption fail.
10. Complete set equality is required; subset, extra internal rows, duplicate external/internal binding, duplicate reverse mapping, and parent mismatch fail closed.
11. SQLite `horses.id` issuance is stable, positive, database-generated and unique; no ID is issued outside the persistence transaction.
12. `v018` migration exact prior-schema gate, deterministic topology, duplicate-key preflight, unique indexes, append-only provenance, foreign keys, and migration rollback on conflict.
13. Concurrent Phase110 issuers cannot allocate two IDs for one `(race_id, horse_no)`; concurrent `save_horse()` / Phase110 / JRA-seed writers cannot create duplicate natural keys.
14. `save_race()` natural-key race is closed by transaction and DB uniqueness; exact Phase110 URL binding remains stricter than legacy lookup.
15. Crash/failure between row insert, origin row, complete binding set, and receipt rolls back the whole Phase110 transaction; no qualified orphan ID remains.
16. Existing exact legacy rows are adopted without ID replacement; unknown-origin/ambiguous rows are not elevated to Phase110 authority.
17. A later `save_horse()` enriches an identity-only row in place only after exact identity match; it does not duplicate/replace the ID or clear the persisted denial marker; mismatch fails closed.
18. Identity-only nonselection uses the explicit durable disposition only, never NULL/zero/name/status/past-race heuristics; enrichment cannot imply ACTIVE or eligibility.
19. `database.get_horses_by_race()` and `DatabaseRaceInputProvider` omit/deny identity-only rows before `RacePredictionInput`; missing/incompatible v018 schema fails closed.
20. `SQLiteRaceEntrySource` rejects direct resolution of identity-only IDs, including requests aimed at bet-plan creation; other saved-artifact reads preserve historical rows.
21. Pure pipeline/input-document APIs are not claimed as DB readers; Phase110 never derives their candidate population from identity-only rows.
22. Phase110 receipt exact reload, deterministic content identity, canonical ordering, complete population count/digest, append-only conflicts, and exact Phase111 ancestry.
23. Phase109-consumable exact forward/reverse fields are available, while V010 row existence is neither read as origin nor written as mapping authority.
24. Phase95 status and Phase41 market eligibility remain unmodified and unasserted.
25. No-network tests use temporary/in-memory SQLite only, make no production DB access/write, no provider HTTP, and leave no changes outside the Approved Allowed Files.
26. A local `(race_date, organization, place, race_no)` match alone cannot authorize parent adoption; exact canonical stored Deba URL equality and Phase111 external-race ancestry are mandatory.
27. Parent adoption rejects absent and duplicate natural-key candidates, wrong organization/date/race number, missing or empty stored Deba URL, noncanonical URL, and URL/external-race/date/babaCode/raceNo contradiction.
28. V018 absent with no Phase110 objects yields `PHASE110_SCHEMA_NOT_INSTALLED` and preserves legacy compatibility; exact V018 yields `PHASE110_SCHEMA_ACTIVE` and enforces denial; registered-but-incomplete, unregistered Phase110 objects, malformed topology, or any contradictory schema yields `PHASE110_SCHEMA_INTEGRITY_FAILURE` and fails closed.
29. Phase110-issued entries are denied even when immediately enriched from the same bytes; later `save_horse()` enrichment preserves internal ID, identity, provenance, and denial; enrichment cannot mutate identity-bearing fields.
30. Phase110 repository atomically creates each missing `horses.id` together with provenance and denial; no qualified ID/origin split can survive a failure.
31. `database.get_horses_by_race()` excludes denied entries, and `SQLiteRaceEntrySource` rejects denied IDs; both use the same exact V018 schema-state validator.
32. DB-backed `DatabaseRaceInputProvider` effective candidate count excludes Phase110-denied entries. A denied row cannot alter candidates or unlock a bet type merely through nominal `races.horse_count`.
33. No generic prediction pipeline, predictor, strategy, value-engine, or bet-generator module change is needed or permitted; only the explicit CLI composition boundary may use the post-gate effective population.

Related regression set must include existing database save/get, race-entry-source, CLI prediction provider, JRA seed repository, Phase111 read-only result, and existing V010/immutable simulation repository tests; do not modify those out-of-scope files. Run the full pytest suite after focused and related tests.

### Stop Condition

STOP rather than broadening scope if:

- complete identity cannot be extracted without Phase95 status semantics or qualified Phase111 bytes are insufficient;
- the Phase111 bytes/archive cannot be consumed read-only without a new provider request;
- a Phase110 parent `races.id` must be created, a second internal entry-ID namespace is needed, or destructive duplicate repair is proposed;
- exact canonical NAR parent race or exact existing entry identity cannot be established;
- the local race natural key is the only evidence for parent binding, or the exact existing parent is absent, duplicated, URL-less, noncanonical, or contradicts the Phase111 URL/external-race identity;
- V018 is partial/corrupt and a reader would need to fall back to legacy selection, or one shared exact schema-state validator cannot be used by both database readers and `SQLiteRaceEntrySource`;
- migration preflight finds duplicate legacy race/entry natural keys (do not merge/delete/renumber);
- safe issuance requires an unreviewed destructive/core schema redesign or a second internal-ID namespace;
- legacy writer coexistence cannot be made race-safe with the additive unique keys and atomic transactions;
- enrichment would replace identity, clear identity-only denial, or imply ACTIVE;
- prediction/betting reader coverage extends beyond the audited DB-backed boundaries and cannot be closed within the Approved Allowed Files;
- denied rows are filtered from returned rows but nominal `races.horse_count` can still affect effective candidates or unlock a bet-type branch, and this cannot be fixed within the approved `run_prediction.py` boundary;
- `HorseParser`, NAR provider/fetcher behavior, a generic prediction/betting engine, Phase109, V010 authority, or Phase95/41 authority must be modified or promoted;
- identity-only rows could enter a Phase109/Phase108 prediction population absent separate status/eligibility authority;
- V010 must be reinterpreted or Phase109 must be implemented simultaneously;
- an additional Deba request, production DB access during design, Phase95/41 authority, or unrelated KeibaAI change is required.

### Downstream relationship

`Phase111 qualified acquisition -> Phase110 complete identity persistence -> Phase109 production external/internal mapping receipt -> Phase108 prestaged manifest -> PRE_C root / operational timing audit`.

Phase110 consumes Phase111 only by read-only byte retrieval and does not create acquisition authority. Phase110 persistence does not self-authenticate V010 rows. Phase95 status authority, Phase41 market eligibility, live campaign authorization and concrete operational timing/Delta remain separate.

`PHASE110_REVISED_ARCHITECTURAL_REVIEW_PASS`.
`PHASE110_IMPLEMENTATION_DESIGN_APPROVED`.
`PHASE110_IMPLEMENTATION_READY`.
`PHASE110_IMPLEMENTATION_APPROVAL = GRANTED`.
`PHASE110_DESIGN_APPROVED_FOR_CODEX`.

### Implementation verification for independent review

Independent review returned `CHANGES_REQUIRED`; the follow-up repair adds a global
exact-URL parent ambiguity check independent of caller-supplied place, protects a
Phase110-bound `horses.id` as well as `race_id`/`horse_no` even when foreign keys are
off on the mutating connection, proves rollback after ID and receipt insert attempts
with a non-schema-changing SQLite authorizer, and proves two real Phase110 issuers
cannot publish duplicate authority against one file-backed database.

V018 is registered in the standard migration runner. It preflights duplicate legacy
natural keys, adds uniqueness and immutable Phase110 identity/provenance/denial
storage, and supplies one shared absent/active/corrupt schema-state validator.
The Phase110 source reads only exact Phase111 qualified archive bytes and retains
identity-bearing cancelled/excluded rows without interpreting status. The repository
adopts one pre-existing exact NAR parent, issues missing `horses.id` values through
SQLite in a single `BEGIN IMMEDIATE` transaction with provenance and denial, and
publishes an exact complete-population receipt. Generic writers use serialized
lookup/write transactions; enrichment preserves identity and denial. Database,
SQLiteRaceEntrySource and CLI input gates exclude denied candidates and use the
effective post-gate population count. The daily replay result repository validates
the current complete application migration registry while retaining V016/V017
schema gates. The Phase108 rehearsal synthetic DB and full-migration test fixtures
are compatible with V018 without changing historical migration prefixes.

Post-repair direct finding tests `5 passed`; Phase110 focused `142 passed, 51 subtests
passed`; the complete related regression set `406 passed, 145 subtests passed`; full
repository suite `4836 passed, 4 skipped, 2846 subtests passed` using
`KEIBAOS_PHASE106_SEALED_COMMIT_SMOKE=48dcc0a359a9b48b7f32fbe3fef846db1da31009`.
The prior Phase108/pre-C set passed `35 passed, 2 skipped`. Final static audit found
no new provider transport, legacy Deba refetch, apparent-encoding fallback, fixed
production DB path in Phase110 simulation modules, destructive repair, Phase109/V010
write, or status/eligibility authority. V018 restrictive UPDATE/DELETE triggers and
SQLite-generated `lastrowid` issuance were confirmed. All 38 dirty paths are within
the exact Approved Allowed Files; index is empty and `git diff --check` passes.

Phase95 status authority, Phase41 market eligibility, Phase109 mapping authority,
Phase108 root authority, live campaign activation, and Operational Delta remain
outside Phase110 completion.
The first repair verification did not itself grant review PASS or commit approval;
subsequent independent review granted both for the exact repaired implementation.

Next: `WAITING_FOR_PHASE_INSTRUCTION`.

---

## Frozen predecessor — POST_V0_8_DAILY_REPLAY_111

### POST_V0_8_DAILY_REPLAY_111

Title: NAR Trusted Single-Send Deba Acquisition and Identity-Ingestion Boundary

Status: `WAITING_FOR_PHASE_INSTRUCTION`

Formal Status: `FORMALLY_COMPLETE`

State: `FORMALLY_COMPLETE`

Outcome: `PHASE111_TRUSTED_SINGLE_SEND_DEBA_ACQUISITION_BOUNDARY_FORMALLY_INTEGRATED`

Implementation Commit: `ba420cbc13a5bfbb35f3d66aa5c87873df2d11ac`

Implementation Tree: `4cbbc14af5eed97b17c9c555c51fe5c7d1bcdec8`

Implementation Parent: `79428f6fd6ab62777a8c3f2c877eeddb632d319f`

Implementation Message: `feat: add trusted NAR Deba acquisition boundary`

Branch: `feature/post-v0.8-daily-replay`

### Final independent review and closure evidence

`PHASE111_FINAL_ARCHITECTURAL_REVIEW_PASS`.
`PHASE111_IMPLEMENTATION_REVIEW_PASS`.
`PHASE111_REVIEW_CORRECTIONS_VERIFIED`.
`PHASE111_COMMITTED_DOCUMENTATION_DELTA_REVIEW_PASS`.
`PHASE111_GIT_AWARE_SEALED_VERIFICATION_PASS`.
`PHASE111_POST_COMMIT_SEALED_VERIFICATION_PASS`.
`PHASE111_FINAL_FULL_SUITE_PASS`.
`PHASE111_IMPLEMENTATION_PUSH_PASS`.
`PHASE111_REMOTE_REF_POINTS_TO_IMPLEMENTATION_COMMIT`.
`PHASE111_IMPLEMENTATION_COMMIT_REMOTE_VERIFICATION_PASS`.
`POST_V0_8_DAILY_REPLAY_111 = FORMALLY_COMPLETE`.

Implementation evidence: focused Phase111 tests **64 passed**; related regressions
**84 passed / 76 subtests passed**; final full suite **4782 passed / 4 skipped /
2846 subtests passed**; final sealed Git-blob verification **569/569 MATCH**; static
audit **PASS — no prohibited production behavior**. The implementation commit was
independently verified on the GitHub branch with its exact tree, parent, message and
eight-file path set.

### Formally integrated boundary

Phase111 provides exact RaceList-derived target ancestry; an immutable prospective
Deba request declaration; declaration persistence and exact reload; a durable exclusive
one-send claim committed before transport; fail-closed crash/UNKNOWN handling; reuse of
the reviewed `NAROfficialLiveResponseCaptureService`; exact official-capture archive
reload before lineage issuance; controlled receipt/failure publication; an immutable
acquisition receipt; strict-UTF-8 qualification and pre-cutoff observation enforcement;
and a read-only/no-network qualified result that exposes the same exact archived Deba
bytes to downstream consumers.

Retain:

`PUBLICLY_CONSTRUCTIBLE_CAPTURE != OFFICIAL_LIVE_ACQUISITION_PROOF`.
`PUBLICLY_CONSTRUCTIBLE_RECEIPT != ACQUISITION_AUTHORITY`.
`REQUEST_DECLARATION != SEND_CLAIM`.
`ONE_AUTHORIZATION_MAXIMUM_ONE_SEND`.
`UNKNOWN_SEND_OUTCOME != SAFE_TO_RETRY`.
`PHASE111_RESULT_CONSUMPTION = NO_NETWORK`.
`SAME_RESPONSE_BYTES_REQUIRED_FOR_CAPTURE_AND_IDENTITY_EXTRACTION`.

### Explicit non-authorities and remaining dependencies

Phase111 does not establish Phase110 identity persistence, issue `races.id` or
`horses.id`, persist cancelled entries, repair legacy enrichment, prove complete
prediction/betting-reader nonselection, create Phase109 mapping authority, resolve
Phase95 status semantics, assert ACTIVE, grant Phase41 market eligibility, authorize a
live campaign, choose operational Delta, or establish production readiness for the
complete betting workflow.

`TRUSTED_DEBA_ACQUISITION_AUTHORITY != PHASE110_IDENTITY_PERSISTENCE_AUTHORITY`.
`TRUSTED_DEBA_CAPTURE != COMPLETE_ENTRY_STATUS_AUTHORITY`.
`TRUSTED_DEBA_CAPTURE != ACTIVE_STATUS`.
`TRUSTED_DEBA_CAPTURE != MARKET_ELIGIBILITY`.
`IDENTITY_PERSISTENCE_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.

The trusted single-send acquisition prerequisite for Phase110 is now satisfied.
Phase110 itself remains unimplemented and must address status-independent complete
entry identity persistence, legacy writer atomicity/race safety, compatible enrichment
of identity-only rows, and prediction/betting reader nonselection coverage. Phase109
production mapping remains dependent on completed Phase110 identity persistence.
Phase95 and Phase41 remain separate downstream blockers.

Expected dependency chain:

`Phase111 COMPLETE -> Phase110 implementation -> Phase109 production mapping ->
Phase108 prestaged manifest integration -> PRE_C root / operational timing audit`.

`LIVE_CAMPAIGN_AUTHORIZATION = BLOCKED`.
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`.

Next: `CHATGPT_PREPARE_PHASE110_IMPLEMENTATION`.

---

## Historical Phase111 design and implementation record (superseded)

The material below preserves the design and execution audit trail. Its transitional
status statements and next-action recommendations describe earlier points in the
workflow; the authoritative current Phase111 state and closure evidence are recorded
above.

### Historical frozen predecessor state

`PHASE110_FINAL_DOCUMENTATION_REMOTE_VERIFICATION_PASS`.
`PHASE110_REVISED_ARCHITECTURAL_REVIEW_PASS`.
`POST_V0_8_DAILY_REPLAY_110 = ARCHITECTURAL_AUDIT_COMPLETE`.
`PHASE110_IMPLEMENTATION = BLOCKED_PENDING_TRUSTED_INGESTION_PREREQUISITE`.
`PHASE110_IDENTITY_PERSISTENCE_BLOCKED_BY_TRUSTED_ACQUISITION_AND_LEGACY_WRITER_SAFETY`.

Historical design statement: Phase111 designs only the trusted single-send upstream
boundary. It does not issue Phase110 internal IDs, repair `save_horse()`, define entry
status, grant market eligibility, choose Delta, authorize a live campaign, or perform
provider HTTP.

Freeze:

`IMMUTABLE_CAPTURE_CONTENT != AUTHORIZED_CAPTURE_PROVENANCE`.
`CAPTURE_ARCHIVE_EXACT_RELOAD != ACQUISITION_AUTHORITY`.
`PUBLICLY_CONSTRUCTIBLE_CAPTURE != OFFICIAL_LIVE_ACQUISITION_PROOF`.
`LEGACY_LOCALFETCHER_DEBA_RESPONSE != TRUSTED_CAPTURE_LINEAGE`.
`CAPTURE_IDENTITY != CAPTURE_ACQUISITION_LINEAGE`.
`PHASE110_MUST_NOT_CREATE_REDUNDANT_DEBA_REQUEST`.
`ONE_OPERATIONAL_DEBA_ACQUISITION_MAY_FEED_MULTIPLE_DOWNSTREAM_CONSUMERS`.
`SAME_RESPONSE_BYTES_REQUIRED_FOR_CAPTURE_AND_IDENTITY_EXTRACTION`.
`TRUSTED_DEBA_ACQUISITION_AUTHORITY != PHASE110_IDENTITY_PERSISTENCE_AUTHORITY`.
`TRUSTED_DEBA_ACQUISITION_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.

### Current Deba acquisition inventory (historical audit)

| Caller/path | Request and transport semantics | Capture/authority result | Classification |
| --- | --- | --- | --- |
| `LocalFetcher.get_today_races()` → `NARProvider.fetch_deba_table()` | Direct `requests.Session.get`, scalar 10-second timeout, default redirect behaviour, default TLS verification, no explicit retry adapter; response is decoded through `apparent_encoding`; HTML is logged. | No canonical URL declaration, no Phase104/105-like request authority, no immutable capture/archive, and no exact reload. | Ordinary legacy ingestion; unqualified for Phase111/110. |
| `NAROfficialLiveResponseCaptureService.capture_response()` | Canonical official URL validation; private Requests transport with `max_retries=0`, redirects disabled, TLS verification enabled, 10-second connect/read limits, identity content encoding, bounded byte streaming, effective-URL equality and HTTP 200 validation. | Saves immutable strict-UTF-8 capture to the existing append-only archive but returns after save without archive exact reload; the public service has no prospective request declaration or campaign/workflow authorization. | Trusted byte acquisition primitive; usable transport, insufficient authority on its own. |
| `NARPreCCurrentProcessRootContext` / Phase108 harness | Uses the live capture service through Phase105 `measure_nar_operation`, guarded session, exact expected URL and fake adapter beneath `Session.send`. | Child attempt, actual-send environment, capture and closures are bound to the diagnostic no-network root. | Phase108 rehearsal only; timing/diagnostic authority cannot authorize ordinary ingestion. |
| Phase104/105 runner, passive wrapper and guarded session | Controlled V2 session, claim, readiness, attempt exact reload, one guarded send per attempt and terminal observation. | Correct authority for an operational-timing attempt under its own approved session/window. | Candidate transport/control mechanism only; not ordinary identity-ingestion authority. |
| Daily-target bootstrap live-capture modules | Capture official home/monthly root/locator resources using a separate closed transport profile. | Produces bootstrap supplier captures for target discovery, not a DebaTable declaration/capture lineage. | Target-discovery evidence; may be upstream target ancestry, not a Deba send authorization. |

Repository search found no other production-capable DebaTable request path.  The closed
official capture URL vocabulary already admits `DEBA_TABLE`, `HORSE_MARK_INFO`, and
`RACE_MARK_TABLE`; Phase111 concerns only an exact canonical `DEBA_TABLE` request.

### Pre-send authority audit and decision

Caller-supplied external race ID, Deba URL, date, baba code or race number cannot
authorize a request.  A declaration is likewise not its own target authority.

`CALLER_SUPPLIED_TARGET_FIELDS != PROSPECTIVE_TARGET_AUTHORITY`.
`REQUEST_DECLARATION != ITS_OWN_TARGET_AUTHORITY`.

The exact target-identity semantics already exist in
`nar_historical_daily_target_source.py`.  `normalize_nar_race_list()` validates each
RaceList target row's race number, scheduled time, exactly one title link and the Deba
link grammar; it requires that the link's date, baba code and race number agree with
the RaceList request and row.  It derives `nar:YYYYMMDD:babaCode:raceNo` and binds a
provider-disposition reference to the exact RaceList capture and structural locator.
`build_nar_historical_daily_replay_target_set()` deterministically combines the exact
monthly/RaceList captures into a sorted `DailyHistoricalReplayTargetSet` whose
`content_sha256` includes target and completeness evidence.

This is suitable upstream target ancestry, subject to reconstruction.  It is not an
automatic Deba request authorization: `DailyHistoricalReplayTarget` does not retain a
raw Deba URL, and the daily-target archive stores source captures rather than an
independently loadable target-set object.  Phase111 must exact-reload the referenced
daily-target evidence captures, reconstruct the set through the reviewed source
function, and require equality of the reconstructed content hash and target membership
before declaration issuance.  A detached caller-supplied target-set hash cannot qualify.

`DAILY_TARGET_IDENTITY_EVIDENCE != AUTOMATIC_DEBA_REQUEST_AUTHORIZATION`.
`EXACT_RACELIST_DERIVED_TARGET_MAY_ANCHOR_PHASE111_REQUEST_AUTHORITY`.
`DETACHED_TARGET_SET_HASH != TARGET_AUTHORITY`.
`PHASE111_DECLARATION_REQUIRES_RECONSTRUCTIBLE_TARGET_ANCESTRY`.
`TARGET_MEMBERSHIP_MUST_BE_EXACT`.

No existing authority is semantically sufficient to authorize the request itself.
Ordinary race-day ingestion has no durable exact pre-send declaration.  Phase104/105
governs a timing campaign attempt, and Phase106 is diagnostic; neither may be promoted
to ordinary production identity ingestion merely because it can control a send.

Freeze:

`TIMING_CAMPAIGN_AUTHORITY != ORDINARY_IDENTITY_INGESTION_AUTHORITY`.
`DIAGNOSTIC_AUTHORITY != PRODUCTION_INGESTION_AUTHORITY`.
`RESPONSE_EXISTENCE != PRE_SEND_REQUEST_AUTHORIZATION`.

Phase111 therefore requires an additive immutable
`NARProspectiveDebaAcquisitionDeclarationV1` (name subject to later review).  Its
canonical payload binds provider/organisation, source system, canonical external race
identity, exact scheduled start where present, exact target-set content identity,
target provider-disposition reference, upstream RaceList capture/reference ancestry,
exact canonical Deba URL, acquisition purpose and semantic version, issuance time,
prediction-cutoff/allowed-observation window, one-send request identity, and schema
version.  Its content identity is derived from this complete canonical payload.  It is
persisted and exact-reloaded before an HTTP operation may begin.

Phase111 has one canonical Deba derivation: parse the verified external race identity,
construct the reviewed `DEBA_TABLE` candidate URL, pass it through
`canonicalize_nar_official_capture_url(...)`, and require that its parsed date/baba/race
components agree with the exact Deba href recorded by the RaceList target evidence. The
result is the sole URL stored in the declaration:

`https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?k_babaCode={babaCode}&k_raceDate={YYYY}%2F{MM}%2F{DD}&k_raceNo={raceNo}`.

`EXTERNAL_RACE_ID_AND_DEBA_URL_MUST_SHARE_ONE_VERIFIED_ANCESTRY`.
`HISTORICAL_TARGET_IDENTITY_EVIDENCE_REUSE != HISTORICAL_REPLAY_POLICY_REUSE`.

`PRE_SEND_DECLARATION_MUST_PRECEDE_ACTUAL_SEND`.
`REQUEST_AUTHORITY_CANNOT_BE_BACKFILLED_AFTER_RESPONSE`.

### Recommended architecture — dedicated acquisition application

| Option | Assessment |
| --- | --- |
| A. Extend `LocalFetcher` directly with the live capture service | Leaves declaration, durable send claim, archive reload and consumer authority entangled with the legacy orchestration path.  It also makes unqualified legacy entry points too easy to confuse with qualified ingestion. |
| B. Add a dedicated Phase111 acquisition application and a read-only same-byte consumer boundary | Recommended. The application owns declaration, durable claim, transport invocation, capture save/reload, lineage receipt and same-byte fan-out. It proves a qualified consumer can strict-decode archived bytes for `HorseParser`, without globally routing `LocalFetcher` through this boundary. |
| C. Replace all direct Deba transport with a capture-first upstream service | Strongest uniformity, but broader migration and compatibility scope than the currently identified prerequisite. |

The recommended application uses `NAROfficialLiveResponseCaptureService`'s reviewed
transport unchanged.  It must not redefine canonical URL, retry, redirect, TLS,
timeout, maximum-response or official-host/path/query validation rules.

`PHASE111_ORCHESTRATION_MUST_NOT_REDEFINE_PROVIDER_TRANSPORT_SEMANTICS`.
`LEGACY_DEBA_FETCH != PHASE111_QUALIFIED_ACQUISITION`.

For a qualified operation the causal sequence is:

`reconstruct/verify target authority -> declaration save/reload -> durable one-send
claim -> existing trusted capture service invocation -> immutable capture save -> capture
exact reload -> lineage receipt save/reload -> same-byte consumer fan-out`.

The ordinary direct `fetch_deba_table()` route may remain for legacy operations, but it
is prohibited as the source of a Phase111-qualified result.  First implementation does
not require a global LocalFetcher migration.  A qualified consumer demonstrates the
strict-byte adapter directly; future Phase110/qualified ingestion composition consumes
the Phase111 result and must not call the legacy fetch.  A LocalFetcher change is
deferred unless later evidence shows a tiny adapter is necessary.

`PHASE111_IMPLEMENTATION_COMPLETE != LEGACY_FETCHER_GLOBAL_MIGRATION_COMPLETE`.
`PHASE111_RESULT_CONSUMPTION = NO_NETWORK`.

### Single-send, terminal, crash and concurrency semantics

Target authority, request declaration, one-send claim, and HTTP invocation are distinct
authority events. The required order is exact target reconstruction and membership
verification, declaration persistence and exact reload, atomic one-send claim
acquisition, then invocation of the existing trusted capture service.

`TARGET_AUTHORITY != REQUEST_DECLARATION`.
`REQUEST_DECLARATION != SEND_CLAIM`.
`SEND_CLAIM_MUST_PRECEDE_TRANSPORT_INVOCATION`.

Single-send means at most one application-authorized provider send attempt for one
declaration identity. It does not claim exactly-once receipt by the remote provider.
There is no automatic retry, fallback to `NARProvider.fetch_deba_table()`, or consumer
refetch. A later observation requires a distinct prospective declaration and may use one
new send under that declaration.

`AT_MOST_ONE_APPLICATION_AUTHORIZED_SEND_ATTEMPT`.
`SINGLE_SEND_PER_AUTHORIZATION != SINGLE_LIFETIME_CAPTURE`.
`NO_REDUNDANT_CONSUMER_FETCH != NO_SEPARATELY_AUTHORIZED_REFRESH`.
`FAILED_AUTHORIZED_SEND != AUTHORITY_FOR_RETRY`.
`ONE_AUTHORIZATION_MAXIMUM_ONE_SEND`.

An additive companion archive should store append-only declarations, durable send
claims, terminal/send evidence and acquisition receipts.  A declaration identity has
one unique claim.  Claim publication occurs before the transport is invoked under a
database transaction/lock so two processes cannot consume the same authorization.
Terminal classifications include `SUCCESS`, `CONNECT_TIMEOUT`, `READ_TIMEOUT`,
`TRANSPORT_FAILURE`, `VALIDATION_OR_UNSUPPORTED_RESPONSE`,
`CAPTURE_PERSISTENCE_FAILURE`, and `UNKNOWN_SEND_OUTCOME`.

The closed lifecycle is `DECLARED_NOT_CLAIMED`, then
`CLAIMED_SEND_OUTCOME_UNKNOWN`, followed by either `SEND_TERMINAL_FAILURE`,
`CAPTURE_PERSISTED`, or `RECEIPT_COMPLETE`. The claim is deliberately consumed before
socket transmission can be proven, so a crash can conservatively retain
`CLAIMED_SEND_OUTCOME_UNKNOWN` even if no provider receipt occurred.

Crash after declaration before claim leaves the declaration unused.  Crash after claim
and before a known terminal, during send, or after a successful send before durable
capture/receipt publication remains indeterminate.  Restart must reconcile it as
`UNKNOWN_SEND_OUTCOME`; it cannot resend under the same declaration.  A later refresh
requires a new declaration after separate review.

`UNKNOWN_SEND_OUTCOME != SAFE_TO_RETRY`.
`CRASH_RECOVERY_MUST_NOT_DUPLICATE_PROVIDER_SEND`.

### Capture lineage and deterministic byte fan-out

The immutable `NARProspectiveDebaAcquisitionReceiptV1` (name subject to review) binds
the declaration identity, send-claim identity, terminal disposition, exact target
identity, canonical request and effective URL, capture ID, response SHA-256,
requested/observed/stored timestamps, capture archive exact-reload result,
target/cutoff ancestry, source/runtime provenance, and receipt semantic/schema version.
It proves that the capture belongs to the exact pre-send declaration; capture ID alone
is never sufficient. The application issues it only after the trusted capture service
returns and its saved capture exact-reloads from the existing capture archive.

`CAPTURE_ID_ALONE != ACQUISITION_LINEAGE`.
`ACQUISITION_RECEIPT_MUST_BIND_REQUEST_AUTHORITY_TO_EXACT_CAPTURE`.

The Phase111 application reloads the saved capture and exposes those exact archived
bytes to named consumers.  It does not reconstruct HTML from a previous decoded string.
The legacy adapter must decode `capture.response_body` once with `utf-8`, strict errors,
then pass that text to the unchanged `HorseParser`; future Phase110 reads the same
reloaded capture/receipt without provider operation.

Strict UTF-8 is the reviewed supported profile for a Phase111-qualified capture; the
existing trusted capture contract is retained. A non-UTF-8 Deba response fails closed
as unsupported for this qualified path. It must not fall back to the legacy apparent-
encoding behavior. This design does not require advance proof that every possible future
production response is UTF-8: a later prospective profile-qualification or
live-readiness activity determines observed operational compatibility.

`LEGACY_APPARENT_ENCODING != TRUSTED_CAPTURE_ENCODING_AUTHORITY`.
`NON_UTF8_DEBA_RESPONSE = UNSUPPORTED_FOR_PHASE111_QUALIFIED_ACQUISITION`.
`UNSUPPORTED_ENCODING != AUTHORITY_FOR_LEGACY_FALLBACK`.

`SEMANTICALLY_EQUIVALENT_HTML != SAME_CAPTURE_BYTES`.
`DOWNSTREAM_DECODE_MUST_BE_DETERMINISTIC_AND_REVIEWED`.

### Phase110 handoff, cutoff and timing relationship

Future Phase110 consumes declaration identity, acquisition receipt identity, capture ID,
canonical URL, response digest, exact reloaded bytes, external race identity,
`observed_at`, and cutoff/window ancestry as read-only inputs.  It cannot issue HTTP.

`PHASE110_CONSUMPTION_OF_PHASE111_AUTHORITY = READ_ONLY_NO_PROVIDER_SEND`.

The intended ordering is:

`prospective target authority -> Phase111 declaration -> Deba capture -> Phase111
receipt -> Phase110 identity persistence -> Phase109 mapping receipt -> Phase108
prestaged manifest -> Phase108 root start`.

For a Phase109 mapping claimed as pre-cutoff authority, the minimum rule is
`capture.observed_at <= prediction_information_cutoff`; a post-cutoff capture cannot
establish that mapping.

`POST_C_CAPTURE != PRE_C_IDENTITY_MAPPING_AUTHORITY`.

Phase111 upstream ingestion must have an independently reviewed race-day purpose.  It
cannot be declared pre-root solely to remove work from a target's timing envelope.  The
later Phase108 current Deba capture may still have an independent snapshot/freeze
purpose at root dispatch.  The two observations are not duplicates solely because their
URLs match, but Phase110 and legacy enrichment may not add any further request.

`PRE_ROOT_PREREQUISITE != FREE_TIMING_PREWORK_BY_ASSERTION`.
`ORDINARY_UPSTREAM_INGESTION_MUST_HAVE_INDEPENDENT_OPERATIONAL_PURPOSE`.
`MEASUREMENT_CAMPAIGN_MUST_NOT_GENERATE_REDUNDANT_PROVIDER_LOAD`.
`TRUSTED_DEBA_CAPTURE != COMPLETE_ENTRY_STATUS_AUTHORITY`.
`TRUSTED_DEBA_CAPTURE != ACTIVE_STATUS`.
`TRUSTED_DEBA_CAPTURE != MARKET_ELIGIBILITY`.

### Archive architecture

The existing official-capture archive and capture identities remain unchanged. Phase111
needs an additive companion authorization/lineage archive with exact references to the
approved daily-target evidence archive, a declaration, one-send claim, terminal
disposition, declaration-to-capture lineage, and receipt tables. It must not duplicate
response bodies or full RaceList bytes, and it must not reuse Phase105 timing attempts
as ordinary-ingestion rows.

`PHASE111_LINEAGE_ARCHIVE != RESPONSE_BODY_ARCHIVE`.

The archive must reject unknown/partial schema topology, orphan terminals/receipts,
duplicate claims, receipt/capture contradiction, missing reconstructed target ancestry,
and mutation.

### Allowed Files

The Phase111 implementation may modify or create only:

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`
- `scripts/simulation/nar_trusted_deba_acquisition.py`
- `scripts/simulation/nar_trusted_deba_acquisition_archive_migration.py`
- `scripts/simulation/sqlite_nar_trusted_deba_acquisition_archive.py`
- `tests/test_nar_trusted_deba_acquisition.py`
- `tests/test_nar_trusted_deba_acquisition_archive_migration.py`
- `tests/test_sqlite_nar_trusted_deba_acquisition_archive.py`

This is the complete Allowed Files set. A separate bootstrap module requires a contract
amendment before it may be created.

### Forbidden Files

Every repository path not listed in Allowed Files is forbidden. In particular, Phase111
must not modify:

- `scripts/fetch_local.py`, `scripts/providers/nar_provider.py`,
  `scripts/parsers/horse_parser.py`, `scripts/database.py`, or `scripts/models.py`;
- `scripts/simulation/nar_official_response_capture.py`,
  `scripts/simulation/nar_official_response_live_capture.py`, or
  `scripts/simulation/repositories/sqlite_nar_official_response_capture_repository.py`;
- `scripts/simulation/nar_historical_daily_target_source.py`,
  `scripts/simulation/nar_historical_daily_target_capture.py`,
  `scripts/simulation/nar_historical_daily_target_live_capture.py`,
  `scripts/simulation/sqlite_nar_daily_target_evidence_archive.py`, or existing
  daily-target migrations;
- Phase104/105/106/108 authority modules, Phase109/110 implementation paths, prediction
  pipeline/readers, `database/**`, or `logs/**`.

These modules may be imported through their existing APIs. Phase111 may not change
provider, transport, target-source, parser, or legacy-ingestion semantics.

### Required Tests

The implementation must add and pass:

- `tests/test_nar_trusted_deba_acquisition.py`
- `tests/test_nar_trusted_deba_acquisition_archive_migration.py`
- `tests/test_sqlite_nar_trusted_deba_acquisition_archive.py`

The focused tests must prove at minimum:

1. Caller-supplied race fields or a detached target-set digest cannot self-authorize.
2. Exact archived daily-target evidence reconstructs deterministically, reproduces the
   target-set identity, proves target membership and external race identity, and derives
   a canonical Deba URL with the same RaceList ancestry; any contradiction fails closed.
3. The declaration is immutable/content-addressed, persists and exact-reloads before a
   durable exclusive claim; concurrent claimants cannot both obtain send authority.
4. Claim acquisition precedes transport; one declaration permits at most one
   application-authorized send; unknown send, connect timeout, read timeout, and
   transport failure do not retry; a distinct refresh declaration may send once.
5. The existing trusted official capture service is reused without redefining retry,
   redirect, TLS, timeout, body-limit, or canonical URL semantics.
6. Returned captures exact-reload before receipt issuance; a missing or contradictory
   reload blocks the receipt; the receipt binds target, declaration, claim, canonical
   URL, capture, digest, timestamps, terminal disposition, and semantic version.
7. A caller-constructed `NAROfficialResponseCapture` cannot replace Phase111 lineage;
   the companion archive stores no response bytes; the qualified result has no refetch
   capability; and exact archived bytes remain available to multiple consumers.
8. Strict UTF-8 is enforced; non-UTF-8 fails closed; no apparent-encoding fallback
   exists; and identical archived bytes can feed the `HorseParser` adapter and remain
   available to Phase110.
9. A post-cutoff observation cannot qualify as pre-cutoff Phase110/109 authority.
10. Phase111 infers no ACTIVE/status/market eligibility, issues no `races.id` or
    `horses.id`, and creates no V010 mapping.
11. Focused tests use deterministic injected/fake no-network boundaries, make zero real
    provider HTTP calls, and use only temporary/in-memory test databases, never
    `database/keiba.db`.

Required related regressions are `tests/test_nar_official_response_capture.py`,
`tests/test_nar_official_response_live_capture.py`,
`tests/test_sqlite_nar_official_response_capture_repository.py`, and the repository's
matching existing daily-target capture/live-capture/archive tests, including where
present `tests/test_nar_historical_daily_target_capture.py`,
`tests/test_nar_historical_daily_target_live_capture.py`, and
`tests/test_sqlite_nar_daily_target_evidence_archive.py`. Existing regression files are
read-only under this contract. Then run the complete repository pytest suite.

Required order: focused Phase111 tests, related official-capture/daily-target
regressions, full repository suite, `git diff --check`, exact changed-path audit, and
`git status --short`. No test may perform real provider HTTP.

### Stop Condition

Stop rather than broadening scope if exact upstream target ancestry cannot be
reconstructed; the declaration would self-authorize; external race identity and
canonical Deba URL cannot share exact RaceList ancestry; the only usable authority is
Phase105 diagnostic/timing authority; trusted official transport semantics must change;
an extra Deba request is required; crash/concurrency cannot guarantee at-most-one send;
a bootstrap module outside Allowed Files is required; a forbidden module must change;
LocalFetcher must be globally migrated; legacy apparent-encoding fallback is required;
Phase110 internal-ID issuance, Phase95 status semantics, or Phase41 market eligibility
is required; production database access or real provider HTTP is required for
verification; or an unrelated failing test needs an out-of-scope change.

### Approved implementation boundary

Phase111 first implementation is additive only. It provides:

`RaceList-derived target authority -> declaration -> exact reload -> exclusive send
claim -> trusted capture-service invocation boundary -> exact capture reload ->
acquisition lineage receipt -> no-network/read-only qualified result`.

It does not provide global LocalFetcher migration, Phase110 ID persistence,
cancelled-entry persistence, safe enrichment, prediction-reader filtering, Phase109
mapping receipt, Phase95 status authority, Phase41 eligibility, operational Delta, or
live campaign authorization.

Phase111 implementation leaves Phase110 writer atomicity, compatible
enrichment, complete prediction-reader nonselection coverage, Phase109 mapping receipt,
Phase95 status authority, Phase41 market eligibility, official campaign authorization
and operational timing audit unresolved.

### Revised implementation-readiness decision

`PHASE111_IMPLEMENTATION_READY` is approved by independent architectural review.
The design now closes reconstructible target ancestry, canonical Deba derivation,
immutable declaration, exclusive durable claim, conservative crash behavior, trusted
transport reuse, exact capture reload, immutable receipt, no-refetch result, additive
scope, and strict UTF-8 fail-closed handling. Global LocalFetcher migration, live
profile qualification, Phase110 persistence, Phase109 mapping, Phase95, Phase41, and a
live timing campaign remain later work and do not expand this first Phase111 scope.

### Limited implementation-review correction

Independent review found that `_publish_receipt()` and `_publish_failure()` checked
only exact record types. Publicly constructed immutable receipts, even when backed by
a manually archived public capture and genuine claim, could therefore be published
without the controlled acquisition application. Persisted content did not prove
controlled issuance.

`PERSISTED_RECEIPT_CONTENT != CONTROLLED_RECEIPT_ISSUANCE`.
`PUBLICLY_CONSTRUCTIBLE_RECEIPT != ACQUISITION_AUTHORITY`.
`PUBLICLY_CONSTRUCTIBLE_CAPTURE != OFFICIAL_LIVE_ACQUISITION_PROOF`.
`UNCONTROLLED_TERMINAL_PUBLICATION != PHASE111_LINEAGE_AUTHORITY`.
`EXACT_DUPLICATE_CONTENT != CONTROLLED_ISSUANCE`.
`ARBITRARY_CAPTURE_RESPONSE_PROTOCOL != TRUSTED_CAPTURE_SERVICE`.

The archive now owns one private current-process
`_PHASE111_TERMINAL_ISSUANCE_MARKER`. Both terminal publication methods require its
exact identity before type/ancestry validation, duplicate handling or insertion.
Missing or unrelated markers are rejected even for already-persisted exact duplicates.
This follows Phase105 trusted API discipline; it is not cryptographic security.
The marker is absent from every canonical record, persisted payload, qualified result
and public application constructor.

`NARTrustedDebaAcquisitionApplication.acquire()` supplies the marker after the existing
success causal path, including renewed target reconstruction, durable claim, trusted
capture invocation, official archive exact reload and capture verification. Known
failure publication uses the same marker. Failure-publication failure still leaves
the consumed claim `UNKNOWN_SEND_OUTCOME`; no retry or claim semantics changed.
The application constructor requires
`type(capture_service) is NAROfficialLiveResponseCaptureService`. The reviewed service
with deterministic fake transport remains accepted; arbitrary protocol objects and
overriding subclasses are rejected. No existing capture module changed.

Correction changes are confined to the two Phase111 application/archive modules, their
two focused test modules and these two docs. Migration/schema and migration tests are
unchanged from the independent-review bundle. Ten new cases cover forged receipts,
manual capture plus manual receipt, uncontrolled failure, absent/wrong markers on exact
duplicates, pre-ancestry rejection, and arbitrary/subclass service rejection. All
existing controlled-success/failure, publication-failure, concurrency and crash cases
remain passing.

Correction verification: focused tests **64 passed**; all eight related regression
modules **84 passed, 76 subtests passed**; full repository **4782 passed, 4 skipped,
2846 subtests passed**, exit 0, 1038.21 seconds. The full command was
`python -m pytest -q --junitxml=C:/Users/garim/AppData/Local/Temp/keibaos-phase111-correction-full-20260928.xml`
with
`KEIBAOS_PHASE106_SEALED_COMMIT_SMOKE=79428f6fd6ab62777a8c3f2c877eeddb632d319f`.
This is the established Phase106 committed-source regression configuration, not sealed
verification of uncommitted Phase111 bytes. Static searches found no additional HTTP,
fallback, repair or Phase110/V010 persistence. Marker exposure checks, whitespace
checks, `git diff --check`, the exact eight-path Allowed-Files audit and empty-index
check pass. Provider HTTP, production DB, live campaign, stage, commit and push activity
were zero. No implementation-review PASS or commit approval is claimed.

Next: `CHATGPT_REVIEW_PHASE111_IMPLEMENTATION_CORRECTION`.

### Initial implementation and precommit verification record (before correction)

The additive implementation consists only of the three approved production modules
and three dedicated test modules, plus these two documents. No existing provider,
transport, target-source, parser, ingestion, migration, or prediction module changed.
There is no separate bootstrap module and no global LocalFetcher migration.

`NARTrustedDebaAcquisitionApplication.declare()` exact-loads the monthly/envelope and
RaceList capture identities from the existing daily-target archive. It reconstructs
the target set using `build_nar_historical_daily_replay_target_set()`, checks its exact
content hash and unique NAR/nar_official membership, verifies disposition capture/digest
ancestry and evidence persistence before declaration issuance, and derives the Deba URL
through the existing canonicalizer. It accepts no caller-created target as authority.
The reviewed normalizer remains responsible for proving the RaceList href ancestry;
Phase111 does not duplicate its HTML grammar or inherit historical replay policy.

Frozen, versioned canonical records are
`NARProspectiveDebaAcquisitionDeclarationV1`, `NARProspectiveDebaSendClaimV1`,
`NARProspectiveDebaFailureV1`, and `NARProspectiveDebaAcquisitionReceiptV1`.
Their complete canonical UTF-8 JSON payloads determine SHA-256 content identities.
Exact reload rejects schema/content/identity or parent-ancestry contradictions.

The explicit migration installs a dedicated V1 registry and `phase111_declarations`,
`phase111_claims`, `phase111_failures`, and `phase111_receipts` tables. Exact topology,
registry, restrictive foreign keys, append-only triggers, and exclusive terminal
constraints are validated. Constructors never migrate or repair. Schema inspection
excludes only the literal
`sqlite_` internal-name prefix, not unrelated legal names such as `sqliteXunexpected`.
Storage-layer `BEGIN IMMEDIATE` and a unique declaration-to-claim relation enforce
one committed claim before transport without process-local exclusivity,
including independent concurrent SQLite connections. A consumed claim with no durable
terminal is `UNKNOWN_SEND_OUTCOME`; restart cannot resume/retry it. A separately
declared refresh has a distinct identity and may acquire its own single claim.

After exact declaration reload and renewed target reconstruction, the application
invokes the existing trusted capture-service boundary once. It exact-reloads the
returned capture from the unchanged official archive, compares it exactly, and verifies
Deba target/page, strict UTF-8 and claim/request/observation/cutoff ordering before
publishing and reloading a success receipt. Known failures are immutable terminal
evidence; known repository publication errors are distinguished from transport errors,
and failure-publication failure leaves the durable claim consumed/unknown.
There is no retry, fallback, retrospective receipt reconstruction, or new HTTP stack.

The receipt binds declaration, claim, provider, external target, canonical URL,
capture/digest, requested/observed/stored timestamps, cutoff, success disposition and
V1 identity. `NARQualifiedDebaResultV1` exposes no provider/refetch capability.
`read_qualified_deba_bytes()` verifies exact receipt/declaration/claim/capture
consistency and returns the existing archive's unchanged bytes without network access.
The lineage archive stores neither Deba bodies nor RaceList bodies. Same-byte fan-out
and strict decoding into the existing HorseParser boundary were tested. Unsupported
UTF-8 and post-cutoff observations do not receive qualified receipts.

`CAPTURE_RETURN_VALUE_ALONE != PHASE111_ACQUISITION_AUTHORITY`.
`VALID_RAW_CAPTURE != VALID_PRE_C_IDENTITY_AUTHORITY`.
`LIVE_CAMPAIGN_AUTHORIZATION = BLOCKED`.
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`.

Required verification was rerun on this uncommitted implementation:

- Phase111 focused on final source: **54 passed**.
- All eight required official-capture/daily-target regression modules: **84 passed,
  76 subtests passed**.
- Full repository, final invocation: **4772 passed, 4 skipped, 2846 subtests passed**,
  exit 0, 947.86 seconds. XML has zero failures/errors.
- Static prohibited-behavior searches, new-file whitespace audit, `git diff --check`,
  exact eight-path Allowed-Files audit and empty-index check passed.

The first full invocation without the established Phase106 smoke configuration ended
with 1 existing diagnostic sealed-child failure, 4767 passes, 4 skips and 2846 subtests.
Its temporary-clone diagnostic commit had no source difference; the clone remained
clean at the approved base. No Phase111 failure or forbidden-file correction occurred.
The existing test then passed separately and in the final full run with
`KEIBAOS_PHASE106_SEALED_COMMIT_SMOKE=79428f6fd6ab62777a8c3f2c877eeddb632d319f`,
the established committed-source regression mode. This does not seal or attest Phase111
worktree bytes. The four full-suite skips are the existing two environment-gated
Phase108 final-sealed cases and two unavailable Windows symlink-capability cases;
Phase108's already-reviewed formal/sealed completion remains unchanged.

An intermediate configured full run passed 4768 tests before four final focused cases
were added for publication-error classification and literal SQLite internal-prefix
schema rejection. An ensuing verification run was intentionally interrupted before
completion to fix the reproduced schema-prefix issue; it is not counted as a pass.
All focused, related and full verification was then rerun on the final source above.

Provider HTTP, production DB reads/writes, live campaign, workspace staging, commit and
push were zero. All new tests use fake transport and temporary/in-memory databases.
The separate KeibaAI repository was untouched. Phase111 is not formally complete;
independent implementation review and explicit commit approval remain required.

Next: `CHATGPT_REVIEW_PHASE111_IMPLEMENTATION`.

---

## Historical record — POST_V0_8_DAILY_REPLAY_110

Title: NAR Prospective Identity-Complete Race and Entry Persistence Authority

Status: `WAITING_FOR_PHASE_INSTRUCTION`

Formal Status: `ARCHITECTURAL_AUDIT_COMPLETE`

State: `BLOCKED_PENDING_TRUSTED_SINGLE_SEND_IDENTITY_INGESTION_PREREQUISITE`

Outcome: `PHASE110_IDENTITY_PERSISTENCE_BLOCKED_BY_TRUSTED_ACQUISITION_AND_LEGACY_WRITER_SAFETY`

Review disposition: `PHASE110_REVISED_ARCHITECTURAL_REVIEW_PASS`

`PHASE110_REVISED_ARCHITECTURAL_REVIEW_PASS`.
`POST_V0_8_DAILY_REPLAY_110 = ARCHITECTURAL_AUDIT_COMPLETE`.
`PHASE110_IMPLEMENTATION = BLOCKED_PENDING_TRUSTED_INGESTION_PREREQUISITE`.

Base Commit: `64f9ad239cabad13feaa8febb6cb5754dce57a6b`

Base Tree: `caa62f5c4bb8971b158a8598d9cdb2d05448ae20`

Branch: `feature/post-v0.8-daily-replay`

### Frozen predecessor disposition

`POST_V0_8_DAILY_REPLAY_108 = FORMALLY_COMPLETE`.
`NAR_TARGET_SCOPED_PRE_C_CRITICAL_PATH_ENVELOPE = FORMALLY_INTEGRATED`.
`FINAL_COMMIT_SEALED_SOURCE_VERIFICATION = PASS`.

`POST_V0_8_DAILY_REPLAY_109 = ARCHITECTURAL_AUDIT_COMPLETE`.
`PHASE109_REVISED_ARCHITECTURAL_REVIEW_PASS`.
`PHASE109_IMPLEMENTATION = BLOCKED_NOT_AUTHORIZED`.
`PHASE109_PRODUCTION_ENTRY_MAPPING_BLOCKED_BY_IDENTITY_COMPLETE_INGESTION`.

`LIVE_CAMPAIGN_AUTHORIZATION = BLOCKED`.
`CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`.

Phase110 is a prerequisite-authority design only.  It does not authorize provider
HTTP, an official timing campaign, a concrete Delta, market eligibility, a positive
ACTIVE conclusion, historical-status authority, or complete entry-status semantics.

Freeze:

`IDENTITY_PERSISTENCE_AUTHORITY != ENTRY_STATUS_AUTHORITY`.
`IDENTITY_PERSISTENCE_AUTHORITY != MARKET_ELIGIBILITY`.
`IDENTITY_PERSISTENCE_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.
`ENTRY_IDENTITY_UNIVERSE != OBSERVED_ENTRY_STATUS_UNIVERSE`.
`IDENTITY_COMPLETE_POPULATION != COMPLETE_STATUS_UNIVERSE`.

### Problem and retained Phase109 findings

`build_historical_input_snapshot(...)` takes caller-supplied `internal_race_id` and
`race_entry_id_by_external_entry_id`.  Phase108 can bind fixture mappings, but those
fixtures are not a production producer.  The later Phase109 mapping receipt needs an
independent, prospective source for both internal identities before the Phase108 root
starts.

Freeze:

`CALLER_SUPPLIED_INTERNAL_MAPPING != PRODUCTION_MAPPING_AUTHORITY`.
`HORSE_NUMBER != INTERNAL_RACE_ENTRY_ID`.
`ENTRY_ENUMERATION != INTERNAL_RACE_ENTRY_ID`.
`HASH_DERIVATION != INTERNAL_RACE_ENTRY_ID`.
`EXTERNAL_ENTRY_ID != INTERNAL_RACE_ENTRY_ID`.
`FIXTURE_MAPPING_AUTHORITY != PRODUCTION_MAPPING_AUTHORITY`.
`V010_MAPPING_ROW_EXISTENCE != INDEPENDENT_PRODUCTION_MAPPING_AUTHORITY`.
`SNAPSHOT_SAVE_DERIVED_MAPPING != PRE_SNAPSHOT_MAPPING_AUTHORITY`.
`READ_ONLY_RELOAD_CANNOT_LAUNDER_CALLER_SUPPLIED_MAPPING`.
`STATUS_FILTERED_HORSE_ROWS != COMPLETE_NAR_ENTRY_IDENTITY_UNIVERSE`.
`CANCELLED_ENTRY != NONEXISTENT_ENTRY_IDENTITY`.
`ENTRY_STATUS_INTERPRETATION != ENTRY_IDENTITY_BINDING`.
`OMITTED_CANCELLED_HORSE_ROW != AUTHORIZED_MAPPING_ABSENCE`.
`ROOT_CURRENT_DEBA_CAPTURE != PRE_ROOT_MAPPING_AUTHORITY`.
`PHASE88_FIXTURE_BINDER != DYNAMIC_PRODUCTION_MAPPING_PRODUCER`.

### Audited ingestion and internal-ID inventory

| Producer / reader | Authority and retained identity | ID allocation / persistence | Completeness and suitability |
| --- | --- | --- | --- |
| `scripts/fetch_races.py` | Selects JRA or local fetcher, then calls `save_race`; no NAR identity receipt. | Delegates to legacy persistence. | Orchestration only; it cannot prove an exact NAR race or entry binding. |
| `scripts/fetch_local.py` | NAR race-list and DebaTable response, parsed by `NARParser` and `HorseParser`. | Calls `save_race`, then `save_horse` for parser output. | Official NAR input, but ordinary request/retry/log path has no immutable capture authority and loses cancelled rows before `save_horse`. |
| `scripts/providers/nar_provider.py` / `scripts/parsers/nar_parser.py` | Race date, organisation/place, race number, Deba URL and descriptive fields. | No authoritative canonical NAR identity persistence. | URL and query material are useful race evidence, but existing storage does not make the canonical binding unique. |
| `scripts/database.py:races` / `save_race` | Legacy `(race_date, organization, place, race_no)` lookup and Deba URL. | `races.id` is `INTEGER PRIMARY KEY AUTOINCREMENT`; lookup is `LIMIT 1`, not a schema uniqueness constraint. | An internal race origin, but not yet an exact provider-namespace binding.  A new receipt must reject duplicate/ambiguous legacy matches. |
| `scripts/database.py:horses` / `save_horse` | Race-bound horse-number row, name/detail URL and optional race-day fields. | `horses.id` is `INTEGER PRIMARY KEY AUTOINCREMENT`; existing lookup is `(race_id, horse_no)` with `LIMIT 1`. | The detailed design and prediction inputs use `horses.id` as `race_entry_id`, scoped by `horses.race_id`; it is not proof of a global horse identity.  It is status-filtered at source. |
| `scripts/parsers/horse_parser.py` | Parses Deba rows but `_is_cancelled(...)` skips cancellation/exclusion markers before a `Horse` is emitted. | Thus no `horses.id` is allocated for those identity-bearing rows. | Not identity complete; it cannot be elevated to Phase109 authority. |
| `scripts/simulation/nar_official_response_capture.py` / `nar_historical_input_source.py` | Canonical Deba URL; `nar:YYYYMMDD:babaCode:raceNo`; canonical horse link/provider identity. | Immutable response-capture identity exists in the reviewed simulation authority. | Exact source-identity primitives, but current normalizer requires status-sensitive fields and rejects cancellation rows; it is not the Phase110 generic extractor. |
| `scripts/simulation/nar_race_entry_status_replay_identity_binding.py` | One `td.horseNum`, one horse link, exact parent-race relation. | Fixture-bound result only. | Structural precedent only: fixed target, 1..14 population and frozen hashes prohibit production generalisation. |
| V010 snapshot repository mappings | Relational external race/entry rows. | `save_snapshot() -> _ensure_mappings()` can create them from caller-supplied snapshot IDs. | Consistency evidence only; origin is not independently distinguishable, so they cannot be the Phase110 source of truth. |

The direct legacy writers found are `fetch_local.py` for both `save_race` and
`save_horse`, and `fetch_races.py` for `save_race`.  No audited writer independently
persists a complete canonical NAR entry universe or durable provider-to-internal
binding provenance.

### Semantics and current safety finding

`races.id` is a local allocated race identifier.  It may become a Phase110 internal
race ID only after a controlled issuer proves one canonical NAR DebaTable identity,
one exact parent-race record, and rejects all ambiguity.  No fuzzy place/name match,
row order, or approximate date match is admissible.

`horses.id` is a race-scoped participation/entry identifier in the existing model:
downstream snapshot and prediction code use it as `race_entry_id`, and `horse_id` is
not a separate global-horse table.  This establishes the candidate internal entry
namespace, but does not make every legacy row authoritative nor make a horse number
globally identifying.  The required relation is:

`canonical external race ID -> exactly one internal races.id`, then
`external entry ID -> exactly one horses.id whose race_id is that races.id`.

The current prediction input provider loads `get_horses_by_race(race_id)` without an
entry-status/eligibility filter and can hand each returned `horses.id` to prediction,
ranking and strategy paths.  Consequently, putting cancelled identity-only rows into
the legacy entry population without a separately enforced selection gate could make
them selectable.  This is not safe.

Freeze:

`HORSES_TABLE_NAME != GLOBAL_HORSE_IDENTITY_PROOF`.
`INTERNAL_ENTRY_ID_SEMANTICS_MUST_BE_ESTABLISHED_BEFORE_ISSUANCE`.
`IDENTITY_ROW_EXISTENCE != ACTIVE_STATUS`.
`IDENTITY_ROW_PERSISTENCE_MUST_NOT_REQUIRE_MARKET_FIELDS`.
`IDENTITY_ROW_PERSISTENCE_MUST_NOT_REQUIRE_POSITIVE_STATUS_SEMANTICS`.
`IDENTITY_COMPLETE_POPULATION != PREDICTION_ELIGIBLE_POPULATION`.
`PERSISTED_ENTRY != SELECTABLE_ENTRY`.

### Architecture alternatives and recommendation

| Option | Assessment |
| --- | --- |
| A. Change legacy `HorseParser` ingestion to create ordinary `horses` for every Deba row | Rejected.  It mixes identity persistence with legacy enrichment/status behaviour and can silently broaden prediction input. |
| B. Dedicated identity registry with a new independent entry-ID namespace | Rejected.  A second ID namespace cannot satisfy the existing snapshot `race_entry_id` relationship without a later synthetic or circular translation. |
| C. Controlled identity-only issuance into the existing race-entry namespace, separate from legacy enrichment | Recommended, subject to an explicit non-selection gate.  A new status-independent extractor reads an exact archived Deba capture; a controlled transaction allocates/reuses only proven `races.id`/`horses.id`; an additive provenance registry and immutable receipt bind the identity origin.  The ordinary status-sensitive parser remains unchanged. |
| D. Existing persisted producer | Not supported by the audit.  Current rows lack a complete identity population and durable independent origin proof. |

The recommended Option C is not an implementation approval.  Its safety precondition
is a narrow, tested prediction-source gate: Phase110-issued `identity_only` entries
must not be returned by sanctioned selectable-entry reads until an independent future
status/eligibility authority admits them.  That gate is an exclusion default, not an
ACTIVE inference and not Phase95/41 work.  If compatibility review cannot prove this
gate covers all prediction/selection readers, Phase110 implementation must stop.

### Proposed exact source and extractor contract

An immutable `DEBA_TABLE` capture is not, by itself, an acquisition authority.  The
ordinary `LocalFetcher -> NARProvider.fetch_deba_table() -> decoded text ->
HorseParser` path neither issues a `NAROfficialResponseCapture` nor archives trusted
provider provenance.  `NAROfficialLiveResponseCaptureService` is a reviewed trusted
capture primitive, but is not wired as the normal `LocalFetcher` acquisition boundary.
Its publicly constructible capture objects and SQLite archive prove content and archive
consistency, not that bytes came from an authorized prospective send.

Freeze:

`IMMUTABLE_CAPTURE_CONTENT != AUTHORIZED_CAPTURE_PROVENANCE`.
`CAPTURE_ARCHIVE_EXACT_RELOAD != ACQUISITION_AUTHORITY`.
`PUBLICLY_CONSTRUCTIBLE_CAPTURE != OFFICIAL_LIVE_ACQUISITION_PROOF`.
`LEGACY_LOCALFETCHER_DEBA_RESPONSE != TRUSTED_CAPTURE_LINEAGE`.
`ARCHIVED_CAPTURE_EXISTENCE != PROSPECTIVE_CAPTURE_AUTHORITY`.
`CAPTURE_IDENTITY != CAPTURE_ACQUISITION_LINEAGE`.

No currently wired, authorized pre-root Deba producer exists.  The future design
therefore requires a distinct, exact prospective acquisition-lineage receipt before
Phase110 may issue production identity persistence.  It must bind the reviewed
campaign/request authorization, current claim/capability as applicable, canonical Deba
URL, exact target, exact Phase105-style actual-send/terminal observation, one actual
send with no retry/fallback, capture ID, response SHA-256, observation timestamp,
successful capture archive save/exact reload, and reviewed source/runtime ancestry.
This is a companion binding over existing authorities, not a change to Phase104/105
canonical payloads.  A bare capture ID cannot satisfy it.

The preferred future wiring is one normal prospective race-day Deba acquisition:

`authorized provider send once -> exact response bytes -> trusted immutable capture ->
capture archive exact reload -> legacy parsing/enrichment -> Phase110 identity
extraction/persistence`.

Both consumers receive the identical response bytes; Phase110 never issues a second
Deba request.  If this single boundary cannot be introduced without changing provider
semantics beyond a separately approved scope, it is a prerequisite blocker rather than
a justification for a second fetch.

`PHASE110_MUST_NOT_CREATE_REDUNDANT_DEBA_REQUEST`.
`ONE_OPERATIONAL_DEBA_ACQUISITION_MAY_FEED_MULTIPLE_DOWNSTREAM_CONSUMERS`.
`SAME_RESPONSE_BYTES_REQUIRED_FOR_CAPTURE_AND_IDENTITY_EXTRACTION`.

Only after that lineage is exact-reloaded may a generic identity-only extractor derive
the existing canonical race form `nar:YYYYMMDD:babaCode:raceNo` from the reviewed
canonical Deba URL/query semantics and require equality with the target.  It may reuse
Phase88's structural checks, but must derive all rows from the supplied capture and
must not retain its fixed target, fixed 1..14 population, fixture hash, or bundle
identity.

For every identity-bearing row it requires exactly one canonical horse-number token
and one canonical official horse link/provider identity under the exact parent race.
It does not require odds, popularity, jockey, trainer, weight, or positive status.
It fails closed on missing/malformed/duplicate horse number, ambiguous/missing link,
wrong host/scheme/page, duplicate provider horse identity where prohibited, duplicate
external entry identity, wrong parent race, or an identity-bearing row silently
dropped.  A cancellation/exclusion marker may be retained as opaque source context,
but does not determine identity existence or status.

`PHASE88_FROZEN_TARGET_RULES != GENERIC_PRODUCTION_EXTRACTOR`.

### Proposed persistence and provenance authority

The audit supports an additive main-database migration rather than reinterpretation of
V010.  The future Phase110 design should introduce a versioned provider-identity
registry plus a content-addressed `NARProspectiveIdentityPersistenceReceiptV1` (exact
name subject to implementation review).  The registry must have restrictive parent
race/entry foreign keys and enforce, per canonical NAR provider namespace:

- one canonical external race ID to one internal `races.id`, with reverse uniqueness;
- one complete canonical external entry population to race-scoped `horses.id` values;
- unique external entry IDs and unique internal entry IDs within the target;
- each internal entry's `race_id` equals the receipt's internal race;
- durable origin type `phase110_prospective_identity`, never a V010/snapshot/fixture/
  JRA/unknown substitute; and
- an identity-only non-selection state until separately admitted.

The receipt canonically binds organisation/source system, external race ID, internal
race ID, exact Deba capture identity/canonical URL/content digest, ordered external
entry ID/external horse ID/horse number/internal entry ID tuples, population count and
digest, issuer provenance, issuance time, schema/semantic version and its own
content-addressed identity.  It is append-only, exact-reloadable and rejects conflicts,
ambiguous legacy rows, incomplete/extra population, stale target/capture ancestry, or
any origin not issued by the reviewed Phase110 path.

`IDENTITY_ORIGIN_MUST_BE_DURABLY_DISTINGUISHABLE`.
`INTERNAL_ID_ORIGIN != EXTERNAL_IDENTITY_OBSERVATION`.
`EXTERNAL_IDENTITY_OBSERVATION != BINDING_AUTHORITY`.
`BINDING_AUTHORITY != V010_ROW_EXISTENCE`.
`V010_ROW_EXISTENCE != PHASE109_RECEIPT_AUTHORITY`.

The Phase110 transaction may allocate the established SQLite internal IDs only after
the source extraction and exact target binding succeed; enumeration, horse number,
external ID and hashes never supply IDs.  Existing unproven legacy collisions fail
closed rather than being silently reused.  V010 may later be checked for consistency,
never used as origin authority.

### Temporal ordering and Phase109/108 handoff

Phase110 identity issuance is prospective upstream ingestion only after the new exact
acquisition-lineage authority has been reviewed and issued.  The capture used for a
future Phase109 mapping prerequisite must be bound to the target/cutoff and, absent a
narrower future proof, satisfy `capture.observed_at <= prediction_information_cutoff`.
Post-cutoff capture cannot prove the pre-root universe.  It must complete, persist and
exact-reload before the Phase109 mapping receipt; it cannot use the Phase108 root's
current Deba capture retrospectively.  It also must not create duplicate provider load.

`IDENTITY_PERSISTENCE_DESIGN != NEW_PROVIDER_REQUEST_AUTHORIZATION`.
`MAPPING_PREREQUISITE_MUST_NOT_CREATE_REDUNDANT_PROVIDER_LOAD`.
`IDENTITY_PERSISTENCE_MUST_PRECEDE_PHASE109_MAPPING_RECEIPT`.
`PHASE109_MAPPING_RECEIPT_MUST_PRECEDE_PHASE108_ROOT_START`.
`MAPPING_LOOKUP_AFTER_ENVELOPE_START != PRESTAGED_MAPPING_AUTHORITY`.
`POST_C_CAPTURE != PRE_C_IDENTITY_MAPPING_AUTHORITY`.

The intended handoff is:

`authorized prospective Deba acquisition lineage -> Phase110 exact identity universe
-> internal row adoption/controlled missing-ID issuance -> Phase110 receipt exact
reload -> Phase109 production mapping binder/receipt -> Phase108 prestaged-input
manifest -> target root start`.

Phase109 reads only approved Phase110 receipts, verifies current target/cutoff and full
entry population, and may use V010 only as consistency evidence.  It does not infer
origin from a generic persisted mapping row.

This does not prove historical availability merely from a present database row:
`CURRENT_DB_MAPPING_EXISTENCE != HISTORICAL_MAPPING_AVAILABILITY_PROOF`.  The receipt's
prospective capture/issuance provenance is the required availability evidence.  The
future campaign still needs separately reviewed timing/cutoff scheduling before this
pre-root activity can be considered available for a specific target.

### Architectural revision — row adoption, issuance and durable nonselection

The preferred post-review ordering is deliberately not identity-placeholder-first:

1. normal race-list ingestion has already created one exact parent `races` row;
2. one trusted, lineage-authorized Deba acquisition is made and archived;
3. existing legacy parsing/enrichment runs over those same bytes and persists its
   ordinary parser-produced rows;
4. Phase110 independently extracts the complete identity universe from those exact
   bytes;
5. it adopts an existing `horses.id` only after exact parent-race and canonical provider
   horse-identity agreement;
6. it issues internal entry rows only for identity-bearing entries absent from normal
   persistence (for example cancellation/exclusion rows);
7. every such new row is durably `IDENTITY_ONLY` and non-selectable; and
8. it saves the complete binding/origin graph and immutable receipt.

This preserves ordinary non-cancelled legacy enrichment before any identity-only row
exists, so current `save_horse()` duplicate suppression cannot prevent that enrichment.
For a later repeat/enrichment path, a narrowly approved `save_horse()` adoption branch
must recognise only an exact Phase110 identity-only row, recheck exact parent race and
canonical horse identity, update compatible enrichment fields, and retain the explicit
nonselection state.  It must reject any mismatch and must not grant ACTIVE, market or
prediction eligibility.  All non-Phase110 duplicate behaviour stays unchanged.

`IDENTITY_ONLY_INSERTION_MUST_NOT_BLOCK_LATER_ENRICHMENT`.
`DUPLICATE_SUPPRESSION != SAFE_IDENTITY_ENRICHMENT`.

Race adoption requires canonical Deba URL -> canonical external race ID -> exact target
ancestry -> exactly one existing `races.id`.  The legacy
`(date, organization, place, race_no)` key alone is never sufficient.  This Phase110
design does **not** issue a missing parent race: no exact unique existing row is a
fail-closed prerequisite failure, because its own independent race-list creation
authority has not been designed here.

Entry adoption first requires that proven parent race, then exact horse number under
that parent **and** canonical equivalence between `horses.horse_detail_url` and the
captured provider horse identity.  A malformed/noncanonical stored URL, absent row,
duplicate candidate, wrong parent race or provider-identity mismatch fails closed for
adoption.  Only a truly absent captured identity may take the controlled identity-only
issuance branch.

`LEGACY_RACE_LOOKUP_KEY != CANONICAL_NAR_RACE_BINDING`.
`HORSE_NUMBER_WITHOUT_EXACT_PARENT_RACE != ENTRY_BINDING_AUTHORITY`.
`HORSE_NUMBER_ONLY_MATCH != EXISTING_INTERNAL_ENTRY_ADOPTION`.
`EXISTING_INTERNAL_ROW_ADOPTION_REQUIRES_PROVIDER_IDENTITY_CONSISTENCY`.

The companion schema must be additive and distinct from V010.  It must persist
canonical external-race -> internal-race bindings; complete external-entry ->
internal-entry bindings; canonical provider-horse identity; exact acquisition/capture
lineage; a closed issuance disposition (`ADOPTED_EXISTING_INTERNAL_ID` or
`ISSUED_IDENTITY_ONLY_INTERNAL_ID`); explicit durable identity-only nonselection; and
an append-only content-addressed receipt with restrictive ancestry.  Legacy rows obtain
Phase110 authority only by a successful explicit binding record.  Unrelated, ambiguous
or merely pre-existing rows remain unqualified.

`PHASE110_IDENTITY_ORIGIN_REGISTRY != V010_MAPPING_CONSISTENCY_LAYER`.
`LEGACY_ROW_EXISTENCE != PHASE110_ORIGIN_AUTHORITY`.
`IDENTITY_ONLY_ROW != PREDICTION_INPUT`.
`IDENTITY_ONLY_DENIAL_MUST_BE_DURABLE_NOT_INFERRED`.

The durable nonselection query must consult this explicit Phase110 provenance/class
only; it may not infer an answer from NULLs, zero odds, empty name/jockey, missing past
races, cancellation text or field completeness.  It is a negative safety gate only:
it means “do not send this identity-only row to legacy prediction,” not ACTIVE,
eligible, market-eligible, or status-complete.  It must be applied at the current
`DatabaseRaceInputProvider.load() -> get_horses_by_race()` selection boundary and
audited for every other selectable-entry reader.

`PHASE110_NONSELECTION_GATE != POSITIVE_ENTRY_STATUS_AUTHORITY`.
`NOT_IDENTITY_ONLY != ACTIVE`.
`LEGACY_ENRICHMENT_PRESENT != OFFICIAL_ENTRY_ELIGIBILITY`.

For controlled missing-entry issuance, the internal row, origin/binding graph and
receipt payload must be transactionally inseparable.  The reviewed atomic boundary must
cover exact trusted acquisition-lineage verification; parent-race adoption; complete
identity-universe validation; exact existing-row adoption; missing internal-ID
issuance; binding/origin persistence; explicit identity-only nonselection; immutable
receipt publication; and exact reload/qualification.  If the storage implementation
cannot include reload in the transaction, same-transaction canonical readback must
prove the committed candidate before commit, and a post-commit exact reload must occur
before any caller may consume Phase110 authority.  A crash before commit leaves no
issued row; a committed ID always has durable origin and nonselection even if later
receipt qualification/reload fails.  Such a row remains unqualified and unusable as
Phase110 authority until exact receipt reload succeeds; it cannot be repaired by
reconstruction or later backfill.

`INTERNAL_ID_ISSUANCE_WITHOUT_DURABLE_ORIGIN != PHASE110_AUTHORITY`.

The pre-root identity capture and the later Phase108 root capture can be distinct only
because the former establishes prospective identity availability before C/root start,
while the latter remains the target snapshot/freeze measurement at root dispatch.
Neither is a benchmark-only repeat; each must have independently reviewed operational
purpose, and an implementation must reuse a lawful same-time observation where the
contracts permit it.

`MEASUREMENT_CAMPAIGN_MUST_NOT_GENERATE_REDUNDANT_PROVIDER_LOAD`.

### Phase95 / Phase41 separation and current decision

Phase110 can define the identity universe without deciding which identities are
ACTIVE, cancelled, eligible, marketable, predicted or bettable.  Phase95's complete
positive-status source semantics and Phase41 market eligibility remain separate.
However, Phase110 implementation is blocked unless the identity-only non-selection
gate is proven not to let newly persisted rows enter current prediction paths.  This
is a compatibility guard, not a resolution of Phase95/41.

Design decision: an independent production identity producer does **not** exist today;
the accepted direction is a new, status-independent, provenance-bearing identity
persistence capability (Outcome C).  Implementation is blocked pending a trusted
single-send ingestion prerequisite and resolution of the legacy writer/reader safety
conditions below.  It does not authorize a live campaign:

`PRODUCTION_MAPPING_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.
`MAPPING_AUTHORITY_COMPLETE != CONCRETE_DELTA_AUTHORITY`.
`PRODUCTION_MAPPING_AUTHORITY_PRECEDES_OFFICIAL_OPERATIONAL_TIMING_CAMPAIGN`.

### Final implementation blockers

`NAROfficialLiveResponseCaptureService` is a trusted exact-byte capture/persistence
primitive, but does not itself prove campaign/workflow authorization for the request.
Ordinary `LocalFetcher` still uses `NARProvider.fetch_deba_table()` and therefore does
not naturally yield trusted capture lineage.  A constructed capture or archive reload
alone cannot satisfy that lineage.  The required upstream prerequisite is a reviewed
single-send prospective Deba boundary that authorizes one canonical target request,
performs exactly one actual provider send, captures and exact-reloads immutable bytes,
and fans those same bytes to legacy enrichment and Phase110 extraction.

`PHASE110_MUST_NOT_CREATE_REDUNDANT_DEBA_REQUEST`.
`ONE_OPERATIONAL_DEBA_ACQUISITION_MAY_FEED_MULTIPLE_DOWNSTREAM_CONSUMERS`.
`SAME_RESPONSE_BYTES_REQUIRED_FOR_CAPTURE_AND_IDENTITY_EXTRACTION`.
`TRUSTED_DEBA_ACQUISITION_AUTHORITY != PHASE110_IDENTITY_PERSISTENCE_AUTHORITY`.
`TRUSTED_DEBA_ACQUISITION_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.

The current `save_horse()` performs a `(race_id, horse_no)` existence check and later
inserts through another connection.  The schema has no reviewed database-level unique
constraint that makes concurrent Phase110 issuance safe.  Phase110 must not race this
legacy writer or rely on assumed serial execution.  A missing-row insertion and its
origin/binding/identity-only provenance must share one atomic ownership boundary.

`APPLICATION_LEVEL_HORSE_EXISTS_CHECK != ATOMIC_ENTRY_ID_ISSUANCE`.
`CHECK_THEN_INSERT_ACROSS_CONNECTIONS != UNIQUE_IDENTITY_AUTHORITY`.
`PHASE110_ISSUANCE_MUST_NOT_RACE_LEGACY_SAVE_HORSE`.

If Phase110 inserts a missing identity-only `horses` row, current `save_horse()` later
sees `(race_id, horse_no)` and returns without enriching it.  A reviewed compatible
enrichment/adoption path is required; it must keep explicit nonselection until a
separate status/eligibility authority changes it.  Enrichment cannot infer ACTIVE.

`IDENTITY_ONLY_INSERTION_MUST_NOT_BLOCK_LATER_ENRICHMENT`.
`DUPLICATE_SUPPRESSION != SAFE_IDENTITY_ENRICHMENT`.

`DatabaseRaceInputProvider.load()` calls `database.get_horses_by_race(race_id)` and
places every returned row into `RacePredictionInput`; the prediction pipeline then
evaluates that supplied population.  A partial CLI-only guard is insufficient.  A
future implementation must audit all production `horses` readers and prove each path
that can feed prediction/bet selection uses one reviewed eligibility-filtering
repository boundary or independently enforces the exact same explicit Phase110
nonselection authority.  If complete reader coverage cannot be proven, identity-row
issuance remains blocked.

`ALL_HORSES_QUERY != PREDICTION_ELIGIBLE_POPULATION`.
`IDENTITY_ONLY_DENIAL_MUST_BE_ENFORCED_BEFORE_RACE_PREDICTION_INPUT`.

### Recommended prerequisite phase — design only

`POST_V0_8_DAILY_REPLAY_111`

Title: `NAR Trusted Single-Send Deba Acquisition and Identity-Ingestion Boundary`

Phase111 should design the single prospective Deba acquisition boundary required by
Phase110: explicit prospective request authority; exact canonical target/URL; exactly
one actual send; no retry/fallback unless separately reviewed; immutable capture and
exact archive reload; unforgeable acquisition lineage; same-response fan-out to legacy
enrichment and later Phase110 extraction; no redundant provider load; deterministic
no-network testability; and exact relation to Phase104/105 timing authority without
promoting diagnostic authority.

Phase111 must not create Phase110 internal entry IDs, solve Phase95 status semantics,
grant market eligibility, choose Delta, or authorize a live timing campaign.

Expected dependency chain:

`Phase111 trusted single-send prospective Deba acquisition -> return to Phase110
identity-complete persistence implementation -> Phase109 production mapping authority
-> Phase108 prestaged manifest -> PRE_C root -> operational timing audit`.

Phase95 and Phase41 remain independent downstream blockers.

### Proposed future implementation boundary

Allowed files, only if a later Phase110 implementation is separately approved:

- `scripts/migrations/runner.py` and one new additive migration under
  `scripts/migrations/versions/`;
- `scripts/database.py` for the controlled identity-only adoption/enrichment branch,
  the atomic issue path, and the narrow explicit-provenance exclusion at the sanctioned
  selectable-entry read boundary;
- new `scripts/simulation/nar_prospective_identity_persistence.py` and a SQLite
  repository module for acquisition-lineage validation, receipt/registry issue and
  exact reload;
- a new narrow composition adapter that makes the existing trusted official-response
  capture service the single normal Deba acquisition boundary for legacy enrichment and
  Phase110 extraction, only if provider/request semantics remain unchanged;
- new focused Phase110 tests and narrowly related database/migration tests;
- `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`.

Forbidden without a later explicit contract: `HorseParser`, NAR provider/request URL
semantics, current historical normalizers, snapshot builder, Phase108 authority
payloads, V010 meanings, Phase95/41 logic, prediction/strategy semantics beyond the
narrow non-selection guard, production databases, provider HTTP and live campaigns.

### Required future tests

The later contract must prove all of the following with deterministic fake adapters and
temporary databases only:

- an arbitrary constructed `NAROfficialResponseCapture`, a capture ID alone, and an
  archive reload alone cannot issue Phase110 authority; exact authorised prospective
  acquisition lineage is required;
- the one Deba response's exact bytes feed trusted capture, legacy enrichment and the
  Phase110 extractor; Phase110 sends no second request and adds no retry/fallback;
- canonical external-race derivation, exact one-race adoption and fuzzy/legacy-key-only
  race matching rejection; missing or duplicate parent race fails closed;
- generic identity extraction retains a cancelled identity-bearing row, requires no
  odds/status for existence, rejects malformed/ambiguous rows, duplicate horse number,
  duplicate external entry/provider-horse identity and wrong target ancestry;
- exact existing entry adoption requires the proven parent race and canonical provider
  horse identity; horse-number-only adoption and wrong external-horse identity fail;
- a missing cancelled entry receives a controlled SQLite internal ID, and its row,
  origin graph and receipt are atomic; a crash before qualification cannot leave usable
  authority;
- later compatible enrichment of a Phase110 identity-only row is safe and does not
  silently block on duplicate suppression, while mismatched enrichment is rejected;
- explicit provenance, not NULL/zero-field heuristics, excludes identity-only rows
  from prediction input; that exclusion neither proves ACTIVE nor market eligibility;
- legacy rows without a Phase110 binding cannot masquerade as qualified authority;
  V010 snapshot-derived rows remain distinct consistency evidence; Phase88 remains
  fixture-only; and no enumeration/horse-number/hash supplies an internal ID;
- post-cutoff capture is rejected for a pre-cutoff mapping receipt; Phase109 can consume
  only an exact successful Phase110 receipt; and Phase108 still rejects root start
  absent a preclosed mapping authority;
- canonical receipt identity, exact reload, append-only conflict, full population,
  internal-entry uniqueness/reverse mapping, no duplicate provider request, no provider
  HTTP and no production-database write in tests.

### Stop conditions and downstream blockers

Stop a future implementation rather than guessing if `horses.id` cannot safely retain
race-entry semantics; a cancelled identity row could enter prediction through an
uncovered reader; canonical NAR race identity is not uniquely bindable; complete
identity persistence needs positive status semantics; a synthetic ID is necessary;
the only candidate is a bare/archive-only/Phase108-root capture; the normal ingestion
cannot be made a single trusted capture boundary without broader provider semantics;
existing parent/entry adoption is ambiguous; later enrichment cannot safely adopt an
identity-only row; V010 would need reinterpretation; or Phase95 must be solved first.

After Phase110, Phase109 mapping receipt implementation/review, prospective official
campaign authorization, complete Phase108/109 pre-root composition for a chosen
campaign, Phase95 status semantics, Phase41 eligibility and the operational timing
audit remain blockers.  No concrete Delta follows from this phase.

---

## Historical record — POST_V0_8_DAILY_REPLAY_109

Title: NAR Production Internal Race and Entry Mapping Authority

Status: WAITING_FOR_PHASE_INSTRUCTION

Formal Status: ARCHITECTURAL_AUDIT_COMPLETE

State: BLOCKED_PENDING_IDENTITY_COMPLETE_INGESTION_PREREQUISITE

Outcome: PHASE109_PRODUCTION_ENTRY_MAPPING_BLOCKED_BY_IDENTITY_COMPLETE_INGESTION

Audit: NAR_PRODUCTION_INTERNAL_RACE_AND_ENTRY_MAPPING_AUTHORITY_DESIGN_COMPLETE

`PHASE109_REVISED_ARCHITECTURAL_REVIEW_PASS`.
`POST_V0_8_DAILY_REPLAY_109 = ARCHITECTURAL_AUDIT_COMPLETE`.
`PHASE109_IMPLEMENTATION = BLOCKED_NOT_AUTHORIZED`.

Base Commit and Branch: `6fc980ab89695b4a083d5e7b4d4811a7ec294d90` / `feature/post-v0.8-daily-replay`

Base Tree: `db06291060dfeebb146a376f27a53b597bff2eae`

### Phase108 reconciliation and boundary

`POST_V0_8_DAILY_REPLAY_108 = FORMALLY_COMPLETE`.
`NAR_TARGET_SCOPED_PRE_C_CRITICAL_PATH_ENVELOPE = FORMALLY_INTEGRATED`.
`FINAL_COMMIT_SEALED_SOURCE_VERIFICATION = PASS`.

Phase108 proves only the no-network target-root mechanics. It does not supply a production NAR internal race/entry identity source, and formal completion does not authorize provider HTTP, a live campaign, or a concrete Delta. `LIVE_CAMPAIGN_AUTHORIZATION = BLOCKED` and `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remain frozen.

The unresolved precondition is that `build_historical_input_snapshot(...)` still accepts caller-supplied `internal_race_id` and `race_entry_id_by_external_entry_id`. The Phase108 fixture manifest proves only an exact diagnostic fixture mapping. It is not production authority.

`CALLER_SUPPLIED_INTERNAL_MAPPING != PRODUCTION_MAPPING_AUTHORITY`.
`INTERNAL_RACE_ID_ARGUMENT != INTERNAL_RACE_AUTHORITY`.
`RACE_ENTRY_MAPPING_REQUIRES_AUTHORITATIVE_PARENT_RACE_BINDING`.
`HORSE_NUMBER != INTERNAL_RACE_ENTRY_ID`.
`ENTRY_ENUMERATION != INTERNAL_RACE_ENTRY_ID`.
`HASH_DERIVATION != INTERNAL_RACE_ENTRY_ID`.
`EXTERNAL_ENTRY_ID != INTERNAL_RACE_ENTRY_ID`.
`FIXTURE_MAPPING_AUTHORITY != PRODUCTION_MAPPING_AUTHORITY`.

### Architectural-review revision — authoritative disposition

`PHASE109_ARCHITECTURAL_REVIEW_REQUIRES_REVISION`.
`PHASE109_IMPLEMENTATION_APPROVAL = NOT_GRANTED`.

The revised audit ends in a specific architectural blocker, not an implementation-ready design:

`PHASE109_PRODUCTION_ENTRY_MAPPING_BLOCKED_BY_IDENTITY_COMPLETE_INGESTION`.
`PHASE109_MAPPING_AUTHORITY_REQUIRES_STATUS_INDEPENDENT_ENTRY_IDENTITY_PERSISTENCE`.

The following layering is mandatory and must not be collapsed by a future receipt:

```text
internal ID origin authority
!= external NAR identity observation authority
!= binding authority
!= V010 persisted relation
!= Phase109 immutable mapping receipt
```

`INTERNAL_ID_ORIGIN != EXTERNAL_IDENTITY_OBSERVATION`.
`EXTERNAL_IDENTITY_OBSERVATION != BINDING_AUTHORITY`.
`BINDING_AUTHORITY != V010_ROW_EXISTENCE`.
`V010_ROW_EXISTENCE != PHASE109_RECEIPT_AUTHORITY`.

`V010_MAPPING_ROW_EXISTENCE != INDEPENDENT_PRODUCTION_MAPPING_AUTHORITY`.
`SNAPSHOT_SAVE_DERIVED_MAPPING != PRE_SNAPSHOT_MAPPING_AUTHORITY`.
`READ_ONLY_RELOAD_CANNOT_LAUNDER_CALLER_SUPPLIED_MAPPING`.
`PERSISTED_RELATION != PROVENANCE_OF_RELATION`.

`STATUS_FILTERED_HORSE_ROWS != COMPLETE_NAR_ENTRY_IDENTITY_UNIVERSE`.
`CANCELLED_ENTRY != NONEXISTENT_ENTRY_IDENTITY`.
`ENTRY_STATUS_INTERPRETATION != ENTRY_IDENTITY_BINDING`.
`OMITTED_CANCELLED_HORSE_ROW != AUTHORIZED_MAPPING_ABSENCE`.
`HORSES_TABLE_POPULATION != COMPLETE_MAPPING_POPULATION_UNLESS_PROVEN`.

`ROOT_CURRENT_DEBA_CAPTURE != PRE_ROOT_MAPPING_AUTHORITY`.
`PHASE88_FIXTURE_BINDER != DYNAMIC_PRODUCTION_MAPPING_PRODUCER`.

### Authority inventory

| Candidate | Inputs and output | Existing authority and integrity | Phase109 assessment |
| --- | --- | --- | --- |
| `scripts/migrations/versions/v010_historical_input_snapshot_schema.py` | Defines provider-scoped external race/entry relations to existing internal IDs. | `historical_input_external_races` has the provider-scoped primary key, reverse uniqueness, and FK to `races`; `historical_input_external_entries` has the provider-scoped entry key, reverse uniqueness, parent-race FK, and `(race_id,id)` horse-membership FK. | A relational consistency layer only. V010 stores neither the independent origin of an internal ID nor the provenance of the external-to-internal binding. Row existence is not self-authenticating production authority. |
| `scripts/simulation/sqlite_nar_daily_evidence_resolver.py::_prediction` | exact NAR external race → internal race | Requires one forward row, one matching reverse row, and an existing `races.id`; absent map is `INTERNAL_RACE_MAPPING_MISSING`. | A race-only read-side precedent. It neither returns a complete entry map nor issues immutable pre-start authority. |
| `scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py` | caller-supplied snapshot identities and IDs → source identity/V010 rows → snapshot | `save_snapshot()` calls `_ensure_mappings()` before the snapshot header; `_ensure_external_race()` and `_ensure_external_entry()` insert absent V010 rows using `snapshot.internal_race_id` and each caller-supplied `entry.race_entry_id`. | **Snapshot-derived writer.** This is production-capable persistence, but circular for Phase109: a later read-only reload cannot prove that its mapping existed independently before the supplied snapshot mapping. Current V010 schema has no origin discriminator to distinguish these rows afterward. |
| `scripts/simulation/nar_race_entry_status_replay_identity_binding.py` | frozen Phase85 V3 Deba identity rows + V010 tables → complete internal binding | Read-only, query-only, schema-validated, full-set checked; validates parent race, entry membership, and horse number as a consistency check. | Strong implementation pattern, but hard-coded to the one published 2025-01-01 / baba 21 / race 6 fixture. It is not a dynamic production NAR campaign producer. |
| `scripts/database.py`, `scripts/fetch_local.py`, `scripts/parsers/nar_parser.py`, `scripts/parsers/horse_parser.py`, `scripts/models.py` | legacy NAR pages → `races.id` / `horses.id` | `save_race()` and `save_horse()` allocate SQLite AUTOINCREMENT IDs. The race row holds date/place/race number/deba URL, but no exact provider external-race identity contract or enforcing uniqueness. Horse rows hold `race_id`, `horse_no`, and descriptive fields, but no exact external entry/horse identity. `HorseParser._is_cancelled()` skips cancellation/exclusion rows before `Horse` construction. | The only ordinary NAR internal-ID origin path, but it is neither a canonical external binding producer nor identity-complete. `races.id` is only partial internal-race evidence; `horses.id` cannot prove a complete NAR entry universe. |
| `scripts/simulation/repositories/sqlite_race_entry_source.py` | selected internal horse IDs → same race-entry IDs | Read-only internal selection resolver over `horses`. | Not an external-NAR-to-internal mapper. It cannot establish the parent race or external entry mapping. |
| `scripts/simulation/repositories/sqlite_jra_race_replay_seed_repository.py` / V015 | reviewed JRA source material → newly created internal IDs and V010 relations | Creates `historical_input_source_identities`, `races`, `horses`, and external mapping rows under its JRA seed proof. | **Independently authoritative producer for JRA only.** It cannot establish any NAR mapping and must not be generalized by provider substitution. |
| Phase108 `NARPreCPrestagedInputManifestV1` | fixture SHA + tuple of external-entry → internal-entry values | Diagnostic fixture-specific content authority; its target scope receives caller `internal_race_id`. | Correct for sealed rehearsal only. It cannot promote a fixture mapping or its diagnostic schema into production authority. |

### Race and entry findings

NAR normalization in `scripts/simulation/nar_historical_input_source.py` deterministically emits `nar:YYYYMMDD:babaCode:raceNo` and `<external_race_id>:entry:<horse_no>`. These are source/provider identities. They are not database IDs, and neither entry order, horse name, jockey, approximate date/place, row position, a hash, nor horse number alone may bind them to internal rows.

**Race finding: `RACE_BINDING_AUTHORITY_PARTIAL`.** V010 can prove relational consistency for a pre-existing `(NAR, nar_official, external_race_id)` row: one internal race ID, a reverse uniqueness check, and an FK to `races`. It cannot prove how that relation was produced. The legacy NAR writer allocates `races.id` from parsed race-list fields, but does not persist the canonical `nar:YYYYMMDD:babaCode:raceNo` identity as an independently observed binding. `deba_table_url` is legacy descriptive data, not a reviewed canonical-NAR-identity uniqueness contract. Therefore `INTERNAL_RACE_ID_ARGUMENT != INTERNAL_RACE_AUTHORITY` remains true.

**Entry finding: `ENTRY_BINDING_AUTHORITY_PARTIAL_AND_IDENTITY_INCOMPLETE`.** V010's entry relation and `(internal_race_id, race_entry_id)` FK prove parent ancestry only after a row exists. The ordinary NAR path obtains `horses.id` only for `HorseParser` output; `HorseParser._is_cancelled()` skips rows containing `取消`, `除外`, `競走除外`, or `出走取消` before any `Horse` exists or is saved. A cancelled identity-bearing DebaTable row may consequently have no ordinary `horses` row or V010 row. The implementation has no general persisted external entry/horse identity field for that omitted row. Horse number is usable only as a post-binding contradiction check under a proven race binding, never as a producer or global key.

The V010 writer audit is closed as follows:

| Writer/path | Classification | Independent external observation? | Internal IDs already caller/producer supplied? | Durable origin distinguishable afterward? |
| --- | --- | --- | --- | --- |
| V010 migration | migration/schema only | No | No | No rows are produced. |
| `SQLiteHistoricalInputSnapshotRepository.save_snapshot()` → `_ensure_mappings()` | snapshot-derived writer | Snapshot caller supplies source identity/entries | Yes: `internal_race_id` and `race_entry_id` already exist in the supplied snapshot | **No.** V010 has no producer-kind, receipt, or pre-snapshot-origin column. |
| JRA replay seed repository | independently authoritative producer, JRA only | Yes, through reviewed JRA seed/source chain | It creates its own IDs when needed | JRA seed proof exists; it is inapplicable to NAR. |
| Phase88 fixture binder / NAR daily resolver | read-only consumers | No new observation | No new IDs | They write no V010 rows and cannot remedy provenance. |
| tests/fixtures | test/fixture writers | Fixture only | Test-controlled | Never production authority. |

The evidence-supported revised outcome is **C plus D**: a relational V010 layer exists, but no independently provenance-bearing, identity-complete NAR producer exists today. A generic read-only receipt over extant V010 rows is **not** an implementation-safe Phase109 solution. It must fail closed rather than populate, repair, enumerate, hash-map, or launder a caller-derived relation.

### Temporal and anti-hindsight conclusion

`CURRENT_DB_MAPPING_EXISTENCE != HISTORICAL_MAPPING_AVAILABILITY_PROOF`.

For historical replay, present-day V010 rows cannot prove they existed at a past cutoff. Phase109 must never backdate a receipt or use current mapping existence to validate historical availability. For a future prospective campaign, the mapping is limited to stable identity correspondence, not a race-status, odds, result, or feature claim. A controlled read before the target root, recorded with a campaign-owned UTC issuance time and exact mapping payload, may prove **prospective pre-start availability** only. It does not prove historical availability and cannot resolve Phase94/95/41 semantics.

`MAPPING_LOOKUP_AFTER_ENVELOPE_START != PRESTAGED_MAPPING_AUTHORITY`.
`PRODUCTION_MAPPING_AUTHORITY_PRECEDES_OFFICIAL_OPERATIONAL_TIMING_CAMPAIGN`.
`PRODUCTION_MAPPING_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.
`MAPPING_AUTHORITY_COMPLETE != CONCRETE_DELTA_AUTHORITY`.

### Conditional future immutable mapping authority

**No Phase109 implementation is currently authorized or possible.** Only after an upstream, independently provenance-bearing and status-independent NAR identity producer exists may a later reviewed phase add an immutable `NARProductionInternalRaceEntryMappingAuthorityV1` with a content-addressed identity such as `nar-production-internal-race-entry-mapping-v1:<sha256>`. Its canonical payload must bind:

* exact `NAR` / `nar_official` source-system identity and external race ID;
* exact internal race ID and the checked parent `races` row identity;
* canonical complete tuple of `(external_entry_id, race_entry_id, checked_horse_no)` entries;
* one-to-one forward and reverse entry/race population proof;
* exact upstream identity-producer receipt/identity-observation evidence, binding evidence, and V010 schema/topology fingerprint; V010 rows are consistency evidence, not the sole origin proof;
* source-of-truth descriptor, controlled read/issuance UTC time, target/cutoff/claim ancestry where available, and semantic/version;
* canonical entry ordering, expected entry population SHA, and a content SHA; and
* an explicit `PROSPECTIVE_PRESTART_IDENTITY_RELATION` temporal semantic.

The authority is invalid if its upstream binding is absent, snapshot-derived, unproven, or temporally incompatible; the race mapping is missing, duplicated, or reverse-inconsistent; any entry is missing, duplicated, cross-race, or maps twice; the internal horse row is absent; the horse number disagrees after binding; or the complete identity-bearing source set differs from the persisted mapping set. No cancellation/status filter, implicit extra-entry exception, or partial result is permitted. If a current source population is not yet available before root start, the authority still binds the complete independently observed expected population; Phase108-style prerequisite reconciliation must later prove exact equality with normalized current identities before snapshot construction, otherwise the root fails closed.

The artifact must be persisted in an explicit append-only mapping-authority companion, then exact-reloaded. The companion is not a normal Phase105/Phase108 bootstrap upgrade and is not a production mapping-table writer. Controlled issuance must require a held runner lock, current-process Phase104 capability, exact claim/session/target ancestry, a separately supplied `query_only` mapping-source connection, and the upstream producer's immutable provenance. It must validate the exact V010 schema, foreign keys, and uniqueness under an owned read transaction that it rolls back; it must never create, update, attach, repair, or close the mapping source.

### Phase108 integration boundary

Phase108 V1 remains a diagnostic-only, fixture-bound authority family and must not be rewritten or promoted. Its manifest currently requires diagnostic fixture content for `mapping_content_authority`; changing that V1 payload would change its identity and is outside Phase109.

The Phase109 mapping authority is therefore an additive prerequisite for the **future official Phase107/Phase108-style prestaged manifest**, not a replacement for the diagnostic V1 manifest. The required ordering remains:

```text
read exact V010 mapping relation (query_only)
→ construct mapping authority
→ persist and exact-reload mapping authority
→ bind its identity and complete expected population into the future official prestaged manifest
→ exact-reload manifest and validate target/cutoff/claim ancestry
→ issue target-root start evidence
→ current normalization proves mapping population equality
→ snapshot assembly
```

No mapping lookup occurs after root start. No current Phase108 root timing rule changes: the mapping authority must be durable before `ENVELOPE_START_AUTHORITY_MUST_PRECEDE_FIRST_CAUSAL_OPERATION`, the root remains the sole additive elapsed owner, and a valid snapshot remains insufficient without execution-plan/prerequisite reconciliation. The later official-manifest implementation requires its own approved authority phase; Phase109 does not authorize that composition itself.

### Required upstream dependency and future implementation boundary

The immediate prerequisite is a separate reviewed workstream for **status-independent, independently provenance-bearing NAR race/entry identity persistence**. It must observe every identity-bearing current DebaTable row before status interpretation, bind canonical NAR race and entry/horse identities to internally created IDs under exact parent race ancestry, preserve immutable producer provenance, and make the complete identity population retrievable without a snapshot caller supplying the result. It must not assign synthetic IDs, alter source identities, or infer absence from a cancellation marker.

`PHASE95_PROSPECTIVE_ENTRY_STATUS_SOURCE_SEMANTICS_OR_EQUIVALENT_STATUS_INDEPENDENT_IDENTITY_INGESTION = PREREQUISITE_TO_PHASE109_IMPLEMENTATION`.

Phase94 historical entry-status authority is not itself the identity producer, and Phase41 market eligibility is not a mapping requirement. Neither may be silently used to omit identities. The current Phase95-class prospective source/status boundary is the direct dependency because current NAR ingestion discards identity-bearing cancelled/excluded rows before `horses.id` issuance. If that workstream is not approved as the appropriate producer, a new narrowly scoped prerequisite phase must be designed before Phase109; Phase109 must not fabricate an Allowed Files code plan while this authority is absent.

Once that prerequisite is independently reviewed and integrated, a later Phase109 redesign may propose additive authority/archive/repository/bootstrap modules and focused tests. Its forbidden surface must retain Phase108 V1 domain/archive payloads, Phase99–105 canonical authority payloads, `historical_input_snapshot_builder.py`, NAR normalizers/capture code, legacy `database.py`, provider URLs/retries/TLS behavior, `database/keiba.db`, logs, Phase94/95/41 canonical semantics, and production mapping-table mutation. V010 may then remain consistency evidence only; the future authority must not seed or repair it.

### Required future tests and stop conditions

The prerequisite and any later Phase109 design must test exact race binding; complete entry binding; missing/duplicate/contradictory race mappings; missing/duplicate external entries; duplicate internal-entry assignment; wrong-race internal entry; horse-number consistency without horse-number lookup; incomplete and extra population; deterministic identity and exact reload; append-only conflict; stale/incompatible mapping; no enumeration/hash/external-entry-as-ID derivation; query-only/no-write enforcement; Phase108-style prestaged-manifest ancestry; durable mapping authority before root start; and proof that read capability cannot authorize a live campaign.

It must additionally prove that a V010 row created by `save_snapshot()` / `_ensure_mappings()` cannot establish independent authority; read-only reload cannot launder caller-supplied IDs; independently authoritative and snapshot-derived mappings are durably distinguishable or the latter is rejected; an identity-bearing cancelled entry cannot disappear; status interpretation does not decide identity existence; a status-filtered `horses` population cannot qualify without full exact proof; a duplicate horse number under a wrong parent race cannot bind; a canonical parent race must be proven before horse number is considered; the frozen Phase88 binder cannot accept an arbitrary target; and current-root Deba capture cannot retroactively authorize a prestaged mapping. All tests use temporary SQLite databases and fixtures only: no provider HTTP and no production DB writes.

Regression scope must include V010 migration, snapshot repository/builder, `sqlite_nar_daily_evidence_resolver`, Phase88 identity binding, and Phase108 envelope/reconciliation tests. A future full suite is required before implementation review.

Stop rather than implement if an independent status-independent NAR producer is unavailable; internal race/entry IDs cannot be given their exact producer meanings; V010 remains the only evidence of provenance; the V010 schema admits ambiguity without an authoritative discriminator; a dynamic NAR binding requires changed source identity semantics; cancellation/status completeness requires unresolved Phase95-class source semantics; a synthetic enumeration/hash is the only source; or provider evidence after the prediction cutoff would be needed to form the mapping.

### Remaining downstream blockers

Phase109 design does not authorize live execution. Remaining blockers include the upstream status-independent identity-complete NAR ingestion/provenance workstream; only then a re-reviewed Phase109 implementation; a future official (non-diagnostic) prestaged-manifest/campaign authority that can consume the mapping receipt; exact production target/current-entry control-plane authority; Phase94 historical entry-status authority; Phase95 prospective source semantics; Phase41 market eligibility; prospective official timing-campaign authorization; and `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`.

### Phase95 relationship and recommended prerequisite

Phase95 freezes `ENTRY_IDENTITY_UNIVERSE != OBSERVED_ENTRY_STATUS_UNIVERSE`. Complete status semantics are not required to define that an entry identity exists, but a status-independent identity persistence layer is required before Phase109 can issue a complete mapping authority. The broader Phase95 blocker `PROSPECTIVE_NAR_ENTRY_STATUS_AUTHORITY_CAPTURE_BLOCKED_SOURCE_SEMANTICS` remains unresolved and is not claimed solved here.

Recommended next phase concept (design only; not started):

`POST_V0_8_DAILY_REPLAY_110`

Title: `NAR Prospective Identity-Complete Race and Entry Persistence Authority`

Its scope is to preserve canonical external NAR race/entry identities, internally bind them under exact parent-race ancestry, include cancelled/withdrawn rows as identities, preserve durable provenance, and expose a complete read-only population. It must not decide positive ACTIVE semantics, full Phase95 status authority, market eligibility, concrete Delta, or live campaign authorization.

`IDENTITY_PERSISTENCE_AUTHORITY != ENTRY_STATUS_AUTHORITY`.
`IDENTITY_PERSISTENCE_AUTHORITY != MARKET_ELIGIBILITY`.
`IDENTITY_PERSISTENCE_AUTHORITY != LIVE_CAMPAIGN_AUTHORIZATION`.

The expected dependency chain is:

```text
Phase110 identity-complete persistence authority
→ Phase109 production mapping authority
→ Phase108 prestaged mapping manifest
→ PRE_C root start
→ later operational timing audit
```

Provider HTTP / production DB reads / production DB writes / live campaign: `0 / 0 / 0 / 0` for this PREPARE activity.

Next: `CHATGPT_PREPARE_PHASE110`.

---

## Historical record — POST_V0_8_DAILY_REPLAY_108

Title: NAR Target-Scoped PRE_C Critical-Path Envelope Wiring

Status: FORMALLY_COMPLETE

Formal Status: FORMALLY_COMPLETE

State: COMPLETED

Outcome: PHASE108_TARGET_SCOPED_PRE_C_ENVELOPE_FORMALLY_INTEGRATED

Audit: NAR_PRE_C_CRITICAL_PATH_ENVELOPE_WIRING_DESIGN_COMPLETE

Design Review: PHASE108_PRE_C_CRITICAL_PATH_ENVELOPE_WIRING_DESIGN_REVIEW_PASS

Implementation: NAR_TARGET_SCOPED_PRE_C_CRITICAL_PATH_ENVELOPE_IMPLEMENTED

Base Commit and Branch: `fefcda45ce9e01a13724209ae6012b81bbc0bd46` / `feature/post-v0.8-daily-replay`

### Final implementation and verification disposition

`PHASE108_IMPLEMENTATION_REVIEW_PASS`

`PHASE108_REVIEW_CORRECTIONS_VERIFIED`

`PHASE108_POST_COMMIT_SEALED_VERIFICATION_REVIEW_PASS`

`PHASE108_IMPLEMENTATION_COMMIT_REMOTE_VERIFICATION_PASS`

`POST_V0_8_DAILY_REPLAY_108 = FORMALLY_COMPLETE`

`NAR_TARGET_SCOPED_PRE_C_CRITICAL_PATH_ENVELOPE = FORMALLY_INTEGRATED`

`TARGET_SCOPED_PRE_C_ENVELOPE_CONTRACT = VERIFIED`

`FINAL_COMMIT_SEALED_SOURCE_VERIFICATION = PASS`

The reviewed implementation is authoritative in local and remote commit `f0bfaed77c86d266050e8e56afc4686936213492`, tree `66466e50cc36842c23daa7c42a180a66fbe7ecb3`, parent `fefcda45ce9e01a13724209ae6012b81bbc0bd46`. Phase108 is formally integrated. Formal completion does not authorize an official/live campaign.

Sealed markers:

`FINAL_COMMIT_SEALED_PHASE108_REHEARSAL_PASS:PRESTAGED_HISTORY`

`FINAL_COMMIT_SEALED_PHASE108_REHEARSAL_PASS:ROOT_GENERATED_HISTORY`

#### Correction 1 — identity-bound request-family authority

`EXECUTION_PLAN_REQUEST_FAMILY_SET_MUST_BE_IDENTITY_BOUND`

`NARPreCOperationalEnvelopeExecutionPlanV1` must bind, in its canonical serialized payload and therefore in its content-addressed identity, the exact reviewed Phase108 V1 request-family tuple `(DEBA_TABLE, HORSE_MARK_INFO, RACE_MARK_TABLE)`. The tuple is closed, versioned, and validated against the reviewed V1 set; it must not be derived by iterating the current `NAROfficialPageKind` enum at runtime. A future page-kind expansion requires a new reviewed plan semantic/version and must not silently broaden an existing V1 plan.

#### Correction 2 — shared derived-provider request/capture authority

`SHARED_DERIVED_PROVIDER_REQUEST_MUST_NOT_FORCE_DUPLICATE_IO_OR_ROOT_FAILURE`

`ONE_PROVIDER_REQUEST_MAY_SATISFY_MULTIPLE_PROSPECTIVELY_CLOSED_DEPENDENCIES`

`SHARED_CAPTURE_REUSE_REQUIRES_EXACT_PRIOR_AUTHORIZED_CAPTURE_AND_CURRENT_CLOSURE`

`SHARED_CAPTURE_REUSE != RETRY`

`SHARED_CAPTURE_REUSE != PRE_CLOSURE_DERIVED_WORK`

Multiple immutable past-race history closures may depend on the same canonical RaceMarkTable request. The archive/execution model must represent one target-root/request identity and append-only closure-to-request dependency edges: exactly one provider acquisition/capture is admitted for that canonical URL, with no retry and no root failure merely because a later closure discovers the already-authorized URL. A later closure must be constructed, persisted, and exact-reloaded before it may consume the prior exact capture; the resulting source record must bind that same capture evidence.

`PRIOR_CAPTURE_EXISTENCE_ALONE != LATER_CLOSURE_AUTHORITY`

`LATER_CLOSURE_EXACT_RELOAD_PRECEDES_SHARED_CAPTURE_REUSE`

Reconciliation must report unique provider requests/captures separately from closure dependency edges. A shared timeout/failure remains one provider-denominator observation and causally leaves every dependent closure incomplete; no second request is permitted. Child completion evidence is provider-request based, not duplicated per closure.

Required correction tests must cover canonical request-family identity/versioning, rejection of unreviewed page kinds, shared RaceMarkTable closure dependencies with exactly one fake provider request, later-closure exact reload before reuse, source-record reuse where existing normalizers permit it, shared failure retention/no retry, and deterministic reconciliation of one provider observation versus multiple dependency edges. Existing Phase108 rehearsals, zero-history, start/closure ordering, freeze/timing, crash/no-resume, schema, and regression requirements remain unchanged.

The verification distinction remains frozen: `PRECOMMIT_IMPLEMENTATION_VERIFICATION != FINAL_COMMIT_SEALED_SOURCE_VERIFICATION`; `FINAL_COMMIT_SEALED_SOURCE_VERIFICATION = PASS`. The sealed verification used the post-commit/pre-push Git-object workflow.

### Verified implementation and verification disposition

The committed implementation is confined to the 14 reviewed Allowed Files. It provides the target-scoped diagnostic root, immutable prestaged manifest/execution plan, controlled durable start, entry/history closures, append-only explicit companion, guarded Phase105 HTTP children, independent snapshot prerequisite proof, real builder/save/exact reload path, noninterfering freeze observer, same-process monotonic completion, and deterministic read-only reconciliation. Phase108 formal completion is recorded; official/live authorization remains blocked.

Both worktree modes are `PRECOMMIT_NO_NETWORK_REHEARSAL_PASS`: prestaged history uses one current DebaTable fake-adapter call and no history acquisition; root-generated history uses the current call, two HorseMarkInfo calls (including canonical proven zero history), and one authorized RaceMarkTable call. Existing source/discovery/builder/repository semantics are unchanged. The exact committed fixture mapping is prestaged in both modes; a production NAR entry-mapping/internal-race producer remains unresolved. Synthetic fixture lineage pairing is disclosed in `docs/LATEST_CODEX_REPORT.md` and has no official source standing.

Correction verification was rerun: existing Phase108/freeze focused tests 37 passed / 2 deferred sealed tests skipped; new correction-focused tests 5 passed; required historical-input/capture/Phase99–106 regressions 191 passed / 201 subtests passed. Full repository pytest on the final corrective implementation: 4718 passed / 4 skipped / 2846 subtests passed. The other two skips are existing Windows symlink-capability conditions. Both primary rehearsals remain `PRECOMMIT_NO_NETWORK_REHEARSAL_PASS`. A synthetic two-horse shared-page integration also completes with one RaceMarkTable provider observation and two closure dependency edges; shared timeout/failure retains one observation and leaves both dependencies unsatisfied without retry. Static/search and Allowed-Files audits passed; final diff/status evidence is recorded in the latest report.

`PRECOMMIT_IMPLEMENTATION_VERIFICATION != FINAL_COMMIT_SEALED_SOURCE_VERIFICATION`.
`FINAL_COMMIT_SEALED_SOURCE_VERIFICATION = PASS`.
Precommit tests proved functional composition; post-commit sealed verification used the exact Git-object source with real `python -I -B`. The verified implementation commit was pushed normally with no force push.

`PHASE108_FORMAL_COMPLETION != LIVE_CAMPAIGN_AUTHORIZATION`.
`PRE_C_ENVELOPE_IMPLEMENTATION_COMPLETE != CONCRETE_DELTA_AUTHORITY`.
`LIVE_CAMPAIGN_AUTHORIZATION = BLOCKED` and `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT` remain frozen. Production NAR internal entry/race mapping authority, concrete operational timing/Delta decision, and Phase94/95/41 blockers remain downstream authorization dependencies. Next: `CHATGPT_REVIEW_PHASE108_FINAL_DOCUMENTATION`.

### Retained approved implementation contract

Phase107 is reconciled: `PHASE107_PROSPECTIVE_OFFICIAL_TIMING_CAMPAIGN_AUTHORIZATION_DESIGN_REVIEW_PASS`, `POST_V0_8_DAILY_REPLAY_107 = ARCHITECTURAL_AUDIT_COMPLETE`, `LIVE_CAMPAIGN_AUTHORIZATION = BLOCKED`, and `LIVE_CAMPAIGN_AUTHORIZATION_BLOCKED_PENDING_END_TO_END_PRE_C_ENVELOPE_WIRING = CONFIRMED`. Phase106 remains formally complete. Phase99–107 authority, anti-hindsight, source isolation, actual-send, zero-retry, denominator, diagnostic-separation, and crash/no-resume invariants remain frozen.

Architectural Revision: `PHASE108_ARCHITECTURAL_REVIEW_REQUIRES_REVISION` was addressed by the approved contract below. The root is an exact target/cutoff envelope, with separately immutable root-required-work planning and controlled dynamic-discovery closures. The committed implementation follows that approval; live authorization does not follow.

Allowed Files:

Documentation:

* `docs/CURRENT_PHASE.md`
* `docs/LATEST_CODEX_REPORT.md`

New Phase108 production files:

* `scripts/simulation/nar_pre_c_operational_envelope.py`
* `scripts/simulation/nar_pre_c_operational_envelope_archive_migration.py`
* `scripts/simulation/sqlite_nar_pre_c_operational_envelope_archive.py`
* `scripts/simulation/nar_pre_c_operational_envelope_harness.py`
* `scripts/simulation/nar_pre_c_operational_envelope_reconciliation.py`
* `scripts/simulation/nar_pre_c_operational_envelope_archive_bootstrap.py` only if an explicit Phase108 bootstrap is required

Existing production files allowed for narrow changes:

* `scripts/simulation/historical_input_snapshot_freeze_receipt.py`
* `scripts/simulation/nar_operational_timing_attempt_archive_migration.py`
* `scripts/simulation/nar_operational_timing_runtime_execution_archive_migration.py`
* `scripts/simulation/sqlite_nar_operational_timing_attempt_archive.py`
* `scripts/simulation/sqlite_nar_operational_timing_runtime_execution_archive.py`

New Phase108 tests:

* `tests/test_nar_pre_c_operational_envelope.py`
* `tests/test_nar_pre_c_operational_envelope_sealed_child.py`

Existing tests allowed for narrow regression additions:

* `tests/test_historical_input_snapshot_freeze_receipt.py`
* `tests/test_nar_operational_timing_attempt_archive_migration.py`
* `tests/test_nar_operational_timing_runtime_execution_archive.py`

Read/use only; do not modify:

* `scripts/simulation/nar_official_response_capture.py`
* `scripts/simulation/nar_official_response_live_capture.py`
* `scripts/simulation/nar_historical_input_source.py`
* `scripts/simulation/nar_historical_past_race_discovery.py`
* `scripts/simulation/nar_historical_past_race_source.py`
* `scripts/simulation/nar_historical_past_race_absence_source.py`
* `scripts/simulation/historical_input_snapshot_builder.py`
* `scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py`

Forbidden Files:

* Phase99–105 canonical authority payloads and identities
* `scripts/simulation/nar_operational_timing_attempt_v2.py`
* `scripts/simulation/nar_operational_timing_runtime_execution.py`
* `scripts/simulation/nar_operational_timing_session_activation_v2.py`
* `scripts/simulation/nar_operational_timing_guarded_session.py`
* `scripts/simulation/nar_operational_timing_passive_wrapper.py`
* provider URL/request semantics
* timeout/retry/redirect/TLS semantics
* production databases, `database/keiba.db`, and `logs/`
* Phase94/95/41 semantics
* concrete Delta and statistical policy

Provider HTTP, live campaigns, and production database writes are forbidden.

Required Tests:

* immutable/content-addressed Phase108 identities
* explicit Phase108 bootstrap and confirmation normal Phase105 bootstrap installs no Phase108 schema
* append-only archive and current-process capability enforcement
* root-start evidence before causal work; start-publication failure blocks work
* prestaged manifest and execution plan
* current-entry closure and rejection of HorseMarkInfo before closure
* past-race discovery closure and rejection of RaceMarkTable before closure
* provider timeout/failure retention and proven zero-history
* failure cannot become zero-history
* stale/incompatible mapping and missing snapshot prerequisite
* snapshot build/save/exact reload
* UTC freeze sample before monotonic endpoint
* endpoint observer failure does not alter semantic freeze
* completion-publication failure produces incomplete timing evidence
* crash/cross-process resume rejection
* nested child timing is not added to root
* deterministic read-only reconciliation
* prestaged-history and root-generated-history rehearsals
* historical snapshot freeze receipt and snapshot builder/repository regressions
* official response capture/live capture and historical source/past-race regressions
* Phase104 runner, Phase105 passive wrapper, and Phase106 diagnostic/sealed-child regressions
* full repository pytest

Required pre-commit verification: both primary Phase108 rehearsals must run from the current worktree with deterministic fake adapters as ordinary pre-commit tests. They prove composition only and must be reported as `PRECOMMIT_NO_NETWORK_REHEARSAL_PASS`, never as sealed Git-object or final source-provenance verification.

Deferred sealed verification: `FINAL_COMMIT_SEALED_SOURCE_VERIFICATION = PENDING_EXPLICIT_COMMIT_APPROVAL` during `EXECUTE_APPROVED_PHASE`. After independent review and explicit commit approval, derive the sealed runtime source only from the final local Git commit/tree, run both principal rehearsals under real `python -I -B`, and complete the sealed-child focused tests before any separately approved push. `PRECOMMIT_IMPLEMENTATION_VERIFICATION != FINAL_COMMIT_SEALED_SOURCE_VERIFICATION`; `UNCOMMITTED_WORKTREE_IMPLEMENTATION != SEALED_GIT_OBJECT_SOURCE`; `FINAL_COMMIT_SEALED_VERIFICATION_REQUIRES_COMMIT_OBJECT`; `SEALED_FINAL_SOURCE_VERIFICATION_IS_POST_COMMIT_PRE-PUSH`; `NO_PUSH_BEFORE_FINAL_COMMIT_SEALED_VERIFICATION_PASS`; `UNCOMMITTED_WORKTREE_BYTES_MUST_NOT_BE_MISREPRESENTED_AS_SEALED_SOURCE_AUTHORITY`.

Required final checks: `git diff --check`, exact changed-path audit, and `git status --short`.

Stop Condition: stop if the remote/base commit differs, unexpected initial files exist, an unlisted file must change, provider semantics or retry semantics must change, a new NAR page kind is required, Phase104/105 canonical authority must change, internal mapping authority would have to be invented, snapshot-freeze semantics would change, the timing observer cannot remain noninterfering, Phase94/95/41 work is required, real provider HTTP/live campaign/concrete Delta/statistical choice is required, unrelated failing tests need out-of-scope changes, or a final sealed verification fails after the explicit commit stage. A final sealed verification being unavailable before that commit is expected and is not a stop condition.

### Frozen objective and live disposition

`SEMANTIC_SUBSTAGE_VISIBILITY != CRITICAL_PATH_COVERAGE_REQUIREMENT`.
`UNRESOLVED_SUBSTAGE_LABEL != UNMEASURED_TIME_INTERVAL`.
`STAGE_DURATION_SUM != CRITICAL_PATH_DURATION_UNLESS_COMPOSITION_PROVEN`.
`NESTED_HTTP_TIMING_IS_OBSERVABILITY_NOT_ADDITIVE_BUDGET`.
`TIME_CRITICAL_AUTHORITY_OVERHEAD_AFTER_ENVELOPE_START_MUST_BE_COVERED`.
`DISCOVERY_CLOSURE_GATE_OVERHEAD_WITHIN_PRE_C_EXECUTION_MUST_BE_COVERED`.
`PRE_C_ROOT_ENVELOPE_MUST_BE_TARGET_SCOPED`.
`SHARED_DISCOVERY_CONTROL_PLANE != PER_TARGET_DELTA_ENVELOPE`.
`PRESTAGED_INPUT_AUTHORITY_MUST_BE_CLOSED_BEFORE_ENVELOPE_START`.
`CALLER_SUPPLIED_SNAPSHOT_INPUT != FREE_PRE_C_DEPENDENCY`.
`ENVELOPE_START_SAMPLE_REQUIRES_PREWORK_DURABLE_ISSUANCE`.
`ENVELOPE_START_AUTHORITY_MUST_PRECEDE_FIRST_CAUSAL_OPERATION`.
`ROOT_CONTAINED_REQUIRED_WORK_MUST_BE_PROSPECTIVELY_CLOSED_OR_DISCOVERY_GOVERNED`.
`PAST_RACE_DISCOVERY_CLOSURE_REQUIRED_FOR_ROOT_GENERATED_HISTORY`.
`VALID_SNAPSHOT != COMPLETE_TIMING_EXECUTION_PLAN`.
`DISCOVERED_HISTORY_IN_MEMORY != AUTHORIZED_DERIVED_REQUEST_POPULATION`.
`NO_DISCOVERED_HISTORY_WITHOUT_PROOF != PROVEN_ZERO_HISTORY`.
`TIMING_ENDPOINT_INSTRUMENTATION_FAILURE != SNAPSHOT_FREEZE_FAILURE`.
`FREEZE_ENDPOINT_TELEMETRY_MUST_NOT_CHANGE_FREEZE_SEMANTICS`.
`PERSISTED_SNAPSHOT_FREEZE != COMPLETE_OPERATIONAL_TIMING_EVIDENCE`.

**Live authorization remains blocked.** The exact blocker is not that every semantic V2 label lacks a distinct timer. The committed no-network composition and post-commit sealed-source verification prove the target-root mechanics, but prospective official production composition/authorization remains absent. Retain `LIVE_CAMPAIGN_AUTHORIZATION_BLOCKED_PENDING_END_TO_END_PRE_C_ENVELOPE_WIRING`; fixture success cannot authorize a provider operation.

### Campaign control plane versus target PRE_C envelope

`NARHistoricalReplayPredictionCutoffPlan` carries one exact prediction-information cutoff decision per target. Therefore the future Delta candidate is **one completed target root**, never one daily elapsed value copied to every race. Campaign/day control-plane work has distinct evidence and duration: sealed runtime, normal bootstrap, lock/claim/readiness, daily target discovery, supplier bootstrap, monthly schedule and RaceList target-set discovery, cutoff-plan production, official authorization, and any discovery closure that is truthfully complete before a target dispatch. `CAMPAIGN_CONTROL_PLANE_DURATION != TARGET_PRE_C_FREEZE_DURATION`.

Daily discovery establishes target identities and scheduled starts; only then can the approved policy derive each exact target cutoff `C`. It cannot truthfully be work that starts at `C - Delta` for a cutoff not yet derived. Such discovery is pre-stageable control-plane work and is referenced by target roots without duplicating its elapsed time. If a provider identity genuinely cannot be determined before one target dispatch, its canonical discovery/closure gate is inside that target root only. The same shared interval must never be copied into multiple target durations.

The pre-start declaration is conceptually `NARPreCOperationalEnvelopeDeclarationV1`: it binds the exact Phase104 claim, future official authorization, target-set content identity, cutoff-plan identity/SHA and exact decision, target identity, prediction-information cutoff `C`, dataset/source scope, sealed software/runtime ancestry, prestaged-input manifest identity, and envelope semantic/version. It has one start and at most one successful completion. The completed immutable `NARPreCOperationalEnvelopeV1` binds that declaration **and** the resulting exact snapshot identity/content SHA, so it supplies the target-scoped identity available to later Delta review without pretending a future snapshot existed at dispatch. A day-wide root has no standing as a Delta observation.

### Pre-staged-input closure and snapshot prerequisite inventory

Before issuing any root-start sample, a controlled `NARPreCPrestagedInputManifestV1` must be persisted and exact-reloaded. It enumerates every dependency excluded from the target duration by exact identity/content hash and prospective availability proof, and binds the target/cutoff/envelope. No row may be silently caller-supplied. Each snapshot prerequisite has exactly one disposition: `PRESTAGED_AND_AUTHORITY_CLOSED_BEFORE_ROOT` or `GENERATED_INSIDE_TARGET_ROOT`.

| Snapshot prerequisite | Required disposition/authority |
| --- | --- |
| Target identity, target-set content, scheduled start, cutoff-plan identity and exact `C` | Prestaged control-plane authority; exact plan/decision is in the manifest before root start. |
| Dataset identity and internal-race identity | Prestaged only with an exact target-to-internal-race authority; otherwise controlled lookup/construction is root-contained. |
| Current-race track, entry, jockey, and odds source records | Normally root-contained: authorized current official response/market acquisition plus inclusive normalization, with actual-send evidence where HTTP. |
| Current external entry IDs and `race_entry_id_by_external_entry_id` | Normally root-contained after current entries are known. The builder merely validates its caller mapping; Phase108 must supply a controlled resolver/authority. Prestaging is allowed only when a complete exact external-entry mapping is already immutable and manifest-bound. |
| Every required `past_race` or `past_race_absence` record | Root-contained by default because required horse/entry lineage follows current target entry evidence. Prestaging is allowed only with an exact immutable pre-target authority for the same entries, content hashes, and availability proof. |
| Source-record tuple and its raw evidence identities | Root-contained unless every record is manifest-bound prestaged evidence; no mixed implicit caller collection. |
| `information_cutoff` | Exact prestaged cutoff decision `C`. |
| `captured_at` | Root-contained campaign-owned UTC sample at the reviewed snapshot-input closure; never caller supplied or prestaged. |
| Snapshot save and exact reload | Always root-contained; this produces the semantic freeze boundary. |

The NAR past-race discovery/source and absence-source modules establish possible source transformations, not prospective free availability. A future production model must either acquire/discover/normalize their required horse-history and result evidence inside the root after current entries are known, or present the manifest with exact earlier immutable authority. The same rule applies to internal entry mapping: the current builder's `race_entry_id_by_external_entry_id` parameter is validation input, not an issuer. No mapping may be treated as free merely because a caller can construct a dictionary.

`PRESTAGING_REQUIRES_PROSPECTIVE_AVAILABILITY_PROOF`. An input acquired after start can never be reclassified as prestaged. If a required manifest input is absent or contradicted at dispatch, a complete target root does not start; this is a precondition/control-plane failure, not a provider latency observation.

### Immutable target-root execution plan and dynamic closure

The prestaged-input manifest proves only what is legitimately excluded from a target root. A distinct immutable `NARPreCOperationalEnvelopeExecutionPlanV1` closes what **must** occur inside that root before its start anchor is issued. It binds the exact root declaration, target, cutoff decision and `C`, prestaged-manifest identity, canonical ordered initial root operations, allowed provider request families, canonical dynamic-discovery algorithm identifiers/versions, continuation and failure semantics, ordering constraints, `max_retries = 0`, and the sole successful terminal condition: exact snapshot reload followed by `SNAPSHOT_FREEZE_COMPLETION`. It is persisted and exact-reloaded before the root start; outcome-dependent plan mutation is prohibited. `ROOT_CONTAINED_REQUIRED_WORK_MUST_BE_PROSPECTIVELY_CLOSED_OR_DISCOVERY_GOVERNED`.

The plan declares only exact initial operations whose material is knowable before dispatch. For a target whose official-response request identity is already authoritative, this includes that exact acquisition and its inclusive normalization/source-record operation. It may declare the entry-mapping resolver as an ordered non-HTTP operation after current-entry closure, but it must not invent a request URL before the current evidence makes that URL canonical. All later request populations are admitted only through an authority-bound closure, never merely because application code has found them in memory.

After current-race normalization, a controlled `NARCurrentEntryWorkClosureV1` (or exact equivalent) closes the entry-dependent population in canonical entry order. It binds the parent normalized evidence, exact target, each external entry and horse identity, each canonical HorseMarkInfo request identity/URL where required, the relevant algorithm/version, and declared continuation semantics. The closure is constructed, saved, and exact-reloaded before any HorseMarkInfo child request. A failure for one entry retains its provider observation and cannot remove another already-authorized entry from this closure.

For root-generated history, each exact HorseMarkInfo evidence item feeds `discover_nar_historical_past_race_history(...)`; an immutable `NARPastRaceDiscoveryClosureV1` then binds the parent evidence identity, target entry/horse, discovery algorithm/version, canonical ordered discovered events, and exact derived RaceMarkTable request identities. It distinguishes a proven NAR actual start from proven non-start, JRA/unsupported states, and a genuine zero-history result. JRA/unsupported branches do not manufacture NAR request identities. Only controlled save/reload of this closure admits its RaceMarkTable children. `PAST_RACE_DISCOVERY_CLOSURE_REQUIRED_FOR_ROOT_GENERATED_HISTORY` and `DISCOVERED_HISTORY_IN_MEMORY != AUTHORIZED_DERIVED_REQUEST_POPULATION`.

The closure is complete or explicitly failed/integrity-invalid; it may not retain only quick/successful events, discard timeout entries, or turn a partial HorseMarkInfo parse into a complete request population. A zero-history branch is permitted only when the exact official HorseMarkInfo evidence and the canonical discovery function prove it; discovery/transport failure never authorizes a `past_race_absence`. `NO_DISCOVERED_HISTORY_WITHOUT_PROOF != PROVEN_ZERO_HISTORY`.

### Snapshot prerequisite and execution-plan reconciliation

`build_historical_input_snapshot(...)` validates a supplied record set, but it does not prove the campaign executed every prospectively required acquisition, discovery, mapping, or closure. `VALID_SNAPSHOT != COMPLETE_TIMING_EXECUTION_PLAN`. Before a root can be timing-complete, read-only reconciliation must account for every snapshot prerequisite exactly once as either `PRESTAGED_AND_AUTHORITY_CLOSED_BEFORE_ROOT` or `GENERATED_INSIDE_TARGET_ROOT_UNDER_EXECUTION_PLAN`; there is no implicit caller-only third source.

The mapping is therefore authority-bound as well. A root-generated `race_entry_id_by_external_entry_id` is deterministically produced after current-entry closure and exact-reloaded before snapshot construction. A prestaged mapping is eligible only when the manifest proves exact compatibility with the discovered/current target and external-entry identities; a stale or partial mapping fails closed. Track, entry, jockey, odds, each past-race or proven absence, dataset/internal-race binding, source records, and temporal/cutoff material receive the same reconciliation treatment.

### Exact PRE_C start and pre-stageable work

`PRE_C_OPERATIONAL_ENVELOPE_START` is the campaign runner's first `perf_counter_ns()` sample inside the controlled **execute one exact target PRE_C acquisition/freeze now** dispatch. It is taken only after the exact target envelope, cutoff decision, prestaged-input manifest, current-process capability, and official-plan capability have passed controlled checks. It is immediately followed by controlled start issuance and precedes every acquisition, closure, normalization, mapping, snapshot, persistence, or instrumentation action. No logging, transport/session construction, closure work, attempt publication, or callable dispatch may occur between the dispatch transition and this sample.

The following may complete before this boundary only when fully qualified, durable, and not triggered by the target dispatch: sealed isolated-child startup/source checks; normal official archive bootstrap; V2 configuration/session persistence; target-set/cutoff-plan and prestaged-input-manifest issuance; prospective plan persistence/reload; V2 activation; Phase104 runtime binding, claim, readiness, lock, and current-process capability; and controlled official-plan authorization. `ENVELOPE_START_SAMPLE_REQUIRES_PREWORK_DURABLE_ISSUANCE`. The runner must not hide a later re-bootstrap, re-lock, re-authorization, profile build, source check, input-manifest issuance, or mapping resolution. Any authority work deferred until after the sample is a declared target-root segment and is included once in that target duration.

### Chosen non-overlapping architecture

Phase108 should use one campaign-owned **target root PRE_C envelope**, not an arithmetic patch over `measure_nar_operation()` records. Conceptually, append-only controlled records are:

- `NARPreCOperationalEnvelopeStartV1`: exact pre-start declaration/target/cutoff/manifest, claim/session/configuration/official-plan/composition ancestry and `start_monotonic_ns`;
- `NARPreCEnvelopeCompositionV1`: the predeclared parent/child, sequence, dependency, coverage-owner, and endpoint contract; and
- `NARPreCFreezeEndpointV1` completion artifact: exact root-start and target/cutoff ancestry, snapshot identity/content SHA, receipt identity, `freeze_completed_at`, exact start/end monotonic evidence (or derived integer elapsed), and closed completion semantic. Exact endpoint reload then constructs the completed `NARPreCOperationalEnvelopeV1`; a separate failure-termination receipt applies when no freeze endpoint occurs.

The start issuer receives the exact in-memory Phase104 capability object, calls `require_current_owner`, and creates a nonpersistent target-envelope capability that retains that exact object by reference. The persisted start record binds the serializable claim/binding/session/lock-scope/runner ancestry and the target envelope, and records the closed semantic `CURRENT_PROCESS_CAPABILITY_VERIFIED_V1`; the object itself is intentionally nonserializable and cannot be reconstructed from the record. Private controlled issuance requires both capability-object identity and the held lock. `ENVELOPE_START_AUTHORITY_MUST_PRECEDE_FIRST_CAUSAL_OPERATION`.

The start anchor is saved and exact-reloaded after the start sample and before any provider operation; failure prevents provider operation, normalization, mapping, and snapshot work. Its publication is inside the target root interval. The final successful envelope elapsed is exactly `(freeze_endpoint_monotonic_ns - start_monotonic_ns) // 1000`, with nonnegative integer inputs, floor/truncation, submicrosecond zero, and no UTC subtraction or float. Endpoint/termination evidence is saved and exact-reloaded **after** the captured endpoint; its publication is post-end evidence and does not extend the elapsed interval.

`MONOTONIC_ENVELOPE_CANNOT_RESUME_ACROSS_PROCESS_BOUNDARY`. Start and end ticks are usable only through the same live runner and monotonic clock domain. A crash leaves the target root incomplete; Phase104 already consumes the session/claim, so a later process needs a new prospectively authorized session, claim, campaign, and target envelope. It must never subtract ticks from different processes or reconstruct completion from snapshot metadata.

This directly resolves the Phase105 outer-attempt issue. `measure_nar_operation()` samples its own operation start only after attempt construction, attempt save/reload, and `ATTEMPT_START_PUBLICATION` overhead. The root start precedes all of these. Therefore the root contains required attempt-publication and closure-gate overhead without summing it with operation elapsed. Phase105 operation/terminal rows remain useful leaf or nested observations, never components automatically added to the root critical-path duration.

### Acquisition, discovery, normalization, and snapshot composition

The primary inclusive acquisition boundary is `NARDailyTargetLiveAcquisitionApplication.acquire(target_date=...)`, but it is normally campaign control-plane work: it covers official-home capture, root resolution/capture, locator-script resolution/capture, monthly request/capture, monthly normalization/discovery, sequential RaceList captures, and target-set construction before per-target cutoff roots begin. Phase108 may introduce a narrow controlled composition seam after the canonical monthly envelope and before the RaceList loop: the default path is semantically unchanged, while official composition persists/reloads the Phase107 control-plane closure and verifies derived canonical request ordering. This control-plane closure is referenced by target roots and its elapsed is not duplicated. Only discovery that genuinely cannot close until a target root has begun is a contained target-root gate.

Each capture may expose a contained inclusive segment around its existing capture service (`capture_official_home`, `capture_monthly_root`, `capture_locator_script`, or `capture_supplied_response`). A Phase105 guarded HTTP attempt is a child of that segment: it proves actual-send environment, provider failure/timeout, and transport duration. `CHILD_HTTP_DURATION_IS_CONTAINED_WITHIN_PARENT_ACQUISITION_ENVELOPE`; the evaluator must never sum it with its containing capture or the root.

`normalize_nar_historical_input_source_records(...)` is one exact public, pure, inclusive normalization/source-record boundary. It may cover its parsing, raw validation, canonical URL checks, provider/external identity derivation, normalization, and source-record construction without splitting helpers. Individual `PARSING`, `RAW_CAPTURE_VALIDATION`, and `PROVIDER_IDENTITY_BINDING` labels remain unavailable as separately measured semantics, but do not make an interval unmeasured.

`build_historical_input_snapshot(...)` was `WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED` at the design audit. Its clear standalone pure boundary is now called unchanged inside the no-network target root after independently verified source/mapping prerequisites and before snapshot persistence. This does not claim an authorized official live composition.

### Freeze persistence and dual-clock endpoint

`SNAPSHOT_FREEZE_COMPLETION = EXACT_SNAPSHOT_RELOAD_VERIFIED_BOUNDARY`. Existing ordering remains immutable:

1. snapshot repository save;
2. exact snapshot reload and content/identity verification;
3. service-owned UTC sample stored as existing `freeze_completed_at`;
4. receipt construction;
5. receipt archive save and exact reload.

Phase108 adds no new freeze meaning. It introduces a narrow campaign-owned completion observer in `issue_historical_input_snapshot_freeze_receipt(...)`, invoked only after step 3 and before receipt construction. The observer immediately takes `runner.monotonic_timer_ns()` and returns an in-memory endpoint token to the controlled root adapter. This freezes `MONOTONIC_FREEZE_ENDPOINT_MUST_NOT_PRECEDE_CAUSAL_FREEZE_COMPLETION_SAMPLE`.

`FREEZE_ENDPOINT_TELEMETRY_MUST_NOT_CHANGE_FREEZE_SEMANTICS`. The observer is observational: if it fails after the successful exact reload and UTC sample, the ordinary receipt construction/publication/reload continues under the existing business contract where possible. It must not move, replace, or roll back `freeze_completed_at`, nor transform a successful snapshot freeze into a snapshot failure. `TIMING_ENDPOINT_INSTRUMENTATION_FAILURE != SNAPSHOT_FREEZE_FAILURE`. The root adapter persists/exact-reloads a completion artifact only when it received the endpoint token; endpoint-observer or endpoint-publication failure leaves the semantic snapshot/receipt valid but the timing envelope incomplete and unusable for Delta review. It must never reconstruct a missing monotonic endpoint later from snapshot or UTC metadata: `PERSISTED_SNAPSHOT_FREEZE != COMPLETE_OPERATIONAL_TIMING_EVIDENCE`.

`FREEZE_RECEIPT_PUBLICATION_AFTER_FREEZE_COMPLETION != PRE_C_FREEZE_BUDGET`. Receipt construction/save/reload remains independently reportable audit/observability overhead and may be measured without recursion, but it is not selected as the prediction-cutoff endpoint or appended to the root elapsed time. An enclosing Phase105 timer that runs through receipt publication is never used blindly as the PRE_C cutoff duration; the dedicated endpoint cuts the root at step 3. A future action contract may separately require receipt publication before a later action, but that is not a Delta extension here.

### No-gap/no-overlap coverage proof

The initial critical-path rule is deliberately conservative: each exact target root is the sole `CRITICAL_PATH_OWNER` for its closed interval from start anchor to successful freeze endpoint. All other records are predeclared as `CONTAINED_OBSERVATION`, `INCLUSIVE_SEGMENT`, `EXCLUSIVE_LEAF`, `SEQUENTIAL_EDGE`, `DEPENDENCY_EDGE`, `DISCOVERY_GATE`, or post-freeze `AUDIT_OVERHEAD`; they cannot be arithmetically added to that root elapsed. The composition identity, not inferred wall-clock ordering, declares each relation and its required predecessor/success/failure continuation. Shared control-plane identities may be referenced, never counted as target elapsed.

The read-only evaluator validates: exact immutable execution plan and prestaged manifest; exact root start before any planned operation; one exact claimed composition; all required initial operations and closure gates mapped to declared nodes; every dynamic derived request preceded by its exact persisted/reloaded closure; every attempted Phase105 row bound to the root claim and a declared node; no omitted required child or unauthorized request; snapshot prerequisites sourced exactly once; the endpoint no earlier than the start; every contained child explicitly parented; no selected critical-path child in root-only mode; and exact failure/causal-skip termination if no endpoint exists. This proves coverage because the controlled root adapter owns every synchronous causal action between anchors. A later exclusive partition may replace root-only calculation only after independently proving a complete nonoverlapping partition; simply sorting timestamps is prohibited.

### Failure, session, and authority semantics

A qualified provider timeout/failure remains its own provider observation. The containing capture/target-root branch records the corresponding failure, dependent nodes become nonexecutable only under the prospective DAG, and independent authorized branches continue only when the plan says so. No successful freeze endpoint is fabricated; full-freeze reconciliation is incomplete. If snapshot save or exact reload fails, no successful endpoint is sampled or claimed; existing operation/failure evidence remains immutable. If the session window ends before causal freeze completion, the actual evidence is retained without backdating or extension, but that target envelope is `INCOMPLETE_SESSION_WINDOW`. One target failure never erases another target's records; no target duration is merged with another.

Phase107 prospective plan, discovery closure, explicit authorization, diagnostic exclusion, zero retries, no redundant provider load, sealed source/runtime, actual-send environment gate, and Phase104 crash/no-resume all remain prerequisites. Phase108 does not make fixture latency official, change Phase104/105 identities, add a retry, or create entry-status/market-eligibility authority. If the current snapshot path cannot run without a Phase94/95/41 authority, the implementation must report that exact dependency rather than synthesize it.

### No-network rehearsal and deferred sealed verification

Both Phase108 cases have passed as ordinary precommit worktree tests. Only after independent review, explicit commit approval and local commit creation must those same cases run in a sealed `python -I -B` child from the exact final Git commit/tree, with Git-object fixtures, fake adapters below guarded `Session.send`, real unmodified source isolation, Phase104/105 controlled authority, and durable root start/endpoint path. The cases are: (1) prestaged history with compatible prestaged mapping and no history reacquisition; and (2) current response, normalization/entry closure, HorseMarkInfo children, exact-reloaded history closures, derived RaceMarkTable children, historical/absence construction, exact mapping, snapshot construction, and the real save/reload/receipt path. No NAR request is permitted; both remain structurally nonofficial diagnostic evidence.

`PRE_C_ENVELOPE_RECONCILIATION` is pure/read-only and target-scoped. It reports exact target/cutoff and start authority, exact prestaged manifest closure, root-generated input evidence, same-process monotonic clock domain, endpoint/termination authority, integer elapsed duration, composition identity, contained child observations, discovery state, provider failures/timeouts, freeze save/reload success or failure, session compliance, gaps/illegal selected overlaps, missing declared nodes, and official-versus-diagnostic classification. It rejects cross-target duration merge and never repairs evidence or calculates Delta. Success is only `COMPLETE_NONOVERLAPPING_MONOTONIC_PRE_C_FREEZE_ENVELOPE`.

### Future implementation paths, tests, and recommendation

Likely future paths are a narrow target PRE_C envelope/composition module, controlled envelope archive companion/repository, prestaged-input manifest authority, immutable root execution-plan and entry/history-closure authorities, a freeze-completion observer owned by campaign composition, narrow daily-acquisition closure seam, controlled entry-mapping resolver/authority, and focused tests. Required tests cover: exact target/cutoff identity; immutable plan and durable manifest before start; start sample then exact start reload before first causal operation; caller input cannot bypass manifest/root generation; shared control-plane duration nonduplication; attempt publication contained by root; child HTTP nonaddition; current-entry and past-race closure save/reload before derived children; inclusive source normalization; exact past-race/mapping authority; genuine zero-history versus failure; partial closure/stale mapping rejection; standalone snapshot construction; save/reload then UTC then monotonic endpoint order; endpoint telemetry noninterference; receipt publication excluded; no-gap/root-only and no-double-count validation; provider failure, discovery failure, snapshot persistence failure, and session-expiry outcomes; sealed-child two-mode fake-adapter rehearsal; and deterministic target reconciliation.

Remaining blockers: `LIVE_CAMPAIGN_AUTHORIZATION_BLOCKED_PENDING_END_TO_END_PRE_C_ENVELOPE_WIRING`; unimplemented prospective official plan/closure/authorization and official production dispatch; real NAR entry-mapping/internal-race authority; official-response/market-odds closure definitions; `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`; Phase94 historical entry-status authority; Phase95 prospective entry-status semantics; Phase41 market eligibility; and separate explicit live-campaign authorization. Independent review, sealed verification, and implementation remote verification are complete.

The implementation and post-commit sealed verification have passed independent review, and the target-scoped envelope is formally integrated. Do not authorize a live campaign or concrete Delta selection from Phase108 alone, and do not contact NAR.

---

## Historical record — POST_V0_8_DAILY_REPLAY_107

## POST_V0_8_DAILY_REPLAY_107

Title: NAR Prospective Official Operational-Timing Campaign Authorization

Status: DRAFT_FOR_REVIEW

Outcome: READY_FOR_ARCHITECTURAL_REVIEW

Audit: NAR_PROSPECTIVE_OFFICIAL_TIMING_CAMPAIGN_AUTHORIZATION_DESIGN_COMPLETE

Base Commit and Branch: `fefcda45ce9e01a13724209ae6012b81bbc0bd46` / `feature/post-v0.8-daily-replay`

Phase106 is formally reconciled: `PHASE106_FINAL_DOCUMENTATION_CORRECTION_REMOTE_VERIFICATION_PASS`, `PHASE106_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`, `POST_V0_8_DAILY_REPLAY_106 = FORMALLY_COMPLETE`, `NAR_DIAGNOSTIC_CAMPAIGN_AND_TIMING_QUALIFICATION = FORMALLY_INTEGRATED`, and `DIAGNOSTIC_DENOMINATOR_AND_RECONCILIATION_CONTRACT = VERIFIED`. All Phase99–106 anti-hindsight, sealed-source, execution, actual-send environment, denominator, and diagnostic invariants remain frozen.

Architectural Revision: `PHASE107_ARCHITECTURAL_REVIEW_REQUIRES_REVISION` is addressed by this draft, replacing substage-granularity as the live blocker with exact end-to-end PRE_C envelope coverage. No live authorization follows from the revision.

Allowed Files: `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md` only for this design/preparation activity.

Forbidden Files: all production code, tests, migrations/schemas, production databases, logs, and all non-document paths. Provider HTTP, live campaigns, concrete Delta selection, commits, and pushes are forbidden.

Required Verification: read-only source/history audit; `git diff --check`; exact changed-path audit; and `git status --short`. No test run or database write is required for this documentation-only preparation.

Stop Condition: do not approve a live campaign if a complete PRE_C critical path cannot be measured, a discovery population cannot be prospectively closed, a required authorization would be retrospective, Phase104/105 canonical authority would need rewriting, retries/provider semantics would need changing, or diagnostic evidence would need promotion.

### Formal distinctions and disposition

`DIAGNOSTIC_CAMPAIGN_SUCCESS != OFFICIAL_LIVE_CAMPAIGN_AUTHORIZATION`.
`SYNTHETIC_LATENCY != PROVIDER_OPERATIONAL_LATENCY`.
`DIAGNOSTIC_AUTHORITY_CANNOT_PROMOTE_TO_OFFICIAL_AUTHORITY`.
`OFFICIAL_CAMPAIGN_REQUIRES_PREDECLARED_LIVE_MEASUREMENT_AUTHORITY`.
`MEASUREMENT_CAMPAIGN_MUST_NOT_GENERATE_REDUNDANT_PROVIDER_LOAD`.

**Disposition: no live campaign is authorized.** The prospective authority described below is necessary but not sufficient: the current code has no production call site for `measure_nar_operation`, and no reviewed monotonic composition yet covers every interval from the PRE_C operational start through exact snapshot-reload-verified freeze completion. Freeze `LIVE_CAMPAIGN_AUTHORIZATION_BLOCKED_PENDING_END_TO_END_PRE_C_ENVELOPE_WIRING`.

`SEMANTIC_SUBSTAGE_VISIBILITY != CRITICAL_PATH_COVERAGE_REQUIREMENT` and `UNRESOLVED_SUBSTAGE_LABEL != UNMEASURED_TIME_INTERVAL`. A semantically distinguishable helper needs a separate V2 attempt only when separate observability is reviewed as useful; concrete-Delta sufficiency instead requires exactly one approved inclusive or exclusive envelope for every causal interval, with nesting recorded so that a critical-path evaluator does not double count it.

### Stage-boundary sufficiency audit

| V2 family | Current state | Effect on official PRE_C evidence |
| --- | --- | --- |
| Bootstrap home, monthly root, locator script, monthly schedule, RaceList, official response, market odds | Wrapper primitive available but not wired into production acquisition | No official attempt/actual-send/terminal ancestry is currently produced for these real call boundaries. |
| Raw validation, parsing, provider identity binding | Blocked by unresolved **separate substage** boundaries | `normalize_nar_historical_input_source_records(...)` can instead be measured as one reviewed inclusive normalization/source-record envelope; individual labels remain unavailable without creating a timing gap. |
| Raw persistence, normalization, source-record construction, snapshot construction/persistence/exact reload | Wrapper primitive available but not wired | `build_historical_input_snapshot(...)` is an exact standalone pure snapshot-construction boundary. The other candidate boundaries need reviewed composition and critical-path relations, not semantic splitting merely for telemetry. |
| Freeze receipt construction, publication, exact reload | Blocked by unresolved substage boundaries | Receipt overhead cannot be allocated to an operational budget as three independent stages. |
| Campaign preparation, runtime readiness, scheduler dispatch | Blocked or not currently reachable | Control timing is not an executable V2 operation path. |
| Attempt-start / terminal publication | Wired nonrecursive overhead evidence | Useful overhead evidence only; it does not establish a complete acquisition/freeze path. |
| POST_C adapter/prediction/allocation/bet-plan | Wrapper primitive available but not wired | Not evidence of PRE_C completion and must operate only on frozen input. |

The live acquisition graph is serial in source (`home -> root -> script -> monthly schedule -> canonical venue locators -> sequential RaceList captures`), but local call-graph seriality is not campaign authority and does not make the stages measured. Nested timing would also be inclusive unless an explicit composition rule marks a leaf as exclusive. Therefore `STAGE_DURATION_SUM != CRITICAL_PATH_DURATION_UNLESS_COMPOSITION_PROVEN` remains decisive.

The exact missing coverage is not every named semantic substage. It is the absent end-to-end wiring of: an inclusive live-capture envelope from its reviewed start through capture persistence; the inclusive source-normalization/source-record envelope; standalone snapshot construction; snapshot persistence and exact reload; and one monotonic endpoint at exact freeze completion. Child HTTP attempts remain independently observable but are contained by inclusive acquisition envelopes and must not be added to them. Receipt construction/publication/reload are post-freeze audit overhead, not a missing PRE_C freeze interval. No live request may be authorized merely to collect partial numbers.

### Prospective official plan and discovery closure contract

The future official companion shall use a new immutable envelope, conceptually `NAROperationalTimingProspectiveCampaignPlanV1`, with identity `nar-operational-timing-prospective-campaign-plan-v1:<sha256>`. It is distinct from every Phase106 diagnostic plan/declaration and binds only pre-request material:

- exact V2 configuration and session identities, repository/declared commit, target-day scope, provider, and mode `OFFICIAL_PROSPECTIVE_OPERATIONAL_TIMING_V1`;
- fixed session window, `CONTROLLED_SINGLE_WORKER_SERIAL_V1`, zero-retry rule, fixed stopping rule, and no-redundant-load rule;
- ordered root request nodes (official home, monthly root, locator script, and monthly schedule), each with exact safe URL identity, transport family, `DIRECT_REQUEST_ENVIRONMENT_V1` expectation, stage, sequence slot, and continuation rule;
- the closed allowed discovery graph, canonical algorithm/version identities, maximum request families, target/race scope grammar, predecessor edges, and composition role; and
- no outcome, payout, ROI, entry-status result, retrospective timestamp, success-count goal, or mutable result field.

The plan must be canonical, append-only, persisted and exact-reloaded before V2 activation. The declaration form carries no self-asserted completion time. Its plan fixes the denominator *shape*, not a post-outcome list of successes.

Discovery-dependent nodes require a separate immutable declaration/verification pair. `NAROperationalTimingProspectiveDiscoveryClosureV1` binds plan identity, exact terminal/source evidence identities, canonical discovery algorithm/version, canonical ordered derived request-node material, and closure semantic. After its exact reload, a campaign-owned UTC source samples time for an append-only closure-verification receipt; only its exact reload authorizes the derived nodes. This avoids treating a caller timestamp as closure authority. A derived request must be admitted after the verified closure and within the unchanged session window.

For the existing NAR day graph, complete normalized monthly-schedule evidence is the first valid closure point: `normalize_nar_monthly_convene_info` supplies canonically ordered venue locators, from which exact RaceList request identities can be committed. A successful monthly HTTP response that yields incomplete/invalid canonical venue evidence is **not** a partial closure. Official-response and market-odds populations need their own later, source-bound closure algorithms before they can join an official plan; no such reviewed closure exists now.

`DISCOVERY_FAILURE != EMPTY_DISCOVERY_SUCCESS`. A root failure/timeout is retained as an observation when its Phase105 direct environment qualified and the provider operation began. Its dependent undiscovered nodes are causally nonexecutable; no empty closure is persisted. Partial discovery is `DISCOVERY_CLOSURE_FAILED` or `EVIDENCE_INTEGRITY_FAILURE`, never a selectable successful subset.

### Authorization and admission ordering

The future official schema is only storage. `OFFICIAL_SCHEMA_PRESENT != OFFICIAL_LIVE_CAMPAIGN_AUTHORIZED`.

The required causal order is:

1. Archive exact V2 configuration and fixed V2 session; construct, persist, and exact-reload the official prospective envelope.
2. Prospectively issue and exact-reload V2 activation declaration/verification; verification must qualify no later than session start.
3. Under Phase104's held local lock, create the sealed source/runtime binding, one-shot claim, readiness receipt, and current-process capability; readiness must qualify no later than session start.
4. Confirm that the archive contains no Phase106 diagnostic companion/declaration and zero Phase105 attempts for the claim.
5. Construct, persist, and exact-reload `NAROperationalTimingProspectiveExecutionAuthorizationV1`, binding exact plan, activation, runtime binding, readiness, claim, source/runtime ancestry, and authorization semantic. Its controlled service UTC verification must also qualify before the fixed session start.
6. Issue a nonpersistent official-plan capability only while the same current-process Phase104 capability and lock are live.
7. Admit a root request only if it maps exactly to one persisted/reloaded root node. Admit a derived request only after its exact closure-verification receipt reload maps it to one committed derived node.
8. Phase105 then persists/reloads the attempt, starts monotonic timing, obtains actual-send verification inside guarded `Session.send`, sends only after `QUALIFIED_DIRECT_REQUEST_ENVIRONMENT`, and persists/reloads the terminal.

The authorization is one controlled artifact per claim, requires zero attempts before issuance, and cannot be backfilled. It binds claim/session/configuration contradictions through restrictive foreign keys and exact reload. It is not a caller `official=True` flag, and a persisted authorization does not recreate a later process's current-process capability.

Every provider URL is thereby authorized before Phase105 attempt publication: by an exact root node or by an exact verified closure node. The existing actual-send chain remains `attempt -> request-effective-environment verification -> send -> terminal`; a nonqualifying environment sends no bytes and is not provider latency. `HTTPAdapter(max_retries=0)` remains unchanged: a qualified timeout/failure is one planned observation, not an automatic replacement or retry.

### Denominator, continuation, and campaign boundaries

The eventual denominator is the immutable union of predeclared root nodes plus all exact nodes in prospectively verified discovery closures, governed by the envelope's predeclared DAG. It is never `len(observed_attempts)` and never “until N successes.” Each node declares whether it requires predecessor successful output, runs after a predecessor terminal regardless of outcome, is independent, or terminates a branch.

A qualified provider failure/timeout remains a denominator observation. Downstream nodes requiring its successful bytes are `EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE`; they do not erase the upstream terminal. Independently authorized nodes continue only when the predeclared DAG says so. A missing terminal is unresolved evidence, not a proven failure; therefore its dependents are blocked by unresolved predecessor and the campaign fails evidence integrity. A runnable node with no evidence is `MISSING_UNEXPLAINED`.

If closure completes after the fixed V2 session window, no late request is admitted, no window is extended, and no admission timestamp is backdated. Reconciliation records session-window incompleteness. A crash after Phase104 claim publication consumes the session permanently: `CRASHED_OFFICIAL_SESSION_REQUIRES_NEW_PREDECLARED_SESSION`. Replacement requires a new session, activation, claim, plan, authorization, and target scope; populations from separate claims/campaigns cannot silently merge.

The plan permits only the normal acquisition operations required by its canonical graph, once per authorized node. It forbids benchmark polling, repeated successful samples, artificial request volume, and retry-until-success. This preserves provider load ethics and makes the population operational rather than synthetic.

### Freeze interpretation and reconciliation

`SNAPSHOT_FREEZE_COMPLETION = EXACT_SNAPSHOT_RELOAD_VERIFIED_BOUNDARY`. `freeze_completed_at` remains the existing Phase99/98 UTC causal sample after snapshot repository save and exact snapshot reload, before receipt construction/archive publication; it proves `COMMITTED_AND_EXACT_RELOAD_VERIFIED` snapshot availability and must not be redefined. `FREEZE_RECEIPT_PUBLICATION_AFTER_FREEZE_COMPLETION != PRE_C_FREEZE_BUDGET`.

Phase108 needs one narrow campaign-owned monotonic boundary at the same already-approved semantic point: after successful save plus exact reload, retain the existing controlled UTC `freeze_completed_at` sample and immediately record the monotonic freeze-completion tick. Elapsed duration uses exact integer monotonic arithmetic, never UTC subtraction, float conversion, backdating, or changed receipt semantics. The timing observer is noninterfering: a missing tick leaves timing evidence incomplete, not the semantic freeze failed. Receipt construction/save/reload remain separately useful audit/observability overhead, but do not automatically extend the prediction-cutoff Delta budget.

The future official reconciler is pure and read-only. It must independently report exact plan/closure/authorization ancestry, qualified observations, qualified provider failures/timeouts, nonqualifying environment blocks, causally nonexecutable nodes, unresolved attempts, missing authorized operations, missing/duplicate sequence conditions, closure failure/partial evidence, publication-overhead completeness, session-window blocks, and execution-integrity defects. Proposed closed campaign states are `COMPLETE_OFFICIAL_MEASUREMENT_CAMPAIGN`, `INCOMPLETE_CAUSAL_PROVIDER_FAILURE`, `DISCOVERY_CLOSURE_FAILED`, `INCOMPLETE_SESSION_WINDOW`, and `INCOMPLETE_EVIDENCE_INTEGRITY_FAILURE`. Campaign incompleteness never deletes an already-qualified provider observation, and reconciliation never repairs evidence or calculates Delta.

### Future implementation paths and tests

Recommended prerequisite path, before any later live authorization review:

1. **Phase108 — PRE_C Critical-Path Envelope Wiring:** wire approved production operations to Phase105 authority without altering business semantics; establish inclusive parent/leaf/dependency/nesting relations; cover acquisition, inclusive normalization, standalone snapshot construction, persistence, exact reload, and the monotonic freeze endpoint; implement the official plan, closure declaration/verification, controlled authorization, exact official companion, and request-admission gates without provider HTTP. It does **not** split every unresolved semantic substage.
2. **Independent implementation review:** prove exact normal/official schema compatibility, no diagnostic companion, no canonical Phase104/105 change, and sealed-child no-network end-to-end authority issuance.
3. **Separate prospective live-campaign authorization review:** select no dates until then; approve a minimal normal-load scope only if the complete PRE_C proof and prospective denominator are verified.

Required future tests include: schema alone cannot send; exact envelope/authorization precedes first request; immutable root execution plan and prestaged manifest reload before start; roots outside plan and derived requests before closure are rejected; current-entry closure admits only its canonical HorseMarkInfo population; history closure declaration/receipt reloads exactly; HorseMarkInfo timeout, parse/validation failure, and closure-publication failure cannot create a partial history population; one derived RaceMarkTable timeout remains an observation; proven zero history differs from failed discovery; stale prestaged mapping rejects; qualified timeout remains observed while independent nodes follow the declared DAG; session expiry blocks late admission; crash requires a new session; diagnostic archive/evidence never qualifies; actual-send direct environment still gates every HTTP send; zero retries/no duplicate planned request; endpoint telemetry failure after successful snapshot reload preserves semantic freeze but leaves timing incomplete; deterministic read-only reconciliation; and incomplete campaign states retain qualified observations.

Phase108 success requires a deterministic no-network rehearsal proving: an exact PRE_C operational start; real controlled Phase105 wiring; exact discovery authority; coverage of every inclusive operation; snapshot construction, persistence, and exact reload; the monotonic freeze-completion endpoint; no uncovered causal interval; no double-counted critical-path interval; retained failures/timeouts; separately reported post-freeze receipt overhead; and pure reconciliation of envelope completeness.

Remaining blockers: `LIVE_CAMPAIGN_AUTHORIZATION_BLOCKED_PENDING_END_TO_END_PRE_C_ENVELOPE_WIRING`; official discovery closure algorithms for official-response/market-odds populations; no current production wrapper wiring; `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`; Phase94 historical entry-status authority; Phase95 prospective entry-status semantics; Phase41 market eligibility; and a separately approved prospective live campaign.

Recommendation: retain `DRAFT_FOR_REVIEW`; do not authorize provider HTTP or a live campaign.

---

## Historical record — POST_V0_8_DAILY_REPLAY_106

## POST_V0_8_DAILY_REPLAY_106

Title: NAR No-Network Diagnostic Campaign Rehearsal and Timing Qualification

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Implementation: NAR_DIAGNOSTIC_CAMPAIGN_AND_TIMING_QUALIFICATION_IMPLEMENTED

Base Commit and Branch: `d250e0954f50dfe27d6efe569f149a876b8ca684` / `feature/post-v0.8-daily-replay`

Design Review: PHASE106_DIAGNOSTIC_CAMPAIGN_AND_TIMING_QUALIFICATION_DESIGN_REVIEW_PASS

Allowed Files: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`, new Phase106 diagnostic domain, fixture, migration, SQLite archive, harness and reconciliation modules under `scripts/simulation/`, narrow Phase99–105 compatible-schema gates, the four NAR transport modules for private adapter injection, and matching Phase106 tests under `tests/`.

Forbidden Files: Phase99–105 canonical authority payloads, ordinary transport request semantics, normal Phase105 bootstrap, production databases, logs, and unrelated production/tests.

Required Tests: Phase106 focused tests; Phase105 and Phase104 focused suites; Phase103/100/99 timing and archive regressions; affected transport tests; full repository pytest; `git diff --check`; exact changed-path audit.

Stop Condition: baseline advances, unexpected initial files appear, ordinary provider behavior or immutable Phase104/105 semantics must change, diagnostic schema must enter normal bootstrap, Git-object fixture authority or no-network adapter boundary cannot be proven, out-of-scope tests fail, or normal push requires force.

Implementation boundary: a Git-object-derived fixture manifest, fixed diagnostic
plan/DAG, one declaration per existing Phase104 claim, explicit diagnostic-only
companion, controlled Phase105 attempt admission, fake-adapter guarded HTTP,
and read-only reconciliation. A plan node's `sequence` is its fixed scheduled
slot; Phase105 attempt sequences remain dense among nodes actually executed.
The maximum attempt count is predeclared, but upstream failures may causally
disable dependent nodes without erasing the qualified upstream observation.
`DIAGNOSTIC_ONLY` overrides every inner observation for official eligibility.
No normal Phase105 bootstrap installs the companion. The diagnostic rehearsal
does not authorize provider HTTP or a concrete Delta.

### Phase105 reconciliation

`PHASE105_CORRECTION_REMOTE_VERIFICATION_PASS`;
`PHASE105_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`; and
`POST_V0_8_DAILY_REPLAY_105 = FORMALLY_COMPLETE`. Retain
`NAR_PASSIVE_TIMING_AND_ACTUAL_SEND_ENVIRONMENT_AUTHORITY = FORMALLY_INTEGRATED`
and `CONTROLLED_TIMING_EVIDENCE_ISSUANCE = VERIFIED`. Phase104 remains
formally complete with
`NAR_RUNTIME_BINDING_AND_CAMPAIGN_EXECUTION_AUTHORITY = FORMALLY_INTEGRATED`.

Freeze `DIAGNOSTIC_DRY_RUN != PROSPECTIVE_OFFICIAL_CAMPAIGN`,
`SYNTHETIC_TRANSPORT_TIMING != PROVIDER_OPERATIONAL_TIMING_EVIDENCE`,
`INSTRUMENTATION_COVERAGE != CONCRETE_DELTA_AUTHORITY`, and
`STAGE_DURATION_SUM != CRITICAL_PATH_DURATION_UNLESS_COMPOSITION_PROVEN`.
The design preparation itself authorized no production-code or test change;
the subsequent explicit Phase106 implementation instruction authorized the
restricted implementation and one normal commit/push after verification.
Provider HTTP, live campaign, production DB writes, and Delta choice remain
forbidden.

### Primary finding: generic measurement is present; operational wiring is not

Phase105 supplies `measure_nar_operation`, controlled attempt/terminal/
overhead publication, `NAROfficialTimingGuardedSession`, and private Session
factory hooks. A source audit found no production call site of
`measure_nar_operation`; it is currently exercised only by focused tests.
Consequently no V2 production stage is already an end-to-end wired timing
campaign stage. The first rehearsal must be an explicit diagnostic composition,
not an assertion that the ordinary acquisition/prediction applications are
already measured.

### Exact V2 stage coverage matrix

| Stage | Current callable boundary / artifact | Role | State | Diagnostic design decision |
| --- | --- | --- | --- | --- |
| `CAMPAIGN_EXECUTION_PREPARATION` | runner bootstrap, lock, source/runtime derivation | campaign control | BLOCKED_BY_UNRESOLVED_SEMANTICS | occurs before a capability; use a non-attempt control receipt, never Phase105 recursive attempt |
| `RUNTIME_BINDING_READINESS` | `issue_current_process_execution` readiness receipt | campaign control | BLOCKED_BY_UNRESOLVED_SEMANTICS | same pre-capability boundary; report provenance, not an attempt duration |
| `SCHEDULER_DISPATCH` | none; no scheduler is authorized | PRE_C | NOT_CURRENTLY_REACHABLE | exclude from diagnostic plan and future stage set until a separately reviewed runner dispatch boundary exists |
| `BOOTSTRAP_HOME_ACQUISITION` | `capture_official_home` -> bootstrap transport `fetch`; supplier capture | PRE_C / HTTP | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | transport proxy + guarded bootstrap Session; provider correlation; output supplier capture SHA/ID |
| `MONTHLY_ROOT_ACQUISITION` | `capture_monthly_root` -> bootstrap transport; root locator | PRE_C / HTTP | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | same; correlation is provider/target-date plan instance; output supplier capture |
| `LOCATOR_SCRIPT_ACQUISITION` | `capture_locator_script` -> bootstrap transport; script resolution | PRE_C / HTTP | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | same; output capture and deterministic locator material |
| `MONTHLY_SCHEDULE_ACQUISITION` | daily `capture_supplied_response` for monthly request | PRE_C / HTTP | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | guarded daily-target transport proxy; output monthly capture |
| `RACE_LIST_ACQUISITION` | daily capture for each normalized venue locator | PRE_C / HTTP | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | one predeclared diagnostic instance per fixture venue, serial order, capture output |
| `OFFICIAL_RESPONSE_ACQUISITION` | `NAROfficialLiveResponseCaptureService.capture_response` -> private Requests transport | PRE_C / HTTP | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | needs diagnostic composition factory for its private transport; output official capture |
| `MARKET_ODDS_RAW_ACQUISITION` | `acquire_nar_market_odds_raw_response` -> market transport `fetch` | PRE_C / HTTP | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | public transport with guarded Session factory; output raw capture SHA/ID |
| `RAW_CAPTURE_VALIDATION` | validation is interleaved with each capture transport/service | PRE_C | BLOCKED_BY_UNRESOLVED_SEMANTICS | do not relabel a composite capture as validation; require a reviewed split boundary |
| `RAW_CAPTURE_PERSISTENCE` | `save_supplier_capture` / `save_capture` on distinct evidence archives | PRE_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | archive proxy can time exact save/reload per concrete capture type; no composite capture double count |
| `PARSING` | daily `_parse`, bootstrap parser, market parser, historical-input parser | PRE_C | BLOCKED_BY_UNRESOLVED_SEMANTICS | current public functions combine parsing and normalization; no separate attempt until boundary is reviewed |
| `NORMALIZATION` | `normalize_nar_monthly_convene_info`, `normalize_nar_race_list`, source parsers | PRE_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | only whole public pure operation may be measured as inclusive diagnostic dimension; never summed with child parse time |
| `SOURCE_RECORD_CONSTRUCTION` | `normalize_nar_historical_input_source_records` / daily target bundle construction | PRE_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | wrap exact public constructor once fixture capture ancestry is present; artifact is resulting source-record/bundle digest |
| `PROVIDER_IDENTITY_BINDING` | target/evidence identities are constructed inside daily source functions | PRE_C | BLOCKED_BY_UNRESOLVED_SEMANTICS | no standalone callable; require a narrow identity-binding adapter if separately measured |
| `SNAPSHOT_CONSTRUCTION` | `build_historical_input_snapshot` | PRE_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | direct pure wrapper; output snapshot content SHA |
| `SNAPSHOT_PERSISTENCE` | `SQLiteHistoricalInputSnapshotRepository.save_snapshot` | PRE_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | exact repository-save adapter; output snapshot identity/content SHA |
| `SNAPSHOT_EXACT_RELOAD_CONFIRMATION` | `load_snapshot_by_identity` comparison | PRE_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | separate exact-load adapter; no inferred reload success |
| `FREEZE_RECEIPT_CONSTRUCTION` | internal part of `issue_historical_input_snapshot_freeze_receipt` | freeze provenance | BLOCKED_BY_UNRESOLVED_SEMANTICS | receipt construction/publication/reload are currently one controlled function; do not claim three timings until reviewed callbacks exist |
| `FREEZE_RECEIPT_PUBLICATION` | controlled receipt archive save | freeze provenance | BLOCKED_BY_UNRESOLVED_SEMANTICS | same composite limitation; required provenance cost remains visible, not zero |
| `FREEZE_RECEIPT_EXACT_RELOAD` | controlled receipt archive load | freeze provenance | BLOCKED_BY_UNRESOLVED_SEMANTICS | same composite limitation |
| `ATTEMPT_START_PUBLICATION` | Phase105 nonrecursive attempt save/reload overhead | observability overhead | WIRED_AND_DIAGNOSTICALLY_EXECUTABLE | automatically emitted by real wrapper; never a recursive attempt |
| `TERMINAL_PUBLICATION` | Phase105 nonrecursive terminal save/reload overhead | observability overhead | WIRED_AND_DIAGNOSTICALLY_EXECUTABLE | automatically emitted after terminal publication; never recursive |
| `SNAPSHOT_ADAPTER` | `build_simulation_race_input_from_historical_snapshot` | POST_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | pure direct wrapper from a frozen fixture snapshot |
| `PREDICTION_PIPELINE` | `PredictionPipeline.run` through historical plan execution | POST_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | direct wrapper over frozen adapter output; no provider collaborator |
| `ALLOCATION` | `FixedStakeBetAllocator.allocate` inside persisted plan service | POST_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | requires a service-level adapter to avoid reimplementing allocation |
| `BET_PLAN_CONSTRUCTION` | `SimulationBetPlanBuilder.build` inside persisted plan service | POST_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | requires same narrow service decomposition or inclusive service measurement |
| `BET_PLAN_PERSISTENCE` | bet-plan snapshot repository `save_snapshot` | POST_C | WRAPPER_PRIMITIVE_AVAILABLE_NOT_WIRED | repository proxy after exact builder output |
| `SHADOW_ARTIFACT_PUBLICATION` | no NAR Phase105 shadow publication path | POST_C | NOT_CURRENTLY_REACHABLE | exclude until a separately reviewed shadow artifact exists |

`NARTimingCorrelation` remains descriptive only: it supports provider,
target-set, and race/cutoff joins, but not a nested operation tree, target date,
venue, request URL, or snapshot edge. The diagnostic plan therefore owns
non-authoritative instance keys, fixture digests, and a composition DAG; it
does not retrofit authority into correlation.

### Diagnostic authority and archive decision

Do not alter the immutable Phase104 execution-claim payload. Phase106 should
add a distinct immutable `NAROperationalTimingDiagnosticCampaignPlanV1` and
an immutable post-claim `NAROperationalTimingDiagnosticExecutionDeclarationV1`.
The plan object is constructed from reviewed Git objects before entering the
runner, but it is not durably persisted before V2 activation or Phase104
authority issuance. It binds `DIAGNOSTIC_NO_NETWORK_V1`, exact V2
configuration/session, sealed fixture manifest, fixed expected stage
instances, sequence/order/composition rules, and a fixed-window stopping rule.
The declaration, issued only after exact
Phase104 claim/readiness reload and before any attempt, binds exact plan,
claim, configuration/session/activation/runtime ancestry, and fixture manifest.
It is not an official execution claim and supplies no `official=True` flag.

Use a separate temporary diagnostic SQLite archive with a Phase106 diagnostic
companion registry. Its exact union contains the Phase99--105 tables plus
diagnostic plan/declaration tables and an append-only trigger requiring a
diagnostic declaration for every Phase105 attempt insert. Phase106-compatible
gates may accept this exact union; historical strict validators remain strict.
Future official aggregation must reject both a diagnostic companion registry
and any diagnostic execution declaration. Thus copied diagnostic evidence
retains its `DIAGNOSTIC_ONLY` structural marker and cannot qualify merely by
having valid V2/Phase104/Phase105 ancestry.

The final implemented no-network authority order is:

1. Construct immutable fixture and plan objects from reviewed Git objects.
2. Enter the normal Phase105 runner/archive composition.
3. Establish the prospectively activated V2 session.
4. Issue the Phase104 runtime binding, one-shot claim, readiness, and current-process capability.
5. Confirm that zero attempts exist for the claim.
6. Under the same held campaign lock, explicitly install the Phase106 diagnostic companion.
7. Persist and exact-reload the fixture authority.
8. Persist and exact-reload the diagnostic plan.
9. Persist and exact-reload the diagnostic execution declaration binding the exact plan and claim.
10. Only then allow the first Phase105 timing attempt. Execute only predeclared fixture operations; HTTP uses guarded Sessions with deterministic fake adapters below `Session.send`, so no NAR bytes are requested.

The plan population and continuation rules are immutable before step 10;
durable plan publication is deliberately after the normal Phase104 authority
chain and still before the first attempt. Close the runner and derive a
read-only reconciliation. No retry, resume, plan mutation, or post-hoc stage
selection occurs.

The diagnostic plan's exact fixture stage instances fix sequence numbers and
expected cardinality. The first rehearsal must be complete only relative to
that exact fixture plan; it is not a claim of full V2 taxonomy coverage. For a
future live plan, discovery must itself be predeclared: bootstrap=3,
monthly=1, and every race-list locator produced by the canonical monthly
discovery rule is acquired once in canonical serial order. A discovery-closure
receipt must be immutable before iterating those derived requests. Neither
success, timeout, nor executability may determine whether an already-planned
operation is retained.

### Qualification and reconciliation contract

The reconciliation is a pure, read-only `NAROperationalTimingCampaignReconciliation`
derived from archive rows and the immutable plan. It neither saves a summary
nor repairs evidence. It reports expected instances; observed attempts;
terminals; sequence gaps/conflicts; unresolved attempts; environment rows;
nonqualifying HTTP preconditions; overhead coverage; activation/readiness/
claim ancestry; the separately derived plan-node state; and a closed campaign
completeness result. It does not use a generic “missing required stage” result
that can erase or misclassify an upstream provider observation.

`PHASE106_ARCHITECTURAL_REVIEW_REQUIRES_REVISION` is recorded. Freeze
`UPSTREAM_PROVIDER_FAILURE_MUST_NOT_CAUSE_DENOMINATOR_ERASURE`,
`DIAGNOSTIC_PLAN_MUST_DISTINGUISH_CAUSAL_NONEXECUTION_FROM_MISSING_STAGE`,
`QUALIFIED_PROVIDER_FAILURE_REMAINS_IN_DENOMINATOR`, and
`DOWNSTREAM_CAUSAL_NONEXECUTION_DOES_NOT_ERASE_UPSTREAM_FAILURE`. The prior
single vocabulary is replaced by two independent, non-convertible layers.

**Observation qualification** is derived per persisted operation attempt and
its child evidence. Its closed states are
`QUALIFIED_OPERATIONAL_TIMING_OBSERVATION`,
`NONQUALIFYING_REQUEST_ENVIRONMENT`, `UNRESOLVED_ATTEMPT`,
`EXECUTION_ANCESTRY_INVALID`, and `DIAGNOSTIC_ONLY`. Terminal disposition
(`SUCCESS`, provider `FAILURE`, or provider `TIMEOUT`) remains a separate fact:
a qualified provider failure or timeout is still a qualified observation. A
missing terminal is instead `UNRESOLVED_ATTEMPT`, an evidence-integrity issue.
For HTTP, qualification requires exact attempt/execution ancestry, a terminal,
and a qualifying actual-send environment verification; a terminal alone is
not enough. A diagnostic declaration has structural precedence:
`DIAGNOSTIC_ONLY_OVERRIDES_INNER_OBSERVATION_QUALIFICATION`. Thus a diagnostic
fake HTTP request with a qualifying direct environment and a successful or
timeout terminal remains `DIAGNOSTIC_ONLY` and cannot enter official
aggregation.

**Plan-node reconciliation** is independently derived from the immutable plan
and archive evidence. Its closed states are `OBSERVED_AS_PLANNED`,
`EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE`,
`PRECONDITION_BLOCKED`, `MISSING_UNEXPLAINED`, and
`EVIDENCE_INTEGRITY_FAILURE`. A reconciliation state never retroactively
changes an observation qualification. Example: a planned HTTP node that
qualifies at the send guard and then produces a proven `READ_TIMEOUT` is
`OBSERVED_AS_PLANNED`; its provider timeout remains in the future official
denominator. Parsing, normalization, and snapshot nodes that predeclared
`REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS` are
`EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE`, not missing. In contrast,
a successful acquisition followed by no parsing evidence is
`MISSING_UNEXPLAINED`; an environment rejection is `PRECONDITION_BLOCKED`; and
an attempt without terminal is `EVIDENCE_INTEGRITY_FAILURE`.

Freeze `MEASUREMENT_DENOMINATOR_MUST_BE_PREDECLARED_BEFORE_FIRST_ATTEMPT`.
The plan fixes its scheduled operation population, stopping rule, dependency
DAG, and continuation semantics before any attempt. It never uses “continue
until N successful observations.” Each node declares one closed continuation
rule: `INDEPENDENT`, `EXECUTE_AFTER_PREDECESSORS_TERMINATE_REGARDLESS_OUTCOME`,
or `REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS`, together with any branch
terminal rule. Therefore independent later work still executes after a branch
failure when planned, while genuinely dependent work is causally nonexecutable
without becoming unexplained missing evidence.

Critical-path reconstruction uses the plan's directed dependency/composition
graph, not a sum of rows. An inclusive composite dimension and any contained
leaf attempts may both be recorded for diagnosis, but reconciliation labels
them non-additive and computes no Delta. HTTP elapsed intentionally includes
environment verification publication/reload; attempt and terminal publication
costs remain separate nonrecursive overhead records.

### Revised plan identity, diagnostic isolation, and fixture contract

Each `NARDiagnosticCampaignPlanNodeV1` has a deterministic identity distinct
from a Phase105 attempt: exact plan identity; deterministic node key; stage;
expected sequence for an **operation-attempt** node only; target/race/request
scope; correlation material; expected HTTP transport, direct-policy semantic,
and safe canonical URL digest where applicable; predecessor node keys;
continuation rule; branch-terminal rule; and composition role. A future
attempt cannot be fully predeclared because it includes the causal admission
time. The diagnostic execution context instead validates the next exact plan
node before invoking `measure_nar_operation`; the reconciler independently
maps the resulting attempt by execution identity, sequence, stage, scope,
correlation, expected policy, and URL digest. An extra or mismatched attempt
is rejected at the gate where possible and is always an integrity failure in
read-only reconciliation.

Do not model all V2 stages as normal attempts. The plan separates (1)
operation-attempt nodes, (2) nonrecursive Phase105 overhead evidence for
`ATTEMPT_START_PUBLICATION` and `TERMINAL_PUBLICATION`, and (3)
control/provenance evidence such as runner/readiness and the currently
composite freeze receipt. Overhead records receive no fake attempt sequence;
control prerequisites are required evidence rather than invented timing
attempts. Stages whose truthful boundary remains unresolved stay
`BLOCKED_BY_UNRESOLVED_SEMANTICS`; Phase106 must not refactor the freeze receipt
or composite capture pipeline merely to report complete enum coverage.

Freeze `DIAGNOSTIC_SCHEMA_INSTALLATION != NORMAL_OFFICIAL_ARCHIVE_UPGRADE`.
Only an explicit `bootstrap_nar_operational_timing_diagnostic_archive` may
install the exact Phase106 companion on a temporary diagnostic archive. The
normal Phase105 bootstrap and its official-parent known state remain unchanged.
The diagnostic repository accepts only the exact Phase99--105 union plus the
Phase106 diagnostic registry/tables/triggers; partial or unknown state fails
closed. Historical strict validators remain strict. Controlled plan and
declaration issuance require private trusted-composition markers, exact
save/reload, and active Phase104 capability respectively. They cannot
retrospectively label an unrelated archive or backfill a declaration. The
final implemented order is immutable plan construction -> normal Phase105
runner/archive -> prospectively activated V2 session -> Phase104 binding,
claim, readiness, and current-process capability -> zero-attempt check ->
diagnostic companion installation under the same lock -> fixture save/reload ->
plan save/reload -> diagnostic declaration save/reload -> first attempt.

Freeze `FIXTURE_PATH != DIAGNOSTIC_FIXTURE_CONTENT_AUTHORITY`. A
`NARDiagnosticFixtureBundleV1` is content addressed from local Git objects,
not mutable worktree paths: repository identity, commit and tree SHA, ordered
repository paths, Git blob identity where available, byte length, SHA-256, and
a canonical member manifest are bound to one bundle identity. The plan binds
that identity; fixture materialization verifies those bytes before use. A
worktree edit after bundle materialization cannot change diagnostic inputs.

Diagnostic fake adapters sit below the real guarded `Session.send` path and
never contact NAR. Private diagnostic adapter-factory injection must preserve
the direct default `_HTTPAdapter(max_retries=0)` branch in all four transports,
including market odds, or narrowly update the Phase104 AST inspector. In both
cases regression tests must prove that the default derived static profile is
exactly unchanged for timeout, retry, redirect, TLS, stream,
`Accept-Encoding`, and `trust_env`; a diagnostic adapter identity is never
production runtime-profile authority.

### Required future implementation and tests

Likely new paths are
`scripts/simulation/nar_operational_timing_diagnostic_campaign.py`,
`scripts/simulation/nar_operational_timing_diagnostic_archive_migration.py`,
`scripts/simulation/sqlite_nar_operational_timing_diagnostic_archive.py`, and
`scripts/simulation/nar_operational_timing_campaign_reconciliation.py`, with
matching focused tests and a real sealed-child no-network E2E. Narrow
compatibility-gate/bootstrap updates are permissible; Phase99--105 canonical
domains and claim payload remain untouched. A diagnostic adapter factory may
need a private default-preserving HTTP-adapter injection at the four transport
constructors because their current constructors install a normal
`HTTPAdapter` after Session construction; a fake adapter must sit below the
guarded `Session.send` path without global monkeypatching.

Required tests include the full sealed-child diagnostic path; fake HTTP success,
ConnectTimeout, ReadTimeout, generic transport error, and direct-policy
rejection; and real guarded pre-send fake-adapter ordering. They must prove
that a qualified provider timeout remains an observation while its dependent
parse/normalize/snapshot nodes become
`EXPECTED_NOT_EXECUTABLE_DUE_TO_UPSTREAM_FAILURE`; that an independent later
node still executes when the predeclared rule requires it; and that successful
upstream work followed by an absent runnable node is
`MISSING_UNEXPLAINED`, not causal nonexecution. An unresolved terminal is an
integrity failure, never an inferred provider outcome.

Also require fixed-plan/no-success-stopping behavior, plan save/reload before
declaration and declaration save/reload before first attempt, rejection or
deterministic detection of unexpected attempts, diagnostic structural
precedence over inner environment/terminal success, exact diagnostic-only
bootstrap (and proof normal Phase105 bootstrap does not install it), immutable
Git-object fixture manifests, worktree-mutation/corruption rejection, all
currently wired overhead records, deterministic pure reconciliation,
nested/inclusive no-double-count labels, POST_C no-provider proof, and default
four-transport/market-odds static-runtime-profile equivalence after private
adapter-factory injection. Use committed fixtures and temporary archives only.

Remaining blockers are `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`,
Phase94 historical entry-status authority, Phase95 prospective entry-status
semantics, Phase41 market eligibility, explicit prospective live-campaign
authorization, and reviewed exact split boundaries for the currently composite
raw-validation/parsing/freeze stages. Recommended disposition:
`DRAFT_FOR_REVIEW`; do not authorize an all-stage diagnostic claim until the
diagnostic authority/plan/reconciliation contract and the exact selected
stage-adapter set receive architectural review.

## POST_V0_8_DAILY_REPLAY_105

Title: NAR V2 Passive Timing, Request-Effective Environment, and Sealed-Child E2E

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Audit: NAR_PASSIVE_TIMING_AND_REQUEST_ENVIRONMENT_DESIGN_COMPLETE

Design Review: PHASE105_PASSIVE_TIMING_AND_REQUEST_ENVIRONMENT_DESIGN_REVIEW_PASS

Implementation: NAR_PASSIVE_TIMING_AND_ACTUAL_SEND_ENVIRONMENT_AUTHORITY_IMPLEMENTED

Base Commit and Branch: `7e82b5c870e153eefac14cc7cdfbd00c126f8983` / `feature/post-v0.8-daily-replay`

### Limited controlled-issuance correction authorization

Independent verdict: `PHASE105_IMPLEMENTATION_REMOTE_VERIFICATION_REQUIRES_CORRECTION`.
Blockers: `PERSISTED_TIMING_EVIDENCE_CAN_BYPASS_CURRENT_PROCESS_CAPABILITY` and
`ATTEMPT_TERMINAL_CONTROLLED_ISSUANCE_REQUIRED`. Freeze
`PERSISTED_CLAIM_ANCESTRY != CONTROLLED_TIMING_EVIDENCE_ISSUANCE` and
`TIMING_EVIDENCE_PUBLICATION_REQUIRES_CURRENT_PROCESS_CONTROLLED_ISSUANCE`.
Attempt, terminal, and nonrecursive overhead saves require a private controlled
issuance marker before either insertion or exact-duplicate handling. The passive
wrapper supplies it only while holding a live matching runner capability;
request-environment issuance remains restricted to the existing guarded
pre-network-send marker. Terminal save and load additionally require causal
UTC finish no earlier than the archived attempt admission timestamp. These are
trusted-composition/API-discipline rules, not cryptographic authority.

Correction implementation: attempt, terminal, and nonrecursive overhead
publication now reject an uncontrolled call, including an exact duplicate.
The passive wrapper rechecks its live current-process capability before each
controlled publication. The existing guarded pre-send environment marker is
unchanged. Terminal publication and exact reload require
`operation_finished_at >= attempt_admitted_at` against the archived attempt.
A closed runner's persisted claim/readiness cannot authorize direct timing
evidence publication. Focused stale-runner, direct-save, duplicate, and
backdated/corrupt-terminal regressions passed; the independent correction
review remains pending. The correction neither changes Phase104 authority nor
claims cryptographic protection against code operating outside trusted
composition.

Allowed Files for this correction: `docs/CURRENT_PHASE.md`,
`docs/LATEST_CODEX_REPORT.md`,
`scripts/simulation/sqlite_nar_operational_timing_attempt_archive.py`,
`scripts/simulation/nar_operational_timing_passive_wrapper.py`, and
`tests/test_nar_operational_timing_passive_wrapper.py`.
Forbidden Files: every other production module and test, production databases,
logs, Phase99–104 contracts, provider transports, cutoff/policy code.
Required Tests: corrected Phase105 focused tests; all Phase104 focused tests;
Phase99/100/103 timing/archive regressions; affected transport tests; full
repository pytest; `git diff --check`; exact changed-path audit; final clean
`git status --short`; and a post-commit no-network sealed-child smoke of the
correction commit using real `python -I -B` isolation.
Stop Condition: a wider production/schema change is necessary, provider HTTP
or production DB write becomes necessary, tests fail outside the correction,
unexpected paths change, or normal push would require force.

### Implementation for independent review

Phase105 adds separate V2 attempt and terminal canonical domains, an append-only
same-database companion with a restrictive execution-claim FK, one environment
verification per HTTP attempt, and nonrecursive publication-overhead records.
The campaign runner owns UTC/monotonic providers and a one-shot sequence
allocator. An admitted attempt is committed and exact-reloaded before the
underlying callable begins. A terminal write failure leaves that attempt
discoverable; it does not replace the production result or exception.
HTTP attempts bind a safe exact expected-request-URL SHA-256; the later child
verification binds the prepared URL SHA-256 and must agree with that ancestry
when marked as an exact URL match. The actual environment verification identity
remains absent from the earlier attempt payload.

The guarded Requests Session checks the actual PreparedRequest and merged send
kwargs immediately before adapter I/O. It publishes and exact-reloads a
non-secret child verification before delegating. A proxy, CA path override,
authorization, client certificate, URL mismatch, or static-profile mismatch
records nonqualifying evidence and prevents send. `PERSISTED_ATTEMPT !=
OFFICIAL_TIMING_SAMPLE`; an HTTP sample requires its own
`QUALIFIED_DIRECT_REQUEST_ENVIRONMENT` child. Request-environment publication
cost is inside HTTP elapsed time. The four NAR transports gained only a private
default-preserving Session factory; no default URL, header, timeout, retry,
parsing, or prediction semantics were changed. No provider request, live
campaign, Delta calculation, or production-database write was performed.

A real Git-object-derived sealed `python -I -B` child test obtains the Phase104
current-process capability without monkeypatching the isolation check or making
an HTTP request. This test exercises the reviewed committed Phase104 bundle;
Phase105 official code must itself be run from its subsequently reviewed sealed
commit before a future authorized campaign. Phase105 remains not formally
complete pending independent implementation review. Prospective live campaign
authorization, `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`, and
Phase94/95/41 source-semantic blockers remain unresolved.

### Phase104 reconciliation

`PHASE104_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`; `POST_V0_8_DAILY_REPLAY_104 = FORMALLY_COMPLETE`; `NAR_RUNTIME_BINDING_AND_CAMPAIGN_EXECUTION_AUTHORITY = FORMALLY_INTEGRATED`; and `ONE_SHOT_CAMPAIGN_EXECUTION_PARENT = VERIFIED` are reconciled. Phase103 remains formally complete. Retain `REQUEST_EFFECTIVE_NETWORK_ENVIRONMENT_BINDING_REQUIRED_FOR_OFFICIAL_ATTEMPTS` and `SEALED_BUNDLE_ISOLATED_CHILD_SUCCESS_PATH_REQUIRES_PHASE105_E2E`.

### Architectural revision markers

`PHASE105_ARCHITECTURAL_REVIEW_REQUIRES_REVISION` is accepted. The resolved design blockers are `PRECOMPUTED_REQUEST_ENVIRONMENT_DESCRIPTOR_NOT_CAUSALLY_BOUND_TO_ACTUAL_SEND` and `ATTEMPT_ENVIRONMENT_IDENTITY_CAUSAL_ORDER_CONFLICT`. Freeze `PRE_REQUEST_ENVIRONMENT_OBSERVATION != REQUEST_EFFECTIVE_SEND_CONFIGURATION` and `ATTEMPT_PUBLICATION_PRECEDES_ACTUAL_SEND_ENVIRONMENT_RESOLUTION`. A pre-call observation may be diagnostic but cannot qualify an official provider send.

### Authority, attempt, and terminal contract

Official ancestry is V2 configuration -> V2 session -> V2 activation -> runtime binding -> campaign execution claim -> current-process capability -> V2 attempt -> V2 terminal. `PERSISTED_EXECUTION_CLAIM != CURRENT_PROCESS_EXECUTION_CAPABILITY`. A Phase105 attempt table must reference the Phase104 claim with `ON UPDATE RESTRICT ON DELETE RESTRICT` from creation; a terminal must strictly reference its attempt. No weak text parent, table rebuild, synthetic capability, or backfill.

`NAROperationalTimingAttemptV2` is `nar-operational-timing-attempt-v2:<sha256>` over canonical JSON and binds exact V2 configuration/session/claim, stage, version-independent descriptive correlation, runner-owned sequence, `attempt_admitted_at`, closed load context, and only the closed expected HTTP policy semantic `DIRECT_REQUEST_ENVIRONMENT_V1` where applicable. It must **not** bind a future actual-send verification identity. Enforce `UNIQUE(claim_identity, attempt_sequence)`. `attempt_admitted_at` is `MEASUREMENT_ATTEMPT_ADMISSION_TIMESTAMP`: a campaign-owned UTC sample before durable publication and callable entry. Membership remains `start <= admitted < end`; callable entry may be later because publication overhead.

`NAROperationalTimingTerminalV2` is `nar-operational-timing-terminal-v2:<sha256>` and binds attempt, causal UTC finish, integer monotonic microseconds, closed disposition/failure classification, and optional existing artifact SHA. It excludes exception text, results, payouts, ROI, and policy material. Coherent initial states are `SUCCESS`/none; `TIMEOUT`/`CONNECT_TIMEOUT|READ_TIMEOUT`; `FAILURE`/`TRANSPORT|VALIDATION|PERSISTENCE|INTERNAL`; and `UNSUPPORTED`/`UNSUPPORTED`.

### Timing order, propagation, and overhead

The sole production elapsed source is campaign-owned `time.perf_counter_ns()` with `(finish_ns - start_ns) // 1000`, integer-only, nonnegative, floor-truncated, and zero below one microsecond. UTC is causal only. Non-HTTP ordering is capability validation -> UTC admission -> half-open check -> attempt save and exact reload -> monotonic start -> untouched callable -> monotonic finish -> UTC finish -> terminal publication. HTTP uses this same order through monotonic start, then enters the guarded Requests send boundary below.

Successful return values and all provider/prediction inputs and outputs remain exact. On a production exception, record finish values, classify exact types/cause ancestry, try terminal publication, then re-raise the original exception unchanged. Existing transports wrap Requests errors, so timeout inference is allowed only from exact direct or `__cause__` type chains; otherwise use conservative `TRANSPORT`, never message text. Attempt publication/reload failure fails the official wrapper before callable execution. Terminal publication failure preserves the operation's result/exception and leaves the prior attempt unresolved; it is diagnostic only.

`ATTEMPT_START_PUBLICATION` and `TERMINAL_PUBLICATION` use a direct nonrecursive publication-overhead family bound to claim/attempt/terminal where available, not recursively emitted attempts. Missing overhead evidence is explicit and cannot alter production behavior; later Delta review must not treat mandatory overhead as zero.

### Request-effective environment verification authority

`STATIC_RUNTIME_TRANSPORT_PROFILE != REQUEST_EFFECTIVE_NETWORK_ENVIRONMENT`. Replace the precomputed descriptor with `NARRequestEffectiveEnvironmentVerification`, `nar-request-effective-environment-verification-v1:<sha256>`, a strict child of the exact V2 attempt. Its direction is `verification -> attempt`, never an impossible forward `attempt -> future verification`. Persistent HTTP ancestry is claim -> attempt -> verification -> terminal; non-HTTP attempts have no verification row.

The verification is made at the actual Requests pre-network boundary: after `Session.prepare_request(...)` and `Session.merge_environment_settings(...)` produce the concrete `PreparedRequest` and send kwargs, but immediately before adapter network I/O. `NAROfficialTimingGuardedSession` preserves normal Requests preparation and `send` semantics, but its `send` guard validates live capability and exact attempt/session/claim ancestry; validates PreparedRequest URL against the domain-expected URL; inspects actual send kwargs; persists and exact-reloads one verification; then delegates to ordinary `Session.send`. It does not recompute proxies or environment settings. Environment changes after merge cannot change the resolved kwargs for that invocation, without claiming protection against kernel/network changes after send begins.

The payload is limited to schema/version, attempt identity, canonical PreparedRequest URL identity, transport/static-profile identity, `trust_env`, non-secret effective proxy mode/material, effective verify mode, client-cert presence/mode, Authorization-present state, Proxy-Authorization-present state, and direct-policy semantic. It stores neither credentials, proxy passwords, netrc contents, private-key material, nor secret-bearing URLs. The URL must be exact canonical HTTPS without userinfo and equal the stage/correlation-derived expected URL; `allow_redirects=False` prevents redirect reuse.

`DIRECT_REQUEST_ENVIRONMENT_V1` requires before send: empty actual effective proxy mapping; `verify is True`; no client certificate; no Authorization; no Proxy-Authorization; exact reviewed static ancestry; and still-valid capability. This observes concrete send inputs rather than inferring absent environment variables, naturally covering proxy variables, `NO_PROXY`, Windows/system proxy resolution, CA bundles, and netrc auth. Market odds (`trust_env=False`) is not exempt and must pass the same send guard. Violation means no network send. `UNIQUE(attempt_identity)` enforces one verification per official HTTP attempt. Verification save/reload occurs inside the already-started monotonic HTTP interval and is included in HTTP elapsed duration; direct nonrecursive overhead may also record it.

### Composition boundaries and E2E

Use decorators around injected protocol boundaries, not provider rewrites. The three persistent-session transports (bootstrap, daily target, official response) receive an optional private Session-factory dependency whose default remains `requests.Session`; market odds receives the same factory at its fetch-local construction point. Official composition supplies the guarded factory; ordinary callers retain the default path. Global monkeypatching of `requests.Session` is forbidden. Bootstrap `fetch` maps page kind to home/root/locator stages; daily-target `fetch` maps validated request identity to schedule/race-list stages; official and market-odds transport `fetch` compose at canonical URLs. Existing `NARDailyTargetLiveAcquisitionApplication` already accepts both transport protocols. Decorate exact validated boundaries for raw validation/persistence, parsing, normalization, source-record/provider identity, snapshot build/save/exact reload, Phase99 freeze receipt construction/publication/reload, and POST-C snapshot adapter/pipeline/allocation/plan build/save/shadow publication. No wrapper may acquire provider information after C or change Phase99 freeze meaning.

Phase105 requires a real no-network isolated-child E2E, without monkeypatching `_require_isolated_source`: materialize the Git-object bundle, launch `python -I -B`, use a minimal stdlib-only launcher that rejects `PYTHONPATH`/`PYTHONHOME` ambiguity, changes outside the worktree, inserts only sealed root, validates sole `scripts` namespace and critical origins, bootstraps a temporary archive with a prospective activated V2 session, and obtains the genuine Phase104 capability with no provider operation. The launcher is not a provider client and never imports mutable KeibaOS modules before sealed-root setup.

### Persistence, bootstrap, and separation

A new Phase105 same-database companion persists attempts, terminals, request-effective environment verification records, and nonrecursive overhead records. It requires exact Phase99 + Phase100 + Phase103 + Phase104 schema, adds atomically, validates only the exact State-5 union, has append-only triggers and exact-reload/idempotency/conflict rules, and makes no backfill. Its FKs are attempt -> claim, verification -> attempt, and terminal -> attempt; HTTP verification has `UNIQUE(attempt_identity)`. Bootstrap advances only known State 0/1/2/3/4 to State 5 under the existing archive lock; partial/unknown topology fails and historical strict validators remain strict.

No caller `official=True` authorizes evidence. Official attempts require archived V2 activation, Phase104 binding/claim/readiness, live current-process capability, qualified request environment when HTTP, and strict attempt/terminal ancestry. Diagnostic evidence stays separately classified and cannot enter official Delta aggregation. Phase105 implementation would still not authorize provider HTTP or a live campaign.

### Expected scope, tests, and stop condition

Likely new paths are `scripts/simulation/nar_operational_timing_attempt_v2.py`, `nar_operational_timing_request_environment.py`, `nar_operational_timing_passive_wrappers.py`, `nar_operational_timing_isolated_child_launcher.py`, `nar_operational_timing_attempt_archive_migration.py`, and `sqlite_nar_operational_timing_attempt_archive.py`; narrow bootstrap/compatible-schema changes and optional private Session-factory injection in the four transport modules require review. Provider request arguments and semantics, timeout/retry, parsing, cutoff, and Phase99 receipt semantics are forbidden from change.

Future tests cover claim/capability/FKs, admission/reload-before-call, deterministic sequence, elapsed conversion, result/exception preservation, type-based timeout handling, unresolved attempts, actual PreparedRequest/send proxy/CA/auth verification (including `trust_env`, proxy, `NO_PROXY`, CA bundle, and netrc without secrets), rejection before adapter send, one verification/HTTP attempt, sealed-child success/shadow rejection, nonrecursive overhead, exact schema transitions, append-only behavior, and Phase99-104 coexistence; then all Phase99-104 regression suites and full pytest.

Allowed Files for implementation: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`, new Phase105 attempt, request environment, wrapper, isolated launcher, migration and SQLite archive modules under `scripts/simulation/`, the four reviewed NAR live transport modules, Phase99–104 compatible schema gate modules, `scripts/simulation/nar_operational_timing_archive_bootstrap.py`, `scripts/simulation/nar_operational_timing_campaign_runner.py`, and matching new Phase105 tests under `tests/`. Forbidden Files: all other production modules, existing tests, production database and logs. Required Tests: new Phase105 focused tests; Phase99–104 timing/archive/activation tests; affected transport tests; full repository pytest; `git diff --check` and exact changed-path audit. Stop Condition: changed provider semantics, a weak execution parent, leaked secret material, unguarded network send, unexpected initial worktree files, out-of-scope test failure, or non-fast-forward push requirement.

Remaining blockers: independent Phase105 implementation review; later prospective-campaign authorization; `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`; Phase94/95 entry-status authority; and Phase41 market eligibility. Recommended disposition: `READY_FOR_REVIEW`.

Next: `CHATGPT_REVIEW_PHASE105_IMPLEMENTATION`.

## POST_V0_8_DAILY_REPLAY_104

Title: NAR Runtime Binding and One-Shot Campaign Execution Authority

Formal Status: READY_FOR_REVIEW

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Audit: NAR_RUNTIME_BINDING_AND_CAMPAIGN_EXECUTION_AUTHORITY_DESIGN_COMPLETE

Design Review: PHASE104_RUNTIME_AND_EXECUTION_AUTHORITY_DESIGN_REVIEW_PASS

Implementation: NAR_RUNTIME_BINDING_AND_CAMPAIGN_EXECUTION_AUTHORITY_IMPLEMENTED

Base Commit and Branch: `1236f1e0db84ce6025d07c052abbb3c7348aab3e` / `feature/post-v0.8-daily-replay`

### Implementation result (pending independent verification)

Phase104 adds a Git-object-derived content-addressed source bundle, exact local
bundle/origin checks for isolated execution, content-addressed runtime dependency
and static production transport profiles, immutable runtime binding, one local
archive-scope process lock, an append-only one-claim-per-session execution parent,
and a controlled receipt sampled only after binding and claim exact reload. A
process-local capability is issued only after pre-start readiness while the lock
remains held. The companion archive and bootstrap recognize only exact known
schema unions; Phase99/100/103 canonical domain and row semantics remain unchanged.
No v2 attempt or terminal table, passive wrapper, provider request, live campaign,
or concrete Delta was added. Static `trust_env` is bound, but
`STATIC_RUNTIME_TRANSPORT_PROFILE != REQUEST_EFFECTIVE_NETWORK_ENVIRONMENT`;
`REQUEST_EFFECTIVE_NETWORK_ENVIRONMENT_BINDING_REQUIRED_FOR_OFFICIAL_ATTEMPTS`
remains a Phase105 prerequisite. The earlier PREPARE discussion of a direct/no-proxy
mode is not implemented as request-effective authority in Phase104; the approved
review clarification supersedes that reading. The controlled runner does not publish attempts
and a normal pytest process cannot issue its isolated-source capability.

New focused tests: 16 passed. Phase99–103 regressions: 70 passed. Full repository
suite: 4,633 passed, 2 skipped, 2,846 subtests passed. Tests use temporary local
Git and SQLite fixtures only; no production DB write or provider HTTP occurred.
`ONE_MEASUREMENT_SESSION = AT_MOST_ONE_OFFICIAL_CAMPAIGN_EXECUTION` and
`CRASHED_OFFICIAL_SESSION_REQUIRES_NEW_PREDECLARED_SESSION` remain frozen.
Phase104 is not formally complete before independent remote review.

Next: `CHATGPT_REVIEW_PHASE104_IMPLEMENTATION`.

### Historical Phase104 PREPARE contract

Allowed Files in PREPARE: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`.
Forbidden Files: production code, tests, database/archive files, and logs. Required
Tests: none (design-only audit); require `git diff --check` and `git status --short`.
Stop Condition: a runtime assertion would replace independent provenance, a V1/V2
canonical contract would need reinterpretation, or work outside these two docs is
required. Do not stage, commit, push, call the NAR provider, or run a campaign.

### Phase103 reconciliation and primary findings

`PHASE103_IMPLEMENTATION_REMOTE_VERIFICATION_PASS`;
`POST_V0_8_DAILY_REPLAY_103 = FORMALLY_COMPLETE`;
`NAR_V2_MEASUREMENT_CONFIG_SESSION_ACTIVATION_FOUNDATION = FORMALLY_INTEGRATED`;
`V2_PERSISTENCE_BOUNDARY_CONFIG_SESSION_ACTIVATION_ONLY = VERIFIED`; and
`V2_ATTEMPT_TERMINAL_PERSISTENCE_DEFERRED_PENDING_EXECUTION_PARENT = CONFIRMED`.
Phase102 remains `PHASE102_CAMPAIGN_RUNNER_AND_RUNTIME_AUTHORITY_REVIEW_PASS`, with
`CRASH_NO_OFFICIAL_RESUME_CONTRACT = FROZEN`. The v2 ancestry prerequisite for
designing runtime binding is now met; this does **not** resolve runtime provenance
or authorize implementation/campaign execution. The historical Phase102 marker
`PHASE102_RUNTIME_BINDING_IMPLEMENTATION_DEFERRED_PENDING_V2_AUTHORITY_CONTRACT`
is resolved as an architectural dependency only, pending this Phase104 review.

Primary finding: Phase104 needs two independent controls. A process-held lock
excludes concurrent compliant runners; an immutable one-shot claim consumes the
session even after a crash. `PROCESS_LOCK != PERSISTENT_SESSION_CONSUMPTION_AUTHORITY`
and `PERSISTED_EXECUTION_CLAIM != CURRENT_PROCESS_EXECUTION_CAPABILITY` remain
frozen. Neither a clean worktree nor a declared Git SHA proves executed bytes.
The official ancestry is exact v2 configuration → session → activation declaration
→ activation verification → runtime binding → campaign execution claim → future
v2 attempt → terminal. `V2_ATTEMPT_REQUIRES_CAMPAIGN_EXECUTION_ANCESTRY`,
`RUNTIME_BINDING_REQUIRES_EXACT_V2_ACTIVATION_ANCESTRY`, and
`CAMPAIGN_EXECUTION_REQUIRES_EXACT_RUNTIME_BINDING` admit no bypass.

### Sealed source bundle and import isolation

Freeze `CONTROLLED_SEALED_GIT_SOURCE_BUNDLE_V1` with public namespace
`nar-runtime-source-bundle-v1:<sha256>`. Its canonical manifest binds repository
`garimapo/KeibaOS`, lowercase 40-hex commit SHA, exact commit-tree SHA, bundle
semantic/version, sorted normalized relative member paths, Git mode/type, byte
length, and SHA-256 of each included Git-blob byte sequence. The bundle identity
hashes that exact canonical manifest. File mtimes, a mutable worktree copy, and
`git status` are not source authority. Reject included symlinks/submodules/path
escape rather than following them. Verify the local Git commit and tree objects,
materialize from `git archive <exact commit>` or equivalent object reads with no
network, hash every extracted member against the independently derived manifest,
and publish the completed bundle atomically into an isolated content-addressed
directory; partial extraction has no authority. The directory must not alias the
developer worktree, archive DB, or lock path. Recheck member integrity and origins
at launch; read-only ACL/restricted write access and a final integrity check protect
the trusted local run without claiming adversarial or power-loss immutability.

The deterministic initial include rule is all Git-tracked `scripts/**/*.py`,
`main.py`, `config/**`, `prompts/**`, and `requirements.txt` at the exact commit.
This deliberately covers the current scripts import graph and tracked runtime
configuration/resources; no database, logs, tests, docs, generated artifacts, or
developer-only files enter the executable bundle. An import/resource needed outside
this reviewed set is a fail-closed scope finding, not an implicit worktree fallback.
The runtime data/archive and external evidence remain separately controlled inputs;
bundling `config/settings.json` does not adopt its legacy timing value as Phase97 Δ.

Use a **new isolated child process** for official execution: `python -I -B` or an
equivalent reviewed isolation mode, a minimal launcher that inserts only the sealed
root as the KeibaOS import root, a controlled current directory outside the mutable
worktree, and sanitized `PYTHONPATH`/user-site behavior. An in-process runner may
already have imported mutable modules and is insufficient. Because `scripts` is a
PEP 420 namespace package (`scripts/__init__.py` is absent), require
`scripts.__path__ == (sealed_root/scripts,)` exactly; verify each critical
operational-timing/activation/archive, live NAR, snapshot, prediction, and bet-plan
module's resolved origin against its manifest member. Reject any second namespace
portion, preloaded conflicting module, origin alias, or shadowing. The prior
Phase79 import-isolation preflight supplies a local pattern, not automatic Phase104
authority. `DEVELOPER_WORKTREE_STATE != SEALED_RUNTIME_SOURCE_AUTHORITY` and
`GIT_HEAD_MATCH != RUNTIME_SOURCE_TREE_PROVENANCE` remain explicit. A clean tracked/
staged/untracked worktree and no merge/rebase/cherry-pick are optional operator
preflight; ignored or generated executable files reachable from approved import
roots are rejected. Later developer edits cannot change the isolated bundle bytes.

### Dependency and effective transport provenance

Add a content-addressed, immutable dependency profile with exact Python
implementation and major/minor/micro, `requests` and `urllib3` versions, SQLite
runtime version, OS family/release/build, and machine architecture. These are
compatibility-critical for timing populations; CPU/storage capacity and contention
are reported as reviewed load context rather than fabricated guarantees. Do not
hash unrelated installed packages or claim dependency-wheel attestation. Compare
the profile in the isolated child, not from the launcher worktree. Exact profile
identity must accompany future aggregation compatibility in addition to v2
configuration identity.

The four current transport constructors are confirmed locally: bootstrap, daily
target, and official response use connect/read `10s/10s`; market odds uses
`10s/20s`; all create `HTTPAdapter(max_retries=0)`, use `stream=True`,
`allow_redirects=False`, `verify=True`, and request `Accept-Encoding: identity`.
Market odds sets `Session.trust_env=False`; the other three leave Requests' default
environment behavior enabled. The existing v2 configuration captures exact timeout
microseconds and declared `NO_RETRY/0/0`, **not** redirect/TLS/stream/proxy details.
Do not change its canonical payload retrospectively. A closed Phase104 supplemental
effective-transport profile must be derived from the actual standard transport
instances/descriptors, record adapter mount/effective Retry fields, request flags,
headers relevant to encoding, `trust_env`, and proxy/CA/auth environment mode, then
be bound by the runtime identity. A caller-supplied transport protocol/stub is
diagnostic unless the controlled composition proves its exact reviewed descriptor.
The declared timeout/retry material must match this derived profile exactly.

For an initial official **direct** profile, retain current transport semantics but
require a sanitized child environment and fail closed if an effective proxy,
environment CA override, or environment auth changes any reviewed request. Since
three sessions retain `trust_env=True` and effective proxy resolution may depend on
the target URL (including Windows system proxy settings), Phase104 readiness alone
cannot certify every future request. Phase105 must verify effective request settings
per exact URL before official attempt execution; otherwise the attempt/campaign is
nonqualifying (`EFFECTIVE_REQUEST_ENVIRONMENT_BINDING_REQUIRED`). No silent proxy
substitution and no transport behavior change in Phase104. `max_retries=0` describes
the configured Requests adapter only; it does not prove absence of TCP/kernel
retransmission, DNS, or intermediary retries.

### Serial runner, canonical archive lock, and runtime binding

The runner is a controlled **execution envelope**, not a race scheduler. It owns one
official session, one active target workflow and HTTP operation, no worker pool,
async fan-out, or parallel venue work, and preserves sequential RaceList calls.
`DECLARED_CONCURRENCY_REGIME != PROVEN_CAMPAIGN_CONCURRENCY_AUTHORITY` and local
call-graph seriality is not process-wide exclusion. Only a lock-holding runner may
issue the in-process serial-concurrency capability consumed by runtime binding.
It proves compliant processes sharing the same local archive scope, not unrelated
processes or distributed uniqueness.

On Windows use a held exclusive OS file lock with a separate cross-platform test
adapter. Derive the stable lock key from the configured absolute archive DB path:
resolve its **existing parent directory** without reparse aliases, bind that
parent's volume/file identity where available plus the case-normalized DB basename,
and keep this key unchanged whether the DB file exists yet or not. Verify a present
DB is a regular non-reparse file under that parent and reject a multi-link/hardlink
DB, but do not add its newly created file ID to the lock key. A deterministic lock
file in the canonical control directory represents the scope; relative paths,
aliases, and unresolved
substitutions fail closed. A copied DB on another machine is outside
this trusted single-machine claim. Use the **same archive-scope lock** from before
schema bootstrap through claim publication and the complete official execution;
bootstrap-only tools must acquire that lock too. Thus there is no bootstrap-to-run
unlock gap or simultaneous migration. This is one physical lock with separate
logical bootstrap and campaign phases, not a time lease.

`NAROperationalTimingRuntimeBinding` is frozen/slotted/content-addressed as
`nar-operational-timing-runtime-binding-v1:<sha256>`. It binds exact v2 configuration,
session, declaration, and verification identities; sealed bundle/commit/tree
identity; dependency profile identity; derived transport/retry/environment profile
identity; enabled v2 stage set and instrumentation version; and the runner-issued
serial concurrency semantic/lock-scope identity. It is constructed only after
exact archive reload and qualifying v2 activation, source/import verification,
child-runtime profile derivation, and exact declared-vs-effective config comparison.
No `matches=True`, outcome, payout, ROI, prediction-policy, or caller-selected
authority. `RUNTIME_BINDING != CAMPAIGN_EXECUTION_AUTHORITY`: binding does not
consume the session or authorize a prediction policy. Distinguish closed
nonqualifying reasons for missing/contradictory ancestry, source/commit/tree,
dependency, transport, retry/environment, stage/version, and concurrency mismatch.
Missing environment/request proof remains nonofficial, not assumed equal.

### One-shot claim, readiness receipt, and crash semantics

The immutable `NAROperationalTimingCampaignExecutionClaim` uses exact namespace
`nar-operational-timing-campaign-execution-v1:<sha256>` and binds v2 configuration,
session, activation declaration/verification, runtime binding, bundle identity,
canonical lock-scope identity, runner/instrumentation semantic, and no result or
favorable timing material. The archive enforces `UNIQUE(v2_session_identity)` and
restrictive exact ancestry. **Any** existing claim permanently consumes that
session, whether execution completed, crashed, or the first process failed before
an attempt. Exact duplicate publication may be storage-idempotent but must never
issue a second process capability. Claim publication/commit followed by a crash
still consumes the session: `CRASHED_OFFICIAL_SESSION_REQUIRES_NEW_PREDECLARED_SESSION`.
No mutable execution status or claim deletion; an optional future append-only
completion receipt is deferred because Phase105 reconciliation has not frozen it.

Select one controlled `NAROperationalTimingCampaignReadinessVerificationReceipt`
rather than a self-timestamped binding. Persist and exact-reload runtime binding,
then claim; **only after both exact reloads** sample the runner-owned aware-UTC clock.
The receipt binds exact binding/claim/session and that service-owned
`readiness_verified_at`; persist and exact-reload it before any official attempt.
It proves those parents were already committed and exact-reload verified by the
timestamp under the reviewed SQLite semantics, not that the receipt itself was
published then or that crash durability beyond SQLite settings was proven.
Require `readiness_verified_at <= measurement_start_at` (equality allowed) and
require the controlled receipt-reload/launch check to finish by session start.
If either check is late, receipt persistence/reload fails, or a parent contradicts,
refuse official execution **without moving the fixed session window**. A claim
already committed stays consumed. Diagnostic work must use a separately classified
path and cannot rehabilitate the official session.

The exact controlled order is: resolve canonical scope and acquire its lock;
bootstrap exact archive state; exact-reload v2 configuration/session and qualifying
activation; verify sealed bundle and isolated child imports; derive dependency and
effective transport profile; prove serial runner authority; construct/save/reload
binding; assert no prior claim; construct/save/reload claim; sample readiness clock;
save/reload readiness receipt; require pre-start qualification; issue a **current-
process-only** capability while still holding the lock; only then may Phase105
publish official attempts. Loading an archived claim or receipt in a later process
can never recreate that capability. On crash the OS lock may release but the claim
remains; unresolved attempts remain unresolved, with no time reconstruction.

### Same-database companion, bootstrap, and Phase105 parent contract

Phase104 adds a separate version-1 runtime/execution companion registry to the
existing archive, leaving Phase99/100/103 registries, DDL, rows, and canonical
meanings unchanged. Its typed append-only families are sealed bundle manifests,
dependency profiles, effective transport profiles, runtime bindings, execution
claims, and readiness verification receipts. Restrictive FKs bind binding to exact
v2 configuration/session/activation verification (with contradiction checks through
declaration), claim to exact binding/session, and receipt to exact claim/binding.
Use `ON UPDATE/DELETE RESTRICT`, no update/delete triggers, exact-duplicate
idempotency for values, `UNIQUE(session_identity)` for claims, exact reload, and an
exact union schema gate. No backfill or synthetic authority. A persisted bundle
manifest is still not proof the child imported it; controlled origin checks supply
that operational proof.

Top-level bootstrap accepts only exact states: empty → Phase99 base → Phase100
activation → Phase103 v2 → Phase104 companion; base-only → remaining companions;
activation-only → v2 then Phase104; exact v2 union → Phase104; exact Phase104 union
→ no-op. Partial/unknown/registry-conflicting states fail closed. It takes the
archive-scope lock before examining even an empty DB and never blindly invokes a
historical strict migration on an extended schema. Historical strict validators
retain their original meaning; normal repository gates may accept only enumerated
exact unions. Bootstrap writes are schema-only and separate from campaign claim
issuance.

**Phase104 creates execution parents only.** Phase105 owns v2 attempt/terminal
pure domains and tables when their exact payload, sequence/correlation, disposition,
and archive contract are independently reviewed. Phase105 creates attempt FK to
Phase104 execution claim and terminal FK to attempt **at table creation time**;
no speculative text-only parent or immutable-table rebuild. Its attempted payload
must bind exact v2 configuration/session, execution identity, closed stage,
correlation, sequence, `attempt_admitted_at`, and load context; terminal binds
attempt, UTC finish, integer monotonic microseconds, closed disposition/failure,
and optional artifact SHA. Runtime binding need not be redundantly copied because
attempt → claim → binding is restrictive ancestry. No Phase104 attempt publication.

### Future implementation paths and tests

Likely CREATE: `scripts/simulation/nar_operational_timing_runtime_source_provenance.py`,
`nar_operational_timing_runtime_dependency_profile.py`,
`nar_operational_timing_runtime_profile.py`,
`nar_operational_timing_runtime_binding.py`,
`nar_operational_timing_campaign_execution.py`,
`nar_operational_timing_campaign_runner.py`,
`nar_operational_timing_archive_bootstrap.py`,
`nar_operational_timing_runtime_execution_archive_migration.py`, and
`sqlite_nar_operational_timing_runtime_execution_archive.py` under the same
`scripts/simulation/` directory. Exact likely CREATE tests are
`tests/test_nar_operational_timing_runtime_source_provenance.py`,
`tests/test_nar_operational_timing_runtime_dependency_profile.py`,
`tests/test_nar_operational_timing_runtime_profile.py`,
`tests/test_nar_operational_timing_runtime_binding.py`,
`tests/test_nar_operational_timing_campaign_execution.py`,
`tests/test_nar_operational_timing_campaign_runner.py`,
`tests/test_nar_operational_timing_archive_bootstrap.py`,
`tests/test_nar_operational_timing_runtime_execution_archive_migration.py`, and
`tests/test_sqlite_nar_operational_timing_runtime_execution_archive.py`.
Narrow read-only descriptor additions may be needed in
`nar_historical_daily_target_bootstrap_live_capture.py`,
`nar_historical_daily_target_live_capture.py`,
`nar_official_response_live_capture.py`, and
`nar_market_odds_raw_acquisition.py` under `scripts/simulation/`; exact
compatible-schema gates in the Phase99/100/103 migration/repository modules may
also need extension. Each must be explicitly named in later Phase104 Allowed Files.
No live capture/wrapper implementation is authorized by this draft.

Required future tests: exact Git commit/tree/object extraction and deterministic
manifest; worktree mutation independence; corrupt member/manifest, symlink/path
escape and import-origin/PYTHONPATH/PEP420 shadow rejection; exact Python/Requests/
urllib3/SQLite/OS profile changes yield distinct identities; actual transport
timeouts, Retry/redirect/TLS/stream/encoding/`trust_env` derivation and proxy/
CA/auth mismatch fail closed; caller override impossible; exact activated v2
ancestry and config/profile/concurrency mismatch; binding/claim/receipt canonical
SHA and archive roundtrip; clock after both parent reloads and late readiness
nonqualification; two processes excluded; one claim per session; normal/crash
release cannot re-enter; old claim cannot issue a new-process capability; new
predeclared session may enter; every exact bootstrap state upgrades/no-ops, and
malformed/partial/unknown schema fails while historical strict validators remain
strict; no outcome/ROI/HTTP/attempt/terminal dependency.

Remaining blockers: `RUNTIME_SOFTWARE_COMMIT_PROVENANCE_REQUIRED`,
`RUNTIME_MEASUREMENT_CONFIGURATION_BINDING_REQUIRED`,
`EFFECTIVE_REQUEST_ENVIRONMENT_BINDING_REQUIRED` for future per-request proof,
Phase105 passive wrappers/attempt ancestry, separately authorized prospective
campaign, `CONCRETE_FIXED_OFFSET_REQUIRES_OPERATIONAL_TIMING_AUDIT`, and
Phase94/95/41 source-semantic authority. `POLICY_IDENTITY != PRE_OUTCOME_POLICY_AUTHORITY`.
Phase104 is architectural review only, not authority issuance or HTTP approval.

Recommended disposition: `DRAFT_FOR_REVIEW`.

Next: `CHATGPT_REVIEW_PHASE104_RUNTIME_AND_EXECUTION_AUTHORITY`.

---

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
