import unittest
from qseries_v2.oracle_adapters.independent.oad_305_solana_launch_security_profile import *
class T(unittest.TestCase):
    def test_physical(self):
        x=build_current_solana_launch_security_profile()
        print("[PHYSICAL] token=",x.token_address); print("[PHYSICAL] evidence_state=",x.evidence_state); print("[PHYSICAL] creator_claims=",len(x.creator_deployer_claims))
        self.assertEqual(x.chain_mint_payload.get("token_address"),x.token_address)
        self.assertEqual(x.evidence_state,"INDEPENDENT_CHAIN_AND_PROVIDER_EVIDENCE_UNBLENDED"); self.assertFalse(x.execution_authority)
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-305 Solana launch/security evidence profile physically certified")
