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

    def test_signer_fail_fast(self):
        self.assertIn("signer_preflight()",self.s)
        self.assertIn("zero hydration attempted",self.s)
        self.assertIn("discovery_started",self.s)

    def test_signer_uses_real_identity_path(self):
        self.assertIn("money_core.sim_identity()",self.s)
        self.assertIn("QSB_SOLANA_PRIVATE_KEY",self.s)

    def test_paced_exact_binder(self):
        self.assertIn("q44.bind(MRIYA_BIND_LIMIT)",self.s)
        self.assertIn("rpc_valve.install()",self.s)
        self.assertIn("MRIYA_BIND_LIMIT=12",self.s)

    def test_mriya_replenishment_only(self):
        self.assertIn(
            "[MRIYA_ROLE] replenishment_only=True execution_path=False",
            self.s,
        )

    def test_unbound_held_out(self):
        self.assertIn(
            "unbound_candidates_never_enter_execution",
            self.s,
        )
        self.assertIn(
            "[MRIYA_UNBOUND]",
            self.s,
        )

    def test_recheck_signer_each_generation(self):
        self.assertIn(
            "Re-check signer before EVERY new generation",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)
        self.assertIn("[BROADCAST] disabled",self.s)


if __name__=="__main__":
    unittest.main(verbosity=2)
