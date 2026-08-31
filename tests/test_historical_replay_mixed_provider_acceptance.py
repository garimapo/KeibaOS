from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
import io
import json
from pathlib import Path
import socket
import sqlite3
from typing import Any

import pytest

from scripts.cli.run_historical_replay import run
from scripts.migrations.runner import apply_migrations
import scripts.migrations.runner as migration_runner
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalEntryIdentity,
    HistoricalExternalRaceIdentity,
    HistoricalInputProvenance,
    HistoricalInputSnapshot,
    HistoricalInputSnapshotIdentity,
    HistoricalRaceEntrySnapshot,
    HistoricalRaceSnapshot,
    HistoricalSourceIdentity,
)
from scripts.simulation.jra_official_identity import (
    build_jra_external_entry_id,
    parse_jra_result_url_identity,
)
from scripts.simulation.jra_official_response_capture import JRAOfficialResponseCapture
from scripts.simulation.jra_official_response_capture_migration_runner import (
    apply_jra_capture_schema_migrations,
)
from scripts.simulation.nar_official_response_capture import NAROfficialResponseCapture
from scripts.simulation.nar_official_response_capture_migration_runner import (
    apply_capture_schema_migrations,
)
from scripts.simulation.repositories.interfaces import (
    PayoutStatus,
    RaceResultStatus,
)
from scripts.simulation.repositories.sqlite import (
    SQLitePayoutRepository,
    SQLiteRaceResultRepository,
)
from scripts.simulation.repositories.sqlite_historical_input_snapshot_repository import (
    SQLiteHistoricalInputSnapshotRepository,
)
from scripts.simulation.repositories.sqlite_jra_official_response_capture_repository import (
    SQLiteJRAOfficialResponseCaptureRepository,
)
from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import (
    SQLiteNAROfficialResponseCaptureRepository,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPOSITORY_ROOT / "tests/fixtures/historical_replay/official"
PROVENANCE_PATH = FIXTURE_ROOT / "provenance.json"

FORMAL_BASE = "6ea6c3720f2e30e2dc0d1d13466193e8a4658ee0"
RUN_ID = "c4i3b-mixed-provider-run-v1"
DATASET_ID = "c4i3b-mixed-provider-dataset-v1"
RUN_CONTEXT_STARTED_AT = datetime(2026, 8, 30, 15, 25, tzinfo=UTC)
TARGET_COMMIT_CREATED_AT = datetime(2026, 8, 30, 15, 24, 15, tzinfo=UTC)
STRATEGY_ID = "RuleBasedBetStrategy:e05f27f5729da71b"
STRATEGY_CONFIG_HASH = "e05f27f5729da71b9d057aebe9b60c70c98ee2d7877266cdf6f392e65bb9e60e"

JRA_CAPTURE_ID = "jra-capture-v1:2d8fbee2df4a201923a49a48e02de3f6837293e0166a1347e30ef3f0b0aad296"
NAR_CAPTURE_ID = "nar-capture-v1:d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b"
JRA_BODY_SHA256 = "f5daa967f05ae1ee0cfcbe8d4c0e59aa8a6b3ceef126ce9d8689fe10ffa8ed0e"
NAR_BODY_SHA256 = "3b909b6c9509713150199c3bb3821051181671e10c906f5c315aa4a4c4dbf2db"


class _FixedMigrationDateTime:
    @classmethod
    def now(cls, timezone: object) -> datetime:
        assert timezone is UTC
        return RUN_CONTEXT_STARTED_AT


class _ReplayClockSentinel:
    @classmethod
    def now(cls, timezone: object) -> datetime:
        raise AssertionError("migration runner current clock used during replay")


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value: {value}")


def _provenance_by_provider() -> dict[str, dict[str, Any]]:
    value = json.loads(
        PROVENANCE_PATH.read_text(encoding="utf-8"),
        object_pairs_hook=_strict_pairs,
        parse_constant=_reject_constant,
    )
    assert type(value) is dict
    assert set(value) == {"schema_version", "fixtures"}
    assert value["schema_version"] == 1
    assert tuple(item["provider"] for item in value["fixtures"]) == ("JRA", "NAR")
    return {item["provider"]: item for item in value["fixtures"]}


def _capture(
    provenance: dict[str, Any],
    response_body: bytes,
) -> JRAOfficialResponseCapture | NAROfficialResponseCapture:
    arguments = {
        "canonical_source_url": provenance["source_canonical_source_url"],
        "response_body": response_body,
        "charset": provenance["source_charset"],
        "requested_at": datetime.fromisoformat(provenance["source_requested_at"]),
        "observed_at": datetime.fromisoformat(provenance["source_observed_at"]),
        "stored_at": datetime.fromisoformat(provenance["source_stored_at"]),
        "http_status": provenance["source_http_status"],
        "content_type": provenance["source_content_type"],
        "content_encoding": provenance["source_content_encoding"],
        "http_date": provenance["source_http_date"],
        "etag": provenance["source_etag"],
        "last_modified": provenance["source_last_modified"],
        "content_length": provenance["source_content_length"],
    }
    if provenance["provider"] == "JRA":
        capture = JRAOfficialResponseCapture(**arguments)
        assert capture.capture_id == JRA_CAPTURE_ID
        assert capture.response_sha256 == JRA_BODY_SHA256
        assert len(capture.response_body) == 94570
        return capture
    capture = NAROfficialResponseCapture(**arguments)
    assert capture.capture_id == NAR_CAPTURE_ID
    assert capture.response_sha256 == NAR_BODY_SHA256
    assert len(capture.response_body) == 96614
    return capture


def _evidence(
    *,
    provider: str,
    role: str,
    available_at: datetime,
    observed_at: datetime,
) -> HistoricalInputEvidenceReference:
    token = f"c4i3b_test_generated:{provider}:{role}"
    return HistoricalInputEvidenceReference(
        evidence_role=role,
        canonical_source_url=f"https://c4i3b.example.test/{provider.lower()}/{role}",
        response_sha256=sha256(token.encode("utf-8")).hexdigest(),
        available_at=available_at,
        observed_at=observed_at,
    )


def _snapshot(
    *,
    provider: str,
    capture_url: str,
) -> HistoricalInputSnapshot:
    if provider == "JRA":
        organization = "JRA"
        source_system = "jra_official"
        external_race_id = "jra:race:2025:06:04:03:04"
        internal_race_id = 700
        entry_base = 1000
        horse_numbers = tuple(range(1, 14))
        available_at = datetime(2025, 9, 12, 23, 50, tzinfo=UTC)
        observed_at = datetime(2025, 9, 12, 23, 55, tzinfo=UTC)
        captured_at = datetime(2025, 9, 13, 0, 0, tzinfo=UTC)
        information_cutoff = datetime(2025, 9, 13, 1, 0, tzinfo=UTC)
        scheduled_start_at = datetime(2025, 9, 13, 2, 30, tzinfo=UTC)
        target_race_date = date(2025, 9, 13)
        place, distance_m, track, condition = "中山", 1600, "芝", "良"
        race_identity = parse_jra_result_url_identity(capture_url)

        def external_entry_id(horse_number: int) -> str:
            return build_jra_external_entry_id(
                race_identity=race_identity,
                horse_no=horse_number,
            )
    else:
        organization = "NAR"
        source_system = "nar_official"
        external_race_id = "nar:20260503:31:1"
        internal_race_id = 800
        entry_base = 2000
        horse_numbers = tuple(range(1, 12))
        available_at = datetime(2026, 5, 2, 11, 50, tzinfo=UTC)
        observed_at = datetime(2026, 5, 2, 11, 55, tzinfo=UTC)
        captured_at = datetime(2026, 5, 2, 12, 0, tzinfo=UTC)
        information_cutoff = datetime(2026, 5, 2, 13, 0, tzinfo=UTC)
        scheduled_start_at = datetime(2026, 5, 3, 3, 0, tzinfo=UTC)
        target_race_date = date(2026, 5, 3)
        place, distance_m, track, condition = "高知", 1400, "ダート", "不良"

        def external_entry_id(horse_number: int) -> str:
            return f"{external_race_id}:entry:{horse_number}"

    assert available_at <= observed_at <= captured_at <= information_cutoff <= scheduled_start_at
    source = HistoricalSourceIdentity(
        organization=organization,
        source_system=source_system,
        external_race_id=external_race_id,
        source_url=f"https://c4i3b.example.test/{provider.lower()}/snapshot",
    )
    external_race = HistoricalExternalRaceIdentity(
        organization=organization,
        source_system=source_system,
        external_race_id=external_race_id,
    )
    entries = tuple(
        HistoricalRaceEntrySnapshot(
            race_entry_id=entry_base + horse_number,
            external_entry_identity=HistoricalExternalEntryIdentity(
                external_race_identity=external_race,
                external_entry_id=external_entry_id(horse_number),
                external_horse_id=None,
            ),
            horse_no=horse_number,
            jockey=f"c4i3b_test_generated jockey {horse_number}",
            win_odds=Decimal("2.0"),
            entry_order=horse_number - 1,
        )
        for horse_number in horse_numbers
    )
    provenance: list[HistoricalInputProvenance] = [
        HistoricalInputProvenance(
            input_type="track",
            audit_key="track",
            source="c4i3b_test_generated",
            source_id=f"c4i3b_test_generated:{provider}:track",
            race_entry_id=None,
            evidence=(
                _evidence(
                    provider=provider,
                    role="track",
                    available_at=available_at,
                    observed_at=observed_at,
                ),
            ),
        )
    ]
    for entry in entries:
        for input_type, role in (
            ("entry", "entry"),
            ("odds", "odds_win"),
            ("jockey", "jockey"),
        ):
            provenance.append(
                HistoricalInputProvenance(
                    input_type=input_type,
                    audit_key=f"{input_type}/{entry.race_entry_id}",
                    source="c4i3b_test_generated",
                    source_id=f"c4i3b_test_generated:{provider}:{input_type}:{entry.race_entry_id}",
                    race_entry_id=entry.race_entry_id,
                    evidence=(
                        _evidence(
                            provider=provider,
                            role=role,
                            available_at=available_at,
                            observed_at=observed_at,
                        ),
                    ),
                )
            )
        provenance.append(
            HistoricalInputProvenance(
                input_type="past_race",
                audit_key=f"past_race/{entry.race_entry_id}/none",
                source="c4i3b_test_generated",
                source_id=f"c4i3b_test_generated:{provider}:past_race:{entry.race_entry_id}:none",
                race_entry_id=entry.race_entry_id,
                evidence=(
                    _evidence(
                        provider=provider,
                        role="past_race_absence_query",
                        available_at=available_at,
                        observed_at=observed_at,
                    ),
                ),
            )
        )
    return HistoricalInputSnapshot(
        identity=HistoricalInputSnapshotIdentity(
            dataset_id=DATASET_ID,
            source_identity=source,
            captured_at=captured_at,
        ),
        internal_race_id=internal_race_id,
        information_cutoff=information_cutoff,
        race=HistoricalRaceSnapshot(
            target_race_date=target_race_date,
            scheduled_start_at=scheduled_start_at,
            place=place,
            distance_m=distance_m,
            track=track,
            track_condition=condition,
            race_name="c4i3b_test_generated",
            race_class="c4i3b_test_generated",
            weather="c4i3b_test_generated",
        ),
        entries=entries,
        past_races=(),
        provenance=tuple(provenance),
    )


def _setup_capture_archive(
    *,
    path: Path,
    capture: JRAOfficialResponseCapture | NAROfficialResponseCapture,
) -> None:
    connection = sqlite3.connect(path)
    try:
        if type(capture) is JRAOfficialResponseCapture:
            apply_jra_capture_schema_migrations(connection)
            repository = SQLiteJRAOfficialResponseCaptureRepository(connection=connection)
        else:
            apply_capture_schema_migrations(connection)
            repository = SQLiteNAROfficialResponseCaptureRepository(connection=connection)
        repository.save_capture(capture=capture)
    finally:
        connection.close()


def _load_capture_read_only(
    *,
    path: Path,
    capture: JRAOfficialResponseCapture | NAROfficialResponseCapture,
) -> JRAOfficialResponseCapture | NAROfficialResponseCapture:
    connection = sqlite3.connect(path.absolute().as_uri() + "?mode=ro", uri=True)
    try:
        if type(capture) is JRAOfficialResponseCapture:
            repository = SQLiteJRAOfficialResponseCaptureRepository(connection=connection)
        else:
            repository = SQLiteNAROfficialResponseCaptureRepository(connection=connection)
        loaded = repository.load_capture(capture_id=capture.capture_id)
        assert loaded == capture
        return loaded
    finally:
        connection.close()


def _setup_main_database(
    *,
    path: Path,
    snapshots: tuple[HistoricalInputSnapshot, HistoricalInputSnapshot],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE races (id INTEGER PRIMARY KEY)")
        connection.execute(
            "CREATE TABLE horses ("
            "id INTEGER PRIMARY KEY, race_id INTEGER NOT NULL, horse_no INTEGER NOT NULL)"
        )
        connection.executemany("INSERT INTO races(id) VALUES(?)", ((700,), (800,)))
        connection.executemany(
            "INSERT INTO horses(id,race_id,horse_no) VALUES(?,?,?)",
            tuple((1000 + value, 700, value) for value in range(1, 14))
            + tuple((2000 + value, 800, value) for value in range(1, 12)),
        )
        connection.commit()
        with monkeypatch.context() as setup_patch:
            setup_patch.setattr(migration_runner, "datetime", _FixedMigrationDateTime)
            apply_migrations(connection)
        repository = SQLiteHistoricalInputSnapshotRepository(connection=connection)
        for snapshot in snapshots:
            repository.save_snapshot(snapshot=snapshot)
    finally:
        connection.close()


def _request_document(
    *,
    jra_capture: JRAOfficialResponseCapture,
    nar_capture: NAROfficialResponseCapture,
) -> dict[str, Any]:
    assert TARGET_COMMIT_CREATED_AT < RUN_CONTEXT_STARTED_AT
    return {
        "schema_version": 1,
        "database_path": "main.sqlite3",
        "capture_archives": {
            "JRA/jra_official": "jra_official.sqlite3",
            "NAR/nar_official": "nar_official.sqlite3",
        },
        "run_context": {
            "run_id": RUN_ID,
            "dataset_id": DATASET_ID,
            "started_at": "2026-08-30T15:25:00+00:00",
            "target_commit_id": FORMAL_BASE,
        },
        "strategy": {
            "strategy_name": "RuleBasedBetStrategy",
            "allowed_bet_types": ["単勝"],
            "max_bet_count": 1,
            "selection_style": "formation",
            "min_combination_score": 0.0,
            "max_candidates": 1,
            "sort_condition": "generator_rank",
            "allocation_policy": {
                "policy_name": "fixed_stake_per_recommendation",
                "policy_version": "1",
                "parameters": {"stake_amount": 100},
            },
        },
        "budgets_by_race_id": {
            "700": {"total_amount": 100},
            "800": {"total_amount": 100},
        },
        "races": [
            {
                "snapshot_identity": {
                    "dataset_id": DATASET_ID,
                    "organization": "NAR",
                    "source_system": "nar_official",
                    "external_race_id": "nar:20260503:31:1",
                    "captured_at": "2026-05-02T12:00:00+00:00",
                },
                "internal_race_id": 800,
                "settlement_information_cutoff": "2026-08-27T15:41:31.026438+00:00",
                "result_capture_id": nar_capture.capture_id,
                "payout_capture_catalog_by_bet_type": {"単勝": nar_capture.capture_id},
            },
            {
                "snapshot_identity": {
                    "dataset_id": DATASET_ID,
                    "organization": "JRA",
                    "source_system": "jra_official",
                    "external_race_id": "jra:race:2025:06:04:03:04",
                    "captured_at": "2025-09-13T00:00:00+00:00",
                },
                "internal_race_id": 700,
                "settlement_information_cutoff": "2026-08-26T11:38:28.113891+00:00",
                "result_capture_id": jra_capture.capture_id,
                "payout_capture_catalog_by_bet_type": {"単勝": jra_capture.capture_id},
            },
        ],
    }


def _expected_summary() -> dict[str, Any]:
    return {
        "strategy_id": STRATEGY_ID,
        "strategy_name": "RuleBasedBetStrategy",
        "strategy_config_hash": STRATEGY_CONFIG_HASH,
        "race_count": 2,
        "settled_race_count": 2,
        "unsettled_race_count": 0,
        "no_bet_race_count": 0,
        "void_race_count": 0,
        "error_race_count": 0,
        "unsupported_race_count": 0,
        "bet_count": 2,
        "settled_bet_count": 2,
        "settled_purchase_race_count": 2,
        "hit_bet_count": 0,
        "hit_race_count": 0,
        "investment": 200,
        "payout": 0,
        "profit": -200,
        "roi": "0",
        "bet_hit_rate": "0",
        "race_hit_rate": "0",
        "maximum_drawdown": 200,
        "by_bet_type": {
            "単勝": {
                "bet_type": "単勝",
                "bet_count": 2,
                "settled_bet_count": 2,
                "hit_bet_count": 0,
                "investment": 200,
                "payout": 0,
                "profit": -200,
                "roi": "0",
                "bet_hit_rate": "0",
            }
        },
    }


def _fail_network(*args: object, **kwargs: object) -> None:
    raise AssertionError("network access attempted during historical replay")


def test_mixed_provider_historical_replay_is_exact_and_no_network(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provenance = _provenance_by_provider()
    fixture_paths = {
        provider: REPOSITORY_ROOT / item["fixture_relative_path"]
        for provider, item in provenance.items()
    }
    fixture_before = {provider: path.read_bytes() for provider, path in fixture_paths.items()}
    assert (len(fixture_before["JRA"]), sha256(fixture_before["JRA"]).hexdigest()) == (
        94570,
        JRA_BODY_SHA256,
    )
    assert (len(fixture_before["NAR"]), sha256(fixture_before["NAR"]).hexdigest()) == (
        96614,
        NAR_BODY_SHA256,
    )
    jra_capture = _capture(provenance["JRA"], fixture_before["JRA"])
    nar_capture = _capture(provenance["NAR"], fixture_before["NAR"])
    assert type(jra_capture) is JRAOfficialResponseCapture
    assert type(nar_capture) is NAROfficialResponseCapture

    jra_archive_path = tmp_path / "jra_official.sqlite3"
    nar_archive_path = tmp_path / "nar_official.sqlite3"
    main_path = tmp_path / "main.sqlite3"
    request_path = tmp_path / "historical_replay.json"
    _setup_capture_archive(path=jra_archive_path, capture=jra_capture)
    _setup_capture_archive(path=nar_archive_path, capture=nar_capture)
    assert _load_capture_read_only(path=jra_archive_path, capture=jra_capture).response_body == fixture_before["JRA"]
    assert _load_capture_read_only(path=nar_archive_path, capture=nar_capture).response_body == fixture_before["NAR"]
    archive_before = {
        "JRA": jra_archive_path.read_bytes(),
        "NAR": nar_archive_path.read_bytes(),
    }

    jra_snapshot = _snapshot(
        provider="JRA",
        capture_url=provenance["JRA"]["source_canonical_source_url"],
    )
    nar_snapshot = _snapshot(
        provider="NAR",
        capture_url=provenance["NAR"]["source_canonical_source_url"],
    )
    assert tuple(entry.race_entry_id for entry in jra_snapshot.entries) == tuple(range(1001, 1014))
    assert tuple(entry.race_entry_id for entry in nar_snapshot.entries) == tuple(range(2001, 2012))
    _setup_main_database(
        path=main_path,
        snapshots=(jra_snapshot, nar_snapshot),
        monkeypatch=monkeypatch,
    )
    request = _request_document(jra_capture=jra_capture, nar_capture=nar_capture)
    request_path.write_text(
        json.dumps(request, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    stdout, stderr = io.StringIO(), io.StringIO()
    with monkeypatch.context() as replay_patch:
        replay_patch.setattr(migration_runner, "datetime", _ReplayClockSentinel)
        replay_patch.setattr(socket, "create_connection", _fail_network)
        replay_patch.setattr(socket.socket, "connect", _fail_network)
        exit_code = run([str(request_path)], stdout=stdout, stderr=stderr)

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert stdout.getvalue().count("\n") == 1
    payload = json.loads(stdout.getvalue())
    assert payload == {
        "schema_version": 1,
        "status": "ok",
        "summary": _expected_summary(),
    }
    assert stdout.getvalue() == json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"

    assert jra_archive_path.read_bytes() == archive_before["JRA"]
    assert nar_archive_path.read_bytes() == archive_before["NAR"]
    assert _load_capture_read_only(path=jra_archive_path, capture=jra_capture) == jra_capture
    assert _load_capture_read_only(path=nar_archive_path, capture=nar_capture) == nar_capture
    fixture_after = {provider: path.read_bytes() for provider, path in fixture_paths.items()}
    assert fixture_after == fixture_before

    connection = sqlite3.connect(main_path)
    try:
        plan_headers = connection.execute(
            "SELECT run_id,race_id,strategy_id,strategy_config_hash,information_cutoff "
            "FROM simulation_bet_plans ORDER BY race_id"
        ).fetchall()
        assert plan_headers == [
            (
                RUN_ID,
                700,
                STRATEGY_ID,
                STRATEGY_CONFIG_HASH,
                "2025-09-13T01:00:00+00:00",
            ),
            (
                RUN_ID,
                800,
                STRATEGY_ID,
                STRATEGY_CONFIG_HASH,
                "2026-05-02T13:00:00+00:00",
            ),
        ]
        planned_bets = connection.execute(
            "SELECT p.race_id,b.bet_type,s.race_entry_id,b.stake "
            "FROM simulation_bet_plans p "
            "JOIN simulation_bet_plan_bets b ON b.plan_id=p.id "
            "JOIN simulation_bet_plan_bet_selections s ON s.bet_id=b.id "
            "ORDER BY p.race_id,s.selection_order"
        ).fetchall()
        assert planned_bets == [(700, "単勝", 1001, 100), (800, "単勝", 2001, 100)]

        result_repository = SQLiteRaceResultRepository(connection)
        payout_repository = SQLitePayoutRepository(connection)
        jra_result = result_repository.get_race_result(700)
        nar_result = result_repository.get_race_result(800)
        assert jra_result is not None and jra_result.result_status is RaceResultStatus.COMPLETE
        assert nar_result is not None and nar_result.result_status is RaceResultStatus.COMPLETE
        assert jra_result.source == JRA_CAPTURE_ID
        assert nar_result.source == NAR_CAPTURE_ID
        jra_payout = payout_repository.get_latest_payout_publication(700, "単勝")
        nar_payout = payout_repository.get_latest_payout_publication(800, "単勝")
        assert jra_payout is not None and jra_payout.source == JRA_CAPTURE_ID
        assert nar_payout is not None and nar_payout.source == NAR_CAPTURE_ID
        assert jra_payout.is_complete and nar_payout.is_complete
        assert all(item.payout_status is PayoutStatus.WINNING for item in jra_payout.entries)
        assert all(item.payout_status is PayoutStatus.WINNING for item in nar_payout.entries)
        assert connection.execute("SELECT count(*) FROM race_results").fetchone() == (2,)
        assert connection.execute("SELECT count(*) FROM payout_publications").fetchone() == (2,)
    finally:
        connection.close()
