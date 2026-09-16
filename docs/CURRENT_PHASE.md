# Current Phase

## Identity

- Phase: `POST_V0_8_DAILY_REPLAY_66`
- Title: `Tracked Safe Structural Root-Cause Diagnostics`
- Base HEAD: `beb9eca33b53f543a46eb07b71cc3b8a5e0256f9`
- Branch: `feature/post-v0.8-daily-replay`
- Status: `INTEGRATED_PENDING_REMOTE_VERIFICATION`
- Design Review: `PHASE66_DESIGN_REVIEW_PASS`
- Implementation Review: `PHASE66_IMPLEMENTATION_REVIEW_PASS`
- Outcome: `IMPLEMENTED_TRACKED_SAFE_STRUCTURAL_ROOT_CAUSE_DIAGNOSTICS`

## Baseline and immutable evidence

- Required Phase65 dependency is formally complete at commit `beb9eca33b53f543a46eb07b71cc3b8a5e0256f9`, tree `ce8efa96d96e0423b87051024c34bf88bdabe231`.
- Local and remote HEAD equal the base; branch is correct; index, untracked set, and worktree were clean at PREPARE entry.
- Phase64 remains `FORMALLY_COMPLETE_DIAGNOSTIC_RUN` with `DIAGNOSTIC_OBJECTIVE_COMPLETED_WITH_SOURCE_PROFILE_BLOCK`; its authorization is `PHASE64_DIAGNOSTIC_ACQUISITION_AUTHORIZATION_CONSUMED_FAIL_CLOSED` and retry is forbidden.
- Phase65 conclusions remain frozen: `SAFETY_ADDITIONAL_STRUCTURE_DIAGNOSTIC_REQUIRED`, `CURRENT_SAFE_EVIDENCE_INSUFFICIENT_FOR_DIRECT_SAFETY_STRUCTURE_FIX`, `PROFILE_B_ADDITIONAL_ANCESTRY_DIAGNOSTIC_REQUIRED`, `CURRENT_SAFE_EVIDENCE_DOES_NOT_PROVE_CANDIDATE_2_ANCESTRY`, and `PREDICATE_ORDERING_LIMITATION_CONFIRMED`.
- Phase64 observed DebaTable `PASS / FAIL / NOT_REACHED`, RaceList `PASS / PASS / PASS`, and normal Safety `UNSUPPORTED`. Ordinary Profile-B remains blocked at `UNIQUE_TARGET_6R=2`; no candidate selection is authorized.

## Strict-structure recovery diagnostic design

- Schema: `nar-race-entry-status-strict-structure-recovery-diagnostics`; `schema_version: 1`.
- Top-level exact keys: `schema`, `schema_version`, `document_results`. Results are exactly ordered `deba_table`, then `race_list`.
- Each exact result key set: `document_role`, `failure_kind`, `event_index`, `stack_depth`, `expected_open_tag`, `observed_end_tag`, `tolerant_parse`.
- Exact `failure_kind` vocabulary: `PASS`, `END_TAG_EMPTY_STACK`, `END_TAG_MISMATCH`, `UNCLOSED_STACK_AT_CLOSE`. There is no generic fail or parser-feed enum: only the three explicit current strict-validator branches become diagnostic values. Any unexpected `HTMLParser.feed`/`close` failure is a bounded diagnostic-operation error, produces no fabricated payload, and retains no exception text.
- `event_index` is a bounded nonnegative integer. It counts 1-based structural callbacks only—`handle_starttag`, `handle_startendtag`, and `handle_endtag`—not text, comments, or character references. For an end-tag failure it is the failing callback; for close failure and pass it is the total callbacks processed.
- `stack_depth` is a bounded nonnegative integer: immediately before the failing end tag for either end-tag failure; the final remaining depth for close failure; zero after a pass. A separate unclosed-depth field is omitted because it would duplicate `stack_depth` for the close-failure case.
- `expected_open_tag` and `observed_end_tag` are either JSON `null` or a fixed enum: `HTML`, `HEAD`, `TITLE`, `BODY`, `MAIN`, `HEADER`, `FOOTER`, `NAV`, `ARTICLE`, `SECTION`, `ASIDE`, `DIV`, `H1`, `H2`, `H3`, `H4`, `H5`, `H6`, `P`, `SPAN`, `A`, `STRONG`, `EM`, `B`, `I`, `U`, `UL`, `OL`, `LI`, `DL`, `DT`, `DD`, `TABLE`, `CAPTION`, `COLGROUP`, `THEAD`, `TBODY`, `TFOOT`, `TR`, `TH`, `TD`, `FORM`, `FIELDSET`, `LEGEND`, `LABEL`, `BUTTON`, `SELECT`, `OPTGROUP`, `OPTION`, `TEXTAREA`, `SCRIPT`, `STYLE`, `NOSCRIPT`, `TEMPLATE`, `DETAILS`, `SUMMARY`, `FIGURE`, `FIGCAPTION`, `PICTURE`, `CANVAS`, `VIDEO`, `AUDIO`, `OBJECT`, `MAP`, `FONT`, `CENTER`, `OTHER_OR_CUSTOM`. HTMLParser-normalized lowercase tags map deterministically; no provider tag string is retained.
- Legal combinations: `PASS` has depth `0` and both tags `null`; `END_TAG_EMPTY_STACK` has depth `0`, expected `null`, observed non-null; `END_TAG_MISMATCH` has depth `>0` and both tags non-null; `UNCLOSED_STACK_AT_CLOSE` has depth `>0`, expected non-null (the remaining stack top), and observed `null`.
- `tolerant_parse` is always attempted after successful strict UTF-8 decode and strict-diagnostic classification and is exactly `PASS` or `FAIL`; `NOT_RUN` is not a valid emitted value. It records only `BeautifulSoup(source, "html.parser")` reachability and never affects Phase56 Safety. Exact-byte inputs decode with `bytes.decode("utf-8", errors="strict")`; a decode failure raises a fixed bounded diagnostic error, retains no exception text, and remains Phase63 Safety-recovery evidence rather than inventing a structural result.
- Strategy: an independent diagnostic `HTMLParser` mirrors the current `_StrictStructureParser` transitions and void-tag set, while recording only the bounded state above. It neither imports nor mutates Profile-A private parser behavior. Parity tests must prove identical PASS/strict-ValueError classification for valid, empty-stack, mismatch, unclosed, void, and self-closing cases.

## Candidate-ancestry recovery diagnostic design

- Schema: `nar-race-entry-status-profile-b-candidate-ancestry-recovery-diagnostics`; `schema_version: 1`.
- Exact top-level keys: `schema`, `schema_version`, `target`, `race_table_scope_count`, `target_candidate_count`, `candidate_details_complete`, `candidate_results`.
- Candidate discovery exactly mirrors current Phase53 and Phase63: `section.raceTable` → `tr.data` → direct `td` → first direct cell normalized to exact `{race_no}R`. It does not change ordinary Profile-B semantics.
- `MAX_RETAINED_CANDIDATE_DETAILS = 8`. If there is one unique scope and candidate count is at most eight, details are complete and cardinality matches count. Above eight, details are explicitly incomplete and results are empty; no prefix is retained. Any non-unique/unavailable scope has count zero, incomplete details, and empty results.
- Each exact candidate key set: `candidate_ordinal`, `nearest_table_role`, `inside_change_info_table`, `nested_table_depth_within_race_scope`, `direct_schedule_table_descendant`.
- `candidate_ordinal` is positive, contiguous, and follows DOM order. `nearest_table_role` is exactly `RACE_SCHEDULE_TABLE`, `CHANGE_INFO_TABLE`, `OTHER_TABLE`, or `NO_TABLE`.
- Classification uses only fixed structural authorities. Let `nearest_table` be the closest ancestor `table` before the selected `section.raceTable`; table depth counts all such ancestor tables, including `nearest_table` as depth `1`. `inside_change_info_table` is true only when an ancestor table within the selected scope matches exact selector `table.changeInfo`. `CHANGE_INFO_TABLE` means `nearest_table` itself matches that selector. `RACE_SCHEDULE_TABLE` means exactly one table ancestor exists before the scope and `nearest_table` is not `table.changeInfo`. `OTHER_TABLE` means a nearest table exists, is not `table.changeInfo`, and depth is two or greater. `NO_TABLE` means none exists.
- `direct_schedule_table_descendant` is true exactly for `RACE_SCHEDULE_TABLE`; it means the candidate's closest table is the sole table ancestor between it and the selected race scope, not that it was inferred from text. This makes the name a fixed structural fact, not a row-selection rule.
- Cross-field invariants: `NO_TABLE` requires `inside_change_info_table=false`, depth `0`, and direct-schedule false. `CHANGE_INFO_TABLE` requires inside-change-info true, depth at least `1`, and direct-schedule false. `RACE_SCHEDULE_TABLE` requires inside-change-info false, depth `1`, and direct-schedule true. `OTHER_TABLE` requires depth at least `2` and direct-schedule false; inside-change-info may be true for an outer changeInfo ancestor. All counts use the existing safe ceiling `10,000`.
- The result never contains a selected, canonical, preferred, excluded, or deduplicated candidate. Even confirmed `CHANGE_INFO_TABLE` ancestry is diagnostic evidence only.

## Phase50 durable observability design

- Add exactly two optional milestones: `PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED` with exact detail key `profile_b_candidate_ancestry_recovery_diagnostics`, and `STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED` with exact detail key `strict_structure_recovery_diagnostics`. No third event.
- Required relative order: `RACELIST_CAPTURE_METADATA_RETAINED` → `PROFILE_B_DIAGNOSTICS_RETAINED` → `PROFILE_B_RECOVERY_DIAGNOSTICS_RETAINED` → `PROFILE_B_CANDIDATE_ANCESTRY_RECOVERY_DIAGNOSTICS_RETAINED` → `IDENTITY_VERIFICATION_PASS` → `PUBLICATION_SAFETY_RECOVERY_DIAGNOSTICS_RETAINED` → `STRICT_STRUCTURE_RECOVERY_DIAGNOSTICS_RETAINED` → unchanged normal Safety branch. This preserves all existing Phase63 relative ordering and records strict evidence before normal Safety terminal evidence.
- Both events use canonical append → flush → fsync and must be retained before transient raw cleanup. Phase50 independently validates exact nested schemas, field sets, enum/nullability, target, count bounds, complete/incomplete rules, ordinal continuity, and cross-field invariants. No raw bytes or arbitrary strings are accepted in journal details.
- `JOURNAL_SCHEMA_VERSION = 1` remains correct: this is additive optional milestone evolution under the existing v1 reader, every payload is independently versioned, old record structures are unchanged, and old v1 journals—including Phase57 and Phase64 shapes—remain readable without new events. No migration or rewrite is permitted. `_ALLOWED_OUTCOMES` remains unchanged.
- `MAX_RECORD_BYTES = 4096` remains unchanged. Actual maximum-valid payloads in the established conservative six-digit sequence envelope (`131072`), including LF, measure `837` bytes for strict diagnostics (margin `3259`) and `2598` bytes for eight ancestry records (margin `1498`). The ancestry measurement includes the allowed 512-byte formal baba code, maximum target race number, and maximum bounded depths. These replace PREPARE estimates of `836` and `2087`. Real writer output is also verified byte-for-byte at sequence 1 (five bytes shorter); no writer or record bound was changed.

## Tests and static audit required for implementation

- Strict diagnostics: valid nesting; empty-stack end tag; mismatch; unclosed close; void/self-closing behavior; known/other tag mapping; every legal/impossible typed state; canonical determinism; no markup/text/attribute leakage; tolerant PASS and deterministic FAIL path; Profile-A parity.
- Ancestry diagnostics: zero/one/two candidates; same schedule table; nested exact `table.changeInfo`; other nested table; no ancestor table; eight complete/nine incomplete; DOM order; depth and enum classification; all cross-field rejections; canonical determinism; no class/text leakage; Phase53/Phase63 candidate-discovery parity.
- Phase50: both events and exact keys; malformed schema/version; bad role/enum/tag/tolerant state; contradictory strict fields; candidate cardinality/overflow/depth/ancestry contradictions; order violation and valid order; old journal, Phase57 shape, Phase64 24-record shape, and Phase63 behavior unchanged; v1 and both record bounds.
- The new production module has no HTTP, socket, filesystem I/O, database, subprocess, clock, randomness, environment, Git, or publication authority. Parsing in-memory inputs only.

## Scope, future acquisition, and persistent constraints

- Exact implemented manifest: `scripts/simulation/nar_race_entry_status_source_profile_structural_recovery_diagnostics.py`; `tests/test_nar_race_entry_status_source_profile_structural_recovery_diagnostics.py`; `scripts/simulation/nar_race_entry_status_reacquisition_observability.py`; `tests/test_nar_race_entry_status_reacquisition_observability.py`; `docs/CURRENT_PHASE.md`; `docs/LATEST_CODEX_REPORT.md`.
- No Phase44, Phase53 ordinary diagnostics, Phase56 Profile-A/Safety/publication contract, Phase60, Phase61, or Phase63 change is required. No tracked safe-evidence artifact is required for this support-only phase.
- A later diagnostic acquisition is eventually required, but Phase66 issues none. It needs a new PREPARE → review → APPROVE → one-shot authorization for `CONTROLLED_REACQUISITION_FOR_STRICT_STRUCTURE_AND_CANDIDATE_ANCESTRY_DIAGNOSTICS`; it is never a Phase64 retry.
- Phase57 remains `POST_AUTHORIZATION_STOP` with consumed-fail-closed authorization. Phase54 remains `PHASE54_AUTHORIZATION_UNCONSUMED_BUT_UNUSABLE_FOR_V2`; Phase41 remains `DESIGN_BLOCKED`. Market eligibility, positive market eligibility, and whole-meeting cancellation remain `UNSUPPORTED`.
- EXECUTE changes exactly the six implemented paths, leaves the index empty, and makes no commit or push. Provider HTTP is `0`; Phase44 live entry is `NO`; authorization action is `NONE`.

## Implementation and final verification

- Public APIs: `diagnose_nar_race_entry_status_strict_structure_recovery(*, deba_table_bytes, race_list_bytes)` returns frozen `StrictStructureRecoveryDiagnostics`; `diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery(*, race_list_bytes, target)` returns frozen `ProfileBCandidateAncestryRecoveryDiagnostics`.
- The independent structural parser imports only the existing void-tag set, not the Profile-A parser. It increments at structural callback entry; bounded overflow fails the operation without clamping. Unknown tags map to `OTHER_OR_CUSTOM`, including mismatch cases whose two safe enums can be equal. Strict UTF-8 and unexpected parser failures raise fixed bounded errors without retained exception context. BeautifulSoup is always attempted after structural classification; only `ParserRejectedMarkup` maps to tolerant `FAIL`.
- Candidate discovery reuses `_direct_cells` and `_normalized_cell`; strict decode or parser rejection returns unavailable scope/count zero with incomplete empty details. Nonunique scopes and detail overflow are separately fail-closed. The ancestor walk stops at the selected raceTable scope; only exact `changeInfo` class-token membership is recognized.
- Both result families enforce exact immutable types, keys, bools, bounded integers, and sorted compact UTF-8 JSON (`ensure_ascii=False`, `allow_nan=False`). No provider text, custom tag, class, attribute, href, query, raw HTML, or selection is emitted.
- Phase50 independently validates payload dictionaries and chronological placement; ancestry target/count/completeness must agree with Phase63 recovery, and strict classification must agree with Phase63 UTF-8/strict stages. For a strict pass, DOM-parse results must also agree. Existing append/flush/fsync behavior is unchanged.
- Dedicated command: `python -B -m pytest -q tests/test_nar_race_entry_status_source_profile_structural_recovery_diagnostics.py` — `152 passed`.
- Phase50 command: `python -B -m pytest -q tests/test_nar_race_entry_status_reacquisition_observability.py` — `327 passed` on final code.
- Relevant command: `python -B -m pytest -q tests/test_nar_race_entry_status_source_profile_structural_recovery_diagnostics.py tests/test_nar_race_entry_status_reacquisition_observability.py tests/test_nar_race_entry_status_source_profile_diagnostics.py tests/test_nar_race_entry_status_source_profile_profile_a.py tests/test_nar_race_entry_status_source_profile_publication_contract.py tests/test_nar_race_entry_status_source_profile_recovery_diagnostics.py tests/test_nar_race_entry_status_source_profile_publication_plan.py` — `657 passed`; includes Phase59/61 compatibility cases in Phase50 and Phase60 publication-plan tests.
- Full final suite, run once: `python -B -m pytest -q` — `4258 passed`, `2841 subtests passed`, `0 failed` in `31.89s`.
- Static AST/source audit: `PASS`, no new network or side-effect imports/calls. Profile-A structural PASS/FAIL and Phase53/63 candidate count/order parity: `PASS`. Historical v1, synthetic Phase57 22-record and Phase64 24-record shapes remain readable with no Phase66 events or migration; external temp evidence was not read for these regressions.
- Phase44, ordinary Phase53, Phase56 Profile-A/Safety/publication contract, Phase60/61, Phase63 module/schemas, fixtures, `.gitattributes`, database, and logs have no diff. Outcome and authorization vocabularies remain unchanged.
- No live structural diagnostics were collected. The actual Deba failure kind and Candidate 2 ancestry remain unknown; Safety and Profile-B are not remediated. No later acquisition is authorized by this implementation.
- Final status/diff checks: exact four tracked modified and two new untracked implementation paths, staged empty, `git diff --check` PASS. There are no additional visible database/log/cache artifacts.

## Next permitted action

- Implementation manifest is frozen to the exact six listed paths. Provider HTTP is `0`; Phase44 is not entered; Phase66 authorization is `NONE`.
- Remote verification is required before any subsequent phase. This phase is not formally complete locally.
- `INDEPENDENT_REMOTE_VERIFICATION`. Stop without provider HTTP, Phase44 entry, authorization, or acquisition.
