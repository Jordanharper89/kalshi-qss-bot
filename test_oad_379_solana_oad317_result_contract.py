import unittest
from qseries_v2.oracle_adapters.independent.oad_376_solana_learned_experience_bridge import SolanaLearnedExperienceRecord
from qseries_v2.oracle_adapters.independent.oad_379_solana_oad317_result_contract import *
class T(unittest.TestCase):
    def test_contract(self):
        r=SolanaLearnedExperienceRecord("e","c","DEX_SWAP","orca","A","B",15,"UP",0.01,"SOLANA_CANONICAL_HISTORY","0"*64,"EXISTING_OCL",False)
        x,_=inspect_oad317_result((r,))
        print("[OAD317-RESULT] type=",x.result_type,"state=",x.state,"fields=",x.fields,"downstream=",x.downstream_hints)
        self.assertTrue(x.result_type)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-379 real OAD-317 return/downstream contract exposed")
