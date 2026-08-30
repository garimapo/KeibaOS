from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

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
from scripts.simulation.jra_official_identity import build_jra_external_entry_id, parse_jra_result_url_identity
from scripts.simulation.jra_official_response_capture import JRAOfficialPageKind, JRAOfficialResponseCapture
from scripts.simulation.jra_target_race_payout_persistence import normalize_and_persist_jra_target_race_payout
from scripts.simulation.jra_target_race_result_persistence import normalize_and_persist_jra_target_race_result
from scripts.simulation.nar_official_response_capture import NAROfficialPageKind, NAROfficialResponseCapture
from scripts.simulation.nar_target_race_payout_persistence import normalize_and_persist_nar_target_race_payout
from scripts.simulation.nar_target_race_result_persistence import normalize_and_persist_nar_target_race_result
from scripts.simulation.repositories.interfaces import (
    PayoutPublication,
    PayoutStatus,
    PersistedRaceResult,
    RaceResultEntryStatus,
    RaceResultStatus,
)


UTC = timezone.utc
REPOSITORY_ROOT = Path(__file__).parent.parent
FIXTURE_ROOT = REPOSITORY_ROOT / "tests/fixtures/historical_replay/official"
PROVENANCE_PATH = FIXTURE_ROOT / "provenance.json"
EXPECTED_FACTS_PATH = FIXTURE_ROOT / "expected_facts.json"
SUPPORTED_BET_TYPES = ("単勝", "馬連", "ワイド", "3連複")

JRA_CAPTURE_ID = "jra-capture-v1:2d8fbee2df4a201923a49a48e02de3f6837293e0166a1347e30ef3f0b0aad296"
NAR_CAPTURE_ID_PREFIX = "nar-capture-v1:"
NAR_CAPTURE_ID_SUFFIX = "d6692261a54c1038a5ffd804ae79edda9ca543cb5d78f37c41ffaeefe281013b"
NAR_EXPECTED_COMPLETE_CAPTURE_ID = NAR_CAPTURE_ID_PREFIX + NAR_CAPTURE_ID_SUFFIX

ROOT_KEYS = {"schema_version", "fixtures"}
PROVENANCE_FIXTURE_KEYS = {
    "provider",
    "fixture_role",
    "source_capture_id",
    "source_canonical_source_url",
    "source_page_kind",
    "source_response_sha256",
    "source_response_byte_length",
    "source_charset",
    "source_requested_at",
    "source_observed_at",
    "source_stored_at",
    "source_http_status",
    "source_content_type",
    "source_content_encoding",
    "source_http_date",
    "source_etag",
    "source_last_modified",
    "source_content_length",
    "source_race_identity",
    "derivation_kind",
    "fixture_relative_path",
    "fixture_sha256",
    "fixture_byte_length",
    "fixture_charset",
    "fixture_capture_identity_policy",
    "supported_normalization_roles",
}
EXPECTED_FIXTURE_KEYS = {
    "provider",
    "fixture_relative_path",
    "source_race_identity",
    "result_status",
    "finish_order",
    "payouts_by_bet_type",
}
FINISH_KEYS = {"horse_number", "finish_position", "result_status"}
PAYOUT_KEYS = {"horse_numbers", "payout_per_100", "payout_status"}


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value: {value}")


def _load_strict_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_strict_pairs,
        parse_constant=_reject_constant,
    )
    if type(value) is not dict:
        raise ValueError("JSON root must be an object")
    return value


class _Archive:
    def __init__(self, capture: JRAOfficialResponseCapture | NAROfficialResponseCapture) -> None:
        self.capture = capture
        self.calls: list[str] = []

    def load_capture(self, *, capture_id: str) -> JRAOfficialResponseCapture | NAROfficialResponseCapture | None:
        self.calls.append(capture_id)
        return self.capture if capture_id == self.capture.capture_id else None


class _RaceResultRepository:
    def __init__(self) -> None:
        self.saved: list[PersistedRaceResult] = []

    def save_race_result(self, result: PersistedRaceResult) -> None:
        self.saved.append(result)


class _PayoutRepository:
    def __init__(self) -> None:
        self.saved: list[PayoutPublication] = []

    def save_payout_publication(self, publication: PayoutPublication) -> PayoutPublication:
        self.saved.append(publication)
        return publication


def _capture(provenance: dict[str, Any], body: bytes) -> JRAOfficialResponseCapture | NAROfficialResponseCapture:
    arguments = {
        "canonical_source_url": provenance["source_canonical_source_url"],
        "response_body": body,
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
        return JRAOfficialResponseCapture(**arguments)
    return NAROfficialResponseCapture(**arguments)


def _evidence(provider: str, captured_at: datetime, role: str) -> HistoricalInputEvidenceReference:
    return HistoricalInputEvidenceReference(
        role,
        f"https://evidence.example.test/{provider.lower()}",
        ("a" if provider == "JRA" else "b") * 64,
        None,
        captured_at - timedelta(minutes=1),
    )


def _snapshot(provider: str, provenance: dict[str, Any]) -> HistoricalInputSnapshot:
    if provider == "JRA":
        organization, source_system = "JRA", "jra_official"
        race_identity = parse_jra_result_url_identity(provenance["source_canonical_source_url"])
        external_race_id = race_identity.external_race_id
        target_date, place, horse_numbers = date(2025, 9, 13), "中山", tuple(range(1, 14))
        captured_at = datetime(2025, 9, 13, tzinfo=UTC)
        internal_race_id, scheduled = 700, datetime(2025, 9, 13, 2, 30, tzinfo=UTC)
        external_entry_id = lambda horse_no: build_jra_external_entry_id(  # noqa: E731
            race_identity=race_identity,
            horse_no=horse_no,
        )
    else:
        organization, source_system = "NAR", "nar_official"
        external_race_id = "nar:20260503:31:1"
        target_date, place, horse_numbers = date(2026, 5, 3), "高知", tuple(range(1, 12))
        captured_at = datetime(2026, 5, 2, 12, tzinfo=UTC)
        internal_race_id, scheduled = 800, datetime(2026, 5, 3, 3, tzinfo=UTC)
        external_entry_id = lambda horse_no: f"{external_race_id}:entry:{horse_no}"  # noqa: E731

    source = HistoricalSourceIdentity(
        organization,
        source_system,
        external_race_id,
        provenance["source_canonical_source_url"],
    )
    external_race = HistoricalExternalRaceIdentity(organization, source_system, external_race_id)
    entries = tuple(
        HistoricalRaceEntrySnapshot(
            race_entry_id=1000 + horse_no,
            external_entry_identity=HistoricalExternalEntryIdentity(
                external_race,
                external_entry_id(horse_no),
                None,
            ),
            horse_no=horse_no,
            jockey=f"騎手{horse_no}",
            win_odds=Decimal("2.0"),
            entry_order=index,
        )
        for index, horse_no in enumerate(horse_numbers)
    )
    provenance_rows: list[HistoricalInputProvenance] = [
        HistoricalInputProvenance(
            "track",
            "track",
            source_system,
            "track",
            None,
            (_evidence(provider, captured_at, "track"),),
        )
    ]
    for entry in entries:
        entry_id = entry.race_entry_id
        provenance_rows.extend(
            (
                HistoricalInputProvenance("entry", f"entry/{entry_id}", source_system, f"entry-{entry_id}", entry_id, (_evidence(provider, captured_at, "entry"),)),
                HistoricalInputProvenance("odds", f"odds/{entry_id}", source_system, f"odds-{entry_id}", entry_id, (_evidence(provider, captured_at, "odds_win"),)),
                HistoricalInputProvenance("jockey", f"jockey/{entry_id}", source_system, f"jockey-{entry_id}", entry_id, (_evidence(provider, captured_at, "jockey"),)),
                HistoricalInputProvenance("past_race", f"past_race/{entry_id}/none", source_system, f"absence-{entry_id}", entry_id, (_evidence(provider, captured_at, "past_race_absence_query"),)),
            )
        )
    return HistoricalInputSnapshot(
        identity=HistoricalInputSnapshotIdentity(f"dataset-{provider.lower()}", source, captured_at),
        internal_race_id=internal_race_id,
        information_cutoff=captured_at + timedelta(hours=1),
        race=HistoricalRaceSnapshot(
            target_race_date=target_date,
            scheduled_start_at=scheduled,
            place=place,
            distance_m=1600 if provider == "JRA" else 1400,
            track="芝" if provider == "JRA" else "ダート",
            track_condition="良" if provider == "JRA" else "不良",
        ),
        entries=entries,
        past_races=(),
        provenance=tuple(provenance_rows),
    )


def _documents() -> tuple[dict[str, Any], dict[str, Any]]:
    return _load_strict_json(PROVENANCE_PATH), _load_strict_json(EXPECTED_FACTS_PATH)


def test_fixture_documents_and_raw_bytes_are_exact() -> None:
    provenance, expected = _documents()
    assert set(provenance) == ROOT_KEYS
    assert set(expected) == ROOT_KEYS
    assert provenance["schema_version"] == expected["schema_version"] == 1
    assert tuple(item["provider"] for item in provenance["fixtures"]) == ("JRA", "NAR")
    assert tuple(item["provider"] for item in expected["fixtures"]) == ("JRA", "NAR")
    assert tuple(item["source_capture_id"] for item in provenance["fixtures"]) == (
        JRA_CAPTURE_ID,
        NAR_EXPECTED_COMPLETE_CAPTURE_ID,
    )

    expected_by_provider = {item["provider"]: item for item in expected["fixtures"]}
    for item in provenance["fixtures"]:
        assert set(item) == PROVENANCE_FIXTURE_KEYS
        assert item["fixture_role"] == "historical_replay_official_result_and_payout"
        assert item["derivation_kind"] == "exact_source_bytes"
        assert item["fixture_capture_identity_policy"] == "reconstructs_exact_source_capture_identity"
        assert item["supported_normalization_roles"] == ["target_race_result", "target_race_payout"]
        fixture_path = REPOSITORY_ROOT / item["fixture_relative_path"]
        body = fixture_path.read_bytes()
        digest = sha256(body).hexdigest()
        assert len(body) == item["fixture_byte_length"] == item["source_response_byte_length"]
        assert digest == item["fixture_sha256"] == item["source_response_sha256"]
        assert b"\0" not in body
        if item["provider"] == "JRA":
            assert len(body) == 94570
            assert digest == "f5daa967f05ae1ee0cfcbe8d4c0e59aa8a6b3ceef126ce9d8689fe10ffa8ed0e"
            assert body.count(b"\r\n") == 963
            assert body.count(b"\n") - body.count(b"\r\n") == 893
        else:
            assert len(body) == 96614
            assert digest == "3b909b6c9509713150199c3bb3821051181671e10c906f5c315aa4a4c4dbf2db"
            assert body.count(b"\n") == 1177
            assert body.count(b"\r\n") == 0
        assert body.decode(item["fixture_charset"], errors="strict").encode(item["fixture_charset"]) == body

        facts = expected_by_provider[item["provider"]]
        assert set(facts) == EXPECTED_FIXTURE_KEYS
        assert facts["fixture_relative_path"] == item["fixture_relative_path"]
        assert facts["source_race_identity"] == item["source_race_identity"]
        assert facts["result_status"] == "complete"
        assert all(set(row) == FINISH_KEYS and row["result_status"] == "confirmed" for row in facts["finish_order"])
        assert all(
            type(row["horse_number"]) is int and type(row["finish_position"]) is int
            for row in facts["finish_order"]
        )
        assert tuple(facts["payouts_by_bet_type"]) == SUPPORTED_BET_TYPES
        assert all(
            set(row) == PAYOUT_KEYS and row["payout_status"] == "winning"
            for rows in facts["payouts_by_bet_type"].values()
            for row in rows
        )
        assert all(
            type(row["payout_per_100"]) is int
            and all(type(horse_number) is int for horse_number in row["horse_numbers"])
            for rows in facts["payouts_by_bet_type"].values()
            for row in rows
        )

    attributes = (REPOSITORY_ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert attributes == [
        "tests/fixtures/historical_replay/official/jra/race_result_20250913_nakayama_04.cp932.html -text -diff",
        "tests/fixtures/historical_replay/official/nar/race_mark_table_20260503_31_01.utf8.html -text -diff",
    ]


def test_duplicate_json_keys_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate JSON key"):
        json.loads('{"schema_version": 1, "schema_version": 1}', object_pairs_hook=_strict_pairs)


def test_formal_capture_identity_and_public_normalizers_match_expected_facts() -> None:
    provenance, expected = _documents()
    expected_by_provider = {item["provider"]: item for item in expected["fixtures"]}
    for item in provenance["fixtures"]:
        provider = item["provider"]
        fixture_path = REPOSITORY_ROOT / item["fixture_relative_path"]
        before = fixture_path.read_bytes()
        before_sha = sha256(before).hexdigest()
        capture = _capture(item, before)
        assert capture.capture_id == item["source_capture_id"]
        assert capture.response_sha256 == item["source_response_sha256"]
        assert capture.canonical_source_url == item["source_canonical_source_url"]
        assert capture.page_kind.value == item["source_page_kind"]
        assert capture.charset == item["source_charset"]
        assert capture.requested_at == datetime.fromisoformat(item["source_requested_at"])
        assert capture.observed_at == datetime.fromisoformat(item["source_observed_at"])
        assert capture.stored_at == datetime.fromisoformat(item["source_stored_at"])
        assert capture.http_status == item["source_http_status"]
        assert capture.content_type == item["source_content_type"]
        assert capture.content_encoding == item["source_content_encoding"]
        assert capture.http_date == item["source_http_date"]
        assert capture.etag == item["source_etag"]
        assert capture.last_modified == item["source_last_modified"]
        assert capture.content_length == item["source_content_length"]
        if provider == "JRA":
            assert type(capture) is JRAOfficialResponseCapture
            assert capture.capture_id == JRA_CAPTURE_ID
            assert capture.page_kind is JRAOfficialPageKind.RACE_RESULT
        else:
            assert type(capture) is NAROfficialResponseCapture
            assert capture.capture_id == NAR_EXPECTED_COMPLETE_CAPTURE_ID
            assert capture.page_kind is NAROfficialPageKind.RACE_MARK_TABLE

        snapshot = _snapshot(provider, item)
        assert snapshot.identity.source_identity.external_race_id == item["source_race_identity"]
        horse_number_by_entry_id = MappingProxyType({entry.race_entry_id: entry.horse_no for entry in snapshot.entries})
        archive = _Archive(capture)
        result_repository = _RaceResultRepository()
        if provider == "JRA":
            result = normalize_and_persist_jra_target_race_result(
                capture_id=capture.capture_id,
                capture_archive=archive,
                snapshot=snapshot,
                race_result_repository=result_repository,
            )
        else:
            result = normalize_and_persist_nar_target_race_result(
                capture_id=capture.capture_id,
                capture_archive=archive,
                snapshot=snapshot,
                race_result_repository=result_repository,
            )
        assert archive.calls == [capture.capture_id]
        assert result_repository.saved == [result]
        assert result.result_status is RaceResultStatus.COMPLETE
        assert result.source == capture.capture_id
        assert result.observed_at == result.finalized_at == capture.observed_at
        actual_finish = [
            {
                "horse_number": entry.horse_no,
                "finish_position": entry.finish_position,
                "result_status": entry.result_status.value,
            }
            for entry in sorted(result.entries, key=lambda value: value.finish_position or 0)
        ]
        assert actual_finish == expected_by_provider[provider]["finish_order"]
        assert all(entry.result_status is RaceResultEntryStatus.CONFIRMED for entry in result.entries)
        assert all(horse_number_by_entry_id[entry.race_entry_id] == entry.horse_no for entry in result.entries)

        for bet_type in SUPPORTED_BET_TYPES:
            payout_archive = _Archive(capture)
            payout_repository = _PayoutRepository()
            if provider == "JRA":
                publication = normalize_and_persist_jra_target_race_payout(
                    capture_id=capture.capture_id,
                    capture_archive=payout_archive,
                    snapshot=snapshot,
                    bet_type=bet_type,
                    payout_repository=payout_repository,
                )
            else:
                publication = normalize_and_persist_nar_target_race_payout(
                    capture_id=capture.capture_id,
                    capture_archive=payout_archive,
                    snapshot=snapshot,
                    bet_type=bet_type,
                    payout_repository=payout_repository,
                )
            assert payout_archive.calls == [capture.capture_id]
            assert payout_repository.saved == [publication]
            assert publication.source == capture.capture_id
            assert publication.observed_at == publication.finalized_at == capture.observed_at
            actual_payouts = sorted(
                (
                    tuple(horse_number_by_entry_id[entry_id] for entry_id in record.race_entry_ids),
                    record.payout_per_100,
                    record.payout_status.value,
                )
                for record in publication.entries
            )
            expected_payouts = sorted(
                (
                    tuple(row["horse_numbers"]),
                    row["payout_per_100"],
                    row["payout_status"],
                )
                for row in expected_by_provider[provider]["payouts_by_bet_type"][bet_type]
            )
            assert actual_payouts == expected_payouts
            assert all(record.payout_status is PayoutStatus.WINNING for record in publication.entries)

        after = fixture_path.read_bytes()
        assert after == before == capture.response_body
        assert sha256(after).hexdigest() == before_sha
