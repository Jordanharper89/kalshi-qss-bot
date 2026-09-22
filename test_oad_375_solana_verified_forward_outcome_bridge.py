\

import unittest
from qseries_v2.oracle_adapters.independent.oad_373_solana_universal_economic_event_promotion import promote_economic_behavior
from qseries_v2.oracle_adapters.independent.oad_374_solana_temporal_case_bridge import build_temporal_learning_case
from qseries_v2.oracle_adapters.independent.oad_375_solana_verified_forward_outcome_bridge import *

class T(unittest.TestCase):
    def test_outcome(self):
        e=promote_economic_behavior({"event_id":"e1","slot":1,"behavior_type":"DEX_SWAP","primary_asset":"A"})
        c=build_temporal_learning_case(e,(15,))
        x=attribute_verified_forward_outcome(c,15,100,105)
        print("[OUTCOME]",x.case_id,x.horizon_seconds,x.outcome,x.return_fraction)
        self.assertTrue(x.verified)
        self.assertEqual(x.outcome,"UP")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-375 verified forward outcome bridge certified")

