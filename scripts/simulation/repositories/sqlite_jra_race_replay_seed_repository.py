"""Atomic SQLite materialization for immutable JRA replay seeds."""

from __future__ import annotations

from datetime import date as _date, datetime as _datetime, timezone as _timezone
import hashlib as _hashlib
import sqlite3

from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference as _Evidence
from scripts.simulation.historical_input_source_records import HistoricalInputSourceRecord as _Record
from scripts.simulation.jra_official_identity import (
    JRAOfficialIdentityValidationError as _IdentityError,
    parse_jra_external_race_id as _parse_race_id,
)
from scripts.simulation.jra_official_response_live_capture import (
    JRATargetRaceNavigationCaptureResult as _NavigationResult,
)
from scripts.simulation.jra_race_replay_seed import (
    JRARaceReplaySeed as _Seed,
    JRARaceReplaySeedEntry as _SeedEntry,
    JRARaceReplaySeedValidationError as _SeedValidationError,
    build_jra_race_replay_seed as _build_seed,
    is_jra_race_replay_seed_id as _is_seed_id,
    jra_race_replay_seed_datetime_text as _datetime_text,
)
from scripts.simulation.jra_target_race_card_resolution import (
    JRATargetRaceCardResolution as _Resolution,
)
from scripts.simulation.jra_target_race_input_source import (
    JRATargetRaceSourceCollection as _TargetSources,
)

from .errors import RepositoryConflictError, RepositoryDataIntegrityError, RepositoryValidationError


_ORGANIZATION = "JRA"
_SOURCE_SYSTEM = "jra_official"


class SQLiteJRARaceReplaySeedRepository:
    """Persist exact JRA materialization proof without capture/archive ownership."""

    __slots__ = ("_connection",)

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if type(connection) is not sqlite3.Connection:
            raise RepositoryValidationError("connection must be exact sqlite3.Connection")
        self._connection = connection
        self._ensure_foreign_keys()

    def materialize_seed(
        self,
        *,
        dataset_id: str,
        navigation_capture_result: _NavigationResult,
        target_race_card_resolution: _Resolution,
        target_sources: _TargetSources,
        information_cutoff: _datetime,
    ) -> _Seed:
        """Atomically create or revalidate one exact JRA race and entry mapping seed."""

        if self._connection.in_transaction:
            raise RepositoryValidationError("materialize_seed requires no active transaction")
        facts = self._validate_lineage(
            dataset_id=dataset_id,
            navigation_capture_result=navigation_capture_result,
            target_race_card_resolution=target_race_card_resolution,
            target_sources=target_sources,
            information_cutoff=information_cutoff,
        )
        self._ensure_foreign_keys()
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._ensure_source_identity()
            internal_race_id = self._resolve_or_create_race(facts=facts)
            entries = self._resolve_or_create_entries(facts=facts, internal_race_id=internal_race_id)
            seed = _build_seed(
                dataset_id=facts.dataset_id,
                external_race_id=facts.external_race_id,
                internal_race_id=internal_race_id,
                target_race_selection_capture_id=facts.v4_capture_id,
                target_race_card_capture_id=facts.v3_capture_id,
                target_race_card_response_sha256=facts.v3_response_sha256,
                canonical_target_race_card_url=facts.card_url,
                captured_at=facts.captured_at,
                information_cutoff=facts.information_cutoff,
                entries=entries,
            )
            existing = self._find_existing_natural_identity(seed)
            if existing is not None:
                existing_seed_id, existing_digest = existing
                if existing_digest != seed.content_sha256 or existing_seed_id != seed.seed_id:
                    raise RepositoryConflictError("JRA replay seed differs from existing natural identity")
                reconstructed = self._load_seed_unvalidated(seed_id=seed.seed_id)
                if reconstructed != seed:
                    raise RepositoryDataIntegrityError("stored JRA replay seed differs from identical materialization")
                self._connection.commit()
                return reconstructed
            self._insert_seed(seed)
            self._connection.commit()
            return seed
        except RepositoryConflictError:
            self._connection.rollback()
            raise
        except RepositoryDataIntegrityError:
            self._connection.rollback()
            raise
        except _SeedValidationError as error:
            self._connection.rollback()
            raise RepositoryDataIntegrityError("materialized JRA replay seed is invalid") from error
        except sqlite3.IntegrityError as error:
            self._connection.rollback()
            raise RepositoryDataIntegrityError("SQLite rejected JRA replay seed materialization") from error
        except sqlite3.Error as error:
            self._connection.rollback()
            raise RepositoryDataIntegrityError("SQLite failed JRA replay seed materialization") from error
        except BaseException:
            self._connection.rollback()
            raise

    def load_seed(self, *, seed_id: str) -> _Seed | None:
        """Load and fully revalidate one immutable seed by its exact deterministic ID."""

        if not _is_seed_id(seed_id):
            raise RepositoryValidationError("seed_id is invalid")
        try:
            row = self._connection.execute(
                "SELECT seed_id FROM jra_race_replay_seeds WHERE seed_id=?", (seed_id,)
            ).fetchone()
        except sqlite3.Error as error:
            raise RepositoryDataIntegrityError("could not read JRA replay seed") from error
        if row is None:
            return None
        try:
            return self._load_seed_unvalidated(seed_id=seed_id)
        except RepositoryDataIntegrityError:
            raise
        except (_SeedValidationError, _IdentityError, KeyError, TypeError, ValueError, sqlite3.Error) as error:
            raise RepositoryDataIntegrityError("stored JRA replay seed violates repository invariants") from error

    def _validate_lineage(
        self,
        *,
        dataset_id: object,
        navigation_capture_result: object,
        target_race_card_resolution: object,
        target_sources: object,
        information_cutoff: object,
    ) -> "_MaterializationFacts":
        if type(navigation_capture_result) is not _NavigationResult:
            raise RepositoryValidationError("navigation_capture_result must be exact JRATargetRaceNavigationCaptureResult")
        if type(target_race_card_resolution) is not _Resolution:
            raise RepositoryValidationError("target_race_card_resolution must be exact JRATargetRaceCardResolution")
        if type(target_sources) is not _TargetSources:
            raise RepositoryValidationError("target_sources must be exact JRATargetRaceSourceCollection")
        try:
            dataset = _Seed(
                dataset_id=dataset_id,
                external_race_id="jra:race:2025:01:01:01:01",
                internal_race_id=1,
                target_race_selection_capture_id="jra-capture-v4:" + "0" * 64,
                target_race_card_capture_id="jra-capture-v3:" + "0" * 64,
                target_race_card_response_sha256="0" * 64,
                canonical_target_race_card_url="https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0101202501010120250101%2F00",
                captured_at=_datetime(2025, 1, 1, tzinfo=_timezone.utc),
                information_cutoff=_datetime(2025, 1, 1, tzinfo=_timezone.utc),
                entries=(_SeedEntry(0, "jra:race:2025:01:01:01:01:entry:1", "jra:horse:0000000001", 1, 1),),
            ).dataset_id
        except _SeedValidationError as error:
            raise RepositoryValidationError("dataset_id is invalid") from error
        resolution = target_race_card_resolution
        navigation = navigation_capture_result
        if (
            navigation.target_race_selection_capture_id != resolution.target_race_selection_capture_id
            or navigation.discovery != resolution.discovery
        ):
            raise RepositoryValidationError("navigation result and target-card resolution provenance disagree")
        try:
            race = _parse_race_id(resolution.discovery.locator.external_race_id)
        except _IdentityError as error:
            raise RepositoryValidationError("target-card resolution race identity is invalid") from error
        track = target_sources.target_track_record
        if (
            type(track) is not _Record
            or track.record_kind != "track"
            or track.organization != _ORGANIZATION
            or track.source_system != _SOURCE_SYSTEM
            or track.external_race_id != race.external_race_id
        ):
            raise RepositoryValidationError("target source track identity is invalid")
        if resolution.response.response_url != resolution.discovery.locator.canonical_target_race_card_url:
            raise RepositoryValidationError("target-card resolution response URL is invalid")
        response_sha256 = _hashlib.sha256(resolution.response.response_body).hexdigest()
        for record in target_sources.source_records:
            if (
                type(record) is not _Record
                or record.organization != _ORGANIZATION
                or record.source_system != _SOURCE_SYSTEM
                or record.external_race_id != race.external_race_id
                or record.provider_record_id is not None
                or type(record.evidence) is not tuple
                or len(record.evidence) != 1
            ):
                raise RepositoryValidationError("target source record lineage is invalid")
            evidence = record.evidence[0]
            if (
                type(evidence) is not _Evidence
                or evidence.evidence_role != record.record_kind
                or evidence.canonical_source_url != resolution.response.response_url
                or evidence.response_sha256 != response_sha256
                or evidence.observed_at != resolution.response.observed_at
                or evidence.available_at is not None
                or evidence.request_identity_sha256 is not None
            ):
                raise RepositoryValidationError("target sources do not prove the resolved target-card response")
        values = track.record_values
        scheduled = values.get("scheduled_start_at")
        if type(scheduled) is not _datetime or scheduled.tzinfo is None or scheduled.utcoffset() is None:
            raise RepositoryValidationError("target scheduled_start_at is invalid")
        cutoff = _normalize_utc(information_cutoff, "information_cutoff")
        captured = _normalize_utc(resolution.captured_at, "captured_at")
        scheduled_utc = _normalize_utc(scheduled, "scheduled_start_at")
        if captured > cutoff or cutoff > scheduled_utc:
            raise RepositoryValidationError("JRA replay causal time guard is invalid")
        if resolution.target_race_card_capture_id == "" or resolution.target_race_card_response_sha256 == "":
            raise RepositoryValidationError("target-card provenance is invalid")
        entries: list[_TargetEntryFacts] = []
        for entry in target_sources.target_entry_records:
            if type(entry) is not _Record or entry.record_kind != "entry" or entry.external_race_id != race.external_race_id:
                raise RepositoryValidationError("target entry source record is invalid")
            external_entry_id = entry.external_entry_id
            external_horse_id = entry.record_values.get("external_horse_id")
            horse_no = entry.record_values.get("horse_no")
            if type(external_entry_id) is not str or type(external_horse_id) is not str or type(horse_no) is not int:
                raise RepositoryValidationError("target entry identity values are invalid")
            entries.append(_TargetEntryFacts(external_entry_id, external_horse_id, horse_no))
        if not entries:
            raise RepositoryValidationError("target entry set is empty")
        return _MaterializationFacts(
            dataset_id=dataset,
            external_race_id=race.external_race_id,
            race_number=int(race.race_number),
            v4_capture_id=resolution.target_race_selection_capture_id,
            v3_capture_id=resolution.target_race_card_capture_id,
            v3_response_sha256=resolution.target_race_card_response_sha256,
            card_url=resolution.response.response_url,
            captured_at=captured,
            information_cutoff=cutoff,
            track_values=values,
            entries=tuple(entries),
        )

    def _ensure_source_identity(self) -> None:
        row = self._connection.execute(
            "SELECT organization,source_system FROM historical_input_source_identities WHERE organization=? AND source_system=?",
            (_ORGANIZATION, _SOURCE_SYSTEM),
        ).fetchone()
        if row is None:
            self._connection.execute(
                "INSERT INTO historical_input_source_identities(organization,source_system) VALUES(?,?)",
                (_ORGANIZATION, _SOURCE_SYSTEM),
            )
        elif tuple(row) != (_ORGANIZATION, _SOURCE_SYSTEM):
            raise RepositoryDataIntegrityError("stored JRA source identity is contradictory")

    def _resolve_or_create_race(self, *, facts: "_MaterializationFacts") -> int:
        row = self._connection.execute(
            """SELECT internal_race_id FROM historical_input_external_races
               WHERE organization=? AND source_system=? AND external_race_id=?""",
            (_ORGANIZATION, _SOURCE_SYSTEM, facts.external_race_id),
        ).fetchone()
        if row is not None:
            if type(row[0]) is not int or row[0] <= 0:
                raise RepositoryDataIntegrityError("stored JRA external race mapping is invalid")
            self._validate_mapped_race(internal_race_id=row[0], facts=facts)
            self._require_race_seed_proof(
                external_race_id=facts.external_race_id,
                internal_race_id=row[0],
            )
            return row[0]
        target_date = facts.track_values["target_race_date"]
        place = facts.track_values["place"]
        if type(target_date) is not _date or type(place) is not str:
            raise RepositoryValidationError("normalized target race facts are invalid")
        collisions = self._connection.execute(
            """SELECT id FROM races WHERE race_date=? AND organization=? AND place=? AND race_no=?""",
            (target_date.isoformat(), _ORGANIZATION, place, facts.race_number),
        ).fetchall()
        if collisions:
            raise RepositoryDataIntegrityError("unproven legacy race collision prevents JRA materialization")
        self._require_legacy_columns(
            "races", ("id", "race_date", "organization", "place", "race_no", "race_name", "distance", "track", "weather", "track_condition", "horse_count")
        )
        cursor = self._connection.execute(
            """INSERT INTO races(
                    race_date,organization,place,race_no,race_name,distance,track,weather,track_condition,horse_count
                ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                target_date.isoformat(),
                _ORGANIZATION,
                place,
                facts.race_number,
                facts.track_values["race_name"],
                facts.track_values["distance_m"],
                facts.track_values["track"],
                facts.track_values["weather"],
                facts.track_values["track_condition"],
                len(facts.entries),
            ),
        )
        internal_race_id = cursor.lastrowid
        if type(internal_race_id) is not int or internal_race_id <= 0:
            raise RepositoryDataIntegrityError("SQLite did not create internal JRA race ID")
        self._connection.execute(
            """INSERT INTO historical_input_external_races(
                    organization,source_system,external_race_id,internal_race_id
                ) VALUES(?,?,?,?)""",
            (_ORGANIZATION, _SOURCE_SYSTEM, facts.external_race_id, internal_race_id),
        )
        return internal_race_id

    def _validate_mapped_race(self, *, internal_race_id: int, facts: "_MaterializationFacts") -> None:
        self._require_legacy_columns("races", ("id", "race_date", "organization", "place", "race_no"))
        row = self._connection.execute(
            "SELECT id,race_date,organization,place,race_no FROM races WHERE id=?",
            (internal_race_id,),
        ).fetchone()
        date_value = facts.track_values["target_race_date"]
        if type(date_value) is not _date:
            raise RepositoryValidationError("target race date is invalid")
        expected = (internal_race_id, date_value.isoformat(), _ORGANIZATION, facts.track_values["place"], facts.race_number)
        if row is None or tuple(row) != expected:
            raise RepositoryDataIntegrityError("mapped internal race identity is invalid")

    def _resolve_or_create_entries(
        self, *, facts: "_MaterializationFacts", internal_race_id: int
    ) -> tuple[_SeedEntry, ...]:
        self._require_legacy_columns("horses", ("id", "race_id", "horse_no"))
        entries: list[_SeedEntry] = []
        for index, item in enumerate(facts.entries):
            row = self._connection.execute(
                """SELECT internal_race_id,race_entry_id FROM historical_input_external_entries
                   WHERE organization=? AND source_system=? AND external_race_id=? AND external_entry_id=?""",
                (_ORGANIZATION, _SOURCE_SYSTEM, facts.external_race_id, item.external_entry_id),
            ).fetchone()
            if row is None:
                collision = self._connection.execute(
                    "SELECT id FROM horses WHERE race_id=? AND horse_no=?",
                    (internal_race_id, item.horse_no),
                ).fetchall()
                if collision:
                    raise RepositoryDataIntegrityError("unproven legacy horse-number collision prevents JRA materialization")
                cursor = self._connection.execute(
                    "INSERT INTO horses(race_id,horse_no) VALUES(?,?)", (internal_race_id, item.horse_no)
                )
                internal_entry_id = cursor.lastrowid
                if type(internal_entry_id) is not int or internal_entry_id <= 0:
                    raise RepositoryDataIntegrityError("SQLite did not create internal JRA entry ID")
                self._connection.execute(
                    """INSERT INTO historical_input_external_entries(
                            organization,source_system,external_race_id,external_entry_id,internal_race_id,race_entry_id
                        ) VALUES(?,?,?,?,?,?)""",
                    (_ORGANIZATION, _SOURCE_SYSTEM, facts.external_race_id, item.external_entry_id, internal_race_id, internal_entry_id),
                )
            else:
                if type(row[0]) is not int or type(row[1]) is not int or row[0] != internal_race_id or row[1] <= 0:
                    raise RepositoryDataIntegrityError("stored JRA external entry mapping is invalid")
                internal_entry_id = row[1]
                self._require_entry_seed_proof(
                    external_race_id=facts.external_race_id,
                    external_entry_id=item.external_entry_id,
                    internal_race_id=internal_race_id,
                    internal_race_entry_id=internal_entry_id,
                )
                horse = self._connection.execute(
                    "SELECT id,race_id,horse_no FROM horses WHERE id=?", (internal_entry_id,)
                ).fetchone()
                if horse is None or tuple(horse) != (internal_entry_id, internal_race_id, item.horse_no):
                    raise RepositoryDataIntegrityError("mapped internal entry disagrees with JRA target identity")
            entries.append(
                _SeedEntry(
                    entry_order=index,
                    external_entry_id=item.external_entry_id,
                    external_horse_id=item.external_horse_id,
                    horse_no=item.horse_no,
                    internal_race_entry_id=internal_entry_id,
                )
            )
        return tuple(entries)

    def _require_race_seed_proof(self, *, external_race_id: str, internal_race_id: int) -> None:
        rows = self._connection.execute(
            """SELECT seed_id FROM jra_race_replay_seeds
               WHERE organization=? AND source_system=? AND external_race_id=? AND internal_race_id=?
               ORDER BY seed_id""",
            (_ORGANIZATION, _SOURCE_SYSTEM, external_race_id, internal_race_id),
        ).fetchall()
        if not rows:
            raise RepositoryDataIntegrityError("existing JRA race mapping lacks prior d0 seed proof")
        for (seed_id,) in rows:
            proof = self._load_seed_unvalidated(seed_id=seed_id)
            if proof.external_race_id != external_race_id or proof.internal_race_id != internal_race_id:
                raise RepositoryDataIntegrityError("prior JRA race seed proof is contradictory")

    def _require_entry_seed_proof(
        self,
        *,
        external_race_id: str,
        external_entry_id: str,
        internal_race_id: int,
        internal_race_entry_id: int,
    ) -> None:
        rows = self._connection.execute(
            """SELECT seed_id FROM jra_race_replay_seed_entries
               WHERE organization=? AND source_system=? AND external_race_id=? AND external_entry_id=?
                 AND internal_race_id=? AND internal_race_entry_id=? ORDER BY seed_id""",
            (
                _ORGANIZATION,
                _SOURCE_SYSTEM,
                external_race_id,
                external_entry_id,
                internal_race_id,
                internal_race_entry_id,
            ),
        ).fetchall()
        if not rows:
            raise RepositoryDataIntegrityError("existing JRA entry mapping lacks prior d0 seed proof")
        for (seed_id,) in rows:
            proof = self._load_seed_unvalidated(seed_id=seed_id)
            if not any(
                entry.external_entry_id == external_entry_id
                and entry.internal_race_entry_id == internal_race_entry_id
                for entry in proof.entries
            ):
                raise RepositoryDataIntegrityError("prior JRA entry seed proof is contradictory")

    def _find_existing_natural_identity(self, seed: _Seed) -> tuple[str, str] | None:
        return self._connection.execute(
            """SELECT seed_id,content_sha256 FROM jra_race_replay_seeds
               WHERE schema_version=? AND dataset_id=? AND external_race_id=?
                 AND target_race_selection_capture_id=? AND captured_at_utc=? AND information_cutoff_utc=?""",
            (
                seed.schema_version, seed.dataset_id, seed.external_race_id,
                seed.target_race_selection_capture_id, _datetime_text(seed.captured_at), _datetime_text(seed.information_cutoff),
            ),
        ).fetchone()

    def _insert_seed(self, seed: _Seed) -> None:
        self._connection.execute(
            """INSERT INTO jra_race_replay_seeds(
                seed_id,schema_version,content_sha256,dataset_id,organization,source_system,external_race_id,
                internal_race_id,target_race_selection_capture_id,target_race_card_capture_id,
                target_race_card_response_sha256,canonical_target_race_card_url,captured_at_utc,information_cutoff_utc
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                seed.seed_id, seed.schema_version, seed.content_sha256, seed.dataset_id, _ORGANIZATION, _SOURCE_SYSTEM,
                seed.external_race_id, seed.internal_race_id, seed.target_race_selection_capture_id,
                seed.target_race_card_capture_id, seed.target_race_card_response_sha256,
                seed.canonical_target_race_card_url, _datetime_text(seed.captured_at), _datetime_text(seed.information_cutoff),
            ),
        )
        self._connection.executemany(
            """INSERT INTO jra_race_replay_seed_entries(
                seed_id,organization,source_system,external_race_id,internal_race_id,entry_order,
                external_entry_id,external_horse_id,horse_no,internal_race_entry_id
            ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            tuple(
                (
                    seed.seed_id, _ORGANIZATION, _SOURCE_SYSTEM, seed.external_race_id, seed.internal_race_id,
                    entry.entry_order, entry.external_entry_id, entry.external_horse_id, entry.horse_no,
                    entry.internal_race_entry_id,
                )
                for entry in seed.entries
            ),
        )

    def _load_seed_unvalidated(self, *, seed_id: str) -> _Seed:
        header = self._connection.execute(
            """SELECT seed_id,schema_version,content_sha256,dataset_id,organization,source_system,external_race_id,
                      internal_race_id,target_race_selection_capture_id,target_race_card_capture_id,
                      target_race_card_response_sha256,canonical_target_race_card_url,captured_at_utc,information_cutoff_utc
               FROM jra_race_replay_seeds WHERE seed_id=?""",
            (seed_id,),
        ).fetchone()
        if header is None:
            raise RepositoryDataIntegrityError("selected JRA replay seed disappeared")
        if header[4:6] != (_ORGANIZATION, _SOURCE_SYSTEM):
            raise RepositoryDataIntegrityError("stored JRA replay seed source identity is invalid")
        entries = self._connection.execute(
            """SELECT organization,source_system,external_race_id,internal_race_id,
                      entry_order,external_entry_id,external_horse_id,horse_no,internal_race_entry_id
               FROM jra_race_replay_seed_entries WHERE seed_id=? ORDER BY entry_order""",
            (seed_id,),
        ).fetchall()
        if not entries:
            raise RepositoryDataIntegrityError("stored JRA replay seed has no entries")
        expected_child_identity = (_ORGANIZATION, _SOURCE_SYSTEM, header[6], header[7])
        if any(tuple(row[:4]) != expected_child_identity for row in entries):
            raise RepositoryDataIntegrityError("stored JRA replay seed child identity is invalid")
        seed_entries = tuple(_SeedEntry(*row[4:]) for row in entries)
        seed = _build_seed(
            dataset_id=header[3], external_race_id=header[6], internal_race_id=header[7],
            target_race_selection_capture_id=header[8], target_race_card_capture_id=header[9],
            target_race_card_response_sha256=header[10], canonical_target_race_card_url=header[11],
            captured_at=_parse_datetime_text(header[12]), information_cutoff=_parse_datetime_text(header[13]),
            entries=seed_entries,
        )
        if header[0] != seed.seed_id or header[1] != seed.schema_version or header[2] != seed.content_sha256:
            raise RepositoryDataIntegrityError("stored JRA replay seed digest or identity is invalid")
        self._validate_loaded_relations(seed)
        return seed

    def _validate_loaded_relations(self, seed: _Seed) -> None:
        source = self._connection.execute(
            "SELECT organization,source_system FROM historical_input_source_identities WHERE organization=? AND source_system=?",
            (_ORGANIZATION, _SOURCE_SYSTEM),
        ).fetchone()
        if source != (_ORGANIZATION, _SOURCE_SYSTEM):
            raise RepositoryDataIntegrityError("stored JRA replay seed source identity is missing")
        race = self._connection.execute(
            """SELECT r.id FROM historical_input_external_races e JOIN races r ON r.id=e.internal_race_id
               WHERE e.organization=? AND e.source_system=? AND e.external_race_id=? AND e.internal_race_id=?""",
            (_ORGANIZATION, _SOURCE_SYSTEM, seed.external_race_id, seed.internal_race_id),
        ).fetchone()
        if race != (seed.internal_race_id,):
            raise RepositoryDataIntegrityError("stored JRA replay seed race mapping is invalid")
        for entry in seed.entries:
            row = self._connection.execute(
                """SELECT e.race_entry_id,h.race_id,h.horse_no FROM historical_input_external_entries e
                   JOIN horses h ON h.id=e.race_entry_id
                   WHERE e.organization=? AND e.source_system=? AND e.external_race_id=?
                     AND e.external_entry_id=? AND e.internal_race_id=?""",
                (_ORGANIZATION, _SOURCE_SYSTEM, seed.external_race_id, entry.external_entry_id, seed.internal_race_id),
            ).fetchone()
            if row != (entry.internal_race_entry_id, seed.internal_race_id, entry.horse_no):
                raise RepositoryDataIntegrityError("stored JRA replay seed entry mapping is invalid")

    def _ensure_foreign_keys(self) -> None:
        try:
            self._connection.execute("PRAGMA foreign_keys=ON")
            enabled = self._connection.execute("PRAGMA foreign_keys").fetchone()
        except sqlite3.Error as error:
            raise RepositoryValidationError("connection is not usable") from error
        if enabled is None or enabled[0] != 1:
            raise RepositoryValidationError("foreign_keys could not be enabled")

    def _require_legacy_columns(self, table: str, expected: tuple[str, ...]) -> None:
        columns = tuple(row[1] for row in self._connection.execute(f"PRAGMA table_info({table})"))
        if not set(expected) <= set(columns):
            raise RepositoryDataIntegrityError(f"{table} lacks required JRA materialization columns")


class _TargetEntryFacts:
    __slots__ = ("external_entry_id", "external_horse_id", "horse_no")

    def __init__(self, external_entry_id: str, external_horse_id: str, horse_no: int) -> None:
        self.external_entry_id = external_entry_id
        self.external_horse_id = external_horse_id
        self.horse_no = horse_no


class _MaterializationFacts:
    __slots__ = (
        "dataset_id", "external_race_id", "race_number", "v4_capture_id", "v3_capture_id",
        "v3_response_sha256", "card_url", "captured_at", "information_cutoff", "track_values", "entries",
    )

    def __init__(
        self, *, dataset_id: str, external_race_id: str, race_number: int, v4_capture_id: str,
        v3_capture_id: str, v3_response_sha256: str, card_url: str, captured_at: _datetime,
        information_cutoff: _datetime, track_values: object, entries: tuple[_TargetEntryFacts, ...],
    ) -> None:
        self.dataset_id = dataset_id
        self.external_race_id = external_race_id
        self.race_number = race_number
        self.v4_capture_id = v4_capture_id
        self.v3_capture_id = v3_capture_id
        self.v3_response_sha256 = v3_response_sha256
        self.card_url = card_url
        self.captured_at = captured_at
        self.information_cutoff = information_cutoff
        self.track_values = track_values
        self.entries = entries


def _normalize_utc(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise RepositoryValidationError(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError
        return value.astimezone(_timezone.utc)
    except (TypeError, ValueError, OverflowError) as error:
        raise RepositoryValidationError(f"{name} must be timezone-aware") from error


def _parse_datetime_text(value: object) -> _datetime:
    if type(value) is not str:
        raise RepositoryDataIntegrityError("stored JRA replay seed timestamp is invalid")
    try:
        parsed = _datetime.fromisoformat(value)
    except ValueError as error:
        raise RepositoryDataIntegrityError("stored JRA replay seed timestamp is invalid") from error
    try:
        return _normalize_utc(parsed, "stored timestamp")
    except RepositoryValidationError as error:
        raise RepositoryDataIntegrityError("stored JRA replay seed timestamp is invalid") from error


__all__ = ("SQLiteJRARaceReplaySeedRepository",)
