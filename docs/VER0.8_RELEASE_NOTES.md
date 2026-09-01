# KeibaOS Ver0.8 Release Notes

Release target: `v0.8.0`

Status: `RELEASE_CANDIDATE_PENDING_FINAL_INTEGRATION`

## Summary

KeibaOS Ver0.8 adds a deterministic, auditable historical replay platform. It executes
persisted prediction-time inputs through the real planning pipeline and settles the
immutable resulting plans against archived official JRA/NAR evidence.

## What Changed Since v0.7.0

- Immutable audited historical input snapshots with exact natural identities
- Explicit future-information cutoff validation
- Historical execution of the real `PredictionPipeline`
- Deterministic fixed-stake allocation and explicit race budgets
- Immutable SQLite bet-plan persistence, including purchase order
- Exact archived official result and payout normalization for JRA and NAR
- Real settlement aggregation and deterministic JSON CLI output

The release is a platform for honest replay and measurement. It is not a claim that a
particular strategy is profitable.

## Reproducibility and Auditability

Requests bind a target commit, dataset/run identity, exact historical snapshots,
strategy and allocation configuration, budgets, capture IDs, and separate prediction
and settlement cutoffs. Plans are persisted before archived settlement evidence is
opened. Settlement reloads those plans and cannot regenerate bets using result
knowledge.

For identical audited inputs, configuration, databases, and archived evidence, the
application produces deterministic replay and summary JSON. Missing, malformed,
contradictory, unsupported, or non-final evidence fails closed.

## JRA and NAR Archived Settlement Support

Ver0.8 can settle represented JRA and NAR races in one request using provider-specific
read-only SQLite capture archives. Capture lookup uses exact IDs and exact snapshot
provider identities. There is no live fetch, latest-capture discovery, cross-provider
fallback, or archive mutation during replay.

Provider normalizers validate official race identity, finality, entry crosswalk, and
normal payout structure before persisting result/payout facts.

## Supported Bet Types

The formal normal-settlement bet types are:

- `単勝`
- `馬連`
- `ワイド`
- `3連複`

Settlement uses official displayed payout-per-100-yen values. Prediction-time
market-odds EV is formal only for `単勝`; combination-ticket `combination_score` is a
ranking heuristic, not market EV.

## Historical Replay CLI

Run one strict schema-v1 request with:

```bash
python -m scripts.cli.run_historical_replay <request_path>
```

Success writes one deterministic JSON summary line to stdout and exits `0`. Expected
application failures write one deterministic JSON error line to stderr and exit `1`.
The operator contract and request fields are documented in
[`HISTORICAL_REPLAY.md`](HISTORICAL_REPLAY.md).

## Verification State

The release-candidate runtime passed the full test suite and GitHub Actions. Acceptance
includes exact portable official fixture verification, mixed-provider replay from a
clean checkout without network access, read-only archive checks, and replay-time clock
isolation. Exact test counts are release-candidate verification results, not a permanent
semantic contract.

## Known Limitations

- Historical snapshots and capture archives must already exist; Ver0.8 does not build
  arbitrary historical replay inputs automatically.
- Provider-wide historical coverage is not claimed.
- Exceptional result/payout states outside the approved normal-final winning envelope
  remain unsupported rather than inferred.
- Fixed stake is the formal allocator; Kelly, proportional, portfolio, and live-bankroll
  allocation remain future work.
- One request represents one strategy; combined multi-strategy reporting is deferred.

## Explicit Non-Claims

Ver0.8 does not guarantee profitability or 120% ROI. It does not claim calibrated win
probabilities, a statistically demonstrated strategy edge, true prediction-time market
EV for combination tickets, complete historical coverage, support for every exceptional
settlement state, live automated betting, or active external AI/LLM augmentation.

The external AI signal baseline is disabled. KeibaOS Ver0.8 is not marketed as an
LLM-powered replay engine.

## Upgrade and Migration Notes

Ver0.8 introduces numbered SQLite migrations for simulation/replay state, historical
snapshots, immutable plans, and settlement facts. Use the existing application
migration workflow; do not hand-edit schema or migration-history tables.

Archived official capture databases remain separate replay inputs and must contain the
exact IDs referenced by requests. The release does not promise automatic conversion of
arbitrary legacy databases or generation of missing historical evidence.

## Release State

Release-candidate documentation has been prepared and independently reviewed. Master
integration is pending. The `v0.8.0` tag has not been created, and a GitHub Release has
not been published. Final integration, annotated tagging, release date, and publication
require separate authorization.
