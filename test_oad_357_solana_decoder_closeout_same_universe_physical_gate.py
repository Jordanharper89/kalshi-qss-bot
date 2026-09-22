\

import unittest
from qseries_v2.oracle_adapters.independent.oad_357_solana_decoder_closeout_same_universe_physical_gate import *

class T(unittest.TestCase):
    def test_physical(self):
        x=measure_decoder_closeout_physical(2)
        print("[PHYSICAL] blocks=",x.blocks,"transactions=",x.transactions,"program_invocations=",x.program_invocations)
        print("[PHYSICAL] previous_known=",x.previous_known,"final_known=",x.final_known,"previous_unknown=",x.previous_unknown,"final_unknown=",x.final_unknown)
        print("[PHYSICAL] previous_known_ratio=",x.previous_known_ratio,"final_known_ratio=",x.final_known_ratio,"delta=",x.known_ratio_delta)
        print("[PHYSICAL] previous_economic_resolution_ratio=",x.previous_economic_resolution_ratio,"final_economic_resolution_ratio=",x.final_economic_resolution_ratio,"delta=",x.economic_resolution_delta)
        print("[PHYSICAL] wallet_flows=",x.wallet_flows,"decoded_behaviors=",x.decoded_behaviors,"behavior_counts=",x.behavior_counts)
        print("[PHYSICAL] remaining_unknowns=",x.remaining_unknowns[:12])
        self.assertGreaterEqual(x.blocks,1)
        self.assertGreater(x.transactions,0)
        self.assertGreater(x.program_invocations,0)
        self.assertEqual(x.state,"DECODER_CLOSEOUT_PHYSICAL_MEASURED")
        self.assertGreaterEqual(x.final_known,x.previous_known)
        self.assertLessEqual(x.final_unknown,x.previous_unknown)
        self.assertGreaterEqual(x.final_known_ratio,x.previous_known_ratio)
        self.assertGreaterEqual(x.final_economic_resolution_ratio,x.previous_economic_resolution_ratio)
        self.assertFalse(x.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-357 same-universe final Solana decoder closeout physically certified")
    print("[PASS] remaining unknowns preserved as non-blocking evidence backlog")

