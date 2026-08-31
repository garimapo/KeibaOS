"""Command-line boundary for exact historical replay manifests."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
from pathlib import Path
import sqlite3
import sys
from typing import TextIO

from scripts.simulation.historical_replay_request_application import (
    run_historical_replay_request,
)
from scripts.simulation.serialization import to_json_compatible


def build_parser() -> argparse.ArgumentParser:
    """Build the historical-replay request parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "request_path",
        type=Path,
        help="Historical replay request JSON path",
    )
    return parser


def run(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Run one historical replay request and return its CLI exit code."""
    arguments = build_parser().parse_args(argv)
    output = sys.stdout if stdout is None else stdout
    errors = sys.stderr if stderr is None else stderr
    try:
        summary = run_historical_replay_request(
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
        "summary": to_json_compatible(summary),
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


if __name__ == "__main__":
    raise SystemExit(main())
