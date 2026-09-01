# KeibaOS Changelog

## Ver0.8.0 (Unreleased)

Release target: `v0.8.0`

### Added

- Audited `HistoricalInputSnapshot` records and exact natural-identity reload.
- Future-information cutoff enforcement across prediction evidence.
- Historical execution through the real `PredictionPipeline`.
- Deterministic fixed-stake allocation with explicit per-race budgets.
- Immutable persisted bet-plan identity, selection, stake, and purchase order.
- Exact archived official JRA/NAR result and payout settlement.
- Normal payout settlement for `単勝`, `馬連`, `ワイド`, and `3連複`.
- Official payout-per-100-yen integer settlement arithmetic.
- Deterministic `SimulationSummary` metrics for ROI, hit rates, by-bet-type results,
  profit, and maximum drawdown.
- Strict schema-v1 historical replay requests and the historical replay CLI.
- Clean-clone mixed-provider no-network acceptance with replay-clock isolation.

### Reproducibility and safety

- Exact snapshot and capture identities are mandatory; missing or contradictory data
  fails closed.
- Prediction and settlement information cutoffs remain separate.
- Settlement consumes immutable persisted plans and cannot regenerate bets with result
  knowledge.
- Represented provider archives are opened read-only during replay.
- Identical audited inputs, configuration, databases, and archived evidence produce
  deterministic replay output.

### Limitations

- Prediction-time market-odds EV semantics are formal only for `単勝`.
- `combination_score` is a ranking heuristic, not market EV.
- Ver0.8 makes no profitability, 120% ROI, calibrated-probability, or demonstrated-edge
  claim.
- Provider-wide historical coverage and automatic replay-input acquisition are not
  included.
- Exceptional settlement support remains limited to the approved normal-final winning
  envelope.
- External AI/LLM signals are disabled in the deterministic baseline.

## Ver0.7 Race Engine

Release:

- Release Ver0.7 Race Engine
- Commit: 9da9a2c


### Added

- NAR RaceList acquisition
- RaceParser implementation
- Race model expansion
- SQLite race data storage
- Duplicate race detection


### Data Flow
NAR Website

↓

RaceMeeting

↓

RaceList

↓

RaceParser

↓

Race Model

↓

SQLite


### Database

Added support for:

- race_date
- organization
- place
- race_no
- race_name
- start_time
- distance
- track
- weather
- track_condition
- horse_count
- deba_table_url



---

## Ver0.6 Meeting Engine


### Added

- NAR connection
- HTML fetching
- BeautifulSoup integration
- RaceMeeting model
- Today's racecourse acquisition


### Completed

Supported racecourses:

- 門別
- 浦和
- 名古屋
- 園田



---

## Ver0.5 Data Foundation


### Added

- Logger
- SQLite database
- Database layer
- Race model
- Fetch foundation
- Git management



---

Future unapproved work is tracked under Post-Ver0.8 in `docs/ROADMAP.md`.
The former Horse Engine / Result Engine / AI version sequence is retained in historical
design records but is not the current version contract.
