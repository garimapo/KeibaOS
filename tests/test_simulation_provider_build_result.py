from dataclasses import FrozenInstanceError,dataclass
import unittest
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.interfaces import ProviderBuildResult
from scripts.simulation.providers.models import CompletenessResult,CompletenessStatus
def c(s=CompletenessStatus.COMPLETE):return CompletenessResult(s,1,1,reasons=('x',) if s!=CompletenessStatus.COMPLETE else ())
@dataclass(frozen=True)
class V: x:int
class BuildResultTest(unittest.TestCase):
 def test_accepts_integer_value(self):self.assertEqual(ProviderBuildResult(1,c()).value,1)
 def test_accepts_string_value(self):self.assertEqual(ProviderBuildResult('x',c()).value,'x')
 def test_accepts_dataclass_value(self):self.assertEqual(ProviderBuildResult(V(1),c()).value,V(1))
 def test_rejects_none_value(self):
  with self.assertRaises(ProviderValidationError):ProviderBuildResult(None,c())
 def test_rejects_none_completeness(self):
  with self.assertRaises(ProviderValidationError):ProviderBuildResult(1,None)
 def test_rejects_wrong_completeness_type(self):
  with self.assertRaises(ProviderValidationError):ProviderBuildResult(1,'x')
 def test_is_frozen(self):
  x=ProviderBuildResult(1,c())
  with self.assertRaises(FrozenInstanceError):x.value=2
 def test_accepts_complete_completeness(self):self.assertEqual(ProviderBuildResult(1,c()).completeness.status,CompletenessStatus.COMPLETE)
 def test_accepts_incomplete_completeness(self):self.assertEqual(ProviderBuildResult(1,CompletenessResult(CompletenessStatus.INCOMPLETE,1,0,missing_keys=('x',))).completeness.status,CompletenessStatus.INCOMPLETE)
 def test_accepts_invalid_completeness(self):self.assertEqual(ProviderBuildResult(1,c(CompletenessStatus.INVALID)).completeness.status,CompletenessStatus.INVALID)
 def test_accepts_unsupported_completeness(self):self.assertEqual(ProviderBuildResult(1,c(CompletenessStatus.UNSUPPORTED)).completeness.status,CompletenessStatus.UNSUPPORTED)
 def test_generic_aliases_can_be_constructed(self):self.assertEqual(ProviderBuildResult[int](1,c()).value,1)
