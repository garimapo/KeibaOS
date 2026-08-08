from __future__ import annotations

import ast
from datetime import datetime, timezone
from decimal import Decimal
import inspect
from pathlib import Path
import unittest

from scripts.simulation.historical_input_source_records import (
    HistoricalInputSourceRecord,
    validate_historical_input_source_record_set,
)
from scripts.simulation.historical_input_snapshot_builder import (
    build_historical_input_snapshot,
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


def _row(
    horse_no: int,
    jockey: str,
    odds: str,
    lineage_code: str | None = None,
) -> str:
    if lineage_code is None:
        lineage_code = f"3000000000{horse_no}"
    return f"""
    <tr>
      <td class="horseNum">{horse_no}</td>
      <td><a class="horseName" href="../DataRoom/HorseMarkInfo?k_lineageLoginCode={lineage_code}">Horse</a></td>
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


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "nar" / "deba_table_target_horse_identity.html"
FIXTURE_URL = (
    "https://www.keiba.go.jp/KeibaWeb/TodayRaceInfo/DebaTable?"
    "k_babaCode=19&k_raceDate=2026%2F07%2F04&k_raceNo=11"
)


def _fixture_response(
    *,
    observed_at: datetime = datetime(2026, 7, 4, 10, 0, tzinfo=timezone.utc),
) -> NarSuppliedOfficialResponse:
    return NarSuppliedOfficialResponse(
        response_url=FIXTURE_URL,
        response_body=FIXTURE_PATH.read_bytes(),
        charset="utf-8",
        observed_at=observed_at,
    )


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
        self.assertEqual(result[1].record_values["external_horse_id"], "nar:horse:30000000001")
        self.assertEqual(result[2].record_values["jockey"], "Rider One")
        self.assertEqual(result[3].record_values["win_odds"], Decimal("2"))
        self.assertEqual(result[6].record_values["win_odds"], Decimal("3.5"))
        repeated = normalize_nar_historical_input_source_records(response=_response())
        self.assertEqual(result, repeated)
        self.assertEqual(
            [item.source_id for item in result],
            [item.source_id for item in repeated],
        )

    def test_authentic_target_horse_fixture_is_row_local_and_propagates_to_c1c(self) -> None:
        response = _fixture_response()
        result = normalize_nar_historical_input_source_records(response=response)
        entries = tuple(record for record in result if record.record_kind == "entry")
        jockeys = tuple(record for record in result if record.record_kind == "jockey")
        odds = tuple(record for record in result if record.record_kind == "odds_win")
        self.assertEqual(
            [
                (
                    record.record_values["horse_no"],
                    record.external_entry_id,
                    record.record_values["external_horse_id"],
                )
                for record in entries
            ],
            [
                (1, "nar:20260704:19:11:entry:1", "nar:horse:30036406666"),
                (2, "nar:20260704:19:11:entry:2", "nar:horse:30038401876"),
            ],
        )
        self.assertEqual(
            [record.record_values["jockey"] for record in jockeys],
            ["野畑凌", "實川純"],
        )
        self.assertEqual(
            [record.record_values["win_odds"] for record in odds],
            [Decimal("39.2"), Decimal("213.1")],
        )
        old_entry = HistoricalInputSourceRecord(
            record_kind="entry",
            organization=entries[0].organization,
            source_system=entries[0].source_system,
            external_race_id=entries[0].external_race_id,
            external_entry_id=entries[0].external_entry_id,
            canonical_source_url=entries[0].canonical_source_url,
            provider_record_id=None,
            record_values={
                "external_entry_id": entries[0].external_entry_id,
                "external_horse_id": None,
                "horse_no": 1,
            },
            available_at=None,
            observed_at=response.observed_at,
        )
        self.assertNotEqual(entries[0].source_id, old_entry.source_id)
        absence_records = tuple(
            HistoricalInputSourceRecord(
                record_kind="past_race_absence",
                organization=entry.organization,
                source_system=entry.source_system,
                external_race_id=entry.external_race_id,
                external_entry_id=entry.external_entry_id,
                canonical_source_url=entry.canonical_source_url,
                provider_record_id=None,
                record_values={
                    "external_entry_id": entry.external_entry_id,
                    "query_scope": {
                        "external_entry_id": entry.external_entry_id,
                        "target_race_date": result[0].record_values["target_race_date"],
                        "strictly_before_target_race": True,
                    },
                    "result_count": 0,
                },
                available_at=None,
                observed_at=response.observed_at,
            )
            for entry in entries
        )
        snapshot = build_historical_input_snapshot(
            dataset_id="fixture-dataset",
            internal_race_id=1,
            captured_at=datetime(2026, 7, 4, 10, 30, tzinfo=timezone.utc),
            information_cutoff=datetime(2026, 7, 4, 10, 45, tzinfo=timezone.utc),
            source_records=result + absence_records,
            race_entry_id_by_external_entry_id={
                "nar:20260704:19:11:entry:1": 101,
                "nar:20260704:19:11:entry:2": 102,
            },
        )
        self.assertEqual(
            [entry.external_entry_identity.external_horse_id for entry in snapshot.entries],
            ["nar:horse:30036406666", "nar:horse:30038401876"],
        )
        self.assertEqual(
            result,
            normalize_nar_historical_input_source_records(response=_fixture_response()),
        )

    def test_lineage_change_isolates_only_the_selected_entry_source_id(self) -> None:
        baseline = normalize_nar_historical_input_source_records(response=_response())
        changed = normalize_nar_historical_input_source_records(
            response=_response(
                response_body=_body(
                    rows=(
                        _row(2, "Rider Two", "3.5")
                        + _row(1, "Rider One", "2.0", "30000000999")
                    ),
                ),
            ),
        )

        def records_by_kind_and_entry(
            records: tuple[HistoricalInputSourceRecord, ...],
        ) -> dict[tuple[str, str | None], HistoricalInputSourceRecord]:
            return {
                (record.record_kind, record.external_entry_id): record
                for record in records
            }

        baseline_by_key = records_by_kind_and_entry(baseline)
        changed_by_key = records_by_kind_and_entry(changed)
        selected_entry_id = "nar:20260716:32:10:entry:1"
        untouched_entry_id = "nar:20260716:32:10:entry:2"
        selected_key = ("entry", selected_entry_id)

        self.assertEqual(
            baseline_by_key[selected_key].record_values["external_entry_id"],
            selected_entry_id,
        )
        self.assertEqual(
            changed_by_key[selected_key].record_values["external_entry_id"],
            selected_entry_id,
        )
        self.assertEqual(
            baseline_by_key[selected_key].record_values["external_horse_id"],
            "nar:horse:30000000001",
        )
        self.assertEqual(
            changed_by_key[selected_key].record_values["external_horse_id"],
            "nar:horse:30000000999",
        )
        self.assertNotEqual(
            baseline_by_key[selected_key].source_id,
            changed_by_key[selected_key].source_id,
        )

        self.assertEqual(
            baseline_by_key[("track", None)].record_values,
            changed_by_key[("track", None)].record_values,
        )
        self.assertEqual(
            baseline_by_key[("track", None)].source_id,
            changed_by_key[("track", None)].source_id,
        )
        for record_kind in ("jockey", "odds_win"):
            selected_key = (record_kind, selected_entry_id)
            self.assertEqual(
                baseline_by_key[selected_key].record_values,
                changed_by_key[selected_key].record_values,
            )
            self.assertEqual(
                baseline_by_key[selected_key].source_id,
                changed_by_key[selected_key].source_id,
            )
        for record_kind in ("entry", "jockey", "odds_win"):
            untouched_key = (record_kind, untouched_entry_id)
            self.assertEqual(
                baseline_by_key[untouched_key].record_values,
                changed_by_key[untouched_key].record_values,
            )
            self.assertEqual(
                baseline_by_key[untouched_key].source_id,
                changed_by_key[untouched_key].source_id,
            )

        self.assertEqual(
            [
                key
                for key in baseline_by_key
                if baseline_by_key[key].record_values != changed_by_key[key].record_values
            ],
            [("entry", "nar:20260716:32:10:entry:1")],
        )
        self.assertEqual(
            [
                key
                for key in baseline_by_key
                if baseline_by_key[key].source_id != changed_by_key[key].source_id
            ],
            [("entry", "nar:20260716:32:10:entry:1")],
        )

    def test_horse_anchor_href_contract_fails_closed_and_keeps_lexical_tokens(self) -> None:
        default_href = "../DataRoom/HorseMarkInfo?k_lineageLoginCode=30000000001"
        invalid_hrefs = (
            "../DataRoom/HorseMarkInfo",
            "../DataRoom/HorseMarkInfo?k_other=1",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=1&k_lineageLoginCode=2",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=0",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=01",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=+1",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=-1",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=1%202",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=%EF%BC%91",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=1.0",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=1e2",
            "../DataRoom/HorseMarkInfo?k_lineageLoginCode=1%2G",
            "../DataRoom/Other?k_lineageLoginCode=1",
            "https://example.test/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=1",
            "http://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=1",
            "https://x:y@www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=1",
            "https://www.keiba.go.jp:444/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=1",
            "https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=1#fragment",
        )
        for href in invalid_hrefs:
            with self.subTest(href=href):
                body = _body(rows=_row(1, "Rider", "2").replace(default_href, href))
                with self.assertRaises(NarHistoricalInputSourceValidationError):
                    normalize_nar_historical_input_source_records(response=_response(response_body=body))
        no_anchor = _body(
            rows=_row(1, "Rider", "2").replace(f' href="{default_href}"', ""),
        )
        multiple_anchors = _body(
            rows=_row(1, "Rider", "2").replace(
                "</a></td>",
                f'</a><a class="horseName" href="{default_href}">Other</a></td>',
                1,
            ),
        )
        for body in (no_anchor, multiple_anchors):
            with self.subTest(body=body[:40]):
                with self.assertRaises(NarHistoricalInputSourceValidationError):
                    normalize_nar_historical_input_source_records(response=_response(response_body=body))
        absolute = _body(
            rows=_row(1, "Rider", "2").replace(
                default_href,
                "https://www.keiba.go.jp/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=30000000001",
            ),
        )
        self.assertEqual(
            normalize_nar_historical_input_source_records(response=_response(response_body=absolute))[1]
            .record_values["external_horse_id"],
            "nar:horse:30000000001",
        )
        huge = "9" * 10000
        huge_body = _body(rows=_row(1, "Rider", "2", huge))
        self.assertEqual(
            normalize_nar_historical_input_source_records(response=_response(response_body=huge_body))[1]
            .record_values["external_horse_id"],
            f"nar:horse:{huge}",
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
