import unittest
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import live_money_driver as d

class T(unittest.TestCase):
    def test_prefix_unique(self):
        inv={
            "AAA|POOL1":{
                "pair_key":"AAA|POOL1",
                "token":"AAA",
                "meteora_pool":"POOL1",
            }
        }
        self.assertEqual(d._resolve_prefix("AAA",inv)["pair_key"],"AAA|POOL1")

    def test_prefix_ambiguous_fails_closed(self):
        inv={
            "AAA|POOL1":{"pair_key":"AAA|POOL1","token":"AAA","meteora_pool":"POOL1"},
            "AAA|POOL2":{"pair_key":"AAA|POOL2","token":"AAA","meteora_pool":"POOL2"},
        }
        self.assertIsNone(d._resolve_prefix("AAA",inv))

    def test_positive_promotes_exact_pair(self):
        out=d._record_positive(
            {"pairs":[]},
            {"pair_key":"AAA|POOL1","token":"AAA","meteora_pool":"POOL1"},
            "METEORA_TO_PUMP",
            0.1,
            12345,
            now=1000.0,
        )
        self.assertEqual(out["pairs"][0]["pair_key"],"AAA|POOL1")
        self.assertTrue(out["pairs"][0]["sticky"])

    def test_ttl_prunes_old(self):
        out=d._prune_active(
            {"pairs":[{"pair_key":"A|P","last_after_fee_positive_unix":1.0}]},
            now=d.ACTIVE_TTL_SECONDS+2.0,
        )
        self.assertEqual(out["pairs"],[])

    def test_no_send_transaction(self):
        source=Path(d.__file__).read_text(encoding="utf-8")
        self.assertNotIn("sendTransaction",source)
        self.assertIn("[BROADCAST] disabled",source)

    def test_supervisor_is_canonical_child(self):
        cmd=d._supervisor_command(300,60)
        self.assertIn(
            "qseries_v2.oracle_execution.solana_atomic_executor.live_money_supervisor",
            cmd,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
