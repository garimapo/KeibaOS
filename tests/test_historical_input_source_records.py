from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import inspect
from types import MappingProxyType
from typing import get_type_hints
import unittest

import scripts.simulation as simulation_package
from scripts.simulation.historical_input_evidence import HistoricalInputEvidenceReference
from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceConflictError,
    HistoricalInputSourceError,
    HistoricalInputSourceRecord,
    HistoricalInputSourceValidationError,
    SourceRecordKind,
    build_historical_input_source_id,
    canonical_historical_input_source_payload,
    validate_historical_input_source_record_set,
)


UTC = timezone.utc
OBSERVED = datetime(2026, 8, 5, 9, 30, 1, 123456, tzinfo=UTC)
AVAILABLE = OBSERVED - timedelta(minutes=1)


def _values(kind: str, *, entry_id: str = "nar:20260805:1:1:entry:1") -> dict[str, object]:
    if kind == "track":
        return {
            "target_race_date": date(2026, 8, 5),
            "scheduled_start_at": datetime(2026, 8, 5, 15, 30, tzinfo=UTC),
            "place": "Tokyo",
            "distance_m": 1600,
            "track": "turf",
            "track_condition": "good",
            "race_name": None,
            "race_class": None,
            "weather": None,
        }
    if kind == "entry":
        return {"external_entry_id": entry_id, "external_horse_id": None, "horse_no": 1}
    if kind == "jockey":
        return {"external_entry_id": entry_id, "jockey": "Jockey"}
    if kind == "odds_win":
        return {"external_entry_id": entry_id, "horse_no": 1, "win_odds": Decimal("2.00")}
    if kind == "past_race":
        return {
            "race_date": date(2026, 8, 1),
            "place": "Tokyo",
            "race_name": "Prior Race",
            "race_class": "Open",
            "distance_m": 1600,
            "track": "turf",
            "weather": "sunny",
            "track_condition": "good",
            "finish": 1,
            "reference_time_difference_seconds": Decimal("0.00"),
            "race_time": "1:32.0",
            "weight": Decimal("480.0"),
            "weight_diff": Decimal("0.0"),
            "jockey": "Jockey",
            "popularity": 0,
            "odds": Decimal("2.0"),
            "passing_order": "",
            "fourth_corner_position": 0,
        }
    if kind == "past_race_absence":
        return {
            "external_entry_id": entry_id,
            "query_scope": {
                "external_entry_id": entry_id,
                "target_race_date": date(2026, 8, 5),
                "strictly_before_target_race": True,
            },
            "result_count": 0,
        }
    raise AssertionError(kind)


def _record(
    kind: SourceRecordKind = "track",
    *,
    record_values: dict[str, object] | None = None,
    external_entry_id: str | None = None,
    canonical_source_url: str | None = None,
    provider_record_id: str | None = None,
    available_at: datetime | None = AVAILABLE,
    observed_at: datetime = OBSERVED,
) -> HistoricalInputSourceRecord:
    entry_id = "nar:20260805:1:1:entry:1"
    if kind != "track" and external_entry_id is None:
        external_entry_id = entry_id
    if kind == "past_race" and provider_record_id is None:
        provider_record_id = "official-past-race-1"
    if kind == "past_race_absence" and canonical_source_url is None:
        canonical_source_url = "https://EXAMPLE.test/history?z=2&a=1"
    roles = {
        "track": ("track",),
        "entry": ("entry",),
        "jockey": ("jockey",),
        "odds_win": ("odds_win",),
        "past_race": ("historical_race_context", "historical_race_result"),
        "past_race_absence": ("past_race_absence_query",),
    }[kind]
    evidence = tuple(
        HistoricalInputEvidenceReference(
            evidence_role=role,
            canonical_source_url=canonical_source_url,
            response_sha256=(str(index + 1) * 64),
            available_at=available_at,
            observed_at=observed_at,
        )
        for index, role in enumerate(roles)
    )
    return HistoricalInputSourceRecord(
        record_kind=kind,
        organization="NAR",
        source_system="nar_official",
        external_race_id="nar:20260805:1:1",
        external_entry_id=external_entry_id,
        provider_record_id=provider_record_id,
        record_values=_values(kind, entry_id=entry_id) if record_values is None else record_values,
        evidence=evidence,
    )


class HistoricalInputSourceRecordsTest(unittest.TestCase):
    def test_evidence_reference_is_frozen_and_validates_raw_response_identity(self) -> None:
        import scripts.simulation.historical_input_evidence as module

        self.assertEqual(
            {name for name, value in inspect.getmembers(module, inspect.isclass) if not name.startswith("_")},
            {"HistoricalInputEvidenceReference"},
        )
        reference = HistoricalInputEvidenceReference(
            "track", "https://example.test/raw", "a" * 64, AVAILABLE, OBSERVED,
        )
        self.assertFalse(hasattr(reference, "__dict__"))
        self.assertEqual(reference.observed_at, OBSERVED)
        for kwargs in (
            {"response_sha256": "A" * 64},
            {"response_sha256": "a" * 63},
            {"canonical_source_url": "http://example.test/raw"},
            {"observed_at": OBSERVED.replace(tzinfo=None)},
            {"available_at": OBSERVED + timedelta(seconds=1)},
        ):
            with self.subTest(kwargs=kwargs):
                values = {
                    "evidence_role": "track", "canonical_source_url": "https://example.test/raw",
                    "response_sha256": "a" * 64, "available_at": AVAILABLE, "observed_at": OBSERVED,
                }
                values.update(kwargs)
                with self.assertRaises(ValueError):
                    HistoricalInputEvidenceReference(**values)

    def test_evidence_roles_order_timestamps_and_raw_digest_drive_v3_identity(self) -> None:
        baseline = _record("past_race", canonical_source_url="https://example.test/past")
        reversed_roles = tuple(reversed(baseline.evidence))
        reordered = HistoricalInputSourceRecord(
            record_kind=baseline.record_kind, organization=baseline.organization, source_system=baseline.source_system,
            external_race_id=baseline.external_race_id, external_entry_id=baseline.external_entry_id,
            provider_record_id=baseline.provider_record_id, record_values=baseline.record_values, evidence=reversed_roles,
        )
        self.assertEqual(reordered.evidence, baseline.evidence)
        self.assertEqual(reordered.source_id, baseline.source_id)
        shifted = tuple(replace(item, observed_at=item.observed_at + timedelta(minutes=1)) for item in baseline.evidence)
        timestamp_shifted = HistoricalInputSourceRecord(
            record_kind=baseline.record_kind, organization=baseline.organization, source_system=baseline.source_system,
            external_race_id=baseline.external_race_id, external_entry_id=baseline.external_entry_id,
            provider_record_id=baseline.provider_record_id, record_values=baseline.record_values, evidence=shifted,
        )
        self.assertEqual(timestamp_shifted.source_id, baseline.source_id)
        changed_raw = (replace(baseline.evidence[0], response_sha256="b" * 64), baseline.evidence[1])
        raw_shifted = HistoricalInputSourceRecord(
            record_kind=baseline.record_kind, organization=baseline.organization, source_system=baseline.source_system,
            external_race_id=baseline.external_race_id, external_entry_id=baseline.external_entry_id,
            provider_record_id=baseline.provider_record_id, record_values=baseline.record_values, evidence=changed_raw,
        )
        self.assertNotEqual(raw_shifted.source_id, baseline.source_id)
        conflicting = (
            baseline.evidence[0],
            replace(baseline.evidence[1], canonical_source_url=baseline.evidence[0].canonical_source_url,
                    response_sha256=baseline.evidence[0].response_sha256,
                    observed_at=baseline.evidence[1].observed_at + timedelta(minutes=1)),
        )
        with self.assertRaises(HistoricalInputSourceValidationError):
            HistoricalInputSourceRecord(
                record_kind=baseline.record_kind, organization=baseline.organization, source_system=baseline.source_system,
                external_race_id=baseline.external_race_id, external_entry_id=baseline.external_entry_id,
                provider_record_id=baseline.provider_record_id, record_values=baseline.record_values, evidence=conflicting,
            )

    def test_public_api_field_contract_and_no_package_export(self) -> None:
        import scripts.simulation.historical_input_source_records as module

        self.assertTrue(hasattr(HistoricalInputSourceRecord, "__slots__"))
        self.assertEqual(
            tuple(item.name for item in fields(HistoricalInputSourceRecord)),
            (
                "schema_version",
                "record_kind",
                "organization",
                "source_system",
                "external_race_id",
                "external_entry_id",
                "provider_record_id",
                "record_values",
                "evidence",
                "source_id",
            ),
        )
        field_map = {item.name: item for item in fields(HistoricalInputSourceRecord)}
        self.assertEqual(field_map["schema_version"].default, 3)
        self.assertFalse(field_map["schema_version"].init)
        self.assertFalse(field_map["source_id"].init)
        hints = get_type_hints(HistoricalInputSourceRecord)
        self.assertIs(hints["schema_version"], int)
        self.assertIs(hints["source_id"], str)
        self.assertEqual(SourceRecordKind.__args__, ("track", "entry", "jockey", "odds_win", "past_race", "past_race_absence"))
        self.assertEqual(
            {name for name, value in inspect.getmembers(module, inspect.isclass) if not name.startswith("_")},
            {
                "HistoricalInputSourceError",
                "HistoricalInputSourceValidationError",
                "HistoricalInputSourceConflictError",
                "HistoricalInputSourceRecord",
            },
        )
        self.assertEqual(
            {name for name, value in inspect.getmembers(module, inspect.isfunction) if not name.startswith("_")},
            {
                "canonical_historical_input_source_payload",
                "build_historical_input_source_id",
                "validate_historical_input_source_record_set",
            },
        )
        self.assertTrue(issubclass(HistoricalInputSourceValidationError, HistoricalInputSourceError))
        self.assertTrue(issubclass(HistoricalInputSourceConflictError, HistoricalInputSourceError))
        for name in (
            "HistoricalInputSourceRecord",
            "canonical_historical_input_source_payload",
            "build_historical_input_source_id",
            "validate_historical_input_source_record_set",
        ):
            self.assertFalse(hasattr(simulation_package, name))

    def test_six_exact_schemas_nullable_payloads_and_defensive_freeze(self) -> None:
        expected_keys = {
            "track": {"target_race_date", "scheduled_start_at", "place", "distance_m", "track", "track_condition", "race_name", "race_class", "weather"},
            "entry": {"external_entry_id", "external_horse_id", "horse_no"},
            "jockey": {"external_entry_id", "jockey"},
            "odds_win": {"external_entry_id", "horse_no", "win_odds"},
            "past_race": {"race_date", "place", "race_name", "race_class", "distance_m", "track", "weather", "track_condition", "finish", "reference_time_difference_seconds", "race_time", "weight", "weight_diff", "jockey", "popularity", "odds", "passing_order", "fourth_corner_position"},
            "past_race_absence": {"external_entry_id", "query_scope", "result_count"},
        }
        for kind, keys in expected_keys.items():
            with self.subTest(kind=kind):
                original = _values(kind)
                record = _record(kind, record_values=original)
                payload = canonical_historical_input_source_payload(record=record)
                self.assertEqual(set(record.record_values), keys)
                self.assertEqual(set(payload["record_values"]), keys)
                self.assertEqual(
                    set(payload),
                    {
                        "schema_version", "source_system", "record_kind", "organization", "external_race_id",
                        "external_entry_id", "provider_record_id", "record_values", "evidence",
                    },
                )
                self.assertNotIn("available_at", payload)
                self.assertNotIn("observed_at", payload)
                self.assertNotIn("race_id", payload)
                self.assertNotIn("race_entry_id", payload)
                self.assertEqual(payload["schema_version"], 3)
                self.assertTrue(record.source_id.startswith(f"his-v3:{kind}:"))
                self.assertIsInstance(record.record_values, MappingProxyType)
                if kind == "track":
                    self.assertIsNone(payload["external_entry_id"])
                    self.assertEqual(payload["record_values"]["race_name"], None)
                if kind == "past_race_absence":
                    self.assertIsInstance(record.record_values["query_scope"], MappingProxyType)
        absence_values = _values("past_race_absence")
        absence = _record("past_race_absence", record_values=absence_values)
        before = absence.source_id
        absence_values["result_count"] = 4
        absence_values["query_scope"]["strictly_before_target_race"] = False
        self.assertEqual(absence.source_id, before)
        self.assertEqual(absence.record_values["result_count"], 0)
        with self.assertRaises(TypeError):
            absence.record_values["result_count"] = 1
        with self.assertRaises(TypeError):
            absence.record_values["query_scope"]["result_count"] = 1

    def test_schema_type_key_and_scalar_validation(self) -> None:
        for kind in ("track", "entry", "jockey", "odds_win", "past_race", "past_race_absence"):
            with self.subTest(kind=kind, case="missing"):
                values = _values(kind)
                values.pop(next(iter(values)))
                with self.assertRaises(HistoricalInputSourceValidationError):
                    _record(kind, record_values=values)
            with self.subTest(kind=kind, case="extra"):
                values = _values(kind)
                values["unexpected"] = "x"
                with self.assertRaises(HistoricalInputSourceValidationError):
                    _record(kind, record_values=values)
        for invalid_kind in ("unknown", 1, True):
            with self.subTest(invalid_kind=invalid_kind):
                with self.assertRaises(HistoricalInputSourceValidationError):
                    HistoricalInputSourceRecord(
                        record_kind=invalid_kind,  # type: ignore[arg-type]
                        organization="NAR",
                        source_system="nar_official",
                        external_race_id="nar:20260805:1:1",
                        external_entry_id=None,
                        provider_record_id=None,
                        record_values=_values("track"),
                        evidence=_record("track").evidence,
                    )
        values = _values("track"); values["distance_m"] = True
        with self.assertRaises(HistoricalInputSourceValidationError): _record("track", record_values=values)
        values = _values("track"); values["target_race_date"] = datetime(2026, 8, 5, tzinfo=UTC)
        with self.assertRaises(HistoricalInputSourceValidationError): _record("track", record_values=values)
        values = _values("odds_win"); values["win_odds"] = 2.0
        with self.assertRaises(HistoricalInputSourceValidationError): _record("odds_win", record_values=values)
        values = _values("odds_win"); values["win_odds"] = Decimal("0")
        with self.assertRaises(HistoricalInputSourceValidationError): _record("odds_win", record_values=values)
        for bad in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity"), Decimal("-0.01"), 0, True, 0.0):
            with self.subTest(decimal=bad):
                values = _values("past_race"); values["reference_time_difference_seconds"] = bad
                with self.assertRaises(HistoricalInputSourceValidationError): _record("past_race", record_values=values)
        values = _values("past_race"); values["margin"] = Decimal("0")
        with self.assertRaises(HistoricalInputSourceValidationError): _record("past_race", record_values=values)
        values = _values("past_race"); values["margin"] = Decimal("0"); values["reference_time_difference_seconds"] = Decimal("0")
        with self.assertRaises(HistoricalInputSourceValidationError): _record("past_race", record_values=values)
        values = _values("past_race_absence"); values["result_count"] = False
        with self.assertRaises(HistoricalInputSourceValidationError): _record("past_race_absence", record_values=values)
        values = _values("past_race_absence"); values["query_scope"]["strictly_before_target_race"] = 1
        with self.assertRaises(HistoricalInputSourceValidationError): _record("past_race_absence", record_values=values)

    def test_text_decimal_datetime_and_temporal_contract(self) -> None:
        values = _values("past_race")
        values["passing_order"] = ""
        record = _record("past_race", record_values=values)
        self.assertEqual(record.record_values["passing_order"], "")
        self.assertEqual(record.record_values["reference_time_difference_seconds"], Decimal("0"))
        self.assertEqual(record.record_values["weight"], Decimal("480"))
        self.assertEqual(canonical_historical_input_source_payload(record=record)["record_values"]["reference_time_difference_seconds"], "0")
        normalized = _record("jockey", record_values={"external_entry_id": "nar:20260805:1:1:entry:1", "jockey": "Cafe\u0301"})
        self.assertEqual(normalized.record_values["jockey"], "Café")
        tokyo = timezone(timedelta(hours=9))
        observed = OBSERVED.astimezone(tokyo)
        shifted = _record("track", observed_at=observed)
        self.assertEqual(shifted.evidence[0].observed_at, OBSERVED)
        with self.assertRaises(ValueError): _record("track", observed_at=OBSERVED.replace(tzinfo=None))
        with self.assertRaises(ValueError): _record("track", available_at=OBSERVED + timedelta(seconds=1))

    def test_url_validation_policy_and_byte_for_byte_retention(self) -> None:
        valid = "https://EXAMPLE.test/Path/%7e?z=2&a=1"
        record = _record("track", canonical_source_url=valid)
        self.assertEqual(record.evidence[0].canonical_source_url, valid)
        self.assertEqual(canonical_historical_input_source_payload(record=record)["evidence"][0]["canonical_source_url"], valid)
        for invalid in (
            1,
            "",
            "https://example.test/Cafe\u0301",
            " http://example.test ",
            "http://example.test/path",
            "/relative",
            "https:///missing-host",
            "https://user:password@example.test/path",
            "https://example.test/path#fragment",
            "https://example.test/\x01path",
            " https://example.test/path",
        ):
            with self.subTest(url=invalid):
                with self.assertRaises(ValueError):
                    _record("track", canonical_source_url=invalid)  # type: ignore[arg-type]
        self.assertIsNone(_record("track").evidence[0].canonical_source_url)
        self.assertIsNone(_record("entry").evidence[0].canonical_source_url)
        self.assertIsNone(_record("jockey").evidence[0].canonical_source_url)
        self.assertIsNone(_record("odds_win").evidence[0].canonical_source_url)
        self.assertIsNone(_record("past_race").evidence[0].canonical_source_url)
        with self.assertRaises(HistoricalInputSourceValidationError):
            HistoricalInputSourceRecord(
                record_kind="past_race_absence", organization="NAR", source_system="nar_official",
                external_race_id="nar:20260805:1:1", external_entry_id="nar:20260805:1:1:entry:1",
                provider_record_id=None, record_values=_values("past_race_absence"), evidence=(),
            )
        with self.assertRaises(HistoricalInputSourceValidationError):
            HistoricalInputSourceRecord(
                record_kind="past_race", organization="NAR", source_system="nar_official",
                external_race_id="nar:20260805:1:1", external_entry_id="nar:20260805:1:1:entry:1",
                provider_record_id=None, record_values=_values("past_race"), evidence=_record("past_race").evidence,
            )

    def test_deterministic_payload_id_and_timestamp_exclusion(self) -> None:
        one = _record("odds_win")
        two = _record("odds_win", observed_at=OBSERVED + timedelta(days=1), available_at=AVAILABLE + timedelta(days=1))
        self.assertEqual(canonical_historical_input_source_payload(record=one), canonical_historical_input_source_payload(record=two))
        self.assertEqual(one.source_id, two.source_id)
        self.assertEqual(one.source_id, build_historical_input_source_id(record=one))
        changed_values = _values("odds_win"); changed_values["win_odds"] = Decimal("3")
        changed = _record("odds_win", record_values=changed_values)
        self.assertNotEqual(one.source_id, changed.source_id)
        self.assertTrue(one.source_id.startswith("his-v3:odds_win:"))
        self.assertEqual(len(one.source_id.rsplit(":", 1)[1]), 64)

    def test_v3_past_race_factual_change_isolated_to_its_source_id(self) -> None:
        baseline = (
            _record("track"),
            _record("entry"),
            _record("jockey"),
            _record("odds_win"),
            _record("past_race"),
        )
        changed_values = _values("past_race")
        changed_values["reference_time_difference_seconds"] = Decimal("0.2")
        changed_past_race = _record("past_race", record_values=changed_values)
        changed = baseline[:-1] + (changed_past_race,)

        self.assertEqual(validate_historical_input_source_record_set(records=baseline), baseline)
        self.assertEqual(validate_historical_input_source_record_set(records=changed), changed)
        for record in baseline + changed:
            self.assertEqual(record.schema_version, 3)
            self.assertTrue(record.source_id.startswith(f"his-v3:{record.record_kind}:"))

        for original, replacement in zip(baseline[:-1], changed[:-1], strict=True):
            self.assertEqual(original.source_id, replacement.source_id)
            self.assertEqual(
                canonical_historical_input_source_payload(record=original),
                canonical_historical_input_source_payload(record=replacement),
            )

        baseline_past = baseline[-1]
        self.assertNotEqual(baseline_past.source_id, changed_past_race.source_id)
        before = canonical_historical_input_source_payload(record=baseline_past)
        after = canonical_historical_input_source_payload(record=changed_past_race)
        self.assertEqual({key: value for key, value in before.items() if key != "record_values"}, {key: value for key, value in after.items() if key != "record_values"})
        self.assertEqual(
            {key: value for key, value in before["record_values"].items() if key != "reference_time_difference_seconds"},
            {key: value for key, value in after["record_values"].items() if key != "reference_time_difference_seconds"},
        )
        self.assertEqual(before["record_values"]["reference_time_difference_seconds"], "0")
        self.assertEqual(after["record_values"]["reference_time_difference_seconds"], "0.2")

    def test_conflicts_and_set_order(self) -> None:
        track = _record("track")
        entry = _record("entry")
        self.assertEqual(validate_historical_input_source_record_set(records=[entry, track]), (entry, track))
        with self.assertRaises(HistoricalInputSourceConflictError):
            validate_historical_input_source_record_set(records=(track, track))
        first = _record("past_race")
        values = _values("past_race"); values["finish"] = 2
        second = _record("past_race", record_values=values, provider_record_id=first.provider_record_id)
        self.assertNotEqual(first.source_id, second.source_id)
        with self.assertRaises(HistoricalInputSourceConflictError):
            validate_historical_input_source_record_set(records=(first, second))
        with self.assertRaises(HistoricalInputSourceValidationError):
            validate_historical_input_source_record_set(records="not-records")  # type: ignore[arg-type]

    def test_frozen_slots_and_no_side_effect_dependencies(self) -> None:
        record = _record("track")
        self.assertFalse(hasattr(record, "__dict__"))
        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
            record.organization = "other"
        import scripts.simulation.historical_input_source_records as module

        source = inspect.getsource(module)
        tree = ast.parse(source)
        self.assertNotIn("sqlite3", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("open(", source)
        imported_roots = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertFalse({"sqlite3", "requests", "socket"} & imported_roots)


if __name__ == "__main__":
    unittest.main()
