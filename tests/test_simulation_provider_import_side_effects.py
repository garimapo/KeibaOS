"""Fresh-process checks that Provider imports are side-effect free."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).parents[1]
MODULES = (
    "scripts.simulation.providers",
    "scripts.simulation.providers.errors",
    "scripts.simulation.providers.models",
    "scripts.simulation.providers.normalization",
    "scripts.simulation.providers.interfaces",
    "scripts.simulation.providers.result_provider",
    "scripts.simulation.providers.odds_provider",
    "scripts.simulation.providers.payout_provider",
)

CHILD_SCRIPT = """
import importlib, json, os, socket, sqlite3, subprocess, sys, threading
modules = json.loads(sys.argv[1])
before_env = dict(os.environ)
before_cwd = os.getcwd()
before_threads = {thread.ident for thread in threading.enumerate()}
calls = []
def blocked(name):
    def call(*args, **kwargs):
        calls.append(name)
        raise AssertionError(name)
    return call
sqlite3.connect = blocked('sqlite3.connect')
socket.socket.connect = blocked('socket.socket.connect')
socket.create_connection = blocked('socket.create_connection')
subprocess.Popen = blocked('subprocess.Popen')
subprocess.run = blocked('subprocess.run')
os.system = blocked('os.system')
for module in modules:
    importlib.import_module(module)
after_threads = {thread.ident for thread in threading.enumerate()}
assert calls == [], calls
assert dict(os.environ) == before_env
assert os.getcwd() == before_cwd
assert after_threads == before_threads
"""


class ProviderImportSideEffectsTest(unittest.TestCase):
    def _run_imports(self, modules: tuple[str, ...] = MODULES) -> tuple[subprocess.CompletedProcess[str], set[str]]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory)
            environment = {
                "PATH": str(Path(sys.executable).parent),
                "PYTHONPATH": str(ROOT),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            result = subprocess.run(
                [sys.executable, "-c", CHILD_SCRIPT, json.dumps(modules)],
                cwd=path,
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            created = {entry.name for entry in path.iterdir()}
        return result, created

    def _assert_clean_import(self, modules: tuple[str, ...] = MODULES) -> None:
        result, created = self._run_imports(modules)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(created, set())

    def test_package_import_subprocess_succeeds(self) -> None:
        self._assert_clean_import((MODULES[0],))

    def test_errors_import_subprocess_succeeds(self) -> None:
        self._assert_clean_import((MODULES[1],))

    def test_models_import_subprocess_succeeds(self) -> None:
        self._assert_clean_import((MODULES[2],))

    def test_normalization_import_subprocess_succeeds(self) -> None:
        self._assert_clean_import((MODULES[3],))

    def test_interfaces_import_subprocess_succeeds(self) -> None:
        self._assert_clean_import((MODULES[4],))

    def test_result_provider_import_subprocess_succeeds(self) -> None:
        self._assert_clean_import((MODULES[5],))

    def test_odds_provider_import_subprocess_succeeds(self) -> None:
        self._assert_clean_import((MODULES[6],))

    def test_payout_provider_import_subprocess_succeeds(self) -> None:
        self._assert_clean_import((MODULES[7],))

    def test_imports_write_no_stdout_or_stderr(self) -> None:
        self._assert_clean_import()

    def test_imports_create_no_files(self) -> None:
        self._assert_clean_import()

    def test_imports_do_not_connect_to_sqlite(self) -> None:
        self._assert_clean_import()

    def test_imports_do_not_attempt_network(self) -> None:
        self._assert_clean_import()

    def test_imports_do_not_start_subprocesses(self) -> None:
        self._assert_clean_import()

    def test_imports_do_not_change_environment(self) -> None:
        self._assert_clean_import()

    def test_imports_do_not_change_cwd(self) -> None:
        self._assert_clean_import()

    def test_imports_do_not_start_threads(self) -> None:
        self._assert_clean_import()

    def test_imports_do_not_create_database_or_logs(self) -> None:
        self._assert_clean_import()

    def test_imports_do_not_write_bytecode(self) -> None:
        self._assert_clean_import()
