# KeibaOS Roadmap

## Project goal

KeibaOS is a long-term horse-racing research platform that separates acquisition,
prediction, planning, archived settlement, and evaluation so each result can be
audited and reproduced.

## Completed milestones

### Ver0.5 — Data Foundation

- Logging, SQLite storage, and database foundations
- Race domain and fetch foundations
- Repository and Git workflow foundations

### Ver0.6 — Meeting Engine

- NAR connectivity and HTML acquisition
- Beautiful Soup integration
- `RaceMeeting` and today's racecourse acquisition

### Ver0.7 — Race and Prediction Foundations

- Race-list acquisition and parsing
- SQLite race persistence and duplicate detection
- Deterministic prediction engines, candidate generation, strategy selection, and
  single-race prediction CLI

### Ver0.8 — Historical Replay / Simulation Platform

- Audited historical input snapshots with explicit future-information boundaries
- Deterministic execution through the real prediction/recommendation pipeline
- Fixed-stake allocation with explicit race budgets
- Immutable persisted bet-plan identities and purchase order
- Archived official JRA/NAR result and payout settlement
- Real payout arithmetic, ROI/hit-rate/by-type metrics, and maximum drawdown
- Strict replay manifests and deterministic historical replay CLI output
- Clean-clone mixed-provider acceptance without live network access

## Superseded planning

An earlier roadmap proposed `Ver0.8 Horse Engine`, `Ver0.9 Result Engine`, and
`Ver1.0 AI Prediction Engine`. That sequence records historical planning but is not the
current version contract. Horse/result capabilities evolved as prerequisites inside the
audited Ver0.8 replay platform, and no detailed Ver0.9 scope has been approved.

## Post-Ver0.8

Future work remains subject to separate design and approval. Candidate areas include:

- broader historical-input ingestion and request preparation;
- probability calibration and out-of-sample strategy validation;
- true prediction-time market odds/EV for combination tickets;
- additional allocation and portfolio/bankroll policies;
- combined multi-strategy reporting and persistent run-result artifacts;
- wider exceptional settlement-state support;
- operational automation and live betting boundaries;
- optional, independently auditable external AI signals.

The deterministic Ver0.8 baseline remains executable with external AI/LLM signals
disabled.
