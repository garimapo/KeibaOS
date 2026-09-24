"""Read-only, local runtime dependency and standard NAR transport descriptors."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from hashlib import sha256
import importlib
import inspect
import platform
import sqlite3
import sys
import textwrap

import requests
import urllib3

from scripts.simulation.nar_operational_timing_observability import (
    NARHTTPTransportKind, NARHTTPTransportProfile, _json_bytes, _read_json,
)
from scripts.simulation.nar_operational_timing_observability_v2 import (
    NAROperationalTimingMeasurementConfigurationV2 as Configuration,
)


@dataclass(frozen=True, slots=True)
class NARRuntimeDependencyProfile:
    python_implementation: str
    python_version: str
    requests_version: str
    urllib3_version: str
    sqlite_version: str
    platform_name: str
    platform_release: str
    platform_version: str
    architecture: str
    schema_version: int = 1
    profile_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        values = (self.python_implementation, self.python_version, self.requests_version,
                  self.urllib3_version, self.sqlite_version, self.platform_name,
                  self.platform_release, self.platform_version, self.architecture)
        if (any(type(x) is not str or not x for x in values)
                or type(self.schema_version) is not int or self.schema_version != 1):
            raise ValueError("runtime dependency profile is incomplete")
        object.__setattr__(self, "profile_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def profile_identity(self) -> str:
        return "nar-runtime-dependency-profile-v1:" + self.profile_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version,
                **{name: getattr(self, name) for name in (
                    "python_implementation", "python_version", "requests_version",
                    "urllib3_version", "sqlite_version", "platform_name",
                    "platform_release", "platform_version", "architecture")}}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NARRuntimeDependencyProfile:
        p = _read_json(value)
        result = cls(**p)
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("dependency profile JSON is not canonical")
        return result


def derive_runtime_dependency_profile() -> NARRuntimeDependencyProfile:
    return NARRuntimeDependencyProfile(
        platform.python_implementation(), platform.python_version(), requests.__version__,
        urllib3.__version__, sqlite3.sqlite_version, sys.platform, platform.release(),
        platform.version(), platform.machine(),
    )


@dataclass(frozen=True, slots=True)
class NARStaticHTTPTransportDescriptor:
    kind: NARHTTPTransportKind
    connect_timeout_microseconds: int
    read_timeout_microseconds: int
    adapter_retry_total: int
    adapter_retry_read: bool
    adapter_backoff_microseconds: int
    allow_redirects: bool
    verify_tls: bool
    stream: bool
    accept_encoding: str
    trust_env: bool

    def __post_init__(self) -> None:
        if (type(self.kind) is not NARHTTPTransportKind
                or type(self.connect_timeout_microseconds) is not int or self.connect_timeout_microseconds <= 0
                or type(self.read_timeout_microseconds) is not int or self.read_timeout_microseconds <= 0
                or type(self.adapter_retry_total) is not int or self.adapter_retry_total != 0
                or type(self.adapter_retry_read) is not bool or self.adapter_retry_read is not False
                or type(self.adapter_backoff_microseconds) is not int or self.adapter_backoff_microseconds != 0
                or type(self.allow_redirects) is not bool or self.allow_redirects is not False
                or type(self.verify_tls) is not bool or self.verify_tls is not True
                or type(self.stream) is not bool or self.stream is not True
                or type(self.accept_encoding) is not str or self.accept_encoding != "identity"
                or type(self.trust_env) is not bool):
            raise ValueError("unsupported static NAR transport descriptor")

    def payload(self) -> dict[str, object]:
        return {name: (getattr(self, name).value if name == "kind" else getattr(self, name))
                for name in ("kind", "connect_timeout_microseconds", "read_timeout_microseconds",
                             "adapter_retry_total", "adapter_retry_read", "adapter_backoff_microseconds",
                             "allow_redirects", "verify_tls", "stream", "accept_encoding", "trust_env")}


@dataclass(frozen=True, slots=True)
class NARStaticRuntimeTransportProfile:
    descriptors: tuple[NARStaticHTTPTransportDescriptor, ...]
    schema_version: int = 1
    profile_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if (type(self.descriptors) is not tuple
                or len(self.descriptors) != len(NARHTTPTransportKind)
                or any(type(x) is not NARStaticHTTPTransportDescriptor for x in self.descriptors)
                or {x.kind for x in self.descriptors} != set(NARHTTPTransportKind)
                or type(self.schema_version) is not int or self.schema_version != 1):
            raise ValueError("static transport profile lacks an exact transport family")
        object.__setattr__(self, "descriptors", tuple(next(x for x in self.descriptors if x.kind is kind)
                                                    for kind in NARHTTPTransportKind))
        object.__setattr__(self, "profile_sha256", sha256(self.canonical_bytes()).hexdigest())

    @property
    def profile_identity(self) -> str:
        return "nar-static-runtime-transport-profile-v1:" + self.profile_sha256

    def payload(self) -> dict[str, object]:
        return {"schema_version": self.schema_version,
                "semantic": "STATIC_RUNTIME_TRANSPORT_PROFILE_NOT_REQUEST_EFFECTIVE_ENVIRONMENT",
                "descriptors": [x.payload() for x in self.descriptors]}

    def canonical_bytes(self) -> bytes:
        return _json_bytes(self.payload())

    @classmethod
    def from_json(cls, value: str) -> NARStaticRuntimeTransportProfile:
        p = _read_json(value)
        descriptors = tuple(NARStaticHTTPTransportDescriptor(
            NARHTTPTransportKind(x["kind"]), x["connect_timeout_microseconds"],
            x["read_timeout_microseconds"], x["adapter_retry_total"],
            x["adapter_retry_read"], x["adapter_backoff_microseconds"],
            x["allow_redirects"], x["verify_tls"], x["stream"],
            x["accept_encoding"], x["trust_env"]) for x in p["descriptors"])
        result = cls(descriptors, p["schema_version"])
        if result.canonical_bytes() != value.encode("utf-8"):
            raise ValueError("static transport profile JSON is not canonical")
        return result

    def require_matches_declared(self, configuration: Configuration) -> None:
        if type(configuration) is not Configuration:
            raise ValueError("exact V2 configuration required")
        actual = {x.kind: x for x in self.descriptors}
        for declared in configuration.transport_profiles:
            value = actual[declared.kind]
            if ((value.connect_timeout_microseconds, value.read_timeout_microseconds)
                    != (declared.connect_timeout_microseconds, declared.read_timeout_microseconds)):
                raise ValueError("declared/runtime transport timeout mismatch")
        if (configuration.max_retries != 0 or configuration.backoff_microseconds != 0
                or any(x.adapter_retry_total != 0 or x.adapter_backoff_microseconds != 0
                       for x in self.descriptors)):
            raise ValueError("declared/runtime retry mismatch")


def _request_literals(fetch: object, module: object) -> tuple[bool, bool, bool, str]:
    """Reject drift in the fixed Session.get request flags without issuing HTTP."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(fetch)))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == "get"
             and ((isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "_session")
                  or (isinstance(node.func.value, ast.Name) and node.func.value.id == "session"))]
    if len(calls) != 1:
        raise ValueError("standard transport Session.get boundary changed")
    kwargs = {x.arg: x.value for x in calls[0].keywords}
    try:
        redirects = ast.literal_eval(kwargs["allow_redirects"])
        tls = ast.literal_eval(kwargs["verify"])
        stream = ast.literal_eval(kwargs["stream"])
        header_node = kwargs["headers"]
        if (isinstance(header_node, ast.Call) and isinstance(header_node.func, ast.Name)
                and header_node.func.id == "dict" and len(header_node.args) == 1
                and isinstance(header_node.args[0], ast.Name)
                and header_node.args[0].id == "_REQUEST_HEADERS"):
            headers = getattr(module, "_REQUEST_HEADERS")
        else:
            headers = ast.literal_eval(header_node)
        timeout = kwargs["timeout"]
    except (KeyError, ValueError, TypeError, SyntaxError) as error:
        raise ValueError("standard transport request flags changed") from error
    if (not isinstance(timeout, ast.Tuple) or len(timeout.elts) != 2
            or [getattr(x, "id", None) for x in timeout.elts]
            != ["_CONNECT_TIMEOUT_SECONDS", "_READ_TIMEOUT_SECONDS"]
            or type(headers) is not dict or headers.get("Accept-Encoding") != "identity"):
        raise ValueError("standard transport timeout/encoding boundary changed")
    return redirects, tls, stream, headers["Accept-Encoding"]


_STANDARD = (
    ("nar_historical_daily_target_bootstrap_live_capture", "RequestsNARMonthlyConveneInfoBootstrapHTTPTransport", NARHTTPTransportKind.NAR_BOOTSTRAP_HTTP),
    ("nar_historical_daily_target_live_capture", "_RequestsNARHistoricalDailyTargetHTTPTransport", NARHTTPTransportKind.NAR_DAILY_TARGET_HTTP),
    ("nar_official_response_live_capture", "_RequestsNAROfficialHTTPTransport", NARHTTPTransportKind.NAR_OFFICIAL_RESPONSE_HTTP),
    ("nar_market_odds_raw_acquisition", "RequestsNARMarketOddsRawAcquisitionTransport", NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP),
)


def derive_static_runtime_transport_profile() -> NARStaticRuntimeTransportProfile:
    """Inspect exact production constructors/constants and call syntax; no request."""
    descriptors = []
    for module_name, class_name, kind in _STANDARD:
        module = importlib.import_module("scripts.simulation." + module_name)
        transport = getattr(module, class_name)()
        if kind is NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP:
            source = ast.parse(textwrap.dedent(inspect.getsource(transport.fetch)))
            trust_assignments = [node for node in ast.walk(source) if isinstance(node, ast.Assign)
                                 and any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                                         and t.value.id == "session" and t.attr == "trust_env" for t in node.targets)]
            adapter_calls = [node for node in ast.walk(source) if isinstance(node, ast.Call)
                             and isinstance(node.func, ast.Name) and node.func.id == "_HTTPAdapter"]
            if (len(trust_assignments) != 1 or ast.literal_eval(trust_assignments[0].value) is not False
                    or len(adapter_calls) != 1 or len(adapter_calls[0].keywords) != 1
                    or adapter_calls[0].keywords[0].arg != "max_retries"
                    or ast.literal_eval(adapter_calls[0].keywords[0].value) != 0):
                raise ValueError("market odds transport construction changed")
            session = requests.Session()
            session.trust_env = False
            adapter = requests.adapters.HTTPAdapter(max_retries=0)
            session.mount("https://", adapter)
        else:
            session = transport._session
        https_adapter = session.get_adapter("https://example.invalid/")
        http_adapter = session.get_adapter("http://example.invalid/")
        if kind is not NARHTTPTransportKind.NAR_MARKET_ODDS_RAW_HTTP and https_adapter is not http_adapter:
            raise ValueError("standard transport adapter mounts differ")
        retry = https_adapter.max_retries
        if (type(retry.total) is not int or retry.total != 0 or retry.read is not False
                or retry.connect is not None or retry.status is not None
                or retry.other is not None or retry.redirect is not None
                or retry.backoff_factor != 0):
            raise ValueError("standard transport retry descriptor changed")
        connect = getattr(module, "_CONNECT_TIMEOUT_SECONDS")
        read = getattr(module, "_READ_TIMEOUT_SECONDS")
        if (type(connect) is not float or type(read) is not float
                or not connect.is_integer() or not read.is_integer()):
            raise ValueError("standard transport timeout cannot be exact microseconds")
        redirects, tls, stream, encoding = _request_literals(transport.fetch, module)
        descriptors.append(NARStaticHTTPTransportDescriptor(
            kind, int(connect) * 1_000_000, int(read) * 1_000_000,
            retry.total, retry.read, 0, redirects, tls, stream, encoding, session.trust_env,
        ))
        session.close()
    return NARStaticRuntimeTransportProfile(tuple(descriptors))
