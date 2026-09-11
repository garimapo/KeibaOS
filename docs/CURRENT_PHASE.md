# Current Phase

Phase: `POST_V0_8_DAILY_REPLAY_40`
Name: `Pure Deterministic NAR Market Odds Source Parser Implementation`
Type: `IMPLEMENTATION`
Status: `READY_FOR_REVIEW`
Outcome: `SPLIT_REQUIRED`
Base: `dfa9802644668bac9f5863099604b8bcb9713b52`
Branch: `feature/post-v0.8-daily-replay`

## Authority and boundary

Phase38 is formally complete. The integrated source-profile fixture authority is `nar-market-odds-source-profile-fixture-set-v1:14c2ecdbe85ac1f673c015643eabd7d757d971c85cd60599d7dd6c576926e470`. The eight exact raw fixtures are grammar fixtures only: they are not replay, T-5, prediction, EV, strategy, or settlement evidence.

Phase40 implements the newly approved Phase39 design; the old Phase33 draft remains superseded. Phase34's source-state fixture blocker is resolved/superseded. `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE` remains open.

Authority: Phase39 `DESIGN_APPROVED`. WIN is the complete `table.odd_popular_table_02` source; each combination family is one complete `ul.odd_ranking` with its partitioned `table.odd_ranking_table` children. The `formation_*` tables are horse-selection controls, not quote authorities.

Phase40 is a pure boundary only:

```text
exact Phase32 NARMarketOddsResponseCapture
  -> state/profile validation and source quote extraction
  -> immutable provider-horse-number evidence
```

It has no network, clock, filesystem, database, archive, manifest runtime lookup, persistence, replay resolver, cutoff, scheduled start, availability decision, entry mapping, probability, EV, strategy, settlement, scheduler, or JRA behavior.

## Exact qualified source grammar

All eight bodies are strict UTF-8. There must be exactly one root:

```text
article.raceCard > div.innerWrapper > div#odd_content
```

and exactly one state heading:

```text
article.raceCard > div.innerWrapper > div#odd_content > div.odd_header > h4.odd_title
```

For heading comparison only, replace every nonempty run of ASCII `SP`, `HT`, `CR`, `LF`, `FF`, and `VT` with one ASCII `SP`, then remove ASCII whitespace from both ends. Do not normalize Unicode; U+3000 is significant. The normalized title must full-match exactly one value in this table and the capture page kind must agree.

| Page kind | Family title | OPEN suffix | FINAL suffix |
| --- | --- | --- | --- |
| `ODDS_TAN_FUKU` | `単勝・複勝　オッズ` | ` （HH:MM 現在）` | ` （最終）` |
| `ODDS_UM_LEN_FUKU` | `馬連複　オッズ` | ` （HH:MM 現在）` | ` （最終）` |
| `ODDS_WIDE` | `ワイド　オッズ` | ` （HH:MM 現在）` | ` （最終）` |
| `ODDS_3_LEN_FUKU` | `三連複　オッズ` | ` （HH:MM 現在）` | ` （最終）` |

`HH:MM` is ASCII and matches `(?:[01][0-9]|2[0-3]):[0-5][0-9]`. OPEN retains the exact diagnostic text `HH:MM 現在`; FINAL retains no display-time text. It is never combined with a date and is never `available_at`. Missing, duplicate, mixed, unrecognized, or wrong-family headings fail closed.

Attribute order, class-token order, comments, and unrelated nodes outside required containers are harmless. Missing/duplicate authoritative containers, hidden alternate quote data, unexpected required row/cell structure, or semantic ambiguity fail closed. There is no whole-document regex or fallback selector.

The Phase40 review found that node-local visibility checks could accept a hidden state heading or a WIN authority beneath a hidden ancestor. The corrected parser validates each authoritative state heading and quote-container node together with every ancestor through and including the exact `div#odd_content` market root. It rejects the boolean `hidden` attribute, ASCII-trimmed case-insensitive `aria-hidden="true"`, and case-insensitive inline `display: none` or `visibility: hidden` declarations with narrowly tolerated ASCII whitespace. It does not implement a CSS engine, inspect external stylesheets, infer hidden state from class names, or walk beyond the approved market root. Existing row/cell visibility checks remain fail closed.

### Quote-container authority

| Page kind | Exactly one authoritative source | Key and odds facts | Explicitly non-authoritative |
| --- | --- | --- | --- |
| `ODDS_TAN_FUKU` | `div#odd_content table.odd_popular_table_02` | one `tbody`; direct row has 13 `td`; cell 2 is horse number and cell 4 is scalar WIN odds; header facts 1–4 are `枠`, `馬番`, `馬名`, `単勝 オッズ` | frame, horse name, PLACE cells 5–6, jockey/weight/change fields, controls |
| `ODDS_UM_LEN_FUKU` | `div#odd_content > ul.odd_ranking` | its direct `li.odd_ranking_item > table.odd_ranking_table` descendants are partitions of one market; rows are `組合せ`, `オッズ`, `人気`; data cells are pair key/scalar odds/popularity | `table#formation_renfuku.odd_table`, sort/control UI, popularity |
| `ODDS_WIDE` | `div#odd_content > ul.odd_ranking` | same partition structure; second cell is direct lower token, literal `br`, ASCII-hyphen upper token; always a range | `table#formation_quinella.odd_table`, popularity, midpoint/scalar conversion |
| `ODDS_3_LEN_FUKU` | `div#odd_content > ul.odd_ranking` | same partition structure; first cell triple key; second cell scalar odds | `table#formation_trio.odd_table`, popularity, controls |

For ranking-table pages, each table has exactly one direct header row containing `組合せ`, `オッズ`, `人気` and direct data rows with exactly three `td`. WIDE accepts only surrounding ASCII whitespace around its direct child sequence; no nested endpoint tag, alternate dash, text merge, or second `br` is accepted. The qualified fixtures establish no unavailable, suspended, cancelled, maintenance, scratch-special, or placeholder grammar; every such state/profile is unsupported rather than synthetic/incomplete usable evidence.

## Implemented public API

Production module: `scripts/simulation/nar_market_odds_source_parser.py`.

```python
class NARMarketOddsSourceState(StrEnum):
    OPEN = "open"
    FINAL = "final"


class NARMarketOddsSourceCompleteness(StrEnum):
    UNVERIFIED = "unverified"


class NARMarketOddsSourceQuoteKind(StrEnum):
    EXACT = "exact"
    RANGE = "range"


class NARMarketOddsSourceParseError(Exception):
    pass


class NARMarketOddsSourceParseValidationError(NARMarketOddsSourceParseError):
    pass


class NARMarketOddsSourceParseUnsupportedError(NARMarketOddsSourceParseError):
    pass


class NARMarketOddsSourceParseDataError(NARMarketOddsSourceParseError):
    pass


class NARMarketOddsSourceParseNumericError(NARMarketOddsSourceParseDataError):
    pass


@dataclass(frozen=True, slots=True)
class NARMarketOddsExactQuote:
    selection: tuple[int, ...]
    exact_odds: Decimal
    quote_kind: NARMarketOddsSourceQuoteKind = field(
        init=False, default=NARMarketOddsSourceQuoteKind.EXACT,
    )


@dataclass(frozen=True, slots=True)
class NARMarketOddsRangeQuote:
    selection: tuple[int, ...]
    lower_odds: Decimal
    upper_odds: Decimal
    quote_kind: NARMarketOddsSourceQuoteKind = field(
        init=False, default=NARMarketOddsSourceQuoteKind.RANGE,
    )


NARMarketOddsSourceQuote = NARMarketOddsExactQuote | NARMarketOddsRangeQuote


@dataclass(frozen=True, slots=True)
class NARMarketOddsSourceEvidence:
    page_kind: NARMarketOddsPageKind
    race_identity: NARMarketOddsRaceIdentity
    request_identity: str
    request_identity_sha256: str
    canonical_request_url: str
    capture_id: str
    response_sha256: str
    response_byte_length: int
    requested_at: datetime
    observed_at: datetime
    captured_at: datetime
    source_state: NARMarketOddsSourceState
    provider_display_as_of_text: str | None
    source_completeness: NARMarketOddsSourceCompleteness
    provider_horse_numbers: tuple[int, ...] | None
    quotes: tuple[NARMarketOddsSourceQuote, ...]

    schema_version: int = field(init=False, default=1)
    organization: str = field(init=False, default="NAR")
    source_system: str = field(init=False, default="keiba.go.jp")
    parser_name: str = field(init=False, default="nar-market-odds-source-parser")
    parser_version: str = field(init=False, default="v1")
    evidence_content_sha256: str = field(init=False)
    evidence_id: str = field(init=False)


def parse_nar_market_odds_source_capture(
    *,
    capture: NARMarketOddsResponseCapture,
) -> NARMarketOddsSourceEvidence:
    ...
```

This is the entire public parser surface. It accepts no arbitrary HTML/bytes/URL/page kind/target/universe input. It requires an exact Phase32 capture, safely reads all required fields, and re-constructs the same `NARMarketOddsResponseCapture` through Phase32 before decoding. Malformed or forged capture state raises `NARMarketOddsSourceParseValidationError`, never a raw attribute or library exception. It uses the existing dependency exactly as `BeautifulSoup(html, "html.parser")`; no new parser dependency is authorized. Production code may not read the Phase38 manifest or fixture paths.

Quote objects require an exact built-in tuple of one to three positive exact built-in `int` values, never `bool`, strictly ascending and distinct. Exact quotes require one finite positive `Decimal`; range quotes require two finite positive Decimals with `lower_odds <= upper_odds`. The evidence requires exact page-kind arity and quote type:

| Page kind | Selection arity | Quote type |
| --- | ---: | --- |
| `ODDS_TAN_FUKU` | 1 | `NARMarketOddsExactQuote` |
| `ODDS_UM_LEN_FUKU` | 2 | `NARMarketOddsExactQuote` |
| `ODDS_WIDE` | 2 | `NARMarketOddsRangeQuote` |
| `ODDS_3_LEN_FUKU` | 3 | `NARMarketOddsExactQuote` |

`NARMarketOddsPageKind` is the formal market-family type; no stringly bet-type field is introduced. Existing generic `OddsSnapshotBatch` and `BET_TYPES` are not reused because they require internal race-entry selections, represent only scalar odds, and do not retain Phase32 capture provenance/source state.

## Selection, Decimal, and completeness semantics

WIN keys match `[1-9][0-9]*`. Pair/triple keys join those exact ASCII tokens using literal ASCII `-`, with no internal whitespace, leading zero, sign, Unicode/full-width digit, horse name, or fuzzy identity. Pair/triple values are numerically sorted; duplicate members cause `NARMarketOddsSourceParseDataError`. Output quotes sort lexicographically by canonical selection. Duplicate canonical selections also cause that error; first/last/average/deduplicate behavior is prohibited.

Every scalar token and WIDE endpoint must match `[1-9][0-9]*\\.[0-9]+` after surrounding ASCII-whitespace trim only. Decimal point and fractional digits are mandatory. This rejects integers, commas, full-width forms, signs, exponent notation, zero, negative, NaN, Infinity, empty text, and placeholders. Use only `Decimal(token)`, never float, locale, or ambient Decimal context. Bad numeric data, absent WIDE endpoint, or inverted WIDE range is `NARMarketOddsSourceParseNumericError`.

V1 proves no portable page-local active participant universe across all four families. Consequently `provider_horse_numbers` is exactly `None` and `source_completeness` exactly `UNVERIFIED`; parser v1 parses every validated quote but does not claim a complete/usable market, enumerate `n` / `C(n,2)` / `C(n,3)`, or fill missing quotes. Phase41 must design explicit provider-horse-number to race-entry universe reconciliation, exclusion handling, expected selections, and complete-market proof.

## Deterministic evidence identity

The parser name/version are exactly `nar-market-odds-source-parser` / `v1`. Capture timestamps are serialized as UTC microsecond ISO-8601. Decimal identity text is context-free plain ASCII from the Decimal sign/digits/exponent tuple: fixed point, no exponent, and only redundant fractional trailing zeroes removed. Thus `1.50` and `1.5` have one semantic quote identity while Phase32 `response_sha256` retains raw text distinction.

Use one private serializer exactly equivalent to:

```python
json.dumps(payload, ensure_ascii=False, allow_nan=False,
           sort_keys=True, separators=(",", ":")).encode("utf-8")
```

The exact identity payload contains only:

```text
baba_code
canonical_request_url
capture_id
captured_at_utc
observed_at_utc
organization
page_kind
parser_name
parser_version
provider_display_as_of_text
provider_horse_numbers
quotes
race_date
race_no
request_identity
request_identity_sha256
requested_at_utc
response_byte_length
response_sha256
schema_version
source_completeness
source_state
source_system
```

`quotes` is sorted. EXACT item keys are `exact_odds`, `quote_kind`, `selection`; RANGE item keys are `lower_odds`, `quote_kind`, `selection`, `upper_odds`; selections are JSON int arrays and Decimal values use the fixed canonical text. `provider_horse_numbers` is JSON `null`; self-derived fields are excluded. `evidence_content_sha256` is SHA-256 of those bytes and `evidence_id` is exactly `nar-market-odds-source-evidence-v1:` plus that hash. No clock/random/UUID/filesystem/network/database/locale/manifest dependency is allowed.

## Error and causal isolation

- `NARMarketOddsSourceParseValidationError`: malformed or forged capture input / failure to reconstruct Phase32 capture.
- `NARMarketOddsSourceParseUnsupportedError`: unsupported state/profile, family mismatch, missing/duplicate authoritative root/container, or structural/helper/hidden-content ambiguity.
- `NARMarketOddsSourceParseDataError`: contradictory located data, including duplicate canonical selections.
- `NARMarketOddsSourceParseNumericError`: invalid numeric token or range bounds.

Narrow expected translation only: raw `KeyError`, `IndexError`, `AttributeError`, HTML-parser internals, and `decimal.InvalidOperation` must not escape. No broad whole-function `except Exception`, `BaseException`, or silent fallback is allowed.

Both OPEN and FINAL tables are parsed. FINAL remains explicit evidence but is not prediction/EV eligible; Phase40 receives no causal inputs and decides no eligibility. A later resolver must reject `source_state == FINAL` before prediction/EV use.

## Verification and scope

The dedicated parser test reconstructs Phase32 captures from manifest primitives plus fixture bytes; production code never reads the manifest. It covers all eight fixtures, states, page kinds, exact provenance, deterministic equality/identity/order, and these source facts:

| Family | OPEN | FINAL |
| --- | --- | --- |
| WIN | `(1,)`, `Decimal("3.3")` | `(1,)`, `Decimal("12.0")` |
| QUINELLA | `(1, 2)`, `Decimal("3.4")` | `(2, 5)`, `Decimal("3.8")` |
| WIDE | `(1, 2)`, `1.4–1.5` | `(2, 5)`, `1.9–2.1` |
| TRIO | `(1, 2, 8)`, `Decimal("7.3")` | `(2, 5, 11)`, `Decimal("6.2")` |

Mutated valid Phase32 captures fail closed for missing/duplicate containers, hidden authoritative rows, a hidden state heading, a hidden WIN-container ancestor, a hidden combination-container ancestor, case-insensitive `aria-hidden="true"`, whitespace-tolerant/case-insensitive inline `display: none` and `visibility: hidden`, wrong/missing/mixed headings, malformed horse keys, duplicate pair/triple/selection, malformed/zero/negative decimals, missing/inverted WIDE endpoints, and unexpected key shapes. Static tests prove no manifest runtime dependency, persistence, network, clock, parser fallback, mapping, replay, EV, or JRA behavior. The eight unchanged visible fixtures retain their exact previously pinned evidence identities.

Verification results:

```text
Phase40 dedicated: 51 passed
Phase40 dedicated with ResourceWarning as error: 51 passed
Phase38 + Phase36 + Phase32 focused regressions: 71 passed, 74 subtests passed
Phase30 + Phase25/27/28 daily replay regressions: 97 passed, 66 subtests passed
all NAR test modules: 339 passed, 514 subtests passed
full pytest suite: 3506 passed, 2841 subtests passed
focused compilation and static forbidden-boundary audit: passed
deterministic repeated parsing of all 8 fixtures: passed
```

Phase40 name: `Pure Deterministic NAR Market Odds Source Parser Implementation`.

Phase40 Allowed Files (exactly 4):

```text
scripts/simulation/nar_market_odds_source_parser.py
tests/test_nar_market_odds_source_parser.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

No Phase38 fixture, manifest, `.gitattributes`, generic odds module, migration, or database file may change. Expected later split: Phase41 reconciliation/completeness design, then later persistence, causal resolver, and scalar-market EV adapter. WIN/QUINELLA/TRIO may eventually support scalar EV after those conditions; WIDE remains range evidence with no exact EV semantics. StrategyConfig v1 stays unchanged.

## Allowed files and stop condition

Exactly the following four paths are modified:

```text
scripts/simulation/nar_market_odds_source_parser.py
tests/test_nar_market_odds_source_parser.py
docs/CURRENT_PHASE.md
docs/LATEST_CODEX_REPORT.md
```

Stop at `READY_FOR_REVIEW`. Do not integrate, modify fixtures/manifest/attributes, perform HTTP, stage, commit, push, or prepare a subsequent phase.
