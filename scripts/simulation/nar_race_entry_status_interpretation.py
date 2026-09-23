"""Current-observation evidence for the one published NAR V3 race fixture.

The result is status evidence from the 2026 capture, not a historical snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from bs4 import BeautifulSoup, Tag

from scripts.simulation import nar_historical_input_source as _nar_identity
from scripts.simulation import nar_race_entry_status_replay_identity_binding as _identity
from scripts.simulation.nar_race_entry_status_raw_capture import NARRaceEntryStatusRaceIdentity
from scripts.simulation.nar_race_entry_status_replay_identity_binding import (
    NARRaceEntryStatusReplayEntryIdentityBinding,
    NARRaceEntryStatusReplayIdentityBinding,
)
from scripts.simulation.nar_race_entry_status_source_profile_fixture_consumer import (
    NARRaceEntryStatusSourceProfileFixtureBundleV3,
)


_RACE_ID = "nar:20250101:21:6"
_WITHDRAWAL = "出走取消"
_ACQUISITION_SEMANTICS = "CURRENT_ACQUISITION_CONCERNING_HISTORICAL_TARGET"
_HISTORICAL_BLOCK = "HISTORICAL_ENTRY_STATUS_AUTHORITY_BLOCKED"
_OBSERVED_WITHDRAWAL = "EXPLICIT_WITHDRAWAL_PRESENT"
_NO_WITHDRAWAL_EVIDENCE = "NO_EXPLICIT_WITHDRAWAL_EVIDENCE"

ERROR_CLASSIFICATIONS = frozenset({
    "UNSUPPORTED_BUNDLE", "UNSUPPORTED_BINDING", "TARGET_CONTRADICTION",
    "ENTRY_SET_CONTRADICTION", "STATUS_EVIDENCE_MISSING",
    "STATUS_EVIDENCE_AMBIGUOUS", "DEBA_RACELIST_CONTRADICTION",
    "PROFILE_B_CONTRADICTION", "HORSE_ASSOCIATION_CONTRADICTION",
    "UNSUPPORTED_STATUS_REPRESENTATION", "TEMPORAL_AUTHORITY_CONTRADICTION",
})


class NARRaceEntryStatusInterpretationError(ValueError):
    """A stable failure of the current-observation evidence boundary."""

    def __init__(self, classification: str, message: str) -> None:
        if classification not in ERROR_CLASSIFICATIONS:
            raise ValueError("unknown interpretation error classification")
        self.classification = classification
        super().__init__(f"{classification}: {message}")


def _failure(classification: str, message: str) -> NARRaceEntryStatusInterpretationError:
    return NARRaceEntryStatusInterpretationError(classification, message)


@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusEvidenceTimestamp:
    role: str
    capture_identity: str
    observed_at: str
    captured_at: str


@dataclass(frozen=True, slots=True)
class NARRaceEntryCurrentStatusEvidence:
    external_entry_id: str
    race_entry_id: int
    horse_no: int
    current_observation: str
    evidence_roles: tuple[str, str]


@dataclass(frozen=True, slots=True)
class NARRaceEntryStatusInterpretation:
    target: NARRaceEntryStatusRaceIdentity
    organization: str
    source_system: str
    external_race_id: str
    internal_race_id: int
    acquisition_semantics: str
    current_observation_authority: str
    historical_status_authority: str
    entry_statuses: tuple[NARRaceEntryCurrentStatusEvidence, ...]
    evidence_timestamps: tuple[NARRaceEntryStatusEvidenceTimestamp, NARRaceEntryStatusEvidenceTimestamp]


def _authentic_bundle(bundle: object) -> NARRaceEntryStatusSourceProfileFixtureBundleV3:
    try:
        return _identity._validate_bundle(bundle)
    except (_identity.NARRaceEntryStatusReplayIdentityBindingError, AttributeError, TypeError, ValueError) as error:
        raise _failure("UNSUPPORTED_BUNDLE", "the frozen Phase85 bundle is invalid") from error


def _binding_entries(
    bundle: NARRaceEntryStatusSourceProfileFixtureBundleV3,
    binding: object,
) -> tuple[NARRaceEntryStatusReplayEntryIdentityBinding, ...]:
    if type(binding) is not NARRaceEntryStatusReplayIdentityBinding:
        raise _failure("UNSUPPORTED_BINDING", "binding must have the exact Phase88 type")
    if type(binding.target) is not NARRaceEntryStatusRaceIdentity or binding.target != bundle.target:
        raise _failure("TARGET_CONTRADICTION", "bundle and binding targets differ")
    if (binding.organization, binding.source_system, binding.external_race_id) != (
        "NAR", "nar_official", _RACE_ID
    ) or type(binding.internal_race_id) is not int or binding.internal_race_id <= 0:
        raise _failure("UNSUPPORTED_BINDING", "binding race authority is invalid")
    entries = binding.entry_bindings
    if type(entries) is not tuple or len(entries) != 14 or any(
        type(item) is not NARRaceEntryStatusReplayEntryIdentityBinding for item in entries
    ):
        raise _failure("ENTRY_SET_CONTRADICTION", "binding must contain fourteen exact entry values")
    if tuple(item.horse_no for item in entries) != tuple(range(1, 15)):
        raise _failure("ENTRY_SET_CONTRADICTION", "binding horse numbers are incomplete or unordered")
    if any(
        type(item.horse_no) is not int
        or type(item.external_entry_id) is not str
        or item.external_entry_id != f"{_RACE_ID}:entry:{item.horse_no}"
        or type(item.external_horse_id) is not str
        or not item.external_horse_id.startswith("nar:horse:")
        or type(item.race_entry_id) is not int
        or item.race_entry_id <= 0
        for item in entries
    ) or len({item.race_entry_id for item in entries}) != 14:
        raise _failure("ENTRY_SET_CONTRADICTION", "entry identities are contradictory")
    try:
        source = _identity._extract_source_entries(bundle.deba_table_bytes, _RACE_ID)
    except _identity.NARRaceEntryStatusReplayIdentityBindingError as error:
        raise _failure("ENTRY_SET_CONTRADICTION", "source entry identities are invalid") from error
    if tuple((item.external_entry_id, item.external_horse_id, item.horse_no) for item in entries) != tuple(
        (item.external_entry_id, item.external_horse_id, item.horse_no) for item in source
    ):
        raise _failure("ENTRY_SET_CONTRADICTION", "binding entries differ from frozen source identities")
    return entries


def _direct_cells(row: Tag) -> list[Tag]:
    return [cell for cell in row.find_all("td", recursive=False) if type(cell) is Tag]


def _deba_current_changes(payload: bytes) -> frozenset[int]:
    """Inspect only the current td.info in each five-row target entry block."""
    try:
        document = BeautifulSoup(payload.decode("utf-8", errors="strict"), "html.parser")
        identity_rows = _nar_identity._horse_rows(document)
    except (UnicodeError, _nar_identity.NarHistoricalInputSourceError) as error:
        raise _failure("STATUS_EVIDENCE_MISSING", "target Deba entry table is unavailable") from error
    tables = {id(row.find_parent("table")): row.find_parent("table") for row in identity_rows}
    if len(tables) != 1:
        raise _failure("STATUS_EVIDENCE_AMBIGUOUS", "Deba entry table is ambiguous")
    table = next(iter(tables.values()))
    bodies = table.find_all("tbody", recursive=False)
    if len(bodies) != 1:
        raise _failure("STATUS_EVIDENCE_MISSING", "Deba entry table body is invalid")
    rows = bodies[0].find_all("tr", recursive=False)
    starts = []
    for index, row in enumerate(rows):
        horse_cells = [cell for cell in _direct_cells(row) if "horseNum" in cell.get("class", ())]
        if horse_cells:
            if len(horse_cells) != 1:
                raise _failure("STATUS_EVIDENCE_AMBIGUOUS", "horse-number row is ambiguous")
            token = horse_cells[0].get_text(strip=False)
            if re.fullmatch(r"[1-9][0-9]*", token, flags=re.ASCII) is None:
                raise _failure("HORSE_ASSOCIATION_CONTRADICTION", "horse number is noncanonical")
            starts.append((index, int(token)))
    if tuple(number for _, number in starts) != tuple(range(1, 15)) or len(identity_rows) != 14:
        raise _failure("HORSE_ASSOCIATION_CONTRADICTION", "Deba entry universe differs from binding")
    changed = set()
    for position, (start, number) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(rows)
        horse_cell = [cell for cell in _direct_cells(rows[start]) if "horseNum" in cell.get("class", ())][0]
        if end - start != 5 or horse_cell.get("rowspan") != "5":
            raise _failure("STATUS_EVIDENCE_MISSING", "current-status row position is unsupported")
        fields = [cell for cell in _direct_cells(rows[start + 4]) if "info" in cell.get("class", ())]
        if len(fields) != 1:
            raise _failure("STATUS_EVIDENCE_AMBIGUOUS", "current-status field cardinality is invalid")
        value = fields[0].get_text(" ", strip=True)
        if value == _WITHDRAWAL:
            changed.add(number)
        elif value:
            raise _failure("UNSUPPORTED_STATUS_REPRESENTATION", "unrecognized current Deba status")
    return frozenset(changed)


def _race_list_current_changes(payload: bytes) -> frozenset[int]:
    try:
        document = BeautifulSoup(payload.decode("utf-8", errors="strict"), "html.parser")
    except UnicodeError as error:
        raise _failure("STATUS_EVIDENCE_MISSING", "RaceList is not UTF-8") from error
    tables = document.select("table.changeInfo")
    if len(tables) != 1:
        raise _failure(
            "STATUS_EVIDENCE_MISSING" if not tables else "STATUS_EVIDENCE_AMBIGUOUS",
            "RaceList changeInfo table cardinality is invalid",
        )
    target = []
    for row in tables[0].select("tr.data"):
        cells = _direct_cells(row)
        if cells and cells[0].get_text(" ", strip=True) == "6R":
            target.append(cells)
    if len(target) != 1:
        raise _failure(
            "STATUS_EVIDENCE_MISSING" if not target else "STATUS_EVIDENCE_AMBIGUOUS",
            "target RaceList change row cardinality is invalid",
        )
    cells = target[0]
    if len(cells) != 6:
        raise _failure("STATUS_EVIDENCE_AMBIGUOUS", "target RaceList change row shape is invalid")
    horse_text = cells[1].get_text(" ", strip=True)
    if re.fullmatch(r"[1-9][0-9]*", horse_text, flags=re.ASCII) is None:
        raise _failure("HORSE_ASSOCIATION_CONTRADICTION", "RaceList horse number is noncanonical")
    number = int(horse_text)
    if number != 14:
        raise _failure("HORSE_ASSOCIATION_CONTRADICTION", "RaceList change row is not for horse 14")
    if cells[3].get_text(" ", strip=True) != _WITHDRAWAL:
        raise _failure("UNSUPPORTED_STATUS_REPRESENTATION", "RaceList change is not explicit withdrawal")
    return frozenset({number})


def _require_profile_b(bundle: NARRaceEntryStatusSourceProfileFixtureBundleV3) -> None:
    try:
        data = bundle.manifest.qualification.profile_b.to_canonical_dict()
        association = next(
            item for item in data["predicate_results"]
            if item["identifier"] == "HORSE_14_WITHDRAWAL_ASSOCIATION"
        )
        fields = association["safe_fields"]
        valid = (
            data["overall_result"] == "QUALIFIED"
            and data["terminal_semantic"] == "EXPLICIT_WITHDRAWAL_PRESENT"
            and association["outcome"] == "PASS"
            and fields["withdrawn_provider_horse_no"] == 14
            and fields["horse_14_withdrawal_count"] == 1
            and fields["withdrawal_label_match"] is True
        )
    except (AttributeError, KeyError, StopIteration, TypeError):
        valid = False
    if not valid:
        raise _failure("PROFILE_B_CONTRADICTION", "frozen Profile-B withdrawal authority is contradictory")


def _timestamps(bundle: NARRaceEntryStatusSourceProfileFixtureBundleV3) -> tuple[
    NARRaceEntryStatusEvidenceTimestamp, NARRaceEntryStatusEvidenceTimestamp
]:
    try:
        summary = bundle.manifest.fixture_set.capture_summary
        values = (summary.deba_table, summary.race_list)
        dates = []
        for item in values:
            requested = datetime.fromisoformat(item.requested_at.replace("Z", "+00:00"))
            observed = datetime.fromisoformat(item.observed_at.replace("Z", "+00:00"))
            captured = datetime.fromisoformat(item.captured_at.replace("Z", "+00:00"))
            if not (requested <= observed <= captured and observed.date() > bundle.target.race_date):
                raise ValueError("observation is not post-target or correctly ordered")
            dates.append((requested, observed, captured))
        if dates[0][2] > dates[1][0]:
            raise ValueError("document acquisition order is contradictory")
        return tuple(
            NARRaceEntryStatusEvidenceTimestamp(item.document_role, item.capture_identity, item.observed_at, item.captured_at)
            for item in values
        )  # type: ignore[return-value]
    except (AttributeError, TypeError, ValueError) as error:
        raise _failure("TEMPORAL_AUTHORITY_CONTRADICTION", "manifest acquisition times are contradictory") from error


def interpret_nar_race_entry_status_v3(
    *,
    bundle: NARRaceEntryStatusSourceProfileFixtureBundleV3,
    binding: NARRaceEntryStatusReplayIdentityBinding,
) -> NARRaceEntryStatusInterpretation:
    """Interpret exact current-observation evidence without historical promotion."""
    bundle = _authentic_bundle(bundle)
    entries = _binding_entries(bundle, binding)
    _require_profile_b(bundle)
    deba = _deba_current_changes(bundle.deba_table_bytes)
    race_list = _race_list_current_changes(bundle.race_list_bytes)
    if deba != race_list:
        raise _failure("DEBA_RACELIST_CONTRADICTION", "current withdrawal evidence disagrees")
    if deba != frozenset({14}):
        raise _failure("PROFILE_B_CONTRADICTION", "parsed status contradicts frozen Profile-B")
    if not deba <= {item.horse_no for item in entries}:
        raise _failure("HORSE_ASSOCIATION_CONTRADICTION", "withdrawn horse is not bound")
    timestamps = _timestamps(bundle)
    statuses = tuple(
        NARRaceEntryCurrentStatusEvidence(
            item.external_entry_id,
            item.race_entry_id,
            item.horse_no,
            _OBSERVED_WITHDRAWAL if item.horse_no in deba else _NO_WITHDRAWAL_EVIDENCE,
            ("deba_table", "race_list"),
        )
        for item in entries
    )
    return NARRaceEntryStatusInterpretation(
        bundle.target, binding.organization, binding.source_system,
        binding.external_race_id, binding.internal_race_id,
        _ACQUISITION_SEMANTICS, "SUPPORTED", _HISTORICAL_BLOCK,
        statuses, timestamps,
    )
