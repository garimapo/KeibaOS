# Current Phase

## Status

DRAFT_FOR_REVIEW

## Phase

Phase 4C-2d3b1i6c1d3 — Historical past-race result-field contract preparation

## Base Commit and Branch

Formal base: `2b6d389b4296be2f6749b71fc4ed827f244ce570 feat: preserve NAR target horse identity`

Formal branch: `feature/ver0.8-simulator`

Preparation review branch: `review/4c-2d3b1i6c1d3-prepare`

Canonical workspace: `C:\Users\garim\Desktop\KeibaAI-review-1i5b2b`

The original workspace, `C:\Users\garim\Desktop\KeibaAI`, is read-only.

## Objective and Non-goals

d3 freezes the smallest provider-neutral contract for a historical past race from supplied official NAR responses.
It resolves race-name/class semantics, margin semantics, fourth-corner derivation, and whether one logical record
needs multiple immutable evidence responses. It does not implement production, tests, a schema, a migration, a
normalizer, a parser, an HTTP client, an absence proof, or a package export.

All future evidence is caller-supplied captured bytes. No page's later current state proves what was available at a
historical prediction cutoff. Each contributing response must have its own caller-supplied `observed_at`, and every
such timestamp must be no later than both snapshot `captured_at` and `information_cutoff`.

## Actual Repository Consumers and Current Asymmetry

The following are the actual production uses found by repository-wide search:

| field | actual consumers | current semantic behavior |
| --- | --- | --- |
| `race_name` | c1a validation/digest, historical snapshot canonical payload, SQLite snapshot repository, c1c builder, legacy database/model pass-through | no direct AbilityEngine, PaceEngine, TrackEngine, or Predictor field read was found |
| `race_class` | same persistence/digest/builder path; `AbilityEngine._class_score` | NFKC/uppercase string matching of G/Jpn/OP/A/B/C-like labels; unknown strings receive neutral 50 |
| `margin` | same persistence/digest/builder path; `AbilityEngine._margin_score` | finite positive scalar only; score is `100 - margin * 20`; zero/nonpositive/nonfinite is neutral 50 |
| `passing_order` | same persistence/digest/builder path; `PaceEngine` fallback | legacy regex/final-token fallback guesses a late corner; it is not authoritative evidence |
| `fourth_corner_position` | same persistence/digest/builder path; `PaceEngine` | positive explicit value is preferred for running-style calculation; zero means unavailable |

`SimulationRaceInput` construction and the historical snapshot SQLite repository only validate, persist, reconstruct,
and digest these fields. Predictors consume AbilityEngine/PaceEngine outputs rather than these fields directly.
TrackEngine has no direct consumer of these past-race fields. `scripts/models.py`, `database.py`,
`fetch_past_races.py`, and `scripts/parsers/past_race_parser.py` are legacy ingestion/model paths, not authority
for this new historical evidence boundary.

The target `HistoricalRaceSnapshot` permits `race_name: str | None` and `race_class: str | None` because target
DebaTable evidence can legitimately lack separate semantic values. `HistoricalPastRaceSnapshot` and c1a past-race
records require both nonempty strings because a historical record otherwise cannot support the established immutable
feature/audit payload. This asymmetry is justified for the supported NAR subset: HorseMarkInfo exposes provider-
separated nonempty `競走名` and `格組` columns. d3 keeps both past-race fields required; a page missing either is
unsupported rather than turning the fields optional.

## Official Source Semantics

| official response | verified useful semantics | limits | d3 role |
| --- | --- | --- | --- |
| HorseMarkInfo, bound by d1 lineage ID | `年月日`, `競馬場`, `R`, `競走名`, `格組`, distance, weather/condition, finish, race time, `差`, weight, jockey; race-name cells link to historical RaceMarkTable | no historical win odds, detailed passing sequence, or page-level corner labels | primary source for race name, race class, and official reference time difference |
| CompeteTable, target-entry historical cells | historical `競走名`, `格組`, race facts and a direct NAR description of the displayed `差` as a time difference | bounded last-N target-page display; no full RaceMarkTable result facts or complete history | semantic cross-check only; not a required evidence page |
| RaceMarkTable, canonical historical race URL | exact historical race identity, row-local d1 lineage identity, result-row finish/time/weight/jockey/popularity/win odds/passing sequence and page corner labels | its h3 is not a reliable split into race_name/race_class; its `着差` is a different finish-margin display concept | primary source for identity, odds, passing order, and corner derivation |
| DebaTable embedded prior-run cells | may show compact prior-run display | no proven complete field or identity/provenance contract | not an authority for a complete record |

HorseMarkInfo is bound only through the target `external_horse_id = nar:horse:{k_lineageLoginCode}`; horse-name
matching is forbidden. A historical result joins only when the HorseMarkInfo historical race link and RaceMarkTable
canonical race identity agree on provider-native date, baba/place identity, and race number, and the RaceMarkTable row
contains exactly the same d1 lineage identity. Date plus race name, date plus place, horse number, or horse name alone
cannot join the evidence.

## Race Name and Race Class Decision

`race_name` is the exact NFC provider value in HorseMarkInfo's `競走名` column. It is the official race display/name
field even when it includes class-like wording; d3 does not require a human-only proper name. `race_class` is the exact
NFC provider value in the separately labelled HorseMarkInfo `格組` column. CompeteTable supplies a secondary semantic
cross-check only. RaceMarkTable h3, subtitle, sponsor text, and regex stripping are not sources for either field.

Both fields remain required for the initial supported flat-NAR subset. Missing/blank/ambiguous columns fail closed.
AbilityEngine may score a provider `格組` string only through its current unknown-neutral behavior; no historical
evidence text may be translated merely to fit the scorer. A later feature-normalization layer, not a source normalizer,
owns any scoring representation change.

## Margin / Time-difference Decision

RaceMarkTable `着差` and HorseMarkInfo/CompeteTable `差` are distinct official concepts. RaceMarkTable displays
finish-margin text such as fractions or Japanese labels and has a blank winner cell. HorseMarkInfo/CompeteTable
describe `差` as the time difference to first place for non-winners and to second place for a winner. The latter is a
direct official numeric value but is not a signed deficit to the winner.

The legacy `PastRaceParser` mappings of Japanese finish-margin labels to constants, fraction parsing, fallback zeros,
and float conversion are **UNTRUSTED_FOR_HISTORICAL_EVIDENCE**. Legacy fourth-corner guessing and NFKC/default repair
are equally non-authoritative.

Current `margin` has no precise provider-neutral domain contract: AbilityEngine merely treats a small positive scalar
as generic closeness. It cannot establish that a horse-length finish margin and an official reference time difference
are interchangeable. Therefore:

- `MARGIN_CURRENT_MEANING = generic positive numeric closeness; unit not defined by current domain`.
- `OFFICIAL_TIME_DIFFERENCE_SEMANTICS = direct Decimal reference_time_difference_seconds`, compared with first place
  for non-winners and second place for winners.
- `MARGIN_DOMAIN_CHANGE_REQUIRED = YES`.

The proposed domain replacement is `reference_time_difference_seconds: Decimal`, direct-parsed without float, finite
and nonnegative (zero is valid if officially displayed). Blank/abnormal/unavailable values are unsupported. d3 does not
preserve RaceMarkTable finish-margin text because no current approved feature/audit field needs it; adding a text field
would be unnecessary domain expansion. A later feature contract must decide whether and how the existing ability score
uses the new unit. No source normalizer may populate legacy `margin` from either official concept.

## Passing Order and Fourth Corner Decision

`passing_order` remains the exact NFC row-local RaceMarkTable display string for audit preservation.
`FOURTH_CORNER_MAPPING = NOT_YET_PROVEN`. A future supported page may derive the existing integer field without a
domain change only where the same response proves the mapping:

- page labels `[1, 2, 3, 4]` and row positions `[a, b, c, d]` yield fourth corner `d`; or
- page labels `[3, 4]` and row positions `[a, b]` yield fourth corner `b`.

The page-level `section.cornerPassTable` labels and the row-local sequence must be present, count-compatible, and
unambiguous. Absence, mismatch, an absent corner 4, or ambiguity fails closed. Row length, the final token, course or
distance lookup, and legacy parser/PaceEngine fallback cannot prove a corner. Thus
`FOURTH_CORNER_DOMAIN_CHANGE_REQUIRED = NOT_YET_PROVEN`; retain `int` if the supported subset proves corner 4,
and consider optionality only after a separate downstream PaceEngine contract review.

## One-response versus Multi-response Evidence

No one inspected official response contains all semantically correct fields for a complete future past-race record.
HorseMarkInfo/CompeteTable provide separate race-name/class and reference-time-difference semantics but do not provide
RaceMarkTable's historical odds, detailed passing sequence, row identity, and corner evidence. RaceMarkTable provides
those result facts but cannot authoritatively split its h3 into race_name and race_class and supplies a different margin
concept.

Therefore:

- `SINGLE_RESPONSE_COMPLETE_SOURCE = NO`.
- `MULTI_RESPONSE_EVIDENCE_REQUIRED = YES`.
- `C1A_PROVENANCE_EXTENSION_REQUIRED = YES`.

A logical record must preserve at least two factual evidence references: (1) HorseMarkInfo for explicit name/class and
reference time difference and (2) RaceMarkTable for exact historical race/horse identity, odds, passing order, and
corner facts. CompeteTable is optional semantic cross-check and must not affect the digest merely by being viewed.

The current single `canonical_source_url` / `observed_at` / `available_at` on HistoricalInputSourceRecord cannot
truthfully represent this record. The smallest candidate architecture is an immutable provider-neutral
`HistoricalInputEvidenceRef` tuple owned by c1a, with canonical URL, exact observed/available timestamps, and a
closed evidence role. Its canonical identity must include only the two fact-proving references in deterministic role
order; it changes when any fact-contributing reference identity changes and excludes navigation-only pages. One record
must not collapse distinct observations into a fake timestamp.

Component records would burden c1c with provider assembly and expand record kinds; a separate external evidence bundle
would duplicate c1a digest/audit responsibility. Both are rejected pending the narrower evidence-reference contract.
The evidence model must let c1c enforce every reference timestamp against capture and cutoff.

## Domain, Schema, and Repository Impact

Field-domain change and evidence-reference change are separate prerequisites. Neither is authorized here.

A future field-domain implementation would affect exactly:

- `scripts/simulation/historical_input_source_records.py`
- `scripts/simulation/historical_input_snapshots.py`
- `scripts/simulation/historical_input_snapshot_builder.py`
- `scripts/simulation/repositories/sqlite_historical_input_snapshot_repository.py`
- `scripts/migrations/versions/v011_historical_past_race_field_contract.py`
- `scripts/migrations/runner.py`
- their dedicated source-record, snapshot, builder, repository, and migration tests
- `docs/CURRENT_PHASE.md` and `docs/LATEST_CODEX_REPORT.md`.

The currently formal v010 schema persists `margin`, title fields, and fourth-corner integer in immutable snapshot
rows. The migration runner registers ordered applied versions and rejects name mismatch; v010 must not be rewritten.
The correct future schema path is append-only v011, even if a development database happens to contain no snapshot rows.
Legacy `scripts/models.py`, legacy SQLite `past_races`, AbilityEngine, PaceEngine, and their tests are not
authorized as part of the historical field-domain phase; they need an explicit later feature/adapter contract.

A subsequent evidence-reference phase will overlap c1a, c1c, snapshot domain, v011-or-later schema/repository, and
their tests. It must first decide whether the domain change's v011 should include the evidence table/reference shape or
whether an additional append-only v012 is required; this d3 PREPARE does not collapse those decisions.

## Recommended Prerequisite Order and Future Scope

Outcome: **D — both field-domain and provenance changes are required**.

1. **Phase 4C-2d3b1i6c1d3a — Historical past-race field-domain contract implementation**: replace ambiguous
   `margin` with `reference_time_difference_seconds` in the historical source/snapshot path and append v011.
2. **Phase 4C-2d3b1i6c1d3b — Historical multi-source evidence/provenance contract preparation**: freeze immutable
   evidence references, digest identity, timestamp eligibility, and append-only persistence design.
3. Only then return to c1d provider-normalizer PREPARE.

Future Allowed Files for d3 itself are exactly:

- `docs/CURRENT_PHASE.md`
- `docs/LATEST_CODEX_REPORT.md`

No production/test/migration Allowed Files are authorized until d3a or d3b is separately prepared and approved.

## Blockers and Stop Condition

Blockers are: approved field-domain implementation for reference time difference; approved multi-source evidence
provenance representation; an exact same-page RaceMarkTable corner-label/row-position proof; and a later explicit
feature contract before AbilityEngine/PaceEngine consumes changed historical semantics.

No production, test, fixture, schema, migration, database, provider, parser, CLI, README, package export, log, or
original-workspace change is authorized. Stop at `DRAFT_FOR_REVIEW` for ChatGPT design review.

blocker: historical past-race field domain and multi-source evidence provenance must be separately approved before any
NAR past-race normalizer can be designed or implemented.
