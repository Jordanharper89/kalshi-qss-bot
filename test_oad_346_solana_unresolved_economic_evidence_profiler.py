\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_346_solana_unresolved_economic_evidence_profiler import *

class T(unittest.TestCase):
    def test_profile(self):
        attrs=(SimpleNamespace(signature="s",unknown_program_ids=("X","X")),)
        flows=(SimpleNamespace(signature="s",mint="A",delta=-1.0),SimpleNamespace(signature="s",mint="B",delta=1.0))
        x=profile_unresolved_economic_evidence((),attrs,flows)[0]
        print("[UNKNOWN-EVIDENCE]",x.program_id,x.invocations,x.evidence_class)
        self.assertEqual(x.program_id,"X")
        self.assertEqual(x.invocations,2)
        self.assertEqual(x.bidirectional_flow_transactions,1)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-346 unresolved-program economic evidence profiler certified")
    print("[PASS] evidence is measured without assigning unverified protocol identities")

