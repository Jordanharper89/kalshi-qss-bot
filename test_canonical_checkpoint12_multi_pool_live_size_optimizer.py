import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint12_multi_pool_live_size_optimizer.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(
            encoding="utf-8"
        )
        ast.parse(cls.s)

    def test_registry_authoritative(self):
        self.assertIn(
            "registry_is_authoritative=True",
            self.s,
        )

    def test_bounded_429_hydration(self):
        self.assertIn(
            "for attempt in range(1,7):",
            self.s,
        )
        self.assertIn(
            "[CHECKPOINT12_429]",
            self.s,
        )

    def test_hydration_failure_visible(self):
        self.assertIn(
            "[CHECKPOINT12_HYDRATE_FAIL]",
            self.s,
        )

    def test_pair_ready_count_visible(self):
        self.assertIn(
            "r.READY_TOKENS={",
            self.s,
        )
        self.assertIn(
            "pair_key(pair)",
            self.s,
        )

    def test_full_size_ladder(self):
        for value in (
            "0.001","0.010","0.025",
            "0.050","0.100","0.180",
            "0.280","0.500","1.000",
            "1.400",
        ):
            self.assertIn(
                value,
                self.s,
            )

    def test_no_execution(self):
        self.assertNotIn(
            "compile_current(",
            self.s,
        )
        self.assertNotIn(
            "simulateTransaction",
            self.s,
        )
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )

if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
