import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026_022d_paper_pnl_ledger as q

class T(unittest.TestCase):
    def test_parse_022d_signal(self):
        x=q.parse_signal("[HOT_SIGNAL] token=ABC buy=PUMPSWAP sell=METEORA_DLMM size=0.500000 net=+0.008000000 SOL bps=+160.00 age_ms=1.0")
        self.assertEqual(x["direction"],"PUMPSWAP->METEORA_DLMM")
        self.assertAlmostEqual(x["quoted_net_sol"],0.008)
        print("[PASS] parses physical 022D HOT_SIGNAL format")

    def test_dedup_and_friction(self):
        with tempfile.TemporaryDirectory() as td:
            l=q.Ledger(td)
            s={"token":"T","direction":"PUMPSWAP->METEORA_DLMM","size_sol":1.0,
               "quoted_net_sol":0.01,"quoted_bps":100.0}
            a=l.admit(s,100.0)
            b=l.admit(s,100.5)
            self.assertIsNotNone(a);self.assertIsNone(b)
            self.assertAlmostEqual(a["paper_net_sol"],0.01-q.EXTRA_FRICTION_BPS/10000.0)
        print("[PASS] repeated HOT_SIGNAL deduped and conservative friction applied")

    def test_no_execution(self):
        self.assertFalse(q.EXECUTION_AUTHORITY)
        self.assertTrue(q.PAPER_ONLY)
        print("[PASS] paper-only; no execution authority")

if __name__=="__main__":
    unittest.main(verbosity=2)
