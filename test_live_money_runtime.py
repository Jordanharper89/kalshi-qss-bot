import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "live_money_runtime.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_runtime_cap(self):
        self.assertIn("MAX_RUNTIME_ACCOUNTS=320",cls.s if False else self.s)
        self.assertIn("RUNTIME_ACCOUNT_RESERVE=2",self.s)

    def test_shards_48(self):
        self.assertIn("WS_SHARD_SIZE=48",self.s)

    def test_truthful_429(self):
        self.assertIn('"http 429" in low',self.s)
        self.assertIn('"too many requests" in low',self.s)

    def test_inventory_preserved(self):
        self.assertIn("full_inventory_preserved_outside_hot_book",self.s)

    def test_money_chain(self):
        self.assertIn("return c26.main()",self.s)

    def test_no_live_send(self):
        self.assertNotIn("sendTransaction",self.s)
        self.assertIn("[LIVE_SEND] DISABLED",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
