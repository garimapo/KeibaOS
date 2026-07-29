"""Readonly structural input contracts for prediction evaluation."""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence


class PastRaceInput(Protocol):
    """Readonly past-race data required by the prediction engines."""

    @property
    def horse_id(self) -> int: ...

    @property
    def race_date(self) -> str: ...

    @property
    def place(self) -> str: ...

    @property
    def race_name(self) -> str: ...

    @property
    def race_class(self) -> str: ...

    @property
    def distance(self) -> int: ...

    @property
    def track(self) -> str: ...

    @property
    def weather(self) -> str: ...

    @property
    def track_condition(self) -> str: ...

    @property
    def finish(self) -> int: ...

    @property
    def margin(self) -> float: ...

    @property
    def time(self) -> str: ...

    @property
    def weight(self) -> float: ...

    @property
    def weight_diff(self) -> float: ...

    @property
    def jockey(self) -> str: ...

    @property
    def popularity(self) -> int: ...

    @property
    def odds(self) -> float: ...

    @property
    def passing_order(self) -> str: ...

    @property
    def fourth_corner_position(self) -> int: ...


class RaceTrackConditionsInput(Protocol):
    """Readonly race-track data required by the track engine."""

    @property
    def place(self) -> str: ...

    @property
    def distance(self) -> int: ...

    @property
    def track(self) -> str: ...

    @property
    def track_condition(self) -> str: ...


class PredictionPipelineInput(Protocol):
    """Readonly structural input accepted by the prediction pipeline."""

    @property
    def horse_past_races(self) -> Mapping[int, Sequence[PastRaceInput]]: ...

    @property
    def jockey_names_by_horse(self) -> Mapping[int, str]: ...

    @property
    def track_conditions(self) -> RaceTrackConditionsInput: ...

    @property
    def odds_by_horse(self) -> Mapping[int, object]: ...

    @property
    def race_horse_count(self) -> int: ...

    @property
    def race_id(self) -> int: ...

    @property
    def prediction_time(self) -> str: ...
