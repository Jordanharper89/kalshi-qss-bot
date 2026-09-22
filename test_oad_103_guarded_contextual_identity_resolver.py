import unittest
from qseries_v2.oracle_adapters.independent.oad_102_universal_identity_evidence_envelope import IdentityEvidence, IdentityEnvelope
from qseries_v2.oracle_adapters.independent.oad_103_guarded_contextual_identity_resolver import resolve_guarded_identity
class T(unittest.TestCase):
    def test_direct(self):
        e=IdentityEnvelope("P",0,"x",(IdentityEvidence("local","sport","baseball",95,"x"),),(),())
        r=resolve_guarded_identity(e); self.assertEqual((r.sport,r.state),("baseball","RESOLVED_DIRECT"))
    def test_sibling_not_promoted(self):
        e=IdentityEnvelope("P",0,"x",(),(),(IdentityEvidence("sibling","sport","soccer",55,"y"),))
        r=resolve_guarded_identity(e); self.assertEqual((r.sport,r.state),("UNKNOWN","SIBLING_ADVISORY_ONLY"))
if __name__=="__main__":
    print("="*96); print(" OAD-103 CERTIFICATION TEST"); print("="*96)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Direct and parent evidence may resolve only under guarded rules")
    print("[PASS] Sibling-only evidence cannot promote identity")
    print("[DONE] OAD-103 CERTIFIED")
