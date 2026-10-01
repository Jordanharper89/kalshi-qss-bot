import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_048d_cpmm_artifact_field_gap_locator as q

class T(unittest.TestCase):
    def test_required_descriptor(self):
        self.assertEqual(q.NEED,("pool","token_a","token_b","vault_a","vault_b"))

if __name__=="__main__":unittest.main(verbosity=2)
