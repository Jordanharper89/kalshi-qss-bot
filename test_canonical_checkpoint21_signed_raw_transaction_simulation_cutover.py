import ast
import unittest
from pathlib import Path

P=Path("qseries_v2/oracle_execution/solana_atomic_executor/checkpoint21_signed_raw_transaction_simulation_cutover.py")

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_uses_existing_signed_tx_helper(self):
        self.assertIn("r.q87.c.signed_tx(",self.s)

    def test_requires_message_bytes(self):
        self.assertIn("(bytes,bytearray)",self.s)

    def test_sigverify_true(self):
        self.assertIn('"sigVerify":True',self.s)

    def test_no_versionedtransaction_constructor(self):
        self.assertNotIn("VersionedTransaction(",self.s)

    def test_checkpoint20_reused(self):
        self.assertIn("return c20.main()",self.s)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction",self.s)

if __name__=="__main__":
    unittest.main(verbosity=2)
