import unittest
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_115_observation_impact import ObservationDescriptor,UMD_115_REVISION
from datetime import datetime,timezone
from qseries_v2.oracle_adapters.independent.oad_074_strong_structured_market_association import *
class T(unittest.TestCase):
 def test_no_generic_collision(self):
  l=ImmutableLineage("UMD","UMD-115",UMD_115_REVISION,"1.0.0",(),("oad://074",),datetime.now(timezone.utc))
  d=ObservationDescriptor("x",(("event","earthquake"),),l)
  r=strong_associations(d,{"event=new":("K1",),"event=earthquake":("K2",)})
  self.assertEqual(tuple(x.market_id for x in r),("K2",))
 def test_empty(self):
  l=ImmutableLineage("UMD","UMD-115",UMD_115_REVISION,"1.0.0",(),("oad://074b",),datetime.now(timezone.utc))
  self.assertEqual(strong_associations(ObservationDescriptor("x",(),l),{}),())
if __name__=="__main__":
 print("="*88);print(" OAD-074 CERTIFICATION TEST");print(" STRONG STRUCTURED MARKET ASSOCIATION");print("="*88)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Generic word overlap cannot create an association")
 print("[DONE] OAD-074 CERTIFIED")
