from dataclasses import FrozenInstanceError
from decimal import Decimal
import unittest
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import RawOddsEntry,RawOddsBatch
class RawOddsTest(unittest.TestCase):
 def test_entry_paths(self): self.assertEqual(RawOddsEntry([2,1],None,' x ').race_entry_ids,(2,1));self.assertEqual(RawOddsEntry(None,[1],'').horse_numbers,(1,))
 def test_entry_sources(self):
  for a,b in (([1],[1]),(None,None)):
   with self.assertRaises(ProviderValidationError):RawOddsEntry(a,b,'x')
 def test_ids(self):
  for x in ([],[0],[-1],[True],['1'],[1.0],[1,1]):
   with self.subTest(x=x):
    with self.assertRaises(ProviderValidationError):RawOddsEntry(x,None,'x')
 def test_odds(self): self.assertEqual(RawOddsEntry([1],None,Decimal('1.2300')).odds_text,Decimal('1.2300'))
 def test_odds_bad(self):
  for x in (1,1.0,True,None):
   with self.subTest(x=x):
    with self.assertRaises(ProviderValidationError):RawOddsEntry([1],None,x)
 def test_immutable(self):
  a=[1];e=RawOddsEntry(a,None,'x');a.append(2);self.assertEqual(e.race_entry_ids,(1,))
  with self.assertRaises(FrozenInstanceError):e.odds_text='y'
 def test_batches(self):
  for b in ('単勝','馬連','ワイド','3連複'):self.assertEqual(RawOddsBatch(b,[],False).bet_type,b)
 def test_batch_bad(self):
  for x in ('x',):
   with self.assertRaises(ProviderValidationError):RawOddsBatch(x,[],False)
 def test_bool(self):
  for x in (0,1,None,'x'):
   with self.assertRaises(ProviderValidationError):RawOddsBatch('単勝',[],x)
 def test_entries(self):
  a=[RawOddsEntry([1],None,'x')];b=RawOddsBatch('単勝',a,False);a.clear();self.assertEqual(len(b.entries),1)
 def test_wrong_entry(self):
  with self.assertRaises(ProviderValidationError):RawOddsBatch('単勝',[1],False)
 def test_duplicate_raw_allowed(self): self.assertEqual(len(RawOddsBatch('単勝',[RawOddsEntry([1],None,'x'),RawOddsEntry([1],None,'y')],False).entries),2)
