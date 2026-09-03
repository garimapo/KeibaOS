# Current Phase

Status: `APPROVED_FOR_COMMIT`

## Identity and authority

- Phase: `POST_V0_8_DAILY_REPLAY_12`
- Name: `JRA Initial Supported Profile Final Decision`
- Phase type: `RESEARCH_AND_DESIGN_ONLY`
- Base Commit: `b94277432d3e0a805efb721f53f78c5e124728e1`
- Branch: `feature/post-v0.8-daily-replay`
- Outcome: `JRA_INITIAL_SUPPORT_DEFERRED`
- Production/test/fixture implementation and materialization: `NOT_AUTHORIZED`
- PREPARE staging/commit/push and `EXECUTE_APPROVED_PHASE`: `NOT_AUTHORIZED`

Authority: AGENTS.md, the applicable existing Ver0.8 design and implementation
contracts, and the reviewed Phase 8-11 findings in Git history. Phase 11 was committed,
pushed normally, fetched, and local/remote equality verified at the Base Commit before
this PREPARE. This is the final initial-support decision, awaiting independent review.
It is not another BLOCKED outcome carried into a JRA gap-resolution phase.

## Final decision

Of the three allowed outcomes, select only `JRA_INITIAL_SUPPORT_DEFERRED`.
Neither candidate meets every machine-checkable acceptance predicate:

| Candidate | Initial decision | Decisive unmet requirement |
| --- | --- | --- |
| A: supplied year-program / nittei / bangumi / accessS composite | Do not implement initially | Complete non-OCR PDF identity decoding and geometry/cell grammar are not frozen; the planned tuple set cannot be machine-established |
| B: accessS-led source family alone | Do not implement initially | Complete observed result lists cannot positively prove the complete original target denominator or detect an omitted meeting/race |
| v0.9 initial daily-target capability | NAR-only, explicitly requested scope | Reuse the already approved/implemented NAR supported profile without broadening its accepted dates or states |

There is no winning JRA profile and no new JRA production/test file or API proposal.
The Phase 10-11 calendar HTML locator profile was not reconsidered. No calendar asset
was acquired or re-examined, no network request was made, and PDF extraction/rendering
was not repeated. Only existing diagnostics, provenance, relevant accessS response
bytes, source code and prior reports were read.

The PDF profile remains preserved as a future candidate. This decision defers its
initial delivery; it neither declares non-OCR decoding impossible nor changes the
approved source semantics to make the implementation appear ready.

## Candidate A: PDF profile final assessment

The authority chain remains the captured historical year-program HTML and its exact
supplied nittei/bangumi hrefs and labels, followed by exact PDF bytes and accessS actual
evidence. OFFICIAL_YEAR_PROGRAM_SCHEDULE_VERSION retains the Phase 4 reviewed meaning.
In particular, the 2020 label supplies an April 6 revised schedule version, not proof
of what was known before the January event.

The Phase 8 manifest and all 21 recorded body length/digest pairs were verified from
existing local bytes. Six of those bodies are the following PDFs; their request identity,
supplied parent label/href, requested/observed time and digest remain in that manifest.

| Existing PDF basename | Bytes | SHA-256 | Stored page-1 extraction: unresolved CID tokens |
| --- | ---: | --- | ---: |
| nittei_2020.pdf | 46902 | 2a4d09505de286a574f760b9a4b386baf65734fa273d621f279ed7330bacc139 | 2724 |
| nittei_2024.pdf | 443138 | bc4a22849b33215bc9f1c127735654080c69b886b41b82d24f969197b4c553d1 | 2722 |
| bangumi_nakayama1_2020.pdf | 508250 | fa7ab3e6a38c7d3ab1de717af85594b44f4be02c17e143a32bc8dc7d4201928d | 0 |
| bangumi_nakayama1_2024.pdf | 117394 | 2cf7cba2265a00d1cdabb7f7ccdfc1682a7c033525a33c3d5882b249d509bd3a | 0 |
| bangumi_kyoto1_2020.pdf | 523275 | 301752db3d02846b29f9b87bb643edf499ccb0a02785e95313063ea06ed50f4c | 8 |
| bangumi_kyoto1_2024.pdf | 127671 | 6149a6e4cb96554b142b2e2800eef46238a7321ff034ff2ff1829038e81a9139 | 7 |

These counts inspect saved diagnostic text; they are not a new extraction, completeness
metric or assertion that every bangumi is unreadable. Some bangumi headings/day labels
are readable. That does not repair the necessary nittei date/meeting mapping or prove
a strict all-page race-tuple grammar.

| Required predicate | Evidence and decision |
| --- | --- |
| Exact PDF locator authority | Supplied historical year-program labels/hrefs are retained for the sampled PDFs; filenames never create identity |
| Exact PDF bytes | Six original bodies match the reviewed manifest; no recapture, conversion or re-save |
| Deterministic extraction without OCR | Phase 8-9 tested pypdf 6.10.0 and pdfplumber 0.11.9; saved nittei text still contains unresolved identity-bearing CID tokens |
| Pinned implementation dependency contract | Those are recorded research versions, not a qualified production stack; required CMap/font resources and extraction settings are not frozen |
| Geometry/text-object strict layout | Saved character objects include page number, font, matrix and bounding coordinates; no reviewed complete cell/annotation/page-role mapping joins them to all date/meeting/race identities |
| Complete meeting/day/race enumeration | Not established; readable examples, printed totals and sequential race-number inference are insufficient |
| Ambiguity/missing-object failure | Fail-closed remains required, but an unspecified parser that rejects everything is not an implementable supported profile |
| Exact planned/actual tuple equality | Actual-side observations exist; the machine-qualified planned tuple set needed for equality does not |

A fixed library version makes an extraction repeatable, not necessarily correct.
Geometry supplies coordinates, not a missing glyph-to-identity mapping. No invented CID
mapping, manual transcription, OCR, PDF filename, global digit regex, or inferred
meeting-day/race sequence may complete the evidence. Candidate A is therefore rejected
for initial implementation even if the separate accessS capture-boundary issue is later
resolved.

## Candidate B: accessS-led profile final assessment

The existing actual-source chain has useful positive observations:

- Captured year-program navigation supplies the accessS root/search POST.
- The root/search response supplies year/month selectors, a setParameter expression
  and objParam tail data. Historical month selection is source-owned research material;
  it is not permission to generate or guess opaque CNAME tokens.
- A month response exposes dated meeting actions. Each meeting response exposes direct
  result rows. Existing parse_jra_result_url_identity owns the supplied result identity.
- Phase 9 verified 48 exact result pages for four meetings on 2020-01-05 and 2024-01-06.
  Phase 10 added ordinary 2021/2025 samples. All-row parsing can reject malformed or
  duplicate represented rows and compare their supplied identities/dates.
- The result-header selector yields a historical displayed time with an exact date.
  It does not prove actual off-time, an unchanged original pre-race announcement, or
  a prediction-time snapshot cutoff. Exceptional start-time semantics are not qualified.

The decisive counterexample uses the already captured October 2019 month response:

| Exact parent date | Supplied meeting CNAME | Represented meeting/race list |
| --- | --- | --- |
| 2019-10-12 | pw01srl10082019040320191012/FE | 4回京都3日; 12 direct result rows |
| 2019-10-15 | pw01srl10052019040320191015/91 | 4回東京3日; 12 direct result rows |

Phase 10 had independently established cancelled Tokyo and its substitute date. The
accessS day-unit on October 12 lists only Kyoto. It cannot account for the original
Tokyo target membership/identities using its own represented result rows. October 15's
Tokyo results cannot be backdated or joined to October 12 by inference.

This out-of-initial-floor exception is a semantic counterexample, not a request to
support 2019. It shows why the proposed accessS-only ordinary-day acceptance predicate
cannot be inferred from a populated day/month table. The current research provides no
additional source-owned completeness or exception-exclusion predicate that rules out
the same omission mechanism for an otherwise normal-looking admitted date.

| Required predicate | Evidence and decision |
| --- | --- |
| Source-owned root/month authority | Observed source relation; exact root/search capture-kind and strict expression contract remain unapproved from Phase 7-9 |
| Exact target_date | Strict parent header/CNAME/result-header agreement is feasible for represented targets |
| Complete meeting set | No positive proof that all scheduled/original target meetings are represented, including omitted non-run meetings |
| Complete race set | Every represented row can be validated; unrepresented races cannot be detected by row contiguity or count |
| Scheduled/displayed start semantics | Historical displayed field observed; cannot silently substitute for an unqualified original scheduled time |
| Missing versus zero | No positive absence/completeness predicate; missing row/day is neither no race nor proven zero |
| Opaque token prohibition | Preserve exact source-owned action/table provenance; never synthesize a tail or use current time |
| Standalone complete denominator | Not proven; even resolving root/month capture mechanics does not resolve the semantic gap |

The equality of two lists built from the same result hierarchy is a consistency check,
not independent coverage evidence. Defining an ordinary day as "all returned rows look
normal" would silently accept a cancelled/missing partition that is absent entirely.
Defining the denominator as only races with results would change the approved target
membership contract and introduce hindsight-based selection. Candidate B is rejected.

## Causality and reporting consequences

Later-acquired historical official material is not automatically future leakage:
approved completeness evidence can be acquired after target_date when its historical
membership semantics are proven and its observed_at is honest. The failures here are
unproven membership and unsafe identity/time substitution, not merely late acquisition.

Neither candidate justifies deriving targets from outcomes, filling missing scheduled
times from current/post-event values, backdating acquisition, or feeding completeness
metadata into prediction. Snapshot selection and settlement cutoffs retain their
separate existing contracts. Historical displayed accessS time must not be promoted
into a causal bound merely because it can be parsed.

For the initial daily capability, a request containing JRA cannot return a successful
complete target set or a zero/full-day ROI by omitting JRA. Its unsupported completeness
remains a whole-request TARGET_DISCOVERY_INCOMPLETE boundary. No new failure enum,
daily persistence implementation, or provider-dispatch API is introduced here.
SimulationSummary.race_count and the existing replay request/engine contracts are
unchanged.

## NAR-only initial scope and architecture compatibility

The selected v0.9 initial daily-target scope is explicitly
`{HistoricalDailyProviderIdentity("NAR", "nar_official")}`. This is a capability/scope
decision, not a release-readiness claim or automatic implementation approval. The
existing NAR floor and ordinary/approved retained-row Kanazawa predicates stay intact;
not every NAR date is supported.

Read-only source inspection establishes compatibility:

| Existing component | Evidence for compatibility |
| --- | --- |
| DailyHistoricalReplayProviderScope | Accepts a nonempty, unique provider tuple; a NAR singleton is valid |
| HistoricalDailyTargetEvidenceBundle | One exact provider identity with its targets and provenance; no requirement for a JRA sibling |
| build_daily_historical_replay_target_set | Requires bundle-provider equality to requested closed scope; missing JRA in a mixed scope already fails with MISSING_ENVELOPE_EVIDENCE |
| build_nar_historical_daily_replay_target_set | Already constructs the NAR singleton scope and invokes the shared builder with its one audited NAR bundle |
| Shared ordering/digest | Already includes exact provider scope and canonical targets/provenance; no new schema, hash rule or provider assumption needed |
| Existing schema-v1 replay application | Separate from daily discovery; already dispatches exact known-race JRA and NAR evidence. Deferring automatic JRA daily discovery does not disable existing v0.8 JRA replay |

The shared scope/value validation does not itself certify source completeness: only a
qualified provider builder can supply a valid audited bundle. No fabricated empty JRA
bundle or relabelled NAR bundle can represent a JRA day. A caller asking for JRA+NAR
must receive failure, not a reduced NAR success; a NAR-only result must label that exact
scope and must not imply all-provider coverage.

The committed provider-neutral domain and NAR source need no changes for this decision.
Any later orchestration integration remains subject to its own PREPARE/review/approval.

## Reopening criteria and recommended next work

JRA remains a later provider extension using the same shared immutable bundle/target-set
boundary. Reopening requires new material evidence, not another phase carrying the
same research gaps:

- PDF route: demonstrated non-OCR identity decoding with pinned extraction/resources,
  strict geometry/all-cell/page grammar, complete tuples and reviewed planned/actual
  equality including rejection cases.
- accessS route: a positive official completeness and omission/exception-detection
  contract independent of the mere existence of result rows, plus reviewed
  root/month request authority and exact start semantics.
- Either route: qualified raw capture/provenance and fixture contracts, separate
  PREPARE, independent review and explicit implementation approval.

These are conditions for a future extension, not unresolved tasks blocking this initial
scope decision. The Phase 12 final outcome is DEFERRED, not BLOCKED.

Recommended next phase only: `NAR Daily Historical Evidence Resolver Design`
(`DESIGN_ONLY`), consuming an already audited NAR target set and applying the approved
exact snapshot/result/payout selection and classification contracts. It would require
a separate user PREPARE instruction and review. Monthly locator bootstrap, durable
capture storage, manifest builder and replay orchestration retain their own boundaries.
No next phase has started.

## Reused evidence and verification

- Phase 8 at commit 58750303a5fca21c2e2fcea7dd13b74b1aa76b93 and Phase 9 at
  adfac3946475d19058f9d24f15a1ae6588824fa7 supply the PDF/accessS investigation authority.
- Phase 10 at 2445a997d6614bb4406548243a777c152599edfc supplies ordinary and exception
  observations; Phase 11 at the Base Commit closes the calendar alternative.
- Existing external Phase 8 directory:
  C:/Users/garim/AppData/Local/Temp/keiba-phase8-jra-24517bdcf7524eedb5bf7c7f2db7cc95.
  candidate-provenance.json SHA-256:
  bff17dec9bb3f65b5265adf000eeeed956283b52f83029f135840789ef666ad8.
  Manifest and all 21 source bodies verified, including six PDFs.
- Existing external Phase 10 accesss-exception-2019 directory under
  C:/Users/garim/AppData/Local/Temp/keiba-phase10-jra-calendar-1f75d8f9f6c84f9d915b5b88494cfa38.
  provenance.json SHA-256:
  b8c0f8283d5f090b19361220f7560551e3c787174524d0135814e846eee644e3.
  Manifest and all four bodies verified; the month body SHA-256 is
  17d9645ba484ed4f6826888a1e70d1daed0125a35f9487593a7fb729cff634c1.
- Saved PDF text and character-object diagnostics were read only. No extraction library
  was installed, no source bytes were changed/reacquired, and no official fixture adopted.
- Original requested/observed times remain in external manifests. Research materials
  remain non-replay evidence and cannot supply formal bundle or causal timestamps.
- No dedicated/full test suite was run: this phase changes documentation only.
  Existing shared scope-validation tests were inspected, not executed.

## Allowed Files

```text
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

## Forbidden Files and actions

Every other repository file: production, tests, fixtures, dependencies, schemas,
migrations, database, logs, archives, CLI, NAR/shared code, tags and release history.
No stage, commit, push, implementation, fixture materialization, or next-phase start
is authorized during this PREPARE.

## Required PREPARE checks and stop condition

```text
git diff --check
git diff --name-only
git status --short
git diff --cached --name-only
```

Require only the two Allowed Files modified and an empty index. Stop at
DRAFT_FOR_REVIEW with the single outcome JRA_INITIAL_SUPPORT_DEFERRED. Any unexpected
file, evidence digest mismatch or contract conflict stops the workflow; do not repair
evidence or relax a predicate.
