"""Command-line boundary for persisted simulation request execution."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
import sys
from typing import TextIO

from scripts.simulation.models import BetTypeSummary, SimulationSummary
from scripts.simulation.persisted_simulation_request_application import (
    run_persisted_simulation_request,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the persisted-simulation request parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "request_path",
        type=Path,
        help="Persisted simulation request JSON path",
    )
    return parser


def run(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run the CLI boundary and return its deterministic exit code."""
    arguments = build_parser().parse_args(argv)
    output = sys.stdout if stdout is None else stdout
    errors = sys.stderr if stderr is None else stderr
    try:
        summary = run_persisted_simulation_request(
            request_path=arguments.request_path,
        )
    except (OSError, RuntimeError, TypeError, ValueError, sqlite3.Error) as error:
        payload = {
            "error": {
                "message": str(error) or type(error).__name__,
                "type": type(error).__name__,
            },
            "schema_version": 1,
            "status": "error",
        }
        errors.write(_encode_json(payload) + "\n")
        return 1
    payload = {
        "schema_version": 1,
        "status": "ok",
        "summary": _summary_payload(summary),
    }
    output.write(_encode_json(payload) + "\n")
    return 0


def main() -> int:
    """Run the command using process arguments and standard streams."""
    return run()


def _encode_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _decimal_payload(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _bet_type_summary_payload(summary: BetTypeSummary) -> dict[str, object]:
    return {
        "bet_type": summary.bet_type,
        "bet_count": summary.bet_count,
        "settled_bet_count": summary.settled_bet_count,
        "hit_bet_count": summary.hit_bet_count,
        "investment": summary.investment,
        "payout": summary.payout,
        "profit": summary.profit,
        "roi": _decimal_payload(summary.roi),
        "bet_hit_rate": _decimal_payload(summary.bet_hit_rate),
    }


def _summary_payload(summary: SimulationSummary) -> dict[str, object]:
    return {
        "strategy_id": summary.strategy_id,
        "strategy_name": summary.strategy_name,
        "strategy_config_hash": summary.strategy_config_hash,
        "race_count": summary.race_count,
        "settled_race_count": summary.settled_race_count,
        "unsettled_race_count": summary.unsettled_race_count,
        "no_bet_race_count": summary.no_bet_race_count,
        "void_race_count": summary.void_race_count,
        "error_race_count": summary.error_race_count,
        "unsupported_race_count": summary.unsupported_race_count,
        "bet_count": summary.bet_count,
        "settled_bet_count": summary.settled_bet_count,
        "settled_purchase_race_count": summary.settled_purchase_race_count,
        "hit_bet_count": summary.hit_bet_count,
        "hit_race_count": summary.hit_race_count,
        "investment": summary.investment,
        "payout": summary.payout,
        "profit": summary.profit,
        "roi": _decimal_payload(summary.roi),
        "bet_hit_rate": _decimal_payload(summary.bet_hit_rate),
        "race_hit_rate": _decimal_payload(summary.race_hit_rate),
        "maximum_drawdown": summary.maximum_drawdown,
        "by_bet_type": {
            bet_type: _bet_type_summary_payload(summary.by_bet_type[bet_type])
            for bet_type in sorted(summary.by_bet_type)
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
