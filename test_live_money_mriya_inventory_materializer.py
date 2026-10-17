import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "live_money_supervisor.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_materializes_full_surface(self):
        self.assertIn(
            "full_surface_replenishment_inventory.json",
            self.s,
        )
        self.assertIn(
            "[MRIYA_MATERIALIZED]",
            self.s,
        )

    def test_exact_identity(self):
        self.assertIn(
            'return token+"|"+pool',
            self.s,
        )

    def test_reuses_cp24(self):
        self.assertIn(
            "checkpoint24_capacity_aware_warm_universe",
            self.s,
        )
        self.assertIn(
            "INVENTORY_ACCOUNT_CAP=768",
            self.s,
        )

    def test_rotation_between_generations(self):
        self.assertIn(
            "[ROTATION_POLICY] replenishment_between_generations_only=True",
            self.s,
        )
        self.assertIn(
            "rc=child.wait()",
            self.s,
        )

    def test_signer_fail_fast(self):
        self.assertIn(
            "signer_preflight()",
            self.s,
        )
        self.assertIn(
            "zero replenishment attempted",
            self.s,
        )

    def test_mriya_priority_from_capacity(self):
        self.assertIn(
            "[MRIYA_PROMOTE]",
            self.s,
        )
        self.assertIn(
            "[MRIYA_PRIORITY_READY]",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)
        self.assertIn("[BROADCAST] disabled",self.s)


if __name__=="__main__":
    unittest.main(verbosity=2)
