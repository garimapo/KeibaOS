# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and authority

- Phase: `4C-2d3b1i6d1d5f1c4j1`
- Name: `Ver0.8 Release Documentation and Version-State Preparation`
- Base Commit: `c6c2f17934c2274d5bc720c60e40e52bd0c3ee58`
- Branch: `review/4c-2d3b1i6d1d5f1c4j1-ver0.8-release-docs-prepare`
- Formal branch: `feature/ver0.8-simulator`
- Approved C4j0 audit: `0cdee716c703c32867231719d65bd8f567b725a9`
- C4j0 disposition: `VER0_8_RELEASE_READY_AFTER_DOCS`

The C4j1 architecture is approved with the exact clarifications in this document.
This approval activity may change only this file and `docs/LATEST_CODEX_REPORT.md`.
Implementation must wait for a separate `EXECUTE_APPROVED_PHASE` instruction;
public/release documents, production, tests, fixtures, schemas, migrations, workflows,
master, tags, and GitHub Releases remain unchanged in this activity.

```text
IMPLEMENTATION_AUTHORIZATION:
EXECUTED_REVIEW_PENDING

MASTER_INTEGRATION_AUTHORIZATION:
NO

TAG_AUTHORIZATION:
NO

GITHUB_RELEASE_AUTHORIZATION:
NO

VER0_9_AUTHORIZATION:
NO

C4J1_ARCHITECTURE:
APPROVED

C4J1_IMPLEMENTATION:
COMPLETE_PENDING_INDEPENDENT_REVIEW
```

## Release target and version source

```text
VERSION_TARGET:
0.8.0

TAG_TARGET:
v0.8.0

RELEASE_NAME:
KeibaOS v0.8.0

VERSION_SOURCE_DECISION:
NO_NEW_RUNTIME_VERSION_SOURCE_FOR_V0_8

TAG_TYPE:
ANNOTATED

TAG_NAME:
v0.8.0

TAG_MESSAGE:
KeibaOS Ver0.8.0

TAG_CREATION:
NOT_AUTHORIZED_IN_C4J1
```

Repository inspection found no authoritative Python/package version source. Migration
version constants, request schema versions, allocation-policy versions, and fixture
schema versions are not application-release versions. C4j1 must not introduce
`__version__`, `pyproject.toml`, `setup.py`, `setup.cfg`, `version`, `VERSION`, package
metadata, or another runtime version constant merely to label this release. Release
documentation, CHANGELOG, the final annotated Git tag, and GitHub Release metadata will
identify Ver0.8.

## Public documentation contract

### README plan

`README.md` must make Ver0.8 the current release-candidate capability and use this
concise operator-facing order:

1. KeibaOS Ver0.8 purpose: deterministic, auditable replay of persisted historical
   prediction inputs through real planning and archived official settlement.
2. Supported envelope: archived JRA/NAR, formal bet types `単勝`, `馬連`, `ワイド`,
   `3連複`, and normal-final winning payout evidence only.
3. Requirements and setup for Python 3.12, SQLite, and the two requirements files.
4. Existing one-race prediction CLI, explicitly separated from historical replay.
5. Historical replay CLI:
   `python -m scripts.cli.run_historical_replay <request_path>`.
6. Manifest purpose and a link to `docs/HISTORICAL_REPLAY.md` and the checked-in
   schema-v1 template.
7. Reproducibility and auditability: exact snapshot natural identity, target commit,
   strategy/config identity, fixed-stake plan identity, exact capture IDs, separate
   prediction and settlement cutoffs, read-only archives, and deterministic JSON.
8. Official result/payout settlement and `SimulationSummary` metrics, including real
   ROI and maximum-drawdown arithmetic.
9. Prediction-time payout/EV distinction and fail-closed behavior.
10. Test command and research/non-profit-guarantee statement.
11. Known limits and post-Ver0.8 extensions.

The leading persisted-simulation CLI description must no longer substitute for the
Ver0.8 replay overview. It may remain as a secondary legacy/application-boundary note.
The stale statement that stake allocation is unimplemented must be corrected: Ver0.8
has deterministic fixed stake per recommendation and explicit per-race budgets, while
Kelly/proportional/portfolio allocation and live bankroll management remain deferred.

### ROADMAP plan

`docs/ROADMAP.md` must retain the completed Ver0.5-Ver0.7 milestones concisely, add
Ver0.8 as the completed/release-candidate `Historical Replay / Simulation Platform`,
and list its audited replay, planning, archived settlement, metrics, and CLI outcomes.
The former `Ver0.8 Horse Engine -> Ver0.9 Result Engine -> Ver1.0 AI Prediction Engine`
sequence must be retained only as an explicitly superseded historical roadmap concept,
not as the current version mapping. Unapproved future work belongs under
`Post-Ver0.8`; C4j1 must not invent a detailed Ver0.9 contract.

### CHANGELOG plan

`docs/CHANGELOG.md` must add a top entry titled exactly `Ver0.8.0 (Unreleased)` with no
release date. It must summarize platform-visible changes rather than internal phase
commits:

- auditable `HistoricalInputSnapshot` and future-information cutoff enforcement;
- historical execution of the real `PredictionPipeline`;
- deterministic fixed-stake allocation and immutable persisted bet plans;
- exact archived JRA/NAR official result and payout settlement;
- the four formal normal-settlement bet types;
- real payout arithmetic, summary/ROI/hit-rate/drawdown metrics;
- strict schema-v1 historical replay request and CLI;
- clean-checkout, mixed-provider, no-network acceptance.

The same entry must list material limitations and non-claims. Published v0.5-v0.7
history remains intact. Obsolete future-version promises must not remain presented as
current commitments.

### ARCHITECTURE plan

`docs/ARCHITECTURE.md` must receive the smallest coherent update that replaces its
obsolete top-level flow with the implemented replay flow:

```text
HistoricalInputSnapshot
-> PredictionPipeline
-> BetStrategy
-> BetStakeAllocator
-> SimulationBetPlanSnapshot
-> immutable persisted plan
-> archived official JRA/NAR result and payout evidence
-> final settlement
-> SimulationSummary
-> historical replay CLI JSON
```

The document must show prediction `information_cutoff` and per-race settlement cutoff
as separate causal boundaries. It must explain that the replay CLI is a thin wrapper,
the SQLite application owns exact snapshot loading/planning/read-only archives, and
final settlement consumes persisted plans rather than regenerating bets. Legacy live
acquisition remains a separate concern. The architecture page must link to the
authoritative detailed simulator design rather than reproduce its chronology.

### VER0.8 design disposition

```text
VER0_8_DESIGN_DISPOSITION:
RETAIN_AS_HISTORICAL_WITH_PROMINENT_SUPERSEDED_NOTICE
```

Choose disposition A. Preserve the old Horse Engine proposal in
`docs/VER0.8_DESIGN.md` as historical project evidence, but add a prominent notice at
the top stating that it was superseded and that
`docs/VER0.8_SIMULATOR_DESIGN.md` is the authoritative Ver0.8 design. Rewriting the old
proposal as though it had always described the simulator would destroy useful design
chronology; replacing all content is unnecessary.

## Operator guide and manifest template

Create exactly one operator guide:

```text
OPERATOR_GUIDE:
docs/HISTORICAL_REPLAY.md
```

Its sections are exactly: Purpose; Prerequisites; Historical replay trust boundary;
Request-file location and relative-path anchoring; `database_path`;
`capture_archives`; `run_context`; `strategy`; `budgets_by_race_id`; races and
snapshot identity; prediction cutoff vs settlement cutoff; executing the CLI;
deterministic success JSON; deterministic expected-error JSON / exit codes; archived
no-network replay behavior; fail-closed conditions; reproducibility checklist;
supported capabilities and explicit non-claims.

The guide must not present internal fixture construction as operator behavior. It must
state that replay does not acquire live data or manufacture snapshots/captures, that
all represented providers need an archive, and that required payout catalog entries
are determined only after planning.

Create one machine-readable template:

```text
MANIFEST_EXAMPLE:
examples/historical_replay_request.v1.example.json

MANIFEST_EXAMPLE_POLICY:
STRICT_SCHEMA_VALID_SINGLE_PROVIDER_TEMPLATE_NON_EXECUTABLE_UNTIL_EXACT_EVIDENCE_REPLACED

STRICT_JSON:
YES

SCHEMA_VERSION:
1

SCHEMA_VALID:
YES

INTENTIONALLY_EXECUTABLE:
NO

OFFICIAL_EVIDENCE:
NO
```

The JSON uses every exact schema-v1 root/race/nested key, one JRA race, one matching
budget, `RuleBasedBetStrategy`, and fixed-stake policy version string `"1"`. Paths and
identity/capture values use conspicuous `REPLACE_WITH_EXACT_*` or `example-only-*`
strings, including `REPLACE_WITH_MAIN_DATABASE.sqlite3`,
`REPLACE_WITH_JRA_CAPTURE_ARCHIVE.sqlite3`, `REPLACE_WITH_TARGET_COMMIT_SHA`,
`REPLACE_WITH_EXTERNAL_RACE_ID`, `REPLACE_WITH_EXACT_RESULT_CAPTURE_ID`, and
`REPLACE_WITH_EXACT_PAYOUT_CAPTURE_ID`. It uses the exact `JRA / jra_official`
provider pair, `allowed_bet_types: ["単勝"]`, stake `100`, a positive internal race ID
with the same canonical budget key, and timezone-aware ISO-8601 timestamps. It must
contain no official-looking fake capture ID, no JSON comments, no `pipeline`, and no
`track_reference_date`. The guide must label it a structural template, not executable
official ROI evidence, and require replacement with exact persisted identities and
capture IDs before replay. README and the guide must state prominently that this is a
schema template, placeholder capture IDs are not official evidence identities, exact
audited replacement values are mandatory, and successful schema parsing does not prove
that referenced archives, snapshots, or captures exist or are trustworthy. During
implementation, load this file through the public strict request loader as a
verification command without requiring referenced paths to exist; no committed test
source is needed.

## Release notes contract

Create:

```text
RELEASE_NOTES:
docs/VER0.8_RELEASE_NOTES.md

RELEASE_TARGET:
v0.8.0

RELEASE_STATE:
RELEASE_CANDIDATE_PENDING_FINAL_INTEGRATION
```

The top must state `Release target: v0.8.0` and
`Status: RELEASE_CANDIDATE_PENDING_FINAL_INTEGRATION`. Sections are exactly: Summary;
What Changed Since v0.7.0; Reproducibility and Auditability; JRA and NAR Archived
Settlement Support; Supported Bet Types; Historical Replay CLI; Verification State;
Known Limitations; Explicit Non-Claims; Upgrade and Migration Notes; Release State.
No final release date is included. The verification section may say the release
candidate passed the full suite, GitHub Actions remote CI, and mixed-provider
no-network acceptance, but raw pytest counts remain phase evidence rather than a
long-term public contract. It must not claim that v0.8.0 is already merged to master,
tagged, or published as a GitHub Release.

## Shared claim boundary

README, operator guide, CHANGELOG, and release notes must use one consistent boundary.

Platform guarantees:

- deterministic replay for the same audited inputs, configuration, database, and
  archived evidence;
- future-information boundary validation;
- immutable strategy/allocation/plan identity and reproducible fixed-stake plans;
- exact archived official JRA/NAR settlement with real per-100-yen payout arithmetic;
- fail-closed missing, corrupt, contradictory, unsupported, or non-final evidence;
- deterministic summary serialization.

Not guaranteed:

- future profitability, 120% ROI, calibrated win probability, or demonstrated strategy
  edge;
- true market EV for combination tickets (`combination_score` is only a ranking
  heuristic; prediction-time odds EV is formal only for `単勝`);
- complete historical-data coverage or automatic historical-data collection;
- exceptional race/settlement states outside the normal-final winning envelope;
- live automated betting;
- active AI/LLM augmentation.

```text
AI_SIGNAL_USAGE_BASELINE:
DISABLED
```

Existing deterministic prediction engines are not marketed as an external AI/LLM
service. Optional external AI signals remain post-Ver0.8.

## Deferred release-state workflow

Repository evidence is exact:

- `v0.7.0` is an annotated tag with message `KeibaOS Ver0.7.0`;
- GitHub currently has no published Releases;
- `master` is `a136ab8d4d6aa48e37d3a62f5b8b79560dcc5b7a`;
- the formal base is 158 commits ahead of and zero behind `master`;
- `master` is an ancestor of formal.

```text
MASTER_INTEGRATION:
DEFERRED_TO_FINAL_RELEASE_PHASE

PREFERRED_FUTURE_INTEGRATION:
FAST_FORWARD_ONLY_IF_MASTER_UNCHANGED_AND_ANCESTOR

TAG_POLICY:
DEFERRED_ANNOTATED_V0_8_0_AFTER_MASTER_EQUALS_APPROVED_RELEASE_COMMIT

GITHUB_RELEASE:
YES_AFTER_FINAL_TAG

GITHUB_RELEASE_TAG:
v0.8.0

GITHUB_RELEASE_TITLE:
KeibaOS v0.8.0

GITHUB_RELEASE_BODY_SOURCE:
INDEPENDENTLY_APPROVED_DOCS_VER0_8_RELEASE_NOTES

RELEASE_DATE_POLICY:
OMIT_UNTIL_ACTUAL_RELEASE_OPERATION
```

C4j1 implementation must not update `master`, tag, or publish. A separately authorized
final release phase must verify the exact approved release-candidate formal commit,
formal CI, unchanged/ancestor `master`, and zero formal-behind-master count. If true,
fast-forward `master` to that exact commit; do not create an unnecessary merge commit.
If not true, stop for review rather than rebase or improvise.

After independently verified master integration, create an annotated `v0.8.0` tag with
message `KeibaOS Ver0.8.0`, only when `master` equals the approved release commit. Then
create GitHub Release title `KeibaOS v0.8.0` for that tag, using the approved
`docs/VER0.8_RELEASE_NOTES.md` body and the actual publication date where appropriate.

## Proposed C4j1 implementation scope

Allowed Files are exactly:

```text
README.md
docs/ROADMAP.md
docs/CHANGELOG.md
docs/ARCHITECTURE.md
docs/VER0.8_DESIGN.md
docs/HISTORICAL_REPLAY.md
docs/VER0.8_RELEASE_NOTES.md
examples/historical_replay_request.v1.example.json
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Every other path is forbidden. In particular, do not modify production, tests,
fixtures, `docs/VER0.8_SIMULATOR_DESIGN.md`, `AGENTS.md`, requirements, schemas,
migrations, workflows, package exports, CLI implementation, or runtime version state.

No committed example-validation test is proposed. The example must be checked with the
existing public loader during C4j1 implementation. If that cannot pass without changing
runtime/test code, stop for independent review rather than expanding scope.

## Implementation verification

The approved implementation completed these checks:

1. Load the checked-in example through
   `load_historical_replay_request_document(request_path=...)` without running replay.
2. Run `tests/test_cli_run_historical_replay.py` and
   `tests/test_historical_replay_request_document.py`.
3. Run the full suite: `python -m pytest -q`.
4. Run `git diff --check`.
5. Verify exactly the ten allowed implementation files differ from the formal base.
6. Verify no production/test/fixture/schema/migration/workflow/runtime-version change.
7. Verify no master, tag, or GitHub Release change.
8. Commit exactly the ten files once, push only the review branch, and require GitHub
   Actions `Tests / pytest (3.12)` PASS before reporting review readiness.

The unchanged exact formal runtime tree currently passes:

```text
FULL_SUITE:
3125 passed, 2506 subtests passed in 15.15s

EXAMPLE_MANIFEST_PUBLIC_LOADER_VALIDATION:
PASS

REQUEST_DOCUMENT_TESTS:
19 passed, 143 subtests passed in 0.62s

CLI_TESTS:
13 passed in 0.28s

MIXED_PROVIDER_ACCEPTANCE:
1 passed in 0.72s

RELEASE_DOCS_IMPLEMENTED:
YES

CLAIM_BOUNDARY_CONSISTENCY:
PASS

PRODUCTION_CHANGED:
NO

TEST_CHANGED:
NO

FIXTURE_CHANGED:
NO

SCHEMA_CHANGED:
NO

MIGRATION_CHANGED:
NO

WORKFLOW_CHANGED:
NO

PACKAGE_VERSION_SOURCE_CHANGED:
NO

MASTER_CHANGED:
NO

TAG_CREATED:
NO

GITHUB_RELEASE_CREATED:
NO

AI_SIGNAL_USAGE_BASELINE:
DISABLED
```

## Stop condition

After exactly one ten-file review commit, review-branch push, and successful remote CI,
stop for independent review. Do not integrate master, create `v0.8.0`, publish a GitHub
Release, or begin Ver0.9.

Formal integration remains pending a separate user command:

```text
RECOMMENDED_NEXT_PHASE:
INDEPENDENT_C4J1_IMPLEMENTATION_REVIEW
```
