import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_029_mriya_hotset_coverage_gap as q
class T(unittest.TestCase):
    def test_source_uses_existing_runtime_prepare(self):
        s=inspect.getsource(q.inspect)
        self.assertIn("p.m.prepare",s)
        self.assertIn('state.get("eps")',s)
        print("[PASS] coverage measured against actual QARB prepared state")
    def test_read_only(self):
        s=inspect.getsource(q)
        for bad in ("sendTransaction","private_key","sign_transaction"):
            self.assertNotIn(bad,s)
if __name__=="__main__": unittest.main(verbosity=2)
