# Latest Codex Report

## POST_V0_8_DAILY_REPLAY_40 — Pure Deterministic NAR Market Odds Source Parser Implementation

Status: `READY_FOR_REVIEW`
Outcome: `SPLIT_REQUIRED`
Base: `dfa9802644668bac9f5863099604b8bcb9713b52`
Blockers: none

Implemented the exact Phase39-approved pure boundary:

```python
parse_nar_market_odds_source_capture(
    *,
    capture: NARMarketOddsResponseCapture,
) -> NARMarketOddsSourceEvidence
```

The parser safely reconstructs the exact Phase32 capture, strict-decodes its authoritative UTF-8 bytes, and uses the existing BeautifulSoup `html.parser`. It has no arbitrary HTML/URL input, manifest runtime dependency, filesystem access, network, clock, database, persistence, participant reconciliation, replay/cutoff eligibility, probability, EV, strategy, scheduler, settlement, or JRA dependency.

Implemented immutable `NARMarketOddsExactQuote`, `NARMarketOddsRangeQuote`, and `NARMarketOddsSourceEvidence`, with exact OPEN/FINAL, EXACT/RANGE, and UNVERIFIED enums and the approved parser exception hierarchy. Provider selections use canonical positive horse-number tuples. Scalar and WIDE endpoint tokens use direct `Decimal` construction after exact positive ASCII dotted-token validation. WIDE remains a lower/upper RANGE even when endpoints are equal.

Authoritative source extraction is exact:

- WIN: one `table.odd_popular_table_02`; horse number cell two and scalar WIN cell four; PLACE cells excluded.
- QUINELLA: one partitioned `ul.odd_ranking`; 28 OPEN and 55 FINAL rows.
- WIDE: one partitioned `ul.odd_ranking`; 28 OPEN and 55 FINAL ranges using lower text, literal `br`, and ASCII-hyphen upper text.
- TRIO: one partitioned `ul.odd_ranking`; 56 OPEN and 165 FINAL rows.

The `formation_*` controls are never quote inputs. Every authoritative row must validate; malformed, hidden, or duplicate canonical selections fail closed without partial evidence. `provider_horse_numbers` remains `None` and source completeness `UNVERIFIED`; Phase41 owns participant/race-entry reconciliation and causal completeness.

The final review identified one MEDIUM visibility defect: node-local checks accepted a hidden state heading and a WIN authority beneath a `display:none` ancestor. The correction uses one narrow ancestor-chain visibility boundary from each authoritative heading/container through the exact market root. It rejects boolean `hidden`, ASCII-trimmed case-insensitive `aria-hidden="true"`, and case-insensitive inline `display: none` / `visibility: hidden` with narrow ASCII-whitespace tolerance. It does not inspect external CSS or class names and does not walk above the market root. Real-fixture mutations now cover a hidden heading, hidden WIN ancestor, hidden combination ancestor, `aria-hidden`, and `visibility:hidden`.

Parser identity is `nar-market-odds-source-parser` / `v1`. Evidence uses the exact Phase39 canonical-JSON algorithm, context-free fixed Decimal text, deterministic lexical selection order, and prefix `nar-market-odds-source-evidence-v1:`. All eight fixture evidence IDs are pinned by tests and repeated parsing is exactly equal.

Verification:

```text
dedicated Phase40: 51 passed
dedicated ResourceWarning-as-error: 51 passed
Phase38/36/32 focused: 71 passed, 74 subtests passed
Phase30 + Phase25/27/28 daily replay focused: 97 passed, 66 subtests passed
all NAR test modules: 339 passed, 514 subtests passed
full pytest: 3506 passed, 2841 subtests passed
compilation/static forbidden-boundary audit: passed
all 8 unchanged fixture evidence identities: unchanged and pinned
```

Exactly four approved paths are modified. Phase38 fixtures, manifest, `.gitattributes`, Phase32/36 production, database, and logs are unchanged. Cached state is empty; nothing is staged, committed, or pushed.

Phase38 remains `FORMALLY_COMPLETE`; Phase34 remains resolved/superseded; the old Phase33 draft remains superseded. `COMBINATION_EV_REQUIRES_MARKET_ODDS_CAPTURE` remains open. No Phase41 work was prepared or started.
