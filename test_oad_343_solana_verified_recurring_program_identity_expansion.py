\

import unittest
from qseries_v2.oracle_adapters.independent.oad_343_solana_verified_recurring_program_identity_expansion import *

class T(unittest.TestCase):
    def test_verified(self):
        p=identify_expanded_program(PHOENIX_ETERNAL_PROGRAM_ID)
        a=identify_expanded_program(ARCHER_EXCHANGE_PROGRAM_ID)
        y=identify_expanded_program(PYTH_PRICE_FEED_PROGRAM_ID)
        u=identify_expanded_program("W1LDCARDa67SPBG7TFpQivHnEZXRtxCFP13ysEd1bWR")
        print("[IDENTITIES]",p.name,a.name,y.name,u.name)
        self.assertEqual(p.category,"ORDER_BOOK_DEX")
        self.assertEqual(a.category,"ORDER_BOOK_DEX")
        self.assertEqual(y.category,"ORACLE_INFRASTRUCTURE")
        self.assertFalse(y.market_relevant)
        self.assertFalse(u.known)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-343 verified recurring Solana program identity expansion certified")
    print("[PASS] unverified recurring IDs remain unresolved")

