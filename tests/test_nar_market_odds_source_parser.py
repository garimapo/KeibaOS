from __future__ import annotations

import ast
from dataclasses import fields, replace
from datetime import date, datetime
from decimal import Decimal
import inspect
import json
from pathlib import Path
from typing import get_type_hints

from bs4 import BeautifulSoup
import pytest

from scripts.simulation.nar_market_odds_capture import (
    NARMarketOddsPageKind,
    NARMarketOddsResponseCapture,
    build_nar_market_odds_request_identity,
)
from scripts.simulation.nar_market_odds_source_parser import (
    NARMarketOddsExactQuote,
    NARMarketOddsRangeQuote,
    NARMarketOddsSourceCompleteness,
    NARMarketOddsSourceEvidence,
    NARMarketOddsSourceParseDataError,
    NARMarketOddsSourceParseError,
    NARMarketOddsSourceParseNumericError,
    NARMarketOddsSourceParseUnsupportedError,
    NARMarketOddsSourceParseValidationError,
    NARMarketOddsSourceQuoteKind,
    NARMarketOddsSourceState,
    parse_nar_market_odds_source_capture,
)


REPOSITORY_ROOT = Path(__file__).parent.parent
FIXTURE_ROOT = REPOSITORY_ROOT / "tests/fixtures/nar_market_odds/source_profiles/v1"
MANIFEST = json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))
ITEMS = {item["fixture_slot"]: item for item in MANIFEST["fixtures"]}
EXPECTED = {
    "open/odds_tan_fuku": (NARMarketOddsSourceState.OPEN, 8, (1,), (Decimal("3.3"),)),
    "open/odds_um_len_fuku": (NARMarketOddsSourceState.OPEN, 28, (1, 2), (Decimal("3.4"),)),
    "open/odds_wide": (
        NARMarketOddsSourceState.OPEN,
        28,
        (1, 2),
        (Decimal("1.4"), Decimal("1.5")),
    ),
    "open/odds_3_len_fuku": (NARMarketOddsSourceState.OPEN, 56, (1, 2, 8), (Decimal("7.3"),)),
    "final/odds_tan_fuku": (NARMarketOddsSourceState.FINAL, 11, (1,), (Decimal("12.0"),)),
    "final/odds_um_len_fuku": (NARMarketOddsSourceState.FINAL, 55, (2, 5), (Decimal("3.8"),)),
    "final/odds_wide": (
        NARMarketOddsSourceState.FINAL,
        55,
        (2, 5),
        (Decimal("1.9"), Decimal("2.1")),
    ),
    "final/odds_3_len_fuku": (NARMarketOddsSourceState.FINAL, 165, (2, 5, 11), (Decimal("6.2"),)),
}
EXPECTED_EVIDENCE_IDS = {
    "open/odds_tan_fuku": "nar-market-odds-source-evidence-v1:41f8cc51ca0323f690e8ac4e9e113782bbb43177c45a0cea9b8cb79f8d1692fb",
    "open/odds_um_len_fuku": "nar-market-odds-source-evidence-v1:e7a29cdde590f59ea5ed150f63ffa2df2b1d39924238687883addea4e199a6b7",
    "open/odds_wide": "nar-market-odds-source-evidence-v1:321426d15f542671221716d6e7de57e18e27c8a162337ba0139a4474350ae4d0",
    "open/odds_3_len_fuku": "nar-market-odds-source-evidence-v1:fdd4c980f4b7fdf95996e1d1217f6b399a52338fdcdf86805c7a43a3d8094b48",
    "final/odds_tan_fuku": "nar-market-odds-source-evidence-v1:c5eccdfabcc5c35c995a1a44461c35dd657d7b1d8a6670003c90a36003ba9294",
    "final/odds_um_len_fuku": "nar-market-odds-source-evidence-v1:0d3c374b2037dc617a4e45218615d47f9f3b83164c01f851f4186db9a446d767",
    "final/odds_wide": "nar-market-odds-source-evidence-v1:555233ef117976cc5170a6b9f7c589137d590d3414e6eba4cc8dd6c80d3ba8c3",
    "final/odds_3_len_fuku": "nar-market-odds-source-evidence-v1:cc35d2fd8df6733bf1f41bce3f8d763118f7604153fc60911e5a43a6d029ac03",
}


def _capture(
    item: dict[str, object],
    *,
    body: bytes | None = None,
    request=None,
) -> NARMarketOddsResponseCapture:
    if request is None:
        request = build_nar_market_odds_request_identity(
            page_kind=NARMarketOddsPageKind(item["page_kind"]),
            baba_code=item["baba_code"],
            race_date=date.fromisoformat(item["race_date"]),
            race_no=item["race_no"],
        )
    if body is None:
        body = (REPOSITORY_ROOT / item["fixture_relative_path"]).read_bytes()
    return NARMarketOddsResponseCapture(
        request_identity=request,
        effective_url=request.canonical_request_url,
        response_body=body,
        charset="utf-8",
        requested_at=datetime.fromisoformat(item["requested_at_utc"]),
        observed_at=datetime.fromisoformat(item["observed_at_utc"]),
        captured_at=datetime.fromisoformat(item["captured_at_utc"]),
        http_status=200,
        content_type=item["content_type"],
        content_encoding=item["content_encoding"],
        http_date=item["http_date"],
        etag=item["etag"],
        last_modified=item["last_modified"],
        content_length=None,
    )


def _soup_capture(slot: str, mutate) -> NARMarketOddsResponseCapture:
    item = ITEMS[slot]
    body = (REPOSITORY_ROOT / item["fixture_relative_path"]).read_bytes()
    soup = BeautifulSoup(body.decode("utf-8"), "html.parser")
    mutate(soup)
    return _capture(item, body=str(soup).encode("utf-8"))


def _first_ranking_row(soup: BeautifulSoup):
    return soup.select_one("div#odd_content > ul.odd_ranking table.odd_ranking_table tr:nth-of-type(2)")


def _quote(evidence: NARMarketOddsSourceEvidence, selection: tuple[int, ...]):
    return next(quote for quote in evidence.quotes if quote.selection == selection)


def test_exact_public_api_and_enums() -> None:
    assert tuple(NARMarketOddsSourceState) == (
        NARMarketOddsSourceState.OPEN,
        NARMarketOddsSourceState.FINAL,
    )
    assert tuple(NARMarketOddsSourceCompleteness) == (NARMarketOddsSourceCompleteness.UNVERIFIED,)
    assert tuple(NARMarketOddsSourceQuoteKind) == (
        NARMarketOddsSourceQuoteKind.EXACT,
        NARMarketOddsSourceQuoteKind.RANGE,
    )
    assert issubclass(NARMarketOddsSourceParseValidationError, NARMarketOddsSourceParseError)
    assert issubclass(NARMarketOddsSourceParseUnsupportedError, NARMarketOddsSourceParseError)
    assert issubclass(NARMarketOddsSourceParseDataError, NARMarketOddsSourceParseError)
    assert issubclass(NARMarketOddsSourceParseNumericError, NARMarketOddsSourceParseDataError)
    signature = inspect.signature(parse_nar_market_odds_source_capture)
    assert tuple(signature.parameters) == ("capture",)
    assert signature.parameters["capture"].kind is inspect.Parameter.KEYWORD_ONLY
    hints = get_type_hints(parse_nar_market_odds_source_capture)
    assert hints == {
        "capture": NARMarketOddsResponseCapture,
        "return": NARMarketOddsSourceEvidence,
    }
    assert tuple(field.name for field in fields(NARMarketOddsExactQuote)) == (
        "selection",
        "exact_odds",
        "quote_kind",
    )
    assert tuple(field.name for field in fields(NARMarketOddsRangeQuote)) == (
        "selection",
        "lower_odds",
        "upper_odds",
        "quote_kind",
    )


@pytest.mark.parametrize("slot", tuple(EXPECTED))
def test_all_integrated_fixtures_parse_exact_normalized_facts(slot: str) -> None:
    item = ITEMS[slot]
    capture = _capture(item)
    first = parse_nar_market_odds_source_capture(capture=capture)
    second = parse_nar_market_odds_source_capture(capture=capture)
    expected_state, expected_count, selection, values = EXPECTED[slot]

    assert first == second
    assert first.page_kind is NARMarketOddsPageKind(item["page_kind"])
    assert first.source_state is expected_state
    assert len(first.quotes) == expected_count
    assert tuple(quote.selection for quote in first.quotes) == tuple(
        sorted(quote.selection for quote in first.quotes)
    )
    assert len({quote.selection for quote in first.quotes}) == expected_count
    quote = _quote(first, selection)
    if type(quote) is NARMarketOddsExactQuote:
        assert values == (quote.exact_odds,)
        assert quote.quote_kind is NARMarketOddsSourceQuoteKind.EXACT
    else:
        assert type(quote) is NARMarketOddsRangeQuote
        assert values == (quote.lower_odds, quote.upper_odds)
        assert quote.quote_kind is NARMarketOddsSourceQuoteKind.RANGE
    assert first.request_identity_sha256 == capture.request_identity.request_identity_sha256
    assert first.request_identity == capture.request_identity.request_identity
    assert first.capture_id == capture.capture_id
    assert first.response_sha256 == capture.response_sha256
    assert first.response_byte_length == capture.byte_length
    assert (first.requested_at, first.observed_at, first.captured_at) == (
        capture.requested_at,
        capture.observed_at,
        capture.captured_at,
    )
    assert first.source_completeness is NARMarketOddsSourceCompleteness.UNVERIFIED
    assert first.provider_horse_numbers is None
    assert first.parser_name == "nar-market-odds-source-parser"
    assert first.parser_version == "v1"
    assert first.evidence_id == EXPECTED_EVIDENCE_IDS[slot]
    assert first.evidence_id.endswith(first.evidence_content_sha256)
    assert first.provider_display_as_of_text is None if expected_state is NARMarketOddsSourceState.FINAL else first.provider_display_as_of_text.endswith(" 現在")


def test_decimal_semantic_identity_removes_only_redundant_fractional_zeroes() -> None:
    evidence = parse_nar_market_odds_source_capture(capture=_capture(ITEMS["open/odds_tan_fuku"]))
    left = replace(evidence, quotes=(NARMarketOddsExactQuote((1,), Decimal("1.50")),))
    right = replace(evidence, quotes=(NARMarketOddsExactQuote((1,), Decimal("1.5")),))
    assert left.evidence_id == right.evidence_id


def test_evidence_rejects_forged_phase32_provenance() -> None:
    evidence = parse_nar_market_odds_source_capture(capture=_capture(ITEMS["open/odds_tan_fuku"]))
    with pytest.raises(NARMarketOddsSourceParseValidationError):
        replace(evidence, request_identity_sha256="0" * 64)
    with pytest.raises(NARMarketOddsSourceParseValidationError):
        replace(evidence, canonical_request_url=evidence.canonical_request_url + "&forged=1")
    with pytest.raises(NARMarketOddsSourceParseValidationError):
        replace(evidence, response_sha256="A" * 64)


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ((True,), NARMarketOddsSourceParseDataError),
        ((0,), NARMarketOddsSourceParseDataError),
        ((2, 1), NARMarketOddsSourceParseDataError),
        ((1, 1), NARMarketOddsSourceParseDataError),
    ],
)
def test_quote_domain_rejects_noncanonical_selections(value, error) -> None:
    with pytest.raises(error):
        NARMarketOddsExactQuote(value, Decimal("1.0"))


def test_range_domain_retains_equal_endpoints_and_rejects_inversion() -> None:
    quote = NARMarketOddsRangeQuote((1, 2), Decimal("2.0"), Decimal("2.0"))
    assert quote.quote_kind is NARMarketOddsSourceQuoteKind.RANGE
    with pytest.raises(NARMarketOddsSourceParseNumericError):
        NARMarketOddsRangeQuote((1, 2), Decimal("2.1"), Decimal("2.0"))


def test_malformed_or_forged_capture_is_validation_error() -> None:
    capture = _capture(ITEMS["open/odds_tan_fuku"])
    object.__delattr__(capture, "capture_id")
    with pytest.raises(NARMarketOddsSourceParseValidationError):
        parse_nar_market_odds_source_capture(capture=capture)
    with pytest.raises(NARMarketOddsSourceParseValidationError):
        parse_nar_market_odds_source_capture(capture=object())


def test_missing_authoritative_container_fails_closed() -> None:
    capture = _soup_capture(
        "open/odds_tan_fuku",
        lambda soup: soup.select_one("table.odd_popular_table_02").extract(),
    )
    with pytest.raises(NARMarketOddsSourceParseUnsupportedError):
        parse_nar_market_odds_source_capture(capture=capture)


@pytest.mark.parametrize("slot,selector", [
    ("open/odds_tan_fuku", "table.odd_popular_table_02"),
    ("open/odds_um_len_fuku", "div#odd_content > ul.odd_ranking"),
])
def test_duplicate_authoritative_container_fails_closed(slot: str, selector: str) -> None:
    def mutate(soup: BeautifulSoup) -> None:
        node = soup.select_one(selector)
        duplicate = BeautifulSoup(str(node), "html.parser").find(node.name)
        node.insert_after(duplicate)

    with pytest.raises(NARMarketOddsSourceParseUnsupportedError):
        parse_nar_market_odds_source_capture(capture=_soup_capture(slot, mutate))


def test_wrong_page_family_fails_closed() -> None:
    win_item = ITEMS["open/odds_tan_fuku"]
    quinella_item = ITEMS["open/odds_um_len_fuku"]
    request = build_nar_market_odds_request_identity(
        page_kind=NARMarketOddsPageKind.ODDS_UM_LEN_FUKU,
        baba_code=win_item["baba_code"],
        race_date=date.fromisoformat(win_item["race_date"]),
        race_no=win_item["race_no"],
    )
    body = (REPOSITORY_ROOT / win_item["fixture_relative_path"]).read_bytes()
    capture = _capture(quinella_item, body=body, request=request)
    with pytest.raises(NARMarketOddsSourceParseUnsupportedError):
        parse_nar_market_odds_source_capture(capture=capture)


@pytest.mark.parametrize("mode", ("missing", "ambiguous"))
def test_missing_or_ambiguous_state_heading_fails_closed(mode: str) -> None:
    def mutate(soup: BeautifulSoup) -> None:
        heading = soup.select_one("h4.odd_title")
        if mode == "missing":
            heading.extract()
        else:
            heading.string = "単勝・複勝　オッズ （11:33 現在）（最終）"

    with pytest.raises(NARMarketOddsSourceParseUnsupportedError):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_tan_fuku", mutate))


@pytest.mark.parametrize("selection", ("0", "01", "Ａ", "1-1"))
def test_malformed_win_horse_number_fails_closed(selection: str) -> None:
    def mutate(soup: BeautifulSoup) -> None:
        row = soup.select_one("table.odd_popular_table_02 tbody tr")
        row.find_all("td", recursive=False)[1].string = selection

    with pytest.raises(NARMarketOddsSourceParseDataError):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_tan_fuku", mutate))


def test_duplicate_horse_inside_pair_and_triple_fails_closed() -> None:
    for slot, value in (("open/odds_um_len_fuku", "1-1"), ("open/odds_3_len_fuku", "1-2-1")):
        def mutate(soup: BeautifulSoup, value=value) -> None:
            _first_ranking_row(soup).find_all("td", recursive=False)[0].string = value

        with pytest.raises(NARMarketOddsSourceParseDataError):
            parse_nar_market_odds_source_capture(capture=_soup_capture(slot, mutate))


@pytest.mark.parametrize("token", ("1", "01.0", "+1.0", "-1.0", "0.0", "1e2", "１.０", "NaN", "Infinity", ""))
def test_malformed_scalar_decimal_fails_closed(token: str) -> None:
    def mutate(soup: BeautifulSoup) -> None:
        _first_ranking_row(soup).find_all("td", recursive=False)[1].string = token

    with pytest.raises(NARMarketOddsSourceParseNumericError):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_um_len_fuku", mutate))


def test_duplicate_canonical_selection_fails_closed() -> None:
    def mutate(soup: BeautifulSoup) -> None:
        rows = soup.select("ul.odd_ranking table.odd_ranking_table tr")
        data_rows = [row for row in rows if row.find_all("td", recursive=False)]
        first = data_rows[0].find_all("td", recursive=False)[0].get_text(strip=True)
        data_rows[1].find_all("td", recursive=False)[0].string = first

    with pytest.raises(NARMarketOddsSourceParseDataError, match="duplicate"):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_um_len_fuku", mutate))


@pytest.mark.parametrize("mode", ("missing", "malformed", "inverted"))
def test_malformed_wide_range_fails_closed(mode: str) -> None:
    def mutate(soup: BeautifulSoup) -> None:
        cell = _first_ranking_row(soup).find_all("td", recursive=False)[1]
        cell.clear()
        if mode == "missing":
            cell.append("1.4")
        else:
            cell.append("2.0" if mode == "inverted" else "bad")
            cell.append(soup.new_tag("br"))
            cell.append("-1.0" if mode == "inverted" else "-1.x")

    with pytest.raises(NARMarketOddsSourceParseNumericError):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_wide", mutate))


def test_malformed_authoritative_row_is_not_silently_skipped() -> None:
    def mutate(soup: BeautifulSoup) -> None:
        row = _first_ranking_row(soup)
        row.find_all("td", recursive=False)[2].extract()

    with pytest.raises(NARMarketOddsSourceParseUnsupportedError):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_um_len_fuku", mutate))


def test_hidden_authoritative_row_fails_closed() -> None:
    def mutate(soup: BeautifulSoup) -> None:
        _first_ranking_row(soup)["style"] = "display: none"

    with pytest.raises(NARMarketOddsSourceParseUnsupportedError):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_um_len_fuku", mutate))


def test_hidden_state_heading_fails_closed() -> None:
    def mutate(soup: BeautifulSoup) -> None:
        soup.select_one("h4.odd_title")["hidden"] = ""

    with pytest.raises(NARMarketOddsSourceParseUnsupportedError, match="source-state heading is hidden"):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_tan_fuku", mutate))


def test_aria_hidden_state_heading_fails_closed_case_insensitively() -> None:
    def mutate(soup: BeautifulSoup) -> None:
        soup.select_one("h4.odd_title")["aria-hidden"] = " TRUE "

    with pytest.raises(NARMarketOddsSourceParseUnsupportedError, match="source-state heading is hidden"):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_tan_fuku", mutate))


def test_hidden_ancestor_of_win_authority_fails_closed() -> None:
    def mutate(soup: BeautifulSoup) -> None:
        table = soup.select_one("table.odd_popular_table_02")
        wrapper = soup.new_tag("div")
        wrapper["style"] = "DISPLAY : NONE"
        table.wrap(wrapper)

    with pytest.raises(NARMarketOddsSourceParseUnsupportedError, match="WIN quote table is hidden"):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_tan_fuku", mutate))


def test_hidden_ancestor_of_combination_authority_fails_closed() -> None:
    def mutate(soup: BeautifulSoup) -> None:
        soup.select_one("article.raceCard > div.innerWrapper > div#odd_content")["style"] = (
            "display\t:\tnone"
        )

    with pytest.raises(NARMarketOddsSourceParseUnsupportedError, match="is hidden"):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_um_len_fuku", mutate))


def test_visibility_hidden_combination_authority_fails_closed() -> None:
    def mutate(soup: BeautifulSoup) -> None:
        soup.select_one("div#odd_content > ul.odd_ranking")["style"] = "VISIBILITY : HIDDEN"

    with pytest.raises(NARMarketOddsSourceParseUnsupportedError, match="ranking quote container is hidden"):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_wide", mutate))


def test_noncontiguous_ranking_partition_fails_closed() -> None:
    def mutate(soup: BeautifulSoup) -> None:
        headings = soup.select("ul.odd_ranking > li.odd_ranking_item > h4.odd_ranking_title")
        headings[1].string = "30～32件"

    with pytest.raises(NARMarketOddsSourceParseUnsupportedError):
        parse_nar_market_odds_source_capture(capture=_soup_capture("open/odds_um_len_fuku", mutate))


def test_production_module_has_pure_static_boundary() -> None:
    module_path = REPOSITORY_ROOT / "scripts/simulation/nar_market_odds_source_parser.py"
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {
        "requests",
        "urllib",
        "sqlite3",
        "pathlib",
        "random",
        "uuid",
        "ranking_probability",
    }
    forbidden = (
        "datetime.now",
        "datetime.utcnow",
        "date.today",
        "ValueEngine",
        "BetGenerator",
        "SQLiteNARMarketOddsCaptureArchive",
        "tests/fixtures",
        "manifest.json",
    )
    assert not any(token in source for token in forbidden)
