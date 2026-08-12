from __future__ import annotations

import ast
from dataclasses import is_dataclass
import inspect
from pathlib import Path
import unittest

from scripts.simulation.jra_official_identity import (
    JRAExternalHorseIdentity,
    JRAExternalRaceIdentity,
    JRAOfficialIdentityError,
    JRAOfficialIdentityValidationError,
    build_jra_external_entry_id,
    build_jra_provider_record_id,
    parse_jra_external_horse_id,
    parse_jra_external_race_id,
    parse_jra_horse_profile_url_identity,
    parse_jra_result_url_identity,
)


RACE_ID = "jra:race:2025:06:04:03:04"
HORSE_ID = "jra:horse:2020102902"
ACCESS_S_01 = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC"
ACCESS_S_10 = "https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde1006202504030420250913/BB"
ACCESS_U_00 = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud002020102902%2F22"
ACCESS_U_10 = "https://www.jra.go.jp/JRADB/accessU.html?CNAME=pw01dud102020102902/EB"


class JRAOfficialIdentityTests(unittest.TestCase):
    def test_exact_public_api_and_pure_boundary(self) -> None:
        import scripts.simulation.jra_official_identity as module

        self.assertEqual(
            {name for name in vars(module) if not name.startswith("_")},
            {
                "JRAOfficialIdentityError", "JRAOfficialIdentityValidationError", "JRAExternalRaceIdentity",
                "JRAExternalHorseIdentity", "parse_jra_external_race_id", "parse_jra_external_horse_id",
                "parse_jra_result_url_identity", "parse_jra_horse_profile_url_identity",
                "build_jra_external_entry_id", "build_jra_provider_record_id",
            },
        )
        self.assertTrue(issubclass(JRAOfficialIdentityValidationError, JRAOfficialIdentityError))
        self.assertTrue(is_dataclass(JRAExternalRaceIdentity) and JRAExternalRaceIdentity.__dataclass_params__.frozen)
        self.assertTrue(is_dataclass(JRAExternalHorseIdentity) and JRAExternalHorseIdentity.__dataclass_params__.frozen)
        self.assertEqual(tuple(inspect.signature(build_jra_external_entry_id).parameters), ("race_identity", "horse_no"))
        self.assertEqual(tuple(inspect.signature(build_jra_provider_record_id).parameters), ("race_identity", "horse_identity"))
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden = {"requests", "httpx", "sqlite3", "pathlib", "random", "subprocess", "time", "socket"}
        self.assertFalse(any(
            (isinstance(node, ast.Import) and any(item.name.split(".")[0] in forbidden for item in node.names))
            or (isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in forbidden)
            for node in ast.walk(tree)
        ))
        self.assertNotIn("open(", source)
        self.assertNotIn("now(", source)
        self.assertNotIn("nar_", source.lower())
        self.assertNotIn("HorseMark", source)
        self.assertNotIn("lineage", source.lower())

    def test_race_identity_uses_exact_lexical_fields(self) -> None:
        identity = parse_jra_external_race_id(RACE_ID)
        self.assertEqual(
            (identity.year, identity.venue_code, identity.meeting_number, identity.meeting_day, identity.race_number),
            ("2025", "06", "04", "03", "04"),
        )
        self.assertEqual(identity.external_race_id, RACE_ID)
        self.assertEqual(identity, JRAExternalRaceIdentity("2025", "06", "04", "03", "04"))
        with self.assertRaises((AttributeError, TypeError)):
            identity.year = "2026"  # type: ignore[misc]

    def test_race_identity_rejects_invalid_tokens_and_non_exact_types(self) -> None:
        invalid = (
            "jra:race:2025:00:04:03:04", "jra:race:2025:11:04:03:04", "jra:race:2025:99:04:03:04",
            "jra:race:2025:06:00:03:04", "jra:race:2025:06:04:00:04", "jra:race:2025:06:04:13:04",
            "jra:race:2025:06:04:03:00", "jra:race:2025:06:04:03:13", "jra:race:2025:6:04:03:04",
            "jra:race:2025:06:4:03:04", "jra:race:２０２５:06:04:03:04", "jra:race:+2025:06:04:03:04",
            "jra:race:2025:06:04:03:04 ", "JRA:race:2025:06:04:03:04", "jra:RACE:2025:06:04:03:04",
            "jra:race:2025:06:04:03", "jra:race:2025:06:04:03:04:extra",
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(JRAOfficialIdentityValidationError):
                parse_jra_external_race_id(value)
        for value in (b"jra:race:2025:06:04:03:04", 1, True, object(), type("S", (str,), {})(RACE_ID)):
            with self.subTest(type=type(value)), self.assertRaises(JRAOfficialIdentityValidationError):
                parse_jra_external_race_id(value)  # type: ignore[arg-type]

    def test_result_access_s_aliases_collapse_and_omit_navigation_material(self) -> None:
        one = parse_jra_result_url_identity(ACCESS_S_01)
        two = parse_jra_result_url_identity(ACCESS_S_10)
        self.assertEqual(one, two)
        self.assertEqual(one.external_race_id, RACE_ID)
        self.assertEqual(parse_jra_result_url_identity(ACCESS_S_01.replace("20250913", "20251213")), one)
        self.assertNotIn("20250913", one.external_race_id)
        self.assertNotIn("sde", one.external_race_id)
        self.assertNotIn("DC", one.external_race_id)
        self.assertNotEqual(
            parse_jra_result_url_identity(ACCESS_S_01.replace("0403", "0404", 1)), one
        )
        self.assertNotEqual(
            parse_jra_result_url_identity(ACCESS_S_01.replace("0106", "0105", 1)), one
        )
        self.assertNotEqual(
            parse_jra_result_url_identity(ACCESS_S_01.replace("0403", "0503", 1)), one
        )

    def test_result_access_s_rejects_noncanonical_or_malformed_urls(self) -> None:
        invalid = (
            ACCESS_S_01.replace("https://", "http://"), ACCESS_S_01.replace("www.jra.go.jp", "jra.go.jp"),
            ACCESS_S_01.replace("www.jra.go.jp", "www2.jra.go.jp"), ACCESS_S_01.replace("www.jra.go.jp", "WWW.JRA.GO.JP"),
            ACCESS_S_01.replace("accessS.html", "accessD.html"), ACCESS_S_01.replace("?CNAME=", ":443?CNAME="),
            ACCESS_S_01.replace("https://", "https://user@"), ACCESS_S_01 + "#fragment",
            ACCESS_S_01 + "&other=x", ACCESS_S_01 + "&CNAME=x", "https://www.jra.go.jp/JRADB/accessS.html",
            "https://www.jra.go.jp/JRADB/accessS.html?CNAME=", ACCESS_S_01.replace("%2F", "%252F"),
            ACCESS_S_01.replace("%2F", "%2f"), ACCESS_S_01.replace("%2F", "+"), ACCESS_S_01.replace("DC", "D"),
            ACCESS_S_01.replace("DC", "DG"), ACCESS_S_01.replace("DC", "dc"), ACCESS_S_01.replace("sde01", "sde11"),
            ACCESS_S_01.replace("2025040304", "2026040304"), ACCESS_S_01.replace("20250913", "20251313"),
            ACCESS_S_01 + "%0A", " https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde0106202504030420250913%2FDC",
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(JRAOfficialIdentityValidationError):
                parse_jra_result_url_identity(value)

    def test_horse_identity_and_access_u_aliases_collapse(self) -> None:
        identity = parse_jra_external_horse_id(HORSE_ID)
        self.assertEqual(identity.horse_key, "2020102902")
        self.assertEqual(identity.external_horse_id, HORSE_ID)
        self.assertEqual(parse_jra_horse_profile_url_identity(ACCESS_U_00), identity)
        self.assertEqual(parse_jra_horse_profile_url_identity(ACCESS_U_10), identity)
        self.assertNotEqual(parse_jra_external_horse_id("jra:horse:2020102903"), identity)
        for value in (
            "jra:horse:202010290", "jra:horse:20201029020", "jra:horse:２０２０１０２９０２",
            "jra:horse:+2020102902", "jra:horse:2020102902 ", "nar:horse:2020102902",
            "jra:horse:2020102902:extra", b"jra:horse:2020102902", 1, True,
        ):
            with self.subTest(value=value), self.assertRaises(JRAOfficialIdentityValidationError):
                parse_jra_external_horse_id(value)  # type: ignore[arg-type]

    def test_access_u_rejects_malformed_urls_and_cnames(self) -> None:
        invalid = (
            ACCESS_U_00.replace("https://", "http://"), ACCESS_U_00.replace("www.jra.go.jp", "jra.go.jp"),
            ACCESS_U_00.replace("accessU.html", "accessS.html"), ACCESS_U_00.replace("?CNAME=", ":443?CNAME="),
            ACCESS_U_00.replace("https://", "https://user:pass@"), ACCESS_U_00 + "#fragment",
            ACCESS_U_00 + "&x=1", ACCESS_U_00 + "&CNAME=x", ACCESS_U_00.replace("%2F", "%252F"),
            ACCESS_U_00.replace("%2F", "%2f"), ACCESS_U_00.replace("%2F", "+"), ACCESS_U_00.replace("dud00", "dud11"),
            ACCESS_U_00.replace("22", "2"), ACCESS_U_00.replace("22", "2G"), ACCESS_U_00.replace("22", "aa"),
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(JRAOfficialIdentityValidationError):
                parse_jra_horse_profile_url_identity(value)

    def test_entry_and_result_builders_are_exact_and_fail_closed(self) -> None:
        race = parse_jra_external_race_id(RACE_ID)
        horse = parse_jra_external_horse_id(HORSE_ID)
        self.assertEqual(build_jra_external_entry_id(race_identity=race, horse_no=7), RACE_ID + ":entry:7")
        self.assertEqual(build_jra_external_entry_id(race_identity=race, horse_no="18"), RACE_ID + ":entry:18")
        self.assertEqual(
            build_jra_provider_record_id(race_identity=race, horse_identity=horse),
            "jra:result:2025:06:04:03:04:horse:2020102902",
        )
        for value in (0, -1, True, 1.0, "0", "01", "+1", " 1", "１", b"1"):
            with self.subTest(value=value), self.assertRaises(JRAOfficialIdentityValidationError):
                build_jra_external_entry_id(race_identity=race, horse_no=value)  # type: ignore[arg-type]
        with self.assertRaises(JRAOfficialIdentityValidationError):
            build_jra_external_entry_id(race_identity=object(), horse_no=1)  # type: ignore[arg-type]
        with self.assertRaises(JRAOfficialIdentityValidationError):
            build_jra_provider_record_id(race_identity=race, horse_identity=object())  # type: ignore[arg-type]
        changed_race = parse_jra_external_race_id("jra:race:2025:06:04:03:05")
        changed_horse = parse_jra_external_horse_id("jra:horse:2020102903")
        self.assertNotEqual(
            build_jra_provider_record_id(race_identity=race, horse_identity=horse),
            build_jra_provider_record_id(race_identity=changed_race, horse_identity=horse),
        )
        self.assertNotEqual(
            build_jra_provider_record_id(race_identity=race, horse_identity=horse),
            build_jra_provider_record_id(race_identity=race, horse_identity=changed_horse),
        )


if __name__ == "__main__":
    unittest.main()
