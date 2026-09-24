"""Git-object-derived source bundle for controlled local timing execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path, PurePosixPath
import os
import re
import shutil
import subprocess
import tempfile

from scripts.simulation.nar_operational_timing_observability import _json_bytes, _read_json


_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_REPOSITORY = "garimapo/KeibaOS"


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    if result.returncode:
        raise ValueError("local Git object operation failed")
    return result.stdout


def _included(path: str) -> bool:
    return (path.startswith("scripts/") and path.endswith(".py")
            or path == "main.py" or path == "requirements.txt"
            or path.startswith("config/") or path.startswith("prompts/"))


@dataclass(frozen=True, slots=True)
class NARRuntimeSourceMember:
    path: str
    mode: str
    size: int
    sha256_hex: str

    def __post_init__(self) -> None:
        parts = PurePosixPath(self.path).parts
        if (type(self.path) is not str or not _included(self.path) or not parts
                or any(part in (".", "..") for part in parts) or self.path.startswith("/")
                or type(self.mode) is not str or self.mode not in ("100644", "100755")
                or type(self.size) is not int or self.size < 0
                or type(self.sha256_hex) is not str or re.fullmatch(r"[0-9a-f]{64}", self.sha256_hex) is None):
            raise ValueError("invalid sealed source member")


@dataclass(frozen=True, slots=True)
class NARRuntimeSourceBundle:
    commit_sha: str
    tree_sha: str
    members: tuple[NARRuntimeSourceMember, ...]
    repository_identity: str = _REPOSITORY
    schema_version: int = 1
    manifest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if (type(self.commit_sha) is not str or _HEX40.fullmatch(self.commit_sha) is None
                or type(self.tree_sha) is not str or _HEX40.fullmatch(self.tree_sha) is None
                or type(self.repository_identity) is not str or self.repository_identity != _REPOSITORY
                or type(self.schema_version) is not int or self.schema_version != 1
                or type(self.members) is not tuple or not self.members
                or any(type(x) is not NARRuntimeSourceMember for x in self.members)
                or tuple(sorted(self.members, key=lambda x: x.path)) != self.members
                or len({x.path for x in self.members}) != len(self.members)):
            raise ValueError("invalid sealed Git source manifest")
        object.__setattr__(self, "manifest_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def bundle_identity(self) -> str:
        return "nar-runtime-source-bundle-v1:" + self.manifest_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version, "repository_identity": self.repository_identity,
                "commit_sha": self.commit_sha, "tree_sha": self.tree_sha,
                "semantic": "CONTROLLED_SEALED_GIT_SOURCE_BUNDLE_V1",
                "members": [{"path": x.path, "mode": x.mode, "size": x.size,
                             "sha256": x.sha256_hex} for x in self.members]}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NARRuntimeSourceBundle:
        p = _read_json(value)
        members = tuple(NARRuntimeSourceMember(x["path"], x["mode"], x["size"], x["sha256"])
                        for x in p["members"])
        result = cls(p["commit_sha"], p["tree_sha"], members,
                     p["repository_identity"], p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("sealed source manifest is not canonical")
        return result


def _git_manifest(root: Path, commit_sha: str) -> tuple[NARRuntimeSourceBundle, dict[str, str]]:
    if type(commit_sha) is not str or _HEX40.fullmatch(commit_sha) is None:
        raise ValueError("exact lowercase Git commit is required")
    if Path(_git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve() != root:
        raise ValueError("Git repository root differs")
    remote = _git(root, "remote", "get-url", "origin").decode("utf-8").strip()
    if remote not in ("https://github.com/garimapo/KeibaOS.git",
                      "git@github.com:garimapo/KeibaOS.git"):
        raise ValueError("Git repository identity differs")
    if _git(root, "rev-parse", "--verify", f"{commit_sha}^{{commit}}").strip().decode("ascii") != commit_sha:
        raise ValueError("commit does not resolve exactly")
    tree_sha = _git(root, "rev-parse", f"{commit_sha}^{{tree}}").strip().decode("ascii")
    if _HEX40.fullmatch(tree_sha) is None:
        raise ValueError("invalid Git tree")
    blobs: dict[str, str] = {}
    members: list[NARRuntimeSourceMember] = []
    for item in _git(root, "ls-tree", "-r", "-z", "--full-tree", commit_sha).split(b"\0"):
        if not item:
            continue
        header, raw_path = item.split(b"\t", 1)
        path = raw_path.decode("utf-8", "strict")
        if not _included(path):
            continue
        mode, kind, blob_sha = header.decode("ascii").split(" ")
        if kind != "blob" or mode not in ("100644", "100755") or _HEX40.fullmatch(blob_sha) is None:
            raise ValueError("included Git member is not a regular blob")
        data = _git(root, "cat-file", "blob", blob_sha)
        members.append(NARRuntimeSourceMember(path, mode, len(data), sha256(data).hexdigest()))
        blobs[path] = blob_sha
    members.sort(key=lambda x: x.path)
    return NARRuntimeSourceBundle(commit_sha, tree_sha, tuple(members)), blobs


def verify_sealed_bundle(*, bundle: NARRuntimeSourceBundle, bundle_root: Path) -> None:
    root = bundle_root.resolve(strict=True)
    expected = {x.path for x in bundle.members}
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    if actual != expected:
        raise ValueError("sealed bundle member set differs")
    for member in bundle.members:
        path = root.joinpath(*PurePosixPath(member.path).parts)
        if path.is_symlink() or not path.is_file() or root not in path.resolve(strict=True).parents:
            raise ValueError("sealed member path escapes bundle")
        data = path.read_bytes()
        if len(data) != member.size or sha256(data).hexdigest() != member.sha256_hex:
            raise ValueError("sealed member bytes differ from Git object")


def verify_bundle_against_git_objects(*, repository_root: Path, bundle: NARRuntimeSourceBundle) -> None:
    expected, _ = _git_manifest(repository_root.resolve(strict=True), bundle.commit_sha)
    if expected != bundle:
        raise ValueError("sealed manifest differs from exact local Git object tree")


def materialize_sealed_git_source_bundle(
    *, repository_root: Path, commit_sha: str, destination_parent: Path,
) -> tuple[NARRuntimeSourceBundle, Path]:
    """Create exact object-derived bytes atomically outside the mutable worktree."""
    root = repository_root.resolve(strict=True)
    parent = destination_parent.resolve(strict=True)
    if root == parent or root in parent.parents or parent in root.parents:
        raise ValueError("bundle parent must be separate from developer worktree")
    bundle, blobs = _git_manifest(root, commit_sha)
    target = parent / ("nar-runtime-source-bundle-v1-" + bundle.manifest_sha256)
    if target.exists():
        verify_sealed_bundle(bundle=bundle, bundle_root=target)
        return bundle, target
    staging = Path(tempfile.mkdtemp(prefix="nar-source-staging-", dir=parent))
    try:
        for member in bundle.members:
            output = staging.joinpath(*PurePosixPath(member.path).parts)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(_git(root, "cat-file", "blob", blobs[member.path]))
        verify_sealed_bundle(bundle=bundle, bundle_root=staging)
        os.replace(staging, target)
        return bundle, target
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def require_sealed_module_origins(*, bundle: NARRuntimeSourceBundle, bundle_root: Path,
                                  scripts_namespace_locations: tuple[Path, ...],
                                  module_origins: tuple[Path, ...]) -> None:
    """Reject PEP 420 extra portions and critical-module shadowing."""
    root = bundle_root.resolve(strict=True)
    verify_sealed_bundle(bundle=bundle, bundle_root=root)
    if (type(scripts_namespace_locations) is not tuple
            or tuple(x.resolve(strict=True) for x in scripts_namespace_locations) != (root / "scripts",)
            or type(module_origins) is not tuple or not module_origins):
        raise ValueError("scripts namespace is not isolated to sealed bundle")
    allowed = {root.joinpath(*PurePosixPath(x.path).parts) for x in bundle.members if x.path.endswith(".py")}
    for origin in module_origins:
        if not isinstance(origin, Path) or origin.resolve(strict=True) not in allowed:
            raise ValueError("critical module origin is outside sealed manifest")
