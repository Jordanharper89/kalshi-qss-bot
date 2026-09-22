\
import unittest
from qseries_v2.oracle_adapters.independent.oad_338_solana_token2022_memo_foundation_repair import *

class T(unittest.TestCase):
    def test_ids(self):
        a=identify_foundation_program(TOKEN_2022_PROGRAM_ID)
        b=identify_foundation_program(MEMO_PROGRAM_ID)
        c=identify_foundation_program("UNRESOLVED_PROGRAM")
        print("[FOUNDATION]",a.name,a.program_id,b.name,b.program_id,c.name)
        self.assertEqual(a.name,"TOKEN_2022")
        self.assertEqual(a.category,"TOKEN")
        self.assertTrue(a.market_relevant)
        self.assertEqual(b.name,"MEMO")
        self.assertEqual(b.category,"INFRASTRUCTURE")
        self.assertFalse(b.market_relevant)
        self.assertEqual(c.name,"UNRESOLVED")
        self.assertFalse(c.market_relevant)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-338 exact Token-2022 + Memo foundation identities certified")
    print("[PASS] unresolved programs remain unresolved rather than guessed")
