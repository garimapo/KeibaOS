# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and authority

- Phase: `4C-2d3b1i6d1d5f1c4j2`
- Name: `Ver0.8 Final Release-State and Publication Gate Preparation`
- Base Commit: `5c633d7c81c09df1851baabd2bcc22e064a43042`
- Branch: `review/4c-2d3b1i6d1d5f1c4j2-ver0.8-final-release-prepare`
- Formal branch: `feature/ver0.8-simulator`
- Previous phase: `4C-2d3b1i6d1d5f1c4j1`
- Previous phase status: `FORMALLY_COMPLETE`
- Version target: `0.8.0`
- Tag target: `v0.8.0`
- Release name: `KeibaOS v0.8.0`

The C4j2 architecture and exact finalization contract were independently approved and
the six-file documentation implementation is complete pending independent review.
This implementation authorizes no formal integration, master update, tag, GitHub
Release, or post-Ver0.8 phase.

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
```

## Verified repository and release state

The PREPARE audit verified the following exact remote state on 2026-09-01:

```text
FORMAL_REMOTE_HEAD:
5c633d7c81c09df1851baabd2bcc22e064a43042

MASTER_REMOTE_HEAD:
a136ab8d4d6aa48e37d3a62f5b8b79560dcc5b7a

FORMAL_AHEAD_MASTER:
159

FORMAL_BEHIND_MASTER:
0

MASTER_IS_ANCESTOR_OF_FORMAL:
PASS

FORMAL_REMOTE_CI:
PASS

FORMAL_REMOTE_CI_RUN:
33456151832

FORMAL_REMOTE_CI_JOB:
99696405437

EXISTING_RELEASE_TAGS:
v0.7.0_ONLY

V0_7_0_TAG_TYPE:
ANNOTATED

V0_7_0_TAG_MESSAGE:
KeibaOS Ver0.7.0

V0_8_0_TAG_STATE:
DOES_NOT_EXIST

GITHUB_RELEASE_STATE:
NONE
```

The existing annotated `v0.7.0` tag resolves to current master
`a136ab8d4d6aa48e37d3a62f5b8b79560dcc5b7a`. Any changed remote state requires
fail-closed re-review; it must not be repaired by merge, rebase, or force push.

## C4j2 purpose and durable-state rule

C4j1 formally integrated the runtime-complete and release-documentation-complete
Ver0.8 release candidate. C4j2 freezes the smallest final documentation transition
whose content is true both immediately before publication and after publication.

The final tagged release commit must not require a post-tag documentation mutation.
Transient claims about a review branch, pending master integration, a missing tag, a
missing GitHub Release, or candidate status must not remain in the release-facing
final state. Historical phase reports remain unchanged because they are audit records
of the state that existed when they were written.

## Exact finalization proposal

### README

Change only the opening description from release-candidate wording to:

```text
KeibaOS Ver0.8 is a deterministic, auditable historical horse-racing replay platform.
```

All capability, setup, CLI, auditability, payout/EV, test, limitation, and non-claim
content remains unchanged. No release date or profitability claim is added.

```text
README_FINALIZATION:
REMOVE_RELEASE_CANDIDATE_QUALIFIER_ONLY
```

### ROADMAP

Remove only the transient line:

```text
Status: release candidate pending final integration.
```

Keep the exact `Ver0.8 — Historical Replay / Simulation Platform` heading, completed
capability list, superseded-planning explanation, and Post-Ver0.8 section. Do not
invent a Ver0.9 contract or add a publication date.

```text
ROADMAP_FINALIZATION:
REMOVE_TRANSIENT_STATUS_LINE_ONLY
```

### CHANGELOG

Change only the heading:

```text
## Ver0.8.0 (Unreleased)
```

to:

```text
## Ver0.8.0
```

Preserve the complete approved Ver0.8 entry, complete published Ver0.7/Ver0.6/Ver0.5
history, and superseded-future-plan notice exactly. Do not add a guessed or predated
release date.

```text
CHANGELOG_FINALIZATION:
REMOVE_UNRELEASED_QUALIFIER_ONLY

CHANGELOG_PUBLISHED_HISTORY_POLICY:
PRESERVE_EXACTLY

CHANGELOG_OBSOLETE_FUTURE_PLAN:
REMAIN_SUPERSEDED
```

### Release notes

Change the top identity from:

```text
Release target: `v0.8.0`

Status: `RELEASE_CANDIDATE_PENDING_FINAL_INTEGRATION`
```

to exactly:

```text
Release: `v0.8.0`
```

Remove the transient candidate status. Keep the existing capability, limitation,
verification, migration, and non-claim sections. The two uses of
`release-candidate` in `Verification State` remain valid provenance: they describe
which candidate runtime passed verification and explicitly state that raw counts are
not a permanent semantic contract.

Rewrite only `Release State` to this durable meaning:

```text
This document defines the approved release content for KeibaOS v0.8.0.
The authoritative publication identity is the annotated v0.8.0 Git tag and the
corresponding GitHub Release.

The release remains a deterministic historical replay and verification platform.
Its release identity does not imply profitability, calibrated predictive probability,
or a demonstrated strategy edge.
```

The final text must not say that master integration is pending, that the tag or
GitHub Release does not exist, that the release is a candidate, or that final
integration is pending.

```text
RELEASE_NOTES_FINALIZATION:
DURABLE_RELEASE_IDENTITY_AND_RELEASE_STATE
```

## Release date policy

```text
RELEASE_DATE_IN_REPOSITORY_DOCS:
OMITTED
```

The annotated tag and GitHub Release metadata provide the actual publication time.
Omitting a repository release date prevents guessing, backdating, and a post-tag docs
commit.

## Transient release-state search audit

The exact formal-base search covered, case-insensitively:

```text
release-candidate
release candidate
pending final integration
RELEASE_CANDIDATE_PENDING_FINAL_INTEGRATION
Unreleased
master integration is pending
tag has not been created
GitHub Release has not been published
```

It returned 24 baseline hit lines. Their exact disposition is:

### A — needs correction

- `README.md:3` — remove the opening release-candidate qualifier.
- `docs/ROADMAP.md:32` — remove the transient status line.
- `docs/CHANGELOG.md:3` — remove `(Unreleased)` from the Ver0.8 heading.
- `docs/VER0.8_RELEASE_NOTES.md:5` — remove the transient status line as part of the
  top identity replacement.
- `docs/VER0.8_RELEASE_NOTES.md:115-116` — replace the transient `Release State`
  paragraph with the durable release identity contract.
- Former C4j1 `docs/CURRENT_PHASE.md:99,130,139,274,278,358` — superseded live-phase
  instructions; replaced by this C4j2 PREPARE document. These are not release-facing
  implementation edits.

### B — historical/audit record; preserve unchanged

- `docs/LATEST_CODEX_REPORT.md:6263,6282,6342,6345,6392,6402,6427,6487,6498,6499`
  — append-only C4j1 PREPARE, approval, implementation, and correction evidence.

### C — valid non-transient context; preserve unchanged

- `docs/VER0.8_RELEASE_NOTES.md:76,79` — verification provenance describing the
  candidate runtime that passed and clarifying that exact counts are not a permanent
  semantic contract.

The audit found no additional release-facing path that requires a final-state edit.
Any matching terms added to this document or the appended PREPARE report are audit
quotations and therefore disposition B.

## Proposed C4j2 implementation scope

Allowed Files are exactly:

```text
README.md
docs/ROADMAP.md
docs/CHANGELOG.md
docs/VER0.8_RELEASE_NOTES.md
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Every other path is forbidden. In particular, implementation must not modify:

```text
scripts/**
tests/**
tests/fixtures/**
scripts/migrations/**
.github/**
requirements.txt
requirements-dev.txt
AGENTS.md
examples/historical_replay_request.v1.example.json
docs/HISTORICAL_REPLAY.md
docs/ARCHITECTURE.md
docs/VER0.8_DESIGN.md
docs/VER0.8_SIMULATOR_DESIGN.md
```

No production, test, fixture, schema, migration, workflow, package-version source,
manifest, architecture, runtime, or AI behavior is part of C4j2.

## Proposed implementation verification

A later separately approved C4j2 implementation must:

1. make only the four exact release-facing edits above;
2. preserve the published CHANGELOG history byte-for-byte outside the Ver0.8 heading;
3. repeat the transient-state search and classify any remaining match;
4. run `python -m pytest -q`;
5. run `git diff --check`;
6. prove exactly the six allowed files differ from the formal implementation base;
7. prove no production, test, fixture, schema, migration, workflow, manifest,
   package-version source, or AI runtime change;
8. stop for independent review without updating formal, master, tags, or Releases.

The proposed implementation review branch is:

```text
review/4c-2d3b1i6d1d5f1c4j2-ver0.8-final-release-state
```

The proposed review commit message is:

```text
docs: finalize Ver0.8 release state
```

These implementation details are architecturally approved but remain unexecuted until
a later `EXECUTE_APPROVED_PHASE` instruction.

## Future publication transaction — design only

The publication transaction is not authorized by this PREPARE or by the future docs
implementation. It requires a separate independent approval after the exact final
release-state docs commit is formally integrated and verified.

### Preconditions

Freeze the following exact gates:

```text
FORMAL_RELEASE_COMMIT:
EXACT_INDEPENDENTLY_APPROVED_COMMIT_REQUIRED

FORMAL_RELEASE_TREE:
EXACT_INDEPENDENTLY_APPROVED_TREE_REQUIRED

MASTER_PRECONDITION:
origin/master == a136ab8d4d6aa48e37d3a62f5b8b79560dcc5b7a

ANCESTRY:
MASTER_IS_ANCESTOR_OF_FORMAL_RELEASE_COMMIT

FORMAL_BEHIND_MASTER:
0

FORMAL_REMOTE_CI:
PASS_FOR_EXACT_FORMAL_RELEASE_COMMIT

TAG_PRECONDITION:
refs/tags/v0.8.0_DOES_NOT_EXIST

GITHUB_RELEASE_PRECONDITION:
NO_EXISTING_V0_8_0_RELEASE
```

If master has moved, formal is behind, CI is not green, the tag exists, or a v0.8.0
release exists, stop for changed-state review. Do not merge, rebase, overwrite, or
repair refs.

### Master policy

```text
MASTER_INTEGRATION_METHOD:
FAST_FORWARD_ONLY
```

Fast-forward master to the exact approved formal release commit with no merge commit,
squash, rebase, or force push. Verify remote master equals that exact commit. If the
master push triggers a new CI run, require it to complete successfully before tagging.

### Tag policy

```text
TAG_TYPE:
ANNOTATED

TAG_NAME:
v0.8.0

TAG_MESSAGE:
KeibaOS Ver0.8.0
```

Create the annotated tag only after remote master equals the exact approved release
commit. The tag object must peel to that exact commit. Push only the tag, then
independently verify its object type, message, and target.

### GitHub Release policy

```text
CREATE_GITHUB_RELEASE:
YES

GITHUB_RELEASE_TITLE:
KeibaOS v0.8.0

GITHUB_RELEASE_TAG:
v0.8.0

GITHUB_RELEASE_BODY_SOURCE:
EXACT_APPROVED_DOCS_VER0_8_RELEASE_NOTES
```

Create the GitHub Release only after the annotated tag is independently verified.
Use exact approved `docs/VER0.8_RELEASE_NOTES.md` content as the body; do not derive
claims from commit history or publish alternate draft text. Independently verify the
published title, tag, body, target, and non-draft/non-prerelease state.

## C4j2 implementation result

The exact four release-facing transitions were applied. README now uses the approved
durable platform description. ROADMAP has no transient Ver0.8 status line. CHANGELOG
uses `Ver0.8.0` without a date and otherwise matches the approved baseline exactly.
Release notes use `Release: v0.8.0`, preserve Verification State provenance, and use
the exact durable Release State wording.

The release-facing transient-state search now returns exactly two hits, both in
`docs/VER0.8_RELEASE_NOTES.md` Verification State:

```text
docs/VER0.8_RELEASE_NOTES.md:74
release-candidate runtime passed the full test suite and GitHub Actions

docs/VER0.8_RELEASE_NOTES.md:77
release-candidate verification results are not a permanent semantic contract
```

Both are approved provenance. README, ROADMAP, CHANGELOG, release-note top metadata,
and release-note Release State contain no transient public release-state wording.

```text
PHASE:
4C-2d3b1i6d1d5f1c4j2

PHASE_NAME:
Ver0.8 Final Release-State and Publication Gate Preparation

FORMAL_BASE:
5c633d7c81c09df1851baabd2bcc22e064a43042

VERSION_TARGET:
0.8.0

TAG_TARGET:
v0.8.0

RELEASE_STATE_FINALIZED:
YES

README_DURABLE_STATE:
PASS

ROADMAP_DURABLE_STATE:
PASS

CHANGELOG_DURABLE_STATE:
PASS

RELEASE_NOTES_DURABLE_STATE:
PASS

VERIFICATION_PROVENANCE_PRESERVED:
PASS

PUBLISHED_HISTORY_PRESERVED:
PASS

TRANSIENT_PUBLIC_RELEASE_STATE:
NONE

REMAINING_TRANSIENT_SEARCH_HITS:
43_HIT_LINES_TOTAL; 2_RELEASE_NOTES_PROVENANCE; 20_CURRENT_PHASE_AUDIT;
21_LATEST_REPORT_HISTORY_AND_AUDIT

RELEASE_DATE_IN_REPOSITORY_DOCS:
OMITTED

MASTER_INTEGRATION_METHOD:
FAST_FORWARD_ONLY

FULL_SUITE:
3125 passed, 2506 subtests passed in 13.00s

MASTER_CHANGED:
NO

TAG_CREATED:
NO

GITHUB_RELEASE_CREATED:
NO

PRODUCTION_CHANGED:
NO

TEST_CHANGED:
NO

SCHEMA_CHANGED:
NO

MIGRATION_CHANGED:
NO

WORKFLOW_CHANGED:
NO

AI_RUNTIME_CHANGED:
NO

PUBLICATION_AUTHORIZATION:
NO
```

## Implementation and publication authorization

```text
C4J2_PHASE_STATUS:
READY_FOR_REVIEW

C4J2_ARCHITECTURE:
APPROVED

C4J2_IMPLEMENTATION:
COMPLETE_PENDING_INDEPENDENT_REVIEW

MASTER_INTEGRATION_AUTHORIZATION:
NO

TAG_AUTHORIZATION:
NO

GITHUB_RELEASE_AUTHORIZATION:
NO

PUBLICATION_AUTHORIZATION:
NO

POST_VER0_8_WORK:
NOT_AUTHORIZED
```

## Stop condition

After exactly one six-file review commit, review-branch push, and successful remote
CI, stop. Do not formally integrate C4j2, update master, create or push a tag, publish
a Release, add a date, or begin post-Ver0.8 work.

The only recommended next activity is:

```text
RECOMMENDED_NEXT_PHASE:
INDEPENDENT_C4J2_FINAL_RELEASE_STATE_REVIEW
```
