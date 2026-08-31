from __future__ import annotations

import argparse
import ast
from collections.abc import Sequence
from dataclasses import fields
from decimal import Decimal
import inspect
import io
import json
from pathlib import Path
import sqlite3
from typing import TextIO, get_type_hints
from unittest.mock import patch

import pytest

import scripts.cli as cli_package
import scripts.cli.run_historical_replay as cli_module
from scripts.cli.run_historical_replay import build_parser, main, run
from scripts.simulation.models import BetTypeSummary, SimulationSummary
from scripts.simulation.serialization import to_json_compatible


def _summary() -> SimulationSummary:
    win = BetTypeSummary(
        bet_type="単勝",
        bet_count=1,
        settled_bet_count=1,
        hit_bet_count=1,
        investment=100,
        payout=300,
        profit=200,
        roi=Decimal("300.00"),
        bet_hit_rate=Decimal("100.0"),
    )
    wide = BetTypeSummary(
        bet_type="ワイド",
        bet_count=1,
        settled_bet_count=1,
        hit_bet_count=0,
        investment=100,
        payout=0,
        profit=-100,
        roi=Decimal("0"),
        bet_hit_rate=Decimal("0"),
    )
    return SimulationSummary(
        strategy_id="strategy-id",
        strategy_name="RuleBasedBetStrategy",
        strategy_config_hash="a" * 64,
        race_count=1,
        settled_race_count=1,
        unsettled_race_count=0,
        no_bet_race_count=0,
        void_race_count=0,
        error_race_count=0,
        unsupported_race_count=0,
        bet_count=2,
        settled_bet_count=2,
        settled_purchase_race_count=1,
        hit_bet_count=1,
        hit_race_count=1,
        investment=200,
        payout=300,
        profit=100,
        roi=Decimal("150.00"),
        bet_hit_rate=Decimal("50.0"),
        race_hit_rate=Decimal("100"),
        maximum_drawdown=100,
        by_bet_type={"ワイド": wide, "単勝": win},
    )


def test_public_surface_parser_signature_and_thin_ownership_are_exact() -> None:
    parser = build_parser()
    assert len(parser._actions) == 2
    action = parser._actions[-1]
    assert (action.dest, action.type, action.help, action.required) == (
        "request_path",
        Path,
        "Historical replay request JSON path",
        True,
    )
    assert inspect.signature(build_parser).parameters == {}
    assert get_type_hints(build_parser)["return"] is argparse.ArgumentParser
    signature = inspect.signature(run)
    assert tuple(signature.parameters) == ("argv", "stdout", "stderr")
    assert signature.parameters["argv"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert signature.parameters["argv"].default is None
    assert all(
        signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        and signature.parameters[name].default is None
        for name in ("stdout", "stderr")
    )
    hints = get_type_hints(run)
    assert hints == {
        "argv": Sequence[str] | None,
        "stdout": TextIO | None,
        "stderr": TextIO | None,
        "return": int,
    }
    assert inspect.signature(main).parameters == {}
    assert get_type_hints(main)["return"] is int
    assert not hasattr(cli_package, "run")
    assert not hasattr(cli_package, "build_parser")
    assert not hasattr(cli_package, "main")

    source = inspect.getsource(cli_module)
    tree = ast.parse(source)
    public_functions = [
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]
    assert public_functions == ["build_parser", "run", "main"]
    assert not [node for node in tree.body if isinstance(node, ast.ClassDef)]
    handlers = [node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)]
    assert len(handlers) == 1
    assert ast.unparse(handlers[0].type) == (
        "(OSError, RuntimeError, TypeError, ValueError, sqlite3.Error)"
    )
    application_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_historical_replay_request"
    ]
    assert len(application_calls) == 1
    forbidden = {
        "load_historical_replay_request_document",
        "run_sqlite_historical_replay",
        "execute_and_persist_historical_bet_plans",
        "acquire_and_persist_official_settlement_facts",
        "execute_final_historical_settlement_simulation",
        "apply_migrations",
        "connect",
        "load_capture",
        "save_capture",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not forbidden & (called_names | called_attributes)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not {"requests", "httpx", "urllib", "socket"} & imported_modules
    assert "PredictionPipeline" not in source
    assert "datetime.now" not in source
    assert "datetime.utcnow" not in source
    assert "time.time" not in source


def test_success_calls_application_once_and_serializes_exact_summary() -> None:
    summary = _summary()
    stdout, stderr = io.StringIO(), io.StringIO()
    request_path = Path("再生要求.json")
    with patch.object(
        cli_module,
        "run_historical_replay_request",
        return_value=summary,
    ) as application:
        assert run([str(request_path)], stdout=stdout, stderr=stderr) == 0

    application.assert_called_once_with(request_path=request_path)
    expected = json.dumps(
        {
            "schema_version": 1,
            "status": "ok",
            "summary": to_json_compatible(summary),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    assert stdout.getvalue() == expected
    assert stderr.getvalue() == ""
    assert stdout.getvalue().count("\n") == 1
    assert "\\u" not in stdout.getvalue()
    assert ": " not in stdout.getvalue()
    assert ", " not in stdout.getvalue()
    payload = json.loads(stdout.getvalue())
    assert set(payload["summary"]) == {field.name for field in fields(SimulationSummary)}
    assert list(payload["summary"]["by_bet_type"]) == ["ワイド", "単勝"]
    assert payload["summary"]["roi"] == "150.00"
    assert payload["summary"]["race_hit_rate"] == "100"
    assert payload["summary"]["by_bet_type"]["単勝"]["roi"] == "300.00"
    assert payload["summary"]["by_bet_type"]["ワイド"]["roi"] == "0"

    empty = SimulationSummary(
        strategy_id="empty-id",
        strategy_name="empty-name",
        strategy_config_hash="b" * 64,
        race_count=0,
        settled_race_count=0,
        unsettled_race_count=0,
        no_bet_race_count=0,
        void_race_count=0,
        error_race_count=0,
        unsupported_race_count=0,
        bet_count=0,
        settled_bet_count=0,
        settled_purchase_race_count=0,
        hit_bet_count=0,
        hit_race_count=0,
        investment=0,
        payout=0,
        profit=0,
        roi=None,
        bet_hit_rate=None,
        race_hit_rate=None,
        maximum_drawdown=0,
        by_bet_type={},
    )
    empty_payload = to_json_compatible(empty)
    assert empty_payload["roi"] is None
    assert empty_payload["bet_hit_rate"] is None
    assert empty_payload["race_hit_rate"] is None


@pytest.mark.parametrize(
    "error",
    (
        OSError("os failure"),
        RuntimeError("runtime failure"),
        TypeError("type failure"),
        ValueError("value failure"),
        sqlite3.Error("sqlite failure"),
        ValueError(),
    ),
)
def test_expected_application_failures_use_exact_stderr_contract(error: BaseException) -> None:
    stdout, stderr = io.StringIO(), io.StringIO()
    with patch.object(cli_module, "run_historical_replay_request", side_effect=error) as application:
        assert run(["request.json"], stdout=stdout, stderr=stderr) == 1

    application.assert_called_once_with(request_path=Path("request.json"))
    message = str(error) or type(error).__name__
    expected = json.dumps(
        {
            "error": {"message": message, "type": type(error).__name__},
            "schema_version": 1,
            "status": "error",
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == expected
    assert stderr.getvalue().count("\n") == 1


@pytest.mark.parametrize("error", (KeyboardInterrupt(), SystemExit(7)))
def test_non_application_control_flow_is_not_caught(error: BaseException) -> None:
    with patch.object(cli_module, "run_historical_replay_request", side_effect=error):
        with pytest.raises(type(error)) as caught:
            run(["request.json"], stdout=io.StringIO(), stderr=io.StringIO())
    if isinstance(error, SystemExit):
        assert caught.value.code == 7


def test_argparse_errors_remain_native_system_exit() -> None:
    with patch.object(cli_module, "run_historical_replay_request") as application:
        with pytest.raises(SystemExit) as caught:
            run([], stdout=io.StringIO(), stderr=io.StringIO())
    assert caught.value.code == 2
    application.assert_not_called()


def test_main_returns_exact_run_result() -> None:
    with patch.object(cli_module, "run", return_value=23) as run_mock:
        assert main() == 23
    run_mock.assert_called_once_with()


def test_module_guard_raises_system_exit_from_main() -> None:
    tree = ast.parse(inspect.getsource(cli_module))
    guard = tree.body[-1]
    assert isinstance(guard, ast.If)
    assert ast.unparse(guard.test) == "__name__ == '__main__'"
    assert len(guard.body) == 1
    statement = guard.body[0]
    assert isinstance(statement, ast.Raise)
    assert ast.unparse(statement.exc) == "SystemExit(main())"
