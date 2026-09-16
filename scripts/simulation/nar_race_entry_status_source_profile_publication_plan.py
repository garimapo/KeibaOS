from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata

from scripts.simulation.nar_race_entry_status_source_profile_publication_contract import (
    FixtureSetV2,
    SourceProfilePublicationContractError,
    validate_nar_race_entry_status_fixture_set_v2,
)


AUTHORITY_SEMANTIC = "PHASE60_PUBLICATION_PLAN_AUTHORITY_EFFECTIVE_FROM_INTEGRATION"
REQUIRED_GITATTRIBUTES_RULE = (
    "tests/fixtures/nar_race_entry_status/source_profiles/v2/**/*.html -text -diff"
)
EXPECTED_DEBA_TABLE_PATH = (
    "tests/fixtures/nar_race_entry_status/source_profiles/v2/"
    "baba_21__2025-01-01__race_06/deba_table.html"
)
EXPECTED_RACE_LIST_PATH = (
    "tests/fixtures/nar_race_entry_status/source_profiles/v2/"
    "baba_21__2025-01-01__race_06/race_list.html"
)
EXPECTED_MANIFEST_PATH = (
    "tests/fixtures/nar_race_entry_status/source_profiles/v2/"
    "baba_21__2025-01-01__race_06/manifest.json"
)
EXPECTED_DEDICATED_FIXTURE_TEST_PATH = (
    "tests/test_nar_race_entry_status_source_profile_v2_fixtures.py"
)
EXPECTED_CURRENT_PHASE_DOC_PATH = "docs/CURRENT_PHASE.md"
EXPECTED_LATEST_CODEX_REPORT_PATH = "docs/LATEST_CODEX_REPORT.md"

FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS = (
    "EXACT_DEBA_SHA256",
    "EXACT_DEBA_BYTE_LENGTH",
    "EXACT_RACELIST_SHA256",
    "EXACT_RACELIST_BYTE_LENGTH",
    "EXACT_TARGET",
    "DOCUMENT_ROLE_ORDER",
    "FIXTURE_SET_V2_RECOMPUTATION",
    "QUALIFICATION_V2_RECOMPUTATION",
    "MANIFEST_CANONICAL_SERIALIZATION",
    "MANIFEST_VALIDATION",
    "PUBLICATION_SAFETY_SAFE",
    "PROFILE_A_QUALIFIED",
    "PROFILE_B_QUALIFIED",
    "PROFILE_B_EXPLICIT_WITHDRAWAL_PRESENT",
    "CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET",
    "MARKET_ELIGIBILITY_UNSUPPORTED",
    "NO_NETWORK",
)

_WINDOWS_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")
_RAW_FIXTURE_ROOT = "tests/fixtures/nar_race_entry_status/source_profiles/v2/"


class PublicationPlanError(ValueError):
    """The prospective Phase57 publication plan is not the Phase60 authority."""


class PublicationRole(str, Enum):
    DEBA_TABLE_FIXTURE = "DEBA_TABLE_FIXTURE"
    RACE_LIST_FIXTURE = "RACE_LIST_FIXTURE"
    MANIFEST = "MANIFEST"
    DEDICATED_FIXTURE_TEST = "DEDICATED_FIXTURE_TEST"
    CURRENT_PHASE_DOC = "CURRENT_PHASE_DOC"
    LATEST_CODEX_REPORT = "LATEST_CODEX_REPORT"


class PublicationPathPolicy(str, Enum):
    CREATE_ONLY = "CREATE_ONLY"
    MODIFY_EXISTING = "MODIFY_EXISTING"
    VALIDATE_ONLY = "VALIDATE_ONLY"


_ROLE_ORDER = tuple(PublicationRole)
_ROLE_PATHS = {
    PublicationRole.DEBA_TABLE_FIXTURE: EXPECTED_DEBA_TABLE_PATH,
    PublicationRole.RACE_LIST_FIXTURE: EXPECTED_RACE_LIST_PATH,
    PublicationRole.MANIFEST: EXPECTED_MANIFEST_PATH,
    PublicationRole.DEDICATED_FIXTURE_TEST: EXPECTED_DEDICATED_FIXTURE_TEST_PATH,
    PublicationRole.CURRENT_PHASE_DOC: EXPECTED_CURRENT_PHASE_DOC_PATH,
    PublicationRole.LATEST_CODEX_REPORT: EXPECTED_LATEST_CODEX_REPORT_PATH,
}
_ROLE_POLICIES = {
    PublicationRole.DEBA_TABLE_FIXTURE: PublicationPathPolicy.CREATE_ONLY,
    PublicationRole.RACE_LIST_FIXTURE: PublicationPathPolicy.CREATE_ONLY,
    PublicationRole.MANIFEST: PublicationPathPolicy.CREATE_ONLY,
    PublicationRole.DEDICATED_FIXTURE_TEST: PublicationPathPolicy.CREATE_ONLY,
    PublicationRole.CURRENT_PHASE_DOC: PublicationPathPolicy.MODIFY_EXISTING,
    PublicationRole.LATEST_CODEX_REPORT: PublicationPathPolicy.MODIFY_EXISTING,
}


def _error(message: str) -> PublicationPlanError:
    return PublicationPlanError(message)


def _validate_repository_path(value: object) -> str:
    if type(value) is not str or not value:
        raise _error("publication path must be a non-empty exact str")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise _error("publication path must be valid UTF-8") from error
    if "\\" in value:
        raise _error("publication path must use forward slashes")
    if value.startswith("/") or _WINDOWS_DRIVE_PREFIX.match(value):
        raise _error("publication path must be repository-relative")
    if any(unicodedata.category(character) == "Cc" for character in value):
        raise _error("publication path contains a control character")
    components = value.split("/")
    if any(component in {"", ".", ".."} for component in components):
        raise _error("publication path is not canonical")
    return value


@dataclass(frozen=True, slots=True)
class PublicationPlanEntry:
    role: PublicationRole
    repository_path: str
    policy: PublicationPathPolicy

    def __post_init__(self) -> None:
        if type(self.role) is not PublicationRole:
            raise _error("publication role has the wrong type")
        if type(self.policy) is not PublicationPathPolicy:
            raise _error("publication path policy has the wrong type")
        object.__setattr__(self, "repository_path", _validate_repository_path(self.repository_path))


@dataclass(frozen=True, slots=True)
class Phase57PublicationPlan:
    authority_semantic: str
    provider: str
    baba_code: str
    race_date: str
    race_no: int
    entries: tuple[PublicationPlanEntry, ...]
    required_gitattributes_rule: str
    gitattributes_policy: PublicationPathPolicy

    def __post_init__(self) -> None:
        if self.authority_semantic != AUTHORITY_SEMANTIC:
            raise _error("publication-plan authority semantic is invalid")
        if (
            self.provider != "NAR"
            or self.baba_code != "21"
            or self.race_date != "2025-01-01"
            or type(self.race_no) is not int
            or self.race_no != 6
        ):
            raise _error("publication plan is not for the frozen Phase57 target")
        if type(self.entries) is not tuple or len(self.entries) != len(_ROLE_ORDER):
            raise _error("publication plan must contain exactly six entries")
        if any(type(entry) is not PublicationPlanEntry for entry in self.entries):
            raise _error("publication plan entries have the wrong type")
        if tuple(entry.role for entry in self.entries) != _ROLE_ORDER:
            raise _error("publication roles are missing, duplicated, or out of order")
        paths = tuple(entry.repository_path for entry in self.entries)
        if len(set(paths)) != len(paths):
            raise _error("publication plan contains duplicate paths")
        for entry in self.entries:
            if entry.repository_path != _ROLE_PATHS[entry.role]:
                raise _error(f"{entry.role.value} path is outside the closed authority")
            if entry.policy is not _ROLE_POLICIES[entry.role]:
                raise _error(f"{entry.role.value} policy is invalid")
        if not paths[0].startswith(_RAW_FIXTURE_ROOT) or not paths[1].startswith(_RAW_FIXTURE_ROOT):
            raise _error("raw fixture path is outside the approved v2 subtree")
        if self.required_gitattributes_rule != REQUIRED_GITATTRIBUTES_RULE:
            raise _error("binary-preservation rule is invalid")
        if self.gitattributes_policy is not PublicationPathPolicy.VALIDATE_ONLY:
            raise _error("future .gitattributes policy must be VALIDATE_ONLY")

    @property
    def future_live_paths(self) -> tuple[str, ...]:
        return tuple(entry.repository_path for entry in self.entries)

    @property
    def rollback_paths(self) -> tuple[str, ...]:
        return self.future_live_paths


def _validated_fixture_paths(fixture_set: object) -> tuple[str, str]:
    if type(fixture_set) is not FixtureSetV2:
        raise _error("fixture_set must be exact Phase56 FixtureSetV2")
    try:
        validate_nar_race_entry_status_fixture_set_v2(
            value=fixture_set,
            target=fixture_set.target,
            capture_summary=fixture_set.capture_summary,
        )
        payload = fixture_set.to_canonical_dict()
    except (SourceProfilePublicationContractError, AttributeError, TypeError) as error:
        raise _error("fixture_set is not valid Phase56 authority") from error
    if payload.get("provider") != "NAR" or payload.get("target") != {
        "baba_code": "21",
        "race_date": "2025-01-01",
        "race_no": 6,
    }:
        raise _error("fixture_set is not for the frozen Phase57 target")
    documents = payload.get("documents")
    if type(documents) is not list or len(documents) != 2:
        raise _error("fixture_set must contain exactly two Phase56 documents")
    expected_roles = ("deba_table", "race_list")
    paths: list[str] = []
    for document, role in zip(documents, expected_roles, strict=True):
        if type(document) is not dict or document.get("role") != role:
            raise _error("fixture_set document roles are invalid")
        paths.append(_validate_repository_path(document.get("fixture_relative_path")))
    result = (paths[0], paths[1])
    if result != (EXPECTED_DEBA_TABLE_PATH, EXPECTED_RACE_LIST_PATH):
        raise _error("Phase56 fixture paths do not match the approved Phase60 target")
    return result


def build_nar_race_entry_status_phase57_publication_plan(
    *, fixture_set: FixtureSetV2
) -> Phase57PublicationPlan:
    deba_path, race_list_path = _validated_fixture_paths(fixture_set)
    paths = {
        **_ROLE_PATHS,
        PublicationRole.DEBA_TABLE_FIXTURE: deba_path,
        PublicationRole.RACE_LIST_FIXTURE: race_list_path,
    }
    entries = tuple(
        PublicationPlanEntry(role=role, repository_path=paths[role], policy=_ROLE_POLICIES[role])
        for role in _ROLE_ORDER
    )
    return Phase57PublicationPlan(
        authority_semantic=AUTHORITY_SEMANTIC,
        provider="NAR",
        baba_code="21",
        race_date="2025-01-01",
        race_no=6,
        entries=entries,
        required_gitattributes_rule=REQUIRED_GITATTRIBUTES_RULE,
        gitattributes_policy=PublicationPathPolicy.VALIDATE_ONLY,
    )


def validate_nar_race_entry_status_phase57_publication_plan(
    *, value: Phase57PublicationPlan, fixture_set: FixtureSetV2
) -> Phase57PublicationPlan:
    if type(value) is not Phase57PublicationPlan:
        raise _error("publication-plan value has the wrong type")
    expected = build_nar_race_entry_status_phase57_publication_plan(fixture_set=fixture_set)
    if value != expected:
        raise _error("publication plan does not match deterministic Phase60 authority")
    return value


__all__ = (
    "AUTHORITY_SEMANTIC",
    "EXPECTED_CURRENT_PHASE_DOC_PATH",
    "EXPECTED_DEBA_TABLE_PATH",
    "EXPECTED_DEDICATED_FIXTURE_TEST_PATH",
    "EXPECTED_LATEST_CODEX_REPORT_PATH",
    "EXPECTED_MANIFEST_PATH",
    "EXPECTED_RACE_LIST_PATH",
    "FUTURE_OFFICIAL_FIXTURE_TEST_REQUIREMENTS",
    "Phase57PublicationPlan",
    "PublicationPathPolicy",
    "PublicationPlanEntry",
    "PublicationPlanError",
    "PublicationRole",
    "REQUIRED_GITATTRIBUTES_RULE",
    "build_nar_race_entry_status_phase57_publication_plan",
    "validate_nar_race_entry_status_phase57_publication_plan",
)
