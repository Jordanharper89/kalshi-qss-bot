import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_048f_cpmm_vault_evidence_probe as q
class T(unittest.TestCase):
    def test_sources(self):
        self.assertIn("raydium_exact_instruction_pool_roles",str(q.POOLS))
        self.assertIn("raydium_exact_pair_orientation",str(q.ORIENT))
if __name__=="__main__":unittest.main(verbosity=2)
