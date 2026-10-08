"""Strict canonical values are content identities, never standalone authority."""

import json
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta

import pytest

from scripts.simulation.nar_pre_c_production_root_scope_admission import (
    RootScopeAdmissionError as Error, parse_record, canonical, target_set_from_json,
    NARPreCProductionCutoffPolicyApprovalV1 as Approval,
    NARPreCProductionRootScopeAdmissionAvailabilityReceiptV1 as Availability,
)
from test_nar_pre_c_production_root_scope_admission_issuance import context, parents_context, policy, scope, OFFSET


def test_four_exact_values_content_addressed_and_immutable(context):
    content, approval = policy(context)
    admitted, receipt = scope(context, approval)
    for value in (content, approval, admitted, receipt):
        assert parse_record(type(value), value.canonical_json(), value.identity) == value
        assert len(value.identity.split(":")[-1]) == 64
        assert value.identity == replace(value).identity
        with pytest.raises(FrozenInstanceError):
            value.schema_version = 2
        for bad_json in ("{}", value.canonical_json() + " ", canonical(dict(value.payload(), extra=True))):
            with pytest.raises(Error):
                parse_record(type(value), bad_json, value.identity)
        assert "authorized" not in value.payload()
        assert "can_execute" not in value.payload()
    assert "policy_approved_at" not in content.payload()
    assert "admitted_at" not in admitted.payload()
    assert "claim_identity" not in admitted.payload()
    assert "entry_mapping" not in admitted.payload()


@pytest.mark.parametrize("field", ["anchor_declaration_id", "cutoff_policy_identity", "target_set_content_sha256", "cutoff_plan_sha256"])
def test_policy_invalid_exact_identity(context, field):
    content, _ = policy(context)
    value = getattr(content, field)
    with pytest.raises(ValueError):
        replace(content, **{field: value + ":extra"})


@pytest.mark.parametrize("field", ["phase113_binding_identity", "policy_approval_identity", "target_declaration_id"])
@pytest.mark.parametrize("suffix", ["extra:", "UPPER", "short", "long"])
def test_receipt_and_scope_exact_prefix_shape(context, field, suffix):
    _, approval = policy(context)
    admitted, _ = scope(context, approval)
    value = getattr(admitted, field)
    prefix, digest = value.rsplit(":", 1)
    bad = {"extra:": prefix + ":extra:" + digest, "UPPER": prefix + ":" + "A" * 64,
           "short": prefix + ":" + digest[:63], "long": prefix + ":" + digest + "0"}[suffix]
    with pytest.raises(Error):
        replace(admitted, **{field: bad})


@pytest.mark.parametrize("dataset", ["", " leading", "trailing ", "a\nb", "a\x00b", "e\u0301", "a\u200bb", 99])
def test_dataset_canonical_requested_namespace_only(context, dataset):
    _, approval = policy(context)
    with pytest.raises(Error):
        scope(context, approval, dataset_id=dataset)
    assert context.c.execute("SELECT count(*) FROM nar_pre_c_production_root_scope_contents").fetchone() == (0,)


@pytest.mark.parametrize("mutation", ["missing", "extra", "reordered", "duplicate", "evidence", "date", "digest", "plan", "policy"])
def test_complete_population_and_plan_not_arbitrary_json(context, mutation):
    content, _ = policy(context)
    raw = json.loads(content.target_set_json)
    if mutation == "missing":
        raw["target_races"].pop()
    elif mutation == "extra":
        raw["unreviewed"] = True
    elif mutation == "reordered":
        raw["target_races"].reverse()
    elif mutation == "duplicate":
        raw["target_races"].append(raw["target_races"][0])
    elif mutation == "evidence":
        raw["completeness_evidence"].pop()
    elif mutation == "date":
        raw["target_date"] = "2025-01-02"
    if mutation in ("missing", "extra", "reordered", "duplicate", "evidence", "date"):
        kwargs = {"target_set_json": canonical(raw)}
    elif mutation == "digest":
        kwargs = {"target_set_content_sha256": "f" * 64}
    elif mutation == "plan":
        plan = json.loads(content.cutoff_plan_json)
        plan["decisions"].pop()
        kwargs = {"cutoff_plan_json": canonical(plan)}
    else:
        kwargs = {"cutoff_policy_json": "{}"}
    with pytest.raises(ValueError):
        replace(content, **kwargs)


@pytest.mark.parametrize("field", ["external_race_id", "internal_race_id", "prediction_information_cutoff", "cutoff_plan_json", "organization", "source_system", "schema_version"])
def test_scope_wrong_target_or_plan_or_type(context, field):
    _, approval = policy(context)
    admitted, _ = scope(context, approval)
    bad = {"external_race_id": "nar:20250101:21:2", "internal_race_id": True,
           "prediction_information_cutoff": admitted.prediction_information_cutoff + timedelta(seconds=1),
           "cutoff_plan_json": "{}", "organization": "JRA", "source_system": "manual", "schema_version": True}[field]
    with pytest.raises((ValueError, TypeError)):
        replace(admitted, **{field: bad})
