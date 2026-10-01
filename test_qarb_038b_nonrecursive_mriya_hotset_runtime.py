import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038b_nonrecursive_mriya_hotset_runtime as q
class T(unittest.TestCase):
    def test_no_037_runtime_dependency(self):
        s=inspect.getsource(q)
        self.assertNotIn("qarb_037",s)
        self.assertNotIn("h.hydrate",s)
        print("[PASS] QARB-037 removed from runtime hydration path")
    def test_frozen_original_prepare(self):
        self.assertIsNot(q._BASE_PREPARE_PAIRS,q.priority_prepare_pairs)
        self.assertIn("_BASE_PREPARE_PAIRS(Path(root))",inspect.getsource(q.priority_prepare_pairs))
        print("[PASS] frozen original prepare_pairs called directly")
    def test_original_serve_preserved(self):
        s=inspect.getsource(q)
        self.assertNotIn("async def serve(",s)
        self.assertIn("runtime.serve(Path.cwd()",s)
        print("[PASS] persistent_profit_runtime.serve unchanged")
    def test_read_only(self):
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.EXECUTION_AUTHORITY)
        print("[PASS] PAPER_ONLY=True execution_authority=FALSE")
if __name__=="__main__": unittest.main(verbosity=2)
