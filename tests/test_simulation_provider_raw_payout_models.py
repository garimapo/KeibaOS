from dataclasses import FrozenInstanceError
from datetime import datetime,timezone
from decimal import Decimal
import unittest
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import RawPayoutRecord,RawPayoutPublication
class RawPayoutTest(unittest.TestCase):
 def r(self,**kw): return RawPayoutRecord([2,1],None,' 1,000 ',' ok ',**kw)
 def test_paths(self): self.assertEqual(self.r().race_entry_ids,(2,1));self.assertEqual(RawPayoutRecord(None,[1],'0','x').horse_numbers,(1,))
 def test_sources(self):
  for a,b in (([1],[1]),(None,None)):
   with self.assertRaises(ProviderValidationError):RawPayoutRecord(a,b,'0','x')
 def test_ids(self):
  for x in ([],[0],[-1],[True],['1'],[1.0],[1,1]):
   with self.assertRaises(ProviderValidationError):RawPayoutRecord(x,None,'0','x')
 def test_payout(self): self.assertEqual(self.r().payout_text,'1,000');self.assertEqual(RawPayoutRecord([1],None,0,'x').payout_text,0)
 def test_payout_bad(self):
  for x in (-1,1.0,True,None,Decimal('1')):
   with self.assertRaises(ProviderValidationError):RawPayoutRecord([1],None,x,'x')
 def test_status(self):
  with self.assertRaises(ProviderValidationError):RawPayoutRecord([1],None,'0',' ')
 def test_immutable(self):
  a=[1];r=RawPayoutRecord(a,None,'0','x');a.append(2);self.assertEqual(r.race_entry_ids,(1,))
  with self.assertRaises(FrozenInstanceError):r.status_text='y'
 def test_publications(self):
  for b in ('単勝','馬連','ワイド','3連複'):self.assertEqual(RawPayoutPublication(b,None,[],False,False,False).bet_type,b)
 def test_publication_bad(self):
  with self.assertRaises(ProviderValidationError):RawPayoutPublication('x',None,[],False,False,False)
 def test_naive(self):
  with self.assertRaises(ProviderValidationError):RawPayoutPublication('単勝',datetime.now(),[],False,False,False)
 def test_flags(self):
  for x in (0,1,None,'x'):
   with self.assertRaises(ProviderValidationError):RawPayoutPublication('単勝',None,[],x,False,False)
 def test_entries_copy(self):
  a=[self.r()];p=RawPayoutPublication('単勝',datetime.now(timezone.utc),a,True,False,True);a.clear();self.assertEqual(len(p.entries),1)
