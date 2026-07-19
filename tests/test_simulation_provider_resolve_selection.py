import unittest
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import RaceEntryUniverse,RawOddsEntry,RawPayoutRecord
from scripts.simulation.providers.normalization import resolve_selection
from scripts.simulation.repositories.interfaces import normalize_selection
class ResolveTest(unittest.TestCase):
 def setUp(self):self.u=RaceEntryUniverse(1,{1,2,3,4},{5},{6},{11:1,12:2,13:3,14:4,15:5,16:6})
 def r(self,a=None,b=None,k='単勝'):return resolve_selection(a,b,k,self.u)
 def test_resolves_win_from_race_entry_ids(self):self.assertEqual(self.r([1]),(1,))
 def test_resolves_quinella_from_race_entry_ids_in_sorted_order(self):self.assertEqual(self.r([2,1],k='馬連'),(1,2))
 def test_resolves_wide_from_horse_numbers(self):self.assertEqual(self.r(b=[12,11],k='ワイド'),(1,2))
 def test_resolves_trio_from_horse_numbers(self):self.assertEqual(self.r(b=[13,11,12],k='3連複'),(1,2,3))
 def test_rejects_both_selection_sources(self):
  with self.assertRaises(ProviderValidationError):self.r([1],[11])
 def test_rejects_missing_selection_sources(self):
  with self.assertRaises(ProviderValidationError):self.r()
 def test_rejects_empty_race_entry_ids(self):
  with self.assertRaises(ProviderValidationError):self.r([])
 def test_rejects_empty_horse_numbers(self):
  with self.assertRaises(ProviderValidationError):self.r(b=[])
 def test_rejects_invalid_universe_type(self):
  with self.assertRaises(ProviderValidationError):resolve_selection([1],None,'単勝',{})
 def test_rejects_bad_ids(self):
  for x in (True,0,-1,1.0,'1',None):
   with self.assertRaises(ProviderValidationError):self.r([x])
 def test_rejects_duplicates(self):
  with self.assertRaises(ProviderValidationError):self.r([1,1],k='馬連')
 def test_rejects_inactive(self):
  for x in (5,6,99):
   with self.assertRaises(ProviderValidationError):self.r([x])
 def test_rejects_unknown_horse(self):
  with self.assertRaises(ProviderValidationError):self.r(b=[99])
 def test_rejects_inactive_horse(self):
  for x in (15,16):
   with self.assertRaises(ProviderValidationError):self.r(b=[x])
 def test_rejects_wrong_count(self):
  with self.assertRaises(ProviderValidationError):self.r([1],k='馬連')
 def test_rejects_unsupported_bet_type(self):
  with self.assertRaises(ProviderValidationError):self.r([1],k='x')
 def test_does_not_mutate_inputs(self):
  a=[2,1];self.r(a,k='馬連');self.assertEqual(a,[2,1])
 def test_accepts_raw_entries(self):
  o=RawOddsEntry([1],None,'x');p=RawPayoutRecord(None,[11],'0','x');self.assertEqual(self.r(o.race_entry_ids),(1,));self.assertEqual(self.r(b=p.horse_numbers),(1,))
 def test_output_matches_repository_normalize_selection(self):self.assertEqual(self.r([2,1],k='馬連'),normalize_selection([2,1],'馬連'))
