import inspect
from typing import get_args,get_origin,get_type_hints
import unittest
from scripts.simulation.providers.interfaces import RaceResultProvider,OddsSnapshotProvider,PayoutProvider,ProviderBuildResult
from scripts.simulation.providers.models import RawRaceResult,RawOddsBatch,RawPayoutPublication,ProviderContext,RaceEntryUniverse
from scripts.simulation.repositories.interfaces import PersistedRaceResult,OddsSnapshotBatch,PayoutPublication
class ProtocolSignatureTest(unittest.TestCase):
 def test_race_result_provider_is_protocol(self):self.assertTrue(RaceResultProvider._is_protocol)
 def test_odds_snapshot_provider_is_protocol(self):self.assertTrue(OddsSnapshotProvider._is_protocol)
 def test_payout_provider_is_protocol(self):self.assertTrue(PayoutProvider._is_protocol)
 def test_protocols_are_not_runtime_checkable(self):self.assertFalse(RaceResultProvider._is_runtime_protocol);self.assertFalse(OddsSnapshotProvider._is_runtime_protocol);self.assertFalse(PayoutProvider._is_runtime_protocol)
 def _sig(self,c,n):self.assertEqual(list(inspect.signature(getattr(c,n)).parameters),['self','raw','context','universe'])
 def test_race_result_provider_signature(self):self._sig(RaceResultProvider,'build_race_result')
 def test_odds_snapshot_provider_signature(self):self._sig(OddsSnapshotProvider,'build_odds_batch')
 def test_payout_provider_signature(self):self._sig(PayoutProvider,'build_payout_publication')
 def _hints(self,c,n,raw,value):
  h=get_type_hints(getattr(c,n));self.assertIs(h['raw'],raw);self.assertIs(h['context'],ProviderContext);self.assertIs(h['universe'],RaceEntryUniverse);self.assertIs(get_origin(h['return']),ProviderBuildResult);self.assertEqual(get_args(h['return']),(value,))
 def test_race_result_provider_type_hints(self):self._hints(RaceResultProvider,'build_race_result',RawRaceResult,PersistedRaceResult)
 def test_odds_snapshot_provider_type_hints(self):self._hints(OddsSnapshotProvider,'build_odds_batch',RawOddsBatch,OddsSnapshotBatch)
 def test_payout_provider_type_hints(self):self._hints(PayoutProvider,'build_payout_publication',RawPayoutPublication,PayoutPublication)
 def test_protocol_methods_have_no_repository_parameter(self):
  for c,n in ((RaceResultProvider,'build_race_result'),(OddsSnapshotProvider,'build_odds_batch'),(PayoutProvider,'build_payout_publication')):self.assertEqual(len(inspect.signature(getattr(c,n)).parameters),4)
