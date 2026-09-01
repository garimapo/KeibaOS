# KeibaOS

KeibaOS Ver0.8 is a deterministic, auditable historical horse-racing replay platform.
It loads exact persisted prediction-time snapshots, executes the
real prediction and recommendation pipeline, fixes purchase plans before settlement,
and settles them against archived official JRA/NAR result and payout evidence.

The project is for research and verification. It does not guarantee profit or future
performance.

## Ver0.8 capabilities

- Audited `HistoricalInputSnapshot` inputs with explicit future-information cutoffs.
- The existing deterministic Engine -> Predictor -> Value -> Generator -> Strategy ->
  Pipeline prediction path.
- Deterministic fixed stake per recommendation, explicit per-race budgets, and
  immutable persisted `SimulationBetPlanSnapshot` identities.
- Archived official JRA and NAR result/payout settlement without live network access.
- Exact payout-per-100-yen arithmetic and deterministic `SimulationSummary` metrics,
  including investment, payout, profit, ROI, hit rates, per-bet-type summaries, and
  maximum drawdown.
- A strict schema-v1 request manifest and one-line deterministic JSON CLI result.
- Fail-closed rejection of missing, malformed, contradictory, unsupported, or non-final
  replay evidence.

The formal bet types are `単勝`, `馬連`, `ワイド`, and `3連複`. Archived normal-final
settlement supports all four. Exceptional states outside the approved normal-final
winning envelope are not inferred.

## Requirements and setup

- Python 3.12 or later
- SQLite through Python's standard-library `sqlite3`

Create and activate a virtual environment, then install runtime and development
dependencies.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Prediction CLI

The existing single-race prediction CLI reads saved SQLite race inputs and executes the
`PredictionPipeline`:

```bash
python -m scripts.cli.run_prediction <race_id>
```

For example:

```bash
python -m scripts.cli.run_prediction 37 \
  --bet-types "単勝,馬連,ワイド" \
  --max-bets 10 \
  --max-candidates 50 \
  --style formation \
  --min-combination-score 0.0 \
  --sort generator_rank
```

This command produces prediction and candidate output. It is distinct from the
audited historical replay application below.

## Historical replay CLI

Run one strict historical replay request with:

```bash
python -m scripts.cli.run_historical_replay <request_path>
```

The request selects the main SQLite database, provider capture archives, exact snapshot
identities, run and strategy configuration, race budgets, exact result/payout capture
IDs, and per-race settlement cutoffs. Relative database and archive paths are anchored
to the request JSON's parent directory.

See [Historical Replay](docs/HISTORICAL_REPLAY.md) for the operator contract and
[the schema-v1 example](examples/historical_replay_request.v1.example.json) for a
machine-readable template.

> The example JSON is a schema template only. Its placeholder capture IDs are not
> official evidence. Replace every `REPLACE_WITH_...` value with exact audited values
> before replay. Successful schema parsing does not prove that the referenced database,
> archive, snapshot, or capture exists or is trustworthy; replay fails closed if it
> does not.

On success the CLI writes one compact JSON line to stdout and exits `0`. Expected
filesystem, request, application, or SQLite errors write one JSON line to stderr and
exit `1`. Native argument errors remain argparse-owned and exit `2`.

The older persisted-simulation request CLI remains available as a separate application
boundary:

```bash
python -m scripts.cli.run_persisted_simulation <request_path>
```

## Reproducibility and auditability

Replay binds an exact audited snapshot natural identity, target commit, strategy and
allocation configuration, immutable plan identity, exact official capture IDs, and
explicit cutoffs. Prediction uses only evidence at or before its prediction
`information_cutoff`. Later official result/payout evidence is bounded independently
by the settlement cutoff and cannot flow backward into planning.

For identical audited inputs, configuration, databases, and archived evidence, the
replay and serialized summary are deterministic. Capture archives are opened read-only
during replay. The CLI does not discover a latest capture, switch providers, fetch live
data, or manufacture missing evidence.

## Payout and prediction-time EV

Settlement uses official displayed payout-per-100-yen values and integer stake
arithmetic. It never substitutes predicted EV, scores, popularity, or hindsight odds
for an official payout.

Prediction-time market-odds EV semantics are formal only for `単勝`. Combination-ticket
`combination_score` values are ranking heuristics, not true market EV for `馬連`,
`ワイド`, or `3連複`.

## Tests

Run the complete suite with:

```bash
python -m pytest -q
```

Verbose execution is also available:

```bash
python -m pytest -v
```

## Limitations and non-claims

Ver0.8 does not claim guaranteed profitability, 120% ROI, calibrated win
probabilities, or a statistically proven strategy edge. It does not provide complete
provider-wide historical coverage, automatic historical replay-input construction,
all exceptional settlement states, live automated betting, or true combination-ticket
market EV.

External AI/LLM signals are disabled in the Ver0.8 baseline. The implemented prediction
engines are deterministic formal components; optional external AI augmentation remains
post-Ver0.8 work.
