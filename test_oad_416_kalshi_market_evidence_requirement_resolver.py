import unittest
from qseries_v2.oracle_adapters.independent.oad_416_kalshi_market_evidence_requirement_resolver import *
class T(unittest.TestCase):
 def test_weather(self):
  x=resolve_market_evidence_requirement({'ticker':'WX','title':'Will temperature exceed 100 F?'}); self.assertEqual(x.domain,'weather'); self.assertIn('NWS/NOAA',x.source_families)
 def test_crypto(self):
  x=resolve_market_evidence_requirement({'ticker':'BTC','title':'Will Bitcoin exceed 100000?'}); self.assertEqual(x.domain,'crypto'); self.assertIn('COINBASE',x.source_families)
 def test_unknown(self): self.assertEqual(resolve_market_evidence_requirement({'ticker':'X','title':'Completely novel thing'}).state,'UNMAPPED')
if __name__=='__main__':unittest.main(verbosity=2)
