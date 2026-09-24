"""Actual Requests pre-adapter guard for one exact archived HTTP attempt."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
from urllib.parse import parse_qsl, urlsplit
from collections.abc import Mapping

import requests

from scripts.simulation.nar_operational_timing_attempt_v2 import (
    NAROperationalTimingAttemptV2, NARRequestEffectiveEnvironmentVerification,
    NARRequestEnvironmentQualification, NARSafeSendSetting,
)
from scripts.simulation.nar_operational_timing_observability import NARHTTPTransportKind
from scripts.simulation.nar_operational_timing_observability_v2 import _REQUIRED_TRANSPORT
from scripts.simulation.sqlite_nar_operational_timing_attempt_archive import _SEND_VERIFICATION_ISSUANCE_MARKER


class NARRequestEnvironmentRejected(RuntimeError):
    """Pre-network authority failure; never a provider latency/timeout result."""


@dataclass(slots=True)
class _HTTPAttemptContext:
    runner: object
    capability: object
    attempt: NAROperationalTimingAttemptV2
    expected_url: str
    transport_kind: NARHTTPTransportKind
    send_started: bool = False


_ACTIVE_HTTP_ATTEMPT: ContextVar[_HTTPAttemptContext | None] = ContextVar("nar_active_http_attempt", default=None)


def _require_safe_url(url: str) -> None:
    if type(url) is not str or not url or any(ord(x) < 33 for x in url):
        raise ValueError("exact non-secret request URL required")
    parts = urlsplit(url)
    if (parts.scheme != "https" or not parts.hostname or parts.username is not None
            or parts.password is not None or parts.fragment
            or parts.hostname not in ("www.keiba.go.jp", "www2.keiba.go.jp")
            or parts.port not in (None, 443)
            or any(key.lower() in {"password", "token", "secret", "authorization", "api_key", "apikey"}
                   for key, _ in parse_qsl(parts.query, keep_blank_values=True))):
        raise ValueError("official request URL must be HTTPS without credentials or fragment")


class NARHTTPAttemptContext:
    """Scoped context shared by the outer timing wrapper and guarded Session.send."""

    __slots__ = ("_context", "_token")

    def __init__(self, *, runner: object, capability: object,
                 attempt: NAROperationalTimingAttemptV2, expected_url: str,
                 transport_kind: NARHTTPTransportKind) -> None:
        _require_safe_url(expected_url)
        if (type(attempt) is not NAROperationalTimingAttemptV2 or type(transport_kind) is not NARHTTPTransportKind
                or _REQUIRED_TRANSPORT.get(attempt.stage) is not transport_kind
                or attempt.expected_request_url_sha256 != sha256(expected_url.encode("utf-8")).hexdigest()):
            raise ValueError("HTTP attempt stage/transport ancestry contradicts")
        self._context = _HTTPAttemptContext(runner, capability, attempt, expected_url, transport_kind)
        self._token = None

    def __enter__(self):
        if _ACTIVE_HTTP_ATTEMPT.get() is not None:
            raise RuntimeError("nested official HTTP attempt is unsupported")
        self._context.capability.require_current_owner(self._context.runner)
        if self._context.runner.attempt_archive.load_attempt(attempt_identity=self._context.attempt.attempt_identity) != self._context.attempt:
            raise RuntimeError("HTTP attempt must be archived and exact-reloaded")
        self._token = _ACTIVE_HTTP_ATTEMPT.set(self._context)
        return self

    def __exit__(self, *_: object) -> None:
        if self._token is not None:
            _ACTIVE_HTTP_ATTEMPT.reset(self._token)
            self._token = None


class NAROfficialTimingGuardedSession(requests.Session):
    """Observes concrete PreparedRequest/send kwargs without rerunning env resolution."""

    def __init__(self, *, runner: object, capability: object, transport_kind: NARHTTPTransportKind) -> None:
        super().__init__()
        if type(transport_kind) is not NARHTTPTransportKind:
            raise ValueError("closed transport kind required")
        self._timing_runner = runner
        self._timing_capability = capability
        self._timing_transport_kind = transport_kind

    def send(self, request: requests.PreparedRequest, **kwargs):
        context = _ACTIVE_HTTP_ATTEMPT.get()
        if (context is None or context.runner is not self._timing_runner
                or context.capability is not self._timing_capability
                or context.transport_kind is not self._timing_transport_kind):
            raise NARRequestEnvironmentRejected("guarded Session requires exact active HTTP attempt")
        context.capability.require_current_owner(context.runner)
        if context.send_started:
            raise NARRequestEnvironmentRejected("one HTTP attempt cannot perform a second send")
        context.send_started = True
        if type(request) is not requests.PreparedRequest or type(request.url) is not str:
            raise NARRequestEnvironmentRejected("exact prepared request required")
        try:
            _require_safe_url(request.url)
        except ValueError as error:
            raise NARRequestEnvironmentRejected("prepared request URL is outside safe NAR scope") from error
        archive = context.runner.attempt_archive
        attempt = archive.load_attempt(attempt_identity=context.attempt.attempt_identity)
        if attempt != context.attempt or attempt.expected_http_environment_policy is None:
            raise NARRequestEnvironmentRejected("archived HTTP attempt ancestry is unavailable")
        claim = archive.runtime.load_claim_for_session(session_identity=attempt.session_identity)
        binding = archive.runtime.load_binding(binding_identity=claim.binding_identity) if claim else None
        profile = archive.runtime.load_transport_profile(profile_identity=binding.transport_profile_identity) if binding else None
        descriptor = next((d for d in profile.descriptors if d.kind is self._timing_transport_kind), None) if profile else None
        timeout = kwargs.get("timeout")
        adapter = self.get_adapter(request.url)
        retry = getattr(adapter, "max_retries", None)
        static_match = (binding is not None and descriptor is not None
                        and self.trust_env is descriptor.trust_env
                        and kwargs.get("allow_redirects") is descriptor.allow_redirects
                        and kwargs.get("stream") is descriptor.stream
                        and request.headers.get("Accept-Encoding") == descriptor.accept_encoding
                        and retry is not None and type(retry.total) is int
                        and retry.total == descriptor.adapter_retry_total
                        and retry.read is descriptor.adapter_retry_read
                        and retry.connect is None and retry.status is None
                        and retry.other is None and retry.redirect is None
                        and retry.backoff_factor == 0
                        and type(timeout) is tuple and len(timeout) == 2
                        and all(type(x) in (int, float) for x in timeout)
                        and timeout[0] * 1_000_000 == descriptor.connect_timeout_microseconds
                        and timeout[1] * 1_000_000 == descriptor.read_timeout_microseconds)
        url_match = (request.url == context.expected_url
                     and sha256(request.url.encode("utf-8")).hexdigest() == attempt.expected_request_url_sha256)
        proxies = kwargs.get("proxies")
        proxy_state = NARSafeSendSetting.DIRECT if isinstance(proxies, Mapping) and not proxies else NARSafeSendSetting.NONEMPTY
        verify_state = NARSafeSendSetting.TRUE if kwargs.get("verify") is True else NARSafeSendSetting.OTHER
        cert_state = NARSafeSendSetting.ABSENT if kwargs.get("cert") is None else NARSafeSendSetting.PRESENT
        auth_state = NARSafeSendSetting.PRESENT if "Authorization" in request.headers else NARSafeSendSetting.ABSENT
        proxy_auth_state = NARSafeSendSetting.PRESENT if "Proxy-Authorization" in request.headers else NARSafeSendSetting.ABSENT
        qualified = (url_match and static_match and proxy_state is NARSafeSendSetting.DIRECT
                     and verify_state is NARSafeSendSetting.TRUE and cert_state is NARSafeSendSetting.ABSENT
                     and auth_state is NARSafeSendSetting.ABSENT and proxy_auth_state is NARSafeSendSetting.ABSENT)
        verification = NARRequestEffectiveEnvironmentVerification(
            attempt.attempt_identity, sha256(request.url.encode("utf-8")).hexdigest(),
            binding.transport_profile_identity if binding else "nar-static-runtime-transport-profile-v1:" + "0" * 64,
            self.trust_env, proxy_state, verify_state, cert_state, auth_state, proxy_auth_state,
            url_match, static_match,
            NARRequestEnvironmentQualification.QUALIFIED_DIRECT_REQUEST_ENVIRONMENT if qualified
            else NARRequestEnvironmentQualification.NONQUALIFYING_REQUEST_ENVIRONMENT,
        )
        archive.save_environment(verification=verification,
                                 _issuance_marker=_SEND_VERIFICATION_ISSUANCE_MARKER)
        if archive.load_environment_for_attempt(attempt_identity=attempt.attempt_identity) != verification:
            raise NARRequestEnvironmentRejected("request environment verification did not exact-reload")
        if not qualified:
            raise NARRequestEnvironmentRejected("request-effective send configuration is not direct")
        return super().send(request, **kwargs)


def guarded_session_factory(*, runner: object, capability: object, transport_kind: NARHTTPTransportKind):
    """Private transport injection; ordinary transport defaults stay requests.Session."""
    return lambda: NAROfficialTimingGuardedSession(runner=runner, capability=capability,
                                                     transport_kind=transport_kind)
