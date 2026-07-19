import ast
from pathlib import Path
import unittest
P=Path(__file__).parents[1]/'scripts/simulation/providers/interfaces.py'
T=ast.parse(P.read_text(encoding='utf-8'))
def imports():return [n.module or '' for n in ast.walk(T) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(T) if isinstance(n,ast.Import) for a in n.names]
def cls(name):return next(n for n in T.body if isinstance(n,ast.ClassDef) and n.name==name)
class AstProtocolTest(unittest.TestCase):
 def test_interfaces_source_parses_as_ast(self):self.assertIsInstance(T,ast.Module)
 def test_interfaces_imports_only_allowed_modules(self):self.assertTrue(all(not x.startswith(('sqlite3','requests','httpx','urllib','selenium','playwright')) for x in imports()))
 def test_interfaces_does_not_import_sqlite3(self):self.assertNotIn('sqlite3',imports())
 def test_interfaces_does_not_import_repository_sqlite(self):self.assertNotIn('scripts.simulation.repositories.sqlite',imports())
 def test_interfaces_does_not_import_migrations(self):self.assertFalse(any('migration' in x for x in imports()))
 def test_interfaces_does_not_import_fetch_modules(self):self.assertFalse(any(x in ('scripts.fetch_local','scripts.fetch_jra') for x in imports()))
 def test_interfaces_does_not_import_network_libraries(self):self.assertFalse(any(x.startswith(('requests','httpx','urllib')) for x in imports()))
 def test_protocol_classes_exist_in_ast(self):self.assertEqual({x.name for x in T.body if isinstance(x,ast.ClassDef)}&{'RaceResultProvider','OddsSnapshotProvider','PayoutProvider'},{'RaceResultProvider','OddsSnapshotProvider','PayoutProvider'})
 def test_protocols_expose_only_expected_build_methods(self):
  for n,m in [('RaceResultProvider','build_race_result'),('OddsSnapshotProvider','build_odds_batch'),('PayoutProvider','build_payout_publication')]:self.assertEqual([x.name for x in cls(n).body if isinstance(x,ast.FunctionDef)],[m])
 def test_protocols_do_not_expose_persistence_members(self):
  bad={'save','persist','insert','commit','rollback','connect','cursor'}
  for n in ('RaceResultProvider','OddsSnapshotProvider','PayoutProvider'):self.assertFalse({x.name for x in cls(n).body if isinstance(x,ast.FunctionDef)}&bad)
 def test_race_build_method_is_declaration_only(self):self.assertIsInstance(cls('RaceResultProvider').body[0].body[0].value,ast.Constant)
 def test_odds_build_method_is_declaration_only(self):self.assertIsInstance(cls('OddsSnapshotProvider').body[0].body[0].value,ast.Constant)
 def test_payout_build_method_is_declaration_only(self):self.assertIsInstance(cls('PayoutProvider').body[0].body[0].value,ast.Constant)
 def test_provider_build_result_ast_has_no_database_calls(self):self.assertFalse(any(isinstance(x,ast.Call) and getattr(x.func,'id','') in {'connect','execute'} for x in ast.walk(cls('ProviderBuildResult'))))
 def test_provider_build_result_ast_has_no_network_calls(self):self.assertFalse(any(isinstance(x,ast.Call) and getattr(x.func,'id','') in {'get','post'} for x in ast.walk(cls('ProviderBuildResult'))))
