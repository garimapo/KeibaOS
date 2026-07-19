from decimal import Decimal
import unittest
from scripts.simulation.providers.errors import ProviderValidationError
from scripts.simulation.providers.normalization import *
from scripts.simulation.repositories.interfaces import RaceResultStatus,RaceResultEntryStatus,PayoutStatus
class ValueNormalizationTest(unittest.TestCase):
 def test_parse_positive_int_accepts_supported_values(self):
  for x in (1,'1','01',' 001 '):self.assertEqual(parse_positive_int(x),1)
 def test_parse_positive_int_rejects_non_positive_and_bool(self):
  for x in (True,False,0,-1):
   with self.assertRaises(ProviderValidationError):parse_positive_int(x)
 def test_parse_positive_int_rejects_non_ascii_and_numeric_formats(self):
  for x in (1.0,Decimal('1'),None,'',' ','1.0','+1','-1','1e2','１'):
   with self.assertRaises(ProviderValidationError):parse_positive_int(x)
 def test_parse_positive_int_rejects_invalid_name(self):
  for n in ('',' ',1):
   with self.assertRaises(ProviderValidationError):parse_positive_int(1,n)
 def test_parse_finish_position_accepts_rank_values(self):
  for x in (1,'1','01',' 01 '):self.assertEqual(parse_finish_position(x),1)
 def test_parse_finish_position_maps_explicit_void_markers_to_none(self):
  for x in (None,'',' ','-','取消','除外','中止','競走中止'):self.assertIsNone(parse_finish_position(x))
 def test_parse_finish_position_rejects_invalid_values(self):
  for x in (True,0,-1,1.0,Decimal('1'),'1.0','失格',[]):
   with self.assertRaises(ProviderValidationError):parse_finish_position(x)
 def test_parse_decimal_odds_preserves_trailing_scale(self):self.assertEqual(parse_decimal_odds('1.2300'),Decimal('1.2300'))
 def test_parse_decimal_odds_accepts_decimal_positive_exponent(self):self.assertEqual(parse_decimal_odds(Decimal('1E+2')),Decimal('1E+2'))
 def test_parse_decimal_odds_rejects_string_exponent_notation(self):
  for x in ('1E+2','1e2'):
   with self.assertRaises(ProviderValidationError):parse_decimal_odds(x)
 def test_parse_decimal_odds_rejects_non_positive_and_non_finite(self):
  for x in (Decimal('0'),Decimal('-1'),Decimal('NaN'),Decimal('Infinity')):
   with self.assertRaises(ProviderValidationError):parse_decimal_odds(x)
 def test_parse_decimal_odds_rejects_wrong_types_and_markers(self):
  for x in (1.0,1,True,None,'','-','発売なし','取消','1,230'):
   with self.assertRaises(ProviderValidationError):parse_decimal_odds(x)
 def test_parse_decimal_odds_rejects_more_than_six_decimal_places(self):
  with self.assertRaises(ProviderValidationError):parse_decimal_odds('1.0000001')
 def test_parse_payout_accepts_supported_formats(self):
  for x in (0,100,'0','100','1,230','¥1,230','￥1,230','  ¥1,230  ','999,999'):self.assertEqual(parse_payout_per_100(x),int(str(x).replace('¥','').replace('￥','').replace(',','').strip()))
 def test_parse_payout_rejects_invalid_grouping(self):
  for x in ('1,23','12,34','1,,230',',123','123,','¥','1¥230','1,230円'):
   with self.assertRaises(ProviderValidationError):parse_payout_per_100(x)
 def test_parse_payout_rejects_wrong_types_and_negative_values(self):
  for x in (True,-1,1.0,Decimal('1'),None,'',' ','-100','+100','1.0'):
   with self.assertRaises(ProviderValidationError):parse_payout_per_100(x)
 def test_normalize_result_status_all_values(self):
  for x,y in [('complete',RaceResultStatus.COMPLETE),('一部',RaceResultStatus.PARTIAL),('中止',RaceResultStatus.VOID),('対応外',RaceResultStatus.UNSUPPORTED)]:self.assertEqual(normalize_result_status(x),y)
 def test_normalize_result_entry_status_all_values(self):
  for x,y in [('confirmed',RaceResultEntryStatus.CONFIRMED),('取消',RaceResultEntryStatus.VOID),('対応外',RaceResultEntryStatus.UNSUPPORTED)]:self.assertEqual(normalize_result_entry_status(x),y)
 def test_normalize_payout_status_all_values(self):
  for x,y in [('winning',PayoutStatus.WINNING),('返還',PayoutStatus.REFUND),('中止',PayoutStatus.VOID),('対応外',PayoutStatus.UNSUPPORTED)]:self.assertEqual(normalize_payout_status(x),y)
 def test_status_normalizers_accept_matching_enum(self):self.assertIs(normalize_result_status(RaceResultStatus.COMPLETE),RaceResultStatus.COMPLETE)
 def test_status_normalizers_reject_unknown_and_wrong_types(self):
  for f in (normalize_result_status,normalize_result_entry_status,normalize_payout_status):
   for x in (True,None,1,'','x'):
    with self.assertRaises(ProviderValidationError):f(x)
