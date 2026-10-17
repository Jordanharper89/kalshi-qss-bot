import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint7_live_90s_fee_ranked_watch.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_exact_90_seconds(self):
        self.assertIn("seconds=90.0",self.s)

    def test_direct_canonical_runtime(self):
        self.assertIn("r.run(",self.s)
        self.assertIn("r.canonical_price=live_price",self.s)

    def test_directions_are_independent(self):
        self.assertIn("def _reverse_only(",self.s)
        self.assertIn("def _forward_only(",self.s)

    def test_all_sizes(self):
        for value in (
            "0.001","0.010","0.025","0.050","0.100",
            "0.180","0.280","0.500","1.000","1.400",
        ):
            self.assertIn(value,self.s)

    def test_positive_only_compile(self):
        self.assertIn(
            'if int(op["local_net"])<=0:',
            self.s,
        )

    def test_real_fee_path(self):
        self.assertIn(
            "c6._compiled_fee(",
            self.s,
        )

    def test_no_sim_or_send(self):
        self.assertNotIn("simulateTransaction",self.s)
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
