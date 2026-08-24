from __future__ import annotations

import sqlite3

import pytest

from scripts.simulation.repositories.errors import RepositoryValidationError
from scripts.simulation.repositories.sqlite_jra_race_replay_seed_repository import SQLiteJRARaceReplaySeedRepository


def test_repository_requires_exact_connection_and_valid_seed_id() -> None:
    with pytest.raises(RepositoryValidationError):
        SQLiteJRARaceReplaySeedRepository(connection=object())  # type: ignore[arg-type]
    repository = SQLiteJRARaceReplaySeedRepository(connection=sqlite3.connect(":memory:"))
    with pytest.raises(RepositoryValidationError):
        repository.load_seed(seed_id="not-a-seed")
