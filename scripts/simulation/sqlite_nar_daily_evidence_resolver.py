"""Read-only NAR metadata selection followed by existing exact repository loads."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import date as _date, datetime as _datetime, timezone as _timezone
import re as _re
import sqlite3 as _sqlite3
from unicodedata import normalize as _normalize
from urllib.parse import parse_qsl as _parse_qsl, urlsplit as _urlsplit

from scripts.simulation.historical_daily_targets import (
    DailyHistoricalReplayTarget as _Target, DailyHistoricalReplayTargetSet as _TargetSet,
    DailyTargetDiscoveryFailureCode as _DiscoveryCode, TargetDiscoveryIncompleteError as _DiscoveryError,
    HistoricalDailyProviderIdentity as _Provider,
)
from scripts.simulation.historical_daily_evidence_resolution import (
    DailyHistoricalReplayCaptureReference as _Reference,
    DailyHistoricalReplayEvidenceDisposition as _Disposition,
    DailyHistoricalReplayEvidenceResolution as _Resolution,
    DailyHistoricalReplayTargetOutcome as _Outcome,
)
from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalRaceIdentity as _External, HistoricalSourceIdentity as _Source,
    HistoricalInputSnapshotIdentity as _Identity, HistoricalInputSnapshot as _Snapshot,
)
from scripts.simulation.nar_official_response_capture import (
    canonicalize_nar_official_capture_url as _canonical_url,
    NAROfficialPageKind as _Kind, NAROfficialResponseCapture as _Capture,
    NAROfficialResponseCaptureError as _CaptureError,
)
from scripts.simulation.repositories.errors import (
    RepositoryDataIntegrityError as _Integrity, RepositoryValidationError as _Validation,
)
from scripts.simulation.repositories.sqlite_historical_input_snapshot_repository import (
    SQLiteHistoricalInputSnapshotRepository as _Snapshots,
)
from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import (
    SQLiteNAROfficialResponseCaptureRepository as _Captures,
)


_NAR = _Provider("NAR", "nar_official")
_NORMAL = "nar-race-list-target-row-v1"
_NON_RUN = "nar-race-list-whole-meeting-cancelled-no-substitute-v1"
_RACE_ID = _re.compile(r"nar:([0-9]{8}):([1-9][0-9]*):([1-9][0-9]*)\Z")
_SHA = _re.compile(r"[0-9a-f]{64}\Z")
_CAPTURE_ID = _re.compile(r"nar-capture-v1:[0-9a-f]{64}\Z")
_EXTERNAL_KEY = ("organization", "source_system", "external_race_id")
_SNAPSHOT_KEY = ("dataset_id", *_EXTERNAL_KEY, "captured_at_utc")
_ARCHIVE_KEY = ("canonical_source_url", "response_sha256", "observed_at_utc")

# Read contracts only: column types and primary keys consumed by the pinned loaders.
# No DDL or migration imports; unspecified columns retain their existing owner.
_MAIN = {
    "races": ("id:I", ("id",)),
    "horses": ("id:I race_id:I", ("id",)),
    "historical_input_source_identities": ("organization source_system", ("organization", "source_system")),
    "historical_input_external_races": (
        "organization source_system external_race_id internal_race_id:I", _EXTERNAL_KEY),
    "historical_input_external_entries": (
        "organization source_system external_race_id external_entry_id internal_race_id:I race_entry_id:I",
        (*_EXTERNAL_KEY, "external_entry_id")),
    "historical_input_snapshots": (
        "snapshot_id:I dataset_id organization source_system external_race_id internal_race_id:I source_url "
        "captured_at_utc information_cutoff_utc content_sha256", ("snapshot_id",)),
    "historical_input_snapshot_races": (
        "snapshot_id:I target_race_date scheduled_start_at_utc place distance_m:I track track_condition race_name race_class weather",
        ("snapshot_id",)),
    "historical_input_snapshot_entries": (
        "snapshot_id:I race_entry_id:I external_entry_id external_horse_id horse_no:I jockey win_odds_text entry_order:I",
        ("snapshot_id", "race_entry_id")),
    "historical_input_snapshot_past_races": (
        "snapshot_id:I race_entry_id:I past_race_index:I race_date place race_name race_class distance_m:I track weather "
        "track_condition finish:I race_time weight_text weight_diff_text jockey popularity:I odds_text passing_order fourth_corner_position:I",
        ("snapshot_id", "race_entry_id", "past_race_index")),
    "historical_input_snapshot_provenance": (
        "snapshot_id:I input_type audit_key source source_id race_entry_id:I past_race_index:I", ("snapshot_id", "audit_key")),
    "historical_input_snapshot_provenance_evidence": (
        "snapshot_id:I audit_key evidence_order:I evidence_role canonical_source_url response_sha256 available_at_utc "
        "observed_at_utc request_identity_sha256", ("snapshot_id", "audit_key", "evidence_order")),
}
_ARCHIVE = {
    "nar_official_response_bodies": ("response_sha256 response_body:B byte_length:I", ("response_sha256",)),
    "nar_official_response_captures": (
        "capture_id schema_version:I page_kind canonical_source_url response_sha256 charset requested_at_utc "
        "observed_at_utc stored_at_utc http_status:I content_type content_encoding http_date etag last_modified content_length:I",
        ("capture_id",)),
}
_MAIN_UNIQUE = {
    "horses": (("race_id", "id"),),
    "historical_input_external_races": (("organization", "source_system", "internal_race_id"), (*_EXTERNAL_KEY, "internal_race_id")),
    "historical_input_external_entries": (("organization", "source_system", "internal_race_id", "race_entry_id"),),
    "historical_input_snapshots": (_SNAPSHOT_KEY,),
}
_FK = {
    "historical_input_external_races": (
        (("internal_race_id",), "races", ("id",)),
        (("organization", "source_system"), "historical_input_source_identities", ("organization", "source_system"))),
    "historical_input_external_entries": (
        ((*_EXTERNAL_KEY, "internal_race_id"), "historical_input_external_races", (*_EXTERNAL_KEY, "internal_race_id")),
        (("internal_race_id", "race_entry_id"), "horses", ("race_id", "id"))),
    "historical_input_snapshots": (
        ((*_EXTERNAL_KEY, "internal_race_id"), "historical_input_external_races", (*_EXTERNAL_KEY, "internal_race_id")),
        (("internal_race_id",), "races", ("id",))),
    "historical_input_snapshot_races": ((("snapshot_id",), "historical_input_snapshots", ("snapshot_id",)),),
    "historical_input_snapshot_entries": ((("snapshot_id",), "historical_input_snapshots", ("snapshot_id",)),),
    "historical_input_snapshot_past_races": (
        (("snapshot_id", "race_entry_id"), "historical_input_snapshot_entries", ("snapshot_id", "race_entry_id")),),
    "historical_input_snapshot_provenance": (
        (("snapshot_id",), "historical_input_snapshots", ("snapshot_id",)),
        (("snapshot_id", "race_entry_id"), "historical_input_snapshot_entries", ("snapshot_id", "race_entry_id")),
        (("snapshot_id", "race_entry_id", "past_race_index"), "historical_input_snapshot_past_races", ("snapshot_id", "race_entry_id", "past_race_index"))),
    "historical_input_snapshot_provenance_evidence": (
        (("snapshot_id", "audit_key"), "historical_input_snapshot_provenance", ("snapshot_id", "audit_key")),),
    "nar_official_response_captures": ((("response_sha256",), "nar_official_response_bodies", ("response_sha256",)),),
}


def _text(value: object) -> str:
    if type(value) is not str or not value or value != _normalize("NFC", value) or value != value.strip():
        raise ValueError("nonempty canonical text required")
    return value


def _utc(value: object) -> _datetime:
    if type(value) is not _datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("aware datetime required")
    return value.astimezone(_timezone.utc)


def _time_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _stored_time(value: object) -> _datetime:
    try:
        if type(value) is not str:
            raise ValueError("not text")
        parsed = _datetime.fromisoformat(value)
        if _time_text(_utc(parsed)) != value:
            raise ValueError("not canonical UTC")
        return parsed
    except (TypeError, ValueError, OverflowError) as error:
        raise _Integrity("stored selection timestamp is invalid") from error


def _positive(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise _Integrity("stored linkage is not a positive integer")
    return value


def _schema(connection: _sqlite3.Connection, tables: dict, unique: dict) -> None:
    for table, (spec, primary) in tables.items():
        info = list(connection.execute(f'PRAGMA table_info("{table}")'))
        types = {row[1]: row[2].upper() for row in info}
        expected = {part.split(":")[0]: {"I": "INTEGER", "B": "BLOB"}.get(part.split(":")[-1], "TEXT") for part in spec.split()}
        if any(types.get(key) != value for key, value in expected.items()):
            raise _Integrity(f"missing/incompatible columns: {table}")
        if tuple(row[1] for row in sorted(info, key=lambda row: row[5]) if row[5]) != primary:
            raise _Integrity(f"incompatible primary key: {table}")
        keys = set()
        for row in connection.execute(f'PRAGMA index_list("{table}")'):
            if row[2] != 1 or row[4] != 0:
                continue
            name = row[1].replace('"', '""')
            columns = [item for item in connection.execute(f'PRAGMA index_xinfo("{name}")') if item[5]]
            if all(item[2] is not None and item[4] == "BINARY" for item in columns):
                keys.add(tuple(item[2] for item in columns))
        if any(key not in keys for key in unique.get(table, ())):
            raise _Integrity(f"required unique key absent: {table}")
        groups = {}
        for row in connection.execute(f'PRAGMA foreign_key_list("{table}")'):
            groups.setdefault(row[0], []).append(row)
        relations = set()
        for rows in groups.values():
            rows.sort(key=lambda row: row[1])
            if all(row[5] == "RESTRICT" and row[6] == "RESTRICT" for row in rows):
                relations.add((tuple(row[3] for row in rows), rows[0][2], tuple(row[4] for row in rows)))
        if any(relation not in relations for relation in _FK.get(table, ())):
            raise _Integrity(f"required foreign key absent: {table}")
        if connection.execute(f'PRAGMA foreign_key_check("{table}")').fetchone() is not None:
            raise _Integrity(f"broken stored linkage: {table}")


@_dataclass(frozen=True, slots=True)
class _SnapshotMetadata:
    identity: _Identity
    internal_id: int
    cutoff: _datetime
    digest: str


def _prediction(connection: _sqlite3.Connection, repository: _Snapshots, target: _Target, dataset: str, target_date: _date):
    external = _External("NAR", "nar_official", target.external_race_id)
    key = (external.organization, external.source_system, external.external_race_id)
    mapped = list(connection.execute(
        "SELECT internal_race_id FROM historical_input_external_races WHERE organization=? AND source_system=? AND external_race_id=?", key))
    headers = list(connection.execute(
        "SELECT internal_race_id,source_url,captured_at_utc,information_cutoff_utc,content_sha256 "
        "FROM historical_input_snapshots WHERE dataset_id=? AND organization=? AND source_system=? AND external_race_id=?", (dataset, *key)))
    if not mapped:
        if headers:
            raise _Integrity("snapshot has no exact internal mapping")
        return None, None, ("INTERNAL_RACE_MAPPING_MISSING",)
    if len(mapped) != 1:
        raise _Integrity("ambiguous internal mapping")
    internal = _positive(mapped[0][0])
    reverse = list(connection.execute(
        "SELECT external_race_id FROM historical_input_external_races WHERE organization=? AND source_system=? AND internal_race_id=?", (*key[:2], internal)))
    if len(reverse) != 1 or reverse[0][0] != target.external_race_id:
        raise _Integrity("contradictory internal mapping")
    if len(list(connection.execute("SELECT id FROM races WHERE id=?", (internal,)))) != 1:
        raise _Integrity("mapped race does not exist")
    eligible = []
    seen = set()
    for stored_internal, url, captured, cutoff, digest in headers:
        if _positive(stored_internal) != internal:
            raise _Integrity("snapshot internal identity disagrees")
        captured, cutoff = _stored_time(captured), _stored_time(cutoff)
        if captured in seen or captured > cutoff:
            raise _Integrity("duplicate snapshot identity or noncausal metadata")
        seen.add(captured)
        if type(digest) is not str or _SHA.fullmatch(digest) is None:
            raise _Integrity("invalid snapshot digest metadata")
        try:
            identity = _Identity(dataset, _Source(*key, url), captured)
        except ValueError as error:
            raise _Integrity("invalid snapshot identity metadata") from error
        if captured <= target.scheduled_start_at and cutoff <= target.scheduled_start_at:
            eligible.append(_SnapshotMetadata(identity, internal, cutoff, digest))
    latest = None
    if eligible:
        greatest = max(item.identity.captured_at for item in eligible)
        winners = [item for item in eligible if item.identity.captured_at == greatest]
        if len(winners) != 1:
            raise _Integrity("ambiguous greatest snapshot")
        latest = winners[0]
    loaded = repository.load_latest_snapshot(
        dataset_id=dataset, race_id=internal, information_cutoff=target.scheduled_start_at, source_identity=external)
    if latest is None:
        if loaded is not None:
            raise _Integrity("metadata/latest not-found disagreement")
        return internal, None, ("SNAPSHOT_AFTER_SELECTION_BOUND" if headers else "SNAPSHOT_MISSING",)
    if (type(loaded) is not _Snapshot or loaded.identity != latest.identity or loaded.internal_race_id != internal
            or loaded.information_cutoff != latest.cutoff or loaded.content_sha256 != latest.digest):
        raise _Integrity("metadata/latest snapshot disagreement")
    exact = repository.load_snapshot_by_identity(identity=loaded.identity)
    if type(exact) is not _Snapshot or exact != loaded or exact.content_sha256 != latest.digest:
        raise _Integrity("latest/exact snapshot disagreement")
    if exact.race.target_race_date != target_date or exact.race.scheduled_start_at != target.scheduled_start_at:
        return internal, None, ("SNAPSHOT_TARGET_MISMATCH",)
    return internal, exact, ()


_CAPTURE_COLUMNS = (
    "capture_id,schema_version,page_kind,canonical_source_url,response_sha256,charset,"
    "requested_at_utc,observed_at_utc,stored_at_utc,http_status,content_type,content_encoding,"
    "http_date,etag,last_modified,content_length"
)


@_dataclass(frozen=True, slots=True)
class _CaptureMetadata:
    row: tuple
    external_id: str
    observed: _datetime


def _capture_metadata(connection: _sqlite3.Connection) -> tuple[_CaptureMetadata, ...]:
    result = []
    ids, identities = set(), set()
    for raw in connection.execute(f"SELECT {_CAPTURE_COLUMNS} FROM nar_official_response_captures"):
        row = tuple(raw)
        identifier, version, kind, url, digest, charset, requested, observed, stored, status, content_type, encoding, http_date, etag, modified, length = row
        if type(identifier) is not str or _CAPTURE_ID.fullmatch(identifier) is None or identifier in ids:
            raise _Integrity("invalid/duplicate stored capture ID")
        ids.add(identifier)
        if type(version) is not int or version != 1 or type(digest) is not str or _SHA.fullmatch(digest) is None:
            raise _Integrity("invalid stored capture version/digest")
        try:
            page, canonical = _canonical_url(url)
        except _CaptureError as error:
            raise _Integrity("invalid stored official URL") from error
        if canonical != url or type(kind) is not str or page.value != kind:
            raise _Integrity("stored page/URL identity disagrees")
        requested, observed, stored = (_stored_time(value) for value in (requested, observed, stored))
        if not requested <= observed <= stored:
            raise _Integrity("noncausal capture metadata")
        if charset != "utf-8" or type(status) is not int or status != 200 or encoding not in (None, "identity"):
            raise _Integrity("invalid capture response metadata")
        if any(value is not None and type(value) is not str for value in (content_type, http_date, etag, modified)):
            raise _Integrity("invalid capture headers")
        if length is not None and (type(length) is not int or length < 0):
            raise _Integrity("invalid content length")
        evidence_key = (url, digest, observed)
        if evidence_key in identities:
            raise _Integrity("duplicate persisted evidence identity")
        identities.add(evidence_key)
        if page is _Kind.RACE_MARK_TABLE:
            query = dict(_parse_qsl(_urlsplit(url).query, strict_parsing=True))
            date = _date.fromisoformat(query["k_raceDate"].replace("/", "-"))
            external = f"nar:{date:%Y%m%d}:{query['k_babaCode']}:{query['k_raceNo']}"
            result.append(_CaptureMetadata(row, external, observed))
    return tuple(result)


def _settlement(metadata: tuple[_CaptureMetadata, ...], repository: _Captures, target: _Target, cutoff: _datetime):
    candidates = [item for item in metadata if item.external_id == target.external_race_id and item.observed <= cutoff]
    if not candidates:
        return None, ("RESULT_CAPTURE_MISSING", "PAYOUT_CAPTURE_MISSING")
    greatest = max(item.observed for item in candidates)
    winners = [item for item in candidates if item.observed == greatest]
    if len(winners) != 1:
        return None, ("SETTLEMENT_CAPTURE_AMBIGUOUS",)
    selected = winners[0]
    capture = repository.load_capture(capture_id=selected.row[0])
    if type(capture) is not _Capture:
        raise _Integrity("selected capture disappeared")
    actual = (
        capture.capture_id, capture.schema_version, capture.page_kind.value, capture.canonical_source_url,
        capture.response_sha256, capture.charset, _time_text(capture.requested_at), _time_text(capture.observed_at),
        _time_text(capture.stored_at), capture.http_status, capture.content_type, capture.content_encoding,
        capture.http_date, capture.etag, capture.last_modified, capture.content_length,
    )
    if actual != selected.row:
        raise _Integrity("capture metadata/exact load disagreement")
    return _Reference(capture.capture_id, capture.canonical_source_url, capture.response_sha256, capture.observed_at), ()


def _native_reasons(target: _Target, target_date: _date) -> tuple[str, ...]:
    match = _RACE_ID.fullmatch(target.external_race_id)
    if match is None or match[1] != target_date.strftime("%Y%m%d"):
        return ("TARGET_EVIDENCE_IDENTITY_MISMATCH",)
    kind = target.provider_disposition_evidence.evidence_kind_and_version
    if kind == _NORMAL:
        return () if target.scheduled_start_at is not None else ("SCHEDULED_START_UNAVAILABLE",)
    reasons = ("NATIVE_NON_RUN",) if kind == _NON_RUN else ("UNKNOWN_NATIVE_DISPOSITION",)
    return reasons if target.scheduled_start_at is not None else (*reasons, "SCHEDULED_START_UNAVAILABLE")


def _disposition(reasons: tuple[str, ...]) -> _Disposition:
    if any(reason in reasons for reason in ("SNAPSHOT_TARGET_MISMATCH", "SETTLEMENT_CAPTURE_AMBIGUOUS", "TARGET_EVIDENCE_IDENTITY_MISMATCH")):
        return _Disposition.INVALID_EVIDENCE
    if "NATIVE_NON_RUN" in reasons or "UNKNOWN_NATIVE_DISPOSITION" in reasons:
        return _Disposition.UNSUPPORTED
    if "SCHEDULED_START_UNAVAILABLE" in reasons:
        return _Disposition.INVALID_EVIDENCE
    if any(reason in reasons for reason in ("INTERNAL_RACE_MAPPING_MISSING", "SNAPSHOT_MISSING", "SNAPSHOT_AFTER_SELECTION_BOUND")):
        return _Disposition.MISSING_PREDICTION_EVIDENCE
    return _Disposition.MISSING_SETTLEMENT_EVIDENCE if reasons else _Disposition.EXECUTABLE


def resolve_sqlite_nar_daily_evidence(
    *, target_set: _TargetSet, dataset_id: str, settlement_information_cutoff: _datetime,
    snapshot_connection: _sqlite3.Connection, capture_connection: _sqlite3.Connection,
) -> _Resolution:
    """Resolve every audited target, or raise without returning a partial day."""
    if type(target_set) is not _TargetSet:
        raise ValueError("target_set must be an audited exact target-set value")
    dataset = _text(dataset_id)
    cutoff = _utc(settlement_information_cutoff)
    if target_set.provider_scope.providers != (_NAR,) or not target_set.target_races:
        raise _DiscoveryError(_DiscoveryCode.UNSUPPORTED_ENVELOPE_STATE, "NAR nonempty audited scope required")
    connections = (snapshot_connection, capture_connection)
    if snapshot_connection is capture_connection:
        raise _Validation("distinct main and archive connections required")
    try:
        for connection in connections:
            if type(connection) is not _sqlite3.Connection or connection.in_transaction:
                raise _Validation("usable connections without caller transactions required")
        for connection in connections:
            connection.execute("PRAGMA query_only=ON")
            if connection.execute("PRAGMA query_only").fetchone()[0] != 1:
                raise _Validation("query_only could not be enabled")
        snapshots = _Snapshots(connection=snapshot_connection)
        captures = _Captures(connection=capture_connection)
    except _sqlite3.Error as error:
        raise _Validation("unusable database connection") from error
    owned = []
    try:
        for connection in connections:
            connection.execute("BEGIN")
            owned.append(connection)
        _schema(snapshot_connection, _MAIN, _MAIN_UNIQUE)
        _schema(capture_connection, _ARCHIVE, {"nar_official_response_captures": (_ARCHIVE_KEY,)})
        metadata = _capture_metadata(capture_connection)
        outcomes = []
        for target in target_set.target_races:
            reasons = _native_reasons(target, target_set.target_date)
            internal, snapshot, reference = None, None, None
            if not reasons:
                internal, snapshot, prediction_reasons = _prediction(snapshot_connection, snapshots, target, dataset, target_set.target_date)
                reference, settlement_reasons = _settlement(metadata, captures, target, cutoff)
                reasons = (*prediction_reasons, *settlement_reasons)
            outcomes.append(_Outcome(
                target, _disposition(reasons), reasons, internal,
                None if snapshot is None else snapshot.identity,
                None if snapshot is None else snapshot.content_sha256,
                reference, reference,
            ))
        return _Resolution(target_set, dataset, "LATEST_CAUSAL_IN_DATASET", cutoff, tuple(outcomes))
    except _sqlite3.Error as error:
        raise _Integrity("daily evidence SQLite read failed") from error
    finally:
        for connection in reversed(owned):
            connection.rollback()


if "annotations" in globals():
    del annotations
