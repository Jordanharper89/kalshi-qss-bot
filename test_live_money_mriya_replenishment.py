import ast
import unittest
from pathlib import Path

R=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "live_money_runtime.py"
)
S=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "live_money_supervisor.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=R.read_text(encoding="utf-8")
        cls.s=S.read_text(encoding="utf-8")
        ast.parse(cls.r)
        ast.parse(cls.s)

    def test_mriya_is_replenishment_only(self):
        self.assertIn("mriya_replenishment_only",self.r)
        self.assertIn("[MRIYA_ROLE] replenishment_only=True execution_path=False",self.s)

    def test_uses_existing_mriya_sources(self):
        self.assertIn("qarb_045b_evidence_window_hotset_lifecycle",self.s)
        self.assertIn("qarb_080_single_runtime_dynamic_mriya_supervisor",self.s)
        self.assertIn("run_qarb_043b_paced_mriya_token_discovery.py",self.s)

    def test_unbound_never_enters_execution(self):
        self.assertIn("unbound_candidates_never_enter_execution",self.s)
        self.assertIn("[MRIYA_UNBOUND]",self.s)

    def test_hot_book_prioritizes_mriya(self):
        self.assertIn("identity in mriya_pairs",self.r)
        self.assertIn("token in mriya_tokens",self.r)

    def test_account_cap_preserved(self):
        self.assertIn("MAX_RUNTIME_ACCOUNTS=320",self.r)
        self.assertIn("WS_SHARD_SIZE=48",self.r)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.r)
        self.assertNotIn("sendTransaction",self.s)
        self.assertIn("[BROADCAST] disabled",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
