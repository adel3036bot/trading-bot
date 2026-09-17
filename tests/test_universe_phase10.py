from unittest import TestCase
from market.universe_engine import UniverseEngine
class Ref:
 def iter_us_stocks(self,max_pages=None): return [{"ticker":"AAA","active":True,"market":"stocks","type":"CS","primary_exchange":"NYSE"},{"ticker":"ETF","active":True,"market":"stocks","type":"ETF","primary_exchange":"NYSE"},{"ticker":"PENNY","active":True,"market":"stocks","type":"CS","primary_exchange":"NYSE"}]
class Quote:
 def get_quote(self,s): return {"last": 1.0 if s=='PENNY' else 10.0,"data_quality":"VERIFIED"}
class T(TestCase):
 def test_eligibility_and_price_are_not_signal(self):
  r=UniverseEngine(Ref(),Quote()).scan(); self.assertEqual(r['raw'],3);self.assertEqual(len(r['eligible']),2);self.assertEqual(len(r['qualified']),1);self.assertIn('non_common_stock',r['rejections']);self.assertIn('price_below_1_50',r['rejections'])
