from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
import inspect
from typing import Mapping, Sequence, get_type_hints
import unittest

import scripts.simulation as simulation_package
import scripts.simulation.exact_race_entry_selection_resolver as resolver_module
from scripts.simulation.exact_race_entry_selection_resolver import (
    ExactRaceEntrySelectionResolver,
)
from scripts.simulation.selection_resolver import RaceEntrySelectionResolver


class ExactRaceEntrySelectionResolverTests(unittest.TestCase):
    def test_exact_public_surface_and_shape(self) -> None:
        self.assertEqual(resolver_module.__all__, ("ExactRaceEntrySelectionResolver",))
        self.assertFalse(hasattr(simulation_package, "ExactRaceEntrySelectionResolver"))
        self.assertEqual(
            tuple(field.name for field in fields(ExactRaceEntrySelectionResolver)),
            ("race_id", "allowed_race_entry_ids"),
        )
        self.assertTrue(hasattr(ExactRaceEntrySelectionResolver, "__slots__"))
        resolver = ExactRaceEntrySelectionResolver(71, (901, 902))
        with self.assertRaises(FrozenInstanceError):
            resolver.race_id = 72  # type: ignore[misc]

        signature = inspect.signature(
            ExactRaceEntrySelectionResolver.resolve_race_entry_ids
        )
        self.assertEqual(tuple(signature.parameters), ("self", "race_id", "horse_ids"))
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                for parameter in tuple(signature.parameters.values())[1:]
            )
        )
        hints = get_type_hints(ExactRaceEntrySelectionResolver.resolve_race_entry_ids)
        self.assertIs(hints["race_id"], int)
        self.assertEqual(hints["horse_ids"], Sequence[int])
        self.assertEqual(hints["return"], tuple[int, ...])

    def test_constructor_requires_exact_positive_unique_tuple(self) -> None:
        invalid_values = (
            (True, (901,)),
            (0, (901,)),
            (-1, (901,)),
            (71, [901]),
            (71, set((901,))),
            (71, ()),
            (71, (True,)),
            (71, (0,)),
            (71, (-1,)),
            (71, (901, 901)),
        )
        for race_id, allowlist in invalid_values:
            with self.subTest(race_id=race_id, allowlist=allowlist):
                with self.assertRaises(ValueError):
                    ExactRaceEntrySelectionResolver(race_id, allowlist)  # type: ignore[arg-type]

    def test_exact_request_tuple_and_order_are_preserved(self) -> None:
        resolver = ExactRaceEntrySelectionResolver(71, (901, 902, 903))
        requested = [903, 901]
        result = resolver.resolve_race_entry_ids(race_id=71, horse_ids=requested)
        self.assertEqual(result, (903, 901))
        self.assertEqual(requested, [903, 901])

    def test_wrong_race_and_unallowlisted_values_fail_closed(self) -> None:
        resolver = ExactRaceEntrySelectionResolver(71, (901, 902))
        with self.assertRaises(ValueError):
            resolver.resolve_race_entry_ids(race_id=72, horse_ids=(901,))
        with self.assertRaises(ValueError):
            resolver.resolve_race_entry_ids(race_id=71, horse_ids=(903,))

    def test_request_requires_nonempty_nonmapping_sequence_of_unique_positive_ints(self) -> None:
        resolver = ExactRaceEntrySelectionResolver(71, (901, 902))
        invalid_requests: tuple[object, ...] = (
            "901",
            b"901",
            bytearray(b"901"),
            {"id": 901},
            iter((901,)),
            (),
            (True,),
            (0,),
            (-1,),
            (901, 901),
        )
        for value in invalid_requests:
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    resolver.resolve_race_entry_ids(race_id=71, horse_ids=value)  # type: ignore[arg-type]

    def test_structurally_matches_existing_resolver_protocol(self) -> None:
        protocol_signature = inspect.signature(
            RaceEntrySelectionResolver.resolve_race_entry_ids
        )
        implementation_signature = inspect.signature(
            ExactRaceEntrySelectionResolver.resolve_race_entry_ids
        )
        self.assertEqual(
            tuple(protocol_signature.parameters),
            tuple(implementation_signature.parameters),
        )
        self.assertEqual(
            get_type_hints(RaceEntrySelectionResolver.resolve_race_entry_ids),
            get_type_hints(ExactRaceEntrySelectionResolver.resolve_race_entry_ids),
        )

    def test_static_boundary_has_no_identity_or_external_dependencies(self) -> None:
        source = inspect.getsource(resolver_module)
        tree = ast.parse(source)
        imports = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ] + [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        forbidden = (
            "sqlite3",
            "requests",
            "httpx",
            "pathlib",
            "subprocess",
            "scripts.simulation.repositories",
            "scripts.simulation.race_entry_source",
        )
        self.assertFalse(any(name.startswith(forbidden) for name in imports))
        self.assertNotIn("RaceEntrySource", source)
        self.assertNotIn("horses", source.lower())
        self.assertNotIn("except Exception", source)
        self.assertNotIn("except BaseException", source)


if __name__ == "__main__":
    unittest.main()
