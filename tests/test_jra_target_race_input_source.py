from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import inspect

import pytest

from scripts.simulation.jra_official_response_capture import JRASuppliedOfficialResponse
from scripts.simulation.jra_target_race_input_source import (
    JRATargetRaceSourceCollection,
    JRATargetRaceSourceUnsupportedError,
    JRATargetRaceSourceValidationError,
    normalize_jra_target_race_input_source_records,
)


URL = "https://www.jra.go.jp/JRADB/accessD.html?CNAME=pw01dde0105202501010120250105%2FAB"
OBSERVED = datetime(2025, 1, 5, 1, 0, tzinfo=timezone.utc)


def _row(number: int, horse: str, *, odds: str = "2.5", anchor: bool = True) -> str:
    link = f'<a href="/JRADB/accessU.html?CNAME=pw01dud00{horse}%2FAB">horse</a>' if anchor else ""
    return f'''<tr><td class="num">{number}</td><td class="horse"><div class="name_line"><div class="name">{link}</div><div class="odds"><div class="odds_line"><span class="num">{odds}</span></div></div></div></td><td class="jockey"><p class="jockey">騎手 {number}</p></td></tr>'''


def _html(*, rows: str | None = None, weather: bool = True, condition: str = "良", course: str = "コース：1600メートル（芝・左）", date: str = "2025年1月5日(日) 1回東京1日", race: str = "1レース") -> str:
    weather_html = '<li class="weather"><span class="inner"><span class="txt">晴</span></span></li>' if weather else ""
    return f'''<div id="contentsBody"><div class="line main"><div class="inner"><h1>{race}</h1></div></div><div class="syutsuba"><table class="basic narrow-xy mt20"><caption><div class="race_header"><div class="left"><div class="date_line"><div class="inner"><div class="cell date">{date}</div><div class="cell time"><strong>15時00分</strong></div></div></div></div><div class="race_title"><div class="inner"><div class="txt"><span class="main"><span class="race_name">テストレース</span></span></div></div><div class="type"><div class="cell course">{course}</div><div class="cell class">3歳1勝</div></div></div><div class="cell baba"><ul><li class="turf"><span class="cap">芝</span><span class="txt">{condition}</span></li>{weather_html}</ul></div></div></caption><tbody>{rows if rows is not None else _row(2, "1234567890") + _row(1, "1234567891", odds="3.1")}</tbody></table></div></div>'''


def _response(html: str | None = None, *, observed: datetime = OBSERVED) -> JRASuppliedOfficialResponse:
    return JRASuppliedOfficialResponse(response_url=URL, response_body=(html or _html()).encode("cp932"), observed_at=observed)


def test_public_surface_signature_and_immutable_collection() -> None:
    assert tuple(inspect.signature(normalize_jra_target_race_input_source_records).parameters) == ("response",)
    result = normalize_jra_target_race_input_source_records(response=_response())
    assert isinstance(result, JRATargetRaceSourceCollection)
    with pytest.raises(FrozenInstanceError):
        result.source_records = ()  # type: ignore[misc]


def test_happy_path_maps_track_entries_odds_evidence_and_order() -> None:
    response = _response()
    result = normalize_jra_target_race_input_source_records(response=response)
    track = result.target_track_record
    assert track.record_values == {
        "target_race_date": track.record_values["target_race_date"],
        "scheduled_start_at": datetime(2025, 1, 5, 6, 0, tzinfo=timezone.utc),
        "place": "東京", "distance_m": 1600, "track": "芝", "track_condition": "良",
        "race_name": "テストレース", "race_class": "3歳1勝", "weather": "晴",
    }
    assert [record.record_values["horse_no"] for record in result.target_entry_records] == [1, 2]
    assert [record.record_kind for record in result.source_records] == ["track", "entry", "jockey", "odds_win", "entry", "jockey", "odds_win"]
    assert result.source_records[3].record_values["win_odds"] == Decimal("3.1")
    assert result.target_entry_records[0].external_entry_id == "jra:race:2025:05:01:01:01:entry:1"
    digest = hashlib.sha256(response.response_body).hexdigest()
    assert [record.evidence[0].evidence_role for record in result.source_records] == ["track", "entry", "jockey", "odds_win", "entry", "jockey", "odds_win"]
    assert all(record.evidence[0].response_sha256 == digest and record.evidence[0].available_at is None and record.evidence[0].observed_at == OBSERVED and record.evidence[0].request_identity_sha256 is None for record in result.source_records)
    assert all(record.provider_record_id is None for record in result.source_records)


@pytest.mark.parametrize("replacement", [
    ("accessD.html", "accessS.html"),
    ("pw01dde", "pw01sde"),
    ("%2F", "/"),
])
def test_noncanonical_or_wrong_family_response_is_rejected(replacement: tuple[str, str]) -> None:
    url = URL.replace(*replacement)
    with pytest.raises(Exception):
        JRASuppliedOfficialResponse(response_url=url, response_body=_html().encode("cp932"), observed_at=OBSERVED)


@pytest.mark.parametrize("html", [
    _html(rows=""),
    _html().replace('class="syutsuba"', 'class="syutsuba"') + _html(),
    _html(date="2025年1月5日(日) 1回中山1日"),
    _html(race="2レース"),
    _html(course="コース：1600メートル（ダート・左）"),
])
def test_structural_or_identity_failures_are_validation(html: str) -> None:
    with pytest.raises(JRATargetRaceSourceValidationError):
        normalize_jra_target_race_input_source_records(response=_response(html))


@pytest.mark.parametrize("odds", ["", "-", "取消", "0", "-1", "NaN"])
def test_unique_unsupported_odds_values_fail_closed_as_unsupported(odds: str) -> None:
    with pytest.raises(JRATargetRaceSourceUnsupportedError):
        normalize_jra_target_race_input_source_records(response=_response(_html(rows=_row(1, "1234567890", odds=odds))))


def test_missing_or_duplicate_odds_and_anchor_are_validation() -> None:
    missing_odds = _html(rows=_row(1, "1234567890").replace('<span class="num">2.5</span>', ""))
    duplicate_odds = _html(rows=_row(1, "1234567890").replace('</span></div></div></div></td>', '</span><span class="num">2.5</span></div></div></div></td>'))
    duplicate_anchor = _html(rows=_row(1, "1234567890").replace('</a>', '</a><a href="/JRADB/accessU.html?CNAME=pw01dud001234567891%2FAB">again</a>'))
    for html in (missing_odds, duplicate_odds, duplicate_anchor, _html(rows=_row(1, "1234567890", anchor=False))):
        with pytest.raises(JRATargetRaceSourceValidationError):
            normalize_jra_target_race_input_source_records(response=_response(html))


def test_duplicates_late_evidence_and_weather_absent() -> None:
    duplicate_no = _html(rows=_row(1, "1234567890") + _row(1, "1234567891"))
    duplicate_horse = _html(rows=_row(1, "1234567890") + _row(2, "1234567890"))
    for html in (duplicate_no, duplicate_horse):
        with pytest.raises(JRATargetRaceSourceValidationError):
            normalize_jra_target_race_input_source_records(response=_response(html))
    with pytest.raises(JRATargetRaceSourceValidationError):
        normalize_jra_target_race_input_source_records(response=_response(observed=datetime(2025, 1, 5, 7, 0, tzinfo=timezone.utc)))
    result = normalize_jra_target_race_input_source_records(response=_response(_html(weather=False)))
    assert result.target_track_record.record_values["weather"] is None


def test_determinism_and_no_package_root_export() -> None:
    first = normalize_jra_target_race_input_source_records(response=_response())
    second = normalize_jra_target_race_input_source_records(response=_response())
    assert first == second
    assert [record.source_id for record in first.source_records] == [record.source_id for record in second.source_records]
    import scripts.simulation as package
    assert not hasattr(package, "normalize_jra_target_race_input_source_records")
