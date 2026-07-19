import unittest
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import expected_selections,RaceEntryUniverse
from scripts.simulation.repositories.interfaces import normalize_selection
class ExpectedSelectionsTest(unittest.TestCase):
 def test_expected_win_selections(self):self.assertEqual(expected_selections([3,1,2],'単勝'),((1,),(2,),(3,)))
 def test_expected_quinella_selections(self):self.assertEqual(expected_selections([3,1,2],'馬連'),((1,2),(1,3),(2,3)))
 def test_expected_wide_selections(self):self.assertEqual(expected_selections([3,1,2],'ワイド'),((1,2),(1,3),(2,3)))
 def test_expected_trio_selections(self):self.assertEqual(expected_selections([4,1,3,2],'3連複'),((1,2,3),(1,2,4),(1,3,4),(2,3,4)))
 def test_input_order_does_not_change_output(self):self.assertEqual(expected_selections([3,1,2],'馬連'),expected_selections([2,3,1],'馬連'))
 def test_empty_input_returns_empty_tuple(self):self.assertEqual(expected_selections([],'単勝'),())
 def test_insufficient_entries_return_empty_tuple(self):self.assertEqual(expected_selections([1],'馬連'),())
 def test_rejects_bool_zero_and_negative_ids(self):
  for x in (True,0,-1):
   with self.assertRaises(ProviderValidationError):expected_selections([x],'単勝')
 def test_rejects_float_string_and_none_ids(self):
  for x in (1.0,'1',None):
   with self.assertRaises(ProviderValidationError):expected_selections([x],'単勝')
 def test_rejects_duplicate_ids(self):
  with self.assertRaises(ProviderValidationError):expected_selections([1,1],'単勝')
 def test_rejects_unsupported_bet_type(self):
  with self.assertRaises(ProviderValidationError):expected_selections([1],'x')
 def test_rejects_string_bytes_and_mapping_collections(self):
  for x in ('12',b'12',{1:2}):
   with self.assertRaises(ProviderValidationError):expected_selections(x,'単勝')
 def test_accepts_generator_without_double_consumption(self):self.assertEqual(expected_selections((x for x in [2,1]),'馬連'),((1,2),))
 def test_does_not_mutate_input_list(self):
  x=[2,1];expected_selections(x,'馬連');self.assertEqual(x,[2,1])
 def test_accepts_universe_active_entries(self):
  u=RaceEntryUniverse(1,{1,2},{3},{4},{1:1,2:2,3:3,4:4});self.assertEqual(expected_selections(u.active_entries,'馬連'),((1,2),))
 def test_matches_repository_selection_normalization(self):
  for kind in ('単勝','馬連','ワイド','3連複'):
   for item in expected_selections([1,2,3],'3連複' if kind=='3連複' else kind):self.assertEqual(item,normalize_selection(item,kind))
 def test_output_is_fully_immutable_tuple_structure(self):
  out=expected_selections([1,2],'馬連');self.assertIsInstance(out,tuple);self.assertIsInstance(out[0],tuple)
