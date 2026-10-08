"""Canonical scope content, not root execution or snapshot correctness authority.

Values alone are inert. Qualified authority requires controlled archive publication
and exact authoritative reload. Injected clocks are trusted composition, not a
cryptographic defense against arbitrary Python, malicious clocks or SQL writers.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, fields
from datetime import date, datetime, timezone

from scripts.simulation import historical_daily_targets as daily
from scripts.simulation.nar_historical_replay_prediction_cutoff import (
    validate_nar_historical_replay_prediction_cutoff_plan_json,
)
from scripts.simulation.nar_historical_replay_prediction_cutoff_policy import (
    NARHistoricalReplayPredictionCutoffPolicy,
    build_nar_historical_replay_prediction_cutoff_plan,
)


class RootScopeAdmissionError(ValueError):
    """Missing, noncanonical or contradictory durable scope evidence."""


class RootScopeAdmissionConflict(RootScopeAdmissionError):
    """Permanent immutable selection/reservation conflict."""


POLICY_CONTENT_PREFIX = "nar-pre-c-production-cutoff-policy-approval-content-v1:"
POLICY_APPROVAL_PREFIX = "nar-pre-c-production-cutoff-policy-approval-v1:"
SCOPE_PREFIX = "nar-pre-c-production-root-scope-admission-v1:"
AVAILABILITY_PREFIX = "nar-pre-c-production-root-scope-admission-availability-receipt-v1:"
BINDING_PREFIX = "nar-pre-c-production-claim-binding-v1:"
DECLARATION_PREFIX = "phase111-NARProspectiveDebaAcquisitionDeclarationV1:"


def identity(value, prefix):
    if type(value) is not str or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value) is None:
        raise RootScopeAdmissionError("exact versioned identity required")


def text(value):
    if (type(value) is not str or not value or value != value.strip()
            or value != unicodedata.normalize("NFC", value)
            or any(unicodedata.category(c).startswith("C") for c in value)):
        raise RootScopeAdmissionError("exact nonempty canonical NFC text required")
    return value


def utc(value):
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise RootScopeAdmissionError("aware UTC time required")
    return value.astimezone(timezone.utc)


def clock_sample(clock):
    value = clock()
    if utc(value).utcoffset() != value.utcoffset():
        raise RootScopeAdmissionError("service clock must report UTC")
    return utc(value)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def target_set_from_json(value):
    """Strict typed projection decoder, without source parsing or source authority."""
    try:
        raw = json.loads(value)
        provider = lambda item: daily.HistoricalDailyProviderIdentity(item["organization"], item["source_system"])
        result = daily.DailyHistoricalReplayTargetSet(
            date.fromisoformat(raw["target_date"]),
            daily.DailyHistoricalReplayProviderScope(tuple(provider(p) for p in raw["provider_scope"])),
            tuple(daily.DailyHistoricalReplayTarget(
                provider(t), t["external_race_id"],
                None if t["scheduled_start_at_utc"] is None else datetime.fromisoformat(t["scheduled_start_at_utc"]),
                daily.ProviderNativeDispositionEvidenceReference(**t["provider_disposition_evidence"]))
                for t in raw["target_races"]),
            tuple(daily.DailyHistoricalReplayCompletenessEvidence(
                provider(e), e["evidence_kind_and_version"], e["exact_capture_or_reference_identity"],
                e["canonical_source_or_request_identity"], e["content_sha256"],
                datetime.fromisoformat(e["observed_at_utc"]),
                None if e["provider_available_at_utc"] is None else datetime.fromisoformat(e["provider_available_at_utc"]),
                e["coverage_identity"]) for e in raw["completeness_evidence"]))
        if daily._target_set_bytes(result).decode("utf-8") != value:
            raise RootScopeAdmissionError("noncanonical complete target-set projection")
        return result
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise RootScopeAdmissionError("invalid complete target-set projection") from exc


class _Record:
    prefix = ""

    def payload(self):
        result = {}
        for f in fields(self):
            v = getattr(self, f.name)
            result[f.name] = v.isoformat() if type(v) in (datetime, date) else v
        return result

    def canonical_json(self):
        return canonical(self.payload())

    @property
    def identity(self):
        return self.prefix + hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def _version(self):
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise RootScopeAdmissionError("exact schema version 1 required")

    def _namespace(self):
        self._version()
        if (type(self.organization) is not str or self.organization != "NAR"
                or type(self.source_system) is not str or self.source_system != "nar_official"):
            raise RootScopeAdmissionError("exact NAR/nar_official namespace required")


@dataclass(frozen=True, slots=True)
class NARPreCProductionCutoffPolicyApprovalContentV1(_Record):
    organization: str
    source_system: str
    target_date: date
    target_set_content_sha256: str
    target_set_json: str
    anchor_declaration_id: str
    anchor_declaration_issued_at: datetime
    source_stored_at_json: str
    cutoff_policy_json: str
    cutoff_policy_identity: str
    cutoff_plan_json: str
    cutoff_plan_sha256: str
    schema_version: int = 1
    prefix = POLICY_CONTENT_PREFIX

    def __post_init__(self):
        self._namespace()
        identity(self.anchor_declaration_id, DECLARATION_PREFIX)
        identity(self.target_set_content_sha256, "")
        identity(self.cutoff_plan_sha256, "")
        object.__setattr__(self, "anchor_declaration_issued_at", utc(self.anchor_declaration_issued_at))
        target_set = target_set_from_json(self.target_set_json)
        if (type(self.target_date) is not date or self.target_date != target_set.target_date
                or self.target_set_content_sha256 != target_set.content_sha256):
            raise RootScopeAdmissionError("target-set date/digest differs")
        try:
            raw = json.loads(self.cutoff_policy_json)
            policy = NARHistoricalReplayPredictionCutoffPolicy(raw["offset_microseconds"])
            plan = build_nar_historical_replay_prediction_cutoff_plan(target_set=target_set, policy=policy)
            if (policy.canonical_bytes().decode() != self.cutoff_policy_json
                    or policy.policy_identity != self.cutoff_policy_identity
                    or plan.canonical_bytes().decode() != self.cutoff_plan_json
                    or plan.plan_sha256 != self.cutoff_plan_sha256):
                raise RootScopeAdmissionError("policy/complete derived plan differs")
            stored = json.loads(self.source_stored_at_json)
            ids = sorted(e.exact_capture_or_reference_identity for e in target_set.completeness_evidence)
            if (type(stored) is not list or len(stored) != len(ids)
                    or [s["capture_id"] for s in stored] != ids):
                raise RootScopeAdmissionError("source temporal provenance population differs")
            for item in stored:
                if set(item) != {"capture_id", "stored_at"}:
                    raise RootScopeAdmissionError("source temporal provenance fields differ")
                observed = utc(datetime.fromisoformat(item["stored_at"]))
                if observed.isoformat() != item["stored_at"] or observed > self.anchor_declaration_issued_at:
                    raise RootScopeAdmissionError("sources must preexist original declaration")
            if canonical(stored) != self.source_stored_at_json:
                raise RootScopeAdmissionError("noncanonical source temporal provenance")
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise RootScopeAdmissionError("invalid complete policy provenance") from exc

    @property
    def earliest_cutoff(self):
        return min(datetime.fromisoformat(d["prediction_information_cutoff"])
                   for d in json.loads(self.cutoff_plan_json)["decisions"])


@dataclass(frozen=True, slots=True)
class NARPreCProductionCutoffPolicyApprovalV1(_Record):
    policy_content_identity: str
    policy_approved_at: datetime
    schema_version: int = 1
    prefix = POLICY_APPROVAL_PREFIX

    def __post_init__(self):
        self._version()
        identity(self.policy_content_identity, POLICY_CONTENT_PREFIX)
        object.__setattr__(self, "policy_approved_at", utc(self.policy_approved_at))


@dataclass(frozen=True, slots=True)
class NARPreCProductionRootScopeAdmissionV1(_Record):
    phase113_binding_identity: str
    policy_approval_identity: str
    target_declaration_id: str
    organization: str
    source_system: str
    external_race_id: str
    internal_race_id: int
    prediction_information_cutoff: datetime
    target_date: date
    target_set_content_sha256: str
    cutoff_policy_identity: str
    cutoff_plan_sha256: str
    cutoff_plan_json: str
    dataset_id: str
    schema_version: int = 1
    prefix = SCOPE_PREFIX

    def __post_init__(self):
        self._namespace()
        identity(self.phase113_binding_identity, BINDING_PREFIX)
        identity(self.policy_approval_identity, POLICY_APPROVAL_PREFIX)
        identity(self.target_declaration_id, DECLARATION_PREFIX)
        identity(self.target_set_content_sha256, "")
        identity(self.cutoff_plan_sha256, "")
        text(self.dataset_id)
        if type(self.internal_race_id) is not int or self.internal_race_id <= 0:
            raise RootScopeAdmissionError("pre-existing internal race identity required")
        match = re.fullmatch(r"nar:([0-9]{8}):[1-9][0-9]*:[1-9][0-9]*", self.external_race_id)
        if type(self.target_date) is not date or match is None or match[1] != self.target_date.strftime("%Y%m%d"):
            raise RootScopeAdmissionError("canonical target/date agreement required")
        object.__setattr__(self, "prediction_information_cutoff", utc(self.prediction_information_cutoff))
        plan = validate_nar_historical_replay_prediction_cutoff_plan_json(
            canonical_json=self.cutoff_plan_json, plan_sha256=self.cutoff_plan_sha256,
            target_set_content_sha256=self.target_set_content_sha256)
        decisions = [d for d in plan["decisions"] if d["external_race_id"] == self.external_race_id]
        if (plan["cutoff_policy_identity"] != self.cutoff_policy_identity or len(decisions) != 1
                or utc(datetime.fromisoformat(decisions[0]["prediction_information_cutoff"])) != self.prediction_information_cutoff):
            raise RootScopeAdmissionError("selected target/cutoff must equal complete plan")


@dataclass(frozen=True, slots=True)
class NARPreCProductionRootScopeAdmissionAvailabilityReceiptV1(_Record):
    scope_identity: str
    policy_approval_identity: str
    phase113_binding_identity: str
    admitted_at: datetime
    schema_version: int = 1
    prefix = AVAILABILITY_PREFIX

    def __post_init__(self):
        self._version()
        for v, p in ((self.scope_identity, SCOPE_PREFIX), (self.policy_approval_identity, POLICY_APPROVAL_PREFIX),
                     (self.phase113_binding_identity, BINDING_PREFIX)):
            identity(v, p)
        object.__setattr__(self, "admitted_at", utc(self.admitted_at))


def parse_record(kind, value, expected_identity):
    identity(expected_identity, kind.prefix)
    try:
        raw = json.loads(value)
        if type(raw) is not dict or set(raw) != {f.name for f in fields(kind)}:
            raise RootScopeAdmissionError("exact persisted field set required")
        args = dict(raw)
        for key in ("anchor_declaration_issued_at", "policy_approved_at", "prediction_information_cutoff", "admitted_at"):
            if key in args:
                args[key] = datetime.fromisoformat(args[key])
        if "target_date" in args:
            args["target_date"] = date.fromisoformat(args["target_date"])
        result = kind(**args)
        if result.canonical_json() != value or result.identity != expected_identity:
            raise RootScopeAdmissionError("noncanonical content/identity")
        return result
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise RootScopeAdmissionError("corrupt persisted scope record") from exc


def validate_policy_pair(content, approval):
    if approval.policy_content_identity != content.identity:
        raise RootScopeAdmissionError("approval parent differs")
    floors = [content.anchor_declaration_issued_at] + [
        datetime.fromisoformat(s["stored_at"]) for s in json.loads(content.source_stored_at_json)]
    if not max(floors) <= approval.policy_approved_at <= content.earliest_cutoff:
        raise RootScopeAdmissionError("policy observation outside full-set approval window")


def validate_scope_pair(scope, availability, content, approval):
    validate_policy_pair(content, approval)
    if (scope.policy_approval_identity != approval.identity
            or any(getattr(scope, k) != getattr(content, k) for k in (
                "organization", "source_system", "target_date", "target_set_content_sha256",
                "cutoff_policy_identity", "cutoff_plan_sha256", "cutoff_plan_json"))
            or availability.scope_identity != scope.identity
            or availability.policy_approval_identity != approval.identity
            or availability.phase113_binding_identity != scope.phase113_binding_identity
            or availability.admitted_at < approval.policy_approved_at):
        raise RootScopeAdmissionError("scope/policy/availability projection differs")
