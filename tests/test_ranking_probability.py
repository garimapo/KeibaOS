"""Tests for the deterministic strict-ranking probability core."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import (
    Context,
    Decimal,
    ROUND_DOWN,
    ROUND_HALF_EVEN,
    getcontext,
    localcontext,
    setcontext,
)
import inspect
import math
from pathlib import Path
import unittest

import scripts.prediction.ranking_probability as ranking_probability
from scripts.models import Prediction
from scripts.prediction.ranking_probability import (
    BetSelectionModelProbability,
    PlackettLuceBetProbabilitySet,
    RaceEntryLatentWeight,
    RaceEntryModelScore,
    calculate_plackett_luce_bet_probabilities,
)
from scripts.prediction.value_engine import ValueEngine


_CONTEXT = Context(
    prec=50,
    rounding=ROUND_HALF_EVEN,
    Emin=-999999,
    Emax=999999,
    capitals=1,
    clamp=0,
)
_TOLERANCE = Decimal("1e-47")


def _scores(*items: tuple[int, float]) -> tuple[RaceEntryModelScore, ...]:
    return tuple(RaceEntryModelScore(entry_id, score) for entry_id, score in items)


def _calculate(
    items: tuple[tuple[int, float], ...] = (
        (1, 40.0),
        (2, 30.0),
        (3, 20.0),
        (4, 10.0),
    ),
    *,
    temperature: Decimal = Decimal("10"),
) -> PlackettLuceBetProbabilitySet:
    return calculate_plackett_luce_bet_probabilities(
        entry_scores=_scores(*items),
        temperature=temperature,
    )


def _probability(
    result: PlackettLuceBetProbabilitySet,
    bet_type: str,
    selection: tuple[int, ...],
) -> Decimal:
    matches = [
        item.model_probability
        for item in result.probabilities
        if item.bet_type == bet_type and item.race_entry_ids == selection
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one probability for {bet_type} {selection}")
    return matches[0]


def _sum_for_type(result: PlackettLuceBetProbabilitySet, bet_type: str) -> Decimal:
    with localcontext(_CONTEXT):
        return sum(
            (
                item.model_probability
                for item in result.probabilities
                if item.bet_type == bet_type
            ),
            Decimal(0),
        )


def _ordered_probability(
    order: tuple[int, ...],
    weights: dict[int, Decimal],
    total: Decimal,
) -> Decimal:
    remaining_ids = list(weights)
    remaining = total
    probability = Decimal(1)
    for entry_id in order:
        probability *= weights[entry_id] / remaining
        remaining_ids.remove(entry_id)
        if remaining_ids:
            remaining = sum((weights[item] for item in remaining_ids), Decimal(0))
    return probability


class RankingProbabilityTest(unittest.TestCase):
    def test_public_api_shape_versions_and_frozen_values(self) -> None:
        result = _calculate()

        self.assertTrue(is_dataclass(RaceEntryModelScore))
        self.assertTrue(is_dataclass(RaceEntryLatentWeight))
        self.assertTrue(is_dataclass(BetSelectionModelProbability))
        self.assertTrue(is_dataclass(PlackettLuceBetProbabilitySet))
        self.assertEqual(
            [item.name for item in fields(RaceEntryModelScore)],
            ["race_entry_id", "prediction_score", "prediction_score_float_hex"],
        )
        self.assertEqual(result.schema_version, 1)
        self.assertEqual(result.model_name, "plackett_luce")
        self.assertEqual(result.model_version, "score-softmax-decimal-v1")
        self.assertEqual(result.event_model, "strict_finish_order_no_ties_v1")
        self.assertRegex(result.probability_content_sha256, r"^[0-9a-f]{64}$")
        with self.assertRaises(FrozenInstanceError):
            result.temperature = Decimal("2")  # type: ignore[misc]

        signature = inspect.signature(calculate_plackett_luce_bet_probabilities)
        self.assertEqual(tuple(signature.parameters), ("entry_scores", "temperature"))
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            )
        )

    def test_result_construction_is_factory_only(self) -> None:
        result = _calculate()
        with self.assertRaises(TypeError):
            PlackettLuceBetProbabilitySet(
                schema_version=1,
                model_name="plackett_luce",
                model_version="score-softmax-decimal-v1",
                event_model="strict_finish_order_no_ties_v1",
                temperature=result.temperature,
                entry_scores=result.entry_scores,
                latent_weights=result.latent_weights,
                probabilities=result.probabilities,
            )
        with self.assertRaises(TypeError):
            replace(result, temperature=Decimal("20"))

    def test_score_validation_and_exact_binary64_identity(self) -> None:
        score = RaceEntryModelScore(7, 0.1)
        self.assertEqual(score.prediction_score_float_hex, (0.1).hex())
        self.assertEqual(RaceEntryModelScore(8, 0.0).prediction_score, 0.0)

        for invalid in (-1.0, float("nan"), float("inf"), float("-inf")):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    RaceEntryModelScore(1, invalid)
        for invalid in (True, 1, Decimal("1"), "1"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    RaceEntryModelScore(1, invalid)  # type: ignore[arg-type]
        for invalid_id in (0, -1, True, 1.5):
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(ValueError):
                    RaceEntryModelScore(invalid_id, 1.0)  # type: ignore[arg-type]

    def test_empty_duplicate_and_non_sequence_fields_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate_plackett_luce_bet_probabilities(
                entry_scores=(),
                temperature=Decimal("10"),
            )

        tampered = RaceEntryModelScore(1, 10.0)
        object.__setattr__(tampered, "prediction_score_float_hex", (20.0).hex())
        with self.assertRaises(ValueError):
            calculate_plackett_luce_bet_probabilities(
                entry_scores=(tampered,),
                temperature=Decimal("10"),
            )
        with self.assertRaises(ValueError):
            calculate_plackett_luce_bet_probabilities(
                entry_scores=_scores((1, 10.0), (1, 20.0)),
                temperature=Decimal("10"),
            )
        with self.assertRaises(TypeError):
            calculate_plackett_luce_bet_probabilities(
                entry_scores=(item for item in _scores((1, 10.0))),  # type: ignore[arg-type]
                temperature=Decimal("10"),
            )

    def test_temperature_validation_is_exact_and_has_no_default(self) -> None:
        signature = inspect.signature(calculate_plackett_luce_bet_probabilities)
        self.assertIs(signature.parameters["temperature"].default, inspect.Parameter.empty)
        for invalid in (
            Decimal("0"),
            Decimal("-1"),
            Decimal("NaN"),
            Decimal("Infinity"),
            Decimal("-Infinity"),
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    calculate_plackett_luce_bet_probabilities(
                        entry_scores=_scores((1, 10.0)),
                        temperature=invalid,
                    )
        for invalid in (10.0, 10, True, "10"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    calculate_plackett_luce_bet_probabilities(
                        entry_scores=_scores((1, 10.0)),
                        temperature=invalid,  # type: ignore[arg-type]
                    )

    def test_numerically_unrepresentable_positive_weight_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            calculate_plackett_luce_bet_probabilities(
                entry_scores=_scores((1, float("1e308")), (2, 0.0)),
                temperature=Decimal("1"),
            )

    def test_single_entry_has_only_win_probability_one(self) -> None:
        result = _calculate(((11, 0.0),))
        self.assertEqual(
            result.probabilities,
            (BetSelectionModelProbability("単勝", (11,), Decimal(1)),),
        )
        self.assertEqual(result.latent_weights[0].latent_weight, Decimal(1))

    def test_equal_score_four_entry_probabilities_are_hand_computable(self) -> None:
        result = _calculate(((1, 5.0), (2, 5.0), (3, 5.0), (4, 5.0)))

        self.assertEqual(_probability(result, "単勝", (1,)), Decimal("0.25"))
        with localcontext(_CONTEXT):
            equal_weights = {entry_id: Decimal(1) for entry_id in (1, 2, 3, 4)}
            enumerated_quinella = _ordered_probability(
                (1, 2), equal_weights, Decimal(4)
            ) + _ordered_probability((2, 1), equal_weights, Decimal(4))
            self.assertEqual(
                _probability(result, "馬連", (1, 2)),
                enumerated_quinella,
            )
            self.assertLessEqual(
                abs(enumerated_quinella - Decimal(1) / Decimal(6)),
                _TOLERANCE,
            )
        self.assertLessEqual(
            abs(_probability(result, "ワイド", (1, 2)) - Decimal("0.5")),
            _TOLERANCE,
        )
        self.assertLessEqual(
            abs(_probability(result, "3連複", (1, 2, 3)) - Decimal("0.25")),
            _TOLERANCE,
        )

    def test_first_place_is_exact_weight_normalization(self) -> None:
        result = _calculate()
        weights = {item.race_entry_id: item.latent_weight for item in result.latent_weights}
        with localcontext(_CONTEXT):
            total = sum(weights.values(), Decimal(0))
            for entry_id, weight in weights.items():
                self.assertEqual(
                    _probability(result, "単勝", (entry_id,)),
                    weight / total,
                )

    def test_win_matches_intended_softmax_and_legacy_with_tolerance(self) -> None:
        items = ((1, 60.0), (2, 40.0), (3, 10.0))
        result = _calculate(items)
        with localcontext(_CONTEXT):
            exact_scores = [Decimal.from_float(score) for _, score in items]
            maximum = max(exact_scores)
            weights = [((score - maximum) / Decimal("10")).exp() for score in exact_scores]
            total = sum(weights, Decimal(0))
            expected = [weight / total for weight in weights]
        self.assertEqual(
            [_probability(result, "単勝", (entry_id,)) for entry_id, _ in items],
            expected,
        )

        predictions = [Prediction(1, "", "", score, False, "", entry_id) for entry_id, score in items]
        legacy = ValueEngine(temperature=10.0).evaluate(predictions, {})
        for formal, old in zip(expected, legacy):
            self.assertLessEqual(
                abs(float(formal) - old.estimated_win_probability),
                1e-15,
            )

    def test_quinella_is_exact_two_order_sum_not_product_heuristic(self) -> None:
        result = _calculate()
        weights = {item.race_entry_id: item.latent_weight for item in result.latent_weights}
        with localcontext(_CONTEXT):
            total = sum(weights.values(), Decimal(0))
            expected = _ordered_probability((1, 2), weights, total)
            expected += _ordered_probability((2, 1), weights, total)
            heuristic = (
                Decimal(2)
                * _probability(result, "単勝", (1,))
                * _probability(result, "単勝", (2,))
            )
        actual = _probability(result, "馬連", (1, 2))
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, heuristic)

    def test_trio_is_exact_six_order_sum_not_product_heuristic(self) -> None:
        result = _calculate()
        weights = {item.race_entry_id: item.latent_weight for item in result.latent_weights}
        with localcontext(_CONTEXT):
            total = sum(weights.values(), Decimal(0))
            expected = Decimal(0)
            for first, second, third in (
                (1, 2, 3),
                (1, 3, 2),
                (2, 1, 3),
                (2, 3, 1),
                (3, 1, 2),
                (3, 2, 1),
            ):
                expected += _ordered_probability(
                    (first, second, third),
                    weights,
                    total,
                )
            heuristic = Decimal(6)
            for entry_id in (1, 2, 3):
                heuristic *= _probability(result, "単勝", (entry_id,))
        actual = _probability(result, "3連複", (1, 2, 3))
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, heuristic)

    def test_wide_is_exact_top_three_inclusion_and_not_quinella(self) -> None:
        result = _calculate()
        weights = {item.race_entry_id: item.latent_weight for item in result.latent_weights}
        with localcontext(_CONTEXT):
            total = sum(weights.values(), Decimal(0))
            expected = Decimal(0)
            ordered_events: set[tuple[int, int, int]] = set()
            for third_entry_id in (3, 4):
                for order in (
                    (1, 2, third_entry_id),
                    (1, third_entry_id, 2),
                    (2, 1, third_entry_id),
                    (2, third_entry_id, 1),
                    (third_entry_id, 1, 2),
                    (third_entry_id, 2, 1),
                    ):
                    ordered_events.add(order)
                    expected += _ordered_probability(order, weights, total)
        self.assertEqual(len(ordered_events), 12)
        actual = _probability(result, "ワイド", (1, 2))
        self.assertEqual(actual, expected)
        self.assertGreater(actual, _probability(result, "馬連", (1, 2)))

    def test_partition_masses_follow_strict_ranking_events(self) -> None:
        result = _calculate()
        self.assertLessEqual(abs(_sum_for_type(result, "単勝") - 1), _TOLERANCE)
        self.assertLessEqual(abs(_sum_for_type(result, "馬連") - 1), _TOLERANCE)
        self.assertLessEqual(abs(_sum_for_type(result, "3連複") - 1), _TOLERANCE)
        self.assertLessEqual(abs(_sum_for_type(result, "ワイド") - 3), _TOLERANCE)

    def test_complete_events_canonicalize_fixed_context_rounding_to_one(self) -> None:
        quinella = _calculate(
            (
                (1, float.fromhex("0x1.633835cf14e88p+5")),
                (2, float.fromhex("0x1.316e730dde50cp+4")),
            )
        )
        self.assertEqual(_probability(quinella, "馬連", (1, 2)), Decimal(1))
        self.assertEqual(_sum_for_type(quinella, "馬連"), Decimal(1))

        three_entries = _calculate(
            (
                (1, float.fromhex("0x1.d752a9e81a3d6p+3")),
                (2, float.fromhex("0x1.0649c53936977p+6")),
                (3, float.fromhex("0x1.cf2afa84267ecp+4")),
            )
        )
        self.assertEqual(_probability(three_entries, "3連複", (1, 2, 3)), Decimal(1))
        self.assertEqual(_sum_for_type(three_entries, "3連複"), Decimal(1))
        for pair in ((1, 2), (1, 3), (2, 3)):
            with self.subTest(pair=pair):
                self.assertEqual(_probability(three_entries, "ワイド", pair), Decimal(1))

    def test_complete_event_rounding_envelope_is_not_an_unconditional_clamp(self) -> None:
        operation_count = 101
        envelope = ranking_probability._rounding_envelope(
            rounded_operation_count=operation_count,
        )
        with localcontext(_CONTEXT):
            tiny_excess = Decimal(1) + envelope
        self.assertEqual(
            ranking_probability._validate_probability(
                tiny_excess,
                complete_event=True,
                rounded_operation_count=operation_count,
            ),
            Decimal(1),
        )
        with self.assertRaises(ValueError):
            ranking_probability._validate_probability(
                Decimal("1.0001"),
                complete_event=True,
                rounded_operation_count=operation_count,
            )
        with self.assertRaises(ValueError):
            ranking_probability._validate_probability(
                Decimal("1.0000000000000000000000000000000000000000000000001"),
            )

    def test_canonical_order_and_candidate_identity_are_input_order_independent(self) -> None:
        forward = _calculate()
        reverse = _calculate(((4, 10.0), (3, 20.0), (2, 30.0), (1, 40.0)))

        self.assertEqual(forward, reverse)
        self.assertEqual(forward.probability_content_sha256, reverse.probability_content_sha256)
        self.assertEqual([item.race_entry_id for item in forward.entry_scores], [1, 2, 3, 4])
        keys = [(item.bet_type, item.race_entry_ids) for item in forward.probabilities]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(keys[:4], [("単勝", (1,)), ("単勝", (2,)), ("単勝", (3,)), ("単勝", (4,))])
        self.assertEqual(keys[4:10], [("馬連", pair) for pair in ((1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4))])
        self.assertEqual(keys[10:16], [("ワイド", pair) for pair in ((1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4))])

    def test_all_probabilities_and_weights_are_exact_finite_decimals(self) -> None:
        result = _calculate()
        for item in result.latent_weights:
            self.assertIs(type(item.latent_weight), Decimal)
            self.assertTrue(item.latent_weight.is_finite())
            self.assertGreater(item.latent_weight, 0)
        for item in result.probabilities:
            self.assertIs(type(item.model_probability), Decimal)
            self.assertTrue(item.model_probability.is_finite())
            self.assertGreaterEqual(item.model_probability, 0)
            self.assertLessEqual(item.model_probability, 1)

    def test_derived_value_classes_reject_malformed_candidates(self) -> None:
        with self.assertRaises(ValueError):
            RaceEntryLatentWeight(1, Decimal(0))
        with self.assertRaises(ValueError):
            BetSelectionModelProbability("馬連", (1,), Decimal("0.5"))
        with self.assertRaises(ValueError):
            BetSelectionModelProbability("馬連", (1, 1), Decimal("0.5"))
        with self.assertRaises(ValueError):
            BetSelectionModelProbability("馬連", (2, 1), Decimal("0.5"))
        with self.assertRaises(ValueError):
            BetSelectionModelProbability("馬単", (1, 2), Decimal("0.5"))
        with self.assertRaises(ValueError):
            BetSelectionModelProbability("単勝", (1,), Decimal("1.1"))
        with self.assertRaises(ValueError):
            BetSelectionModelProbability("単勝", (1,), Decimal(0))

    def test_ambient_decimal_context_and_repeated_calls_do_not_change_output(self) -> None:
        original = getcontext().copy()
        try:
            baseline = _calculate()
            getcontext().prec = 7
            getcontext().rounding = ROUND_DOWN
            altered = _calculate()
            getcontext().prec = 83
            getcontext().rounding = ROUND_HALF_EVEN
            repeated = _calculate()
        finally:
            setcontext(original)

        self.assertEqual(baseline, altered)
        self.assertEqual(baseline, repeated)
        self.assertEqual(
            baseline.probability_content_sha256,
            altered.probability_content_sha256,
        )

    def test_decimal_temperature_representation_is_canonical(self) -> None:
        plain = _calculate(temperature=Decimal("10"))
        trailing = _calculate(temperature=Decimal("10.000"))
        self.assertEqual(plain, trailing)
        self.assertEqual(plain.probability_content_sha256, trailing.probability_content_sha256)

    def test_semantic_score_or_temperature_change_changes_content_identity(self) -> None:
        baseline = _calculate()
        changed_score = _calculate(((1, 41.0), (2, 30.0), (3, 20.0), (4, 10.0)))
        changed_temperature = _calculate(temperature=Decimal("11"))
        self.assertNotEqual(
            baseline.probability_content_sha256,
            changed_score.probability_content_sha256,
        )
        self.assertNotEqual(
            baseline.probability_content_sha256,
            changed_temperature.probability_content_sha256,
        )

    def test_no_tie_or_dead_heat_probability_is_exposed(self) -> None:
        result = _calculate()
        self.assertEqual(
            {item.bet_type for item in result.probabilities},
            {"単勝", "馬連", "ワイド", "3連複"},
        )
        self.assertFalse(hasattr(result, "tie_probability"))
        self.assertFalse(hasattr(result, "dead_heat_probability"))

    def test_production_module_has_only_pure_allowed_dependencies(self) -> None:
        source_path = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "prediction"
            / "ranking_probability.py"
        )
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        forbidden_fragments = (
            "value_engine",
            "bet_generator",
            "bet_strategy",
            "settlement",
            "payout",
            "sqlite",
            "repository",
            "requests",
            "urllib",
            "httpx",
            "datetime",
            "random",
            "uuid",
        )
        self.assertFalse(
            [name for name in imports if any(fragment in name for fragment in forbidden_fragments)]
        )
        self.assertNotIn("execute(", source)
        self.assertNotIn("executemany(", source)
        self.assertNotIn("executescript(", source)
        self.assertNotIn("expected_value", source)
        self.assertNotIn("market_odds", source)


if __name__ == "__main__":
    unittest.main()
