"""Pure deterministic parser for captured NAR market-odds source pages."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import datetime as _datetime, timezone as _timezone
from decimal import Decimal as _Decimal, InvalidOperation as _InvalidOperation
from enum import StrEnum as _StrEnum
import hashlib as _hashlib
import json as _json
import re as _re

from bs4 import BeautifulSoup as _BeautifulSoup
from bs4 import ParserRejectedMarkup as _ParserRejectedMarkup
from bs4.element import Comment as _Comment, NavigableString as _NavigableString, Tag as _Tag

from scripts.simulation.nar_market_odds_capture import (
    NARMarketOddsCaptureError as _NARMarketOddsCaptureError,
    NARMarketOddsPageKind,
    NARMarketOddsRaceIdentity,
    NARMarketOddsResponseCapture,
    build_nar_market_odds_request_identity as _build_nar_market_odds_request_identity,
)


class NARMarketOddsSourceState(_StrEnum):
    OPEN = "open"
    FINAL = "final"


class NARMarketOddsSourceCompleteness(_StrEnum):
    UNVERIFIED = "unverified"


class NARMarketOddsSourceQuoteKind(_StrEnum):
    EXACT = "exact"
    RANGE = "range"


class NARMarketOddsSourceParseError(Exception):
    """Base error for the pure NAR market-odds source parser."""


class NARMarketOddsSourceParseValidationError(NARMarketOddsSourceParseError):
    """Raised for malformed or forged Phase32 capture input."""


class NARMarketOddsSourceParseUnsupportedError(NARMarketOddsSourceParseError):
    """Raised for a source state or structural profile outside parser v1."""


class NARMarketOddsSourceParseDataError(NARMarketOddsSourceParseError):
    """Raised for contradictory data in an authoritative quote container."""


class NARMarketOddsSourceParseNumericError(NARMarketOddsSourceParseDataError):
    """Raised for a malformed or invalid source odds value."""


_PARSER_NAME = "nar-market-odds-source-parser"
_PARSER_VERSION = "v1"
_EVIDENCE_PREFIX = "nar-market-odds-source-evidence-v1:"
_REQUEST_PREFIX = "nar-market-odds-request-v1:"
_CAPTURE_PREFIX = "nar-market-odds-capture-v1:"
_ASCII_WHITESPACE = " \t\r\n\f\v"
_ASCII_WHITESPACE_RUN = _re.compile(r"[ \t\r\n\f\v]+")
_INLINE_DISPLAY_NONE = _re.compile(
    r"(?:^|;)[ \t\r\n\f\v]*display[ \t\r\n\f\v]*:[ \t\r\n\f\v]*"
    r"none[ \t\r\n\f\v]*(?:![ \t\r\n\f\v]*important[ \t\r\n\f\v]*)?(?=;|$)",
    _re.IGNORECASE,
)
_INLINE_VISIBILITY_HIDDEN = _re.compile(
    r"(?:^|;)[ \t\r\n\f\v]*visibility[ \t\r\n\f\v]*:[ \t\r\n\f\v]*"
    r"hidden[ \t\r\n\f\v]*(?:![ \t\r\n\f\v]*important[ \t\r\n\f\v]*)?(?=;|$)",
    _re.IGNORECASE,
)
_POSITIVE_TOKEN = _re.compile(r"[1-9][0-9]*\Z")
_DECIMAL_TOKEN = _re.compile(r"[1-9][0-9]*\.[0-9]+\Z")
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_DISPLAY_TIME = r"(?:[01][0-9]|2[0-3]):[0-5][0-9]"
_PAGE_TITLES = {
    NARMarketOddsPageKind.ODDS_TAN_FUKU: "単勝・複勝　オッズ",
    NARMarketOddsPageKind.ODDS_UM_LEN_FUKU: "馬連複　オッズ",
    NARMarketOddsPageKind.ODDS_WIDE: "ワイド　オッズ",
    NARMarketOddsPageKind.ODDS_3_LEN_FUKU: "三連複　オッズ",
}
_PAGE_ARITIES = {
    NARMarketOddsPageKind.ODDS_TAN_FUKU: 1,
    NARMarketOddsPageKind.ODDS_UM_LEN_FUKU: 2,
    NARMarketOddsPageKind.ODDS_WIDE: 2,
    NARMarketOddsPageKind.ODDS_3_LEN_FUKU: 3,
}
_CAPTURE_FIELDS = (
    "request_identity",
    "effective_url",
    "response_body",
    "charset",
    "requested_at",
    "observed_at",
    "captured_at",
    "http_status",
    "content_type",
    "content_encoding",
    "http_date",
    "etag",
    "last_modified",
    "content_length",
    "schema_version",
    "response_sha256",
    "byte_length",
    "capture_id",
)


def _validation(message: str) -> NARMarketOddsSourceParseValidationError:
    return NARMarketOddsSourceParseValidationError(message)


def _unsupported(message: str) -> NARMarketOddsSourceParseUnsupportedError:
    return NARMarketOddsSourceParseUnsupportedError(message)


def _data_error(message: str) -> NARMarketOddsSourceParseDataError:
    return NARMarketOddsSourceParseDataError(message)


def _numeric_error(message: str) -> NARMarketOddsSourceParseNumericError:
    return NARMarketOddsSourceParseNumericError(message)


def _canonical_json_bytes(payload: object) -> bytes:
    return _json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _utc_datetime(value: object, name: str) -> _datetime:
    if type(value) is not _datetime:
        raise _validation(f"{name} must be exact datetime")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise _validation(f"{name} must be timezone-aware")
        return value.astimezone(_timezone.utc)
    except NARMarketOddsSourceParseValidationError:
        raise
    except (OverflowError, TypeError, ValueError) as error:
        raise _validation(f"{name} cannot be converted to UTC") from error


def _datetime_text(value: _datetime) -> str:
    return value.astimezone(_timezone.utc).isoformat(timespec="microseconds")


def _canonical_decimal_text(value: _Decimal) -> str:
    sign, digits, exponent = value.as_tuple()
    if sign or not value.is_finite() or value <= 0 or type(exponent) is not int:
        raise _numeric_error("odds must be a finite positive Decimal")
    raw_digits = "".join(str(digit) for digit in digits) or "0"
    if exponent >= 0:
        text = raw_digits + ("0" * exponent)
    else:
        point = len(raw_digits) + exponent
        if point <= 0:
            text = "0." + ("0" * -point) + raw_digits
        else:
            text = raw_digits[:point] + "." + raw_digits[point:]
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _selection(value: object) -> tuple[int, ...]:
    if type(value) is not tuple or not 1 <= len(value) <= 3:
        raise _data_error("selection must be an exact tuple with arity one to three")
    if any(type(item) is not int or item <= 0 for item in value):
        raise _data_error("selection values must be exact positive ints")
    if tuple(sorted(value)) != value or len(set(value)) != len(value):
        raise _data_error("selection must be strictly ascending and distinct")
    return value


def _decimal(value: object, name: str) -> _Decimal:
    if type(value) is not _Decimal or not value.is_finite() or value <= 0:
        raise _numeric_error(f"{name} must be an exact finite positive Decimal")
    return value


@_dataclass(frozen=True, slots=True)
class NARMarketOddsExactQuote:
    selection: tuple[int, ...]
    exact_odds: _Decimal
    quote_kind: NARMarketOddsSourceQuoteKind = _field(
        init=False,
        default=NARMarketOddsSourceQuoteKind.EXACT,
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "selection", _selection(self.selection))
        object.__setattr__(self, "exact_odds", _decimal(self.exact_odds, "exact_odds"))


@_dataclass(frozen=True, slots=True)
class NARMarketOddsRangeQuote:
    selection: tuple[int, ...]
    lower_odds: _Decimal
    upper_odds: _Decimal
    quote_kind: NARMarketOddsSourceQuoteKind = _field(
        init=False,
        default=NARMarketOddsSourceQuoteKind.RANGE,
    )

    def __post_init__(self) -> None:
        selection = _selection(self.selection)
        lower = _decimal(self.lower_odds, "lower_odds")
        upper = _decimal(self.upper_odds, "upper_odds")
        if lower > upper:
            raise _numeric_error("lower_odds must not exceed upper_odds")
        object.__setattr__(self, "selection", selection)
        object.__setattr__(self, "lower_odds", lower)
        object.__setattr__(self, "upper_odds", upper)


NARMarketOddsSourceQuote = NARMarketOddsExactQuote | NARMarketOddsRangeQuote


def _quote_payload(quote: NARMarketOddsSourceQuote) -> dict[str, object]:
    if type(quote) is NARMarketOddsExactQuote:
        return {
            "exact_odds": _canonical_decimal_text(quote.exact_odds),
            "quote_kind": quote.quote_kind.value,
            "selection": list(quote.selection),
        }
    if type(quote) is NARMarketOddsRangeQuote:
        return {
            "lower_odds": _canonical_decimal_text(quote.lower_odds),
            "quote_kind": quote.quote_kind.value,
            "selection": list(quote.selection),
            "upper_odds": _canonical_decimal_text(quote.upper_odds),
        }
    raise _data_error("quotes must contain exact approved quote types")


@_dataclass(frozen=True, slots=True)
class NARMarketOddsSourceEvidence:
    page_kind: NARMarketOddsPageKind
    race_identity: NARMarketOddsRaceIdentity
    request_identity: str
    request_identity_sha256: str
    canonical_request_url: str
    capture_id: str
    response_sha256: str
    response_byte_length: int
    requested_at: _datetime
    observed_at: _datetime
    captured_at: _datetime
    source_state: NARMarketOddsSourceState
    provider_display_as_of_text: str | None
    source_completeness: NARMarketOddsSourceCompleteness
    provider_horse_numbers: tuple[int, ...] | None
    quotes: tuple[NARMarketOddsSourceQuote, ...]
    schema_version: int = _field(init=False, default=1)
    organization: str = _field(init=False, default="NAR")
    source_system: str = _field(init=False, default="keiba.go.jp")
    parser_name: str = _field(init=False, default=_PARSER_NAME)
    parser_version: str = _field(init=False, default=_PARSER_VERSION)
    evidence_content_sha256: str = _field(init=False)
    evidence_id: str = _field(init=False)

    def __post_init__(self) -> None:
        if type(self.page_kind) is not NARMarketOddsPageKind:
            raise _validation("page_kind must be exact NARMarketOddsPageKind")
        if type(self.race_identity) is not NARMarketOddsRaceIdentity:
            raise _validation("race_identity must be exact NARMarketOddsRaceIdentity")
        try:
            race = NARMarketOddsRaceIdentity(
                baba_code=self.race_identity.baba_code,
                race_date=self.race_identity.race_date,
                race_no=self.race_identity.race_no,
            )
        except (AttributeError, _NARMarketOddsCaptureError) as error:
            raise _validation("race_identity is invalid") from error
        try:
            expected_request = _build_nar_market_odds_request_identity(
                page_kind=self.page_kind,
                baba_code=race.baba_code,
                race_date=race.race_date,
                race_no=race.race_no,
            )
        except _NARMarketOddsCaptureError as error:
            raise _validation("evidence request provenance is invalid") from error
        if (
            type(self.request_identity_sha256) is not str
            or _SHA256.fullmatch(self.request_identity_sha256) is None
            or self.request_identity_sha256 != expected_request.request_identity_sha256
            or type(self.request_identity) is not str
            or self.request_identity != _REQUEST_PREFIX + self.request_identity_sha256
            or self.request_identity != expected_request.request_identity
            or type(self.canonical_request_url) is not str
            or self.canonical_request_url != expected_request.canonical_request_url
        ):
            raise _validation("evidence request provenance is contradictory")
        if (
            type(self.capture_id) is not str
            or not self.capture_id.startswith(_CAPTURE_PREFIX)
            or _SHA256.fullmatch(self.capture_id[len(_CAPTURE_PREFIX) :]) is None
            or type(self.response_sha256) is not str
            or _SHA256.fullmatch(self.response_sha256) is None
        ):
            raise _validation("evidence capture provenance is invalid")
        if type(self.response_byte_length) is not int or self.response_byte_length <= 0:
            raise _validation("response_byte_length must be an exact positive int")
        requested = _utc_datetime(self.requested_at, "requested_at")
        observed = _utc_datetime(self.observed_at, "observed_at")
        captured = _utc_datetime(self.captured_at, "captured_at")
        if not requested <= observed <= captured:
            raise _validation("capture timestamps are out of order")
        if type(self.source_state) is not NARMarketOddsSourceState:
            raise _validation("source_state must be exact NARMarketOddsSourceState")
        if self.source_state is NARMarketOddsSourceState.OPEN:
            if type(self.provider_display_as_of_text) is not str or _re.fullmatch(
                rf"{_DISPLAY_TIME} 現在",
                self.provider_display_as_of_text,
            ) is None:
                raise _validation("OPEN evidence requires exact provider display text")
        elif self.provider_display_as_of_text is not None:
            raise _validation("FINAL evidence must not carry provider display text")
        if self.source_completeness is not NARMarketOddsSourceCompleteness.UNVERIFIED:
            raise _validation("source_completeness must be UNVERIFIED")
        if self.provider_horse_numbers is not None:
            raise _validation("provider_horse_numbers must be None in parser v1")
        if type(self.quotes) is not tuple or not self.quotes:
            raise _data_error("quotes must be a non-empty exact tuple")
        arity = _PAGE_ARITIES[self.page_kind]
        expected_type = (
            NARMarketOddsRangeQuote
            if self.page_kind is NARMarketOddsPageKind.ODDS_WIDE
            else NARMarketOddsExactQuote
        )
        if any(type(quote) is not expected_type or len(quote.selection) != arity for quote in self.quotes):
            raise _data_error("quote type or selection arity disagrees with page kind")
        selections = tuple(quote.selection for quote in self.quotes)
        if selections != tuple(sorted(selections)) or len(set(selections)) != len(selections):
            raise _data_error("quotes must be strictly ordered with unique selections")
        object.__setattr__(self, "race_identity", race)
        object.__setattr__(self, "requested_at", requested)
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "captured_at", captured)
        payload = {
            "baba_code": race.baba_code,
            "canonical_request_url": self.canonical_request_url,
            "capture_id": self.capture_id,
            "captured_at_utc": _datetime_text(captured),
            "observed_at_utc": _datetime_text(observed),
            "organization": "NAR",
            "page_kind": self.page_kind.value,
            "parser_name": _PARSER_NAME,
            "parser_version": _PARSER_VERSION,
            "provider_display_as_of_text": self.provider_display_as_of_text,
            "provider_horse_numbers": None,
            "quotes": [_quote_payload(quote) for quote in self.quotes],
            "race_date": race.race_date.isoformat(),
            "race_no": race.race_no,
            "request_identity": self.request_identity,
            "request_identity_sha256": self.request_identity_sha256,
            "requested_at_utc": _datetime_text(requested),
            "response_byte_length": self.response_byte_length,
            "response_sha256": self.response_sha256,
            "schema_version": 1,
            "source_completeness": self.source_completeness.value,
            "source_state": self.source_state.value,
            "source_system": "keiba.go.jp",
        }
        digest = _hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
        object.__setattr__(self, "evidence_content_sha256", digest)
        object.__setattr__(self, "evidence_id", _EVIDENCE_PREFIX + digest)


def _validated_capture(value: object) -> NARMarketOddsResponseCapture:
    if type(value) is not NARMarketOddsResponseCapture:
        raise _validation("capture must be exact NARMarketOddsResponseCapture")
    try:
        supplied = {name: getattr(value, name) for name in _CAPTURE_FIELDS}
        rebuilt = NARMarketOddsResponseCapture(
            request_identity=supplied["request_identity"],
            effective_url=supplied["effective_url"],
            response_body=supplied["response_body"],
            charset=supplied["charset"],
            requested_at=supplied["requested_at"],
            observed_at=supplied["observed_at"],
            captured_at=supplied["captured_at"],
            http_status=supplied["http_status"],
            content_type=supplied["content_type"],
            content_encoding=supplied["content_encoding"],
            http_date=supplied["http_date"],
            etag=supplied["etag"],
            last_modified=supplied["last_modified"],
            content_length=supplied["content_length"],
        )
        if any(supplied[name] != getattr(rebuilt, name) for name in _CAPTURE_FIELDS):
            raise _validation("capture derived values are contradictory")
    except NARMarketOddsSourceParseValidationError:
        raise
    except (AttributeError, KeyError, TypeError, _NARMarketOddsCaptureError) as error:
        raise _validation("capture is malformed or contradictory") from error
    return rebuilt


def _one(nodes: object, name: str) -> _Tag:
    try:
        values = tuple(nodes)  # type: ignore[arg-type]
    except TypeError as error:
        raise _unsupported(f"{name} is invalid") from error
    if len(values) != 1 or type(values[0]) is not _Tag:
        raise _unsupported(f"{name} must occur exactly once")
    return values[0]


def _direct_tags(node: _Tag) -> tuple[_Tag, ...]:
    return tuple(child for child in node.children if type(child) is _Tag)


def _normalized_text(node: _Tag) -> str:
    return _ASCII_WHITESPACE_RUN.sub(" ", node.get_text(" ")).strip(_ASCII_WHITESPACE)


def _strict_direct_text(node: _Tag, name: str) -> str:
    if _direct_tags(node):
        raise _unsupported(f"{name} has unexpected nested elements")
    values = tuple(
        str(child)
        for child in node.children
        if isinstance(child, _NavigableString) and not isinstance(child, _Comment)
    )
    return "".join(values).strip(_ASCII_WHITESPACE)


def _require_visible(node: _Tag, name: str) -> None:
    aria_hidden = node.get("aria-hidden")
    style = node.get("style")
    if (
        node.has_attr("hidden")
        or (
            type(aria_hidden) is str
            and aria_hidden.strip(_ASCII_WHITESPACE).casefold() == "true"
        )
        or (
            type(style) is str
            and (
                _INLINE_DISPLAY_NONE.search(style) is not None
                or _INLINE_VISIBILITY_HIDDEN.search(style) is not None
            )
        )
    ):
        raise _unsupported(f"{name} is hidden")


def _require_visible_within(node: _Tag, root: _Tag, name: str) -> None:
    current = node
    while True:
        _require_visible(current, name)
        if current is root:
            return
        parent = current.parent
        if type(parent) is not _Tag:
            raise _unsupported(f"{name} is outside the market-odds root")
        current = parent


def _source_state(root: _Tag, page_kind: NARMarketOddsPageKind) -> tuple[NARMarketOddsSourceState, str | None]:
    heading = _one(root.select(":scope > div.odd_header > h4.odd_title"), "source-state heading")
    _require_visible_within(heading, root, "source-state heading")
    if _direct_tags(heading):
        raise _unsupported("source-state heading has unexpected nested elements")
    text = _normalized_text(heading)
    title = _PAGE_TITLES[page_kind]
    open_match = _re.fullmatch(rf"{_re.escape(title)} （(?P<time>{_DISPLAY_TIME}) 現在）", text)
    if open_match is not None:
        return NARMarketOddsSourceState.OPEN, open_match.group("time") + " 現在"
    if text == title + " （最終）":
        return NARMarketOddsSourceState.FINAL, None
    raise _unsupported("source-state heading is unsupported or disagrees with page kind")


def _positive_number(text: str, name: str) -> int:
    if _POSITIVE_TOKEN.fullmatch(text) is None:
        raise _data_error(f"{name} is not a canonical positive ASCII horse number")
    return int(text)


def _selection_token(node: _Tag, arity: int) -> tuple[int, ...]:
    text = _strict_direct_text(node, "selection")
    pattern = rf"[1-9][0-9]*(?:-[1-9][0-9]*){{{arity - 1}}}"
    if _re.fullmatch(pattern, text) is None:
        raise _data_error("selection token shape is invalid")
    values = tuple(_positive_number(token, "selection member") for token in text.split("-"))
    if len(set(values)) != arity:
        raise _data_error("selection members must be distinct")
    return tuple(sorted(values))


def _source_decimal(text: str, name: str) -> _Decimal:
    token = text.strip(_ASCII_WHITESPACE)
    if _DECIMAL_TOKEN.fullmatch(token) is None:
        raise _numeric_error(f"{name} must be a positive ASCII dotted decimal")
    try:
        value = _Decimal(token)
    except _InvalidOperation as error:
        raise _numeric_error(f"{name} is invalid") from error
    if not value.is_finite() or value <= 0:
        raise _numeric_error(f"{name} must be finite and positive")
    return value


def _scalar_odds(node: _Tag) -> _Decimal:
    return _source_decimal(_strict_direct_text(node, "scalar odds"), "scalar odds")


def _wide_odds(node: _Tag) -> tuple[_Decimal, _Decimal]:
    parts: list[tuple[str, object]] = []
    for child in node.children:
        if isinstance(child, _Comment):
            continue
        if isinstance(child, _NavigableString):
            text = str(child).strip(_ASCII_WHITESPACE)
            if text:
                parts.append(("text", text))
        elif type(child) is _Tag:
            parts.append(("tag", child))
        else:
            raise _numeric_error("WIDE odds contain unsupported content")
    if (
        len(parts) != 3
        or parts[0][0] != "text"
        or parts[1][0] != "tag"
        or parts[2][0] != "text"
    ):
        raise _numeric_error("WIDE odds must contain lower, br, and upper")
    separator = parts[1][1]
    if type(separator) is not _Tag or separator.name != "br" or separator.attrs:
        raise _numeric_error("WIDE odds separator must be one literal br")
    lower_text = parts[0][1]
    upper_text = parts[2][1]
    if type(lower_text) is not str or type(upper_text) is not str or not upper_text.startswith("-"):
        raise _numeric_error("WIDE odds endpoint text is invalid")
    lower = _source_decimal(lower_text, "WIDE lower odds")
    upper = _source_decimal(upper_text[1:], "WIDE upper odds")
    if lower > upper:
        raise _numeric_error("WIDE lower odds must not exceed upper odds")
    return lower, upper


def _win_quotes(root: _Tag) -> tuple[NARMarketOddsExactQuote, ...]:
    table = _one(root.select(":scope table.odd_popular_table_02"), "WIN quote table")
    _require_visible_within(table, root, "WIN quote table")
    heading = _one(table.select(":scope > thead > tr"), "WIN table heading")
    header_cells = tuple(heading.find_all("th", recursive=False))
    if len(header_cells) != 12 or tuple(_normalized_text(cell) for cell in header_cells[:4]) != (
        "枠",
        "馬番",
        "馬名",
        "単勝 オッズ",
    ):
        raise _unsupported("WIN table heading is outside parser v1")
    tbody = _one(table.select(":scope > tbody"), "WIN table body")
    rows = tuple(child for child in _direct_tags(tbody) if child.name == "tr")
    if not rows or len(rows) != len(_direct_tags(tbody)):
        raise _unsupported("WIN table rows are missing or structurally invalid")
    quotes: list[NARMarketOddsExactQuote] = []
    for row in rows:
        _require_visible(row, "WIN quote row")
        cells = tuple(row.find_all("td", recursive=False))
        if len(cells) != 13 or len(_direct_tags(row)) != 13:
            raise _unsupported("WIN quote row must have exactly 13 cells")
        _require_visible(cells[1], "WIN horse number")
        _require_visible(cells[3], "WIN scalar odds")
        horse_number = _positive_number(_strict_direct_text(cells[1], "WIN horse number"), "WIN horse number")
        quotes.append(NARMarketOddsExactQuote((horse_number,), _scalar_odds(cells[3])))
    return _ordered_quotes(quotes)


def _ranking_quotes(
    root: _Tag,
    *,
    page_kind: NARMarketOddsPageKind,
) -> tuple[NARMarketOddsSourceQuote, ...]:
    container = _one(root.select(":scope > ul.odd_ranking"), "ranking quote container")
    _require_visible_within(container, root, "ranking quote container")
    items = _direct_tags(container)
    if not items or any(item.name != "li" or "odd_ranking_item" not in (item.get("class") or ()) for item in items):
        raise _unsupported("ranking quote partitions are invalid")
    partitions: list[tuple[_Tag, int, int]] = []
    expected_start = 1
    for item in items:
        _require_visible(item, "ranking quote partition")
        children = _direct_tags(item)
        if tuple(child.name for child in children) != ("h4", "table"):
            raise _unsupported("ranking quote partition direct structure is invalid")
        partition_heading, table = children
        if (
            "odd_ranking_title" not in (partition_heading.get("class") or ())
            or "odd_ranking_table" not in (table.get("class") or ())
        ):
            raise _unsupported("ranking quote partition classes are invalid")
        partition_match = _re.fullmatch(
            r"(?P<start>[1-9][0-9]*)～(?P<end>[1-9][0-9]*)件",
            _normalized_text(partition_heading),
        )
        if partition_match is None:
            raise _unsupported("ranking quote partition heading is invalid")
        start = int(partition_match.group("start"))
        end = int(partition_match.group("end"))
        if start != expected_start or end < start:
            raise _unsupported("ranking quote partitions are not contiguous")
        _require_visible(table, "ranking quote table")
        partitions.append((table, start, end))
        expected_start = end + 1
    quotes: list[NARMarketOddsSourceQuote] = []
    arity = _PAGE_ARITIES[page_kind]
    for table, start, end in partitions:
        rows = tuple(table.find_all("tr", recursive=False))
        if len(rows) < 2 or len(_direct_tags(table)) != len(rows):
            raise _unsupported("ranking table rows are incomplete or nested unexpectedly")
        if len(rows) - 1 != end - start + 1:
            raise _unsupported("ranking quote partition row count is inconsistent")
        headers = tuple(rows[0].find_all("th", recursive=False))
        if len(headers) != 3 or len(_direct_tags(rows[0])) != 3 or tuple(_normalized_text(cell) for cell in headers) != (
            "組合せ",
            "オッズ",
            "人気",
        ):
            raise _unsupported("ranking table heading is outside parser v1")
        for row in rows[1:]:
            _require_visible(row, "ranking quote row")
            cells = tuple(row.find_all("td", recursive=False))
            if len(cells) != 3 or len(_direct_tags(row)) != 3:
                raise _unsupported("ranking quote row must have exactly three cells")
            _require_visible(cells[0], "ranking selection")
            _require_visible(cells[1], "ranking odds")
            selection = _selection_token(cells[0], arity)
            if page_kind is NARMarketOddsPageKind.ODDS_WIDE:
                lower, upper = _wide_odds(cells[1])
                quotes.append(NARMarketOddsRangeQuote(selection, lower, upper))
            else:
                quotes.append(NARMarketOddsExactQuote(selection, _scalar_odds(cells[1])))
    if not quotes:
        raise _unsupported("authoritative quote container is empty")
    return _ordered_quotes(quotes)


def _ordered_quotes(quotes: list[NARMarketOddsSourceQuote]) -> tuple[NARMarketOddsSourceQuote, ...]:
    selections = tuple(quote.selection for quote in quotes)
    if len(set(selections)) != len(selections):
        raise _data_error("authoritative source contains duplicate canonical selections")
    return tuple(sorted(quotes, key=lambda quote: quote.selection))


def parse_nar_market_odds_source_capture(
    *,
    capture: NARMarketOddsResponseCapture,
) -> NARMarketOddsSourceEvidence:
    """Parse one exact Phase32 capture into provider-level source evidence."""

    trusted = _validated_capture(capture)
    try:
        document = _BeautifulSoup(trusted.response_body.decode("utf-8", errors="strict"), "html.parser")
        root = _one(
            document.select("article.raceCard > div.innerWrapper > div#odd_content"),
            "market-odds root",
        )
        page_kind = trusted.request_identity.page_kind
        state, display_text = _source_state(root, page_kind)
        if page_kind is NARMarketOddsPageKind.ODDS_TAN_FUKU:
            quotes: tuple[NARMarketOddsSourceQuote, ...] = _win_quotes(root)
        else:
            quotes = _ranking_quotes(root, page_kind=page_kind)
    except NARMarketOddsSourceParseError:
        raise
    except _ParserRejectedMarkup as error:
        raise _unsupported("HTML parser rejected source markup") from error
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
        raise _unsupported("source structure is outside parser v1") from error

    request = trusted.request_identity
    return NARMarketOddsSourceEvidence(
        page_kind=request.page_kind,
        race_identity=request.race_identity,
        request_identity=request.request_identity,
        request_identity_sha256=request.request_identity_sha256,
        canonical_request_url=request.canonical_request_url,
        capture_id=trusted.capture_id,
        response_sha256=trusted.response_sha256,
        response_byte_length=trusted.byte_length,
        requested_at=trusted.requested_at,
        observed_at=trusted.observed_at,
        captured_at=trusted.captured_at,
        source_state=state,
        provider_display_as_of_text=display_text,
        source_completeness=NARMarketOddsSourceCompleteness.UNVERIFIED,
        provider_horse_numbers=None,
        quotes=quotes,
    )


__all__ = (
    "NARMarketOddsExactQuote",
    "NARMarketOddsRangeQuote",
    "NARMarketOddsSourceCompleteness",
    "NARMarketOddsSourceEvidence",
    "NARMarketOddsSourceParseDataError",
    "NARMarketOddsSourceParseError",
    "NARMarketOddsSourceParseNumericError",
    "NARMarketOddsSourceParseUnsupportedError",
    "NARMarketOddsSourceParseValidationError",
    "NARMarketOddsSourceQuote",
    "NARMarketOddsSourceQuoteKind",
    "NARMarketOddsSourceState",
    "parse_nar_market_odds_source_capture",
)


if "annotations" in globals():
    del annotations
