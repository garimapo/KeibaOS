from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import inspect
from unittest.mock import Mock, patch

import pytest

import scripts.simulation as simulation_package
import scripts.simulation.jra_race_historical_snapshot_persistence as _module
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_snapshots import (
    HistoricalExternalEntryIdentity,
    HistoricalExternalRaceIdentity,
    HistoricalInputProvenance,
    HistoricalInputSnapshot,
    HistoricalInputSnapshotIdentity,
    HistoricalRaceEntrySnapshot,
    HistoricalRaceSnapshot,
    HistoricalSourceIdentity,
)
from scripts.simulation.jra_race_historical_replay import (
    JRARaceHistoricalReplayResult,
    JRARaceHistoricalReplayUnavailableError,
    JRARaceHistoricalReplayUnsupportedError,
    JRARaceHistoricalReplayValidationError,
)
from scripts.simulation.jra_race_historical_snapshot_persistence import (
    JRAPersistedHistoricalSnapshotReference,
    JRARaceHistoricalSnapshotPersistenceError,
    JRARaceHistoricalSnapshotPersistenceUnavailableError,
    JRARaceHistoricalSnapshotPersistenceUnsupportedError,
    JRARaceHistoricalSnapshotPersistenceValidationError,
    persist_jra_race_historical_snapshot,
)
from scripts.simulation.jra_race_replay_seed import (
    JRARaceReplaySeed,
    JRARaceReplaySeedEntry,
    build_jra_race_replay_seed,
)
from scripts.simulation.repositories.errors import (
    RepositoryConflictError,
    RepositoryDataIntegrityError,
    RepositoryValidationError,
)


UTC = timezone.utc
RACE_ID = "jra:race:2025:05:01:01:01"
CARD_URL = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105%2FAB"
CAPTURED = datetime(2025, 1, 5, 2, 0, tzinfo=UTC)
CUTOFF = datetime(2025, 1, 5, 3, 0, tzinfo=UTC)
START = datetime(2025, 1, 5, 6, 0, tzinfo=UTC)


def _seed(*, dataset_id: str = "dataset-jra-replay") -> JRARaceReplaySeed:
    return build_jra_race_replay_seed(
        dataset_id=dataset_id,
        external_race_id=RACE_ID,
        internal_race_id=77,
        target_race_selection_capture_id="jra-capture-v4:" + "1" * 64,
        target_race_card_capture_id="jra-capture-v3:" + "2" * 64,
        target_race_card_response_sha256="3" * 64,
        canonical_target_race_card_url=CARD_URL,
        captured_at=CAPTURED,
        information_cutoff=CUTOFF,
        entries=(
            JRARaceReplaySeedEntry(
                entry_order=0,
                external_entry_id=f"{RACE_ID}:entry:1",
                external_horse_id="jra:horse:1234567890",
                horse_no=1,
                internal_race_entry_id=101,
            ),
        ),
    )


def _snapshot(*, seed: JRARaceReplaySeed, source_url: str = CARD_URL) -> HistoricalInputSnapshot:
    source = HistoricalSourceIdentity("JRA", "jra_official", RACE_ID, source_url)
    identity = HistoricalInputSnapshotIdentity(seed.dataset_id, source, seed.captured_at)
    external_race = HistoricalExternalRaceIdentity("JRA", "jra_official", RACE_ID)
    entry = HistoricalRaceEntrySnapshot(
        101,
        HistoricalExternalEntryIdentity(
            external_race,
            f"{RACE_ID}:entry:1",
            "jra:horse:1234567890",
        ),
        1,
        "騎手",
        Decimal("2.5"),
        0,
    )
    race = HistoricalRaceSnapshot(
        date(2025, 1, 5),
        START,
        "東京",
        1600,
        "芝",
        "良",
        "テストレース",
        "1勝",
        "晴",
    )

    def evidence(role: str, digit: str) -> tuple[HistoricalInputEvidenceReference, ...]:
        return (
            HistoricalInputEvidenceReference(
                role,
                "https://www.jra.go.jp/evidence",
                digit * 64,
                None,
                CAPTURED,
            ),
        )

    provenance = (
        HistoricalInputProvenance("track", "track", "jra", "track", None, evidence("track", "1")),
        HistoricalInputProvenance("entry", "entry/101", "jra", "entry", 101, evidence("entry", "2")),
        HistoricalInputProvenance("odds", "odds/101", "jra", "odds", 101, evidence("odds_win", "3")),
        HistoricalInputProvenance("jockey", "jockey/101", "jra", "jockey", 101, evidence("jockey", "4")),
        HistoricalInputProvenance(
            "past_race",
            "past_race/101/none",
            "jra",
            "absence",
            101,
            evidence("past_race_absence_query", "5"),
        ),
    )
    return HistoricalInputSnapshot(
        identity,
        seed.internal_race_id,
        seed.information_cutoff,
        race,
        (entry,),
        (),
        provenance,
    )


class _Persistence:
    def __init__(self, *, reloaded: object) -> None:
        self.reloaded = reloaded
        self.saved: list[HistoricalInputSnapshot] = []
        self.loaded: list[HistoricalInputSnapshotIdentity] = []
        self.save_error: BaseException | None = None
        self.load_error: BaseException | None = None

    def save_snapshot(self, *, snapshot: HistoricalInputSnapshot) -> None:
        self.saved.append(snapshot)
        if self.save_error is not None:
            raise self.save_error

    def load_snapshot_by_identity(
        self,
        *,
        identity: HistoricalInputSnapshotIdentity,
    ) -> HistoricalInputSnapshot | None:
        self.loaded.append(identity)
        if self.load_error is not None:
            raise self.load_error
        return self.reloaded  # type: ignore[return-value]


def _providers(*, seed: JRARaceReplaySeed) -> dict[str, object]:
    return {
        "seed_provider": Mock(return_value=seed),
        "target_race_selection_capture_provider": Mock(),
        "target_race_card_capture_by_id_provider": Mock(),
        "horse_history_response_provider": Mock(),
        "race_result_response_provider": Mock(),
        "final_win_odds_response_provider": Mock(),
    }


def _invoke(
    *,
    seed: JRARaceReplaySeed,
    persistence: object,
    providers: dict[str, object] | None = None,
) -> JRAPersistedHistoricalSnapshotReference:
    values = _providers(seed=seed) if providers is None else providers
    return persist_jra_race_historical_snapshot(
        seed_id=seed.seed_id,
        snapshot_persistence=persistence,  # type: ignore[arg-type]
        **values,  # type: ignore[arg-type]
    )


def test_exact_public_surface_signature_errors_and_reference_contract() -> None:
    assert _module.__all__ == (
        "JRARaceHistoricalSnapshotPersistenceError",
        "JRARaceHistoricalSnapshotPersistenceValidationError",
        "JRARaceHistoricalSnapshotPersistenceUnavailableError",
        "JRARaceHistoricalSnapshotPersistenceUnsupportedError",
        "JRAPersistedHistoricalSnapshotReference",
        "persist_jra_race_historical_snapshot",
    )
    assert issubclass(JRARaceHistoricalSnapshotPersistenceError, ValueError)
    for error_type in (
        JRARaceHistoricalSnapshotPersistenceValidationError,
        JRARaceHistoricalSnapshotPersistenceUnavailableError,
        JRARaceHistoricalSnapshotPersistenceUnsupportedError,
    ):
        assert error_type.__bases__ == (JRARaceHistoricalSnapshotPersistenceError,)
    signature = inspect.signature(persist_jra_race_historical_snapshot)
    assert tuple(signature.parameters) == (
        "seed_id",
        "seed_provider",
        "target_race_selection_capture_provider",
        "target_race_card_capture_by_id_provider",
        "horse_history_response_provider",
        "race_result_response_provider",
        "final_win_odds_response_provider",
        "snapshot_persistence",
    )
    assert all(item.kind is inspect.Parameter.KEYWORD_ONLY for item in signature.parameters.values())
    assert tuple(field.name for field in fields(JRAPersistedHistoricalSnapshotReference)) == (
        "seed_id",
        "snapshot_identity",
        "content_sha256",
    )
    seed = _seed()
    reference = JRAPersistedHistoricalSnapshotReference(
        seed.seed_id,
        _snapshot(seed=seed).identity,
        "a" * 64,
    )
    with pytest.raises((FrozenInstanceError, AttributeError)):
        reference.content_sha256 = "b" * 64  # type: ignore[misc]
    assert not hasattr(reference, "__dict__")
    assert not hasattr(simulation_package, "JRAPersistedHistoricalSnapshotReference")


def test_reference_validation() -> None:
    seed = _seed()
    identity = _snapshot(seed=seed).identity
    for values in (
        ("invalid", identity, "a" * 64),
        (1, identity, "a" * 64),
        (seed.seed_id, object(), "a" * 64),
        (seed.seed_id, identity, "A" * 64),
        (seed.seed_id, identity, "a" * 63),
        (seed.seed_id, identity, 1),
    ):
        with pytest.raises(JRARaceHistoricalSnapshotPersistenceValidationError):
            JRAPersistedHistoricalSnapshotReference(*values)  # type: ignore[arg-type]


def test_validation_precedes_every_collaborator_call() -> None:
    seed = _seed()
    valid = _providers(seed=seed)
    collaborators = tuple(valid.values())
    persistence = _Persistence(reloaded=_snapshot(seed=seed))
    with pytest.raises(JRARaceHistoricalSnapshotPersistenceValidationError):
        persist_jra_race_historical_snapshot(
            seed_id="invalid",
            snapshot_persistence=persistence,
            **valid,  # type: ignore[arg-type]
        )
    assert all(item.call_count == 0 for item in collaborators)
    assert persistence.saved == [] and persistence.loaded == []

    for name in tuple(valid):
        providers = _providers(seed=seed)
        all_mocks = tuple(providers.values())
        providers[name] = object()
        persistence = _Persistence(reloaded=_snapshot(seed=seed))
        with pytest.raises(JRARaceHistoricalSnapshotPersistenceValidationError):
            _invoke(seed=seed, persistence=persistence, providers=providers)
        assert all(item.call_count == 0 for item in all_mocks)
        assert persistence.saved == [] and persistence.loaded == []

    for persistence in (object(), type("Bad", (), {"save_snapshot": None, "load_snapshot_by_identity": None})()):
        providers = _providers(seed=seed)
        with pytest.raises(JRARaceHistoricalSnapshotPersistenceValidationError):
            _invoke(seed=seed, persistence=persistence, providers=providers)
        assert all(item.call_count == 0 for item in providers.values())


def test_success_calls_seed_replay_save_and_exact_reload_once_with_identical_objects() -> None:
    seed = _seed()
    snapshot = _snapshot(seed=seed)
    result = JRARaceHistoricalReplayResult(seed, snapshot)
    providers = _providers(seed=seed)
    persistence = _Persistence(reloaded=snapshot)
    with patch.object(_module, "_build_replay", return_value=result) as replay:
        reference = _invoke(seed=seed, persistence=persistence, providers=providers)

    providers["seed_provider"].assert_called_once_with(seed_id=seed.seed_id)  # type: ignore[union-attr]
    replay.assert_called_once_with(
        seed=seed,
        target_race_selection_capture_provider=providers["target_race_selection_capture_provider"],
        target_race_card_capture_by_id_provider=providers["target_race_card_capture_by_id_provider"],
        horse_history_response_provider=providers["horse_history_response_provider"],
        race_result_response_provider=providers["race_result_response_provider"],
        final_win_odds_response_provider=providers["final_win_odds_response_provider"],
    )
    assert persistence.saved == [snapshot]
    assert persistence.loaded == [snapshot.identity]
    assert reference == JRAPersistedHistoricalSnapshotReference(
        seed.seed_id,
        snapshot.identity,
        snapshot.content_sha256,
    )


def test_seed_absence_wrong_type_and_wrong_id_fail_before_replay() -> None:
    seed = _seed()
    snapshot = _snapshot(seed=seed)
    for returned, expected in (
        (None, JRARaceHistoricalSnapshotPersistenceUnavailableError),
        (object(), JRARaceHistoricalSnapshotPersistenceValidationError),
        (_seed(dataset_id="other"), JRARaceHistoricalSnapshotPersistenceValidationError),
    ):
        providers = _providers(seed=seed)
        providers["seed_provider"] = Mock(return_value=returned)
        with patch.object(_module, "_build_replay") as replay, pytest.raises(expected):
            _invoke(seed=seed, persistence=_Persistence(reloaded=snapshot), providers=providers)
        replay.assert_not_called()


@pytest.mark.parametrize(
    ("source_error", "target_error"),
    (
        (JRARaceHistoricalReplayValidationError("invalid"), JRARaceHistoricalSnapshotPersistenceValidationError),
        (JRARaceHistoricalReplayUnavailableError("missing"), JRARaceHistoricalSnapshotPersistenceUnavailableError),
        (JRARaceHistoricalReplayUnsupportedError("unsupported"), JRARaceHistoricalSnapshotPersistenceUnsupportedError),
    ),
)
def test_c4d_public_errors_are_translated(source_error: Exception, target_error: type[Exception]) -> None:
    seed = _seed()
    persistence = _Persistence(reloaded=_snapshot(seed=seed))
    with patch.object(_module, "_build_replay", side_effect=source_error), pytest.raises(target_error):
        _invoke(seed=seed, persistence=persistence)
    assert persistence.saved == [] and persistence.loaded == []


def test_provider_and_repository_integrity_errors_propagate_unchanged() -> None:
    seed = _seed()
    snapshot = _snapshot(seed=seed)
    integrity = RepositoryDataIntegrityError("corrupt provider")
    with patch.object(_module, "_build_replay", side_effect=integrity), pytest.raises(
        RepositoryDataIntegrityError
    ) as caught:
        _invoke(seed=seed, persistence=_Persistence(reloaded=snapshot))
    assert caught.value is integrity

    result = JRARaceHistoricalReplayResult(seed, snapshot)
    for error in (
        RepositoryValidationError("invalid repository"),
        RepositoryConflictError("conflict"),
        RepositoryDataIntegrityError("corrupt repository"),
    ):
        persistence = _Persistence(reloaded=snapshot)
        persistence.save_error = error
        with patch.object(_module, "_build_replay", return_value=result), pytest.raises(type(error)) as caught:
            _invoke(seed=seed, persistence=persistence)
        assert caught.value is error
        assert persistence.loaded == []


def _forged_result(*, seed: object, snapshot: object) -> JRARaceHistoricalReplayResult:
    result = object.__new__(JRARaceHistoricalReplayResult)
    object.__setattr__(result, "seed", seed)
    object.__setattr__(result, "snapshot", snapshot)
    return result


def test_wrong_replay_result_seed_or_snapshot_fails_before_save() -> None:
    seed = _seed()
    snapshot = _snapshot(seed=seed)
    other_equal_seed = _seed()
    cases = (
        object(),
        JRARaceHistoricalReplayResult(other_equal_seed, snapshot),
        _forged_result(seed=seed, snapshot=object()),
    )
    for result in cases:
        persistence = _Persistence(reloaded=snapshot)
        with patch.object(_module, "_build_replay", return_value=result), pytest.raises(
            JRARaceHistoricalSnapshotPersistenceValidationError
        ):
            _invoke(seed=seed, persistence=persistence)
        assert persistence.saved == [] and persistence.loaded == []


def test_exact_reload_absence_wrong_type_and_mismatches_fail_closed() -> None:
    seed = _seed()
    snapshot = _snapshot(seed=seed)
    result = JRARaceHistoricalReplayResult(seed, snapshot)
    different_identity = replace(
        snapshot.identity,
        captured_at=snapshot.identity.captured_at + timedelta(seconds=1),
    )
    identity_mismatch = replace(snapshot, identity=different_identity)
    source_url_mismatch = _snapshot(seed=seed, source_url=CARD_URL.replace("%2FAB", "%2FAC"))
    digest_mismatch = replace(snapshot)
    object.__setattr__(digest_mismatch, "content_sha256", "0" * 64)

    for reloaded, expected in (
        (None, JRARaceHistoricalSnapshotPersistenceUnavailableError),
        (object(), JRARaceHistoricalSnapshotPersistenceValidationError),
        (identity_mismatch, JRARaceHistoricalSnapshotPersistenceValidationError),
        (source_url_mismatch, JRARaceHistoricalSnapshotPersistenceValidationError),
        (digest_mismatch, JRARaceHistoricalSnapshotPersistenceValidationError),
    ):
        persistence = _Persistence(reloaded=reloaded)
        with patch.object(_module, "_build_replay", return_value=result), pytest.raises(expected):
            _invoke(seed=seed, persistence=persistence)
        assert persistence.saved == [snapshot]
        assert persistence.loaded == [snapshot.identity]

    corruption = RepositoryDataIntegrityError("corrupt reload")
    persistence = _Persistence(reloaded=snapshot)
    persistence.load_error = corruption
    with patch.object(_module, "_build_replay", return_value=result), pytest.raises(
        RepositoryDataIntegrityError
    ) as caught:
        _invoke(seed=seed, persistence=persistence)
    assert caught.value is corruption


def test_idempotent_retry_returns_the_same_reference_after_prior_save() -> None:
    seed = _seed()
    snapshot = _snapshot(seed=seed)
    result = JRARaceHistoricalReplayResult(seed, snapshot)
    persistence = _Persistence(reloaded=snapshot)
    with patch.object(_module, "_build_replay", return_value=result) as replay:
        first = _invoke(seed=seed, persistence=persistence)
        second = _invoke(seed=seed, persistence=persistence)
    assert first == second
    assert persistence.saved == [snapshot, snapshot]
    assert persistence.loaded == [snapshot.identity, snapshot.identity]
    assert replay.call_count == 2


def test_retry_after_save_completed_but_first_exact_reload_was_unavailable() -> None:
    seed = _seed()
    snapshot = _snapshot(seed=seed)
    result = JRARaceHistoricalReplayResult(seed, snapshot)

    class FirstReloadUnavailable(_Persistence):
        def load_snapshot_by_identity(
            self,
            *,
            identity: HistoricalInputSnapshotIdentity,
        ) -> HistoricalInputSnapshot | None:
            self.loaded.append(identity)
            return None if len(self.loaded) == 1 else snapshot

    persistence = FirstReloadUnavailable(reloaded=snapshot)
    with patch.object(_module, "_build_replay", return_value=result):
        with pytest.raises(JRARaceHistoricalSnapshotPersistenceUnavailableError):
            _invoke(seed=seed, persistence=persistence)
        reference = _invoke(seed=seed, persistence=persistence)
    assert persistence.saved == [snapshot, snapshot]
    assert persistence.loaded == [snapshot.identity, snapshot.identity]
    assert reference.content_sha256 == snapshot.content_sha256


def test_static_ownership_has_no_forbidden_dependencies_or_broad_catch() -> None:
    source = inspect.getsource(_module)
    tree = ast.parse(source)
    forbidden = (
        "sqlite3",
        "requests",
        "httpx",
        "urllib",
        "pathlib",
        "subprocess",
        "random",
        "datetime.now",
        "datetime.today",
        "prediction",
        "settlement",
        "betting",
        "load_latest_snapshot",
        "materialize",
    )
    assert all(value not in source for value in forbidden)
    assert not any(
        isinstance(node, ast.ExceptHandler)
        and (
            node.type is None
            or isinstance(node.type, ast.Name)
            and node.type.id in {"Exception", "BaseException"}
        )
        for node in ast.walk(tree)
    )
