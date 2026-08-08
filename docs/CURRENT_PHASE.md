# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d — NAR official past-race source evidence preparation

## Base Commit

`960c3419e52205cbfd94c3466eaabbb85d14e6ba feat: assemble historical input snapshots`

## Branch and Workspace

Formal branch: `feature/ver0.8-simulator`

Preparation review branch: `review/4c-2d3b1i6c1d-prepare`

Canonical workspace: `C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is read-only for this phase.

## Objective and Boundary

c1d investigates the smallest fail-closed *supplied official NAR evidence* boundary that could emit committed c1a
`HistoricalInputSourceRecord(record_kind="past_race")` values for target-race entries. It may support
`past_race_absence` only if supplied official evidence proves the complete zero-result query scope. The question is
identity and causal provenance, not whether historical rows can be scraped.

This PREPARE changes documentation only. It must not fetch, parse, save, query SQLite, use a clock, add an API,
modify c1a/c1b/c1c, or implement tests. A later normalizer, if approved, must accept only caller-supplied immutable
official responses and must never perform HTTP, filesystem, database, provider, parser, or legacy-data work.

## Read-only Investigation Findings

Committed c1a requires a `past_race` record to contain a non-null provider record ID and all race-result values:
race date, place, race name, race class, distance, surface, weather, condition, finish, Decimal margin, race time,
Decimal weight and weight difference, jockey, popularity, Decimal odds, passing order, and fourth-corner position.
It permits no made-up defaults. `past_race_absence` separately requires a non-null canonical source URL and an exact
zero-result scope for one external entry and target date. c1a owns source-ID construction and duplicate/conflicting
provider-record detection through `validate_historical_input_source_record_set()`.

Committed c1b accepts only one supplied DebaTable response and emits track, entry, jockey, and odds-win records. Its
entry contract deliberately emits `external_horse_id = None`; its deterministic external entry ID is target-race plus
horse number. The reviewed fixture contains no official horse `href`, and c1b retains neither a horse-detail URL nor
an immutable target-row-to-horse linkage artifact. Therefore a c1b tuple cannot bind a historical row to a target
external entry and remains intentionally incomplete for c1c.

Read-only inspection of official `https://www.keiba.go.jp` pages found these observed navigation forms:

* `/KeibaWeb/TodayRaceInfo/RaceMarkTable` uses the same target-race query family observed by c1b:
  `k_babaCode`, `k_raceDate`, and `k_raceNo`; its normal completed-race table exposes a horse row plus race
  facts and result columns.
* An official horse-history page was observed at
  `/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=<decimal>` and its historical-race title links led to an
  official RaceMarkTable page. The exact `k_lineageLoginCode` appears provider-native, but this observation alone
  does not prove that a c1b target row refers to that code.
* The normal RaceMarkTable result table visibly has finish, horse number, horse link, body weight/increase-decrease,
  time, margin, corner passing order, popularity, and win odds. It also demonstrates non-decimal display margins
  such as `ハナ`, `クビ`, and `大差` alongside decimal-like values. Those cannot become a required c1a Decimal margin
  without a separately approved semantic conversion contract.
* The observed ばんえい result layout does not provide the normal corner-passing representation required to prove
  c1a `fourth_corner_position`; it is not a supported variant for the initial boundary.

Existing legacy `HorseParser`, `PastRaceParser`, and `fetch_past_races` are read-only historical code only. They use
HTTP/DB or heuristic/defaulting behavior, including legacy table fallbacks and inferred fields, and are not trusted or
reusable as c1d evidence semantics.

## Identity and Contract Decision

### Stable Official Horse Identity

**NOT_PROVEN in the committed c1b contract.** Official HorseMarkInfo URLs expose a plausible provider-side
`k_lineageLoginCode`, but current c1b neither extracts nor verifies a target DebaTable horse anchor nor preserves the
code in `external_horse_id`. Horse name, jockey, horse number across races, list position, local IDs, and legacy
parser identifiers are forbidden substitutes.

The desired proof chain is:

    target DebaTable row / target external_entry_id
    -> exact official horse anchor and validated provider horse identity
    -> supplied official HorseMarkInfo history link
    -> exact supplied historical RaceMarkTable row for that same official horse identity

The historical race page must remain enveloped by the *target* `external_race_id` and target `external_entry_id`; it
must never replace them with the historical race identity.

### Required Prerequisites

**C1B contract change required: YES.** A prerequisite phase must decide and review exact extraction, canonicalization,
and immutable preservation of the official target horse-link identity from a DebaTable row. c1d must not silently
reparse a target page and duplicate c1b's target-row boundary merely to recover discarded identity.

**Single-record provenance prerequisite required: YES.** The target-row/horse-history pages prove target-horse
linkage, while RaceMarkTable supplies the historical result facts. A single c1a record presently has only one
`canonical_source_url` and one observed stamp. Selecting only the result URL would omit the identity evidence; using
only the history URL would misrepresent the fact source. Before c1d can combine pages, ChatGPT must approve a
provider-neutral immutable evidence-chain/provenance representation or prove that the committed c1a model can record
the chain without misleading a record's canonical source URL and timestamps. This PREPARE does not change c1a.

Consequently, c1d is **PREREQUISITE_REQUIRED**, not an implementation-ready four-file phase.

## Supported-page and URL Findings

| Page / variant | State | Reason |
| --- | --- | --- |
| Target DebaTable horse-link extraction | PREREQUISITE_REQUIRED | c1b currently discards the official horse anchor. |
| Horse detail/profile / HorseMarkInfo | DEFERRED | Provider-native lineage query was observed, but raw target-link compatibility, canonical URL grammar, and pagination proof are not frozen. |
| Normal completed RaceMarkTable row | PREREQUISITE_REQUIRED | Result facts are available, but target identity and multi-response provenance are not representable yet. |
| Abnormal/cancelled/removed/disqualified row | UNSUPPORTED | c1a strict numeric/result fields cannot receive invented values. |
| Same-date multiple starts | UNSUPPORTED | c1c rejects unprovable same-date chronology; provider ID/list order is not a tie-breaker. |
| ばんえい RaceMarkTable | UNSUPPORTED | Required corner/fourth-corner evidence is not uniformly present. |
| `past_race` output | PREREQUISITE_REQUIRED | Requires both identity and provenance prerequisites. |
| `past_race_absence` output | UNSUPPORTED | Complete official zero-history/pagination proof has not been established. |

No HTML ID or class may dispatch a future page kind. Each supported kind must be selected from a strict canonical URL:
`https`, exact `www.keiba.go.jp` host, no credentials/fragment/control characters, no unsupported port, exact path,
and an exact page-specific query-key set with duplicate/unknown keys rejected. Percent-escape, date, and numeric
spelling rules must be frozen from supplied official examples before implementation. RaceMarkTable is an observed
separate path (`/KeibaWeb/TodayRaceInfo/RaceMarkTable`); its path, rather than a marker in its HTML, determines kind.
The canonical HorseMarkInfo URL policy is intentionally not frozen yet.

## Candidate Field Evidence and Fail-closed Policy

The future normalizer may use only an exact normal completed RaceMarkTable row after raw supplied-byte selectors have
been independently frozen. The following is an investigation map, not an implementation authorization.

| c1a value | Official evidence candidate | Initial policy |
| --- | --- | --- |
| race_date, place, race_name, distance_m, track, weather, track_condition | RaceMarkTable race heading/facts | Must have distinct validated nodes; missing/ambiguous fails. |
| race_class | Official result-page class/condition element | DEFERRED until a semantic element distinct from promotional subtitle text is proven. |
| finish, race_time, jockey, popularity, odds | Exact completed-result row columns | Only strict committed type forms; cancellation/non-numeric state fails. |
| margin | Exact result-row margin | Only an approved direct Decimal spelling could be supported. `ハナ`, `クビ`, `大差`, fractions, or blank are unsupported until separately designed. |
| weight, weight_diff | Exact body-weight display such as `513(3)` or `459(-1)` | Only an exact validated numeric parenthetical form; `計不`/missing fails. |
| passing_order, fourth_corner_position | Exact row corner-passing column | Only a validated complete official passing form with a provable fourth component; no heuristic inference. |

No field may come from target odds, legacy DB values, another horse, a name match, a default zero/empty value, or a
guess. Target-race inclusion, a historical date not strictly before the target date, duplicate official history links,
duplicate historical identities, or incompatible result rows must fail closed.

## Provider Record Identity and Response Provenance

No provider-record-ID representation is frozen. A RaceMarkTable URL alone identifies a race page, not necessarily one
horse's result. A possible future identity would need the exact canonical historical RaceMarkTable race identity plus
the validated official `k_lineageLoginCode` bound through the target and history chain. That pair cannot be adopted
until the prerequisites establish its canonical syntax, target linkage, one-row uniqueness, and immutable provenance.
It must never be a source ID, URL alone, Python hash, random UUID, local ID, target horse number, or horse name.

Every future raw response needs caller-supplied exact bytes, strict UTF-8 policy where applicable, a canonical official
response URL, and an explicit aware `observed_at`; no current-time fallback is permitted. `available_at` remains
`None` unless an official page itself exposes defensible publication-time evidence. It must not be derived from race
date, result time, HTTP Date, file metadata, crawl time, or a clock.

An eventual bundle must preserve all official pages needed for the identity proof and reject missing, duplicate, or
incompatible links. Reusing `NarSuppliedOfficialResponse` is not approved merely because it is convenient: it models
one response, while the required relation is multi-response. The evidence-chain prerequisite must first decide whether
a new frozen/slotted bundle and a c1a-compatible immutable chain representation are sufficient.

## Temporal and Pagination Policy

For eventual snapshot use, every response whose evidence contributes to a record must have
`observed_at <= information_cutoff`; the normalizer preserves the exact caller-supplied stamp rather than deriving it.
A past race occurring before the target race does not itself prove that the result was available before prediction.

Absence is deliberately unsupported. An empty first page, no link, failed parse, missing pagination response, or
history page with no visible row is not zero-history evidence. Support would require an official, supplied,
complete query proof scoped exactly to `(external_entry_id, target_race_date, strictly_before_target_race=True)` with
zero results, including all pages or a validated official count/terminal-page proof. Unknown pagination state,
missing page, or duplicate page must fail closed. No bounded first-page window is authorized.

## Future Public API and Allowed Files

No c1d production public API is frozen, because the identity and provenance prerequisites are unresolved. The
candidate module name `scripts/simulation/nar_historical_past_race_source.py`, an associated dedicated test module,
and a small supplied-response bundle/error/normalizer surface are **not authorized** until ChatGPT decides the
prerequisite contract extension.

Accordingly, no c1d implementation Allowed Files are approved. A later prerequisite may need to change the c1b target
identity contract and/or the c1a provenance model; it must be separately designed and phased. c1d must not silently
broaden a nominal four-file scope to change `historical_input_source_records.py`,
`nar_historical_input_source.py`, or `historical_input_snapshot_builder.py`.

## Future Dedicated Test Plan

After a prerequisite is approved, dedicated tests must cover exact public API; exact supplied response/bundle types;
strict UTF-8; URL-path-only dispatch; canonical URL rejection; target horse identity linkage; rejection of horse-name
matching; target external-entry envelope binding; historical race identity; deterministic provider-record identity;
full required field mapping; direct Decimal parsing with no float; target/future-date exclusion; abnormal states;
missing columns; duplicate history links/identities; identity mismatch; response permutation determinism; exact
observed-at preservation; no clock/network/DB/filesystem/legacy parser/provider dependency; c1a validation/conflict
propagation; and package-root non-export.

If absence is ever proposed, tests must prove full pagination/count/terminal-page coverage and reject every incomplete
or ambiguous zero-result case. Tests must also prove that c1b DebaTable-only records remain insufficient until actual
past evidence is supplied.

## Allowed Files for this PREPARE

    docs/CURRENT_PHASE.md
    docs/LATEST_CODEX_REPORT.md

Production, tests, migration/schema, repositories, providers/parsers, fixtures, database files, logs, README, CLI,
main, and package exports are forbidden. This PREPARE creates a documentation-only review commit and stops for
independent design review; it does not authorize c1d implementation, c1a/c1b extension, stage/commit to the formal
branch, or merge.

## Blockers

blocker: c1b does not retain a verified target-row-to-official-horse identity, and current c1a single-record
canonical URL/timestamp fields cannot faithfully represent the multi-response official identity-and-result evidence
chain. `past_race` is PREREQUISITE_REQUIRED and `past_race_absence` is UNSUPPORTED pending separate approved contracts.
