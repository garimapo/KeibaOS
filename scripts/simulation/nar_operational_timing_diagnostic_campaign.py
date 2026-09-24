"""Immutable, outcome-free authority for a no-network timing rehearsal."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from pathlib import PurePosixPath, Path
import re
import subprocess

from scripts.simulation.nar_operational_timing_observability import (
    NARHTTPTransportKind, NARTimingCorrelation, _json_bytes, _read_json,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingStageV2, _REQUIRED_TRANSPORT,
)


_SHA = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SESSION = re.compile(r"nar-operational-timing-session-v2:[0-9a-f]{64}\Z")
_CONFIG = re.compile(r"nar-operational-timing-config-v2:[0-9a-f]{64}\Z")
_CLAIM = re.compile(r"nar-operational-timing-campaign-execution-v1:[0-9a-f]{64}\Z")
_PLAN = re.compile(r"nar-operational-timing-diagnostic-plan-v1:[0-9a-f]{64}\Z")
_FIXTURE = re.compile(r"nar-operational-timing-diagnostic-fixture-bundle-v1:[0-9a-f]{64}\Z")
_PLANNABLE_OPERATION_STAGES = frozenset({
    NAROperationalTimingStageV2.BOOTSTRAP_HOME_ACQUISITION,
    NAROperationalTimingStageV2.MONTHLY_ROOT_ACQUISITION,
    NAROperationalTimingStageV2.LOCATOR_SCRIPT_ACQUISITION,
    NAROperationalTimingStageV2.MONTHLY_SCHEDULE_ACQUISITION,
    NAROperationalTimingStageV2.RACE_LIST_ACQUISITION,
    NAROperationalTimingStageV2.OFFICIAL_RESPONSE_ACQUISITION,
    NAROperationalTimingStageV2.MARKET_ODDS_RAW_ACQUISITION,
    NAROperationalTimingStageV2.RAW_CAPTURE_PERSISTENCE,
    NAROperationalTimingStageV2.NORMALIZATION,
    NAROperationalTimingStageV2.SOURCE_RECORD_CONSTRUCTION,
    NAROperationalTimingStageV2.SNAPSHOT_CONSTRUCTION,
    NAROperationalTimingStageV2.SNAPSHOT_PERSISTENCE,
    NAROperationalTimingStageV2.SNAPSHOT_EXACT_RELOAD_CONFIRMATION,
    NAROperationalTimingStageV2.SNAPSHOT_ADAPTER,
    NAROperationalTimingStageV2.PREDICTION_PIPELINE,
    NAROperationalTimingStageV2.ALLOCATION,
    NAROperationalTimingStageV2.BET_PLAN_CONSTRUCTION,
    NAROperationalTimingStageV2.BET_PLAN_PERSISTENCE,
})


def _git(repository_root: Path, *args: str) -> bytes:
    result = subprocess.run(("git", "-C", str(repository_root), *args),
                            capture_output=True, check=False)
    if result.returncode:
        raise ValueError("exact local fixture Git object is unavailable")
    return result.stdout


def _require_repository(repository_root: Path, repository_identity: str, commit_sha: str) -> None:
    if repository_identity != "garimapo/KeibaOS" or not isinstance(repository_root, Path):
        raise ValueError("reviewed fixture repository identity required")
    root = repository_root.resolve(strict=True)
    if Path(_git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve() != root:
        raise ValueError("fixture repository root differs")
    if _git(root, "remote", "get-url", "origin").decode("utf-8").strip() not in (
            "https://github.com/garimapo/KeibaOS.git", "git@github.com:garimapo/KeibaOS.git"):
        raise ValueError("fixture repository origin differs")
    if _git(root, "rev-parse", "--verify", f"{commit_sha}^{{commit}}").decode("ascii").strip() != commit_sha:
        raise ValueError("fixture commit does not resolve exactly")


def _member_path(value: str) -> str:
    if (type(value) is not str or not value or "\\" in value or "\x00" in value
            or PurePosixPath(value).is_absolute() or any(part in (".", "..", "") for part in value.split("/"))):
        raise ValueError("fixture member requires a safe repository-relative path")
    return value


@dataclass(frozen=True, slots=True)
class NARDiagnosticFixtureMemberV1:
    path: str
    blob_sha: str
    byte_length: int
    sha256_hex: str

    def __post_init__(self) -> None:
        _member_path(self.path)
        if (type(self.blob_sha) is not str or not _SHA.fullmatch(self.blob_sha)
                or type(self.byte_length) is not int or self.byte_length < 0
                or type(self.sha256_hex) is not str or not _DIGEST.fullmatch(self.sha256_hex)):
            raise ValueError("invalid Git fixture member")

    def payload(self) -> dict[str, object]:
        return {"path": self.path, "blob_sha": self.blob_sha,
                "byte_length": self.byte_length, "sha256": self.sha256_hex}


@dataclass(frozen=True, slots=True)
class NAROperationalTimingDiagnosticFixtureBundleV1:
    repository_identity: str
    commit_sha: str
    tree_sha: str
    members: tuple[NARDiagnosticFixtureMemberV1, ...]
    schema_version: int = 1
    bundle_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if (type(self.repository_identity) is not str or not self.repository_identity
                or type(self.commit_sha) is not str or not _SHA.fullmatch(self.commit_sha)
                or type(self.tree_sha) is not str or not _SHA.fullmatch(self.tree_sha)
                or type(self.schema_version) is not int or self.schema_version != 1
                or type(self.members) is not tuple or not self.members
                or any(type(x) is not NARDiagnosticFixtureMemberV1 for x in self.members)
                or tuple(sorted(x.path for x in self.members)) != tuple(x.path for x in self.members)
                or len({x.path for x in self.members}) != len(self.members)):
            raise ValueError("fixture bundle is not an exact ordered Git manifest")
        object.__setattr__(self, "bundle_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def bundle_identity(self) -> str:
        return "nar-operational-timing-diagnostic-fixture-bundle-v1:" + self.bundle_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "repository_identity": self.repository_identity,
                "commit_sha": self.commit_sha, "tree_sha": self.tree_sha,
                "members": [x.payload() for x in self.members]}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingDiagnosticFixtureBundleV1:
        p = _read_json(value)
        if set(p) != {"schema_version", "repository_identity", "commit_sha", "tree_sha", "members"}:
            raise ValueError("fixture payload fields differ")
        result = cls(p["repository_identity"], p["commit_sha"], p["tree_sha"],
                     tuple(NARDiagnosticFixtureMemberV1(x["path"], x["blob_sha"], x["byte_length"], x["sha256"])
                           for x in p["members"]), p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("fixture payload is not canonical")
        return result

    @classmethod
    def from_git(cls, *, repository_root: Path, repository_identity: str,
                 commit_sha: str, paths: tuple[str, ...]) -> NAROperationalTimingDiagnosticFixtureBundleV1:
        if type(commit_sha) is not str or not _SHA.fullmatch(commit_sha):
            raise ValueError("exact local Git commit required")
        _require_repository(repository_root, repository_identity, commit_sha)
        tree_sha = _git(repository_root, "rev-parse", f"{commit_sha}^{{tree}}").decode("ascii").strip()
        members = []
        for path in sorted(paths):
            _member_path(path)
            entry = _git(repository_root, "ls-tree", commit_sha, "--", path).decode("utf-8").strip()
            match = re.fullmatch(r"100644 blob ([0-9a-f]{40})\t(.+)", entry)
            if match is None or match.group(2) != path:
                raise ValueError("fixture is absent, nonregular, or ambiguous in Git tree")
            blob = match.group(1)
            data = _git(repository_root, "cat-file", "blob", blob)
            members.append(NARDiagnosticFixtureMemberV1(path, blob, len(data), sha256(data).hexdigest()))
        result = cls(repository_identity, commit_sha, tree_sha, tuple(members))
        result.read_verified_bytes(repository_root=repository_root)
        return result

    def read_verified_bytes(self, *, repository_root: Path) -> dict[str, bytes]:
        _require_repository(repository_root, self.repository_identity, self.commit_sha)
        if _git(repository_root, "rev-parse", f"{self.commit_sha}^{{tree}}").decode("ascii").strip() != self.tree_sha:
            raise ValueError("fixture commit/tree ancestry changed")
        material = {}
        for member in self.members:
            entry = _git(repository_root, "ls-tree", self.commit_sha, "--", member.path).decode("utf-8").strip()
            if entry != f"100644 blob {member.blob_sha}\t{member.path}":
                raise ValueError("fixture path/blob ancestry changed")
            data = _git(repository_root, "cat-file", "blob", member.blob_sha)
            if len(data) != member.byte_length or sha256(data).hexdigest() != member.sha256_hex:
                raise ValueError("fixture Git-object bytes differ from manifest")
            material[member.path] = data
        return material


class NARDiagnosticContinuationV1(StrEnum):
    INDEPENDENT = "INDEPENDENT"
    EXECUTE_AFTER_PREDECESSORS_TERMINATE_REGARDLESS_OUTCOME = "EXECUTE_AFTER_PREDECESSORS_TERMINATE_REGARDLESS_OUTCOME"
    REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS = "REQUIRES_ALL_PREDECESSOR_SUCCESSFUL_OUTPUTS"


class NARDiagnosticCompositionV1(StrEnum):
    INCLUSIVE_COMPOSITE = "INCLUSIVE_COMPOSITE"
    EXCLUSIVE_LEAF = "EXCLUSIVE_LEAF"
    SEQUENTIAL_SIBLING = "SEQUENTIAL_SIBLING"
    DEPENDENCY_ONLY = "DEPENDENCY_ONLY"


@dataclass(frozen=True, slots=True)
class NARDiagnosticPlanNodeSpecV1:
    key: str
    stage: NAROperationalTimingStageV2
    sequence: int
    scope: str
    correlation: NARTimingCorrelation
    predecessors: tuple[str, ...]
    continuation: NARDiagnosticContinuationV1
    composition: NARDiagnosticCompositionV1
    fixture_path: str | None = None
    transport_kind: NARHTTPTransportKind | None = None
    expected_url_sha256: str | None = None
    terminal_on_non_success: bool = False

    def __post_init__(self) -> None:
        if (type(self.key) is not str or not re.fullmatch(r"[a-z][a-z0-9_-]{0,79}", self.key)
                or type(self.stage) is not NAROperationalTimingStageV2
                or self.stage not in _PLANNABLE_OPERATION_STAGES
                or type(self.sequence) is not int or self.sequence < 0
                or type(self.scope) is not str or not self.scope
                or type(self.correlation) is not NARTimingCorrelation
                or type(self.predecessors) is not tuple or len(set(self.predecessors)) != len(self.predecessors)
                or type(self.continuation) is not NARDiagnosticContinuationV1
                or type(self.composition) is not NARDiagnosticCompositionV1
                or type(self.terminal_on_non_success) is not bool):
            raise ValueError("invalid diagnostic operation node")
        if self.fixture_path is not None:
            _member_path(self.fixture_path)
        required = _REQUIRED_TRANSPORT.get(self.stage)
        if required is None:
            if self.transport_kind is not None or self.expected_url_sha256 is not None:
                raise ValueError("non-HTTP diagnostic node has HTTP policy")
        elif self.transport_kind is not required or type(self.expected_url_sha256) is not str or not _DIGEST.fullmatch(self.expected_url_sha256):
            raise ValueError("HTTP diagnostic node needs exact URL/transport policy")
        expected_scope = ("request-url-sha256:" + self.expected_url_sha256 if required is not None
                          else "correlation:" + self.correlation.correlation_identity)
        if self.scope != expected_scope:
            raise ValueError("diagnostic scope must derive from attempt-visible URL or correlation")
        if self.continuation is NARDiagnosticContinuationV1.INDEPENDENT and self.predecessors:
            raise ValueError("independent node cannot name predecessors")
        if self.continuation is not NARDiagnosticContinuationV1.INDEPENDENT and not self.predecessors:
            raise ValueError("dependent node requires predecessors")

    def payload(self) -> dict[str, object]:
        return {"key": self.key, "stage": self.stage.value, "sequence": self.sequence,
                "scope": self.scope, "correlation": self.correlation.payload(),
                "predecessors": list(self.predecessors), "continuation": self.continuation.value,
                "composition": self.composition.value, "fixture_path": self.fixture_path,
                "transport_kind": self.transport_kind.value if self.transport_kind else None,
                "expected_url_sha256": self.expected_url_sha256,
                "terminal_on_non_success": self.terminal_on_non_success,
                "expected_http_policy": "DIRECT_REQUEST_ENVIRONMENT_V1" if self.transport_kind else None}


@dataclass(frozen=True, slots=True)
class NAROperationalTimingDiagnosticCampaignPlanV1:
    repository_identity: str
    commit_sha: str
    configuration_identity: str
    session_identity: str
    fixture_bundle_identity: str
    nodes: tuple[NARDiagnosticPlanNodeSpecV1, ...]
    scope: str
    schema_version: int = 1
    plan_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if (type(self.repository_identity) is not str or not self.repository_identity
                or type(self.commit_sha) is not str or not _SHA.fullmatch(self.commit_sha)
                or type(self.configuration_identity) is not str or not _CONFIG.fullmatch(self.configuration_identity)
                or type(self.session_identity) is not str or not _SESSION.fullmatch(self.session_identity)
                or type(self.fixture_bundle_identity) is not str or not _FIXTURE.fullmatch(self.fixture_bundle_identity)
                or type(self.scope) is not str or not self.scope
                or type(self.schema_version) is not int or self.schema_version != 1
                or type(self.nodes) is not tuple or not self.nodes
                or any(type(x) is not NARDiagnosticPlanNodeSpecV1 for x in self.nodes)
                or tuple(x.sequence for x in self.nodes) != tuple(range(len(self.nodes)))
                or len({x.key for x in self.nodes}) != len(self.nodes)):
            raise ValueError("diagnostic plan must predeclare a fixed ordered population")
        earlier: set[str] = set()
        terminal_branches: set[str] = set()
        for node in self.nodes:
            if any(parent not in earlier for parent in node.predecessors):
                raise ValueError("diagnostic DAG requires earlier predecessor nodes")
            if (node.continuation is NARDiagnosticContinuationV1.EXECUTE_AFTER_PREDECESSORS_TERMINATE_REGARDLESS_OUTCOME
                    and any(parent in terminal_branches for parent in node.predecessors)):
                raise ValueError("terminal branch cannot continue after predecessor failure")
            earlier.add(node.key)
            if node.terminal_on_non_success:
                terminal_branches.add(node.key)
        object.__setattr__(self, "plan_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def plan_identity(self) -> str:
        return "nar-operational-timing-diagnostic-plan-v1:" + self.plan_sha256

    def node_identity(self, key: str) -> str:
        node = next(x for x in self.nodes if x.key == key)
        return "nar-operational-timing-diagnostic-node-v1:" + sha256(
            _json_bytes({"plan_identity": self.plan_identity, "node": node.payload()})).hexdigest()

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "repository_identity": self.repository_identity,
                "commit_sha": self.commit_sha, "configuration_identity": self.configuration_identity,
                "session_identity": self.session_identity, "fixture_bundle_identity": self.fixture_bundle_identity,
                "scope": self.scope, "mode": "DIAGNOSTIC_ONLY", "stopping_rule": "FIXED_PLAN_AND_SESSION_WINDOW_V1",
                "maximum_attempt_count": len(self.nodes), "nodes": [x.payload() for x in self.nodes]}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingDiagnosticCampaignPlanV1:
        p = _read_json(value)
        if set(p) != {"schema_version", "repository_identity", "commit_sha", "configuration_identity",
                      "session_identity", "fixture_bundle_identity", "scope", "mode", "stopping_rule",
                      "maximum_attempt_count", "nodes"} or p["mode"] != "DIAGNOSTIC_ONLY" or p["stopping_rule"] != "FIXED_PLAN_AND_SESSION_WINDOW_V1":
            raise ValueError("diagnostic plan payload is invalid")
        nodes = []
        for x in p["nodes"]:
            if set(x) != {"key", "stage", "sequence", "scope", "correlation", "predecessors", "continuation",
                          "composition", "fixture_path", "transport_kind", "expected_url_sha256",
                          "terminal_on_non_success", "expected_http_policy"}:
                raise ValueError("diagnostic node payload differs")
            kind = NARHTTPTransportKind(x["transport_kind"]) if x["transport_kind"] is not None else None
            nodes.append(NARDiagnosticPlanNodeSpecV1(x["key"], NAROperationalTimingStageV2(x["stage"]),
                         x["sequence"], x["scope"], NARTimingCorrelation.from_payload(x["correlation"]),
                         tuple(x["predecessors"]), NARDiagnosticContinuationV1(x["continuation"]),
                         NARDiagnosticCompositionV1(x["composition"]), x["fixture_path"], kind,
                         x["expected_url_sha256"], x["terminal_on_non_success"]))
        result = cls(p["repository_identity"], p["commit_sha"], p["configuration_identity"],
                     p["session_identity"], p["fixture_bundle_identity"], tuple(nodes), p["scope"], p["schema_version"])
        if p["maximum_attempt_count"] != len(nodes) or result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("diagnostic plan content is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class NAROperationalTimingDiagnosticExecutionDeclarationV1:
    plan_identity: str
    claim_identity: str
    configuration_identity: str
    session_identity: str
    fixture_bundle_identity: str
    schema_version: int = 1
    declaration_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if (type(self.plan_identity) is not str or not _PLAN.fullmatch(self.plan_identity)
                or type(self.claim_identity) is not str or not _CLAIM.fullmatch(self.claim_identity)
                or type(self.configuration_identity) is not str or not _CONFIG.fullmatch(self.configuration_identity)
                or type(self.session_identity) is not str or not _SESSION.fullmatch(self.session_identity)
                or type(self.fixture_bundle_identity) is not str or not _FIXTURE.fullmatch(self.fixture_bundle_identity)
                or type(self.schema_version) is not int or self.schema_version != 1):
            raise ValueError("diagnostic declaration ancestry is invalid")
        object.__setattr__(self, "declaration_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def declaration_identity(self) -> str:
        return "nar-operational-timing-diagnostic-execution-v1:" + self.declaration_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "plan_identity": self.plan_identity,
                "claim_identity": self.claim_identity, "configuration_identity": self.configuration_identity,
                "session_identity": self.session_identity, "fixture_bundle_identity": self.fixture_bundle_identity,
                "mode": "DIAGNOSTIC_ONLY"}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NAROperationalTimingDiagnosticExecutionDeclarationV1:
        p = _read_json(value)
        if set(p) != {"schema_version", "plan_identity", "claim_identity", "configuration_identity",
                      "session_identity", "fixture_bundle_identity", "mode"} or p["mode"] != "DIAGNOSTIC_ONLY":
            raise ValueError("diagnostic declaration payload differs")
        result = cls(p["plan_identity"], p["claim_identity"], p["configuration_identity"],
                     p["session_identity"], p["fixture_bundle_identity"], p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("diagnostic declaration payload is not canonical")
        return result
