import unittest
from qseries_v2.oracle_adapters.independent.oad_376_solana_learned_experience_bridge import SolanaLearnedExperienceRecord
from qseries_v2.oracle_adapters.independent.oad_378_solana_oad317_exact_case_execution import *
class T(unittest.TestCase):
    def test_exact(self):
        r=SolanaLearnedExperienceRecord("e","c","DEX_SWAP","orca","A","B",15,"UP",0.01,"SOLANA_CANONICAL_HISTORY","0"*64,"EXISTING_OCL",False)
        meta,_=invoke_oad317_exact((r,))
        print("[OAD317-EXACT] cases=",meta.cases_count,"type=",meta.result_type,"state=",meta.result_state,"fields=",meta.result_fields)
        self.assertEqual(meta.cases_count,1)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-378 exact OAD-317 (cases) execution contract certified")
