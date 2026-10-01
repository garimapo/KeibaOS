"""Status-independent identities from an already qualified Phase111 Deba capture."""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from scripts.simulation.nar_historical_input_source import (
    NarHistoricalInputSourceError, _canonical_horse_identity,
)
from scripts.simulation.nar_trusted_deba_acquisition import (
    NARQualifiedDebaResultV1, canonical_deba_url, read_qualified_deba_bytes,
)
from scripts.simulation.sqlite_nar_trusted_deba_acquisition_archive import (
    SQLiteNARTrustedDebaAcquisitionArchive,
)
from scripts.simulation.repositories.sqlite_nar_official_response_capture_repository import (
    SQLiteNAROfficialResponseCaptureRepository,
)


_RACE_ID = re.compile(r"nar:[0-9]{8}:[1-9][0-9]*:[1-9][0-9]*\Z", re.ASCII)
_HORSE_NO = re.compile(r"[1-9][0-9]*\Z", re.ASCII)


class NARIdentityCompleteSourceError(ValueError):
    """The qualified source cannot prove one complete entry identity universe."""


def nar_entry_v1(external_race_id: str, horse_no: int) -> str:
    """Derived, not provider-issued: <race-id>:entry:<canonical ASCII number>."""
    if type(external_race_id) is not str or not _RACE_ID.fullmatch(external_race_id):
        raise NARIdentityCompleteSourceError("noncanonical external race identity")
    if type(horse_no) is not int or horse_no <= 0:
        raise NARIdentityCompleteSourceError("noncanonical horse number")
    return f"{external_race_id}:entry:{horse_no}"


@dataclass(frozen=True, slots=True)
class NARIdentityEntryV1:
    external_entry_id: str
    horse_no: int
    external_horse_id: str | None


@dataclass(frozen=True, slots=True)
class NARIdentityCompleteSourceV1:
    external_race_id: str
    canonical_deba_url: str
    phase111_declaration_id: str
    phase111_receipt_id: str
    phase111_capture_id: str
    response_sha256: str
    observed_at: object
    prediction_cutoff: object
    entries: tuple[NARIdentityEntryV1, ...]


def extract_identity_entries(response_body: bytes, external_race_id: str) -> tuple[NARIdentityEntryV1, ...]:
    """Require every identity-bearing row; do not consult status/enrichment text."""
    if type(response_body) is not bytes:
        raise NARIdentityCompleteSourceError("exact response bytes required")
    nar_entry_v1(external_race_id, 1)
    try:
        soup = BeautifulSoup(response_body.decode("utf-8", errors="strict"), "html.parser")
        tables = []
        for table in soup.select("article.raceCard section.cardTable table"):
            if table.select("tr.tBorder, td.horseNum, a.horseName"):
                tables.append(table)
        if len(tables) != 1:
            raise NARIdentityCompleteSourceError("one Deba entry table required")
        rows = []
        for row in tables[0].select("tr"):
            if ("tBorder" in row.get("class", [])
                    or row.select("td.horseNum, a.horseName")):
                rows.append(row)
        if not rows:
            raise NARIdentityCompleteSourceError("no identity-bearing entry rows")
        result = []
        seen_horses = set()
        for row in rows:
            cells = row.find_all("td", class_="horseNum", recursive=False)
            if len(cells) != 1:
                raise NARIdentityCompleteSourceError("horse-number cardinality")
            token = cells[0].get_text(strip=False)
            if not _HORSE_NO.fullmatch(token):
                raise NARIdentityCompleteSourceError("noncanonical horse number")
            number = int(token)
            links = row.select("a.horseName")
            if len(links) > 1 or (links and not links[0].has_attr("href")):
                raise NARIdentityCompleteSourceError("ambiguous horse link")
            horse_identity = _canonical_horse_identity(links[0]["href"]) if links else None
            if number in {item.horse_no for item in result} or (horse_identity is not None and horse_identity in seen_horses):
                raise NARIdentityCompleteSourceError("duplicate entry identity")
            if horse_identity is not None:
                seen_horses.add(horse_identity)
            result.append(NARIdentityEntryV1(nar_entry_v1(external_race_id, number), number, horse_identity))
        return tuple(sorted(result, key=lambda entry: entry.horse_no))
    except (UnicodeError, ValueError, TypeError, KeyError, NarHistoricalInputSourceError) as error:
        if isinstance(error, NARIdentityCompleteSourceError):
            raise
        raise NARIdentityCompleteSourceError("invalid Deba identity structure") from error


def load_identity_complete_source_and_bytes(*, result: NARQualifiedDebaResultV1,
                                            lineage_archive, capture_archive
                                            ) -> tuple[NARIdentityCompleteSourceV1, bytes]:
    """One exact archive read supplies identity extraction and optional enrichment."""
    if type(result) is not NARQualifiedDebaResultV1:
        raise NARIdentityCompleteSourceError("Phase111 qualified result required")
    if (type(lineage_archive) is not SQLiteNARTrustedDebaAcquisitionArchive
            or type(capture_archive) is not SQLiteNAROfficialResponseCaptureRepository):
        raise NARIdentityCompleteSourceError("exact persisted Phase111 archives required")
    body = read_qualified_deba_bytes(
        result=result, lineage_archive=lineage_archive, capture_archive=capture_archive)
    declaration = lineage_archive.load_declaration(declaration_id=result.declaration_id)
    receipt = lineage_archive.load_receipt(receipt_id=result.receipt_id)
    if (declaration.external_race_id != receipt.external_race_id
            or declaration.canonical_deba_url != result.canonical_deba_url
            or canonical_deba_url(declaration.external_race_id) != result.canonical_deba_url):
        raise NARIdentityCompleteSourceError("Phase111 race ancestry contradiction")
    source = NARIdentityCompleteSourceV1(
        declaration.external_race_id, result.canonical_deba_url,
        result.declaration_id, result.receipt_id, result.capture_id,
        result.response_sha256, result.observed_at,
        declaration.prediction_information_cutoff,
        extract_identity_entries(body, declaration.external_race_id))
    return source, body


def load_identity_complete_source(*, result: NARQualifiedDebaResultV1,
                                  lineage_archive, capture_archive) -> NARIdentityCompleteSourceV1:
    """Only Phase111 archive readback supplies bytes and external race ancestry."""
    source, _ = load_identity_complete_source_and_bytes(
        result=result, lineage_archive=lineage_archive, capture_archive=capture_archive)
    return source


def load_identity_with_legacy_enrichment(*, result: NARQualifiedDebaResultV1,
                                         lineage_archive, capture_archive, race_id: int):
    """Demonstrate unchanged HorseParser fan-out; parser omissions never define identity."""
    if type(race_id) is not int or race_id <= 0:
        raise NARIdentityCompleteSourceError("positive existing race ID required")
    source, body = load_identity_complete_source_and_bytes(
        result=result, lineage_archive=lineage_archive, capture_archive=capture_archive)
    from scripts.parsers.horse_parser import HorseParser
    return source, tuple(HorseParser().parse(body.decode("utf-8", errors="strict"), race_id))
