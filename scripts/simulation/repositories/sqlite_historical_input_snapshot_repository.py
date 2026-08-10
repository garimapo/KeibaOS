"""Atomic SQLite persistence for immutable historical input snapshots."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import sqlite3
from unicodedata import normalize

from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalEntryIdentity,
    HistoricalExternalRaceIdentity,
    HistoricalInputProvenance,
    HistoricalInputSnapshot,
    HistoricalInputSnapshotIdentity,
    HistoricalPastRaceSnapshot,
    HistoricalRaceEntrySnapshot,
    HistoricalRaceSnapshot,
    HistoricalSourceIdentity,
)
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference

from .errors import RepositoryConflictError, RepositoryDataIntegrityError, RepositoryValidationError


class SQLiteHistoricalInputSnapshotRepository:
    """Persist one complete V3a snapshot through the committed v010 schema."""

    __slots__ = ("_connection",)

    def __init__(self, *, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise RepositoryValidationError("connection must be sqlite3.Connection")
        self._connection = connection
        self._ensure_foreign_keys()

    def load_latest_snapshot(
        self,
        *,
        dataset_id: str,
        race_id: int,
        information_cutoff: datetime,
        source_identity: HistoricalExternalRaceIdentity,
    ) -> HistoricalInputSnapshot | None:
        dataset = self._validate_dataset_id(dataset_id)
        requested_race_id = self._validate_race_id(race_id)
        cutoff = self._validate_information_cutoff(information_cutoff)
        source = self._validate_source_identity(source_identity)
        cutoff_text = self._datetime_text(cutoff)

        try:
            row = self._connection.execute(
                """SELECT snapshot_id,dataset_id,organization,source_system,external_race_id,internal_race_id,
                          source_url,captured_at_utc,information_cutoff_utc,content_sha256
                   FROM historical_input_snapshots
                   WHERE dataset_id=? AND internal_race_id=? AND organization=? AND source_system=?
                     AND external_race_id=? AND captured_at_utc<=? AND information_cutoff_utc<=?
                   ORDER BY captured_at_utc DESC
                   LIMIT 1""",
                (
                    dataset,
                    requested_race_id,
                    source.organization,
                    source.source_system,
                    source.external_race_id,
                    cutoff_text,
                    cutoff_text,
                ),
            ).fetchone()
        except sqlite3.Error as exc:
            raise RepositoryDataIntegrityError("could not read historical snapshot header") from exc
        if row is None:
            return None

        try:
            return self._reconstruct_selected_snapshot(
                row=row,
                dataset_id=dataset,
                race_id=requested_race_id,
                information_cutoff=cutoff,
                source_identity=source,
            )
        except RepositoryDataIntegrityError:
            raise
        except (AttributeError, KeyError, TypeError, ValueError, InvalidOperation, sqlite3.Error) as exc:
            raise RepositoryDataIntegrityError("stored historical snapshot violates repository invariants") from exc

    def save_snapshot(self, *, snapshot: HistoricalInputSnapshot) -> None:
        if type(snapshot) is not HistoricalInputSnapshot:
            raise RepositoryValidationError("snapshot must be HistoricalInputSnapshot")
        if self._connection.in_transaction:
            raise RepositoryValidationError("repository writes require no active transaction")

        self._ensure_foreign_keys()
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            existing = self._find_existing_header(snapshot)
            if existing is not None:
                _snapshot_id, content_sha256 = existing
                if content_sha256 == snapshot.content_sha256:
                    self._connection.commit()
                    return
                raise RepositoryConflictError("historical input snapshot differs from existing snapshot")

            self._ensure_mappings(snapshot)
            snapshot_id = self._insert_header(snapshot)
            self._insert_race(snapshot_id, snapshot)
            self._insert_entries(snapshot_id, snapshot)
            self._insert_past_races(snapshot_id, snapshot)
            self._insert_provenance(snapshot_id, snapshot)
            self._connection.commit()
        except RepositoryConflictError:
            self._connection.rollback()
            raise
        except RepositoryDataIntegrityError:
            self._connection.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            self._connection.rollback()
            raise RepositoryDataIntegrityError("SQLite integrity constraint failed") from exc
        except Exception:
            self._connection.rollback()
            raise

    def _ensure_foreign_keys(self) -> None:
        try:
            self._connection.execute("PRAGMA foreign_keys=ON")
            enabled = self._connection.execute("PRAGMA foreign_keys").fetchone()
        except sqlite3.Error as exc:
            raise RepositoryValidationError("connection is not usable") from exc
        if enabled is None or enabled[0] != 1:
            raise RepositoryValidationError("foreign_keys could not be enabled")

    @staticmethod
    def _validate_dataset_id(value: object) -> str:
        if type(value) is not str or not value or normalize("NFC", value) != value:
            raise RepositoryValidationError("dataset_id must be a non-empty NFC str")
        return value

    @staticmethod
    def _validate_race_id(value: object) -> int:
        if type(value) is not int or value <= 0:
            raise RepositoryValidationError("race_id must be a positive int")
        return value

    @staticmethod
    def _validate_information_cutoff(value: object) -> datetime:
        if type(value) is not datetime or value.tzinfo is None:
            raise RepositoryValidationError("information_cutoff must be a timezone-aware datetime")
        try:
            if value.utcoffset() is None:
                raise RepositoryValidationError("information_cutoff must be a timezone-aware datetime")
            return value.astimezone(timezone.utc)
        except (OverflowError, TypeError, ValueError) as exc:
            raise RepositoryValidationError("information_cutoff cannot be converted to UTC") from exc

    @staticmethod
    def _validate_source_identity(value: object) -> HistoricalExternalRaceIdentity:
        if type(value) is not HistoricalExternalRaceIdentity:
            raise RepositoryValidationError("source_identity must be HistoricalExternalRaceIdentity")
        return value

    @staticmethod
    def _stored_required_text(value: object, name: str, *, allow_empty: bool = False) -> str:
        if type(value) is not str or (not allow_empty and not value) or normalize("NFC", value) != value:
            raise RepositoryDataIntegrityError(f"stored {name} is not canonical text")
        return value

    @classmethod
    def _stored_optional_text(cls, value: object, name: str) -> str | None:
        if value is None:
            return None
        return cls._stored_required_text(value, name)

    @staticmethod
    def _stored_positive_int(value: object, name: str) -> int:
        if type(value) is not int or value <= 0:
            raise RepositoryDataIntegrityError(f"stored {name} must be a positive int")
        return value

    @staticmethod
    def _stored_non_negative_int(value: object, name: str) -> int:
        if type(value) is not int or value < 0:
            raise RepositoryDataIntegrityError(f"stored {name} must be a non-negative int")
        return value

    @classmethod
    def _stored_optional_non_negative_int(cls, value: object, name: str) -> int | None:
        if value is None:
            return None
        return cls._stored_non_negative_int(value, name)

    @staticmethod
    def _stored_datetime(value: object, name: str) -> datetime:
        if type(value) is not str:
            raise RepositoryDataIntegrityError(f"stored {name} must be text")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise RepositoryDataIntegrityError(f"stored {name} is not a datetime") from exc
        if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
            raise RepositoryDataIntegrityError(f"stored {name} must be UTC")
        canonical = parsed.astimezone(timezone.utc).isoformat(timespec="microseconds")
        if value != canonical:
            raise RepositoryDataIntegrityError(f"stored {name} is not canonical UTC text")
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _stored_optional_datetime(value: object, name: str) -> datetime | None:
        if value is None:
            return None
        return SQLiteHistoricalInputSnapshotRepository._stored_datetime(value, name)

    @staticmethod
    def _stored_date(value: object, name: str) -> date:
        if type(value) is not str:
            raise RepositoryDataIntegrityError(f"stored {name} must be text")
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise RepositoryDataIntegrityError(f"stored {name} is not a date") from exc
        if value != parsed.isoformat():
            raise RepositoryDataIntegrityError(f"stored {name} is not canonical date text")
        return parsed

    @staticmethod
    def _stored_decimal(value: object, name: str) -> Decimal:
        if type(value) is not str:
            raise RepositoryDataIntegrityError(f"stored {name} must be text")
        try:
            parsed = Decimal(value)
        except (InvalidOperation, ValueError) as exc:
            raise RepositoryDataIntegrityError(f"stored {name} is not a Decimal") from exc
        if not parsed.is_finite():
            raise RepositoryDataIntegrityError(f"stored {name} must be finite")
        normalized = Decimal("0") if parsed == 0 else parsed.normalize()
        if value != format(normalized, "f"):
            raise RepositoryDataIntegrityError(f"stored {name} is not canonical Decimal text")
        return normalized

    @staticmethod
    def _stored_sha256(value: object) -> str:
        if type(value) is not str or len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise RepositoryDataIntegrityError("stored content_sha256 is malformed")
        return value

    def _reconstruct_selected_snapshot(
        self,
        *,
        row: object,
        dataset_id: str,
        race_id: int,
        information_cutoff: datetime,
        source_identity: HistoricalExternalRaceIdentity,
    ) -> HistoricalInputSnapshot:
        try:
            (
                snapshot_id,
                stored_dataset_id,
                organization,
                source_system,
                external_race_id,
                internal_race_id,
                source_url,
                captured_at,
                stored_cutoff,
                stored_digest,
            ) = tuple(row)
        except (TypeError, ValueError) as exc:
            raise RepositoryDataIntegrityError("stored historical snapshot header is malformed") from exc

        identifier = self._stored_positive_int(snapshot_id, "snapshot_id")
        stored_dataset = self._stored_required_text(stored_dataset_id, "dataset_id")
        stored_organization = self._stored_required_text(organization, "organization")
        stored_system = self._stored_required_text(source_system, "source_system")
        stored_external_race_id = self._stored_required_text(external_race_id, "external_race_id")
        stored_race_id = self._stored_positive_int(internal_race_id, "internal_race_id")
        stored_source_url = self._stored_optional_text(source_url, "source_url")
        stored_captured_at = self._stored_datetime(captured_at, "captured_at_utc")
        stored_information_cutoff = self._stored_datetime(stored_cutoff, "information_cutoff_utc")
        digest = self._stored_sha256(stored_digest)

        if (
            stored_dataset != dataset_id
            or stored_race_id != race_id
            or stored_organization != source_identity.organization
            or stored_system != source_identity.source_system
            or stored_external_race_id != source_identity.external_race_id
            or stored_captured_at > information_cutoff
            or stored_information_cutoff > information_cutoff
        ):
            raise RepositoryDataIntegrityError("selected historical snapshot header does not match lookup")

        self._validate_external_race_mapping(
            organization=stored_organization,
            source_system=stored_system,
            external_race_id=stored_external_race_id,
            internal_race_id=stored_race_id,
        )
        source = HistoricalSourceIdentity(
            stored_organization,
            stored_system,
            stored_external_race_id,
            stored_source_url,
        )
        external_race = HistoricalExternalRaceIdentity(
            stored_organization,
            stored_system,
            stored_external_race_id,
        )
        identity = HistoricalInputSnapshotIdentity(stored_dataset, source, stored_captured_at)
        race = self._load_race(identifier)
        entries = self._load_entries(
            snapshot_id=identifier,
            external_race_identity=external_race,
            organization=stored_organization,
            source_system=stored_system,
            external_race_id=stored_external_race_id,
            internal_race_id=stored_race_id,
        )
        past_races = self._load_past_races(identifier)
        provenance = self._load_provenance(identifier)
        snapshot = HistoricalInputSnapshot(
            identity,
            stored_race_id,
            stored_information_cutoff,
            race,
            tuple(entries),
            tuple(past_races),
            tuple(provenance),
        )
        if snapshot.content_sha256 != digest:
            raise RepositoryDataIntegrityError("stored historical snapshot digest does not match content")
        return snapshot

    def _validate_external_race_mapping(
        self,
        *,
        organization: str,
        source_system: str,
        external_race_id: str,
        internal_race_id: int,
    ) -> None:
        rows = self._connection.execute(
            """SELECT internal_race_id FROM historical_input_external_races
               WHERE organization=? AND source_system=? AND external_race_id=?""",
            (organization, source_system, external_race_id),
        ).fetchall()
        if len(rows) != 1 or tuple(rows[0]) != (internal_race_id,):
            raise RepositoryDataIntegrityError("historical external-race mapping is malformed")

    def _load_race(self, snapshot_id: int) -> HistoricalRaceSnapshot:
        rows = self._connection.execute(
            """SELECT target_race_date,scheduled_start_at_utc,place,distance_m,track,track_condition,
                      race_name,race_class,weather
               FROM historical_input_snapshot_races WHERE snapshot_id=?""",
            (snapshot_id,),
        ).fetchall()
        if len(rows) != 1:
            raise RepositoryDataIntegrityError("historical snapshot must have exactly one race child")
        try:
            target_date, scheduled_start, place, distance_m, track, condition, name, race_class, weather = tuple(rows[0])
        except (TypeError, ValueError) as exc:
            raise RepositoryDataIntegrityError("stored historical race child is malformed") from exc
        return HistoricalRaceSnapshot(
            self._stored_date(target_date, "target_race_date"),
            self._stored_datetime(scheduled_start, "scheduled_start_at_utc"),
            self._stored_required_text(place, "place"),
            self._stored_positive_int(distance_m, "distance_m"),
            self._stored_required_text(track, "track"),
            self._stored_required_text(condition, "track_condition"),
            self._stored_optional_text(name, "race_name"),
            self._stored_optional_text(race_class, "race_class"),
            self._stored_optional_text(weather, "weather"),
        )

    def _load_entries(
        self,
        *,
        snapshot_id: int,
        external_race_identity: HistoricalExternalRaceIdentity,
        organization: str,
        source_system: str,
        external_race_id: str,
        internal_race_id: int,
    ) -> list[HistoricalRaceEntrySnapshot]:
        rows = self._connection.execute(
            """SELECT race_entry_id,external_entry_id,external_horse_id,horse_no,jockey,win_odds_text,entry_order
               FROM historical_input_snapshot_entries WHERE snapshot_id=? ORDER BY entry_order ASC""",
            (snapshot_id,),
        ).fetchall()
        entries: list[HistoricalRaceEntrySnapshot] = []
        for row in rows:
            try:
                race_entry_id, external_entry_id, external_horse_id, horse_no, jockey, win_odds, entry_order = tuple(row)
            except (TypeError, ValueError) as exc:
                raise RepositoryDataIntegrityError("stored historical entry is malformed") from exc
            entry_id = self._stored_positive_int(race_entry_id, "race_entry_id")
            external_id = self._stored_required_text(external_entry_id, "external_entry_id")
            self._validate_external_entry_mapping(
                organization=organization,
                source_system=source_system,
                external_race_id=external_race_id,
                external_entry_id=external_id,
                internal_race_id=internal_race_id,
                race_entry_id=entry_id,
            )
            external = HistoricalExternalEntryIdentity(
                external_race_identity,
                external_id,
                self._stored_optional_text(external_horse_id, "external_horse_id"),
            )
            entries.append(
                HistoricalRaceEntrySnapshot(
                    entry_id,
                    external,
                    self._stored_positive_int(horse_no, "horse_no"),
                    self._stored_required_text(jockey, "jockey"),
                    self._stored_decimal(win_odds, "win_odds_text"),
                    self._stored_non_negative_int(entry_order, "entry_order"),
                )
            )
        return entries

    def _validate_external_entry_mapping(
        self,
        *,
        organization: str,
        source_system: str,
        external_race_id: str,
        external_entry_id: str,
        internal_race_id: int,
        race_entry_id: int,
    ) -> None:
        rows = self._connection.execute(
            """SELECT internal_race_id,race_entry_id FROM historical_input_external_entries
               WHERE organization=? AND source_system=? AND external_race_id=? AND external_entry_id=?""",
            (organization, source_system, external_race_id, external_entry_id),
        ).fetchall()
        if len(rows) != 1 or tuple(rows[0]) != (internal_race_id, race_entry_id):
            raise RepositoryDataIntegrityError("historical external-entry mapping is malformed")

    def _load_past_races(self, snapshot_id: int) -> list[HistoricalPastRaceSnapshot]:
        rows = self._connection.execute(
            """SELECT race_entry_id,past_race_index,race_date,place,race_name,race_class,distance_m,track,
                      weather,track_condition,finish,reference_time_difference_seconds_text,race_time,weight_text,weight_diff_text,jockey,
                      popularity,odds_text,passing_order,fourth_corner_position
               FROM historical_input_snapshot_past_races
               WHERE snapshot_id=? ORDER BY race_entry_id ASC,past_race_index ASC""",
            (snapshot_id,),
        ).fetchall()
        values: list[HistoricalPastRaceSnapshot] = []
        for row in rows:
            try:
                (
                    race_entry_id,
                    index,
                    race_date,
                    place,
                    race_name,
                    race_class,
                    distance_m,
                    track,
                    weather,
                    condition,
                    finish,
                    reference_time_difference_seconds,
                    race_time,
                    weight,
                    weight_diff,
                    jockey,
                    popularity,
                    odds,
                    passing_order,
                    corner,
                ) = tuple(row)
            except (TypeError, ValueError) as exc:
                raise RepositoryDataIntegrityError("stored historical past race is malformed") from exc
            values.append(
                HistoricalPastRaceSnapshot(
                    self._stored_positive_int(race_entry_id, "past_race.race_entry_id"),
                    self._stored_non_negative_int(index, "past_race_index"),
                    self._stored_date(race_date, "past_race.race_date"),
                    self._stored_required_text(place, "past_race.place"),
                    self._stored_required_text(race_name, "past_race.race_name"),
                    self._stored_required_text(race_class, "past_race.race_class"),
                    self._stored_positive_int(distance_m, "past_race.distance_m"),
                    self._stored_required_text(track, "past_race.track"),
                    self._stored_required_text(weather, "past_race.weather"),
                    self._stored_required_text(condition, "past_race.track_condition"),
                    self._stored_positive_int(finish, "past_race.finish"),
                    self._stored_decimal(
                        reference_time_difference_seconds,
                        "reference_time_difference_seconds_text",
                    ),
                    self._stored_required_text(race_time, "past_race.race_time"),
                    self._stored_decimal(weight, "weight_text"),
                    self._stored_decimal(weight_diff, "weight_diff_text"),
                    self._stored_required_text(jockey, "past_race.jockey"),
                    self._stored_non_negative_int(popularity, "past_race.popularity"),
                    self._stored_decimal(odds, "odds_text"),
                    self._stored_required_text(passing_order, "passing_order", allow_empty=True),
                    self._stored_non_negative_int(corner, "past_race.fourth_corner_position"),
                )
            )
        return values

    def _load_provenance(self, snapshot_id: int) -> list[HistoricalInputProvenance]:
        rows = self._connection.execute(
            """SELECT input_type,audit_key,source,source_id,race_entry_id,past_race_index
               FROM historical_input_snapshot_provenance WHERE snapshot_id=? ORDER BY audit_key ASC""",
            (snapshot_id,),
        ).fetchall()
        values: list[HistoricalInputProvenance] = []
        for row in rows:
            try:
                input_type, audit_key, source, source_id, race_entry_id, index = tuple(row)
            except (TypeError, ValueError) as exc:
                raise RepositoryDataIntegrityError("stored historical provenance is malformed") from exc
            audit = self._stored_required_text(audit_key, "provenance.audit_key")
            evidence_rows = self._connection.execute(
                """SELECT evidence_order,evidence_role,canonical_source_url,response_sha256,available_at_utc,observed_at_utc
                   FROM historical_input_snapshot_provenance_evidence
                   WHERE snapshot_id=? AND audit_key=? ORDER BY evidence_order ASC""",
                (snapshot_id, audit),
            ).fetchall()
            evidence = []
            for order, role, url, digest, available, observed in evidence_rows:
                if self._stored_non_negative_int(order, "evidence_order") != len(evidence):
                    raise RepositoryDataIntegrityError("stored provenance evidence order is invalid")
                evidence.append(
                    HistoricalInputEvidenceReference(
                        self._stored_required_text(role, "evidence_role"),
                        self._stored_optional_text(url, "canonical_source_url"),
                        self._stored_sha256(digest),
                        self._stored_optional_datetime(available, "available_at_utc"),
                        self._stored_datetime(observed, "observed_at_utc"),
                    )
                )
            values.append(
                HistoricalInputProvenance(
                    self._stored_required_text(input_type, "provenance.input_type"),
                    audit,
                    self._stored_required_text(source, "provenance.source"),
                    self._stored_required_text(source_id, "provenance.source_id"),
                    None if race_entry_id is None else self._stored_positive_int(race_entry_id, "provenance.race_entry_id"),
                    tuple(evidence),
                    self._stored_optional_non_negative_int(index, "provenance.past_race_index"),
                )
            )
        return values

    def _find_existing_header(self, snapshot: HistoricalInputSnapshot) -> tuple[int, str] | None:
        source = snapshot.identity.source_identity
        rows = self._connection.execute(
            """SELECT snapshot_id, content_sha256
               FROM historical_input_snapshots
               WHERE dataset_id=? AND organization=? AND source_system=?
                 AND external_race_id=? AND captured_at_utc=?""",
            (
                snapshot.identity.dataset_id,
                source.organization,
                source.source_system,
                source.external_race_id,
                self._datetime_text(snapshot.identity.captured_at),
            ),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise RepositoryDataIntegrityError("multiple historical snapshot headers match one identity")
        snapshot_id, content_sha256 = rows[0]
        if type(snapshot_id) is not int or type(content_sha256) is not str:
            raise RepositoryDataIntegrityError("historical snapshot header is malformed")
        return snapshot_id, content_sha256

    def _ensure_mappings(self, snapshot: HistoricalInputSnapshot) -> None:
        source = snapshot.identity.source_identity
        self._ensure_source_identity(source.organization, source.source_system)
        self._ensure_external_race(
            organization=source.organization,
            source_system=source.source_system,
            external_race_id=source.external_race_id,
            internal_race_id=snapshot.internal_race_id,
        )
        for entry in snapshot.entries:
            external = entry.external_entry_identity
            race_identity = external.external_race_identity
            self._ensure_external_entry(
                organization=race_identity.organization,
                source_system=race_identity.source_system,
                external_race_id=race_identity.external_race_id,
                external_entry_id=external.external_entry_id,
                internal_race_id=snapshot.internal_race_id,
                race_entry_id=entry.race_entry_id,
            )

    def _ensure_source_identity(self, organization: str, source_system: str) -> None:
        row = self._connection.execute(
            """SELECT 1 FROM historical_input_source_identities
               WHERE organization=? AND source_system=?""",
            (organization, source_system),
        ).fetchone()
        if row is None:
            self._connection.execute(
                "INSERT INTO historical_input_source_identities(organization,source_system) VALUES(?,?)",
                (organization, source_system),
            )

    def _ensure_external_race(
        self,
        *,
        organization: str,
        source_system: str,
        external_race_id: str,
        internal_race_id: int,
    ) -> None:
        forward = self._connection.execute(
            """SELECT internal_race_id FROM historical_input_external_races
               WHERE organization=? AND source_system=? AND external_race_id=?""",
            (organization, source_system, external_race_id),
        ).fetchall()
        if len(forward) > 1:
            raise RepositoryDataIntegrityError("multiple external-race mappings match one identity")
        if forward:
            if forward[0][0] != internal_race_id:
                raise RepositoryConflictError("external race maps to a different internal race")
            return

        reverse = self._connection.execute(
            """SELECT external_race_id FROM historical_input_external_races
               WHERE organization=? AND source_system=? AND internal_race_id=?""",
            (organization, source_system, internal_race_id),
        ).fetchall()
        if len(reverse) > 1:
            raise RepositoryDataIntegrityError("multiple external-race mappings match one internal race")
        if reverse:
            raise RepositoryConflictError("internal race maps to a different external race")
        self._connection.execute(
            """INSERT INTO historical_input_external_races
               (organization,source_system,external_race_id,internal_race_id) VALUES(?,?,?,?)""",
            (organization, source_system, external_race_id, internal_race_id),
        )

    def _ensure_external_entry(
        self,
        *,
        organization: str,
        source_system: str,
        external_race_id: str,
        external_entry_id: str,
        internal_race_id: int,
        race_entry_id: int,
    ) -> None:
        forward = self._connection.execute(
            """SELECT internal_race_id,race_entry_id FROM historical_input_external_entries
               WHERE organization=? AND source_system=? AND external_race_id=? AND external_entry_id=?""",
            (organization, source_system, external_race_id, external_entry_id),
        ).fetchall()
        if len(forward) > 1:
            raise RepositoryDataIntegrityError("multiple external-entry mappings match one identity")
        if forward:
            if tuple(forward[0]) != (internal_race_id, race_entry_id):
                raise RepositoryConflictError("external entry maps to a different internal entry")
            return

        reverse = self._connection.execute(
            """SELECT external_entry_id FROM historical_input_external_entries
               WHERE organization=? AND source_system=? AND internal_race_id=? AND race_entry_id=?""",
            (organization, source_system, internal_race_id, race_entry_id),
        ).fetchall()
        if len(reverse) > 1:
            raise RepositoryDataIntegrityError("multiple external-entry mappings match one internal entry")
        if reverse:
            raise RepositoryConflictError("internal entry maps to a different external entry")
        self._connection.execute(
            """INSERT INTO historical_input_external_entries
               (organization,source_system,external_race_id,external_entry_id,internal_race_id,race_entry_id)
               VALUES(?,?,?,?,?,?)""",
            (organization, source_system, external_race_id, external_entry_id, internal_race_id, race_entry_id),
        )

    def _insert_header(self, snapshot: HistoricalInputSnapshot) -> int:
        source = snapshot.identity.source_identity
        cursor = self._connection.execute(
            """INSERT INTO historical_input_snapshots(
                   dataset_id,organization,source_system,external_race_id,internal_race_id,source_url,
                   captured_at_utc,information_cutoff_utc,content_sha256
               ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                snapshot.identity.dataset_id,
                source.organization,
                source.source_system,
                source.external_race_id,
                snapshot.internal_race_id,
                source.source_url,
                self._datetime_text(snapshot.identity.captured_at),
                self._datetime_text(snapshot.information_cutoff),
                snapshot.content_sha256,
            ),
        )
        return int(cursor.lastrowid)

    def _insert_race(self, snapshot_id: int, snapshot: HistoricalInputSnapshot) -> None:
        race = snapshot.race
        self._connection.execute(
            """INSERT INTO historical_input_snapshot_races(
                   snapshot_id,target_race_date,scheduled_start_at_utc,place,distance_m,track,track_condition,
                   race_name,race_class,weather
               ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                snapshot_id,
                self._date_text(race.target_race_date),
                self._datetime_text(race.scheduled_start_at),
                race.place,
                race.distance_m,
                race.track,
                race.track_condition,
                race.race_name,
                race.race_class,
                race.weather,
            ),
        )

    def _insert_entries(self, snapshot_id: int, snapshot: HistoricalInputSnapshot) -> None:
        self._connection.executemany(
            """INSERT INTO historical_input_snapshot_entries(
                   snapshot_id,race_entry_id,external_entry_id,external_horse_id,horse_no,jockey,
                   win_odds_text,entry_order
               ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                (
                    snapshot_id,
                    entry.race_entry_id,
                    entry.external_entry_identity.external_entry_id,
                    entry.external_entry_identity.external_horse_id,
                    entry.horse_no,
                    entry.jockey,
                    self._decimal_text(entry.win_odds),
                    entry.entry_order,
                )
                for entry in snapshot.entries
            ),
        )

    def _insert_past_races(self, snapshot_id: int, snapshot: HistoricalInputSnapshot) -> None:
        self._connection.executemany(
            """INSERT INTO historical_input_snapshot_past_races(
                   snapshot_id,race_entry_id,past_race_index,race_date,place,race_name,race_class,distance_m,
                   track,weather,track_condition,finish,reference_time_difference_seconds_text,race_time,weight_text,weight_diff_text,
                   jockey,popularity,odds_text,passing_order,fourth_corner_position
               ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                (
                    snapshot_id,
                    item.race_entry_id,
                    item.past_race_index,
                    self._date_text(item.race_date),
                    item.place,
                    item.race_name,
                    item.race_class,
                    item.distance_m,
                    item.track,
                    item.weather,
                    item.track_condition,
                    item.finish,
                    self._decimal_text(item.reference_time_difference_seconds),
                    item.race_time,
                    self._decimal_text(item.weight),
                    self._decimal_text(item.weight_diff),
                    item.jockey,
                    item.popularity,
                    self._decimal_text(item.odds),
                    item.passing_order,
                    item.fourth_corner_position,
                )
                for item in snapshot.past_races
            ),
        )

    def _insert_provenance(self, snapshot_id: int, snapshot: HistoricalInputSnapshot) -> None:
        self._connection.executemany(
            """INSERT INTO historical_input_snapshot_provenance(
                   snapshot_id,input_type,audit_key,source,source_id,race_entry_id,past_race_index
               ) VALUES(?,?,?,?,?,?,?)""",
            (
                (
                    snapshot_id,
                    item.input_type,
                    item.audit_key,
                    item.source,
                    item.source_id,
                    item.race_entry_id,
                    item.past_race_index,
                )
                for item in snapshot.provenance
            ),
        )
        self._connection.executemany(
            """INSERT INTO historical_input_snapshot_provenance_evidence(
                   snapshot_id,audit_key,evidence_order,evidence_role,canonical_source_url,response_sha256,
                   available_at_utc,observed_at_utc
               ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                (
                    snapshot_id,
                    item.audit_key,
                    order,
                    evidence.evidence_role,
                    evidence.canonical_source_url,
                    evidence.response_sha256,
                    None if evidence.available_at is None else self._datetime_text(evidence.available_at),
                    self._datetime_text(evidence.observed_at),
                )
                for item in snapshot.provenance
                for order, evidence in enumerate(item.evidence)
            ),
        )

    @staticmethod
    def _datetime_text(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds")

    @staticmethod
    def _date_text(value: date) -> str:
        return value.isoformat()

    @staticmethod
    def _decimal_text(value: Decimal) -> str:
        return format(value, "f")
