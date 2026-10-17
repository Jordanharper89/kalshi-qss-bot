from pathlib import Path
import unittest

P=Path("qseries_v2/oracle_execution/solana_atomic_executor/checkpoint2c_alt_projection.py")

class T(unittest.TestCase):
    def test_projection_only(self):
        s=P.read_text(encoding="utf-8")
        self.assertIn("CHECKPOINT2C_ALT_PROJECTION_PASS",s)
        self.assertIn("alt_accounts=lambda",s)
        self.assertNotIn("sendTransaction(",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
