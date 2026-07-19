import unittest
from scripts.simulation.providers.models import CompletenessResult,CompletenessStatus,RaceEntryUniverse
class CoreModelsTest(unittest.TestCase):
 def c(self,**kw): return CompletenessResult(CompletenessStatus.COMPLETE,1,1,**kw)
 def test_complete(self): self.assertEqual(self.c().status,CompletenessStatus.COMPLETE)
 def test_complete_count(self):
  with self.assertRaises(ValueError): CompletenessResult(CompletenessStatus.COMPLETE,1,0)
 def test_complete_missing(self):
  with self.assertRaises(ValueError): self.c(missing_keys=('x',))
 def test_incomplete(self): self.assertEqual(CompletenessResult(CompletenessStatus.INCOMPLETE,2,1,missing_keys=('x',)).missing_keys,('x',))
 def test_incomplete_empty(self):
  with self.assertRaises(ValueError): CompletenessResult(CompletenessStatus.INCOMPLETE,1,1)
 def test_invalid_reason(self):
  with self.assertRaises(ValueError): CompletenessResult(CompletenessStatus.INVALID,1,1)
 def test_unsupported_reason(self):
  with self.assertRaises(ValueError): CompletenessResult(CompletenessStatus.UNSUPPORTED,1,1)
 def test_key_overlap(self):
  with self.assertRaises(ValueError): CompletenessResult(CompletenessStatus.INVALID,1,1,missing_keys=('x',),unexpected_keys=('x',),reasons=('r',))
 def test_reasons(self): self.assertEqual(CompletenessResult(CompletenessStatus.INVALID,1,1,reasons=(' b ','a','a')).reasons,('a','b'))
 def test_counts(self):
  with self.assertRaises(ValueError): CompletenessResult(CompletenessStatus.COMPLETE,True,1)
 def test_universe(self): self.assertEqual(RaceEntryUniverse(1,{2,1},{3},{4},{1:1,2:2}).active_entries,(1,2))
 def test_universe_overlap(self):
  with self.assertRaises(ValueError): RaceEntryUniverse(1,{1},{1},set(),{})
 def test_universe_mapping(self):
  with self.assertRaises(ValueError): RaceEntryUniverse(1,{1,2},set(),set(),{1:1,2:1})
 def test_universe_immutable(self):
  a={1};m={1:1};u=RaceEntryUniverse(1,a,set(),set(),m);a.add(2);m[2]=2;self.assertEqual(u.active_entries,(1,));
  with self.assertRaises(TypeError): u.horse_no_to_race_entry_id[2]=2
