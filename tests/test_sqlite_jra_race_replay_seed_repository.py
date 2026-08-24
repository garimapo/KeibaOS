from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import sqlite3

import pytest

from scripts.migrations.runner import apply_migrations
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.jra_official_response_capture import (
    JRAOfficialTargetRaceCardResponseCapture,
    JRATargetRaceSelectionResponseCapture,
)
from scripts.simulation.jra_official_response_live_capture import JRATargetRaceNavigationCaptureResult
from scripts.simulation.jra_target_race_card_locator import build_jra_target_race_selection_request_locator
from scripts.simulation.jra_target_race_card_resolution import resolve_jra_target_race_card_response
from scripts.simulation.jra_target_race_input_source import (
    JRATargetRaceSourceCollection,
    normalize_jra_target_race_input_source_records,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)
from scripts.simulation.repositories.sqlite_jra_race_replay_seed_repository import SQLiteJRARaceReplaySeedRepository


UTC = timezone.utc
RACE_ID = "jra:race:2025:05:01:01:01"
RACE_CNAME = "pw01drl00052025010120250105/AB"
RAW_CARD_URL = "/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105/AB"
CARD_URL = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105%2FAB"
OBSERVED = datetime(2025, 1, 5, 1, tzinfo=UTC)
CAPTURED = datetime(2025, 1, 5, 2, tzinfo=UTC)
CUTOFF = datetime(2025, 1, 5, 3, tzinfo=UTC)
STORED = datetime(2025, 1, 5, 4, tzinfo=UTC)


def _selection_body() -> bytes:
    return (
        '<div id="contentsBody"><div class="race_select"><table id="race_list" '
        'class="basic mt20"><tbody><tr><th class="race_num"><a href="'
        + RAW_CARD_URL
        + '">1R</a></th><td class="syutsuba"><a class="btn-def btn-sm btn-narrow" href="'
        + RAW_CARD_URL
        + '">出馬表</a></td></tr></tbody></table></div></div>'
    ).encode("cp932")


def _target_body(*, weather: str = "晴", condition: str = "良", extra_runner: bool = False) -> bytes:
    extra = '''<tr><td class="num">2</td><td class="horse"><div class="name_line"><div class="name"><a href="/JRADB/accessU.html?CNAME=pw01dud009876543210%2FAC">horse2</a></div><div class="odds"><div class="odds_line"><span class="num">3.5</span></div></div></div></td><td class="jockey"><p class="jockey">騎手2</p></td></tr>''' if extra_runner else ""
    return f'''<div id="contentsBody"><div class="line main"><div class="inner"><h1>1レース</h1></div></div><div class="syutsuba"><table class="basic narrow-xy mt20"><caption><div class="race_header"><div class="left"><div class="date_line"><div class="inner"><div class="cell date">2025年1月5日(日) 1回東京1日</div><div class="cell time"><strong>15時00分</strong></div></div></div></div><div class="race_title"><div class="inner"><div class="txt"><span class="main"><span class="race_name">テストレース</span></span></div></div><div class="type"><div class="cell course">コース：1600メートル（芝・左）</div><div class="cell class">3歳1勝</div></div></div><div class="cell baba"><ul><li class="turf"><span class="cap">芝</span><span class="txt">{condition}</span></li><li class="weather"><span class="inner"><span class="txt">{weather}</span></span></li></ul></div></div></caption><tbody><tr><td class="num">1</td><td class="horse"><div class="name_line"><div class="name"><a href="/JRADB/accessU.html?CNAME=pw01dud001234567890%2FAB">horse</a></div><div class="odds"><div class="odds_line"><span class="num">2.5</span></div></div></div></td><td class="jockey"><p class="jockey">騎手</p></td></tr>{extra}</tbody></table></div></div>'''.encode("cp932")


def _formal_inputs(*, weather: str = "晴", condition: str = "良", extra_runner: bool = False):
    selection = JRATargetRaceSelectionResponseCapture(
        request_locator=build_jra_target_race_selection_request_locator(cname=RACE_CNAME),
        response_body=_selection_body(), charset="cp932", requested_at=OBSERVED,
        observed_at=OBSERVED, stored_at=STORED, http_status=200, content_type="text/html",
    )
    card = JRAOfficialTargetRaceCardResponseCapture(
        canonical_source_url=CARD_URL, response_body=_target_body(weather=weather, condition=condition, extra_runner=extra_runner),
        charset="cp932", requested_at=OBSERVED, observed_at=OBSERVED, stored_at=STORED,
        http_status=200, content_type="text/html",
    )
    resolution = resolve_jra_target_race_card_response(
        external_race_id=RACE_ID,
        target_race_selection_capture_id=selection.capture_id,
        captured_at=CAPTURED,
        target_race_selection_capture_provider=lambda *, capture_id: selection,
        target_race_card_capture_provider=lambda *, locator, observed_at_not_after: card,
    )
    navigation = JRATargetRaceNavigationCaptureResult(discovery=resolution.discovery, capture=selection)
    sources = normalize_jra_target_race_input_source_records(response=resolution.response)
    return navigation, resolution, sources


def _initialize(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.execute(
        """CREATE TABLE races(
            id INTEGER PRIMARY KEY, race_date TEXT, organization TEXT, place TEXT, race_no INTEGER,
            race_name TEXT, distance INTEGER, track TEXT, weather TEXT, track_condition TEXT,
            horse_count INTEGER
        )"""
    )
    connection.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER, horse_no INTEGER)")
    apply_migrations(connection)
    return connection


def _connection() -> sqlite3.Connection:
    return _initialize(sqlite3.connect(":memory:"))


def _materialize(repository: SQLiteJRARaceReplaySeedRepository, *, dataset_id: str = "dataset-1", inputs=None):
    navigation, resolution, sources = _formal_inputs() if inputs is None else inputs
    return repository.materialize_seed(
        dataset_id=dataset_id,
        navigation_capture_result=navigation,
        target_race_card_resolution=resolution,
        target_sources=sources,
        information_cutoff=CUTOFF,
    )


def test_repository_requires_exact_connection_and_valid_seed_id() -> None:
    with pytest.raises(RepositoryValidationError):
        SQLiteJRARaceReplaySeedRepository(connection=object())  # type: ignore[arg-type]
    repository = SQLiteJRARaceReplaySeedRepository(connection=sqlite3.connect(":memory:"))
    with pytest.raises(RepositoryValidationError):
        repository.load_seed(seed_id="not-a-seed")


def test_first_materialization_bootstraps_exact_identity_and_round_trips() -> None:
    connection = _connection()
    repository = SQLiteJRARaceReplaySeedRepository(connection=connection)
    seed = _materialize(repository)
    assert connection.execute("SELECT organization,source_system FROM historical_input_source_identities").fetchall() == [("JRA", "jra_official")]
    assert connection.execute("SELECT COUNT(*) FROM races").fetchone() == (1,)
    assert connection.execute("SELECT COUNT(*) FROM horses").fetchone() == (1,)
    assert connection.execute("SELECT external_race_id,internal_race_id FROM historical_input_external_races").fetchone() == (RACE_ID, seed.internal_race_id)
    assert connection.execute("SELECT external_entry_id,race_entry_id FROM historical_input_external_entries").fetchone() == (RACE_ID + ":entry:1", seed.entries[0].internal_race_entry_id)
    assert connection.execute("SELECT COUNT(*) FROM jra_race_replay_seeds").fetchone() == (1,)
    assert connection.execute("SELECT COUNT(*) FROM jra_race_replay_seed_entries").fetchone() == (1,)
    assert repository.load_seed(seed_id=seed.seed_id) == seed
    assert _materialize(repository) == seed


def test_prior_valid_seed_is_required_before_existing_mapping_reuse() -> None:
    connection = _connection()
    connection.execute("INSERT INTO historical_input_source_identities VALUES('JRA','jra_official')")
    connection.execute("INSERT INTO races VALUES(1,'2025-01-05','JRA','東京',1,'テストレース',1600,'芝','晴','良',1)")
    connection.execute("INSERT INTO historical_input_external_races VALUES('JRA','jra_official',?,1)", (RACE_ID,))
    connection.commit()
    with pytest.raises(RepositoryDataIntegrityError, match="prior d0 seed proof"):
        _materialize(SQLiteJRARaceReplaySeedRepository(connection=connection))
    assert connection.execute("SELECT COUNT(*) FROM jra_race_replay_seeds").fetchone() == (0,)


def test_valid_prior_seed_allows_revision_reuse_without_revision_fact_gate() -> None:
    connection = _connection()
    repository = SQLiteJRARaceReplaySeedRepository(connection=connection)
    first = _materialize(repository)
    revised = _formal_inputs(weather="雨", condition="重", extra_runner=True)
    second = _materialize(repository, dataset_id="dataset-2", inputs=revised)
    assert first.seed_id != second.seed_id
    assert first.internal_race_id == second.internal_race_id
    assert first.entries[0].internal_race_entry_id == second.entries[0].internal_race_entry_id
    assert connection.execute("SELECT COUNT(*) FROM races").fetchone() == (1,)
    assert connection.execute("SELECT COUNT(*) FROM horses").fetchone() == (2,)
    assert connection.execute("SELECT weather,track_condition FROM races").fetchone() == ("晴", "良")


def test_existing_entry_mapping_without_prior_seed_entry_proof_fails() -> None:
    connection = _connection()
    repository = SQLiteJRARaceReplaySeedRepository(connection=connection)
    _materialize(repository)
    internal_race_id = connection.execute("SELECT id FROM races").fetchone()[0]
    connection.execute("INSERT INTO horses(race_id,horse_no) VALUES(?,2)", (internal_race_id,))
    internal_entry_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
    connection.execute(
        "INSERT INTO historical_input_external_entries VALUES('JRA','jra_official',?,?,?,?)",
        (RACE_ID, RACE_ID + ":entry:2", internal_race_id, internal_entry_id),
    )
    connection.commit()
    with pytest.raises(RepositoryDataIntegrityError, match="entry mapping lacks prior d0 seed proof"):
        _materialize(repository, dataset_id="dataset-2", inputs=_formal_inputs(extra_runner=True))


def test_unproven_legacy_collisions_are_integrity_failures() -> None:
    connection = _connection()
    connection.execute("INSERT INTO races VALUES(1,'2025-01-05','JRA','東京',1,'legacy',1600,'芝','晴','良',1)")
    connection.commit()
    with pytest.raises(RepositoryDataIntegrityError, match="legacy race collision"):
        _materialize(SQLiteJRARaceReplaySeedRepository(connection=connection))


@pytest.mark.parametrize("record_index", [0, 1, 2, 3])
@pytest.mark.parametrize("mismatch", ["sha", "url", "observed"])
def test_every_source_record_must_prove_exact_resolved_response_before_transaction(
    record_index: int,
    mismatch: str,
) -> None:
    connection = _connection()
    repository = SQLiteJRARaceReplaySeedRepository(connection=connection)
    navigation, resolution, sources = _formal_inputs()
    original = sources.source_records[record_index]
    evidence = HistoricalInputEvidenceReference(
        original.record_kind,
        "https://example.test/mixed" if mismatch == "url" else CARD_URL,
        "f" * 64 if mismatch == "sha" else hashlib.sha256(resolution.response.response_body).hexdigest(),
        None,
        datetime(2025, 1, 5, 0, tzinfo=UTC) if mismatch == "observed" else resolution.response.observed_at,
    )
    bad_record = replace(original, evidence=(evidence,))
    records = list(sources.source_records)
    records[record_index] = bad_record
    mixed = JRATargetRaceSourceCollection(
        target_track_record=bad_record if record_index == 0 else sources.target_track_record,
        target_entry_records=(bad_record,) if record_index == 1 else sources.target_entry_records,
        target_horse_history_locators=sources.target_horse_history_locators,
        source_records=tuple(records),
    )
    with pytest.raises(RepositoryValidationError, match="resolved target-card response"):
        repository.materialize_seed(
            dataset_id="dataset-1", navigation_capture_result=navigation,
            target_race_card_resolution=resolution, target_sources=mixed, information_cutoff=CUTOFF,
        )
    assert not connection.in_transaction
    assert connection.execute("SELECT COUNT(*) FROM historical_input_source_identities").fetchone() == (0,)


@pytest.mark.parametrize("cutoff", [
    datetime(2025, 1, 5, 1, 59, tzinfo=UTC),
    datetime(2025, 1, 5, 6, 1, tzinfo=UTC),
])
def test_invalid_causal_time_fails_before_transaction(cutoff: datetime) -> None:
    connection = _connection()
    repository = SQLiteJRARaceReplaySeedRepository(connection=connection)
    navigation, resolution, sources = _formal_inputs()
    with pytest.raises(RepositoryValidationError, match="causal time guard"):
        repository.materialize_seed(
            dataset_id="dataset-1", navigation_capture_result=navigation,
            target_race_card_resolution=resolution, target_sources=sources, information_cutoff=cutoff,
        )
    assert not connection.in_transaction
    assert connection.execute("SELECT COUNT(*) FROM historical_input_source_identities").fetchone() == (0,)


def test_unexpected_post_begin_exception_rolls_back_and_rethrows() -> None:
    class Marker(BaseException):
        pass

    class ExplodingRepository(SQLiteJRARaceReplaySeedRepository):
        def _resolve_or_create_race(self, *, facts):
            raise Marker

    connection = _connection()
    repository = ExplodingRepository(connection=connection)
    with pytest.raises(Marker):
        _materialize(repository)
    assert not connection.in_transaction
    for table in (
        "historical_input_source_identities", "races", "horses", "historical_input_external_races",
        "historical_input_external_entries", "jra_race_replay_seeds", "jra_race_replay_seed_entries",
    ):
        assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone() == (0,)


def test_natural_identity_conflict_and_distinct_dataset() -> None:
    connection = _connection()
    repository = SQLiteJRARaceReplaySeedRepository(connection=connection)
    first = _materialize(repository)
    second = _materialize(repository, dataset_id="dataset-2")
    assert first.seed_id != second.seed_id
    revised = _formal_inputs(weather="雨")
    with pytest.raises(RepositoryConflictError):
        _materialize(repository, inputs=revised)


def test_process_restart_loads_exact_seed(tmp_path) -> None:
    path = tmp_path / "seed.sqlite"
    connection = _initialize(sqlite3.connect(path))
    seed = _materialize(SQLiteJRARaceReplaySeedRepository(connection=connection))
    connection.close()
    reopened = sqlite3.connect(path)
    try:
        assert SQLiteJRARaceReplaySeedRepository(connection=reopened).load_seed(seed_id=seed.seed_id) == seed
    finally:
        reopened.close()


@pytest.mark.parametrize("column,value", [
    ("organization", "NAR"),
    ("source_system", "other"),
    ("external_race_id", "jra:race:2025:05:01:01:02"),
    ("internal_race_id", 99),
])
def test_load_rejects_corrupt_repeated_child_identity(column: str, value: object) -> None:
    connection = _connection()
    repository = SQLiteJRARaceReplaySeedRepository(connection=connection)
    seed = _materialize(repository)
    connection.execute("PRAGMA foreign_keys=OFF")
    connection.execute("PRAGMA ignore_check_constraints=ON")
    connection.execute(
        f"UPDATE jra_race_replay_seed_entries SET {column}=? WHERE seed_id=?", (value, seed.seed_id)
    )
    connection.execute("PRAGMA ignore_check_constraints=OFF")
    connection.execute("PRAGMA foreign_keys=ON")
    with pytest.raises(RepositoryDataIntegrityError, match="child identity"):
        repository.load_seed(seed_id=seed.seed_id)


@pytest.mark.parametrize("column,value", [
    ("content_sha256", "d" * 64),
    ("target_race_card_capture_id", "jra-capture-v3:" + "d" * 64),
    ("target_race_card_response_sha256", "d" * 64),
    ("canonical_target_race_card_url", CARD_URL.replace("%2FAB", "%2FAC")),
])
def test_load_rejects_corrupt_header_provenance(column: str, value: object) -> None:
    connection = _connection()
    repository = SQLiteJRARaceReplaySeedRepository(connection=connection)
    seed = _materialize(repository)
    connection.execute("PRAGMA ignore_check_constraints=ON")
    connection.execute(f"UPDATE jra_race_replay_seeds SET {column}=? WHERE seed_id=?", (value, seed.seed_id))
    connection.execute("PRAGMA ignore_check_constraints=OFF")
    with pytest.raises(RepositoryDataIntegrityError):
        repository.load_seed(seed_id=seed.seed_id)


def test_load_rejects_missing_child() -> None:
    connection = _connection()
    repository = SQLiteJRARaceReplaySeedRepository(connection=connection)
    seed = _materialize(repository)
    connection.execute("PRAGMA foreign_keys=OFF")
    connection.execute("DELETE FROM jra_race_replay_seed_entries WHERE seed_id=?", (seed.seed_id,))
    with pytest.raises(RepositoryDataIntegrityError, match="no entries"):
        repository.load_seed(seed_id=seed.seed_id)


def test_static_boundary_has_no_archive_http_latest_or_c4d_ownership() -> None:
    source = __import__(
        "scripts.simulation.repositories.sqlite_jra_race_replay_seed_repository", fromlist=["x"]
    ).__file__
    text = open(source, encoding="utf-8").read()
    assert "requests" not in text
    assert "official_response_capture_repository" not in text
    assert "load_latest" not in text
    assert "c4d" not in text.lower()
    assert "LIMIT 1" not in text
