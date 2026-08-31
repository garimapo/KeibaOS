# Current Phase

Status: `DRAFT_FOR_REVIEW`

## Identity and authorization

- Phase: `4C-2d3b1i6d1d5f1c4j0`
- Name: `Ver0.8 Completion and Release-Readiness Audit PREPARE`
- Formal base: `c6c2f17934c2274d5bc720c60e40e52bd0c3ee58`
- Formal branch: `feature/ver0.8-simulator`
- Review branch: `review/4c-2d3b1i6d1d5f1c4j0-ver0.8-completion-audit-prepare`
- Previous formal phase: `4C-2d3b1i6d1d5f1c4i3b` (`FORMALLY_COMPLETE`)
- Allowed files: `docs/CURRENT_PHASE.md`, `docs/LATEST_CODEX_REPORT.md`
- Implementation authorization: `NO`
- Release authorization: `NO`
- Formal integration authorization: `NO`

This PREPARE audits the exact formal tree. It does not implement a gap, change release
metadata, update public documentation, tag a release, merge to `master`, or begin
Ver0.9.

## Controlling Ver0.8 completion goal

Ver0.8 is a reproducible and auditable historical replay platform. From an already
audited pre-race `HistoricalInputSnapshot`, it executes the existing prediction/value/
recommendation stack, deterministic stake allocation, immutable plan persistence,
exact archived official result and payout acquisition, settlement, and aggregation.
It must preserve causal cutoffs, real official payout arithmetic, fail-closed behavior,
SQLite auditability, JRA/NAR provider binding, valid `NO_BET`, clean-clone operation,
and no-network replay.

Automatic live construction of every historical prediction snapshot is not the replay
runtime boundary. Live acquisition and snapshot assembly are separate ingestion work;
the replay contract starts from an exact persisted, audited snapshot identity.

## Completion matrix

| Goal | Formal implementation / evidence | Status | Release-blocking? | Exact next action |
| --- | --- | --- | --- | --- |
| Future-information isolation | Evidence validates `available_at <= observed_at`; snapshot assembly/domain enforce `observed_at <= captured_at <= information_cutoff <= scheduled_start_at`; replay exact-loads the requested natural identity and completes C4g1 before opening settlement archives. | PASS (`D`) | No | Document the causal boundary for operators. |
| Historical input audit persistence | `HistoricalInputSnapshot` carries source identity, evidence roles/times, external entry crosswalk, cutoff, canonical digest; the v010-v014 SQLite path persists and reconstructs it, recomputes the digest, and rejects corruption without fallback. | PASS (`D`) | No | None. |
| PredictionPipeline execution | C4g0 builds the real historical `PredictionPipeline` and executes Ability, Pace, Jockey, Track, Predictor, Value, BetGenerator, and RuleBasedBetStrategy once per race. | PASS (`D`) | No | None. |
| Strategy identity/config reproducibility | Canonical config and allocation-policy payloads produce SHA-256 identities; run, strategy, config hash, and cutoff bind each persisted plan. | PASS (`D`) | No | Document comparison workflow and claim limits. |
| Stake allocation | Explicit per-race budget, hashed fixed-stake policy, positive 100-yen units, deterministic purchase order, unused-budget properties, empty plans, and insufficient-budget fail-closed behavior are implemented. | PASS (`D`) | No | Additional policies remain post-Ver0.8. |
| Bet-plan persistence | `SimulationBetPlanSnapshot` is immutable; normalized SQLite rows preserve purchase/selection order, budget and policy identity; equal saves are idempotent, conflicts/corruption fail, and settlement reloads rather than regenerates bets. | PASS (`D`) | No | None. |
| JRA official result settlement | Exact capture ID, page/race identity, visible identity, race-local crosswalk, complete normal result, and same-capture finality are validated and persisted. Exact fixture coverage exists. | PASS (`D`) | No | Document the normal-final support envelope. |
| JRA official payout settlement | Exact archived source supports normal complete winning payouts for `単勝`, `馬連`, `ワイド`, and `3連複`, with canonical selections and per-100-yen values. | PASS (`D`) | No | Do not claim exceptional-state support. |
| NAR official result settlement | Exact RaceMarkTable identity, visible identity, crosswalk, complete result and finality are validated and persisted. Exact fixture coverage exists. | PASS (`D`) | No | Document the normal-final support envelope. |
| NAR official payout settlement | Exact normal winning groups for all four formal types are exhaustively parsed; NAR's official 100-yen denomination maps directly to `payout_per_100`. | PASS (`D`) | No | Do not claim refund/void/dead-heat support. |
| Mixed-provider replay | C4i3b runs JRA and NAR in one request through CLI -> C4g1 -> C4h4a -> C4h4b, with canonical race ordering and exact persisted facts. | PASS (`D`) | No | None. |
| NO_BET behavior | Persisted empty plans remain distinct from missing plans, yield `NO_BET`, do not enter investment/rate denominators, and remain valid final races. | PASS (`D`) | No | None. |
| Non-settled fail-closed behavior | Missing/incomplete/void/error/unsupported states carry zero settled money; final historical settlement refuses any non-final summary. No partial state is presented as final ROI. | PASS (`D`) | No | None. |
| Real payout arithmetic | Settlement matches canonical selections against complete official publications and computes exact integer yen as `stake * payout_per_100 / 100`; estimates, odds, scores and `combination_score` never determine payout. | PASS (`D`) | No | Keep predictive and realized-ROI claims separate. |
| Maximum drawdown | Only `SETTLED` results are ordered by `(settled_at, race_id)` and folded from an initial zero peak; non-settled and `NO_BET` are excluded. | PASS (`D`) | No | None. |
| By-bet-type metrics | Immutable, deterministic mappings aggregate counts, settled money, profit, ROI and hit rate and cross-check their totals against the overall summary. | PASS (`D`) | No | None. |
| SQLite auditability | Request + exact snapshot rows + plan rows + result/payout sources reconstruct race, dataset/evidence, cutoffs, strategy/policy hashes, budget, ordered bets, and summary. The summary itself is returned/serialized, not stored as a run-result row. | PASS (`D`) | No | Run-result persistence (`C4g2c`) remains post-Ver0.8. |
| Deterministic CLI | `python -m scripts.cli.run_historical_replay <request_path>` is a thin one-call boundary with exact schema-v1 compact sorted JSON, fixed Decimal serialization, error JSON and exit codes. | PASS (`D`) | No | Add operator documentation and a copyable manifest example. |
| Clean-clone portability | Repository-owned exact-byte fixtures, relative request paths, portable SQLite read-only URIs, Linux CI, and clean-checkout evidence tests pass. | PASS (`D`) | No | None. |
| No-network replay | Settlement uses exact read-only local archives; the mixed-provider acceptance installs socket sentinels and succeeds without network access. | PASS (`D`) | No | Live acquisition remains outside replay. |
| Current-clock isolation | Causal replay values come from the request, snapshot and captures. After prerequisite migrations, the mixed-provider acceptance installs a migration-clock sentinel and replay succeeds. Migration audit timestamps are setup metadata, not prediction or settlement inputs. | PASS (`D`) | No | Document the pre-migrated database prerequisite. |
| Strategy/config comparison | One strategy is executed per request. Stable strategy/config identities and deterministic repeated requests support controlled comparison; one-command multi-strategy orchestration and a combined report are not required for the baseline. | PASS (`D`); enhanced orchestration is `C` | No | Document repeated-run comparison; defer combined orchestration. |
| Documentation accuracy | README, ROADMAP, CHANGELOG, ARCHITECTURE, and the obsolete Horse Engine `VER0.8_DESIGN.md` do not describe the completed simulator/replay release accurately. | GAP (`B`) | Yes, documentation gate only | Correct public/release docs in C4j1. |
| Version/release metadata | Latest tag is `v0.7.0`; no `v0.8.0` tag or GitHub release exists; no package/version constant is present; formal is 158 commits ahead of `master`. | GAP (`B`) | Yes, release-state gate only | Freeze release notes, integration/version/tag state in C4j1; do not tag or merge without later authorization. |
| Remote CI | Formal commit `c6c2f1...` passed `Tests / pytest (3.12)`, run `33389634074`, job `99480037939`; the local exact-base suite also passes. | PASS (`D`) | No | Require the C4j0 docs-only review branch CI to pass. |

Legend: `A = VER0_8_RELEASE_BLOCKER`, `B = VER0_8_RELEASE_DOCUMENTATION_ONLY`,
`C = POST_VER0_8_EXTENSION`, `D = NOT_A_REAL_GAP / ALREADY_SATISFIED`.

## Exact support and claim boundaries

- Candidate generation and settlement domains recognize `単勝`, `馬連`, `ワイド`, and
  `3連複`.
- Exact archived JRA/NAR normal-final evidence can normalize and settle all four.
- Only `単勝` has prediction-time market-odds EV semantics. Combination
  `combination_score` is a deterministic ranking heuristic, not real odds or EV.
- The mixed-provider release acceptance deliberately buys only `単勝`.
- The release may claim deterministic replay arithmetic and reproducible official
  settlement. It may not claim profitability, 120% ROI, calibrated probability,
  statistically demonstrated edge, or long-term performance.
- Archived replay is required and complete. Live acquisition is not a replay
  requirement and is not needed to reproduce a request.

## Gap classification

### A — `VER0_8_RELEASE_BLOCKER`

`NONE`. No production, test, schema, migration, fixture, workflow, or architecture
change is required before release preparation.

### B — `VER0_8_RELEASE_DOCUMENTATION_ONLY`

1. README still presents Ver0.7, lacks the historical replay CLI/manifest workflow,
   and its capability exclusions no longer describe fixed-stake allocation accurately.
2. ROADMAP, CHANGELOG and `VER0.8_DESIGN.md` still define Ver0.8 as Horse Engine and
   results as Ver0.9; ARCHITECTURE omits the formal replay layers.
3. Operator guidance lacks one copyable strict schema-v1 replay-manifest example and
   the prerequisite database/archive preparation and claim limitations.
4. Ver0.8 release notes/version state are absent: only tag `v0.7.0` exists, no
   package-version source exists, no GitHub release exists, and `master` has not
   integrated the formal simulator branch.

### C — `POST_VER0_8_EXTENSION`

- automatic live historical prediction-input collection/request generation;
- more allocation policies, Kelly/proportional/portfolio allocation, and live bankroll;
- true combination-ticket prediction-time odds/EV;
- probability calibration and statistical edge validation;
- one-command multi-strategy comparison and combined capital-curve reporting;
- persistent run-result/manifest audit (`C4g2c`), race-detail/CSV report artifacts;
- result revision/time-travel and exceptional settlement semantics beyond the frozen
  normal-final winning envelope;
- automated daily execution, live betting, X/note publishing;
- optional external AI/LLM signals, which must remain disabled in the deterministic
  baseline until separately validated.

### D — `NOT_A_REAL_GAP / ALREADY_SATISFIED`

Every PASS row in the completion matrix. In particular, losing strategy output is not
a platform defect; live HTTP is not needed for archived replay; and separate stable,
identified runs satisfy the baseline strategy/config comparison goal.

## Dependency and fallback audit

The normal replay path has no HTTP/network client, random source, environment-variable
input, implicit `database/keiba.db`, live capture discovery, current/live refetch,
name-based horse matching, race-only capture lookup, cross-provider fallback, or
settlement-to-prediction feedback. Request paths select the database and archives;
relative paths anchor to the manifest. Exact snapshot identities and capture IDs are
mandatory. Archives open with SQLite `mode=ro` plus verified `query_only`.

Latest historical snapshot and latest payout repository APIs exist for other bounded
contracts, but C4i replay uses exact snapshot identity and exact capture ID. Settlement
selects the latest payout publication at or before the explicit per-race cutoff; an
incomplete latest publication remains non-final and is not replaced by an older
complete one. Malformed selected data raises integrity/validation errors and is not
repaired or skipped. C4h4 acquisition stops on failure; C4h4b refuses non-final batches.

## Test-quality disposition

`PASS`. Dedicated boundary tests cover causal timestamps and provenance completeness;
snapshot digest/corruption/no-fallback; allocation units, identity, unused/insufficient
budget and empty plans; plan idempotency/conflict/order corruption; persisted-plan-only
settlement; exact JRA/NAR capture identity, parser structure, crosswalk and finality;
missing/unsupported/non-final states; official per-100 arithmetic; denominator,
drawdown and by-type metrics; SQLite orchestration barriers; read-only archives;
deterministic CLI/error output; exact fixture bytes; mixed-provider no-network and
clock-isolated replay. The full exact-base suite reports `3125 passed, 2506 subtests
passed`.

No untested high-risk Ver0.8 release boundary was found. Provider-wide historical data
coverage, predictive calibration, exceptional official states and multi-strategy report
orchestration are explicitly outside the frozen baseline rather than silently asserted
by the tests.

## GO / NO-GO

```text
VER0_8_GO_NO_GO:
VER0_8_RELEASE_READY_AFTER_DOCS

RELEASE_BLOCKERS:
NONE

IMPLEMENTATION_AUTHORIZATION:
NO

RELEASE_AUTHORIZATION:
NO
```

The platform completion gate passes. Release itself remains blocked only by the
documentation and release-state work in category B.

## Exactly one recommended next phase

```text
RECOMMENDED_NEXT_PHASE:
4C-2d3b1i6d1d5f1c4j1 — Ver0.8 Release Documentation and Version-State Preparation
```

C4j1 must be restricted to public/release documentation, an operator-safe manifest
example, and explicit version/integration/tag/release-state preparation. It must not
add simulator behavior, schema, migrations, data acquisition, AI, or Ver0.9 work.
Actual merge, tag, and release publication still require separate explicit approval.

## Required verification and stop condition

- Full suite: `3125 passed, 2506 subtests passed`.
- `git diff --check`: required PASS after the docs edits.
- Static scope: exactly the two authorized docs relative to formal base.
- Review-branch GitHub Actions: `Tests / pytest (3.12)` must complete successfully.

After one docs-only commit and successful review-branch CI, stop for independent
completion review. Do not correct the audited documentation, implement an extension,
merge, tag, publish a release, or begin C4j1.
