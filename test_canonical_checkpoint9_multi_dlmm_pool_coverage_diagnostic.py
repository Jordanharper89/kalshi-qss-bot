import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint9_multi_dlmm_pool_coverage_diagnostic.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_page_size_100(self):
        self.assertIn(
            "page=1&page_size=100",
            self.s,
        )

    def test_exact_wsol_pair_filter(self):
        self.assertIn(
            "if {mx,my}!={c.WSOL,str(token)}:",
            self.s,
        )

    def test_all_pools_not_best_only(self):
        self.assertIn(
            "return sorted(",
            self.s,
        )
        self.assertNotIn(
            "best=(",
            self.s,
        )

    def test_selected_pool_comparison(self):
        self.assertIn(
            "currently_selected=",
            self.s,
        )
        self.assertIn(
            "alternate_pools=",
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
