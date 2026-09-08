"""Strict supplied-capture bootstrap for NAR MonthlyConveneInfo."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass, field as _field
from datetime import date as _date
from html import unescape as _html_unescape
from html.parser import HTMLParser as _HTMLParser
import hashlib as _hashlib
import json as _json
import re as _re

from scripts.simulation.nar_historical_daily_target_bootstrap_capture import (
    NARMonthlyConveneInfoBootstrapCaptureError as _CaptureError,
    NARMonthlyConveneInfoBootstrapPageKind as _PageKind,
    NARMonthlyConveneInfoBootstrapSupplierCapture as _SupplierCapture,
)
from scripts.simulation.nar_historical_daily_target_capture import (
    NARHistoricalDailyTargetCaptureError as _DailyTargetCaptureError,
    NARHistoricalDailyTargetPageKind as _DailyTargetPageKind,
    NARHistoricalDailyTargetRequestIdentity as _DailyTargetRequestIdentity,
)


_INITIAL_DATE = _date(2020, 1, 1)
_OFFICIAL_ORIGIN = "https://www.keiba.go.jp"
_ROOT_RAW = "/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop"
_SCRIPT_RAW = "/KeibaWeb/resources/js/monthltconveninfo.js?t=20260130_1"
_SCRIPT_URL = _OFFICIAL_ORIGIN + _SCRIPT_RAW
_SCRIPT_LENGTH = 438
_SCRIPT_SHA256 = "bdf86457a9c917fc8259f8b87593c9bbece72d501a95fb5d3573a93b43532515"
_REQUEST_PREFIX = b"/KeibaWeb/MonthlyConveneInfo/MonthlyConveneInfoTop?k_year="
_REQUEST_SEPARATOR = b"&k_month="
_CAPTURE_ID = _re.compile(r"nar-monthly-bootstrap-capture-v1:[0-9a-f]{64}\Z")
_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_YEAR = _re.compile(r"[0-9]{4}\Z")
_MONTH = _re.compile(r"(?:[1-9]|1[0-2])\Z")
_ROOT_STRUCTURAL_LOCATOR = "li.gNaviitem2>a[href]"
_SCRIPT_STRUCTURAL_LOCATOR = (
    "head>script[src];article.monthlySchedule form "
    "select#selectedYear[name=k_year];ul.monthTab>li.tab[month]"
)
_VOID = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
_JS_GRAMMAR = _re.compile(
    rb"\A\$\(function \(\) \{\n"
    rb"  function changePage\(year, month\) \{\n"
    rb'    window\.location\.href = "(?P<prefix>'
    + _re.escape(_REQUEST_PREFIX)
    + rb')" \+ year \+ "(?P<separator>'
    + _re.escape(_REQUEST_SEPARATOR)
    + rb')" \+ month;\n'
    rb"  \}\n"
    rb"  \$\('#selectedYear'\)\.on\('change', function\(e\) \{\n"
    rb"    changePage\(e\.target\.value, \$\('li\.tab\.active'\)\.attr\('month'\)\);\n"
    rb"  \}\);\n"
    rb"  \$\('li\.tab:not\(\.active\)'\)\.on\('click', function\(e\) \{\n"
    rb"    changePage\(\$\('#selectedYear'\)\.val\(\), e\.target\.getAttribute\('month'\)\);\n"
    rb"  \}\);\n"
    rb"\}\);\n"
    rb"//EOF\n\Z"
)


class NARMonthlyConveneInfoBootstrapError(Exception):
    """Base error for the supplied-capture bootstrap."""


class NARMonthlyConveneInfoBootstrapValidationError(NARMonthlyConveneInfoBootstrapError):
    """Raised for invalid API values."""


class NARMonthlyConveneInfoBootstrapUnsupportedError(NARMonthlyConveneInfoBootstrapError):
    """Raised when source material is outside the qualified grammar."""


class NARMonthlyConveneInfoBootstrapIntegrityError(NARMonthlyConveneInfoBootstrapError):
    """Raised when immutable supplier evidence cannot be reconstructed exactly."""


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    return _json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _derived_identity(prefix: str, payload: dict[str, object]) -> tuple[str, str]:
    digest = _hashlib.sha256(_canonical_bytes(payload)).hexdigest()
    return digest, f"{prefix}{digest}"


def _require_capture_id(value: object, name: str) -> str:
    if type(value) is not str or _CAPTURE_ID.fullmatch(value) is None:
        raise NARMonthlyConveneInfoBootstrapValidationError(f"{name} is invalid")
    return value


def _require_sha256(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise NARMonthlyConveneInfoBootstrapValidationError(f"{name} is invalid")
    return value


@_dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoRootLocator:
    homepage_capture_id: str
    homepage_response_sha256: str
    raw_href: bytes
    resolved_url: str
    structural_locator: str
    schema_version: int = _field(init=False, default=1)
    page_kind: _PageKind = _field(init=False, default=_PageKind.MONTHLY_ROOT)
    locator_identity_sha256: str = _field(init=False)
    locator_identity: str = _field(init=False)

    def __post_init__(self) -> None:
        _require_capture_id(self.homepage_capture_id, "homepage_capture_id")
        _require_sha256(self.homepage_response_sha256, "homepage_response_sha256")
        if type(self.raw_href) is not bytes or self.raw_href != _ROOT_RAW.encode("ascii"):
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "raw_href is not the exact supplied Monthly root href"
            )
        if type(self.resolved_url) is not str or self.resolved_url != _OFFICIAL_ORIGIN + _ROOT_RAW:
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "resolved_url is not the exact qualified Monthly root URL"
            )
        if type(self.structural_locator) is not str or self.structural_locator != _ROOT_STRUCTURAL_LOCATOR:
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "structural_locator is not the qualified homepage relation"
            )
        digest, identity = _derived_identity(
            "nar-monthly-bootstrap-root-locator-v1:",
            {
                "homepage_capture_id": self.homepage_capture_id,
                "homepage_response_sha256": self.homepage_response_sha256,
                "page_kind": self.page_kind.value,
                "raw_href_hex": self.raw_href.hex(),
                "resolved_url": self.resolved_url,
                "schema_version": 1,
                "structural_locator": self.structural_locator,
            },
        )
        object.__setattr__(self, "locator_identity_sha256", digest)
        object.__setattr__(self, "locator_identity", identity)


@_dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoLocatorScriptResolution:
    root_locator: NARMonthlyConveneInfoRootLocator
    monthly_root_capture_id: str
    monthly_root_response_sha256: str
    target_date: _date
    raw_script_src: bytes
    resolved_script_url: str
    offered_year_token: bytes
    offered_month_token: bytes
    structural_locator: str
    schema_version: int = _field(init=False, default=1)
    page_kind: _PageKind = _field(init=False, default=_PageKind.LOCATOR_SCRIPT)
    resolution_identity_sha256: str = _field(init=False)
    resolution_identity: str = _field(init=False)

    def __post_init__(self) -> None:
        _require_root_locator(self.root_locator)
        _require_capture_id(self.monthly_root_capture_id, "monthly_root_capture_id")
        _require_sha256(self.monthly_root_response_sha256, "monthly_root_response_sha256")
        if type(self.target_date) is not _date or self.target_date < _INITIAL_DATE:
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "target_date is outside the qualified exact-date profile"
            )
        if type(self.raw_script_src) is not bytes or self.raw_script_src != _SCRIPT_RAW.encode("ascii"):
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "raw_script_src is not the exact supplied locator-script src"
            )
        if type(self.resolved_script_url) is not str or self.resolved_script_url != _SCRIPT_URL:
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "resolved_script_url is not the pinned locator-script URL"
            )
        expected_year = str(self.target_date.year).encode("ascii")
        expected_month = str(self.target_date.month).encode("ascii")
        if type(self.offered_year_token) is not bytes or self.offered_year_token != expected_year:
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "offered_year_token does not exactly match target_date"
            )
        if type(self.offered_month_token) is not bytes or self.offered_month_token != expected_month:
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "offered_month_token does not exactly match target_date"
            )
        if type(self.structural_locator) is not str or self.structural_locator != _SCRIPT_STRUCTURAL_LOCATOR:
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "structural_locator is not the qualified Monthly root relation"
            )
        digest, identity = _derived_identity(
            "nar-monthly-bootstrap-script-resolution-v1:",
            {
                "monthly_root_capture_id": self.monthly_root_capture_id,
                "monthly_root_response_sha256": self.monthly_root_response_sha256,
                "offered_month_token_hex": self.offered_month_token.hex(),
                "offered_year_token_hex": self.offered_year_token.hex(),
                "page_kind": self.page_kind.value,
                "raw_script_src_hex": self.raw_script_src.hex(),
                "resolved_script_url": self.resolved_script_url,
                "root_locator_identity": self.root_locator.locator_identity,
                "schema_version": 1,
                "structural_locator": self.structural_locator,
                "target_date": self.target_date.isoformat(),
            },
        )
        object.__setattr__(self, "resolution_identity_sha256", digest)
        object.__setattr__(self, "resolution_identity", identity)


@_dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoRequestMaterialResolution:
    locator_script_resolution: NARMonthlyConveneInfoLocatorScriptResolution
    locator_script_capture_id: str
    locator_script_response_sha256: str
    official_supplied_request_material: bytes
    resolved_request_url: str
    schema_version: int = _field(init=False, default=1)
    resolution_identity_sha256: str = _field(init=False)
    resolution_identity: str = _field(init=False)

    def __post_init__(self) -> None:
        _require_script_resolution(self.locator_script_resolution)
        _require_capture_id(self.locator_script_capture_id, "locator_script_capture_id")
        _require_sha256(self.locator_script_response_sha256, "locator_script_response_sha256")
        expected_material = (
            _REQUEST_PREFIX
            + self.locator_script_resolution.offered_year_token
            + _REQUEST_SEPARATOR
            + self.locator_script_resolution.offered_month_token
        )
        if (
            type(self.official_supplied_request_material) is not bytes
            or self.official_supplied_request_material != expected_material
        ):
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "official_supplied_request_material is not the source-owned material"
            )
        expected_url = _OFFICIAL_ORIGIN + expected_material.decode("ascii")
        if type(self.resolved_request_url) is not str or self.resolved_request_url != expected_url:
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "resolved_request_url contradicts the supplied request material"
            )
        digest, identity = _derived_identity(
            "nar-monthly-bootstrap-request-material-v1:",
            {
                "locator_script_capture_id": self.locator_script_capture_id,
                "locator_script_resolution_identity": self.locator_script_resolution.resolution_identity,
                "locator_script_response_sha256": self.locator_script_response_sha256,
                "official_supplied_request_material_hex": self.official_supplied_request_material.hex(),
                "resolved_request_url": self.resolved_request_url,
                "schema_version": 1,
            },
        )
        object.__setattr__(self, "resolution_identity_sha256", digest)
        object.__setattr__(self, "resolution_identity", identity)


def _require_root_locator(value: object) -> NARMonthlyConveneInfoRootLocator:
    if type(value) is not NARMonthlyConveneInfoRootLocator:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "root_locator must be NARMonthlyConveneInfoRootLocator"
        )
    try:
        rebuilt = NARMonthlyConveneInfoRootLocator(
            homepage_capture_id=value.homepage_capture_id,
            homepage_response_sha256=value.homepage_response_sha256,
            raw_href=value.raw_href,
            resolved_url=value.resolved_url,
            structural_locator=value.structural_locator,
        )
    except NARMonthlyConveneInfoBootstrapValidationError as error:
        raise NARMonthlyConveneInfoBootstrapIntegrityError(
            "root_locator cannot be reconstructed exactly"
        ) from error
    if rebuilt != value:
        raise NARMonthlyConveneInfoBootstrapIntegrityError(
            "root_locator derived identity is corrupt"
        )
    return value


def _require_script_resolution(value: object) -> NARMonthlyConveneInfoLocatorScriptResolution:
    if type(value) is not NARMonthlyConveneInfoLocatorScriptResolution:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "locator_script_resolution must be NARMonthlyConveneInfoLocatorScriptResolution"
        )
    try:
        rebuilt = NARMonthlyConveneInfoLocatorScriptResolution(
            root_locator=value.root_locator,
            monthly_root_capture_id=value.monthly_root_capture_id,
            monthly_root_response_sha256=value.monthly_root_response_sha256,
            target_date=value.target_date,
            raw_script_src=value.raw_script_src,
            resolved_script_url=value.resolved_script_url,
            offered_year_token=value.offered_year_token,
            offered_month_token=value.offered_month_token,
            structural_locator=value.structural_locator,
        )
    except NARMonthlyConveneInfoBootstrapError as error:
        raise NARMonthlyConveneInfoBootstrapIntegrityError(
            "locator_script_resolution cannot be reconstructed exactly"
        ) from error
    if rebuilt != value:
        raise NARMonthlyConveneInfoBootstrapIntegrityError(
            "locator_script_resolution derived identity is corrupt"
        )
    return value


def _evidence_identity(
    homepage_capture: _SupplierCapture,
    monthly_root_capture: _SupplierCapture,
    locator_script_capture: _SupplierCapture,
) -> str:
    payload = {
        "homepage_capture_id": homepage_capture.capture_id,
        "locator_script_capture_id": locator_script_capture.capture_id,
        "monthly_root_capture_id": monthly_root_capture.capture_id,
        "schema_version": 1,
    }
    digest = _hashlib.sha256(_canonical_bytes(payload)).hexdigest()
    return f"nar-monthly-bootstrap-evidence-v1:{digest}"


@_dataclass(frozen=True, slots=True)
class NARMonthlyConveneInfoBootstrapEvidence:
    homepage_capture: _SupplierCapture
    monthly_root_capture: _SupplierCapture
    locator_script_capture: _SupplierCapture
    schema_version: int = _field(init=False, default=1)
    supplier_evidence_identity: str = _field(init=False)

    def __post_init__(self) -> None:
        values = (
            (self.homepage_capture, _PageKind.OFFICIAL_HOME, "homepage_capture"),
            (self.monthly_root_capture, _PageKind.MONTHLY_ROOT, "monthly_root_capture"),
            (self.locator_script_capture, _PageKind.LOCATOR_SCRIPT, "locator_script_capture"),
        )
        for value, kind, name in values:
            if type(value) is not _SupplierCapture:
                raise NARMonthlyConveneInfoBootstrapValidationError(
                    f"{name} must be NARMonthlyConveneInfoBootstrapSupplierCapture"
                )
            if value.page_kind is not kind:
                raise NARMonthlyConveneInfoBootstrapValidationError(
                    f"{name} has the wrong page kind"
                )
        identifiers = tuple(value.capture_id for value, _kind, _name in values)
        if len(set(identifiers)) != len(identifiers):
            raise NARMonthlyConveneInfoBootstrapValidationError(
                "supplier capture identities must be unique"
            )
        object.__setattr__(
            self,
            "supplier_evidence_identity",
            _evidence_identity(
                self.homepage_capture,
                self.monthly_root_capture,
                self.locator_script_capture,
            ),
        )


@_dataclass(slots=True)
class _Node:
    tag: str
    attrs: tuple[tuple[str, str | None], ...]
    raw_start: str
    content: list[object]

    def attr(self, name: str) -> str | None:
        values = [value for key, value in self.attrs if key == name]
        if len(values) > 1:
            raise ValueError(f"duplicate {name} attribute")
        return values[0] if values else None

    def classes(self) -> tuple[str, ...]:
        value = self.attr("class")
        return () if value is None else tuple(value.split())

    def children(self, tag: str | None = None) -> tuple[_Node, ...]:
        values = tuple(item for item in self.content if type(item) is _Node)
        return values if tag is None else tuple(item for item in values if item.tag == tag)

    def descendants(self, tag: str | None = None) -> tuple[_Node, ...]:
        result: list[_Node] = []
        for child in self.children():
            if tag is None or child.tag == tag:
                result.append(child)
            result.extend(child.descendants(tag))
        return tuple(result)

    def raw_text(self) -> str:
        return "".join(
            item.raw_text() if type(item) is _Node else str(item)
            for item in self.content
        )

    def text(self) -> str:
        return _html_unescape(self.raw_text())


class _TreeParser(_HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.root = _Node("#document", (), "", [])
        self.stack = [self.root]
        self.structural_errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag, tuple(attrs), self.get_starttag_text(), [])
        self.stack[-1].content.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1].content.append(_Node(tag, tuple(attrs), self.get_starttag_text(), []))

    def handle_endtag(self, tag: str) -> None:
        positions = [index for index, node in enumerate(self.stack) if node.tag == tag]
        if not positions:
            self.structural_errors.append(f"unmatched closing tag {tag}")
            return
        del self.stack[positions[-1]:]

    def handle_data(self, data: str) -> None:
        self.stack[-1].content.append(data)

    def handle_entityref(self, name: str) -> None:
        self.stack[-1].content.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.stack[-1].content.append(f"&#{name};")


def _tree(body: bytes, name: str) -> _Node:
    try:
        text = body.decode("utf-8", errors="strict")
        parser = _TreeParser()
        parser.feed(text)
        parser.close()
    except (UnicodeDecodeError, TypeError, ValueError) as error:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            f"{name} is not strict parseable UTF-8 HTML"
        ) from error
    return parser.root


def _raw_double_attribute(node: _Node, name: str) -> str:
    pattern = _re.compile(r'(?:^|\s)' + _re.escape(name) + r'\s*=\s*"([^"]*)"(?:\s|>)')
    matches = tuple(pattern.finditer(node.raw_start))
    if len(matches) != 1:
        raise ValueError(f"{name} must be one raw double-quoted attribute")
    return matches[0].group(1)


def _collapsed(node: _Node) -> str:
    return " ".join(node.text().split())


def _class_nodes(root: _Node, tag: str, class_name: str) -> tuple[_Node, ...]:
    result: list[_Node] = []
    for node in root.descendants(tag):
        try:
            if class_name in node.classes():
                result.append(node)
        except ValueError:
            continue
    return tuple(result)


def _reconstruct_capture(value: _SupplierCapture, name: str) -> None:
    try:
        reconstructed = _SupplierCapture(
            page_kind=value.page_kind,
            canonical_request_url=value.canonical_request_url,
            effective_url=value.effective_url,
            response_body=value.response_body,
            charset=value.charset,
            requested_at=value.requested_at,
            observed_at=value.observed_at,
            stored_at=value.stored_at,
            http_status=value.http_status,
            content_type=value.content_type,
            content_encoding=value.content_encoding,
            content_length=value.content_length,
        )
    except _CaptureError as error:
        raise NARMonthlyConveneInfoBootstrapIntegrityError(
            f"{name} cannot be reconstructed as an exact immutable capture"
        ) from error
    if reconstructed != value:
        raise NARMonthlyConveneInfoBootstrapIntegrityError(
            f"{name} exact digest or identity is corrupt"
        )


def _validate_integrity(evidence: NARMonthlyConveneInfoBootstrapEvidence) -> None:
    for value, name in (
        (evidence.homepage_capture, "homepage_capture"),
        (evidence.monthly_root_capture, "monthly_root_capture"),
        (evidence.locator_script_capture, "locator_script_capture"),
    ):
        _reconstruct_capture(value, name)
    expected = _evidence_identity(
        evidence.homepage_capture,
        evidence.monthly_root_capture,
        evidence.locator_script_capture,
    )
    if evidence.supplier_evidence_identity != expected:
        raise NARMonthlyConveneInfoBootstrapIntegrityError(
            "supplier evidence identity is corrupt"
        )


def resolve_nar_monthly_convene_info_root_locator(
    *,
    homepage_capture: _SupplierCapture,
) -> NARMonthlyConveneInfoRootLocator:
    if type(homepage_capture) is not _SupplierCapture:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "homepage_capture must be NARMonthlyConveneInfoBootstrapSupplierCapture"
        )
    _reconstruct_capture(homepage_capture, "homepage_capture")
    if homepage_capture.page_kind is not _PageKind.OFFICIAL_HOME:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "homepage_capture has the wrong page kind"
        )
    root = _tree(homepage_capture.response_body, "homepage capture")
    exact: list[_Node] = []
    for anchor in root.descendants("a"):
        try:
            if _raw_double_attribute(anchor, "href") == _ROOT_RAW:
                exact.append(anchor)
        except ValueError:
            continue
    qualified: list[_Node] = []
    for item in _class_nodes(root, "li", "gNaviitem2"):
        for anchor in item.descendants("a"):
            try:
                if _raw_double_attribute(anchor, "href") == _ROOT_RAW:
                    qualified.append(anchor)
            except ValueError:
                continue
    if len(exact) != 1 or len(qualified) != 1 or exact[0] is not qualified[0]:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "homepage does not contain one exact qualified Monthly root href"
        )
    return NARMonthlyConveneInfoRootLocator(
        homepage_capture_id=homepage_capture.capture_id,
        homepage_response_sha256=homepage_capture.response_sha256,
        raw_href=_ROOT_RAW.encode("ascii"),
        resolved_url=_OFFICIAL_ORIGIN + _ROOT_RAW,
        structural_locator=_ROOT_STRUCTURAL_LOCATOR,
    )


def resolve_nar_monthly_convene_info_locator_script(
    *,
    target_date: _date,
    root_locator: NARMonthlyConveneInfoRootLocator,
    monthly_root_capture: _SupplierCapture,
) -> NARMonthlyConveneInfoLocatorScriptResolution:
    if type(target_date) is not _date:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "target_date must be exact date"
        )
    if target_date < _INITIAL_DATE:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "target_date precedes the qualified initial profile"
        )
    _require_root_locator(root_locator)
    if type(monthly_root_capture) is not _SupplierCapture:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "monthly_root_capture must be NARMonthlyConveneInfoBootstrapSupplierCapture"
        )
    _reconstruct_capture(monthly_root_capture, "monthly_root_capture")
    if monthly_root_capture.page_kind is not _PageKind.MONTHLY_ROOT:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "monthly_root_capture has the wrong page kind"
        )
    if monthly_root_capture.canonical_request_url != root_locator.resolved_url:
        raise NARMonthlyConveneInfoBootstrapIntegrityError(
            "Monthly root capture contradicts the source-bound root locator"
        )
    root = _tree(monthly_root_capture.response_body, "Monthly root capture")
    exact_scripts: list[_Node] = []
    for script in root.descendants("script"):
        try:
            if _raw_double_attribute(script, "src") == _SCRIPT_RAW:
                exact_scripts.append(script)
        except ValueError:
            continue
    head_scripts: list[_Node] = []
    for head in root.descendants("head"):
        for script in head.descendants("script"):
            try:
                if _raw_double_attribute(script, "src") == _SCRIPT_RAW:
                    head_scripts.append(script)
            except ValueError:
                continue
    if (
        len(exact_scripts) != 1
        or len(head_scripts) != 1
        or exact_scripts[0] is not head_scripts[0]
    ):
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "Monthly root does not contain one exact qualified locator-script src"
        )
    articles = _class_nodes(root, "article", "monthlySchedule")
    if len(articles) != 1:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "Monthly schedule article is not unique"
        )
    article = articles[0]
    forms = article.descendants("form")
    if len(forms) != 1:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "Monthly schedule form is not unique"
        )
    selects: list[_Node] = []
    try:
        for node in forms[0].descendants("select"):
            if node.attr("id") == "selectedYear" and node.attr("name") == "k_year":
                selects.append(node)
    except ValueError as error:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "official year control contains duplicated attributes"
        ) from error
    if len(selects) != 1:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "official year control is not unique"
        )
    years: dict[str, bytes] = {}
    try:
        options = selects[0].children("option")
        if not options:
            raise ValueError("year options are missing")
        for option in options:
            token = _raw_double_attribute(option, "value")
            if _YEAR.fullmatch(token) is None or _collapsed(option) != token or token in years:
                raise ValueError("year option is malformed or duplicated")
            years[token] = token.encode("ascii")
    except (UnicodeEncodeError, ValueError) as error:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "official year options are malformed or duplicated"
        ) from error
    year_key = str(target_date.year)
    if year_key not in years:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "target year is not offered by the supplied official root"
        )
    month_lists = _class_nodes(article, "ul", "monthTab")
    if len(month_lists) != 1:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "official month control is not unique"
        )
    months: dict[str, bytes] = {}
    try:
        items = month_lists[0].children("li")
        if len(items) != 12:
            raise ValueError("month item count is not twelve")
        for item in items:
            token = _raw_double_attribute(item, "month")
            if (
                _MONTH.fullmatch(token) is None
                or item.attr("id") != f"monthTab{token}"
                or "tab" not in item.classes()
                or token in months
            ):
                raise ValueError("month item is malformed or duplicated")
            paragraphs = item.children("p")
            if len(paragraphs) != 1 or _collapsed(paragraphs[0]) != f"{token}月":
                raise ValueError("month display is contradictory")
            months[token] = token.encode("ascii")
        if set(months) != {str(value) for value in range(1, 13)}:
            raise ValueError("month set is incomplete")
    except (UnicodeEncodeError, ValueError) as error:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "official month tokens are malformed or incomplete"
        ) from error
    month_key = str(target_date.month)
    if month_key not in months:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "target month is not offered by the supplied official root"
        )
    return NARMonthlyConveneInfoLocatorScriptResolution(
        root_locator=root_locator,
        monthly_root_capture_id=monthly_root_capture.capture_id,
        monthly_root_response_sha256=monthly_root_capture.response_sha256,
        target_date=target_date,
        raw_script_src=_SCRIPT_RAW.encode("ascii"),
        resolved_script_url=_SCRIPT_URL,
        offered_year_token=years[year_key],
        offered_month_token=months[month_key],
        structural_locator=_SCRIPT_STRUCTURAL_LOCATOR,
    )


def _script_literals(capture: _SupplierCapture) -> tuple[bytes, bytes]:
    if (
        capture.canonical_request_url != _SCRIPT_URL
        or len(capture.response_body) != _SCRIPT_LENGTH
        or capture.response_sha256 != _SCRIPT_SHA256
        or _hashlib.sha256(capture.response_body).hexdigest() != _SCRIPT_SHA256
    ):
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "locator script does not match the pinned qualified asset"
        )
    match = _JS_GRAMMAR.fullmatch(capture.response_body)
    if match is None:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "locator script grammar is outside the qualified profile"
        )
    return match.group("prefix"), match.group("separator")


def resolve_nar_monthly_convene_info_request_material(
    *,
    locator_script_resolution: NARMonthlyConveneInfoLocatorScriptResolution,
    locator_script_capture: _SupplierCapture,
) -> NARMonthlyConveneInfoRequestMaterialResolution:
    _require_script_resolution(locator_script_resolution)
    if type(locator_script_capture) is not _SupplierCapture:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "locator_script_capture must be NARMonthlyConveneInfoBootstrapSupplierCapture"
        )
    _reconstruct_capture(locator_script_capture, "locator_script_capture")
    if locator_script_capture.page_kind is not _PageKind.LOCATOR_SCRIPT:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "locator_script_capture has the wrong page kind"
        )
    if locator_script_capture.canonical_request_url != locator_script_resolution.resolved_script_url:
        raise NARMonthlyConveneInfoBootstrapIntegrityError(
            "locator script capture contradicts the source-bound script resolution"
        )
    prefix, separator = _script_literals(locator_script_capture)
    request_material = (
        prefix
        + locator_script_resolution.offered_year_token
        + separator
        + locator_script_resolution.offered_month_token
    )
    return NARMonthlyConveneInfoRequestMaterialResolution(
        locator_script_resolution=locator_script_resolution,
        locator_script_capture_id=locator_script_capture.capture_id,
        locator_script_response_sha256=locator_script_capture.response_sha256,
        official_supplied_request_material=request_material,
        resolved_request_url=_OFFICIAL_ORIGIN + request_material.decode("ascii"),
    )


def resolve_nar_monthly_convene_info_request_identity(
    *,
    target_date: _date,
    supplier_evidence: NARMonthlyConveneInfoBootstrapEvidence,
) -> _DailyTargetRequestIdentity:
    if type(target_date) is not _date:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "target_date must be exact date"
        )
    if target_date < _INITIAL_DATE:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "target_date precedes the qualified initial profile"
        )
    if type(supplier_evidence) is not NARMonthlyConveneInfoBootstrapEvidence:
        raise NARMonthlyConveneInfoBootstrapValidationError(
            "supplier_evidence must be NARMonthlyConveneInfoBootstrapEvidence"
        )
    _validate_integrity(supplier_evidence)
    root_locator = resolve_nar_monthly_convene_info_root_locator(
        homepage_capture=supplier_evidence.homepage_capture
    )
    script_resolution = resolve_nar_monthly_convene_info_locator_script(
        target_date=target_date,
        root_locator=root_locator,
        monthly_root_capture=supplier_evidence.monthly_root_capture,
    )
    material_resolution = resolve_nar_monthly_convene_info_request_material(
        locator_script_resolution=script_resolution,
        locator_script_capture=supplier_evidence.locator_script_capture,
    )
    request_material = material_resolution.official_supplied_request_material
    try:
        request = _DailyTargetRequestIdentity(
            _DailyTargetPageKind.MONTHLY_CONVENE_INFO,
            request_material,
            material_resolution.resolved_request_url,
            supplier_evidence.supplier_evidence_identity,
        )
    except (UnicodeDecodeError, _DailyTargetCaptureError) as error:
        raise NARMonthlyConveneInfoBootstrapUnsupportedError(
            "source-owned locator is rejected by the existing request identity"
        ) from error
    if (
        request.page_kind is not _DailyTargetPageKind.MONTHLY_CONVENE_INFO
        or request.official_supplied_request_material != request_material
        or request.target_year != target_date.year
        or request.target_month != target_date.month
        or request.supplier_evidence_identity
        != supplier_evidence.supplier_evidence_identity
    ):
        raise NARMonthlyConveneInfoBootstrapIntegrityError(
            "existing request identity contradicts the supplied source chain"
        )
    return request


if "annotations" in globals():
    del annotations
