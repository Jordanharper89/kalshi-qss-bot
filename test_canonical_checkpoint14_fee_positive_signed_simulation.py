import ast,unittest
from pathlib import Path
P=Path("qseries_v2/oracle_execution/solana_atomic_executor/checkpoint14_fee_positive_signed_simulation.py")
class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8"); ast.parse(cls.s)
    def test_fee_positive_gate(self): self.assertIn('if proof["after_fee"]<=0:',self.s)
    def test_freshness_gate(self):
        self.assertIn("MAX_EVENT_AGE_MS=1500.0",self.s); self.assertIn("self.newer_waiting(identity,generation)",self.s)
    def test_signed_simulation(self):
        self.assertIn("VersionedTransaction(",self.s); self.assertIn('"sigVerify":True',self.s)
    def test_full_size_ladder(self): self.assertIn("for size in c12.SIZES:",self.s)
    def test_no_raw_transaction_print(self): self.assertNotIn("print(encoded",self.s)
    def test_no_broadcast(self): self.assertNotIn("sendTransaction",self.s)
if __name__=="__main__": unittest.main(verbosity=2)
