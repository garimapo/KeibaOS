"""Deterministic no-network Profile-A source qualification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from html.parser import HTMLParser
import json
import re
from types import MappingProxyType
from typing import Mapping

from bs4 import BeautifulSoup
from bs4 import ParserRejectedMarkup
from bs4.element import Tag

from scripts.simulation import nar_race_entry_status_raw_capture as _raw_capture


PROFILE_A_SCHEMA_VERSION = 2
PROFILE_A_SEMANTIC = "ENTRY_LISTING_PRESENT"
_MAX_COUNT = 10_000
_HORSE_NUMBER = re.compile(r"[1-9][0-9]*\Z", flags=re.ASCII)
_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)


class NARRaceEntryStatusProfileAError(Exception):
    """Base error for invalid Profile-A authority or values."""


class NARRaceEntryStatusProfileAValidationError(NARRaceEntryStatusProfileAError):
    """Raised for programmer/type contract violations."""


class ProfileAOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class ProfileAPredicateIdentifier(StrEnum):
    ENTRY_TABLE_SCOPE = "ENTRY_TABLE_SCOPE"
    ORDINARY_HORSE_ROW_SHAPE = "ORDINARY_HORSE_ROW_SHAPE"
    SELECTED_NON14_LISTING = "SELECTED_NON14_LISTING"


_ORDER = tuple(ProfileAPredicateIdentifier)
_FIELDS = {
    ProfileAPredicateIdentifier.ENTRY_TABLE_SCOPE: frozenset({"entry_table_scope_count"}),
    ProfileAPredicateIdentifier.ORDINARY_HORSE_ROW_SHAPE: frozenset({"ordinary_row_count"}),
    ProfileAPredicateIdentifier.SELECTED_NON14_LISTING: frozenset(
        {"selected_non14_candidate_count", "selected_provider_horse_no"},
    ),
}


def _validation(message: str) -> NARRaceEntryStatusProfileAValidationError:
    return NARRaceEntryStatusProfileAValidationError(message)


def _canonical_bytes(payload: object) -> bytes:
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as error:
        raise _validation("Profile-A result is not canonically serializable") from error


def _target(value: object) -> _raw_capture.NARRaceEntryStatusRaceIdentity:
    if type(value) is not _raw_capture.NARRaceEntryStatusRaceIdentity:
        raise _validation("target must be exact NARRaceEntryStatusRaceIdentity")
    try:
        return _raw_capture.NARRaceEntryStatusRaceIdentity(
            baba_code=value.baba_code,
            race_date=value.race_date,
            race_no=value.race_no,
        )
    except (_raw_capture.NARRaceEntryStatusRawCaptureError, AttributeError, TypeError) as error:
        raise _validation("target identity is malformed") from error


class _StrictStructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in _VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return None

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_TAGS:
            return
        if not self.stack or self.stack[-1] != tag:
            raise ValueError("source tag structure is unsupported")
        self.stack.pop()

    def close(self) -> None:
        super().close()
        if self.stack:
            raise ValueError("source tag structure is unsupported")


def _validate_html_structure(source: str) -> None:
    parser = _StrictStructureParser()
    parser.feed(source)
    parser.close()


@dataclass(frozen=True, slots=True)
class _PredicateResult:
    identifier: ProfileAPredicateIdentifier
    outcome: ProfileAOutcome
    safe_fields: Mapping[str, object]

    def __post_init__(self) -> None:
        if type(self.identifier) is not ProfileAPredicateIdentifier:
            raise _validation("Profile-A predicate identifier has the wrong type")
        if type(self.outcome) is not ProfileAOutcome:
            raise _validation("Profile-A predicate outcome has the wrong type")
        if type(self.safe_fields) is not dict or frozenset(self.safe_fields) != _FIELDS[self.identifier]:
            raise _validation("Profile-A safe fields do not match the allowlist")
        values = dict(self.safe_fields)
        for name, value in values.items():
            if name == "selected_provider_horse_no":
                if value is not None and (type(value) is not int or value <= 0 or value == 14):
                    raise _validation("selected_provider_horse_no is invalid")
            elif type(value) is not int or not 0 <= value <= _MAX_COUNT:
                raise _validation(f"{name} must be a bounded nonnegative exact int")
        object.__setattr__(self, "safe_fields", MappingProxyType(values))

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "identifier": self.identifier.value,
            "outcome": self.outcome.value,
            "safe_fields": dict(self.safe_fields),
        }


@dataclass(frozen=True, slots=True)
class ProfileADiagnostics:
    target: _raw_capture.NARRaceEntryStatusRaceIdentity
    predicate_results: tuple[_PredicateResult, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", _target(self.target))
        if type(self.predicate_results) is not tuple or len(self.predicate_results) != 3:
            raise _validation("predicate_results must be the exact three-result tuple")
        if any(type(item) is not _PredicateResult for item in self.predicate_results):
            raise _validation("predicate_results contains an unexpected result type")
        if tuple(item.identifier for item in self.predicate_results) != _ORDER:
            raise _validation("predicate_results are outside the frozen order")

    @property
    def overall_result(self) -> str:
        return "QUALIFIED" if all(item.outcome is ProfileAOutcome.PASS for item in self.predicate_results) else "BLOCKED"

    @property
    def first_nonpass_predicate(self) -> ProfileAPredicateIdentifier | None:
        return next((item.identifier for item in self.predicate_results if item.outcome is not ProfileAOutcome.PASS), None)

    @property
    def terminal_reason(self) -> str:
        if self.first_nonpass_predicate is None:
            return "QUALIFIED"
        if any(item.outcome is ProfileAOutcome.UNSUPPORTED for item in self.predicate_results):
            return "UNSUPPORTED_INPUT"
        return "FIRST_NONPASS_PREDICATE"

    def to_canonical_dict(self) -> dict[str, object]:
        first = self.first_nonpass_predicate
        return {
            "schema_version": PROFILE_A_SCHEMA_VERSION,
            "profile": PROFILE_A_SEMANTIC,
            "overall_result": self.overall_result,
            "terminal_semantic": PROFILE_A_SEMANTIC if first is None else None,
            "target": {
                "baba_code": self.target.baba_code,
                "race_date": self.target.race_date.isoformat(),
                "race_no": self.target.race_no,
            },
            "predicate_results": [item.to_canonical_dict() for item in self.predicate_results],
            "first_nonpass_predicate": None if first is None else first.value,
            "terminal_reason": self.terminal_reason,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical_bytes(self.to_canonical_dict())


def _result(identifier: ProfileAPredicateIdentifier, outcome: ProfileAOutcome, **fields: object) -> _PredicateResult:
    return _PredicateResult(identifier, outcome, fields)


def _unsupported(target: _raw_capture.NARRaceEntryStatusRaceIdentity) -> ProfileADiagnostics:
    return ProfileADiagnostics(
        target,
        (
            _result(ProfileAPredicateIdentifier.ENTRY_TABLE_SCOPE, ProfileAOutcome.UNSUPPORTED, entry_table_scope_count=0),
            _result(ProfileAPredicateIdentifier.ORDINARY_HORSE_ROW_SHAPE, ProfileAOutcome.UNSUPPORTED, ordinary_row_count=0),
            _result(
                ProfileAPredicateIdentifier.SELECTED_NON14_LISTING,
                ProfileAOutcome.UNSUPPORTED,
                selected_non14_candidate_count=0,
                selected_provider_horse_no=None,
            ),
        ),
    )


def diagnose_nar_race_entry_status_profile_a(
    *,
    deba_table_bytes: bytes,
    target: _raw_capture.NARRaceEntryStatusRaceIdentity,
) -> ProfileADiagnostics:
    """Qualify the frozen ordinary non-14 DebaTable listing profile."""

    canonical_target = _target(target)
    if type(deba_table_bytes) is not bytes:
        raise _validation("deba_table_bytes must be exact bytes")
    try:
        source = deba_table_bytes.decode("utf-8", errors="strict")
        _validate_html_structure(source)
        document = BeautifulSoup(source, "html.parser")
    except (UnicodeDecodeError, ValueError, ParserRejectedMarkup):
        return _unsupported(canonical_target)

    tables: list[Tag] = []
    for card in document.select("article.raceCard"):
        if type(card) is not Tag:
            continue
        for table in card.select("section.cardTable table"):
            if type(table) is not Tag:
                continue
            if any(
                len(row.find_all("td", class_="horseNum", recursive=False)) == 1
                for row in table.find_all("tr")
                if type(row) is Tag
            ):
                tables.append(table)

    scope_outcome = ProfileAOutcome.PASS if len(tables) == 1 else (
        ProfileAOutcome.FAIL if not tables else ProfileAOutcome.AMBIGUOUS
    )
    scope = _result(
        ProfileAPredicateIdentifier.ENTRY_TABLE_SCOPE,
        scope_outcome,
        entry_table_scope_count=len(tables),
    )

    parsed_rows: list[int] = []
    shape_outcome = ProfileAOutcome.UNSUPPORTED
    row_count = 0
    if scope_outcome is ProfileAOutcome.PASS:
        candidate_rows = [
            row
            for row in tables[0].find_all("tr")
            if type(row) is Tag and row.find_all("td", class_="horseNum", recursive=False)
        ]
        row_count = len(candidate_rows)
        ambiguous = False
        unsupported = False
        for row in candidate_rows:
            cells = row.find_all("td", class_="horseNum", recursive=False)
            anchors = row.select("a.horseName[href]")
            if len(cells) != 1 or len(anchors) != 1:
                ambiguous = True
                continue
            href = anchors[0].get("href")
            text = "".join(cells[0].stripped_strings)
            if type(href) is not str or not href or _HORSE_NUMBER.fullmatch(text) is None:
                unsupported = True
                continue
            parsed_rows.append(int(text))
        if unsupported:
            shape_outcome = ProfileAOutcome.UNSUPPORTED
        elif ambiguous:
            shape_outcome = ProfileAOutcome.AMBIGUOUS
        elif not candidate_rows:
            shape_outcome = ProfileAOutcome.FAIL
        else:
            shape_outcome = ProfileAOutcome.PASS
    shape = _result(
        ProfileAPredicateIdentifier.ORDINARY_HORSE_ROW_SHAPE,
        shape_outcome,
        ordinary_row_count=row_count,
    )

    eligible = [number for number in parsed_rows if number != 14]
    if shape_outcome is not ProfileAOutcome.PASS:
        listing_outcome = ProfileAOutcome.UNSUPPORTED
        selected = None
    elif not eligible:
        listing_outcome = ProfileAOutcome.FAIL
        selected = None
    elif len(eligible) != len(set(eligible)):
        listing_outcome = ProfileAOutcome.AMBIGUOUS
        selected = None
    else:
        listing_outcome = ProfileAOutcome.PASS
        selected = min(eligible)
    listing = _result(
        ProfileAPredicateIdentifier.SELECTED_NON14_LISTING,
        listing_outcome,
        selected_non14_candidate_count=len(eligible),
        selected_provider_horse_no=selected,
    )
    return ProfileADiagnostics(canonical_target, (scope, shape, listing))


__all__ = (
    "ProfileADiagnostics",
    "ProfileAOutcome",
    "ProfileAPredicateIdentifier",
    "diagnose_nar_race_entry_status_profile_a",
)
