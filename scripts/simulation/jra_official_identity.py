"""Pure lexical identities for supplied official JRA URL contexts."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from datetime import date as _date
import hashlib as _hashlib
import json as _json
import re as _re
from urllib.parse import urlsplit as _urlsplit


class JRAOfficialIdentityError(ValueError):
    """Base error for the closed JRA official identity domain."""


class JRAOfficialIdentityValidationError(JRAOfficialIdentityError):
    """Raised when a JRA identity input is malformed or outside this contract."""


_HOST = "www.jra.go.jp"
_RESULT_PATH = "/JRADB/accessS.html"
_PROFILE_PATH = "/JRADB/accessU.html"
_RACE_CARD_PATH = "/JRADB/accessD.html"
_FINAL_ODDS_ENDPOINT = "https://www.jra.go.jp/JRADB/accessO.html"
_RACE_PREFIX = "jra:race"
_HORSE_PREFIX = "jra:horse"
_YEAR = _re.compile(r"[0-9]{4}\Z")
_VENUE = _re.compile(r"(?:0[1-9]|10)\Z")
_MEETING = _re.compile(r"(?:0[1-9]|[1-9][0-9])\Z")
_DAY_OR_RACE = _re.compile(r"(?:0[1-9]|1[0-2])\Z")
_HORSE_KEY = _re.compile(r"[0-9]{10}\Z")
_ENTRY_HORSE = _re.compile(r"[1-9][0-9]*\Z")
_PERCENT = _re.compile(r"%(?:[0-9A-Fa-f]{2})")
_RESULT_CNAME = _re.compile(
    r"pw01sde(?:01|10)(?P<venue>(?:0[1-9]|10))(?P<year>[0-9]{4})"
    r"(?P<meeting>(?:0[1-9]|[1-9][0-9]))(?P<day>(?:0[1-9]|1[0-2]))"
    r"(?P<race>(?:0[1-9]|1[0-2]))(?P<date>[0-9]{8})/(?P<tail>[0-9A-F]{2})\Z"
)
_PROFILE_CNAME = _re.compile(
    r"pw01dud(?:00|10)(?P<horse_key>[0-9]{10})/(?P<tail>[0-9A-F]{2})\Z"
)
_RACE_CARD_CNAME = _re.compile(
    r"pw01dde(?:01|10)(?P<venue>(?:0[1-9]|10))(?P<year>[0-9]{4})"
    r"(?P<meeting>(?:0[1-9]|[1-9][0-9]))(?P<day>(?:0[1-9]|1[0-2]))"
    r"(?P<race>(?:0[1-9]|1[0-2]))(?P<date>[0-9]{8})/(?P<tail>[0-9A-F]{2})\Z"
)
_FINAL_ODDS_CNAME = _re.compile(
    r"pw151ou10(?P<venue>(?:0[1-9]|10))(?P<year>[0-9]{4})"
    r"(?P<meeting>(?:0[1-9]|[1-9][0-9]))(?P<day>(?:0[1-9]|1[0-2]))"
    r"(?P<race>(?:0[1-9]|1[0-2]))(?P<date>[0-9]{8})Z/(?P<tail>[0-9A-F]{2})\Z"
)


def _validation(message: str) -> JRAOfficialIdentityValidationError:
    return JRAOfficialIdentityValidationError(message)


def _strict_str(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise _validation(f"{name} must be a non-empty exact str")
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value):
        raise _validation(f"{name} must not contain whitespace or control characters")
    return value


def _race_tokens(
    year: object,
    venue_code: object,
    meeting_number: object,
    meeting_day: object,
    race_number: object,
) -> tuple[str, str, str, str, str]:
    values = (
        (_strict_str(year, "year"), _YEAR, "year"),
        (_strict_str(venue_code, "venue_code"), _VENUE, "venue_code"),
        (_strict_str(meeting_number, "meeting_number"), _MEETING, "meeting_number"),
        (_strict_str(meeting_day, "meeting_day"), _DAY_OR_RACE, "meeting_day"),
        (_strict_str(race_number, "race_number"), _DAY_OR_RACE, "race_number"),
    )
    for value, grammar, name in values:
        if grammar.fullmatch(value) is None:
            raise _validation(f"{name} is outside the JRA lexical domain")
    return tuple(value for value, _grammar, _name in values)  # type: ignore[return-value]


@_dataclass(frozen=True, slots=True)
class JRAExternalRaceIdentity:
    """One provider-native JRA race identity with lexical canonical fields."""

    year: str
    venue_code: str
    meeting_number: str
    meeting_day: str
    race_number: str

    def __post_init__(self) -> None:
        _race_tokens(self.year, self.venue_code, self.meeting_number, self.meeting_day, self.race_number)

    @property
    def external_race_id(self) -> str:
        return ":".join(
            (_RACE_PREFIX, self.year, self.venue_code, self.meeting_number, self.meeting_day, self.race_number)
        )


@_dataclass(frozen=True, slots=True)
class JRAExternalHorseIdentity:
    """One provider-native JRA accessU profile identity."""

    horse_key: str

    def __post_init__(self) -> None:
        if type(self.horse_key) is not str or _HORSE_KEY.fullmatch(self.horse_key) is None:
            raise _validation("horse_key must be ten ASCII digits")

    @property
    def external_horse_id(self) -> str:
        return f"{_HORSE_PREFIX}:{self.horse_key}"


def _final_odds_identity(cname: object) -> JRAExternalRaceIdentity:
    value = _strict_str(cname, "cname")
    if "%" in value or "+" in value:
        raise _validation("cname must be raw canonical request material")
    match = _FINAL_ODDS_CNAME.fullmatch(value)
    if match is None:
        raise _validation("cname is outside the approved accessO family")
    fields = match.groupdict()
    _validate_cname_date(fields["date"], fields["year"])
    return JRAExternalRaceIdentity(
        fields["year"], fields["venue"], fields["meeting"], fields["day"], fields["race"]
    )


def _final_odds_fingerprint(cname: str) -> str:
    material = {
        "endpoint_url": _FINAL_ODDS_ENDPOINT,
        "form": {"cname": cname},
        "method": "POST",
        "schema_version": 1,
    }
    return _hashlib.sha256(
        _json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


@_dataclass(frozen=True, slots=True)
class JRAOfficialFinalWinOddsRequestLocator:
    """Validated official accessO POST material for one JRA race."""

    endpoint_url: str
    cname: str
    external_race_identity: JRAExternalRaceIdentity
    request_identity_sha256: str

    def __post_init__(self) -> None:
        if type(self.endpoint_url) is not str or self.endpoint_url != _FINAL_ODDS_ENDPOINT:
            raise _validation("endpoint_url is not the approved accessO endpoint")
        identity = _final_odds_identity(self.cname)
        if type(self.external_race_identity) is not JRAExternalRaceIdentity or self.external_race_identity != identity:
            raise _validation("external_race_identity disagrees with cname")
        fingerprint = _final_odds_fingerprint(self.cname)
        if type(self.request_identity_sha256) is not str or self.request_identity_sha256 != fingerprint:
            raise _validation("request_identity_sha256 disagrees with canonical request material")


def build_jra_final_win_odds_request_locator(*, cname: str) -> JRAOfficialFinalWinOddsRequestLocator:
    """Build the sole approved accessO final-win-odds request locator."""

    identity = _final_odds_identity(cname)
    return JRAOfficialFinalWinOddsRequestLocator(
        endpoint_url=_FINAL_ODDS_ENDPOINT,
        cname=cname,
        external_race_identity=identity,
        request_identity_sha256=_final_odds_fingerprint(cname),
    )


def parse_jra_external_race_id(value: str) -> JRAExternalRaceIdentity:
    """Parse the sole canonical JRA external race-ID spelling."""

    text = _strict_str(value, "external_race_id")
    parts = text.split(":")
    if len(parts) != 7 or tuple(parts[:2]) != ("jra", "race"):
        raise _validation("external_race_id is invalid")
    return JRAExternalRaceIdentity(*parts[2:])


def parse_jra_external_horse_id(value: str) -> JRAExternalHorseIdentity:
    """Parse the sole canonical JRA external horse-ID spelling."""

    text = _strict_str(value, "external_horse_id")
    parts = text.split(":")
    if len(parts) != 3 or tuple(parts[:2]) != ("jra", "horse"):
        raise _validation("external_horse_id is invalid")
    return JRAExternalHorseIdentity(parts[2])


def _bad_percent_encoding(value: str) -> bool:
    return any(value[index] == "%" and _PERCENT.match(value, index) is None for index in range(len(value)))


def _resolved_cname(value: object, path: str, name: str) -> str:
    url = _strict_str(value, name)
    if _bad_percent_encoding(url):
        raise _validation(f"{name} contains malformed percent encoding")
    try:
        parsed = _urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise _validation(f"{name} is invalid") from error
    if parsed.scheme != "https" or parsed.netloc != _HOST or parsed.hostname != _HOST or port is not None:
        raise _validation(f"{name} host, scheme, or port is invalid")
    if parsed.username is not None or parsed.password is not None or parsed.fragment or parsed.path != path:
        raise _validation(f"{name} structure is invalid")
    if not parsed.query or "+" in parsed.query:
        raise _validation(f"{name} query is invalid")
    pairs = parsed.query.split("&")
    if len(pairs) != 1 or "=" not in pairs[0]:
        raise _validation(f"{name} query is invalid")
    key, raw_cname = pairs[0].split("=", 1)
    if key != "CNAME" or not raw_cname:
        raise _validation(f"{name} query is invalid")
    if "%" in raw_cname:
        if raw_cname.count("%2F") != 1 or raw_cname.replace("%2F", "/") != raw_cname.replace("%2F", "/", 1):
            raise _validation(f"{name} CNAME encoding is invalid")
        raw_cname = raw_cname.replace("%2F", "/")
    return raw_cname


def _validate_cname_date(value: str, year: str) -> None:
    if value[:4] != year:
        raise _validation("result CNAME date year disagrees with race year")
    try:
        _date.fromisoformat(f"{value[:4]}-{value[4:6]}-{value[6:8]}")
    except ValueError as error:
        raise _validation("result CNAME date is invalid") from error


def parse_jra_result_url_identity(value: str) -> JRAExternalRaceIdentity:
    """Validate a resolved official accessS URL and return its race identity."""

    cname = _resolved_cname(value, _RESULT_PATH, "result_url")
    match = _RESULT_CNAME.fullmatch(cname)
    if match is None:
        raise _validation("result_url CNAME is outside the approved accessS family")
    fields = match.groupdict()
    _validate_cname_date(fields["date"], fields["year"])
    return JRAExternalRaceIdentity(
        fields["year"], fields["venue"], fields["meeting"], fields["day"], fields["race"]
    )


def parse_jra_horse_profile_url_identity(value: str) -> JRAExternalHorseIdentity:
    """Validate a resolved official accessU URL and return its horse identity."""

    cname = _resolved_cname(value, _PROFILE_PATH, "horse_profile_url")
    match = _PROFILE_CNAME.fullmatch(cname)
    if match is None:
        raise _validation("horse_profile_url CNAME is outside the approved accessU family")
    return JRAExternalHorseIdentity(match.group("horse_key"))


def parse_jra_race_card_url_identity(value: str) -> JRAExternalRaceIdentity:
    """Validate a canonical official accessD card URL and return its race identity."""

    if type(value) is not str or "%2F" not in value or "/" not in value.split("CNAME=", 1)[-1].replace("%2F", "/"):
        raise _validation("race_card_url must use the canonical %2F delimiter")
    cname = _resolved_cname(value, _RACE_CARD_PATH, "race_card_url")
    match = _RACE_CARD_CNAME.fullmatch(cname)
    if match is None:
        raise _validation("race_card_url CNAME is outside the approved accessD family")
    fields = match.groupdict()
    _validate_cname_date(fields["date"], fields["year"])
    return JRAExternalRaceIdentity(
        fields["year"], fields["venue"], fields["meeting"], fields["day"], fields["race"]
    )


def _entry_horse_number(value: object) -> str:
    if type(value) is int:
        if value <= 0:
            raise _validation("horse_no must be positive")
        return str(value)
    if type(value) is str and _ENTRY_HORSE.fullmatch(value) is not None:
        return value
    raise _validation("horse_no must be a positive canonical decimal int or str")


def build_jra_external_entry_id(*, race_identity: JRAExternalRaceIdentity, horse_no: int | str) -> str:
    """Build the race-local JRA entry identity without conflating horse identity."""

    if type(race_identity) is not JRAExternalRaceIdentity:
        raise _validation("race_identity must be JRAExternalRaceIdentity")
    return f"{race_identity.external_race_id}:entry:{_entry_horse_number(horse_no)}"


def build_jra_provider_record_id(
    *, race_identity: JRAExternalRaceIdentity, horse_identity: JRAExternalHorseIdentity
) -> str:
    """Build one JRA horse-result provider record identity."""

    if type(race_identity) is not JRAExternalRaceIdentity:
        raise _validation("race_identity must be JRAExternalRaceIdentity")
    if type(horse_identity) is not JRAExternalHorseIdentity:
        raise _validation("horse_identity must be JRAExternalHorseIdentity")
    return (
        f"jra:result:{race_identity.year}:{race_identity.venue_code}:{race_identity.meeting_number}:"
        f"{race_identity.meeting_day}:{race_identity.race_number}:horse:{horse_identity.horse_key}"
    )


if "annotations" in globals():
    del annotations
