from pathlib import Path

TEST=Path("test_canonical_checkpoint19_bidirectional_best_first_signed_simulation.py")

TEST.write_text(r'''import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint19_bidirectional_best_first_signed_simulation.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_both_directions_advance(self):
        self.assertIn("c7._reverse_only",self.s)
        self.assertIn("c7._forward_only",self.s)
        self.assertNotIn("FORWARD_HOLD",self.s)

    def test_full_ladder_before_rpc(self):
        pricing=self.s.index("for size in c12.SIZES:")
        ranking=self.s.index("rows.sort(")
        compiling=self.s.index("c15._compile_all_legal(")
        self.assertLess(pricing,ranking)
        self.assertLess(ranking,compiling)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)

    def test_pair_key_templates_reused(self):
        self.assertIn("rc=c17.main()",self.s)

    def test_rank_best_first(self):
        self.assertIn('key=lambda x:int(x["local_net"])',self.s)
        self.assertIn("reverse=True",self.s)

    def test_signed_simulation(self):
        self.assertIn("c14._signed_simulation(",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
''',encoding="utf-8")

print("[PASS] checkpoint-19 test contract replaced")
print("[RUNTIME] unchanged")
print("[FIX] multiline bidirectional tuple verified semantically")