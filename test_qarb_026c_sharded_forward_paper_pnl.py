import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026c_sharded_forward_paper_pnl as q

class T(unittest.TestCase):
    def test_sharding(self):
        x=list(range(144))
        s=q.shard_addresses(x,40)
        self.assertEqual([len(a) for a in s],[40,40,40,24])
        self.assertTrue(all(len(a)<=40 for a in s))
        print("[PASS] 144 accounts split into 4 bounded websocket shards")

    def test_no_single_socket_fanout(self):
        src=inspect.getsource(q.serve)
        self.assertIn("shard_addresses(addresses)",src)
        self.assertNotIn("subscription_requests(addresses)",src)
        print("[PASS] serve uses bounded shards instead of one 144-subscription socket")

    def test_no_simulation_or_composer(self):
        src=inspect.getsource(q)
        self.assertNotIn("qsb059",src)
        self.assertNotIn("candidate_instruction_sets",src)
        self.assertFalse(q.EXECUTION_AUTHORITY)
        self.assertTrue(q.PAPER_ONLY)
        print("[PASS] paper-only; no transaction composer or execution authority")

if __name__=="__main__":
    unittest.main(verbosity=2)
