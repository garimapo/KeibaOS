# Current Phase

## POST_V0_8_DAILY_REPLAY_96

Title: NAR Historical Replay Prediction-Cutoff Coherence Implementation

Formal Status: READY_FOR_REVIEW

Design Review: PHASE96_PREDICTION_CUTOFF_DESIGN_REVIEW_PASS

Base Commit and Branch: `3a8bb363838110d5b918829e19e97fef1718fdaf` / `feature/post-v0.8-daily-replay`

State: IMPLEMENTED_FOR_REVIEW

Outcome: READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW

Audit: PREDICTION_CUTOFF_COHERENCE_AUDIT_COMPLETE

Authorization: NONE_REQUIRED_NO_NETWORK_IMPLEMENTATION

Implementation: NAR_PREDICTION_CUTOFF_PLAN_AND_V017_PROVENANCE_IMPLEMENTED

Implementation evidence: the separate immutable cutoff plan binds the exact target set, closed policy identity, ordered per-target C values, canonical JSON, and SHA-256. Phase93 requires exact-C temporal coverage; the SQLite resolver selects prediction snapshots at C while settlement remains independent. The orchestration result retains the plan and its audit SHA binds the plan SHA. v017 adds an immutable one-to-one companion without altering v016 objects or legacy rows; new parent/companion publication is atomic. Strict aggregation rejects selected legacy rows and compares cutoff policy identities, not daily plan SHAs.

Validation: focused plan 4 passed; Phase93 8 passed/5 subtests; resolver 27 passed/38 subtests; orchestrator 23 passed/11 subtests; persistence 12 passed/12 subtests; result repository 26 passed/19 subtests; aggregation 22 passed; historical migration 11 passed; simulation migrations 22 passed/10 subtests. Final full suite: 4,528 passed, 2 skipped, 2,846 subtests passed. Provider HTTP / Phase44 / GET: 0 / 0 / 0. No production database writes, live replay, source acquisition, Phase97 timing policy, or authority issuer. Three additional regression-test paths only update exact migration-registry expectations for v017.

Branch: `feature/post-v0.8-daily-replay`

Starting HEAD/tree: `3a8bb363838110d5b918829e19e97fef1718fdaf` / `19986e75e450150032e631fe4dac111d3e59e581`

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

Primary classification: `PREDICTION_CUTOFF_MODEL_REQUIRES_EXPLICIT_CUTOFF`. Phase93 compatibility remains `PHASE93_CUTOFF_CONTRACT_REQUIRES_HARDENING`.

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

### Allowed Files

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

### Forbidden Files

Every other path, including provider target discovery, historical target identity, snapshot schemas, settlement domains, fixtures, capture archives, `database/**`, and `logs/**`.

### Required Tests and Checks

Run the new cutoff-plan test and focused Phase93, resolver, orchestrator, persistence, SQLite repository, aggregation, v017 migration and simulation migration tests; then run the full repository pytest suite. All must pass. Require `git diff --check`, exact scope audit, and `git status --short` before the approved one-commit normal push.

### Stop Condition

Stop if the remote baseline advances, an unapproved path or provider-denominator change is required, a fail-closed invariant cannot be represented, or a required test fails outside the approved scope. No Phase97 policy, authority issuer, or live acquisition is included.

Next: `CHATGPT_REVIEW_PHASE96_IMPLEMENTATION`

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
