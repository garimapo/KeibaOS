from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta, timezone
import hashlib
import inspect
import json
from pathlib import Path
from typing import get_type_hints

import pytest
import requests

from scripts.simulation import nar_race_entry_status_raw_capture as subject
from scripts.simulation.nar_race_entry_status_raw_capture import (
    NARRaceEntryStatusDayScope,
    NARRaceEntryStatusPageKind,
    NARRaceEntryStatusRaceIdentity,
    NARRaceEntryStatusRawCaptureBundle,
    NARRaceEntryStatusRawCaptureBundleIntegrityError,
    NARRaceEntryStatusRawCaptureError,
    NARRaceEntryStatusRawCaptureTransportError,
    NARRaceEntryStatusRawCaptureUnsupportedResponseError,
    NARRaceEntryStatusRawCaptureValidationError,
    NARRaceEntryStatusRawHTTPResponse,
    NARRaceEntryStatusRequestIdentity,
    NARRaceEntryStatusResponseCapture,
    RequestsNARRaceEntryStatusRawCaptureTransport,
    acquire_nar_race_entry_status_raw_capture_bundle,
    build_nar_race_entry_status_request_identity,
)


UTC = timezone.utc
RACE_DATE = date(2026, 9, 12)
BODY = "<html>\r\n地方競馬\n</html>".encode("utf-8")
CONTENT_TYPE = "text/html; charset=UTF-8"
REQUEST_PREFIX = "nar-race-entry-status-request-v1:"
CAPTURE_PREFIX = "nar-race-entry-status-capture-v1:"
BUNDLE_PREFIX = "nar-race-entry-status-raw-bundle-v1:"
MODULE_PATH = Path(subject.__file__)


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(payload: object) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _day() -> NARRaceEntryStatusDayScope:
    return NARRaceEntryStatusDayScope("23", RACE_DATE)


def _target(*, baba_code: str = "23", race_no: int = 3) -> NARRaceEntryStatusRaceIdentity:
    return NARRaceEntryStatusRaceIdentity(baba_code, RACE_DATE, race_no)


def _request(
    page_kind: NARRaceEntryStatusPageKind,
    *,
    baba_code: str = "23",
    race_no: int = 3,
) -> NARRaceEntryStatusRequestIdentity:
    return build_nar_race_entry_status_request_identity(
        page_kind=page_kind,
        day_scope=NARRaceEntryStatusDayScope(baba_code, RACE_DATE),
        request_race_no=(race_no if page_kind is NARRaceEntryStatusPageKind.DEBA_TABLE else None),
    )


def _raw(
    request: NARRaceEntryStatusRequestIdentity,
    *,
    body: bytes = BODY,
    content_type: str | None = CONTENT_TYPE,
    content_encoding: str | None = None,
    status: int = 200,
    effective_url: str | None = None,
    content_length: int | None = None,
    http_date: str | None = None,
    etag: str | None = None,
    last_modified: str | None = None,
) -> NARRaceEntryStatusRawHTTPResponse:
    return NARRaceEntryStatusRawHTTPResponse(
        effective_url=effective_url or request.canonical_request_url,
        response_body=body,
        http_status=status,
        content_type=content_type,
        content_encoding=content_encoding,
        http_date=http_date,
        etag=etag,
        last_modified=last_modified,
        content_length=content_length,
    )


def _capture(
    request: NARRaceEntryStatusRequestIdentity,
    *,
    body: bytes = BODY,
    offset: int = 0,
    content_length: int | None = None,
    http_date: str | None = None,
    etag: str | None = None,
    last_modified: str | None = None,
) -> NARRaceEntryStatusResponseCapture:
    start = datetime(2026, 9, 12, 1, 2, offset, 123456, tzinfo=UTC)
    return NARRaceEntryStatusResponseCapture(
        request_identity=request,
        effective_url=request.canonical_request_url,
        response_body=body,
        charset="UTF-8",
        requested_at=start,
        observed_at=start + timedelta(microseconds=1),
        captured_at=start + timedelta(microseconds=2),
        http_status=200,
        content_type=CONTENT_TYPE,
        content_encoding=None,
        http_date=http_date,
        etag=etag,
        last_modified=last_modified,
        content_length=content_length,
    )


def _bundle() -> NARRaceEntryStatusRawCaptureBundle:
    return NARRaceEntryStatusRawCaptureBundle(
        target_race_identity=_target(),
        deba_table_capture=_capture(_request(NARRaceEntryStatusPageKind.DEBA_TABLE), offset=0),
        race_list_capture=_capture(_request(NARRaceEntryStatusPageKind.RACE_LIST), offset=3),
    )


def test_public_api_is_exactly_frozen() -> None:
    assert set(subject.__all__) == {
        "NARRaceEntryStatusDayScope",
        "NARRaceEntryStatusPageKind",
        "NARRaceEntryStatusRaceIdentity",
        "NARRaceEntryStatusRawCaptureBundle",
        "NARRaceEntryStatusRawCaptureBundleIntegrityError",
        "NARRaceEntryStatusRawCaptureClock",
        "NARRaceEntryStatusRawCaptureError",
        "NARRaceEntryStatusRawCaptureTransport",
        "NARRaceEntryStatusRawCaptureTransportError",
        "NARRaceEntryStatusRawCaptureUnsupportedResponseError",
        "NARRaceEntryStatusRawCaptureValidationError",
        "NARRaceEntryStatusRawHTTPResponse",
        "NARRaceEntryStatusRequestIdentity",
        "NARRaceEntryStatusResponseCapture",
        "RequestsNARRaceEntryStatusRawCaptureTransport",
        "acquire_nar_race_entry_status_raw_capture_bundle",
        "build_nar_race_entry_status_request_identity",
    }


def test_exception_hierarchy_is_exact() -> None:
    assert NARRaceEntryStatusRawCaptureError.__bases__ == (Exception,)
    for error_type in (
        NARRaceEntryStatusRawCaptureValidationError,
        NARRaceEntryStatusRawCaptureTransportError,
        NARRaceEntryStatusRawCaptureUnsupportedResponseError,
        NARRaceEntryStatusRawCaptureBundleIntegrityError,
    ):
        assert error_type.__bases__ == (NARRaceEntryStatusRawCaptureError,)


def test_deba_request_has_exact_url_payload_and_identity() -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    assert request.canonical_request_url == (
        "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable"
        "?k_babaCode=23&k_raceDate=2026%2F09%2F12&k_raceNo=3"
    )
    payload = {
        "canonical_request_url": request.canonical_request_url,
        "http_method": "GET",
        "organization": "NAR",
        "page_kind": "deba_table",
        "request_scope": {
            "baba_code": "23",
            "race_date": "2026-09-12",
            "race_no": 3,
            "scope_kind": "race",
        },
        "schema_version": 1,
        "source_system": "keiba.go.jp",
    }
    assert request.request_identity_sha256 == _digest(payload)
    assert request.request_identity == REQUEST_PREFIX + _digest(payload)


def test_race_list_request_has_exact_day_scope_url_payload_and_identity() -> None:
    request = _request(NARRaceEntryStatusPageKind.RACE_LIST)
    assert request.canonical_request_url == (
        "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/RaceList"
        "?k_raceDate=2026%2F09%2F12&k_babaCode=23"
    )
    assert "k_raceNo" not in request.canonical_request_url
    payload = {
        "canonical_request_url": request.canonical_request_url,
        "http_method": "GET",
        "organization": "NAR",
        "page_kind": "race_list",
        "request_scope": {
            "baba_code": "23",
            "race_date": "2026-09-12",
            "scope_kind": "venue_day",
        },
        "schema_version": 1,
        "source_system": "keiba.go.jp",
    }
    assert "race_no" not in payload["request_scope"]
    assert request.request_identity_sha256 == _digest(payload)
    assert request.request_identity == REQUEST_PREFIX + _digest(payload)


def test_request_identity_is_deterministic_and_scope_sensitive() -> None:
    assert _request(NARRaceEntryStatusPageKind.DEBA_TABLE) == _request(
        NARRaceEntryStatusPageKind.DEBA_TABLE,
    )
    assert _request(NARRaceEntryStatusPageKind.DEBA_TABLE).request_identity != _request(
        NARRaceEntryStatusPageKind.DEBA_TABLE,
        race_no=4,
    ).request_identity
    assert _request(NARRaceEntryStatusPageKind.DEBA_TABLE).request_identity != _request(
        NARRaceEntryStatusPageKind.RACE_LIST,
    ).request_identity


@pytest.mark.parametrize("field", ["canonical_request_url", "request_identity_sha256", "request_identity"])
def test_request_derived_fields_cannot_be_injected(field: str) -> None:
    arguments = {
        "page_kind": NARRaceEntryStatusPageKind.DEBA_TABLE,
        "day_scope": _day(),
        "request_race_no": 3,
        field: "forged",
    }
    with pytest.raises(TypeError):
        NARRaceEntryStatusRequestIdentity(**arguments)


def test_request_is_frozen_and_forged_derived_state_fails_closed() -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    with pytest.raises(FrozenInstanceError):
        request.canonical_request_url = "forged"  # type: ignore[misc]
    object.__setattr__(request, "request_identity", REQUEST_PREFIX + "0" * 64)
    with pytest.raises(NARRaceEntryStatusRawCaptureValidationError):
        _capture(request)


@pytest.mark.parametrize("baba_code", ["", "0", "01", "+23", "２３", 23, True])
def test_invalid_baba_code_fails_closed(baba_code: object) -> None:
    with pytest.raises(NARRaceEntryStatusRawCaptureValidationError):
        NARRaceEntryStatusDayScope(baba_code, RACE_DATE)  # type: ignore[arg-type]


@pytest.mark.parametrize("race_no", [True, False, 0, -1, 1.0, "1"])
def test_invalid_race_number_fails_closed(race_no: object) -> None:
    with pytest.raises(NARRaceEntryStatusRawCaptureValidationError):
        NARRaceEntryStatusRaceIdentity("23", RACE_DATE, race_no)  # type: ignore[arg-type]


def test_datetime_is_not_accepted_as_race_date() -> None:
    with pytest.raises(NARRaceEntryStatusRawCaptureValidationError):
        NARRaceEntryStatusDayScope("23", datetime(2026, 9, 12, tzinfo=UTC))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("page_kind", "race_no"),
    [
        (NARRaceEntryStatusPageKind.DEBA_TABLE, None),
        (NARRaceEntryStatusPageKind.RACE_LIST, 3),
        ("deba_table", 3),
    ],
)
def test_wrong_page_scope_pairing_fails_closed(page_kind: object, race_no: object) -> None:
    with pytest.raises(NARRaceEntryStatusRawCaptureValidationError):
        build_nar_race_entry_status_request_identity(
            page_kind=page_kind,  # type: ignore[arg-type]
            day_scope=_day(),
            request_race_no=race_no,  # type: ignore[arg-type]
        )


def test_capture_preserves_raw_bytes_and_literal_identity_payload() -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    body = "<html>\r\n出走情報\n</html>".encode("utf-8")
    capture = _capture(
        request,
        body=body,
        content_length=len(body),
        http_date="Sat, 12 Sep 2026 01:02:03 GMT",
        etag='"abc"',
        last_modified="Sat, 12 Sep 2026 00:00:00 GMT",
    )
    response_sha = hashlib.sha256(body).hexdigest()
    payload = {
        "captured_at": "2026-09-12T01:02:00.123458Z",
        "charset": "UTF-8",
        "effective_url": request.canonical_request_url,
        "http_status": 200,
        "observed_at": "2026-09-12T01:02:00.123457Z",
        "organization": "NAR",
        "request_identity": request.request_identity,
        "request_identity_sha256": request.request_identity_sha256,
        "requested_at": "2026-09-12T01:02:00.123456Z",
        "response_byte_length": len(body),
        "response_sha256": response_sha,
        "retained_http_metadata": {
            "content_encoding": None,
            "content_length": len(body),
            "content_type": CONTENT_TYPE,
            "date": "Sat, 12 Sep 2026 01:02:03 GMT",
            "etag": '"abc"',
            "last_modified": "Sat, 12 Sep 2026 00:00:00 GMT",
        },
        "schema_version": 1,
        "source_system": "keiba.go.jp",
    }
    assert capture.response_body == body
    assert capture.response_sha256 == response_sha
    assert capture.byte_length == len(body)
    assert capture.capture_sha256 == _digest(payload)
    assert capture.capture_id == CAPTURE_PREFIX + _digest(payload)


def test_capture_normalizes_aware_datetime_to_utc_six_digits() -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    jst = timezone(timedelta(hours=9))
    start = datetime(2026, 9, 12, 10, 2, 0, tzinfo=jst)
    capture = NARRaceEntryStatusResponseCapture(
        request_identity=request,
        effective_url=request.canonical_request_url,
        response_body=BODY,
        charset="UTF-8",
        requested_at=start,
        observed_at=start,
        captured_at=start,
        http_status=200,
        content_type=CONTENT_TYPE,
    )
    assert capture.requested_at == datetime(2026, 9, 12, 1, 2, tzinfo=UTC)
    expected_fragment = b'"requested_at":"2026-09-12T01:02:00.000000Z"'
    payload = {
        "captured_at": "2026-09-12T01:02:00.000000Z",
        "charset": "UTF-8",
        "effective_url": request.canonical_request_url,
        "http_status": 200,
        "observed_at": "2026-09-12T01:02:00.000000Z",
        "organization": "NAR",
        "request_identity": request.request_identity,
        "request_identity_sha256": request.request_identity_sha256,
        "requested_at": "2026-09-12T01:02:00.000000Z",
        "response_byte_length": len(BODY),
        "response_sha256": hashlib.sha256(BODY).hexdigest(),
        "retained_http_metadata": {
            "content_encoding": None,
            "content_length": None,
            "content_type": CONTENT_TYPE,
            "date": None,
            "etag": None,
            "last_modified": None,
        },
        "schema_version": 1,
        "source_system": "keiba.go.jp",
    }
    assert expected_fragment in _canonical_bytes(payload)
    assert capture.capture_sha256 == _digest(payload)


def test_capture_identity_changes_with_body_or_timestamp() -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    original = _capture(request)
    assert original.capture_id != _capture(request, body=BODY + b"x").capture_id
    assert original.capture_id != _capture(request, offset=1).capture_id
    assert original == _capture(request)


@pytest.mark.parametrize("bad_time", [datetime(2026, 9, 12, 1, 2), "2026-09-12T01:02:00Z"])
def test_capture_rejects_naive_or_non_datetime_timestamp(bad_time: object) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    good = datetime(2026, 9, 12, 1, 2, tzinfo=UTC)
    with pytest.raises(NARRaceEntryStatusRawCaptureValidationError):
        NARRaceEntryStatusResponseCapture(
            request_identity=request,
            effective_url=request.canonical_request_url,
            response_body=BODY,
            charset="UTF-8",
            requested_at=bad_time,  # type: ignore[arg-type]
            observed_at=good,
            captured_at=good,
            http_status=200,
            content_type=CONTENT_TYPE,
        )


def test_capture_rejects_timestamp_regression() -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    start = datetime(2026, 9, 12, 1, 2, tzinfo=UTC)
    with pytest.raises(NARRaceEntryStatusRawCaptureValidationError):
        NARRaceEntryStatusResponseCapture(
            request_identity=request,
            effective_url=request.canonical_request_url,
            response_body=BODY,
            charset="UTF-8",
            requested_at=start,
            observed_at=start - timedelta(seconds=1),
            captured_at=start,
            http_status=200,
            content_type=CONTENT_TYPE,
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"status": 404},
        {"effective_url": "https://www.keiba.go.jp/wrong"},
        {"content_type": "text/html;charset=UTF-8"},
        {"content_type": "text/html; charset=utf-8"},
        {"content_type": None},
        {"content_encoding": "gzip"},
        {"body": b""},
        {"body": b"\xff"},
    ],
)
def test_capture_rejects_unsupported_response_profiles(changes: dict[str, object]) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    raw = _raw(request, **changes)  # type: ignore[arg-type]
    start = datetime(2026, 9, 12, 1, 2, tzinfo=UTC)
    with pytest.raises(NARRaceEntryStatusRawCaptureUnsupportedResponseError):
        NARRaceEntryStatusResponseCapture(
            request_identity=request,
            effective_url=raw.effective_url,
            response_body=raw.response_body,
            charset="UTF-8",
            requested_at=start,
            observed_at=start,
            captured_at=start,
            http_status=raw.http_status,
            content_type=raw.content_type,
            content_encoding=raw.content_encoding,
        )


def test_capture_rejects_wrong_charset_and_declared_length() -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    base = dict(
        request_identity=request,
        effective_url=request.canonical_request_url,
        response_body=BODY,
        requested_at=datetime(2026, 9, 12, 1, 2, tzinfo=UTC),
        observed_at=datetime(2026, 9, 12, 1, 2, tzinfo=UTC),
        captured_at=datetime(2026, 9, 12, 1, 2, tzinfo=UTC),
        http_status=200,
        content_type=CONTENT_TYPE,
    )
    with pytest.raises(NARRaceEntryStatusRawCaptureUnsupportedResponseError):
        NARRaceEntryStatusResponseCapture(charset="utf-8", **base)
    with pytest.raises(NARRaceEntryStatusRawCaptureUnsupportedResponseError):
        NARRaceEntryStatusResponseCapture(charset="UTF-8", content_length=len(BODY) + 1, **base)


def test_bundle_literal_payload_and_identity_are_exact() -> None:
    bundle = _bundle()
    deba = bundle.deba_table_capture
    race_list = bundle.race_list_capture
    payload = {
        "acquisition_algorithm": {
            "name": "nar-race-entry-status-raw-bundle",
            "order": ["deba_table", "race_list"],
            "version": "v1",
        },
        "deba_table": {
            "capture_id": deba.capture_id,
            "captured_at": "2026-09-12T01:02:00.123458Z",
            "observed_at": "2026-09-12T01:02:00.123457Z",
            "request_identity_sha256": deba.request_identity.request_identity_sha256,
            "requested_at": "2026-09-12T01:02:00.123456Z",
            "response_sha256": deba.response_sha256,
        },
        "organization": "NAR",
        "race_list": {
            "capture_id": race_list.capture_id,
            "captured_at": "2026-09-12T01:02:03.123458Z",
            "observed_at": "2026-09-12T01:02:03.123457Z",
            "request_identity_sha256": race_list.request_identity.request_identity_sha256,
            "requested_at": "2026-09-12T01:02:03.123456Z",
            "response_sha256": race_list.response_sha256,
        },
        "schema_version": 1,
        "source_system": "keiba.go.jp",
        "target_race": {"baba_code": "23", "race_date": "2026-09-12", "race_no": 3},
    }
    assert bundle.bundle_sha256 == _digest(payload)
    assert bundle.bundle_id == BUNDLE_PREFIX + _digest(payload)
    assert bundle == _bundle()


def test_bundle_identity_changes_when_either_child_capture_changes() -> None:
    original = _bundle()
    changed_deba = NARRaceEntryStatusRawCaptureBundle(
        target_race_identity=_target(),
        deba_table_capture=_capture(
            _request(NARRaceEntryStatusPageKind.DEBA_TABLE),
            body=BODY + b"x",
            offset=0,
        ),
        race_list_capture=original.race_list_capture,
    )
    changed_race = NARRaceEntryStatusRawCaptureBundle(
        target_race_identity=_target(),
        deba_table_capture=original.deba_table_capture,
        race_list_capture=_capture(
            _request(NARRaceEntryStatusPageKind.RACE_LIST),
            body=BODY + b"x",
            offset=3,
        ),
    )
    assert len({original.bundle_id, changed_deba.bundle_id, changed_race.bundle_id}) == 3


def test_bundle_rejects_wrong_page_member_scope_and_cross_document_time() -> None:
    deba = _capture(_request(NARRaceEntryStatusPageKind.DEBA_TABLE), offset=0)
    race_list = _capture(_request(NARRaceEntryStatusPageKind.RACE_LIST), offset=3)
    with pytest.raises(NARRaceEntryStatusRawCaptureBundleIntegrityError):
        NARRaceEntryStatusRawCaptureBundle(_target(), race_list, race_list)
    with pytest.raises(NARRaceEntryStatusRawCaptureBundleIntegrityError):
        NARRaceEntryStatusRawCaptureBundle(_target(race_no=4), deba, race_list)
    late_deba = _capture(_request(NARRaceEntryStatusPageKind.DEBA_TABLE), offset=4)
    with pytest.raises(NARRaceEntryStatusRawCaptureBundleIntegrityError):
        NARRaceEntryStatusRawCaptureBundle(_target(), late_deba, race_list)


class _RawHeaders:
    def __init__(self, lengths: object) -> None:
        self.lengths = lengths

    def getlist(self, name: str) -> object:
        assert name == "Content-Length"
        return self.lengths


class _RawStream:
    def __init__(self, body: bytes, lengths: object) -> None:
        self.body = body
        self.headers = _RawHeaders(lengths)
        self.decode_content: bool | None = None
        self.stream_calls: list[tuple[int, bool]] = []

    def stream(self, *, amt: int, decode_content: bool) -> list[bytes]:
        self.stream_calls.append((amt, decode_content))
        return [self.body]


class _HTTPResponse:
    def __init__(
        self,
        url: str,
        *,
        body: bytes = BODY,
        lengths: object = None,
        status: int = 200,
        content_type: str | None = CONTENT_TYPE,
        content_encoding: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status
        self.url = url
        self.raw = _RawStream(body, [] if lengths is None else lengths)
        self.headers = {
            "Content-Type": content_type,
            "Content-Encoding": content_encoding,
            "Date": "Sat, 12 Sep 2026 01:02:03 GMT",
            "ETag": '"abc"',
            "Last-Modified": "Sat, 12 Sep 2026 00:00:00 GMT",
        }
        if extra_headers:
            self.headers.update(extra_headers)
        self.closed = False

    def close(self) -> None:
        self.closed = True


class _Session:
    def __init__(self, response: _HTTPResponse | Exception) -> None:
        self.response = response
        self.trust_env = True
        self.headers: dict[str, str] = {"Default": "header"}
        self.mounts: list[tuple[str, object]] = []
        self.get_calls: list[tuple[str, dict[str, object]]] = []
        self.closed = False

    def mount(self, prefix: str, adapter: object) -> None:
        self.mounts.append((prefix, adapter))

    def get(self, url: str, **options: object) -> _HTTPResponse:
        self.get_calls.append((url, options))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response

    def close(self) -> None:
        self.closed = True


def _install_session(monkeypatch: pytest.MonkeyPatch, response: _HTTPResponse | Exception) -> _Session:
    session = _Session(response)
    monkeypatch.setattr(subject._requests, "Session", lambda: session)
    return session


def test_concrete_transport_uses_exact_options_and_preserves_raw_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    response = _HTTPResponse(
        request.canonical_request_url,
        lengths=[str(len(BODY))],
        extra_headers={"Set-Cookie": "secret", "X-Request-Id": "secret"},
    )
    session = _install_session(monkeypatch, response)
    raw = RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)
    assert raw.response_body == BODY
    assert raw.content_length == len(BODY)
    assert raw.http_date == "Sat, 12 Sep 2026 01:02:03 GMT"
    assert raw.etag == '"abc"'
    assert not hasattr(raw, "set_cookie") and not hasattr(raw, "headers")
    assert session.trust_env is False
    assert session.headers == {}
    assert len(session.mounts) == 1 and session.mounts[0][0] == "https://"
    adapter = session.mounts[0][1]
    assert adapter.max_retries.total == 0  # type: ignore[attr-defined]
    assert session.get_calls == [
        (
            request.canonical_request_url,
            {
                "headers": {
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Encoding": "identity",
                },
                "stream": True,
                "allow_redirects": False,
                "verify": True,
                "timeout": (10.0, 20.0),
            },
        ),
    ]
    assert response.raw.decode_content is False
    assert response.raw.stream_calls == [(64 * 1024, False)]
    assert response.closed and session.closed


@pytest.mark.parametrize("encoding", [None, "identity"])
def test_concrete_transport_accepts_only_absent_or_identity_encoding(
    monkeypatch: pytest.MonkeyPatch,
    encoding: str | None,
) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    response = _HTTPResponse(request.canonical_request_url, content_encoding=encoding)
    _install_session(monkeypatch, response)
    assert RequestsNARRaceEntryStatusRawCaptureTransport().fetch(
        request_identity=request,
    ).content_encoding == encoding


@pytest.mark.parametrize("length", ["00", "01", " 1", "1 ", "\t1", "1\t", "+1", "-1", "1,1", "1.0", "1e1", "", "１"])
def test_content_length_malformed_text_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    length: str,
) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    session = _install_session(monkeypatch, _HTTPResponse(request.canonical_request_url, lengths=[length]))
    with pytest.raises(NARRaceEntryStatusRawCaptureUnsupportedResponseError):
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)
    assert session.closed


@pytest.mark.parametrize("lengths", [[str(len(BODY)), str(len(BODY))], ["1", "2"]])
def test_duplicate_content_length_always_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    lengths: list[str],
) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    _install_session(monkeypatch, _HTTPResponse(request.canonical_request_url, lengths=lengths))
    with pytest.raises(NARRaceEntryStatusRawCaptureUnsupportedResponseError):
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)


def test_missing_or_unreliable_raw_getlist_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    response = _HTTPResponse(request.canonical_request_url)
    response.raw.headers = object()
    _install_session(monkeypatch, response)
    with pytest.raises(NARRaceEntryStatusRawCaptureTransportError):
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)
    response = _HTTPResponse(request.canonical_request_url)
    response.raw.headers = _RawHeaders((str(len(BODY)),))
    _install_session(monkeypatch, response)
    with pytest.raises(NARRaceEntryStatusRawCaptureTransportError):
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)


def test_content_length_absent_and_valid_positive_are_canonical(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    _install_session(monkeypatch, _HTTPResponse(request.canonical_request_url, lengths=[]))
    assert RequestsNARRaceEntryStatusRawCaptureTransport().fetch(
        request_identity=request,
    ).content_length is None
    _install_session(
        monkeypatch,
        _HTTPResponse(request.canonical_request_url, lengths=[str(len(BODY))]),
    )
    assert RequestsNARRaceEntryStatusRawCaptureTransport().fetch(
        request_identity=request,
    ).content_length == len(BODY)


def test_content_length_zero_and_length_mismatch_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    _install_session(monkeypatch, _HTTPResponse(request.canonical_request_url, body=b"", lengths=["0"]))
    with pytest.raises(NARRaceEntryStatusRawCaptureUnsupportedResponseError):
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)
    _install_session(monkeypatch, _HTTPResponse(request.canonical_request_url, lengths=["1"]))
    with pytest.raises(NARRaceEntryStatusRawCaptureUnsupportedResponseError):
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)


def test_per_document_body_limit_is_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    exact = b"x" * (4 * 1024 * 1024)
    _install_session(monkeypatch, _HTTPResponse(request.canonical_request_url, body=exact, lengths=[str(len(exact))]))
    assert len(
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(
            request_identity=request,
        ).response_body,
    ) == len(exact)
    oversized = exact + b"x"
    _install_session(monkeypatch, _HTTPResponse(request.canonical_request_url, body=oversized, lengths=[]))
    with pytest.raises(NARRaceEntryStatusRawCaptureUnsupportedResponseError):
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)


@pytest.mark.parametrize(
    "response_options",
    [
        {"status": 500},
        {"content_type": "text/plain; charset=UTF-8"},
        {"content_type": "text/html; charset=utf-8"},
        {"content_type": None},
        {"content_encoding": "gzip"},
    ],
)
def test_concrete_transport_rejects_response_profile(
    monkeypatch: pytest.MonkeyPatch,
    response_options: dict[str, object],
) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    _install_session(monkeypatch, _HTTPResponse(request.canonical_request_url, **response_options))  # type: ignore[arg-type]
    with pytest.raises(NARRaceEntryStatusRawCaptureUnsupportedResponseError):
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)


def test_concrete_transport_rejects_wrong_effective_url(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    _install_session(monkeypatch, _HTTPResponse("https://www.keiba.go.jp/wrong"))
    with pytest.raises(NARRaceEntryStatusRawCaptureUnsupportedResponseError):
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)


def test_requests_failure_is_translated_and_resources_close(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _install_session(monkeypatch, requests.Timeout("boom"))
    with pytest.raises(NARRaceEntryStatusRawCaptureTransportError) as caught:
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(
            request_identity=_request(NARRaceEntryStatusPageKind.DEBA_TABLE),
        )
    assert isinstance(caught.value.__cause__, requests.Timeout)
    assert session.closed


def test_cleanup_failure_is_translated_without_skipping_session_close(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request(NARRaceEntryStatusPageKind.DEBA_TABLE)
    response = _HTTPResponse(request.canonical_request_url)

    def broken_close() -> None:
        raise AttributeError("close failed")

    response.close = broken_close  # type: ignore[method-assign]
    session = _install_session(monkeypatch, response)
    with pytest.raises(NARRaceEntryStatusRawCaptureTransportError) as caught:
        RequestsNARRaceEntryStatusRawCaptureTransport().fetch(request_identity=request)
    assert isinstance(caught.value.__cause__, AttributeError)
    assert session.closed


class _Clock:
    def __init__(
        self,
        values: list[object] | None = None,
        *,
        fail_at: int | None = None,
    ) -> None:
        start = datetime(2026, 9, 12, 1, 0, tzinfo=UTC)
        self.values = values or [start + timedelta(seconds=index) for index in range(6)]
        self.fail_at = fail_at
        self.calls = 0

    def now_utc(self) -> object:
        self.calls += 1
        if self.calls == self.fail_at:
            raise ValueError("clock failed")
        return self.values[self.calls - 1]


class _Transport:
    def __init__(
        self,
        *,
        fail_at: int | None = None,
        invalid_at: int | None = None,
    ) -> None:
        self.fail_at = fail_at
        self.invalid_at = invalid_at
        self.calls: list[NARRaceEntryStatusRequestIdentity] = []

    def fetch(self, *, request_identity: NARRaceEntryStatusRequestIdentity) -> NARRaceEntryStatusRawHTTPResponse:
        self.calls.append(request_identity)
        index = len(self.calls)
        if index == self.fail_at:
            raise RuntimeError("transport failed")
        if index == self.invalid_at:
            return _raw(request_identity, content_type="text/plain; charset=UTF-8")
        return _raw(request_identity, content_length=len(BODY))


def test_acquisition_is_exactly_two_gets_in_order_with_six_clocks() -> None:
    transport = _Transport()
    clock = _Clock()
    bundle = acquire_nar_race_entry_status_raw_capture_bundle(
        target=_target(),
        transport=transport,
        clock=clock,
    )
    assert [request.page_kind for request in transport.calls] == [
        NARRaceEntryStatusPageKind.DEBA_TABLE,
        NARRaceEntryStatusPageKind.RACE_LIST,
    ]
    assert len(transport.calls) == 2
    assert clock.calls == 6
    assert bundle.deba_table_capture.captured_at <= bundle.race_list_capture.requested_at
    assert transport.calls[1].request_race_no is None


@pytest.mark.parametrize(
    ("failure_kind", "failure_at", "expected_clocks", "expected_gets", "expected_error"),
    [
        ("clock", 1, 1, 0, NARRaceEntryStatusRawCaptureValidationError),
        ("transport", 1, 1, 1, NARRaceEntryStatusRawCaptureTransportError),
        ("clock", 2, 2, 1, NARRaceEntryStatusRawCaptureValidationError),
        ("invalid", 1, 2, 1, NARRaceEntryStatusRawCaptureUnsupportedResponseError),
        ("clock", 3, 3, 1, NARRaceEntryStatusRawCaptureValidationError),
        ("clock", 4, 4, 1, NARRaceEntryStatusRawCaptureValidationError),
        ("transport", 2, 4, 2, NARRaceEntryStatusRawCaptureTransportError),
        ("clock", 5, 5, 2, NARRaceEntryStatusRawCaptureValidationError),
        ("invalid", 2, 5, 2, NARRaceEntryStatusRawCaptureUnsupportedResponseError),
        ("clock", 6, 6, 2, NARRaceEntryStatusRawCaptureValidationError),
    ],
)
def test_failure_paths_use_exact_clock_and_get_counts(
    failure_kind: str,
    failure_at: int,
    expected_clocks: int,
    expected_gets: int,
    expected_error: type[Exception],
) -> None:
    clock = _Clock(fail_at=failure_at if failure_kind == "clock" else None)
    transport = _Transport(
        fail_at=failure_at if failure_kind == "transport" else None,
        invalid_at=failure_at if failure_kind == "invalid" else None,
    )
    with pytest.raises(expected_error):
        acquire_nar_race_entry_status_raw_capture_bundle(
            target=_target(),
            transport=transport,
            clock=clock,
        )
    assert clock.calls == expected_clocks
    assert len(transport.calls) == expected_gets


def test_invalid_target_uses_zero_clock_and_zero_gets() -> None:
    target = object.__new__(NARRaceEntryStatusRaceIdentity)
    object.__setattr__(target, "baba_code", "0")
    object.__setattr__(target, "race_date", RACE_DATE)
    object.__setattr__(target, "race_no", 3)
    transport = _Transport()
    clock = _Clock()
    with pytest.raises(NARRaceEntryStatusRawCaptureValidationError):
        acquire_nar_race_entry_status_raw_capture_bundle(
            target=target,
            transport=transport,
            clock=clock,
        )
    assert clock.calls == 0
    assert transport.calls == []


def test_cross_document_timestamp_failure_occurs_after_six_clocks_and_two_gets() -> None:
    start = datetime(2026, 9, 12, 1, 0, tzinfo=UTC)
    values = [
        start,
        start + timedelta(seconds=1),
        start + timedelta(seconds=3),
        start + timedelta(seconds=2),
        start + timedelta(seconds=4),
        start + timedelta(seconds=5),
    ]
    clock = _Clock(values)
    transport = _Transport()
    with pytest.raises(NARRaceEntryStatusRawCaptureBundleIntegrityError):
        acquire_nar_race_entry_status_raw_capture_bundle(
            target=_target(),
            transport=transport,
            clock=clock,
        )
    assert clock.calls == 6
    assert len(transport.calls) == 2


def test_low_level_fake_transport_failures_are_translated() -> None:
    class BrokenTransport:
        def fetch(self, *, request_identity: NARRaceEntryStatusRequestIdentity) -> object:
            raise AttributeError("broken")

    with pytest.raises(NARRaceEntryStatusRawCaptureTransportError) as caught:
        acquire_nar_race_entry_status_raw_capture_bundle(
            target=_target(),
            transport=BrokenTransport(),
            clock=_Clock(),
        )
    assert isinstance(caught.value.__cause__, AttributeError)


def test_acquisition_api_has_no_current_date_or_url_default() -> None:
    signature = inspect.signature(acquire_nar_race_entry_status_raw_capture_bundle)
    assert list(signature.parameters) == ["target", "transport", "clock"]
    assert all(parameter.default is inspect.Parameter.empty for parameter in signature.parameters.values())
    builder = inspect.signature(build_nar_race_entry_status_request_identity)
    assert list(builder.parameters) == ["page_kind", "day_scope", "request_race_no"]
    assert all(parameter.default is inspect.Parameter.empty for parameter in builder.parameters.values())


def test_static_boundary_has_no_parser_persistence_clock_or_other_provider() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert not imported_roots.intersection(
        {"bs4", "lxml", "sqlite3", "pathlib", "urllib", "selenium", "playwright"},
    )
    lowered = source.lower()
    for forbidden in (
        "horseNum",
        "td.horseNum",
        "出走取消",
        "beautifulsoup",
        "datetime.now",
        "datetime.utcnow",
        "open(",
        "sqlite",
        "jra",
        "keiba.db",
    ):
        assert forbidden.lower() not in lowered


def test_models_are_frozen_and_closed_bundle_has_no_optional_member() -> None:
    bundle = _bundle()
    with pytest.raises(FrozenInstanceError):
        bundle.bundle_id = "forged"  # type: ignore[misc]
    annotations = get_type_hints(NARRaceEntryStatusRawCaptureBundle)
    assert annotations["deba_table_capture"] is NARRaceEntryStatusResponseCapture
    assert annotations["race_list_capture"] is NARRaceEntryStatusResponseCapture
