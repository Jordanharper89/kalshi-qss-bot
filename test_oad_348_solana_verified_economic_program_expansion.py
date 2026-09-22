\

import unittest
from qseries_v2.oracle_adapters.independent.oad_348_solana_verified_economic_program_expansion import *

class T(unittest.TestCase):
    def test_verified(self):
        rows=(
            identify_verified_economic_program(TESSERA_V_PROGRAM_ID),
            identify_verified_economic_program(BISONFI_PROGRAM_ID),
            identify_verified_economic_program(OKX_LABS_2_PROGRAM_ID),
            identify_verified_economic_program(DFLOW_AGGREGATOR_V4_PROGRAM_ID),
            identify_verified_economic_program(HUMIDIFI_PROGRAM_ID),
        )
        print("[VERIFIED]",tuple((x.name,x.category) for x in rows))
        self.assertTrue(all(x.known and x.market_relevant for x in rows))
        self.assertEqual(identify_verified_economic_program("FLUX6xBayGxLX9UcimVRxXFMHH6q43mAbRvDzSpCsvfK").name,"UNRESOLVED")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-348 verified economically active Solana identity expansion certified")
    print("[PASS] FLUX and other weaker-evidence IDs intentionally remain unresolved")

