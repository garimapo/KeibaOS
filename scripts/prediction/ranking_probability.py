"""Deterministic strict-ranking Plackett-Luce model probabilities.

This module deliberately owns no raw-prediction normalization, market odds,
expected-value, strategy, persistence, settlement, or clock behavior.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import (
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    ROUND_HALF_EVEN,
    localcontext,
)
import hashlib
from itertools import combinations, permutations
import json
import math
import unicodedata


_SCHEMA_VERSION = 1
_MODEL_NAME = "plackett_luce"
_MODEL_VERSION = "score-softmax-decimal-v1"
_EVENT_MODEL = "strict_finish_order_no_ties_v1"
_CONTENT_VERSION = "formal-bet-probability-plackett-luce-v1"
_BET_TYPES = ("単勝", "馬連", "ワイド", "3連複")
_BET_TYPE_ARITY = {"単勝": 1, "馬連": 2, "ワイド": 2, "3連複": 3}


def _build_arithmetic_context() -> Context:
    context = Context(
        prec=50,
        rounding=ROUND_HALF_EVEN,
        Emin=-999999,
        Emax=999999,
        capitals=1,
        clamp=0,
    )
    for signal in context.traps:
        context.traps[signal] = False
    context.traps[InvalidOperation] = True
    context.traps[DivisionByZero] = True
    context.traps[Overflow] = True
    context.clear_flags()
    return context


_ARITHMETIC_CONTEXT = _build_arithmetic_context()


def _rounding_envelope(*, rounded_operation_count: int) -> Decimal:
    """Return the fixed-context forward-error envelope at probability scale.

    A precision-p base-10 operation has relative roundoff bounded by one unit
    in its last significant place, ``10 ** (1 - p)``.  The usual sequential
    error bound for n rounded operations is gamma(n) = n*u/(1-n*u).  All
    probability intermediates accepted by this module are non-negative and at
    most one, so gamma(n) is also a conservative absolute envelope here.
    """

    if type(rounded_operation_count) is not int or rounded_operation_count <= 0:
        raise ValueError("rounded_operation_count must be a positive built-in int")
    with localcontext(_ARITHMETIC_CONTEXT):
        unit_roundoff = Decimal(1).scaleb(1 - _ARITHMETIC_CONTEXT.prec)
        accumulated = Decimal(rounded_operation_count) * unit_roundoff
        if accumulated >= 1:
            raise ValueError("rounding-operation count exceeds the fixed context")
        return accumulated / (Decimal(1) - accumulated)


def _ordered_prefix_rounding_operation_count(
    *,
    field_size: int,
    prefix_length: int,
) -> int:
    # At rank r, rebuilding the remaining total takes at most field_size-r
    # additions, followed by one division and one product.  Counting every
    # addition is conservative (the first add-to-zero is exact).
    return sum(field_size - rank + 2 for rank in range(prefix_length))


def _require_race_entry_id(value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError("race_entry_id must be a positive built-in int")
    return value


def _require_decimal(value: object, *, name: str, positive: bool) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if positive and value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _decimal_text(value: Decimal, *, context: Context) -> str:
    if value.is_zero():
        return "0"
    normalized = value.normalize(context=context)
    return format(normalized, "f")


@dataclass(frozen=True, slots=True)
class RaceEntryModelScore:
    race_entry_id: int
    prediction_score: float
    prediction_score_float_hex: str = field(init=False)

    def __post_init__(self) -> None:
        _require_race_entry_id(self.race_entry_id)
        if type(self.prediction_score) is not float:
            raise TypeError("prediction_score must be an exact built-in float")
        if not math.isfinite(self.prediction_score):
            raise ValueError("prediction_score must be finite")
        if self.prediction_score < 0:
            raise ValueError("prediction_score must be non-negative")
        object.__setattr__(
            self,
            "prediction_score_float_hex",
            self.prediction_score.hex(),
        )


@dataclass(frozen=True, slots=True)
class RaceEntryLatentWeight:
    race_entry_id: int
    latent_weight: Decimal

    def __post_init__(self) -> None:
        _require_race_entry_id(self.race_entry_id)
        _require_decimal(self.latent_weight, name="latent_weight", positive=True)


@dataclass(frozen=True, slots=True)
class BetSelectionModelProbability:
    bet_type: str
    race_entry_ids: tuple[int, ...]
    model_probability: Decimal

    def __post_init__(self) -> None:
        if type(self.bet_type) is not str or self.bet_type not in _BET_TYPE_ARITY:
            raise ValueError("unsupported bet_type")
        if type(self.race_entry_ids) is not tuple:
            raise TypeError("race_entry_ids must be an exact tuple")
        expected_arity = _BET_TYPE_ARITY[self.bet_type]
        if len(self.race_entry_ids) != expected_arity:
            raise ValueError("race_entry_ids has invalid cardinality")
        if any(type(value) is not int or value <= 0 for value in self.race_entry_ids):
            raise ValueError("race_entry_ids must contain positive built-in ints")
        if tuple(sorted(self.race_entry_ids)) != self.race_entry_ids:
            raise ValueError("race_entry_ids must be in ascending canonical order")
        if len(set(self.race_entry_ids)) != len(self.race_entry_ids):
            raise ValueError("race_entry_ids must not contain duplicates")
        probability = _require_decimal(
            self.model_probability,
            name="model_probability",
            positive=True,
        )
        if probability > 1:
            raise ValueError("model_probability must be no greater than one")


@dataclass(frozen=True, slots=True, init=False)
class PlackettLuceBetProbabilitySet:
    schema_version: int
    model_name: str
    model_version: str
    event_model: str
    temperature: Decimal
    entry_scores: tuple[RaceEntryModelScore, ...]
    latent_weights: tuple[RaceEntryLatentWeight, ...]
    probabilities: tuple[BetSelectionModelProbability, ...]
    probability_content_sha256: str = field(init=False)

    @classmethod
    def _create(
        cls,
        *,
        temperature: Decimal,
        entry_scores: tuple[RaceEntryModelScore, ...],
        latent_weights: tuple[RaceEntryLatentWeight, ...],
        probabilities: tuple[BetSelectionModelProbability, ...],
        probability_content_sha256: str,
    ) -> PlackettLuceBetProbabilitySet:
        value = object.__new__(cls)
        object.__setattr__(value, "schema_version", _SCHEMA_VERSION)
        object.__setattr__(value, "model_name", _MODEL_NAME)
        object.__setattr__(value, "model_version", _MODEL_VERSION)
        object.__setattr__(value, "event_model", _EVENT_MODEL)
        object.__setattr__(value, "temperature", temperature)
        object.__setattr__(value, "entry_scores", entry_scores)
        object.__setattr__(value, "latent_weights", latent_weights)
        object.__setattr__(value, "probabilities", probabilities)
        object.__setattr__(
            value,
            "probability_content_sha256",
            probability_content_sha256,
        )
        return value


def _ordered_prefix_probability(
    ordered_entry_ids: tuple[int, ...],
    *,
    weights_by_id: dict[int, Decimal],
    total_weight: Decimal,
) -> Decimal:
    if not ordered_entry_ids:
        raise ValueError("ordered prefix must not be empty")
    if len(set(ordered_entry_ids)) != len(ordered_entry_ids):
        raise ValueError("ordered prefix must not contain duplicates")
    if any(entry_id not in weights_by_id for entry_id in ordered_entry_ids):
        raise ValueError("ordered prefix contains an unknown race_entry_id")

    remaining_entry_ids = list(weights_by_id)
    remaining_weight = total_weight
    probability = Decimal(1)
    for entry_id in ordered_entry_ids:
        weight = weights_by_id[entry_id]
        probability *= weight / remaining_weight
        remaining_entry_ids.remove(entry_id)
        if remaining_entry_ids:
            # Re-summing the authoritative remaining set avoids cancellation
            # from repeatedly subtracting small weights from a rounded total.
            remaining_weight = sum(
                (weights_by_id[item] for item in remaining_entry_ids),
                Decimal(0),
            )
    return _validate_probability(probability)


def _validate_probability(
    probability: Decimal,
    *,
    complete_event: bool = False,
    rounded_operation_count: int | None = None,
) -> Decimal:
    with localcontext(_ARITHMETIC_CONTEXT):
        if not probability.is_finite() or probability < 0:
            raise ValueError("calculated probability is outside [0, 1]")
        if probability <= 1:
            return probability
        if complete_event:
            if rounded_operation_count is None:
                raise ValueError("complete-event validation requires an operation count")
            excess = probability - Decimal(1)
            if excess <= _rounding_envelope(
                rounded_operation_count=rounded_operation_count,
            ):
                return Decimal(1)
        raise ValueError("calculated probability is outside [0, 1]")


def _accumulate_ordered_event_probability(
    orders: Sequence[tuple[int, ...]],
    *,
    weights_by_id: dict[int, Decimal],
    total_weight: Decimal,
    complete_event: bool,
) -> Decimal:
    exact_orders = tuple(orders)
    if not exact_orders:
        raise ValueError("ordered event must not be empty")
    prefix_length = len(exact_orders[0])
    if prefix_length <= 0 or any(len(order) != prefix_length for order in exact_orders):
        raise ValueError("ordered event prefixes must have one exact length")

    terms = tuple(
        _ordered_prefix_probability(
            order,
            weights_by_id=weights_by_id,
            total_weight=total_weight,
        )
        for order in exact_orders
    )
    probability = sum(terms, Decimal(0))
    per_term_operations = _ordered_prefix_rounding_operation_count(
        field_size=len(weights_by_id),
        prefix_length=prefix_length,
    )
    rounded_operation_count = (
        len(terms) * per_term_operations + max(len(terms) - 1, 0)
    )
    return _validate_probability(
        probability,
        complete_event=complete_event,
        rounded_operation_count=rounded_operation_count,
    )


def _canonical_payload(
    *,
    temperature: Decimal,
    entry_scores: tuple[RaceEntryModelScore, ...],
    latent_weights: tuple[RaceEntryLatentWeight, ...],
    probabilities: tuple[BetSelectionModelProbability, ...],
    context: Context,
) -> dict[str, object]:
    return {
        "content_version": _CONTENT_VERSION,
        "entry_scores": [
            {
                "prediction_score_float_hex": item.prediction_score_float_hex,
                "race_entry_id": item.race_entry_id,
            }
            for item in entry_scores
        ],
        "event_model": _EVENT_MODEL,
        "latent_weights": [
            {
                "latent_weight": _decimal_text(item.latent_weight, context=context),
                "race_entry_id": item.race_entry_id,
            }
            for item in latent_weights
        ],
        "model_name": _MODEL_NAME,
        "model_version": _MODEL_VERSION,
        "probabilities": [
            {
                "bet_type": item.bet_type,
                "model_probability": _decimal_text(
                    item.model_probability,
                    context=context,
                ),
                "race_entry_ids": list(item.race_entry_ids),
            }
            for item in probabilities
        ],
        "schema_version": _SCHEMA_VERSION,
        "temperature": _decimal_text(temperature, context=context),
    }


def _content_sha256(payload: dict[str, object]) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    canonical = unicodedata.normalize("NFC", serialized).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def calculate_plackett_luce_bet_probabilities(
    *,
    entry_scores: Sequence[RaceEntryModelScore],
    temperature: Decimal,
) -> PlackettLuceBetProbabilitySet:
    """Calculate every supported strict-order model probability for one field."""

    if not isinstance(entry_scores, Sequence) or isinstance(
        entry_scores,
        (str, bytes, bytearray),
    ):
        raise TypeError("entry_scores must be a sequence")
    supplied_scores = tuple(entry_scores)
    if not supplied_scores:
        raise ValueError("entry_scores must not be empty")
    validated_scores: list[RaceEntryModelScore] = []
    for item in supplied_scores:
        if type(item) is not RaceEntryModelScore:
            raise TypeError("entry_scores must contain RaceEntryModelScore values")
        reconstructed = RaceEntryModelScore(item.race_entry_id, item.prediction_score)
        if reconstructed != item:
            raise ValueError("entry score derived identity is inconsistent")
        validated_scores.append(reconstructed)
    if len({item.race_entry_id for item in validated_scores}) != len(validated_scores):
        raise ValueError("entry_scores must not contain duplicate race_entry_id values")
    canonical_scores = tuple(sorted(validated_scores, key=lambda item: item.race_entry_id))
    exact_temperature = _require_decimal(
        temperature,
        name="temperature",
        positive=True,
    )

    try:
        with localcontext(_ARITHMETIC_CONTEXT) as context:
            decimal_scores = {
                item.race_entry_id: Decimal.from_float(item.prediction_score)
                for item in canonical_scores
            }
            maximum_score = max(decimal_scores.values())
            weights_by_id: dict[int, Decimal] = {}
            for item in canonical_scores:
                exponent = (decimal_scores[item.race_entry_id] - maximum_score) / exact_temperature
                weight = exponent.exp(context=context)
                if not weight.is_finite() or weight <= 0:
                    raise ValueError("score/temperature produced an invalid latent weight")
                weights_by_id[item.race_entry_id] = weight

            latent_weights = tuple(
                RaceEntryLatentWeight(
                    race_entry_id=item.race_entry_id,
                    latent_weight=weights_by_id[item.race_entry_id],
                )
                for item in canonical_scores
            )
            total_weight = sum(weights_by_id.values(), Decimal(0))
            if not total_weight.is_finite() or total_weight <= 0:
                raise ValueError("latent weight total must be positive and finite")

            entry_ids = tuple(item.race_entry_id for item in canonical_scores)
            calculated: list[BetSelectionModelProbability] = []

            for entry_id in entry_ids:
                probability = _validate_probability(
                    weights_by_id[entry_id] / total_weight,
                    complete_event=len(entry_ids) == 1,
                    rounded_operation_count=2,
                )
                calculated.append(
                    BetSelectionModelProbability("単勝", (entry_id,), probability)
                )

            if len(entry_ids) >= 2:
                for selection in combinations(entry_ids, 2):
                    probability = _accumulate_ordered_event_probability(
                        tuple(permutations(selection)),
                        weights_by_id=weights_by_id,
                        total_weight=total_weight,
                        complete_event=len(entry_ids) == 2,
                    )
                    calculated.append(
                        BetSelectionModelProbability(
                            "馬連",
                            selection,
                            probability,
                        )
                    )

            if len(entry_ids) >= 3:
                for selection in combinations(entry_ids, 2):
                    orders: list[tuple[int, ...]] = []
                    for third_entry_id in entry_ids:
                        if third_entry_id in selection:
                            continue
                        orders.extend(permutations((*selection, third_entry_id)))
                    probability = _accumulate_ordered_event_probability(
                        orders,
                        weights_by_id=weights_by_id,
                        total_weight=total_weight,
                        complete_event=len(entry_ids) == 3,
                    )
                    calculated.append(
                        BetSelectionModelProbability(
                            "ワイド",
                            selection,
                            probability,
                        )
                    )

                for selection in combinations(entry_ids, 3):
                    probability = _accumulate_ordered_event_probability(
                        tuple(permutations(selection)),
                        weights_by_id=weights_by_id,
                        total_weight=total_weight,
                        complete_event=len(entry_ids) == 3,
                    )
                    calculated.append(
                        BetSelectionModelProbability(
                            "3連複",
                            selection,
                            probability,
                        )
                    )

            probabilities = tuple(calculated)
            payload = _canonical_payload(
                temperature=exact_temperature,
                entry_scores=canonical_scores,
                latent_weights=latent_weights,
                probabilities=probabilities,
                context=context,
            )
            content_sha256 = _content_sha256(payload)
    except DecimalException as exc:
        raise ValueError("Decimal probability calculation failed") from exc

    return PlackettLuceBetProbabilitySet._create(
        temperature=exact_temperature,
        entry_scores=canonical_scores,
        latent_weights=latent_weights,
        probabilities=probabilities,
        probability_content_sha256=content_sha256,
    )


__all__ = [
    "BetSelectionModelProbability",
    "PlackettLuceBetProbabilitySet",
    "RaceEntryLatentWeight",
    "RaceEntryModelScore",
    "calculate_plackett_luce_bet_probabilities",
]
