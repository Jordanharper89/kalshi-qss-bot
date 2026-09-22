import unittest
from qseries_v2.oracle_adapters.oad_001_foundation import build_oracle_adapter_identity
from qseries_v2.oracle_adapters.oad_002_common_contract import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_002_common_adapter_contract())

    def test_missing_detected(self):
        c = build_oracle_adapter_contract(build_oracle_adapter_identity("a","s","venue"))
        class Empty: pass
        self.assertEqual(set(validate_adapter_implementation(Empty(), c)), set(REQUIRED_OPERATIONS))

    def test_contract_read_only(self):
        c = build_oracle_adapter_contract(build_oracle_adapter_identity("a","s","venue"))
        self.assertTrue(c.read_only)

if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-002 CERTIFICATION TEST")
    print(" COMMON ORACLE ADAPTER CONTRACT")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Common Oracle Adapter contract certified")
    print("[DONE] OAD-002 CERTIFIED")
