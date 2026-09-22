\
import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_341_solana_token2022_activity_decoder import *

class T(unittest.TestCase):
    def test_decode(self):
        e=SimpleNamespace(signature="s",slot=1)
        a=SimpleNamespace(
            signature="s",
            top_level_program_ids=("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",),
            inner_program_ids=()
        )
        fs=(
            SimpleNamespace(signature="s",mint="A",delta=-2.0),
            SimpleNamespace(signature="s",mint="B",delta=3.0),
        )
        x=decode_token2022_activity((e,),(a,),fs)[0]
        print("[TOKEN2022]",x.token2022_invocations,x.behavior,x.mints)
        self.assertEqual(x.token2022_invocations,1)
        self.assertEqual(x.behavior,"TOKEN_2022_TRANSFER_OR_SWAP_FLOW")
        self.assertEqual(x.mints,("A","B"))

    def test_no_fabrication(self):
        e=SimpleNamespace(signature="u",slot=2)
        a=SimpleNamespace(
            signature="u",
            top_level_program_ids=("UNRESOLVED_PROGRAM",),
            inner_program_ids=()
        )
        x=decode_token2022_activity((e,),(a,),())
        self.assertEqual(x,())

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-341 Token-2022 activity decoder certified")
    print("[PASS] unresolved programs are not mislabeled as Token-2022")
