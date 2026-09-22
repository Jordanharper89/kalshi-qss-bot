import unittest
from qseries_v2.oracle_adapters.oad_001_foundation import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_001_oracle_adapter_subsystem_foundation())

    def test_read_only(self):
        p = OracleAdapterSubsystemPolicy()
        self.assertTrue(p.read_only_acquisition)
        self.assertFalse(p.execution_authority)

    def test_identity(self):
        x = build_oracle_adapter_identity("a","s","venue")
        self.assertEqual(x.category_scope, "ALL")

if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-001 CERTIFICATION TEST")
    print(" ORACLE ADAPTER SUBSYSTEM FOUNDATION")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Oracle Adapter subsystem foundation certified")
    print("[DONE] OAD-001 CERTIFIED")
