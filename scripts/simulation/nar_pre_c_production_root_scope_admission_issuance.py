"""Controlled two-stage policy/scope issuance; no execution admission.

Publication deep-verifies archived daily source evidence. Ordinary authoritative
load trusts the accepted immutable Phase114 boundary and never reopens it.
There is deliberately no cross-store atomicity or upstream rollback claim.
"""

from __future__ import annotations

from scripts.simulation import historical_daily_targets as daily
from scripts.simulation import nar_pre_c_production_root_scope_admission_archive_migration as schema
from scripts.simulation.nar_pre_c_production_root_scope_admission import (
    NARPreCProductionCutoffPolicyApprovalContentV1 as PolicyContent,
    NARPreCProductionCutoffPolicyApprovalV1 as PolicyApproval,
    NARPreCProductionRootScopeAdmissionV1 as Scope,
    NARPreCProductionRootScopeAdmissionAvailabilityReceiptV1 as Availability,
    RootScopeAdmissionError, DECLARATION_PREFIX, identity, canonical,
    clock_sample, validate_policy_pair, validate_scope_pair,
)
from scripts.simulation.nar_historical_replay_prediction_cutoff_policy import (
    NARHistoricalReplayPredictionCutoffPolicy,
    build_nar_historical_replay_prediction_cutoff_plan,
)
from scripts.simulation.nar_trusted_deba_acquisition import (
    NARProspectiveDebaAcquisitionDeclarationV1, reconstruct_declaration,
)
from scripts.simulation.nar_historical_daily_target_capture import NARHistoricalDailyTargetResponseCapture
from scripts.simulation.nar_historical_daily_target_source import build_nar_historical_daily_replay_target_set
from scripts.simulation.sqlite_nar_trusted_deba_acquisition_archive import SQLiteNARTrustedDebaAcquisitionArchive
from scripts.simulation.sqlite_nar_daily_target_evidence_archive import SQLiteNARDailyTargetEvidenceArchive
from scripts.simulation.sqlite_nar_pre_c_production_root_scope_admission_archive import (
    SQLiteNARPreCProductionRootScopeAdmissionArchive, require_idle, load_binding_authority,
)


def _source(*, declaration_id, lineage_archive, daily_archive):
    """Read-only original-field reconstruction; no Deba population extraction."""
    if (type(lineage_archive) is not SQLiteNARTrustedDebaAcquisitionArchive
            or type(daily_archive) is not SQLiteNARDailyTargetEvidenceArchive):
        raise RootScopeAdmissionError("exact injected source archives required")
    require_idle(lineage_archive, daily_archive)
    identity(declaration_id, DECLARATION_PREFIX)
    declaration = lineage_archive.load_declaration(declaration_id=declaration_id)
    if type(declaration) is not NARProspectiveDebaAcquisitionDeclarationV1 or declaration.identity != declaration_id:
        raise RootScopeAdmissionError("exact original declaration required")
    rebuilt = reconstruct_declaration(
        target_archive=daily_archive, target_date=declaration.target_date,
        envelope_capture_id=declaration.envelope_capture_id, race_list_capture_ids=declaration.race_list_capture_ids,
        expected_target_set_sha256=declaration.target_set_sha256, external_race_id=declaration.external_race_id,
        prediction_information_cutoff=declaration.prediction_information_cutoff, issued_at=declaration.issued_at)
    if rebuilt != declaration:
        raise RootScopeAdmissionError("original declaration/source reconstruction differs")
    ids = (declaration.envelope_capture_id,) + declaration.race_list_capture_ids
    captures = tuple(daily_archive.load_capture(capture_id=cid) for cid in ids)
    if any(type(c) is not NARHistoricalDailyTargetResponseCapture or c.capture_id != cid
           for cid, c in zip(ids, captures, strict=True)):
        raise RootScopeAdmissionError("exact complete daily capture reload required")
    if any(c.stored_at > declaration.issued_at for c in captures):
        raise RootScopeAdmissionError("all original captures must preexist declaration")
    target_set = build_nar_historical_daily_replay_target_set(
        target_date=declaration.target_date, envelope_capture=captures[0], race_list_captures=captures[1:])
    if target_set.content_sha256 != declaration.target_set_sha256:
        raise RootScopeAdmissionError("complete set differs from declaration")
    return declaration, target_set, captures


def _policy_content(source, offset_microseconds):
    declaration, target_set, captures = source
    policy = NARHistoricalReplayPredictionCutoffPolicy(offset_microseconds)
    plan = build_nar_historical_replay_prediction_cutoff_plan(target_set=target_set, policy=policy)
    decisions = [d for d in plan.decisions if d.target.external_race_id == declaration.external_race_id]
    if len(decisions) != 1 or decisions[0].prediction_information_cutoff != declaration.prediction_information_cutoff:
        raise RootScopeAdmissionError("anchor cutoff differs from reviewed full plan decision")
    return PolicyContent(
        "NAR", "nar_official", target_set.target_date, target_set.content_sha256,
        daily._target_set_bytes(target_set).decode("utf-8"), declaration.identity, declaration.issued_at,
        canonical([{"capture_id": c.capture_id, "stored_at": c.stored_at.isoformat()}
                   for c in sorted(captures, key=lambda c: c.capture_id)]),
        policy.canonical_bytes().decode("utf-8"), policy.policy_identity,
        plan.canonical_bytes().decode("utf-8"), plan.plan_sha256)


def _verify_policy_source(content, *, lineage_archive, daily_archive):
    import json
    original = _policy_content(_source(declaration_id=content.anchor_declaration_id,
                              lineage_archive=lineage_archive, daily_archive=daily_archive),
                              json.loads(content.cutoff_policy_json)["offset_microseconds"])
    if original != content:
        raise RootScopeAdmissionError("immutable policy source projection changed")


class NARPreCProductionRootScopeAdmissionIssuer:
    """Trusted injected service clock; caller selects identities, never timestamps."""

    def __init__(self, *, companion_archive, lineage_archive, daily_archive, utc_clock):
        if type(companion_archive) is not SQLiteNARPreCProductionRootScopeAdmissionArchive or not callable(utc_clock):
            raise RootScopeAdmissionError("exact companion and controlled service clock required")
        self._archive = companion_archive
        self._lineage = lineage_archive
        self._daily = daily_archive
        self._clock = utc_clock

    def publish_policy(self, *, anchor_declaration_id, offset_microseconds):
        require_idle(self._archive)
        content = _policy_content(_source(declaration_id=anchor_declaration_id,
                                         lineage_archive=self._lineage, daily_archive=self._daily), offset_microseconds)
        content = self._archive._stage_content(schema.POLICY_CONTENTS, content)
        _verify_policy_source(content, lineage_archive=self._lineage, daily_archive=self._daily)
        def first():
            approval = PolicyApproval(content.identity, clock_sample(self._clock))
            validate_policy_pair(content, approval)
            return approval
        approval = self._archive._stage_receipt(schema.POLICY_APPROVALS, "policy_content_identity", content.identity, first)
        reloaded = self._archive.load_policy(approval_identity=approval.identity)
        _verify_policy_source(reloaded[0], lineage_archive=self._lineage, daily_archive=self._daily)
        if reloaded != (content, approval):
            raise RootScopeAdmissionError("completed policy pair differs")
        return reloaded

    def publish_scope(self, *, policy_approval_identity, phase113_binding_identity, dataset_id,
                      phase113_archive, runtime_archive, phase112_archive, phase109_repository):
        require_idle(self._archive)
        upstreams = dict(phase113_archive=phase113_archive, runtime_archive=runtime_archive,
                        phase112_archive=phase112_archive, phase109_repository=phase109_repository)
        content, approval = self._archive.load_policy(approval_identity=policy_approval_identity)
        _verify_policy_source(content, lineage_archive=self._lineage, daily_archive=self._daily)
        binding, pair, mapping = load_binding_authority(binding_identity=phase113_binding_identity, **upstreams)
        declaration, target_set, _ = _source(declaration_id=mapping.phase111_declaration_id,
                                             lineage_archive=self._lineage, daily_archive=self._daily)
        if (daily._target_set_bytes(target_set).decode("utf-8") != content.target_set_json
                or declaration.external_race_id != binding.external_race_id
                or declaration.prediction_information_cutoff != binding.prediction_cutoff):
            raise RootScopeAdmissionError("accepted target declaration/set/cutoff differs")
        scope = Scope(binding.identity, approval.identity, declaration.identity, "NAR", "nar_official",
                      binding.external_race_id, binding.internal_race_id, binding.prediction_cutoff,
                      content.target_date, content.target_set_content_sha256, content.cutoff_policy_identity,
                      content.cutoff_plan_sha256, content.cutoff_plan_json, dataset_id)
        scope = self._archive._stage_content(schema.SCOPES, scope)
        def first():
            receipt = Availability(scope.identity, approval.identity, binding.identity, clock_sample(self._clock))
            validate_scope_pair(scope, receipt, content, approval)
            if receipt.admitted_at < pair.availability_receipt.available_at:
                raise RootScopeAdmissionError("admission must follow Phase112 availability")
            return receipt
        receipt = self._archive._stage_receipt(schema.AVAILABILITY, "scope_identity", scope.identity, first)
        reloaded = self._archive.load_admission(availability_receipt_identity=receipt.identity,
                      expected_phase113_binding_identity=binding.identity, **upstreams)
        _verify_policy_source(content, lineage_archive=self._lineage, daily_archive=self._daily)
        original, original_set, _ = _source(declaration_id=declaration.identity,
                                          lineage_archive=self._lineage, daily_archive=self._daily)
        if (original != declaration or daily._target_set_bytes(original_set) != daily._target_set_bytes(target_set)
                or reloaded != (scope, receipt)):
            raise RootScopeAdmissionError("post-publication exact local/upstream/source reread differs")
        return reloaded
