import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint23_full_surface_replenishment_inventory.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_expands_discovery_budget(self):
        self.assertIn("engine.DISCOVERY_BUDGET",self.s)
        self.assertIn("c.MAX_TOKENS",self.s)

    def test_all_matching_dlmm_pools(self):
        self.assertIn("page_size=100",self.s)
        self.assertIn("{mx,my}!={WSOL,token}",self.s)

    def test_pair_identity(self):
        self.assertIn('identity=token+"|"+meta["address"]',self.s)

    def test_no_hard_tvl_filter(self):
        self.assertIn('"hard_tvl_filter":False',self.s)

    def test_replenishment_only(self):
        self.assertIn('"replenishment_only":True',self.s)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
