"""Strict local read-side for the one published NAR V3 source profile."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import stat

from scripts.simulation import nar_race_entry_status_raw_capture as _raw_capture
from scripts.simulation import nar_race_entry_status_source_profile_diagnostics as _profile_b
from scripts.simulation import nar_race_entry_status_source_profile_profile_a as _profile_a
from scripts.simulation import nar_race_entry_status_source_profile_publication_contract as _contract
from scripts.simulation import nar_race_entry_status_source_profile_publication_plan as _plan
from scripts.simulation import nar_race_entry_status_source_profile_structural_recovery_diagnostics as _phase66
from scripts.simulation.nar_race_entry_status_source_profile_publication_plan import (
    EXPECTED_DEBA_TABLE_PATH_V3,
    EXPECTED_MANIFEST_PATH_V3,
    EXPECTED_RACE_LIST_PATH_V3,
)


_SUPPORTED_TARGET = _raw_capture.NARRaceEntryStatusRaceIdentity("21", date(2025, 1, 1), 6)
_CONCRETE_PATH_TYPE = type(Path())
_EXPECTED_DIRECTORY_NAMES = frozenset({"deba_table.html", "race_list.html", "manifest.json"})
_EXPECTED_MANIFEST_KEYS = frozenset(
    {
        "acquisition_semantics",
        "closed_bundle_identity",
        "documents",
        "fixture_set_identity",
        "manifest_schema",
        "manifest_schema_version",
        "market_eligibility",
        "profile_a",
        "profile_b",
        "provider",
        "publication_safety",
        "qualification_identity",
        "target",
    }
)
_EXPECTED_DOCUMENT_KEYS = frozenset(
    {
        "capture_identity",
        "captured_at",
        "effective_url_matches_canonical",
        "fixture_relative_path",
        "observed_at",
        "request_identity",
        "requested_at",
        "response_byte_length",
        "response_sha256",
        "role",
    }
)

_FROZEN_DEBA_LENGTH = 313317
_FROZEN_DEBA_SHA256 = "6c9aa3ea614c17e14f0e7a5050190ca923445925d67f8e61e71db95e87c87727"
_FROZEN_RACE_LIST_LENGTH = 66307
_FROZEN_RACE_LIST_SHA256 = "1eb363621c7a152929765ff7ffecabea2d7cf15283d45fa9c31036527c0b53a1"
_FROZEN_MANIFEST_LENGTH = 4254
_FROZEN_MANIFEST_SHA256 = "3ca36ed4cec1002e0440fb02e466f40dd7f4d74ffb7c0bdf7b55be2271af321d"
_FROZEN_FIXTURE_SET_IDENTITY = (
    "nar-race-entry-status-source-profile-fixture-set-v3:"
    "11f18aae600df59ab90ce9cd3dd3614ff250698d783bcd96e6917cc38a8ab225"
)
_FROZEN_QUALIFICATION_IDENTITY = (
    "nar-race-entry-status-source-profile-qualification-v3:"
    "a7f0ba5ed66a71f9785c80b1ba1b5f556b2328d09ead597839cc068a84b0d3ff"
)


class NARRaceEntryStatusSourceProfileFixtureConsumerError(Exception):
    """Base failure for strict local V3 fixture consumption."""

    def __init__(self, classification: str, message: str) -> None:
        self.classification = classification
        super().__init__(f"{classification}: {message}")


class NARRaceEntryStatusSourceProfileFixtureUnsupportedError(
    NARRaceEntryStatusSourceProfileFixtureConsumerError
):
    """Raised when a caller requests unsupported authority."""


class NARRaceEntryStatusSourceProfileFixtureFilesystemError(
    NARRaceEntryStatusSourceProfileFixtureConsumerError
):
    """Raised when local path or stable-read authority fails."""


class NARRaceEntryStatusSourceProfileFixtureManifestError(
    NARRaceEntryStatusSourceProfileFixtureConsumerError
):
    """Raised when manifest syntax or declared identity is contradictory."""


class NARRaceEntryStatusSourceProfileFixtureAuthorityError(
    NARRaceEntryStatusSourceProfileFixtureConsumerError
):
    """Raised when formal or frozen V3 authority fails."""


def _unsupported(message: str) -> NARRaceEntryStatusSourceProfileFixtureUnsupportedError:
    return NARRaceEntryStatusSourceProfileFixtureUnsupportedError("UNSUPPORTED_TARGET", message)


def _filesystem(
    classification: str, message: str
) -> NARRaceEntryStatusSourceProfileFixtureFilesystemError:
    return NARRaceEntryStatusSourceProfileFixtureFilesystemError(classification, message)


def _manifest(classification: str, message: str) -> NARRaceEntryStatusSourceProfileFixtureManifestError:
    return NARRaceEntryStatusSourceProfileFixtureManifestError(classification, message)


def _authority(
    classification: str, message: str
) -> NARRaceEntryStatusSourceProfileFixtureAuthorityError:
    return NARRaceEntryStatusSourceProfileFixtureAuthorityError(classification, message)


@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusSourceProfileFixtureBundleV3:
    target: _raw_capture.NARRaceEntryStatusRaceIdentity
    deba_table_bytes: bytes
    race_list_bytes: bytes
    manifest_bytes: bytes
    manifest: _contract.SourceProfileManifestV3
    phase66_ancestry: _phase66.ProfileBCandidateAncestryRecoveryDiagnostics
    publication_plan: _plan.SourceProfilePublicationPlanV3
    repository_relative_paths: tuple[str, str, str]

    def __post_init__(self) -> None:
        if type(self.target) is not _raw_capture.NARRaceEntryStatusRaceIdentity or self.target != _SUPPORTED_TARGET:
            raise _unsupported("bundle target is outside the single published authority")
        if any(type(value) is not bytes for value in (
            self.deba_table_bytes,
            self.race_list_bytes,
            self.manifest_bytes,
        )):
            raise _authority("FORMAL_AUTHORITY_VALIDATION_FAILURE", "bundle bytes must be exact bytes")
        if type(self.manifest) is not _contract.SourceProfileManifestV3:
            raise _authority("FORMAL_AUTHORITY_VALIDATION_FAILURE", "bundle manifest type is invalid")
        if type(self.phase66_ancestry) is not _phase66.ProfileBCandidateAncestryRecoveryDiagnostics:
            raise _authority("FORMAL_AUTHORITY_VALIDATION_FAILURE", "bundle Phase66 type is invalid")
        if type(self.publication_plan) is not _plan.SourceProfilePublicationPlanV3:
            raise _authority("FORMAL_AUTHORITY_VALIDATION_FAILURE", "bundle publication plan type is invalid")
        expected_paths = (
            EXPECTED_DEBA_TABLE_PATH_V3,
            EXPECTED_RACE_LIST_PATH_V3,
            EXPECTED_MANIFEST_PATH_V3,
        )
        if type(self.repository_relative_paths) is not tuple or self.repository_relative_paths != expected_paths:
            raise _authority("FORMAL_AUTHORITY_VALIDATION_FAILURE", "bundle path tuple is invalid")


def _is_reparse(value: os.stat_result) -> bool:
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(value, "st_file_attributes", 0)
    return bool(flag and attributes & flag)


def _unsafe_redirect(value: os.stat_result) -> bool:
    return stat.S_ISLNK(value.st_mode) or _is_reparse(value)


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns)


def _lstat(path: Path, *, missing_message: str) -> os.stat_result:
    try:
        return path.lstat()
    except (FileNotFoundError, NotADirectoryError) as error:
        raise _filesystem("MISSING_FIXTURE", missing_message) from error
    except (OSError, ValueError) as error:
        raise _filesystem("FILESYSTEM_VIOLATION", "local path metadata could not be read") from error


def _validate_directory(path: Path, *, missing_message: str) -> os.stat_result:
    value = _lstat(path, missing_message=missing_message)
    if _unsafe_redirect(value) or not stat.S_ISDIR(value.st_mode):
        raise _filesystem("FILESYSTEM_VIOLATION", "expected directory is unsafe or not a directory")
    return value


def _validate_regular_file(path: Path, *, missing_message: str) -> os.stat_result:
    value = _lstat(path, missing_message=missing_message)
    if _unsafe_redirect(value) or not stat.S_ISREG(value.st_mode):
        raise _filesystem("FILESYSTEM_VIOLATION", "fixture artifact is unsafe or not a regular file")
    return value


def _path_from_authority(repository_root: Path, repository_path: str) -> Path:
    relative = PurePosixPath(repository_path)
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise _filesystem("FILESYSTEM_VIOLATION", "publication path authority is noncanonical")
    return repository_root.joinpath(*relative.parts)


def _contained_resolved(path: Path, repository_root: Path) -> Path:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(repository_root)
    except (FileNotFoundError, NotADirectoryError) as error:
        raise _filesystem("MISSING_FIXTURE", "required fixture path is missing") from error
    except (OSError, RuntimeError, ValueError) as error:
        raise _filesystem("FILESYSTEM_VIOLATION", "fixture path escapes or cannot be resolved") from error
    return resolved


def _validate_component_chain(repository_root: Path, path: Path) -> None:
    try:
        relative = path.relative_to(repository_root)
    except ValueError as error:
        raise _filesystem("FILESYSTEM_VIOLATION", "fixture path is outside repository root") from error
    current = repository_root
    for index, part in enumerate(relative.parts):
        current = current / part
        value = _lstat(current, missing_message="required fixture path is missing")
        if _unsafe_redirect(value):
            raise _filesystem("FILESYSTEM_VIOLATION", "fixture path contains a link or reparse point")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(value.st_mode):
            raise _filesystem("FILESYSTEM_VIOLATION", "fixture path has a non-directory parent")


def _stable_read(path: Path) -> bytes:
    before = _validate_regular_file(path, missing_message="required fixture artifact is missing")
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if _unsafe_redirect(opened) or not stat.S_ISREG(opened.st_mode):
                raise _filesystem("FILESYSTEM_VIOLATION", "opened fixture artifact is unsafe")
            if _stat_identity(before) != _stat_identity(opened):
                raise _filesystem("FILESYSTEM_VIOLATION", "fixture identity changed before read")
            payload = handle.read()
            opened_after = os.fstat(handle.fileno())
    except NARRaceEntryStatusSourceProfileFixtureConsumerError:
        raise
    except (OSError, ValueError) as error:
        raise _filesystem("FILESYSTEM_VIOLATION", "fixture artifact could not be read") from error
    after = _validate_regular_file(path, missing_message="fixture artifact disappeared after read")
    if _stat_identity(opened) != _stat_identity(opened_after) or _stat_identity(opened_after) != _stat_identity(after):
        raise _filesystem("FILESYSTEM_VIOLATION", "fixture identity changed during read")
    if len(payload) != opened_after.st_size:
        raise _filesystem("FILESYSTEM_VIOLATION", "fixture size contradicts opened file metadata")
    return payload


class _DuplicateManifestKey(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateManifestKey(key)
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"non-finite constant {value}")


def _parse_manifest(manifest_bytes: bytes) -> dict[str, object]:
    try:
        text = manifest_bytes.decode("utf-8", errors="strict")
        payload = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateManifestKey, TypeError, ValueError) as error:
        raise _manifest("MANIFEST_INVALID", "manifest is malformed or ambiguous") from error
    if type(payload) is not dict or canonical != manifest_bytes:
        raise _manifest("MANIFEST_INVALID", "manifest is not one canonical JSON object")
    return payload


def _basic_manifest_documents(payload: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    if frozenset(payload) != _EXPECTED_MANIFEST_KEYS:
        raise _manifest("MANIFEST_INVALID", "manifest keys do not match the exact V3 schema")
    if payload.get("manifest_schema") != _contract.MANIFEST_SCHEMA or payload.get("manifest_schema_version") != 3:
        raise _manifest("MANIFEST_INVALID", "manifest schema or version is unsupported")
    expected_target = {"baba_code": "21", "race_date": "2025-01-01", "race_no": 6}
    if payload.get("provider") != "NAR":
        raise _manifest("TARGET_OR_PATH_CONTRADICTION", "manifest provider is not NAR")
    if payload.get("target") != expected_target:
        raise _manifest("TARGET_OR_PATH_CONTRADICTION", "manifest target is contradictory")
    if payload.get("acquisition_semantics") != _contract.ACQUISITION_SEMANTICS:
        raise _manifest("TARGET_OR_PATH_CONTRADICTION", "manifest acquisition semantics are contradictory")
    if payload.get("market_eligibility") != _contract.MARKET_ELIGIBILITY:
        raise _manifest("TARGET_OR_PATH_CONTRADICTION", "manifest market eligibility is contradictory")
    documents = payload.get("documents")
    if type(documents) is not list or len(documents) != 2 or any(type(item) is not dict for item in documents):
        raise _manifest("MANIFEST_INVALID", "manifest must contain exactly two document objects")
    deba, race_list = documents
    if frozenset(deba) != _EXPECTED_DOCUMENT_KEYS or frozenset(race_list) != _EXPECTED_DOCUMENT_KEYS:
        raise _manifest("MANIFEST_INVALID", "manifest document keys are noncanonical")
    if [deba.get("role"), race_list.get("role")] != ["deba_table", "race_list"]:
        raise _manifest("TARGET_OR_PATH_CONTRADICTION", "manifest document role order is contradictory")
    if [deba.get("fixture_relative_path"), race_list.get("fixture_relative_path")] != [
        EXPECTED_DEBA_TABLE_PATH_V3,
        EXPECTED_RACE_LIST_PATH_V3,
    ]:
        raise _manifest("TARGET_OR_PATH_CONTRADICTION", "manifest fixture paths are contradictory")
    return deba, race_list


def _document_metadata(document: dict[str, object], role: str) -> _profile_b.CaptureDocumentMetadata:
    try:
        return _profile_b.CaptureDocumentMetadata(
            document_role=role,
            request_identity=document["request_identity"],
            capture_identity=document["capture_identity"],
            response_sha256=document["response_sha256"],
            response_byte_length=document["response_byte_length"],
            requested_at=document["requested_at"],
            observed_at=document["observed_at"],
            captured_at=document["captured_at"],
            effective_url_matches_canonical=document["effective_url_matches_canonical"],
        )
    except Exception as error:
        raise _manifest("MANIFEST_INVALID", "capture metadata is invalid") from error


def _require_document_identity(document: dict[str, object], payload: bytes, role: str) -> None:
    digest = sha256(payload).hexdigest()
    if document.get("response_sha256") != digest or document.get("response_byte_length") != len(payload):
        raise _manifest("DOCUMENT_IDENTITY_MISMATCH", f"{role} bytes contradict manifest metadata")


def _recompute_authority(
    *,
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
    deba_table_bytes: bytes,
    race_list_bytes: bytes,
    manifest_bytes: bytes,
    payload: dict[str, object],
    deba_document: dict[str, object],
    race_list_document: dict[str, object],
) -> tuple[
    _contract.SourceProfileManifestV3,
    _phase66.ProfileBCandidateAncestryRecoveryDiagnostics,
    _plan.SourceProfilePublicationPlanV3,
]:
    try:
        capture_summary = _profile_b.CaptureMetadataSummary(
            deba_table=_document_metadata(deba_document, "deba_table"),
            race_list=_document_metadata(race_list_document, "race_list"),
            closed_bundle_identity=payload["closed_bundle_identity"],
        )
        profile_a = _profile_a.diagnose_nar_race_entry_status_profile_a_v3(
            deba_table_bytes=deba_table_bytes,
            target=target,
        )
        profile_b = _profile_b.diagnose_nar_race_entry_status_profile_b_v2(
            race_list_bytes=race_list_bytes,
            target=target,
        )
        safety = _contract.assess_nar_race_entry_status_raw_fixture_publication_safety_v3(
            deba_table_bytes=deba_table_bytes,
            race_list_bytes=race_list_bytes,
        )
        ancestry = _phase66.diagnose_nar_race_entry_status_profile_b_candidate_ancestry_recovery(
            race_list_bytes=race_list_bytes,
            target=target,
        )
        if (
            type(profile_a) is not _profile_a.ProfileADiagnosticsV3
            or profile_a.overall_result != "QUALIFIED"
            or len(profile_a.predicate_results) != 3
            or any(item.outcome is not _profile_a.ProfileAOutcome.PASS for item in profile_a.predicate_results)
        ):
            raise ValueError("Profile-A v3 is not fully qualified")
        if (
            type(profile_b) is not _profile_b.ProfileBDiagnosticsV2
            or profile_b.overall_result != "QUALIFIED"
            or len(profile_b.predicate_results) != 6
            or any(item.outcome is not _profile_b.ProfileBPredicateOutcome.PASS for item in profile_b.predicate_results)
        ):
            raise ValueError("Profile-B v2 is not fully qualified")
        schedule_count = profile_b.predicate_results[1].safe_fields["target_6r_row_count"]
        if schedule_count != 1:
            raise ValueError("Profile-B schedule count is not one")
        if (
            type(safety) is not _contract.RawFixturePublicationSafetyV3
            or safety.result is not _contract.PublicationSafetyOutcome.SAFE
            or not safety.raw_fixture_publication_safe
            or len(safety.category_results) != 5
            or any(
                item.outcome is not _contract.PublicationSafetyOutcome.SAFE or item.finding_count != 0
                for item in safety.category_results
            )
        ):
            raise ValueError("publication Safety v3 is not fully safe")
        if (
            type(ancestry) is not _phase66.ProfileBCandidateAncestryRecoveryDiagnostics
            or ancestry.race_table_scope_count != 1
            or ancestry.target_candidate_count != 2
            or not ancestry.candidate_details_complete
        ):
            raise ValueError("Phase66 candidate ancestry is contradictory")
        direct_count = sum(item.direct_schedule_table_descendant for item in ancestry.candidate_results)
        change_count = sum(item.inside_change_info_table for item in ancestry.candidate_results)
        if direct_count != 1 or change_count != 1 or schedule_count != direct_count:
            raise ValueError("Profile-B and Phase66 structure is contradictory")
        fixture_set = _contract.build_nar_race_entry_status_fixture_set_v3(
            target=target,
            capture_summary=capture_summary,
        )
        qualification = _contract.build_nar_race_entry_status_qualification_v3(
            target=target,
            fixture_set=fixture_set,
            profile_a=profile_a,
            profile_b=profile_b,
        )
        rebuilt_manifest = _contract.build_nar_race_entry_status_manifest_v3(
            fixture_set=fixture_set,
            qualification=qualification,
            publication_safety=safety,
        )
        if rebuilt_manifest.canonical_bytes() != manifest_bytes:
            raise ValueError("rebuilt manifest bytes differ from loaded manifest")
        validated_manifest = _contract.validate_nar_race_entry_status_manifest_v3(
            manifest_bytes=manifest_bytes,
            fixture_set=fixture_set,
            qualification=qualification,
            publication_safety=safety,
        )
        publication_plan = _plan.build_nar_race_entry_status_source_profile_publication_plan_v3(
            fixture_set=fixture_set,
        )
        _plan.validate_nar_race_entry_status_source_profile_publication_plan_v3(
            value=publication_plan,
            fixture_set=fixture_set,
        )
    except NARRaceEntryStatusSourceProfileFixtureConsumerError:
        raise
    except Exception as error:
        raise _authority(
            "FORMAL_AUTHORITY_VALIDATION_FAILURE",
            "existing V3 authority rejected the local fixture",
        ) from error
    return validated_manifest, ancestry, publication_plan


def _require_frozen_phase83_identity(
    *,
    deba_table_bytes: bytes,
    race_list_bytes: bytes,
    manifest_bytes: bytes,
    manifest: _contract.SourceProfileManifestV3,
) -> None:
    actual = (
        (len(deba_table_bytes), sha256(deba_table_bytes).hexdigest()),
        (len(race_list_bytes), sha256(race_list_bytes).hexdigest()),
        (len(manifest_bytes), sha256(manifest_bytes).hexdigest()),
    )
    expected = (
        (_FROZEN_DEBA_LENGTH, _FROZEN_DEBA_SHA256),
        (_FROZEN_RACE_LIST_LENGTH, _FROZEN_RACE_LIST_SHA256),
        (_FROZEN_MANIFEST_LENGTH, _FROZEN_MANIFEST_SHA256),
    )
    if actual != expected:
        raise _authority("FROZEN_PHASE83_IDENTITY_MISMATCH", "artifact bytes differ from Phase83")
    if (
        manifest.fixture_set.identity != _FROZEN_FIXTURE_SET_IDENTITY
        or manifest.qualification.identity != _FROZEN_QUALIFICATION_IDENTITY
    ):
        raise _authority("FROZEN_PHASE83_IDENTITY_MISMATCH", "formal identities differ from Phase83")


def load_nar_race_entry_status_source_profile_v3_fixture(
    *,
    repository_root: Path,
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
) -> NARRaceEntryStatusSourceProfileFixtureBundleV3:
    """Load and validate the exact Phase83-published local V3 fixture."""

    if type(repository_root) is not _CONCRETE_PATH_TYPE:
        raise _filesystem("FILESYSTEM_VIOLATION", "repository_root must be exact concrete Path")
    if "\x00" in str(repository_root) or not repository_root.is_absolute():
        raise _filesystem("FILESYSTEM_VIOLATION", "repository_root must be NUL-free and absolute")
    if type(target) is not _raw_capture.NARRaceEntryStatusRaceIdentity or target != _SUPPORTED_TARGET:
        raise _unsupported("only NAR / 21 / 2025-01-01 / 6 is supported")

    _validate_directory(repository_root, missing_message="repository_root is missing")
    try:
        resolved_root = repository_root.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise _filesystem("FILESYSTEM_VIOLATION", "repository_root cannot be resolved") from error
    if resolved_root != repository_root:
        raise _filesystem("FILESYSTEM_VIOLATION", "repository_root must already be canonical")

    relative_paths = (
        EXPECTED_DEBA_TABLE_PATH_V3,
        EXPECTED_RACE_LIST_PATH_V3,
        EXPECTED_MANIFEST_PATH_V3,
    )
    artifact_paths = tuple(_path_from_authority(resolved_root, value) for value in relative_paths)
    parents = tuple(path.parent for path in artifact_paths)
    if len(set(parents)) != 1:
        raise _filesystem("FILESYSTEM_VIOLATION", "V3 path authority does not share one target directory")
    target_directory = parents[0]
    _validate_component_chain(resolved_root, target_directory)
    _validate_directory(target_directory, missing_message="V3 target fixture directory is missing")
    _contained_resolved(target_directory, resolved_root)

    try:
        with os.scandir(target_directory) as entries:
            directory_entries = tuple(entries)
    except OSError as error:
        raise _filesystem("FILESYSTEM_VIOLATION", "fixture directory cannot be enumerated") from error
    names = frozenset(entry.name for entry in directory_entries)
    if _EXPECTED_DIRECTORY_NAMES - names:
        raise _filesystem("MISSING_FIXTURE", "fixture directory is missing a required artifact")
    if names != _EXPECTED_DIRECTORY_NAMES:
        raise _filesystem(
            "UNEXPECTED_FIXTURE_DIRECTORY_CONTENT",
            "fixture directory contains unexpected content",
        )
    for entry in directory_entries:
        try:
            value = entry.stat(follow_symlinks=False)
        except OSError as error:
            raise _filesystem("FILESYSTEM_VIOLATION", "fixture directory entry cannot be inspected") from error
        if entry.is_symlink() or _unsafe_redirect(value) or not stat.S_ISREG(value.st_mode):
            raise _filesystem("FILESYSTEM_VIOLATION", "fixture directory entry is unsafe")

    for path in artifact_paths:
        _validate_component_chain(resolved_root, path)
        _contained_resolved(path, resolved_root)
    deba_table_bytes, race_list_bytes, manifest_bytes = tuple(_stable_read(path) for path in artifact_paths)

    payload = _parse_manifest(manifest_bytes)
    deba_document, race_list_document = _basic_manifest_documents(payload)
    _require_document_identity(deba_document, deba_table_bytes, "deba_table")
    _require_document_identity(race_list_document, race_list_bytes, "race_list")
    manifest, ancestry, publication_plan = _recompute_authority(
        target=target,
        deba_table_bytes=deba_table_bytes,
        race_list_bytes=race_list_bytes,
        manifest_bytes=manifest_bytes,
        payload=payload,
        deba_document=deba_document,
        race_list_document=race_list_document,
    )
    _require_frozen_phase83_identity(
        deba_table_bytes=deba_table_bytes,
        race_list_bytes=race_list_bytes,
        manifest_bytes=manifest_bytes,
        manifest=manifest,
    )
    return NARRaceEntryStatusSourceProfileFixtureBundleV3(
        target=target,
        deba_table_bytes=deba_table_bytes,
        race_list_bytes=race_list_bytes,
        manifest_bytes=manifest_bytes,
        manifest=manifest,
        phase66_ancestry=ancestry,
        publication_plan=publication_plan,
        repository_relative_paths=relative_paths,
    )


__all__ = (
    "NARRaceEntryStatusSourceProfileFixtureAuthorityError",
    "NARRaceEntryStatusSourceProfileFixtureBundleV3",
    "NARRaceEntryStatusSourceProfileFixtureConsumerError",
    "NARRaceEntryStatusSourceProfileFixtureFilesystemError",
    "NARRaceEntryStatusSourceProfileFixtureManifestError",
    "NARRaceEntryStatusSourceProfileFixtureUnsupportedError",
    "load_nar_race_entry_status_source_profile_v3_fixture",
)
