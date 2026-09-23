"""Current-only status evidence from the frozen NAR V3 fixture, with no DB access."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup
import pytest

from scripts.simulation import nar_race_entry_status_interpretation as status
from scripts.simulation import nar_race_entry_status_replay_identity_binding as identity
from scripts.simulation.nar_race_entry_status_raw_capture import NARRaceEntryStatusRaceIdentity
from scripts.simulation.nar_race_entry_status_source_profile_fixture_consumer import (
    load_nar_race_entry_status_source_profile_v3_fixture,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET = NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
RACE_ID = "nar:20250101:21:6"


@pytest.fixture(scope="module")
def bundle():
    return load_nar_race_entry_status_source_profile_v3_fixture(repository_root=ROOT, target=TARGET)


@pytest.fixture(scope="module")
def binding(bundle):
    source = identity._extract_source_entries(bundle.deba_table_bytes, RACE_ID)
    entries = tuple(
        identity.NARRaceEntryStatusReplayEntryIdentityBinding(
            item.external_entry_id, item.external_horse_id, item.horse_no, 100 + item.horse_no
        )
        for item in source
    )
    return identity.NARRaceEntryStatusReplayIdentityBinding(
        TARGET, "NAR", "nar_official", RACE_ID, 1, entries
    )


def _fails(classification, *, bundle, binding):
    with pytest.raises(status.NARRaceEntryStatusInterpretationError) as caught:
        status.interpret_nar_race_entry_status_v3(bundle=bundle, binding=binding)
    assert caught.value.classification == classification


def _deba_mutation(bundle, mutate):
    soup = BeautifulSoup(bundle.deba_table_bytes.decode("utf-8"), "html.parser")
    table = next(x for x in soup.select("article.raceCard section.cardTable table") if x.find("td", class_="horseNum"))
    rows = table.find("tbody", recursive=False).find_all("tr", recursive=False)
    first = {int(cell.get_text(strip=True)): index for index, row in enumerate(rows)
             for cell in row.find_all("td", class_="horseNum", recursive=False)}
    mutate(soup, rows, first)
    return str(soup).encode("utf-8")


def _race_mutation(bundle, mutate):
    soup = BeautifulSoup(bundle.race_list_bytes.decode("utf-8"), "html.parser")
    table = soup.select_one("table.changeInfo")
    row = next(row for row in table.select("tr.data") if row.find("td").get_text(strip=True) == "6R")
    mutate(soup, table, row)
    return str(soup).encode("utf-8")


def test_complete_current_observation_is_immutable_and_deterministic(bundle, binding):
    result = status.interpret_nar_race_entry_status_v3(bundle=bundle, binding=binding)
    assert result == status.interpret_nar_race_entry_status_v3(bundle=bundle, binding=binding)
    assert type(result) is status.NARRaceEntryStatusInterpretation
    assert tuple(field.name for field in fields(result)) == (
        "target", "organization", "source_system", "external_race_id", "internal_race_id",
        "acquisition_semantics", "current_observation_authority", "historical_status_authority",
        "entry_statuses", "evidence_timestamps",
    )
    assert result.target == TARGET
    assert (result.organization, result.source_system, result.external_race_id, result.internal_race_id) == (
        "NAR", "nar_official", RACE_ID, 1
    )
    assert result.acquisition_semantics == "CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET"
    assert result.current_observation_authority == "SUPPORTED"
    assert result.historical_status_authority == "HISTORICAL_ENTRY_STATUS_AUTHORITY_BLOCKED"
    assert type(result.entry_statuses) is tuple and len(result.entry_statuses) == 14
    assert tuple(item.horse_no for item in result.entry_statuses) == tuple(range(1, 15))
    assert tuple(item.race_entry_id for item in result.entry_statuses) == tuple(range(101, 115))
    assert all(item.current_observation == "NO_EXPLICIT_WITHDRAWAL_EVIDENCE" for item in result.entry_statuses[:-1])
    assert result.entry_statuses[-1].current_observation == "EXPLICIT_WITHDRAWAL_PRESENT"
    assert all(item.current_observation != "ACTIVE" for item in result.entry_statuses)
    assert all(item.evidence_roles == ("deba_table", "race_list") for item in result.entry_statuses)
    assert type(result.entry_statuses[-1]) is status.NARRaceEntryCurrentStatusEvidence
    assert type(result.evidence_timestamps) is tuple and len(result.evidence_timestamps) == 2
    assert tuple(field.name for field in fields(result.entry_statuses[-1])) == (
        "external_entry_id", "race_entry_id", "horse_no", "current_observation", "evidence_roles"
    )
    with pytest.raises(FrozenInstanceError):
        result.internal_race_id = 2
    with pytest.raises(AttributeError):
        result.market_eligibility = "SUPPORTED"


def test_capture_times_are_actual_post_target_observations(bundle, binding):
    result = status.interpret_nar_race_entry_status_v3(bundle=bundle, binding=binding)
    assert tuple((item.role, item.observed_at, item.captured_at) for item in result.evidence_timestamps) == (
        ("deba_table", "2026-09-21T23:27:42.678776Z", "2026-09-21T23:27:42.678947Z"),
        ("race_list", "2026-09-21T23:27:43.165338Z", "2026-09-21T23:27:43.165400Z"),
    )
    assert all(item.capture_identity.startswith("nar-race-entry-status-capture-v1:") for item in result.evidence_timestamps)


def test_current_deba_field_only_ignores_historical_cancellation_text(bundle):
    def mutate(soup, rows, first):
        previous_race = rows[first[1]].select_one("div.raceInfo")
        previous_race.string = "past race 出走取消"
    payload = _deba_mutation(bundle, mutate)
    assert status._deba_current_changes(payload) == frozenset({14})


def test_current_status_does_not_require_odds(bundle):
    def mutate(soup, rows, first):
        for cell in soup.select("td.odds_weight"):
            cell.clear()
    assert status._deba_current_changes(_deba_mutation(bundle, mutate)) == frozenset({14})


@pytest.mark.parametrize("number", [1, 13, 14])
def test_deba_current_field_is_the_only_status_authority(bundle, number):
    def mutate(soup, rows, first):
        cell = rows[first[number] + 4].select_one("td.info")
        cell.string = "出走取消" if number != 14 else ""
    expected = frozenset({14, number}) if number != 14 else frozenset()
    assert status._deba_current_changes(_deba_mutation(bundle, mutate)) == expected


@pytest.mark.parametrize("replacement,classification", [
    ("", "STATUS_EVIDENCE_MISSING"),
    ("5R", "STATUS_EVIDENCE_MISSING"),
])
def test_race_list_wrong_or_missing_target_race(bundle, replacement, classification):
    def mutate(soup, table, row):
        if replacement:
            row.find_all("td", recursive=False)[0].string = replacement
        else:
            row.decompose()
    with pytest.raises(status.NARRaceEntryStatusInterpretationError) as caught:
        status._race_list_current_changes(_race_mutation(bundle, mutate))
    assert caught.value.classification == classification


@pytest.mark.parametrize("index,value,expected", [
    (1, "13", "HORSE_ASSOCIATION_CONTRADICTION"),
    (3, "変更", "UNSUPPORTED_STATUS_REPRESENTATION"),
])
def test_race_list_exact_horse_and_change_label(bundle, index, value, expected):
    def mutate(soup, table, row):
        row.find_all("td", recursive=False)[index].string = value
    with pytest.raises(status.NARRaceEntryStatusInterpretationError) as caught:
        status._race_list_current_changes(_race_mutation(bundle, mutate))
    assert caught.value.classification == expected


def test_duplicate_race_list_target_change_row_fails(bundle):
    def mutate(soup, table, row):
        row.insert_after(BeautifulSoup(str(row), "html.parser").tr)
    with pytest.raises(status.NARRaceEntryStatusInterpretationError) as caught:
        status._race_list_current_changes(_race_mutation(bundle, mutate))
    assert caught.value.classification == "STATUS_EVIDENCE_AMBIGUOUS"


@pytest.mark.parametrize("field", ["deba_table_bytes", "race_list_bytes", "manifest_bytes"])
def test_forged_bundle_bytes_fail_first(bundle, binding, field):
    forged = replace(bundle, **{field: b"forged"})
    _fails("UNSUPPORTED_BUNDLE", bundle=forged, binding=binding)


def test_wrong_bundle_type_fails(binding):
    _fails("UNSUPPORTED_BUNDLE", bundle=object(), binding=binding)


def test_wrong_binding_type_fails(bundle):
    _fails("UNSUPPORTED_BINDING", bundle=bundle, binding=object())


@pytest.mark.parametrize("change,expected", [
    ({"target": NARRaceEntryStatusRaceIdentity("22", date(2025, 1, 1), 6)}, "TARGET_CONTRADICTION"),
    ({"external_race_id": "nar:20250101:21:5"}, "UNSUPPORTED_BINDING"),
    ({"entry_bindings": ()}, "ENTRY_SET_CONTRADICTION"),
])
def test_binding_target_race_and_complete_set(bundle, binding, change, expected):
    _fails(expected, bundle=bundle, binding=replace(binding, **change))


def test_extra_binding_entry_and_duplicate_internal_id_fail(bundle, binding):
    extra = replace(binding.entry_bindings[-1], horse_no=15, external_entry_id=f"{RACE_ID}:entry:15", race_entry_id=115)
    _fails("ENTRY_SET_CONTRADICTION", bundle=bundle, binding=replace(binding, entry_bindings=binding.entry_bindings + (extra,)))
    duplicate = replace(binding.entry_bindings[-1], race_entry_id=binding.entry_bindings[0].race_entry_id)
    _fails("ENTRY_SET_CONTRADICTION", bundle=bundle, binding=replace(binding, entry_bindings=binding.entry_bindings[:-1] + (duplicate,)))


def test_source_and_binding_horse_identity_must_agree(bundle, binding):
    bad = replace(binding.entry_bindings[0], external_horse_id="nar:horse:999")
    _fails("ENTRY_SET_CONTRADICTION", bundle=bundle, binding=replace(binding, entry_bindings=(bad,) + binding.entry_bindings[1:]))


def test_deba_race_list_disagreement_fails_closed(bundle, binding, monkeypatch):
    monkeypatch.setattr(status, "_deba_current_changes", lambda payload: frozenset())
    _fails("DEBA_RACELIST_CONTRADICTION", bundle=bundle, binding=binding)


def test_profile_b_contradiction_fails_closed(bundle, binding, monkeypatch):
    profile_type = type(bundle.manifest.qualification.profile_b)
    original = profile_type.to_canonical_dict
    def contradictory(value):
        data = original(value)
        data["predicate_results"][-1]["safe_fields"]["withdrawal_label_match"] = False
        return data
    monkeypatch.setattr(status, "_authentic_bundle", lambda value: value)
    monkeypatch.setattr(profile_type, "to_canonical_dict", contradictory)
    _fails("PROFILE_B_CONTRADICTION", bundle=bundle, binding=binding)


def test_temporal_contradiction_fails_closed(bundle, binding, monkeypatch):
    # A test-only replacement isolates the temporal gate from frozen manifest hashing.
    summary = bundle.manifest.fixture_set.capture_summary
    original = summary.deba_table
    modified = object.__new__(type(original))
    for member in fields(original):
        value = getattr(original, member.name)
        if member.name in {"requested_at", "observed_at", "captured_at"}:
            value = value.replace("2026-", "2024-", 1)
        object.__setattr__(modified, member.name, value)
    fake_summary = object.__new__(type(summary))
    object.__setattr__(fake_summary, "deba_table", modified)
    object.__setattr__(fake_summary, "race_list", summary.race_list)
    object.__setattr__(fake_summary, "closed_bundle_identity", summary.closed_bundle_identity)
    fixture = object.__new__(type(bundle.manifest.fixture_set))
    for member in fields(bundle.manifest.fixture_set):
        object.__setattr__(fixture, member.name, fake_summary if member.name == "capture_summary" else getattr(bundle.manifest.fixture_set, member.name))
    manifest = object.__new__(type(bundle.manifest))
    for member in fields(bundle.manifest):
        object.__setattr__(manifest, member.name, fixture if member.name == "fixture_set" else getattr(bundle.manifest, member.name))
    forged = object.__new__(type(bundle))
    for member in fields(bundle):
        object.__setattr__(forged, member.name, manifest if member.name == "manifest" else getattr(bundle, member.name))
    with pytest.raises(status.NARRaceEntryStatusInterpretationError) as caught:
        status._timestamps(forged)
    assert caught.value.classification == "TEMPORAL_AUTHORITY_CONTRADICTION"


def test_static_no_database_network_market_snapshot_or_replay_dependency():
    source = (ROOT / "scripts/simulation/nar_race_entry_status_interpretation.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    assert not any(name.startswith(("sqlite3", "requests", "httpx", "socket", "subprocess", "urllib.request")) for name in imports)
    assert "connection.execute" not in source
    assert "build_historical_input_snapshot" not in source
    assert "run_nar_daily_replay" not in source
    assert "market_eligibility:" not in source
    assert "Path.cwd" not in source


def test_current_working_directory_does_not_affect_interpretation(bundle, binding, tmp_path, monkeypatch):
    expected = status.interpret_nar_race_entry_status_v3(bundle=bundle, binding=binding)
    monkeypatch.chdir(tmp_path)
    assert status.interpret_nar_race_entry_status_v3(bundle=bundle, binding=binding) == expected
