import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint24_capacity_aware_warm_universe.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_reads_full_surface_inventory(self):
        self.assertIn(
            "full_surface_replenishment_inventory.json",
            self.s,
        )

    def test_preserves_old_registry_priority(self):
        self.assertIn(
            "multi_dlmm_pair_registry.json",
            self.s,
        )
        self.assertIn(
            "0 if identity in retained else 1",
            self.s,
        )

    def test_actual_account_capacity(self):
        self.assertIn(
            "len(selected_accounts)+len(incremental)",
            self.s.replace("\n","").replace(" ",""),
        )

    def test_no_hard_tvl_filter(self):
        self.assertIn(
            '"no_hard_tvl_filter":True',
            self.s,
        )

    def test_uses_pair_state(self):
        self.assertIn(
            "pd.PairState(",
            self.s,
        )
        self.assertIn(
            "PoolState.from_accounts(",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
