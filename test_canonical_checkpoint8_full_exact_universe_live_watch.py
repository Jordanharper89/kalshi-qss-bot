import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint8_full_exact_universe_live_watch.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_pair_cap_expanded(self):
        self.assertIn("PAIR_CAP=32",self.s)
        self.assertIn("pd.MAX_PAIRS=PAIR_CAP",self.s)

    def test_account_cap_expanded(self):
        self.assertIn("ACCOUNT_CAP=768",self.s)
        self.assertIn("m.MAX_ACCOUNTS=ACCOUNT_CAP",self.s)

    def test_reuses_checkpoint7_live_logic(self):
        self.assertIn(
            "checkpoint7_live_90s_fee_ranked_watch as c7",
            self.s,
        )
        self.assertIn("return c7.main()",self.s)

    def test_caps_restored(self):
        self.assertIn("pd.MAX_PAIRS=old_pair_cap",self.s)
        self.assertIn("m.MAX_ACCOUNTS=old_account_cap",self.s)

    def test_no_new_runtime(self):
        self.assertNotIn("asyncio.run(",self.s)
        self.assertIn(
            "existing_sharded_direct_websocket=True",
            self.s,
        )

    def test_no_sim_or_broadcast(self):
        self.assertNotIn("simulateTransaction",self.s)
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
