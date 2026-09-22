\

import unittest
from qseries_v2.oracle_adapters.independent.oad_373_solana_universal_economic_event_promotion import promote_economic_behavior
from qseries_v2.oracle_adapters.independent.oad_374_solana_temporal_case_bridge import *

class T(unittest.TestCase):
    def test_case(self):
        e=promote_economic_behavior({"event_id":"e1","slot":100,"block_time":123.0,"behavior_type":"DEX_SWAP","primary_asset":"A","secondary_asset":"B"})
        x=build_temporal_learning_case(e,(15,30,60))
        print("[TEMPORAL]",x.case_id,x.horizons_seconds,x.outcome_state)
        self.assertEqual(x.outcome_state,"OUTCOME_PENDING")
        self.assertEqual(x.horizons_seconds,(15,30,60))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-374 promoted Solana economic events -> temporal learning cases certified")

