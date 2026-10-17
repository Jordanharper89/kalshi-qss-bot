import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint3_reverse_atomic_compile.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_single_clean_main(self):
        self.assertEqual(self.s.count("def main():"),1)

    def test_control_flow_sentinel(self):
        self.assertIn("class _Checkpoint3Complete(Exception):",self.s)
        self.assertIn("raise _Checkpoint3Complete()",self.s)

    def test_no_sim_contract_dependency(self):
        tail=self.s[self.s.index("def main():"):]
        self.assertNotIn('result["sim"]',tail)
        self.assertNotIn("simulate_current(",tail)

    def test_reverse_certification_preserved(self):
        self.assertIn("CHECKPOINT3_REVERSE_COMPILE_PASS",self.s)
        self.assertIn("METEORA_TO_PUMP",self.s)
        self.assertIn("_build_meteora_reverse_ix_hot(",self.s)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
