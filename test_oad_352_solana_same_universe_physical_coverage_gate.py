\

import unittest
from qseries_v2.oracle_adapters.independent.oad_352_solana_same_universe_physical_coverage_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_same_universe_coverage(2)
        print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"program_invocations=",x.program_invocations)
        print("[PHYSICAL] old_known=",x.old_known,"new_known=",x.new_known,"old_unknown=",x.old_unknown,"new_unknown=",x.new_unknown)
        print("[PHYSICAL] old_known_ratio=",x.old_known_ratio,"new_known_ratio=",x.new_known_ratio,"delta=",x.known_ratio_delta)
        print("[PHYSICAL] old_economic_resolution_ratio=",x.old_economic_resolution_ratio,"new_economic_resolution_ratio=",x.new_economic_resolution_ratio,"delta=",x.economic_resolution_delta)
        print("[PHYSICAL] wallet_flows=",x.wallet_flows,"decoded_behaviors=",x.decoded_behaviors,"behavior_counts=",x.behavior_counts)
        print("[PHYSICAL] remaining_unknowns=",x.remaining_unknowns[:12])
        self.assertGreaterEqual(x.blocks,1)
        self.assertGreater(x.transactions,0)
        self.assertGreater(x.program_invocations,0)
        self.assertEqual(x.state,"SAME_UNIVERSE_COVERAGE_MEASURED")
        self.assertGreaterEqual(x.new_known,x.old_known)
        self.assertLessEqual(x.new_unknown,x.old_unknown)
        self.assertGreaterEqual(x.new_known_ratio,x.old_known_ratio)
        self.assertGreaterEqual(x.new_economic_resolution_ratio,x.old_economic_resolution_ratio)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-352 same-universe old-vs-new physical Solana coverage certified")
    print("[PASS] coverage deltas are now apples-to-apples on identical live blocks")

