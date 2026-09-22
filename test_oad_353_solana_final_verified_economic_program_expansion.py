\

import unittest
from qseries_v2.oracle_adapters.independent.oad_353_solana_final_verified_economic_program_expansion import *

class T(unittest.TestCase):
    def test_verified(self):
        ids=(METEORA_DBC_PROGRAM_ID,METEORA_DAMM_V2_PROGRAM_ID,ORCA_WHIRLPOOLS_PROGRAM_ID,PUMP_MAYHEM_PROGRAM_ID,RAYDIUM_CLMM_PROGRAM_ID)
        rows=tuple(identify_final_verified_program(x) for x in ids)
        print("[FINAL-VERIFIED]",tuple((x.name,x.category) for x in rows))
        self.assertTrue(all(x.known and x.market_relevant for x in rows))
        self.assertFalse(identify_final_verified_program("99vQwtBwYtrqqD9YSXbdum3KBdxPAVxYTaQ3cfnJSrN2").known)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-353 final verified high-value Solana economic identity expansion certified")
    print("[PASS] weaker-evidence programs remain unresolved")

