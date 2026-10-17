from pathlib import Path
import unittest
P=Path("qseries_v2/oracle_execution/solana_atomic_executor/alt_manager.py")
class T(unittest.TestCase):
    def test_permanent_component(self):
        s=P.read_text(encoding="utf-8")
        self.assertIn("CANONICAL_ALT_SIM_PASS",s)
        self.assertIn("CANONICAL_ALT_READY",s)
        self.assertIn("ORACLE_CANONICAL_ALT_CREATE",s)
    def test_broadcast_guarded(self):
        s=P.read_text(encoding="utf-8")
        self.assertIn("CANONICAL_ALT_CREATE_NOT_ARMED",s)
        self.assertIn("maxRetries",s)
    def test_state_path(self):
        s=P.read_text(encoding="utf-8")
        self.assertIn("runtime_state/oracle/solana_atomic_executor/canonical_alt.json",s)
if __name__=="__main__":
    unittest.main(verbosity=2)
