import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint10_multi_dlmm_exact_static_sweep.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_top_eight_plus_selected(self):
        self.assertIn(
            "MAX_POOLS_PER_TOKEN=8",
            self.s,
        )
        self.assertIn(
            "rows[:MAX_POOLS_PER_TOKEN]",
            self.s,
        )

    def test_exact_pump_sdk_math(self):
        self.assertIn(
            "r.q18.exact_snapshot_opportunities(",
            self.s,
        )

    def test_all_sizes(self):
        for value in (
            "0.001","0.010","0.025","0.050","0.100",
            "0.180","0.280","0.500","1.000","1.400",
        ):
            self.assertIn(value,self.s)

    def test_real_dlmm_hydration(self):
        self.assertIn(
            "c.dlmm_arrays(pool)",
            self.s,
        )
        self.assertIn(
            "PoolState.from_accounts(",
            self.s,
        )

    def test_bounded_429(self):
        self.assertIn(
            "for attempt in range(6):",
            self.s,
        )

    def test_no_execution(self):
        self.assertNotIn(
            "simulateTransaction",
            self.s,
        )
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
