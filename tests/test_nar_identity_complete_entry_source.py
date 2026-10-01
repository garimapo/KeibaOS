"""Offline status-independent identity extraction from exact Phase111 archive bytes."""

import pytest

from scripts.simulation.nar_identity_complete_entry_source import (
    NARIdentityCompleteSourceError, extract_identity_entries,
    load_identity_complete_source, load_identity_with_legacy_enrichment, nar_entry_v1,
)
from test_nar_trusted_deba_acquisition import acquire, environment


def deba(*rows):
    return ("<article class='raceCard'><section class='cardTable'><table>"
            + "".join(rows) + "</table></section></article>").encode("utf-8")


def row(number, lineage="100", extra=""):
    link = (f'<a class="horseName" href="/KeibaWeb/DataRoom/HorseMarkInfo?'
            f'k_lineageLoginCode={lineage}">Horse</a>') if lineage is not None else ""
    return f'<tr><td class="horseNum">{number}</td><td>{link}</td><td>{extra}</td></tr>'


BODY = deba(row("1", "100"), row("2", "200", "出走取消"), row("3", None, "競走除外"))


def qualified_env(body=BODY):
    env = environment()
    env.transport.body = body
    _, result = acquire(env)
    return env, result


def close_env(env):
    for connection in env.connections:
        connection.close()


def test_status_independent_complete_population_and_versioned_identity():
    env, result = qualified_env()
    try:
        source = load_identity_complete_source(result=result, lineage_archive=env.lineage,
                                               capture_archive=env.captures)
        assert [entry.horse_no for entry in source.entries] == [1, 2, 3]
        assert [entry.external_entry_id for entry in source.entries] == [
            "nar:20250101:21:1:entry:1", "nar:20250101:21:1:entry:2",
            "nar:20250101:21:1:entry:3"]
        assert source.entries[2].external_horse_id is None
        assert source.entries[0].external_horse_id == "nar:horse:100"
        assert source.phase111_receipt_id == result.receipt_id
        assert env.transport.urls == [result.canonical_deba_url]
    finally:
        close_env(env)


@pytest.mark.parametrize("number", ["0", "01", " 1", "1 ", "-1", "", "１"])
def test_noncanonical_numbers_fail_closed(number):
    with pytest.raises(NARIdentityCompleteSourceError):
        extract_identity_entries(deba(row(number)), "nar:20250101:21:1")


@pytest.mark.parametrize("body", [
    deba(row("1"), row("1", "200")),
    deba(row("1", "100"), row("2", "100")),
    deba('<tr><td><a class="horseName" href="/KeibaWeb/DataRoom/HorseMarkInfo?k_lineageLoginCode=1">Horse</a></td></tr>'),
    deba('<tr><td class="horseNum">1</td><td class="horseNum">2</td></tr>'),
    deba('<tr><td class="horseNum">1</td><td><a class="horseName">Horse</a></td></tr>'),
    deba('<tr><td class="horseNum">1</td><td><a class="horseName" href="https://evil.invalid/1">Horse</a></td></tr>'),
    deba('<tr class="tBorder"><td>entry number missing</td></tr>'),
    b"\xff",
    b"<html></html>",
])
def test_ambiguous_missing_duplicate_or_invalid_bytes_fail_closed(body):
    with pytest.raises(NARIdentityCompleteSourceError):
        extract_identity_entries(body, "nar:20250101:21:1")


def test_derived_identity_is_canonical_not_provider_issued():
    assert nar_entry_v1("nar:20250101:21:1", 12) == "nar:20250101:21:1:entry:12"
    for bad in (0, -1, True, "1"):
        with pytest.raises(NARIdentityCompleteSourceError):
            nar_entry_v1("nar:20250101:21:1", bad)
    with pytest.raises(NARIdentityCompleteSourceError):
        nar_entry_v1("nar:20250101:21:01", 1)


def test_caller_constructed_result_or_archive_cannot_authorize_extraction():
    env, result = qualified_env()
    try:
        with pytest.raises(NARIdentityCompleteSourceError):
            load_identity_complete_source(result=result, lineage_archive=object(),
                                          capture_archive=env.captures)
        with pytest.raises(NARIdentityCompleteSourceError):
            load_identity_complete_source(result=object(), lineage_archive=env.lineage,
                                          capture_archive=env.captures)
    finally:
        close_env(env)


def test_optional_legacy_parser_receives_strict_decode_of_same_capture_bytes(monkeypatch):
    from scripts.parsers.horse_parser import HorseParser

    seen = []
    def parse(self, html, race_id):
        seen.append((html, race_id))
        return []
    monkeypatch.setattr(HorseParser, "parse", parse)
    env, result = qualified_env()
    try:
        source, enriched = load_identity_with_legacy_enrichment(
            result=result, lineage_archive=env.lineage,
            capture_archive=env.captures, race_id=1)
        assert len(source.entries) == 3 and enriched == ()
        assert seen == [(BODY.decode("utf-8", errors="strict"), 1)]
        assert len(env.transport.urls) == 1
    finally:
        close_env(env)
