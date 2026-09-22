\

import unittest
from qseries_v2.oracle_adapters.independent.oad_347_solana_expanded_decode_multiblock_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_expanded_decode_physical(2)
        print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"program_invocations=",x.program_invocations)
        print("[PHYSICAL] oad342_known_ratio=",OAD342_KNOWN_RATIO,"oad342_economic_resolution_ratio=",OAD342_ECONOMIC_RESOLUTION_RATIO)
        print("[PHYSICAL] known_ratio=",x.known_ratio,"economic_resolution_ratio=",x.economic_resolution_ratio)
        print("[PHYSICAL] known=",x.known,"infrastructure=",x.infrastructure,"economic_known=",x.economic_known,"unknown=",x.unknown)
        print("[PHYSICAL] wallet_flows=",x.wallet_flows,"orderbook_behaviors=",x.orderbook_behaviors,"behavior_counts=",x.behavior_counts)
        print("[PHYSICAL] top_unknown_programs=",x.top_unknown_programs[:12])
        print("[PHYSICAL] top_unresolved_economic_evidence=",x.top_unresolved_economic_evidence[:12])
        self.assertGreaterEqual(x.blocks,1)
        self.assertGreater(x.transactions,0)
        self.assertGreater(x.program_invocations,0)
        self.assertEqual(x.state,"EXPANDED_PROGRAM_DECODE_COVERAGE_MEASURED")
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-347 multi-block physical Solana expanded decode coverage measured")
    print("[PASS] verified identities separated from evidence-only unresolved programs")

