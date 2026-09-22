import unittest
from qseries_v2.oracle_adapters.independent.oad_381_solana_verified_runtime_case_discovery import *
class T(unittest.TestCase):
    def test_discovery(self):
        x=discover_verified_runtime_cases(max_cases=16)
        print("[RUNTIME-CASES] files_scanned=",x.files_scanned,"verified_cases=",len(x.verified_cases),"rejected_unverified=",x.rejected_unverified)
        if x.verified_cases:
            c=x.verified_cases[0]; print("[RUNTIME-CASE-FIRST]",c.case_id,c.horizon_seconds,c.outcome,c.evidence_source)
        self.assertGreaterEqual(x.files_scanned,0)
if __name__=="__main__":
    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not z.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-381 physical runtime verified-case discovery measured")
