from pathlib import Path
import unittest

P=Path("qseries_v2/oracle_execution/solana_atomic_executor/checkpoint2_forward_atomic_sim.py")

class T(unittest.TestCase):
    def test_canonical_only(self):
        s=P.read_text(encoding="utf-8")
        self.assertIn("_execute_route_once",s)
        self.assertIn("PUMP_TO_METEORA",s)
        self.assertIn("CHECKPOINT2_FORWARD_ATOMIC_SIM_PASS",s)

    def test_no_broadcast(self):
        s=P.read_text(encoding="utf-8")
        self.assertNotIn("sendTransaction(",s)

if __name__=="__main__":
    unittest.main(verbosity=2)
