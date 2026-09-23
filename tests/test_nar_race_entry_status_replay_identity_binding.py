"""No-network identity-only checks against isolated V010 mapping databases."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date
from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from scripts.migrations.versions import v010_historical_input_snapshot_schema as v010
from scripts.simulation import nar_race_entry_status_replay_identity_binding as binding
from scripts.simulation.nar_race_entry_status_raw_capture import NARRaceEntryStatusRaceIdentity
from scripts.simulation.nar_race_entry_status_source_profile_fixture_consumer import (
    load_nar_race_entry_status_source_profile_v3_fixture,
)


ROOT = Path(__file__).resolve().parents[1]
TARGET = NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
RACE = "nar:20250101:21:6"


@pytest.fixture(scope="module")
def bundle():
    return load_nar_race_entry_status_source_profile_v3_fixture(repository_root=ROOT, target=TARGET)


def _db(*, weaken_entry_unique: bool = False, weaken_race_reverse_unique: bool = False) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
    db.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER, horse_no INTEGER)")
    for statement in v010.STATEMENTS + v010.INDEXES:
        if weaken_entry_unique:
            statement = statement.replace(
                "UNIQUE (organization, source_system, internal_race_id, race_entry_id),", ""
            )
        if weaken_race_reverse_unique:
            statement = statement.replace(
                "UNIQUE (organization, source_system, internal_race_id),", ""
            )
        db.execute(statement)
    db.execute("INSERT INTO races(id) VALUES(1)")
    db.execute("INSERT INTO historical_input_source_identities VALUES('NAR','nar_official')")
    db.execute("INSERT INTO historical_input_external_races VALUES('NAR','nar_official',?,1)", (RACE,))
    for number in range(1, 15):
        db.execute("INSERT INTO horses(id,race_id,horse_no) VALUES(?,?,?)", (100 + number, 1, number))
        db.execute(
            "INSERT INTO historical_input_external_entries VALUES('NAR','nar_official',?,?,1,?)",
            (RACE, f"{RACE}:entry:{number}", 100 + number),
        )
    db.commit()
    db.execute("PRAGMA query_only=ON")
    return db


def _classification(bundle, db, expected):
    with pytest.raises(binding.NARRaceEntryStatusReplayIdentityBindingError) as caught:
        binding.bind_nar_race_entry_status_v3_identity(bundle=bundle, connection=db)
    assert caught.value.classification == expected
    assert not db.in_transaction


def test_complete_identity_only_binding(bundle):
    db = _db()
    first = binding.bind_nar_race_entry_status_v3_identity(bundle=bundle, connection=db)
    second = binding.bind_nar_race_entry_status_v3_identity(bundle=bundle, connection=db)
    assert first == second
    assert type(first) is binding.NARRaceEntryStatusReplayIdentityBinding
    assert first.target == TARGET
    assert (first.organization, first.source_system, first.external_race_id, first.internal_race_id) == (
        "NAR", "nar_official", RACE, 1
    )
    assert type(first.entry_bindings) is tuple
    assert tuple(item.horse_no for item in first.entry_bindings) == tuple(range(1, 15))
    assert tuple(item.external_entry_id for item in first.entry_bindings) == tuple(
        f"{RACE}:entry:{number}" for number in range(1, 15)
    )
    assert all(item.external_horse_id.startswith("nar:horse:") for item in first.entry_bindings)
    assert first.entry_bindings[-1].horse_no == 14
    assert type(first.entry_bindings[0]) is binding.NARRaceEntryStatusReplayEntryIdentityBinding
    assert tuple(item.name for item in fields(first)) == (
        "target", "organization", "source_system", "external_race_id", "internal_race_id", "entry_bindings"
    )
    assert tuple(item.name for item in fields(first.entry_bindings[0])) == (
        "external_entry_id", "external_horse_id", "horse_no", "race_entry_id"
    )
    with pytest.raises(FrozenInstanceError):
        first.internal_race_id = 2
    with pytest.raises(AttributeError):
        first.status = "active"
    assert not db.in_transaction
    assert db.execute("PRAGMA query_only").fetchone() == (1,)
    assert db.execute("PRAGMA foreign_keys").fetchone() == (1,)
    assert db.execute("SELECT count(*) FROM historical_input_external_entries").fetchone() == (14,)
    db.close()


@pytest.mark.parametrize("field,other", [
    ("deba_table_bytes", b"changed"),
    ("race_list_bytes", b"changed"),
    ("manifest_bytes", b"changed"),
    ("target", NARRaceEntryStatusRaceIdentity("22", date(2025, 1, 1), 6)),
    ("repository_relative_paths", ("bad", "bad", "bad")),
])
def test_forged_bundle_rejected_before_database(bundle, field, other):
    forged = replace(bundle, **{field: other}) if field not in ("target", "repository_relative_paths") else None
    if forged is None:
        # Bypass the public dataclass constructor's first-line checks to verify the binder itself.
        forged = object.__new__(type(bundle))
        for member in fields(bundle):
            object.__setattr__(forged, member.name, other if member.name == field else getattr(bundle, member.name))
    _classification(forged, _db(), "UNSUPPORTED_BUNDLE")


def test_wrong_bundle_type(bundle):
    _classification(object(), _db(), "UNSUPPORTED_BUNDLE")


def test_withdrawn_horse_identity_does_not_read_status_or_odds(bundle):
    source = binding._extract_source_entries(bundle.deba_table_bytes, RACE)
    assert source[-1].horse_no == 14
    assert source[-1].external_entry_id == f"{RACE}:entry:14"
    assert "出走取消" in bundle.deba_table_bytes.decode("utf-8")
    assert tuple(item.horse_no for item in source) == tuple(range(1, 15))


def _synthetic_html(*, changed_row: int = 0, replacement: str | None = None) -> bytes:
    rows = []
    for number in range(1, 15):
        row = (
            f'<tr><td class="horseNum">{number}</td>'
            f'<td><a class="horseName" href="/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode={number}">horse</a></td>'
            '</tr>'
        )
        if number == changed_row and replacement is not None:
            row = replacement
        rows.append(row)
    return ('<article class="raceCard"><section class="cardTable"><table>'
            + ''.join(rows) + '</table></section></article>').encode('utf-8')


@pytest.mark.parametrize("replacement", [
    '<tr><td class="horseNum">1</td><td><a class="horseName" href="/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=14">horse</a></td></tr>',
    '<tr><td class="horseNum">014</td><td><a class="horseName" href="/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=14">horse</a></td></tr>',
    '<tr><td class="horseNum"> 14</td><td><a class="horseName" href="/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=14">horse</a></td></tr>',
    '<tr><td class="horseNum">14</td><td class="horseNum">14</td><td><a class="horseName" href="/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=14">horse</a></td></tr>',
    '<tr><td class="horseNum">14</td><td>no link</td></tr>',
    '<tr><td class="horseNum">14</td><td><a class="horseName" href="/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=14">horse</a><a class="horseName" href="/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=15">horse</a></td></tr>',
    '<tr><td class="horseNum">14</td><td><a class="horseName" href="https://example.com/horse/14">horse</a></td></tr>',
    '<tr><td>missing horseNum</td></tr>',
])
def test_source_extractor_rejects_ambiguous_identity(replacement):
    with pytest.raises(binding.NARRaceEntryStatusReplayIdentityBindingError) as caught:
        binding._extract_source_entries(_synthetic_html(changed_row=14, replacement=replacement), RACE)
    assert caught.value.classification == "SOURCE_ENTRY_IDENTITY_INVALID"


def test_source_extractor_rejects_invalid_utf8_or_ambiguous_table():
    for payload in (b'\xff', _synthetic_html() + _synthetic_html()):
        with pytest.raises(binding.NARRaceEntryStatusReplayIdentityBindingError) as caught:
            binding._extract_source_entries(payload, RACE)
        assert caught.value.classification == "SOURCE_ENTRY_IDENTITY_INVALID"


@pytest.mark.parametrize("sql,classification", [
    ("DELETE FROM historical_input_external_entries; DELETE FROM historical_input_external_races", "INTERNAL_RACE_MAPPING_MISSING"),
    ("DELETE FROM historical_input_external_entries WHERE external_entry_id='nar:20250101:21:6:entry:14'", "ENTRY_MAPPING_MISSING"),
    ("UPDATE horses SET horse_no=99 WHERE id=114", "HORSE_NUMBER_CONTRADICTION"),
    ("INSERT INTO horses(id,race_id,horse_no) VALUES(999,1,99)", None),
])
def test_mapping_fail_closed(bundle, sql, classification):
    db = _db()
    db.execute("PRAGMA query_only=OFF")
    for statement in sql.split("; "):
        db.execute(statement)
    db.commit()
    db.execute("PRAGMA query_only=ON")
    if classification:
        _classification(bundle, db, classification)
    else:
        assert len(binding.bind_nar_race_entry_status_v3_identity(bundle=bundle, connection=db).entry_bindings) == 14
    db.close()


def test_unexpected_database_entry(bundle):
    db = _db()
    db.execute("PRAGMA query_only=OFF")
    db.execute("INSERT INTO horses(id,race_id,horse_no) VALUES(999,1,99)")
    db.execute(
        "INSERT INTO historical_input_external_entries VALUES('NAR','nar_official',?,?,1,999)",
        (RACE, f"{RACE}:entry:99"),
    )
    db.commit()
    db.execute("PRAGMA query_only=ON")
    _classification(bundle, db, "DATABASE_ENTRY_SET_CONTRADICTION")
    db.close()


def test_duplicate_mapped_entry_id_is_rejected(bundle, monkeypatch):
    db = _db(weaken_entry_unique=True)
    db.execute("PRAGMA query_only=OFF")
    db.execute(
        "UPDATE historical_input_external_entries SET race_entry_id=101 WHERE external_entry_id=?",
        (f"{RACE}:entry:2",),
    )
    db.commit()
    db.execute("PRAGMA query_only=ON")
    monkeypatch.setattr(binding, "_validate_schema", lambda unused: None)
    _classification(bundle, db, "DUPLICATE_RACE_ENTRY_ID")
    db.close()


def test_reverse_race_mapping_contradiction(bundle, monkeypatch):
    db = _db(weaken_race_reverse_unique=True)
    db.execute("PRAGMA query_only=OFF")
    db.execute(
        "INSERT INTO historical_input_external_races VALUES('NAR','nar_official','nar:other:race',1)"
    )
    db.commit()
    db.execute("PRAGMA query_only=ON")
    monkeypatch.setattr(binding, "_validate_schema", lambda unused: None)
    _classification(bundle, db, "INTERNAL_RACE_MAPPING_CONTRADICTION")
    db.close()


@pytest.mark.parametrize("sql,expected", [
    ("DELETE FROM races WHERE id=1", "INTERNAL_RACE_MAPPING_CONTRADICTION"),
    ("DELETE FROM horses WHERE id=114", "INTERNAL_ENTRY_ROW_MISSING"),
    ("UPDATE historical_input_external_entries SET internal_race_id=2 WHERE external_entry_id='nar:20250101:21:6:entry:14'", "ENTRY_MAPPING_CONTRADICTION"),
])
def test_orphan_or_contradictory_row_fails_closed(bundle, monkeypatch, sql, expected):
    db = _db()
    db.execute("PRAGMA query_only=OFF")
    db.execute("PRAGMA foreign_keys=OFF")
    db.execute(sql)
    db.commit()
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA query_only=ON")
    monkeypatch.setattr(binding, "_validate_schema", lambda unused: None)
    _classification(bundle, db, expected)
    db.close()


def test_foreign_key_integrity_checked_before_mapping(bundle):
    db = _db()
    db.execute("PRAGMA query_only=OFF")
    db.execute("PRAGMA foreign_keys=OFF")
    db.execute("DELETE FROM horses WHERE id=114")
    db.commit()
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA query_only=ON")
    _classification(bundle, db, "SQLITE_SCHEMA_INVALID")
    db.close()


def test_horse_number_is_not_lookup_key_and_cwd_independent(bundle, monkeypatch, tmp_path):
    db = _db()
    db.execute("PRAGMA query_only=OFF")
    db.execute("INSERT INTO horses(id,race_id,horse_no) VALUES(999,1,14)")
    db.commit()
    db.execute("PRAGMA query_only=ON")
    monkeypatch.chdir(tmp_path)
    result = binding.bind_nar_race_entry_status_v3_identity(bundle=bundle, connection=db)
    assert result.entry_bindings[-1].race_entry_id == 114
    db.close()


def test_connection_preconditions(bundle):
    db = _db()
    db.execute("PRAGMA query_only=OFF")
    _classification(bundle, db, "SQLITE_CONNECTION_INVALID")
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA foreign_keys=OFF")
    _classification(bundle, db, "SQLITE_CONNECTION_INVALID")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("BEGIN")
    with pytest.raises(binding.NARRaceEntryStatusReplayIdentityBindingError) as caught:
        binding.bind_nar_race_entry_status_v3_identity(bundle=bundle, connection=db)
    assert caught.value.classification == "SQLITE_CONNECTION_INVALID"
    assert db.in_transaction  # caller transaction remains untouched
    db.rollback()
    db.execute("ATTACH DATABASE ':memory:' AS auxiliary")
    _classification(bundle, db, "SQLITE_CONNECTION_INVALID")
    db.close()
    with pytest.raises(binding.NARRaceEntryStatusReplayIdentityBindingError) as caught:
        binding.bind_nar_race_entry_status_v3_identity(bundle=bundle, connection=object())
    assert caught.value.classification == "SQLITE_CONNECTION_INVALID"


def test_required_schema_is_inspected(bundle):
    db = _db()
    db.execute("PRAGMA query_only=OFF")
    db.execute("DROP INDEX ux_horses_race_id_id")
    db.commit()
    db.execute("PRAGMA query_only=ON")
    _classification(bundle, db, "SQLITE_SCHEMA_INVALID")
    db.close()


@pytest.mark.parametrize("table_index,old,new", [
    (0, "source_system TEXT NOT NULL", "source_system INTEGER NOT NULL"),
    (0, "PRIMARY KEY (organization, source_system)", "PRIMARY KEY (source_system, organization)"),
    (1, "external_race_id TEXT NOT NULL", "external_race_id INTEGER NOT NULL"),
    (1, "PRIMARY KEY (organization, source_system, external_race_id)", "PRIMARY KEY (source_system, organization, external_race_id)"),
    (1, "UNIQUE (organization, source_system, internal_race_id)", "UNIQUE (source_system, internal_race_id)"),
    (1, "ON DELETE RESTRICT ON UPDATE RESTRICT", "ON DELETE CASCADE ON UPDATE RESTRICT"),
    (2, "PRIMARY KEY (organization, source_system, external_race_id, external_entry_id)", "PRIMARY KEY (organization, source_system, external_entry_id)"),
    (2, "UNIQUE (organization, source_system, internal_race_id, race_entry_id)", "UNIQUE (organization, internal_race_id, race_entry_id)"),
    (2, "ON DELETE RESTRICT ON UPDATE RESTRICT", "ON DELETE CASCADE ON UPDATE RESTRICT"),
])
def test_schema_mutation_is_rejected(table_index, old, new):
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
    db.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER, horse_no INTEGER)")
    for index, statement in enumerate(v010.STATEMENTS):
        if index == table_index:
            assert old in statement
            statement = statement.replace(old, new, 1)
        db.execute(statement)
    for statement in v010.INDEXES:
        db.execute(statement)
    db.commit()
    db.execute("PRAGMA query_only=ON")
    with pytest.raises(binding.NARRaceEntryStatusReplayIdentityBindingError) as caught:
        binding._validate_schema(db)
    assert caught.value.classification == "SQLITE_SCHEMA_INVALID"
    db.close()


@pytest.mark.parametrize("table", [
    "historical_input_source_identities", "historical_input_external_races",
    "historical_input_external_entries", "races", "horses",
])
def test_missing_required_table_rejected(table):
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE races(id INTEGER PRIMARY KEY)")
    db.execute("CREATE TABLE horses(id INTEGER PRIMARY KEY, race_id INTEGER, horse_no INTEGER)")
    for statement in v010.STATEMENTS + v010.INDEXES:
        db.execute(statement)
    db.execute("PRAGMA foreign_keys=OFF")
    db.execute(f"DROP TABLE {table}")
    db.commit()
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA query_only=ON")
    with pytest.raises(binding.NARRaceEntryStatusReplayIdentityBindingError) as caught:
        binding._validate_schema(db)
    assert caught.value.classification == "SQLITE_SCHEMA_INVALID"
    db.close()


def test_no_write_or_future_evidence_dependencies():
    source = Path(binding.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    forbidden = ("requests", "httpx", "urllib.request", "socket", "subprocess", "snapshot_builder", "daily_replay", "settlement", "payout", "odds_snapshot")
    assert not any(any(token in ast.unparse(node).lower() for token in forbidden) for node in imports)
    statements = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    assert not any(value.lstrip().upper().startswith(("INSERT ", "UPDATE ", "DELETE ", "REPLACE ", "CREATE ", "DROP ", "ALTER ", "ATTACH ", "DETACH ", "VACUUM ", "REINDEX ")) for value in statements)
    assert "WHERE race_id=? AND horse_no=?" not in source
    assert "horse_detail_url" not in source
    for table in (
        "historical_input_snapshots", "race_results", "payouts", "odds_snapshots",
        "settlement_captures", "market_odds",
    ):
        assert table not in source


def test_stable_error_classifications():
    assert binding.ERROR_CLASSIFICATIONS >= {
        "UNSUPPORTED_BUNDLE", "SQLITE_CONNECTION_INVALID", "SQLITE_SCHEMA_INVALID",
        "EXTERNAL_RACE_IDENTITY_CONTRADICTION", "INTERNAL_RACE_MAPPING_MISSING",
        "INTERNAL_RACE_MAPPING_AMBIGUOUS", "INTERNAL_RACE_MAPPING_CONTRADICTION",
        "SOURCE_ENTRY_IDENTITY_INVALID", "ENTRY_MAPPING_MISSING", "ENTRY_MAPPING_AMBIGUOUS",
        "ENTRY_MAPPING_CONTRADICTION", "DATABASE_ENTRY_SET_CONTRADICTION",
        "DUPLICATE_RACE_ENTRY_ID", "INTERNAL_ENTRY_ROW_MISSING",
        "HORSE_NUMBER_CONTRADICTION", "CROSS_PROVIDER_IDENTITY_UNSUPPORTED",
    }


def test_published_fixture_unchanged():
    paths = (
        ROOT / "tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/deba_table.html",
        ROOT / "tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/race_list.html",
        ROOT / "tests/fixtures/nar_race_entry_status/source_profiles/v3/baba_21__2025-01-01__race_06/manifest.json",
    )
    for path, (length, digest) in zip(paths, binding._FROZEN_BYTES):
        payload = path.read_bytes()
        assert len(payload) == length and sha256(payload).hexdigest() == digest
