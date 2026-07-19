from dataclasses import FrozenInstanceError
from datetime import datetime,timezone
import unittest
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.models import RawRaceResult,RawRaceResultEntry
class RawResultTest(unittest.TestCase):
 def e(self,**kw): return RawRaceResultEntry(1,2,' 01 ',' ok ',**kw)
 def test_entry_trim(self): self.assertEqual(self.e().finish_text,'01');self.assertEqual(self.e().status_text,'ok')
 def test_horse_invalid(self):
  for x in (0,-1,True,'1'):
   with self.subTest(x=x):
    with self.assertRaises(ProviderValidationError): RawRaceResultEntry(x,2,None,'x')
 def test_entry_id_invalid(self):
  for x in (0,-1,True,'2'):
   with self.subTest(x=x):
    with self.assertRaises(ProviderValidationError): RawRaceResultEntry(1,x,None,'x')
 def test_finish_ok(self):
  for x in (1,'1',None): self.assertEqual(RawRaceResultEntry(1,2,x,'x').finish_text,x)
 def test_finish_invalid(self):
  for x in (True,0,-1,1.2):
   with self.subTest(x=x):
    with self.assertRaises(ProviderValidationError): RawRaceResultEntry(1,2,x,'x')
 def test_status_invalid(self):
  for x in ('',' ',None,1):
   with self.subTest(x=x):
    with self.assertRaises(ProviderValidationError): RawRaceResultEntry(1,2,None,x)
 def test_result_trim_and_aware(self): self.assertEqual(RawRaceResult(' ok ',datetime.now(timezone.utc),()).declared_status,'ok')
 def test_naive(self):
  with self.assertRaises(ProviderValidationError): RawRaceResult('x',datetime.now(),())
 def test_entries_tuple(self): self.assertIsInstance(RawRaceResult('x',None,[self.e()]).entries,tuple)
 def test_duplicates(self):
  with self.assertRaises(ProviderValidationError): RawRaceResult('x',None,[self.e(),self.e()])
 def test_wrong_entry(self):
  with self.assertRaises(ProviderValidationError): RawRaceResult('x',None,[1])
 def test_empty(self): self.assertEqual(RawRaceResult('x',None,()).entries,())
 def test_external_list_immutable(self):
  values=[self.e()];r=RawRaceResult('x',None,values);values.clear();self.assertEqual(len(r.entries),1)
 def test_frozen(self):
  with self.assertRaises(FrozenInstanceError): self.e().horse_no=9
