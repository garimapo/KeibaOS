"""Local archive-scoped process lock; not persistent session consumption."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import threading

from scripts.simulation.nar_operational_timing_observability import _json_bytes


_HELD: set[str] = set()
_GUARD = threading.Lock()


def _not_reparse(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("archive scope contains a link")
    info = path.stat()
    if getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError("archive scope contains a reparse point")


class NAROperationalTimingCampaignLock:
    """Held from bootstrap through campaign; one local machine/archive composition."""

    __slots__ = ("archive_path", "scope_identity", "lock_path", "_handle", "_owner_pid")

    def __init__(self, *, archive_path: Path) -> None:
        if not isinstance(archive_path, Path) or not archive_path.is_absolute():
            raise ValueError("absolute archive path required")
        parent = archive_path.parent.resolve(strict=True)
        _not_reparse(parent)
        if archive_path.exists():
            _not_reparse(archive_path)
            if not archive_path.is_file() or archive_path.stat().st_nlink != 1:
                raise ValueError("archive must be one regular non-linked file")
        name = os.path.normcase(archive_path.name)
        stat = parent.stat()
        material = {"schema_version": 1, "archive_basename": name}
        if stat.st_ino:
            material.update(parent_device=stat.st_dev, parent_file_id=stat.st_ino)
        else:
            material["parent_path"] = os.path.normcase(str(parent))
        digest = sha256(_json_bytes(material)).hexdigest()
        self.scope_identity = "nar-operational-timing-lock-scope-v1:" + digest
        self.archive_path = parent / archive_path.name
        self.lock_path = parent / (".nar-operational-timing-" + digest + ".lock")
        self._handle = None
        self._owner_pid = None

    @property
    def held_by_current_process(self) -> bool:
        return self._handle is not None and self._owner_pid == os.getpid()

    def acquire(self) -> None:
        if self._handle is not None:
            raise RuntimeError("campaign lock is already acquired")
        with _GUARD:
            if self.scope_identity in _HELD:
                raise RuntimeError("another local campaign holds this archive scope")
            _HELD.add(self.scope_identity)
        handle = None
        try:
            try:
                handle = open(self.lock_path, "x+b")
            except FileExistsError:
                _not_reparse(self.lock_path)
                handle = open(self.lock_path, "r+b")
            if handle.seek(0, os.SEEK_END) == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._handle = handle
            self._owner_pid = os.getpid()
        except BaseException:
            if handle is not None:
                handle.close()
            with _GUARD:
                _HELD.discard(self.scope_identity)
            raise

    def release(self) -> None:
        if self._handle is None:
            return
        try:
            self._handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None
            self._owner_pid = None
            with _GUARD:
                _HELD.discard(self.scope_identity)

    def __enter__(self) -> NAROperationalTimingCampaignLock:
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()
