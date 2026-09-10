# Current Phase

Status: `READY_FOR_REVIEW`

## Identity and scope

- Phase: `POST_V0_8_DAILY_REPLAY_30`
- Name: `Pure Deterministic Strict-Ranking Probability Core`
- Phase type: `IMPLEMENTATION`
- Base Commit: `6881cd86e12bd5c0eb986ff32f40d1f2736901ed`
- Branch: `feature/post-v0.8-daily-replay`
- Implementation outcome: `IMPLEMENTED`
- Phase 29 authority outcome: `SPLIT_REQUIRED`
- Blocking capability: `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`

Phase 30 implements only the approved immutable pure ranking-probability core for `単勝`, `馬連`,
`ワイド`, and `3連複`. It does not implement capture, market odds, EV, strategy, persistence,
migration, replay, settlement, calibration, or scheduling.

## Allowed and forbidden scope

Phase 30 may change exactly:

```text
scripts/prediction/ranking_probability.py
tests/test_ranking_probability.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

All existing prediction/value/generator/strategy/pipeline files, simulation models, repositories,
migrations, official capture/acquisition, payout/settlement, Phase 27/28 files, database/** and
logs/** are forbidden. Stage, commit, and push remain unauthorized.

## Inherited Phase 29 audit findings

- No canonical ranking-probability or calibrated-probability abstraction exists. The only current
  probability transformation is `ValueEngine`'s binary-float softmax, whose constructor default is
  exactly `ValueEngine.DEFAULT_TEMPERATURE == 10.0`.
- `ValueEngine` evaluates only WIN. It labels its softmax output as an uncalibrated provisional
  estimate and multiplies it by `odds_by_horse`. Its legacy raw-input normalization maps a
  non-`int`/`float`, non-finite, or negative score to `0.0`, accepts zero, leaves every positive
  finite score uncapped, rejects duplicate `horse_id`, returns an empty list for an empty field,
  and returns exact binary-float uniform values when all normalized scores are equal. Because
  Python `bool` is an `int`, the legacy helper also accepts bool; that incidental permissiveness is
  not promoted into the new formal input contract.
- `BetGenerator` creates every supported combination but uses
  `factorial(selection_size) * product(individual estimated win probabilities)`, capped at one.
  Combination `expected_value` is always `None`; `combination_score` is the mean of constituent
  WIN expected values. This is a ranking heuristic, not a combination probability or market EV.
- `RuleBasedBetStrategy` admits combination candidates through `min_combination_score`; there is no
  per-bet-type model-EV or probability threshold. `StrategyConfig` schema version 1 and its exact
  fields, including `min_combination_score`, are bound into `strategy_config_hash`.
- `RacePredictionInput.odds_by_horse` and historical `win_odds` contain WIN odds only. The current
  immutable `SimulationBetPlanSnapshot` persists purchased selection, stake, rank, and cutoff, but
  not raw prediction score, model probability, quote evidence, model EV, rejected candidates, or
  decision reason.
- The v008 generic `OddsSnapshotBatch`/repository can represent all four bet types and canonical
  selections with `Decimal`, but it has only `observed_at`, source, optional URL, and a latest-by-
  cutoff lookup. It lacks the complete official response/capture identity and the full causal
  timestamp/path binding required here. The authoritative simulator design already classifies
  existing v008 odds rows as untrusted for official historical input.
- JRA has a byte-preserving official capture path for `FINAL_WIN_ODDS`; NAR target input parses WIN
  odds from its captured race page. Neither provider has a current official prediction-time
  QUINELLA/WIDE/TRIO odds acquisition, normalization, complete-market evidence, or immutable quote
  archive wired into the prediction input.
- `PayoutPublication` and provider payout parsers support the four settlement bet types, but these
  are post-result facts. Both JRA and NAR parsing currently reject known dead-heat representations
  as unsupported. Payouts and final-result pages are forbidden as market-odds substitutes.
- Existing public selection authority is race-scoped `race_entry_id`: WIN has one ID, QUINELLA and
  WIDE two distinct IDs, and TRIO three distinct IDs; unordered selections are ascending tuples.
  Existing prediction `horse_id` currently denotes that race-entry row, but a future adapter must
  make that equivalence explicit once and must never use horse name as identity.

The audit therefore supports an independently implementable pure probability core, but not a
causally valid end-to-end combination EV path. Full EV implementation must wait for explicit
provider market-odds capture.

## Frozen probability model

The first model is a versioned Plackett-Luce strict-ranking model:

```text
model_name    = "plackett_luce"
model_version = "score-softmax-decimal-v1"
event_model   = "strict_finish_order_no_ties_v1"
```

There is exactly one Phase 30 score-to-weight rule. Let the nonempty active race entries be `E`,
sorted by `race_entry_id`. Each accepted `prediction_score` is an exact built-in Python `float`
that is finite and non-negative. Define `v_i = Decimal.from_float(prediction_score_i)`. Let `T` be
the explicitly supplied positive finite `Decimal` temperature and `m = max(v_i)`:

```text
w_i = exp((v_i - m) / T)
W   = sum(i in E, w_i)

P(i1, ..., ik in that exact leading order)
  = product(r=1..k, w_ir / (W - sum(q=1..r-1, w_iq)))
```

All `w_i` are strictly positive. The subtraction by `m` is a numerical stabilization and does not
change the Plackett-Luce distribution. Candidate enumeration and all denominator summation use
ascending `race_entry_id`; permutation enumeration is lexicographic. Phase 30 exposes no alternate
raw-weight input and no caller-selected score normalization, so production cannot choose another
latent-weight meaning ad hoc.

For the same accepted scores and temperature, the intended existing WIN model is the mathematical
temperature-softmax

```text
P_existing_WIN(i) = exp((v_i - m) / T) / sum(j in E, exp((v_j - m) / T))
```

and the Plackett-Luce first-place marginal is, by the definitions above,

```text
P_PL(i finishes first) = w_i / W = P_existing_WIN(i).
```

This is equality of the mathematical model, not a second formula. Phase 30's fixed Decimal
implementation becomes the formal deterministic numerical authority for this model; it does not
claim exact numeric or bitwise equality with every binary-float rounding produced by legacy
`ValueEngine` and `math.exp`. If the two implementations are compared in a regression test, the
legacy-float comparison uses one explicit documented tolerance. Exact equality is required only
among repeated Phase 30 calculations from the same canonical input.
Phase 30 does not modify or call `ValueEngine`, so existing v0.8 behavior remains unchanged. In the
later formally approved integration, one adapter must validate `Prediction.horse_id` as the exact
`race_entry_id`, own the one raw-`Prediction.score` normalization step, pass the one authoritative
configured temperature into this core, and make the formal WIN path consume this core's WIN values.
That adapter must not calculate another softmax or normalize the same raw prediction twice, and the
formal path must not choose between legacy and Phase 30 probability implementations.

### Numeric and canonical contract

- Phase 30 consumes one already-normalized score representation: `prediction_score` is an exact
  built-in Python `float`, finite and `>= 0`. Bool, integers, other numeric types, NaN, infinity,
  and negative values fail closed. There is no artificial upper cap because current `ValueEngine`
  does not cap a positive finite prediction score. Zero is valid and still produces a strictly
  positive weight. Phase 30 does not import `ValueEngine` and does not accept raw `Prediction`
  objects.
- The exact binary64 score is bound by `float.hex()` and converted only by
  `Decimal.from_float(score)`, which preserves that binary64 value exactly and does not consult the
  ambient Decimal context.
- `temperature` has exact runtime type `Decimal`, is finite and `> 0`, and is used at its supplied
  exact value; Phase 30 performs no float/string conversion or implicit defaulting. The existing
  default-temperature compatibility case is supplied explicitly by a future adapter as
  `Decimal.from_float(ValueEngine.DEFAULT_TEMPERATURE)`, exactly `Decimal("10")`. A later
  integration has one temperature authority and may not maintain a separate combination-model
  temperature.
- The module owns one private arithmetic-context template, never exposed or mutated after
  initialization, with `prec=50`,
  `rounding=ROUND_HALF_EVEN`, `Emin=-999999`, `Emax=999999`, `capitals=1`, and `clamp=0`.
  `InvalidOperation`, `DivisionByZero`, and `Overflow` traps are enabled; all other signal traps are
  disabled. Every subtraction, division by temperature, `Decimal.exp`, ordered sum,
  multiplication, denominator subtraction, probability division, partition check, and Decimal
  canonicalization runs inside `decimal.localcontext(the_private_template)`. No arithmetic reads or
  mutates `decimal.getcontext()` directly, and no flags or precision leak between calls.
- A temperature/score combination whose exponent or subsequent arithmetic does not yield finite
  strictly positive weights and finite probabilities under that fixed context fails closed. No
  ambient Decimal context, float probability conversion, locale, clock, random, UUID, or input
  iteration order may influence output.
- Public probabilities and weights are positive finite `Decimal` values. Mathematical partition
  identities equal one; finite-precision tests use the frozen context's explicit tolerance rather
  than silently adjusting a final candidate.
- A zero-entry field fails closed because no strict ranking distribution exists. A one-entry field
  has WIN probability one and produces no impossible multi-entry candidate. Equal-score fields
  produce exactly symmetric weights and probabilities under the frozen context. Duplicate or
  non-positive `race_entry_id` values fail closed. A requested selection containing an unknown ID,
  repeated ID, wrong cardinality, or more entries than the field is impossible and fails closed;
  impossible candidate families are not generated.
- The future integration adapter is the only boundary authorized to normalize raw
  `Prediction.score`. It must explicitly preserve the intended legacy policy before calling Phase
  30: non-numeric or non-finite raw values become `0.0`, negative finite values clamp to `0.0`, and
  finite non-negative values remain uncapped after conversion to built-in float. Formal bool input
  is rejected rather than inheriting Python's incidental `bool`-is-`int` behavior. After migration,
  neither `ValueEngine` nor any second adapter may independently normalize or softmax the same raw
  predictions on the formal production path. Implementing that adapter/refactor is a later reviewed
  integration phase, not Phase 30.
- Canonical SHA payloads use NFC text, sorted object keys, UTF-8, `ensure_ascii=False`,
  `allow_nan=False`, compact separators, no trailing LF, authoritative tuple order, and lowercase
  SHA-256. Decimal text is `format(value.normalize(frozen_context), "f")` (with exact zero encoded
  as `"0"`), so exponent notation and representational trailing zeros are not identity inputs.

### Exact bet events

For distinct canonical race-entry selections:

```text
WIN {i}
  P_win(i) = w_i / W

QUINELLA {i,j}
  P_quinella({i,j}) = P(i,j) + P(j,i)

TRIO {i,j,k}
  P_trio({i,j,k}) = sum(P(pi) for pi in all 6 permutations of (i,j,k))

WIDE {i,j}
  P_wide({i,j})
    = sum(P(pi) for h in E excluding {i,j}
                 for pi in all 6 permutations of (i,j,h))
```

Thus WIDE is joint inclusion of both chosen entries in the first three positions of a strict
no-tie ranking, not the QUINELLA formula and not a product heuristic. For every `h` distinct from
`i,j`, the six enumerated orders are exactly the ordinary top-three outcomes containing the chosen
pair and that third entry; no tie event is included. WIN and QUINELLA require at least one and two
modeled entries respectively; WIDE and TRIO require at least three. A mathematical probability does
not authorize sale: JRA WIDE sale requires a field of at least four at sale opening, and provider
market availability plus an exact market quote remain separate requirements.

The candidate identities are exactly:

- WIN: one positive `race_entry_id`;
- QUINELLA: two distinct IDs, ascending;
- WIDE: two distinct IDs, ascending;
- TRIO: three distinct IDs, ascending.

Wrong cardinality, duplicate IDs, an ID outside the modeled universe, unsupported type, or an
impossible field size fails closed. Results are ordered by the fixed bet-type order
`単勝`, `馬連`, `ワイド`, `3連複`, then selection tuple. WIN, QUINELLA, and TRIO form unit-mass
partitions where defined; the sum of all WIDE pair probabilities is three because every strict
top-three outcome contains three winning pairs.

### Official WIDE and dead-heat boundary

JRA and NAR describe WIDE as the unordered pair among 1st/2nd, 1st/3rd, or 2nd/3rd. JRA publishes
WIDE only when at least four entries exist at sale opening; NAR notes that offered wager types can
vary by racecourse. Sale eligibility is therefore provider-market evidence, not a probability-core
inference. Both official descriptions state that a pair consisting only of two horses tied for
third is not winning.

Plackett-Luce v1 assigns probability only to strict total orders: tie/dead-heat event probability is
not represented and no pseudo-probability or tie adjustment may be added. Its QUINELLA, TRIO, and
WIDE values are therefore `model_probability` conditional on the frozen strict no-tie ranking
model. They are the ordinary-order event sums above, not a complete empirical model of official
dead-heat settlement. In particular, official JRA/NAR WIDE rules do not award a pair consisting
only of the two horses tied for third; Phase 30 neither models that tie nor moves its mass into an
ordinary-order event. Settlement continues to consume independently recorded official results and
payouts. Any tie-capable probability model requires a new model/event version and a separately
reviewed design. Displayed odds can also differ from an actual dead-heat payout, so v1 must not
claim a fully actuarial dead-heat-adjusted return.

## Implemented probability API

`scripts/prediction/ranking_probability.py` exposes exactly:

```python
@dataclass(frozen=True, slots=True)
class RaceEntryModelScore:
    race_entry_id: int
    prediction_score: float
    prediction_score_float_hex: str = field(init=False)

@dataclass(frozen=True, slots=True)
class RaceEntryLatentWeight:
    race_entry_id: int
    latent_weight: Decimal

@dataclass(frozen=True, slots=True)
class BetSelectionModelProbability:
    bet_type: str
    race_entry_ids: tuple[int, ...]
    model_probability: Decimal

@dataclass(frozen=True, slots=True)
class PlackettLuceBetProbabilitySet:
    schema_version: int
    model_name: str
    model_version: str
    event_model: str
    temperature: Decimal
    entry_scores: tuple[RaceEntryModelScore, ...]
    latent_weights: tuple[RaceEntryLatentWeight, ...]
    probabilities: tuple[BetSelectionModelProbability, ...]
    probability_content_sha256: str = field(init=False)

def calculate_plackett_luce_bet_probabilities(
    *,
    entry_scores: Sequence[RaceEntryModelScore],
    temperature: Decimal,
) -> PlackettLuceBetProbabilitySet:
    ...
```

`schema_version` is exactly 1. Construction is immutable and derives all weights, candidate
probabilities, and `probability_content_sha256`; callers cannot inject trusted derived fields.
The public result constructor rejects ordinary direct construction; the calculation function is the
sole trusted factory and validates/recomputes every derived child before returning.
`probability_content_sha256` uses version
`formal-bet-probability-plackett-luce-v1` and binds every model/input/output semantic field.
No quote, EV, strategy, stake, network, database, or current clock enters this pure API.

## Probability and EV terminology

- `model_probability` is the uncalibrated output of the frozen strict no-tie ranking model. Every
  use must preserve that qualifier; it is neither tie-adjusted nor a complete empirical official-
  settlement probability. It is never named or represented as `calibrated_probability`.
- `calibrated_probability` is reserved for a later empirical calibration model carrying its own
  version, training-data identity, target commit, fit cutoff, and out-of-sample validation. It is
  absent in the first implementation.
- Once a valid quote exists, `model_expected_value_ratio = model_probability * market_decimal_odds`.
  Example: `Decimal("0.082") * Decimal("15.8") = Decimal("1.2956")`.
- The ratio 1 is break-even gross return; it corresponds to 100 percent gross return, not 100
  percent profit. No percent conversion is stored in this field.
- Because its probability is uncalibrated and its quoted dividend may change under dead heat,
  `model_expected_value_ratio` is a model-implied quote value ratio, not a validated profit claim.
  An API or policy requiring calibrated EV must fail closed until calibration evidence exists.
- Legacy `estimated_probability`, `expected_value`, and `combination_score` retain their v0.8
  meanings. They must not be silently reinterpreted. A later integration uses a new explicit
  candidate value rather than changing these fields in place.

## Prediction-time market quote contract

The market-odds phase must define one immutable complete market snapshot and exact quote values.
Each quote/snapshot identity must bind at least:

- schema and collector contract versions;
- `organization` (`JRA` or `NAR`) and exact `source_system`;
- internal `race_id`, provider `external_race_id`, bet type, and canonical `race_entry_ids`;
- positive finite `market_decimal_odds: Decimal`;
- optional provider `available_at`, plus `observed_at`, `captured_at`, explicit
  `information_cutoff`, and `scheduled_start_at` in UTC microseconds;
- exact request identity, canonical source URL, response capture ID, response SHA-256, and complete
  market-snapshot content SHA-256;
- the complete active entry universe, market offered/status fact, and complete expected-versus-
  observed selection coverage for that provider/race/bet type.

Required causal relation is:

```text
available_at <= observed_at <= captured_at <= information_cutoff <= scheduled_start_at
```

where `available_at` may be `None` only under a separately approved observed-only provider policy.
No timestamp is inferred from current time, DB insertion, file mtime, race date, result, or payout.
Historical replay must receive an exact snapshot identity already linked to its prediction input;
it cannot call a latest lookup or substitute closing/current odds. Missing, incomplete, unsupported,
future-dated, mismatched, or corrupt quote evidence makes that candidate unsupported/no-EV and may
make the strategy fail closed according to its explicit policy. There is no fallback to WIN odds,
`combination_score`, settlement payout, or another bet type's quote.

The existing v008 `OddsSnapshotBatch` is not this authority and is not retroactively promoted.
Provider capture design must first freeze the real JRA and NAR request/response grammar, sale-state
rules, completeness, body archive ownership, and exact timestamp source.

## Strategy, BUY/SKIP, and allocation boundary

The responsibility sequence remains:

```text
prediction score -> model probability -> exact market quote -> model EV ratio
                 -> strategy BUY/SKIP eligibility -> stake allocation
```

The probability/EV calculator never chooses BUY or stake. A future formal-EV strategy configuration
must explicitly bind:

- probability basis (`model_uncalibrated_v1`; calibrated variants require separate evidence);
- allowed bet types;
- a complete per-bet-type minimum model-EV-ratio map;
- optional per-bet-type minimum model-probability map;
- maximum candidates/bets and deterministic sort/tie-break policy; and
- existing allocation-policy identity.

No example threshold is frozen as a default. Exact threshold comparison is inclusive (`>=`) and a
strategy may legitimately produce zero bets. Missing quote/EV can never pass the threshold.

Adding these fields to current `StrategyConfig` would change its hash. The existing schema-version-1
payload and every persisted v0.8 strategy identity must remain reproducible. A later integration
must introduce a version-dispatched strategy-config schema version 2 (or return for review if the
actual implementation requires a different compatibility mechanism), retain v1 loading/hashing,
and bind probability model/version, quote contract, threshold maps, and decision sort policy into
the new hash. It must remove `combination_score` as a formal BUY authority without altering legacy
v1 behavior.

## Prediction-decision persistence boundary

The current v009 bet-plan snapshot is insufficient as a full prediction-time decision audit: it
stores only purchased bets. A later, separately reviewed immutable snapshot must preserve every
evaluated candidate, including raw score/model identity, model probability, exact quote identity
and odds, model EV ratio or explicit unavailability, BUY/SKIP decision and reason, rank, and chosen
stake. It must distinguish an unsupported/no-quote candidate from an intentional below-threshold
SKIP and from a purchased zero-return outcome.

No v009 row is rewritten or inferred, and no migration is included in the probability-core phase.
Schema/version and append-only conflict semantics belong to the later decision-evidence persistence
phase. Phase 27/28 replay-result persistence and aggregation remain unchanged and must not feed back
into prediction, calibration, value, or strategy inputs.

## Required phase split

1. **Phase 30 — Formal Plackett-Luce Bet Probability Core Implementation.** Completed within the
   immutable pure probability API/formulas above; the current pipeline and v0.8 behavior remain
   unchanged.
2. **Phase 31 — Prediction-Time Combination Market Odds Capture Design.** Audit and freeze JRA and
   NAR provider request grammar, complete-market semantics, sale availability, causal timestamps,
   capture/archive/database ownership, and exact quote API. This is a design gate; provider-specific
   implementations may need separate phases.
3. **Later approved capture implementation phase(s).** Implement byte-exact official acquisition,
   normalized complete quote snapshots, immutable persistence, exact-ID reload, and historical
   snapshot linkage. No EV integration precedes both provider and causal contracts required by its
   declared scope.
4. **Later formal EV and strategy-v2 integration phase.** Join the probability set to exact
   race-entry quote identities, calculate `model_expected_value_ratio`, create explicit candidate
   values, and apply the versioned strategy BUY/SKIP policy before existing allocation.
5. **Later prediction-decision evidence persistence phase.** Persist the immutable candidate and
   decision audit without changing Phase 27/28 result layers or creating outcome feedback.
6. **Later calibration phase.** Only validated empirical calibration may introduce
   `calibrated_probability` and calibrated-EV terminology.

No scheduler is part of Phase 29/30. Future T-5 operation supplies an explicit cutoff equal to the
approved scheduled start minus five minutes; no engine samples a wall clock.

Exact enumeration is practical at normal race size: QUINELLA is `O(n^2)`, and WIDE/TRIO are
`O(n^3)` with constant six-permutation work. Phase 30 uses no Monte Carlo, sampling, approximation,
or factorial-product shortcut.

## Exact Phase 30 Allowed Files

Phase 30 may modify exactly:

```text
scripts/prediction/ranking_probability.py
tests/test_ranking_probability.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

All existing prediction/value/generator/strategy/pipeline files, simulation models, repositories,
migrations, official capture/acquisition, payout/settlement, Phase 27/28 files, database/** and
logs/** remain unchanged. The implementation stayed within these four files.

## Required Phase 30 tests

The dedicated suite must prove:

1. exact public names/signatures, frozen dataclasses, derived-field construction, schema/model/event
   versions, and deterministic content SHA;
2. strict score/temperature/identity validation, input-order independence, ascending canonical
   entries, canonical selection arities, no duplicate candidates, and impossible selections;
3. hand-computable two-entry WIN values and QUINELLA probability one;
4. exact equality of each PL first-place value to `w_i / sum(w)` and mathematical equality to the
   frozen intended WIN softmax for identical accepted scores/temperature, including the existing
   default-temperature case; any direct legacy `ValueEngine` float comparison uses the one explicit
   test tolerance and makes no bitwise-equality claim;
5. exact ordered-prefix formula, QUINELLA two-order sum, TRIO six-order sum, and WIDE top-three
   joint-inclusion enumeration; WIDE differs from QUINELLA in an eligible four-entry fixture;
6. symmetry under input/candidate permutation, every probability in `[0,1]`, WIN/QUINELLA/TRIO
   unit partition mass at frozen Decimal tolerance, and WIDE total mass three;
7. the exact private Decimal context is used for every arithmetic/canonicalization step; repeated
   calls are exactly identical, and changing ambient precision and rounding to materially different
   values leaves every weight, probability, ordering, and content SHA exactly unchanged;
8. stable exact score conversion, exact temperature handling, equal-score symmetry, zero-score
   validity, empty/impossible-field rejection, no float probability/weight output, no NaN/infinity,
   no locale dependence, and semantic change changes content SHA;
9. the public core exposes no raw-weight alternate authority; duplicate identities are rejected;
   the model exposes no dead-heat/tie pseudo-probability and imports no official settlement logic;
10. no market quote, EV, strategy, allocation, persistence, SQL, migration, network, current clock,
   random, UUID, Monte Carlo, settlement, or payout behavior in the new module;
11. existing `ValueEngine`, including its default-temperature WIN regression, `BetGenerator`,
   `BetStrategy`, pipeline, selection normalization,
   Phase 27/28, settlement, and full-suite regressions remain unchanged.

Later market/EV/strategy tests must additionally cover exact quote-by-bet-type matching, complete
coverage, malformed odds, cutoff violations, payout masquerading, no combination-score fallback,
threshold BUY/SKIP/boundary behavior, zero bet, strategy v1 hash stability/v2 determinism, and
prediction-decision evidence persistence. They are not Phase 30 implementation scope.

The final-review finite-precision correction preserves the approved precision-50
`ROUND_HALF_EVEN` model. Each ordered prefix now rebuilds its denominator from the authoritative
remaining-weight set, avoiding cancellation from iterative subtraction, and validates the ordered
term independently. A complete event may canonicalize a result just above one to exact
`Decimal(1)` only inside the deterministic forward-error envelope
`gamma(n) = n*u/(1-n*u)`, where `u = 10**(1-precision)` and `n` is the conservative count of
remaining-weight additions, divisions, products, and event-sum additions. Non-complete events and
excess beyond that derived envelope still fail closed; there is no unconditional clamp.

## Verification result

```text
Dedicated Phase 30 with ResourceWarning-as-error: 24 passed
Phase 25/27/28 regression: 73 passed
Prediction/value/generator/strategy/pipeline/selection/settlement regression: 106 passed
Full unittest discovery: 3,168 passed
Python compilation and static boundary checks: passed
```

The dedicated and focused related suites are warning-clean. Full discovery emits only the existing
unrelated unclosed-SQLite `ResourceWarning` class already recorded before Phase 30. Static AST and
source checks confirm the new production module has no ValueEngine, generator, strategy,
settlement, payout, database, repository, network, clock, random, UUID, market-odds, or EV
dependency. The only text match for settlement is the module docstring describing its absence.

## Stop condition

Phase 30 stops at `READY_FOR_REVIEW`. No stage, commit, push, Phase 31 preparation, provider
acquisition, market-odds integration, or strategy integration is authorized. End-to-end combination
EV remains split behind `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE`; this is not a blocker to
reviewing the completed pure probability core.
