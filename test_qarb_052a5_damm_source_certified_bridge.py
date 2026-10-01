import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_052a5_damm_source_certified_bridge as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_extract_rejects_other(self): self.assertIsNone(q.extract_role_descriptor({"venue":"ORCA"}))
if __name__=="__main__":unittest.main(verbosity=2)
