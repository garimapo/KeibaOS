from __future__ import annotations

import ast
from datetime import datetime, timezone
from decimal import Decimal
import inspect
import unittest

from scripts.simulation.historical_input_source_records import (
    validate_historical_input_source_record_set,
)
from scripts.simulation.nar_historical_input_source import (
    NarHistoricalInputSourceError,
    NarHistoricalInputSourceUnsupportedError,
    NarHistoricalInputSourceValidationError,
    NarSuppliedOfficialResponse,
    normalize_nar_historical_input_source_records,
)


OBSERVED = datetime(2026, 7, 16, 10, 0, 0, 123456, tzinfo=timezone.utc)
URL = (
    "https://WWW.KEIBA.GO.JP:443/KeibaWeb/TodayRaceInfo/DebaTable?"
    "k_raceNo=10&k_raceDate=2026/07/16&k_babaCode=32"
)
CANONICAL_URL = (
    "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?"
    "k_babaCode=32&k_raceDate=2026%2F07%2F16&k_raceNo=10"
)
PLACE = "\u5927\u4e95"
TRACK = "\u30c0\u30fc\u30c8"
WEATHER = "\u6674"
CONDITION = "\u826f"


def _row(horse_no: int, jockey: str, odds: str) -> str:
    return f"""
    <tr>
      <td class="horseNum">{horse_no}</td>
      <td><a class="horseName">Horse</a></td>
      <td><a class="jockeyName">{jockey}<span class="jockeyarea">Team</span></a></td>
      <td class="odds_weight"><span class="odds_Black">{odds}</span></td>
    </tr>
    """


def _body(
    *,
    rows: str | None = None,
    active_place: str = PLACE,
    h4_place: str = PLACE,
    subtitle: str = "Promotion",
    charset: str = "utf-8",
) -> bytes:
    if rows is None:
        rows = _row(2, "Rider Two", "3.5") + _row(1, "Rider One", "2.0")
    return f"""
    <!doctype html><html><head><meta charset="{charset}"></head><body>
    <article class="raceCard"><div class="innerWrapper">
      <div class="chartNavi trackNameNavi">
        <a class="cNaviBtn courseBtn active">{active_place}</a>
      </div>
      <h4>2026\u5e747\u670816\u65e5\uff08\u6728\uff09{h4_place} \u7b2c10\u7af6\u8d70 20:40\u767a\u8d70</h4>
      <section class="raceTitle">
        <p class="subTitle">{subtitle}</p><h3>Race Name</h3>
        <ul class="dataArea">
          <li>{TRACK} 1400m \u5929\u5019\uff1a{WEATHER} \u99ac\u5834\uff1a{CONDITION}</li>
        </ul>
      </section>
    </div></article>
    <article class="raceCard"><div class="innerWrapper">
      <section class="cardTable"><table><tbody>{rows}</tbody></table></section>
    </div></article></body></html>
    """.encode("utf-8")


def _response(**changes: object) -> NarSuppliedOfficialResponse:
    values: dict[str, object] = {
        "response_url": URL,
        "response_body": _body(),
        "charset": "utf-8",
        "observed_at": OBSERVED,
    }
    values.update(changes)
    return NarSuppliedOfficialResponse(**values)


class NarHistoricalInputSourceTests(unittest.TestCase):
    def test_public_api_and_response_contract(self) -> None:
        import scripts.simulation.nar_historical_input_source as module

        self.assertEqual(
            {name for name in vars(module) if not name.startswith("_")},
            {
                "NarSuppliedOfficialResponse",
                "NarHistoricalInputSourceError",
                "NarHistoricalInputSourceValidationError",
                "NarHistoricalInputSourceUnsupportedError",
                "normalize_nar_historical_input_source_records",
            },
        )
        self.assertEqual(
            tuple(NarSuppliedOfficialResponse.__dataclass_fields__),
            ("response_url", "response_body", "charset", "observed_at"),
        )
        self.assertEqual(
            NarSuppliedOfficialResponse.__slots__,
            ("response_url", "response_body", "charset", "observed_at"),
        )
        response = _response()
        with self.assertRaises((AttributeError, TypeError)):
            setattr(response, "response_url", URL)
        invalid_fields = (
            ("response_url", 1),
            ("response_body", bytearray(b"x")),
            ("charset", "UTF-8"),
            ("observed_at", datetime(2026, 1, 1)),
        )
        for field, value in invalid_fields:
            with self.subTest(field=field):
                values = {
                    "response_url": URL,
                    "response_body": _body(),
                    "charset": "utf-8",
                    "observed_at": OBSERVED,
                }
                values[field] = value
                with self.assertRaises(NarHistoricalInputSourceValidationError):
                    NarSuppliedOfficialResponse(**values)
        with self.assertRaises(NarHistoricalInputSourceValidationError):
            normalize_nar_historical_input_source_records(response=object())

    def test_split_race_cards_are_canonical_and_c1a_valid(self) -> None:
        body = _body()
        self.assertEqual(body.count(b'<article class="raceCard">'), 2)
        result = normalize_nar_historical_input_source_records(
            response=_response(response_body=body),
        )
        self.assertEqual(
            [record.record_kind for record in result],
            [
                "track",
                "entry",
                "jockey",
                "odds_win",
                "entry",
                "jockey",
                "odds_win",
            ],
        )
        self.assertIs(
            validate_historical_input_source_record_set(records=result),
            result,
        )
        track = result[0]
        self.assertEqual(track.external_race_id, "nar:20260716:32:10")
        self.assertEqual(track.canonical_source_url, CANONICAL_URL)
        self.assertEqual(track.record_values["place"], PLACE)
        self.assertEqual(track.record_values["race_class"], None)
        self.assertEqual(track.record_values["race_name"], "Race Name")
        self.assertEqual(track.record_values["distance_m"], 1400)
        self.assertEqual(track.record_values["track"], TRACK)
        self.assertEqual(track.record_values["weather"], WEATHER)
        self.assertEqual(track.record_values["track_condition"], CONDITION)
        self.assertEqual(
            track.record_values["scheduled_start_at"].isoformat(),
            "2026-07-16T11:40:00+00:00",
        )
        self.assertEqual(track.available_at, None)
        self.assertEqual(track.observed_at, OBSERVED)
        self.assertEqual(result[1].external_entry_id, "nar:20260716:32:10:entry:1")
        self.assertEqual(result[1].record_values["external_horse_id"], None)
        self.assertEqual(result[2].record_values["jockey"], "Rider One")
        self.assertEqual(result[3].record_values["win_odds"], Decimal("2"))
        self.assertEqual(result[6].record_values["win_odds"], Decimal("3.5"))
        repeated = normalize_nar_historical_input_source_records(response=_response())
        self.assertEqual(result, repeated)
        self.assertEqual(
            [item.source_id for item in result],
            [item.source_id for item in repeated],
        )

    def test_subtitle_never_becomes_race_class_and_place_cross_checks(self) -> None:
        result = normalize_nar_historical_input_source_records(
            response=_response(response_body=_body(subtitle="Not a class")),
        )
        self.assertIsNone(result[0].record_values["race_class"])
        self.assertNotIn("Not a class", result[0].record_values.values())
        for active, h4, expected in (
            ("Caf\u00e9", "C a f e\u0301", "Caf\u00e9"),
            (PLACE, PLACE, PLACE),
            ("\u4f50\u8cc0", "\u4f50\u3000\u8cc0", "\u4f50\u8cc0"),
        ):
            with self.subTest(active=active):
                body = _body(active_place=active, h4_place=h4)
                actual = normalize_nar_historical_input_source_records(
                    response=_response(response_body=body),
                )
                self.assertEqual(actual[0].record_values["place"], expected)
        bad_bodies = (
            _body(active_place=PLACE, h4_place="\u5927\u4e8c"),
            _body(active_place="", h4_place=""),
            _body().replace(b"courseBtn active", b"courseBtn inactive"),
            _body().replace(
                f">{PLACE}</a>".encode(),
                f">{PLACE}</a><a class=\"cNaviBtn courseBtn active\">\u5927\u4e8c</a>".encode(),
            ),
        )
        for body in bad_bodies:
            with self.subTest(body=body[:40]):
                with self.assertRaises(NarHistoricalInputSourceValidationError):
                    normalize_nar_historical_input_source_records(
                        response=_response(response_body=body),
                    )

    def test_url_policy_and_external_identity_fail_closed(self) -> None:
        cases = {
            "http": URL.replace("https:", "http:"),
            "credentials": URL.replace("https://", "https://x:y@"),
            "fragment": URL + "#x",
            "host": URL.replace("WWW.KEIBA.GO.JP", "example.test"),
            "trailing": URL.replace("DebaTable?", "DebaTable/?"),
            "unknown": URL + "&extra=1",
            "duplicate": URL + "&k_raceNo=11",
            "missing": URL.replace("&k_babaCode=32", ""),
            "blank": URL.replace("k_raceNo=10", "k_raceNo="),
            "bad-percent": URL.replace("2026/07/16", "2026%2G07%2F16"),
            "plus": URL.replace("2026/07/16", "2026+07+16"),
            "leading": URL.replace("k_raceNo=10", "k_raceNo=010"),
            "leading-baba": URL.replace("k_babaCode=32", "k_babaCode=032"),
            "date": URL.replace("2026/07/16", "2026/02/30"),
        }
        for name, url in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(NarHistoricalInputSourceError):
                    normalize_nar_historical_input_source_records(
                        response=_response(response_url=url),
                    )
        with self.assertRaises(NarHistoricalInputSourceUnsupportedError):
            normalize_nar_historical_input_source_records(
                response=_response(
                    response_url=URL.replace("DebaTable", "RaceMarkTable"),
                ),
            )

    def test_url_parser_and_integer_conversion_failures_are_validation_errors(self) -> None:
        malformed_url = URL.replace("WWW.KEIBA.GO.JP:443", "[::1")
        with self.assertRaises(NarHistoricalInputSourceValidationError) as caught:
            normalize_nar_historical_input_source_records(
                response=_response(response_url=malformed_url),
            )
        self.assertIs(type(caught.exception), NarHistoricalInputSourceValidationError)
        huge_token = "9" * 10000
        for name, body in (
            ("horseNum", _body(rows=_row(huge_token, "Rider", "2"))),
            ("distance_m", _body().replace(b"1400m", f"{huge_token}m".encode())),
        ):
            with self.subTest(name=name):
                with self.assertRaises(NarHistoricalInputSourceValidationError) as caught:
                    normalize_nar_historical_input_source_records(
                        response=_response(response_body=body),
                    )
                self.assertIs(
                    type(caught.exception),
                    NarHistoricalInputSourceValidationError,
                )

    def test_utf8_html_and_h4_identity_boundaries(self) -> None:
        invalids = (
            _response(response_body=b"\xff"),
            _response(response_body=_body(charset="UTF-8")),
            _response(
                response_body=_body().replace(
                    b'<meta charset="utf-8">',
                    b"",
                ),
            ),
            _response(
                response_body=_body().replace(
                    b"</head>",
                    b'<meta charset="utf-8"></head>',
                ),
            ),
            _response(
                response_body=_body().replace(
                    "\u7b2c10\u7af6\u8d70".encode(),
                    "\u7b2c11\u7af6\u8d70".encode(),
                ),
            ),
            _response(
                response_body=_body().replace(
                    "2026\u5e747\u670816\u65e5".encode(),
                    "2026\u5e747\u670817\u65e5".encode(),
                ),
            ),
        )
        for response in invalids:
            with self.subTest(response=response.response_body[:20]):
                with self.assertRaises(NarHistoricalInputSourceValidationError):
                    normalize_nar_historical_input_source_records(response=response)

    def test_rows_odds_and_cancellation_fail_closed(self) -> None:
        malformed_odds = _row(1, "Rider", "2").replace(
            'odds_Black">2',
            'odds_Black">2</span><span class="odds_Black">3',
        )
        bodies = (
            _body(rows=_row(1, "Rider", "0")),
            _body(rows=_row(1, "Rider", "-")),
            _body(rows=_row(1, "Rider", "2") + _row(1, "Other", "3")),
            _body(rows=malformed_odds),
            _body(rows=_row(1, "Rider \u53d6\u6d88", "2")),
            _body(rows=_row(1, "Rider", "2").replace("odds_Black", "price_Black")),
            _body(rows=_row(1, "Rider", "2").replace("jockeyName", "riderName")),
            _body(
                rows=_row(1, "Rider", "2").replace(
                    "</td>\n      <td class=\"odds_weight\">",
                    "</td><td><a class=\"jockeyName\">Other</a></td>"
                    "<td class=\"odds_weight\">",
                ),
            ),
        )
        for body in bodies:
            with self.subTest(body=body[:40]):
                with self.assertRaises(NarHistoricalInputSourceError):
                    normalize_nar_historical_input_source_records(
                        response=_response(response_body=body),
                    )

    def test_past_race_kinds_are_not_created(self) -> None:
        result = normalize_nar_historical_input_source_records(response=_response())
        self.assertFalse(
            {"past_race", "past_race_absence"}
            & {record.record_kind for record in result},
        )
        response = _response(
            response_body=_body().replace(
                b"</body>",
                b'<section id="RaceMarkTable"></section></body>',
            ),
        )
        self.assertEqual(
            normalize_nar_historical_input_source_records(response=response)[0].record_kind,
            "track",
        )
        with self.assertRaises(NarHistoricalInputSourceUnsupportedError):
            normalize_nar_historical_input_source_records(
                response=_response(
                    response_url=URL.replace("DebaTable", "RaceMarkTable"),
                ),
            )

    def test_source_ast_dependency_boundary(self) -> None:
        import scripts.simulation.nar_historical_input_source as module

        source = inspect.getsource(module)
        tree = ast.parse(source, type_comments=True)
        self.assertEqual(tree.type_ignores, [])
        self.assertNotIn("# type: ignore", source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertFalse({"Any", "cast", "runtime_checkable"} & imported)
        import scripts.simulation as simulation

        self.assertFalse(
            hasattr(simulation, "normalize_nar_historical_input_source_records"),
        )
        for forbidden in (
            "sqlite3",
            "database",
            "requests",
            "urllib.request",
            "pathlib",
            "open(",
            "datetime.now",
            "datetime.utcnow",
            "random",
            "uuid",
            "nar_provider",
            "horse_parser",
            "payout_provider",
            "float(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
