import inspect
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_025c_pubkey_serialization_repair as q

class T(unittest.TestCase):
    def test_compose_uses_string_payer(self):
        src = inspect.getsource(q.run)
        self.assertIn("compose_exact_candidates(str(user),token,pump,meteora,size)", src)
        print("[PASS] composer receives JSON-serializable string payer")

    def test_packet_still_uses_pubkey(self):
        src = inspect.getsource(q.run)
        self.assertIn("payer=user,recent_blockhash=bh", src)
        print("[PASS] V0 compiler still receives real Pubkey object")

    def test_execution_false(self):
        self.assertIs(q.execution_authority, False)
        print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    unittest.main(verbosity=2)
